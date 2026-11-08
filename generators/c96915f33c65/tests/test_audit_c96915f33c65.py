from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def test_repeated_colors_expose_uniqueness_shortcut():
    rival = GEN.LESSON_COMPETITORS["globally_unique_color_only"]
    for band in ("easy", "medium", "hard"):
        pairs = []
        for i in range(12):
            grid = GEN.generate(9000, i, difficulty=band)
            assert GEN.self_check(grid) == []
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(9):
            demos = pairs[start:start+3]
            assert any(rival(p["input"]) != p["output"] for p in demos)
            assert GEN.lesson_identifiable(demos, pairs[start+3]) == []

def test_literal_repeated_seed_witness():
    grid = [[0]*9 for _ in range(7)]
    grid[2][2] = grid[4][6] = 4
    assert GEN.self_check(grid) == []
    out = GEN.rule_mirror(grid)
    assert sum(a != b for x,y in zip(grid,out) for a,b in zip(x,y)) == 8
    assert GEN.LESSON_COMPETITORS["globally_unique_color_only"](grid) == grid
