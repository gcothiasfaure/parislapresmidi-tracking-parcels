import logging
import schedule
import time
from functions import (
    fetch_ups_api_access_token,
    fetch_mapping_data,
    fetch_sheet_data,
    fetch_status_codes,
    update_google_sheet
)

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_tracking_updates():
    try:
        logging.info("Début de la mise à jour des statuts de suivi.")
        ups_api_token = fetch_ups_api_access_token()
        mapping_data = fetch_mapping_data()
        sheet_data, ups_tracking_numbers = fetch_sheet_data()
        status_codes = fetch_status_codes(ups_tracking_numbers, ups_api_token, mapping_data)
        update_google_sheet(status_codes, sheet_data)
        logging.info("Mise à jour des statuts terminée avec succès.")
    except Exception as e:
        logging.error("Une erreur est survenue lors du traitement des mises à jour : %s", e, exc_info=True)

# Programmer l'exécution toutes les heures à l'heure pile
schedule.every().hour.at(":00").do(process_tracking_updates)

if __name__ == "__main__":
    logging.info("Démarrage du programme de mise à jour des statuts.")
    process_tracking_updates()  # Première exécution immédiate
    while True:
        schedule.run_pending()
        time.sleep(1)