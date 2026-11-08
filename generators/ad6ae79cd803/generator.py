"""Generator for ``medium_n06`` — crop and rotate by a corner key.

A single maroon (9) cell occupies one grid corner.  Its corner encodes the
transform applied to the tight crop of the one interior, single-color motif:
TL=identity, TR=90° clockwise, BR=180°, BL=90° counter-clockwise.

Ordinary lessons use four consecutive ``sample_index`` values, so their four
demonstrations cover every corner code exactly once.  Generated motifs are
rotation-unique to make the key visible, while ``self_check`` deliberately
accepts the mildly symmetric canonical example whose possible rotations are
answer-equivalent for the demonstrated branch.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad6ae79cd803"
TASK_ID = "ad6ae79cd803"
VERSION = "2.0.0"
RULE_HASH = "6b203391dc52"

SUMMARY = (
    "Exactly one color-9 marker is at a corner and exactly one connected, "
    "single-color motif is strictly inside the border. Remove the marker, "
    "crop the motif tightly, then rotate that crop according to the marker: "
    "top-left identity, top-right clockwise 90°, bottom-right 180°, "
    "bottom-left counter-clockwise 90°."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0",
    "exactly one color-9 marker occupies one of the four corners",
    "exactly one 4-connected, single-color motif of 3..6 cells lies inside the border",
    "ordinary generated motifs have four distinct rotations",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 6..16 with a 35% canonical-profile prior",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..17 with a 35% canonical-profile prior",
        "valid": "7..17",
    },
    "corner_code": {
        "type": "int",
        "default": "sample_index mod 4 (TL=0, TR=1, BR=2, BL=3)",
        "valid": "0..3",
    },
    "motif_color": {
        "type": "color",
        "default": "keyed draw from 1..8",
        "valid": "1..8",
    },
    "motif_size": {
        "type": "int",
        "default": "difficulty-aware 3..6; canonical prior uses 3..4",
        "valid": "3..6",
    },
}

_CORNERS = ("tl", "tr", "br", "bl")
_CANONICAL_PRIOR = 0.35


def _norm_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot_norm(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    transformed: list[tuple[int, int]] = []
    for r, c in cells:
        if code == 0:
            transformed.append((r, c))
        elif code == 1:
            transformed.append((c, -r))
        elif code == 2:
            transformed.append((-r, -c))
        elif code == 3:
            transformed.append((-c, r))
        else:
            raise ValueError(f"invalid rotation code {code}")
    return _norm_cells(transformed)


def _rotation_unique(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _norm_cells(cells)
    return len({_rot_norm(normalized, code) for code in range(4)}) == 4


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _build_rotation_unique_motif(rng, size: int, max_dim: int) -> tuple[tuple[int, int], ...]:
    """Grow a connected polyomino whose four rotations are distinct."""
    for _ in range(400):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            cells.add((r + dr, c + dc))
        normalized = _norm_cells(cells)
        h = max(r for r, _ in normalized) + 1
        w = max(c for _, c in normalized) + 1
        if h <= max_dim and w <= max_dim and _rotation_unique(normalized):
            return normalized

    fallbacks = {
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 0), (1, 0), (2, 0), (2, 1)),
        5: ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1)),
        6: ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2)),
    }
    fallback = fallbacks[size]
    if max(max(r for r, _ in fallback), max(c for _, c in fallback)) + 1 > max_dim:
        raise RuntimeError(f"no {size}-cell motif fits max_dim={max_dim}")
    return fallback


def _corner_position(code: int, h: int, w: int) -> tuple[int, int]:
    return (
        (0, 0),
        (0, w - 1),
        (h - 1, w - 1),
        (h - 1, 0),
    )[code]


def _corner_code(grid: list[list[int]]) -> int | None:
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    positions = ((0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0))
    hits = [code for code, (r, c) in enumerate(positions) if grid[r][c] == 9]
    return hits[0] if len(hits) == 1 else None


def _motif_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def _place_motif(
    grid: list[list[int]],
    cells: tuple[tuple[int, int], ...],
    color: int,
    rng,
) -> None:
    """Place the motif strictly inside the border, preserving one component."""
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    positions = [
        (r0, c0)
        for r0 in range(1, h - sh)
        for c0 in range(1, w - sw)
    ]
    rng.shuffle(positions)
    if not positions:
        raise RuntimeError(
            f"motif {sh}x{sw} cannot fit strictly inside {h}x{w} grid"
        )
    r0, c0 = positions[0]
    for r, c in cells:
        grid[r0 + r][c0 + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    # Four consecutive examples cover all transform codes.  Route the scheduled
    # value through GenCtx as an effective exact override so draw provenance and
    # the returned grid agree on ordinary draws as well as caller overrides.
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("corner_code", int(sample_index) % 4)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    canonical_prior_allowed = all(
        overrides.get(axis) is None for axis in ("grid_h", "grid_w", "motif_size")
    )
    canonical_profile = (
        canonical_prior_allowed
        and ctx.draw_rng("canonical_profile").random() < _CANONICAL_PRIOR
    )

    if canonical_profile:
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        motif_size = ctx.draw_int("motif_size", 3, 4)
        max_dim = 3
    else:
        h = ctx.draw_int_diff("grid_h", 6, 16)
        w = ctx.draw_int_diff("grid_w", 7, 17)
        motif_size = ctx.draw_int_diff("motif_size", 3, 6)
        max_dim = 4

    corner_code = ctx.draw_int("corner_code", 0, 3)
    motif_color = ctx.draw_color("motif_color", exclude={0, 9})
    layout_rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    marker_r, marker_c = _corner_position(corner_code, h, w)
    grid[marker_r][marker_c] = 9
    motif = _build_rotation_unique_motif(layout_rng, motif_size, max_dim)
    _place_motif(grid, motif, motif_color, layout_rng)
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned input grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    motif = _motif_cells(grid)
    colors = {value for _, _, value in motif}
    observed: dict[str, int] = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_size": len(motif),
    }
    code = _corner_code(grid)
    if code is not None:
        observed["corner_code"] = code
    if len(colors) == 1:
        observed["motif_color"] = next(iter(colors))
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful input grammar, including all canonical inputs."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]

    h, w = len(grid), len(grid[0])
    if not 6 <= h <= 16:
        errors.append(f"grid height {h} outside 6..16")
    if not 7 <= w <= 17:
        errors.append(f"grid width {w} outside 7..17")

    values = [value for row in grid for value in row]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for value in values):
        errors.append("all cells must be integer ARC colors 0..9")
    if 0 not in values:
        errors.append("background color 0 must be present")

    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    legal_corners = {(0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0)}
    if len(markers) != 1:
        errors.append(f"expected exactly one color-9 marker, got {len(markers)}")
    elif markers[0] not in legal_corners:
        errors.append(f"color-9 marker must be at a corner, got {markers[0]}")

    motif = _motif_cells(grid)
    if not 3 <= len(motif) <= 6:
        errors.append(f"motif must contain 3..6 cells, got {len(motif)}")
        return errors

    motif_colors = {value for _, _, value in motif}
    if len(motif_colors) != 1:
        errors.append(
            "motif must use exactly one non-{0,9} color, got "
            f"{sorted(motif_colors)}"
        )
    elif next(iter(motif_colors)) not in range(1, 9):
        errors.append("motif color must be in 1..8")

    positions = {(r, c) for r, c, _ in motif}
    if not _connected(positions):
        errors.append("motif cells must form one 4-connected component")
    border_cells = [
        (r, c)
        for r, c in positions
        if r in (0, h - 1) or c in (0, w - 1)
    ]
    if border_cells:
        errors.append(f"motif must lie strictly inside the border: {border_cells[:4]}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the official small-canvas, small-motif task manifold."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if h not in (8, 9):
        reasons.append(f"canonical height is 8 or 9, got {h}")
    if w not in (8, 9, 10):
        reasons.append(f"canonical width is 8, 9, or 10, got {w}")
    motif = _motif_cells(grid)
    if len(motif) not in (3, 4):
        reasons.append(f"canonical motif has 3 or 4 cells, got {len(motif)}")
    if motif:
        rows = [r for r, _, _ in motif]
        cols = [c for _, c, _ in motif]
        bbox_h = max(rows) - min(rows) + 1
        bbox_w = max(cols) - min(cols) + 1
        if bbox_h > 3 or bbox_w > 3:
            reasons.append(f"canonical motif bbox is at most 3x3, got {bbox_h}x{bbox_w}")
    return reasons


def _is_corner(code: int):
    return lambda grid: _corner_code(grid) == code


SEMANTIC_WITNESSES = {
    "corner_tl_identity": _is_corner(0),
    "corner_tr_rotate_cw": _is_corner(1),
    "corner_br_rotate_180": _is_corner(2),
    "corner_bl_rotate_ccw": _is_corner(3),
}


def _crop_without_marker(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, c, _ in _motif_cells(grid)]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    out = [list(row) for row in grid]
    for _ in range(code):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def lesson_identifiable(demos, query) -> list[str]:
    """Check that demos identify the complete corner-to-rotation table.

    This is a verifier-only Python mirror.  Generation still emits inputs only;
    the Racket rule remains the sole authority used to materialize outputs.
    """
    reasons: list[str] = []
    possible_by_corner: dict[int, set[int]] = {}

    for index, demo in enumerate(demos):
        grid = demo.get("input")
        output = demo.get("output")
        code = _corner_code(grid)
        if code is None:
            reasons.append(f"demo {index} has no unique corner code")
            continue
        crop = _crop_without_marker(grid)
        matches = {
            transform
            for transform in range(4)
            if _rotate_grid(crop, transform) == output
        }
        if not matches:
            reasons.append(f"demo {index} output matches no corner rotation")
            continue
        possible_by_corner[code] = (
            matches
            if code not in possible_by_corner
            else possible_by_corner[code] & matches
        )
        if not possible_by_corner[code]:
            reasons.append(f"demo {index} contradicts earlier corner-{code} evidence")

    missing = sorted(set(range(4)) - set(possible_by_corner))
    if missing:
        reasons.append(f"demonstrations omit corner code(s) {missing}")
    for code, possible in sorted(possible_by_corner.items()):
        if code not in possible:
            reasons.append(
                f"corner {code} demonstrations do not support canonical rotation {code}"
            )

    query_grid = query.get("input")
    query_corner = _corner_code(query_grid)
    if query_corner is None:
        reasons.append("query has no unique corner code")
    elif query_corner not in possible_by_corner:
        reasons.append(f"query corner {query_corner} was not identified by demos")
    else:
        crop = _crop_without_marker(query_grid)
        candidate_answers = {
            tuple(tuple(row) for row in _rotate_grid(crop, transform))
            for transform in possible_by_corner[query_corner]
        }
        if len(candidate_answers) != 1:
            reasons.append(
                f"query admits {len(candidate_answers)} distinct answers under demo-consistent rotations"
            )
    return reasons
