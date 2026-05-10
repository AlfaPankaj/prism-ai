import tempfile
import unittest
import json
import os

from prism.storage import JSONProfileStore


class TestJSONProfileStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = JSONProfileStore(base_path=self.tmp.name)
        self.user_id = "test_user"

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_and_read_profile(self):
        uiv = {"format": "bullets", "complexity": "simple", "style": "concise"}
        self.store.save_profile(
            self.user_id,
            uiv=uiv,
            confidence=0.72,
            axis_confidence={"format": 0.8, "complexity": 0.7, "style": 0.66},
            source="inferred",
        )

        profile = self.store.get_profile(self.user_id)
        self.assertEqual(profile["uiv"]["format"], "bullets")
        self.assertEqual(profile["metadata"]["source"], "inferred")

    def test_manual_edit_and_reset(self):
        self.store.save_uiv(self.user_id, {"format": "default", "complexity": "default", "style": "default"})
        self.store.edit_uiv(self.user_id, {"style": "concise"})
        profile = self.store.get_profile(self.user_id)
        self.assertEqual(profile["uiv"]["style"], "concise")
        self.assertEqual(profile["metadata"]["source"], "manual")

        self.store.reset_profile(self.user_id)
        self.assertIsNone(self.store.get_profile(self.user_id))

    def test_temporary_override(self):
        base = {"format": "paragraph", "complexity": "detailed", "style": "detailed"}
        override = {"format": "bullets", "complexity": "simple", "style": "concise"}
        self.store.save_uiv(self.user_id, base)
        self.store.set_temporary_override(self.user_id, override, ttl_seconds=120)

        effective = self.store.get_uiv(self.user_id, use_override=True)
        self.assertEqual(effective, override)

        self.store.clear_temporary_override(self.user_id)
        no_override = self.store.get_uiv(self.user_id, use_override=True)
        self.assertEqual(no_override, base)

    def test_export_and_retention_policy(self):
        self.store.save_profile(
            self.user_id,
            uiv={"format": "bullets", "complexity": "simple", "style": "concise"},
            confidence=0.9,
            source="manual",
        )
        exported = self.store.export_profile(self.user_id)
        self.assertEqual(exported["metadata"]["source"], "manual")

        # Force an old timestamp and verify retention deletes it.
        profile_path = os.path.join(self.tmp.name, f"{self.user_id}.json")
        with open(profile_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        payload["metadata"]["updated_at"] = "2000-01-01T00:00:00+00:00"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        deleted = self.store.apply_retention_policy(max_age_days=30)
        self.assertEqual(deleted, 1)
        self.assertIsNone(self.store.get_profile(self.user_id))


if __name__ == "__main__":
    unittest.main()
