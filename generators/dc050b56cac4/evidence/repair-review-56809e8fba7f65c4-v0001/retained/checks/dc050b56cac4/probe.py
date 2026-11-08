"""One bounded, source-bound gray-column-count learnability probe.

Run from the packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/dc050b56cac4/probe.py
"""
from pathlib import Path
import hashlib
import json
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent / "repo"
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from reviewer_support import load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator

TASK = "dc050b56cac4"
EXPECTED_SOURCE = "5c2069293d9871570c6d9210941c26a1e3e3cfd4865ddf04b326cc9d1524a157"


def gray_column_rival(grid):
    """Count gray-bearing columns, erase markers, shift cross down-left."""
    h, w = len(grid), len(grid[0])
    rows = [(r, row[0]) for r, row in enumerate(grid)
            if row[0] not in (0, 5) and len(set(row)) == 1]
    assert len(rows) == 1
    cr, color = rows[0]
    cols = [c for c in range(w) if all(row[c] == color for row in grid)]
    assert len(cols) == 1
    cc = cols[0]
    shift = len({c for row in grid for c, v in enumerate(row) if v == 5})
    nr, nc = cr + shift, cc - shift
    assert 0 <= nr < h and 0 <= nc < w
    return [[color if r == nr or c == nc else 0 for c in range(w)] for r in range(h)]


def main():
    gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == EXPECTED_SOURCE, "This evidence targets exact source bytes."
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK)
    rule_task_id = selected.get("rule_task_id", TASK)
    programs = {v.get("program_solution") for v in catalog._variants().get(rule_task_id, [])}
    assert len(programs) == 1
    program = programs.pop()
    rule_sha256 = hashlib.sha256(program.encode()).hexdigest()
    normalized_rule_sha256 = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
    assert normalized_rule_sha256[:12] == selected["rule_hash"] == gen.RULE_HASH == "4fe6d23687d0"
    apply, runtime_identity, bridge = _real_evaluator(RUNTIME)
    try:
        pairs = []
        for index in range(4):
            grid = gen.generate(424242, index, difficulty="easy")
            assert gen.self_check(grid) == []
            output = apply(program, grid)
            assert output == gen.rule_mirror(grid)
            pairs.append({"input": grid, "output": output})
        fits = [gray_column_rival(p["input"]) == p["output"] for p in pairs]
        assert fits == [True, True, True, False]
        guard_reasons = gen.lesson_identifiable(pairs[:3], pairs[3])
        assert guard_reasons == []

        # Reuse the retained row-count counterexample, without re-reporting it.
        retained_path = ROOT / f"generators/{TASK}/counterexamples/current-shortcut/checks/question/input.json"
        retained = json.loads(retained_path.read_text())
        if isinstance(retained, dict):
            retained = retained["input"]
        regenerated = gen.generate(424242, 1, difficulty="easy", grid_h=8,
            grid_w=8, cross_color=7, n_grays=2, cross_position="center")
        assert regenerated == retained
        retained_output = apply(program, retained)
        retained_refutations = {name: rival(retained) != retained_output
                               for name, rival in gen.LESSON_COMPETITORS.items()}
        assert all(retained_refutations.values())
        try:
            gen.generate(20261003, 0, difficulty="medium", texture="no_grays")
        except ValueError as error:
            historical_override = str(error)
        else:
            raise AssertionError("Historical no_grays override unexpectedly accepted")
    finally:
        bridge.close()

    case = {
        "task_id": TASK, "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH, "rule_sha256": rule_sha256,
        "normalized_rule_sha256": normalized_rule_sha256,
        "generation": {"seed": 424242, "sample_indices": [0, 1, 2, 3], "difficulty": "easy", "overrides": {}},
        "rival": "Move the cross down-left by the number of distinct gray-bearing columns; erase the gray markers.",
        "demos": pairs[:3], "query": pairs[3],
        "rival_query_output": gray_column_rival(pairs[3]["input"]),
        "rival_matches_by_index": fits,
        "counts": [{"gray_cells": sum(v == 5 for row in p["input"] for v in row),
                    "gray_columns": len({c for row in p["input"] for c, v in enumerate(row) if v == 5})} for p in pairs],
        "lesson_identifiable_reasons": guard_reasons,
        "retained_row_count_witness": {"input_regenerated_exactly": True,
            "current_declared_rivals_refuted": retained_refutations},
        "historical_no_grays_override_rejected": historical_override,
        "runtime_identity": runtime_identity,
        "racket_reference_evaluations": 5,
    }
    (OUT / "case.json").write_text(json.dumps(case, indent=2) + "\n")
    result = {
        "task_id": TASK, "status": "finding", "generator_sha256": source_hash,
        "source_path": source.relative_to(ROOT.parent).as_posix(),
        "rule_hash": gen.RULE_HASH, "rule_sha256": rule_sha256,
        "normalized_rule_sha256": normalized_rule_sha256,
        "command": {"argv": ["python3", "../checks/dc050b56cac4/probe.py"], "cwd": "repo", "exit_code": 0},
        "wrapper_command": {"argv": ["WORK/.venv/bin/python", "review.py", "run", "python3", "../checks/dc050b56cac4/probe.py"], "cwd": "packet_root"},
        "prior_attempt": {"exit_code": 1, "reason": "Probe incorrectly compared the raw program-byte SHA prefix with Catalog's whitespace-normalized rule hash. Corrected the probe to record both; this attempt stopped before Racket execution."},
        "evidence_paths": ["checks/dc050b56cac4/probe.py", "checks/dc050b56cac4/case.json"],
        "findings": ["Unlisted gray-column-count rival fits all three visible demos (seed 424242, easy, indices 0,1,2), but differs on the generated query at index 3. Counts are 1,2,3,2 gray cells versus 1,2,3,1 gray-bearing columns. The current lesson_identifiable hook returns no reasons for this lesson."],
        "prior_evidence_assessment": "The retained gray-row witness regenerates exactly and all three declared rivals disagree with its current Racket label. The historical texture=no_grays override is now rejected; neither is reported as a new defect.",
        "proposed_action": "Add the column-count competitor and guarantee a multi-cell vertical-stack demonstration when its query prediction differs. A repair must preserve the existing row/span/stack witnesses and all query rotations.",
        "limits": ["One generated four-pair window and one retained input; five protected Racket evaluations.", "No production-export invocation, full battery, parametric assessment, or universal rival search.", "Reviewer finding only; no production source change, integration, approval, or training admission."],
    }
    (OUT / "peer-review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source_sha256": source_hash,
                      "rule_hash": gen.RULE_HASH, "rival_matches": fits,
                      "evidence": "checks/dc050b56cac4/peer-review.json"}))


if __name__ == "__main__":
    main()
