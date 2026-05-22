import io
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-with-sufficient-length-123456"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-sufficient-length-123456"
    MONGO_URI = "mongodb://xxxxx"
    DATABASE_NAME = "InsightIQ_test"
    MONGO_DB_NAME = DATABASE_NAME
    ALLOW_DB_FALLBACK = True
    MONGO_CONNECT_RETRIES = 1
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 50
    MONGO_CONNECT_TIMEOUT_MS = 50
    MONGO_SOCKET_TIMEOUT_MS = 50
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "tmp_uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    CORS_ORIGINS = ["http://localhost:5173"]


class AdvancedAnalyticsTestCase(unittest.TestCase):
    def setUp(self):
        os.makedirs(TestConfig.UPLOAD_FOLDER, exist_ok=True)
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        register_response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Test User",
                "email": "tester@example.com",
                "password": "secret123",
                "businessName": "Insight Test Co",
            },
        )
        self.assertEqual(register_response.status_code, 201)
        self.token = register_response.get_json()["accessToken"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        for filename in os.listdir(TestConfig.UPLOAD_FOLDER):
            path = os.path.join(TestConfig.UPLOAD_FOLDER, filename)
            if os.path.isfile(path):
                os.remove(path)

    def test_upload_generates_advanced_analytics_payload(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_sales.csv"))
        with open(sample_path, "rb") as handle:
            response = self.client.post(
                "/api/upload/dataset",
                data={"file": (io.BytesIO(handle.read()), "sample_sales.csv"), "uploadType": "auto"},
                headers=self.headers,
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIn("profileReport", payload)
        self.assertIn("semanticGroups", payload)

        settings = self.client.get("/api/settings", headers=self.headers)
        self.assertEqual(settings.status_code, 200)
        self.assertIn("settings", settings.get_json())

        dashboard = self.client.get("/api/analytics/dashboard", headers=self.headers)
        self.assertEqual(dashboard.status_code, 200)
        dashboard_json = dashboard.get_json()
        self.assertIn("executiveSummary", dashboard_json)
        self.assertIn("forecast", dashboard_json)
        self.assertIn("insights", dashboard_json)
        self.assertTrue(len(dashboard_json["insights"]) > 0)
        self.assertIn("savedDashboard", dashboard_json)

        forecast = self.client.get("/api/forecast/sales", headers=self.headers)
        self.assertEqual(forecast.status_code, 200)
        forecast_json = forecast.get_json()
        self.assertIn("modelCandidates", forecast_json)
        self.assertIn("explanation", forecast_json)
        self.assertIn("confidenceSummary", forecast_json)
        self.assertTrue(isinstance(forecast_json["modelCandidates"], list))

        reports = self.client.get("/api/reports", headers=self.headers)
        self.assertEqual(reports.status_code, 200)
        self.assertTrue(len(reports.get_json()["reports"]) >= 1)

    def test_chat_answers_forecast_question(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_sales.csv"))
        with open(sample_path, "rb") as handle:
            self.client.post(
                "/api/upload/dataset",
                data={"file": (io.BytesIO(handle.read()), "sample_sales.csv"), "uploadType": "auto"},
                headers=self.headers,
                content_type="multipart/form-data",
            )

        response = self.client.post(
            "/api/analytics/chat",
            json={"question": "Predict next month sales"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("answer", payload)
        self.assertTrue(len(payload["answer"]) > 20)

        history = self.client.get("/api/analytics/chat/history", headers=self.headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.get_json()["items"]), 1)

    def test_workspace_collections_are_persisted(self):
        connector = self.client.post(
            "/api/connectors",
            json={"name": "Shopify", "type": "commerce", "config": {"shop": "demo-store"}},
            headers=self.headers,
        )
        self.assertEqual(connector.status_code, 201)

        connectors = self.client.get("/api/connectors", headers=self.headers)
        self.assertEqual(connectors.status_code, 200)
        self.assertEqual(connectors.get_json()["connectors"][0]["name"], "Shopify")

        notifications = self.client.get("/api/notifications", headers=self.headers)
        self.assertEqual(notifications.status_code, 200)
        self.assertTrue(len(notifications.get_json()["notifications"]) >= 1)


if __name__ == "__main__":
    unittest.main()
