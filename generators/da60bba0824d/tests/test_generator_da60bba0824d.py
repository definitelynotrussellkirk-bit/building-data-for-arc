from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "da60bba0824d"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def test_rule_hash_and_declared_axes_are_current():
    assert gen.RULE_HASH == "881e1dbb1e82"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_motifs"}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_full_declared_override_boundaries_are_honored(difficulty):
    cases = [
        {"grid_h": 7, "grid_w": 9, "n_motifs": 2},
        {"grid_h": 12, "grid_w": 14, "n_motifs": 4},
        {"grid_h": 7, "grid_w": 14, "n_motifs": 4},
        {"grid_h": 12, "grid_w": 9, "n_motifs": 2},
    ]
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(
            93811,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []


def test_removed_inert_axes_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", palette_kind="warm")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", texture="varied")


def test_every_semantic_schedule_branch_is_realized_in_each_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(317, index, difficulty=difficulty) for index in range(7)]
        assert gen.SEMANTIC_WITNESSES["singleton_decoy"](grids[0])
        assert gen.SEMANTIC_WITNESSES["largest_first"](grids[1])
        assert gen.SEMANTIC_WITNESSES["largest_last"](grids[2])
        assert gen.SEMANTIC_WITNESSES["diagonal_only_contact"](grids[3])
        assert gen.SEMANTIC_WITNESSES["bbox_area_decoy"](grids[4])
        assert gen.SEMANTIC_WITNESSES["edge_largest"](grids[5])
        assert gen.SEMANTIC_WITNESSES["interior_largest"](grids[6])


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(101, 0, difficulty="medium")

    wrong_color = copy.deepcopy(base)
    r, c = next(
        (r, c)
        for r, row in enumerate(wrong_color)
        for c, value in enumerate(row)
        if value == 3
    )
    wrong_color[r][c] = 8
    assert any("palette" in error for error in gen.self_check(wrong_color))

    single = [[0] * 10 for _ in range(8)]
    single[2][2] = single[2][3] = single[3][2] = 3
    assert any("2..4" in error for error in gen.self_check(single))

    tied = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 1), (1, 2), (2, 1), (5, 7), (5, 8), (6, 8)):
        tied[r][c] = 3
    assert any("pairwise distinct" in error for error in gen.self_check(tied))

    too_large = [[0] * 12 for _ in range(9)]
    for r in range(3):
        for c in range(3):
            too_large[r][c] = 3
    too_large[6][9] = 3
    assert any("1..8" in error for error in gen.self_check(too_large))

    ragged = copy.deepcopy(base)
    ragged[-1].pop()
    assert gen.self_check(ragged) == ["grid must be rectangular"]


def test_all_canonical_inputs_are_accepted():
    found = 0
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                pairs = row[split] if isinstance(row[split], list) else [row[split]]
                for pair in pairs:
                    found += 1
                    assert gen.self_check(pair["input"]) == []
                    assert gen.strict_canonical_like(pair["input"]) == []
    assert found == 4


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    third = gen.generate(77, 5, difficulty="hard")
    assert third == second
