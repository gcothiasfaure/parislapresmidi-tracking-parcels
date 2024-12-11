# :package: parislapresmidi-tracking-parcels

Robot de récupération des statuts des colis UPS envoyés par [**Paris L'après-midi**](www.parislapresmidi.com/).

## Description du processus

Le robot s'exécute toutes les heures depuis 51.83.41.47 (VPS hébergé chez [OVH](https://www.ovhcloud.com/)).

1. Authentification à l'API *Google Sheets*.

2. Récupération des données de mapping des statuts des colis UPS définis dans un fichier *Google Sheets*.

3. Récupération des données d'expéditions de **Paris L'après-midi** définies dans un fichier *Google Sheets*. On récupère les expéditions dont :
   - Le transporteur est renseigné comme UPS
   - La date d'expédition date de moins de 100 jours
   - Le statut de l'expédition n'est pas encore renseigné comme **LIVRÉ**

   Si il n'existe pas de statuts à récupérer, fin de l'exécution.

4. Authentification à l'API UPS (récupération d'un token).

5. Récupération du statut des expéditions pour chaque colis.

6. Remplissage dans le fichier des expéditions du ou des statut(s) récupéré(s).

## Installation locale

#### MACOS

```
mkdir -p output
cd source-code
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export UPS_API_CLIENT_ID=XXX
export [...]
```

#### WINDOWS

```
New-Item -Path ".\output" -ItemType Directory -Force
cd source-code
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
$Env:UPS_API_CLIENT_ID='XXX'
$Env: [...]
```