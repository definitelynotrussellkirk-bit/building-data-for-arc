## 2b3472c73d30

**A-2b3472c73d30-1 — Reproduced production-lesson counterexample against a plausible canonical-fitting shortcut.** Findings-only audit; no generator, reference, or shared-tool changes. The shortcut is an explicit audit-added rival, not a claim about observed model behavior. No label or validator discrepancy was found in the four authoritative pairs checked.

**Source binding:** generator version 3.0.0, SHA-256 `ad402fc1ed1aab6efd2cd5ffb3363ca4f0e0fae10ab6509a0fc45c18772e8bfa`; selected canonical rule `9f6d9dc4a68d`; executed Racket callable-text SHA-256 `7e2dfa5a7109a24a59121dfc4c4ab522274628bfa3ee712000cba062e3e4a554`. Source matches the audit draw. All results below concern this unchanged source.

### Concrete finding

The audit rival fills black gaps between the first and last occurrence of every repeated nonzero row-local color, while preserving existing nonzero cells. It omits two conditions of the intended rule: the color must occur **exactly twice**, and every intervening cell must be black. This simpler behavior fits **all 3/3 usable canonical pairs** (2 train, 1 labeled test), verified using `reviewer_support.canonical_pairs`.

The ordinary public production command at **seed 3, medium, start sample index 0, no overrides, 3 demonstrations + 1 query** accepted indices **0,1,2,3 with zero rejections**. The rival matches all three Racket-labeled demonstrations exactly, but differs in **5 cells** on the Racket-labeled query. All four inputs pass the target's `self_check`, independently recorded by `arcpuzzles apply --check-generator-domain`, and are actual generated examples in the documented domain.

The query has **12 rows × 12 columns**, and its authoritative output also has **12 rows × 12 columns**. At zero-based row 5, color 4 occurs at columns 4 and 10, with a color-3 blocker at column 9. Racket leaves columns 5..8 black; the rival fills those four cells with 4. At row 8, color 7 occurs at columns 7,8,10. Racket leaves column 9 black because there are three occurrences; the rival fills it with 7. The complete input, Racket output, rival output, source/rule hashes, recipe, commands and mismatch coordinates are in `checks/audit/2b3472c73d30/counterexample.json`.

**Production verdict:** unsupported against this named rival on the retained episode, **1/1 query**. **Diagnostic rotation verdict:** holding out each of the same four materialized pairs once with the other three as demonstrations yields **1/4 unsupported query positions**; the other three rotations include the original negative query among demonstrations and refute this rival. These are four holdouts of one lesson, not four independently generated lessons. This is a narrow rival-specific counterexample; no universal identifiability claim is made.

The generator declares `EXAMPLES_NEEDED = 3` but declares neither `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, nor `lesson_identifiable`. The retained production episode explicitly reports `lesson_check.status: not_declared` and `contract: none`. Generation succeeds without establishing that the demonstrations teach the exact-count and blocker conditions needed by this query.

### Measured coverage and limits

A preliminary Python-only search evaluated seeds **0..63**, medium, indices **0..3** per seed, first 3 as demonstrations and fourth as query: **64 candidate lessons, 256 grid evaluations, 256 unique inputs, 256/256 self-check-valid**. The audit rival fitted all demonstrations but differed from the Python rule mirror on the query in **7/64** lessons. This 7/64 is a **Python-mirror diagnostic**, not a 64-lesson Racket census. The selected seed-3 lesson was then independently materialized by public generation and all its four pairs confirmed by public canonical Racket apply: **4/4 mirror/reference matches, 4/4 valid domain, 4/4 valid Racket outputs**. Exact records are retained in `checks/audit/2b3472c73d30/python-search.json`, `checks/audit/2b3472c73d30/production-seed3.jsonl`, and `checks/audit/2b3472c73d30/racket-seed3.json`.

The probe enumerates the generator's live rival declarations instead of copying a stale rival-name list, and records their absence. The added audit rival is labeled separately. The task has no declared lesson schedule period; no exhaustive schedule/seed claim follows. I did not run a full battery or target regression suite because the direct source-bound production witness and selected-authority checks suffice for this finding. No correctness, malformed-grid acceptance, or authority-parity defect is alleged from these data.

### Proposed task-local follow-up

Declare and test this canonical-fitting rival (and separate exact-two/blocker variants), then assemble complete lessons with the necessary refuting examples in their demonstrations. Retest the actual 3-demo production policy; increasing example count alone does not ensure that a required negative occurs. If a deterministic schedule is introduced, check every cyclic start and report production and rotation policies separately. Preserve the fixed canonical rule and valid input semantics. This is a recommended follow-up, **not an included patch or a resolved audit**.

### Exact reproduction commands

All commands below were run from the outer extracted packet root `/workspace/scratch/341195387165/packet`, exited **0**, and executed payloads in `WORK/repo/`. The actual argument arrays and retained evidence paths are also in `checks/audit/2b3472c73d30/RESULTS-FRAGMENT.json`.

```sh
WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python ../checks/audit/2b3472c73d30/probe_lesson.py

WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python -m arcpuzzles generate 2b3472c73d30 --count 1 --seed 3 --sample-index 0 --difficulty medium --train 3 --test 1 --timeout 180 --out ../checks/audit/2b3472c73d30/production-seed3.jsonl

WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python -m arcpuzzles apply 2b3472c73d30 --input ../checks/audit/2b3472c73d30/witness-inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/2b3472c73d30/racket-seed3.json

WORK/.venv/bin/python review.py run /workspace/scratch/341195387165/packet/WORK/.venv/bin/python ../checks/audit/2b3472c73d30/confirm_lesson.py
```

Public generation/apply output paths must be new for a repeat; preserve original receipts. The probe and confirmation scripts are standalone reviewer-owned evidence under this audit directory. No assignment reroll or audit redraw occurred.
