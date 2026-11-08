"""Reproduce this semantic variant's bounded Racket reference evidence.

Run from any directory with this checkout's Python dependencies and Racket:
  python3 generators/generic_waypoint_route_gen1/workspace/validate_reference.py
The default run checks the retained candidate; --write-candidate relabels it
through real Racket. This never updates the shared ledger or safety metadata.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parents[1]
for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "shared/runtime/arc_repl").is_dir():
        ROOT = ancestor
        sys.path.insert(0, str(ancestor / "shared/runtime"))
        break
else:
    raise RuntimeError("cannot locate this checkout's shared/runtime")

from arc_repl.builtins import _unwrap
from arc_repl.executor import ArcExecutor
from reviewer_support import canonical_path, find_root


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def generator():
    spec = importlib.util.spec_from_file_location("waypoint_reference_generator", HOME / "generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def executor():
    live = ArcExecutor({"train": [], "test": []}, use_racket=True)
    result = live.step((HOME / "reference.rkt").read_text())
    if result.startswith("ERROR"):
        live.close()
        raise AssertionError(result)
    return live


def execute(live, grid):
    return _unwrap(live._apply_rule(grid))


def direction_case(turns):
    """Two coherent panels; two remaining, perpendicular route steps.

    Panel 1 shows p0 and four dots. Panel 2 shows p2 and two dots.
    The next state reaches p4 via p3 and must face along p3 -> p4.
    Rotate panel coordinates, preserving vertical separators, for all headings.
    """
    gen = generator()
    points = [(1, 1), (1, 8), (7, 8), (7, 4), (4, 4)]
    for _ in range(turns):
        points = [(c, 9 - r) for r, c in points]
    panels = []
    for index in (0, 2):
        tip = points[index]
        previous, following = (points[index - 1], tip) if index else (tip, points[1])
        delta = (following[0] - previous[0], following[1] - previous[1])
        panel = [[0] * 10 for _ in range(10)]
        for r, c in gen._arrow_cells(tip, delta) + points[index + 1:]:
            panel[r][c] = 2
        panels.append(panel)
    grid = [left + [5] + right for left, right in zip(*panels)]
    # Independently construct the expected final orientation from the route.
    dr, dc = points[-1][0] - points[-2][0], points[-1][1] - points[-2][1]
    r, c = points[-1]
    tip = (r, c)
    if dr < 0:
        arrow = [tip, (r + 1, c - 1), (r + 1, c + 1)]
        heading = "up"
    elif dc > 0:
        arrow = [tip, (r - 1, c - 1), (r + 1, c - 1)]
        heading = "right"
    elif dr > 0:
        arrow = [tip, (r - 1, c - 1), (r - 1, c + 1)]
        heading = "down"
    else:
        arrow = [tip, (r - 1, c + 1), (r + 1, c + 1)]
        heading = "left"
    expected = [[0] * 10 for _ in range(10)]
    for r, c in arrow:
        expected[r][c] = 2
    return {"input": grid, "expected": expected, "heading": heading,
            "route": [list(p) for p in points]}


def candidate(live):
    gen = generator()
    training = []
    for difficulty in ("easy", "medium", "hard"):
        pair = gen.generate_task(0, difficulty=difficulty)["train"][0]
        training.append({"input": pair["input"], "output": execute(live, pair["input"])})
    queries = []
    for turns in range(4):
        case = direction_case(turns)
        queries.append({"input": case["input"], "output": execute(live, case["input"])})
    return {
        "task_id": gen.TASK_ID,
        "source": "custom",
        "title": "Oriented cursor follows the remaining aligned waypoints",
        "difficulty": "medium",
        "skills": ["path_tracing", "orientation", "sequential_reasoning"],
        "written_solution": "Select the panel after the last full-height separator. Identify the three-cell cursor tip. Repeatedly consume the unique remaining waypoint sharing its row or column. Render a clean panel with the cursor at the final waypoint, oriented along the final leg. Earlier panels are context and do not influence this variant's output.",
        "train": training,
        "test": queries,
        "program_solution": (HOME / "reference.rkt").read_text(),
        "solution_language": "racket",
        "needs_conversion": False,
        "content_hash": gen.TASK_ID,
        "slug": "oriented_cursor_follows_remaining_aligned_waypoints",
        "parent_hash": "5545f144",
        "parent_reason": "semantic_variant_inspired_by_supplied_evaluation_task",
        "reference_evidence": "generators/generic_waypoint_route_gen1/evidence/canonical-reference/manifest.json",
    }


def registered_candidate():
    """Read this tree's registered row, including evidence-free test runtimes."""
    ledger = canonical_path(find_root(__file__))
    task_id = generator().TASK_ID
    matches = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == task_id:
                    matches.append(row)
    assert len(matches) == 1, "expected one registered canonical row for this semantic variant"
    return matches[0]


def validate(live):
    gen = generator()
    program = (HOME / "reference.rkt").read_text()
    assert program == gen.PROGRAM, "standalone reference differs from existing PROGRAM"
    cases = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            task = gen.generate_task(seed, difficulty=difficulty)
            assert gen.self_check_task(task) == []
            for index, pair in enumerate(task["train"] + task["test"]):
                assert gen.strict_canonical_like(pair["input"]) == []
                output = execute(live, pair["input"])
                assert output == pair["output"] == gen._apply(pair["input"])
                cases.append({"difficulty": difficulty, "seed": seed, "pair_index": index,
                              "input_sha256": digest(pair["input"]),
                              "output_sha256": digest(output)})
    directions = []
    for turns in range(4):
        case = direction_case(turns)
        assert gen.strict_canonical_like(case["input"]) == []
        output = execute(live, case["input"])
        assert output == case["expected"] == gen._apply(case["input"])
        directions.append({"heading": case["heading"], "route": case["route"],
                           "input_sha256": digest(case["input"]),
                           "output_sha256": digest(output)})
    # Explicitly preserve, rather than silently repair, the known dead context.
    case = direction_case(0)
    erased = copy.deepcopy(case["input"])
    for row in erased:
        row[:10] = [0] * 10
    original_output = execute(live, case["input"])
    erased_output = execute(live, erased)
    assert original_output == erased_output
    return {"generated_cases": cases, "direction_witnesses": directions,
            "dead_context_probe": {"status": "reproduced_unresolved",
                "original_input_sha256": digest(case["input"]),
                "erased_input_sha256": digest(erased),
                "same_output_sha256": digest(erased_output),
                "erased_input_validator_findings": gen.strict_canonical_like(erased)},
            "racket_evaluations": len(cases) + len(directions) + 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-candidate", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    path = HOME / "evidence/canonical-reference/canonical-record.json"
    with executor() as live:
        checks = validate(live)
        row = candidate(live)
        if args.write_candidate:
            path.write_text(json.dumps(row, indent=2) + "\n")
        else:
            assert registered_candidate() == row
        receipt = {"schema": "arcpuzzles-task-reference-verification-v1",
            "task_id": generator().TASK_ID,
            "status": "passed",
            "basis": "independently_executed_real_racket",
            "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
            "program_sha256": hashlib.sha256((HOME / "reference.rkt").read_bytes()).hexdigest(),
            "rule_hash": generator().RULE_HASH,
            "canonical_record_sha256": hashlib.sha256((json.dumps(row, indent=2) + "\n").encode()).hexdigest(),
            "canonical_pairs": {"train": len(row["train"]), "test": len(row["test"]),
                "labels": "executed_through_racket", "distinct_inputs": 7},
            "racket_evaluations": checks.pop("racket_evaluations") + 7,
            "runtime": live.runtime_identity,
            "checks": checks,
            "scope": "Bounded reference parity and four sequential orientation witnesses; no original-task solution, semantic approval, parameter API or training admission.",
            "command": [sys.executable, str(Path(__file__).relative_to(ROOT)), *sys.argv[1:]]}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "racket_evaluations": receipt["racket_evaluations"],
                      "canonical_pairs": receipt["canonical_pairs"], "rule_hash": receipt["rule_hash"]}))


if __name__ == "__main__":
    main()
