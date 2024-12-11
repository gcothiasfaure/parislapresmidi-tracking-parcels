import os
from urllib.parse import quote

GOOGLE_APIS_SERVICE_ACCOUNT_INFOS = {
  "type": "service_account",
  "project_id": os.environ("GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_PROJECT_ID"),
  "private_key_id": os.environ.get('GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_PRIVATE_KEY_ID'),
  "private_key": os.environ.get('GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_PRIVATE_KEY'),
  "client_email": os.environ.get('GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_CLIENT_EMAIL'),
  "client_id": os.environ.get('GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_CLIENT_ID'),
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/"+quote(os.environ.get('GOOGLE_APIS_SERVICE_ACCOUNT_INFOS_CLIENT_EMAIL'), safe=""),
  "universe_domain": "googleapis.com"
}