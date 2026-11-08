"""Source-bound protected-Racket ambiguity probe for optional peer a98c887acf8f."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

TASK_ID = "a98c887acf8f"
EXPECTED_SOURCE_SHA256 = "ab2cbdc50ce67dbd816e285403e8d105e39279e5261e1ed67ae6a61c63eb0eef"
SEED = 12
RIVAL = """(rule! (let ((dummy 0)) (define (points-of grid color) (sort (find-color grid color) cell<)) (define (distance p q) (+ (abs (- (first p) (first q))) (abs (- (second p) (second q))))) (define (distance-to-set p cells) (apply min (map (lambda (q) (distance p q)) cells))) (define (cells-within grid centers radius) (filter (lambda (p) (<= (distance-to-set p centers) radius)) (grid-positions grid))) (define (mask-intersection a b) (filter (lambda (p) (member p b)) a)) (let* ((a (points-of g 2)) (b (points-of g 3)) (pair-distances (apply append (map (lambda (p) (map (lambda (q) (distance p q)) b)) a))) (radius (/ (apply min pair-distances) 2)) (meet (mask-intersection (cells-within g a radius) (cells-within g b radius)))) (paint-cells (empty-grid (rows g) (cols g) 0) meet 8))))"""


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def minimum_distance(grid: list[list[int]]) -> int:
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    return min(abs(r - rr) + abs(c - cc) for r, c in red for rr, cc in green)


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def canonical_program(root: Path) -> str:
    for line in (root / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise ValueError("canonical task row missing")


def run(output: Path) -> dict:
    root = Path.cwd().resolve()
    module, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"peer source differs: {source_sha256}")
    canonical = canonical_program(root)
    inputs = [module.generate(SEED, index) for index in range(4)]
    runtime = root / "shared/runtime"
    cases = []
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for index, grid in enumerate(inputs):
                reference = apply(canonical, grid)
                rival = apply(RIVAL, grid)
                cases.append({
                    "role": "demonstration" if index < 3 else "query",
                    "sample_index": index,
                    "shape": [len(grid), len(grid[0])],
                    "minimum_set_distance": minimum_distance(grid),
                    "input": grid,
                    "reference_output": reference,
                    "rival_output": rival,
                    "different_cells": changed_cells(reference, rival),
                    "reference_cyan_cells": sum(value == 8 for row in reference for value in row),
                    "rival_cyan_cells": sum(value == 8 for row in rival for value in row),
                })
        finally:
            bridge.close()

    if [row["minimum_set_distance"] % 2 for row in cases] != [0, 0, 0, 1]:
        raise AssertionError("retained parity schedule changed")
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
            "name": "truncate minimum set distance before growing both neighborhoods",
            "program": RIVAL,
            "program_sha256": sha_text(RIVAL),
            "mechanism": (
                "Use integer radius floor(minimum red-green Manhattan distance / 2) once, "
                "instead of increasing radius until the neighborhoods first overlap."
            ),
        },
        "racket": identity,
        "cases": cases,
        "finding": (
            "The first three consecutive samples all have even minimum set distance, so the "
            "truncated-half rival exactly matches every visible label. The fourth sample has "
            "odd distance 15; the canonical search paints 17 cells while the rival paints none."
        ),
        "suggested_repair": (
            "Schedule both even and odd minimum-set-distance examples inside every visible "
            "lesson prefix, then retain this exact protected-Racket case as a regression."
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
        "query_reference_cells": result["cases"][3]["reference_cyan_cells"],
        "query_rival_cells": result["cases"][3]["rival_cyan_cells"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
