"""Semantic generator for ARC task af72e426e241.

True rule
---------
A square zero-background input contains one unique color-9 anchor at the exact
center and one connected single-color motif wholly inside one quadrant.  The
output removes the anchor and completes a four-way arrangement around it:
keep the motif, reflect it left/right across the anchor column, reflect it
up/down across the anchor row, and place the 180-degree copy diagonally
opposite.

The ordinary curriculum deliberately rotates the *source quadrant* through all
four possibilities.  This refutes the canonical-only shortcut "the supplied
motif is always northwest" while preserving the same reflection rule.  Every
ordinary motif is horizontally and vertically asymmetric, so stamping four
unreflected copies cannot masquerade as the intended transformation.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af72e426e241"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5c65ec3a17c8"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A centered color-9 anchor and one connected single-color motif occupy one "
    "quadrant of an odd square grid. Remove the anchor and complete the other "
    "three quadrants by horizontal, vertical, and 180-degree reflection."
)

INVARIANTS = [
    "background is 0 and the square grid size is one of 13, 15, 17, or 19",
    "exactly one color-9 anchor sits at the grid center",
    "exactly one 4-connected motif in one color 1..8 lies wholly in one quadrant",
    "the motif bbox is 2..3 by 2..3 with a 1..2 cell gap from each anchor axis",
    "the motif is asymmetric under both horizontal and vertical reflection",
    "four consecutive samples cover all four possible source quadrants",
]

GRID_SIZES = (13, 15, 17, 19)
QUADRANTS = ("northwest", "northeast", "southwest", "southeast")
MOTIF_DIMS = ((2, 2), (2, 3), (3, 2), (3, 3))
MOTIF_COLORS = tuple(range(1, 9))

AXES = {
    "grid_size": {
        "type": "int",
        "default": "scheduled 13/15 canonical anchor plus larger odd squares",
        "valid": "13|15|17|19",
    },
    "motif_h": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "motif_w": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "quadrant": {
        "type": "str",
        "default": "sample_index cycle covering all four quadrants",
        "valid": "|".join(QUADRANTS),
    },
    "row_gap": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "col_gap": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "motif_color": {
        "type": "color",
        "default": "scheduled 1..8",
        "valid": "1..8",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_scheduled(ctx, name: str, domain: Iterable[Any], scheduled: Any, overrides: dict[str, Any]):
    options = tuple(domain)
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _flip_lr(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in mask)


def _flip_ud(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(reversed(mask))


def _rotate_180(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return _flip_ud(_flip_lr(mask))


@lru_cache(maxsize=None)
def _candidate_masks(height: int, width: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate small connected bbox-filling masks with visible reflections."""
    candidates: list[tuple[tuple[int, int], ...]] = []
    area = height * width
    for bits in range(1, 1 << area):
        count = bits.bit_count()
        if not (3 <= count <= min(6, area - 1)):
            continue
        cells = {
            (index // width, index % width)
            for index in range(area)
            if bits & (1 << index)
        }
        if not _connected(cells):
            continue
        rows = {row for row, _ in cells}
        cols = {col for _, col in cells}
        if min(rows) != 0 or max(rows) != height - 1:
            continue
        if min(cols) != 0 or max(cols) != width - 1:
            continue
        mask = tuple(
            tuple(1 if (row, col) in cells else 0 for col in range(width))
            for row in range(height)
        )
        # Ordinary draws must make both axis reflections observable.  We also
        # avoid 180-symmetric masks even though one canonical training motif is
        # 180-symmetric; self_check remains broad enough to accept that source.
        if mask in {_flip_lr(mask), _flip_ud(mask), _rotate_180(mask)}:
            continue
        candidates.append(tuple(sorted(cells)))
    if not candidates:
        raise RuntimeError(f"no lawful motif masks for {height}x{width}")
    return tuple(sorted(candidates, key=lambda cells: (len(cells), cells)))


def _scheduled_grid_size(seed: int, sample_index: int, band: str) -> int:
    cycles = {
        "easy": (13, 15),
        "medium": (13, 15, 17, 15),
        "hard": (13, 15, 17, 19),
    }
    cycle = cycles[band]
    return cycle[(seed + sample_index) % len(cycle)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic source-quadrant reflection lesson input."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    grid_size = _draw_scheduled(
        ctx,
        "grid_size",
        GRID_SIZES,
        _scheduled_grid_size(seed, sample_index, band),
        overrides,
    )
    quadrant = _draw_scheduled(
        ctx,
        "quadrant",
        QUADRANTS,
        QUADRANTS[sample_index % len(QUADRANTS)],
        overrides,
    )
    dim_index = (seed + sample_index) % len(MOTIF_DIMS)
    scheduled_h, scheduled_w = MOTIF_DIMS[dim_index]
    motif_h = _draw_scheduled(ctx, "motif_h", (2, 3), scheduled_h, overrides)
    motif_w = _draw_scheduled(ctx, "motif_w", (2, 3), scheduled_w, overrides)
    row_gap = _draw_scheduled(
        ctx, "row_gap", (1, 2), 1 + ((seed + sample_index) % 2), overrides
    )
    col_gap = _draw_scheduled(
        ctx, "col_gap", (1, 2), 1 + ((seed + sample_index // 2) % 2), overrides
    )
    motif_color = _draw_scheduled(
        ctx,
        "motif_color",
        MOTIF_COLORS,
        MOTIF_COLORS[(seed + sample_index) % len(MOTIF_COLORS)],
        overrides,
    )

    anchor_row = anchor_col = grid_size // 2
    if quadrant.startswith("north"):
        top = anchor_row - row_gap - motif_h
    else:
        top = anchor_row + row_gap + 1
    if quadrant.endswith("west"):
        left = anchor_col - col_gap - motif_w
    else:
        left = anchor_col + col_gap + 1

    masks = _candidate_masks(motif_h, motif_w)
    motif_cells = ctx.draw_rng("motif_shape").choice(masks)

    grid = full_grid(grid_size, grid_size, 0)
    grid[anchor_row][anchor_col] = 9
    for row, col in motif_cells:
        grid[top + row][left + col] = motif_color
    return grid


def _grid_validation(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return height, width, ["grid must be rectangular"]
    if height != width:
        errors.append("grid must be square")
    if height not in GRID_SIZES:
        errors.append(f"grid size must be one of {GRID_SIZES}, got {height}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    return height, width, errors


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    height, width, errors = _grid_validation(grid)
    info: dict[str, Any] = {"grid_size": height}
    if errors:
        return info, errors

    anchors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, got {len(anchors)}")
        return info, errors
    anchor = anchors[0]
    expected_anchor = (height // 2, width // 2)
    if anchor != expected_anchor:
        errors.append(f"anchor must be centered at {expected_anchor}, got {anchor}")

    motif_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]
    if not motif_cells:
        errors.append("missing non-anchor motif")
        return info, errors
    colors = {grid[row][col] for row, col in motif_cells}
    if len(colors) != 1:
        errors.append(f"motif must use exactly one color, got {sorted(colors)}")
    motif_color = min(colors)
    if not 1 <= motif_color <= 8:
        errors.append(f"motif color must be 1..8, got {motif_color}")

    cell_set = set(motif_cells)
    if not _connected(cell_set):
        errors.append("motif must be one 4-connected component")

    r0 = min(row for row, _ in motif_cells)
    c0 = min(col for _, col in motif_cells)
    r1 = max(row for row, _ in motif_cells)
    c1 = max(col for _, col in motif_cells)
    motif_h = r1 - r0 + 1
    motif_w = c1 - c0 + 1
    if not 2 <= motif_h <= 3:
        errors.append(f"motif height must be 2..3, got {motif_h}")
    if not 2 <= motif_w <= 3:
        errors.append(f"motif width must be 2..3, got {motif_w}")
    if not 3 <= len(motif_cells) <= 6:
        errors.append(f"motif must contain 3..6 cells, got {len(motif_cells)}")

    anchor_row, anchor_col = anchor
    if r1 < anchor_row and c1 < anchor_col:
        quadrant = "northwest"
        row_gap = anchor_row - r1 - 1
        col_gap = anchor_col - c1 - 1
    elif r1 < anchor_row and c0 > anchor_col:
        quadrant = "northeast"
        row_gap = anchor_row - r1 - 1
        col_gap = c0 - anchor_col - 1
    elif r0 > anchor_row and c1 < anchor_col:
        quadrant = "southwest"
        row_gap = r0 - anchor_row - 1
        col_gap = anchor_col - c1 - 1
    elif r0 > anchor_row and c0 > anchor_col:
        quadrant = "southeast"
        row_gap = r0 - anchor_row - 1
        col_gap = c0 - anchor_col - 1
    else:
        quadrant = "invalid"
        row_gap = col_gap = -1
        errors.append("motif bbox must lie wholly in one anchor quadrant")
    if quadrant != "invalid":
        if not 1 <= row_gap <= 2:
            errors.append(f"row gap must be 1..2, got {row_gap}")
        if not 1 <= col_gap <= 2:
            errors.append(f"column gap must be 1..2, got {col_gap}")

    mask = tuple(
        tuple(1 if (r0 + row, c0 + col) in cell_set else 0 for col in range(motif_w))
        for row in range(motif_h)
    )
    if mask == _flip_lr(mask):
        errors.append("motif must be horizontally asymmetric")
    if mask == _flip_ud(mask):
        errors.append("motif must be vertically asymmetric")

    reflected_left = 2 * anchor_col - c0 - motif_w + 1
    reflected_top = 2 * anchor_row - r0 - motif_h + 1
    placements = (
        (r0, c0),
        (r0, reflected_left),
        (reflected_top, c0),
        (reflected_top, reflected_left),
    )
    for top, left in placements:
        if not (0 <= top <= height - motif_h and 0 <= left <= width - motif_w):
            errors.append(f"reflected motif placement {(top, left)} leaves the grid")
            break

    info.update(
        {
            "height": height,
            "width": width,
            "anchor": anchor,
            "bbox": (r0, c0, r1, c1),
            "crop": tuple(
                tuple(grid[r0 + row][c0 + col] for col in range(motif_w))
                for row in range(motif_h)
            ),
            "mask": mask,
            "motif_cells": tuple(sorted(motif_cells)),
            "motif_h": motif_h,
            "motif_w": motif_w,
            "quadrant": quadrant,
            "row_gap": row_gap,
            "col_gap": col_gap,
            "motif_color": motif_color,
            "reflected_top": reflected_top,
            "reflected_left": reflected_left,
            "placements": placements,
        }
    )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def _requested_axes(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    requested = {name: meta[name] for name in AXES if name in meta}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        requested.update({name: nested[name] for name in AXES if name in nested})
    return requested


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding source-quadrant scenes."""
    info, errors = _analyze(grid)
    if errors:
        return errors
    for name, requested in _requested_axes(meta).items():
        if requested is not None and info[name] != requested:
            errors.append(f"{name} requested {requested!r}, observed {info[name]!r}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The task-linked lawful manifold; all ordinary draws are strict."""
    return _analyze(grid)[1]


def _paste_nonzero(out: list[list[int]], crop: Iterable[Iterable[int]], top: int, left: int) -> None:
    for row, values in enumerate(crop):
        for col, value in enumerate(values):
            if value:
                out[top + row][left + col] = value


def _crop_flip_lr(crop: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in crop)


def _crop_flip_ud(crop: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(reversed(crop))


def _crop_rotate_180(crop: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return _crop_flip_ud(_crop_flip_lr(crop))


def _fourway_from_crop(
    size: int,
    anchor: tuple[int, int],
    crop: tuple[tuple[int, ...], ...],
    top: int,
    left: int,
) -> list[list[int]]:
    height, width = len(crop), len(crop[0])
    reflected_left = 2 * anchor[1] - left - width + 1
    reflected_top = 2 * anchor[0] - top - height + 1
    out = full_grid(size, size, 0)
    _paste_nonzero(out, crop, top, left)
    _paste_nonzero(out, _crop_flip_lr(crop), top, reflected_left)
    _paste_nonzero(out, _crop_flip_ud(crop), reflected_top, left)
    _paste_nonzero(out, _crop_rotate_180(crop), reflected_top, reflected_left)
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python parity mirror for tests; Racket remains output authority."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, _r1, _c1 = info["bbox"]
    return _fourway_from_crop(
        info["grid_size"], info["anchor"], info["crop"], r0, c0
    )


def canonical_profile_signature(grid: Any):
    info, errors = _analyze(grid)
    if errors:
        return None
    return (info["grid_size"], info["grid_size"], 3)


def semantic_signature(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        **observe_overrides(grid),
        "motif_cells": len(info["motif_cells"]),
        "mask": info["mask"],
        "strict_canonical_like": True,
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    del seed, difficulty
    return QUADRANTS[sample_index % len(QUADRANTS)]


SCHEDULE_PROFILES = QUADRANTS


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid: Any) -> bool:
        info, errors = _analyze(grid)
        return not errors and bool(predicate(info))

    return wrapped


SEMANTIC_WITNESSES = {
    "source_northwest": _witness(lambda info: info["quadrant"] == "northwest"),
    "source_northeast": _witness(lambda info: info["quadrant"] == "northeast"),
    "source_southwest": _witness(lambda info: info["quadrant"] == "southwest"),
    "source_southeast": _witness(lambda info: info["quadrant"] == "southeast"),
    "square_motif_bbox": _witness(lambda info: info["motif_h"] == info["motif_w"]),
    "non_square_motif_bbox": _witness(lambda info: info["motif_h"] != info["motif_w"]),
    "row_gap_one": _witness(lambda info: info["row_gap"] == 1),
    "row_gap_two": _witness(lambda info: info["row_gap"] == 2),
    "col_gap_one": _witness(lambda info: info["col_gap"] == 1),
    "col_gap_two": _witness(lambda info: info["col_gap"] == 2),
}


def _rival_identity_input(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_preserve_anchor(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = rule_mirror(grid)
    row, col = info["anchor"]
    out[row][col] = 9
    return out


def _rival_unflipped_four_copies(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_size"], info["grid_size"], 0)
    for top, left in info["placements"]:
        _paste_nonzero(out, info["crop"], top, left)
    return out


def _rival_horizontal_pair_only(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, _r1, _c1 = info["bbox"]
    out = full_grid(info["grid_size"], info["grid_size"], 0)
    _paste_nonzero(out, info["crop"], r0, c0)
    _paste_nonzero(out, _crop_flip_lr(info["crop"]), r0, info["reflected_left"])
    return out


def _rival_assume_original_is_northwest(grid: Any) -> list[list[int]]:
    """Canonical-fitting shortcut: reinterpret every source as northwest."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    anchor_row, anchor_col = info["anchor"]
    top = anchor_row - info["row_gap"] - info["motif_h"]
    left = anchor_col - info["col_gap"] - info["motif_w"]
    return _fourway_from_crop(
        info["grid_size"], info["anchor"], info["crop"], top, left
    )


SEMANTIC_RIVALS = {
    "identity_input": _rival_identity_input,
    "preserve_anchor": _rival_preserve_anchor,
    "unflipped_four_copies": _rival_unflipped_four_copies,
    "horizontal_pair_only": _rival_horizontal_pair_only,
    "assume_original_is_northwest": _rival_assume_original_is_northwest,
}

_BASE_RIVAL_CLAIMS = [
    "identity_input",
    "preserve_anchor",
    "unflipped_four_copies",
    "horizontal_pair_only",
]
WITNESS_RIVALS = {
    name: list(_BASE_RIVAL_CLAIMS) for name in SEMANTIC_WITNESSES
}
for _name in ("source_northeast", "source_southwest", "source_southeast"):
    WITNESS_RIVALS[_name].append("assume_original_is_northwest")

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "assume_original_is_northwest": _rival_assume_original_is_northwest,
}


def _pair_errors(pair: Any, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    info, errors = _analyze(pair["input"])
    if errors:
        return None, [f"{label}: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return None, [f"{label} output is not the four-way reflected arrangement"]
    return info, []


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that refute the plausible source-task shortcuts."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        info, pair_reasons = _pair_errors(pair, f"demo {index}")
        reasons.extend(pair_reasons)
        if info is not None:
            analyses.append(info)
    query_info, query_reasons = _pair_errors(query, "query")
    reasons.extend(query_reasons)
    if reasons:
        return reasons

    quadrants = {info["quadrant"] for info in analyses}
    if quadrants != set(QUADRANTS):
        reasons.append(f"demonstrations do not cover all source quadrants: {sorted(quadrants)}")
    dimensions = {(info["motif_h"], info["motif_w"]) for info in analyses}
    if dimensions != set(MOTIF_DIMS):
        reasons.append(f"demonstrations do not cover all motif bbox branches: {sorted(dimensions)}")
    if len({info["grid_size"] for info in analyses}) < 2:
        reasons.append("demonstrations use fewer than two grid sizes")
    if len({info["motif_color"] for info in analyses}) < 4:
        reasons.append("demonstrations use fewer than four motif colors")
    if {info["row_gap"] for info in analyses} != {1, 2}:
        reasons.append("demonstrations do not cover both row gaps")
    if {info["col_gap"] for info in analyses} != {1, 2}:
        reasons.append("demonstrations do not cover both column gaps")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")

    if query_info is None:  # defensive; query errors returned above
        reasons.append("query analysis unavailable")
    return reasons
