# Scoring de churn client

## Contexte

Vous endossez le rôle de Data Scientist au sein de **TelcoWave**, un opérateur télécom présent en Europe.

La direction **Customer Success** souhaite réduire le **churn** au prochain trimestre. L'entreprise veut mettre en place un programme de rétention ciblé : appels sortants, remise commerciale, changement d'offre ou accompagnement client.

L'objectif du projet est de construire un modèle capable d'estimer la probabilité de churn pour chaque client, afin de prioriser les actions sur les clients les plus à risque avec un budget marketing limité.

## Objectif métier

Le projet ne cherche pas seulement à prédire une classe `Churn` / `No Churn`. Il vise surtout à produire un **score de risque** permettant de classer les clients du plus risqué au moins risqué.

La priorité métier est donc :

- identifier les clients les plus susceptibles de churner ;
- concentrer les actions marketing sur les clients les plus à risque ;
- comparer les modèles avec des métriques adaptées au ciblage, notamment `precision@10%`.

## Données

Le jeu de données utilisé est issu du dataset public **Telco Customer Churn**. Il contient un enregistrement par client.

Le fichier est situé dans :

```text
data/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

La variable cible est :

```text
Churn
```

Elle prend deux valeurs :

- `Yes` : le client a résilié ;
- `No` : le client n'a pas résilié.

## Structure des données

Le dataset contient des variables :

- démographiques : `gender`, `SeniorCitizen`, `Partner`, `Dependents` ;
- liées aux services : `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` ;
- contractuelles : `Contract`, `PaperlessBilling`, `PaymentMethod` ;
- financières : `tenure`, `MonthlyCharges`, `TotalCharges`.

### Colonnes principales

| Colonne | Description |
|---|---|
| `customerID` | Identifiant client |
| `tenure` | Ancienneté client en mois |
| `Contract` | Type de contrat |
| `PaymentMethod` | Moyen de paiement |
| `InternetService` | Type d'accès internet |
| `OnlineSecurity` | Option sécurité en ligne |
| `OnlineBackup` | Option sauvegarde |
| `DeviceProtection` | Protection appareil |
| `TechSupport` | Support technique |
| `PaperlessBilling` | Facture dématérialisée |
| `MonthlyCharges` | Montant mensuel facturé |
| `TotalCharges` | Montant total facturé |
| `Churn` | Variable cible |

## Notebooks

Le projet contient deux notebooks principaux.

### `notebooks/01_eda.ipynb`

Ce notebook contient l'analyse exploratoire des données.

Il couvre :

- le chargement du dataset ;
- la vérification des types de données ;
- la recherche de valeurs manquantes ;
- la recherche de doublons ;
- la détection d'outliers sur les variables numériques ;
- les contrôles de cohérence métier ;
- l'analyse du taux global de churn ;
- l'analyse du churn par segments ;
- l'analyse de l'impact financier du churn avec `MonthlyCharges` et `TotalCharges`.

Les principales variables analysées sont :

- `tenure` ;
- `Contract` ;
- `PaymentMethod` ;
- `InternetService` ;
- `OnlineSecurity` ;
- `OnlineBackup` ;
- `DeviceProtection` ;
- `TechSupport` ;
- `PaperlessBilling` ;
- `Partner` ;
- `Dependents` ;
- `PhoneService` ;
- `MultipleLines` ;
- `StreamingTV` ;
- `StreamingMovies` ;
- `MonthlyCharges` ;
- `TotalCharges`.

### Principaux constats EDA

Le taux global de churn est d'environ **26,5%**. Le dataset présente donc un déséquilibre modéré : environ un client sur quatre churn.

L'analyse exploratoire montre que plusieurs variables sont fortement associées au churn :

- les clients récents, notamment ceux avec une faible `tenure`, churnent beaucoup plus que les clients anciens ;
- les contrats `Month-to-month` présentent un taux de churn nettement plus élevé que les contrats d'un ou deux ans ;
- le paiement par `Electronic check` est associé à un churn plus élevé que les paiements automatiques ;
- l'absence de services comme `OnlineSecurity`, `TechSupport`, `OnlineBackup` ou `DeviceProtection` est associée à un risque de churn plus important ;
- les clients avec `Partner` ou `Dependents` semblent plus stables ;
- `PhoneService`, `MultipleLines`, `gender`, `StreamingTV` et `StreamingMovies` semblent moins discriminants pris isolément.

L'analyse financière montre que les clients avec des `MonthlyCharges` élevés représentent un enjeu business important. Les tranches de charges mensuelles élevées combinent un taux de churn important et un revenu mensuel à risque plus élevé.

`TotalCharges` est interprété avec prudence : il représente un revenu historique déjà généré, pas une perte future directe.

## `notebooks/02_baseline_model.ipynb`

Ce notebook contient la préparation des données pour la modélisation, l'entraînement de plusieurs modèles et leur évaluation.

### Split des données

Le dataset est séparé en trois parties :

- un jeu de validation finale de 10% ;
- un jeu d'entraînement ;
- un jeu de test.

La séparation est stratifiée sur `Churn` afin de conserver une proportion similaire de churners dans chaque jeu.

### Variables utilisées

Les variables utilisées pour l'apprentissage sont :

```python
features = [
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
    "Contract",
    "PaymentMethod",
    "OnlineSecurity",
    "InternetService",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "PaperlessBilling",
    "Dependents",
    "Partner",
    "SeniorCitizen"
]
```

### Preprocessing

Le preprocessing est construit avec un `ColumnTransformer`.

Les variables numériques sont :

```python
num_cols = [
    "tenure",
    "MonthlyCharges",
    "SeniorCitizen",
    "TotalCharges"
]
```

Les variables catégorielles sont :

```python
cat_cols = [
    "InternetService",
    "PaymentMethod",
    "Contract",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "PaperlessBilling",
    "Dependents",
    "Partner"
]
```

Les étapes de preprocessing sont :

- imputation de `TotalCharges` manquant avec la formule `tenure * MonthlyCharges` ;
- standardisation des variables numériques avec `StandardScaler` ;
- encodage des variables catégorielles avec `OneHotEncoder` ;
- conservation des noms de colonnes en sortie avec `set_output(transform="pandas")`.

## Modèles comparés

Plusieurs modèles sont entraînés et comparés :

- `DummyClassifier`, comme baseline naïve ;
- `LogisticRegression`, comme baseline interprétable ;
- `RandomForestClassifier` ;
- `GradientBoostingClassifier` ;
- `XGBClassifier` ;
- `LGBMClassifier`.

Le `DummyClassifier` permet de vérifier que les modèles apportent une réelle valeur par rapport à une stratégie simple consistant à prédire systématiquement la classe majoritaire.

## Métriques d'évaluation

Les modèles sont évalués avec des métriques classiques et métier.

Métriques utilisées :

- **ROC-AUC** : capacité globale du modèle à distinguer churners et non-churners ;
- **matrice de confusion** : analyse des vrais positifs, faux positifs, vrais négatifs et faux négatifs ;
- **precision** : proportion de vrais churners parmi les clients prédits comme churners ;
- **recall** : proportion de churners réellement détectés ;
- **F1-score** : compromis entre précision et rappel ;
- **precision@10%** : proportion de vrais churners parmi les 10% de clients ayant la probabilité de churn prédite la plus élevée.

La métrique `precision@10%` est particulièrement importante pour ce projet, car elle simule un cas métier où le budget marketing ne permet de cibler qu'une partie limitée des clients.

## Lecture métier des modèles

Les modèles avec un rappel élevé détectent plus de churners, mais peuvent générer davantage de faux positifs.

Les modèles avec une précision élevée ciblent moins de clients à tort, mais peuvent manquer davantage de churners.

Dans un contexte de budget marketing limité, le choix du modèle ne doit donc pas être fait uniquement avec l'accuracy. Il doit tenir compte du compromis entre :

- la capacité à détecter les clients à risque ;
- la qualité du ciblage ;
- le volume de clients que l'entreprise peut réellement contacter.

## Installation

Créer puis activer un environnement virtuel :

```bash
python -m venv .venv
```

Sous Windows PowerShell :

```bash
.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Dépendances principales

Le projet utilise notamment :

- `pandas` ;
- `numpy` ;
- `scikit-learn` ;
- `matplotlib` ;
- `plotly` ;
- `xgboost` ;
- `lightgbm` ;
- `jupyter` ou `ipykernel`.

## Structure du projet

```text
Projet_DataGong/
├── data/
│   └── WA_Fn-UseC_-Telco-Customer-Churn.csv
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_baseline_model.ipynb
├── README.md
├── requirements.txt
└── .gitignore
```


