"""Generator for cc100a8ad437 — outline every original-orientation match.

Canonical rule
--------------
A full-height color-9 column separates a template panel from a board.  Crop the
non-zero template object, then find every ORIGINAL-ORIENTATION placement whose
non-zero template cells equal the board.  Template zeroes are wildcards: extra
board cells in those positions do not invalidate a match.  Return a board-sized
zero grid with a cyan(8) rectangle outline around every matched window.

The teaching stream constructs exact positive placements at independent,
arbitrary offsets and verifies the full match set after every stamp.  It also
places rotated/reflected same-color near-misses and, on the ``varied`` schedule
branch, non-template clutter in a wildcard slot of a true match.  The exported
semantic contract checks sliding four-demo lessons against literal-zero,
dihedral, and origin-lattice rival rules.  These witnesses rule out the main
cheap shortcuts while preserving exact override behavior.

Sequential lessons use ``sample_index % 3`` to cycle varied/wide/tall template
families, so the default four demonstrations expose all three branches before
the query.  Exact overrides remain valid over the complete declared domains;
incompatible *combinations* reject loudly rather than clamping.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc100a8ad437"
TASK_ID = "cc100a8ad437"
VERSION = "3.1.0"  # arbitrary offsets, semantic rivals, override-safe curriculum
RULE_HASH = "c8e7dd82305a"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A color-9 divider separates a cropped monochrome template from a board. "
    "Find every original-orientation placement matching the template's nonzero "
    "cells (template zeroes are wildcards), then outline each matched bounding "
    "window in cyan(8) on a board-sized zero grid."
)

INVARIANTS = [
    "exactly one full-height color-9 divider occurs at column 3",
    "the cropped template is one orthogonally connected monochrome object of 3..5 cells",
    "the board contains 1..6 original-orientation wildcard matches",
    "ordinary lessons place positives at at least two independent offset residues",
    "normal lessons include lawful wildcard and same-color orientation distractors",
    "the output authority is the canonical Racket rule; Python rule_mirror is test-only",
]

TEXTURES = ("varied", "wide", "tall")
HELPFUL_TEXTURES = TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 6..16; easy anchors canonical 6..8",
        "valid": "6..16",
    },
    "board_w": {
        "type": "int",
        "default": "difficulty-aware 8..20; easy anchors canonical width 8",
        "valid": "8..20",
    },
    "shape_size": {
        "type": "int",
        "default": "easy 5; medium 4..5; hard 3..5",
        "valid": "3..5",
    },
    "n_inst": {
        "type": "int",
        "default": "easy 2..3; medium 2..4; hard 3..6",
        "valid": "1..6",
    },
    "texture": {
        "type": "str",
        "default": "sample_index cycle varied|wide|tall",
        "valid": "varied|wide|tall",
    },
}

# Every shape is connected, fits in 3x3, and has a nontrivial transformed
# orientation.  Wide/tall are paired transposes; varied includes the official
# five-cell L at size 5.
_SHAPES = {
    ("varied", 3): ((0, 0), (1, 0), (1, 1)),
    ("varied", 4): ((0, 0), (1, 0), (1, 1), (2, 1)),
    ("varied", 5): ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ("wide", 3): ((0, 0), (1, 0), (1, 1)),
    ("wide", 4): ((0, 0), (1, 0), (1, 1), (1, 2)),
    ("wide", 5): ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ("tall", 3): ((0, 0), (0, 1), (1, 0)),
    ("tall", 4): ((0, 0), (0, 1), (1, 0), (2, 0)),
    ("tall", 5): ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
}


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = deque(seen)
    while todo:
        r, c = todo.popleft()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen == cells


def _transform_variants(cells):
    """All normalized rotations/reflections, excluding duplicate geometry."""
    current = tuple(cells)
    variants = set()
    for reflected in (False, True):
        work = tuple((r, -c if reflected else c) for r, c in current)
        for _ in range(4):
            work = _normalize(work)
            variants.add(work)
            work = tuple((c, -r) for r, c in work)
    return tuple(sorted(variants))


def _crop_template(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [], (), None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    crop = [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]
    color = next((value for row in crop for value in row if value != 0), None)
    shape = tuple(
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value != 0
    )
    return crop, shape, color


def _split_input(grid):
    h = len(grid)
    w = len(grid[0])
    divider_cols = [
        c for c in range(w) if all(grid[r][c] == 9 for r in range(h))
    ]
    if len(divider_cols) != 1:
        raise ValueError(f"expected one divider, got {divider_cols}")
    div = divider_cols[0]
    return [row[:div] for row in grid], [row[div + 1:] for row in grid], div


def _match_positions(board, shape, color):
    if not board or not board[0] or not shape or color is None:
        return []
    h, w = len(board), len(board[0])
    sh, sw = _dims(shape)
    hits = []
    for r0 in range(h - sh + 1):
        for c0 in range(w - sw + 1):
            if all(board[r0 + dr][c0 + dc] == color for dr, dc in shape):
                hits.append((r0, c0))
    return hits


def _stamp(board, cells, r0, c0, color):
    for dr, dc in cells:
        if board[r0 + dr][c0 + dc] not in (0, color):
            raise ValueError("stamp collision with a different color")
    for dr, dc in cells:
        board[r0 + dr][c0 + dc] = color


def _draw_outline(out, r0, c0, r1, c1):
    for c in range(c0, c1 + 1):
        out[r0][c] = 8
        out[r1][c] = 8
    for r in range(r0, r1 + 1):
        out[r][c0] = 8
        out[r][c1] = 8


def rule_mirror(grid):
    """Independent test mirror of the canonical Racket rule.

    This function is never used by ``generate`` and is not an output authority.
    """
    left, board, _ = _split_input(grid)
    _, shape, color = _crop_template(left)
    if not shape:
        raise ValueError("empty template")
    sh, sw = _dims(shape)
    out = full_grid(len(board), len(board[0]), 0)
    for r0, c0 in _match_positions(board, shape, color):
        _draw_outline(out, r0, c0, r0 + sh - 1, c0 + sw - 1)
    return out


def observe_overrides(grid):
    """Exact realized semantic axes recoverable from the returned grid."""
    left, board, _ = _split_input(grid)
    _, shape, color = _crop_template(left)
    return {
        "board_w": len(board[0]),
        "shape_size": len(shape),
        "n_inst": len(_match_positions(board, shape, color)),
    }


def semantic_observables(grid):
    """Task-linked observables used by focused tests and review evidence."""
    left, board, _ = _split_input(grid)
    crop, shape, color = _crop_template(left)
    hits = _match_positions(board, shape, color)
    sh, sw = _dims(shape)
    wildcard_clutter = 0
    for r0, c0 in hits:
        for r in range(sh):
            for c in range(sw):
                if crop[r][c] == 0 and board[r0 + r][c0 + c] != 0:
                    wildcard_clutter += 1
    covered = {
        (r0 + dr, c0 + dc)
        for r0, c0 in hits
        for dr, dc in shape
    }
    template_color_decoy_cells = sum(
        value == color and (r, c) not in covered
        for r, row in enumerate(board)
        for c, value in enumerate(row)
    )
    output = rule_mirror(grid)
    return {
        "grid_h": len(grid),
        "board_w": len(board[0]),
        "shape_size": len(shape),
        "template_bbox": [sh, sw],
        "template_color": color,
        "match_count": len(hits),
        "match_positions": [list(hit) for hit in hits],
        "wildcard_clutter_cells": wildcard_clutter,
        "template_color_decoy_cells": template_color_decoy_cells,
        "output_cyan_cells": sum(value == 8 for row in output for value in row),
        "palette": sorted({value for row in grid for value in row}),
    }


def _axis_texture(ctx, sample_index):
    if "texture" in ctx.overrides and ctx.overrides["texture"] is not None:
        return ctx.draw_choice("texture", TEXTURES)
    scheduled = TEXTURES[sample_index % len(TEXTURES)]
    return ctx.draw_choice("texture", (scheduled,))


def _preferred_ranges(difficulty):
    if difficulty == "easy":
        return (6, 8), (8, 10), (5, 5), (2, 3)
    if difficulty == "hard":
        return (10, 16), (12, 20), (3, 5), (3, 6)
    return (7, 12), (9, 14), (4, 5), (2, 4)


def _choose_shape_and_count(ctx, rng, texture, difficulty, canonical_anchor):
    """Draw shape/count jointly when exact dimensions constrain capacity.

    A partial override such as ``grid_h=6, board_w=8`` must not fail merely
    because unspecified hard-band defaults happened to draw six 3x3 copies.
    When both dimensions are exact, choose the remaining axes from feasible
    defaults (then their full valid domains if needed). Fully explicit,
    genuinely incompatible combinations still reject loudly downstream.
    """
    _, _, shape_range, count_range = _preferred_ranges(difficulty)
    explicit_shape = ctx.overrides.get("shape_size") is not None
    explicit_count = ctx.overrides.get("n_inst") is not None
    shape_value = (
        ctx.draw_int("shape_size", 3, 5) if explicit_shape else None
    )
    count_value = (
        ctx.draw_int("n_inst", 1, 6) if explicit_count else None
    )

    if canonical_anchor:
        return (
            ctx.draw_int("shape_size", 5, 5),
            ctx.draw_int("n_inst", 2, 2),
        )

    explicit_h = ctx.overrides.get("grid_h") is not None
    explicit_w = ctx.overrides.get("board_w") is not None
    if explicit_h and explicit_w:
        h = int(ctx.overrides["grid_h"])
        w = int(ctx.overrides["board_w"])
        shape_candidates = (
            [shape_value]
            if explicit_shape
            else list(range(shape_range[0], shape_range[1] + 1))
        )
        count_candidates = (
            [count_value]
            if explicit_count
            else list(range(count_range[0], count_range[1] + 1))
        )

        def feasible_pairs(shapes, counts):
            pairs = []
            for shape_size in shapes:
                sh, sw = _dims(_SHAPES[(texture, shape_size)])
                capacity = (h // sh) * (w // sw)
                for n_inst in counts:
                    if capacity >= n_inst:
                        pairs.append((shape_size, n_inst))
            return pairs

        feasible = feasible_pairs(shape_candidates, count_candidates)
        if not feasible:
            # Adapt only axes the caller did not specify. This keeps partial
            # dimension overrides productive without clamping exact requests.
            shape_candidates = [shape_value] if explicit_shape else list(range(3, 6))
            count_candidates = [count_value] if explicit_count else list(range(1, 7))
            feasible = feasible_pairs(shape_candidates, count_candidates)
        if feasible:
            selected_shape, selected_count = rng.choice(feasible)
            if not explicit_shape:
                shape_value = ctx.draw_int(
                    "shape_size", selected_shape, selected_shape
                )
            if not explicit_count:
                count_value = ctx.draw_int("n_inst", selected_count, selected_count)
            return shape_value, count_value

    if shape_value is None:
        shape_value = ctx.draw_int(
            "shape_size", shape_range[0], shape_range[1]
        )
    if count_value is None:
        count_value = ctx.draw_int("n_inst", count_range[0], count_range[1])
    return shape_value, count_value


def _choose_dimensions(
    ctx, rng, sh, sw, n_inst, difficulty, sample_index, canonical_anchor=False
):
    (h_lo, h_hi), (w_lo, w_hi), _, _ = _preferred_ranges(difficulty)

    explicit_h = ctx.overrides.get("grid_h") is not None
    explicit_w = ctx.overrides.get("board_w") is not None
    requested_h = int(ctx.overrides["grid_h"]) if explicit_h else None
    requested_w = int(ctx.overrides["board_w"]) if explicit_w else None
    if explicit_h and not 6 <= requested_h <= 16:
        raise ValueError(f"grid_h override {requested_h} outside 6..16")
    if explicit_w and not 8 <= requested_w <= 20:
        raise ValueError(f"board_w override {requested_w} outside 8..20")

    hs = [requested_h] if explicit_h else list(range(h_lo, h_hi + 1))
    ws = [requested_w] if explicit_w else list(range(w_lo, w_hi + 1))
    # Expand an unoverridden dimension only when the ordinary band cannot fit
    # the requested exact count/shape.  We reserve one tile for a distractor
    # whenever possible, but exact positives remain the hard constraint.
    if not explicit_h:
        hs += [h for h in range(6, 17) if h not in hs]
    if not explicit_w:
        ws += [w for w in range(8, 21) if w not in ws]

    feasible = []
    for h in hs:
        for w in ws:
            capacity = (h // sh) * (w // sw)
            if capacity >= n_inst:
                feasible.append((h, w, capacity))
    if not feasible:
        raise ValueError(
            "incompatible exact overrides: no 6..16 x 8..20 board can fit "
            f"n_inst={n_inst} copies of a {sh}x{sw} template"
        )

    preferred = [
        item for item in feasible
        if h_lo <= item[0] <= h_hi and w_lo <= item[1] <= w_hi
    ]
    pool = preferred or feasible
    # New repairs are checked for canonical-scale support in every difficulty
    # band.  A scheduled, override-free anchor reproduces one of the three
    # observed (height, board-width) pairs; the remaining samples keep the
    # wider band-specific curriculum.
    if canonical_anchor and not explicit_h and not explicit_w:
        canonical_dims = {(6, 8), (7, 8), (7, 9)}
        canonical = [item for item in feasible if item[:2] in canonical_dims]
        if not canonical:
            raise RuntimeError("scheduled canonical anchor unexpectedly infeasible")
        pool = canonical
    # Retain the older easy-only anchor on non-anchor samples for continuity.
    elif (
        difficulty == "easy"
        and not explicit_h
        and not explicit_w
        and sample_index % 4 == 0
    ):
        canonical = [item for item in pool if item[0] in (6, 7) and item[1] == 8]
        if canonical:
            pool = canonical
    reserve = [item for item in pool if item[2] >= n_inst + 1]
    if reserve:
        pool = reserve
    h, w, _ = rng.choice(pool)
    if explicit_h:
        h = ctx.draw_int("grid_h", 6, 16)
    else:
        h = ctx.draw_int("grid_h", h, h)
    if explicit_w:
        w = ctx.draw_int("board_w", 8, 20)
    else:
        w = ctx.draw_int("board_w", w, w)
    if (h // sh) * (w // sw) < n_inst:
        raise ValueError(
            f"incompatible exact overrides grid_h={h}, board_w={w}, "
            f"shape={sh}x{sw}, n_inst={n_inst}"
        )
    return h, w


def _place_positive_copies(board, shape, color, n_inst, rng, texture):
    h, w = len(board), len(board[0])
    sh, sw = _dims(shape)
    all_anchors = [
        (r, c)
        for r in range(h - sh + 1)
        for c in range(w - sw + 1)
    ]

    # Search arbitrary legal windows first.  The former implementation only
    # considered (row % sh, col % sw) == (0, 0), which taught a tile-lattice
    # shortcut that is absent from the canonical examples.  Ordinary scenes
    # have spare capacity, so require independently offset positives whenever
    # the geometry permits it.  Exact tight overrides retain the old lattice
    # fallback below rather than silently changing their contract.
    for _attempt in range(24):
        anchors = list(all_anchors)
        rng.shuffle(anchors)
        trial_board = deepcopy(board)
        selected = []
        residues = set()

        for r0, c0 in anchors:
            residue = (r0 % sh, c0 % sw)
            if not selected and residue == (0, 0):
                continue
            if len(selected) == 1 and n_inst >= 2 and residue in residues:
                continue
            if any(
                abs(r0 - rr) < sh and abs(c0 - cc) < sw
                for rr, cc in selected
            ):
                continue

            trial = deepcopy(trial_board)
            _stamp(trial, shape, r0, c0, color)
            hits = _match_positions(trial, shape, color)
            if len(hits) != len(selected) + 1 or (r0, c0) not in hits:
                continue

            trial_board = trial
            selected.append((r0, c0))
            residues.add(residue)
            if len(selected) == n_inst:
                if n_inst == 1 or len(residues) >= 2:
                    board[:] = trial_board
                    return selected, [a for a in all_anchors if a not in selected]
                break

    row_slots = list(range(0, h - sh + 1, sh))
    col_slots = list(range(0, w - sw + 1, sw))
    anchors = [(r, c) for r in row_slots for c in col_slots]
    if texture == "wide":
        anchors.sort(key=lambda p: (p[0], p[1]))
        groups = {}
        for anchor in anchors:
            groups.setdefault(anchor[0], []).append(anchor)
        anchors = []
        for key in sorted(groups):
            rng.shuffle(groups[key])
            anchors.extend(groups[key])
    elif texture == "tall":
        anchors.sort(key=lambda p: (p[1], p[0]))
        groups = {}
        for anchor in anchors:
            groups.setdefault(anchor[1], []).append(anchor)
        anchors = []
        for key in sorted(groups):
            rng.shuffle(groups[key])
            anchors.extend(groups[key])
    else:
        rng.shuffle(anchors)

    selected = []
    for r0, c0 in anchors:
        trial = deepcopy(board)
        _stamp(trial, shape, r0, c0, color)
        hits = _match_positions(trial, shape, color)
        if len(hits) == len(selected) + 1 and (r0, c0) in hits:
            board[:] = trial
            selected.append((r0, c0))
            if len(selected) == n_inst:
                return selected, [a for a in anchors if a not in selected]
    raise ValueError(
        f"could place only {len(selected)}/{n_inst} exact copies without extra matches"
    )


def _add_orientation_distractor(board, shape, color, anchors, rng):
    original = _normalize(shape)
    variants = [variant for variant in _transform_variants(shape) if variant != original]
    rng.shuffle(variants)
    base_hits = _match_positions(board, shape, color)
    all_anchors = list(anchors)
    rng.shuffle(all_anchors)
    # Also consider every legal anchor: a different-shaped decoy can fit where
    # the positive tile grid did not reserve a slot.
    for variant in variants:
        vh, vw = _dims(variant)
        candidates = [
            (r, c)
            for r in range(len(board) - vh + 1)
            for c in range(len(board[0]) - vw + 1)
        ]
        rng.shuffle(candidates)
        for r0, c0 in all_anchors + candidates:
            if r0 + vh > len(board) or c0 + vw > len(board[0]):
                continue
            if any(board[r0 + dr][c0 + dc] != 0 for dr, dc in variant):
                continue
            trial = deepcopy(board)
            _stamp(trial, variant, r0, c0, color)
            if _match_positions(trial, shape, color) == base_hits:
                board[:] = trial
                return True
    return False


def _add_wildcard_clutter(board, shape, color, hits, rng):
    sh, sw = _dims(shape)
    zeros = [
        (r, c)
        for r in range(sh)
        for c in range(sw)
        if (r, c) not in set(shape)
    ]
    if not zeros or not hits:
        return False
    base_hits = list(hits)
    candidates = [(hit, zero) for hit in hits for zero in zeros]
    rng.shuffle(candidates)
    clutter_color = next(value for value in (1, 2, 3, 4, 5, 6, 7) if value != color)
    for (r0, c0), (dr, dc) in candidates:
        rr, cc = r0 + dr, c0 + dc
        if board[rr][cc] != 0:
            continue
        trial = deepcopy(board)
        trial[rr][cc] = clutter_color
        if _match_positions(trial, shape, color) == base_hits:
            board[:] = trial
            return True
    return False


def _build(seed, sample_index, difficulty, overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")
    texture = _axis_texture(ctx, sample_index)
    # About one third of ordinary samples (even, non-varied schedule slots)
    # anchor the exact canonical scale in every difficulty band.  Requiring an
    # entirely override-free call keeps every declared exact axis authoritative.
    canonical_anchor = (
        sample_index % 2 == 0
        and sample_index % len(TEXTURES) != 0
        and not any(value is not None for value in overrides.values())
    )
    shape_size, n_inst = _choose_shape_and_count(
        ctx, layout_rng, texture, difficulty, canonical_anchor
    )
    shape = _SHAPES[(texture, shape_size)]
    sh, sw = _dims(shape)
    h, board_w = _choose_dimensions(
        ctx,
        layout_rng,
        sh,
        sw,
        n_inst,
        difficulty,
        sample_index,
        canonical_anchor=canonical_anchor,
    )

    color = layout_rng.choice((1, 2, 3, 4, 5, 6, 7))
    template_panel = full_grid(h, 3, 0)
    tr = layout_rng.randint(0, h - sh)
    tc = layout_rng.randint(0, 3 - sw)
    _stamp(template_panel, shape, tr, tc, color)

    board = full_grid(h, board_w, 0)
    positives, spare_anchors = _place_positive_copies(
        board, shape, color, n_inst, layout_rng, texture
    )
    _add_orientation_distractor(
        board, shape, color, spare_anchors, layout_rng
    )
    if texture == "varied":
        _add_wildcard_clutter(
            board,
            shape,
            color,
            _match_positions(board, shape, color),
            layout_rng,
        )

    # The builder verifies the exact requested count after all distractors.
    realized = _match_positions(board, shape, color)
    if len(realized) != n_inst:
        raise RuntimeError(
            f"internal exact-match invariant failed: requested {n_inst}, got {len(realized)}"
        )

    grid = [
        template_panel[r] + [9] + board[r]
        for r in range(h)
    ]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    return _build(seed, sample_index, difficulty, overrides)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural validator shared by canonical and generated inputs.

    It intentionally accepts canonical examples without requiring generated-only
    distractors.  It rejects malformed dividers, empty/multicolor/disconnected
    templates, absent positives, excessive matches, illegal colors, and grids
    outside the declared envelope.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if not 6 <= h <= 16:
        errors.append(f"grid_h {h} outside 6..16")
    if not 12 <= w <= 24:
        errors.append(f"total width {w} outside 12..24")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer color or color outside 0..9")
        return errors

    divider_cols = [
        c for c in range(w) if all(grid[r][c] == 9 for r in range(h))
    ]
    if divider_cols != [3]:
        errors.append(f"expected sole full-height divider at column 3; got {divider_cols}")
        return errors
    if any(grid[r][c] == 9 for r in range(h) for c in range(w) if c != 3):
        errors.append("color 9 appears outside the divider")

    left = [row[:3] for row in grid]
    board = [row[4:] for row in grid]
    crop, shape, color = _crop_template(left)
    if not shape:
        errors.append("template panel has no nonzero object")
        return errors
    if not 3 <= len(shape) <= 5:
        errors.append(f"template has {len(shape)} cells; expected 3..5")
    colors = {value for row in crop for value in row if value != 0}
    if len(colors) != 1 or color not in range(1, 8):
        errors.append(f"template must be monochrome color 1..7; got {sorted(colors)}")
    if not _connected(shape):
        errors.append("template object is not orthogonally connected")
    sh, sw = _dims(shape)
    if sh > 3 or sw > 3:
        errors.append(f"cropped template {sh}x{sw} exceeds 3x3")
    if not 8 <= len(board[0]) <= 20:
        errors.append(f"board_w {len(board[0])} outside 8..20")
    if any(value == 9 for row in board for value in row):
        errors.append("board contains separator color 9")

    hits = _match_positions(board, shape, color)
    if not 1 <= len(hits) <= 6:
        errors.append(f"board has {len(hits)} matches; expected 1..6")
    return errors


def mutation_fixtures():
    """Task-semantic impostors that ``self_check`` must reject."""
    valid = generate(0xCC10, 0, difficulty="medium")
    fixtures = []

    broken_divider = deepcopy(valid)
    broken_divider[len(broken_divider) // 2][3] = 0
    fixtures.append(("broken_full_height_divider", broken_divider))

    extra_divider = deepcopy(valid)
    for row in extra_divider:
        row[4] = 9
    fixtures.append(("second_full_height_divider", extra_divider))

    empty_template = deepcopy(valid)
    for r in range(len(empty_template)):
        for c in range(3):
            empty_template[r][c] = 0
    fixtures.append(("empty_template", empty_template))

    multicolor_template = deepcopy(valid)
    changed = False
    for r in range(len(multicolor_template)):
        for c in range(3):
            value = multicolor_template[r][c]
            if value not in (0, 9):
                multicolor_template[r][c] = 1 if value != 1 else 2
                changed = True
                break
        if changed:
            break
    fixtures.append(("multicolor_template", multicolor_template))

    no_matches = deepcopy(valid)
    for r in range(len(no_matches)):
        for c in range(4, len(no_matches[0])):
            no_matches[r][c] = 0
    fixtures.append(("board_without_matches", no_matches))
    return fixtures


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def _literal_zero_matching_rival(grid):
    """Wrong rule: require template-zero cells to match board zeroes exactly."""
    left, board, _ = _split_input(grid)
    crop, shape, _ = _crop_template(left)
    if not shape:
        raise ValueError("empty template")
    sh, sw = len(crop), len(crop[0])
    out = full_grid(len(board), len(board[0]), 0)
    for r0 in range(len(board) - sh + 1):
        for c0 in range(len(board[0]) - sw + 1):
            if all(
                board[r0 + r][c0 + c] == crop[r][c]
                for r in range(sh)
                for c in range(sw)
            ):
                _draw_outline(out, r0, c0, r0 + sh - 1, c0 + sw - 1)
    return out


def _dihedral_matching_rival(grid):
    """Wrong rule: accept every rotated/reflected template orientation."""
    left, board, _ = _split_input(grid)
    _, shape, color = _crop_template(left)
    if not shape:
        raise ValueError("empty template")
    out = full_grid(len(board), len(board[0]), 0)
    for variant in _transform_variants(shape):
        vh, vw = _dims(variant)
        for r0, c0 in _match_positions(board, variant, color):
            _draw_outline(out, r0, c0, r0 + vh - 1, c0 + vw - 1)
    return out


def _origin_lattice_scan_rival(grid):
    """Wrong rule: inspect only origin-anchored template-sized tile slots."""
    left, board, _ = _split_input(grid)
    _, shape, color = _crop_template(left)
    if not shape:
        raise ValueError("empty template")
    sh, sw = _dims(shape)
    out = full_grid(len(board), len(board[0]), 0)
    for r0 in range(0, len(board) - sh + 1, sh):
        for c0 in range(0, len(board[0]) - sw + 1, sw):
            if all(board[r0 + dr][c0 + dc] == color for dr, dc in shape):
                _draw_outline(out, r0, c0, r0 + sh - 1, c0 + sw - 1)
    return out


def _wildcard_clutter_witness(grid):
    return _literal_zero_matching_rival(grid) != rule_mirror(grid)


def _orientation_decoy_witness(grid):
    return _dihedral_matching_rival(grid) != rule_mirror(grid)


def _independent_offset_witness(grid):
    return _origin_lattice_scan_rival(grid) != rule_mirror(grid)


def strict_canonical_like(grid):
    """Accept the task's executable grammar and its supported shape family."""
    errors = list(self_check(grid))
    if errors:
        return errors
    left, _, _ = _split_input(grid)
    _, shape, _ = _crop_template(left)
    supported = {_normalize(cells) for cells in _SHAPES.values()}
    if _normalize(shape) not in supported:
        errors.append("template morphology is outside the supported task family")
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return TEXTURES[sample_index % len(TEXTURES)]


def lesson_identifiable(demos, query):
    """Require a four-demo window that falsifies every named shortcut."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the task grammar: {grammar[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the canonical rule mirror")
    if reasons:
        return sorted(set(reasons))

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"]
                for pair in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name} fits every demonstration")
    return sorted(set(reasons))


SEMANTIC_WITNESSES = {
    "wildcard_slot_clutter": _wildcard_clutter_witness,
    "same_color_orientation_decoy": _orientation_decoy_witness,
    "independent_match_offsets": _independent_offset_witness,
}
SEMANTIC_RIVALS = {
    "literal_zero_matching": _literal_zero_matching_rival,
    "dihedral_matching": _dihedral_matching_rival,
    "origin_lattice_scan": _origin_lattice_scan_rival,
}
WITNESS_RIVALS = {
    "wildcard_slot_clutter": ["literal_zero_matching"],
    "same_color_orientation_decoy": ["dihedral_matching"],
    "independent_match_offsets": ["origin_lattice_scan"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "literal_zero_matching": _literal_zero_matching_rival,
}
SCHEDULE_PROFILES = TEXTURES
MIN_STRICT_FRAC = 1.0
