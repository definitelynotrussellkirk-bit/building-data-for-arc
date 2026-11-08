"""Show that ordinary lessons never distinguish degree-1 endpoints from two extrema."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

TASK = "af13a88bfcbe"
GENERATOR = REPO / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_endpoint_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def degree_one_rule(grid):
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            neighbors = sum(
                0 <= rr < h and 0 <= cc < w and grid[rr][cc] == value
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            )
            if neighbors == 1:
                output[r][c] = 8
    return output


def two_extrema_per_component(grid):
    """Plausible shortcut: every colored object has exactly two endpoints."""
    output = [row[:] for row in grid]
    for color in sorted({value for row in grid for value in row if value != 0}):
        for component in components(grid, color):
            if len(component) >= 2:
                for r, c in (min(component), max(component)):
                    output[r][c] = 8
    return output


def main():
    gen = load_generator()
    canonical = canonical_pairs(TASK, root=REPO, labeled_only=True)
    assert all(degree_one_rule(pair["input"]) == pair["output"] for pair in canonical)
    assert all(two_extrema_per_component(pair["input"]) == pair["output"] for pair in canonical)

    counts = {}
    for band in ("easy", "medium", "hard"):
        matches = 0
        for index in range(1000):
            grid = gen.generate(200_000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            matches += degree_one_rule(grid) == two_extrema_per_component(grid)
        counts[band] = {"samples": 1000, "two_extrema_rival_matches": matches}

    counterexample = gen.generate(0, 0, texture="dense_branching")
    intended = degree_one_rule(counterexample)
    rival = two_extrema_per_component(counterexample)
    assert gen.self_check(counterexample) == []
    assert intended != rival

    report = {
        "schema": "af13a88bfcbe-audit-v1",
        "finding": "The canonical pairs and 3,000 ordinary draws are all explained by the shortcut 'mark exactly two extrema per component'; the generator's own T-junction fixture refutes it but is never sampled by default.",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "canonical_pairs_checked": len(canonical),
        "canonical_rival_matches": len(canonical),
        "ordinary_draw_census": counts,
        "counterexample": {
            "source": "generate(seed=0, sample_index=0, texture='dense_branching')",
            "input": counterexample,
            "authority_python": intended,
            "two_extrema_rival": rival,
            "differing_cells": [
                [r, c]
                for r in range(len(counterexample))
                for c in range(len(counterexample[0]))
                if intended[r][c] != rival[r][c]
            ],
            "self_check": gen.self_check(counterexample),
        },
        "racket_parity": "pending apply output",
    }
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(__file__).with_name("report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(__file__).with_name("inputs.json").write_text(json.dumps({"inputs": [counterexample]}, indent=2) + "\n")
    print(json.dumps({"census": counts, "counterexample_differing_cells": report["counterexample"]["differing_cells"]}, indent=2))


if __name__ == "__main__":
    main()
