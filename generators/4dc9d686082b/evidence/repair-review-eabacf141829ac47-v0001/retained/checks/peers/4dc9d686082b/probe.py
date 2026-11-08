"""Source-pinned protected-Racket replay of the template/layout role-swap ambiguity."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "4dc9d686082b"
OLD_SHA256 = "2c1f903d81312bbd0683a8923d8bb67605709eeb869ed1c38b136b10451101da"
EXPECTED_NEW_SHA256 = "6d85299157e352c0b4a034e2667c683d95f1e48122a2865f10d3dcab19f9def0"
SEED = 37


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(program)} {_grid_literal(grid)})")


def _canonical_program(root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program; found {len(programs)}")
    return next(iter(programs))


def _swap_program(program: str) -> str:
    outer = "(layout-val (list-ref (list-ref layout lr) lc))"
    inner = "(let ((t (list-ref (list-ref tmpl tr) tc)))"
    if program.count(outer) != 1 or program.count(inner) != 1:
        raise ValueError("canonical source guard failed")
    return program.replace(
        outer, "(layout-val (list-ref (list-ref tmpl lr) lc))", 1
    ).replace(
        inner, "(let ((t (list-ref (list-ref layout tr) tc)))", 1
    )


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def main() -> int:
    root = find_root(Path.cwd())
    old_path = root.parent / ".review/baseline/repo/generators" / TASK_ID / "generator.py"
    current, current_path, current_sha = load_selected_generator(TASK_ID, root=root)
    if _sha(old_path) != OLD_SHA256:
        raise ValueError("baseline source drift")
    if current_sha != EXPECTED_NEW_SHA256:
        raise ValueError(f"current source drift: {current_sha}")
    old = _load(old_path, "_peer_4dc9d686082b_baseline")

    canonical = _canonical_program(root)
    swapped = _swap_program(canonical)
    old_grids = [old.generate(SEED, index) for index in range(5)]
    current_grids = [current.generate(SEED, index) for index in range(5)]

    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        old_cases = []
        for index, grid in enumerate(old_grids):
            label = _apply(bridge, canonical, grid)
            rival = _apply(bridge, swapped, grid)
            old_cases.append(
                {
                    "sample_index": index,
                    "role_swap_matches": label == rival,
                    "diff_cells": _diff_cells(label, rival),
                    "input": grid,
                    "canonical_output": label,
                    "role_swapped_output": rival,
                }
            )
        current_cases = []
        for index, grid in enumerate(current_grids):
            label = _apply(bridge, canonical, grid)
            rival = _apply(bridge, swapped, grid)
            current_cases.append(
                {
                    "sample_index": index,
                    "self_check": current.self_check(grid),
                    "role_swap_matches": label == rival,
                    "diff_cells": _diff_cells(label, rival),
                }
            )
    finally:
        bridge.close()

    stress_failures = []
    stress_inputs = 0
    for seed in range(512):
        for sample_index in range(5):
            grid = current.generate(seed, sample_index)
            stress_inputs += 1
            issues = current.self_check(grid)
            if issues:
                stress_failures.append(
                    {"seed": seed, "sample_index": sample_index, "issues": issues}
                )
                if len(stress_failures) >= 20:
                    break
        if len(stress_failures) >= 20:
            break

    old_demo_matches = [case["role_swap_matches"] for case in old_cases[:4]]
    old_query_disagrees = not old_cases[4]["role_swap_matches"]
    current_all_distinguish = all(
        not case["role_swap_matches"] and not case["self_check"]
        for case in current_cases
    )
    passed = (
        all(old_demo_matches)
        and old_query_disagrees
        and current_all_distinguish
        and not stress_failures
    )
    report = {
        "schema": "4dc9d686082b-role-swap-repair-v1",
        "status": "passed" if passed else "failed",
        "task_id": TASK_ID,
        "finding": (
            "The baseline seed-37 four-demo lesson admits a rule that swaps the "
            "template and layout roles; that rival disagrees on sample 4."
        ),
        "repair": (
            "Version 1.3.3 redraws until the canonical crop contains at least one "
            "cell distinguishing outer-layout/inner-template from the role swap, "
            "and self_check enforces the same condition."
        ),
        "source_binding": {
            "baseline_generator_sha256": OLD_SHA256,
            "current_generator_sha256": current_sha,
            "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "role_swap_program_sha256": hashlib.sha256(swapped.encode()).hexdigest(),
        },
        "old_lesson": {
            "seed": SEED,
            "demonstrations": 4,
            "query_sample_index": 4,
            "all_demos_fit_role_swap": all(old_demo_matches),
            "query_disagrees": old_query_disagrees,
            "cases": old_cases,
        },
        "repaired_seed_37": current_cases,
        "stress": {
            "seeds": [0, 511],
            "samples_per_seed": 5,
            "inputs": stress_inputs,
            "failures": stress_failures,
        },
        "racket": {
            key: identity.get(key)
            for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256")
            if key in identity
        },
        "limits": (
            "Finite source-pinned role-swap audit only; it does not establish "
            "universal lesson uniqueness against every possible rival."
        ),
    }
    out = root / "generators" / TASK_ID / "counterexamples" / "review-eabacf141829ac47" / "role-swap-repair.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "old_demo_matches": old_demo_matches,
                "old_query_diff_cells": old_cases[4]["diff_cells"],
                "current_seed37_all_distinguish": current_all_distinguish,
                "stress_inputs": stress_inputs,
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
