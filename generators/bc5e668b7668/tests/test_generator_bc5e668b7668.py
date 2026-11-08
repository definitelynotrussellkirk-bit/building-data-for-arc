from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random

import pytest

TASK_ID = "bc5e668b7668"
CANONICAL_PROFILES = {(5, 5, 10), (6, 6, 10), (6, 7, 10), (7, 5, 10)}


def _load_generator():
    source = os.environ.get("GENERATOR_UNDER_TEST")
    if source is None:
        source = Path(__file__).resolve().parents[1] / "generator.py"
    source = Path(source)
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_row():
    here = Path(__file__).resolve()
    candidates = []
    for parent in here.parents:
        candidates.extend(
            [
                parent / "shared/data/canonical/puzzles.jsonl",
                parent / "data/canonical/puzzles.jsonl",
            ]
        )
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _pairs():
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def _pack_up(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


@pytest.mark.parametrize("pair", _pairs(), ids=lambda pair: str(_profile(pair["input"])))
def test_accepts_and_solves_every_canonical_pair(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert _pack_up(pair["input"]) == pair["output"]
    assert pair["input"] == original
    assert gen.strict_canonical_like(pair["input"]) == []


def test_pins_the_selected_canonical_rule():
    assert gen.RULE_HASH == "bd83e3df4565"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_canonical_scaled_and_valid(band):
    profiles = set()
    for index in range(24):
        seed = 5000 + index
        before = random.getstate()
        grid = gen.generate(seed, index, difficulty=band)
        assert random.getstate() == before
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert _pack_up(grid) != grid
        profiles.add(_profile(grid))
    assert profiles <= CANONICAL_PROFILES
    assert profiles


def test_four_consecutive_samples_cover_the_teaching_schedule():
    profiles = [gen.schedule_profile(91, i, difficulty="medium") for i in range(4)]
    assert profiles == list(gen.SCHEDULE_PROFILES)
    textures = [gen.observe_overrides(gen.generate(91, i))["texture"] for i in range(4)]
    assert textures == [
        "canonical_dense",
        "singleton_witness",
        "interleaved_order",
        "canonical_dense",
    ]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "texture", ["canonical_dense", "singleton_witness", "interleaved_order"]
)
def test_exact_overrides_are_observable_in_every_band(band, texture):
    grid = gen.generate(
        17,
        9,
        difficulty=band,
        grid_h=9,
        grid_w=8,
        texture=texture,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 9,
        "grid_w": 8,
        "texture": texture,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 4},
        {"grid_h": 10},
        {"grid_w": True},
        {"grid_h": 5.5},
        {"texture": "unknown"},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_singleton_witness_refutes_the_canonical_fitting_ignore_singletons_shortcut():
    grid = gen.generate(31, 1, grid_h=5, grid_w=5, texture="singleton_witness")
    intended = _pack_up(grid)
    rival = gen.SEMANTIC_RIVALS["ignore_singletons"](grid)
    assert gen.SEMANTIC_WITNESSES["singleton_column"](grid)
    assert rival != intended
    assert all(
        gen.SEMANTIC_RIVALS["ignore_singletons"](pair["input"]) == pair["output"]
        for pair in _pairs()
    )


def test_interleaved_witness_refutes_sorting_values_within_columns():
    grid = gen.generate(37, 2, grid_h=5, grid_w=5, texture="interleaved_order")
    intended = _pack_up(grid)
    rival = gen.SEMANTIC_RIVALS["sort_values"](grid)
    assert gen.SEMANTIC_WITNESSES["stable_nonmonotonic_order"](grid)
    assert rival != intended


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)], [[0] * 5 for _ in range(5)]],
)
def test_self_check_is_diagnostic_on_malformed_or_degenerate_inputs(grid):
    assert gen.self_check(grid)


def test_difficulty_bands_select_distinct_canonical_shape_ranges():
    for seed in range(8):
        easy = gen.generate(seed, 17, difficulty="easy")
        hard = gen.generate(seed, 17, difficulty="hard")
        assert (len(easy), len(easy[0])) in {(5, 5), (6, 6)}
        assert (len(hard), len(hard[0])) in {(6, 7), (7, 5)}
