"""Source-bound protected-Racket ambiguity probe for optional peer 0281fbec1cf2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

TASK_ID = "0281fbec1cf2"
EXPECTED_SOURCE_SHA256 = "074f2bad074d925d9b39b7e71a7c743031c47406a85c4893e7020de521c55bc9"
SEED = 54
SOURCE_FILTER = "(and (not (zero? v)) (!= v 2))"
RIVAL_FILTER = "(= v 3)"


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def canonical_program(root: Path) -> str:
    programs = {
        json.loads(line)["program_solution"]
        for line in (root / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("expected one exact canonical program")
    return programs.pop()


def run(output: Path) -> dict:
    root = Path.cwd().resolve()
    module, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"peer source differs: {source_sha256}")
    canonical = canonical_program(root)
    if canonical.count(SOURCE_FILTER) != 1:
        raise ValueError("canonical marker predicate changed")
    rival_program = canonical.replace(SOURCE_FILTER, RIVAL_FILTER)
    inputs = [module.generate(SEED, index) for index in range(4)]
    runtime = root / "shared/runtime"
    cases = []
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for index, grid in enumerate(inputs):
                reference = apply(canonical, grid)
                rival = apply(rival_program, grid)
                facts = module._analysis(grid)["facts"]
                cases.append({
                    "role": "demonstration" if index < 3 else "query",
                    "sample_index": index,
                    "shape": [len(grid), len(grid[0])],
                    "scene_profile": module.observe_overrides(grid)["scene_profile"],
                    "marker_colors": sorted(facts["marker_colors"]),
                    "input": grid,
                    "reference_output": reference,
                    "rival_output": rival,
                    "different_cells": changed_cells(reference, rival),
                })
        finally:
            bridge.close()

    if [row["marker_colors"] for row in cases] != [[3], [3], [3], [4]]:
        raise AssertionError("retained color schedule changed")
    if any(row["different_cells"] for row in cases[:3]):
        raise AssertionError("rival no longer fits all visible demonstrations")
    if cases[3]["different_cells"] <= 0:
        raise AssertionError("rival no longer disagrees on the query")

    result = {
        "schema": "arcpuzzles-optional-peer-adversarial-probe-v1",
        "status": "finding",
        "task_id": TASK_ID,
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
        },
        "seed": SEED,
        "visible_demonstration_indices": [0, 1, 2],
        "hidden_query_index": 3,
        "reference_program_sha256": sha_text(canonical),
        "rival": {
            "name": "only literal color 3 blocks rays",
            "program": rival_program,
            "program_sha256": sha_text(rival_program),
            "mechanism": (
                "Treat only color-3 markers as blockers instead of every nonzero non-red marker."
            ),
        },
        "racket": identity,
        "cases": cases,
        "finding": (
            "The first three consecutive generated samples use only color-3 markers, so the "
            "color-specific rival exactly matches every visible output. The fourth uses color 4; "
            "the rival incorrectly extends nine red cells through the blocked lanes."
        ),
        "suggested_repair": (
            "Schedule at least two blocker colors inside every visible lesson prefix, retaining "
            "the same lane geometry where possible so color irrelevance is the only changed fact."
        ),
        "limits": (
            "One source-bound seed and one executable rival; this establishes a concrete "
            "ambiguity, not a complete audit of the optional peer. No source edit was made."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({
        "status": result["status"],
        "task_id": result["task_id"],
        "demo_differences": [row["different_cells"] for row in result["cases"][:3]],
        "query_difference": result["cases"][3]["different_cells"],
        "demo_marker_colors": [row["marker_colors"] for row in result["cases"][:3]],
        "query_marker_colors": result["cases"][3]["marker_colors"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
