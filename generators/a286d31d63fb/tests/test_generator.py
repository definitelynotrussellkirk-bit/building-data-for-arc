"""Portable regressions for the flat-row-profile component sampler.

The component parser and both semantic oracles are independent of generator
helpers.  They intentionally operate on monochromatic 4-connected components,
matching the canonical Racket `objects g 0` behavior.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a286d31d63fb"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent
BANDS = (None, "easy", "medium", "hard")
PALETTES = {
    "default": {1, 2, 3, 4, 5},
    "warm": {1, 2, 4, 6, 7},
    "cool": {1, 3, 5, 6, 9},
    "varied": {2, 3, 4, 7, 9},
}


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("flat_row_generator", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()

Cell = tuple[int, int]
Grid = list[list[int]]


def components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    """Return monochromatic 4-connected nonzero components."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[tuple[int, set[Cell]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            seen.add((row, col))
            stack = [(row, col)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (rr + dr, cc + dc)
                    if point in seen:
                        continue
                    pr, pc = point
                    if 0 <= pr < height and 0 <= pc < width and grid[pr][pc] == color:
                        seen.add(point)
                        cells.add(point)
                        stack.append(point)
            result.append((color, cells))
    return result


def row_profile(cells: Iterable[Cell]) -> tuple[int, ...]:
    counts = Counter(row for row, _ in cells)
    return tuple(counts[row] for row in sorted(counts))


def is_flat(cells: set[Cell]) -> bool:
    profile = row_profile(cells)
    return bool(profile) and len(set(profile)) == 1


def fills_bbox(cells: set[Cell]) -> bool:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def row_profile_oracle(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in components(grid):
        if is_flat(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def rectangle_only_rival(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for _, cells in components(grid):
        if fills_bbox(cells):
            for row, col in cells:
                output[row][col] = 8
    return output


def observed(grid: Grid) -> dict[str, object]:
    comps = components(grid)
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "flat_component_count": sum(is_flat(cells) for _, cells in comps),
        "nonflat_component_count": sum(not is_flat(cells) for _, cells in comps),
        "colors": {color for color, _ in comps},
        "component_count": len(comps),
        "has_nonrect_flat": any(is_flat(cells) and not fills_bbox(cells) for _, cells in comps),
    }


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_authority_is_pinned() -> None:
    assert gen.RULE_HASH == "bc2002d0a0d4"


def test_canonical_inputs_are_accepted_and_independent_oracle_matches(canonical) -> None:
    assert len(canonical) == 3
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert row_profile_oracle(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "controls",
    (
        {
            "height": 8,
            "width": 11,
            "flat_component_count": 1,
            "nonflat_component_count": 1,
            "palette_kind": "cool",
        },
        {
            "height": 16,
            "width": 18,
            "flat_component_count": 3,
            "nonflat_component_count": 2,
            "palette_kind": "warm",
        },
        {
            "height": 9,
            "width": 15,
            "flat_component_count": 2,
            "nonflat_component_count": 1,
            "palette_kind": "varied",
        },
    ),
)
def test_exact_controls_are_honored_in_every_band(band, controls) -> None:
    grid = gen.generate(319, 17, difficulty=band, **controls)
    facts = observed(grid)
    assert {key: facts[key] for key in controls if key != "palette_kind"} == {
        key: value for key, value in controls.items() if key != "palette_kind"
    }
    assert facts["colors"] <= PALETTES[controls["palette_kind"]]
    assert len(facts["colors"]) == facts["component_count"]
    assert gen.self_check(grid, difficulty=band) == []
    assert facts["has_nonrect_flat"] is True
    assert row_profile_oracle(grid) != rectangle_only_rival(grid)


def test_observer_recovers_exact_component_count_axes() -> None:
    grid = gen.generate(
        731,
        19,
        difficulty="hard",
        flat_component_count=3,
        nonflat_component_count=2,
    )

    assert gen.observe_overrides(grid) == {
        "flat_component_count": 3,
        "nonflat_component_count": 2,
    }


@pytest.mark.parametrize(
    "kwargs",
    (
        {"unknown_axis": 1},
        {"texture": "all_flat"},
        {"palette_size": 2},
        {"n_distinct_colors": 3},
        {"position_bias": "scattered_flat_and_nonflat"},
        {"density": "sparse"},
        {"height": True},
        {"width": 12.0},
        {"flat_component_count": "2"},
        {"nonflat_component_count": False},
        {"palette_kind": 3},
        {"height": 7},
        {"width": 10},
        {"flat_component_count": 0},
        {"nonflat_component_count": 3},
        {"palette_kind": "neon"},
    ),
)
def test_invalid_unknown_and_retired_controls_are_rejected(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("bad_seed", (True, False, 1.0, "1"))
def test_seed_requires_an_actual_integer(bad_seed) -> None:
    with pytest.raises(TypeError):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", (True, False, 1.0, "1", -1))
def test_sample_index_requires_a_nonnegative_integer(bad_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, bad_index)


@pytest.mark.parametrize("bad_band", ("simple", 0.5, True))
def test_unknown_difficulty_is_rejected(bad_band) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=bad_band)


def test_none_overrides_preserve_default_draws() -> None:
    assert gen.generate(
        22,
        5,
        height=None,
        width=None,
        flat_component_count=None,
        nonflat_component_count=None,
        palette_kind=None,
    ) == gen.generate(22, 5)


@pytest.mark.parametrize("band", BANDS)
def test_default_sampler_is_deterministic_lawful_and_refutes_rectangle_shortcut(band) -> None:
    shapes = set()
    profiles = set()
    for index in range(64):
        grid = gen.generate(1200 + index, index * 17 + 3, difficulty=band)
        assert grid == gen.generate(1200 + index, index * 17 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        facts = observed(grid)
        assert facts["has_nonrect_flat"] is True
        assert len(facts["colors"]) == facts["component_count"]
        assert row_profile_oracle(grid) != rectangle_only_rival(grid)
        assert gen.SEMANTIC_WITNESSES["nonrectangular_flat_profile"](grid)
        assert gen.SEMANTIC_RIVALS["rectangle_only"](grid) == rectangle_only_rival(grid)
        shapes.add((facts["height"], facts["width"]))
        profiles.add((facts["flat_component_count"], facts["nonflat_component_count"]))
    assert len(shapes) >= 3
    assert (2, 1) in profiles


@pytest.mark.parametrize(
    "bad_grid",
    (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 11 for _ in range(8)],
        [[10] + [0] * 10 for _ in range(8)],
        ["00000000000"] * 8,
        [[0] * 11 for _ in range(8)],
    ),
)
def test_malformed_or_semantically_empty_grids_return_diagnostics(bad_grid) -> None:
    result = gen.self_check(bad_grid)
    assert isinstance(result, list) and result


def test_retained_counterexample_refutes_rectangle_only_rival() -> None:
    fixture = json.loads((TASK_HOME / "counterexamples/rectangle_only.json").read_text())
    grid = fixture["input"]
    assert gen.self_check(grid) == []
    assert row_profile_oracle(grid) == fixture["intended_output"]
    assert rectangle_only_rival(grid) == fixture["rival_output"]
    assert fixture["intended_output"] != fixture["rival_output"]
    assert gen.SEMANTIC_WITNESSES["nonrectangular_flat_profile"](grid)


def test_semantic_contract_links_witness_to_rectangle_rival() -> None:
    assert gen.LESSON_COMPETITORS == {
        "rectangle_only": gen.rectangle_only_output,
    }
    assert gen.WITNESS_RIVALS == {
        "nonrectangular_flat_profile": ["rectangle_only"],
    }


def test_retained_counterexample_matches_live_canonical_racket() -> None:
    from arcpuzzles import Catalog

    fixture = json.loads((TASK_HOME / "counterexamples/rectangle_only.json").read_text())
    receipt = Catalog(find_root(__file__)).apply(
        TASK_ID, [fixture["input"]], reference="canonical", timeout=120
    )
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["executed_rule_hash"] == gen.RULE_HASH
    result = receipt["results"][0]
    assert result["error"] is None and result["valid_output"] is True
    assert result["output"] == fixture["intended_output"]
