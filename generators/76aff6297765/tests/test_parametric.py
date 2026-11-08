"""Focused prototype semantics and episode contracts; Racket is checked natively."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


CANONICAL_PROGRAM = "(rule! (lambda (g) (zip-halves g (lambda (a b) (if (and (zero? a) (zero? b)) 8 0)) 7)))"
SETTINGS = ({"selection": "all"}, {"selection": "largest"})


@pytest.fixture(scope="module")
def adapter():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/adapter.py"
    assert path.is_file(), "The task-local parametric adapter has not been implemented"
    name = "_parametric_76aff6297765_focused_tests"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_program(adapter):
    assert adapter.program({"selection": "all"}) == CANONICAL_PROGRAM
    assert adapter.program({"selection": "largest"}) != CANONICAL_PROGRAM


def _panels(top, bottom, separator_rows=1):
    return deepcopy(top) + [[7] * len(top[0]) for _ in range(separator_rows)] + deepcopy(bottom)


def _from_mask(mask, separator_rows=1):
    top = [[0 if cell else 2 for cell in row] for row in mask]
    bottom = [[0 if cell else 6 for cell in row] for row in mask]
    return _panels(top, bottom, separator_rows)


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _assert_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_all_marks_only_aligned_joint_zeros_even_with_equal_foregrounds(adapter):
    top = [[0, 0, 2, 2], [2, 0, 2, 0], [0, 2, 0, 2]]
    bottom = [[0, 6, 0, 6], [0, 0, 6, 6], [6, 0, 0, 6]]
    expected = [[8, 0, 0, 0], [0, 8, 0, 0], [0, 0, 8, 0]]
    for foreground in (2, 6):
        recolored = [[foreground if cell else 0 for cell in row] for row in bottom]
        grid = _panels(top, recolored)
        before = deepcopy(grid)
        assert adapter.solve(grid, {"selection": "all"}) == expected
        assert grid == before


def test_default_preserves_every_canonical_label(adapter):
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs("76aff6297765", root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert adapter.solve(pair["input"], {"selection": "all"}) == pair["output"]


def test_largest_preserves_all_ties_and_discards_smaller_components(adapter):
    mask = [[8, 8, 0, 0, 0], [0, 0, 0, 8, 0], [8, 0, 0, 8, 0]]
    expected = [[8, 8, 0, 0, 0], [0, 0, 0, 8, 0], [0, 0, 0, 8, 0]]
    assert adapter.solve(_from_mask(mask), {"selection": "largest"}) == expected
    assert {frozenset(component) for component in adapter.components(mask)} == {
        frozenset({(0, 0), (0, 1)}),
        frozenset({(1, 3), (2, 3)}),
        frozenset({(2, 0)}),
    }


def test_diagonal_contacts_do_not_merge_four_connected_components(adapter):
    mask = [
        [8, 8, 0, 0, 0, 0],
        [0, 0, 8, 0, 0, 0],
        [0, 0, 0, 8, 0, 0],
        [0, 0, 0, 0, 0, 8],
    ]
    expected = [[8, 8, 0, 0, 0, 0], [0] * 6, [0] * 6, [0] * 6]
    assert adapter.solve(_from_mask(mask), {"selection": "largest"}) == expected
    assert sorted(map(len, adapter.components(mask, connectivity=4))) == [1, 1, 1, 2]
    assert sorted(map(len, adapter.components(mask, connectivity=8))) == [1, 4]


def test_empty_and_full_masks_are_total(adapter):
    for mask in ([[0] * 4 for _ in range(3)], [[8] * 4 for _ in range(3)]):
        for settings in SETTINGS:
            assert adapter.solve(_from_mask(mask), settings) == mask
    assert adapter.components([[0, 0], [0, 0]]) == []


def test_component_selection_happens_after_the_joint_zero_mask(adapter):
    # The largest zero component in the top panel is on the left (six cells).
    # Intersecting first leaves a four-cell component on the right and two
    # left singletons. Selecting source components first loses the right answer.
    top = [[0, 0, 2, 2, 0, 0], [0, 0, 2, 2, 0, 0], [0, 0, 2, 2, 2, 2]]
    bottom = [[0, 6, 6, 6, 0, 0], [6, 6, 6, 6, 0, 0], [6, 0, 6, 6, 6, 6]]
    expected = [[0, 0, 0, 0, 8, 8], [0, 0, 0, 0, 8, 8], [0, 0, 0, 0, 0, 0]]
    assert adapter.solve(_panels(top, bottom), {"selection": "largest"}) == expected


def test_demo_and_query_counts_are_independent_with_strict_distinct_grids(adapter):
    for settings in SETTINGS:
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(73, settings, demos=demos, queries=queries)
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["program_solution"] == adapter.program(settings)
                serialized = [json.dumps(grid) for grid in _inputs(episode)]
                assert len(set(serialized)) == demos + queries
                for split in ("train", "test"):
                    for pair in episode[split]:
                        _assert_grid(pair["input"])
                        _assert_grid(pair["output"])


def test_seed_replay_is_deterministic_and_inputs_match_across_settings(adapter):
    all_episode = adapter.generate(99, SETTINGS[0], demos=3, queries=4)
    largest_episode = adapter.generate(99, SETTINGS[1], demos=3, queries=4)
    assert all_episode == adapter.generate(99, SETTINGS[0], demos=3, queries=4)
    assert largest_episode == adapter.generate(99, SETTINGS[1], demos=3, queries=4)
    assert _inputs(all_episode) == _inputs(largest_episode)
    assert _inputs(all_episode) != _inputs(adapter.generate(100, SETTINGS[0], demos=3, queries=4))


def test_demo_and_query_prefixes_do_not_depend_on_requested_counts(adapter):
    from reviewer_support import public_challenge_bytes

    for settings in SETTINGS:
        full = adapter.generate(91, settings, demos=6, queries=4)
        for demos in (2, 3, 6):
            for queries in (1, 2, 4):
                episode = adapter.generate(91, settings, demos=demos, queries=queries)
                assert episode["train"] == full["train"][:demos]
                assert episode["test"] == full["test"][:queries]
        single = adapter.generate(91, settings, demos=3, queries=1)
        multiple = adapter.generate(91, settings, demos=3, queries=4)
        first_turn = {"train": multiple["train"], "test": multiple["test"][:1]}
        assert public_challenge_bytes(single) == public_challenge_bytes(first_turn)


def test_minimum_demonstrations_distinguish_the_declared_settings(adapter):
    for seed in (0, 17):
        all_episode = adapter.generate(seed, SETTINGS[0], demos=2, queries=4)
        largest_episode = adapter.generate(seed, SETTINGS[1], demos=2, queries=4)
        assert any(
            left["output"] != right["output"]
            for left, right in zip(all_episode["train"], largest_episode["train"])
        )


def test_settings_reject_unknown_keys_and_non_string_choices(adapter):
    invalid = (
        {}, {"selection": "unknown"}, {"selection": True}, {"selection": 1.0},
        {"selection": None}, {"selection": "all", "extra": 0}, [], "all",
    )
    grid = _from_mask([[8, 8, 0], [0, 0, 8]])
    for settings in invalid:
        with pytest.raises((ValueError, TypeError)):
            adapter.program(settings)
        with pytest.raises((ValueError, TypeError)):
            adapter.solve(grid, settings)
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(0, settings, demos=3, queries=4)


def test_counts_reject_bool_float_and_out_of_range_requests(adapter):
    for demos in (True, 3.0, 0, 1, 7):
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(0, SETTINGS[0], demos=demos, queries=4)
    for queries in (False, 1.0, 0, 5):
        with pytest.raises((ValueError, TypeError)):
            adapter.generate(0, SETTINGS[0], demos=3, queries=queries)


def test_four_queries_include_substantive_exact_30_by_30_inputs(adapter):
    for settings in SETTINGS:
        episode = adapter.generate(17, settings, demos=3, queries=4)
        large = [pair for pair in episode["test"]
                 if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
        assert large, "Four-query episodes must cover the lawful exact 30x30 boundary"
        for pair in large:
            grid = pair["input"]
            separators = [index for index, row in enumerate(grid) if row == [7] * 30]
            assert separators == [14, 15]
            top, bottom = grid[:14], grid[16:]
            assert sum(a == b == 0 for row_a, row_b in zip(top, bottom)
                       for a, b in zip(row_a, row_b)) >= 100
            assert all(sum(cell != 0 for row in panel for cell in row) >= 100
                       for panel in (top, bottom))
            assert len(pair["output"]) == 14
            assert all(len(row) == 30 for row in pair["output"])


def test_public_projection_contains_only_demonstrations_and_query_inputs(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(23, SETTINGS[1], demos=3, queries=4)
    payload = public_challenge_bytes(episode)
    visible = json.loads(payload)
    assert visible == {
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
    assert public_challenge_id(episode) == hashlib.sha256(payload).hexdigest()
    private_change = deepcopy(episode)
    private_change.update(settings={"selection": "private"}, seed=999, program_solution="private")
    private_change["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(private_change) == payload
    demo_change = deepcopy(episode)
    old = demo_change["train"][0]["output"][0][0]
    demo_change["train"][0]["output"][0][0] = 1 if old != 1 else 2
    assert public_challenge_id(demo_change) != public_challenge_id(episode)
