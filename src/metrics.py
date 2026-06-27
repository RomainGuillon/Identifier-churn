"""
Metriques d'evaluation pour le scoring de churn.

precision_at_k est la metrique metier centrale : elle mesure la qualite
du ciblage marketing sur les clients les plus a risque.
"""

import numpy as np
from sklearn.metrics import (
    brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score,
)


def precision_at_k(y_true, y_proba, k=10):
    """Proportion de vrais churners parmi les k% de clients les plus risques.

    On trie les clients par probabilite de churn decroissante, on garde les
    k% du haut, et on regarde combien ont reellement churne.
    """
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)
    n = int(len(y_true) * k / 100)
    top_idx = np.argsort(y_proba)[::-1][:n]
    return float(y_true[top_idx].mean())


def evaluate(name, model, X, y):
    """Calcule l'ensemble des metriques pour un modele entraine."""
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    return {
        "model": name,
        "roc_auc": round(roc_auc_score(y, y_proba), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y, y_pred, zero_division=0), 4),
        "precision@10%": round(precision_at_k(y, y_proba, k=10), 4),
        "brier_score": round(brier_score_loss(y, y_proba), 4),
    }
