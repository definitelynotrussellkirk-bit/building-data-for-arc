"""Verify the audit hypothesis against retained public Racket apply outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from probe_rotation import HERE, dump, ignore_pure_left_translation


def main():
    receipt_path = HERE / "racket.json"
    receipt = json.loads(receipt_path.read_text())
    report = json.loads((HERE / "counterexample.json").read_text())
    lesson = json.loads((HERE / "rotation_lesson.json").read_text())
    original_pairs = lesson["original_instance"]["train"] + lesson["original_instance"]["test"]
    rows = receipt["results"]
    assert len(rows) == 13
    assert all(row["valid_output"] and not row["error"] for row in rows)
    assert receipt["generator_sha256"] == report["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"]
    assert all(ignore_pure_left_translation(row["input"]) == row["output"] for row in rows[:4])
    assert all(row["input"] == pair["input"] and row["output"] == pair["output"] for row, pair in zip(rows[4:], original_pairs))
    query_index = report["rotation_query_pair_index"]
    assert all(ignore_pure_left_translation(rows[4+i]["input"]) == rows[4+i]["output"] for i in report["rotation_train_indices"])
    query_row = rows[4 + query_index]
    rival = ignore_pure_left_translation(query_row["input"])
    differences = [
        [r, c, expected, rival[r][c]]
        for r, row in enumerate(query_row["output"])
        for c, expected in enumerate(row)
        if expected != rival[r][c]
    ]
    assert differences
    report.update({
        "public_apply_verified": True,
        "public_apply_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "public_apply_case_count": len(rows),
        "public_apply_valid_outputs": len(rows),
        "canonical_racket_fit": 4,
        "rotation_racket_demo_fit": 8,
        "query_actual_racket_output": query_row["output"],
        "query_actual_racket_output_sha256": query_row["output_sha256"],
        "query_rival_output": rival,
        "query_different_cells_r_c_actual_rival": differences,
        "verification_probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    dump("counterexample.json", report)
    summary = json.loads((HERE / "combined/checks/28b87bd4c441_audit_summary.json").read_text())
    gate = json.loads((HERE / "combined/checks/28b87bd4c441_audit_semantic_gate.json").read_text())["audits"][0]
    rotations = gate["lessons"]["rotations"]
    compact = {
        "task_id": report["task_id"],
        "generator_sha256": report["generator_sha256"],
        "rule_text_sha256": report["rule_text_sha256"],
        "preset_passed": summary["passed"],
        "task_test_counts": summary["stages"]["task_tests"]["test_counts"],
        "ordered_lessons_identifiable": gate["lessons"]["identifiable"],
        "ordered_lessons_materialized": gate["lessons"]["materialized"],
        "demonstrations": gate["lessons"]["n_demos"],
        "rotations": {key: rotations[key] for key in ["checked", "ambiguous", "hook_warnings", "errors", "status", "required"]},
        "additional_rival_counterexample": {
            "rival": report["rival"], "canonical_fit": 4,
            "rotation_demo_fit": 8, "query_difference_count": len(differences),
        },
    }
    dump("audit_summary.json", compact)
    section = f'''## 28b87bd4c441

**A1 — Reproduced query-rotation limitation; ordered-production audit passed.**
The audit-only generator and canonical authority were left unchanged.
Generator version 2.0.0, SHA-256 `{report['generator_sha256']}`;
executed rule ID `{report['executed_rule_hash']}`, Racket text SHA-256
`{report['rule_text_sha256']}`.

The public isolated audit preset completed both requested stages: **6 tests
passed, 0 failed, 0 errors, 0 skipped**, and the strict semantic gate passed.
Its ordered lessons used **8 demonstrations plus 1 final query**: **12/12**
were identifiable against the declared rivals. Query rotation was diagnostic:
**108 rotations, 0 declared-rival ambiguities, 84 hook warnings, 0 errors**.
The warnings identify missing scene profiles; they are not evidence that all
rotations are supported. The native twelve-stage battery summary is incomplete
because this was the two-stage audit preset, not a requested full battery.

The retained counterexample rotates out the sole pure-left translation from an
actual generated lesson: difficulty `easy`, seed `{report['seed']}`, requested
lesson start 0, original pair index 1 (independently reproduced by generator
sample index 1). The remaining 8 demonstrations fit the additional hypothesis
“translate normally except pure-left requests produce a blank grid.” This
intentional audit rival also fits **all 3 canonical training pairs and the
labeled canonical test**. The selected Racket authority instead returns three
gray cells for the held-out query, at `(2,2)`, `(3,1)`, and `(3,2)`; the rival
returns a blank 9×12 output. The query has one red marker at `(2,1)` and gray
cells at `(2,8)`, `(3,7)`, `(3,8)`. It passes `self_check`, is observed as
`row_left_hollow_l3`, and was reproduced exactly by `generate`, so this is
inside the documented generator domain. Public `arcpuzzles apply` independently
verified all **13** inputs: 4 canonical pairs plus the 9 generated lesson pairs.

**Decision/domain question:** retain an explicit ordered-only export policy,
or repeat the necessary directional witnesses before claiming arbitrary query
holdouts. If rotation support is intended, add a per-direction omission rival
and a retained rotation test; the current hook correctly warns when the sole
profile is withheld. This finding does not establish an incorrect reference
label or failure of the intended ordered curriculum.

**No issue found in the checked canonical labels, validator acceptance of those
inputs, or the six retained task tests.** The existing tests still use a legacy
staged import; the public preset emitted its portability warning and executed
all six successfully. No broader generator battery or exhaustive seed census
was run for this audit.

Evidence (paths relative to `WORK/`):

- `checks/audit/28b87bd4c441/combined/checks/28b87bd4c441_audit_summary.json`
- `checks/audit/28b87bd4c441/combined/checks/task_tests.xml`
- `checks/audit/28b87bd4c441/combined/checks/28b87bd4c441_audit_semantic_gate.json`
- `checks/audit/28b87bd4c441/counterexample.json`
- `checks/audit/28b87bd4c441/rotation_lesson.json`
- `checks/audit/28b87bd4c441/inputs.json` and `racket.json` in that directory
- `checks/audit/28b87bd4c441/probe_rotation.py`, `verify_rotation.py`, and `commands.json`
'''
    (HERE / "AUDIT_SECTION.md").write_text(section, encoding="utf-8")
    print(json.dumps(compact, sort_keys=True))


if __name__ == "__main__":
    main()
