"""Lawful curriculum for four-fold reflection across a non-background cross.

The background is color 7.  The first row and column containing no 7 form the
reflection axes.  Every non-7 cell off those axes is read from the original
input in row-major order and paints its horizontal, vertical, and diagonal
reflection when that target is in bounds.  Later sources therefore overwrite
earlier sources/reflections.  Nonseparator cells embedded in an axis are not
sources, and each out-of-bounds reflection is skipped independently.

Version 3 alternates exact canonical shape/palette anchors with a mixed teaching
sample.  A mixed sample contains one same-orbit source collision, an off-color
axis cell, and partial clipping, so a single demonstration refutes the three
shortcuts that fit every canonical pair plus an all-or-nothing clipping rival.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "09d287bbfa0b"
VERSION = "3.0.0"
RULE_HASH = "36baa035a1e3"

SUMMARY = (
    "Color 7 is background; the first full non-7 row/column are reflection "
    "axes. Off-axis colored cells paint all in-bounds members of their fourfold "
    "orbit in original row-major order, so later sources overwrite earlier "
    "ones. Scheduled canonical-core inputs reproduce all four canonical "
    "shape/palette profiles. Alternating mixed inputs jointly expose "
    "multi-quadrant overwrite order, axis-cell exclusion, and independent "
    "clipping; every three-demo lesson and every one-query rotation retains a "
    "mixed witness."
)

INVARIANTS = [
    "integer colors 0..9 on a rectangular 7..18 by 7..18 grid",
    "background is 7; exactly one full non-7 row and one full non-7 column",
    "the axis intersection is separator color 1..6",
    "at least two off-axis nonseparator source cells produce a nonidentity output",
    "mixed inputs contain a same-orbit collision, an off-color axis cell, and partial clipping",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical_core", "teaching_mix")
TEXTURES = ("plain", "multi_quadrant", "clip", "axis_dot", "mixed")
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/full-domain 7..18", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "scheduled/full-domain 7..18", "valid": "7..18"},
    "sep_color": {"type": "color", "default": "scheduled/full-domain 1..6", "valid": "1..6"},
    "n_pixels": {"type": "int", "default": "scheduled/full-domain 2..8", "valid": "2..8"},
    "texture": {
        "type": "str",
        "default": "alternating plain canonical_core and mixed teaching witness",
        "valid": "plain|multi_quadrant|clip|axis_dot|mixed",
        "doc": (
            "plain: one safe quadrant; multi_quadrant: a same-orbit collision "
            "across quadrants; clip: at least one source has some but not all "
            "reflections in bounds; axis_dot: an off-color axis cell is not a "
            "source; mixed: all three teaching signals together"
        ),
    },
}
# Every advertised exact-axis combination is constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_INT_DOMAINS = {
    "grid_h": tuple(range(7, 19)),
    "grid_w": tuple(range(7, 19)),
    "sep_color": tuple(range(1, 7)),
    "n_pixels": tuple(range(2, 9)),
}
_CANONICAL_PROFILES = (
    # height, width, total input palette, source count, separator color
    (8, 8, 7, 7, 3),
    (10, 15, 7, 7, 1),
    (11, 11, 7, 7, 6),
    (11, 17, 9, 8, 4),
)
_SOURCE_COLORS = (0, 1, 2, 3, 4, 5, 6, 8, 9)
Grid = list[list[int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternation makes every three demos—and every 3-of-4 rotation—witnessed."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 2]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value} outside {domain[0]}..{domain[-1]}")
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError(f"texture must be a string, not {type(value).__name__}")
        if value not in TEXTURES:
            raise ValueError(f"texture={value!r} not in {TEXTURES}")


def _scheduled_axis(ctx, name: str, domain: tuple[Any, ...], scheduled: Any) -> Any:
    """Expose the full override domain while recording the deterministic schedule."""
    value = ctx.draw_choice(name, domain)
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return value
    # GenCtx currently has no public scheduled-value setter. This is the same
    # provenance path used by typed draws and is intentionally isolated here.
    return ctx._record(name, scheduled, from_override=False)


def _scheduled_defaults(ctx, profile: str) -> tuple[dict[str, Any], int | None]:
    if profile == "canonical_core":
        height, width, palette_size, pixels, separator = _CANONICAL_PROFILES[
            (ctx.sample_index // 2) % len(_CANONICAL_PROFILES)
        ]
        return {
            "grid_h": height,
            "grid_w": width,
            "sep_color": separator,
            "n_pixels": pixels,
            "texture": "plain",
        }, palette_size

    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else "medium"
    rng = ctx.draw_rng("teaching_defaults")
    height_ranges = {"easy": (7, 11), "medium": (9, 15), "hard": (12, 18)}
    pixel_ranges = {"easy": (4, 5), "medium": (5, 7), "hard": (7, 8)}
    hlo, hhi = height_ranges[band]
    nlo, nhi = pixel_ranges[band]
    return {
        "grid_h": rng.randint(hlo, hhi),
        "grid_w": rng.randint(hlo, hhi),
        "sep_color": rng.randint(1, 6),
        "n_pixels": rng.randint(nlo, nhi),
        "texture": "mixed",
    }, None


def _axes(height: int, width: int, texture: str) -> tuple[int, int]:
    if texture in ("clip", "mixed"):
        return 2, 2
    return height // 2, width // 2


def _orbit_points(
    cross_row: int, cross_col: int, dr: int, dc: int, height: int, width: int
) -> list[tuple[int, int]]:
    points = {
        (cross_row + sr * dr, cross_col + sc * dc)
        for sr in (-1, 1)
        for sc in (-1, 1)
    }
    return sorted((r, c) for r, c in points if 0 <= r < height and 0 <= c < width)


def _safe_orbits(height: int, width: int, cross_row: int, cross_col: int) -> list[tuple[int, int]]:
    max_dr = min(cross_row, height - 1 - cross_row)
    max_dc = min(cross_col, width - 1 - cross_col)
    return [(dr, dc) for dr in range(1, max_dr + 1) for dc in range(1, max_dc + 1)]


def _plain_sources(ctx, height: int, width: int, cross_row: int, cross_col: int, count: int):
    rng = ctx.draw_rng("plain_geometry")
    sign_row, sign_col = rng.choice(((-1, -1), (-1, 1), (1, -1), (1, 1)))
    orbits = _safe_orbits(height, width, cross_row, cross_col)
    chosen = rng.sample(orbits, count)
    return [(cross_row + sign_row * dr, cross_col + sign_col * dc) for dr, dc in chosen]


def _multi_sources(ctx, height: int, width: int, cross_row: int, cross_col: int, count: int):
    rng = ctx.draw_rng("multi_geometry")
    orbits = _safe_orbits(height, width, cross_row, cross_col)
    forced = rng.choice(orbits)
    dr, dc = forced
    points = [(cross_row - dr, cross_col - dc), (cross_row + dr, cross_col + dc)]
    remaining = rng.sample([key for key in orbits if key != forced], count - 2)
    for orbit in remaining:
        points.append(rng.choice(_orbit_points(cross_row, cross_col, *orbit, height, width)))
    return points


def _clip_sources(ctx, height: int, width: int, cross_row: int, cross_col: int, count: int):
    rng = ctx.draw_rng("clip_geometry")
    # (dr=1, dc=3) has exactly one in-bounds reflected target for axis (2,2)
    # on every declared grid size, so clipping is partial rather than identity.
    forced = (cross_row + 1, cross_col + 3)
    candidates = [
        (r, c)
        for r in range(cross_row + 1, height)
        for c in range(cross_col + 1, width)
        if (r, c) != forced
    ]
    return [forced, *rng.sample(candidates, count - 1)]


def _mixed_sources(ctx, height: int, width: int, cross_row: int, cross_col: int, count: int):
    rng = ctx.draw_rng("mixed_geometry")
    # Same orbit, different rows/quadrants, and dc=3 clips the left half.
    forced = [(cross_row - 1, cross_col + 3), (cross_row + 1, cross_col + 3)]
    forced_orbit = (1, 3)
    orbit_candidates: dict[int, list[tuple[tuple[int, int], list[tuple[int, int]]]]] = {
        4: [],
        3: [],
        2: [],
        1: [],
    }
    for dr in range(1, max(cross_row, height - 1 - cross_row) + 1):
        for dc in range(1, max(cross_col, width - 1 - cross_col) + 1):
            if (dr, dc) == forced_orbit:
                continue
            points = _orbit_points(cross_row, cross_col, dr, dc, height, width)
            if points:
                orbit_candidates[len(points)].append(((dr, dc), points))
    # Fully visible orbits each guarantee three changed targets. Prefer them to
    # clipped orbits so the teaching sample demonstrates the transformation at
    # useful visual scale rather than merely satisfying a nonidentity check.
    selected = []
    for visible_points in (4, 3, 2, 1):
        tier = orbit_candidates[visible_points]
        rng.shuffle(tier)
        selected.extend(tier)
    selected = selected[: count - 2]
    if len(selected) != count - 2:
        raise RuntimeError("not enough distinct mixed-source orbits")
    return [*forced, *(rng.choice(points) for _key, points in selected)]


def _source_positions(ctx, height: int, width: int, cross_row: int, cross_col: int,
                      count: int, texture: str) -> list[tuple[int, int]]:
    if texture in ("plain", "axis_dot"):
        return _plain_sources(ctx, height, width, cross_row, cross_col, count)
    if texture == "multi_quadrant":
        return _multi_sources(ctx, height, width, cross_row, cross_col, count)
    if texture == "clip":
        return _clip_sources(ctx, height, width, cross_row, cross_col, count)
    return _mixed_sources(ctx, height, width, cross_row, cross_col, count)


def _source_palette(ctx, separator: int, count: int, palette_target: int | None) -> list[int]:
    legal = [color for color in _SOURCE_COLORS if color != separator]
    if palette_target is not None and palette_target - 2 <= count:
        distinct = palette_target - 2
    else:
        upper = min(count, len(legal))
        distinct = ctx.draw_rng("source_palette_size").randint(2, upper)
    colors = ctx.draw_rng("source_palette").sample(legal, distinct)
    return [colors[index % distinct] for index in range(count)]


def _render(ctx, height: int, width: int, separator: int, count: int,
            texture: str, palette_target: int | None) -> Grid:
    cross_row, cross_col = _axes(height, width, texture)
    grid = full_grid(height, width, 7)
    for col in range(width):
        grid[cross_row][col] = separator
    for row in range(height):
        grid[row][cross_col] = separator

    positions = _source_positions(ctx, height, width, cross_row, cross_col, count, texture)
    if len(positions) != count or len(set(positions)) != count:
        raise RuntimeError("constructive source placement shortened or duplicated the requested set")
    colors = _source_palette(ctx, separator, count, palette_target)
    # The forced collision points are already row-major; different first colors
    # guarantee that overwrite-order rivals disagree.
    if texture in ("multi_quadrant", "mixed") and colors[0] == colors[1]:
        raise RuntimeError("collision witness requires two distinct source colors")
    for (row, col), color in zip(positions, colors):
        if row == cross_row or col == cross_col or grid[row][col] != 7:
            raise RuntimeError("constructive source placement collided with the cross")
        grid[row][col] = color

    if texture in ("axis_dot", "mixed"):
        # Its mirror on the same axis remains separator-colored in the intended rule.
        grid[cross_row][cross_col + 1] = colors[0]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults, palette_target = _scheduled_defaults(ctx, profile)
    height = _scheduled_axis(ctx, "grid_h", _INT_DOMAINS["grid_h"], defaults["grid_h"])
    width = _scheduled_axis(ctx, "grid_w", _INT_DOMAINS["grid_w"], defaults["grid_w"])
    separator = _scheduled_axis(
        ctx, "sep_color", _INT_DOMAINS["sep_color"], defaults["sep_color"]
    )
    count = _scheduled_axis(ctx, "n_pixels", _INT_DOMAINS["n_pixels"], defaults["n_pixels"])
    texture = _scheduled_axis(ctx, "texture", TEXTURES, defaults["texture"])
    if any(name in overrides and overrides[name] is not None
           for name in ("grid_h", "grid_w", "n_pixels", "texture")):
        # Exact user controls take priority over profile cosmetics. Preserve a
        # target palette only when it remains mathematically realizable.
        if palette_target is not None and palette_target - 2 > count:
            palette_target = None
    grid = _render(ctx, height, width, separator, count, texture, palette_target)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator violated self_check: {errors}")
    return grid


def _find_axes(grid: Grid) -> tuple[int | None, int | None]:
    height, width = len(grid), len(grid[0])
    cross_row = next((r for r in range(height) if all(v != 7 for v in grid[r])), None)
    cross_col = next(
        (c for c in range(width) if all(grid[r][c] != 7 for r in range(height))),
        None,
    )
    return cross_row, cross_col


def _apply(
    grid: Grid,
    *,
    include_axis_sources: bool = False,
    first_quadrant_only: bool = False,
    preserve_original_sources: bool = False,
    all_or_nothing_clipping: bool = False,
) -> Grid:
    height, width = len(grid), len(grid[0])
    cross_row, cross_col = _find_axes(grid)
    out = [list(row) for row in grid]
    if cross_row is None or cross_col is None:
        return out
    selected_quadrant = None
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 7:
                continue
            on_axis = row == cross_row or col == cross_col
            if on_axis and not include_axis_sources:
                continue
            if not on_axis:
                quadrant = (row < cross_row, col < cross_col)
                if selected_quadrant is None:
                    selected_quadrant = quadrant
                if first_quadrant_only and quadrant != selected_quadrant:
                    continue
            reflected = (
                (row, 2 * cross_col - col),
                (2 * cross_row - row, col),
                (2 * cross_row - row, 2 * cross_col - col),
            )
            valid = [
                (target_row, target_col)
                for target_row, target_col in reflected
                if 0 <= target_row < height
                and 0 <= target_col < width
                and (include_axis_sources or (target_row != cross_row and target_col != cross_col))
            ]
            if all_or_nothing_clipping and len(valid) != 3:
                continue
            for target_row, target_col in valid:
                if preserve_original_sources and grid[target_row][target_col] != 7:
                    continue
                out[target_row][target_col] = value
    return out


def _mirror(grid: Grid) -> Grid:
    return _apply(grid)


def _analyse(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid must have nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not (7 <= height <= 18 and 7 <= width <= 18):
        errors.append(f"grid size {height}x{width} outside 7..18 by 7..18")
    full_rows = [row for row in range(height) if all(value != 7 for value in grid[row])]
    full_cols = [
        col for col in range(width) if all(grid[row][col] != 7 for row in range(height))
    ]
    if len(full_rows) != 1 or len(full_cols) != 1:
        errors.append(
            f"expected exactly one full non-7 row/column, got rows={full_rows} cols={full_cols}"
        )
        return None, errors
    cross_row, cross_col = full_rows[0], full_cols[0]
    if not (1 <= cross_row < height - 1 and 1 <= cross_col < width - 1):
        errors.append("reflection axes must be interior")
    separator = grid[cross_row][cross_col]
    if separator not in range(1, 7):
        errors.append(f"separator color {separator} must be in 1..6")

    sources: list[tuple[int, int, int]] = []
    axis_dots: list[tuple[int, int, int]] = []
    quadrants: set[tuple[bool, bool]] = set()
    orbit_counts: dict[tuple[int, int], int] = {}
    partial_clip = False
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 7:
                continue
            if row == cross_row or col == cross_col:
                if value != separator:
                    axis_dots.append((row, col, value))
                continue
            if value == separator:
                errors.append(f"off-axis source at {(row, col)} reuses separator color")
            sources.append((row, col, value))
            quadrants.add((row < cross_row, col < cross_col))
            orbit = (abs(row - cross_row), abs(col - cross_col))
            orbit_counts[orbit] = orbit_counts.get(orbit, 0) + 1
            reflected = (
                (row, 2 * cross_col - col),
                (2 * cross_row - row, col),
                (2 * cross_row - row, 2 * cross_col - col),
            )
            valid = sum(
                0 <= rr < height
                and 0 <= cc < width
                and rr != cross_row
                and cc != cross_col
                for rr, cc in reflected
            )
            partial_clip |= 0 < valid < 3
    if len(sources) < 2:
        errors.append("need at least two off-axis source cells")
    if _mirror([list(row) for row in grid]) == [list(row) for row in grid]:
        errors.append("input is identity under the selected reflection rule")
    return {
        "height": height,
        "width": width,
        "cross_row": cross_row,
        "cross_col": cross_col,
        "separator": separator,
        "sources": sources,
        "axis_dots": axis_dots,
        "quadrants": quadrants,
        "collision": any(count > 1 for count in orbit_counts.values()),
        "partial_clip": partial_clip,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _info, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict rule-domain predicate; generated and canonical inputs are lawful."""
    return self_check(grid)


def _texture(info: dict[str, Any]) -> str | None:
    axis = bool(info["axis_dots"])
    collision = bool(info["collision"])
    clip = bool(info["partial_clip"])
    multi = len(info["quadrants"]) > 1
    if axis and collision and clip and multi:
        return "mixed"
    if axis and not collision and not clip and not multi:
        return "axis_dot"
    if not axis and collision and not clip and multi:
        return "multi_quadrant"
    if not axis and not collision and clip and not multi:
        return "clip"
    if not axis and not collision and not clip and not multi:
        return "plain"
    return None


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact axis from returned pixels, not RNG bookkeeping."""
    info, errors = _analyse(grid)
    if info is None or errors:
        return {}
    texture = _texture(info)
    if texture is None:
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "sep_color": info["separator"],
        "n_pixels": len(info["sources"]),
        "texture": texture,
    }


def _single_quadrant_only(grid: Grid) -> Grid:
    return _apply(grid, first_quadrant_only=True)


def _reflect_axis_cells(grid: Grid) -> Grid:
    return _apply(grid, include_axis_sources=True)


def _preserve_original_sources(grid: Grid) -> Grid:
    return _apply(grid, preserve_original_sources=True)


def _all_or_nothing_clipping(grid: Grid) -> Grid:
    return _apply(grid, all_or_nothing_clipping=True)


def _witness(predicate: Callable[[dict[str, Any]], bool], rivals: tuple[Callable, ...]):
    def check(grid):
        info, errors = _analyse(grid)
        if info is None or errors or not predicate(info):
            return False
        intended = _mirror(grid)
        return all(rival(deepcopy(grid)) != intended for rival in rivals)
    return check


SEMANTIC_RIVALS = {
    "single_quadrant_only": _single_quadrant_only,
    "reflect_axis_cells": _reflect_axis_cells,
    "preserve_original_sources": _preserve_original_sources,
    "all_or_nothing_clipping": _all_or_nothing_clipping,
}
SEMANTIC_WITNESSES = {
    "multi_quadrant_scan_order": _witness(
        lambda info: info["collision"] and len(info["quadrants"]) > 1,
        (_single_quadrant_only, _preserve_original_sources),
    ),
    "axis_cells_are_not_sources": _witness(
        lambda info: bool(info["axis_dots"]), (_reflect_axis_cells,)
    ),
    "partial_clipping_is_cellwise": _witness(
        lambda info: info["partial_clip"], (_all_or_nothing_clipping,)
    ),
}
WITNESS_RIVALS = {
    "multi_quadrant_scan_order": ["single_quadrant_only", "preserve_original_sources"],
    "axis_cells_are_not_sources": ["reflect_axis_cells"],
    "partial_clipping_is_cellwise": ["all_or_nothing_clipping"],
}
# These three wrong programs fit every labeled canonical pair and therefore need
# generated evidence. The clipping rival is retained semantically but canonical
# examples 2/3 already refute it.
CANONICAL_SHORTCUTS = {
    "single_quadrant_only": _single_quadrant_only,
    "reflect_axis_cells": _reflect_axis_cells,
    "preserve_original_sources": _preserve_original_sources,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require correct demos and at least one refutation of every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    lawful_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labeled pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        intended = _mirror(pair["input"])
        if pair["output"] != intended:
            reasons.append(f"demo {index} output disagrees with row-major fourfold reflection")
            continue
        lawful_demos.append(pair)
    for name, rival in LESSON_COMPETITORS.items():
        if lawful_demos and all(rival(deepcopy(pair["input"])) == pair["output"] for pair in lawful_demos):
            reasons.append(f"rival {name} survives every demonstration")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
    return reasons
