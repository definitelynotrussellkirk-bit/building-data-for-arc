#!/usr/bin/env python3
"""Finalize the bounded audit using retained Racket evidence; no runtime execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE = WORK / "repo/generators/4056ed281704/generator.py"

def read_json(name):
    return json.loads((HERE / name).read_text())

def digest_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def write_json(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")

probe = read_json("probe.json")
applied = read_json("racket.json")
receipt = read_json("apply-command.receipt.json")
rivals = read_json("rival_outputs.json")["rivals"]
formula = read_json("python_formula_output.json")["output"]
input_grid = read_json("input.json")["input"]
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_sha == probe["generator_sha256"] == applied["generator_sha256"]
assert applied["task_id"] == applied["rule_task_id"] == "4056ed281704"
assert applied["reference"] == "canonical"
assert applied["rule_hash_matches_catalog"] is True
assert applied["executed_rule_hash"] == probe["canonical_normalized_rule_hash"]
assert applied["rule_text_sha256"] == probe["canonical_program_sha256"]
assert hashlib.sha256((HERE / "canonical-program.rkt").read_bytes()).hexdigest() == applied["rule_text_sha256"]
assert receipt["exit_code"] == 0
assert len(applied["results"]) == 1
actual = applied["results"][0]
assert actual["valid_output"] is True and actual["error"] is None
assert actual["input"] == input_grid
assert actual["input_sha256"] == digest_grid(input_grid) == probe["selected_input"]["input_sha256"]
assert actual["output_sha256"] == digest_grid(actual["output"])
assert actual["output"] == formula

actual_output = actual["output"]
comparisons = {}
for name, rival in rivals.items():
    output = rival["output"]
    a_h, a_w = len(actual_output), len(actual_output[0])
    r_h, r_w = len(output), len(output[0])
    common_differences = [
        {"row": r, "col": c, "racket": actual_output[r][c], "rival": output[r][c]}
        for r in range(min(a_h, r_h)) for c in range(min(a_w, r_w))
        if actual_output[r][c] != output[r][c]
    ]
    missing_or_extra = a_h * a_w + r_h * r_w - 2 * min(a_h, r_h) * min(a_w, r_w)
    comparisons[name] = {
        "description": rival["description"],
        "canonical_pairs_fit": rival["canonical_pairs_fit"],
        "racket_shape": [a_h, a_w], "rival_shape": [r_h, r_w],
        "same_shape": (a_h, a_w) == (r_h, r_w),
        "equals_racket": output == actual_output,
        "common_cell_differences": common_differences,
        "common_cell_difference_count": len(common_differences),
        "missing_or_extra_cells_due_to_shape": missing_or_extra,
        "rival_output_sha256": digest_grid(output),
    }
    assert output != actual_output, name
assert comparisons["square_by_height"]["rival_shape"] == [10, 10]
assert comparisons["square_by_height"]["missing_or_extra_cells_due_to_shape"] == 40
assert comparisons["closed_border_lattice"]["common_cell_difference_count"] == 7

result = {
    "task_id": "4056ed281704",
    "status": "completed_bounded_audit",
    "semantic_verdict": "no_semantic_issue_found_within_bounded_check",
    "public_contract_verdict": "confirmed_ignored_side_axis_and_dead_helpful_textures",
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "generator_sha256": source_sha,
    "canonical_program_sha256": applied["rule_text_sha256"],
    "executed_rule_hash": applied["executed_rule_hash"],
    "input": {
        "call": probe["selected_input"]["call"], "shape": probe["selected_input"]["shape"],
        "sha256": actual["input_sha256"], "self_check": probe["selected_input"]["self_check"],
        "literal_grid_verified": probe["selected_input"]["all_literal_arc_colors"],
    },
    "actual_racket_result": {
        "exit_code": receipt["exit_code"], "valid_output": actual["valid_output"],
        "output_sha256": actual["output_sha256"], "matches_diagnostic_formula": True,
    },
    "rival_comparisons": comparisons,
    "confirmed_contract_findings": probe["findings"],
    "scope": {
        **probe["scope"], "no_runtime_execution": False,
        "canonical_racket_applications": 1,
        "determinism_repeat_calls": 1,
        "racket_application_owner": "main reviewer, serialized runtime window",
        "additional_racket_execution_for_comparison": False,
    },
    "actual_apply_command": receipt,
    "actual_apply_outer_cwd": str(WORK.parent),
    "actual_apply_payload_cwd": applied["cwd"],
    "evidence": [
        "probe.py", "probe-command.json", "probe.stdout.txt", "probe.json",
        "input.json", "canonical-program.rkt", "python_formula_output.json",
        "rival_outputs.json", "racket.json", "apply-command.receipt.json",
        "apply-command.log", "comparison.json", "AUDIT_SECTION.md",
    ],
    "limitations": [
        "The absence of a semantic failure is limited to four canonical pairs, two explicitly described rivals, and one generator-produced/validator-accepted input executed by Racket.",
        "The ignored controls are an actionable public-interface discrepancy, not an inferred error in the selected parity rule.",
        "The source explicitly supports rectangles despite stale odd-square metadata; the audit distinguishes actual source/validator behavior from that documentation.",
        "This audit creates neither generator approval nor training admission, and makes no claims based on unavailable files.",
        "No source or tests were changed; the main assignment identity was not altered.",
    ],
}
write_json("comparison.json", result)

section = f"""## Audit 4056ed281704 — bounded semantic check passed; public controls remain inconsistent

**Result:** no semantic failure was found in the bounded check. One real canonical Racket application matched the selected parity formula and refuted two plausible rivals that fit all four supplied canonical examples. A separate, reproducible public-interface issue remains: advertised side and helpful-texture controls are ignored. No task source was changed.

**Source binding:** generators/4056ed281704/generator.py, VERSION 2.0.1, SHA-256 {source_sha}. Exact canonical program SHA-256 {applied["rule_text_sha256"]}; executed/catalog rule hash {applied["executed_rule_hash"]}.

### Actual witness and rival check

The selected call was generate(seed=0, sample_index=0, difficulty=None). It produced a literal 10×6 all-zero input accepted by public normalize_grid and the selected self_check (errors=[]). Input SHA-256: {actual["input_sha256"]}.

The actual canonical Racket command exited 0 and returned a valid 10×6 output with SHA-256 {actual["output_sha256"]}. It equals the expected fixed lattice: 0 where both zero-based coordinates are odd, and 1 elsewhere. Input-content independence is the task's rule and was not treated as a shortcut defect.

All four supplied canonical pairs are odd squares of sides 5, 7, 9, and 11. Both exploratory rivals fit all four of those complete labeled pairs:

| Rival | Actual result on the 10×6 generated input |
| --- | --- |
| Assume output width equals input height | Produces 10×10 instead of the actual 10×6; 40 excess cells. |
| Force all perimeter cells of the parity lattice to 1 | Same dimensions, but disagrees with Racket on 7 cells, including (row 1, column 5): Racket 0, rival 1. |

The generator's rectangular/even support therefore provides a distinguishing example against these two canonical-fitting assumptions. This is evidence of coverage for those rivals, not a claim about every possible shortcut.

### Confirmed public-interface discrepancy

At the same seed and sample index, both advertised legal overrides side=5 and side=13 return the unchanged 10×6 grid, so neither honors its requested square size. All five declared HELPFUL_TEXTURES— all_zero, random, sparse, blob, structured—also return the identical untextured draw.

AXES and HELPFUL_TEXTURES advertise those controls at generator.py lines 27–39. The actual implementation only dispatches DEGENERATE_TEXTURES, then draws grid_h and grid_w at lines 56–74; it never consumes the side override or helpful texture values. The source explicitly describes independent rectangular dimensions at lines 64–67, while its opening summary/invariants still describe odd squares. The repository specification names dead texture branches as contract warnings (docs/reference/PUZZLE_GENERATOR_SPEC.md lines 264–269).

Recommended follow-up: align advertised axes, textures, summary, and invariants with the intended all-zero rectangular sampler, or implement the promised controls where semantically appropriate. This audit does not propose adding decorated input content merely to satisfy obsolete metadata. Diagnostic degenerate-texture rejection was not reported as a defect.

### Exact command and bounded scope

The actual command, from the packet root /tmp/arc_review_121953_mount, was:

    /tmp/arc_review_121953_mount/WORK/.venv/bin/python review.py run /tmp/arc_review_121953_mount/WORK/.venv/bin/python -m arcpuzzles apply 4056ed281704 --input ../checks/audit/4056ed281704/input.json --out ../checks/audit/4056ed281704/racket.json

The effective payload cwd was {applied["cwd"]}. Exit code: 0. The main reviewer ran this single application in the serialized Racket window; the independent comparison started no additional runtime.

Scope: one default draw, one determinism repeat, two legal side controls, five helpful-texture controls, four canonical labeled pairs, two described rivals, and one actual Racket input. Global Python RNG state was preserved. No exhaustive seed/difficulty battery was run, no unavailable-file claim was made, and approval/training-admission state was not changed.

Evidence under checks/audit/4056ed281704/: probe.py, probe-command.json, probe.stdout.txt, probe.json, input.json, canonical-program.rkt, python_formula_output.json, rival_outputs.json, racket.json, apply-command.receipt.json, apply-command.log, and comparison.json. probe.json records the pre-Racket stage; comparison.json is the final source-bound outcome.
"""
with (HERE / "AUDIT_SECTION.md").open("x") as stream:
    stream.write(section)
for name in ("run_racket_apply.py", "audit-section.md"):
    path = HERE / name
    if path.is_file():
        path.unlink()  # Remove only this reviewer's unused recorder and superseded draft.
print(json.dumps({
    "status": result["status"],
    "semantic_verdict": result["semantic_verdict"],
    "public_contract_verdict": result["public_contract_verdict"],
    "racket_matches_formula": True,
    "square_rival_extra_cells": 40,
    "border_rival_difference_cells": 7,
    "generator_sha256": source_sha,
}, sort_keys=True))
