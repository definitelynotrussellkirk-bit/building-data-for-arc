from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

TASK = "90870ec1dd92"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_FILES = [
    ROOT / "data/base/solutions/training/e50d258f__90870ec1dd92.json",
    ROOT / "data/base/solutions/augmented/e50d258f__80e0cff19bf0.json",
]


def _canonical_pairs(row):
    visible = row["visible_context"]
    pairs = list(visible["train"])
    expected = row["verification"]["expected_test_outputs"]
    pairs.extend(
        {"input": item["input"], "output": output}
        for item, output in zip(visible["test_inputs"], expected)
    )
    return pairs


def _canonical_inputs():
    grids = []
    for path in AUTHORITY_FILES:
        row = json.loads(path.read_text())
        grids.extend(pair["input"] for pair in _canonical_pairs(row))
    return grids


def _component_cells(grid):
    return [list(rect["cells"]) for rect in gen._analyze_scene(grid)["rectangles"]]


def test_all_canonical_inputs_pass_and_mirror_outputs():
    reviewed = 0
    for path in AUTHORITY_FILES:
        row = json.loads(path.read_text())
        for pair in _canonical_pairs(row):
            assert gen.self_check(pair["input"]) == []
            assert gen.rule_mirror(pair["input"]) == pair["output"]
            reviewed += 1
    assert reviewed == 8


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_overrides_are_observable_at_boundaries(band):
    for n_clusters in (2, 3):
        for winner_red_count in (3, 6):
            for red_gap in (1, 2):
                for winner_position in gen._POSITIONS:
                    grid = gen.generate(
                        991,
                        2,
                        difficulty=band,
                        n_clusters=n_clusters,
                        winner_red_count=winner_red_count,
                        red_gap=red_gap,
                        winner_position=winner_position,
                    )
                    assert gen.observe_overrides(grid) == {
                        "n_clusters": n_clusters,
                        "winner_red_count": winner_red_count,
                        "red_gap": red_gap,
                        "winner_position": winner_position,
                    }
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, difficulty=band, texture="ignored")


def test_self_check_rejects_four_task_specific_impostors():
    base = gen.generate(222, 2, difficulty="medium")
    scene = gen._analyze_scene(base)

    # 1. Tie the top two red counts while retaining rectangular geometry.
    tie = copy.deepcopy(base)
    winner = scene["rectangles"][scene["winner"]]
    runner = sorted(scene["rectangles"], key=lambda r: r["red"], reverse=True)[1]
    needed = winner["red"] - runner["red"]
    for r, c in [cell for cell in runner["cells"] if tie[cell[0]][cell[1]] != 2][:needed]:
        tie[r][c] = 2
    assert any("red counts" in error or "largest red" in error for error in gen.self_check(tie))

    # 2. Hollow one rectangle so its nonzero cells no longer fill its bbox.
    hollow = copy.deepcopy(base)
    rect = scene["rectangles"][0]
    r0, c0, r1, c1 = rect["bbox"]
    hollow[(r0 + r1) // 2][(c0 + c1) // 2] = 0
    assert any("fill its bounding rectangle" in error for error in gen.self_check(hollow))

    # 3. Add a diagonal bridge so separated objects merge under 8-connectivity.
    merged = copy.deepcopy(base)
    rects = list(scene["rectangles"])
    a, b = rects[0], rects[1]
    ar, ac = a["cells"][0]
    br, bc = b["cells"][0]
    # Draw a king-move path between existing object cells.
    r, c = ar, ac
    while (r, c) != (br, bc):
        r += (br > r) - (br < r)
        c += (bc > c) - (bc < c)
        if merged[r][c] == 0:
            merged[r][c] = 1
    assert gen.self_check(merged)

    # 4. Remove color 8 from one object while preserving its solid rectangle.
    missing_color = copy.deepcopy(base)
    victim = scene["rectangles"][0]
    for r, c in victim["cells"]:
        if missing_color[r][c] == 8:
            missing_color[r][c] = 1
    assert any("both colors 1 and 8" in error for error in gen.self_check(missing_color))


def test_three_demo_schedule_refutes_all_declared_shortcuts():
    for band in ("easy", "medium", "hard"):
        for lesson_seed in range(12):
            demos = []
            for sample_index in range(3):
                grid = gen.generate(10000 + lesson_seed, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(20000 + lesson_seed, 3, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_replay_freshness_and_global_rng_are_preserved():
    import random

    state = random.getstate()
    first = gen.generate(123456, 1, difficulty="hard")
    second = gen.generate(123456, 1, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 99
    third = gen.generate(123456, 1, difficulty="hard")
    assert third == second
    assert random.getstate() == state
