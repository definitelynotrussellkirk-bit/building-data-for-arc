"""Request provenance and meaningful spout/large-canvas coverage regressions."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys

import pytest

for parent in Path(__file__).resolve().parents:
    support = next((p for p in (parent / "reviewer_support.py",
                               parent / "shared/runtime/reviewer_support.py")
                    if p.is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break

from reviewer_support import find_root, load_selected_generator

GEN, SOURCE, SOURCE_SHA = load_selected_generator(
    "bee63e6e52bd", root=find_root(__file__)
)
BANDS = (None, "easy", "medium", "hard")
CANONICAL = ("6x6", "7x7", "9x9", "10x10")
LARGE = ("21x21", "21x30", "30x21", "30x30")


def diagonal_lengths(grid):
    """Read available post-anchor ray lengths from input geometry only."""
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    h, w = len(grid), len(grid[0])
    sides = {
        "left": [(r, c0) for r in range(r0, r1 + 1)],
        "right": [(r, c1) for r in range(r0, r1 + 1)],
        "top": [(r0, c) for c in range(c0, c1 + 1)],
        "bottom": [(r1, c) for c in range(c0, c1 + 1)],
    }
    side, positions = next((s, ps) for s, ps in sides.items()
                           if any(grid[r][c] == 0 for r, c in ps))
    missing = [i for i, (r, c) in enumerate(positions) if grid[r][c] == 0]
    a = positions[missing[0] - 1]
    b = positions[missing[-1] + 1]
    if side == "left":
        return min(a[0], c0 - 1), min(h - 1 - b[0], c0 - 1)
    if side == "right":
        return min(a[0], w - c1 - 2), min(h - 1 - b[0], w - c1 - 2)
    if side == "top":
        return min(a[1], r0 - 1), min(w - 1 - b[1], r0 - 1)
    return min(a[1], h - r1 - 2), min(w - 1 - b[1], h - r1 - 2)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_an_actual_integer(band, bad):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad, 0, difficulty=band)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_sample_index_requires_an_actual_integer(band, bad):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, bad, difficulty=band)


@pytest.mark.parametrize("band", BANDS)
def test_negative_sample_index_rejected_even_with_an_explicit_arm_override(band):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, -1, difficulty=band, arm_profile="canonical_2_2")


def test_valid_signed_integer_seeds_and_zero_index_remain_deterministic():
    for seed in (-2**70, -1, 0, 1, 2**70):
        grid = GEN.generate(seed, 0)
        assert grid == GEN.generate(seed, 0)
        assert GEN.self_check(grid) == []


def test_hard_frames_retain_at_least_one_visible_diagonal_step():
    for i, (profile, side, arms) in enumerate(itertools.product(
            CANONICAL, GEN.OPEN_SIDES, GEN.ARM_LENGTHS)):
        grid = GEN.generate(12000 + i, i, difficulty="hard", scene_profile=profile,
                            open_side=side, arm_profile=arms)
        assert max(diagonal_lengths(grid)) >= 1, (profile, side, arms)


@pytest.mark.parametrize("band", BANDS)
def test_large_exact_overrides_scale_geometry_and_expose_long_spouts(band):
    for i, (profile, side, arms) in enumerate(itertools.product(
            LARGE, GEN.OPEN_SIDES, GEN.ARM_LENGTHS)):
        grid = GEN.generate(15000 + i, i, difficulty=band, scene_profile=profile,
                            open_side=side, arm_profile=arms, color=8)
        h, w = map(int, profile.split("x"))
        assert (len(grid), len(grid[0])) == (h, w)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "scene_profile": profile, "open_side": side, "arm_profile": arms, "color": 8}
        assert GEN.strict_canonical_like(grid), "large support is not a canonical profile"
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
        bh = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        assert min(bh, bw) >= 7, "larger inputs must scale the frame, not just pad it"
        assert max(diagonal_lengths(grid)) >= 3, (profile, side, arms)


def test_ordinary_samples_keep_the_canonical_profile_contract():
    for band in BANDS:
        for i in range(80):
            grid = GEN.generate(23000 + i, i, difficulty=band)
            assert f"{len(grid)}x{len(grid[0])}" in CANONICAL
            assert GEN.strict_canonical_like(grid) == []


def test_accepted_tuple_grids_execute_without_mutation():
    grid = GEN.generate(173, 2, difficulty="medium")
    tuples = tuple(tuple(row) for row in grid)
    assert GEN.self_check(tuples) == []
    assert GEN._apply_intended(tuples) == GEN._apply_intended(grid)
    assert tuples == tuple(tuple(row) for row in grid)


def test_no_diagonal_rule_is_a_lesson_rival_but_not_a_canonical_shortcut():
    assert "no_diagonal_spouts" in GEN.LESSON_COMPETITORS
    assert "no_diagonal_spouts" in GEN.SEMANTIC_RIVALS
    assert "no_diagonal_spouts" not in GEN.CANONICAL_SHORTCUTS
    for band in BANDS:
        for seed in range(20):
            pairs = [{"input": GEN.generate(44000 + seed, 4 * seed + j, difficulty=band)}
                     for j in range(4)]
            for pair in pairs:
                pair["output"] = GEN._apply_intended(pair["input"])
            for query_i in range(4):
                demos = [p for i, p in enumerate(pairs) if i != query_i]
                assert any(GEN.LESSON_COMPETITORS["no_diagonal_spouts"](p["input"])
                           != p["output"] for p in demos)
                assert GEN.lesson_identifiable(demos, pairs[query_i]) == []


def test_saved_racket_labelled_lesson_now_exposes_the_missing_spout_rule():
    path = find_root(__file__) / "generators/bee63e6e52bd/counterexamples/no-diagonal-lesson.json"
    record = json.loads(path.read_text())
    assert record["generator_sha256"] == "9ff3ab296a273b534f701a0f46591266a73e8003827f76765588cc14c14ebcb1"
    assert record["rule_hash"] == GEN.RULE_HASH
    pairs = record["pairs"]
    rival = GEN.LESSON_COMPETITORS["no_diagonal_spouts"]
    assert all(GEN.self_check(pair["input"]) == [] for pair in pairs)
    assert [rival(p["input"]) == p["output"] for p in pairs] == [True, True, True, False]
    assert any("no_diagonal_spouts" in reason
               for reason in GEN.lesson_identifiable(pairs[:3], pairs[3]))
