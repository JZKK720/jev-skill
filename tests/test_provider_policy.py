"""Provider policy: Jev calls go only to OpenRouter or official TypeSafe.

Third-party API relays and resellers are not accepted, even when they speak the
same protocol: user evidence and API keys would leave for a service nobody can
verify, and a built-in route doubles as promotion for that service. Changing
anything below needs an explicit maintainer decision, not a routine PR.
"""

import ast
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/jev/scripts"))
import jev

APPROVED_API_HOSTS = {"openrouter.ai", "api.typesafe.ai"}
APPROVED_PROVIDERS = ["openrouter", "typesafe"]
APPROVED_KEY_NAMES = {"OPENROUTER_API_KEY", "TYPESAFE_API_KEY"}
# Hosts code may reference besides the APIs: key/doc pages and public sources.
APPROVED_CODE_HOSTS = APPROVED_API_HOSTS | {
    "console.typesafe.ai", "docs.typesafe.ai", "github.com",
    "raw.githubusercontent.com", "huggingface.co",
}
CODE_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".sh", ".toml"}
URL = re.compile(r"https?://[A-Za-z0-9.-]+[^\s\"'`)<>\]]*")
KEY_NAME = re.compile(r"\b[A-Z][A-Z0-9_]*_API_KEY\b")
API_LIKE = re.compile(r"https?://([A-Za-z0-9.-]+)/(?:api|v\d)(?:/|\b)")


def host(url):
    return urlsplit(url).hostname


def code_files():
    for folder in ("skills", "evals"):
        for path in (ROOT / folder).rglob("*"):
            if path.suffix in CODE_SUFFIXES and "egg-info" not in path.parts:
                yield path
    yield ROOT / "pyproject.toml"


def agent_facing_docs():
    yield from (ROOT / "skills").rglob("*.md")
    yield from (ROOT / "docs").glob("*.md")
    yield ROOT / "README.md"
    yield ROOT / "README.zh.md"
    yield ROOT / "CONTRIBUTING.md"


def read(path):
    return path.read_text(encoding="utf-8")


class ProviderPolicyTests(unittest.TestCase):
    def test_cli_offers_only_approved_providers(self):
        subcommands = next(action for action in jev.parser()._actions
                           if hasattr(action, "choices") and isinstance(action.choices, dict))
        for name in ("decide", "classify"):
            provider = subcommands.choices[name]._option_string_actions["--provider"]
            self.assertEqual(list(provider.choices), APPROVED_PROVIDERS, name)
        with self.assertRaises(jev.JevError):
            jev.request_decisions({}, provider="relay")

    def test_http_allowlist_contains_only_approved_hosts(self):
        tree = ast.parse(read(ROOT / "skills/jev/scripts/jev.py"))
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and node.name == "http_json")
        endpoints = next(node.value for node in ast.walk(function)
                         if isinstance(node, ast.Assign)
                         and any(getattr(target, "id", None) == "endpoints" for target in node.targets))
        self.assertIsInstance(endpoints, ast.Dict)
        urls = [key.value if isinstance(key, ast.Constant) else getattr(jev, key.id)
                for key in endpoints.keys]
        self.assertTrue(urls)
        for url in urls:
            self.assertIn(host(url), APPROVED_API_HOSTS, url)
        for name in dir(jev):
            value = getattr(jev, name)
            if name.endswith("_URL") and isinstance(value, str):
                self.assertIn(host(value), APPROVED_API_HOSTS, name)

    def test_code_references_only_approved_hosts(self):
        for path in code_files():
            for url in URL.findall(read(path)):
                with self.subTest(file=str(path.relative_to(ROOT)), url=url):
                    self.assertIn(host(url), APPROVED_CODE_HOSTS)

    def test_only_approved_provider_key_names(self):
        for path in [*code_files(), *agent_facing_docs()]:
            for name in set(KEY_NAME.findall(read(path))):
                with self.subTest(file=str(path.relative_to(ROOT)), key=name):
                    self.assertIn(name, APPROVED_KEY_NAMES)

    def test_docs_point_agents_only_at_approved_apis(self):
        allowed = APPROVED_API_HOSTS | {"docs.typesafe.ai"}
        for path in agent_facing_docs():
            text = read(path)
            for api_host in API_LIKE.findall(text):
                with self.subTest(file=str(path.relative_to(ROOT)), host=api_host):
                    self.assertIn(api_host, allowed)
            for provider in set(re.findall(r"--provider[ =]([a-z]+)", text)):
                with self.subTest(file=str(path.relative_to(ROOT)), provider=provider):
                    self.assertIn(provider, APPROVED_PROVIDERS)


if __name__ == "__main__":
    unittest.main()
