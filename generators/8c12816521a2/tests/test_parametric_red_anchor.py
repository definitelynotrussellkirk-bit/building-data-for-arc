"""Behavioral contract for the opt-in red-band anchor family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK = "8c12816521a2"
HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "Native red-anchor parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("red_anchor_test_adapter", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = set()
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def test_default_program_is_exact_canonical_source(adapter):
    assert adapter.program({"red_anchor": "far_edge"}) == _canonical_program()


def test_literal_far_and_separator_edge_outputs_in_both_orientations(adapter):
    vertical_left = [
        [0, 0, 0, 0, 8, 0, 2, 2, 0, 0, 0],
        [0, 4, 4, 0, 8, 0, 2, 2, 2, 0, 0],
        [0, 0, 0, 0, 8, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 8, 0, 2, 2, 2, 2, 0],
        [0, 0, 4, 0, 8, 0, 2, 2, 0, 0, 0],
    ]
    far_left = [
        vertical_left[0],
        [0, 3, 3, 4, 8, 8, 8, 8, 2, 2, 2],
        vertical_left[2],
        vertical_left[3],
        [0, 0, 3, 4, 8, 8, 8, 8, 8, 2, 2],
    ]
    separator_left = [
        vertical_left[0],
        [0, 3, 3, 4, 8, 2, 2, 2, 8, 8, 8],
        vertical_left[2],
        vertical_left[3],
        [0, 0, 3, 4, 8, 2, 2, 8, 8, 8, 8],
    ]

    normalized_right = [
        [0, 2, 0, 0, 0, 8, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 8, 0, 4, 4, 0, 0],
        [0, 2, 2, 2, 0, 8, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 8, 0, 0, 4, 0, 0],
        [0, 2, 2, 2, 2, 8, 0, 0, 0, 0, 0],
    ]
    far_right = [
        normalized_right[0],
        [2, 2, 8, 8, 8, 8, 4, 3, 3, 0, 0],
        normalized_right[2],
        [2, 8, 8, 8, 8, 8, 4, 4, 3, 0, 0],
        normalized_right[4],
    ]
    separator_right = [
        normalized_right[0],
        [8, 8, 8, 2, 2, 8, 4, 3, 3, 0, 0],
        normalized_right[2],
        [8, 8, 8, 8, 2, 8, 4, 4, 3, 0, 0],
        normalized_right[4],
    ]
    horizontal_right = _transpose(normalized_right)

    snapshot = copy.deepcopy(vertical_left)
    assert adapter.solve_python(vertical_left, "far_edge") == far_left
    assert adapter.solve_python(vertical_left, "separator_edge") == separator_left
    assert adapter.solve_python(horizontal_right, "far_edge") == _transpose(far_right)
    assert adapter.solve_python(horizontal_right, "separator_edge") == _transpose(separator_right)
    assert vertical_left == snapshot
    assert far_left != separator_left


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _episode_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _normalized_scene_facts(grid):
    horizontal = any(all(value == 8 for value in row) for row in grid)
    normalized = _transpose(grid) if horizontal else [row[:] for row in grid]
    separator = next(
        col
        for col in range(len(normalized[0]))
        if all(row[col] == 8 for row in normalized)
    )
    left = sum(value == 4 for row in normalized for value in row[:separator])
    right = sum(value == 4 for row in normalized for value in row[separator + 1 :])
    return {
        "orientation": "horizontal" if horizontal else "vertical",
        "yellow_side": "left" if left > right else "right",
        "separator": separator,
    }


@pytest.mark.parametrize("anchor", ["far_edge", "separator_edge"])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generate_has_exact_counts_distinct_inputs_and_setting_specific_labels(adapter, anchor, demos):
    settings = {"red_anchor": anchor}
    episode = adapter.generate(73, settings, demos, 4)
    assert set(episode) >= {"train", "test", "program_solution"}
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(settings)

    inputs = _episode_inputs(episode)
    assert len({_frozen(grid) for grid in inputs}) == demos + 4
    other = "separator_edge" if anchor == "far_edge" else "far_edge"
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == adapter.solve_python(pair["input"], anchor)
        assert pair["output"] != adapter.solve_python(pair["input"], other)


def test_inputs_are_setting_neutral_and_demo_prefix_query_stable(adapter):
    small_far = adapter.generate(811, {"red_anchor": "far_edge"}, 2, 4)
    large_far = adapter.generate(811, {"red_anchor": "far_edge"}, 6, 4)
    large_near = adapter.generate(811, {"red_anchor": "separator_edge"}, 6, 4)

    assert [pair["input"] for pair in small_far["train"]] == [
        pair["input"] for pair in large_far["train"][:2]
    ]
    assert [pair["input"] for pair in small_far["test"]] == [
        pair["input"] for pair in large_far["test"]
    ]
    assert _episode_inputs(large_far) == _episode_inputs(large_near)
    assert all(
        far["output"] != near["output"]
        for far, near in zip(
            large_far["train"] + large_far["test"],
            large_near["train"] + large_near["test"],
        )
    )


def test_minimum_lesson_covers_both_orientations_and_yellow_sides(adapter):
    episode = adapter.generate(0, {"red_anchor": "far_edge"}, 2, 4)
    facts = [_normalized_scene_facts(pair["input"]) for pair in episode["train"]]
    assert {fact["orientation"] for fact in facts} == {"vertical", "horizontal"}
    assert {fact["yellow_side"] for fact in facts} == {"left", "right"}

    all_grids = _episode_inputs(adapter.generate(0, {"red_anchor": "far_edge"}, 6, 4))
    dimensions = {len(grid) for grid in all_grids} | {len(grid[0]) for grid in all_grids}
    assert min(dimensions) == 15
    assert max(dimensions) == 30


def test_generate_is_deterministic_fresh_and_global_rng_isolated(adapter):
    import random

    random.seed(91_557)
    state = random.getstate()
    first = adapter.generate(2**20, {"red_anchor": "separator_edge"}, 6, 4)
    assert random.getstate() == state
    second = adapter.generate(2**20, {"red_anchor": "separator_edge"}, 6, 4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    snapshot = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(2**20, {"red_anchor": "separator_edge"}, 6, 4) == snapshot
    assert adapter.generate(2**20 + 1, {"red_anchor": "separator_edge"}, 6, 4) != snapshot


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.5, "0"])
def test_generate_rejects_invalid_seed(adapter, seed):
    with pytest.raises(ValueError, match="seed"):
        adapter.generate(seed, {"red_anchor": "far_edge"}, 2, 4)


@pytest.mark.parametrize("demos", [True, 1, 7, 2.0])
def test_generate_rejects_invalid_demo_count(adapter, demos):
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"red_anchor": "far_edge"}, demos, 4)


@pytest.mark.parametrize("queries", [True, 0, 3, 5, 4.0])
def test_generate_rejects_non_four_query_count(adapter, queries):
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"red_anchor": "far_edge"}, 2, queries)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"red_anchor": "unknown"},
        {"red_anchor": "far_edge", "extra": 1},
        {"red_anchor": True},
        "far_edge",
    ],
)
def test_program_and_generate_reject_undeclared_settings(adapter, settings):
    with pytest.raises(ValueError, match="red_anchor|settings"):
        adapter.program(settings)
    with pytest.raises(ValueError, match="red_anchor|settings"):
        adapter.generate(0, settings, 2, 4)


def _load_audit():
    path = HOME / "workspace/parametric/audit.py"
    assert path.is_file(), "Bounded shortcut audit has not been built"
    spec = importlib.util.spec_from_file_location("red_anchor_test_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("anchor", ["far_edge", "separator_edge"])
def test_two_demo_lesson_rejects_declared_setting_and_named_shortcuts(seed, anchor):
    audit = _load_audit()
    report = audit.teaching_audit(seed, anchor, demos=2)
    expected = {
        "other_anchor",
        "fixed_count_one",
        "global_max_count",
        "yellow_count",
        "all_lanes",
        "no_green",
        "wrong_tip",
        "no_transpose",
    }
    assert report["query_answers_used"] is False
    assert set(report["rejected_by_demo"]) == expected
    assert report["survivors"] == []
    assert all(report["rejected_by_demo"][name] for name in expected)
    assert set(report["demo_features"]) >= {
        "vertical", "horizontal", "yellow_left", "yellow_right",
        "mixed_red_counts", "multi_yellow", "nontrigger_lanes",
    }


def test_public_turn_masks_private_fields_and_reveals_exactly_one_query(adapter):
    episode = adapter.generate(31, {"red_anchor": "separator_edge"}, 3, 4)
    first = adapter.public_turn(episode, 0)
    second = adapter.public_turn(episode, 1)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3 and len(first["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert set(first["test"][0]) == {"input"}
    assert public_challenge_id(first) != public_challenge_id(second)

    changed_private = copy.deepcopy(episode)
    changed_private["settings"] = {"red_anchor": "hidden-change"}
    changed_private["program_solution"] = "hidden-program"
    changed_private["seed"] = 999
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(adapter.public_turn(changed_private, 0)) == public_challenge_bytes(first)

    first["train"][0]["input"][0][0] = 9
    assert adapter.public_turn(episode, 0) != first
    for bad in (True, -1, 4, 1.0):
        with pytest.raises((TypeError, IndexError)):
            adapter.public_turn(episode, bad)
