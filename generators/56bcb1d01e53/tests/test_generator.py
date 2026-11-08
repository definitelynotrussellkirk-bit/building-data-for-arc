"""Task-local regressions for the complete-icon-symmetry generator."""
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
from reference_probe import (  # noqa: E402
    background,
    cardinal_center_only,
    intended_output,
    load_generator,
    no_bridge_merge,
    no_center_fill,
    odd_squares_only,
    pair,
    square_dihedral_closure,
    square_rotation_only,
    witness_flags,
)
from reviewer_support import canonical_pairs, find_root  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {
    (11, 19, 3),
    (11, 19, 4),
    (19, 19, 5),
    (20, 18, 4),
    (22, 22, 5),
}


def test_metadata_and_rule_pin_are_current():
    assert gen.GENERATOR_ID == gen.TASK_ID == "56bcb1d01e53"
    assert gen.RULE_HASH == "a66a93e7a5d4"
    assert gen.VERSION == "3.1.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 2


def test_independent_oracle_matches_every_labeled_canonical_pair():
    pairs = canonical_pairs("56bcb1d01e53", root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for item in pairs:
        original = deepcopy(item["input"])
        assert intended_output(original) == item["output"]
        assert gen.rule_mirror(original) == item["output"]
        assert gen.self_check(original) == []
        assert original == item["input"]


@pytest.mark.parametrize("band", BANDS)
def test_teaching_profile_contains_all_six_rule_branches(band):
    for index in (1, 3, 5, 7):
        grid = gen.generate(8100 + index, index, difficulty=band)
        assert gen.schedule_profile(8100 + index, index, band) == "teaching_mix"
        assert witness_flags(grid) == {
            "bridge_merge": True,
            "rectangular_expansion": True,
            "even_square": True,
            "center_completion": True,
            "diagonal_center_completion": True,
            "rotation_not_dihedral": True,
        }
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert grid != intended_output(grid)


@pytest.mark.parametrize("band", BANDS)
def test_every_four_pair_query_rotation_remains_identifiable(band):
    for start in range(8):
        examples = [
            pair(gen.generate(9200 + start, start + offset, difficulty=band))
            for offset in range(4)
        ]
        for query_index in range(4):
            demos = [item for index, item in enumerate(examples) if index != query_index]
            query = examples[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("color", range(1, 10))
def test_background_override_is_exact_and_observable(band, color):
    grid = gen.generate(17, 7, difficulty=band, background=color)
    assert gen.self_check(grid) == []
    assert background(grid) == color
    assert gen.observe_overrides(grid) == {"background": color}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"background": -1},
        {"background": 0},
        {"background": 10},
        {"background": True},
        {"background": 2.0},
        {"background": "2"},
        {"typo_axis": 2},
    ],
)
def test_bad_or_unknown_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **kwargs)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_bad_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty=difficulty)


def test_default_distribution_covers_every_canonical_profile_and_is_noncollapsed():
    grids = [gen.generate(4400 + index, index) for index in range(80)]
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert CANONICAL_PROFILES <= profiles
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 75
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.rule_mirror(grid) == intended_output(grid) for grid in grids)
    assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) >= 35


def test_named_rivals_are_real_counterexamples_on_teaching_mix():
    grid = gen.generate(33, 1)
    truth = intended_output(grid)
    expected = {
        "no_bridge_merge": no_bridge_merge,
        "square_rotation_only": square_rotation_only,
        "odd_squares_only": odd_squares_only,
        "no_center_fill": no_center_fill,
        "cardinal_center_only": cardinal_center_only,
        "square_dihedral_closure": square_dihedral_closure,
    }
    assert set(gen.SEMANTIC_RIVALS) == set(expected)
    for name, rival in expected.items():
        assert gen.SEMANTIC_RIVALS[name](grid) == rival(grid)
        assert rival(grid) != truth, name


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 11 for _ in range(11)],
        [[0] * 11 for _ in range(11)],
        [[0] * 11 for _ in range(5)] + [[0] * 5 + [1] + [0] * 5] + [[0] * 11 for _ in range(5)],
        [[0] * 11 for _ in range(4)] + [[0] * 4 + [1, 1, 1] + [0] * 4] + [[0] * 11 for _ in range(6)],
        [[0] * 11 for _ in range(4)] + [[0] * 4 + [1, 1] + [0] * 5, [0] * 4 + [1, 1] + [0] * 5] + [[0] * 11 for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_and_trivial_scenes(grid):
    assert gen.self_check(grid)


def test_rule_mirror_and_rivals_are_pure_and_deterministic():
    grid = gen.generate(71, 1)
    before = deepcopy(grid)
    functions = [gen.rule_mirror, *gen.SEMANTIC_RIVALS.values()]
    for fn in functions:
        assert fn(grid) == fn(grid)
        assert grid == before


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_must_be_a_real_integer(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, -1, 1.0, 1.75, "1"])
def test_sample_index_must_be_a_nonnegative_integer(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, bad_index)


def _zero_background_authority_witness():
    cells = {
        (0, 3), (1, 2), (2, 2), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 6), (4, 2), (5, 3), (6, 3),
    }
    return [[2 if (r, c) in cells else 0 for c in range(7)] for r in range(7)]


def test_zero_background_is_rejected_by_validator_and_public_mirror():
    grid = _zero_background_authority_witness()
    reasons = gen.self_check(grid)
    assert reasons
    assert any("background" in reason and "0" in reason for reason in reasons)
    with pytest.raises(ValueError, match="background.*0|0.*background"):
        gen.rule_mirror(grid)
    with pytest.raises(ValueError, match="background.*0|0.*background"):
        gen.observe_overrides(grid)


@pytest.mark.parametrize("band", BANDS)
def test_teaching_mix_refutes_cardinal_only_and_full_dihedral_rivals(band):
    grid = gen.generate(20261020, 1, difficulty=band)
    truth = intended_output(grid)
    flags = witness_flags(grid)
    assert flags["diagonal_center_completion"]
    assert flags["rotation_not_dihedral"]
    assert cardinal_center_only(grid) != truth
    assert square_dihedral_closure(grid) != truth
    assert gen.SEMANTIC_RIVALS["cardinal_center_only"](grid) == cardinal_center_only(grid)
    assert gen.SEMANTIC_RIVALS["square_dihedral_closure"](grid) == square_dihedral_closure(grid)
