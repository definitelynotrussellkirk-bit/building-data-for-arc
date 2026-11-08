"""Generator for 6b:hard_40 — shape-and-color relation matrix.

The input contains isolated, monochrome components.  Components are sorted by
row-major bounding-box position.  The output is the pairwise matrix where the
diagonal is each component's color; an off-diagonal cell is 8 for shapes equal
up to rotation, otherwise 6 for equal colors, otherwise 0.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71982ba2b59e"
TASK_ID = "71982ba2b59e"
RULE_HASH = "65d92f91150b"  # sha256 of whitespace-normalized canonical rule
# 3.0.0: replace dead legacy axes with exact observable controls; teach the
# canonical 8/6/0 branches on every normal draw; add precedence witnesses,
# structural self-checking, exhaustive placement, and a canonical rule pin.
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains 3-6 separated monochrome components.  "
    "Every normal draw has (1) two differently colored rotation-equivalent "
    "shapes, (2) two same-colored non-equivalent shapes, and (3) an unrelated "
    "pair.  Some draws also contain a same-color, same-shape pair to show that "
    "shape equality takes precedence and still emits 8.  Sort components by "
    "bounding-box (top, left); output the NxN relation matrix: diagonal = the "
    "component color, else 8 for rotation-equivalent shape, else 6 for equal "
    "color, else 0."
)

INVARIANTS = [
    "background is 0 and components are separated by an 8-neighborhood buffer",
    "3-6 monochrome components, using 2-4 colors and at least one repeated color",
    "every normal draw witnesses shape-only=8, color-only=6, and neither=0",
    "relation_profile='precedence' additionally witnesses same-shape+same-color -> 8",
]

# All controls are exact and recoverable from the returned grid.  Difficulty
# changes the default component-count mix, never the legal override envelope.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed across 9..18",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed across 11..22",
        "valid": "11..22",
    },
    "n_components": {
        "type": "int",
        "default": "easy 3..4; medium 4..5; hard 5..6",
        "valid": "3..6",
    },
    "n_colors": {
        "type": "int",
        "default": "rng feasible 2..4",
        "valid": "2..4",
    },
    "relation_profile": {
        "type": "str",
        "default": "rng feasible",
        "valid": "core|precedence",
    },
}

# Rotation-distinct, connected motifs; every realization fits a 3x3 box.
_MOTIFS = (
    ((0, 0), (1, 0), (1, 1)),                              # L triomino
    ((0, 0), (0, 1), (0, 2)),                              # I triomino
    ((0, 0), (0, 1), (1, 0), (1, 1)),                      # square
    ((0, 0), (0, 1), (0, 2), (1, 1)),                      # T tetromino
    ((0, 0), (0, 1), (1, 1), (1, 2)),                      # S tetromino
    ((0, 0), (1, 0), (2, 0), (2, 1)),                      # L tetromino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),              # P pentomino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),              # plus pentomino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),      # 2x3 rectangle
)


def _norm_shape(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(shape):
    max_r = max(r for r, _ in shape)
    return _norm_shape((c, max_r - r) for r, c in shape)


def _shape_rotations(shape):
    out = set()
    current = _norm_shape(shape)
    for _ in range(4):
        out.add(current)
        current = _rotate_cw(current)
    return out


def _shape_signature(shape):
    return min(_shape_rotations(shape))


# Fail at import rather than silently treating two nominal families as distinct.
assert len({_shape_signature(shape) for shape in _MOTIFS}) == len(_MOTIFS)


def _components_4(grid):
    """All nonzero 4-connected components, matching the canonical Racket rule."""
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    comps.sort(
        key=lambda cells: (
            min(r for r, _ in cells),
            min(c for _, c in cells),
        )
    )
    return comps


def _component_records(grid):
    records = []
    for cells in _components_4(grid):
        colors = {grid[r][c] for r, c in cells}
        records.append(
            {
                "cells": cells,
                "colors": colors,
                "color": next(iter(colors)) if len(colors) == 1 else None,
                "shape": _norm_shape(cells),
            }
        )
    return records


def _relation_counts(records):
    counts = Counter()
    for i, left in enumerate(records):
        for j, right in enumerate(records):
            if i == j:
                counts["diag"] += 1
                continue
            shape_match = right["shape"] in _shape_rotations(left["shape"])
            color_match = left["color"] == right["color"]
            if shape_match:
                counts[
                    "both_shape_priority" if color_match else "shape_only"
                ] += 1
            elif color_match:
                counts["color_only"] += 1
            else:
                counts["neither"] += 1
    return counts


def semantic_output(grid):
    """Independent Python mirror used only by focused tests and diagnostics."""
    records = _component_records(grid)
    output = []
    for i, left in enumerate(records):
        row = []
        for j, right in enumerate(records):
            if i == j:
                row.append(left["color"])
            elif right["shape"] in _shape_rotations(left["shape"]):
                row.append(8)
            elif left["color"] == right["color"]:
                row.append(6)
            else:
                row.append(0)
        output.append(row)
    return output


def observe_overrides(grid):
    records = _component_records(grid)
    counts = _relation_counts(records)
    return {
        "n_components": len(records),
        "n_colors": len({record["color"] for record in records}),
        "relation_profile": (
            "precedence" if counts["both_shape_priority"] else "core"
        ),
    }


def _band_component_options(difficulty):
    if difficulty == "easy":
        return (3, 4)
    if difficulty == "hard":
        return (5, 6)
    if difficulty in (None, "medium") or isinstance(difficulty, (int, float)):
        return (4, 5)
    raise ValueError(
        f"unknown difficulty {difficulty!r}; expected easy, medium, hard, "
        "None, or a numeric difficulty"
    )


def _choose_component_count(ctx, difficulty, overrides):
    requested_profile = overrides.get("relation_profile")
    requested_colors = overrides.get("n_colors")
    min_count = 3
    if requested_profile == "precedence":
        min_count = 4
    if requested_colors is not None:
        n_colors = int(requested_colors)
        if not 2 <= n_colors <= 4:
            raise ValueError(f"n_colors must be in 2..4, got {requested_colors!r}")
        # Core needs 3 witness slots plus one slot per color beyond the first two;
        # precedence needs one additional duplicate (shape,color) witness.
        min_count = max(
            min_count,
            n_colors + (2 if requested_profile == "precedence" else 1),
        )

    if overrides.get("n_components") is not None:
        count = ctx.draw_choice("n_components", tuple(range(3, 7)))
        if count < min_count:
            raise ValueError(
                f"n_components={count} cannot realize relation_profile="
                f"{requested_profile!r} with n_colors={requested_colors!r}; "
                f"need at least {min_count}"
            )
        return count

    preferred = [
        count
        for count in _band_component_options(difficulty)
        if count >= min_count
    ]
    feasible = preferred or [count for count in range(3, 7) if count >= min_count]
    if not feasible:
        raise ValueError(
            f"no component count in 3..6 can realize relation_profile="
            f"{requested_profile!r} with n_colors={requested_colors!r}"
        )
    return ctx.draw_choice("n_components", tuple(feasible))


def _choose_profile_and_colors(ctx, count, overrides):
    requested_colors = overrides.get("n_colors")
    profiles = []
    if requested_colors is None or int(requested_colors) <= count - 1:
        profiles.append("core")
    if count >= 4 and (
        requested_colors is None or int(requested_colors) <= count - 2
    ):
        profiles.append("precedence")
    profile = ctx.draw_choice("relation_profile", tuple(profiles))

    max_colors = min(4, count - (2 if profile == "precedence" else 1))
    colors = ctx.draw_choice("n_colors", tuple(range(2, max_colors + 1)))
    return profile, colors


def _blueprint(rng, count, n_colors, profile):
    """Return (motif index, color-index) pairs with all required relations."""
    motif_indices = list(range(len(_MOTIFS)))
    rng.shuffle(motif_indices)
    family_a, family_b = motif_indices[:2]

    # A0/A1: shape-only; A0/B0: color-only; A1/B0: neither.
    entries = [(family_a, 0), (family_a, 1), (family_b, 0)]
    if profile == "precedence":
        # Exact duplicate relation witnesses shape-over-color priority (8, not 6).
        entries.append((family_a, 0))

    used_pairs = set(entries)
    for color_index in range(2, n_colors):
        candidates = [
            (family, color_index)
            for family in motif_indices
            if (family, color_index) not in used_pairs
        ]
        choice = rng.choice(candidates)
        entries.append(choice)
        used_pairs.add(choice)

    while len(entries) < count:
        candidates = [
            (family, color_index)
            for family in motif_indices
            for color_index in range(n_colors)
            if (family, color_index) not in used_pairs
        ]
        if not candidates:
            raise RuntimeError("insufficient unique shape/color pairs for blueprint")
        choice = rng.choice(candidates)
        entries.append(choice)
        used_pairs.add(choice)

    rng.shuffle(entries)
    return entries


def _free(grid, r1, c1, r2, c2):
    h, w = len(grid), len(grid[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if grid[r][c] != 0:
                return False
    return True


def _place_at(grid, shape, color, top, left):
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _try_random_placement(h, w, realized, rng):
    grid = full_grid(h, w, 0)
    for shape, color in realized:
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        positions = [
            (top, left)
            for top in range(h - sh + 1)
            for left in range(w - sw + 1)
        ]
        rng.shuffle(positions)
        for top, left in positions:
            if _free(grid, top, left, top + sh - 1, left + sw - 1):
                _place_at(grid, shape, color, top, left)
                break
        else:
            return None
    return grid


def _slot_fallback(h, w, realized, rng):
    """Guaranteed placement for <=6 shapes of max 3x3 on the 9x11 minimum."""
    slots = [
        (top, left)
        for top in range(0, h - 2, 4)
        for left in range(0, w - 2, 4)
    ]
    if len(slots) < len(realized):
        raise RuntimeError(
            f"{h}x{w} exposes only {len(slots)} safe 3x3 slots for "
            f"{len(realized)} components"
        )
    rng.shuffle(slots)
    grid = full_grid(h, w, 0)
    for (shape, color), (top, left) in zip(realized, slots):
        _place_at(grid, shape, color, top, left)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    count = _choose_component_count(ctx, difficulty, overrides)
    profile, n_colors = _choose_profile_and_colors(ctx, count, overrides)
    h = ctx.draw_int_diff("grid_h", 9, 18)
    w = ctx.draw_int_diff("grid_w", 11, 22)

    color_rng = ctx.draw_rng("colors")
    palette = color_rng.sample(list(range(1, 10)), n_colors)
    blueprint_rng = ctx.draw_rng("blueprint")
    blueprint = _blueprint(blueprint_rng, count, n_colors, profile)
    orientation_rng = ctx.draw_rng("orientations")
    realized = []
    for family, color_index in blueprint:
        shape = _MOTIFS[family]
        for _ in range(orientation_rng.randint(0, 3)):
            shape = _rotate_cw(shape)
        realized.append((_norm_shape(shape), palette[color_index]))

    placement_rng = ctx.draw_rng("placement")
    # Several independent whole-layout attempts retain free placement variety.
    for _ in range(8):
        candidate = list(realized)
        placement_rng.shuffle(candidate)
        grid = _try_random_placement(h, w, candidate, placement_rng)
        if grid is not None:
            return grid
    return _slot_fallback(h, w, realized, placement_rng)


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed lessons and task-semantic branch omissions."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular with nonzero width"]

    errors = []
    h, w = len(grid), width
    if not (9 <= h <= 18 and 11 <= w <= 22):
        errors.append(f"dimensions {h}x{w} outside 9..18 x 11..22")
    flat = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in flat
    ):
        errors.append("all cells must be integer colors 0..9")
        return errors
    if 0 not in flat:
        errors.append("background color 0 is absent")

    records = _component_records(grid)
    if not 3 <= len(records) <= 6:
        errors.append(f"expected 3..6 components, found {len(records)}")
    for index, record in enumerate(records):
        if len(record["colors"]) != 1:
            errors.append(f"component {index} is not monochrome")
        cells = record["cells"]
        size = len(cells)
        bh = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if not 3 <= size <= 6:
            errors.append(f"component {index} size {size} outside 3..6")
        if bh > 3 or bw > 3:
            errors.append(f"component {index} bbox {bh}x{bw} exceeds 3x3")

    cell_owner = {}
    for index, record in enumerate(records):
        for cell in record["cells"]:
            cell_owner[cell] = index
    for (r, c), owner in cell_owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = cell_owner.get((r + dr, c + dc))
                if other is not None and other != owner:
                    errors.append("components are not separated by a 1-cell buffer")
                    return errors

    colors = {record["color"] for record in records}
    if not 2 <= len(colors) <= 4:
        errors.append(f"expected 2..4 component colors, found {len(colors)}")
    if len(colors) >= len(records):
        errors.append("no repeated component color, so the color-only branch is hidden")

    counts = _relation_counts(records)
    if counts["shape_only"] == 0:
        errors.append("missing differently-colored rotation-equivalent pair (8 branch)")
    if counts["color_only"] == 0:
        errors.append("missing same-colored non-equivalent pair (6 branch)")
    if counts["neither"] == 0:
        errors.append("missing unrelated pair (0 branch)")

    requested = None
    if isinstance(meta, dict):
        requested = meta.get("relation_profile")
        if requested is None and isinstance(meta.get("overrides"), dict):
            requested = meta["overrides"].get("relation_profile")
    if requested == "precedence" and counts["both_shape_priority"] == 0:
        errors.append("relation_profile='precedence' lacks a same-shape/same-color pair")
    if requested == "core" and counts["both_shape_priority"]:
        errors.append("relation_profile='core' unexpectedly contains a both-match pair")
    return errors
