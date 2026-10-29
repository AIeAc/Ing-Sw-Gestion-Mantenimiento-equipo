import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app import create_app
from app.ml.dataset import generate_synthetic_dataset
from app.ml.decision import analyze_priority_and_cost
from app.ml.features import FEATURE_NAMES, normalize_feature_row
from app.ml.prediction import predict_equipment_risk
from app.ml.training import train_and_save_model


class FixedProbabilityModel:
    def __init__(self, probability):
        self.probability = probability

    def predict_proba(self, rows):
        return np.array(
            [[1 - self.probability, self.probability] for _row in rows]
        )


def equipment_row(measurement_count=20, estado="OPERATIVO"):
    return {
        "id_equipo": 4,
        "codigo_interno": "EQ-004",
        "nombre": "Bomba principal",
        "estado": estado,
        "measurement_count": measurement_count,
        "out_of_range_ratio": 0.25,
        "mean_deviation": 0.15,
        "maximum_deviation": 0.4,
        "trend_per_day": 0.07,
        "correctives_180d": 2,
        "days_since_maintenance": 80,
        "days_since_last_measurement": 1,
        "estimated_corrective_cost": 8000,
        "cost_source": "EQUIPO",
        "cost_observations": 2,
    }


class RiskModelTests(unittest.TestCase):
    def test_synthetic_dataset_is_reproducible_and_clean(self):
        first_x, first_y = generate_synthetic_dataset(300, 17)
        second_x, second_y = generate_synthetic_dataset(300, 17)

        np.testing.assert_array_equal(first_x, second_x)
        np.testing.assert_array_equal(first_y, second_y)
        self.assertEqual(first_x.shape, (300, len(FEATURE_NAMES)))
        self.assertEqual(set(first_y), {0, 1})
        self.assertTrue(np.isfinite(first_x).all())

    def test_training_compares_models_and_persists_an_accepted_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "model.joblib"
            artifact = train_and_save_model(destination, 600, 42)

            self.assertTrue(destination.is_file())
            self.assertTrue(artifact["accepted"])
            self.assertIn(artifact["selected_model"], artifact["evaluations"])
            self.assertEqual(
                set(artifact["evaluations"]),
                {"Regresión logística", "Random Forest"},
            )
            self.assertEqual(artifact["dataset"]["training_samples"], 480)
            self.assertEqual(artifact["dataset"]["test_samples"], 120)
            self.assertEqual(artifact["dataset"]["historical_samples"], 0)
            self.assertEqual(artifact["dataset"]["synthetic_samples"], 600)

    def test_training_can_mix_historical_and_synthetic_cases(self):
        rows = [
            {**equipment_row(measurement_count=35), "target": index % 2}
            for index in range(20)
        ]
        with tempfile.TemporaryDirectory() as directory:
            artifact = train_and_save_model(
                Path(directory) / "model.joblib",
                300,
                17,
                historical_rows=rows,
            )

        self.assertEqual(artifact["dataset"]["samples"], 320)
        self.assertEqual(artifact["dataset"]["historical_samples"], 20)
        self.assertIn("Historial PostgreSQL", artifact["dataset"]["source"])

    def test_risk_levels_and_insufficient_data_are_explicit(self):
        artifact = {
            "model": FixedProbabilityModel(0.78),
            "risk_thresholds": {"medium": 0.40, "high": 0.70},
        }
        enough = normalize_feature_row(equipment_row())
        insufficient = normalize_feature_row(equipment_row(measurement_count=2))

        high = predict_equipment_risk(enough, artifact)
        missing = predict_equipment_risk(insufficient, artifact)

        self.assertEqual(high["level"], "ALTO")
        self.assertEqual(high["probability"], 0.78)
        self.assertEqual(missing["level"], "SIN_DATOS")
        self.assertIsNone(missing["probability"])

    def test_priority_combines_probability_and_financial_impact(self):
        costly = analyze_priority_and_cost(0.45, 12000, 12000)
        inexpensive = analyze_priority_and_cost(0.45, 3000, 12000)

        self.assertEqual(costly["priority"], "ALTA")
        self.assertGreater(costly["priority_score"], inexpensive["priority_score"])
        self.assertEqual(costly["financial_exposure"], 5400)


class RiskPageTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "postgresql://unused",
            }
        )
        self.client = self.app.test_client()
        self.admin = {
            "id_usuario": 1,
            "nombre": "Ana",
            "apellidos": "Torres",
            "correo": "ana@example.com",
            "rol": "Administrador",
        }
        with self.client.session_transaction() as session:
            session["user_id"] = 1

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.risks.load_model_artifact")
    @patch("app.blueprints.risks.risks.list_equipment_feature_rows")
    def test_page_shows_model_metrics_and_equipment_risk(
        self, list_rows, load_artifact, find_user
    ):
        find_user.return_value = self.admin
        list_rows.return_value = [equipment_row()]
        load_artifact.return_value = {
            "model": FixedProbabilityModel(0.78),
            "risk_thresholds": {"medium": 0.40, "high": 0.70},
            "selected_model": "Random Forest",
            "trained_at": "2026-10-29T12:00:00+00:00",
            "target": "Correctivo en 30 días",
            "horizon_days": 30,
            "dataset": {
                "samples": 600,
                "training_samples": 480,
                "test_samples": 120,
            },
            "evaluations": {
                "Random Forest": {
                    "accuracy": 0.84,
                    "precision": 0.81,
                    "recall": 0.82,
                    "f1": 0.815,
                    "confusion_matrix": [[50, 10], [11, 49]],
                },
                "Regresión logística": {
                    "accuracy": 0.80,
                    "precision": 0.77,
                    "recall": 0.79,
                    "f1": 0.78,
                    "confusion_matrix": [[48, 12], [13, 47]],
                },
            },
        }

        response = self.client.get("/riesgos")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Riesgo alto".encode(), response.data)
        self.assertIn(b"78%", response.data)
        self.assertIn(b"Random Forest", response.data)
        self.assertIn("Comparación de algoritmos".encode(), response.data)
        self.assertIn("Atención inmediata".encode(), response.data)
        self.assertIn(b"$8,000", response.data)
        self.assertIn("Exposición".encode(), response.data)

    @patch("app.blueprints.auth.users.find_active_user_by_id")
    @patch("app.blueprints.risks.load_model_artifact")
    @patch("app.blueprints.risks.risks.list_equipment_feature_rows", return_value=[])
    def test_page_explains_how_to_train_when_model_is_missing(
        self, _list_rows, load_artifact, find_user
    ):
        from app.ml.prediction import ModelUnavailableError

        find_user.return_value = self.admin
        load_artifact.side_effect = ModelUnavailableError("Modelo no disponible.")

        response = self.client.get("/riesgos")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"entrenar-modelo-riesgo", response.data)
        self.assertIn(b"Modelo no disponible", response.data)


if __name__ == "__main__":
    unittest.main()
