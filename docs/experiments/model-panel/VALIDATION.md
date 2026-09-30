# Verification — 2026-09-22

- **157 offline tests passed**; full suite needs a localhost listening socket for the existing HTTP transport test. The first sandbox run could not bind that socket; rerun with local-server permission passed. No live model calls occur in the test suite.
- `compileall` passed for evaluation and CLI code. No separate project type-checker is configured.
- All ten derived Markdown result tables regenerate byte-for-byte. JSON metric comparisons allow an absolute tolerance of 1e-12 for floats across Python versions (Python 3.12 changed float summation); counts, labels, structure, and receipt hashes remain exact. All report-relative file links resolve. Seven external dataset adapters and the PR adapter reconstructed the exact frozen sample hashes from retained local source caches.
- Agent observations, actions, persisted final states, success flags, unsafe-attempt counts and usage totals replay from the eight actual episode logs.
- Clean wheel installation and `jev-decide ... --dry-run` passed. Candidate sdist contains exactly five SKILL entries, public derived records and manifest seals; no `.scratch` or `.env`. BBH rescores from the extracted archive offline. Candidate artifacts are local, not a published release.
- Both README result sections were opened as locally rendered Pandoc HTML and visually inspected in the in-app browser. Tables and links render; this is not a GitHub mobile/theme certification.
- Public artifact scan found no OpenRouter-key patterns. Raw source-bearing external data and responses remain in the maintainer's local evidence archive.

## Standards review

Fixed baseline `4d6efbc` (`main`), implementation reviewed through `825cb94`.
Independent reviewer: **0 remaining actionable findings**. Earlier issues fixed with regression tests: response/error contradictions, dropped safe transport diagnostics and silently overridden model options. The final archive/condition-table delta was rechecked.

## Spec review

Independent reviewer: **0 remaining findings in scope** after adding the generated short/full context table with correctness, valid-response coverage, unknown coverage and errors. Ruozhiba options were separately reviewed before model calls; not human review or independent benchmark gold.

## Delivery boundaries

1,900 panel requests + 79 Agent requests + 10 preflight requests. Five HTTP429/503 panel failures stay in their denominators. The separate 200-request sandbox-denied attempt is retained but not treated as an accuracy result. Panel known billing subtotal is **$0.131894**, with five requests lacking billing data; this is not an exact full bill.

Remote cleanup removed only `codex/agent-update-guide`, `codex/jev-followups` and `codex/six-skill-entrypoints`: all had zero commits outside main and no open PR. `codex/triage-smoke-test` was retained because commit `827c038` is not in main; active PR #8 was retained.

Version 0.2.1 is a candidate. [Publication after user merge](RELEASE.md); no tag, Release or self-merge performed.
