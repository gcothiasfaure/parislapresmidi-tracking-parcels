# :package: parislapresmidi-tracking-parcels

Robot de récupération des statuts des colis UPS envoyés par [**Paris L'après-midi**](www.parislapresmidi.com/).

## Description du processus

Le robot s'exécute toutes les heures à la minute 10 depuis 51.83.41.47 : IP de mon VPS hébergé chez [OVH](https://www.ovhcloud.com/).

ÉTAPE 1. Authentification à l'API Google Sheets


ÉTAPE 2. Récupération des données de correspondances des statuts des colis UPS définis dans le fichier Google Sheets de correspondance des statuts

ÉTAPE 3. Récupération des données d'expéditions de Paris L'après-midi définies dans le fichier Google Sheets des expéditions. On récupère les expéditions dont :

- Le transporteur de l'expédition est renseigné comme UPS (colonne D)

- La date de l'expédition (colonne A) date de moins de 100 jours

- Le statut de l'expédition n'est pas encore renseigné comme "LIVRÉ" (colonne K)

Selon les critères précédents et s'il n'existe pas de statuts à récupérer, fin de l'exécution du robot.

ÉTAPE 4. Authentification à l'API UPS (récupération d'un token)

ÉTAPE 5. Récupération du statut des expéditions pour chaque colis via l'API UPS

ÉTAPE 6. Remplissage dans le fichier des expéditions des statuts récupérés dans la nouvelle colonne Statut_suivi (colonne K)

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
