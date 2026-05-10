import unittest
from prism.metrics.clarification import ClarificationDetector
from prism.extractor.uiv_builder import UIVBuilder

class TestPrismCore(unittest.TestCase):
    
    def setUp(self):
        self.detector = ClarificationDetector()
        self.builder = UIVBuilder()

    def test_clarification_detection(self):
        self.assertTrue(self.detector.is_clarification("make it simpler please"))
        self.assertTrue(self.detector.is_clarification("too long, give me bullets"))
        self.assertFalse(self.detector.is_clarification("what is the capital of France?"))

    def test_uiv_extraction(self):
        history = [
            {"role": "user", "content": "Tell me about cars"},
            {"role": "assistant", "content": "Cars are motor vehicles..."},
            {"role": "user", "content": "be more concise and use bullet points"}
        ]
        uiv = self.builder.extract(history)
        self.assertEqual(uiv["style"], "concise")
        self.assertEqual(uiv["format"], "bullets")

if __name__ == "__main__":
    unittest.main()
