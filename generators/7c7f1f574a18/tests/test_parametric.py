"""Public-contract regressions for the task-local hole-area prototype.

Literal grids test topology independently of the Python mirror. The bounded
episode census checks sampling, settings, and demonstration identification;
native qualification separately re-executes the labels in protected Racket.
Exact path imports work both in this checkout and in the staged task runner.
"""
from __future__ import annotations

from collections import Counter
import copy
import importlib.util
import os
from pathlib import Path
import py_compile
import random
import sys

import pytest


TASK_ID = "7c7f1f574a18"
TASK = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK / "workspace" / "parametric"


def _load_path(name: str, path: Path):
    assert path.is_file(), f"Missing required parametric module: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_path(f"test_adapter_{TASK_ID}", PARAMETRIC / "adapter.py")


@pytest.fixture(scope="module")
def prototype():
    return _load_path(f"test_prototype_{TASK_ID}", PARAMETRIC / "prototype.py")


@pytest.fixture(scope="module")
def canonical():
    # Find this test's own library or copied runtime, independent of cwd and
    # package caches. Shared readers own canonical row/string normalization.
    support_path = next(
        parent / relative
        for parent in TASK.parents
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py")
        if (parent / relative).is_file()
    )
    support = _load_path(f"test_reviewer_support_{TASK_ID}", support_path)
    root = support.find_root(__file__)
    reader_path = next(
        root / relative
        for relative in (
            "src/core/canonical_pairs.py",
            "shared/runtime/src/core/canonical_pairs.py",
        )
        if (root / relative).is_file()
    )
    reader = _load_path(
        f"test_canonical_reader_{TASK_ID}",
        reader_path,
    )
    ledger = support.canonical_path(root)
    selected = next(
        row for row in reader.iter_task_rows(TASK_ID, ledger)
        if row.get("program_solution")
    )
    return selected["program_solution"], reader.load_task_pairs(TASK_ID, ledger)


def _grid(*rows: str) -> list[list[int]]:
    assert rows and len({len(row) for row in rows}) == 1
    return [[int(cell) for cell in row] for row in rows]


def _signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _assert_arc_grid(grid: object) -> None:
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert all(type(row) is list for row in grid)
    assert 1 <= len(grid[0]) <= 30
    assert all(len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


# Every object below has a 5x5 bbox and 23 foreground cells. Only the
# four-connected partition of its two missing cells changes. The separated
# holes touch diagonally, so treating complement connectivity as eight-neighbor
# would also be detected. Expected placements are hand-drawn, not solver-built.
HOLE_TWO = _grid(
    "4444444444444",
    "4444444444444",
    "4444111114444",
    "4444111114444",
    "4444144114444",
    "4444111114444",
    "4444111114444",
    "4444444444444",
    "4444444444444",
)
HOLE_TWO_LEFT = _grid(
    "4444444444444",
    "4444444444444",
    "2222244444444",
    "2222244444444",
    "2442244444444",
    "2222244444444",
    "2222244444444",
    "4444444444444",
    "4444444444444",
)
HOLE_TWO_RIGHT = _grid(
    "4444444444444",
    "4444444444444",
    "4444444433333",
    "4444444433333",
    "4444444434433",
    "4444444433333",
    "4444444433333",
    "4444444444444",
    "4444444444444",
)
TWO_SINGLETON_HOLES = _grid(
    "4444444444444",
    "4444444444444",
    "4444111114444",
    "4444141114444",
    "4444114114444",
    "4444111114444",
    "4444111114444",
    "4444444444444",
    "4444444444444",
)
SINGLETONS_LEFT = _grid(
    "4444444444444",
    "4444444444444",
    "2222244444444",
    "2422244444444",
    "2242244444444",
    "2222244444444",
    "2222244444444",
    "4444444444444",
    "4444444444444",
)
SINGLETONS_RIGHT = _grid(
    "4444444444444",
    "4444444444444",
    "4444444433333",
    "4444444434333",
    "4444444433433",
    "4444444433333",
    "4444444433333",
    "4444444444444",
    "4444444444444",
)
OPEN_TWO_CELL_NOTCH = _grid(
    "4444444444444",
    "4444444444444",
    "4444111114444",
    "4444111114444",
    "4444441114444",
    "4444111114444",
    "4444111114444",
    "4444444444444",
    "4444444444444",
)
NOTCH_RIGHT = _grid(
    "4444444444444",
    "4444444444444",
    "4444444433333",
    "4444444433333",
    "4444444444333",
    "4444444433333",
    "4444444433333",
    "4444444444444",
    "4444444444444",
)


def test_default_program_preserves_selected_canonical_bytes(adapter, canonical) -> None:
    source, _ = canonical
    for settings in ({}, {"min_hole_area": 1}):
        actual = adapter.program(settings)
        assert type(actual) is str
        assert actual.encode("utf-8") == source.encode("utf-8")


def test_adapter_executes_current_adjacent_source_despite_timestamp_cache(tmp_path) -> None:
    for filename in ("adapter.py", "prototype.py", "canonical.rkt"):
        (tmp_path / filename).write_bytes((PARAMETRIC / filename).read_bytes())
    source_path = tmp_path / "prototype.py"
    source_before = source_path.read_bytes()
    stamp = source_path.stat()
    py_compile.compile(
        str(source_path), doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
    )
    old = b"DEMO_SIZES = ((19, 21),"
    new = b"DEMO_SIZES = ((20, 21),"
    assert source_before.count(old) == 1
    source_after = source_before.replace(old, new)
    assert len(source_before) == len(source_after)
    source_path.write_bytes(source_after)
    os.utime(source_path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    copied = _load_path(f"test_exact_bytes_adapter_{TASK_ID}_{tmp_path.name}", tmp_path / "adapter.py")
    episode = copied.generate(14, {}, demos=2, queries=1)
    assert len(episode["train"][0]["input"]) == 20


def test_canonical_pairs_stay_exact_at_default_threshold(prototype, canonical) -> None:
    _, pairs = canonical
    assert pairs
    for pair in pairs:
        assert prototype.solve(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "source, threshold, expected",
    [
        (HOLE_TWO, 1, HOLE_TWO_LEFT),
        (HOLE_TWO, 2, HOLE_TWO_LEFT),
        (HOLE_TWO, 3, HOLE_TWO_RIGHT),
        (TWO_SINGLETON_HOLES, 1, SINGLETONS_LEFT),
        (TWO_SINGLETON_HOLES, 2, SINGLETONS_RIGHT),
        (TWO_SINGLETON_HOLES, 3, SINGLETONS_RIGHT),
        (OPEN_TWO_CELL_NOTCH, 1, NOTCH_RIGHT),
        (OPEN_TWO_CELL_NOTCH, 2, NOTCH_RIGHT),
        (OPEN_TWO_CELL_NOTCH, 3, NOTCH_RIGHT),
    ],
    ids=["hole2-t1", "hole2-t2", "hole2-t3", "two-holes-t1", "two-holes-t2",
         "two-holes-t3", "open-notch-t1", "open-notch-t2", "open-notch-t3"],
)
def test_hole_region_partition_controls_docking(prototype, source, threshold, expected) -> None:
    before = copy.deepcopy(source)
    assert prototype.solve(source, threshold=threshold) == expected
    assert source == before


def test_three_cell_hole_meets_the_highest_threshold(prototype) -> None:
    source = _grid(
        "00000000000", "00011111000", "00011111000", "00010001000",
        "00011111000", "00011111000", "00000000000",
    )
    expected = _grid(
        "00000000000", "22222000000", "22222000000", "20002000000",
        "22222000000", "22222000000", "00000000000",
    )
    assert prototype.solve(source, threshold=3) == expected


def test_diagonally_touching_solid_components_remain_separate(prototype) -> None:
    source = _grid("00000000000", "00000100000", "00000010000", "00000000000")
    expected = _grid("00000000000", "20000000000", "20000000000", "00000000000")
    assert prototype.solve(source, threshold=3) == expected


def test_touching_different_colors_are_distinct_foreground_components(prototype) -> None:
    source = _grid(
        "0000000000000", "0000011000000", "0000011700000",
        "0000000770000", "0000000000000", "0000000000000",
    )
    expected = _grid(
        "0000000000000", "2200000000000", "2200000000030",
        "0000000000033", "0000000000000", "0000000000000",
    )
    for threshold in (1, 2, 3):
        assert prototype.solve(source, threshold=threshold) == expected


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_all_admitted_counts_are_distinct_matched_and_identifiable(
    adapter, prototype, demos, queries,
) -> None:
    matched_inputs = None
    for threshold in (1, 2, 3):
        settings = {"min_hole_area": threshold}
        episode = adapter.generate(20261024, settings, demos=demos, queries=queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program(settings)
        pairs = episode["train"] + episode["test"]
        inputs = [_signature(pair["input"]) for pair in pairs]
        assert len(set(inputs)) == demos + queries
        if matched_inputs is None:
            matched_inputs = inputs
        assert inputs == matched_inputs
        for pair in pairs:
            _assert_arc_grid(pair["input"])
            _assert_arc_grid(pair["output"])
            assert len(pair["input"]) == len(pair["output"])
            assert len(pair["input"][0]) == len(pair["output"][0])
            counts = Counter(cell for row in pair["input"] for cell in row)
            assert list(counts.values()).count(max(counts.values())) == 1
            assert pair["output"] == prototype.solve(pair["input"], threshold=threshold)
        survivors = [
            candidate for candidate in (1, 2, 3)
            if all(
                prototype.solve(pair["input"], threshold=candidate) == pair["output"]
                for pair in episode["train"][:2]
            )
        ]
        assert survivors == [threshold]


def test_default_episode_has_three_demos_and_four_query_profiles(adapter) -> None:
    episode = adapter.generate(17, {})
    assert len(episode["train"]) == 3
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]] == [
        (19, 19), (23, 27), (27, 29), (30, 30),
    ]


def test_minimum_demos_disambiguate_background_color(adapter) -> None:
    episode = adapter.generate(14, {"min_hole_area": 2}, demos=2, queries=4)
    backgrounds = {
        Counter(cell for row in pair["input"] for cell in row).most_common(1)[0][0]
        for pair in episode["train"]
    }
    assert len(backgrounds) == 2, "Both demos must challenge a fixed-background-color rule"


def test_minimum_demos_reject_color_selective_docking(adapter, prototype) -> None:
    """Seed 14 formerly taught only one foreground color in both demos.

On the sampler's disjoint row bands, this concrete rival docks objects of one
chosen color and leaves all other foreground objects in place. Its topology is
otherwise the intended rule, so only its color-selection assumption differs.
"""
    episode = adapter.generate(14, {"min_hole_area": 2}, demos=2, queries=4)

    def foreground_colors(grid):
        counts = Counter(cell for row in grid for cell in row)
        background = counts.most_common(1)[0][0]
        return set(counts) - {background}

    def color_selective(grid, chosen):
        background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
        isolated = [[cell if cell == chosen else background for cell in row] for row in grid]
        output = prototype.solve(isolated, threshold=2)
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell not in (background, chosen):
                    output[r][c] = cell
        return output

    candidates = set().union(*(foreground_colors(pair["input"]) for pair in episode["train"]))
    assert len(candidates) >= 2, "Minimum demonstrations must teach multiple foreground colors"
    for color in candidates:
        fits_demos = all(
            color_selective(pair["input"], color) == pair["output"]
            for pair in episode["train"]
        )
        changes_query = any(
            color_selective(pair["input"], color) != pair["output"]
            for pair in episode["test"]
        )
        assert not (fits_demos and changes_query), f"Unrefuted color-selective rival: {color}"


@pytest.mark.parametrize("threshold", (1, 2, 3))
def test_query_prefix_does_not_expose_requested_total(adapter, threshold) -> None:
    settings = {"min_hole_area": threshold}
    one = adapter.generate(53, settings, demos=3, queries=1)
    four = adapter.generate(53, settings, demos=3, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]


@pytest.mark.parametrize("seed", (0, 2**63 - 1))
def test_seed_endpoints_are_deterministic_without_global_rng_mutation(adapter, seed) -> None:
    state = random.getstate()
    first = adapter.generate(seed, {"min_hole_area": 2}, demos=2, queries=1)
    assert random.getstate() == state
    second = adapter.generate(seed, {"min_hole_area": 2}, demos=2, queries=1)
    assert first == second
    first["train"][0]["input"][0][0] = -1
    assert first != second


@pytest.mark.parametrize("settings", [
    {"min_hole_area": True}, {"min_hole_area": False},
    {"min_hole_area": 0}, {"min_hole_area": 4},
    {"min_hole_area": 1.0}, {"min_hole_area": "1"},
    {"min_hole_area": None}, {"hole_area": 2},
    {"min_hole_area": 2, "unexpected": 1},
])
def test_invalid_settings_fail_for_both_entry_points(adapter, settings) -> None:
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(1, settings, demos=2, queries=1)


@pytest.mark.parametrize("request_kwargs", [
    {"demos": 1}, {"demos": 7}, {"demos": True},
    {"demos": 2.0}, {"demos": "3"},
    {"queries": 0}, {"queries": 5}, {"queries": False},
    {"queries": 1.0}, {"queries": "1"},
])
def test_invalid_counts_fail_loudly(adapter, request_kwargs) -> None:
    with pytest.raises(ValueError):
        adapter.generate(1, {}, **request_kwargs)


@pytest.mark.parametrize("seed", (-1, 2**63, True, False, 1.0, "1"))
def test_invalid_seeds_fail_loudly(adapter, seed) -> None:
    with pytest.raises(ValueError):
        adapter.generate(seed, {}, demos=2, queries=1)


@pytest.mark.parametrize("grid", [
    [], [[]], [[0, 0], [0]], [[False, 0]], [[0.0, 0]],
    [[10, 0]], [[-1, 0]], [[0, 1]], [[0] * 31], [[0]] * 31,
])
def test_solver_rejects_malformed_grids_and_tied_backgrounds(prototype, grid) -> None:
    with pytest.raises(ValueError):
        prototype.solve(grid)
