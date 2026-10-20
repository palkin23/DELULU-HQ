"""Route-level tests using an isolated temporary SQLite database."""
import os
import tempfile
import unittest

import app as site


class DeluluAppTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        site.app.config.update(TESTING=True, DATABASE=self.db_path)
        site.init_db()
        self.client = site.app.test_client()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_dashboard_renders_seeded_habits(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"main character era", response.data)
        self.assertIn(b"Drink water", response.data)

    def test_detector_validation_and_analysis(self):
        self.assertEqual(self.client.post("/api/detective", data={"situation":"hmm"}).status_code, 400)
        response = self.client.post("/api/detective", data={"situation":"They watched every story but did not reply."})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["explanations"]), 3)

    def test_movie_and_mood_persist(self):
        self.assertEqual(self.client.post("/api/movie", data={"mood":"Dreamy"}).json["title"], "The Moon Sent Me a Playlist")
        self.assertEqual(self.client.post("/api/checkin", data={"mood":"Soft"}).status_code, 200)
        self.assertIn(b"Today\xe2\x80\x99s mood is Soft", self.client.get("/").data)

    def test_habit_toggle_and_duplicate_validation(self):
        with site.app.app_context():
            habit_id = site.db().execute("SELECT id FROM habits WHERE name='Drink water'").fetchone()[0]
        response = self.client.post(f"/api/habits/{habit_id}/toggle")
        self.assertTrue(response.json["done"])
        self.assertEqual(self.client.post("/api/habits", data={"name":"Drink water"}).status_code, 400)

    def test_diary_create_edit_delete(self):
        data = {"title":"A soft reset", "body":"I am starting again, gently.", "mood":"Soft"}
        created = self.client.post("/api/diary", data=data)
        self.assertEqual(created.status_code, 200)
        entry_id = created.json["id"]
        self.assertEqual(self.client.get(f"/api/diary/{entry_id}").json["body"], data["body"])
        data["title"] = "A softer reset"
        self.assertEqual(self.client.put(f"/api/diary/{entry_id}", data=data).status_code, 200)
        self.assertEqual(self.client.get(f"/api/diary/{entry_id}").json["title"], data["title"])
        self.assertEqual(self.client.delete(f"/api/diary/{entry_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/diary/{entry_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()