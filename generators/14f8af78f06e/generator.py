"""Semantic generator for ARC task 14f8af78f06e.

The non-zero rectangle in the top-left corner is a 2-D seed tile.  A connected,
irregular color-8 mask appears in the lower-right portion of the input.  The
mask is replaced by the seed tile repeated from the mask bounding-box origin;
all non-mask cells are preserved.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "14f8af78f06e"
TASK_ID = "14f8af78f06e"
# 2.0.0 repairs the generator contract rather than merely widening randomness:
# canonical-profile scheduling, exact observable axes, structural self-checks,
# strict override handling, and shortcut-refuting semantic witnesses.
VERSION = "2.0.0"
RULE_HASH = "639bd6069514"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Read the non-zero top-left rectangle as a 2-D seed tile. Find the "
    "connected irregular color-8 mask in the lower-right region. Starting at "
    "the mask bounding-box top-left, replace each mask cell by the seed value "
    "at the corresponding row and column modulo the seed height and width; "
    "preserve every non-mask cell."
)

INVARIANTS = [
    "the seed is a non-zero, non-8 rectangle anchored at (0,0)",
    "a zero immediately after the seed in row 0 and column 0 exposes its width and height",
    "the color-8 mask is 4-connected, irregular, and wholly below and right of the seed",
    "outside the seed and mask every cell is background color 0",
    "the output changes only mask cells and uses bbox-relative two-dimensional tile phase",
]

# Every declared axis is exact, finite, and recoverable from the returned grid.
# Difficulty changes the non-canonical schedule slots, but never narrows the
# legal override domain: all declared boundary values remain valid in all bands.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/extended", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "scheduled canonical/extended", "valid": "9..16"},
    "tile_h": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "tile_w": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "mask_cells": {"type": "int", "default": "scheduled 4..8", "valid": "4..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# These are negative mutation fixtures, not valid training-distribution modes.
DEGENERATE_TEXTURES = ("no_seed", "no_mask", "mask_inside_seed", "rectangular_mask")
HELPFUL_TEXTURES: tuple[str, ...] = ()

_PROFILE_DIMS = (
    (8, 10, 2, 2, 7),   # canonical train geometry A
    (7, 12, 2, 3, 8),   # canonical train geometry B
    (8, 10, 3, 2, 7),   # canonical test geometry
    (10, 13, 3, 3, 8),
)

# Each template is connected, has exactly n cells, and leaves at least one hole
# in its bounding box.  All fit a 3x4 rectangle, so every legal dimension/tile
# override combination has room in the lower-right region.
_MASK_TEMPLATES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    6: ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Stable four-profile lesson schedule used by the semantic gate."""
    del seed, difficulty
    return int(sample_index) % len(_PROFILE_DIMS)


SCHEDULE_PROFILES = tuple(range(len(_PROFILE_DIMS)))


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use the schedule normally, while accepting the full declared override domain."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(shape: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    if code & 4:
        cells = [(row, -col) for row, col in cells]
    for _ in range(code & 3):
        cells = [(col, -row) for row, col in cells]
    return _normalize(cells)


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _choose_mask(mask_cells: int, max_h: int, max_w: int, rng) -> tuple[tuple[int, int], ...]:
    base = _MASK_TEMPLATES[mask_cells]
    candidates = []
    for code in range(8):
        shape = _transform(base, code)
        shape_h, shape_w = _shape_dims(shape)
        if shape_h <= max_h and shape_w <= max_w and shape not in candidates:
            candidates.append(shape)
    if not candidates:
        # The declared domains guarantee at least 3x5 of lower-right space, so
        # this is a loud internal-contract failure rather than a silent fallback.
        raise ValueError(
            f"mask_cells={mask_cells} has no irregular template fitting {max_h}x{max_w}"
        )
    return candidates[rng.randrange(len(candidates))]


def _pick_origin(lo: int, hi: int, modulus: int, preferred_phase: int, rng) -> int:
    candidates = list(range(lo, hi + 1))
    preferred = [value for value in candidates if value % modulus == preferred_phase % modulus]
    pool = preferred or candidates
    return pool[rng.randrange(len(pool))]


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 10, 0)
    if name == "no_seed":
        for row, col in ((3, 5), (3, 6), (4, 5), (5, 5)):
            grid[row][col] = 8
    elif name == "no_mask":
        grid[0][0:2] = [1, 2]
        grid[1][0:2] = [3, 4]
    elif name == "mask_inside_seed":
        grid[0][0:2] = [1, 2]
        grid[1][0:2] = [3, 4]
        grid[1][1] = 8
    elif name == "rectangular_mask":
        grid[0][0:2] = [1, 2]
        grid[1][0:2] = [3, 4]
        for row in range(3, 5):
            for col in range(5, 7):
                grid[row][col] = 8
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(sorted(unknown))}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture fixture: {texture!r}")
        conflicting = sorted(set(overrides) & set(AXES))
        if conflicting:
            raise ValueError(
                "texture fixture is incompatible with exact axes: " + ", ".join(conflicting)
            )
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_th, default_tw, default_mask_cells = _PROFILE_DIMS[profile]

    # Extended profile size varies by band without excluding canonical profiles
    # from any band's sequential schedule.
    if profile == 3:
        if difficulty == "easy":
            default_h, default_w = 9, 11
        elif difficulty == "hard":
            default_h, default_w = 13, 15

    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 7, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 9, 16)
    tile_h = _scheduled_int(ctx, overrides, "tile_h", default_th, 2, 4)
    tile_w = _scheduled_int(ctx, overrides, "tile_w", default_tw, 2, 4)
    mask_cells = _scheduled_int(ctx, overrides, "mask_cells", default_mask_cells, 4, 8)

    max_mask_h = height - tile_h
    max_mask_w = width - tile_w
    mask_rng = ctx.draw_rng("mask_shape")
    mask = _choose_mask(mask_cells, max_mask_h, max_mask_w, mask_rng)
    mask_h, mask_w = _shape_dims(mask)

    grid = full_grid(height, width, 0)
    palette_rng = ctx.draw_rng("seed_palette")
    palette = list(_ALLOWED_COLORS)
    palette_rng.shuffle(palette)
    for row in range(tile_h):
        for col in range(tile_w):
            # Row and column both affect the value; cycling after eight cells
            # preserves a genuine 2-D phase even for the 4x4 boundary case.
            grid[row][col] = palette[(row * tile_w + col) % len(palette)]

    placement_rng = ctx.draw_rng("mask_position")
    # Profiles deliberately vary bbox phase relative to the global grid. This
    # creates counterexamples to a shortcut that tiles from (0,0) instead of
    # from the mask bbox origin.
    top_phase = (1, 0, 0, 1)[profile]
    left_phase = (0, 1, 0, 2)[profile]
    top = _pick_origin(tile_h, height - mask_h, tile_h, top_phase, placement_rng)
    left = _pick_origin(tile_w, width - mask_w, tile_w, left_phase, placement_rng)
    for dr, dc in mask:
        grid[top + dr][left + dc] = 8
    return grid


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed ARC 30x30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _analyze(grid) -> dict:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])

    tile_w = 0
    while tile_w < width and grid[0][tile_w] not in (0, 8):
        tile_w += 1
    tile_h = 0
    while tile_h < height and grid[tile_h][0] not in (0, 8):
        tile_h += 1

    if tile_h < 2 or tile_w < 2:
        errors.append("top-left seed tile must be at least 2x2")
        return {"errors": errors, "tile_h": tile_h, "tile_w": tile_w}
    if tile_h >= height or tile_w >= width:
        errors.append("seed tile must have visible row and column terminators")
        return {"errors": errors, "tile_h": tile_h, "tile_w": tile_w}
    if grid[0][tile_w] != 0 or grid[tile_h][0] != 0:
        errors.append("seed row/column terminators must be zero")

    seed = [list(row[:tile_w]) for row in grid[:tile_h]]
    if any(value in (0, 8) for row in seed for value in row):
        errors.append("seed tile must be entirely nonzero and non-mask-colored")
    if len({value for row in seed for value in row}) < 3:
        errors.append("seed tile must contain at least three distinct colors")

    mask = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 8}
    if len(mask) < 4:
        errors.append("expected at least four visible color-8 mask cells")
    if any(row < tile_h or col < tile_w for row, col in mask):
        errors.append("mask must lie wholly below and right of the seed tile")
    if mask and not _connected(mask):
        errors.append("mask must be 4-connected")

    outside_values = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            in_seed = row < tile_h and col < tile_w
            if not in_seed and value not in (0, 8):
                outside_values.append((row, col, value))
    if outside_values:
        errors.append("non-background texture outside the seed and mask is not allowed")

    bbox = None
    bbox_area = 0
    row_phases: set[int] = set()
    col_phases: set[int] = set()
    if mask:
        row0 = min(row for row, _ in mask)
        row1 = max(row for row, _ in mask)
        col0 = min(col for _, col in mask)
        col1 = max(col for _, col in mask)
        bbox = (row0, col0, row1, col1)
        bbox_area = (row1 - row0 + 1) * (col1 - col0 + 1)
        row_phases = {(row - row0) % tile_h for row, _ in mask}
        col_phases = {(col - col0) % tile_w for _, col in mask}
        if bbox_area == len(mask):
            errors.append("mask must be irregular rather than a filled rectangle")
        if len(row_phases) < 2 or len(col_phases) < 2:
            errors.append("mask must expose at least two row and two column tile phases")

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "tile_h": tile_h,
        "tile_w": tile_w,
        "mask_cells": len(mask),
        "seed": seed,
        "mask": tuple(sorted(mask)),
        "bbox": bbox,
        "bbox_area": bbox_area,
        "row_phase_count": len(row_phases),
        "col_phase_count": len(col_phases),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or shortcut-hiding scenes."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "tile_h": facts["tile_h"],
        "tile_w": facts["tile_w"],
        "mask_cells": facts["mask_cells"],
    }


def semantic_observables(grid) -> dict:
    facts = _analyze(grid)
    if facts.get("errors"):
        return {"errors": list(facts["errors"])}
    row0, col0, row1, col1 = facts["bbox"]
    return {
        "tile_h": facts["tile_h"],
        "tile_w": facts["tile_w"],
        "mask_cells": facts["mask_cells"],
        "mask_bbox": (row0, col0, row1, col1),
        "bbox_holes": facts["bbox_area"] - facts["mask_cells"],
        "row_phase_count": facts["row_phase_count"],
        "col_phase_count": facts["col_phase_count"],
        "bbox_global_phase": (row0 % facts["tile_h"], col0 % facts["tile_w"]),
        "seed_colors": len({value for row in facts["seed"] for value in row}),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent test mirror; canonical Racket remains the output authority."""
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    row0, col0, _, _ = facts["bbox"]
    output = [list(row) for row in grid]
    for row, col in facts["mask"]:
        output[row][col] = facts["seed"][(row - row0) % facts["tile_h"]][
            (col - col0) % facts["tile_w"]
        ]
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_constant_fill(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    value = facts["seed"][0][0]
    output = [list(row) for row in grid]
    for row, col in facts["mask"]:
        output[row][col] = value
    return output


def _rival_global_phase(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = [list(row) for row in grid]
    for row, col in facts["mask"]:
        output[row][col] = facts["seed"][row % facts["tile_h"]][col % facts["tile_w"]]
    return output


def _rival_fill_bbox(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    row0, col0, row1, col1 = facts["bbox"]
    output = [list(row) for row in grid]
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            output[row][col] = facts["seed"][(row - row0) % facts["tile_h"]][
                (col - col0) % facts["tile_w"]
            ]
    return output


def _rival_row_only(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    row0, _, _, _ = facts["bbox"]
    output = [list(row) for row in grid]
    for row, col in facts["mask"]:
        output[row][col] = facts["seed"][(row - row0) % facts["tile_h"]][0]
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "marker_as_answer": _rival_identity,
    "modal_or_first_color_fill": _rival_constant_fill,
    "global_origin_phase": _rival_global_phase,
    "fill_mask_bbox": _rival_fill_bbox,
    "row_phase_only": _rival_row_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _refutes(name: str):
    rival = SEMANTIC_RIVALS[name]

    def predicate(grid):
        try:
            return rule_mirror(grid) != rival(grid)
        except Exception:
            return False

    return predicate


SEMANTIC_WITNESSES = {
    "changes_marker_cells": _refutes("marker_as_answer"),
    "nonconstant_two_dimensional_tile": _refutes("modal_or_first_color_fill"),
    "bbox_relative_phase": _refutes("global_origin_phase"),
    "irregular_mask_holes": _refutes("fill_mask_bbox"),
    "column_phase_matters": _refutes("row_phase_only"),
}
WITNESS_RIVALS = {
    "changes_marker_cells": ["marker_as_answer"],
    "nonconstant_two_dimensional_tile": ["modal_or_first_color_fill"],
    "bbox_relative_phase": ["global_origin_phase"],
    "irregular_mask_holes": ["fill_mask_bbox"],
    "column_phase_matters": ["row_phase_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to falsify every named shortcut before the query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    demo_facts = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with bbox-relative 2-D tiling")
            continue
        demo_facts.append(semantic_observables(pair["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with bbox-relative 2-D tiling")

    if len(demo_facts) != len(demos):
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = True
        for pair in demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    survives = False
                    break
            except Exception:
                survives = False
                break
        if survives:
            reasons.append(f"rival rule {name!r} still fits every demonstration")

    geometries = {(facts["tile_h"], facts["tile_w"]) for facts in demo_facts}
    if len(geometries) < 2:
        reasons.append("demonstrations do not vary seed-tile geometry")
    origins = {facts["bbox_global_phase"] for facts in demo_facts}
    if len(origins) < 2:
        reasons.append("demonstrations do not vary bbox phase relative to the global grid")
    mask_sizes = {facts["mask_cells"] for facts in demo_facts}
    if len(mask_sizes) < 2:
        reasons.append("demonstrations do not vary mask cell count")
    return reasons
