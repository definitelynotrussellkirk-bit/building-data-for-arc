"""Portable behavioral and exact-control regressions for acb1cae24892."""
from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
G, _, _ = load_selected_generator("acb1cae24892", root=ROOT)


def oracle(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = sorted({v for row in grid for v in row if v})
    for color in colors:
        pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(pts) != 2:
            continue
        (r0, c0), (r1, c1) = pts
        lo_r, hi_r = sorted((r0, r1)); lo_c, hi_c = sorted((c0, c1))
        for r in range(lo_r, hi_r + 1):
            for c in range(lo_c, hi_c + 1):
                if r in (lo_r, hi_r) or c in (lo_c, hi_c):
                    out[r][c] = color
    return out


def test_rule_hash_and_canonical_labels():
    pairs = canonical_pairs("acb1cae24892", root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert G.self_check(pair["input"]) == []
        assert G.rule_mirror(pair["input"]) == pair["output"] == oracle(pair["input"])
    assert G.RULE_HASH == "89b3f3e5cc80"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,n", [(7, 7, 1), (7, 14, 3), (14, 7, 3), (14, 14, 3)])
def test_joint_exact_controls_ignore_default_band_ranges(band, h, w, n):
    requested = {"grid_h": h, "grid_w": w, "n_colors": n}
    grid = G.generate(19, 4, difficulty=band, **requested)
    assert G.observe_overrides(grid) == requested
    assert G.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert oracle(grid) == G.rule_mirror(grid)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "n_colors"])
@pytest.mark.parametrize("bad", [True, 7.0, "7", -1, 31])
def test_invalid_scalars_reject(axis, bad):
    with pytest.raises(ValueError):
        G.generate(1, 0, **{axis: bad})


@pytest.mark.parametrize("axis", ["palette_kind", "palette_size", "position_bias", "n_distinct_colors", "density", "texture", "unknown"])
def test_removed_and_unknown_controls_reject(axis):
    with pytest.raises(ValueError, match="unsupported override"):
        G.generate(1, 0, **{axis: None})


def test_determinism_fresh_returns_and_rng_purity():
    random.seed(99); before = random.getstate()
    a = G.generate(22, 3, difficulty="medium")
    assert random.getstate() == before
    b = G.generate(22, 3, difficulty="medium")
    assert a == b and a is not b and all(x is not y for x, y in zip(a, b))
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b


def test_generated_pairs_are_exact_and_cover_all_geometry_branches():
    seen = set()
    for index in range(9):
        grid = G.generate(7, index, difficulty="hard", n_colors=3)
        assert G.self_check(grid) == []
        for color in {v for row in grid for v in row if v}:
            pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
            assert len(pts) == 2
            same_row = pts[0][0] == pts[1][0]
            same_col = pts[0][1] == pts[1][1]
            seen.add("row" if same_row else "col" if same_col else "rect")
    assert seen == {"row", "col", "rect"}


def test_malformed_and_wrong_metadata_reject():
    assert G.self_check([[0, 0], [0]])
    assert G.self_check([[True] * 7 for _ in range(7)])
    grid = G.generate(3, 0, grid_h=7, grid_w=8, n_colors=2)
    assert G.self_check(grid, meta={"overrides": {"grid_h": 8}})
    with pytest.raises(ValueError, match="unsupported difficulty"):
        G.generate(1, 0, difficulty="extreme")

def test_declares_strict_canonical_like_semantic_contract():
    for pair in canonical_pairs("acb1cae24892", root=ROOT, labeled_only=True):
        assert G.strict_canonical_like(pair["input"]) == []
    generated = G.generate(83, 4, difficulty="hard", n_colors=3)
    assert G.strict_canonical_like(generated) == []
    assert G.strict_canonical_like([[1, 0], [0]])

