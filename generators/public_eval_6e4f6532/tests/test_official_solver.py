from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]


def _load_solver():
    path = TASK_DIR / "workspace/parametric/family.py"
    assert path.exists(), "workspace/parametric/family.py missing"
    spec = importlib.util.spec_from_file_location("public_eval_6e4f6532_solver", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _official_pairs():
    challenges = json.loads((REPO / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())
    solutions = json.loads((REPO / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())
    task = challenges["6e4f6532"]
    pairs = [("train", i, p["input"], p["output"]) for i, p in enumerate(task["train"])]
    pairs.extend(("test", i, p["input"], solutions["6e4f6532"][i]) for i, p in enumerate(task["test"]))
    return pairs


def test_solver_matches_every_official_label():
    solver = _load_solver()
    failures = []
    for split, index, grid, expected in _official_pairs():
        actual = solver.solve_grid(grid)
        if actual != expected:
            failures.append((split, index, actual, expected))
    assert failures == []


def test_away_orientation_is_total_and_changes_object_placement():
    solver = _load_solver()
    _, _, grid, _ = _official_pairs()[0]
    toward = solver.solve_grid(grid)
    away = solver.solve_grid(grid, "away")
    assert away != toward
    assert len(away) == len(grid) and all(len(row) == len(grid[0]) for row in away)
    # The alternate is total on the canonical grammar, though official scenes may
    # deliberately place the opposite-facing stamp against a guide and overwrite it.
