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

### Colonnes et types

| Colonne           | Type (brut CSV)   | Description |
|---                |---                |---|
| `customerID`      | `str`             | Identifiant client unique |
| `gender`          | `str`             | Sexe du client |
| `SeniorCitizen`   | `int64`           | Client senior (0/1) |
| `Partner`         | `str`             | A un partenaire (Yes/No) |
| `Dependents`      | `str`             | A des personnes à charge (Yes/No) |
| `tenure`          | `int64`           | Ancienneté client (mois) |
| `PhoneService`    | `str`             | Service téléphonique (Yes/No) |
| `MultipleLines`   | `str`             | Lignes multiples (Yes/No/No phone service) |
| `InternetService` | `str`             | Type d’accès internet |
| `OnlineSecurity`  | `str`             | Option sécurité en ligne |
| `OnlineBackup`    | `str`             | Option sauvegarde en ligne |
| `DeviceProtection`| `str`             | Protection appareil |
| `TechSupport`     | `str`             | Support technique |
| `StreamingTV`     | `str`             | Streaming TV |
| `StreamingMovies` | `str`             | Streaming films |
| `Contract`        | `str`             | Type de contrat |
| `PaperlessBilling`| `str`             | Facture dématérialisée (Yes/No) |
| `PaymentMethod`   | `str`             | Méthode de paiement |
| `MonthlyCharges`  | `float64`         | Facturation mensuelle |
| `TotalCharges`    | `str`             | Facturation cumulée |
| `Churn`           | `str`             | **Cible** (Yes/No) |

## Lexique

⚠️ **Attention :**  Dans les Notebooks (Markdown) j'utilise 'x' pour le signe multiplié pour ne pas le confondre avec * pour les calcul matriciels 



