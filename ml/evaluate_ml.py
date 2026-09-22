from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from model_config import (
    FEATURES,
    MODEL_CONFIGS,
    RANDOM_STATE,
    SELECTED_CONFIGS,
    TARGET,
    make_pipeline,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "Combined_Projects_Dataset_100_enriched_v2.xlsx"


def evaluate_predictions(y_true, y_pred) -> dict[str, float]:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Balanced Accuracy": balanced_accuracy_score(y_true, y_pred),
        "Macro F1": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce the thesis ML comparison without Google Colab."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    df = pd.read_excel(args.dataset)

    required = [*FEATURES, TARGET, "Rule_Based_Risk"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("Dataset is missing required columns: " + ", ".join(missing))

    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"Dataset shape: {df.shape}")
    print(f"Selected ML features: {len(FEATURES)}")
    print(f"Training records: {len(X_train)}")
    print(f"Held-out test records: {len(X_test)}")
    print("\nTarget distribution:")
    print(y.value_counts())

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    cv_rows = []
    for config_name, estimator in MODEL_CONFIGS.items():
        pipeline = make_pipeline(estimator)
        scores = cross_val_score(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring="balanced_accuracy",
        )
        cv_rows.append({
            "Configuration": config_name,
            "CV Balanced Mean": scores.mean(),
            "CV Balanced Std": scores.std(),
        })

    cv_df = pd.DataFrame(cv_rows).sort_values(
        "CV Balanced Mean",
        ascending=False,
    )

    print("\n=== 11-CONFIGURATION CROSS-VALIDATION ===")
    print(cv_df.to_string(index=False))

    final_rows = []

    rule_test_pred = df.loc[y_test.index, "Rule_Based_Risk"]
    rule_metrics = evaluate_predictions(y_test, rule_test_pred)
    final_rows.append({
        "Method": "Rule-based",
        **rule_metrics,
        "CV Balanced Accuracy": None,
        "CV Std": None,
    })

    predictions = {"Rule-based": rule_test_pred}

    for display_name, config_name in SELECTED_CONFIGS.items():
        estimator = MODEL_CONFIGS[config_name]
        pipeline = make_pipeline(estimator)
        pipeline.fit(X_train, y_train)
        pred = pipeline.predict(X_test)
        predictions[display_name] = pred

        metrics = evaluate_predictions(y_test, pred)
        cv_row = cv_df.loc[cv_df["Configuration"] == config_name].iloc[0]

        final_rows.append({
            "Method": display_name,
            **metrics,
            "CV Balanced Accuracy": cv_row["CV Balanced Mean"],
            "CV Std": cv_row["CV Balanced Std"],
        })

    final_df = pd.DataFrame(final_rows)

    print("\n=== HELD-OUT TEST RESULTS ===")
    print(final_df.to_string(index=False))

    labels = ["Low", "Medium", "High"]
    recall_rows = []
    for name, pred in predictions.items():
        recalls = recall_score(
            y_test,
            pred,
            labels=labels,
            average=None,
            zero_division=0,
        )
        recall_rows.append({
            "Method": name,
            "Low Recall": recalls[0],
            "Medium Recall": recalls[1],
            "High Recall": recalls[2],
        })

    recall_df = pd.DataFrame(recall_rows)

    print("\n=== CLASS-LEVEL RECALL ===")
    print(recall_df.to_string(index=False))

    rule_all = evaluate_predictions(y, df["Rule_Based_Risk"])
    print("\n=== RULE-BASED DESCRIPTIVE FULL-DATASET RESULT ===")
    for key, value in rule_all.items():
        print(f"{key}: {value:.3f}")

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        cv_df.to_csv(args.output_dir / "cv_configuration_results.csv", index=False)
        final_df.to_csv(args.output_dir / "heldout_results.csv", index=False)
        recall_df.to_csv(args.output_dir / "class_recall_results.csv", index=False)

        error_df = pd.DataFrame({"Actual": y_test})
        for name, pred in predictions.items():
            error_df[name] = pred
        error_df.to_csv(args.output_dir / "heldout_predictions.csv")

        print(f"\nSaved reproducible result tables to: {args.output_dir}")


if __name__ == "__main__":
    main()
