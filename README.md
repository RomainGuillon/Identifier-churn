# Scoring de churn client

## Contexte

Vous endossez le rôle de Data Scientist au sein de **TelcoWave**, un opérateur télécom (mobile + fibre) présent en Europe.  
La direction **Customer Success** vous confie un enjeu prioritaire : réduire le **churn** (résiliations) au prochain trimestre.

L'entreprise souhaite mettre en place un programme de rétention ciblé (appels sortants, remise commerciale, changement d'offre).  
Votre mission : construire un modèle de scoring capable d'estimer la probabilité de churn pour chaque client, afin de prioriser les actions sur les clients les plus à risque, avec un budget marketing limité.

Le livrable attendu est un dépôt Git reproductible contenant :
- l'analyse exploratoire,
- un modèle baseline,
- puis un modèle finetuné,
- accompagné d'une recommandation de seuil/stratégie de ciblage (top K% ou seuil de probabilité).


## Données et cible

Le jeu de données fourni est un extrait anonymisé de **TelcoWave** (un enregistrement par client).  
Il contient des informations :
- démographiques,
- sur les services souscrits,
- contractuelles,
- et de facturation (`tenure`, `MonthlyCharges`, `TotalCharges`).

**Variable cible :** `Churn` (`Yes`/`No`)  
Le client a résilié dans la dernière période observée.

**Format :** CSV fourni par l'équipe pédagogique (issu du dataset public Kaggle *Telco Customer Churn*).

## Format et structure du CSV

Le fichier de données est situé dans : `./data`.

### Format
- Type de fichier : CSV
- Encodage : UTF-8 (recommandé)
- Séparateur : `,`
- Une ligne = un client
- La variable cible est `Churn` (`Yes` / `No`)

### Structure attendue
Le dataset contient généralement :
- un identifiant client (`customerID`),
- des variables démographiques (ex. `gender`, `SeniorCitizen`, `Partner`, `Dependents`),
- des variables d'abonnement/services (ex. `PhoneService`, `InternetService`, `OnlineSecurity`, etc.),
- des variables contractuelles (ex. `Contract`, `PaperlessBilling`, `PaymentMethod`, `tenure`),
- des variables de facturation (`MonthlyCharges`, `TotalCharges`),
- la cible `Churn`.
