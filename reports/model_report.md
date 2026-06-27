# Rapport de modélisation — Scoring de churn TelcoWave

## 1. Contexte et objectif

La direction Customer Success de TelcoWave souhaite réduire le churn au prochain
trimestre via un programme de rétention ciblé (appel sortant, remise, changement
d'offre), avec un budget marketing limité.

L'objectif n'est pas seulement de prédire une classe `Churn` / `No Churn`, mais de
produire un **score de risque** permettant de classer les clients du plus risqué au
moins risqué, afin de concentrer les actions là où elles rapportent le plus. La
métrique de pilotage est donc la `precision@10%` (qualité du ciblage sur le haut du
classement), complétée par le ROC-AUC, le rappel et le Brier score.

## 2. Données et protocole d'évaluation

Le jeu de données est le Telco Customer Churn (un enregistrement par client, 7043
clients, ~26,5% de churners). La cible est `Churn` (Yes/No).

Le découpage est stratifié sur la cible, en trois jeux :

| Jeu | Part | Rôle |
|---|---|---|
| Train | 72% | Apprentissage |
| Test | 18% | Comparaison des modèles et choix de seuil (1268 clients, churn 26,6%) |
| Validation | 10% | Contrôle final tenu à l'écart |

Toutes les transformations (imputation de `TotalCharges`, scaling, encodage) sont
apprises uniquement sur le train via une `Pipeline` scikit-learn, ce qui évite toute
fuite de données. La logique est factorisée dans `src/` (`data_prep.py`, `metrics.py`,
`train.py`, `infer.py`) et reproductible (`random_state=42`).

## 3. Préparation et encodage

La pipeline de préparation combine, dans un `ColumnTransformer` :

- variables numériques (`tenure`, `MonthlyCharges`, `TotalCharges`, `SeniorCitizen`,
  `has_family`) : imputation de `TotalCharges` par `tenure × MonthlyCharges` pour les
  11 clients à `tenure = 0`, puis `StandardScaler` ;
- variables catégorielles : `OneHotEncoder(handle_unknown="ignore")`.

## 4. Modèle baseline

Le baseline est une `LogisticRegression` (`class_weight="balanced"`) sur les variables
brutes, comparée à un `DummyClassifier` et à plusieurs modèles non linéaires
(RandomForest, GradientBoosting, XGBoost, LightGBM — voir `outputs/metrics_report.csv`).

La régression logistique est retenue comme baseline : elle obtient la meilleure
`precision@10%` (0,754) et le meilleur rappel, tout en restant simple et interprétable,
ce qui est cohérent avec un objectif de ciblage marketing.

## 5. Modèle finetuné

Trois leviers ont été activés, un à la fois :

1. **Feature engineering** : `PaymentMethod_grouped` (regroupement des paiements
   automatiques), `Contract_grouped` (regroupement des contrats longs), `has_family`
   (indicateur Partner ou Dependents).
2. **Hyperparamètres** : `GridSearchCV` (cv=5, scoring=roc_auc) sur `C` et `solver`.
   Meilleure configuration retenue : `C=10`, `solver=liblinear`, `penalty=l2`.
3. **Calibration** : `CalibratedClassifierCV` (méthode sigmoid, cv=5) pour rendre les
   probabilités exploitables dans une décision économique.

### Comparaison baseline vs finetuné (jeu de test)

| Modèle | ROC-AUC | Précision | Rappel | F1 | Precision@10% | Brier |
|---|---|---|---|---|---|---|
| Baseline (LR) | 0,846 | 0,510 | 0,819 | 0,629 | 0,754 | 0,168 |
| Finetuné (LR calibré) | 0,846 | 0,660 | 0,525 | 0,585 | 0,754 | **0,136** |

Le pouvoir de classement (ROC-AUC) et la `precision@10%` sont stables. Le gain réel du
finetuning est ailleurs : la **calibration améliore nettement le Brier score**
(0,168 → 0,136), ce qui rend les probabilités fiables — condition indispensable pour
raisonner en coût/bénéfice au paragraphe suivant. La précision au seuil par défaut
progresse aussi fortement (0,510 → 0,660), au prix d'un rappel plus faible : un
compromis assumé puisque la décision opérationnelle ne se joue pas à 0,5 mais au seuil
économique. Voir `reports/figures/baseline_vs_finetuned.png` et
`calibration_comparison.png`.

## 6. Décision de seuil et stratégie de ciblage

Hypothèses métier : coût d'une action de rétention = **15 €**, valeur mensuelle sauvée
si rétention réussie = **120 €**, taux de succès estimé = **30 %**.

Le seuil économique minimal est `15 / (120 × 0,30) ≈ 0,417` : en dessous, l'action
coûte plus qu'elle ne rapporte en espérance. Le scan de seuils maximisant le gain
attendu total désigne un **seuil optimal de 0,42**, qui cible 369 clients (29,1% du
parc), avec un gain attendu d'environ **2 240 €** sur le jeu de test.

### Comparaison top K%

| Top K% | Clients ciblés | Précision dans le groupe | Gain attendu |
|---|---|---|---|
| 5% | 63 | 76,2% | ~745 € |
| 10% | 126 | 75,4% | ~1 325 € |
| 15% | 190 | 72,6% | ~1 747 € |
| 20% | 253 | 66,4% | ~2 026 € |
| 25% | 317 | 63,7% | ~2 194 € |
| 30% | 380 | 59,2% | ~2 239 € |

Lecture : pour un budget très contraint, le **top 10%** offre la meilleure précision
de ciblage (75,4%). Pour maximiser le gain total, viser le seuil 0,42 (~30% du parc).
Voir `reports/figures/threshold_optimization.png`.

## 7. Interprétabilité et segments à risque

La permutation importance (sur le ROC-AUC) fait ressortir un facteur dominant et
quelques variables secondaires :

| Variable | Importance |
|---|---|
| tenure (ancienneté) | 0,174 |
| TotalCharges | 0,026 |
| Contract — Long term | 0,009 |
| MonthlyCharges | 0,003 |
| PaperlessBilling | 0,003 |
| OnlineSecurity / TechSupport | 0,002 |

L'**ancienneté** est de loin le premier déterminant : les clients récents churnent
massivement. Croisé avec l'EDA, cela dessine les segments prioritaires :

1. Contrat `Month-to-month` (~43% de churn vs 3% pour les contrats 2 ans)
2. Ancienneté < 12 mois (~48% de churn vs ~7% au-delà de 60 mois)
3. Sans `OnlineSecurity` ni `TechSupport` (risque environ doublé)
4. Paiement par `Electronic check` (~45% de churn)
5. `MonthlyCharges` élevé (> 70 €)

Voir `reports/figures/permutation_importance.png`. Le fichier
`outputs/ciblage_top10_commercial.csv` décline ces segments en actions par client.

## 8. Limites et risques

- **Dataset statique** : pas de dimension temporelle, le modèle ne capture pas
  l'évolution du comportement client dans le temps.
- **Taux de succès de rétention** : l'hypothèse de 30% conditionne tout le calcul de
  gain et reste à valider sur le terrain avant d'extrapoler.
- **Pas de fuite de données** détectée : toutes les transformations sont apprises sur
  le train via la pipeline.
- **Pistes d'amélioration** : tester un gradient boosting finetuné, ajouter des
  features d'interaction (ex. `tenure × Contract`), intégrer une dimension temporelle
  si un historique devient disponible.

## 9. Reproduire

```bash
python src/train.py                       # entraîne baseline + finetuné, sauvegarde modèles et métriques
python src/infer.py --threshold 0.42      # produit le fichier de scoring
```

Artefacts produits : `models/baseline.joblib`, `models/finetuned.joblib`,
`outputs/scoring_final.csv` (`customerID`, `proba_churn`, `label_pred`),
`outputs/metrics_report.csv`, figures dans `reports/figures/`.
