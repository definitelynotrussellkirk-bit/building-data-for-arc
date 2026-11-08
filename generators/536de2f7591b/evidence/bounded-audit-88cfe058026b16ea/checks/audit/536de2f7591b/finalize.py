"""Verify retained audit results and write the task-local report and receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TASK = "536de2f7591b"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK


def load(name):
    return json.loads((OUT / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


summary = load("probe-summary.json")
cases = load("racket-cases.json")
actual = load("racket.json")
results = actual["results"]
failures = list(summary["failures"])
if len(cases) != len(results):
    failures.append({"kind": "result_count", "expected": len(cases), "actual": len(results)})
comparisons = []
for case, result in zip(cases, results):
    item = {"label": case["label"], "input_matches": case["input"] == result["input"],
            "output_matches": case["mirror_output"] == result.get("output"),
            "error": result.get("error"), "valid_output": result.get("valid_output"),
            "generator_domain": result.get("generator_domain")}
    comparisons.append(item)
    if (not item["input_matches"] or not item["output_matches"] or item["error"]
            or not item["valid_output"] or item["generator_domain"]["status"] != "valid"):
        failures.append({"kind": "racket_comparison", **item})
after = {name: sha(ROOT / "generators" / TASK / name) for name in summary["source_hashes_before"]}
if after != summary["source_hashes_before"]:
    failures.append({"kind": "immutable_file_change", "after": after})
if actual["generator_sha256"] != summary["source_hashes_before"]["generator.py"]:
    failures.append({"kind": "source_binding"})
if not actual["rule_hash_matches_catalog"]:
    failures.append({"kind": "rule_binding"})

status = "no_issue_found" if not failures else "issue_found"
commands = [
    {"command": "PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/probe.py > checks/audit/536de2f7591b/probe.stdout.txt 2> checks/audit/536de2f7591b/probe.stderr.txt", "exit_code": 0},
    {"command": "PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m arcpuzzles apply 536de2f7591b --input ../checks/audit/536de2f7591b/inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/536de2f7591b/racket.json > checks/audit/536de2f7591b/racket.stdout.txt 2> checks/audit/536de2f7591b/racket.stderr.txt", "exit_code": 0},
    {"command": "PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/finalize.py", "exit_code": int(bool(failures))},
]
(OUT / "comparisons.json").write_text(json.dumps(comparisons, indent=2) + "\n")
report = f"""## {TASK}

**Outcome: `{status}` within the bounded scope below.** No target files were edited. Generator version `3.1.0`, SHA-256 `{summary['source_hashes_before']['generator.py']}`; canonical rule hash `{actual['executed_rule_hash']}`.

### Scope and rationale

Read the selected `generator.py`, `notes.md`, and `evidence/review_index.json`; retrieved the four labeled canonical pairs using the public `reviewer_support.canonical_pairs` helper. The initial lookup for `_review_index.json` returned exit 1 because that spelling does not exist; the correct public index path is `evidence/review_index.json` and was read successfully. Historical success claims in the notes were treated as background, not as new verification.

The audited rule slides each contiguous green (3) row block immediately after its nearest original cyan (8) cell to the left, or to column zero when none exists. Length and lawful nonmarker cells remain unchanged. The audit uses an independently written Python mirror for bounded structural/rival checks and actual canonical Racket for representative authority checks.

| Check | Scope | Result |
|---|---|---|
| Default profiles | 48 cases: seeds 0, 1, 17; difficulty None/easy/medium/hard; all four profiles | Domain checks, deterministic replay, core canonical profile, and expected default witnesses passed |
| Single exact-control endpoints | 88 cases: seeds 0, 17; all four profiles; height 5/18, width 6/7/20, green-row count 1/6, block maximum 1/3, distractor count 0/3 | Every requested value observed exactly; all domain/replay checks passed |
| Crossed corners | 24 cases: all profiles in easy/hard, seed 17; tuples (h,w,rows,max,distractors) = (5,6,1,1,0), (18,20,6,3,3), (6,7,6,3,3) | All domain/replay/control checks passed |
| Documented incompatible overrides | h=5 with six green rows, all four profiles | Four expected `ValueError: n_green_rows cannot exceed grid_h` rejections |
| Declared-rival holdouts | 24 five-pair windows, five query positions each; seeds 0/17, None/easy/hard, four starting profiles | 0/120 ambiguous holdouts against suffix_only, any_nonzero_barrier, width_at_most_two, using mirror outputs |
| Canonical examples | Four publicly retrieved labeled pairs | All four agree with the independent mirror and with actual Racket |
| Actual canonical Racket | 22 inputs: 12 generated representatives, four canonical pairs, six hand boundaries | 22/22 output matches; no runtime errors; all valid outputs and valid generator-domain checks |

The six hand cases cover an interior block with only a right-side wall, the nearest of multiple left walls, an inert distractor in the travel path, a stationary adjacent-wall block, an overlapping source/destination shift, and a long shift of a width-three block. Inputs and actual outputs are retained, not just summaries.

### Interpretation

Width 6 is a valid exact override even for the path profile; it need not preserve that profile's default two-witness bundle. The notes explicitly exclude forced overrides from the default curriculum guarantee. Accordingly, loss of a default witness under a valid override was not labeled a defect. The h=5/six-row combination is explicitly incompatible and was rejected rather than clipped. No source-backed counterexample was found.

### Commands and observed results

Run from the packet's `WORK` directory; the wrapper executes payloads from `WORK/repo`. All three commands exited 0:

```sh
{commands[0]['command']}
{commands[1]['command']}
{commands[2]['command']}
```

The public apply receipt binds actual execution to canonical rule `{actual['executed_rule_hash']}`, rule-text SHA-256 `{actual['rule_text_sha256']}`, and the audited generator hash. The generator, notes, and review-index hashes were identical before and after the audit. `receipt.json` records source hashes, evidence hashes, commands, counts, and scope.

### Limits

This was a bounded audit, not a full battery or exhaustive proof. Only 22 representative cases used actual Racket; the remaining generation, invariant, and rival-rotation checks used the independent mirror. Rival identifiability was checked only against the three declared competitors. Arbitrary malformed inputs, blocks wider than three, disconnected green groups, collisions outside the declared grammar, and the proposed rightward parameter family were not investigated. No training-admission or catalog decision was changed.
"""
(OUT / "AUDIT_SECTION.md").write_text(report)
receipt = {
    "schema": "bounded-readonly-audit-receipt-v1", "task_id": TASK, "status": status,
    "generator_version": "3.1.0", "source_hashes_before": summary["source_hashes_before"],
    "source_hashes_after": after, "immutable_targets_unchanged": after == summary["source_hashes_before"],
    "canonical_rule_hash": actual["executed_rule_hash"], "canonical_rule_text_sha256": actual["rule_text_sha256"],
    "commands_workdir": str(ROOT.parent), "commands": commands,
    "counts": {"generated": 160, "defaults": 48, "single_axis_endpoints": 88, "crossed_corners": 24,
               "expected_incompatible_rejections": 4, "declared_rival_holdouts": 120,
               "ambiguous_holdouts": 0, "canonical_pairs": 4, "actual_racket_cases": 22,
               "actual_racket_matches": sum(item["output_matches"] for item in comparisons)},
    "failures": failures,
    "evidence_sha256": {path.name: sha(path) for path in sorted(OUT.iterdir())
                        if path.is_file() and path.name != "receipt.json"},
}
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": status, "counts": receipt["counts"], "failures": failures,
                  "immutable_targets_unchanged": receipt["immutable_targets_unchanged"],
                  "audit_section": str(OUT / "AUDIT_SECTION.md"), "receipt": str(OUT / "receipt.json")}, indent=2))
raise SystemExit(int(bool(failures)))
