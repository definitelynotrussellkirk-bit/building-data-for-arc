from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

MODULE_PATH = REPO / "generators" / "a3086dea6cff" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_a3086dea6cff", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
CANONICAL_PROFILES = {(8, 10, 4), (9, 11, 4), (10, 12, 4), (11, 13, 5)}


def _norm_grid(grid):
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _canonical_pairs():
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        train = row.get("train") or []
        test = row.get("test") or []
        if isinstance(test, dict):
            test = [test]
        return [
            {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
            for pair in [*train, *test]
        ]
    raise AssertionError("canonical task not found")


def _positions(grid):
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                by_color.setdefault(value, []).append((row, col))
    return by_color


def _features(grid):
    horizontal = []
    vertical = []
    nonaligned = []
    triples = []
    for color, cells in _positions(grid).items():
        if len(cells) == 2:
            (r1, c1), (r2, c2) = cells
            if r1 == r2:
                horizontal.append((color, cells))
            elif c1 == c2:
                vertical.append((color, cells))
            else:
                nonaligned.append((color, cells))
        elif len(cells) == 3:
            triples.append((color, cells))
    return {
        "horizontal": horizontal,
        "vertical": vertical,
        "nonaligned": nonaligned,
        "triples": triples,
    }


def _segment_cells(cells):
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return {(r1, col) for col in range(lo, hi + 1)}
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return {(row, c1) for row in range(lo, hi + 1)}
    return set()


def _has_active_crossing(grid):
    features = _features(grid)
    for _hc, hcells in features["horizontal"]:
        hseg = _segment_cells(hcells)
        hend = set(hcells)
        for _vc, vcells in features["vertical"]:
            vseg = _segment_cells(vcells)
            vend = set(vcells)
            intersection = hseg & vseg
            if intersection and not (intersection & (hend | vend)):
                return True
    return False


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def test_declares_current_authority_hash():
    assert GEN.RULE_HASH == "7563337a81ab"


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "values"),
    [
        ("grid_h", (8, 13)),
        ("grid_w", (10, 15)),
        ("n_pairs", (2, 4)),
    ],
)
def test_declared_axis_boundaries_are_honored_in_every_band(band, axis, values):
    for value in values:
        grid = GEN.generate(17, 5, difficulty=band, **{axis: value})
        observed = GEN.observe_overrides(grid)
        assert observed[axis] == value
        assert GEN.self_check(grid) == []


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_scene_contains_both_connector_orientations(band):
    for seed in range(12):
        for sample_index in range(6):
            grid = GEN.generate(seed, sample_index, difficulty=band)
            features = _features(grid)
            assert features["horizontal"], (band, seed, sample_index, grid)
            assert features["vertical"], (band, seed, sample_index, grid)
            assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_window_refutes_key_rivals_and_anchors_canonical_scale(band):
    for start in range(6):
        grids = [GEN.generate(31, start + offset, difficulty=band) for offset in range(3)]
        features = [_features(grid) for grid in grids]
        assert any(item["nonaligned"] for item in features), (band, start)
        assert any(item["triples"] for item in features), (band, start)
        assert any(_has_active_crossing(grid) for grid in grids), (band, start)
        assert any(_profile(grid) in CANONICAL_PROFILES for grid in grids), (band, start)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_n_pairs_override_counts_only_active_aligned_pairs(band):
    for n_pairs in (2, 3, 4):
        for sample_index in range(3):
            grid = GEN.generate(73, sample_index, difficulty=band, n_pairs=n_pairs)
            features = _features(grid)
            assert len(features["horizontal"]) + len(features["vertical"]) == n_pairs


def test_self_check_accepts_every_canonical_input():
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []


def test_rule_mirror_matches_canonical_pairs_and_is_pure():
    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_canonical_shortcuts_fit_public_pairs_but_generated_witnesses_refute_them():
    shortcuts = GEN.CANONICAL_SHORTCUTS
    assert {"connect_non_aligned_with_l", "connect_aligned_any_count"} <= set(shortcuts)

    for name, shortcut in shortcuts.items():
        for pair in _canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name

    grids = [GEN.generate(101, sample_index, difficulty="medium") for sample_index in range(3)]
    for name, shortcut in shortcuts.items():
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in grids), name


def test_generated_lesson_is_identifiable_and_competitors_are_refuted():
    demos = []
    for sample_index in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(211, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(211, GEN.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}

    assert GEN.lesson_identifiable(demos, query) == []
    for name, competitor in GEN.LESSON_COMPETITORS.items():
        assert not all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        ), name


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991)
    before = random.getstate()
    first = GEN.generate(5, 2, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(5, 2, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == middle == after

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_declared_witness_refutes_a_named_rival_on_every_firing(band):
    for seed in range(24):
        for sample_index in range(9):
            grid = GEN.generate(seed, sample_index, difficulty=band)
            intended = GEN.rule_mirror(grid)
            for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
                if not GEN.SEMANTIC_WITNESSES[witness_name](grid):
                    continue
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != intended
                    for rival_name in rival_names
                ), (band, seed, sample_index, witness_name, grid)
