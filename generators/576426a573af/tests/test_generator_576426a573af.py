"""Portable semantic regressions for generator 576426a573af.

The tests use an independent Python oracle and the public canonical helper.  They
are intentionally about the generator contract and lesson curriculum, not its
private construction helpers.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
for parent in (HOME, *HOME.parents):
    # Portable snapshots also carry shared/runtime mirrors. Execution-layout
    # dependencies must win so the selected-source loader sees one source tree.
    if (parent / "puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT))
        break
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT / "shared/runtime"))
        break
else:  # pragma: no cover - packaging contract
    raise RuntimeError("No independent puzzle_generators runtime found")

from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location("reviewed_576426a573af", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def official(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of ``overlay(flip_ud(grid), grid)`` semantics."""
    h = len(grid)
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def foreground_palette(grid):
    return {value for row in grid for value in row if value != 0}


def has_top_source(grid):
    h = len(grid)
    return any(
        grid[r][c] != 0 and grid[h - 1 - r][c] == 0
        for r in range(h // 2)
        for c in range(len(grid[0]))
    )


def has_bottom_source(grid):
    h = len(grid)
    return any(
        grid[h - 1 - r][c] != 0 and grid[r][c] == 0
        for r in range(h // 2)
        for c in range(len(grid[0]))
    )


def has_conflict(grid):
    h = len(grid)
    return any(
        grid[r][c] != 0
        and grid[h - 1 - r][c] != 0
        and grid[r][c] != grid[h - 1 - r][c]
        for r in range(h // 2)
        for c in range(len(grid[0]))
    )


def pair_for(grid):
    return {"input": grid, "output": official(grid)}


def test_authority_pin_and_small_exact_axis_surface():
    assert gen.RULE_HASH == "892d64eecd2e"
    assert set(gen.AXES) == {"grid_h", "grid_w", "fg_palette_size"}
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for key in ("texture", "fg_density", "fg_layout", "row_bias", "typo_axis"):
        with pytest.raises((TypeError, ValueError), match=key):
            gen.generate(0, 0, **{key: 1})


def test_canonical_pairs_are_owned_and_match_independent_oracle():
    canonical = pairs()
    assert len(canonical) == 3
    for pair in canonical:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert official(pair["input"]) == pair["output"]
        assert pair["input"] == original
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height", [4, 18])
@pytest.mark.parametrize("width", [3, 18])
@pytest.mark.parametrize("palette_size", [3, 6])
def test_every_exact_override_boundary_is_realized(band, height, width, palette_size):
    grid = gen.generate(
        29,
        3,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        fg_palette_size=palette_size,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(foreground_palette(grid)) == palette_size
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "fg_palette_size": palette_size,
    }
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 3},
        {"grid_h": 19},
        {"grid_w": 2},
        {"grid_w": 19},
        {"fg_palette_size": 2},
        {"fg_palette_size": 7},
        {"grid_h": True},
        {"grid_w": 4.5},
        {"fg_palette_size": "3"},
    ],
)
def test_invalid_override_values_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_bad_grids_and_minimal_impostors_are_rejected_without_crashing():
    invalid = [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True, 0], [0, 1]],
        [[10, 0], [0, 0]],
        [[-1, 0], [0, 0]],
        [[1.0, 0], [0, 0]],
        [[0] * 4 for _ in range(10)],
        [[0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 1, 0], [1, 1, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 2, 3], [0, 0, 0], [0, 0, 0], [1, 2, 3]],
    ]
    for grid in invalid:
        assert gen.self_check(grid), grid


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    before = random.getstate()
    first = gen.generate(8128, 31, difficulty="medium")
    after = random.getstate()
    second = gen.generate(8128, 31, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(12))
def test_every_four_demo_window_is_canonical_anchored_and_identifiable(band, start):
    seed = 700 + start
    grids = [gen.generate(seed, index, difficulty=band) for index in range(start, start + 5)]
    demos = [pair_for(grid) for grid in grids[: gen.EXAMPLES_NEEDED]]
    query = pair_for(grids[gen.EXAMPLES_NEEDED])

    assert all(gen.self_check(grid) == [] for grid in grids)
    assert sum(gen.strict_canonical_like(grid) == [] for grid in grids[:4]) == 1
    assert any(has_top_source(grid) for grid in grids[:4])
    assert any(has_bottom_source(grid) for grid in grids[:4])
    assert any(has_conflict(grid) for grid in grids[:4])
    assert gen.lesson_identifiable(demos, query) == []

    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_schedule_profiles_have_the_promised_semantic_roles():
    for band in (None, "easy", "medium", "hard"):
        canonical = gen.generate(991, 0, difficulty=band)
        top = gen.generate(991, 1, difficulty=band)
        bidirectional = gen.generate(991, 2, difficulty=band)
        conflict = gen.generate(991, 3, difficulty=band)

        assert gen.strict_canonical_like(canonical) == []
        assert has_bottom_source(canonical) and not has_top_source(canonical)
        assert has_top_source(top) and not has_bottom_source(top)
        assert has_top_source(bidirectional) and has_bottom_source(bidirectional)
        assert has_conflict(conflict)


def test_declared_witnesses_and_rivals_agree_with_independent_oracle():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(1234, index, difficulty=band) for index in range(4)]
        for grid in grids:
            assert gen.rule_mirror(grid) == official(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert any(predicate(grid) for grid in grids), name
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert any(rival(grid) != official(grid) for grid in grids), name


def test_conflicting_nonzero_mirror_cells_are_preserved_not_swapped():
    grid = [
        [1, 0, 0],
        [0, 3, 0],
        [0, 4, 0],
        [2, 0, 0],
    ]
    expected = [
        [1, 0, 0],
        [0, 3, 0],
        [0, 4, 0],
        [2, 0, 0],
    ]
    assert official(grid) == expected
    assert gen.rule_mirror(grid) == expected


def test_generated_population_is_not_collapsed():
    frozen = set()
    shapes = set()
    palettes = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            grid = gen.generate(seed, seed * 5 + 3, difficulty=band)
            frozen.add(json.dumps(grid, separators=(",", ":")))
            shapes.add((len(grid), len(grid[0])))
            palettes.add(tuple(sorted(foreground_palette(grid))))
    assert len(frozen) >= 60
    assert len(shapes) >= 8
    assert len(palettes) >= 20


def test_pinned_profile_floor_census_meets_the_25_percent_envelope_floor():
    import hashlib

    hits = 0
    total = 0
    canonical_profiles = {(10, 4, 4), (10, 4, 5)}
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
            total += 1
    assert hits >= total / 4, (hits, total)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_holdout_rotation_of_five_consecutive_pairs_remains_identifiable(band, start):
    seed = 5000 + start
    pairs5 = [
        pair_for(gen.generate(seed, index, difficulty=band))
        for index in range(start, start + gen.EXAMPLES_NEEDED + 1)
    ]
    for query_index, query in enumerate(pairs5):
        demos = [pair for index, pair in enumerate(pairs5) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == [], (start, query_index)
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                start,
                query_index,
                name,
            )
