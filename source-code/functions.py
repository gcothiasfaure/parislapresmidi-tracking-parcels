import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import os
import uuid

from GOOGLE_APIS_SERVICE_ACCOUNT_INFOS import GOOGLE_APIS_SERVICE_ACCOUNT_INFOS

UPS_API_BASE_URL = "https://onlinetools.ups.com/"
UPS_API_CLIENT_ID = os.environ.get('UPS_API_CLIENT_ID')
UPS_API_CLIENT_SECRET = os.environ.get('UPS_API_CLIENT_SECRET')
PALAM_EXPEDITIONS_GOOGLE_SHEET_ID = os.environ.get('PALAM_EXPEDITIONS_GOOGLE_SHEET_ID')
MAPPING_PALAM_UPS_STATUS_CODES_GOOGLE_SHEET_ID = os.environ.get('MAPPING_PALAM_UPS_STATUS_CODES_GOOGLE_SHEET_ID')
GOOGLE_SHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_NAME = 'Feuille 1'

def fetch_ups_api_access_token():
    try:
        logging.info("Obtention du token d'accès UPS.")
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
        logging.error("Erreur lors de la récupération du token UPS : %s", e, exc_info=True)
        raise

def get_google_sheet_service():
    try:
        creds = Credentials.from_service_account_info(GOOGLE_APIS_SERVICE_ACCOUNT_INFOS,scopes=GOOGLE_SHEET_SCOPES)
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        logging.error("Erreur lors de la configuration de l'API Google Sheets : %s", e, exc_info=True)
        raise

def fetch_mapping_data(service):
    try:
        logging.info("Chargement des données de mapping UPS.")
        result = service.spreadsheets().values().get(
            spreadsheetId=MAPPING_PALAM_UPS_STATUS_CODES_GOOGLE_SHEET_ID,
            range=GOOGLE_SHEET_NAME
        ).execute()
        rows = result.get('values', [])
        return {row[1].zfill(3): row[0] for row in rows if len(row) >= 2 and row[0] != 'Libellé statut PALAM' and row[0] and row[1]}
    except Exception as e:
        logging.error("Erreur lors de la récupération des données de mapping : %s", e, exc_info=True)
        raise

def fetch_sheet_data(service):
    try:
        logging.info("Chargement des données de la feuille de calcul.")
        result = service.spreadsheets().values().get(
            spreadsheetId=PALAM_EXPEDITIONS_GOOGLE_SHEET_ID,
            range=GOOGLE_SHEET_NAME
        ).execute()
        raw_data = result.get('values', [])
        filtered_data = []
        for row in raw_data[1:]:
            try:
                row_date = datetime.strptime(row[0], "%d/%m/%Y")
            except ValueError:
                continue
            if len(row) >= 4 and row[3] == 'UPS' and len(row[4])>0:
                if row_date >= datetime.now() - timedelta(days=100):
                    if len(row) == 10 or (len(row) > 10 and row[10] != 'LIVRÉ'):
                        filtered_data.append(row)
        tracking_numbers = list(set(row[4] for row in filtered_data))
        return raw_data, tracking_numbers
    except Exception as e:
        logging.error("Erreur lors de la récupération des données de la feuille : %s", e, exc_info=True)
        raise

def fetch_status_codes(tracking_numbers, ups_api_token, mapping_data):
    try:
        logging.info("Récupération des statuts de suivi UPS.")
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
                    logging.warning(f"Nb de shipment : {str(len(shipments))} / Nb de package : {str(len(packages))}")
                status_code = packages[0]['currentStatus']['code']
                status_list.append({
                    'tracking_number': tracking_number,
                    'status_code': mapping_data.get(status_code, 'INCONNU')
                })
        return status_list
    except Exception as e:
        logging.error("Erreur lors de la récupération des statuts UPS : %s", e, exc_info=True)
        raise

def update_google_sheet(status_list, raw_data,service):
    try:
        logging.info("Mise à jour de la feuille de calcul avec les nouveaux statuts.")
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
            logging.info("Feuille de calcul mise à jour avec succès.")
    except Exception as e:
        logging.error("Erreur lors de la mise à jour de la feuille de calcul : %s", e, exc_info=True)
        raise