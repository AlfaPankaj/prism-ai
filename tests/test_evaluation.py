import unittest

from prism.metrics.evaluation import EvaluationTracker, normalize_record


class TestEvaluationTracker(unittest.TestCase):
    def test_normalize_record(self):
        rec = normalize_record(
            {
                "speaker": "prompter",
                "content": "make it simpler",
                "author_id": "u1",
                "conversation_id": "c1",
            }
        )
        self.assertEqual(rec["role"], "user")
        self.assertEqual(rec["user_id"], "u1")
        self.assertEqual(rec["session_id"], "c1")

    def test_tracker_metrics(self):
        tracker = EvaluationTracker()
        examples = [
            {"user_id": "u1", "session_id": "s1", "role": "user", "text": "Explain quantum computing"},
            {"user_id": "u1", "session_id": "s1", "role": "assistant", "text": "A long answer"},
            {"user_id": "u1", "session_id": "s1", "role": "user", "text": "too long, make it concise"},
            {"user_id": "u2", "session_id": "s2", "role": "user", "text": "What is Python"},
            {"user_id": "u2", "session_id": "s2", "role": "assistant", "text": "Python is a language"},
        ]
        for ex in examples:
            tracker.process(ex)

        metrics = tracker.finalize()
        self.assertGreaterEqual(metrics["clarification_rate"], 0.0)
        self.assertLessEqual(metrics["clarification_rate"], 1.0)
        self.assertGreaterEqual(metrics["first_response_acceptance_rate"], 0.0)
        self.assertLessEqual(metrics["first_response_acceptance_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
