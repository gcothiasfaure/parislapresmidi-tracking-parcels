import logging
import os
import uuid
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import requests
from requests.auth import HTTPBasicAuth

UPS_API_BASE_URL = "https://onlinetools.ups.com/"
DHL_API_URL="https://api-eu.dhl.com/track/shipments"
GOOGLE_SHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_NAME = 'Expéditions'
GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_FILE = 'GOOGLE_DRIVE_API_USER_TOKEN_FILE.json'
NB_JOURS_MAX_MAJ_STATUT = 60
UPS_API_CLIENT_ID = os.environ.get('UPS_API_CLIENT_ID')
UPS_API_CLIENT_SECRET = os.environ.get('UPS_API_CLIENT_SECRET')
PALAM_EXPEDITIONS_GOOGLE_SHEET_ID = os.environ.get('PALAM_EXPEDITIONS_GOOGLE_SHEET_ID')
DHL_API_KEY = os.environ.get('DHL_API_KEY')

def fetch_ups_api_access_token():
    try:
        logging.info("Obtention du token d'accès pour l'API UPS")
        url = UPS_API_BASE_URL+"security/v1/oauth/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-merchant-id': '47A51F'
        }
        payload = 'grant_type=client_credentials'
        response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth(UPS_API_CLIENT_ID, UPS_API_CLIENT_SECRET))
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de l'obtention du token d'accès pour l'API UPS : %s", e, exc_info=True)
        raise

def get_google_sheet_service():
    try:
        logging.info("Configuration de l'API Google Sheets")
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_FILE,GOOGLE_SHEET_SCOPES)
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        logging.error("Erreur lors de la configuration de l'API Google Sheets : %s", e, exc_info=True)
        raise

def fetch_sheet_data(service):
    try:
        logging.info("Chargement des données de la feuille Expéditions du fichier Google Sheets PALAM")
        result = service.spreadsheets().values().get(
            spreadsheetId=PALAM_EXPEDITIONS_GOOGLE_SHEET_ID,
            range=GOOGLE_SHEET_NAME
        ).execute()
        raw_data = result.get('values', [])
        filtered_data_UPS = []
        filtered_data_DHL = []
        for row in raw_data[1:]:
            try:
                row_date = datetime.strptime(row[0], "%d/%m/%Y")
            except ValueError:
                continue
            if len(row) >= 4 and len(row[4])>0:
                if row_date >= datetime.now() - timedelta(days=NB_JOURS_MAX_MAJ_STATUT):
                    if len(row) == 10 or (len(row) > 10 and row[10] != 'LIVRÉ'):
                        if row[3] == 'UPS':
                            filtered_data_UPS.append(row)
                        elif row[3] == 'DHL':
                            filtered_data_DHL.append(row)
        tracking_numbers_UPS = list(set(row[4] for row in filtered_data_UPS))
        tracking_numbers_DHL = list(set(row[4] for row in filtered_data_DHL))
        return raw_data, tracking_numbers_UPS, tracking_numbers_DHL
    except Exception as e:
        logging.error("Erreur lors de la récupération des données de la feuille Expéditions du fichier Google Sheets PALAM : %s", e, exc_info=True)
        raise

def fetch_ups_status_codes(tracking_numbers, ups_api_token):
    mapping_data = {
        'D': 'LIVRÉ',
        'I': 'EN TRANSIT',
        'P': 'EN TRANSIT',
        'M': 'EN TRANSIT',
        'X': 'ANOMALIE',
    }
    try:
        logging.info("Récupération des statuts de suivi UPS et correspondance avec les statuts des expéditions PALAM")
        headers = {
            'Authorization': f"Bearer {ups_api_token}",
            'transId': str(uuid.uuid4().hex),
            'transactionSrc': 'parislapresmidi-tracking-parcels_production'
        }
        status_list = []
        for tracking_number in tracking_numbers:
            url = f"{UPS_API_BASE_URL}api/track/v1/details/{tracking_number}?locale=fr_FR"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            shipments = response.json()['trackResponse']['shipment']
            if "warnings" in shipments[0]:
                status_list.append({
                    'tracking_number': tracking_number,
                    'status_code': 'N° NON RECONNU'
                })
            else:
                packages = shipments[0]['package']
                if len(shipments)>1 or len(packages)>1:
                    logging.warning(f"(UPS) Nb de shipment : {str(len(shipments))} / Nb de package : {str(len(packages))}")
                status_code = packages[0]['activity'][0]["status"]["type"]
                if status_code == 'X' and packages[0]['activity'][0]["status"]["description"] == "Votre colis est en route" and packages[0]['activity'][0]["status"]["code"]=="DA" and packages[0]['activity'][0]["status"]["statusCode"]=="014":
                    status_list.append({
                        'tracking_number': tracking_number,
                        'status_code': 'EN TRANSIT'
                    })
                else:
                    status_list.append({
                        'tracking_number': tracking_number,
                        'status_code': mapping_data.get(status_code, 'INCONNU')
                    })
        return status_list
    except Exception as e:
        logging.error("Erreur lors de la récupération des statuts de suivi UPS et correspondance avec les statuts des expéditions PALAM : %s", e, exc_info=True)
        raise

def fetch_dhl_status_codes(tracking_numbers):
    mapping_data = {
        '101': 'LIVRÉ',
        '102': 'EN TRANSIT',
        '104': 'EN TRANSIT',
        '103': 'ANOMALIE',
    }
    try:
        logging.info("Récupération des statuts de suivi UPS et correspondance avec les statuts des expéditions PALAM")
        headers = {
            'DHL-API-Key': DHL_API_KEY
        }
        status_list = []
        for tracking_number in tracking_numbers:
            url = f"{DHL_API_URL}?trackingNumber={tracking_number}&requesterCountryCode=fr&language=fr"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                status_list.append({
                    'tracking_number': tracking_number,
                    'status_code': 'N° NON RECONNU'
                })
            else:
                shipments = response.json()['shipments']
                if len(shipments)>1:
                    logging.warning(f"(DHL) Nb de shipment : {str(len(shipments))}")
                status_code = shipments[0]['status']['status']
                status_list.append({
                    'tracking_number': tracking_number,
                    'status_code': mapping_data.get(status_code, 'INCONNU')
                })
        return status_list
    except Exception as e:
        logging.error("Erreur lors de la récupération des statuts de suivi DHL et correspondance avec les statuts des expéditions PALAM : %s", e, exc_info=True)
        raise

def update_google_sheet(status_list, raw_data,service):
    try:
        logging.info("Mise à jour des status des expéditions de la feuille Expéditions du fichier Google Sheets PALAM")
        requests = []
        for row_index, row in enumerate(raw_data):
            if row_index == 0:
                continue
            if len(row) > 4 and row[4]:
                tracking_number = row[4]
                for status in status_list:
                    if tracking_number == status['tracking_number']:
                        cell_range = f"{GOOGLE_SHEET_NAME}!K{row_index + 1}"
                        requests.append({
                            'range': cell_range,
                            'values': [[status['status_code']]]
                        })
        if len(requests)>0:
            body = {'data': requests, 'valueInputOption': 'RAW'}
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=PALAM_EXPEDITIONS_GOOGLE_SHEET_ID, 
                body=body
            ).execute()
    except Exception as e:
        logging.error("Erreur lors de la mise à jour des status des expéditions de la feuille Expéditions du fichier Google Sheets PALAM : %s", e, exc_info=True)
        raise