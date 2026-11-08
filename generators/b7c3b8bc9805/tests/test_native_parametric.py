"""Bounded public-contract tests for the task-local native parametric adapter."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


ROOT = find_root(__file__)
TASK_HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = TASK_HOME / "workspace/parametric/adapter.py"
PROTOTYPE_PATH = TASK_HOME / "workspace/parametric/prototype.py"
PHASE_RELATIONS = ("same", "opposite")
COUNT_REQUESTS = ((3, 4), (4, 4), (6, 4), (3, 1))


def _load_module(path: Path, name: str):
    assert path.is_file(), f"native parametric source has not been built: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _load_adapter():
    # Resolve this task's source directly, regardless of other loaded adapters.
    return _load_module(ADAPTER_PATH, "native_b7c3b8bc9805_adapter_under_test")


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


@pytest.fixture(scope="module")
def prototype():
    return _load_module(PROTOTYPE_PATH, "native_b7c3b8bc9805_reference_prototype")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


@pytest.fixture(
    scope="module",
    params=COUNT_REQUESTS,
    ids=[f"demos-{demos}-queries-{queries}" for demos, queries in COUNT_REQUESTS],
)
def matched_episodes(request, adapter):
    demos, queries = request.param
    episodes = {
        relation: adapter.generate(
            seed=17,
            settings={"phase_relation": relation},
            demos=demos,
            queries=queries,
        )
        for relation in PHASE_RELATIONS
    }
    return demos, queries, episodes


def _assert_arc_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def _assert_frame_grammar(grid):
    """Check the visible grammar without borrowing the adapter's parser."""
    _assert_arc_grid(grid)
    gray = {
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell == 5
    }
    assert gray, "input needs a gray frame"
    top, bottom = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    assert bottom - top >= 3 and right - left >= 3
    border = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    assert gray == border, "gray cells must form exactly one complete frame"
    assert all(
        grid[r][c] == 0
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
    )
    markers = [
        (r, c, cell)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell not in (0, 5)
    ]
    assert len(markers) == 2 and markers[0][2] != markers[1][2]
    assert all(
        (r < top or r > bottom) and (c < left or c > right)
        for r, c, _ in markers
    ), "both singleton markers must lie in outside corner regions"
    return top, bottom, left, right


def test_same_program_is_the_exact_canonical_default(prototype):
    # Load inside this test so an absent adapter is an explicit assertion failure.
    adapter = _load_adapter()
    assert adapter.program({"phase_relation": "same"}) == prototype.canonical_source(
        root=ROOT
    )


def test_supported_counts_return_distinct_lawful_pairs(adapter, matched_episodes):
    demos, queries, episodes = matched_episodes
    for relation, episode in episodes.items():
        assert type(episode["train"]) is list and len(episode["train"]) == demos
        assert type(episode["test"]) is list and len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program(
            {"phase_relation": relation}
        )
        pairs = episode["train"] + episode["test"]
        inputs = []
        for pair in pairs:
            grid, output = pair["input"], pair["output"]
            top, bottom, left, right = _assert_frame_grammar(grid)
            _assert_arc_grid(output)
            assert (len(output), len(output[0])) == (len(grid), len(grid[0]))
            assert all(
                output[r][c] == grid[r][c]
                for r in range(len(grid))
                for c in range(len(grid[0]))
                if not (top < r < bottom and left < c < right)
            ), "the same/opposite rules must preserve frame and exterior cells"
            inputs.append(tuple(tuple(row) for row in grid))
        assert len(set(inputs)) == demos + queries


def test_phase_settings_share_inputs_and_have_distinct_labels(matched_episodes):
    _, _, episodes = matched_episodes
    for split in ("train", "test"):
        same, opposite = episodes["same"][split], episodes["opposite"][split]
        assert [pair["input"] for pair in same] == [pair["input"] for pair in opposite]
        assert all(
            first["output"] != second["output"]
            for first, second in zip(same, opposite, strict=True)
        ), "demonstration labels must identify the selected phase relation"


def test_queries_include_a_large_active_frame_instead_of_padding(matched_episodes):
    _, _, episodes = matched_episodes
    for episode in episodes.values():
        large_queries = [
            pair for pair in episode["test"]
            if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
        ]
        assert large_queries, "each supported query count must include a 30x30 input"
        for pair in large_queries:
            top, bottom, left, right = _assert_frame_grammar(pair["input"])
            interior_area = (bottom - top - 1) * (right - left - 1)
            assert interior_area >= 400, "large queries need a genuinely large frame"
            changed_inside = sum(
                pair["input"][r][c] != pair["output"][r][c]
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
            )
            assert changed_inside == interior_area


def test_every_claimed_label_is_executed_by_racket(matched_episodes, prototype, bridge):
    _, _, episodes = matched_episodes
    for episode in episodes.values():
        for pair in episode["train"] + episode["test"]:
            assert prototype.execute_rule(
                episode["program_solution"], pair["input"], bridge=bridge
            ) == pair["output"]


@pytest.mark.parametrize("relation", PHASE_RELATIONS)
def test_repeated_generation_is_deterministic(adapter, relation):
    request = {
        "seed": 29,
        "settings": {"phase_relation": relation},
        "demos": 3,
        "queries": 4,
    }
    assert adapter.generate(**request) == adapter.generate(**request)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("seed", True), ("seed", False), ("seed", 17.0), ("seed", "17"),
        ("demos", True), ("demos", False), ("demos", 3.0), ("demos", "3"),
        ("queries", True), ("queries", False), ("queries", 1.0), ("queries", "1"),
    ],
)
def test_seed_and_counts_are_literal_integers(adapter, argument, value):
    request = {
        "seed": 17,
        "settings": {"phase_relation": "same"},
        "demos": 3,
        "queries": 1,
    }
    request[argument] = value
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**request)


@pytest.mark.parametrize(
    ("demos", "queries"),
    [(-1, 1), (0, 1), (1, 1), (2, 1), (7, 1), (3, -1), (3, 0), (3, 5)],
)
def test_counts_outside_the_declared_bounds_are_rejected(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(17, {"phase_relation": "same"}, demos, queries)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"other": "same"},
        {"phase_relation": "same", "unexpected": 1},
        {"phase_relation": "rotated"},
        {"phase_relation": True},
        {"phase_relation": 0},
        {"phase_relation": None},
        None,
        "same",
    ],
)
def test_missing_unknown_or_invalid_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(17, settings, 3, 1)
