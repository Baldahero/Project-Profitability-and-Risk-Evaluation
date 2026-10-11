from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

RANDOM_STATE = 42
TARGET = "Expert_Risk_Assessment"

NUMERIC_FEATURES = [
    "Num_Construction_Types",
    "Total_Value_GBP",
    "Fabrication_Hours",
]

CATEGORICAL_FEATURES = [
    "Technical_Complexity",
    "Profile_Type",
    "Wind_Exposure",
    "Region",
    "RC2_Status",
    "RC3_Status",
    "PAS24_Status",
]

BINARY_FEATURES = [
    "Has_Windows",
    "Has_External_Doors",
    "Has_Sliding_Doors",
    "Has_Folding_Doors",
    "Has_Curtain_Wall",
    "Has_High_Insulation",
    "Has_Access_Control",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    binary_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
    ])

    return ColumnTransformer([
        ("num", numeric_pipeline, NUMERIC_FEATURES),
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ("bin", binary_pipeline, BINARY_FEATURES),
    ])


def make_pipeline(model) -> Pipeline:
    return Pipeline([
        ("preprocess", build_preprocessor()),
        ("model", model),
    ])


MODEL_CONFIGS = {
    "RF_100_None": RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=RANDOM_STATE,
    ),
    "RF_200_None": RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=RANDOM_STATE,
    ),
    "RF_100_depth5": RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=RANDOM_STATE,
    ),
    "RF_200_depth10": RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=RANDOM_STATE,
    ),
    "DT_depth3": DecisionTreeClassifier(
        max_depth=3,
        random_state=RANDOM_STATE,
    ),
    "DT_depth5": DecisionTreeClassifier(
        max_depth=5,
        random_state=RANDOM_STATE,
    ),
    "DT_depth7": DecisionTreeClassifier(
        max_depth=7,
        random_state=RANDOM_STATE,
    ),
    "DT_None": DecisionTreeClassifier(
        max_depth=None,
        random_state=RANDOM_STATE,
    ),
    "LR_C0.1": LogisticRegression(
        C=0.1,
        max_iter=5000,
        random_state=RANDOM_STATE,
    ),
    "LR_C1": LogisticRegression(
        C=1.0,
        max_iter=5000,
        random_state=RANDOM_STATE,
    ),
    "LR_C10": LogisticRegression(
        C=10.0,
        max_iter=5000,
        random_state=RANDOM_STATE,
    ),
}

SELECTED_CONFIGS = {
    "Random Forest": "RF_100_depth5",
    "Decision Tree": "DT_depth5",
    "Logistic Regression": "LR_C10",
}
