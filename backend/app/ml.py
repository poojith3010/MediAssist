from pathlib import Path
from typing import Any

import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


MODEL_PATH = Path("data/models/risk_model.joblib")


def train_model() -> dict[str, Any]:
    dataset = load_breast_cancer(as_frame=True)
    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data, dataset.target, test_size=0.2, random_state=42, stratify=dataset.target
    )
    model = make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=100, random_state=42))
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": list(dataset.feature_names)}, MODEL_PATH)
    return {
        "features": [str(feature) for feature in dataset.feature_names],
        "test_samples": len(x_test),
        "metrics": {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions)),
            "recall": float(recall_score(y_test, predictions)),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        },
    }


def predict(values: dict[str, float]) -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Risk model has not been trained. Run python -m app.train_model.")
    bundle = joblib.load(MODEL_PATH)
    missing = [feature for feature in bundle["features"] if feature not in values]
    if missing:
        raise ValueError(f"Missing features: {', '.join(missing)}")
    row = [[values[feature] for feature in bundle["features"]]]
    model = bundle["model"]
    return {"class": int(model.predict(row)[0]), "informational_only": True}


def explain(values: dict[str, float]) -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Risk model has not been trained. Run python -m app.train_model.")
    bundle = joblib.load(MODEL_PATH)
    missing = [feature for feature in bundle["features"] if feature not in values]
    if missing:
        raise ValueError(f"Missing features: {', '.join(missing)}")
    try:
        import shap
    except ImportError as exc:
        raise RuntimeError("Install the optional explainability dependencies with pip install -e .[explainability]") from exc
    row = [[values[feature] for feature in bundle["features"]]]
    estimator = bundle["model"][-1]
    transformed = bundle["model"][:-1].transform(row)
    explanation = shap.TreeExplainer(estimator)(transformed)
    values_out = explanation.values[0]
    if values_out.ndim > 1:
        values_out = values_out[:, 1]
    return {
        "informational_only": True,
        "features": [
            {"feature": feature, "contribution": float(contribution)}
            for feature, contribution in sorted(zip(bundle["features"], values_out), key=lambda item: abs(item[1]), reverse=True)[:10]
        ],
        "limitation": "Feature attribution indicates model behavior, not causality or clinical importance.",
    }
