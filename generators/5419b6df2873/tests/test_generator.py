"""Focused regressions for the 5419b6df2873 teaching-distribution repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5419b6df2873"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = (None, "easy", "medium", "hard")
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
    for pair in CANONICAL
}


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for column, color in enumerate(grid[0]):
        if color:
            for row in range(height):
                out[row][column] = color
    return out


def preserve_lower_cells_rival(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for column, color in enumerate(grid[0]):
        if color:
            for row in range(len(grid)):
                out[row][column] = color
    return out


def has_erasure_witness(grid: list[list[int]]) -> bool:
    return any(
        grid[row][column] != 0 and grid[0][column] == 0
        for row in range(1, len(grid))
        for column in range(len(grid[0]))
    )


def normalized_rule_hash() -> str:
    root = find_root(__file__)
    canonical_path = root / "shared/data/canonical/puzzles.jsonl"
    for line in canonical_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            return hashlib.sha256(
                " ".join(record["program_solution"].split()).encode()
            ).hexdigest()[:12]
    raise AssertionError("canonical rule missing")


def test_rule_pin_and_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == normalized_rule_hash() == "72e1b062f409"
    for pair in CANONICAL:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_axis_surface_contains_only_exact_observable_controls():
    assert tuple(GEN.AXES) == ("grid_h", "grid_w", "n_markers")
    assert tuple(GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", BANDS)
def test_every_default_sample_contains_an_effective_erasure_witness(band):
    for index in range(24):
        grid = GEN.generate(7100 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert has_erasure_witness(grid)
        assert preserve_lower_cells_rival(grid) != intended_output(grid)
        assert grid == GEN.generate(7100 + index, index, difficulty=band)


@pytest.mark.parametrize("band", BANDS)
def test_every_advertised_override_is_exact_in_every_band(band):
    for options in (
        {"grid_h": 5, "grid_w": 6, "n_markers": 2},
        {"grid_h": 9, "grid_w": 11, "n_markers": 5},
        {"grid_h": 7, "grid_w": 8, "n_markers": 3},
    ):
        grid = GEN.generate(42, 17, difficulty=band, **options)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "unknown"}),
        ((0, 0), {"typo_axis": 1}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_w": 12}),
        ((0, 0), {"n_markers": 1}),
    ],
)
def test_invalid_calls_and_unknown_overrides_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_self_check_rejects_minimal_impostors_without_throwing():
    bad = [
        None,
        [],
        [[]],
        [[0] * 8 for _ in range(6)],
        [[1] * 8 for _ in range(6)],
        [[0] * 8 for _ in range(5)] + [[0] * 7],
        [[True] * 8 for _ in range(6)],
        [[1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]] + [[0] * 6 for _ in range(3)],
    ]
    for grid in bad:
        assert GEN.self_check(grid)


def test_declared_rival_fits_canonical_but_every_generated_lesson_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["preserve_lower_cells"]
    assert GEN.SEMANTIC_RIVALS["preserve_lower_cells"] is rival
    assert GEN.LESSON_COMPETITORS["preserve_lower_cells"] is rival
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL)

    for band in BANDS:
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            grids = [GEN.generate(99, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": intended_output(grid)} for grid in grids]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("band", BANDS)
def test_declared_schedule_covers_all_canonical_profiles_in_each_band(band):
    profiles = set()
    for index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(2026, index, difficulty=band)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert profiles == CANONICAL_PROFILES


def test_difficulty_bands_change_randomized_content_but_not_profile_schedule():
    samples = {
        band: [GEN.generate(314159, index, difficulty=band) for index in range(10)]
        for band in ("easy", "medium", "hard")
    }
    assert samples["easy"] != samples["medium"]
    assert samples["medium"] != samples["hard"]
    assert samples["easy"] != samples["hard"]
    assert [GEN.observe_overrides(grid) for grid in samples["medium"]] == [
        GEN.observe_overrides(GEN.generate(314159, index, difficulty=None))
        for index in range(10)
    ]
