"""Focused contract and teaching checks for the task-local relay prototype.

These checks do not grant canonical approval or replace protected Racket
qualification. Hand-built expected grids below are independent of the adapter.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog


TASK_HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = TASK_HOME / "workspace" / "parametric" / "adapter.py"
ROUTINGS = ("direct", "relay")


def test_adapter_exists():
    assert ADAPTER_PATH.is_file(), "The task-local native relay adapter is missing"


@pytest.mark.parametrize("seed", [0, 17])
def test_two_relay_demos_do_not_teach_a_constant_final_direction(adapter, seed):
    episode = adapter.generate(seed, {"routing": "relay"}, 2, 4)
    directions = set()
    for pair in episode["train"]:
        output = pair["output"]
        center = len(output) // 2
        direction = next(((-1 if r < center else 1, -1 if c < center else 1)
                          for r, row in enumerate(output) for c, value in enumerate(row)
                          if value != 7 and (r, c) != (center, center)), None)
        assert direction is not None
        directions.add(direction)
    assert len(directions) == 2, "Both demos support a query-conflicting constant final ray"


@pytest.mark.parametrize("seed", [0, 17])
def test_two_demos_do_not_identify_relay_by_a_fixed_color_count_offset(adapter, seed):
    from collections import Counter
    episode = adapter.generate(seed, {"routing": "relay"}, 2, 4)
    offsets = set()
    for pair in episode["train"]:
        grid = pair["input"]
        center = len(grid) // 2
        key = grid[center][center]
        selected = pair["output"][center][center]
        counts = Counter(value for row in grid for value in row)
        offsets.add(counts[selected] - counts[key])
    assert len(offsets) == 2, "Color-count arithmetic bypasses the first ray in both demos"


@pytest.mark.parametrize("seed", [0, 17])
def test_ray_population_shortcut_cannot_fit_both_direct_demos(adapter, seed):
    episode = adapter.generate(seed, {"routing": "direct"}, 2, 4)
    matches = []
    dirs = ((-1, -1), (-1, 1), (1, 1), (1, -1))
    for pair in episode["train"]:
        grid = pair["input"]
        n, center = len(grid), len(grid)//2
        key = grid[center][center]
        hit_counts = [sum(grid[center+k*dr][center+k*dc] not in (7, key)
                          for k in range(1, n) if 0 <= center+k*dr < n and 0 <= center+k*dc < n)
                      for dr, dc in dirs]
        dr, dc = dirs[max(range(4), key=lambda i: hit_counts[i])]
        predicted = [[key if ((r-center)*dc == (c-center)*dr and (r-center)*dr >= 0) else 7
                      for c in range(n)] for r in range(n)]
        matches.append(predicted == pair["output"])
    assert not all(matches), "Ray occupancy reveals direction without the key centroid"


@pytest.fixture(scope="module")
def adapter():
    """Load this task's adapter by exact adjacent path, never a cached sibling."""
    assert ADAPTER_PATH.is_file(), "The task-local native relay adapter is missing"
    spec = importlib.util.spec_from_file_location(
        "_test_parametric_relay_85d3a8e1aa7f", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def two_demo_episodes(adapter):
    return {
        (seed, routing): adapter.generate(seed, {"routing": routing}, 2, 4)
        for seed in (0, 17)
        for routing in ROUTINGS
    }


def _assert_grid(grid):
    assert isinstance(grid, list) and grid
    assert isinstance(grid[0], list) and grid[0]
    width = len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)


def _inputs(pairs):
    return [pair["input"] for pair in pairs]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_direct_program_preserves_exact_canonical_source(adapter):
    canonical = Catalog().get("85d3a8e1aa7f")["variants"][0]["program_solution"]
    assert adapter.program({"routing": "direct"}) == canonical
    assert adapter.program({"routing": "relay"}) != canonical


def test_first_hit_skips_key_and_recomputes_selected_color_centroid(adapter):
    # Key 1's centroid is BR. The key at (5,5) must be skipped, then 2 at
    # (6,6) is selected before 3 at (7,7). Color 2's centroid is instead TL.
    grid = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (5, 5), (8, 7), (7, 8), (8, 8)):
        grid[row][col] = 1
    for row, col in ((6, 6), (0, 0), (0, 1), (1, 0), (1, 1), (2, 1)):
        grid[row][col] = 2
    grid[7][7] = 3
    grid[3][5] = 3  # A closer hit on the wrong ray must not be followed.

    direct_expected = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (5, 5), (6, 6), (7, 7), (8, 8)):
        direct_expected[row][col] = 1
    relay_expected = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (3, 3), (2, 2), (1, 1), (0, 0)):
        relay_expected[row][col] = 2

    assert adapter.predict(grid, "direct") == direct_expected
    assert adapter.predict(grid, "relay") == relay_expected


def test_missing_eligible_relay_falls_back_to_key_color(adapter):
    grid = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (5, 5), (8, 8)):
        grid[row][col] = 6
    expected = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (5, 5), (6, 6), (7, 7), (8, 8)):
        expected[row][col] = 6
    assert adapter.predict(grid, "relay") == expected


@pytest.mark.parametrize("routing", ROUTINGS)
def test_even_grid_uses_floor_center_and_positive_ties_including_key_zero(adapter, routing):
    grid = [[7] * 30 for _ in range(30)]
    grid[15][15] = 0
    expected = [[7] * 30 for _ in range(30)]
    for row in range(15, 30):
        expected[row][row] = 0
    assert adapter.predict(grid, routing) == expected


@pytest.mark.parametrize("demos", [True, False, 1, 7, 2.0, "2", None])
def test_invalid_demo_count_is_rejected(adapter, demos):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"routing": "direct"}, demos, 4)


@pytest.mark.parametrize("queries", [True, False, 0, 5, 1.0, "1", None])
def test_invalid_query_count_is_rejected(adapter, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"routing": "direct"}, 2, queries)


@pytest.mark.parametrize(
    "settings",
    [
        {"routing": "unknown"},
        {"routing": True},
        {"routing": ["direct"]},
        {"routing": "direct", "extra": 1},
    ],
)
def test_unknown_or_untyped_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 2, 4)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("routing", ROUTINGS)
def test_generated_episode_counts_grids_and_novelty(adapter, two_demo_episodes, seed, routing):
    episode = two_demo_episodes[(seed, routing)]
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"routing": routing})
    assert [len(pair["input"]) for pair in episode["test"]] == [9, 19, 27, 30]
    pairs = episode["train"] + episode["test"]
    for pair in pairs:
        _assert_grid(pair["input"])
        _assert_grid(pair["output"])
        assert 9 <= len(pair["input"]) <= 30
        assert len(pair["input"]) == len(pair["input"][0])
        assert len(pair["output"]) == len(pair["input"])
        assert len(pair["output"][0]) == len(pair["input"][0])
    assert len({_grid_key(pair["input"]) for pair in pairs}) == len(pairs)


@pytest.mark.parametrize("seed", [0, 17])
def test_settings_use_matched_inputs_and_demonstrations_distinguish_them(two_demo_episodes, seed):
    direct = two_demo_episodes[(seed, "direct")]
    relay = two_demo_episodes[(seed, "relay")]
    assert _inputs(direct["train"]) == _inputs(relay["train"])
    assert _inputs(direct["test"]) == _inputs(relay["test"])
    assert any(
        direct_pair["output"] != relay_pair["output"]
        for direct_pair, relay_pair in zip(direct["train"], relay["train"], strict=True)
    )


@pytest.mark.parametrize("seed", [0, 17])
def test_query_count_preserves_visible_first_turn(adapter, two_demo_episodes, seed):
    short = adapter.generate(seed, {"routing": "relay"}, 2, 1)
    full = two_demo_episodes[(seed, "relay")]
    assert short["train"] == full["train"]
    assert short["test"] == full["test"][:1]


@pytest.mark.parametrize("routing", ROUTINGS)
@pytest.mark.parametrize("seed", [4, 11, 23])
def test_maximum_demo_count_does_not_change_query_count(adapter, routing, seed):
    episode = adapter.generate(seed, {"routing": routing}, 6, 1)
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == len(pairs)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("routing", ROUTINGS)
def test_two_demos_refute_query_conflicting_declared_rivals(
    adapter, two_demo_episodes, seed, routing
):
    episode = two_demo_episodes[(seed, routing)]
    demo_predictions = [
        adapter.rival_predictions(pair["input"], routing) for pair in episode["train"]
    ]
    query_predictions = [
        adapter.rival_predictions(pair["input"], routing) for pair in episode["test"]
    ]
    names = set(demo_predictions[0])
    assert names, "The finite teaching audit must actually name alternative rules"
    for predictions in demo_predictions + query_predictions:
        assert set(predictions) == names
        for output in predictions.values():
            _assert_grid(output)
    query_conflicting = {
        name
        for name in names
        if any(
            predictions[name] != pair["output"]
            for pair, predictions in zip(episode["test"], query_predictions, strict=True)
        )
    }
    assert query_conflicting, "An audit containing only the gold rule is vacuous"
    for name in sorted(query_conflicting):
        assert any(
            predictions[name] != pair["output"]
            for pair, predictions in zip(episode["train"], demo_predictions, strict=True)
        ), f"Seed {seed}, {routing}: rival {name!r} fits both demos but changes a query"


@pytest.mark.parametrize("seed", [0, 17])
def test_thirty_square_query_has_content_across_canvas(two_demo_episodes, seed):
    grid = two_demo_episodes[(seed, "relay")]["test"][3]["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    foreground = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7]
    assert len(foreground) >= 80
    assert min(r for r, _ in foreground) <= 2
    assert max(r for r, _ in foreground) >= 27
    assert min(c for _, c in foreground) <= 2
    assert max(c for _, c in foreground) >= 27
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        assert sum((r - 15) * dr > 0 and (c - 15) * dc > 0 for r, c in foreground) >= 10
