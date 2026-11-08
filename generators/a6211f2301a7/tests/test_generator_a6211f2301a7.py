"""Focused contract tests for the crop-and-rotate-right input sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("generator_under_test", HOME / "generator.py")
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

TASK_ID = "a6211f2301a7"
ROOT = Path(__file__).resolve().parents[3]
CANONICAL = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_colors",
    "bbox_orientation",
    "component_count",
}
CANONICAL_PROFILES = {
    (8, 9, 4),
    (9, 8, 4),
    (7, 10, 2),
    (8, 8, 3),
    (9, 9, 4),
}


def _norm(grid):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in grid]


def _canonical_pairs():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row["train"])
            test = row["test"]
            pairs.extend(test if isinstance(test, list) else [test])
            return [
                {"input": _norm(pair["input"]), "output": _norm(pair["output"])}
                for pair in pairs
            ]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _tight(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _turn_right(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _component_count(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    }
    count = 0
    while remaining:
        count += 1
        stack = [min(remaining)]
        remaining.remove(stack[0])
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return count


def _orientation(grid):
    crop = _tight(grid)
    h, w = len(crop), len(crop[0])
    return "wide" if w > h else "tall" if h > w else "square"


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _tall_witness():
    # Tight crop is [[1,2], [0,0], [3,3]]: tall, padded, two components.
    return [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_metadata_pins_rule_and_exposes_only_observable_axes():
    assert getattr(gen, "RULE_HASH", None) == "aad722fb766b"
    assert set(gen.AXES) == EXPECTED_AXES
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("orientation", ["wide", "tall", "square"])
@pytest.mark.parametrize("components", [1, 2, 3])
def test_every_advertised_combination_is_constructive_and_observable(
    band, orientation, components
):
    options = {
        "grid_h": 7,
        "grid_w": 7,
        "n_colors": 3,
        "bbox_orientation": orientation,
        "component_count": components,
    }
    try:
        grid = gen.generate(101 + components, 17, difficulty=band, **options)
    except Exception as exc:  # Make unsupported desired behavior a test failure, not an error.
        pytest.fail(f"advertised combination raised {exc!r}")
    observer = getattr(gen, "observe_overrides", None)
    assert callable(observer)
    assert observer(grid) == options
    assert gen.self_check(grid) == []
    assert _orientation(grid) == orientation
    assert _component_count(grid) == components
    assert _turn_right(_tight(grid)) != _tight(grid)


def test_unknown_and_invalid_overrides_are_rejected_loudly():
    bad = [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_w": 14},
        {"n_colors": 0},
        {"n_colors": True},
        {"bbox_orientation": "diagonal"},
        {"component_count": 0},
        {"component_count": 4},
    ]
    for overrides in bad:
        with pytest.raises(ValueError):
            gen.generate(0, 0, **overrides)


def test_all_canonical_inputs_are_lawful_and_reference_outputs_are_right_turns():
    strict = getattr(gen, "strict_canonical_like", None)
    assert callable(strict)
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert strict(pair["input"]) == []
        assert _turn_right(_tight(pair["input"])) == pair["output"]


def test_self_check_rejects_trivial_or_unpadded_impostors():
    blank = [[0] * 9 for _ in range(9)]
    short_line = deepcopy(blank)
    short_line[4][3:6] = [1, 1, 1]
    solid_square = deepcopy(blank)
    solid_square[3][3] = solid_square[3][4] = 1
    solid_square[4][3] = solid_square[4][4] = 1
    left_border = deepcopy(blank)
    left_border[3][0:2] = [1, 2]
    left_border[4][0] = 2
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)]]
    for grid in [blank, short_line, solid_square, left_border, *malformed]:
        assert gen.self_check(grid)


def test_default_schedule_covers_each_canonical_profile_band_and_tall_counterexamples():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        orientations = set()
        component_counts = set()
        unique = set()
        for index in range(120):
            grid = gen.generate(2000 + index, index * 17 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            profiles.add(_profile(grid))
            orientations.add(_orientation(grid))
            component_counts.add(_component_count(grid))
            unique.add(tuple(tuple(row) for row in grid))
        assert CANONICAL_PROFILES <= profiles
        assert {"wide", "tall", "square"} <= orientations
        assert {1, 2, 3} <= component_counts
        assert len(unique) >= 100


def test_portrait_normalizer_shortcut_fits_canonical_but_tall_witness_refutes_it():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    rivals = getattr(gen, "SEMANTIC_RIVALS", {})
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", {})
    links = getattr(gen, "WITNESS_RIVALS", {})
    assert "portrait_normalizer" in shortcuts
    assert rivals.get("portrait_normalizer") is shortcuts["portrait_normalizer"]
    assert links.get("tall_bbox") == ["portrait_normalizer"]

    rival = shortcuts["portrait_normalizer"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    grid = _tall_witness()
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert witnesses["tall_bbox"](grid)
    intended = _turn_right(_tight(grid))
    assert intended == [[3, 0, 1], [3, 0, 2]]
    assert rival(grid) == [[1, 2], [0, 0], [3, 3]]
    assert rival(grid) != intended
    assert grid == original


def test_generation_is_deterministic_and_does_not_depend_on_call_order():
    expected = gen.generate(777, 33, difficulty="hard")
    assert expected == gen.generate(777, 33, difficulty="hard")
    for index in range(200):
        gen.generate(index, index * 13, difficulty=("easy", "medium", "hard")[index % 3])
    assert expected == gen.generate(777, 33, difficulty="hard")

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_defaults_refute_portrait_normalizer(band):
    rival = gen.CANONICAL_SHORTCUTS["portrait_normalizer"]
    for seed in range(3):
        schedule = [gen.generate(9000 + seed, index, difficulty=band) for index in range(12)]
        for start in range(10):
            lesson = schedule[start : start + 3]
            assert any(
                rival(grid) != _turn_right(_tight(grid))
                for grid in lesson
            ), (band, seed, start)
