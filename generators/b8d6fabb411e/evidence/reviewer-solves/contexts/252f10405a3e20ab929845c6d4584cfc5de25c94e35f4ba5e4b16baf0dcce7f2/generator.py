"""Generator for b8d6fabb411e — connect aligned markers to a color-3 square.

The authority copies the input, finds the solid color-3 square, then extends
only those non-{0,3} singleton markers whose row or column intersects the
square's span.  The marker color fills every gap cell up to the nearest square
edge.  Markers in diagonal quadrants are decoys and remain isolated.

The generated curriculum is a four-scene cycle.  Every four consecutive
examples contain: all four directions, a horizontal+vertical pair, a single
ray, and a same-color decoy control.  Larger-square scenes put at least one
marker on an *interior* square row AND column in the two-ray scene, refuting
axis-specific as well as canonical-only shortcuts that connect markers
aligned with boundary rows/columns only.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "b8d6fabb411e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
# sha256[:12] of the whitespace-normalized, comment-preserving selected rule.
RULE_HASH = "e88f12aefcff"

SUMMARY = (
    "Find the one solid color-3 square. For every nonzero/non-3 singleton "
    "marker lying left/right on a square row, or above/below on a square "
    "column, paint the zero-cell gap to the nearest square edge in that "
    "marker's color. Preserve the square, the markers, and all diagonal "
    "decoy markers."
)

INVARIANTS = [
    "background is color 0, dimensions are 1..30, and all cells are ARC colors 0..9",
    "exactly one solid color-3 square, 2..4 cells per side",
    "all other colored cells are isolated singleton markers outside the square",
    "at least one marker is axis-aligned with the square and has a visible gap",
    "collinear same-side rays never recolor an existing marker; same-color overlap is safe",
    "generated scenes contain diagonal decoys, but self_check does not mistake that curriculum obligation for the authority grammar",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PIXEL_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each layout is directly recoverable from (height, width, square side).
_LAYOUTS: dict[str, tuple[int, int, int]] = {
    "canonical_10": (10, 10, 2),
    "compact_8x9": (8, 9, 3),
    "medium_12x13": (12, 13, 3),
    "large_16x18": (16, 18, 4),
}

# Counts are intentionally unique, so the scene profile is observable without
# relying on hidden metadata.  The first two fields are aligned/decoy counts.
_PROFILE_COUNTS: dict[str, tuple[int, int]] = {
    "canonical_four": (4, 6),
    "canonical_two": (2, 5),
    "canonical_one": (1, 3),
    "color_control_three": (3, 4),
}
_PROFILE_ORDER = tuple(_PROFILE_COUNTS)
SCHEDULE_PROFILES = _PROFILE_ORDER

AXES = {
    "layout": {
        "type": "enum",
        "default": "scheduled by scene_profile and difficulty",
        "valid": ["canonical_10", "compact_8x9", "medium_12x13", "large_16x18"],
        "doc": "Exact (height, width, square-side) layout; every value works in every difficulty band.",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-step sample_index schedule",
        "valid": ["canonical_four", "canonical_two", "canonical_one", "color_control_three"],
        "doc": "Exact aligned/decoy branch profile, recoverable from the returned grid.",
    },
}

# Every layout/profile Cartesian combination is supported.  Declaring the
# empty contract makes any future multi-axis rejection a loud defect.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()


def _validate_matrix(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        return ["ARC grid dimensions must be at most 30x30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        r, c, value = bad[0]
        return [f"cell ({r},{c})={value!r} is not an ARC color 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    """Return structural roles plus errors; never mutate ``grid``."""
    errors = _validate_matrix(grid)
    if errors:
        return {"errors": errors}

    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    threes = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 3]
    if not threes:
        return {"errors": ["no color-3 square"]}

    r1 = min(r for r, _c in threes)
    r2 = max(r for r, _c in threes)
    c1 = min(c for _r, c in threes)
    c2 = max(c for _r, c in threes)
    side_r, side_c = r2 - r1 + 1, c2 - c1 + 1
    expected_square = {
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    }
    if side_r != side_c or not 2 <= side_r <= 4:
        errors.append(
            f"color-3 bbox {(r1, c1, r2, c2)} is not a 2..4 square"
        )
    if set(threes) != expected_square:
        errors.append(
            f"color-3 region is not solid: bbox has {len(expected_square)} cells, found {len(threes)}"
        )

    markers = sorted(
        (r, c, g[r][c])
        for r in range(h)
        for c in range(w)
        if g[r][c] not in (0, 3)
    )
    aligned: list[tuple[int, int, int, str]] = []
    decoys: list[tuple[int, int, int]] = []
    adjacent_pairs: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    adjacent_square: list[tuple[int, int, int]] = []

    marker_positions = {(r, c) for r, c, _color in markers}
    for r, c, color in markers:
        if r1 <= r <= r2 and c1 <= c <= c2:
            errors.append(f"marker {color} at ({r},{c}) lies inside the square bbox")
            continue

        if r1 <= r <= r2 and c < c1:
            direction = "left"
            if c1 - c <= 1:
                adjacent_square.append((r, c, color))
            aligned.append((r, c, color, direction))
        elif r1 <= r <= r2 and c > c2:
            direction = "right"
            if c - c2 <= 1:
                adjacent_square.append((r, c, color))
            aligned.append((r, c, color, direction))
        elif c1 <= c <= c2 and r < r1:
            direction = "top"
            if r1 - r <= 1:
                adjacent_square.append((r, c, color))
            aligned.append((r, c, color, direction))
        elif c1 <= c <= c2 and r > r2:
            direction = "bottom"
            if r - r2 <= 1:
                adjacent_square.append((r, c, color))
            aligned.append((r, c, color, direction))
        else:
            decoys.append((r, c, color))

        for dr, dc in _DIRS4:
            neighbour = (r + dr, c + dc)
            if neighbour in marker_positions:
                adjacent_pairs.add(tuple(sorted(((r, c), neighbour))))

    if adjacent_pairs:
        errors.append(
            "non-square colored cells are not isolated singletons: "
            f"adjacent pairs={sorted(adjacent_pairs)[:3]}"
        )
    if adjacent_square:
        errors.append(
            "aligned marker touches the square and produces no visible gap: "
            f"{adjacent_square[:3]}"
        )
    if not aligned:
        errors.append("no axis-aligned marker with a visible line transformation")

    # The reference writes through any intervening pixel.  A different-color
    # marker on the same half-ray would therefore be recolored, contradicting
    # this lesson's marker-preservation contract.  Same-color collinearity is
    # safe and remains accepted; this is not a curriculum count restriction.
    lane_colors: dict[tuple[str, int], set[int]] = {}
    for r, c, color, direction in aligned:
        lane = r if direction in {"left", "right"} else c
        lane_colors.setdefault((direction, lane), set()).add(color)
    conflicts = [key for key, colors in lane_colors.items() if len(colors) > 1]
    if conflicts:
        errors.append(
            "conflicting same-side rays recolor existing markers: "
            f"{sorted(conflicts)[:3]}"
        )

    directions = [direction for _r, _c, _color, direction in aligned]
    interior_span = [
        (r, c, color, direction)
        for r, c, color, direction in aligned
        if (
            direction in {"left", "right"} and r not in {r1, r2}
        ) or (
            direction in {"top", "bottom"} and c not in {c1, c2}
        )
    ]
    palette = sorted({value for row in g for value in row})
    return {
        "errors": errors,
        "grid": g,
        "h": h,
        "w": w,
        "square": (r1, c1, r2, c2),
        "square_side": side_r,
        "markers": markers,
        "aligned": aligned,
        "decoys": decoys,
        "directions": directions,
        "interior_span": interior_span,
        "palette": palette,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the authority-valid input grammar and requested exact axes."""
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be one of None, 'easy', 'medium', or 'hard'"]
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors or not isinstance(meta, dict):
        return errors

    requested = meta.get("overrides")
    if not isinstance(requested, dict):
        requested = meta
    # Observe only requested axes.  A lawful canonical/rule input need not
    # belong to our exact scene profiles, but a requested profile must be
    # demonstrably satisfied rather than silently accepted after ValueError.
    observers = {"layout": _layout_name, "scene_profile": _profile_name}
    for key, observer in observers.items():
        if requested.get(key) is None:
            continue
        try:
            observed = observer(analysis)
        except ValueError as exc:
            errors.append(f"override {key} cannot be observed: {exc}")
            continue
        if observed != requested[key]:
            errors.append(
                f"override {key} requested {requested[key]!r}, observed {observed!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public manifold, not merely coarse marginals."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["h"], analysis["w"]) != (10, 10):
        reasons.append(f"canonical dimensions are 10x10, found {analysis['h']}x{analysis['w']}")
    if analysis["square_side"] != 2:
        reasons.append(f"canonical square side is 2, found {analysis['square_side']}")
    if len(analysis["palette"]) not in {3, 4}:
        reasons.append(
            f"canonical palette has 3 or 4 colors, found {len(analysis['palette'])}"
        )
    if not 1 <= len(analysis["aligned"]) <= 4:
        reasons.append(
            f"canonical aligned-marker support is 1..4, found {len(analysis['aligned'])}"
        )
    if not 3 <= len(analysis["decoys"]) <= 6:
        reasons.append(
            f"canonical decoy support is 3..6, found {len(analysis['decoys'])}"
        )
    return reasons


def _profile_name(analysis: dict[str, Any]) -> str:
    counts = (len(analysis["aligned"]), len(analysis["decoys"]))
    matches = [name for name, expected in _PROFILE_COUNTS.items() if expected == counts]
    if len(matches) != 1:
        raise ValueError(f"aligned/decoy counts {counts} do not identify a generated scene profile")
    return matches[0]


def _layout_name(analysis: dict[str, Any]) -> str:
    shape = (analysis["h"], analysis["w"], analysis["square_side"])
    matches = [name for name, expected in _LAYOUTS.items() if expected == shape]
    if len(matches) != 1:
        raise ValueError(f"shape/square tuple {shape} does not identify a generated layout")
    return matches[0]


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact generated axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        "layout": _layout_name(analysis),
        "scene_profile": _profile_name(analysis),
    }


def _expected_output(
    grid: Any, *, boundary_only: bool = False, horizontal_only: bool = False,
    horizontal_boundary_only: bool = False, vertical_boundary_only: bool = False,
) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot apply line rule to invalid scene: " + "; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    r1, c1, r2, c2 = analysis["square"]

    # Row-major marker order matches the selected Racket source.  Generated
    # rays cannot conflict, but preserving the order keeps this mirror useful
    # on canonical and adversarial probes as well.
    for r, c, color in analysis["markers"]:
        if r1 <= r <= r2 and c > c2:
            if (boundary_only or horizontal_boundary_only) and r not in {r1, r2}:
                continue
            for cc in range(c2 + 1, c):
                out[r][cc] = color
        elif r1 <= r <= r2 and c < c1:
            if (boundary_only or horizontal_boundary_only) and r not in {r1, r2}:
                continue
            for cc in range(c + 1, c1):
                out[r][cc] = color
        elif not horizontal_only and c1 <= c <= c2 and r > r2:
            if (boundary_only or vertical_boundary_only) and c not in {c1, c2}:
                continue
            for rr in range(r2 + 1, r):
                out[rr][c] = color
        elif not horizontal_only and c1 <= c <= c2 and r < r1:
            if (boundary_only or vertical_boundary_only) and c not in {c1, c2}:
                continue
            for rr in range(r + 1, r1):
                out[rr][c] = color
    return out


def _boundary_rows_cols_only(grid: Any) -> Grid:
    """Plausible shortcut: connect only exact square-boundary rows/columns."""
    return _expected_output(grid, boundary_only=True)


def _horizontal_boundary_only(grid: Any) -> Grid:
    """Wrong rule: full vertical spans but only boundary horizontal rows."""
    return _expected_output(grid, horizontal_boundary_only=True)


def _vertical_boundary_only(grid: Any) -> Grid:
    """Wrong rule that fit every default 3.0.0 scene: clip vertical spans."""
    return _expected_output(grid, vertical_boundary_only=True)


def _horizontal_only(grid: Any) -> Grid:
    """Plausible shortcut: connect left/right markers and ignore vertical rays."""
    return _expected_output(grid, horizontal_only=True)


def _connect_decoys_horizontally(grid: Any) -> Grid:
    """Wrong rule: true aligned rays plus a horizontal projection for decoys."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot apply rival to invalid scene: " + "; ".join(analysis["errors"]))
    out = _expected_output(grid)
    _r1, c1, _r2, c2 = analysis["square"]
    for r, c, color in analysis["decoys"]:
        if c < c1:
            for cc in range(c + 1, c1 + 1):
                out[r][cc] = color
        elif c > c2:
            for cc in range(c2, c):
                out[r][cc] = color
    return out


def semantic_observables(grid) -> dict[str, Any]:
    """Task-linked branch and shortcut observables for count-backed review."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    aligned_colors = {color for _r, _c, color, _direction in analysis["aligned"]}
    decoy_colors = {color for _r, _c, color in analysis["decoys"]}
    output = _expected_output(grid)
    changed = sum(
        1
        for r in range(analysis["h"])
        for c in range(analysis["w"])
        if output[r][c] != analysis["grid"][r][c]
    )
    return {
        **observe_overrides(grid),
        "square_bbox": list(analysis["square"]),
        "square_side": analysis["square_side"],
        "aligned_count": len(analysis["aligned"]),
        "decoy_count": len(analysis["decoys"]),
        "directions": sorted(set(analysis["directions"])),
        "direction_counts": {
            direction: analysis["directions"].count(direction)
            for direction in ("left", "right", "top", "bottom")
        },
        "interior_span_alignment_count": len(analysis["interior_span"]),
        "horizontal_interior_alignment_count": sum(
            direction in {"left", "right"} for *_rest, direction in analysis["interior_span"]
        ),
        "vertical_interior_alignment_count": sum(
            direction in {"top", "bottom"} for *_rest, direction in analysis["interior_span"]
        ),
        "aligned_decoy_color_overlap": sorted(aligned_colors & decoy_colors),
        "changed_background_cells": changed,
        "canonical_like": not strict_canonical_like(grid),
    }


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _PROFILE_ORDER[int(sample_index) % len(_PROFILE_ORDER)]


def _scheduled_layout(profile: str, band: str) -> str:
    if profile in {"canonical_four", "canonical_one"}:
        return "canonical_10"
    return {
        "easy": "compact_8x9",
        "medium": "medium_12x13",
        "hard": "large_16x18",
    }[band]


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _square_position(rng, h: int, w: int, side: int) -> tuple[int, int]:
    row_hi = h - side - 2
    col_hi = w - side - 2
    if row_hi < 2 or col_hi < 2:
        raise ValueError(f"layout {h}x{w} cannot hold side-{side} square with two-cell margins")
    return rng.randint(2, row_hi), rng.randint(2, col_hi)


def _side_sequence(profile: str, rng) -> list[str]:
    sides = ["left", "right", "top", "bottom"]
    if profile == "canonical_four":
        selected = sides
    elif profile == "canonical_two":
        selected = [rng.choice(sides[:2]), rng.choice(sides[2:])]
    elif profile == "canonical_one":
        selected = [rng.choice(sides)]
    elif profile == "color_control_three":
        missing = rng.randrange(len(sides))
        selected = [side for index, side in enumerate(sides) if index != missing]
    else:
        raise ValueError(f"unknown scene profile {profile!r}")
    # Color lists are attached in this order: randomizing it removes the old
    # invariant that left/top share one color and right/bottom the other.
    rng.shuffle(selected)
    return selected


def _aligned_position(
    rng,
    side_name: str,
    *,
    sr: int,
    sc: int,
    square_side: int,
    h: int,
    w: int,
    use_interior_span: bool,
    ordinal: int,
) -> tuple[int, int]:
    del ordinal  # Kept in the private call signature for archived reproducers.
    if use_interior_span and square_side >= 3:
        span_offset = rng.randint(1, square_side - 2)
    else:
        span_offset = rng.randrange(square_side)

    if side_name == "left":
        return sr + span_offset, rng.randint(0, sc - 2)
    if side_name == "right":
        return sr + span_offset, rng.randint(sc + square_side + 1, w - 1)
    if side_name == "top":
        return rng.randint(0, sr - 2), sc + span_offset
    if side_name == "bottom":
        return rng.randint(sr + square_side + 1, h - 1), sc + span_offset
    raise ValueError(f"unknown side {side_name!r}")


def _marker_colors(profile: str, rng) -> tuple[list[int], list[int]]:
    first, second = rng.sample(_PIXEL_COLORS, 2)
    n_aligned, n_decoy = _PROFILE_COUNTS[profile]
    if profile == "canonical_one":
        return [first], [first] * n_decoy
    if profile == "canonical_two":
        return [first, second], [first, second, first, second, first]
    if profile == "canonical_four":
        return [first, second, first, second], [first, second] * 3
    if profile == "color_control_three":
        # The first decoy deliberately repeats an aligned color.  Its unchanged
        # output is the color-locality control, not a palette accident.
        return [first, second, first], [first, second, second, first]
    raise ValueError(f"unknown scene profile {profile!r} with counts {(n_aligned, n_decoy)}")


def _choose_decoys(
    rng,
    *,
    h: int,
    w: int,
    square: tuple[int, int, int, int],
    occupied: set[tuple[int, int]],
    count: int,
) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = square
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (r1 <= r <= r2)
        and not (c1 <= c <= c2)
        and (r, c) not in occupied
    ]
    rng.shuffle(candidates)
    chosen: list[tuple[int, int]] = []
    reserved = set(occupied)
    for r, c in candidates:
        if any((r + dr, c + dc) in reserved for dr, dc in _DIRS4):
            continue
        chosen.append((r, c))
        reserved.add((r, c))
        if len(chosen) == count:
            return chosen
    raise ValueError(
        f"could place only {len(chosen)}/{count} isolated decoys on {h}x{w} around square {square}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_profile = schedule_profile(seed, sample_index, difficulty=band)
    scene_profile = _draw_scheduled_choice(
        ctx, "scene_profile", _PROFILE_ORDER, scheduled_profile
    )
    scheduled_layout = _scheduled_layout(scene_profile, band)
    layout = _draw_scheduled_choice(ctx, "layout", tuple(_LAYOUTS), scheduled_layout)
    h, w, square_side = _LAYOUTS[layout]

    rng = ctx.draw_rng("scene")
    sr, sc = _square_position(rng, h, w, square_side)
    r1, c1 = sr, sc
    r2, c2 = sr + square_side - 1, sc + square_side - 1
    grid = full_grid(h, w, 0)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            grid[r][c] = 3

    sides = _side_sequence(scene_profile, rng)
    aligned_colors, decoy_colors = _marker_colors(scene_profile, rng)
    occupied = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    interior_axes: set[str] = set()
    for ordinal, (side_name, color) in enumerate(zip(sides, aligned_colors)):
        axis = "horizontal" if side_name in {"left", "right"} else "vertical"
        force_interior = square_side >= 3 and axis not in interior_axes
        r, c = _aligned_position(
            rng,
            side_name,
            sr=sr,
            sc=sc,
            square_side=square_side,
            h=h,
            w=w,
            use_interior_span=force_interior,
            ordinal=ordinal,
        )
        if (r, c) in occupied:
            raise AssertionError(f"aligned placement collision at {(r, c)}")
        grid[r][c] = color
        occupied.add((r, c))
        if force_interior:
            interior_axes.add(axis)

    decoy_positions = _choose_decoys(
        rng,
        h=h,
        w=w,
        square=(r1, c1, r2, c2),
        occupied=occupied,
        count=len(decoy_colors),
    )
    for (r, c), color in zip(decoy_positions, decoy_colors):
        grid[r][c] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"layout": layout, "scene_profile": scene_profile}
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_impostors(grid: Any) -> list[tuple[str, Grid]]:
    """Targeted malformed scenes that a structural self_check must reject."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("need a valid source scene: " + "; ".join(analysis["errors"]))
    source = analysis["grid"]
    r1, c1, r2, c2 = analysis["square"]
    rows: list[tuple[str, Grid]] = []

    missing_square = [row[:] for row in source]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            missing_square[r][c] = 0
    rows.append(("missing_square", missing_square))

    hollow_square = [row[:] for row in source]
    hollow_square[r1][c1] = 0
    rows.append(("hollow_square", hollow_square))

    marker_cluster = [row[:] for row in source]
    for r, c, color in analysis["markers"]:
        candidate = next(
            (
                (r + dr, c + dc)
                for dr, dc in _DIRS4
                if 0 <= r + dr < analysis["h"]
                and 0 <= c + dc < analysis["w"]
                and marker_cluster[r + dr][c + dc] == 0
            ),
            None,
        )
        if candidate is not None:
            rr, cc = candidate
            marker_cluster[rr][cc] = color
            rows.append(("two_cell_marker_cluster", marker_cluster))
            break

    touching_square = [row[:] for row in source]
    ar, ac, color, direction = analysis["aligned"][0]
    touching_square[ar][ac] = 0
    destination = {
        "left": (ar, c1 - 1),
        "right": (ar, c2 + 1),
        "top": (r1 - 1, ac),
        "bottom": (r2 + 1, ac),
    }[direction]
    touching_square[destination[0]][destination[1]] = color
    rows.append(("marker_touches_square", touching_square))

    no_aligned = [row[:] for row in source]
    for r, c, _color, _direction in analysis["aligned"]:
        no_aligned[r][c] = 0
    rows.append(("no_firing_marker", no_aligned))

    marker_inside = [row[:] for row in source]
    marker_inside[r2][c2] = analysis["markers"][0][2]
    rows.append(("marker_inside_square_bbox", marker_inside))
    return rows


def _valid_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness_horizontal(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(d in {"left", "right"} for d in analysis["directions"]))


def _witness_vertical(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(d in {"top", "bottom"} for d in analysis["directions"]))


def _witness_all_four(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and set(analysis["directions"]) == {"left", "right", "top", "bottom"})


def _witness_one_ray(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["aligned"]) == 1)


def _witness_decoys(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["decoys"] and _connect_decoys_horizontally(grid) != _expected_output(grid))


def _witness_interior_span(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["interior_span"] and _boundary_rows_cols_only(grid) != _expected_output(grid))


def _witness_horizontal_interior(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(
        direction in {"left", "right"} for *_rest, direction in analysis["interior_span"]
    ) and _horizontal_boundary_only(grid) != _expected_output(grid))


def _witness_vertical_interior(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(
        direction in {"top", "bottom"} for *_rest, direction in analysis["interior_span"]
    ) and _vertical_boundary_only(grid) != _expected_output(grid))


def _witness_same_color_decoy(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    aligned_colors = {color for _r, _c, color, _direction in analysis["aligned"]}
    return any(color in aligned_colors for _r, _c, color in analysis["decoys"])


def _witness_canonical_anchor(grid: Any) -> bool:
    return not strict_canonical_like(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "horizontal_branch": _witness_horizontal,
    "vertical_branch": _witness_vertical,
    "all_four_sides": _witness_all_four,
    "one_ray_fires": _witness_one_ray,
    "decoys_preserved": _witness_decoys,
    "interior_span_alignment": _witness_interior_span,
    "horizontal_interior_alignment": _witness_horizontal_interior,
    "vertical_interior_alignment": _witness_vertical_interior,
    "same_color_decoy_ignored": _witness_same_color_decoy,
    "canonical_anchor": _witness_canonical_anchor,
}

BRANCH_WITNESSES = {
    "horizontal_branch",
    "vertical_branch",
    "all_four_sides",
    "one_ray_fires",
    "same_color_decoy_ignored",
    "canonical_anchor",
}

SEMANTIC_RIVALS = {
    "boundary_rows_cols_only": _boundary_rows_cols_only,
    "horizontal_boundary_only": _horizontal_boundary_only,
    "vertical_boundary_only": _vertical_boundary_only,
    "horizontal_only": _horizontal_only,
    "connect_decoys_horizontally": _connect_decoys_horizontally,
}

WITNESS_RIVALS = {
    "interior_span_alignment": ["boundary_rows_cols_only"],
    "horizontal_interior_alignment": ["horizontal_boundary_only"],
    "vertical_interior_alignment": ["vertical_boundary_only"],
    "vertical_branch": ["horizontal_only"],
    "decoys_preserved": ["connect_decoys_horizontally"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every supplied square has side 2, so every row/column in its span is also
    # a boundary.  The public pairs therefore cannot distinguish this shortcut.
    "boundary_rows_cols_only": _boundary_rows_cols_only,
    "horizontal_boundary_only": _horizontal_boundary_only,
    "vertical_boundary_only": _vertical_boundary_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to reject the named plausible rivals."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    profiles: list[str] = []
    valid_demo_inputs: list[Any] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} is not a pair dict")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = _expected_output(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        try:
            profiles.append(observe_overrides(grid)["scene_profile"])
        except ValueError as exc:
            reasons.append(f"demo {index} lacks observable profile: {exc}")
            continue
        valid_demo_inputs.append(grid)

    if len(demos) == EXAMPLES_NEEDED and set(profiles) != set(SCHEDULE_PROFILES):
        reasons.append(
            f"four-demo window misses scheduled profiles: observed {sorted(set(profiles))}"
        )

    if valid_demo_inputs:
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(grid) == _expected_output(grid) for grid in valid_demo_inputs):
                reasons.append(f"named rival {name!r} survives every demonstration")

    if not isinstance(query, dict):
        reasons.append("query is not a pair dict")
    else:
        query_grid = query.get("input")
        query_output = query.get("output")
        errors = self_check(query_grid)
        if errors:
            reasons.append(f"query input invalid: {errors[0]}")
        elif query_output != _expected_output(query_grid):
            reasons.append("query output disagrees with the selected rule")

    return sorted(set(reasons))
