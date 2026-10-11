from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from model_config import (
    FEATURES,
    MODEL_CONFIGS,
    RANDOM_STATE,
    TARGET,
    make_pipeline,
)

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "Combined_Projects_Dataset_100_enriched_v2.xlsx"


def main() -> None:
    df = pd.read_excel(DATASET)
    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # Final thesis-selected ML configuration.
    pipeline = make_pipeline(MODEL_CONFIGS["LR_C10"])
    pipeline.fit(X_train, y_train)

    pred = pipeline.predict(X_test)

    print("Selected model: Logistic Regression (C=10)")
    print(f"Training records: {len(X_train)}")
    print(f"Held-out records: {len(X_test)}")
    print(f"Accuracy: {accuracy_score(y_test, pred):.3f}")
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_test, pred):.3f}")
    print(f"Macro F1: {f1_score(y_test, pred, average='macro', zero_division=0):.3f}")
    print(
        "\nThe Streamlit app intentionally retrains this pipeline at startup "
        "instead of loading a pickle/joblib artifact, avoiding Python/"
        "scikit-learn serialization compatibility problems."
    )


if __name__ == "__main__":
    main()
