"""Source-bound regressions for the repaired 78e3f26e92aa generator."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, components, geometry_output, load_generator, observed

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "green_height",
    "green_gap",
    "cyan_height",
    "cyan_gap",
    "vertical_gap",
    "color_order",
}


def _labeled(grid):
    return {"input": grid, "output": geometry_output(grid)}


def test_authority_identity_and_axis_contract_are_pinned():
    assert gen.GENERATOR_ID == "78e3f26e92aa"
    assert gen.TASK_ID == "78e3f26e92aa"
    assert gen.RULE_HASH == "ed1ed1d0980e"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert "texture" not in gen.AXES


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_every_canonical_pair_is_owned_and_matches_independent_geometry(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "axes",
    [
        dict(grid_h=22, grid_w=17, green_height=1, green_gap=1,
             cyan_height=1, cyan_gap=1, vertical_gap=2, color_order="green_above"),
        dict(grid_h=24, grid_w=20, green_height=5, green_gap=4,
             cyan_height=5, cyan_gap=4, vertical_gap=10, color_order="cyan_above"),
        dict(grid_h=23, grid_w=19, green_height=3, green_gap=2,
             cyan_height=4, cyan_gap=3, vertical_gap=7, color_order="green_above"),
        dict(grid_h=22, grid_w=17, green_height=1, green_gap=1,
             cyan_height=4, cyan_gap=2, vertical_gap=9, color_order="green_above"),
    ],
)
def test_all_declared_axes_are_constructive_observable_and_band_independent(difficulty, axes):
    grid = gen.generate(117, 31, difficulty=difficulty, **axes)
    assert gen.self_check(grid, meta={"overrides": axes}) == []
    assert gen.observe_overrides(grid) == axes
    assert observed(grid) == {**axes, "component_count": 4,
                              "magenta_count": observed(grid)["magenta_count"]}
    assert gen.rule_mirror(grid) == geometry_output(grid)


def test_exact_overrides_remain_constructive_when_preferred_branch_has_tiny_pool():
    axes = dict(grid_h=22, grid_w=17, green_height=1, green_gap=1,
                cyan_height=4, cyan_gap=2, vertical_gap=9, color_order="green_above")
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(0, 0, difficulty=difficulty, **axes)
        assert gen.self_check(grid, meta={"overrides": axes}) == []
        assert gen.observe_overrides(grid) == axes


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 21}, {"grid_h": 25}, {"grid_w": 16}, {"grid_w": 21},
        {"green_height": 0}, {"green_height": 6}, {"cyan_height": 2.0},
        {"green_gap": 0}, {"cyan_gap": 5}, {"vertical_gap": 1}, {"vertical_gap": 11},
        {"color_order": "green_first"}, {"grid_h": True}, {"grid_w": "22"},
    ],
)
def test_invalid_or_unknown_axis_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "call",
    [
        lambda: gen.generate(True, 0),
        lambda: gen.generate(0, False),
        lambda: gen.generate(-1, 0),
        lambda: gen.generate(0, -1),
        lambda: gen.generate(0, 0, difficulty=0.5),
        lambda: gen.generate(0, 0, difficulty="expert"),
    ],
)
def test_top_level_scalar_contract_is_strict(call):
    with pytest.raises((TypeError, ValueError)):
        call()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_covers_canonical_profiles_orders_and_semantic_branches(difficulty):
    stats = []
    for index in range(24):
        grid = gen.generate(812, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == geometry_output(grid)
        assert grid == gen.generate(812, index, difficulty=difficulty)
        stats.append(observed(grid))
    assert {(item["grid_h"], item["grid_w"]) for item in stats[:4]} == {
        (22, 18), (23, 17), (24, 19), (24, 20)
    }
    assert {item["component_count"] for item in stats} == {4}
    assert {item["color_order"] for item in stats} == {"green_above", "cyan_above"}
    assert {item["magenta_count"] == 0 for item in stats} == {False, True}
    assert 1 in {item["green_height"] for item in stats} | {item["cyan_height"] for item in stats}
    assert any(item["green_height"] > 1 or item["cyan_height"] > 1 for item in stats)


def test_difficulty_bands_select_distinct_lawful_placements():
    for index in range(12):
        grids = [gen.generate(2400, index, difficulty=band)
                 for band in ("easy", "medium", "hard")]
        assert len({repr(grid) for grid in grids}) == 3
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert all(gen.rule_mirror(grid) == geometry_output(grid) for grid in grids)


def test_default_schedule_does_not_lock_independent_axes_one_to_one():
    stats = [observed(gen.generate(1600, index)) for index in range(8)]

    def has_one_to_many(left, right):
        mapping = {}
        for item in stats:
            mapping.setdefault(item[left], set()).add(item[right])
        return any(len(values) > 1 for values in mapping.values())

    for left, right in (("cyan_height", "green_gap"),
                        ("cyan_height", "vertical_gap"),
                        ("green_gap", "vertical_gap")):
        assert has_one_to_many(left, right) or has_one_to_many(right, left), (left, right)


def test_self_check_rejects_the_old_two_rectangle_grammar_and_destructive_mutations():
    counterexample = json.loads(
        (HOME / "counterexamples" / "legacy_two_rectangles.json").read_text()
    )
    old_rectangles = counterexample["input"]
    assert gen.self_check(old_rectangles)
    assert gen.strict_canonical_like(old_rectangles)

    base = gen.generate(31, 2)
    mutations = []
    mutations.append([row[:-1] if index == 0 else row[:] for index, row in enumerate(base)])

    bad_color = deepcopy(base)
    bad_color[0][0] = 5
    mutations.append(bad_color)

    missing_bar = deepcopy(base)
    green_components = components(missing_bar, 3)
    for r, c in green_components[0]["cells"]:
        missing_bar[r][c] = 0
    mutations.append(missing_bar)

    unequal_heights = deepcopy(base)
    target = components(unequal_heights, 8)[0]
    r, c = max(target["cells"])
    unequal_heights[r][c] = 0
    mutations.append(unequal_heights)

    overlapping_rows = deepcopy(base)
    cyan_cells = set().union(*(part["cells"] for part in components(overlapping_rows, 8)))
    for r, c in cyan_cells:
        overlapping_rows[r][c] = 0
    green_top = min(r for part in components(overlapping_rows, 3) for r, _ in part["cells"])
    cyan_columns = [2, 5]
    for c in cyan_columns:
        for r in range(green_top, green_top + 2):
            overlapping_rows[r][c] = 8
    mutations.append(overlapping_rows)

    for mutation in mutations:
        assert gen.self_check(mutation)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 3]], [[True] * 17 for _ in range(22)]])
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_declared_semantic_rivals_are_real_and_three_demo_lessons_are_identifiable():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.LESSON_COMPETITORS) == {
        "unit_height_steps", "downward_only", "no_magenta_intersections"
    }
    assert set(gen.WITNESS_RIVALS) == {
        "height_scaled_steps", "bidirectional_rays", "magenta_intersections"
    }
    for start in range(12):
        pairs = [_labeled(gen.generate(4200 + start, start + offset, difficulty="hard"))
                 for offset in range(gen.EXAMPLES_NEEDED + 1)]
        demos, query = pairs[:-1], pairs[-1]
        assert gen.lesson_identifiable(demos, query) == []
        for witness, rivals in gen.WITNESS_RIVALS.items():
            firing = [pair for pair in pairs if gen.SEMANTIC_WITNESSES[witness](pair["input"])]
            assert firing, (start, witness)
            assert all(
                any(gen.SEMANTIC_RIVALS[name](pair["input"]) != pair["output"] for name in rivals)
                for pair in firing
            )


def test_rivals_are_pure_deterministic_and_every_four_pair_rotation_is_safe():
    for start in range(8):
        grids = [gen.generate(7700 + start, start + offset) for offset in range(4)]
        pairs = [_labeled(grid) for grid in grids]
        for name, rival in gen.LESSON_COMPETITORS.items():
            before = deepcopy(grids)
            first = [rival(grid) for grid in grids]
            second = [rival(grid) for grid in grids]
            assert grids == before, name
            assert first == second, name
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_repeated_generation_is_fast_enough_for_the_override_matrix():
    started = time.perf_counter()
    for index in range(300):
        grid = gen.generate(9000 + index, index * 8, difficulty="medium")
        assert gen.self_check(grid) == []
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0, f"300 repeated-profile generations took {elapsed:.3f}s"


def test_replay_is_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(412, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(412, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(412, 7, difficulty="hard") == second


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(812,17,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "909"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]
