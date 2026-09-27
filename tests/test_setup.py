import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/jev/scripts"))
import jev


class SetupTests(unittest.TestCase):
    def test_native_key_examples_are_visible_and_pitfalls_are_linked(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("docs/installation.md", "skills/jev/references/setup.md"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertIn('export TYPESAFE_API_KEY=', text, name)
            self.assertIn('--provider typesafe --dry-run', text, name)
        for name in ("README.md", "README.zh.md"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertIn('<a id="pitfalls"></a>', text)
            self.assertIn('skills/jev/references/pitfalls.md', text)
        guide = (root / "skills/jev/references/pitfalls.md").read_text(encoding="utf-8")
        for term in ("repeatability", "accuracy", "relevant", "uid", "pg-jev",
                     "TYPESAFE_API_KEY", "--provider typesafe", "held-out"):
            self.assertIn(term, guide)

    def test_setup_is_a_conversation_with_the_current_coding_agent(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("README.md", "README.zh.md"):
            text = (root / name).read_text(encoding="utf-8")
            setup = text.split('<a id="no-key"></a>', 1)[1].split("### ", 2)[1]
            self.assertIn("```text", setup)
            self.assertNotIn("```bash", setup)
            for term in ("jev", "coding Agent" if name.endswith("zh.md") else "coding agent",
                         "A:", "B:"):
                # Chinese prompts use full-width punctuation.
                self.assertIn(term, setup.replace("：", ":"))
            for term in ("TYPESAFE_API_KEY", "--provider typesafe", "OPENROUTER_API_KEY",
                         "jev_called: false", "null", "docs/installation.md"):
                self.assertIn(term, setup)
        skill = (root / "skills/jev/references/setup.md").read_text(encoding="utf-8")
        self.assertIn("user's own coding agent", skill)
        self.assertIn("Wait for an explicit choice", skill)
        self.assertIn("do not\nmake the user run a terminal checklist", skill)

    def test_native_cli_full_mock_response_uses_native_key_and_model(self):
        payload = {"model": jev.DEFAULT_MODEL, "state": "fixture", "questions": {
            "q": {"type": "choice", "instructions": "Choose from evidence.",
                  "criteria": {"keep": "Evidence supports retaining it.", "review": "Evidence is missing."}}}}
        response = {"model": "jev-1.13.0", "answers": {"q": {
            "type": "choice", "choice": "keep", "probabilities": {"keep": 0.95, "review": 0.05},
            "confidence": 0.8}}, "usage": {"input_tokens": 10, "output_tokens": 0}}
        output = io.StringIO()
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "native-test-secret"}, clear=True), \
                patch("sys.stdin", io.StringIO(json.dumps(payload))), \
                patch("jev.urllib.request.build_opener") as opener, contextlib.redirect_stdout(output):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
            self.assertEqual(jev.main(["decide", "-", "--provider", "typesafe"]), 0)
            sent = opener.return_value.open.call_args.args[0]
            self.assertEqual(sent.full_url, jev.TYPESAFE_URL)
            self.assertEqual(sent.get_header("Authorization"), "Bearer native-test-secret")
            self.assertEqual(json.loads(sent.data)["model"], "jev-1.13.0")
        result = json.loads(output.getvalue())
        self.assertEqual(result["transport"], "typesafe")
        self.assertEqual(result["decisions"]["q"]["value"], "keep")
        self.assertEqual(result["response"], response)
        self.assertNotIn("native-test-secret", output.getvalue())

    def test_setup_is_read_only_and_does_not_expose_keys(self):
        for env, recommendation in [({}, None), ({"OPENROUTER_API_KEY": "or-secret"}, "openrouter"),
                                    ({"TYPESAFE_API_KEY": "ts-secret"}, "typesafe"),
                                    ({"OPENROUTER_API_KEY": "or-secret", "TYPESAFE_API_KEY": "ts-secret"}, "openrouter")]:
            output = io.StringIO()
            with patch.dict(os.environ, env, clear=True), patch("jev.urllib.request.build_opener") as network, \
                    contextlib.redirect_stdout(output):
                self.assertEqual(jev.main(["setup"]), 0)
                network.assert_not_called()
            result = json.loads(output.getvalue())
            self.assertEqual(result["recommended_provider"], recommendation)
            self.assertTrue(result["requires_user_choice"])
            self.assertFalse(result["jev_called"])
            self.assertNotIn("secret", output.getvalue())

    def test_explicit_typesafe_uses_only_typesafe_credential(self):
        payload = {"model": "jev-1.13.0", "state": "fixture", "questions": {
            "q": {"type": "noul", "instructions": "Does the evidence support the claim?"}}}
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "ts-secret", "OPENROUTER_API_KEY": "or-secret"}, clear=True), \
                patch("jev.urllib.request.build_opener") as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"answers":{}}'
            jev.request_decisions(payload, provider="typesafe")
            sent = opener.return_value.open.call_args.args[0]
            self.assertEqual(sent.full_url, "https://api.typesafe.ai/v1/systemone")
            self.assertEqual(sent.get_header("Authorization"), "Bearer ts-secret")
            self.assertEqual(json.loads(sent.data), payload)
            opener.return_value.open.assert_called_once()

    def test_no_key_or_http_error_never_falls_back(self):
        payload = {"model": "jev-1.13.0", "state": "fixture", "questions": {
            "q": {"type": "noul", "instructions": "Judge this fixture."}}}
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-secret"}, clear=True), \
                patch("jev.urllib.request.build_opener") as opener:
            with self.assertRaises(jev.JevError):
                jev.request_decisions(payload, provider="typesafe")
            opener.assert_not_called()
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "ts-secret"}, clear=True), \
                patch("jev.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = urllib.error.HTTPError(
                "https://api.typesafe.ai/v1/systemone", 403, "ts-secret", {}, io.BytesIO(b"ts-secret"))
            with self.assertRaises(jev.JevError) as error:
                jev.request_decisions(payload, provider="typesafe")
            self.assertNotIn("secret", str(error.exception))
            opener.return_value.open.assert_called_once()

    def test_explicit_typesafe_dry_run_maps_only_known_bundled_model(self):
        payload = {"model": jev.DEFAULT_MODEL, "state": "fixture", "questions": {
            "q": {"type": "noul", "instructions": "Judge this fixture."}}}
        for extra, expected in [([], "jev-1.13.0"), (["--model", "jev-latest"], "jev-latest")]:
            output = io.StringIO()
            with patch.dict(os.environ, {}, clear=True), patch("sys.stdin", io.StringIO(json.dumps(payload))), \
                    patch("jev.request_decisions") as network, contextlib.redirect_stdout(output):
                self.assertEqual(jev.main(["decide", "-", "--provider", "typesafe", "--dry-run", *extra]), 0)
                network.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())["model"], expected)


if __name__ == "__main__":
    unittest.main()
