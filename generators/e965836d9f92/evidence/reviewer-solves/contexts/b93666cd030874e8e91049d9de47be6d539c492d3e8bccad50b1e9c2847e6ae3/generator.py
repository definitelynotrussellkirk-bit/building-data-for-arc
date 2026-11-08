"""Generator for 21b:hard_144 — build a transform/recolor gallery.

The non-zero cells in row 0 are transform codes, in left-to-right order.
The non-zero cells in column 0 are output colors, in top-to-bottom order.
The body contains one monochrome 4-connected prototype.  The Racket oracle
binarizes that prototype, applies each transform code, recolors each result to
each header color, and pastes the color × transform cross-product with one-cell
gaps.

This generator uses a nine-slot rotation-complete cycle over four code
profiles, including three canonical anchors.  Every transform code appears at
least twice in every four-sample window, so every leave-one-out lesson directly
witnesses each mapping while retaining robust canonical support.  Noncanonical
defaults use square transform-separating prototypes so quarter turns cannot
collapse through the selected gallery clipping authority.  Every noncanonical
sample also places both headers so physical coordinates cannot masquerade as
the encoded transform codes or output colors.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e965836d9f92"
TASK_ID = GENERATOR_ID
RULE_HASH = "29642118732e"
VERSION = "3.3.1"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Read transform codes from the top header and colors from the left header. "
    "Crop the single body prototype, then output every transformed × recolored "
    "copy in a gallery with one-cell separators."
)

INVARIANTS = [
    "background is 0 and the top-left cell is 0",
    "row 0 contains 2-4 distinct transform codes from 1..6",
    "column 0 contains 2-4 distinct colors from 1..9",
    "the body contains exactly one monochrome 4-connected prototype of 4-9 cells",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "scheduled", "valid": "8..18"},
    "n_codes": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "n_colors": {"type": "int", "default": "difficulty-aware 2..4", "valid": "2..4"},
    "proto_size": {"type": "int", "default": "difficulty-aware 4..9", "valid": "4..9"},
}

# Every boundary tuple in override-contract v7 is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "codes_1_4_5_6",
    "codes_2_4_5_6",
    "codes_3_4_5_6",
)

# Three canonical anchors in nine slots keep strict support safely above the
# declared 25% floor.  The interleaved extra code (1,2,3) makes every code occur
# at least twice in every four-slot window, including across the cycle boundary.
SCHEDULE_CYCLE = (
    "canonical_anchor",
    "codes_1_4_5_6",
    "codes_2_4_5_6",
    "canonical_anchor",
    "codes_3_4_5_6",
    "codes_1_4_5_6",
    "canonical_anchor",
    "codes_2_4_5_6",
    "codes_3_4_5_6",
)

# Connected, transform-separating fallbacks for every legal prototype size.
_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    6: ((0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    7: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1)),
    8: ((0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1)),
    9: ((0, 0), (1, 0), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2), (4, 0), (4, 1)),
}

# Square, connected, transform-separating fallbacks for curriculum profiles.
# No connected four-cell polyomino has six distinct dihedral transforms inside
# a square bounding box, so square-safe defaults begin at five cells.
_SQUARE_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    5: ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    6: ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    7: ((0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    8: ((0, 1), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (3, 0), (3, 1)),
    9: ((0, 3), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 2)),
}

_PROFILE_MANDATORY_OVERRIDE_CODES: dict[str, tuple[int, ...]] = {
    "codes_1_4_5_6": (5, 6),
    "codes_2_4_5_6": (5, 6),
    "codes_3_4_5_6": (5, 6),
}

_CANONICAL_DIMS = ((9, 9), (10, 10), (10, 12), (11, 11))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Stable nine-slot cycle with rotation-complete four-sample windows."""
    del seed, difficulty
    return SCHEDULE_CYCLE[int(sample_index) % len(SCHEDULE_CYCLE)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform_cells(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    transformed: list[tuple[int, int]] = []
    for r, c in cells:
        if code == 2:
            nr, nc = r, w - 1 - c
        elif code == 3:
            nr, nc = h - 1 - r, c
        elif code == 4:
            nr, nc = c, h - 1 - r
        elif code == 5:
            nr, nc = h - 1 - r, w - 1 - c
        elif code == 6:
            nr, nc = w - 1 - c, r
        else:
            nr, nc = r, c
        transformed.append((nr, nc))
    return _normalize(transformed)


def _is_transform_separating(cells: Iterable[tuple[int, int]]) -> bool:
    return len({_transform_cells(cells, code) for code in range(1, 7)}) == 6


def _random_blob(
    rng: Any, size: int, *, require_square: bool = False
) -> tuple[tuple[int, int], ...]:
    """Return a connected transform-separating blob, optionally square-bounded."""
    for _ in range(160):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
            candidate = (r + dr, c + dc)
            if candidate in seen:
                continue
            trial = cells + [candidate]
            normalized = _normalize(trial)
            bh = max(x for x, _ in normalized) + 1
            bw = max(y for _, y in normalized) + 1
            if bh <= 5 and bw <= 5:
                cells.append(candidate)
                seen.add(candidate)
        normalized = _normalize(cells)
        bh = max(r for r, _ in normalized) + 1
        bw = max(c for _, c in normalized) + 1
        if _is_transform_separating(normalized) and (not require_square or bh == bw):
            return normalized
    if require_square:
        try:
            return _SQUARE_FALLBACK_SHAPES[size]
        except KeyError as exc:
            raise ValueError(f"no square transform-separating fallback for size={size}") from exc
    return _FALLBACK_SHAPES[size]


def _axis_int(ctx: Any, label: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled default while accepting every declared boundary."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _default_codes(profile: str, difficulty: Any) -> tuple[int, ...]:
    """Profiles arranged so every four-slot window has two hits per code."""
    del difficulty
    return {
        "canonical_anchor": (1, 2, 3),
        "codes_1_4_5_6": (1, 4, 5, 6),
        "codes_2_4_5_6": (2, 4, 5, 6),
        "codes_3_4_5_6": (3, 4, 5, 6),
    }[profile]


def _default_color_count(profile: str, difficulty: Any, rng: Any) -> int:
    if profile == "canonical_anchor":
        return 2 if difficulty == "easy" else rng.choice((2, 3))
    if difficulty == "easy":
        return 2
    if difficulty == "hard":
        return rng.choice((3, 4))
    return rng.choice((2, 3))


def _default_proto_size(profile: str, difficulty: Any, rng: Any) -> int:
    if profile == "canonical_anchor":
        return rng.choice((4, 5, 6))
    if difficulty == "easy":
        return 5
    if difficulty == "hard":
        return rng.choice((8, 9))
    return rng.choice((6, 7))


def _spread_positions(rng: Any, limit: int, count: int) -> list[int]:
    """Choose sorted header positions and force a visible gap when possible."""
    choices = list(range(1, limit))
    if count == 1:
        return [rng.choice(choices)]
    picked = {choices[0], choices[-1]}
    remaining = [x for x in choices[1:-1] if x not in picked]
    if count > 2:
        picked.update(rng.sample(remaining, count - 2))
    return sorted(picked)


def _refute_physical_header_values(
    positions: list[int], *, limit: int, values: Iterable[int], modulus: int
) -> list[int]:
    """Keep a draw unless physical coordinates would exactly encode its values.

    Noncanonical lessons are meant to teach that header *contents*, not header
    coordinates, carry the transform/color semantics.  A rare random collision
    can otherwise make the coordinate shortcut fit a complete leave-one-out
    lesson.  The deterministic fallback is used only for such collisions (or a
    contiguous draw) and preserves sorted, in-bounds, distinct positions.
    """
    expected = list(values)
    contiguous = list(range(1, len(expected) + 1))

    def refutes(candidate: list[int]) -> bool:
        decoded = [((position - 1) % modulus) + 1 for position in candidate]
        return candidate != contiguous and decoded != expected

    if refutes(positions):
        return positions
    for candidate in combinations(range(1, limit), len(expected)):
        result = list(candidate)
        if refutes(result):
            return result
    raise ValueError("cannot place a noncontiguous header that refutes physical-value decoding")


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)

    scheduled_codes = _default_codes(profile, difficulty)
    n_codes = _axis_int(ctx, "n_codes", 2, 4, len(scheduled_codes))
    if "n_codes" in overrides:
        mandatory = list(_PROFILE_MANDATORY_OVERRIDE_CODES.get(profile, ()))
        mandatory = mandatory[:n_codes]
        available = [code for code in range(1, 7) if code not in mandatory]
        code_values = tuple(mandatory + rng.sample(available, n_codes - len(mandatory)))
        code_values = tuple(rng.sample(list(code_values), len(code_values)))
    else:
        code_values = scheduled_codes

    default_n_colors = _default_color_count(profile, difficulty, rng)
    n_colors = _axis_int(ctx, "n_colors", 2, 4, default_n_colors)
    default_proto_size = _default_proto_size(profile, difficulty, rng)
    proto_size = _axis_int(ctx, "proto_size", 4, 9, default_proto_size)

    if profile == "canonical_anchor" and "proto_size" not in overrides:
        shape = _FALLBACK_SHAPES[proto_size]
    else:
        require_square = profile != "canonical_anchor" and proto_size >= 5
        shape = _random_blob(rng, proto_size, require_square=require_square)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1

    if profile == "canonical_anchor" and not ({"grid_h", "grid_w"} & set(overrides)):
        dims = [dims for dims in _CANONICAL_DIMS if dims[0] >= sh + 3 and dims[1] >= sw + 3]
        default_h, default_w = rng.choice(dims)
    else:
        lo_h = max(8, sh + 3)
        lo_w = max(8, sw + 3)
        if difficulty == "easy":
            default_h = rng.randint(lo_h, max(lo_h, 11))
            default_w = rng.randint(lo_w, max(lo_w, 11))
        elif difficulty == "hard":
            default_h = rng.randint(max(lo_h, 11), 18)
            default_w = rng.randint(max(lo_w, 11), 18)
        else:
            default_h = rng.randint(max(lo_h, 9), 15)
            default_w = rng.randint(max(lo_w, 9), 15)
    h = _axis_int(ctx, "grid_h", 8, 18, default_h)
    w = _axis_int(ctx, "grid_w", 8, 18, default_w)

    if h < sh + 3 or w < sw + 3:
        raise ValueError(
            f"grid_h={h}, grid_w={w}, proto_size={proto_size} cannot preserve the prototype moat"
        )

    grid = full_grid(h, w, 0)
    if profile == "canonical_anchor" and "n_codes" not in overrides:
        code_cols = list(range(1, n_codes + 1))
    elif profile == "codes_1_4_5_6":
        code_cols = _spread_positions(rng, w, n_codes)
    else:
        code_cols = sorted(rng.sample(range(1, w), n_codes))
    if profile != "canonical_anchor":
        code_cols = _refute_physical_header_values(
            code_cols, limit=w, values=code_values, modulus=6
        )

    if profile == "canonical_anchor" and "n_colors" not in overrides:
        color_rows = list(range(1, n_colors + 1))
    elif profile == "codes_1_4_5_6":
        color_rows = _spread_positions(rng, h, n_colors)
    else:
        color_rows = sorted(rng.sample(range(1, h), n_colors))

    header_colors = rng.sample(range(1, 10), n_colors)
    if profile != "canonical_anchor":
        color_rows = _refute_physical_header_values(
            color_rows, limit=h, values=header_colors, modulus=9
        )
    for col, code in zip(code_cols, code_values):
        grid[0][col] = code
    for row, color in zip(color_rows, header_colors):
        grid[row][0] = color

    proto_color = 9 if profile == "canonical_anchor" else rng.randint(1, 9)
    r0 = rng.randint(2, h - sh - 1)
    c0 = rng.randint(2, w - sw - 1)
    for dr, dc in shape:
        grid[r0 + dr][c0 + dc] = proto_color
    return grid


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        info["errors"].append("empty grid")
        return info
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        info["errors"].append("ragged grid")
        return info
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9 for row in grid for value in row):
        info["errors"].append("grid values must be integer colors 0..9")
        return info

    code_positions = [c for c in range(1, w) if grid[0][c] != 0]
    color_positions = [r for r in range(1, h) if grid[r][0] != 0]
    codes = [grid[0][c] for c in code_positions]
    colors = [grid[r][0] for r in color_positions]
    body_cells = {(r, c) for r in range(1, h) for c in range(1, w) if grid[r][c] != 0}
    body_colors = {grid[r][c] for r, c in body_cells}
    comps = _components(body_cells) if body_cells else []

    normalized_shape: tuple[tuple[int, int], ...] = ()
    bbox_h = bbox_w = 0
    if body_cells:
        normalized_shape = _normalize(body_cells)
        bbox_h = max(r for r, _ in normalized_shape) + 1
        bbox_w = max(c for _, c in normalized_shape) + 1

    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "code_positions": code_positions,
            "color_positions": color_positions,
            "codes": codes,
            "colors": colors,
            "n_codes": len(codes),
            "n_colors": len(colors),
            "body_cells": body_cells,
            "body_colors": body_colors,
            "components": comps,
            "proto_size": len(body_cells),
            "shape": normalized_shape,
            "bbox_h": bbox_h,
            "bbox_w": bbox_w,
            "transform_count": (
                len({_transform_cells(normalized_shape, code) for code in range(1, 7)})
                if normalized_shape
                else 0
            ),
        }
    )
    return info


def observe_overrides(grid: Any) -> dict[str, int]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {axis: int(info[axis]) for axis in AXES}


def self_check(grid: Any, *, difficulty: Any = None, meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if grid[0][0] != 0:
        errors.append("top-left cell must be background")
    if not 8 <= info["grid_h"] <= 18 or not 8 <= info["grid_w"] <= 18:
        errors.append("grid dimensions must each be in 8..18")
    if not 2 <= info["n_codes"] <= 4:
        errors.append(f"expected 2-4 transform codes, got {info['n_codes']}")
    if any(code not in range(1, 7) for code in info["codes"]):
        errors.append("transform code outside 1..6")
    if len(set(info["codes"])) != info["n_codes"]:
        errors.append("transform codes must be distinct")
    if not 2 <= info["n_colors"] <= 4:
        errors.append(f"expected 2-4 color headers, got {info['n_colors']}")
    if len(set(info["colors"])) != info["n_colors"]:
        errors.append("color headers must be distinct")
    if not 4 <= info["proto_size"] <= 9:
        errors.append(f"prototype must contain 4-9 cells, got {info['proto_size']}")
    if len(info["components"]) != 1:
        errors.append(f"expected one connected prototype component, got {len(info['components'])}")
    if len(info["body_colors"]) != 1:
        errors.append(f"prototype must be monochrome, got {len(info['body_colors'])} colors")
    if info["bbox_h"] > 5 or info["bbox_w"] > 5:
        errors.append("prototype bounding box exceeds 5x5")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(f"{axis} requested {value!r}, observed {observed.get(axis)!r}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analyze(grid)
    reasons = self_check(grid)
    if reasons:
        return reasons
    if not (9 <= info["grid_h"] <= 11 and 9 <= info["grid_w"] <= 12):
        reasons.append("canonical inputs are 9-11 rows by 9-12 columns")
    if info["code_positions"] != list(range(1, info["n_codes"] + 1)):
        reasons.append("canonical transform headers are contiguous from column 1")
    if info["color_positions"] != list(range(1, info["n_colors"] + 1)):
        reasons.append("canonical color headers are contiguous from row 1")
    if not 2 <= info["n_codes"] <= 3 or any(code > 4 for code in info["codes"]):
        reasons.append("canonical examples use 2-3 codes drawn from 1..4")
    if not 2 <= info["n_colors"] <= 3:
        reasons.append("canonical examples use 2-3 output colors")
    if not 4 <= info["proto_size"] <= 6 or info["bbox_h"] > 3 or info["bbox_w"] > 3:
        reasons.append("canonical prototype is a 4-6 cell shape inside 3x3")
    if info["body_colors"] != {9}:
        reasons.append("canonical prototype color is 9")
    return reasons


MIN_STRICT_FRAC = 0.25


def _matrix_from_cells(cells: Iterable[tuple[int, int]], color: int = 1) -> list[list[int]]:
    cells = _normalize(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    matrix = full_grid(h, w, 0)
    for r, c in cells:
        matrix[r][c] = color
    return matrix


def _gallery(
    grid: list[list[int]],
    *,
    code_mapper: Callable[[int, int], int] | None = None,
    color_mapper: Callable[[int, int, int], int] | None = None,
) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"] or not info["body_cells"] or not info["codes"] or not info["colors"]:
        return []
    code_mapper = code_mapper or (lambda code, index: code)
    body_color = next(iter(info["body_colors"]))
    panels: list[list[list[list[int]]]] = []
    for color_index, color in enumerate(info["colors"]):
        row: list[list[list[int]]] = []
        out_color = color_mapper(color, color_index, body_color) if color_mapper else color
        for code_index, code in enumerate(info["codes"]):
            mapped = code_mapper(code, code_index)
            row.append(_matrix_from_cells(_transform_cells(info["shape"], mapped), out_color))
        panels.append(row)

    ph, pw = len(panels[0][0]), len(panels[0][0][0])
    nr, nc = len(panels), len(panels[0])
    out = full_grid(nr * ph + max(0, nr - 1), nc * pw + max(0, nc - 1), 0)
    for ri, panel_row in enumerate(panels):
        for ci, panel in enumerate(panel_row):
            for r, row in enumerate(panel):
                for c, value in enumerate(row):
                    rr = ri * (ph + 1) + r
                    cc = ci * (pw + 1) + c
                    if value and 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                        out[rr][cc] = value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for semantic tests; Racket remains output authority."""
    return _gallery(grid)


def _identity_codes(grid: list[list[int]]) -> list[list[int]]:
    return _gallery(grid, code_mapper=lambda code, index: 1)


def _rank_as_code(grid: list[list[int]]) -> list[list[int]]:
    return _gallery(grid, code_mapper=lambda code, index: min(index + 1, 6))


def _remap_one_code(
    grid: list[list[int]], target: int, replacement: int
) -> list[list[int]]:
    return _gallery(
        grid,
        code_mapper=lambda code, index: replacement if code == target else code,
    )


def _code1_as_flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 1, 2)


def _code2_as_identity(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 2, 1)


def _code3_as_identity(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 3, 1)


def _code4_as_identity(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 4, 1)


def _code5_as_identity(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 5, 1)


def _code6_as_cw(grid: list[list[int]]) -> list[list[int]]:
    return _remap_one_code(grid, 6, 4)


def _first_color_only(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    first = info["colors"][0]
    return _gallery(grid, color_mapper=lambda color, index, body: first)


def _keep_prototype_color(grid: list[list[int]]) -> list[list[int]]:
    return _gallery(grid, color_mapper=lambda color, index, body: body)


def _header_column_is_transform_code(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: use physical header column, not its numeric value."""
    positions = _analyze(grid)["code_positions"]
    return _gallery(
        grid,
        code_mapper=lambda code, index: ((positions[index] - 1) % 6) + 1,
    )


def _header_row_is_output_color(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: use physical header row, not its numeric color."""
    positions = _analyze(grid)["color_positions"]
    return _gallery(
        grid,
        color_mapper=lambda color, index, body: ((positions[index] - 1) % 9) + 1,
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_transform_codes": _identity_codes,
    "header_rank_is_transform_code": _rank_as_code,
    "code1_is_flip_lr": _code1_as_flip_lr,
    "code2_is_identity": _code2_as_identity,
    "code3_is_identity": _code3_as_identity,
    "code4_is_identity": _code4_as_identity,
    "code5_is_identity": _code5_as_identity,
    "code6_is_rotate_cw": _code6_as_cw,
    "reuse_first_header_color": _first_color_only,
    "keep_prototype_color": _keep_prototype_color,
    "header_column_is_transform_code": _header_column_is_transform_code,
    "header_row_is_output_color": _header_row_is_output_color,
}
# Position-based rivals validate their dedicated witnesses, but are not part of
# the production lesson contract: random header locations can occasionally be
# answer-equivalent on one lesson even though the generated corpus refutes them.
LESSON_COMPETITORS = {
    name: rival
    for name, rival in SEMANTIC_RIVALS.items()
    if name not in {
        "header_column_is_transform_code",
        "header_row_is_output_color",
    }
}

# Codes 5 and 6 are absent from every canonical pair, so generated witnesses
# are the only way to falsify these two particularly dangerous shortcuts.
CANONICAL_SHORTCUTS = {
    "code5_is_identity": _code5_as_identity,
    "code6_is_rotate_cw": _code6_as_cw,
}


def _facts(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return info


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    **{f"code_{code}": (lambda grid, code=code: code in _facts(grid)["codes"]) for code in range(1, 7)},
    "all_coded_transforms_distinct": lambda grid: _facts(grid)["transform_count"] == 6,
    "noncontiguous_code_headers": lambda grid: (
        _facts(grid)["code_positions"]
        != list(range(1, _facts(grid)["n_codes"] + 1))
        and _header_column_is_transform_code(grid) != rule_mirror(grid)
    ),
    "noncontiguous_color_headers": lambda grid: (
        _facts(grid)["color_positions"]
        != list(range(1, _facts(grid)["n_colors"] + 1))
        and _header_row_is_output_color(grid) != rule_mirror(grid)
    ),
    "code_sequence_not_rank": lambda grid: _facts(grid)["codes"] != list(range(1, _facts(grid)["n_codes"] + 1)),
    "multiple_header_colors": lambda grid: _facts(grid)["n_colors"] >= 2,
    "recolor_changes_prototype": lambda grid: any(color not in _facts(grid)["body_colors"] for color in _facts(grid)["colors"]),
}

WITNESS_RIVALS = {
    "code_1": ["code1_is_flip_lr"],
    "code_2": ["code2_is_identity"],
    "code_3": ["code3_is_identity"],
    "code_4": ["code4_is_identity"],
    "code_5": ["code5_is_identity"],
    "code_6": ["code6_is_rotate_cw"],
    "all_coded_transforms_distinct": ["ignore_transform_codes"],
    "noncontiguous_code_headers": ["header_column_is_transform_code"],
    "noncontiguous_color_headers": ["header_row_is_output_color"],
    "code_sequence_not_rank": ["header_rank_is_transform_code"],
    "multiple_header_colors": ["reuse_first_header_color"],
    "recolor_changes_prototype": ["keep_prototype_color"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
    return reasons
