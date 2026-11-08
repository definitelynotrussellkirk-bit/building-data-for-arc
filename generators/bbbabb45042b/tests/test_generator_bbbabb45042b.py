from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.bbbabb45042b import generator as gen


def _canonical_inputs():
    path = Path(__file__).parents[1] / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        return [[[int(cell) for cell in line] for line in pair["input"]] for pair in row["train"] + test]
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_pass_structural_checker():
    assert len(_canonical_inputs()) == 3
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_exact_axes_are_observable_across_bands():
    overrides = {
        "grid_dims": "9x11",
        "template_kind": "t_down",
        "n_anchors": 3,
        "n_red_distractors": 1,
    }
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(91, 7, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_default_four_pair_schedule_exercises_semantic_branches():
    for seed in range(12):
        grids = [gen.generate(seed, i, difficulty="medium") for i in range(4)]
        observations = [gen.observe_overrides(grid) for grid in grids]
        kinds = [obs["template_kind"] for obs in observations]
        assert any((0, 0) in gen.TEMPLATES[kind] for kind in kinds)
        assert any((0, 0) not in gen.TEMPLATES[kind] for kind in kinds)
        assert sum(obs["n_red_distractors"] for obs in observations) == 1


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8128)
    before = random.getstate()
    first = gen.generate(123, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(123, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_minimal_impostors():
    valid = gen.generate(
        8,
        3,
        difficulty="medium",
        grid_dims="10x12",
        template_kind="l_bottom",
        n_anchors=2,
        n_red_distractors=0,
    )
    assert gen.self_check(valid) == []

    all_background = [[0] * 12 for _ in range(10)]
    full_red = [[2] * 12 for _ in range(10)]
    singleton_red = [[0] * 12 for _ in range(10)]
    singleton_red[1][1] = 2
    solid_square = [[0] * 12 for _ in range(10)]
    for r in (1, 2):
        for c in (1, 2):
            solid_square[r][c] = 2
    solid_square[6][7] = 1
    short_line = [[0] * 12 for _ in range(10)]
    for c in (1, 2, 3):
        short_line[1][c] = 2
    short_line[6][7] = 1

    for impostor in (all_background, full_red, singleton_red, solid_square, short_line):
        assert gen.self_check(impostor)

    adjacent_anchor = copy.deepcopy(valid)
    red = max(gen._components_of_color(adjacent_anchor, 2), key=len)
    rr, cc = red[0]
    for dr, dc in gen._CARDINAL:
        ar, ac = rr + dr, cc + dc
        if 0 <= ar < len(valid) and 0 <= ac < len(valid[0]) and adjacent_anchor[ar][ac] == 0:
            adjacent_anchor[ar][ac] = 1
            break
    assert any("4-touch" in err or "overlap" in err for err in gen.self_check(adjacent_anchor))

    out_of_bounds = copy.deepcopy(valid)
    for r, row in enumerate(out_of_bounds):
        for c, value in enumerate(row):
            if value == 1:
                out_of_bounds[r][c] = 0
    out_of_bounds[-1][-1] = 1
    assert any("cannot fit" in err for err in gen.self_check(out_of_bounds))
