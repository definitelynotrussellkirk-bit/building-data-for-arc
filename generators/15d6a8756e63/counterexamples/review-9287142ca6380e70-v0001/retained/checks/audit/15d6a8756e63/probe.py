#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "15d6a8756e63"
SEED = 112390243908552922


def canonical_program(root: Path) -> str:
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.append(row["program_solution"])
    unique = set(programs)
    if len(unique) != 1:
        raise RuntimeError(f"expected one unique canonical program, found {len(unique)}")
    return unique.pop()


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    bridge.define_grid("audit_input", grid)
    expression = f"({body} audit_input)" if body.lstrip().startswith("(lambda") else body
    return bridge.eval_text(expression)


def global_overlay_rival(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    return [
        [grid[r % h][c % w] if grid[r % h][c % w] else 8 for c in range(2 * w)]
        for r in range(2 * h)
    ]


def blank_columns(grid: list[list[int]]) -> list[int]:
    return [c for c in range(len(grid[0])) if all(row[c] == 0 for row in grid)]


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    program = canonical_program(root)
    all_active = generator.generate(
        SEED,
        0,
        difficulty="medium",
        grid_h=4,
        grid_w=4,
        texture="all_active_cols",
    )
    with RacketBridge() as bridge:
        all_active_output = execute(bridge, program, all_active)
        normal = None
        normal_output = None
        normal_seed = None
        for seed in range(128):
            candidate = generator.generate(seed, 0, difficulty="medium")
            if blank_columns(candidate):
                output = execute(bridge, program, candidate)
                if output != global_overlay_rival(candidate):
                    normal, normal_output, normal_seed = candidate, output, seed
                    break
    if normal is None or normal_output is None or normal_seed is None:
        raise RuntimeError("could not find a normal blank-column witness")

    rival_all_active = global_overlay_rival(all_active)
    rival_normal = global_overlay_rival(normal)
    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "finding": "all_active_cols removes the only distinction between selective active-column overlay and global background overlay",
        "all_active_case": {
            "seed": SEED,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {"grid_h": 4, "grid_w": 4, "texture": "all_active_cols"},
            "input": all_active,
            "blank_columns": blank_columns(all_active),
            "self_check": generator.self_check(all_active),
            "canonical_output": all_active_output,
            "global_overlay_rival_output": rival_all_active,
            "outputs_equal": all_active_output == rival_all_active,
        },
        "ordinary_distinguishing_case": {
            "seed": normal_seed,
            "sample_index": 0,
            "difficulty": "medium",
            "input": normal,
            "blank_columns": blank_columns(normal),
            "canonical_output": normal_output,
            "global_overlay_rival_output": rival_normal,
            "outputs_equal": normal_output == rival_normal,
        },
        "contract_reproducers": {},
    }
    for name, kwargs in {
        "declared_grid_h_7_rejected": {"grid_h": 7, "grid_w": 7},
        "declared_palette_size_1_rejected": {"palette_size": 1},
    }.items():
        try:
            generator.generate(0, 0, difficulty="medium", **kwargs)
        except Exception as exc:  # evidence intentionally records the public error
            evidence["contract_reproducers"][name] = {
                "kwargs": kwargs,
                "exception_type": type(exc).__name__,
                "message": str(exc),
            }
        else:
            evidence["contract_reproducers"][name] = {"kwargs": kwargs, "accepted": True}

    if blank_columns(all_active) or generator.self_check(all_active) != [] or all_active_output != rival_all_active:
        raise AssertionError("all-active shortcut was not reproduced")
    if not blank_columns(normal) or normal_output == rival_normal:
        raise AssertionError("ordinary distinguishing control failed")

    out = Path(__file__).with_name("evidence.json")
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "reproduced",
        "evidence": str(out),
        "source_sha256": source_sha,
        "all_active_matches_rival": True,
        "ordinary_case_refutes_rival": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
