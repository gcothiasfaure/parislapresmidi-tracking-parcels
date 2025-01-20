import logging
from datetime import datetime
import time
import os
import schedule
from pytz import timezone
from functions import (
    get_google_sheet_service,
    fetch_ups_api_access_token,
    fetch_sheet_data,
    fetch_ups_status_codes,
    fetch_dhl_status_codes,
    update_google_sheet
)

log_file_path=os.path.join(os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")), "output"), "app.log")
with open(log_file_path, "w", encoding="utf-8"):
    pass
def timetz(*args):
    return datetime.now(timezone('Europe/Paris')).timetuple()
logging.Formatter.converter = timetz
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("oauth2client").setLevel(logging.WARNING)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)

def process_tracking_updates():
    try:
        logging.info("Début du programme")
        service = get_google_sheet_service()
        sheet_data, ups_tracking_numbers, dhl_tracking_numbers = fetch_sheet_data(service)
        if len(ups_tracking_numbers)>0 or len(dhl_tracking_numbers)>0:
            # UPS
            ups_status_codes = []
            if len(ups_tracking_numbers)>0:
                logging.info(f"Il y a {len(ups_tracking_numbers)} statuts d'expéditions UPS à mettre à jour")
                ups_api_token = fetch_ups_api_access_token()
                ups_status_codes = fetch_ups_status_codes(ups_tracking_numbers, ups_api_token)
            else:
                logging.info("Il n'y a pas de statuts d'expéditions UPS à mettre à jour")
            # DHL
            dhl_status_codes = []
            if len(dhl_tracking_numbers)>0:
                logging.info(f"Il y a {len(dhl_tracking_numbers)} statuts d'expéditions DHL à mettre à jour")
                dhl_status_codes = fetch_dhl_status_codes(dhl_tracking_numbers)
            else:
                logging.info("Il n'y a pas de statuts d'expéditions DHL à mettre à jour")
            status_codes = ups_status_codes+dhl_status_codes
            update_google_sheet(status_codes, sheet_data, service)
        else:
            logging.info("Il n'y a pas de statuts d'expéditions à mettre à jour")
        logging.info("Fin du programme")
        logging.info("")
    except Exception as e:
        pass

# Programmer l'exécution toutes les heures à minute 10
schedule.every().hour.at(":10").do(process_tracking_updates)

logging.info("Lancement du programme")
logging.info("")
# Première exécution immédiate
process_tracking_updates()
while True:
    schedule.run_pending()
    time.sleep(1)