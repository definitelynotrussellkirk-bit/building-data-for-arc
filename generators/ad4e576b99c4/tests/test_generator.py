"""Task-local regressions for the repaired opposite-side shear sampler."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    fixed_public_comb,
    geometry,
    load_generator,
    observed,
    oracle_output,
    racket_outputs,
    source_mask,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def signature(grid):
    return tuple(tuple(row) for row in grid)


def test_contract_metadata_is_pinned_and_small():
    assert gen.RULE_HASH == "6de9bdaa4c45"
    assert gen.EXAMPLES_NEEDED == 2
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_comb",
        "odd_teeth",
        "alternating_bands",
    )
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "bottom_rows",
        "patch_width",
        "patch_height",
        "side",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=["train0", "train1", "test0"],
)
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 16,
            "grid_w": 16,
            "bottom_rows": 6,
            "patch_width": 7,
            "patch_height": 10,
            "side": "left",
        },
        {
            "grid_h": 22,
            "grid_w": 22,
            "bottom_rows": 3,
            "patch_width": 3,
            "patch_height": 4,
            "side": "right",
        },
        {
            "grid_h": 17,
            "grid_w": 20,
            "bottom_rows": 5,
            "patch_width": 5,
            "patch_height": 7,
            "side": "left",
        },
    ],
)
def test_every_exact_control_is_observable_and_total(difficulty, overrides):
    grid = gen.generate(20261007, 2, difficulty=difficulty, **overrides)
    assert gen.self_check(grid, difficulty=difficulty) == []
    assert gen.strict_canonical_like(grid) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides
    assert gen.rule_mirror(grid) == oracle_output(grid)
    assert grid == gen.generate(20261007, 2, difficulty=difficulty, **overrides)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 15),
        ("grid_h", 23),
        ("grid_w", 15),
        ("grid_w", 23),
        ("bottom_rows", 2),
        ("bottom_rows", 7),
        ("patch_width", 2),
        ("patch_width", 8),
        ("patch_height", 3),
        ("patch_height", 11),
        ("side", "middle"),
        ("grid_h", True),
        ("grid_w", 16.0),
        ("patch_height", "7"),
        ("side", 1),
    ],
)
def test_rejects_unknown_invalid_and_coerced_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_rejects_unknown_difficulty():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_distribution_is_valid_diverse_and_replays_cleanly(difficulty):
    shapes, sides, heights, widths, masks, profiles, inputs = set(), set(), set(), set(), set(), set(), set()
    canonical_profiles = 0
    for index in range(180):
        seed = 700_000 + index
        grid = gen.generate(seed, index, difficulty=difficulty)
        replay = gen.generate(seed, index, difficulty=difficulty)
        assert grid == replay
        assert grid is not replay
        assert all(a is not b for a, b in zip(grid, replay))
        assert gen.self_check(grid, difficulty=difficulty) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == oracle_output(grid)
        obs = observed(grid)
        assert gen.observe_overrides(grid) == obs
        shapes.add((obs["grid_h"], obs["grid_w"]))
        sides.add(obs["side"])
        heights.add(obs["patch_height"])
        widths.add(obs["patch_width"])
        masks.add(tuple(sorted(source_mask(grid))))
        profiles.add(gen.schedule_profile(seed, index, difficulty))
        inputs.add(signature(grid))
        canonical_profiles += (
            obs["grid_h"] == obs["grid_w"]
            and obs["grid_h"] in (16, 17, 18)
            and len({value for row in grid for value in row}) == 3
        )
    assert profiles == set(gen.SCHEDULE_PROFILES)
    assert sides == {"left", "right"}
    assert len(shapes) >= 12
    assert len(heights) >= 6
    assert len(widths) >= 4
    assert len(masks) >= 30
    assert len(inputs) >= 150
    assert canonical_profiles >= 100


def test_public_comb_shortcut_fits_all_canonical_pairs_but_generated_witnesses_refute_it():
    rival = gen.CANONICAL_SHORTCUTS["fixed_public_comb"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    assert all(fixed_public_comb(pair["input"]) == pair["output"] for pair in canonical_pairs())

    for index in range(12):
        grid = gen.generate(712, index, difficulty="hard")
        truth = oracle_output(grid)
        if gen.schedule_profile(712, index, "hard") == "canonical_comb":
            assert rival(grid) == truth
            assert not gen.SEMANTIC_WITNESSES["noncanonical_source_mask"](grid)
        else:
            assert rival(grid) != truth
            assert gen.SEMANTIC_WITNESSES["noncanonical_source_mask"](grid)
            assert gen.SEMANTIC_RIVALS["fixed_public_comb"](grid) != truth


def test_every_three_pair_window_refutes_the_declared_rival_under_every_query_rotation():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(3):
                grid = gen.generate(321, start + offset, difficulty=difficulty)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            assert {
                gen.schedule_profile(321, start + offset, difficulty)
                for offset in range(3)
            } == set(gen.SCHEDULE_PROFILES)
            for query_index in range(3):
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert any(fixed_public_comb(pair["input"]) != pair["output"] for pair in demos)
                assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[1], [1, 6]],
        [[1] * 16 for _ in range(16)],
        [[True] * 16 for _ in range(16)],
        [[0] * 16 for _ in range(16)],
    ],
)
def test_malformed_or_shape_blind_impostors_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("mutation", ["break_lower_field", "unknown_color", "interior_patch", "erase_patch", "detach_cell"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 1, grid_h=16, grid_w=16, bottom_rows=5, patch_width=5, patch_height=7, side="left")
    g = geometry(grid)
    if mutation == "break_lower_field":
        grid[g["boundary"]][0] = 1
    elif mutation == "unknown_color":
        grid[0][-1] = 9
    elif mutation == "interior_patch":
        # Move the left edge cell inward, so the bbox no longer touches an edge.
        for r in range(g["r0"], g["r1"] + 1):
            grid[r][0] = 1
        grid[g["r0"]][1] = 5
    elif mutation == "erase_patch":
        for r in range(g["r0"], g["r1"] + 1):
            for c in range(g["c0"], g["c1"] + 1):
                if grid[r][c] == 5:
                    grid[r][c] = 1
    elif mutation == "detach_cell":
        grid[g["r0"] - 1][-1] = 5
    assert gen.self_check(grid)


def test_rule_mirror_and_rival_do_not_mutate_inputs():
    grid = gen.generate(19, 2, difficulty="hard")
    before = deepcopy(grid)
    assert gen.rule_mirror(grid) == oracle_output(grid)
    assert gen.CANONICAL_SHORTCUTS["fixed_public_comb"](grid) == fixed_public_comb(grid)
    assert grid == before


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(24)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]


def test_retained_fixed_comb_counterexample_is_exact_and_authority_backed():
    payload = json.loads((HOME / "counterexamples/fixed-public-comb.json").read_text())
    grid = payload["input"]
    expected = payload["expected_output"]
    rival = payload["rival_output"]
    assert payload["task_id"] == "ad4e576b99c4"
    assert payload["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(grid) == []
    assert oracle_output(grid) == expected == payload["racket_output"]
    assert fixed_public_comb(grid) == rival
    assert expected != rival
    assert payload["differing_cells"] == [
        [r, c]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if expected[r][c] != rival[r][c]
    ]
    assert gen.SEMANTIC_WITNESSES["noncanonical_source_mask"](grid)
