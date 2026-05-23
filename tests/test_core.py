import unittest

from prism.metrics.clarification import ClarificationDetector
from prism.extractor.uiv_builder import UIVBuilder
from prism.adapter.prompt_injector import PrismAdapter


class TestPrismCore(unittest.TestCase):

    def setUp(self):
        self.detector = ClarificationDetector()
        self.builder = UIVBuilder()
        self.adapter = PrismAdapter()

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

    def test_temporal_decay_uses_previous_profile(self):
        history = [
            {"role": "user", "content": "Tell me about space."},
            {"role": "assistant", "content": "Space is vast..."},
            {"role": "user", "content": "too long, be concise"},
        ]
        previous = {"format": "default", "complexity": "simple", "style": "default"}

        profile = self.builder.extract_profile(history, previous_uiv=previous, decay=0.7)

        self.assertEqual(profile["uiv"]["style"], "concise")
        self.assertEqual(profile["uiv"]["complexity"], "simple")

    def test_adapter_abstains_when_no_signal(self):
        history = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
        ]
        wrapped = self.adapter.wrap_prompt("Explain decorators", history=history)
        self.assertEqual(wrapped, "Explain decorators")


if __name__ == "__main__":
    unittest.main()
