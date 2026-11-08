from __future__ import annotations

import copy
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
from puzzle_generators.per_puzzle.e797eb4ae5d6 import generator as gen


TASK_ID = "e797eb4ae5d6"


def _demo(grid):
    return {"input": grid, "output": gen._rule_mirror(grid)}


def test_rule_hash_is_pinned_to_selected_canonical_authority():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "865e9da6c30a"


def test_all_canonical_inputs_pass_structural_self_check():
    pairs = list(canonical_pairs(TASK_ID))
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []


def test_local_blockers_only_is_real_canonical_shortcut_and_generated_witness_kills_it():
    pairs = list(canonical_pairs(TASK_ID))
    assert all(
        gen._rival_local_blockers_only(pair["input"]) == pair["output"]
        for pair in pairs
    )

    witness = gen.generate(seed=91, sample_index=1, difficulty="medium")
    assert gen._witness_off_mask_global_switch(witness)
    true_out = gen._rule_mirror(witness)
    rival_out = gen._rival_local_blockers_only(witness)
    assert rival_out != true_out
    # The decisive difference is the disconnected lower bar: the true rule
    # suppresses it merely because an off-stencil blocker exists.
    seed = gen._seed_position(witness)
    assert seed is not None
    tail = [
        gen._absolute(seed, rel)
        for rel in gen._TAIL_RELS
        if gen._in_bounds(len(witness), len(witness[0]), gen._absolute(seed, rel))
    ]
    assert any(true_out[r][c] == 0 and rival_out[r][c] == 3 for r, c in tail)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_four_demo_window_is_identifiable(band):
    for start in range(8):
        grids = [gen.generate(seed=700 + start, sample_index=i, difficulty=band)
                 for i in range(start, start + 4)]
        demos = [_demo(grid) for grid in grids]
        query_grid = gen.generate(seed=700 + start, sample_index=start + 4, difficulty=band)
        query = _demo(query_grid)
        assert gen.lesson_identifiable(demos, query) == []
        assert any(gen._witness_no_blockers_full_mask(grid) for grid in grids)
        assert any(gen._witness_off_mask_global_switch(grid) for grid in grids)
        assert any(gen._witness_early_path_cut(grid) for grid in grids)
        assert any(gen._witness_late_path_cut(grid) for grid in grids)
        assert any(gen._witness_shifted_clipped_anchor(grid) for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 11, "grid_w": 11, "blockers": 0},
        {"grid_h": 11, "grid_w": 20, "blockers": 12},
        {"grid_h": 20, "grid_w": 11, "blockers": 12},
        {"grid_h": 20, "grid_w": 20, "blockers": 0},
    ],
)
def test_exact_override_boundaries_round_trip(band, overrides):
    grid = gen.generate(seed=123, sample_index=77, difficulty=band, **overrides)
    assert gen.observe_overrides(grid) == overrides
    assert gen.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(seed=0, sample_index=0, typo_axis=1)


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(seed=33, sample_index=0, difficulty="easy")
    seed = gen._seed_position(base)
    assert seed is not None

    missing_seed = copy.deepcopy(base)
    missing_seed[seed[0]][seed[1]] = 0
    assert gen.self_check(missing_seed)

    duplicate_seed = copy.deepcopy(base)
    duplicate_seed[0][0] = 3
    assert any("exactly one" in reason for reason in gen.self_check(duplicate_seed))

    foreign_color = copy.deepcopy(base)
    foreign_color[0][0] = 9
    assert any("palette" in reason for reason in gen.self_check(foreign_color))

    immediate_cut = copy.deepcopy(base)
    r, c = gen._absolute(seed, gen._CORE_PATH[1])
    immediate_cut[r][c] = 2
    assert any("identity" in reason for reason in gen.self_check(immediate_cut))

    too_many_blockers = gen.generate(seed=8, sample_index=81, grid_h=20, grid_w=20, blockers=12)
    added = False
    for r, row in enumerate(too_many_blockers):
        for c, value in enumerate(row):
            if value == 0:
                too_many_blockers[r][c] = 2
                added = True
                break
        if added:
            break
    assert any("0..12 blockers" in reason for reason in gen.self_check(too_many_blockers))


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(seed=444, sample_index=7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(seed=444, sample_index=7, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    third = gen.generate(seed=444, sample_index=7, difficulty="hard")
    assert third == second
