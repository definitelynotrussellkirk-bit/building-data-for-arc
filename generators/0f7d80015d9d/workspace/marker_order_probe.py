#!/usr/bin/env python3
"""Source-bound Racket probe for the marker-order teaching repair.

This is a reusable, focused reviewer tool rather than a production interface. It
executes the exact canonical Racket rule on official pairs, a fresh four-profile
lesson, a width-three repaired witness, and lawful edge-contact scenes. It also
checks that the audited ``red_col < cyan_col`` shortcut still fits every official
pair but is refuted by the generated lesson.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for dependency in (REPO, REPO / "shared" / "runtime"):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import strip_rule_wrapper  # noqa: E402
from reviewer_support import (  # noqa: E402
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "0f7d80015d9d"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_program(root: Path) -> str:
    matches = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical record, found {len(matches)}")
    return matches[0]


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _application(program: str, grid: list[list[int]]) -> str:
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("canonical program is not a lambda rule")
    return f"({body} {_grid_literal(grid)})"


def _find_case(generator: Any, predicate, *, profile: str) -> tuple[int, list[list[int]]]:
    for seed in range(2048):
        grid = generator.generate(
            seed,
            3,
            grid_h=7 if profile == "right_same_side" else 9,
            grid_w=7 if profile == "right_same_side" else 9,
            rect_aspect="tall" if profile == "right_same_side" else "wide",
            scene_profile=profile,
        )
        facts = generator._analyze(grid)
        if not facts["errors"] and predicate(facts):
            return seed, grid
    raise RuntimeError(f"could not construct focused case for {profile}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=731)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    program = _canonical_program(root)
    official = canonical_pairs(TASK_ID, root=root)

    cases: list[dict[str, Any]] = []
    for index, pair in enumerate(official):
        cases.append(
            {
                "name": f"canonical-{pair['split']}-{pair['pair_index']}",
                "kind": "canonical",
                "input": pair["input"],
                "expected": pair["output"],
            }
        )

    demos = []
    for index, profile in enumerate(generator.SCHEDULE_PROFILES):
        grid = generator.generate(
            args.seed,
            index,
            grid_h=11,
            grid_w=11,
            rect_aspect="wide",
            scene_profile=profile,
        )
        output = generator.rule_mirror(grid)
        demos.append({"input": grid, "output": output})
        cases.append(
            {
                "name": f"lesson-{profile}",
                "kind": "generated_lesson",
                "profile": profile,
                "input": grid,
                "expected": output,
            }
        )

    query = generator.generate(
        args.seed,
        4,
        grid_h=13,
        grid_w=13,
        rect_aspect="tall",
        scene_profile="right_opposite",
    )
    lesson_errors = generator.lesson_identifiable(demos, {"input": query})
    if lesson_errors:
        raise SystemExit(f"fresh lesson is not identifiable: {lesson_errors}")

    width_seed, width_three = _find_case(
        generator,
        lambda facts: facts["rect_w"] == 3
        and facts["red"][1] == facts["midpoint"] < facts["cyan"][1],
        profile="right_same_side",
    )
    cases.append(
        {
            "name": "width-three-marker-order-witness",
            "kind": "boundary",
            "profile": "right_same_side",
            "seed": width_seed,
            "input": width_three,
            "expected": generator.rule_mirror(width_three),
        }
    )

    left_seed, left_edge = _find_case(
        generator,
        lambda facts: facts["rect"][2] == 0,
        profile="left_opposite",
    )
    right_seed, right_edge = _find_case(
        generator,
        lambda facts: facts["rect"][3] == facts["width"] - 1,
        profile="right_opposite",
    )
    for name, seed, profile, grid in (
        ("left-edge-nondestination-contact", left_seed, "left_opposite", left_edge),
        ("right-edge-nondestination-contact", right_seed, "right_opposite", right_edge),
    ):
        cases.append(
            {
                "name": name,
                "kind": "boundary",
                "profile": profile,
                "seed": seed,
                "input": grid,
                "expected": generator.rule_mirror(grid),
            }
        )

    shortcut = generator.CANONICAL_SHORTCUTS["red_left_of_cyan"]
    if not all(shortcut(pair["input"]) == pair["output"] for pair in official):
        raise SystemExit("marker-order shortcut no longer fits every canonical pair")

    executions = []
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        runtime_identity = bridge.runtime_identity
        for case in cases:
            observed = bridge.eval_text(_application(program, case["input"]))
            if observed != case["expected"]:
                raise SystemExit(f"Racket mismatch for {case['name']}")
            facts = generator._analyze(case["input"])
            rival_output = shortcut(case["input"])
            executions.append(
                {
                    "name": case["name"],
                    "kind": case["kind"],
                    "profile": facts.get("scene_profile"),
                    "rect": facts.get("rect"),
                    "rect_w": facts.get("rect_w"),
                    "red": facts.get("red"),
                    "cyan": facts.get("cyan"),
                    "midpoint": facts.get("midpoint"),
                    "racket_matches_expected": True,
                    "marker_order_rival_matches": rival_output == case["expected"],
                }
            )

    witness_rows = [
        row
        for row in executions
        if row["name"] in {"lesson-right_same_side", "width-three-marker-order-witness"}
    ]
    if not witness_rows or any(row["marker_order_rival_matches"] for row in witness_rows):
        raise SystemExit("repaired same-side witnesses did not refute marker ordering")

    report = {
        "schema": "0f7d80015d9d-marker-order-racket-probe-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "generator_source": str(source_path),
        "generator_sha256": source_sha,
        "canonical_program_sha256": _sha256(program.encode()),
        "declared_rule_hash": generator.RULE_HASH,
        "lesson_seed": args.seed,
        "lesson_identifiable_errors": lesson_errors,
        "counts": {
            "canonical_pairs": len(official),
            "generated_lesson_pairs": len(demos),
            "boundary_pairs": 3,
            "racket_executions": len(executions),
        },
        "canonical_shortcut": {
            "name": "red_left_of_cyan",
            "fits_all_canonical_pairs": True,
            "refuted_by_repaired_lesson": True,
            "refuted_at_width_three": True,
        },
        "racket_runtime": runtime_identity,
        "executions": executions,
        "limitations": [
            "This is a focused finite probe, not a full production battery.",
            "The named shortcut is one audited plausible rival, not every possible solver.",
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "out": str(out), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
