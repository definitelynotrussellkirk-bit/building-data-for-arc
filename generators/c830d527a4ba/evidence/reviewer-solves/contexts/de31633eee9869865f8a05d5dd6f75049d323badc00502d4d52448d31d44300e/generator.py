"""Generator for ``c830d527a4ba`` — transform-code mosaic decoding.

A color-1 source template and a separate code grid are embedded in the input.
Each code color selects both a transform and the output color: 2 keeps the
source unchanged, 3 rotates it 90 degrees clockwise, 4 rotates it 180 degrees,
and 5 flips it left-to-right.  Code-grid cells are replaced by the transformed,
recolored tiles; tiles and tile rows are centered with one-cell gaps.

The four-profile schedule deliberately varies which side contains the source
and whether the code bbox has a zero gap.  Every three consecutive examples
therefore refute the canonical-only shortcuts "the source is always left" and
"the code grid is always dense", while every ordinary example distinguishes
the four transform codes with an asymmetric source shape.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c830d527a4ba"
TASK_ID = "c830d527a4ba"
VERSION = "3.0.0"
RULE_HASH = "0b137f4534ae"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Extract the color-1 template. Replace each code-grid cell by a recolored "
    "template transform: 2 = identity, 3 = 90° clockwise, 4 = 180°, and "
    "5 = horizontal flip; preserve zero code gaps and center tiles with "
    "one-cell spacing."
)

INVARIANTS = [
    "all nonzero cells belong to one color-1 template or a {2,3,4,5} code bbox",
    "the template and code bboxes are horizontally separated by background",
    "the template is 4-connected and cropped to a 2x2..3x3 bbox",
    "ordinary draws contain all four transform codes and an asymmetric template",
]

SCHEDULE_PROFILES = (
    "canonical_left",
    "canonical_right",
    "gapped_left",
    "gapped_right",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6 (canonical anchor; exact override supported)",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "9 (canonical anchor; exact override supported)",
        "valid": "8..14",
    },
    "template_h": {
        "type": "int",
        "default": "difficulty-shaped 2..3",
        "valid": "2..3",
    },
    "template_w": {
        "type": "int",
        "default": "difficulty-shaped 2..3",
        "valid": "2..3",
    },
    "code_h": {
        "type": "int",
        "default": "3",
        "valid": "2..3",
    },
    "code_w": {
        "type": "int",
        "default": "3",
        "valid": "2..3",
    },
    "template_side": {
        "type": "str",
        "default": "scheduled left/right",
        "valid": "left|right",
    },
}

# Every legal cross-product fits even on the minimum 6x8 canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CODES = (2, 3, 4, 5)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_exact_or_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Pin a scheduled default while retaining every declared exact override."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _choice_exact_or_default(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _default_template_dims(profile: str, difficulty: str | None) -> tuple[int, int]:
    band = difficulty or "medium"
    if band == "easy":
        return (2, 3) if profile in ("canonical_left", "gapped_left") else (3, 2)
    if band == "hard":
        return 3, 3
    return (3, 2) if profile in ("canonical_left", "gapped_right") else (2, 3)


def _normalize(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _connected(cells: tuple[tuple[int, int], ...]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for dr, dc in _CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return seen == remaining


def _shape_rot_cw(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize([(col, -row) for row, col in cells])


def _shape_rot_180(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize([(-row, -col) for row, col in cells])


def _shape_flip_lr(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize([(row, -col) for row, col in cells])


@lru_cache(maxsize=None)
def _template_catalog(height: int, width: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All small connected bbox-filling shapes that distinguish codes 2..5."""
    shapes: list[tuple[tuple[int, int], ...]] = []
    for bits in product((0, 1), repeat=height * width):
        cells = tuple(
            divmod(index, width)
            for index, occupied in enumerate(bits)
            if occupied
        )
        if len(cells) < 3 or not _connected(cells):
            continue
        if min(row for row, _ in cells) != 0 or max(row for row, _ in cells) != height - 1:
            continue
        if min(col for _, col in cells) != 0 or max(col for _, col in cells) != width - 1:
            continue
        images = {
            _normalize(cells),
            _shape_rot_cw(cells),
            _shape_rot_180(cells),
            _shape_flip_lr(cells),
        }
        if len(images) == 4:
            shapes.append(tuple(sorted(cells)))
    if not shapes:
        raise ValueError(f"no asymmetric connected template for {height}x{width}")
    return tuple(shapes)


def _build_code_grid(height: int, width: int, *, gapped: bool, rng) -> list[list[int]]:
    area = height * width
    if area < len(_CODES):
        raise ValueError("code grid must have room for all four transform codes")

    values = list(_CODES)
    while len(values) < area:
        values.append(_CODES[(len(values) + rng.randrange(4)) % 4])
    rng.shuffle(values)

    grid = [values[row * width : (row + 1) * width] for row in range(height)]
    if gapped and area >= 5:
        # Prefer a true interior hole when 3x3; otherwise choose a cell whose
        # removal cannot collapse any edge of the code bbox.
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if any(r != row for r in range(height) for c in range(width) if grid[r][c] != 0)
            and any(c != col for r in range(height) for c in range(width) if grid[r][c] != 0)
        ]
        center = (height // 2, width // 2)
        candidates.sort(key=lambda p: (p != center, abs(p[0] - center[0]) + abs(p[1] - center[1]), p))
        for row, col in candidates:
            trial = [line[:] for line in grid]
            trial[row][col] = 0
            flat = {value for line in trial for value in line}
            if set(_CODES) <= flat and _bbox_of_nonzero(trial) == (0, 0, height - 1, width - 1):
                grid = trial
                break
    return grid


def _bbox(cells: list[tuple[int, int]] | list[tuple[int, int, int]]) -> tuple[int, int, int, int]:
    return (
        min(cell[0] for cell in cells),
        min(cell[1] for cell in cells),
        max(cell[0] for cell in cells),
        max(cell[1] for cell in cells),
    )


def _bbox_of_nonzero(grid: list[list[int]]) -> tuple[int, int, int, int] | None:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    return _bbox(cells) if cells else None


def _layout_positions(
    *,
    height: int,
    width: int,
    template_h: int,
    template_w: int,
    code_h: int,
    code_w: int,
    template_side: str,
    profile: str,
    rng,
) -> tuple[tuple[int, int], tuple[int, int]]:
    slack = width - template_w - code_w
    if slack < 1:
        raise ValueError("canvas too narrow to separate template and code")

    canonical = profile.startswith("canonical_")
    if canonical:
        gap = min(3, slack)
        total_width = template_w + code_w + gap
        block_left = 0 if template_side == "left" else width - total_width
        code_top = 0
        template_top = rng.randrange(height - template_h + 1)
    else:
        gap = 1 + rng.randrange(min(3, slack))
        total_width = template_w + code_w + gap
        block_left = rng.randrange(width - total_width + 1)
        template_top = rng.randrange(height - template_h + 1)
        code_top = rng.randrange(height - code_h + 1)

    if template_side == "left":
        template_left = block_left
        code_left = block_left + template_w + gap
    else:
        code_left = block_left
        template_left = block_left + code_w + gap
    return (template_top, template_left), (code_top, code_left)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")

    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_th, default_tw = _default_template_dims(profile, difficulty)
    height = _draw_exact_or_default(ctx, "grid_h", 6, 12, 6)
    default_width = 8 if profile.startswith("gapped_") else 9
    width = _draw_exact_or_default(ctx, "grid_w", 8, 14, default_width)
    template_h = _draw_exact_or_default(ctx, "template_h", 2, 3, default_th)
    template_w = _draw_exact_or_default(ctx, "template_w", 2, 3, default_tw)
    code_h = _draw_exact_or_default(ctx, "code_h", 2, 3, 3)
    code_w = _draw_exact_or_default(ctx, "code_w", 2, 3, 3)
    scheduled_side = "left" if profile.endswith("left") else "right"
    template_side = _choice_exact_or_default(
        ctx, "template_side", ("left", "right"), scheduled_side
    )

    shape_rng = ctx.draw_rng("template_shape")
    template_shape = shape_rng.choice(_template_catalog(template_h, template_w))
    code_rng = ctx.draw_rng("code_values")
    code_grid = _build_code_grid(
        code_h,
        code_w,
        gapped=profile.startswith("gapped_"),
        rng=code_rng,
    )
    layout_rng = ctx.draw_rng("layout")
    template_origin, code_origin = _layout_positions(
        height=height,
        width=width,
        template_h=template_h,
        template_w=template_w,
        code_h=code_h,
        code_w=code_w,
        template_side=template_side,
        profile=profile,
        rng=layout_rng,
    )

    grid = full_grid(height, width, 0)
    tr, tc = template_origin
    for dr, dc in template_shape:
        grid[tr + dr][tc + dc] = 1
    cr, cc = code_origin
    for row in range(code_h):
        for col in range(code_w):
            grid[cr + row][cc + col] = code_grid[row][col]
    return grid


def _facts_or_raise(grid) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value not in range(6)
        for row in grid
        for value in row
    ):
        raise ValueError("grid palette must be integer colors 0..5")

    height = len(grid)
    template_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    code_cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in _CODES
    ]
    if not template_cells:
        raise ValueError("missing color-1 template")
    if not code_cells:
        raise ValueError("missing code colors 2..5")
    if not _connected(tuple(template_cells)):
        raise ValueError("color-1 template must be one 4-connected component")

    template_bbox = _bbox(template_cells)
    code_bbox = _bbox(code_cells)
    ttop, tleft, tbottom, tright = template_bbox
    ctop, cleft, cbottom, cright = code_bbox
    template_h = tbottom - ttop + 1
    template_w = tright - tleft + 1
    code_h = cbottom - ctop + 1
    code_w = cright - cleft + 1
    if not (2 <= template_h <= 3 and 2 <= template_w <= 3):
        raise ValueError("template bbox must be 2x2 through 3x3")
    if not (2 <= code_h <= 3 and 2 <= code_w <= 3):
        raise ValueError("code bbox must be 2x2 through 3x3")

    if tright + 1 < cleft:
        template_side = "left"
        gap = cleft - tright - 1
    elif cright + 1 < tleft:
        template_side = "right"
        gap = tleft - cright - 1
    else:
        raise ValueError("template and code bboxes must be horizontally separated")
    if gap < 1:
        raise ValueError("template and code need at least one background column")

    source = [
        [1 if grid[row][col] == 1 else 0 for col in range(tleft, tright + 1)]
        for row in range(ttop, tbottom + 1)
    ]
    code_grid = [
        [
            grid[row][col] if grid[row][col] in _CODES else 0
            for col in range(cleft, cright + 1)
        ]
        for row in range(ctop, cbottom + 1)
    ]
    template_shape = tuple(
        sorted((row - ttop, col - tleft) for row, col in template_cells)
    )
    return {
        "height": height,
        "width": width,
        "template_cells": template_cells,
        "code_cells": code_cells,
        "template_bbox": template_bbox,
        "code_bbox": code_bbox,
        "template_h": template_h,
        "template_w": template_w,
        "code_h": code_h,
        "code_w": code_w,
        "template_side": template_side,
        "template_shape": template_shape,
        "source": source,
        "code_grid": code_grid,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    reasons: list[str] = []
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, requested in meta["overrides"].items():
            if name in observed and observed[name] != requested:
                reasons.append(f"override {name!r} requested {requested!r}, observed {observed[name]!r}")
    # Keep `facts` live so malformed parser changes cannot silently bypass the
    # validation above under static simplification.
    if not facts["source"] or not facts["code_grid"]:
        reasons.append("missing parsed template or code grid")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = _facts_or_raise(grid)
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "template_h": facts["template_h"],
        "template_w": facts["template_w"],
        "code_h": facts["code_h"],
        "code_w": facts["code_w"],
        "template_side": facts["template_side"],
    }


def _rot_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rot_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _recolor(grid: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value != 0 else 0 for value in row] for row in grid]


def _hstack_center(grids: list[list[list[int]]], gap: int = 1) -> list[list[int]]:
    if not grids:
        return [[]]
    height = max(len(grid) for grid in grids)
    width = sum(len(grid[0]) for grid in grids) + gap * (len(grids) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for grid in grids:
        top = (height - len(grid)) // 2
        for row, line in enumerate(grid):
            for col, value in enumerate(line):
                if value != 0:
                    out[top + row][left + col] = value
        left += len(grid[0]) + gap
    return out


def _vstack_center(grids: list[list[list[int]]], gap: int = 1) -> list[list[int]]:
    if not grids:
        return [[]]
    width = max(len(grid[0]) for grid in grids)
    height = sum(len(grid) for grid in grids) + gap * (len(grids) - 1)
    out = full_grid(height, width, 0)
    top = 0
    for grid in grids:
        left = (width - len(grid[0])) // 2
        for row, line in enumerate(grid):
            for col, value in enumerate(line):
                if value != 0:
                    out[top + row][left + col] = value
        top += len(grid) + gap
    return out


def _assemble(source: list[list[int]], code_grid: list[list[int]], mapping: dict[int, str]) -> list[list[int]]:
    rows: list[list[list[int]]] = []
    for code_row in code_grid:
        pieces: list[list[list[int]]] = []
        for code in code_row:
            if code == 0:
                piece = full_grid(len(source), len(source[0]), 0)
            else:
                mode = mapping[code]
                if mode == "identity":
                    transformed = [line[:] for line in source]
                elif mode == "rot_cw":
                    transformed = _rot_cw(source)
                elif mode == "rot_180":
                    transformed = _rot_180(source)
                elif mode == "flip_lr":
                    transformed = _flip_lr(source)
                else:  # defensive: only internal fixed mappings reach here
                    raise ValueError(f"unknown transform mode {mode!r}")
                piece = _recolor(transformed, code)
            pieces.append(piece)
        rows.append(_hstack_center(pieces, 1))
    return _vstack_center(rows, 1)


_TRUE_MAPPING = {2: "identity", 3: "rot_cw", 4: "rot_180", 5: "flip_lr"}


def rule_mirror(grid):
    """Pure Python mirror of the selected canonical Racket authority."""
    facts = _facts_or_raise(grid)
    return _assemble(facts["source"], facts["code_grid"], _TRUE_MAPPING)


def _no_transforms(grid):
    facts = _facts_or_raise(grid)
    return _assemble(
        facts["source"],
        facts["code_grid"],
        {2: "identity", 3: "identity", 4: "identity", 5: "identity"},
    )


def _swap_green_gray(grid):
    facts = _facts_or_raise(grid)
    return _assemble(
        facts["source"],
        facts["code_grid"],
        {2: "identity", 3: "flip_lr", 4: "rot_180", 5: "rot_cw"},
    )


def _template_must_be_left(grid):
    facts = _facts_or_raise(grid)
    if facts["template_side"] == "left":
        return rule_mirror(grid)
    return [list(row) for row in grid]


def _drop_code_gaps(grid):
    facts = _facts_or_raise(grid)
    compressed = [[value for value in row if value != 0] for row in facts["code_grid"]]
    compressed = [row for row in compressed if row]
    if not compressed:
        return [[0]]
    return _assemble(facts["source"], compressed, _TRUE_MAPPING)


def _has_code_gap(grid) -> bool:
    try:
        code_grid = _facts_or_raise(grid)["code_grid"]
    except (TypeError, ValueError):
        return False
    return any(value == 0 for row in code_grid for value in row)


def strict_canonical_like(grid) -> list[str]:
    try:
        facts = _facts_or_raise(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    reasons: list[str] = []
    palette_size = len({value for row in grid for value in row})
    if (facts["height"], facts["width"], palette_size) not in {
        (6, 8, 5),
        (6, 9, 5),
        (6, 9, 6),
    }:
        reasons.append("canonical inputs use profile 6x8/5 or 6x9/5..6")
    if facts["template_side"] != "left":
        reasons.append("canonical inputs place the template left of the code")
    if _has_code_gap(grid):
        reasons.append("canonical code bboxes are dense")
    return reasons


def _transform_lookup_discriminator(grid) -> bool:
    try:
        truth = rule_mirror(grid)
        return _no_transforms(grid) != truth and _swap_green_gray(grid) != truth
    except (TypeError, ValueError):
        return False


def _template_side_discriminator(grid) -> bool:
    try:
        return (
            _facts_or_raise(grid)["template_side"] == "right"
            and _template_must_be_left(grid) != rule_mirror(grid)
        )
    except (TypeError, ValueError):
        return False


def _code_gap_discriminator(grid) -> bool:
    try:
        return _has_code_gap(grid) and _drop_code_gaps(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "transform_lookup_discriminator": _transform_lookup_discriminator,
    "template_side_discriminator": _template_side_discriminator,
    "code_gap_discriminator": _code_gap_discriminator,
}

SEMANTIC_RIVALS = {
    "recolor_without_transforms": _no_transforms,
    "swap_green_gray_transforms": _swap_green_gray,
    "template_must_be_left": _template_must_be_left,
    "drop_code_gaps": _drop_code_gaps,
}

WITNESS_RIVALS = {
    "transform_lookup_discriminator": [
        "recolor_without_transforms",
        "swap_green_gray_transforms",
    ],
    "template_side_discriminator": ["template_must_be_left"],
    "code_gap_discriminator": ["drop_code_gaps"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "template_must_be_left": _template_must_be_left,
    "drop_code_gaps": _drop_code_gaps,
}
MIN_STRICT_FRAC = 0.25


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    episodes = [*demos, query]
    reasons: list[str] = []
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the transform-code rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query_truth:
                reasons.append(f"demos do not falsify shortcut {name!r}")
    return reasons
