"""Generator for bank task M114 / d552baa9e49e.

The top-left cell is a command.  Clear that cell, tightly crop every remaining
nonzero cell, and transform the crop:

    1 -> rotate clockwise
    2 -> rotate 180 degrees
    3 -> transpose
    4 -> reflect left/right
    5 -> reflect up/down

Normal generated motifs are deliberately transform-disambiguating: all five
command outputs differ and none is the untransformed crop.  One quarter of the
default stream stays on the demonstrated 8x9 / 3x3 / two-color morphology;
the rest broadens canvas, crop, color-count, topology, placement, and palette.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d552baa9e49e"
TASK_ID = "d552baa9e49e"
VERSION = "2.0.0"
RULE_HASH = "21cd1730c540"

SUMMARY = (
    "Read command 1..5 from (0,0), clear that command cell, tightly crop all "
    "remaining nonzero content, then apply clockwise rotation, 180-degree "
    "rotation, transpose, left/right reflection, or up/down reflection "
    "respectively. The output is the transformed crop, never the full canvas."
)

# Three demonstrations identify three command meanings; the fourth generated
# pair repeats one demonstrated command on a different asymmetric motif.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the command at (0,0) is one of 1,2,3,4,5",
    "all non-command content lies strictly inside the canvas",
    "the cropped motif has 2..4 colors and never reuses the command color",
    "canonical inputs may be disconnected; crop-to-content consumes all nonzero cells",
    "normal generated motifs make all five command transforms distinguishable",
]

MOTIF_PROFILES = ("canonical_morphology", "generalized_morphology")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8 on canonical-morphology draws; difficulty-skewed 8..15 otherwise",
        "valid": "8..15",
    },
    "grid_w": {
        "type": "int",
        "default": "9 on canonical-morphology draws; difficulty-skewed 9..16 otherwise",
        "valid": "9..16",
    },
    "cmd": {
        "type": "int",
        "default": "four-pair pedagogical schedule over 1..5",
        "valid": "1..5",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "2 on canonical morphology; scheduled 2..4 otherwise",
        "valid": "2..4",
    },
    "motif_profile": {
        "type": "str",
        "default": "canonical_morphology every fourth sample; generalized otherwise",
        "valid": "canonical_morphology|generalized_morphology",
    },
}

# Occupancy masks derived from every canonical train/test input.  The focused
# regression test re-derives this set from data/canonical/puzzles.jsonl.
_CANONICAL_MASKS = (
    (
        (1, 1, 0),
        (1, 0, 1),
        (1, 1, 1),
    ),
    (
        (1, 1, 0),
        (1, 1, 0),
        (1, 0, 1),
    ),
    (
        (1, 0, 1),
        (0, 1, 0),
        (1, 1, 0),
    ),
)

# Each aligned four-pair lesson has three distinct demo commands and a query
# command that repeats demo zero.  Across five blocks every command appears.
_COMMAND_BLOCKS = (
    (1, 2, 3, 1),
    (4, 5, 2, 4),
    (3, 5, 1, 3),
    (2, 4, 5, 2),
    (1, 5, 4, 1),
)

_GENERALIZED_DIMS = {
    "easy": ((3, 3), (3, 4), (4, 3)),
    "medium": ((3, 4), (4, 3), (4, 4), (3, 5), (5, 3)),
    "hard": ((4, 5), (5, 4), (5, 5), (3, 5), (5, 3)),
}


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [row[:] for row in reversed(grid)]


def _apply_transform(grid, cmd):
    if cmd == 1:
        return _rotate_cw(grid)
    if cmd == 2:
        return _rotate_180(grid)
    if cmd == 3:
        return _transpose(grid)
    if cmd == 4:
        return _flip_lr(grid)
    if cmd == 5:
        return _flip_ud(grid)
    raise ValueError(f"unsupported command: {cmd!r}")


def _mask_from_crop(crop):
    return tuple(tuple(int(value != 0) for value in row) for row in crop)


def _rotate_mask(mask):
    return tuple(tuple(row) for row in zip(*mask[::-1]))


def _flip_mask(mask):
    return tuple(tuple(reversed(row)) for row in mask)


def _dihedral_forms(mask):
    forms = set()
    current = tuple(tuple(row) for row in mask)
    for _ in range(4):
        forms.add(current)
        forms.add(_flip_mask(current))
        current = _rotate_mask(current)
    return tuple(sorted(forms))


def _dihedral_key(mask):
    return min(_dihedral_forms(mask))


_CANONICAL_MASK_KEYS = frozenset(_dihedral_key(mask) for mask in _CANONICAL_MASKS)


def _scheduled_command(sample_index):
    block = _COMMAND_BLOCKS[(sample_index // 4) % len(_COMMAND_BLOCKS)]
    return block[sample_index % 4]


def _default_profile(sample_index):
    return "canonical_morphology" if sample_index % 4 == 0 else "generalized_morphology"


def _default_color_count(sample_index, profile):
    if profile == "canonical_morphology":
        return 2
    return 2 + (sample_index % 3)


def _band_name(difficulty):
    if difficulty in _GENERALIZED_DIMS:
        return difficulty
    return "medium"


def _pick_exact_axis(ctx, overrides, label, default, lo=None, hi=None, options=None):
    if label in overrides and overrides[label] is not None:
        if options is not None:
            return ctx.draw_choice(label, options)
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _component_sizes(mask):
    cells = {
        (row, col)
        for row, values in enumerate(mask)
        for col, value in enumerate(values)
        if value
    }
    sizes = []
    while cells:
        start = min(cells)
        cells.remove(start)
        queue = deque([start])
        size = 0
        while queue:
            row, col = queue.popleft()
            size += 1
            for candidate in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if candidate in cells:
                    cells.remove(candidate)
                    queue.append(candidate)
        sizes.append(size)
    return tuple(sorted(sizes))


def _coerce_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None, ["grid rows must be nonempty sequences"]
    width = len(first)
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within ARC's 1..30 range")
    converted = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _crop_content(grid):
    cells = [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0 and (row, col) != (0, 0)
    ]
    if not cells:
        return [], (), None
    row0 = min(row for row, _col, _value in cells)
    row1 = max(row for row, _col, _value in cells)
    col0 = min(col for _row, col, _value in cells)
    col1 = max(col for _row, col, _value in cells)
    crop = [
        [0 for _col in range(col0, col1 + 1)]
        for _row in range(row0, row1 + 1)
    ]
    for row, col, value in cells:
        crop[row - row0][col - col0] = value
    return crop, tuple(cells), (row0, row1, col0, col1)


def _analyze_grid(grid, *, require_teaching):
    normalized, errors = _coerce_grid(grid)
    if errors:
        return None, errors
    height, width = len(normalized), len(normalized[0])
    if not 8 <= height <= 15:
        errors.append("grid height must be in 8..15")
    if not 9 <= width <= 16:
        errors.append("grid width must be in 9..16")

    cmd = normalized[0][0]
    if cmd not in {1, 2, 3, 4, 5}:
        errors.append("cmd at (0,0) must be in 1..5")

    crop, cells, bbox = _crop_content(normalized)
    if not cells:
        errors.append("no nonzero motif cells outside the command")
        return None, errors

    row0, row1, col0, col1 = bbox
    if row0 < 2 or col0 < 2 or row1 > height - 2 or col1 > width - 2:
        errors.append("motif must lie strictly inside the canvas and away from the command row/column")

    crop_h, crop_w = len(crop), len(crop[0])
    if not (3 <= crop_h <= 5 and 3 <= crop_w <= 5):
        errors.append("cropped motif dimensions must each be in 3..5")
    if len(cells) < 5:
        errors.append("motif must contain at least five occupied cells")

    colors = {value for _row, _col, value in cells}
    if not 2 <= len(colors) <= 4:
        errors.append("motif must contain 2..4 distinct colors")
    if cmd in colors:
        errors.append("motif colors must not reuse the command color")

    mask = _mask_from_crop(crop)
    outputs = tuple(_freeze(_apply_transform(crop, branch)) for branch in range(1, 6))
    if require_teaching:
        if any(output == _freeze(crop) for output in outputs):
            errors.append("normal generated motif must not be invariant under any command transform")
        if len(set(outputs)) != 5:
            errors.append("normal generated motif must distinguish all five command transforms")

    profile = (
        "canonical_morphology"
        if _dihedral_key(mask) in _CANONICAL_MASK_KEYS
        else "generalized_morphology"
    )
    facts = {
        "grid_h": height,
        "grid_w": width,
        "cmd": cmd,
        "n_distinct_colors": len(colors),
        "motif_profile": profile,
        "crop": crop,
        "crop_h": crop_h,
        "crop_w": crop_w,
        "occupied_cells": len(cells),
        "component_sizes": _component_sizes(mask),
        "bbox": bbox,
        "transform_outputs": outputs,
    }
    return facts, errors


def _random_colored_crop(ctx, sample_index, profile, n_colors, cmd):
    if profile == "canonical_morphology":
        base_mask = _CANONICAL_MASKS[(sample_index // 4) % len(_CANONICAL_MASKS)]
        forms = _dihedral_forms(base_mask)
        orientation_rng = ctx.draw_rng("canonical_orientation")
        mask = forms[orientation_rng.randrange(len(forms))]
        dims = (len(mask), len(mask[0]))
    else:
        band = _band_name(ctx.difficulty)
        choices = _GENERALIZED_DIMS[band]
        dims = choices[(sample_index + (0 if band == "easy" else 1 if band == "medium" else 2)) % len(choices)]
        mask = None

    for attempt in range(256):
        rng = ctx.draw_rng(f"motif_attempt_{attempt}")
        motif_h, motif_w = dims
        if profile == "generalized_morphology":
            area = motif_h * motif_w
            mandatory = {
                (0, rng.randrange(motif_w)),
                (motif_h - 1, rng.randrange(motif_w)),
                (rng.randrange(motif_h), 0),
                (rng.randrange(motif_h), motif_w - 1),
            }
            target = rng.randint(max(5, n_colors, len(mandatory)), max(5, area - 1))
            cells = set(mandatory)
            all_cells = [(row, col) for row in range(motif_h) for col in range(motif_w)]
            rng.shuffle(all_cells)
            for candidate in all_cells:
                if len(cells) >= target:
                    break
                cells.add(candidate)
            candidate_mask = tuple(
                tuple(int((row, col) in cells) for col in range(motif_w))
                for row in range(motif_h)
            )
            if _dihedral_key(candidate_mask) in _CANONICAL_MASK_KEYS:
                continue
        else:
            candidate_mask = mask
            cells = {
                (row, col)
                for row, values in enumerate(candidate_mask)
                for col, value in enumerate(values)
                if value
            }

        palette = [color for color in range(1, 10) if color != cmd]
        rng.shuffle(palette)
        chosen = palette[:n_colors]
        ordered_cells = sorted(cells)
        rng.shuffle(ordered_cells)
        crop = [[0 for _col in range(motif_w)] for _row in range(motif_h)]
        for index, (row, col) in enumerate(ordered_cells):
            color = chosen[index] if index < n_colors else rng.choice(chosen)
            crop[row][col] = color

        frozen = _freeze(crop)
        outputs = tuple(_freeze(_apply_transform(crop, branch)) for branch in range(1, 6))
        if any(output == frozen for output in outputs):
            continue
        if len(set(outputs)) != 5:
            continue
        return crop
    raise RuntimeError("could not construct a transform-disambiguating motif")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = _pick_exact_axis(
        ctx,
        overrides,
        "motif_profile",
        _default_profile(sample_index),
        options=MOTIF_PROFILES,
    )
    cmd = _pick_exact_axis(
        ctx,
        overrides,
        "cmd",
        _scheduled_command(sample_index),
        lo=1,
        hi=5,
    )
    n_colors = _pick_exact_axis(
        ctx,
        overrides,
        "n_distinct_colors",
        _default_color_count(sample_index, profile),
        lo=2,
        hi=4,
    )

    if "grid_h" in overrides and overrides["grid_h"] is not None:
        height = ctx.draw_int("grid_h", 8, 15)
    elif profile == "canonical_morphology":
        height = ctx.draw_choice("grid_h", (8,))
    else:
        height = ctx.draw_int_diff("grid_h", 8, 15)

    if "grid_w" in overrides and overrides["grid_w"] is not None:
        width = ctx.draw_int("grid_w", 9, 16)
    elif profile == "canonical_morphology":
        width = ctx.draw_choice("grid_w", (9,))
    else:
        width = ctx.draw_int_diff("grid_w", 9, 16)

    crop = _random_colored_crop(ctx, sample_index, profile, n_colors, cmd)
    motif_h, motif_w = len(crop), len(crop[0])
    row_hi = height - motif_h - 1
    col_hi = width - motif_w - 1
    if row_hi < 2 or col_hi < 2:
        raise ValueError(
            f"requested canvas {height}x{width} cannot fit a {motif_h}x{motif_w} "
            "motif with the required command separation and border"
        )
    placement_rng = ctx.draw_rng("placement")
    row0 = placement_rng.randint(2, row_hi)
    col0 = placement_rng.randint(2, col_hi)

    grid = full_grid(height, width, 0)
    grid[0][0] = cmd
    for row in range(motif_h):
        for col in range(motif_w):
            grid[row0 + row][col0 + col] = crop[row][col]
    return grid


def observe_overrides(grid):
    facts, errors = _analyze_grid(grid, require_teaching=True)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "cmd": facts["cmd"],
        "n_distinct_colors": facts["n_distinct_colors"],
        "motif_profile": facts["motif_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    canonical = bool(isinstance(meta, dict) and meta.get("canonical"))
    _facts, errors = _analyze_grid(grid, require_teaching=not canonical)
    return errors


def mutation_fixtures():
    """Five task-local impostors that the structural checker must reject."""
    base = generate(91_337, 1, difficulty="medium")

    invalid_cmd = [row[:] for row in base]
    used = {value for row in invalid_cmd[1:] for value in row if value}
    replacement = next(color for color in (9, 8, 7, 6) if color not in used)
    invalid_cmd[0][0] = replacement

    no_motif = [[0 for _col in row] for row in base]
    no_motif[0][0] = 1

    monochrome = [row[:] for row in base]
    cells = [
        (row, col)
        for row in range(len(monochrome))
        for col in range(len(monochrome[0]))
        if monochrome[row][col] != 0 and (row, col) != (0, 0)
    ]
    mono_color = next(color for color in range(1, 10) if color != monochrome[0][0])
    for row, col in cells:
        monochrome[row][col] = mono_color

    touches_header = [row[:] for row in base]
    source = cells[0]
    touches_header[0][2] = touches_header[source[0]][source[1]]
    touches_header[source[0]][source[1]] = 0

    symmetric = full_grid(8, 9, 0)
    symmetric[0][0] = 1
    for row in range(3):
        for col in range(3):
            symmetric[3 + row][4 + col] = 2 if (row + col) % 2 == 0 else 3

    return [
        ("invalid_command_absent_from_motif", invalid_cmd),
        ("missing_motif", no_motif),
        ("monochrome_motif", monochrome),
        ("motif_touches_command_row", touches_header),
        ("transform_ambiguous_symmetric_motif", symmetric),
    ]
