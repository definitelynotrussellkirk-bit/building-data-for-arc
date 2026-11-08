from __future__ import annotations

import copy
import json
import random

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

REPO = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator("0ed4fa8c0b40", root=REPO)


def canonical_row() -> dict:
    path = canonical_path(REPO)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "d42dbc127318"
    row = canonical_row()
    for pair in [*row["train"], *row["test"]]:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_selected_target_code_is_exactly_the_canonical_program():
    row = canonical_row()
    base_path = (
        REPO
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "training"
        / "760b3cac__0ed4fa8c0b40.json"
    )
    base = json.loads(base_path.read_text())
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_schedule_has_linked_canonical_support_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(918273, i, difficulty=difficulty) for i in range(20)]
        strict = [grid for grid in grids if not GEN.strict_canonical_like(grid)]
        assert len(strict) >= 8
        assert all((len(grid), len(grid[0])) == (6, 9) for grid in strict)
        assert {GEN.schedule_profile(918273, i, difficulty) for i in range(8)} == set(
            GEN.SCHEDULE_PROFILES
        )


def test_exact_override_boundaries_are_realized_and_observed():
    cases = [
        {
            "grid_h": 6,
            "grid_w": 9,
            "direction": "left",
            "cyan_h": 2,
            "cyan_w": 2,
            "fill_level": "dense",
            "arrow_vertical": "top",
            "arrow_horizontal": "right",
        },
        {
            "grid_h": 14,
            "grid_w": 18,
            "direction": "right",
            "cyan_h": 3,
            "cyan_w": 3,
            "fill_level": "sparse",
            "arrow_vertical": "bottom",
            "arrow_horizontal": "left",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for case in cases:
            grid = GEN.generate(8081, 17, difficulty=difficulty, **case)
            assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": case}) == []
            observed = GEN.observe_overrides(grid)
            assert {name: observed[name] for name in case} == case


def test_unknown_axes_and_unknown_modes_fail_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")
    with pytest.raises(ValueError, match="texture"):
        GEN.generate(1, 0, texture="not_a_fixture")


def test_self_check_rejects_ambiguous_arrow_and_disconnected_cyan():
    base = GEN.generate(
        44,
        2,
        grid_h=8,
        grid_w=12,
        direction="right",
        cyan_h=3,
        cyan_w=3,
        fill_level="sparse",
        arrow_vertical="bottom",
        arrow_horizontal="center",
    )
    assert GEN.self_check(base) == []

    ambiguous = copy.deepcopy(base)
    arrow = GEN._decode_arrow(ambiguous)
    assert arrow is not None
    ambiguous[arrow.top][arrow.center - arrow.direction] = 4
    assert GEN.self_check(ambiguous)

    disconnected = copy.deepcopy(base)
    cyan = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 8]
    for r, c in cyan:
        disconnected[r][c] = 0
    disconnected[0][0] = 8
    disconnected[0][2] = 8
    disconnected[2][0] = 8
    assert GEN.self_check(disconnected)


@pytest.mark.parametrize("texture", GEN.DEGENERATE_TEXTURES)
def test_negative_texture_fixtures_are_rejected_by_self_check(texture):
    grid = GEN.generate(7, 3, texture=texture)
    assert GEN.self_check(grid), texture


def test_every_sliding_four_demo_window_refutes_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(9991 + start, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_declared_witnesses_fire_and_really_refute_their_rivals():
    firings = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(24):
        grid = GEN.generate(314159, sample_index, difficulty="medium")
        official = GEN.rule_mirror(grid)
        for witness, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                firings[witness] += 1
                for rival_name in GEN.WITNESS_RIVALS.get(witness, ()):
                    assert GEN.SEMANTIC_RIVALS[rival_name](copy.deepcopy(grid)) != official
    assert all(count > 0 for count in firings.values())


def test_determinism_freshness_and_global_rng_independence():
    random.seed(0x0ED4)
    state = random.getstate()
    first = GEN.generate(123, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 19, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    pristine = copy.deepcopy(first)
    GEN.rule_mirror(first)
    assert first == pristine
    first[0][0] = 9
    assert GEN.generate(123, 19, difficulty="hard") == second


def test_large_sample_retains_input_and_output_diversity():
    grids = [
        GEN.generate(seed, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
        for seed in range(120)
    ]
    outputs = [GEN.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 110
    assert len({frozen(grid) for grid in outputs}) >= 110


@pytest.mark.parametrize("difficulty", ("easy", None, "hard"))
@pytest.mark.parametrize("bad_seed", (True, False, 1.0, 1.75, "1", None))
def test_generate_rejects_non_literal_integer_seeds(difficulty, bad_seed):
    with pytest.raises(TypeError, match="seed must be a literal Python integer"):
        GEN.generate(bad_seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", ("easy", None, "hard"))
@pytest.mark.parametrize("bad_index", (True, False, 1.0, 1.75, "1", None))
def test_generate_rejects_non_literal_integer_sample_indices(difficulty, bad_index):
    with pytest.raises(TypeError, match="sample_index must be a literal Python integer"):
        GEN.generate(991, bad_index, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", ("easy", None, "hard"))
def test_generate_rejects_negative_sample_indices(difficulty):
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GEN.generate(991, -1, difficulty=difficulty)


@pytest.mark.parametrize("seed,sample_index", ((0, 0), (-7, 1), (2**80, 2)))
@pytest.mark.parametrize("difficulty", ("easy", None, "hard"))
def test_generate_accepts_all_literal_integer_seeds_and_nonnegative_indices(
    difficulty, seed, sample_index
):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    assert GEN.self_check(grid, difficulty=difficulty) == []


def test_schedule_profile_uses_the_same_strict_scalar_contract():
    with pytest.raises(TypeError, match="seed must be a literal Python integer"):
        GEN.schedule_profile(True, 0)
    with pytest.raises(TypeError, match="sample_index must be a literal Python integer"):
        GEN.schedule_profile(0, False)
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GEN.schedule_profile(0, -1)
