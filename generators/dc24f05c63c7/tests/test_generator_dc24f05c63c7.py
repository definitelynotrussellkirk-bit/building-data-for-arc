from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "dc24f05c63c7"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK_ID)
    return list(row["train"]) + [row["test"]]


def test_canonical_inputs_and_outputs_match_rule_mirror():
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_observable():
    cases = [
        {"grid_h": 11, "grid_w": 15, "source_basis": 0, "target_basis": 7,
         "motif_quadrant": "pos_pos", "motif_kind": "diagonal_2"},
        {"grid_h": 16, "grid_w": 24, "source_basis": 7, "target_basis": 0,
         "motif_quadrant": "neg_neg", "motif_kind": "canonical_c"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(100 + index, index, difficulty="hard", **overrides)
        observed = gen.observe_overrides(grid)
        assert observed == overrides
        assert gen.self_check(grid) == []


def test_unknown_override_and_bad_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis="typo")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_every_four_sample_window_is_identifiable():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(500, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(501, start + 20, difficulty="hard")
        assert gen.lesson_identifiable(
            demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        ) == []


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(700, 2, difficulty="medium")
    info, errors = gen._analyse(base)
    assert errors == []

    impostors = []

    extra_color = copy.deepcopy(base)
    extra_color[0][0] = 9
    impostors.append(extra_color)

    mixed_quadrant = copy.deepcopy(base)
    r, c = info["motif_cells"][0]
    mixed_quadrant[r][c] = 0
    source = info["source_frame"]
    u, v = info["motif_uvs"][0]
    rr, cc = gen._glob(source[0], source[1], source[2], -u, v)
    if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and mixed_quadrant[rr][cc] == 0:
        mixed_quadrant[rr][cc] = 8
        impostors.append(mixed_quadrant)

    hidden_fill = copy.deepcopy(base)
    missing_uv = next(uv for uv in info["fill_uvs"] if uv not in info["motif_uvs"])
    rr, cc = gen._glob(info["source_frame"][0], info["source_frame"][1], info["source_frame"][2], *missing_uv)
    hidden_fill[rr][cc] = 8
    impostors.append(hidden_fill)

    occupied_target = copy.deepcopy(base)
    tr, tc = info["target_cells"][0]
    occupied_target[tr][tc] = 8
    impostors.append(occupied_target)

    broken_frame = copy.deepcopy(base)
    p3 = next((r, c) for r, row in enumerate(broken_frame) for c, value in enumerate(row) if value == 3)
    broken_frame[p3[0]][p3[1]] = 0
    broken_frame[0][0] = 3
    impostors.append(broken_frame)

    assert len(impostors) >= 4
    for grid in impostors:
        assert gen.self_check(grid), "malformed scene was accepted"


def test_replay_freshness_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="easy")
    middle = random.getstate()
    second = gen.generate(42, 9, difficulty="easy")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
