# Copyright (c) 2026 Romain Guillon. Tous droits réservés.
#
# Ce fichier est publié en accès visible à des fins de démonstration.
# Toute reproduction, modification, redistribution ou utilisation
# commerciale est interdite sans autorisation écrite préalable.
# Voir le fichier LICENSE à la racine du dépôt.

import pandas as pd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
SCORING_PATH = ROOT / "outputs" / "scoring_final.csv"
OUT_TOP10 = ROOT / "outputs" / "ciblage_top10_commercial.csv"
OUT_TOP20 = ROOT / "outputs" / "ciblage_top20_commercial.csv"


def action_recommandee(row):
    if row["Contract"] == "Month-to-month":
        return "Proposer migration vers contrat 1 an avec remise"
    if row["TechSupport"] == "No" or row["OnlineSecurity"] == "No":
        return "Proposer pack support + securite"
    if row["PaymentMethod"] == "Electronic check":
        return "Proposer passage au prelevement auto avec avantage"
    return "Appel de retention standard"


def main():
    df_clients = pd.read_csv(DATA_PATH)
    df_score = pd.read_csv(SCORING_PATH)

    # Jointure pour récupérer les infos métier utiles aux commerciaux
    df = df_score.merge(df_clients, on="customerID", how="left")

    # Tri décroissant du risque
    df = df.sort_values("proba_churn", ascending=False).reset_index(drop=True)

    # Taille des cibles
    n = len(df)
    top10_n = max(1, int(round(n * 0.10)))
    top20_n = max(1, int(round(n * 0.20)))

    # Segments de priorité
    df["priorite"] = "P3 - A suivre"
    df.loc[: top10_n - 1, "priorite"] = "P1 - Appel immediat"
    df.loc[top10_n : top20_n - 1, "priorite"] = "P2 - Appel cette semaine"

    # Action recommandée simple
    df["action_recommandee"] = df.apply(action_recommandee, axis=1)

    cols = [
        "customerID",
        "proba_churn",
        "priorite",
        "action_recommandee",
        "tenure",
        "Contract",
        "PaymentMethod",
        "MonthlyCharges",
        "TechSupport",
        "OnlineSecurity",
        "InternetService",
    ]
    df_out = df[cols].copy()
    df_out["proba_churn"] = df_out["proba_churn"].round(4)

    df_out.head(top10_n).to_csv(OUT_TOP10, index=False)
    df_out.head(top20_n).to_csv(OUT_TOP20, index=False)

    print(f"Top 10% exporté: {OUT_TOP10} ({top10_n} clients)")
    print(f"Top 20% exporté: {OUT_TOP20} ({top20_n} clients)")


if __name__ == "__main__":
    main()
