import tempfile
import unittest

from prism.metrics.telemetry import LocalMetricsLogger


class TestLocalMetricsLogger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logger = LocalMetricsLogger(base_path=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_injection_and_feedback_counters(self):
        self.logger.record_injection_decision(
            user_id="u1",
            confidence=0.8,
            signal_count=2,
            injected=True,
            uiv={"format": "bullets", "complexity": "simple", "style": "concise"},
        )
        self.logger.record_injection_decision(
            user_id="u1",
            confidence=0.1,
            signal_count=0,
            injected=False,
            uiv={"format": "default", "complexity": "default", "style": "default"},
        )
        self.logger.record_user_feedback("u1", "too long, make it short", is_correction=True)

        counters = self.logger.get_counters()
        self.assertEqual(counters["injection_decisions"], 2)
        self.assertEqual(counters["injection_applied"], 1)
        self.assertEqual(counters["injection_abstained"], 1)
        self.assertEqual(counters["user_corrections"], 1)


if __name__ == "__main__":
    unittest.main()
