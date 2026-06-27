"""
Inference : applique un modele sauvegarde pour produire un fichier de scoring.

Genere un CSV (customerID, proba_churn, label_pred) trie du client le plus
risque au moins risque.

Usage :
    python src/infer.py                       # scoring du modele finetune sur tout le dataset
    python src/infer.py --model models/finetuned.joblib --threshold 0.42
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import pandas as pd

from data_prep import FEATURES, PROJECT_ROOT, add_features, load_data

MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def load_model(path):
    """Charge une pipeline scikit-learn sauvegardee au format joblib."""
    return joblib.load(path)


def score(model, df, threshold=0.42):
    """Retourne le scoring trie par probabilite de churn decroissante.

    df doit contenir customerID et les colonnes brutes ; le feature
    engineering est applique ici pour rester coherent avec l'entrainement.
    """
    df = add_features(df)
    proba_churn = model.predict_proba(df[FEATURES])[:, 1]
    label_pred = (proba_churn >= threshold).astype(int)
    scoring = pd.DataFrame({
        "customerID": df["customerID"].values,
        "proba_churn": proba_churn,
        "label_pred": label_pred,
    })
    return scoring.sort_values("proba_churn", ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Scoring de churn client")
    parser.add_argument("--model", default=str(MODELS_DIR / "finetuned.joblib"))
    parser.add_argument("--data", default=None, help="CSV a scorer (defaut : dataset brut)")
    parser.add_argument("--threshold", type=float, default=0.42)
    parser.add_argument("--output", default=str(OUTPUTS_DIR / "scoring_final.csv"))
    args = parser.parse_args()

    model = load_model(args.model)
    df = load_data(args.data) if args.data else load_data()
    scoring = score(model, df, threshold=args.threshold)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    scoring.to_csv(args.output, index=False)
    print(f"Scoring sauvegarde : {args.output} ({len(scoring)} clients)")
    print(f"Clients cibles (label_pred=1) : {int(scoring['label_pred'].sum())}")


if __name__ == "__main__":
    main()
