"""High-signal generator for ARC task 053118990e92: Voronoi inside an 8 bbox.

The selected Racket rule treats every non-zero, non-8 cell strictly inside the
bounding box of the 8-cells as a seed.  It fills the bbox interior by Manhattan
nearest-seed color.  A nearest tie stays 0 only when the tied seeds have
*different* colors; same-color nearest ties still fill.

The four-sample curriculum schedule supplies explicit counterexamples to the
plausible shortcuts left open by the public task: requiring a complete 8 ring,
blanking every multi-seed tie, resolving different-color ties, or using
Euclidean distance.  Outputs remain owned by the selected Racket authority;
``rule_mirror`` is an independently testable audit mirror only.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "053118990e92"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "a2e9b991269f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "The bounding box of color 8 defines a region; the 8s may be a full ring "
    "or only its four corners. Every non-zero, non-8 interior cell is a seed. "
    "Fill each interior cell with the Manhattan-nearest seed color. If nearest "
    "seeds have different colors, leave 0; if they share one color, fill it."
)

INVARIANTS = [
    "a rectangular 9..14 by 11..16 ARC grid with background 0",
    "8-cells are exactly a full bbox ring or exactly the four bbox corners",
    "the bbox has at least a 5x6 interior and all outside-bbox cells are 0",
    "2..4 single-cell seeds lie strictly inside the bbox",
    "seed colors are all distinct or contain exactly one duplicated pair",
    "every four consecutive default samples cover all teaching profiles",
]

SCHEDULE_PROFILES = (
    "canonical_ring",
    "different_color_tie",
    "same_color_tie",
    "corners_manhattan",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10 on canonical anchors; otherwise difficulty-weighted",
        "valid": "9..14",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "12 on canonical anchors; otherwise difficulty-weighted",
        "valid": "11..16",
        "doc": "Exact returned grid width.",
    },
    "n_seeds": {
        "type": "int",
        "default": "2 on anchors/easy; up to 4 on harder draws",
        "valid": "2..4",
        "doc": "Exact number of interior Voronoi seeds.",
    },
    "frame_style": {
        "type": "str",
        "default": "ring except the scheduled corners counterexample",
        "valid": "ring|corners",
        "doc": "Exact 8-bbox representation: full perimeter or four corners.",
    },
    "seed_color_mode": {
        "type": "str",
        "default": "distinct except the scheduled same-color tie witness",
        "valid": "distinct|duplicate_pair",
        "doc": "All seed colors distinct, or exactly one color used twice.",
    },
}

# Every Cartesian combination advertised above is constructive in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_INT_BOUNDS = {
    "grid_h": (9, 14),
    "grid_w": (11, 16),
    "n_seeds": (2, 4),
}
_CHOICE_VALUES = {
    "frame_style": ("ring", "corners"),
    "seed_color_mode": ("distinct", "duplicate_pair"),
}
_CANONICAL_SHAPES = {(10, 12), (11, 13), (9, 11), (12, 14), (10, 15)}
_CANONICAL_SEED_COLORS = frozenset({2, 3, 4, 5, 6, 7})
_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _INT_BOUNDS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    for name, options in _CHOICE_VALUES.items():
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"{name} must be one of {', '.join(options)}")


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _INT_BOUNDS[name]
    if overrides.get(name) is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _draw_exact_choice(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: str,
) -> str:
    options = _CHOICE_VALUES[name]
    if overrides.get(name) is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def schedule_profile(
    seed: int, sample_index: int, difficulty: str | None = None
) -> str:
    """Return the semantic teaching profile scheduled at ``sample_index``."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _default_scalar(ctx, label: str, lo: int, hi: int) -> int:
    return ctx.draw_rng(label).randint(lo, hi)


def _default_parameters(
    ctx, profile: str, difficulty: str | None
) -> tuple[int, int, int, str, str]:
    if profile == "canonical_ring":
        return 10, 12, 2, "ring", "distinct"

    if difficulty == "easy":
        h = _default_scalar(ctx, "default_grid_h", 9, 10)
        w = _default_scalar(ctx, "default_grid_w", 11, 12)
        n_seeds = 2
    elif difficulty == "medium":
        h = _default_scalar(ctx, "default_grid_h", 10, 12)
        w = _default_scalar(ctx, "default_grid_w", 12, 14)
        n_seeds = _default_scalar(ctx, "default_n_seeds", 2, 3)
    elif difficulty == "hard":
        h = _default_scalar(ctx, "default_grid_h", 12, 14)
        w = _default_scalar(ctx, "default_grid_w", 14, 16)
        n_seeds = _default_scalar(ctx, "default_n_seeds", 3, 4)
    else:
        h = _default_scalar(ctx, "default_grid_h", 9, 14)
        w = _default_scalar(ctx, "default_grid_w", 11, 16)
        n_seeds = _default_scalar(ctx, "default_n_seeds", 2, 4)

    # Overlap semantic coverage across profiles so a five-pair lesson remains
    # identifiable when any one pair is rotated into the query position.
    if profile in ("same_color_tie", "corners_manhattan"):
        n_seeds = max(3, n_seeds)
    frame_style = (
        "corners"
        if profile in ("different_color_tie", "corners_manhattan")
        else "ring"
    )
    color_mode = (
        "duplicate_pair"
        if profile in ("same_color_tie", "corners_manhattan")
        else "distinct"
    )
    return h, w, n_seeds, frame_style, color_mode


def _frame_bbox(
    ctx, h: int, w: int, *, canonical_anchor: bool
) -> tuple[int, int, int, int]:
    # Recreate a public-profile bbox without replaying a public input.
    if canonical_anchor and (h, w) == (10, 12):
        return 1, 2, 8, 9

    vertical = [
        (top, bottom)
        for top in range(4)
        for bottom in range(4)
        if h - top - bottom - 2 >= 5
    ]
    horizontal = [
        (left, right)
        for left in range(4)
        for right in range(4)
        if w - left - right - 2 >= 6
    ]
    if not vertical or not horizontal:
        raise ValueError(f"grid {h}x{w} cannot fit the declared bbox interior")
    top, bottom = ctx.draw_rng("frame_vertical_padding").choice(vertical)
    left, right = ctx.draw_rng("frame_horizontal_padding").choice(horizontal)
    return top, left, h - 1 - bottom, w - 1 - right


def _ring_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _corner_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _interior_cells(
    bbox: tuple[int, int, int, int]
) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
    ]


def _far_extras(
    ctx,
    bbox: tuple[int, int, int, int],
    occupied: list[tuple[int, int]],
    witness: tuple[int, int],
    count: int,
    minimum_distance: int,
) -> list[tuple[int, int]]:
    candidates = [
        cell
        for cell in _interior_cells(bbox)
        if cell not in occupied
        and cell != witness
        and abs(cell[0] - witness[0]) + abs(cell[1] - witness[1])
        > minimum_distance
    ]
    rng = ctx.draw_rng("extra_seed_positions")
    rng.shuffle(candidates)
    candidates.sort(
        key=lambda cell: abs(cell[0] - witness[0]) + abs(cell[1] - witness[1]),
        reverse=True,
    )
    if len(candidates) < count:
        raise ValueError("bbox cannot place extra seeds beyond the teaching witness")
    return candidates[:count]


def _seed_positions(
    ctx,
    bbox: tuple[int, int, int, int],
    n_seeds: int,
    profile: str,
) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    if profile in ("canonical_ring", "different_color_tie"):
        # P=(r1+1,c1+4) is Manhattan distance 3 from both seeds, but squared
        # Euclidean distance 9 from A and 5 from B. Thus one zero cell jointly
        # witnesses different-color tie handling and L1 rather than L2 distance.
        pair = [(r1 + 1, c1 + 1), (r1 + 3, c1 + 5)]
        witness = (r1 + 1, c1 + 4)
        return pair + _far_extras(ctx, bbox, pair, witness, n_seeds - 2, 3)

    if profile in ("same_color_tie", "corners_manhattan"):
        if n_seeds == 2:
            # Exact n_seeds overrides remain constructive even when they remove
            # some profile-specific teaching coverage.
            witness = ((r1 + r2) // 2, (c1 + c2) // 2)
            return [(witness[0], witness[1] - 1),
                    (witness[0], witness[1] + 1)]

        # With the default duplicate-pair palette, the first and second seeds
        # share a color and the third is distinct. This compact arrangement
        # contains both tie kinds and also separates Manhattan from Euclidean
        # output. It therefore makes same-color coverage redundant across the
        # final two profiles without increasing EXAMPLES_NEEDED.
        core = [
            (r1 + 1, c1 + 1),
            (r1 + 2, c1 + 2),
            (r1 + 1, c1 + 3),
        ]
        witness = (r1 + 1, c1 + 2)
        return core + _far_extras(
            ctx, bbox, core, witness, n_seeds - 3, 2
        )

    cells = _interior_cells(bbox)
    return ctx.draw_rng("seed_positions").sample(cells, n_seeds)


def _seed_palette(
    ctx,
    n_seeds: int,
    color_mode: str,
    *,
    canonical_anchor: bool,
) -> list[int]:
    if canonical_anchor:
        # Stay inside the public 2..7 palette while avoiding a constant
        # sample-index-0 anchor across seeds.  Geometry remains a stable
        # semantic witness; ordered colors supply lawful seed diversity.
        palette = [2, 3, 4, 5, 6, 7]
        ctx.draw_rng("canonical_seed_palette").shuffle(palette)
        palette.extend((1, 9))
    else:
        palette = list(_SEED_COLORS)
        ctx.draw_rng("seed_palette").shuffle(palette)
    if color_mode == "distinct":
        return palette[:n_seeds]
    return [palette[0], palette[0], *palette[1 : n_seeds - 1]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n, default_frame, default_colors = (
        _default_parameters(ctx, profile, difficulty)
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", default_h)
    w = _draw_exact_int(ctx, overrides, "grid_w", default_w)
    n_seeds = _draw_exact_int(ctx, overrides, "n_seeds", default_n)
    frame_style = _draw_exact_choice(
        ctx, overrides, "frame_style", default_frame
    )
    color_mode = _draw_exact_choice(
        ctx, overrides, "seed_color_mode", default_colors
    )

    canonical_anchor = profile == "canonical_ring"
    bbox = _frame_bbox(ctx, h, w, canonical_anchor=canonical_anchor)
    grid = full_grid(h, w, 0)
    frame_cells = _ring_cells(bbox) if frame_style == "ring" else _corner_cells(bbox)
    for r, c in frame_cells:
        grid[r][c] = 8

    positions = _seed_positions(ctx, bbox, n_seeds, profile)
    colors = _seed_palette(
        ctx, n_seeds, color_mode, canonical_anchor=canonical_anchor
    )
    for (r, c), color in zip(positions, colors):
        if grid[r][c] != 0:
            raise RuntimeError("constructive seed placement collided with the frame")
        grid[r][c] = color
    return grid


def _normalise_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["every grid row must be a list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return None, ["grid must be rectangular with nonempty rows"]
    values = [list(row) for row in grid]
    bad = [
        value
        for row in values
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        return values, ["cells must be literal ARC color integers 0..9"]
    return values, []


def _analyse(grid: Any) -> dict[str, Any]:
    values, errors = _normalise_grid(grid)
    if values is None:
        return {"errors": errors}
    h, w = len(values), len(values[0])
    if errors:
        return {"errors": errors, "grid": values, "height": h, "width": w}
    if not 9 <= h <= 14:
        errors.append(f"grid height must be in 9..14, got {h}")
    if not 11 <= w <= 16:
        errors.append(f"grid width must be in 11..16, got {w}")

    eights = {
        (r, c)
        for r, row in enumerate(values)
        for c, value in enumerate(row)
        if value == 8
    }
    if not eights:
        errors.append("expected 8-cells defining a bbox")
        return {"errors": errors, "grid": values, "height": h, "width": w}
    r1 = min(r for r, _ in eights)
    c1 = min(c for _, c in eights)
    r2 = max(r for r, _ in eights)
    c2 = max(c for _, c in eights)
    bbox = (r1, c1, r2, c2)
    interior_h, interior_w = r2 - r1 - 1, c2 - c1 - 1
    if interior_h < 5 or interior_w < 6:
        errors.append(
            f"8 bbox interior must be at least 5x6, got {interior_h}x{interior_w}"
        )

    ring = _ring_cells(bbox)
    corners = _corner_cells(bbox)
    frame_style: str | None
    if eights == ring:
        frame_style = "ring"
    elif eights == corners:
        frame_style = "corners"
    else:
        frame_style = None
        errors.append("8-cells must be exactly a full bbox ring or its four corners")

    outside_nonzero = [
        (r, c)
        for r, row in enumerate(values)
        for c, value in enumerate(row)
        if value != 0
        and not (r1 <= r <= r2 and c1 <= c <= c2)
    ]
    if outside_nonzero:
        errors.append("all cells outside the 8 bbox must be 0")

    border_nonseed = [
        (r, c)
        for r, row in enumerate(values)
        for c, value in enumerate(row)
        if value not in (0, 8)
        and not (r1 < r < r2 and c1 < c < c2)
    ]
    if border_nonseed:
        errors.append("all non-zero non-8 cells must be strictly inside the bbox")

    seeds = [
        (r, c, values[r][c])
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if values[r][c] not in (0, 8)
    ]
    if not 2 <= len(seeds) <= 4:
        errors.append(f"expected 2..4 interior seeds, got {len(seeds)}")

    counts = Counter(color for _, _, color in seeds)
    if counts and all(count == 1 for count in counts.values()):
        color_mode = "distinct"
    elif sorted(counts.values()) == [1] * (len(counts) - 1) + [2]:
        color_mode = "duplicate_pair"
    else:
        color_mode = None
        errors.append(
            "seed colors must be all distinct or contain exactly one duplicated pair"
        )

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "bbox": bbox,
        "frame_style": frame_style,
        "seeds": seeds,
        "n_seeds": len(seeds),
        "seed_color_mode": color_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generator's declared lawful manifold without mutation."""
    del difficulty, meta
    return list(_analyse(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """Recognise the public task's ring/distinct/size/palette profile."""
    analysis = _analyse(grid)
    reasons = list(analysis.get("errors", []))
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) not in _CANONICAL_SHAPES:
        reasons.append("shape is not one of the canonical input shapes")
    if analysis["frame_style"] != "ring":
        reasons.append("canonical inputs use a complete 8 ring")
    if analysis["n_seeds"] not in (2, 3):
        reasons.append("canonical inputs use 2 or 3 seeds")
    if analysis["seed_color_mode"] != "distinct":
        reasons.append("canonical inputs use distinct seed colors")
    colors = {color for _, _, color in analysis["seeds"]}
    if not colors <= _CANONICAL_SEED_COLORS:
        reasons.append("canonical seed colors are drawn from 2..7")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact axis from returned pixels, not RNG bookkeeping."""
    analysis = _analyse(grid)
    if analysis.get("errors"):
        raise ValueError(
            "cannot observe malformed grid: " + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_seeds": analysis["n_seeds"],
        "frame_style": analysis["frame_style"],
        "seed_color_mode": analysis["seed_color_mode"],
    }


def _nearest(
    seeds: list[tuple[int, int, int]],
    r: int,
    c: int,
    *,
    metric: str,
) -> list[tuple[int, int, int]]:
    if metric == "manhattan":
        distances = [abs(sr - r) + abs(sc - c) for sr, sc, _ in seeds]
    elif metric == "euclidean":
        distances = [(sr - r) ** 2 + (sc - c) ** 2 for sr, sc, _ in seeds]
    else:  # defensive internal contract
        raise ValueError(f"unknown metric {metric!r}")
    minimum = min(distances)
    return [seed for seed, distance in zip(seeds, distances) if distance == minimum]


def _voronoi(
    grid,
    *,
    metric: str = "manhattan",
    tie_policy: str = "unique_color",
    require_ring: bool = False,
) -> list[list[int]]:
    analysis = _analyse(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    values = analysis["grid"]
    out = [row[:] for row in values]
    if require_ring and analysis["frame_style"] != "ring":
        return out
    r1, c1, r2, c2 = analysis["bbox"]
    seeds = analysis["seeds"]
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if values[r][c] == 8:
                continue
            nearest = _nearest(seeds, r, c, metric=metric)
            colors = {color for _, _, color in nearest}
            if tie_policy == "unique_color":
                value = next(iter(colors)) if len(colors) == 1 else 0
            elif tie_policy == "single_seed":
                value = nearest[0][2] if len(nearest) == 1 else 0
            elif tie_policy == "lowest_color":
                value = min(colors)
            else:  # defensive internal contract
                raise ValueError(f"unknown tie policy {tie_policy!r}")
            out[r][c] = value
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Audit mirror of the selected Manhattan/unique-nearest-color rule."""
    return _voronoi(grid)


def _rival_ties_always_blank(grid) -> list[list[int]]:
    """Wrong: any tie between two seed cells stays blank, even same-color."""
    return _voronoi(grid, tie_policy="single_seed")


def _rival_resolve_different_ties(grid) -> list[list[int]]:
    """Wrong: resolve a different-color nearest tie to its lowest color."""
    return _voronoi(grid, tie_policy="lowest_color")


def _rival_requires_full_ring(grid) -> list[list[int]]:
    """Wrong: treat an incomplete 8 perimeter as no actionable region."""
    return _voronoi(grid, require_ring=True)


def _rival_euclidean_distance(grid) -> list[list[int]]:
    """Wrong: use squared Euclidean rather than Manhattan distance."""
    return _voronoi(grid, metric="euclidean")


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ties_always_blank": _rival_ties_always_blank,
    "resolve_different_ties": _rival_resolve_different_ties,
    "requires_full_ring": _rival_requires_full_ring,
    "euclidean_distance": _rival_euclidean_distance,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ties_always_blank": _rival_ties_always_blank,
    "requires_full_ring": _rival_requires_full_ring,
}


def _tie_kinds(grid) -> tuple[bool, bool]:
    analysis = _analyse(grid)
    if analysis.get("errors"):
        return False, False
    r1, c1, r2, c2 = analysis["bbox"]
    same_color = False
    different_color = False
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            nearest = _nearest(analysis["seeds"], r, c, metric="manhattan")
            if len(nearest) < 2:
                continue
            colors = {color for _, _, color in nearest}
            same_color |= len(colors) == 1
            different_color |= len(colors) > 1
    return same_color, different_color


def _has_same_color_nearest_tie(grid) -> bool:
    return _tie_kinds(grid)[0]


def _has_different_color_nearest_tie(grid) -> bool:
    return _tie_kinds(grid)[1]


def _has_corners_only_frame(grid) -> bool:
    analysis = _analyse(grid)
    return not analysis.get("errors") and analysis["frame_style"] == "corners"


def _manhattan_differs_from_euclidean(grid) -> bool:
    analysis = _analyse(grid)
    return (
        not analysis.get("errors")
        and rule_mirror(grid) != _rival_euclidean_distance(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "same_color_nearest_tie": _has_same_color_nearest_tie,
    "different_color_nearest_tie": _has_different_color_nearest_tie,
    "corners_only_frame": _has_corners_only_frame,
    "manhattan_not_euclidean": _manhattan_differs_from_euclidean,
}
WITNESS_RIVALS = {
    "same_color_nearest_tie": ["ties_always_blank"],
    "different_color_nearest_tie": ["resolve_different_ties"],
    "corners_only_frame": ["requires_full_ring"],
    "manhattan_not_euclidean": ["euclidean_distance"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that a materialized lesson validates and refutes every rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    lawful_pairs: list[dict[str, Any]] = []
    witnessed = {name: False for name in SEMANTIC_WITNESSES}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyse(pair["input"])
        if analysis.get("errors"):
            reasons.append(f"demo {index} input is unlawful: {analysis['errors'][0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the Voronoi rule")
            continue
        lawful_pairs.append(pair)
        for name, witness in SEMANTIC_WITNESSES.items():
            witnessed[name] |= bool(witness(pair["input"]))

    missing = sorted(name for name, present in witnessed.items() if not present)
    if missing:
        reasons.append(f"demonstrations omit semantic witnesses: {missing}")

    for name, rival in LESSON_COMPETITORS.items():
        if lawful_pairs and all(
            rival(pair["input"]) == pair["output"] for pair in lawful_pairs
        ):
            reasons.append(f"rival rule {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output grids")
    else:
        analysis = _analyse(query["input"])
        if analysis.get("errors"):
            reasons.append(f"query input is unlawful: {analysis['errors'][0]}")
        elif query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the Voronoi rule")
    return reasons
