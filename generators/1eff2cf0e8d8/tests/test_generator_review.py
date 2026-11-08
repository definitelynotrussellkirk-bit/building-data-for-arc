"""Task-local regression tests for the reviewed Template Copies generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

TASK_ID = "1eff2cf0e8d8"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _norm(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        pairs = list(row.get("train") or [])
        test = row.get("test") or []
        pairs.extend(test if isinstance(test, list) else [test])
        return [
            {"input": _norm(pair["input"]), "output": _norm(pair["output"])}
            for pair in pairs
        ]
    raise AssertionError("canonical task row not found")


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_declares_source_bound_contract():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "ede1d75f92cd"
    assert gen.EXAMPLES_NEEDED == 4
    assert len(gen.SCHEDULE_PROFILES) == gen.EXAMPLES_NEEDED
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_pairs_are_accepted_and_python_mirror_matches():
    for pair in canonical_pairs():
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    requested = {
        "grid_h": 7,
        "grid_w": 11,
        "template_h": 3,
        "template_w": 3,
        "n_template_colors": 3,
        "n_markers": 3,
        "top_left_filled": False,
    }
    grid = gen.generate(71, 19, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(71, 19, difficulty=band, **requested)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 10),
        ("grid_w", 17),
        ("template_h", 1),
        ("template_h", 4),
        ("template_w", 1),
        ("template_w", 4),
        ("n_template_colors", 0),
        ("n_template_colors", 4),
        ("n_markers", 0),
        ("n_markers", 4),
        ("grid_h", True),
        ("n_markers", 2.5),
        ("template_w", "3"),
        ("top_left_filled", 1),
        ("top_left_filled", "false"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "values",
    itertools.product(
        (7, 14),
        (11, 16),
        (2, 3),
        (2, 3),
        (1, 3),
        (1, 3),
        (False, True),
    ),
)
def test_every_boundary_override_combination_is_constructive(values):
    keys = (
        "grid_h",
        "grid_w",
        "template_h",
        "template_w",
        "n_template_colors",
        "n_markers",
        "top_left_filled",
    )
    requested = dict(zip(keys, values))
    grid = gen.generate(901, 37, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


def test_canonical_profile_support_is_present_in_every_band():
    canonical_profiles = {profile(pair["input"]) for pair in canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        seen = []
        for index in range(20):
            # Same off-diagonal sample-index shape used by the repository gate.
            seed = int.from_bytes(f"{TASK_ID}:{band}:{index}".encode(), "little")
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            seen.append(profile(grid))
        assert any(item in canonical_profiles for item in seen), (band, seen)


def _lesson(start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        index = start + offset
        grid = gen.generate(5100 + index, index, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    return demos


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_every_cyclic_four_demo_window_refutes_all_declared_competitors(band, start):
    demos = _lesson(start, band)
    assert gen.lesson_identifiable(demos, demos[0]["input"]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_canonical_shortcuts_reproduce_every_canonical_pair():
    pairs = canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_each_semantic_witness_produces_a_real_rival_counterexample():
    seen = set()
    for index in range(32):
        grid = gen.generate(6200 + index, index, difficulty="medium")
        authority = gen.rule_mirror(grid)
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            seen.add(witness_name)
            rivals = gen.WITNESS_RIVALS[witness_name]
            assert any(gen.SEMANTIC_RIVALS[name](grid) != authority for name in rivals)
    assert seen == set(gen.SEMANTIC_WITNESSES)


def test_rule_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(812, 9, difficulty="hard")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 0]], [[True] * 11 for _ in range(7)]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_validator_rejects_missing_markers_and_overlapping_stamp_regions():
    grid = gen.generate(99, 7, grid_h=10, grid_w=14, n_markers=2)
    no_markers = [[0 if value == 9 else value for value in row] for row in grid]
    assert gen.self_check(no_markers)

    # Move one marker into the template bounding box without changing dimensions.
    damaged = deepcopy(grid)
    marker_positions = [
        (row, col)
        for row, values in enumerate(damaged)
        for col, value in enumerate(values)
        if value == 9
    ]
    row, col = marker_positions[0]
    damaged[row][col] = 0
    template_cells = [
        (r, c)
        for r, values in enumerate(damaged)
        for c, value in enumerate(values)
        if value not in (0, 9)
    ]
    top = min(r for r, _ in template_cells)
    left = min(c for _, c in template_cells)
    damaged[top][left] = 9
    assert gen.self_check(damaged)
