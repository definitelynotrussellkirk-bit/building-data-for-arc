"""Focused regression tests for generator 1d23d72f3b43."""
from __future__ import annotations

from collections import defaultdict
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1d23d72f3b43"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", SOURCE)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _positions(grid):
    out: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[value].append((r, c))
    return dict(out)


def _intended(grid):
    """Independent Python reading of the unchanged canonical Racket rule."""
    out = [list(row) for row in grid]
    for color, points in _positions(grid).items():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                out[r][c] = color
    return out


def _bbox_cells(points):
    (r0, c0), (r1, c1) = points
    return {
        (r, c)
        for r in range(min(r0, r1), max(r0, r1) + 1)
        for c in range(min(c0, c1), max(c0, c1) + 1)
    }


def _orientations(grid):
    signs = set()
    for points in _positions(grid).values():
        (r0, c0), (r1, c1) = sorted(points)
        signs.add("main" if c1 > c0 else "anti")
    return signs


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_canonical_inputs_are_lawful_and_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_round_trip_in_every_band(band):
    requested = {"grid_h": 8, "grid_w": 8, "n_pairs": 4}
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert _orientations(grid) == {"main", "anti"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"palette_size": 2},
        {"texture": "warm"},
        {"grid_h": True},
        {"grid_h": 7},
        {"grid_w": 13},
        {"n_pairs": 1},
        {"n_pairs": 5},
        {"n_pairs": 2.5},
    ],
)
def test_invalid_and_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_ordinary_draws_are_lawful_deterministic_and_refute_orientation_shortcut(band):
    for index in range(32):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert grid == GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert _orientations(grid) == {"main", "anti"}
        assert GEN.SEMANTIC_WITNESSES["anti_diagonal_pair"](grid)
        assert GEN.SEMANTIC_RIVALS["main_diagonal_only"](grid) != _intended(grid)


def test_declared_shortcut_fits_every_canonical_pair():
    rival = GEN.CANONICAL_SHORTCUTS["main_diagonal_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())


def test_rectangles_do_not_overlap_and_each_color_has_two_diagonal_corners():
    seen_shapes = set()
    for index in range(160):
        grid = GEN.generate(1200 + index, index)
        boxes = []
        for points in _positions(grid).values():
            assert len(points) == 2
            (r0, c0), (r1, c1) = points
            assert r0 != r1 and c0 != c1
            cells = _bbox_cells(points)
            assert all(not (cells & prior) for prior in boxes)
            boxes.append(cells)
            seen_shapes.add((abs(r1 - r0) + 1, abs(c1 - c0) + 1))
    assert any(h == 2 and w > 2 for h, w in seen_shapes)
    assert any(w == 2 and h > 2 for h, w in seen_shapes)
    assert any(h >= 3 and w >= 3 for h, w in seen_shapes)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(8)],
        [[4 if (r, c) in {(1, 1), (1, 5)} else 0 for c in range(8)] for r in range(8)],
        [[4 if (r, c) in {(1, 1), (4, 4)} else 6 if (r, c) in {(2, 2), (5, 5)} else 0
          for c in range(8)] for r in range(8)],
    ],
)
def test_self_check_rejects_malformed_or_ambiguous_inputs(grid):
    assert GEN.self_check(grid)


def test_rule_hash_is_pinned_to_current_authority():
    assert GEN.RULE_HASH == "013675ae7255"


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def _profile_floor_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_every_difficulty_band_retains_exact_canonical_profile_support():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profiles.append(_profile(grid))
        assert canonical_profiles.intersection(profiles), (band, profiles)


def test_retained_orientation_counterexample_is_lawful_and_refutes_shortcut():
    path = HOME / "counterexamples" / "main_diagonal_only.json"
    artifact = json.loads(path.read_text())
    grid = artifact["input"]
    assert GEN.self_check(grid) == []
    assert _intended(grid) == artifact["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS["main_diagonal_only"](grid) == artifact["rival_output"]
    assert artifact["intended_output"] != artifact["rival_output"]
