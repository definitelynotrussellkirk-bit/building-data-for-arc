"""Regression tests for the fill-between-matching-endpoints sampler."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2038a3a66886"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def intended_output(grid):
    """Independent oracle matching the selected per-color row-span authority."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            cols = [c for c, value in enumerate(row) if value == color]
            if len(cols) >= 2:
                for c in range(cols[0], cols[-1] + 1):
                    out[r][c] = color
    return out


def outermost_nonzero_shortcut(grid):
    """Wrong canonical-fitting rival: one leftmost-colored span per nonempty row."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value != 0]
        if len(cols) >= 2:
            color = row[cols[0]]
            for c in range(cols[0], cols[-1] + 1):
                out[r][c] = color
    return out


def exact_pair_only_shortcut(grid):
    """Wrong canonical-fitting rival: ignore colors occurring three or more times."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [c for c, value in enumerate(row) if value == color]
                for c in range(cols[0], cols[-1] + 1):
                    out[r][c] = color
    return out


def observed_pattern(grid):
    patterns = set()
    for row in grid:
        counts = sorted(Counter(value for value in row if value != 0).values())
        if not counts:
            continue
        patterns.add({
            (2,): "canonical",
            (3,): "triple",
            (2, 2): "multi_pair",
            (1, 2): "distractor",
            (2, 3): "combined",
        }[tuple(counts)])
    assert len(patterns) == 1
    return patterns.pop()


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "aefdabd461d1"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "rows", "row_pattern"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("pattern", ["canonical", "triple", "multi_pair", "distractor", "combined"])
def test_every_exact_override_is_constructive_in_every_band(band, pattern):
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=6,
        grid_w=9,
        rows=6,
        row_pattern=pattern,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 9,
        "rows": 6,
        "row_pattern": pattern,
    }
    assert observed_pattern(grid) == pattern
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 5),
        ("grid_h", 19),
        ("grid_w", 8),
        ("grid_w", 23),
        ("rows", 0),
        ("rows", 7),
        ("row_pattern", "unknown"),
        ("typo_axis", 1),
        ("rows", True),
        ("grid_w", 9.5),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


def test_canonical_inputs_are_owned_and_oracle_matches_all_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_covers_all_semantic_row_patterns(band):
    seen = set()
    exact_profiles = set()
    canonical_profiles = {(7, 10, 4), (8, 12, 4), (6, 9, 3), (9, 11, 4), (7, 13, 4)}
    for index in range(180):
        grid = GEN.generate(3000 + index, index * 13 + 5, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(3000 + index, index * 13 + 5, difficulty=band)
        seen.add(GEN.observe_overrides(grid)["row_pattern"])
        exact_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert intended_output(grid) != grid
    assert seen == {"canonical", "triple", "multi_pair", "distractor", "combined"}
    assert canonical_profiles & exact_profiles


def test_declared_shortcuts_fit_canonical_but_generated_witnesses_refute_them():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert all(outermost_nonzero_shortcut(p["input"]) == p["output"] for p in pairs)
    assert all(exact_pair_only_shortcut(p["input"]) == p["output"] for p in pairs)

    distractor = GEN.generate(44, 1, row_pattern="distractor", rows=2)
    triple = GEN.generate(44, 2, row_pattern="triple", rows=2)
    assert GEN.SEMANTIC_WITNESSES["mixed_row"](distractor)
    assert GEN.SEMANTIC_RIVALS["outermost_nonzero"](distractor) == outermost_nonzero_shortcut(distractor)
    assert outermost_nonzero_shortcut(distractor) != intended_output(distractor)
    assert GEN.SEMANTIC_WITNESSES["triple_occurrence"](triple)
    assert GEN.SEMANTIC_RIVALS["exact_pair_only"](triple) == exact_pair_only_shortcut(triple)
    assert exact_pair_only_shortcut(triple) != intended_output(triple)


def test_generation_and_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 202, row_pattern="combined")
    original = deepcopy(grid)
    assert intended_output(grid) != grid
    for function in GEN.SEMANTIC_RIVALS.values():
        function(grid)
        assert grid == original
    GEN.strict_canonical_like(grid)
    GEN.observe_overrides(grid)
    assert grid == original


def test_pinned_profile_floor_has_cross_band_exact_and_envelope_support():
    """Lock the repaired palette-scale defect to the shared gate's census."""
    import hashlib

    canonical_profiles = {(7, 10, 4), (8, 12, 4), (6, 9, 3), (9, 11, 4), (7, 13, 4)}
    pooled_envelope = 0
    for band in ("easy", "medium", "hard"):
        exact = 0
        envelope = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact += profile in canonical_profiles
            envelope += 6 <= profile[0] <= 9 and 9 <= profile[1] <= 13 and 3 <= profile[2] <= 4
        assert exact >= 1, band
        assert envelope >= 5, band
        pooled_envelope += envelope
    assert pooled_envelope >= 15
