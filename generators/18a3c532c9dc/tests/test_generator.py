"""Portable regressions for the reviewed quarter-overlay generator."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "18a3c532c9dc"
EVEN_SIZES = (4, 6, 8, 10, 12, 14, 16, 18, 20)


def _load_generator():
    default = Path(__file__).resolve().parents[1] / "generator.py"
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", default))
    spec = spec_from_file_location("generator_under_test_18a3c532c9dc", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _overlay(grid, order=("tl", "br", "bl", "tr")):
    h, w = len(grid), len(grid[0])
    hh, hw = h // 2, w // 2
    out = []
    for r in range(hh):
        row = []
        for c in range(hw):
            values = {
                "tl": grid[r][c],
                "tr": grid[r][c + hw],
                "bl": grid[r + hh][c],
                "br": grid[r + hh][c + hw],
            }
            value = 0
            for quadrant in order:
                if values[quadrant] != 0:
                    value = values[quadrant]
            row.append(value)
        out.append(row)
    return out


def _axis_values(name):
    return tuple(int(part) for part in gen.AXES[name]["valid"].split("|"))


def test_rule_pin_and_python_mirror_match_every_canonical_label():
    assert gen.RULE_HASH == "c6cdd9647cb6"
    assert CANONICAL
    for pair in CANONICAL:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert _overlay(pair["input"]) == pair["output"]


def test_only_exact_observable_size_axes_are_advertised():
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert _axis_values("grid_h") == EVEN_SIZES
    assert _axis_values("grid_w") == EVEN_SIZES


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", EVEN_SIZES)
@pytest.mark.parametrize("grid_w", EVEN_SIZES)
def test_every_declared_size_combination_is_exact_and_lawful(band, grid_h, grid_w):
    grid = gen.generate(1701 + grid_h, grid_w, difficulty=band, grid_h=grid_h, grid_w=grid_w)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": grid_h, "grid_w": grid_w}
    assert len(grid) == grid_h
    assert len(grid[0]) == grid_w


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 8},
        {"grid_h": 2},
        {"grid_w": 22},
        {"grid_h": 5},
        {"grid_w": 7},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"grid_h": "8"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_invalid_seed_runtime_scalars_fail_loudly(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_runtime_scalars_fail_loudly(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)


def test_canonical_anchor_still_records_both_exact_axis_draws():
    class RecordingContext:
        def __init__(self):
            self.keys = []

        def draw_choice(self, key, choices):
            self.keys.append(key)
            if key == "canonical_profile":
                return True
            return tuple(choices)[0]

    ctx = RecordingContext()
    assert gen._choose_dimensions(ctx, 0, 0, None, {}) == (8, 8)
    assert ctx.keys == ["canonical_profile", "grid_h", "grid_w"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_canonical_anchored_and_semantic(band):
    shapes = set()
    inputs = set()
    first_twenty_profiles = set()
    for index in range(60):
        grid = gen.generate(80_000 + index, index, difficulty=band)
        assert grid == gen.generate(80_000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        shapes.add((len(grid), len(grid[0])))
        inputs.add(tuple(tuple(row) for row in grid))
        if index < 20:
            first_twenty_profiles.add(
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            )
        truth = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), witness_name
            rivals = gen.WITNESS_RIVALS[witness_name]
            if isinstance(rivals, str):
                rivals = [rivals]
            assert any(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rivals)
    assert (8, 8, 5) in first_twenty_profiles
    assert len(shapes) >= 4
    assert len(inputs) >= 58


def test_every_three_example_lesson_and_rotation_refutes_declared_rivals():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            lesson = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(9100 + start, start + offset, difficulty=band)
                lesson.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(lesson):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_structural_corruptions():
    grid = gen.generate(44, 1, grid_h=8, grid_w=10)
    assert gen.self_check(grid) == []

    ragged = deepcopy(grid)
    ragged[0].pop()
    assert gen.self_check(ragged)

    odd = deepcopy(grid[:-1])
    assert gen.self_check(odd)

    hh, hw = len(grid) // 2, len(grid[0]) // 2
    tl_color = next(grid[r][c] for r in range(hh) for c in range(hw) if grid[r][c])
    tr_color = next(grid[r][c] for r in range(hh) for c in range(hw, len(grid[0])) if grid[r][c])
    assert tl_color != tr_color
    mixed_quadrant = deepcopy(grid)
    mixed_quadrant[0][0] = tr_color
    assert gen.self_check(mixed_quadrant)

    empty_quadrant = deepcopy(grid)
    for r in range(hh):
        for c in range(hw):
            empty_quadrant[r][c] = 0
    assert gen.self_check(empty_quadrant)
