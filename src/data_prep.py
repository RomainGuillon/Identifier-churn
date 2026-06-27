"""
Preparation des donnees pour le scoring de churn.

Regroupe le chargement du CSV, le feature engineering, le split
train/test/validation et la construction du preprocessor scikit-learn.
La meme logique est utilisee par les notebooks ; elle est ici factorisee
pour etre importable et reutilisable (train.py, infer.py).
"""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

RANDOM_STATE = 42

# Chemins du projet, calcules depuis l'emplacement de ce fichier
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV_PATH = PROJECT_ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

# Features du modele finetune (avec les variables construites)
FEATURES = [
    "tenure", "MonthlyCharges", "TotalCharges",
    "OnlineSecurity", "InternetService", "OnlineBackup",
    "DeviceProtection", "TechSupport", "PaperlessBilling",
    "SeniorCitizen", "has_family",
    "PaymentMethod_grouped", "Contract_grouped",
]
NUM_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen", "has_family"]
CAT_COLS = [
    "InternetService", "PaymentMethod_grouped", "Contract_grouped",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "PaperlessBilling",
]

# Features du modele baseline (variables brutes, sans feature engineering)
FEATURES_BASELINE = [
    "tenure", "MonthlyCharges", "TotalCharges", "Contract",
    "PaymentMethod", "OnlineSecurity", "InternetService", "OnlineBackup",
    "DeviceProtection", "TechSupport", "PaperlessBilling",
    "Dependents", "Partner", "SeniorCitizen",
]
NUM_COLS_BASELINE = ["tenure", "MonthlyCharges", "SeniorCitizen", "TotalCharges"]
CAT_COLS_BASELINE = [
    "InternetService", "PaymentMethod", "Contract", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "PaperlessBilling",
    "Dependents", "Partner",
]


def load_data(path=RAW_CSV_PATH):
    """Charge le CSV client. Les TotalCharges vides (tenure=0) sont lus en NaN."""
    return pd.read_csv(path, sep=",", skipinitialspace=True)


def add_features(df):
    """Cree les variables derivees utilisees par le modele finetune.

    - PaymentMethod_grouped : regroupe les deux paiements automatiques
    - Contract_grouped      : regroupe les contrats longs (1 et 2 ans)
    - has_family            : indicateur Partner ou Dependents
    """
    df = df.copy()
    df["PaymentMethod_grouped"] = df["PaymentMethod"].replace({
        "Bank transfer (automatic)": "Automatic",
        "Credit card (automatic)": "Automatic",
    })
    df["Contract_grouped"] = df["Contract"].replace({
        "One year": "Long term",
        "Two year": "Long term",
    })
    df["has_family"] = (
        (df["Partner"] == "Yes") | (df["Dependents"] == "Yes")
    ).astype(int)
    return df


def split_data(df, target="Churn"):
    """Split stratifie en train / test / validation.

    On met d'abord 10% de cote pour la validation finale, puis on coupe
    le reste en 80/20 train/test. Stratification sur la cible a chaque etape.
    """
    df_without_val, df_val = train_test_split(
        df, test_size=0.10, random_state=RANDOM_STATE, stratify=df[target]
    )
    df_train, df_test = train_test_split(
        df_without_val, test_size=0.20, random_state=RANDOM_STATE,
        stratify=df_without_val[target],
    )
    return df_train, df_test, df_val


def fill_total_charge(X):
    """Impute les TotalCharges manquants par tenure * MonthlyCharges.

    Place dans la pipeline via FunctionTransformer, donc applique seulement
    a partir des donnees vues a l'entrainement (pas de fuite de donnees).
    """
    X = X.copy()
    mask = X["TotalCharges"].isna()
    X.loc[mask, "TotalCharges"] = X.loc[mask, "tenure"] * X.loc[mask, "MonthlyCharges"]
    return X


def build_preprocessor(num_cols=NUM_COLS, cat_cols=CAT_COLS):
    """Construit le ColumnTransformer : imputation + scaling sur les numeriques,
    One-Hot sur les categorielles."""
    num_pipe = make_pipeline(
        FunctionTransformer(fill_total_charge, validate=False, feature_names_out="one-to-one"),
        StandardScaler(),
    )
    preprocessor = ColumnTransformer(transformers=[
        ("num", num_pipe, num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ])
    preprocessor.set_output(transform="pandas")
    return preprocessor
