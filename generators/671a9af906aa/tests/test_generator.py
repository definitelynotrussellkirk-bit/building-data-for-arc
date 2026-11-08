"""Task-local regression suite for 671a9af906aa.

The semantic oracle and rivals live in workspace/maze_probe.py and do not import
production code, so these tests can detect a generator implementation mistake.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from maze_probe import (
    always_visit_key_rival,
    canonical_record,
    classify,
    global_key_unlock_rival,
    rule_output,
)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def test_contract_is_rule_pinned_and_only_exact_axes_are_advertised():
    assert gen.RULE_HASH == "09280085884a"
    assert set(gen.AXES) == {"grid_h", "grid_w", "route_mode"}
    assert gen.AXES["route_mode"]["valid"] == "key_detour|unreachable|key_bypass"
    assert gen.EXAMPLES_NEEDED == 5


def test_canonical_pairs_are_accepted_and_python_mirror_is_exact():
    record = canonical_record(REPO)
    for pair in record["train"] + record["test"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert rule_output(pair["input"]) == pair["output"]


def test_unreachable_identity_branch_is_explicitly_runner_lawful():
    assert gen.ALLOW_IDENTITY_OUTPUT is True
    grid = gen.generate(107, 1, grid_h=11, grid_w=15, route_mode="unreachable")
    assert gen.rule_mirror(grid) == grid


def test_always_visit_key_is_a_real_canonical_shortcut():
    record = canonical_record(REPO)
    assert all(always_visit_key_rival(pair["input"]) == pair["output"] for pair in record["train"])
    assert always_visit_key_rival(record["test"][0]["input"]) != record["test"][0]["output"]
    assert gen.CANONICAL_SHORTCUTS["always_visit_key"](record["test"][0]["input"]) == always_visit_key_rival(record["test"][0]["input"])


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("mode", ["key_detour", "unreachable", "key_bypass"])
def test_exact_overrides_are_observable_in_every_band(band, mode):
    grid = gen.generate(71, 9, difficulty=band, grid_h=11, grid_w=15, route_mode=mode)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": 11, "grid_w": 15, "route_mode": mode}
    assert classify(grid) == mode


def test_five_example_schedule_covers_all_semantic_profiles():
    modes = [
        gen.schedule_profile(19, i, difficulty="medium")
        for i in range(gen.EXAMPLES_NEEDED)
    ]
    assert set(modes) == set(gen.SCHEDULE_PROFILES) == {"key_detour", "unreachable", "key_bypass"}
    for start in range(12):
        assert {
            gen.schedule_profile(19, start + offset, difficulty="hard")
            for offset in range(gen.EXAMPLES_NEEDED)
        } == set(gen.SCHEDULE_PROFILES)


def test_each_profile_has_the_promised_counterfactual():
    detour = gen.generate(101, 0, grid_h=11, grid_w=15, route_mode="key_detour")
    unreachable = gen.generate(102, 1, grid_h=11, grid_w=15, route_mode="unreachable")
    bypass = gen.generate(103, 3, grid_h=11, grid_w=15, route_mode="key_bypass")

    assert gen.rule_mirror(detour) != global_key_unlock_rival(detour)
    assert gen.rule_mirror(unreachable) == unreachable
    assert global_key_unlock_rival(unreachable) != unreachable
    assert gen.rule_mirror(bypass) != always_visit_key_rival(bypass)


def test_standard_six_pair_episode_stays_below_identity_warning_threshold():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(211, index, difficulty=band) for index in range(6)]
        identity = sum(gen.rule_mirror(grid) == grid for grid in grids)
        assert identity <= 1


def test_default_size_does_not_predict_route_reachability():
    # The previous five-scene size cycle enlarged only the unreachable slot.
    # Inspect actual generated grids so a schedule/constructor disagreement fails.
    support = {mode: [0, 0] for mode in gen.SCHEDULE_PROFILES}
    strict = []
    for index in range(25):
        grid = gen.generate(671900, index, difficulty="medium")
        canonical_size = len(grid) == 7 and 9 <= len(grid[0]) <= 11
        support[classify(grid)][not canonical_size] += 1
        strict.append(canonical_size)
    for mode, (canonical, enlarged) in support.items():
        assert canonical and enlarged, (mode, support)
        assert canonical == 4 * enlarged, (mode, support)
    # Keep the documented support floor for any six-pair materialization window,
    # including windows crossing the end of the schedule period.
    for start in range(25):
        assert sum((strict + strict)[start:start + 6]) / 6 >= gen.MIN_STRICT_FRAC


@pytest.mark.parametrize("numeric_alias", ["float", "bool"])
def test_lesson_rejects_noninteger_output_colors(numeric_alias):
    pairs = []
    for index in range(6):
        grid = gen.generate(671901, index)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:5], pairs[5]) == []
    if numeric_alias == "float":
        pairs[0]["output"] = [[float(cell) for cell in row] for row in pairs[0]["output"]]
    else:
        pairs[0]["output"] = [[False if cell == 0 else cell for cell in row]
                              for row in pairs[0]["output"]]
    assert any("demo 0 output" in reason
               for reason in gen.lesson_identifiable(pairs[:5], pairs[5]))


def test_default_distribution_is_deterministic_lawful_and_varied():
    for band in ("easy", "medium", "hard"):
        modes, shapes, grids = set(), set(), set()
        canonical_scale = 0
        for index in range(48):
            grid = gen.generate(500 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(500 + index, index, difficulty=band)
            obs = gen.observe_overrides(grid)
            modes.add(obs["route_mode"])
            shapes.add((len(grid), len(grid[0])))
            grids.add(tuple(map(tuple, grid)))
            canonical_scale += len(grid) == 7 and 9 <= len(grid[0]) <= 11
        assert modes == {"key_detour", "unreachable", "key_bypass"}
        assert len(shapes) >= 4
        assert len(grids) >= 44
        assert canonical_scale >= 8


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_h": 14},
        {"grid_w": 8},
        {"grid_w": 18},
        {"route_mode": "plain"},
        {"grid_h": True},
        {"grid_w": "11"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[9] * 9 for _ in range(7)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
