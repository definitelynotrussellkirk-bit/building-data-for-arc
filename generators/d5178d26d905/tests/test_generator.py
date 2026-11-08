"""Task-local regressions for the template/reference row-mapping generator."""
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
import reference_probe  # noqa: E402
from reference_probe import (  # noqa: E402
    analyze,
    canonical_pairs,
    first_two_special_rows_only,
    fixed_reference_width_seven,
    intended_output,
    load_generator,
    observed_controls,
    pair,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


def test_metadata_and_authority_pin_are_current():
    assert gen.GENERATOR_ID == gen.TASK_ID == "d5178d26d905"
    assert gen.RULE_HASH == "70d9964daef1"
    assert gen.VERSION == "2.1.0"
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0


@pytest.mark.parametrize("item", canonical_pairs())
def test_all_canonical_pairs_are_accepted_and_match_independent_oracle(item):
    grid = deepcopy(item["input"])
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert intended_output(grid) == item["output"]
    assert gen.rule_mirror(grid) == item["output"]
    assert grid == item["input"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("side", ("left", "right"))
@pytest.mark.parametrize("alignment", ("top", "center", "bottom"))
def test_exact_public_controls_are_observable_and_rule_correct(band, side, alignment):
    grid = gen.generate(
        3701,
        11,
        difficulty=band,
        reference_side=side,
        template_alignment=alignment,
    )
    assert gen.self_check(grid) == []
    assert observed_controls(grid) == {
        "reference_side": side,
        "template_alignment": alignment,
    }
    assert gen.observe_overrides(grid) == observed_controls(grid)
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reference_side": "up"},
        {"template_alignment": "offset"},
        {"reference_side": 1},
        {"template_alignment": True},
        {"typo_axis": "left"},
    ],
)
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **kwargs)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty=difficulty)


@pytest.mark.parametrize("seed", (True, 1.5, "1", None))
def test_invalid_seed_types_fail_closed(seed):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(seed, 2)
    with pytest.raises(TypeError, match="seed"):
        gen.schedule_profile(seed, 2)


@pytest.mark.parametrize("sample_index", (True, 2.0, "2", None))
def test_invalid_sample_index_types_fail_closed(sample_index):
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(1, sample_index)
    with pytest.raises(TypeError, match="sample_index"):
        gen.schedule_profile(1, sample_index)


def test_negative_sample_index_fails_closed():
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(1, -1)
    with pytest.raises(ValueError, match="sample_index"):
        gen.schedule_profile(1, -1)


@pytest.mark.parametrize("band", BANDS)
def test_every_three_consecutive_examples_cover_the_semantic_schedule(band):
    for start in range(12):
        profiles = [
            gen.schedule_profile(77, start + offset, difficulty=band)
            for offset in range(3)
        ]
        assert set(profiles) == set(gen.SCHEDULE_PROFILES)

        grids = [
            gen.generate(77, start + offset, difficulty=band)
            for offset in range(4)
        ]
        for grid in grids:
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == intended_output(grid)

        demos = [pair(grid) for grid in grids[:3]]
        query = pair(grids[3])
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_hits_each_intended_counterexample_profile(band):
    seen = set()
    serialized = set()
    exact_profiles = set()
    for index in range(90):
        grid = gen.generate(5000 + index, index, difficulty=band)
        info = analyze(grid)
        seen.add(gen.schedule_profile(5000 + index, index, difficulty=band))
        serialized.add(json.dumps(grid))
        exact_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert 5 <= info["reference_width"] <= 9
        assert 1 <= len(info["reference_line_cols"]) <= 4
        assert 1 <= len(info["reference_special_indexes"]) <= 3
    assert seen == set(gen.SCHEDULE_PROFILES)
    assert len(serialized) >= 80
    assert exact_profiles & {
        (7, 13, 6),
        (9, 11, 6),
        (9, 13, 6),
        (11, 13, 6),
        (12, 15, 6),
    }


def test_declared_shortcuts_fit_every_canonical_pair_and_generated_witnesses_refute_them():
    pairs = canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "first_two_special_rows_only",
        "fixed_reference_width_seven",
        "yellow_density_order",
    }
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(item["input"]) == item["output"] for item in pairs), name

    third_special = gen.generate(19, 1)
    variable_width = gen.generate(19, 2)
    assert len(analyze(third_special)["reference_special_indexes"]) == 3
    assert first_two_special_rows_only(third_special) != intended_output(third_special)
    assert analyze(variable_width)["reference_width"] != 7
    assert fixed_reference_width_seven(variable_width) != intended_output(variable_width)


def test_semantic_witness_contract_names_real_counterexamples():
    third_special = gen.generate(19, 1)
    variable_width = gen.generate(19, 2)
    assert gen.SEMANTIC_WITNESSES["third_special_row"](third_special)
    assert gen.SEMANTIC_WITNESSES["variable_reference_width"](variable_width)
    assert gen.SEMANTIC_WITNESSES["nonmonotonic_yellow_density"](third_special)
    assert gen.SEMANTIC_WITNESSES["nonmonotonic_yellow_density"](variable_width)
    assert gen.SEMANTIC_RIVALS["first_two_special_rows_only"](third_special) != gen.rule_mirror(third_special)
    assert gen.SEMANTIC_RIVALS["fixed_reference_width_seven"](variable_width) != gen.rule_mirror(variable_width)
    assert gen.SEMANTIC_RIVALS["yellow_density_order"](third_special) != gen.rule_mirror(third_special)
    assert gen.SEMANTIC_RIVALS["yellow_density_order"](variable_width) != gen.rule_mirror(variable_width)
    assert gen.WITNESS_RIVALS["nonmonotonic_yellow_density"] == ["yellow_density_order"]


def test_independent_density_oracle_matches_declared_rival():
    assert callable(reference_probe.yellow_density_order)
    for band in BANDS:
        for sample_index in range(12):
            grid = gen.generate(101, sample_index, difficulty=band)
            assert reference_probe.yellow_density_order(grid) == gen.SEMANTIC_RIVALS["yellow_density_order"](grid)


@pytest.mark.parametrize("band", BANDS)
def test_every_noncanonical_profile_refutes_density_order_rival(band):
    rival = gen.SEMANTIC_RIVALS["yellow_density_order"]
    for seed in range(5):
        for sample_index in range(18):
            profile = gen.schedule_profile(seed, sample_index, difficulty=band)
            if profile == "canonical_scale":
                continue
            grid = gen.generate(seed, sample_index, difficulty=band)
            info = analyze(grid)
            assert info["reference_width"] - len(info["reference_line_cols"]) >= 2
            assert reference_probe.yellow_density_order(grid) == rival(grid)
            assert rival(grid) != intended_output(grid), (band, seed, sample_index, profile)
            assert gen.SEMANTIC_WITNESSES["nonmonotonic_yellow_density"](grid)


def test_retained_density_order_lesson_recipe_is_now_teaching_safe():
    examples = [
        pair(gen.generate(0, sample_index, difficulty="medium"))
        for sample_index in (7, 8, 9, 10)
    ]
    rival = gen.LESSON_COMPETITORS["yellow_density_order"]
    demos, query = examples[:3], examples[3]
    assert any(rival(item["input"]) != item["output"] for item in demos)
    assert rival(query["input"]) != query["output"]
    assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(7)], [[0] * 11 for _ in range(7)]],
)
def test_malformed_grids_are_reported_not_raised(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_structure_destroying_mutations():
    base = gen.generate(44, 1)
    mutations = []

    no_divider = deepcopy(base)
    divider = analyze(base)["divider"]
    no_divider[0][divider] = 0
    mutations.append(no_divider)

    extra_divider = deepcopy(base)
    for row in extra_divider:
        row[0] = 5
    mutations.append(extra_divider)

    illegal_reference_color = deepcopy(base)
    info = analyze(base)
    col = 0 if info["reference_side"] == "left" else info["divider"] + 1
    illegal_reference_color[0][col] = 9
    mutations.append(illegal_reference_color)

    missing_special = deepcopy(base)
    info = analyze(base)
    special_row = info["reference_special_indexes"][0]
    raw_row = info["reference_rows"][special_row]
    start = 0 if info["reference_side"] == "left" else info["divider"] + 1
    for offset, value in enumerate(info["reference_normal"]):
        missing_special[raw_row][start + offset] = value
    mutations.append(missing_special)

    for changed in mutations:
        assert gen.self_check(changed)


def test_keyed_rng_is_independent_of_python_hash_seed():
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

@pytest.mark.parametrize("band", BANDS)
def test_any_query_rotation_of_four_consecutive_examples_remains_identifiable(band):
    """A lesson must not depend on always placing one profile in the query slot."""
    for start in range(9):
        examples = [
            pair(gen.generate(9100 + start, start + offset, difficulty=band))
            for offset in range(4)
        ]
        for query_index in range(4):
            demos = [
                item for index, item in enumerate(examples)
                if index != query_index
            ]
            query = examples[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), (start, query_index, name)
