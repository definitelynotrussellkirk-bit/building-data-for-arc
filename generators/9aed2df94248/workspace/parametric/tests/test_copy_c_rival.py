"""A two-demo lesson must teach double application rather than copying C."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "adapter.py"
SPEC = importlib.util.spec_from_file_location("copy_c_rival_adapter", SOURCE)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def unchanged_third_panel(grid):
    columns = [c for c in range(len(grid[0])) if any(row[c] for row in grid)]
    runs = []
    for column in columns:
        if not runs or column != runs[-1][-1] + 1:
            runs.append([])
        runs[-1].append(column)
    assert len(runs) == 3
    left, right = runs[2][0], runs[2][-1]
    rows = [r for r, row in enumerate(grid) if any(row[left:right + 1])]
    return [row[left:right + 1] for row in grid[min(rows):max(rows) + 1]]


def test_seed_zero_twice_demos_reject_copy_c():
    episode = adapter.generate(0, {"transfer": "twice"}, demos=2)
    assert any(unchanged_third_panel(pair["input"]) != pair["output"]
               for pair in episode["train"])


def test_minimum_lessons_reject_copy_c_across_seeded_profiles():
    rotation_positions = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(40):
            episode = adapter.generate(seed, {"transfer": "twice"}, demos=2,
                                       difficulty=difficulty)
            distinguishes = [unchanged_third_panel(p["input"]) != p["output"]
                             for p in episode["train"]]
            assert any(distinguishes), (seed, difficulty)
            rotation_positions.add(distinguishes.index(True))
    assert rotation_positions == {0, 1}
