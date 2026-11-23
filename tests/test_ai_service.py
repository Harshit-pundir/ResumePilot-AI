import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services import ai_service


class AIServiceCharacterizationTests(unittest.TestCase):
    def test_sends_resume_prompt_with_existing_groq_options(self):
        resume_text = "Python developer with API experience."
        expected_text = "Faithful improvement suggestions."
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=expected_text))]
        )
        completion_api = SimpleNamespace(create=None)
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completion_api))

        with patch.object(completion_api, "create", return_value=response) as create, \
             patch.object(ai_service, "client", fake_client):
            result = ai_service.generate_ai_resume_feedback(resume_text)

        self.assertEqual(result, expected_text)
        request = create.call_args.kwargs
        self.assertEqual(request["model"], "openai/gpt-oss-120b")
        self.assertEqual(request["temperature"], 0.4)
        self.assertEqual(request["max_tokens"], 4000)
        self.assertEqual(request["timeout"], 45.0)
        self.assertEqual(request["messages"][0]["role"], "user")
        prompt = request["messages"][0]["content"]
        self.assertIn(resume_text, prompt)
        self.assertIn("Never hallucinate", prompt)
        self.assertIn("## ATS Tips", prompt)

    def test_missing_groq_configuration_disables_only_optional_ai(self):
        with patch.object(ai_service, "client", None):
            self.assertIsNone(ai_service.generate_ai_resume_feedback("Local resume text"))


if __name__ == "__main__":
    unittest.main()
