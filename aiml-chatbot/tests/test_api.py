import unittest

import app as nexus_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        nexus_app.app.config["TESTING"] = True
        self.client = nexus_app.app.test_client()

    def test_chat_rejects_invalid_json(self):
        resp = self.client.post(
            "/api/chat",
            data="{invalid-json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("status"), "error")

    def test_chat_returns_expected_shape(self):
        resp = self.client.post("/api/chat", json={"message": "hello"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIsInstance(body, dict)
        self.assertIn("response", body)
        self.assertIn("status", body)
        self.assertIn("game_active", body)

    def test_game_state_isolated_between_sessions(self):
        client_one = nexus_app.app.test_client()
        client_two = nexus_app.app.test_client()

        start = client_one.post("/api/chat", json={"message": "hangman"})
        self.assertEqual(start.status_code, 200)
        self.assertTrue(start.get_json().get("game_active"))

        # Session two should not be inside session one's game.
        second = client_two.post("/api/chat", json={"message": "A"})
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.get_json().get("game_active"))

    def test_stats_endpoint_works(self):
        resp = self.client.get("/api/stats")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIsInstance(body, dict)
        self.assertIn("patterns", body)
        self.assertIn("version", body)


if __name__ == "__main__":
    unittest.main()
