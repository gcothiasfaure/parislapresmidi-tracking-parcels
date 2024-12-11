import logging
from datetime import datetime
import schedule
import time
import os
from pytz import timezone
from functions import (
    get_google_sheet_service,
    fetch_ups_api_access_token,
    fetch_mapping_data,
    fetch_sheet_data,
    fetch_status_codes,
    update_google_sheet
)

def timetz(*args):
    return datetime.now(timezone('Europe/Paris')).timetuple()
logging.Formatter.converter = timetz
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")), "output"), "app.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def process_tracking_updates():
    try:
        logging.info("Début de la mise à jour des statuts de suivi.")
        service = get_google_sheet_service()
        mapping_data = fetch_mapping_data(service)
        sheet_data, ups_tracking_numbers = fetch_sheet_data(service)
        if len(ups_tracking_numbers)>0:
            logging.info(f"Il y a {len(ups_tracking_numbers)} statuts à mettre à jour.")
            ups_api_token = fetch_ups_api_access_token()
            status_codes = fetch_status_codes(ups_tracking_numbers, ups_api_token, mapping_data)
            update_google_sheet(status_codes, sheet_data,service)
        else:
            logging.info("Il n'y a pas de statuts à mettre à jour.")
        logging.info("Mise à jour des statuts terminée avec succès.")
        logging.info("")
    except Exception as e:
        pass

# Programmer l'exécution toutes les heures à l'heure pile
schedule.every().hour.at(":20").do(process_tracking_updates)

logging.info("Démarrage du programme.")
# Première exécution immédiate
process_tracking_updates()
while True:
    schedule.run_pending()
    time.sleep(1)