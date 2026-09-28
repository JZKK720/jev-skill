import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".github/scripts"))
import update_contributors as contributors


def user(login, kind="User"):
    return {"login": login, "type": kind, "avatar_url": f"https://avatars.example/{login}?v=4"}


class ContributorTests(unittest.TestCase):
    def test_merged_pr_authors_join_commit_authors_and_bots_are_dropped(self):
        responses = {
            "/repos/o/r/contributors": [{**user("alice"), "contributions": 5},
                                        {**user("bob"), "contributions": 9},
                                        {**user("ci[bot]", "Bot"), "contributions": 50}],
            "/repos/o/r/pulls?state=closed": [
                {"user": user("carol"), "merged_at": "2026-09-27T00:00:00Z"},
                {"user": user("dave"), "merged_at": None},
                {"user": user("alice"), "merged_at": "2026-09-27T00:00:00Z"}],
        }
        with patch.object(contributors, "pages", lambda path, token: iter(responses[path])):
            people = contributors.collect("o/r", "token")
        self.assertEqual([login for login, _ in people], ["bob", "alice", "carol"])

    def test_render_and_update_replace_only_the_marked_block(self):
        block = contributors.render([("alice", "https://avatars.example/alice?v=4")])
        self.assertIn('src="https://avatars.example/alice?v=4&s=96"', block)
        text = f"intro\n{contributors.START}\nold\n{contributors.END}\noutro\n"
        self.assertEqual(contributors.update(text, block), f"intro\n{block}\noutro\n")
        with self.assertRaises(SystemExit):
            contributors.update("no markers", block)

    def test_both_readmes_have_exactly_one_block(self):
        for path in contributors.READMES:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count(contributors.START), 1, path.name)
            self.assertEqual(text.count(contributors.END), 1, path.name)
            self.assertNotIn("contrib.rocks", text)


if __name__ == "__main__":
    unittest.main()
