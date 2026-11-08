"""Task-local regression suite for the repaired 9fbd0923e6ae sampler."""
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
    canonical_pairs,
    canonical_rule_hash,
    guide,
    has_opposite_counterexample,
    intended_output,
    load_generator,
    mirror_selector_too,
    observed,
    palette_size,
    racket_outputs,
    selector_side_only,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "guide_orientation",
    "guide_position",
    "n_targets",
    "target_layout",
    "n_distractors",
    "n_distractor_colors",
    "n_guide_noise",
}


def _lesson(seed, start, band):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    return pairs


def test_contract_is_rule_pinned_and_axes_are_exact():
    assert canonical_rule_hash() == "63d7f8006f35"
    assert gen.RULE_HASH == canonical_rule_hash()
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.ALLOW_IDENTITY_OUTPUT is True
    assert gen.EXAMPLES_NEEDED == 3
    assert len(gen.SCHEDULE_PROFILES) == 6
    assert set(gen.CANONICAL_SHORTCUTS) == {"selector_side_only"}
    assert set(gen.LESSON_COMPETITORS) == {"selector_side_only"}


def test_accepts_every_canonical_input_and_independent_oracle_matches():
    for pair in canonical_pairs():
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 8,
            "grid_w": 9,
            "guide_orientation": "vertical",
            "guide_position": "start",
            "n_targets": 2,
            "target_layout": "selector_side",
            "n_distractors": 2,
            "n_distractor_colors": 1,
            "n_guide_noise": 0,
        },
        {
            "grid_h": 11,
            "grid_w": 12,
            "guide_orientation": "horizontal",
            "guide_position": "end",
            "n_targets": 7,
            "target_layout": "both_sides",
            "n_distractors": 6,
            "n_distractor_colors": 2,
            "n_guide_noise": 3,
        },
        {
            "grid_h": 9,
            "grid_w": 11,
            "guide_orientation": "vertical",
            "guide_position": "middle",
            "n_targets": 5,
            "target_layout": "opposite_side",
            "n_distractors": 5,
            "n_distractor_colors": 2,
            "n_guide_noise": 2,
        },
    ],
)
def test_exact_overrides_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(271, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(271, 13, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 12),
        ("grid_w", 8),
        ("grid_w", 13),
        ("guide_orientation", "diagonal"),
        ("guide_position", "far"),
        ("n_targets", 1),
        ("n_targets", 8),
        ("target_layout", "random"),
        ("n_distractors", 1),
        ("n_distractors", 7),
        ("n_distractor_colors", 0),
        ("n_distractor_colors", 3),
        ("n_guide_noise", -1),
        ("n_guide_noise", 4),
        ("grid_h", True),
        ("n_targets", 2.0),
        ("guide_orientation", 1),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_schedule_covers_profiles_and_every_three_demos_refute_shortcut():
    assert set(gen.schedule_profile(19, i) for i in range(6)) == set(gen.SCHEDULE_PROFILES)
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            lesson = _lesson(314159, start, band)
            demos, query = lesson[: gen.EXAMPLES_NEEDED], lesson[-1]
            assert gen.lesson_identifiable(demos, query) == []
            assert any(
                selector_side_only(pair["input"]) != pair["output"]
                for pair in demos
            )


def test_every_cyclic_query_rotation_keeps_a_rival_refuting_demo():
    """All four choices of query remain teachable in every schedule window."""
    for band in (None, "easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            lesson = _lesson(271828, start, band)
            for query_index in range(len(lesson)):
                demos = [
                    pair for index, pair in enumerate(lesson) if index != query_index
                ]
                query = lesson[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                assert any(
                    selector_side_only(pair["input"]) != pair["output"]
                    for pair in demos
                )


def test_declared_shortcut_fits_all_canonical_pairs_but_generated_case_refutes_it():
    for pair in canonical_pairs():
        assert selector_side_only(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["selector_side_only"](pair["input"]) == pair["output"]
    grid = gen.generate(99, 2, difficulty="medium")
    assert gen.self_check(grid) == []
    assert has_opposite_counterexample(grid)
    assert gen.SEMANTIC_WITNESSES["opposite_side_target"](grid)
    assert gen.SEMANTIC_RIVALS["selector_side_only"](grid) == selector_side_only(grid)


def test_scheduled_identity_case_is_lawful_and_intentional():
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(401, 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) == grid


def test_selector_is_not_reflected_when_its_mirror_is_in_bounds():
    grid = gen.generate(
        7,
        0,
        grid_h=9,
        grid_w=9,
        guide_orientation="horizontal",
        guide_position="middle",
        n_targets=3,
        target_layout="selector_side",
        n_distractors=2,
        n_distractor_colors=1,
        n_guide_noise=0,
    )
    assert intended_output(grid) != mirror_selector_too(grid)
    orientation, axis = guide(grid)
    assert orientation == "horizontal"
    assert intended_output(grid)[2 * axis][0] != grid[0][0]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_covers_branches(band):
    orientations = set()
    positions = set()
    layouts = set()
    palettes = set()
    shapes = set()
    unique = set()
    identity = 0
    rival_witnesses = 0
    canonical_profiles = 0
    canonical_dimensions = {(8, 10), (9, 9), (8, 11), (10, 10), (9, 11)}
    for index in range(120):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        assert gen.observe_overrides(grid) == stats
        orientations.add(stats["guide_orientation"])
        positions.add(stats["guide_position"])
        layouts.add(stats["target_layout"])
        palettes.add(palette_size(grid))
        shapes.add((stats["grid_h"], stats["grid_w"]))
        unique.add(json.dumps(grid, separators=(",", ":")))
        truth = intended_output(grid)
        identity += truth == grid
        rival_witnesses += truth != selector_side_only(grid)
        canonical_profiles += (
            (stats["grid_h"], stats["grid_w"]) in canonical_dimensions
            and palette_size(grid) in {4, 5}
        )
    assert orientations == {"vertical", "horizontal"}
    assert positions == {"start", "middle", "end"}
    assert layouts == {"selector_side", "opposite_side", "both_sides"}
    assert {4, 5} <= palettes
    assert len(shapes) >= 5
    assert len(unique) >= 112
    assert 10 <= identity <= 30
    assert rival_witnesses >= 50
    assert canonical_profiles >= 80


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_missing_guide_selector_and_target_mutations():
    grid = gen.generate(8, 2)

    no_guide = deepcopy(grid)
    orientation, axis = guide(no_guide)
    if orientation == "vertical":
        for row in no_guide:
            row[axis] = 0
    else:
        no_guide[axis] = [0] * len(no_guide[axis])
    assert gen.self_check(no_guide)

    bad_selector = deepcopy(grid)
    bad_selector[0][0] = 0
    assert gen.self_check(bad_selector)

    no_other_targets = deepcopy(grid)
    target = no_other_targets[0][0]
    for r, row in enumerate(no_other_targets):
        for c, value in enumerate(row):
            if value == target and (r, c) != (0, 0):
                no_other_targets[r][c] = 0
    assert gen.self_check(no_other_targets)


def test_real_racket_reference_matches_independent_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(811, index, difficulty="hard") for index in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,os,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
