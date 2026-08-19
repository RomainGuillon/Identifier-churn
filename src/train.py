# Copyright (c) 2026 Romain Guillon. Tous droits réservés.
#
# Ce fichier est publié en accès visible à des fins de démonstration.
# Toute reproduction, modification, redistribution ou utilisation
# commerciale est interdite sans autorisation écrite préalable.
# Voir le fichier LICENSE à la racine du dépôt.

"""
Entrainement des modeles de scoring de churn.

Reproduit la chaine complete des notebooks 02 et 03 :
  baseline (LogisticRegression) -> finetuning (GridSearch) -> calibration
  -> choix de seuil cout/benefice -> sauvegarde modeles et metriques.

Usage :
    python src/train.py
"""

import sys
from pathlib import Path

# Permet d'importer les modules voisins quel que soit le repertoire courant
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder

from data_prep import (
    CAT_COLS, CAT_COLS_BASELINE, FEATURES, FEATURES_BASELINE,
    NUM_COLS, NUM_COLS_BASELINE, PROJECT_ROOT, RANDOM_STATE,
    add_features, build_preprocessor, load_data, split_data,
)
from metrics import evaluate

MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Hypotheses metier pour le choix de seuil
COST_OFFER = 15      # cout d'une action de retention
SAVED_VALUE = 120    # valeur mensuelle sauvee si retention reussie
RETENTION_RATE = 0.30  # taux de succes estime


def train_baseline(df_train, y_train):
    """LogisticRegression sur les features brutes, sans feature engineering."""
    preprocessor = build_preprocessor(NUM_COLS_BASELINE, CAT_COLS_BASELINE)
    pipe = make_pipeline(
        preprocessor,
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
    )
    pipe.fit(df_train[FEATURES_BASELINE], y_train)
    return pipe


def train_finetuned(X_train, y_train):
    """GridSearch sur C/solver puis calibration sigmoid des probabilites.

    Retourne la pipeline calibree et les meilleurs hyperparametres trouves.
    """
    preprocessor = build_preprocessor(NUM_COLS, CAT_COLS)
    pipe_lr = make_pipeline(
        preprocessor,
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
    )
    param_grid = {
        "logisticregression__C": [0.01, 0.1, 1, 10, 100],
        "logisticregression__solver": ["liblinear", "lbfgs"],
        "logisticregression__penalty": ["l2"],
    }
    grid = GridSearchCV(pipe_lr, param_grid=param_grid, scoring="roc_auc", cv=5, n_jobs=-1)
    grid.fit(X_train, y_train)

    best = grid.best_params_
    calibrated = make_pipeline(
        build_preprocessor(NUM_COLS, CAT_COLS),
        CalibratedClassifierCV(
            estimator=LogisticRegression(
                C=best["logisticregression__C"],
                solver=best["logisticregression__solver"],
                penalty="l2", max_iter=1000,
                class_weight="balanced", random_state=RANDOM_STATE,
            ),
            method="sigmoid", cv=5,
        ),
    )
    calibrated.fit(X_train, y_train)
    return calibrated, best


def optimize_threshold(y_true, y_proba):
    """Cherche le seuil qui maximise le gain attendu (cout/benefice).

    Retourne le tableau de scan et le seuil optimal.
    """
    seuil_eco = COST_OFFER / (SAVED_VALUE * RETENTION_RATE)
    rows = []
    for thr in np.arange(0.05, 0.90, 0.01):
        targeted = y_proba >= thr
        nb = int(targeted.sum())
        if nb == 0:
            continue
        gain = (y_proba[targeted] * SAVED_VALUE * RETENTION_RATE - COST_OFFER).sum()
        rows.append({
            "threshold": round(float(thr), 2),
            "nb_targeted": nb,
            "target_rate": round(nb / len(y_proba), 3),
            "expected_gain": round(float(gain), 1),
            "precision@k": round(float(y_true[targeted].mean()), 3),
        })
    threshold_df = pd.DataFrame(rows)
    optimal = float(threshold_df.loc[threshold_df["expected_gain"].idxmax(), "threshold"])
    return threshold_df, optimal, seuil_eco


def main():
    MODELS_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)

    df = add_features(load_data())
    df_train, df_test, df_val = split_data(df)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(df_train["Churn"].values)
    y_test = label_encoder.transform(df_test["Churn"].values)

    X_train = df_train[FEATURES]
    X_test = df_test[FEATURES]

    # 1. Baseline
    baseline_pipe = train_baseline(df_train, y_train)
    metrics_baseline = evaluate("Baseline (LR)", baseline_pipe, df_test[FEATURES_BASELINE], y_test)

    # 2. Finetune + calibration
    finetuned_pipe, best_params = train_finetuned(X_train, y_train)
    metrics_finetuned = evaluate("Finetune (LR calibre)", finetuned_pipe, X_test, y_test)

    # 3. Choix du seuil sur les probas calibrees du test
    y_proba = finetuned_pipe.predict_proba(X_test)[:, 1]
    threshold_df, optimal_threshold, seuil_eco = optimize_threshold(y_test, y_proba)

    # 4. Sauvegarde des modeles
    joblib.dump(baseline_pipe, MODELS_DIR / "baseline.joblib")
    joblib.dump(finetuned_pipe, MODELS_DIR / "finetuned.joblib")

    # 5. Rapport de metriques
    report = pd.DataFrame([metrics_baseline, metrics_finetuned])
    report.to_csv(OUTPUTS_DIR / "metrics_report.csv", index=False)

    print("Meilleurs hyperparametres :", best_params)
    print(report.to_string(index=False))
    print(f"\nSeuil economique minimal : {seuil_eco:.3f}")
    print(f"Seuil optimal (gain max) : {optimal_threshold}")
    print(f"Modeles sauvegardes dans : {MODELS_DIR}")
    return optimal_threshold


if __name__ == "__main__":
    main()
