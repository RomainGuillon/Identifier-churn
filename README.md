# Scoring de churn client — Telco Customer Churn

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

Le jeu de données utilisé est issu du dataset public **Telco Customer Churn** (Kaggle). Il contient un enregistrement par client.

Le fichier est situé dans :

```text
data/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

La variable cible est `Churn` (Yes / No) — environ **26,5% de churners** (déséquilibre modéré).

## Structure des données

Le dataset contient des variables :

- démographiques : `gender`, `SeniorCitizen`, `Partner`, `Dependents` ;
- liées aux services : `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` ;
- contractuelles : `Contract`, `PaperlessBilling`, `PaymentMethod` ;
- financières : `tenure`, `MonthlyCharges`, `TotalCharges`.

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
| `TotalCharges` | Montant total facturé (11 valeurs vides si tenure = 0) |
| `Churn` | Variable cible — Yes / No |

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

## Reproduire le projet

Exécuter les notebooks dans l'ordre suivant :

```
notebooks/01_eda.ipynb           → Analyse exploratoire
notebooks/02_baseline_model.ipynb → Modèle baseline
notebooks/03_finetuned_model.ipynb → Modèle finetuné + scoring final
```

Chaque notebook est autonome et reproductible (`random_state=42` partout).

La logique des notebooks est aussi factorisée dans `src/`, exécutable en ligne de commande :

```bash
python src/train.py                    # baseline + finetuné calibré, sauvegarde modèles et métriques
python src/infer.py --threshold 0.42   # génère le fichier de scoring
```

Les artefacts produits sont sauvegardés automatiquement dans :

- `models/` — pipelines entraînées (`.joblib`)
- `outputs/` — fichiers de scoring (`.csv`)
- `reports/figures/` — graphiques exportés

## Notebooks

### `notebooks/01_eda.ipynb` — Analyse exploratoire

- Dictionnaire de données (type, description, exemple, manquants)
- Contrôle qualité : valeurs manquantes, doublons, outliers (IQR), cohérences métier
- Taux de churn global et par segments (contrat, tenure, PaymentMethod, InternetService, services additionnels, profil familial)
- Analyse de l'impact financier (revenu mensuel à risque par tranche de MonthlyCharges)
- Définition du protocole d'évaluation

**Principaux constats :**

- Les clients récents (tenure < 12 mois) ont un taux de churn de ~48%, contre ~7% pour les clients anciens (> 60 mois)
- Les contrats `Month-to-month` churnent à 43%, contre 3% pour les contrats `Two year`
- Le paiement par `Electronic check` est associé à un churn de ~45%
- L'absence de `OnlineSecurity` ou `TechSupport` double environ le risque de churn
- `gender`, `PhoneService`, `MultipleLines` sont peu discriminants

### `notebooks/02_baseline_model.ipynb` — Modèle baseline

- Pipeline scikit-learn complète : imputation `TotalCharges`, `StandardScaler`, `OneHotEncoder` via `ColumnTransformer`
- Comparaison de 6 modèles : `DummyClassifier`, `LogisticRegression`, `RandomForestClassifier`, `GradientBoostingClassifier`, `XGBClassifier`, `LGBMClassifier`
- Évaluation : ROC-AUC, precision, recall, F1, precision@10%
- Tableau comparatif visuel + matrices de confusion
- Sauvegarde du modèle retenu et du fichier de scoring (`customerID`, `proba_churn`, `label_pred`)

**Modèle retenu :** `LogisticRegression` — meilleure `precision@10%` (75,4%) et meilleur rappel, cohérent avec l'objectif de ciblage marketing.

### `notebooks/03_finetuned_model.ipynb` — Modèle finetuné

- **Feature engineering** : `PaymentMethod_grouped` (paiements automatiques regroupés), `Contract_grouped` (contrats longs regroupés), `has_family` (indicateur Partner ou Dependents)
- **Hyperparamètres** : GridSearchCV sur `C` et `solver` (cv=5, scoring=roc_auc)
- **Calibration** : `CalibratedClassifierCV` (sigmoid) — courbe de calibration + Brier score
- **Interprétabilité** : permutation importance — top 15 variables
- **Choix de seuil** : optimisation coût/bénéfice (coût offre = 15 €, valeur sauvée = 120 €, taux de succès = 30 %)
- **Rapport comparatif** : baseline vs finetuné côte à côte
- **Scoring final** : `customerID`, `proba_churn`, `label_pred`

## Résultats

| Modèle | ROC-AUC | Recall | Precision@10% | Brier Score |
|---|---|---|---|---|
| Baseline (LR) | 0.846 | 0.819 | 0.754 | 0.168 |
| Finetuné (LR calibré) | 0.846 | 0.525 | 0.754 | 0.136 |

Le finetuning n'améliore pas le pouvoir de classement (ROC-AUC et precision@10% stables) : son apport est la **calibration** (Brier 0.168 → 0.136), qui rend les probabilités fiables pour la décision coût/bénéfice. Détail complet dans `reports/model_report.md` et `outputs/metrics_report*.csv`.

## Décision de seuil et stratégie de ciblage

**Hypothèses métier :**

- Coût d'une action de rétention : **15 €**
- Valeur mensuelle sauvée si rétention réussie : **120 €**
- Taux de succès estimé de la rétention : **30 %**

Le seuil économique minimal est : `15 / (120 × 0.30) ≈ 0.42`

En dessous de ce seuil, l'action coûte plus qu'elle ne rapporte en espérance.

**Recommandation :** utiliser le seuil optimal calculé dans `03_finetuned_model.ipynb` (section 9) qui maximise le gain attendu total. Pour un budget très contraint, cibler le **top 10%** offre la meilleure precision@10%.

**Segments prioritaires (par ordre d'importance) :**

1. Contrat `Month-to-month`
2. Ancienneté < 12 mois
3. Sans `OnlineSecurity` ni `TechSupport`
4. Paiement par `Electronic check`
5. `MonthlyCharges` > 70 €

## Limites et risques

- **Dataset statique** : pas de dimension temporelle, le modèle ne capture pas l'évolution du comportement client dans le temps.
- **Taux de succès de rétention** : l'hypothèse de 30% est à valider sur le terrain avant d'extrapoler le gain attendu.
- **SeniorCitizen** : variable binaire (0/1) traitée comme numérique — à surveiller.
- **Fuite de données** : toutes les transformations apprennent uniquement sur le train via la Pipeline scikit-learn. Aucun leakage détecté.
- **Pistes d'amélioration** : tester XGBoost/LightGBM finetuné, ajouter des features d'interaction (ex. `tenure × Contract`), intégrer une dimension temporelle si des données historiques sont disponibles.

## Structure du projet

```text
Projet_DataGong/
├── data/
│   └── WA_Fn-UseC_-Telco-Customer-Churn.csv
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_baseline_model.ipynb
│   └── 03_finetuned_model.ipynb
├── models/
│   ├── baseline.joblib
│   └── finetuned.joblib
├── outputs/
│   ├── scoring_test.csv
│   ├── scoring_val.csv
│   ├── scoring_final.csv
│   ├── metrics_report.csv
│   └── metrics_report_calibrated.csv
├── reports/
│   ├── model_report.md
│   └── figures/
│       ├── model_comparison.png
│       ├── calibration_comparison.png
│       ├── permutation_importance.png
│       ├── threshold_optimization.png
│       └── baseline_vs_finetuned.png
├── src/
│   ├── data_prep.py
│   ├── train.py
│   ├── metrics.py
│   └── infer.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Dépendances principales

- `pandas`, `numpy`
- `scikit-learn`
- `matplotlib`, `plotly`
- `xgboost`, `lightgbm`
- `joblib`
- `jupyter` / `ipykernel`
