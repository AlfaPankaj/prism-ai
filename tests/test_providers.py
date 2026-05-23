import unittest

from prism.providers import build_anthropic_payload, build_gemini_payload, build_openai_payload


class TestProviderPayloads(unittest.TestCase):
    def setUp(self):
        self.messages = [
            {"role": "system", "content": "System rules"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

    def test_openai_payload_keeps_system(self):
        payload = build_openai_payload(self.messages, model="gpt-4o-mini", temperature=0.2, max_tokens=120)
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(len(payload["messages"]), 3)
        self.assertEqual(payload["messages"][0]["role"], "system")

    def test_anthropic_payload_moves_system(self):
        payload = build_anthropic_payload(self.messages, model="claude-3-5-sonnet-latest", temperature=0.1, max_tokens=200)
        self.assertEqual(payload["system"], "System rules")
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "user")

    def test_gemini_payload_system_instruction(self):
        payload = build_gemini_payload(self.messages, model="gemini-1.5-flash", temperature=0.3, max_tokens=80)
        self.assertIn("systemInstruction", payload)
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "System rules")
        self.assertEqual(payload["contents"][0]["role"], "user")
        self.assertEqual(payload["contents"][1]["role"], "model")


if __name__ == "__main__":
    unittest.main()
