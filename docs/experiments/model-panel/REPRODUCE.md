# Protocol, sources and reproduction

[Results first](README.md). Run commands from the repository root. No model request is made by preparation, export or rescoring. Only `--live` bills your account.

## Protocol

- Same frozen item, evidence and choices across five models; gold stays outside requests. Per-item model order rotates. At most **4 concurrent requests per campaign**, no automatic retries. Some independent campaigns overlap, so these are not isolated latency benchmarks.
- Chat: temperature 0, max 1024 output tokens, strict JSON-schema enum; `provider.require_parameters=true`. Reasoning disabled for DeepSeek/Qwen, omitted for Llama. Jev uses typed Decisions. Settings are **not equal compute**, and provider availability/cache state can affect both cost and time.
- Transport timeout **30 seconds per socket operation**, not a hard whole-campaign deadline. Fatal400/401/402/403/404 stops after the current wave. HTTP/format failures remain in the denominator. No failed item is replaced by a successful retry.
- Each run seals sample bytes and manifest, records source hashes, request/response and timing. v1 manifests omit explicit protocol/timeout fields; [archived v1 runner](runner-v1.py.txt) plus source hashes identify that implementation. [v2](runner-v2.py.txt) states those fields and retains safe transport diagnostics. Current v3 also fails locally before any live artifact when the key is missing. **The payload/scoring protocol is unchanged**; v1's unused `json_object` option was replaced at execution by the enum schema recorded in each request.
- Current offline validation also reparses response-bearing errors. Every published run passed this validation. `needs_review` is merely a flag; no reviewer was executed and no hypothetical correction receives accuracy credit.
- Jev probability-vector calibration, confidence-shape diagnostics, confusion matrices and per-label counts are in `summary.json`. Calibration is descriptive for each small sample; no universal0.9 threshold claim. Chat models emit labels only: probability calibration is N/A.
- PR agreement uses pre-call host-Agent labels, aware of merge status. Thirty merged and ten closed-unmerged PRs include routine upkeep, documentation changes and bug/security fixes. **No negative-value gold**: this experiment does not validate detecting useless PRs. Related README edits are correlated, patches capped at18000 characters, no patch code executed.
- The Agent pilot separately uses the existing harness: `reasoning.effort=none`, max512 tokens, JSON object. Both arms use identical base settings. Final persisted states and observations replay from actual tool actions; the environment is synthetic, not a real browser or long-running production task.

## Data map and terms

Pinned files and SHA256: [`panel-sources.json`](../../../evals/fixtures/panel-sources.json). Exact revisions, split, sample IDs and pre-call labels are in each run's `index.json`. Sampling for native external datasets is `random.Random('20260922:'+dataset).sample(eligible,20)`, then lexicographic ID order. No conditioning on gold labels or observed performance.

| Dataset | Split / eligible pool | Source / terms | Skill |
| --- | --- | --- | --- |
| BBH | Same frozen160:40 each from4 tasks | [Authors](https://github.com/suzgunmirac/BIG-Bench-Hard/tree/9ee07bd481feebf959a6b59d61ea57bdcf30964d); [existing attribution](../../../evals/THIRD_PARTY.md) | jev |
| LogiQA2.0 | Chinese test1594 | [Authors](https://github.com/csitfun/LogiQA2.0/tree/955e1d3df6c59d9bfb44d9913da1e1a27ec14e18); CC-BY-NC-SA4.0 | jev |
| OCNLI | dev3000 →2950; exclude50 label`-` | [Authors](https://github.com/CLUEbenchmark/OCNLI/tree/b53efdee17257a5c33993cf6fcf8ffff0497ea0e); CC-BY-NC2.0; heed upstream LCMC notices | jev-documents |
| COIG-CQIA Ruozhiba |240 open answers →20 adapted MC | [Card](https://huggingface.co/datasets/m-a-p/COIG-CQIA/tree/8b55868c6168adf86c30e7ca0f782cca1c514297); license unspecified | jev |
| Banking77 | test3080; all77 label options | [PolyAI](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b); CC-BY4.0 | jev-triage |
| BoolQ | validation3270 | [Google card](https://huggingface.co/datasets/google/boolq/tree/35b264d03638db9f4ce671b711558bf7ff0f80d5); CC-BY-SA3.0 | jev-documents |
| BFCL v4 multiple |200; one unique gold function name | [Authors](https://github.com/ShishirPatil/gorilla/tree/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard); Apache2.0; name-only adaptation | jev-act |
| deepset prompt-injections | test116 | [Card](https://huggingface.co/datasets/deepset/prompt-injections/tree/4f61ecb038e9c3fb77e21034b22511b523772cdd); conflicting nestedCC-BY4.0/topApache2.0 | jev-eval |
| Public PRs | Previous20 + latest10 merged and10 unmerged from30 closed Browser Use PRs at collection | [URLs, hashes, rationale](../../../evals/fixtures/pr-mixed-annotations.json); raw snapshots local only | jev-eval |
| Context / Agent | Existing20 synthetic pairs /4 synthetic environments | [Context source](../context-pilot/cases.json), [Agent source](../../../evals/scenarios.py); project-authored | jev / jev-act |

Dataset licenses do not become the code's MIT license. External source-bearing requests/responses stay in the maintainer's local evidence archive; public derived records contain IDs, hashes, labels, predictions, probabilities and numeric usage only. This allows public **metric** recomputation, not independent authentication of withheld raw responses. The pinned downloader reconstructs original questions locally, subject to upstream availability and your use rights; it does not grant redistribution rights.

**Candidate not used:** Salesforce xLAM60k required gated terms; no terms were accepted and no gated data fetched. Public BFCL supplies the narrower tool-name pilot instead. COIG's `logi_qa` subset was not mistaken for native LogiQA2.0.

**Ruozhiba review:** original references are marked LLM-generated/human-verified upstream, not independent gold. Six initially sampled items excluded for reference errors, subjective/ambiguous interpretations or open-ended grief response; reserve exclusions and seeds are retained in the run index. A separate reviewing Agent approved all20 authored questions **before model calls**. Correct positions A/B/C/D each5; mean correct-option length20.10 characters versus19.32 for distractors; longest including ties15/20. This is easy misconception discrimination with residual option cues, not a hard reasoning benchmark. Original questions/reference prose are not republished in the authored [option fixture](../../../evals/fixtures/ruozhiba-mc-options.json).

## Recompute published results — offline, no key

```bash
python -m evals.panel_report --output docs/experiments/model-panel/runs/logiqa
python -m evals.panel_overview
python -m evals.summarize evals/results/agent-v4-panel-2026-09-22
python -m unittest discover -s tests -v
```

`panel_report` verifies derived-record hashes/completeness and rebuilds metrics/table. `model_panel` verifies original request/response records when available:

```bash
python -m evals.model_panel --output evals/results/panel-bbh-2026-09-22
```

## Reconstruct source inputs, then optionally run again

Review source terms first. `pyarrow` is optional and needed **only** to prepare BoolQ/injection Parquet, not to score published records or install the skill. Nothing installs it automatically.

```bash
python -m evals.panel_prepare --dataset logiqa \
  --cache /tmp/jev-source-cache --download \
  --publication docs/experiments/model-panel/runs/logiqa \
  --output /tmp/jev-logiqa-new-run
# Inspect samples.json: exact input, all choices, gold stored separately from request payloads.
# ONLY the next command makes paid calls (100 max here); key comes from your environment.
python -m evals.model_panel --output /tmp/jev-logiqa-new-run --live
python -m evals.panel_report --export /tmp/jev-logiqa-new-run --output /tmp/jev-logiqa-new-report
```

Dataset choices: `logiqa`, `ocnli`, `banking`, `boolq`, `bfcl`, `ruozhiba`, `injection`. Cache-only reconstruction is default; `--download` is an explicit network opt-in. All source hashes and **the complete reconstructed sample hash** must match before preparation succeeds. v2 source hashes freeze the current runner for the new run; it never reuses historical responses as new observations.

For PRs, `--collect` uses your existing `gh` authentication to read public metadata/diffs, performs no writes and executes no patch:

```bash
python -m evals.panel_pr --cache /tmp/jev-pr-new-cache --collect \
  --publication docs/experiments/model-panel/runs/pr --output /tmp/jev-pr-new-run
```

Mutable upstream PR bodies may no longer reconstruct exactly; the command then stops, rather than silently evaluating changed samples. For BBH/context, load the committed `samples.json`, choose explicit model options without `response_format`/`provider` overrides, and call `evals.model_panel.prepare(new_directory, samples, models, provenance)` before `--live`.

For the Agent comparison:

```bash
python -m evals.run --base-model deepseek/deepseek-v4-flash --repeats 1 --max-steps 10
# Dry manifest above makes no requests. Opt in explicitly for max92 calls:
python -m evals.run --base-model deepseek/deepseek-v4-flash --repeats 1 --max-steps 10 \
  --live --output /tmp/jev-agent-new-run
```

## Failed preparations and preflights stay visible

- [Initial5-call preflight](../../../evals/results/panel-preflight-2026-09-22): DeepSeek returned a choice description, not its label. Strict parser rejected it. This predates manifest sealing; retain its original receipt/summary, not a retroactively sealed claim.
- [Separate enum-schema5-call preflight](../../../evals/results/panel-schema-preflight-2026-09-22): all5 valid. The changed protocol, not a hidden retry, became the panel format.
- [Sandbox-denied context attempt](../../../evals/results/panel-context-2026-09-22): all200 transport errors, **not an accuracy result**. [Separate network-enabled campaign](../../../evals/results/panel-context-network-2026-09-22) used the same40 inputs. v1 did not retain DNS/phase detail; command-environment logs established restricted networking. v2 preserves safe transport diagnostics.
- Published model panels retain **5 Llama failures**: 3 BBH (two HTTP429, one503), 1 LogiQA (HTTP503), 1 PR (HTTP503). These are provider request failures, not malformed choice labels. Every failure remains in its original denominator.

No automatic retry, model substitution, hidden human correction, target attack, trade, PR merge or real browser action was part of these experiments.
