"""Regression tests for the template-at-colored-anchors generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "a41ff6269d40"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _normalize(cells):
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _template(grid):
    return _normalize(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    )


def _flip_lr(shape):
    right = max(c for _, c in shape)
    return _normalize((r, right - c) for r, c in shape)


def _flip_ud(shape):
    bottom = max(r for r, _ in shape)
    return _normalize((bottom - r, c) for r, c in shape)


def independent_rule(grid, *, color2="flip_lr", color3="flip_ud"):
    """Independent mirror of the selected Racket rule."""
    h, w = len(grid), len(grid[0])
    shape = _template(grid)
    transforms = {
        "identity": shape,
        "flip_lr": _flip_lr(shape),
        "flip_ud": _flip_ud(shape),
    }
    by_color = {1: transforms["identity"], 2: transforms[color2], 3: transforms[color3]}
    out = [[0] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in by_color:
                continue
            for dr, dc in by_color[value]:
                out[r + dr][c + dc] = 4
    return out


def color2_is_identity(grid):
    return independent_rule(grid, color2="identity")


def color3_is_identity(grid):
    return independent_rule(grid, color3="identity")


def _pair(grid):
    return {"input": deepcopy(grid), "output": independent_rule(grid)}


def _anchor_colors(grid):
    return [value for row in grid for value in row if value in (1, 2, 3)]


def test_metadata_pins_the_authority_and_exposes_only_real_axes():
    assert GEN.RULE_HASH == "9011a3cbeac9"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "template_cells", "n_anchors"}


def test_canonical_pairs_are_accepted_and_the_independent_rule_matches():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_canonical_shortcut_really_fits_every_labeled_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"color2_is_identity"}
    assert all(color2_is_identity(pair["input"]) == pair["output"] for pair in pairs)
    assert all(
        GEN.CANONICAL_SHORTCUTS["color2_is_identity"](pair["input"]) == pair["output"]
        for pair in pairs
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 11, "grid_w": 11, "template_cells": 4, "n_anchors": 3},
        {"grid_h": 12, "grid_w": 18, "template_cells": 6, "n_anchors": 4},
        {"grid_h": 18, "grid_w": 12, "template_cells": 7, "n_anchors": 4},
    ],
)
def test_exact_overrides_are_constructive_observable_and_semantically_rich(band, options):
    grid = GEN.generate(813, 9, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    assert set(_anchor_colors(grid)) == {1, 2, 3}
    assert len(_anchor_colors(grid)) == options["n_anchors"]
    shape = _template(grid)
    assert len({shape, _flip_lr(shape), _flip_ud(shape)}) == 3
    expected = independent_rule(grid)
    assert color2_is_identity(grid) != expected
    assert color3_is_identity(grid) != expected
    assert GEN.SEMANTIC_RIVALS["color2_is_identity"](grid) == color2_is_identity(grid)
    assert GEN.SEMANTIC_RIVALS["color3_is_identity"](grid) == color3_is_identity(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 10},
        {"grid_h": 19},
        {"grid_w": 10},
        {"grid_w": 19},
        {"template_cells": 3},
        {"template_cells": 8},
        {"n_anchors": 2},
        {"n_anchors": 5},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"template_cells": "4"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_contains_visible_counterexamples_to_both_role_shortcuts(band):
    for index in range(64):
        grid = GEN.generate(1201, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert set(_anchor_colors(grid)) == {1, 2, 3}
        shape = _template(grid)
        assert len({shape, _flip_lr(shape), _flip_ud(shape)}) == 3
        answer = independent_rule(grid)
        assert color2_is_identity(grid) != answer
        assert color3_is_identity(grid) != answer
        assert GEN.SEMANTIC_WITNESSES["horizontal_role_visible"](grid)
        assert GEN.SEMANTIC_WITNESSES["vertical_role_visible"](grid)
        assert GEN.SEMANTIC_WITNESSES["all_anchor_roles_present"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_generated_four_pair_window_is_identifiable_under_query_rotation(band):
    for start in range(12):
        pairs = [_pair(GEN.generate(2309 + start, start + offset, difficulty=band))
                 for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_lesson_hook_reproduces_and_then_refutes_the_missing_role_defects():
    rich = GEN.generate(41, 7, grid_h=12, grid_w=12, template_cells=6, n_anchors=3)
    query = _pair(rich)

    without_three = [[1 if value == 3 else value for value in row] for row in rich]
    reasons = GEN.lesson_identifiable([_pair(without_three)], query)
    assert any("color3_is_identity" in reason for reason in reasons)
    assert GEN.lesson_identifiable([query], query) == []

    without_two = [[1 if value == 2 else value for value in row] for row in rich]
    reasons = GEN.lesson_identifiable([_pair(without_two)], query)
    assert any("color2_is_identity" in reason for reason in reasons)


def test_pinned_profile_floor_has_exact_support_in_every_band():
    profiles = {(11, 11, 4), (12, 12, 5)}
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += profile in profiles
        assert exact >= 1, (band, exact)


def test_distribution_varies_dimensions_shapes_and_anchor_positions():
    grids = [GEN.generate(991, index, difficulty="medium") for index in range(160)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert len({item["grid_h"] for item in observed}) >= 6
    assert len({item["grid_w"] for item in observed}) >= 6
    assert {item["template_cells"] for item in observed} == {4, 5, 6, 7}
    assert {item["n_anchors"] for item in observed} == {3, 4}
    assert len({_template(grid) for grid in grids}) >= 40
    anchor_layouts = {
        tuple((r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value in (1, 2, 3))
        for grid in grids
    }
    assert len(anchor_layouts) >= 150


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(16):
            first = GEN.generate(73, index, difficulty=band)
            second = GEN.generate(73, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            assert GEN.self_check(first) == []
            assert GEN.observe_overrides(first) == GEN.observe_overrides(second)
            for fn in (*GEN.SEMANTIC_RIVALS.values(), *GEN.SEMANTIC_WITNESSES.values()):
                fn(first)
                assert first == original


def test_self_check_rejects_malformed_palette_disconnected_and_clipped_instances():
    good = GEN.generate(91, 3, grid_h=12, grid_w=12, template_cells=5, n_anchors=3)
    assert GEN.self_check(good) == []

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(12)]):
        assert GEN.self_check(malformed)

    unknown = deepcopy(good)
    unknown[0][0] = 9
    assert GEN.self_check(unknown)

    disconnected = deepcopy(good)
    for r, row in enumerate(disconnected):
        for c, value in enumerate(row):
            if value == 4:
                disconnected[r][c] = 0
    disconnected[0][0] = 4
    disconnected[-1][-1] = 4
    assert GEN.self_check(disconnected)

    clipped = deepcopy(good)
    # Move one anchor origin to the bottom-right, where any multi-cell template clips.
    moved = False
    for r, row in enumerate(clipped):
        for c, value in enumerate(row):
            if value in (1, 2, 3):
                clipped[r][c] = 0
                clipped[-1][-1] = value
                moved = True
                break
        if moved:
            break
    assert GEN.self_check(clipped)
