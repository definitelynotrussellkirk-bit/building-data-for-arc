"""Focused contract and semantic regressions for ARC generator 98c4483164f7."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "98c4483164f7"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate).resolve() if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("review_98c4483164f7", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_source_binding_and_axis_surface_are_exact():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "18ad2f5cfd8b"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_red_cells", "main_color"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_every_canonical_pair_is_accepted_and_mirrored(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard", 0.0, 0.5, 1.0])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6, "grid_w": 30, "n_red_cells": 1, "main_color": 1},
        {"grid_h": 30, "grid_w": 6, "n_red_cells": 2, "main_color": 9},
        {"grid_h": 9, "grid_w": 9, "n_red_cells": 3, "main_color": 4},
    ],
)
def test_exact_overrides_are_honored_in_every_band(band, overrides):
    grid = gen.generate(173, 29, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"anchor_corner": True},
        {"grid_h": 5},
        {"grid_h": 31},
        {"grid_w": True},
        {"grid_w": 8.5},
        {"n_red_cells": 0},
        {"n_red_cells": 4},
        {"n_red_cells": "2"},
        {"main_color": 0},
        {"main_color": 2},
        {"main_color": 10},
        {"main_color": True},
    ],
)
def test_invalid_unknown_and_retired_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["impossible", -0.1, 1.1, True])
def test_invalid_difficulty_fails_loudly(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_has_canonical_floor_and_semantic_cycle(band):
    grids = [gen.generate(811, index, difficulty=band) for index in range(16)]
    assert sum((len(grid), len(grid[0])) == (9, 9) for grid in grids) >= 4
    assert [gen.observe_overrides(grid)["n_red_cells"] for grid in grids[:4]] == [1, 2, 3, 2]
    assert {
        gen.schedule_profile(811, index, difficulty=band)
        for index in range(4)
    } == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_grids_are_deterministic_lawful_and_semantically_useful(band):
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(32):
        grid = gen.generate(9001, index, difficulty=band)
        assert grid == gen.generate(9001, index, difficulty=band)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        expected = gen.rule_mirror(grid)
        assert expected != grid
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                witness_hits[name] += 1
                for rival_name in gen.WITNESS_RIVALS.get(name, []):
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected
    assert all(count > 0 for count in witness_hits.values()), witness_hits


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_demo_sliding_window_refutes_named_competitors(band):
    for start in range(8):
        grids = [gen.generate(404, start + offset, difficulty=band) for offset in range(4)]
        pairs = [_pair(grid) for grid in grids]
        assert gen.EXAMPLES_NEEDED == 3
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3]), (
                start,
                name,
            )


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 6 for _ in range(6)],
        [[0] * 6 for _ in range(6)],
    ],
)
def test_malformed_or_out_of_grammar_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
