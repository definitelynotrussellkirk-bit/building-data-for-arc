"""Reproduce the 021ea70e8ed8 triple-column teaching ambiguity."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = next(parent for parent in HERE.parents if (parent / "repo").is_dir())
REPO = WORK / "repo"
TASK_ID = "021ea70e8ed8"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
EXPECTED_SOURCE_SHA256 = "308b4a6694158373974f7c170ace1953e39eaef79c87358687b26a2a60cc7053"

sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location("audit_021ea70e8ed8", GENERATOR_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def intended(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for col in range(len(grid[0])):
        occupied = [(row, grid[row][col]) for row in range(len(grid)) if grid[row][col] != 0]
        if len(occupied) == 2 and occupied[0][1] == occupied[1][1]:
            color = occupied[0][1]
            for row in range(occupied[0][0], occupied[1][0] + 1):
                out[row][col] = color
    return out


def rival(grid: list[list[int]]) -> list[list[int]]:
    """Fill first-to-last for >=2 endpoints when all endpoint colors agree."""
    out = [row[:] for row in grid]
    for col in range(len(grid[0])):
        occupied = [(row, grid[row][col]) for row in range(len(grid)) if grid[row][col] != 0]
        if len(occupied) >= 2 and len({color for _, color in occupied}) == 1:
            color = occupied[0][1]
            for row in range(occupied[0][0], occupied[-1][0] + 1):
                out[row][col] = color
    return out


def kind(grid: list[list[int]], col: int) -> str:
    occupied = [(row, grid[row][col]) for row in range(len(grid)) if grid[row][col] != 0]
    colors = {color for _, color in occupied}
    if not occupied:
        return "empty"
    if len(occupied) == 1:
        return "singleton"
    if len(occupied) == 2 and len(colors) == 1:
        return "pair_same"
    if len(occupied) == 2:
        return "pair_mixed"
    if len(occupied) == 3 and len(colors) == 1:
        return "triple_same"
    return f"other_{len(occupied)}_{len(colors)}"


def main() -> None:
    digest = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert digest == EXPECTED_SOURCE_SHA256, digest
    seed, start = 0, 9
    grids = [module.generate(seed, start + offset, difficulty=None) for offset in range(4)]
    intended_outputs = [intended(grid) for grid in grids]
    rival_outputs = [rival(grid) for grid in grids]
    assert all(rival_outputs[index] == intended_outputs[index] for index in range(3))
    assert rival_outputs[3] != intended_outputs[3]
    assert "triple_same" in [kind(grids[3], col) for col in range(len(grids[3][0]))]
    saved = json.loads((HERE.parent / "counterexample.json").read_text())
    assert [entry["input"] for entry in saved["demos"]] + [saved["query"]["input"]] == grids
    print("source hash:", digest)
    print("three demonstrations fit rival; query differs")


if __name__ == "__main__":
    main()
