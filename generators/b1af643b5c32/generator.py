"""Semantic generator for ARC task ``b1af643b5c32`` (original ``abbfd121``).

The input is a large periodic field partially covered by two or three solid,
uniquely colored rectangles.  The output is the periodic field reconstructed
inside the bounding box of the largest rectangle.  Ordinary draws cycle
through the four canonical size/palette/period profiles, while colors, tile
surface form, D4 orientation, and rectangle positions vary deterministically.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b1af643b5c32"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a0d30c9b14a8"
MIN_STRICT_FRAC = 0.90
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 21..23 by 19..22 grid is a primitive 3x3 or 4x4 periodic pattern "
    "using three or four colors. Two or three other colors each form one "
    "solid rectangle and occlude the pattern. Exactly one rectangle has the "
    "largest area. Output the largest rectangle's bounding box with every "
    "occluded cell replaced by the periodic value for its global phase."
)

INVARIANTS = [
    "the visible field has primitive equal row/column period 3 or 4",
    "the periodic field uses exactly three or four colors",
    "two or three non-pattern colors each fill one solid rectangular bbox",
    "one occluder is strictly largest by bbox area",
    "the largest bbox is 6..10 rows by 7..12 columns",
    "every periodic residue class remains visible outside all occluders",
]

COUNTER_HYPOTHESES = [
    "crop the largest rectangle but leave its solid occluder color unchanged",
    "reconstruct the smallest rectangle instead of the largest",
    "always assume period 3, including the canonical period-4 branch",
    "replace the largest rectangle by one modal pattern color",
    "select a fixed position, fixed output size, or the most frequent color",
    "treat the rectangle color itself as the answer rather than an occlusion",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "21..23"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "19..22"},
    "period": {"type": "int", "default": "scheduled 3 or 4", "valid": "3..4"},
    "n_blocks": {"type": "int", "default": "scheduled 2 or 3", "valid": "2..3"},
    "largest_shape": {
        "type": "enum",
        "default": "scheduled canonical profile",
        "valid": ["7x7", "10x10", "6x12", "8x9"],
    },
    "pattern_palette_size": {"type": "int", "default": "scheduled 3 or 4", "valid": "3..4"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# Canonical train-then-test profiles.  Surface details vary, but these linked
# profiles keep ordinary training examples at the observed ARC scale.
_PROFILE_ROWS = (
    {
        "name": "canonical_4x4_square",
        "grid_h": 22,
        "grid_w": 20,
        "period": 4,
        "n_blocks": 2,
        "largest_shape": "7x7",
        "pattern_palette_size": 4,
        "secondary_shapes": ((5, 6),),
    },
    {
        "name": "canonical_3x3_large_square",
        "grid_h": 23,
        "grid_w": 19,
        "period": 3,
        "n_blocks": 2,
        "largest_shape": "10x10",
        "pattern_palette_size": 3,
        "secondary_shapes": ((5, 6),),
    },
    {
        "name": "canonical_3x3_wide",
        "grid_h": 21,
        "grid_w": 22,
        "period": 3,
        "n_blocks": 3,
        "largest_shape": "6x12",
        "pattern_palette_size": 3,
        "secondary_shapes": ((6, 6), (3, 3)),
    },
    {
        "name": "canonical_3x3_rect",
        "grid_h": 23,
        "grid_w": 22,
        "period": 3,
        "n_blocks": 3,
        "largest_shape": "8x9",
        "pattern_palette_size": 3,
        "secondary_shapes": ((7, 9), (6, 5)),
    },
)
# Duplicate the period-4 canonical profile often enough that every four-pair
# lesson window contains a period-4 demonstration before a period-4 query.
# All entries are still exact canonical profiles; this is curriculum ordering,
# not distributional broadening.
_SCHEDULE_PROFILE_INDEXES = (0, 1, 2, 0, 3, 1)
SCHEDULE_PROFILES = tuple(_PROFILE_ROWS[index]["name"] for index in _SCHEDULE_PROFILE_INDEXES)

# Exact primitive-period index tiles.  Values are palette indexes; a draw maps
# them to fresh ARC colors.  Multiple forms prevent one texture from becoming
# an accidental task cue.
_TILE_TEMPLATES = {
    (3, 3): (
        ((0, 0, 0), (0, 1, 2), (0, 2, 1)),
        ((0, 0, 0), (1, 2, 2), (2, 1, 1)),
        ((2, 0, 1), (0, 1, 2), (1, 2, 0)),
    ),
    (3, 4): (
        ((0, 1, 2), (3, 0, 1), (2, 3, 0)),
        ((0, 0, 1), (2, 3, 0), (1, 2, 3)),
    ),
    (4, 3): (
        ((0, 0, 0, 0), (0, 1, 2, 0), (0, 2, 0, 1), (0, 0, 1, 2)),
        ((0, 1, 2, 0), (1, 2, 0, 1), (2, 0, 1, 2), (0, 2, 1, 0)),
    ),
    (4, 4): (
        ((0, 0, 0, 0), (0, 1, 2, 3), (0, 2, 0, 2), (0, 3, 2, 1)),
        ((0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2)),
    ),
}

_CANONICAL_PROFILES = {
    (
        row["grid_h"],
        row["grid_w"],
        row["period"],
        row["n_blocks"],
        row["largest_shape"],
        row["pattern_palette_size"],
        tuple(sorted(row["secondary_shapes"])),
    )
    for row in _PROFILE_ROWS
}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    bounds = {
        "grid_h": (21, 23),
        "grid_w": (19, 22),
        "period": (3, 4),
        "n_blocks": (2, 3),

        "pattern_palette_size": (3, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "largest_shape":
            if value not in tuple(AXES[name]["valid"]):
                raise ValueError(
                    f"override {name!r}={value!r} is not one of {AXES[name]['valid']!r}"
                )
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, overrides: dict[str, Any], name: str, value: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_choice(name, (value,)))


def _scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    name: str,
    value: str,
    options: tuple[str, ...],
) -> str:
    available = options if name in overrides and overrides[name] is not None else (value,)
    return str(ctx.draw_choice(name, available))


def _rot90(tile: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(tile[len(tile) - 1 - r][c] for r in range(len(tile))) for c in range(len(tile[0])))


def _d4(tile: tuple[tuple[int, ...], ...], code: int) -> tuple[tuple[int, ...], ...]:
    out = tile
    for _ in range(code % 4):
        out = _rot90(out)
    if code >= 4:
        out = tuple(tuple(reversed(row)) for row in out)
    return out


def _period_of_tile(tile: tuple[tuple[int, ...], ...]) -> tuple[int, int]:
    h, w = len(tile), len(tile[0])
    row_period = next(
        p for p in range(1, h + 1)
        if all(tile[r][c] == tile[(r + p) % h][c] for r in range(h) for c in range(w))
    )
    col_period = next(
        p for p in range(1, w + 1)
        if all(tile[r][c] == tile[r][(c + p) % w] for r in range(h) for c in range(w))
    )
    return row_period, col_period


def _secondary_sizes(largest_h: int, largest_w: int, n_blocks: int, rng) -> list[tuple[int, int]]:
    target_area = largest_h * largest_w
    medium = [
        (h, w)
        for h in range(4, 7)
        for w in range(5, 8)
        if 20 <= h * w < min(target_area, 40)
    ]
    small = [
        (h, w)
        for h in range(3, 6)
        for w in range(3, 7)
        if 9 <= h * w < min(target_area, 31)
    ]
    rng.shuffle(medium)
    rng.shuffle(small)
    if not medium:
        medium = [(4, 5)]
    sizes = [medium[0]]
    if n_blocks == 3:
        for candidate in small:
            if candidate[0] * candidate[1] != sizes[0][0] * sizes[0][1]:
                sizes.append(candidate)
                break
        if len(sizes) < 2:
            sizes.append((3, 3))
    return sizes


def _separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int], gap: int) -> bool:
    ar, ac, ah, aw = a
    br, bc, bh, bw = b
    return (
        ar + ah + gap <= br
        or br + bh + gap <= ar
        or ac + aw + gap <= bc
        or bc + bw + gap <= ac
    )


def _phase_visible(h: int, w: int, period: int, rects: list[tuple[int, int, int, int]]) -> bool:
    for rr in range(period):
        for cc in range(period):
            if not any(
                all(not (r0 <= r < r0 + bh and c0 <= c < c0 + bw) for r0, c0, bh, bw in rects)
                for r in range(rr, h, period)
                for c in range(cc, w, period)
            ):
                return False
    return True


def _place_rectangles(
    h: int,
    w: int,
    sizes: list[tuple[int, int]],
    period: int,
    rng,
) -> list[tuple[int, int, int, int]]:
    """Place blocks broadly with a bounded search and constant-time fallback.

    Random trials cover interior, edge, and corner positions without the old
    exhaustive Cartesian recursion.  The fallback proves every declared
    override combination terminates quickly.
    """
    for _ in range(96):
        rects = [
            (rng.randrange(h - bh + 1), rng.randrange(w - bw + 1), bh, bw)
            for bh, bw in sizes
        ]
        if all(
            _separated(rects[i], rects[j], 1)
            for i in range(len(rects))
            for j in range(i + 1, len(rects))
        ) and _phase_visible(h, w, period, rects):
            return rects

    corners = {
        "tl": lambda bh, bw: (0, 0, bh, bw),
        "tr": lambda bh, bw: (0, w - bw, bh, bw),
        "br": lambda bh, bw: (h - bh, w - bw, bh, bw),
        "bl": lambda bh, bw: (h - bh, 0, bh, bw),
    }
    opposite = {"tl": "br", "tr": "bl", "br": "tl", "bl": "tr"}
    adjacent = {
        "tl": ("tr", "bl"), "tr": ("tl", "br"),
        "br": ("bl", "tr"), "bl": ("br", "tl"),
    }
    target_corner = rng.choice(tuple(corners))
    chosen = [target_corner, opposite[target_corner]]
    if len(sizes) == 3:
        chosen.append(adjacent[target_corner][rng.randrange(2)])
    rects = [corners[name](*size) for name, size in zip(chosen, sizes)]
    if not all(
        _separated(rects[i], rects[j], 1)
        for i in range(len(rects))
        for j in range(i + 1, len(rects))
    ):
        raise ValueError(f"corner construction failed for {sizes!r} in {h}x{w}")
    return rects


def _global_solid_rectangles(grid: list[list[int]]) -> list[dict[str, Any]]:
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            by_color.setdefault(int(value), []).append((r, c))
    blocks: list[dict[str, Any]] = []
    for color, cells in by_color.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if area == len(cells):
            blocks.append(
                {
                    "color": color,
                    "r0": r0,
                    "r1": r1,
                    "c0": c0,
                    "c1": c1,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "area": area,
                }
            )
    return sorted(blocks, key=lambda block: (block["area"], block["color"]))


def _inside_any_block(r: int, c: int, blocks: list[dict[str, Any]]) -> bool:
    return any(block["r0"] <= r <= block["r1"] and block["c0"] <= c <= block["c1"] for block in blocks)


def _infer_period(grid: list[list[int]], blocks: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Infer the primitive period over visible cells.

    This generator's declared codomain is period 3 or 4, but checking 1..4 is
    useful for rejecting collapsed impostors.  A precomputed mask avoids the
    millions of repeated bbox scans that made the exhaustive override gate
    unnecessarily slow.
    """
    h, w = len(grid), len(grid[0])
    blocked = [[False] * w for _ in range(h)]
    for block in blocks:
        for r in range(block["r0"], block["r1"] + 1):
            blocked[r][block["c0"]:block["c1"] + 1] = [True] * block["width"]
    for pr in range(1, min(4, h - 1) + 1):
        for pc in range(1, min(4, w - 1) + 1):
            valid = True
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if blocked[r][c]:
                        continue
                    if r + pr < h and not blocked[r + pr][c] and grid[r + pr][c] != value:
                        valid = False
                        break
                    if c + pc < w and not blocked[r][c + pc] and row[c + pc] != value:
                        valid = False
                        break
                if not valid:
                    break
            if valid:
                return pr, pc
    return None


def analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be integer ARC colors in 0..9"], "facts": None}

    normalized = [list(map(int, row)) for row in grid]
    h, w = len(normalized), width
    blocks = [block for block in _global_solid_rectangles(normalized) if block["area"] >= 9]
    if len(blocks) not in (2, 3):
        errors.append(f"expected exactly 2 or 3 solid occluder colors, found {len(blocks)}")
    if blocks:
        max_area = max(block["area"] for block in blocks)
        largest = [block for block in blocks if block["area"] == max_area]
        if len(largest) != 1:
            errors.append("largest occluder rectangle must be unique")
            target = None
        else:
            target = largest[0]
    else:
        target = None

    inferred = _infer_period(normalized, blocks) if len(blocks) in (2, 3) else None
    if inferred is None:
        errors.append("no visible two-dimensional period can be inferred")
        period_r = period_c = None
    else:
        period_r, period_c = inferred

    block_colors = {block["color"] for block in blocks}
    pattern_colors = sorted({value for row in normalized for value in row} - block_colors)
    facts = {
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "blocks": blocks,
        "block_colors": sorted(block_colors),
        "n_blocks": len(blocks),
        "target": target,
        "period_r": period_r,
        "period_c": period_c,
        "pattern_colors": pattern_colors,
        "pattern_palette_size": len(pattern_colors),
        "total_palette_size": len(pattern_colors) + len(block_colors),
    }
    return {"errors": errors, "facts": facts}


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid periodic-occlusion scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    target = facts["target"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "period": facts["period_r"],
        "n_blocks": facts["n_blocks"],
        "largest_shape": f"{target['height']}x{target['width']}",
        "pattern_palette_size": facts["pattern_palette_size"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    _validate_difficulty(difficulty)
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    if not 21 <= facts["grid_h"] <= 23 or not 19 <= facts["grid_w"] <= 22:
        errors.append(f"grid dimensions outside 21..23 by 19..22: {facts['grid_h']}x{facts['grid_w']}")
    if facts["period_r"] != facts["period_c"] or facts["period_r"] not in (3, 4):
        errors.append(f"primitive period must be square 3 or 4, found {facts['period_r']}x{facts['period_c']}")
    if facts["pattern_palette_size"] not in (3, 4):
        errors.append(f"pattern palette must contain 3 or 4 colors, found {facts['pattern_palette_size']}")
    if 0 in facts["block_colors"]:
        errors.append("occluder colors must be nonzero")
    target = facts["target"]
    if target is not None:
        if not 6 <= target["height"] <= 10 or not 7 <= target["width"] <= 12:
            errors.append(
                f"largest bbox must be 6..10 by 7..12, found {target['height']}x{target['width']}"
            )
        if any(block["area"] >= target["area"] for block in facts["blocks"] if block is not target):
            errors.append("a secondary block is not strictly smaller than the target")
    rects = [
        (block["r0"], block["c0"], block["height"], block["width"])
        for block in facts["blocks"]
    ]
    if facts["period_r"] in (3, 4) and not _phase_visible(
        facts["grid_h"], facts["grid_w"], facts["period_r"], rects
    ):
        errors.append("at least one periodic residue class is fully occluded")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis not in AXES or expected is None:
                continue
            normalized_expected = expected if axis == "largest_shape" else int(expected)
            if observed[axis] != normalized_expected:
                errors.append(
                    f"override {axis} requested {normalized_expected!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = analyze_scene(grid)
    facts = analysis["facts"]
    observed = observe_overrides(grid)
    profile = (
        observed["grid_h"],
        observed["grid_w"],
        observed["period"],
        observed["n_blocks"],
        observed["largest_shape"],
        observed["pattern_palette_size"],
        tuple(sorted(
            (block["height"], block["width"])
            for block in facts["blocks"]
            if block is not facts["target"]
        )),
    )
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"linked dimensions/palette/period profile is not one of the four canonical profiles: {profile}")
    return reasons


def _reconstruct_bbox(
    grid: list[list[int]],
    blocks: list[dict[str, Any]],
    target: dict[str, Any],
    period_r: int,
    period_c: int,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out: list[list[int]] = []
    for r in range(target["r0"], target["r1"] + 1):
        row: list[int] = []
        for c in range(target["c0"], target["c1"] + 1):
            phase_r, phase_c = r % period_r, c % period_c
            value = None
            for rr in range(phase_r, h, period_r):
                for cc in range(phase_c, w, period_c):
                    if not _inside_any_block(rr, cc, blocks):
                        value = grid[rr][cc]
                        break
                if value is not None:
                    break
            row.append(0 if value is None else value)
        out.append(row)
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return _reconstruct_bbox(
        facts["grid"], facts["blocks"], facts["target"], facts["period_r"], facts["period_c"]
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    profile = _PROFILE_ROWS[_SCHEDULE_PROFILE_INDEXES[int(sample_index) % len(_SCHEDULE_PROFILE_INDEXES)]]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", profile["grid_h"], 21, 23)
    w = _scheduled_int(ctx, overrides, "grid_w", profile["grid_w"], 19, 22)
    period = _scheduled_int(ctx, overrides, "period", profile["period"], 3, 4)
    n_blocks = _scheduled_int(ctx, overrides, "n_blocks", profile["n_blocks"], 2, 3)
    largest_shape = _scheduled_choice(
        ctx,
        overrides,
        "largest_shape",
        profile["largest_shape"],
        tuple(AXES["largest_shape"]["valid"]),
    )
    largest_h, largest_w = (int(part) for part in largest_shape.split("x", 1))
    palette_size = _scheduled_int(
        ctx,
        overrides,
        "pattern_palette_size",
        profile["pattern_palette_size"],
        3,
        4,
    )

    pattern_colors = tuple(ctx.draw_distinct_colors("pattern_colors", n=palette_size))
    # Difficulty is deliberately a surface-form curriculum axis, not a rule
    # change: rotating the palette prevents dead bands while preserving the
    # same canonical dimensions and reconstruction semantics in every band.
    band_code = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    pattern_colors = pattern_colors[band_code:] + pattern_colors[:band_code]
    block_colors = tuple(
        ctx.draw_distinct_colors(
            "block_colors", n=n_blocks, exclude=set(pattern_colors) | {0}
        )
    )
    tile_rng = ctx.draw_rng("tile_surface")
    templates = _TILE_TEMPLATES[(period, palette_size)]
    index_tile = templates[tile_rng.randrange(len(templates))]
    index_tile = _d4(index_tile, tile_rng.randrange(8))
    if _period_of_tile(index_tile) != (period, period):
        raise AssertionError("internal tile template lost its primitive period")
    tile = tuple(tuple(pattern_colors[index] for index in row) for row in index_tile)
    grid = [[tile[r % period][c % period] for c in range(w)] for r in range(h)]

    layout_rng = ctx.draw_rng("block_layout")
    if n_blocks == profile["n_blocks"] and largest_shape == profile["largest_shape"]:
        secondary = list(profile["secondary_shapes"])
    else:
        secondary = _secondary_sizes(largest_h, largest_w, n_blocks, layout_rng)
    sizes = [(largest_h, largest_w), *secondary]
    rects = _place_rectangles(h, w, sizes, period, layout_rng)
    for color, (r0, c0, bh, bw) in zip(block_colors, rects):
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("constructed invalid periodic-occlusion scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "period": period,
        "n_blocks": n_blocks,
        "largest_shape": largest_shape,
        "pattern_palette_size": palette_size,
    }
    if observed != expected:
        raise AssertionError(f"axis observability mismatch: expected {expected!r}, observed {observed!r}")
    return grid


def _rival_crop_occluder(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    target = facts["target"]
    return [row[target["c0"]:target["c1"] + 1] for row in facts["grid"][target["r0"]:target["r1"] + 1]]


def _rival_smallest_block(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    target = min(facts["blocks"], key=lambda block: (block["area"], block["color"]))
    return _reconstruct_bbox(
        facts["grid"], facts["blocks"], target, facts["period_r"], facts["period_c"]
    )



def _rival_second_largest_block(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    target = sorted(facts["blocks"], key=lambda block: (block["area"], block["color"]))[-2]
    return _reconstruct_bbox(
        facts["grid"], facts["blocks"], target, facts["period_r"], facts["period_c"]
    )


def _rival_topmost_block(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    target = min(facts["blocks"], key=lambda block: (block["r0"], block["c0"]))
    return _reconstruct_bbox(
        facts["grid"], facts["blocks"], target, facts["period_r"], facts["period_c"]
    )

def _rival_fixed_period_3(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    return _reconstruct_bbox(facts["grid"], facts["blocks"], facts["target"], 3, 3)


def _rival_modal_fill(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    facts = analysis["facts"]
    visible = [
        value
        for r, row in enumerate(facts["grid"])
        for c, value in enumerate(row)
        if not _inside_any_block(r, c, facts["blocks"])
    ]
    modal = Counter(visible).most_common(1)[0][0]
    target = facts["target"]
    return [[modal for _ in range(target["width"])] for _ in range(target["height"])]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "crop_occluder": _rival_crop_occluder,
    "smallest_block": _rival_smallest_block,
    "second_largest_block": _rival_second_largest_block,
    "topmost_block": _rival_topmost_block,
    "fixed_period_3": _rival_fixed_period_3,
    "modal_fill": _rival_modal_fill,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _facts_if_valid(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"] or self_check(grid):
        return None
    return analysis["facts"]


SEMANTIC_WITNESSES = {
    "period_3": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["period_r"] == 3,
    "period_4": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["period_r"] == 4,
    "two_blocks": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["n_blocks"] == 2,
    "three_blocks": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["n_blocks"] == 3,
    "square_target": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["target"]["height"] == facts["target"]["width"],
    "rectangular_target": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["target"]["height"] != facts["target"]["width"],
    "largest_selector": lambda grid: (facts := _facts_if_valid(grid)) is not None and len({block["area"] for block in facts["blocks"]}) == facts["n_blocks"],
    "near_tie_largest": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["target"]["area"] - sorted(block["area"] for block in facts["blocks"])[-2] <= 10,
    "target_not_topmost": lambda grid: (facts := _facts_if_valid(grid)) is not None and facts["target"] is not min(facts["blocks"], key=lambda block: (block["r0"], block["c0"])),
    "phase_reconstruction": lambda grid: _facts_if_valid(grid) is not None,
}

WITNESS_RIVALS = {
    "period_3": ["crop_occluder", "smallest_block", "modal_fill"],
    "period_4": ["fixed_period_3", "crop_occluder"],
    "two_blocks": ["smallest_block", "crop_occluder"],
    "three_blocks": ["smallest_block", "crop_occluder"],
    "square_target": ["crop_occluder", "modal_fill"],
    "rectangular_target": ["crop_occluder", "modal_fill"],
    "largest_selector": ["smallest_block", "second_largest_block"],
    "near_tie_largest": ["second_largest_block", "crop_occluder"],
    "target_not_topmost": ["topmost_block"],
    "phase_reconstruction": ["crop_occluder", "modal_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input invalid: {'; '.join(errors)}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with largest-block periodic reconstruction")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"named competitor {name} fits every demo but changes the query")
    return reasons
