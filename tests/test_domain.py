import unittest
import base64
import json
from types import SimpleNamespace
from unittest.mock import patch

from construction_platform import analyze_image, assistant_reply, estimate_project, format_inr, get_weather_advisory
from domain import CRACK_DEMO, SAFETY_DEMO, validate_crack_report, validate_safety_report


class ConstructionPlatformTests(unittest.TestCase):
    def test_project_estimate_scales_with_area_and_completion(self):
        half = estimate_project("Residential", 1000, "Tier 2", 50)
        full = estimate_project("Residential", 2000, "Tier 2", 100)
        self.assertEqual(half["total_budget_inr"], 2_300_000)
        self.assertEqual(half["capex_incurred_inr"], 1_150_000)
        self.assertEqual(full["total_budget_inr"], half["total_budget_inr"] * 2)

    def test_rejects_invalid_project_inputs(self):
        with self.assertRaises(ValueError):
            estimate_project("Residential", 0, "Tier 1", 10)
        with self.assertRaises(ValueError):
            estimate_project("Residential", 100, "Tier 9", 10)

    def test_currency_format_in_lakhs_and_crores(self):
        self.assertEqual(format_inr(250_000), "Rs 2.50 L")
        self.assertEqual(format_inr(25_000_000), "Rs 2.50 Cr")

    def test_weather_advisory_has_actions(self):
        advisory = get_weather_advisory("Heavy Rain")
        self.assertIn("electrical", advisory["summary"])
        self.assertGreater(len(advisory["actions"]), 0)

    def test_demo_reports_match_contracts(self):
        self.assertEqual(validate_safety_report(SAFETY_DEMO), SAFETY_DEMO)
        self.assertEqual(validate_crack_report(CRACK_DEMO), CRACK_DEMO)

    def test_safety_score_bounds_are_enforced(self):
        invalid = dict(SAFETY_DEMO, safety_score=101)
        with self.assertRaises(ValueError):
            validate_safety_report(invalid)

    @patch("groq.Groq")
    def test_image_analysis_uses_groq_json_mode(self, client_class):
        client = client_class.return_value
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(SAFETY_DEMO)))]
        )

        report = analyze_image("safety", b"test-image", "image/jpeg", "test-key", "groq-test-model")

        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "groq-test-model")
        self.assertEqual(request["response_format"], {"type": "json_object"})
        self.assertEqual(
            request["messages"][1]["content"][1]["image_url"]["url"],
            f"data:image/jpeg;base64,{base64.b64encode(b'test-image').decode('ascii')}",
        )
        self.assertEqual(report, SAFETY_DEMO)

    @patch("groq.Groq")
    def test_chat_uses_groq_chat_completion(self, client_class):
        client = client_class.return_value
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Review the lift plan limits."))]
        )

        response = assistant_reply("Can we lift today?", "High Wind", [], "test-key", "groq-test-model")

        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "groq-test-model")
        self.assertIn("High Wind", request["messages"][0]["content"])
        self.assertEqual(response, "Review the lift plan limits.")


if __name__ == "__main__":
    unittest.main()