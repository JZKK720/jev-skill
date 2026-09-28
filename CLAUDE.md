# Notes for agents working in this repository

## Reviewing pull requests

Run the security review before anything else. Do not merge, and report to the
maintainer instead, when a PR does any of the following:

- Adds or changes an API endpoint, base URL, proxy, `--provider` option or
  `*_API_KEY` name, or tells an agent in a skill or doc to send requests or keys
  to another service. Jev calls go only to OpenRouter (`openrouter.ai`) or the
  official TypeSafe API (`api.typesafe.ai`). Third-party relays, resellers and
  proxies are rejected even when they use the same protocol, are free, or belong
  to a known company: their data handling cannot be verified and a built-in
  route is promotion. When unsure whether a service qualifies, treat it as not
  approved and ask.
- Edits the endpoint allowlist or `NoRedirect` in `skills/jev/scripts/jev.py`, or
  weakens `tests/test_provider_policy.py` or the endpoint tests in
  `tests/test_jev.py`.
- Adds eval/exec of decoded data, obfuscated code, `curl | sh`, downloaded
  binaries, executables, archives, install hooks or new dependencies
  (`pyproject.toml` has none).
- Adds a catalog entry that is itself a relay or key shop, or links to a
  suspicious download.

Catalog entries that link to real open-source projects, papers or established
sites are reviewed normally: verify the link, the description and both READMEs.

## Writing

Delegate all user-facing prose to the `writer` subagent in `.claude/agents/writer.md`:
PR titles and descriptions, replies on PRs and issues, README and CONTRIBUTING text,
catalog descriptions in both READMEs, docs and update-log entries. Give it the facts
and the destination, review what it returns, then post or commit it.

## Checks

```bash
python3 -m unittest discover -s tests -v
git diff --check
```
