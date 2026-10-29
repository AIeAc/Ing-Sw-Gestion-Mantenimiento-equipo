from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .dataset import generate_synthetic_dataset
from .features import (
    FEATURE_LABELS,
    FEATURE_NAMES,
    MODEL_VERSION,
    PREDICTION_HORIZON_DAYS,
    RISK_THRESHOLDS,
    TARGET_DESCRIPTION,
    normalize_feature_row,
)


ACCEPTANCE_CRITERIA = {"minimum_f1": 0.70, "minimum_recall": 0.70}


def train_and_save_model(
    model_path: str | Path,
    sample_count: int = 1600,
    random_state: int = 42,
    historical_rows: list[dict] | None = None,
):
    synthetic_features, synthetic_target = generate_synthetic_dataset(
        sample_count, random_state
    )
    historical_features, historical_target = _historical_dataset(historical_rows or [])
    if len(historical_target):
        features = np.vstack((synthetic_features, historical_features))
        target = np.concatenate((synthetic_target, historical_target))
    else:
        features, target = synthetic_features, synthetic_target
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.20,
        random_state=random_state,
        stratify=target,
    )

    candidates = {
        "Regresión logística": Pipeline(
            (
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            )
        ),
        "Random Forest": Pipeline(
            (
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=260,
                        max_depth=9,
                        min_samples_leaf=4,
                        class_weight="balanced",
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            )
        ),
    }

    evaluations = {}
    for name, candidate in candidates.items():
        candidate.fit(x_train, y_train)
        predicted = candidate.predict(x_test)
        matrix = confusion_matrix(y_test, predicted, labels=[0, 1])
        evaluations[name] = {
            "model": candidate,
            "accuracy": accuracy_score(y_test, predicted),
            "precision": precision_score(y_test, predicted, zero_division=0),
            "recall": recall_score(y_test, predicted, zero_division=0),
            "f1": f1_score(y_test, predicted, zero_division=0),
            "confusion_matrix": matrix.tolist(),
        }

    selected_name, selected = max(
        evaluations.items(),
        key=lambda item: (
            item[1]["f1"],
            item[1]["recall"],
            item[1]["precision"],
        ),
    )
    accepted = (
        selected["f1"] >= ACCEPTANCE_CRITERIA["minimum_f1"]
        and selected["recall"] >= ACCEPTANCE_CRITERIA["minimum_recall"]
    )

    serialized_metrics = {
        name: {
            key: round(float(value), 4) if key != "confusion_matrix" else value
            for key, value in result.items()
            if key != "model"
        }
        for name, result in evaluations.items()
    }
    artifact = {
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "selected_model": selected_name,
        "model": selected["model"],
        "feature_names": list(FEATURE_NAMES),
        "feature_labels": FEATURE_LABELS,
        "target": TARGET_DESCRIPTION,
        "horizon_days": PREDICTION_HORIZON_DAYS,
        "risk_thresholds": RISK_THRESHOLDS,
        "dataset": {
            "source": (
                "Historial PostgreSQL y escenarios operativos simulados"
                if len(historical_target)
                else "Escenarios operativos académicos simulados"
            ),
            "samples": int(len(target)),
            "historical_samples": int(len(historical_target)),
            "synthetic_samples": int(len(synthetic_target)),
            "training_samples": int(len(x_train)),
            "test_samples": int(len(x_test)),
            "positive_rate": round(float(target.mean()), 4),
            "random_state": int(random_state),
        },
        "evaluations": serialized_metrics,
        "acceptance_criteria": ACCEPTANCE_CRITERIA,
        "accepted": accepted,
    }

    if accepted:
        destination = Path(model_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        joblib.dump(artifact, temporary, compress=3)
        os.replace(temporary, destination)
    return artifact


def _historical_dataset(rows: list[dict]):
    """Valida y transforma los cortes históricos al mismo vector de inferencia."""
    vectors = []
    targets = []
    for row in rows:
        target = int(row.get("target", 0))
        if target not in (0, 1):
            continue
        features = normalize_feature_row(row)
        vectors.append(features.vector())
        targets.append(target)
    if not vectors:
        return np.empty((0, len(FEATURE_NAMES)), dtype=float), np.empty(0, dtype=int)
    return np.asarray(vectors, dtype=float), np.asarray(targets, dtype=int)
