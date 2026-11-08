"""Focused regressions for the knight-halo input sampler.

The geometry oracle and max-color rival below are independent of generator
helpers.  Canonical labels and retained witness labels are also checked through
the public Racket-backed Catalog API.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "a82753d0e28f"
TASK_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "a82753d0e28f_under_test", TASK_DIR / "generator.py"
)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)

KNIGHT = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
)
BANDS = (None, "easy", "medium", "hard")


def knight_output(grid):
    """Independent row-major overwrite oracle matching the selected rule."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            out[r][c] = color
            for dr, dc in KNIGHT:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = color
    return out


def max_color_output(grid):
    """Plausible shortcut: resolve all seed/halo collisions by max color."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            for rr, cc in ((r, c), *((r + dr, c + dc) for dr, dc in KNIGHT)):
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = max(out[rr][cc], color)
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seeds": sum(value != 0 for row in grid for value in row),
    }


def visible_halo_size(grid, r, c):
    h, w = len(grid), len(grid[0])
    return sum(0 <= r + dr < h and 0 <= c + dc < w for dr, dc in KNIGHT)


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_canonical_inputs_are_owned_and_independent_oracle_matches_labels(canonical):
    assert len(canonical) == 3
    for pair in canonical:
        assert gen.self_check(pair["input"]) == [], (pair.get("variant"), pair.get("split"), pair.get("pair_index"))
        assert knight_output(pair["input"]) == pair["output"], (pair.get("variant"), pair.get("split"), pair.get("pair_index"))
        assert gen.strict_canonical_like(pair["input"]) == [], (pair.get("variant"), pair.get("split"), pair.get("pair_index"))


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "options",
    (
        {"grid_h": 7, "grid_w": 8, "seeds": 2},
        {"grid_h": 8, "grid_w": 10, "seeds": 3},
        {"grid_h": 10, "grid_w": 12, "seeds": 4},
    ),
)
def test_exact_controls_are_honored_and_observable_in_every_band(band, options):
    grid = gen.generate(391, 17, difficulty=band, **options)
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.strict_canonical_like(grid) == []
    assert knight_output(grid) != max_color_output(grid)


@pytest.mark.parametrize(
    "key,value",
    (
        ("grid_h", 6), ("grid_h", 11),
        ("grid_w", 7), ("grid_w", 13),
        ("seeds", 1), ("seeds", 5),
        ("grid_h", True), ("grid_w", 9.0), ("seeds", "2"),
        ("palette_kind", "warm"), ("palette_size", 2),
        ("n_distinct_colors", 2), ("position_bias", "interior_separated"),
        ("density", "sparse"), ("texture", "seed_at_corner"),
        ("unknown_axis", 1),
    ),
)
def test_invalid_retired_or_unknown_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_none_controls_preserve_default_draw_convention():
    assert gen.generate(22, 5, grid_h=None, grid_w=None, seeds=None) == gen.generate(22, 5)


@pytest.mark.parametrize(
    "grid",
    (
        None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)],
        [[0] * 9 for _ in range(7)], [[10] + [0] * 8 for _ in range(7)],
        ["000000000"] * 7,
    ),
)
def test_malformed_inputs_return_diagnostics_not_exceptions(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


def test_max_color_shortcut_fits_every_canonical_label(canonical):
    assert set(gen.CANONICAL_SHORTCUTS) == {"max_color_wins"}
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert gen.CANONICAL_SHORTCUTS["max_color_wins"](pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_retained_counterexample_refutes_max_color_shortcut():
    fixture = json.loads((TASK_DIR / "counterexamples/max_color_wins.json").read_text())
    grid = fixture["input"]
    assert gen.self_check(grid) == []
    assert knight_output(grid) == fixture["intended_output"]
    assert max_color_output(grid) == fixture["rival_output"]
    assert fixture["intended_output"] != fixture["rival_output"]
    assert gen.SEMANTIC_WITNESSES["later_lower_overlap"](grid)
    assert gen.SEMANTIC_RIVALS["max_color_wins"](grid) == fixture["rival_output"]
    assert gen.SEMANTIC_RIVALS["max_color_wins"](grid) != fixture["intended_output"]


def test_canonical_and_counterexample_outputs_match_real_racket(canonical):
    fixture = json.loads((TASK_DIR / "counterexamples/max_color_wins.json").read_text())
    grids = [pair["input"] for pair in canonical] + [fixture["input"]]
    expected = [pair["output"] for pair in canonical] + [fixture["intended_output"]]
    receipt = Catalog(find_root(__file__)).apply(
        TASK_ID, grids, reference="canonical", timeout=120
    )
    assert receipt["rule_hash_matches_catalog"]
    assert [row["output"] for row in receipt["results"]] == expected
    assert all(row["valid_output"] and row["error"] is None for row in receipt["results"])


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_sampler_is_deterministic_lawful_varied_and_always_refutes_shortcut(band):
    shapes = set()
    counts = set()
    clipped = full = False
    for index in range(96):
        grid = gen.generate(1200 + index, index * 17 + 3, difficulty=band)
        assert grid == gen.generate(1200 + index, index * 17 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert gen.strict_canonical_like(grid) == []
        assert knight_output(grid) != max_color_output(grid)
        assert gen.SEMANTIC_WITNESSES["later_lower_overlap"](grid)
        shapes.add((len(grid), len(grid[0])))
        counts.add(observed(grid)["seeds"])
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    size = visible_halo_size(grid, r, c)
                    clipped |= size < 8
                    full |= size == 8
    assert len(shapes) >= 8
    assert counts == {2, 3, 4}
    assert clipped and full


def test_profile_floor_support_is_preserved_in_every_band():
    canonical_profiles = {(7, 9, 3), (8, 9, 3), (8, 10, 3)}
    exact_total = envelope_total = 0
    for band in ("easy", "medium", "hard"):
        band_exact = 0
        for index in range(20):
            seed = pinned_seed(band, index)
            sample_index = seed % 7919 + index
            p = profile(gen.generate(seed, sample_index, difficulty=band))
            band_exact += p in canonical_profiles
            envelope_total += 7 <= p[0] <= 8 and 9 <= p[1] <= 10 and p[2] == 3
        assert band_exact >= 1, band
        exact_total += band_exact
    assert exact_total >= 3
    assert envelope_total >= 15

@pytest.mark.parametrize("bad_seed", (True, False, 1.0, 1.75, "1"))
def test_seed_requires_an_actual_integer(bad_seed):
    with pytest.raises(TypeError):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", (True, False, 1.0, 1.75, "1", -1))
def test_sample_index_requires_a_nonnegative_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, bad_index)
