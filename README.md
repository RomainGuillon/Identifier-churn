# Scoring de churn client — TelcoWave

Prédire quels clients vont résilier, et surtout lesquels cibler en priorité avec un budget de rétention limité.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-blue)
![ROC-AUC](https://img.shields.io/badge/ROC--AUC-0.846-informational)
![Precision@10%](https://img.shields.io/badge/Precision%4010%25-75.4%25-informational)
[![Licence : source-available](https://img.shields.io/badge/licence-source--available-red)](./LICENSE)

Projet de Data Science de bout en bout : de l'analyse exploratoire à un fichier de ciblage commercial actionnable, en passant par la comparaison de six modèles, la calibration des probabilités et l'optimisation économique du seuil de décision.

---

## Contexte et problème

TelcoWave, opérateur télécom européen, perd 26,5 % de ses clients. La direction Customer Success lance un programme de rétention (appel sortant, remise commerciale, changement d'offre), mais le budget ne permet pas de contacter l'ensemble du parc.

La question n'est donc pas « ce client va-t-il churner ? » mais :

> Sur quels clients dépenser les 15 € d'une action de rétention pour maximiser le revenu sauvé ?

C'est un problème de classement, pas de classification. La métrique de pilotage retenue est la `precision@10%` : la proportion de vrais churners dans le top 10 % des clients les plus à risque.

---

## Résultats

| Modèle | ROC-AUC | Précision | Rappel | Precision@10% | Brier (plus bas = mieux) |
|---|---|---|---|---|---|
| Baseline — Régression logistique | 0,846 | 0,510 | 0,819 | 0,754 | 0,168 |
| Finetuné — LR calibrée | 0,846 | 0,660 | 0,525 | 0,754 | 0,136 |
| Dummy (référence) | 0,500 | — | — | 0,262 | 0,266 |

Cibler le top 10 % du score capture 75 % de vrais churners, contre 26 % en ciblage aléatoire : un ciblage environ 2,9 fois plus efficace que le hasard.

Le finetuning n'améliore pas le pouvoir de classement — ROC-AUC et `precision@10%` restent stables. Son apport réel est la calibration : le Brier score passe de 0,168 à 0,136, ce qui rend les probabilités fiables, condition indispensable pour raisonner en euros.

![Comparaison baseline vs finetuné](reports/figures/baseline_vs_finetuned.png)

---

## Du score à la décision business

Hypothèses métier : coût d'une action de rétention = 15 €, valeur mensuelle sauvée = 120 €, taux de succès estimé = 30 %.

Le seuil de rentabilité est `15 / (120 × 0,30) ≈ 0,42`. En dessous, l'action coûte plus qu'elle ne rapporte **en espérance**.

| Stratégie | Clients ciblés | Précision | Gain attendu | Gain constaté |
|---|---|---|---|---|
| Top 5 % | 63 | 76,2 % | ~745 € | ~783 € |
| Top 10 % (budget contraint) | 127 | 75,6 % | ~1 333 € | ~1 551 € |
| Top 20 % | 254 | 66,5 % | ~2 029 € | ~2 274 € |
| Seuil 0,42 (seuil de rentabilité) | 369 (29,1 %) | 59,1 % | ~2 240 € | ~2 313 € |
| **Seuil 0,36 (gain constaté maximal)** | **430 (33,9 %)** | **57,9 %** | ~2 184 € | **~2 514 €** |

Mesuré sur le jeu de test (1 268 clients).

**Gain attendu et gain constaté ne sont pas la même chose**, et la distinction change la décision.

Le *gain attendu* se calcule à partir des seules probabilités : il est disponible en production, avant de connaître l'issue, mais il suppose des probabilités parfaitement calibrées. Le *gain constaté* se calcule sur les résiliations réellement observées : il ne repose sur aucune hypothèse, et c'est le seul chiffre défendable devant une direction.

Conséquence directe ici : maximiser le gain attendu ramène mécaniquement au seuil de rentabilité, 0,42 — c'est une propriété du calcul, pas un résultat. Mesuré sur les issues réelles, l'optimum se situe à **0,36** et rapporte **201 € de plus**. Le modèle sous-estime légèrement le risque dans cette bande, et il est donc rentable de descendre sous le seuil théorique.

Trois arbitrages possibles selon la contrainte : maximiser la qualité du ciblage (top 10 %), rester au seuil de rentabilité (0,42), ou maximiser le gain mesuré (0,36).

![Optimisation du seuil](reports/figures/threshold_optimization.png)

---

## Ce que disent les données

L'ancienneté domine largement les autres variables en permutation importance (0,174 contre 0,026 pour la suivante). Croisée avec l'analyse exploratoire, elle dessine cinq segments prioritaires.

| Rang | Segment | Taux de churn |
|---|---|---|
| 1 | Ancienneté < 12 mois | ~48 % (contre ~7 % au-delà de 60 mois) |
| 2 | Contrat `Month-to-month` | ~43 % (contre 3 % en contrat 2 ans) |
| 3 | Paiement par `Electronic check` | ~45 % |
| 4 | Sans `OnlineSecurity` ni `TechSupport` | risque environ doublé |
| 5 | `MonthlyCharges` > 70 € | élevé |

<p align="center">
  <img src="graphs/churn_by_tenure.png" width="48%" alt="Churn par ancienneté" />
  <img src="graphs/churn_by_segments.png" width="48%" alt="Churn par segment" />
</p>

Ces segments sont déclinés en actions commerciales par client dans [`outputs/ciblage_top10_commercial.csv`](outputs/ciblage_top10_commercial.csv).

---

## Démarrage rapide

```bash
git clone https://github.com/RomainGuillon/Identifier-churn.git
cd Identifier-churn

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

Entraînement et scoring en ligne de commande :

```bash
python src/train.py                     # baseline + finetuné calibré, sauvegarde dans models/ et outputs/
python src/infer.py --threshold 0.42    # produit outputs/scoring_final.csv
```

Options d'inférence disponibles : `--model`, `--data`, `--threshold`, `--output`.

Les notebooks s'exécutent dans l'ordre suivant :

| Notebook | Contenu |
|---|---|
| [`01_eda.ipynb`](notebooks/01_eda.ipynb) | Analyse exploratoire, qualité des données, segments à risque |
| [`02_baseline_model.ipynb`](notebooks/02_baseline_model.ipynb) | Pipeline scikit-learn, comparaison de six modèles, choix du baseline |
| [`03_finetuned_model.ipynb`](notebooks/03_finetuned_model.ipynb) | Feature engineering, GridSearchCV, calibration, seuil économique |

L'ensemble est reproductible (`random_state=42`).

---

## Méthodologie

**Protocole d'évaluation.** Découpage stratifié en trois jeux : train 72 %, test 18 % (comparaison des modèles et choix de seuil), validation 10 % tenue à l'écart jusqu'au contrôle final.

**Prévention des fuites de données.** Toutes les transformations — imputation de `TotalCharges`, standardisation, encodage one-hot — sont apprises uniquement sur le train et encapsulées dans une `Pipeline` scikit-learn. Les 11 clients à `tenure = 0` ont leur `TotalCharges` imputé par `tenure × MonthlyCharges`.

**Modèles comparés.** `DummyClassifier`, `LogisticRegression`, `RandomForest`, `GradientBoosting`, `XGBoost`, `LightGBM`. La régression logistique est retenue : meilleure `precision@10%`, meilleur rappel, et interprétable — un critère qui compte lorsque le modèle doit être défendu devant une direction marketing.

**Finetuning en trois leviers**, activés un à un pour mesurer l'apport de chacun :

1. Feature engineering — `PaymentMethod_grouped`, `Contract_grouped`, `has_family`
2. Hyperparamètres — `GridSearchCV` (cv=5, scoring=roc_auc), configuration retenue `C=10`, `solver=liblinear`
3. Calibration — `CalibratedClassifierCV` (sigmoid, cv=5)

![Calibration](reports/figures/calibration_comparison.png)

Rapport de modélisation complet : [`reports/model_report.md`](reports/model_report.md)

---

## Portée du modèle et conditions d'usage

- **Dataset statique.** Aucune dimension temporelle : le modèle ne capture pas l'évolution du comportement client dans le temps. C'est la condition d'usage la plus structurante — les résultats valent pour un scoring ponctuel, pas pour un suivi de trajectoire.
- **Hypothèse de succès de rétention.** Le taux de 30 % conditionne l'intégralité du calcul de gain. Il doit être validé par test A/B sur le terrain avant toute extrapolation du retour sur investissement — c'est le premier chantier d'une mise en production.
- **Périmètre du finetuning.** Le pouvoir de classement n'est pas amélioré ; le bénéfice porte exclusivement sur la calibration des probabilités, ce qui est précisément ce qu'exige un raisonnement en euros.
- **Extensions identifiées.** Gradient boosting finetuné, features d'interaction (`tenure × Contract`), et intégration d'un historique dès qu'il devient disponible.

---

## Structure du projet

```text
Identifier-churn/
├── data/                       # Telco Customer Churn (7 043 clients, Kaggle)
├── notebooks/                  # 01_eda, 02_baseline_model, 03_finetuned_model
├── src/
│   ├── data_prep.py            # chargement, features, split stratifié
│   ├── train.py                # entraînement baseline et finetuné calibré
│   ├── metrics.py              # ROC-AUC, precision@K, Brier, gain attendu
│   └── infer.py                # scoring en ligne de commande, CSV trié par risque
├── models/                     # baseline.joblib, finetuned.joblib
├── outputs/                    # scorings, métriques, ciblage commercial top 10 et 20 %
├── reports/
│   ├── model_report.md                    # rapport de modélisation détaillé
│   ├── generate_ciblage_commercial.py     # génère les fichiers de ciblage top 10 et 20 %
│   └── figures/                           # comparaisons, calibration, importance, seuil
├── graphs/                     # figures de l'analyse exploratoire
├── LICENSE                     # conditions d'utilisation du code
├── NOTICE.md                   # mentions, contact, provenance des données
└── requirements.txt
```

---

## Données

Dataset public [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (Kaggle) : 7 043 clients, un enregistrement par client, variable cible `Churn` (Yes/No).

Les variables couvrent quatre familles : démographiques (`gender`, `SeniorCitizen`, `Partner`, `Dependents`), de services (`InternetService`, `OnlineSecurity`, `TechSupport`, `StreamingTV`, etc.), contractuelles (`Contract`, `PaperlessBilling`, `PaymentMethod`) et financières (`tenure`, `MonthlyCharges`, `TotalCharges`).

Ce jeu de données reste soumis aux conditions de sa source — voir [`NOTICE.md`](./NOTICE.md).

---

## Stack technique

`pandas`, `numpy`, `scikit-learn`, `xgboost`, `lightgbm`, `matplotlib`, `seaborn`, `plotly`, `joblib`, `jupyter`

---

## 📄 Licence

**Copyright (c) 2026 Romain Guillon — Tous droits réservés.**

Ce dépôt est publié en **accès visible (*source-available*)** : le code est consultable pour évaluer mon travail, mais il **n'est pas open source**.

|  | Autorisé | Interdit |
|---|---|---|
| **Lire le code** | ✅ | |
| **Lancer le projet pour reproduire les résultats** | ✅ | |
| **Copier tout ou partie du code** | | ❌ |
| **Modifier / créer une œuvre dérivée** | | ❌ |
| **Redistribuer / republier** | | ❌ |
| **Usage commercial ou en production** | | ❌ |
| **Entraîner un modèle d'IA dessus** | | ❌ |

Conditions complètes : [`LICENSE`](./LICENSE) — mentions et contact : [`NOTICE.md`](./NOTICE.md).

> Cette approche vous intéresse pour votre propre parc client ? Une **licence commerciale** et un accompagnement à l'intégration sont disponibles. Écrivez-moi, c'est le plus simple.

**English —** This repository is *source-available*, not open source. You may read the code and reproduce the results; you may not copy, modify, redistribute or use it commercially. See [`LICENSE`](./LICENSE). Commercial licensing available on request.

---

Réalisé par Romain Guillon — projet Data Scientist.
