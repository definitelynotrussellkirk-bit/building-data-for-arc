"""Teaching schedule regressions against the selected module's declarations.

Canonical answers are authoring data; this file is closed during solve episodes.
All output geometry comes from the independent public-contract test helper.
"""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs


HELPER_SPEC = importlib.util.spec_from_file_location(
    "guide_geometry_probe", Path(__file__).with_name("test_public_contract.py"))
probe = importlib.util.module_from_spec(HELPER_SPEC)
HELPER_SPEC.loader.exec_module(probe)
gen = probe.gen
PAIRS = canonical_pairs(probe.TASK_ID, root=probe.ROOT)
BANDS = (None, "easy", "medium", "hard")


def declaration(namespace):
    result = getattr(gen, namespace, None)
    assert isinstance(result, dict) and result, f"missing executable {namespace}"
    assert all(isinstance(name, str) and callable(rule) for name, rule in result.items())
    return result


def rivals():
    return [(namespace, name, rule)
            for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
            for name, rule in declaration(namespace).items()]


def inspect_observer(grid, requested=None):
    observed = gen.observe_overrides(grid)
    assert isinstance(observed, dict)
    assert observed["grid_h"] == len(grid)
    assert observed["grid_w"] == len(grid[0])
    marks, guide, eligible, outside, output = probe.geometry(grid)
    r0, c0, r1, c1 = guide
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    perimeter = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)}
    actual_style = ("two_corners" if len(marks) == 2 else
                    "corners" if marks == corners else
                    "full" if marks == perimeter else "dashed")
    assert observed["frame_style"] == actual_style
    if actual_style == "dashed":
        assert corners < marks < perimeter
    sticks_out = any(not (r0 <= r <= r1 and c0 <= c <= c1) for r, c in eligible[0])
    center_out = any(any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in obj)
                     for obj in outside)
    texture = observed["texture"]
    assert texture in {"plain", "multi_inside", "sticks_out", "center_out", "teaching"}
    if texture in ("multi_inside", "teaching"):
        assert len(eligible) >= 2
    if texture in ("sticks_out", "teaching"):
        assert sticks_out
    if texture in ("center_out", "teaching"):
        assert center_out
    if texture == "plain":
        assert not sticks_out
    if requested is not None:
        assert all(observed[key] == value for key, value in requested.items())
    assert gen._mirror(grid) == output
    return observed, output


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        expected = probe.geometry(pair["input"])[-1]
        assert expected == pair["output"]
        assert gen._mirror(pair["input"]) == expected
        for name, rule in declaration("CANONICAL_SHORTCUTS").items():
            assert rule(pair["input"]) == expected, (name, pair["split"], pair["pair_index"])


def test_all_declared_teaching_contracts_are_executable():
    rivals()
    profiles = getattr(gen, "SCHEDULE_PROFILES", None)
    assert profiles and len(set(profiles)) >= 2
    assert "teaching" in profiles


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", range(12))
def test_teaching_draws_refute_each_declared_rival(seed, band):
    declared = rivals()
    for index in (0, 1):
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        observed, expected = inspect_observer(grid)
        assert observed["texture"] == "teaching", (seed, index, band)
        for namespace, name, rule in declared:
            assert rule(grid) != expected, (seed, index, band, namespace, name)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", range(12))
def test_default_four_pair_windows_teach_every_query_rotation(seed, band):
    declared = rivals()
    grids = [gen.generate(seed, index, difficulty=band) for index in range(12)]
    observations = [inspect_observer(grid) for grid in grids]
    for index, (observed, _) in enumerate(observations):
        assert (observed["texture"] == "teaching") == (index % 3 in (0, 1)), (seed, band, index)
    for start in range(9):
        window = grids[start:start + 4]
        outputs = [probe.geometry(grid)[-1] for grid in window]
        flags = [observations[start + position][0]["texture"] == "teaching" for position in range(4)]
        assert sum(flags) >= 2, (seed, band, start)
        for query in range(4):
            demonstrations = [position for position in range(4) if position != query]
            assert any(flags[position] for position in demonstrations)
            for namespace, name, rule in declared:
                assert any(rule(window[position]) != outputs[position] for position in demonstrations), (
                    seed, band, start, query, namespace, name)


@pytest.mark.parametrize("texture", ["plain", "multi_inside", "sticks_out", "center_out", "teaching"])
@pytest.mark.parametrize("style", ["corners", "two_corners", "dashed", "full"])
def test_exact_observer_for_joint_style_texture_overrides(texture, style):
    requested = dict(texture=texture, frame_style=style)
    try:
        grid = gen.generate(1441, 0, **requested)
    except ValueError:
        assert probe.declared_incompatibility(requested)
        return
    inspect_observer(grid, requested)
