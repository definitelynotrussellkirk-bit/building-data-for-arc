"""Semantic generator for ARC task 48fee61713bb.

The input contains a full blue edge marker and three coarse block pictures.
Every occupied coarse cell is rendered as a hollow 3x3 ring on a four-cell
stride.  Cyan (8) is the seven-slice main picture; two other colors make
three-slice pictures beside its two ends.  For each long-axis slice, count
the main and aligned small rings and compress those counts into a stacked
bar.  Cyan occupies the side where the main picture lies relative to the
small pictures.  The blue edge is a correlated layout cue, not an operand
of the canonical Racket transformation.
"""
from __future__ import annotations

import itertools

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "48fee61713bb"
TASK_ID = "48fee61713bb"
VERSION = "4.1.0"
RULE_HASH = "88f9214cd87f"
SUMMARY = (
    "Read hollow 3x3 rings on a four-cell lattice; identify cyan as the "
    "seven-slice main picture and the other colors as two aligned small "
    "pictures; then compress per-slice ring counts into colored stacks, "
    "with cyan on the side indicated by its position relative to the small pictures."
)
INVARIANTS = [
    "the calibrated input is exactly 30x30 with one full blue edge marker",
    "every occupied coarse cell is a hollow 3x3 ring on a four-cell stride",
    "cyan is a 7x3 or 3x7 main lattice with every long-axis slice occupied",
    "two distinct non-blue/non-cyan colors form disjoint aligned 3x3 lattices",
    "the marker edge and the main/small layout obey one of four linked rotations",
    "each output slice preserves the main count and its aligned small count",
    "stack side follows relative main/small geometry; blue is a correlated cue",
    "difficulty changes occupancy density without changing the transformation",
]

TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3
EDGE_NAMES = ("top", "right", "bottom", "left")
PUBLIC_PROFILES = tuple(f"public_{name}" for name in EDGE_NAMES)

# In normalized coordinates the main is 7x3 and both smalls are 3x3.
# Horizontal scenes transpose these patterns during rendering.
PUBLIC_MAIN_PATTERNS = (
    ((1, 1, 1), (1, 0, 0), (1, 1, 0), (0, 1, 1),
     (1, 1, 1), (1, 0, 0), (1, 1, 1)),
    ((1, 1, 1), (0, 1, 1), (1, 1, 1), (0, 1, 0),
     (1, 1, 1), (0, 1, 1), (1, 1, 1)),
    ((1, 0, 0), (1, 1, 1), (1, 0, 1), (1, 0, 1),
     (1, 1, 1), (1, 0, 0), (1, 1, 0)),
    ((1, 1, 1), (0, 1, 0), (1, 1, 0), (1, 0, 0),
     (0, 1, 0), (1, 1, 1), (1, 1, 0)),
)
PUBLIC_SMALL_PATTERNS = (
    (
        ((1, 1, 1), (0, 1, 0), (1, 1, 1)),
        ((1, 1, 1), (0, 1, 1), (0, 1, 1)),
    ),
    (
        ((1, 1, 0), (1, 0, 1), (1, 1, 0)),
        ((1, 1, 1), (1, 0, 1), (1, 1, 1)),
    ),
    (
        ((1, 0, 1), (1, 1, 1), (0, 1, 0)),
        ((0, 1, 1), (1, 1, 0), (1, 1, 1)),
    ),
    (
        ((1, 1, 1), (1, 0, 0), (1, 1, 1)),
        ((1, 0, 1), (1, 1, 1), (0, 0, 1)),
    ),
)
PUBLIC_PALETTES = ((2, 3), (6, 4), (9, 4), (2, 7))

# Exact canonical placements.  The small pictures occupy the first and last
# three long-axis slices, leaving the middle slice to the main alone.
LAYOUTS = (
    ((2, 17), (2, 1), (18, 1)),
    ((17, 1), (1, 1), (1, 17)),
    ((1, 1), (1, 17), (17, 17)),
    ((1, 2), (17, 2), (17, 18)),
)


def _transpose(pattern):
    return tuple(tuple(row) for row in zip(*pattern))


def _pattern_key(pattern):
    return tuple(tuple(int(value) for value in row) for row in pattern)


def _make_main_patterns():
    """Build a deterministic, density-diverse bank with public patterns first."""
    patterns = list(PUBLIC_MAIN_PATTERNS)
    seen = set(patterns)
    modulus = 7 ** 7
    candidate = 0
    while len(patterns) < 512:
        value = (candidate * 104729 + 7919) % modulus
        candidate += 1
        rows = []
        for _ in range(7):
            mask = 1 + value % 7
            value //= 7
            rows.append(tuple((mask >> col) & 1 for col in range(3)))
        pattern = tuple(rows)
        count = sum(sum(row) for row in pattern)
        if not 10 <= count <= 19:
            continue
        if not any(row[0] for row in pattern) or not any(row[2] for row in pattern):
            continue
        if pattern not in seen:
            seen.add(pattern)
            patterns.append(pattern)
    return tuple(patterns)


def _make_small_patterns():
    """Enumerate all 3x3 patterns with no blank slice and a pinned bbox."""
    public = [pattern for pair in PUBLIC_SMALL_PATTERNS for pattern in pair]
    patterns = []
    seen = set()
    for pattern in public:
        if pattern not in seen:
            seen.add(pattern)
            patterns.append(pattern)
    for mask in range(1 << 9):
        pattern = tuple(
            tuple((mask >> (3 * row + col)) & 1 for col in range(3))
            for row in range(3)
        )
        if not all(any(row) for row in pattern):
            continue
        if not any(row[0] for row in pattern) or not any(row[2] for row in pattern):
            continue
        if pattern not in seen:
            seen.add(pattern)
            patterns.append(pattern)
    return tuple(patterns)


MAIN_PATTERNS = _make_main_patterns()
SMALL_PATTERNS = _make_small_patterns()
PALETTES = tuple(itertools.permutations((2, 3, 4, 5, 6, 7, 9), 2))
MAIN_TO_INDEX = {pattern: index for index, pattern in enumerate(MAIN_PATTERNS)}
SMALL_TO_INDEX = {pattern: index for index, pattern in enumerate(SMALL_PATTERNS)}
PALETTE_TO_INDEX = {palette: index for index, palette in enumerate(PALETTES)}
MAIN_COUNT = len(MAIN_PATTERNS)
SMALL_COUNT = len(SMALL_PATTERNS)
PALETTE_COUNT = len(PALETTES)
SCENE_COUNT = 4 * PALETTE_COUNT * MAIN_COUNT * SMALL_COUNT * SMALL_COUNT

assert MAIN_COUNT == 512
assert SMALL_COUNT == 290
assert PALETTE_COUNT == 42

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": (
            "deterministic mixed-radix schedule over edge, ordered small-color "
            "palette, main occupancy, and two small occupancies"
        ),
        "valid": "0..7233945599",
        "doc": (
            "Exact index over 4 linked layouts, 42 ordered palettes, 512 main "
            "patterns, and 290 patterns for each small picture."
        ),
    }
}


def _paint_ring(grid, top, left, color):
    for row in range(top, top + 3):
        for col in range(left, left + 3):
            if row in (top, top + 2) or col in (left, left + 2):
                grid[row][col] = color


def _paint_pattern(grid, top, left, pattern, color):
    for block_row, values in enumerate(pattern):
        for block_col, occupied in enumerate(values):
            if occupied:
                _paint_ring(grid, top + 4 * block_row, left + 4 * block_col, color)


def _make_grid(edge, palette, main_pattern, first_pattern, second_pattern):
    grid = [[0] * 30 for _ in range(30)]
    if edge == TOP:
        grid[0] = [1] * 30
    elif edge == RIGHT:
        for row in range(30):
            grid[row][29] = 1
    elif edge == BOTTOM:
        grid[29] = [1] * 30
    elif edge == LEFT:
        for row in range(30):
            grid[row][0] = 1
    else:
        raise ValueError(f"unknown edge index: {edge!r}")

    horizontal = edge in (RIGHT, LEFT)
    rendered_main = _transpose(main_pattern) if horizontal else main_pattern
    rendered_first = _transpose(first_pattern) if horizontal else first_pattern
    rendered_second = _transpose(second_pattern) if horizontal else second_pattern
    main_at, first_at, second_at = LAYOUTS[edge]
    _paint_pattern(grid, *main_at, rendered_main, 8)
    _paint_pattern(grid, *first_at, rendered_first, palette[0])
    _paint_pattern(grid, *second_at, rendered_second, palette[1])
    return grid


def _encode_scene(edge, palette_index, main_index, first_index, second_index):
    code = edge
    code = code * PALETTE_COUNT + palette_index
    code = code * MAIN_COUNT + main_index
    code = code * SMALL_COUNT + first_index
    return code * SMALL_COUNT + second_index


def _decode_scene(scene_code):
    scene_code, second_index = divmod(scene_code, SMALL_COUNT)
    scene_code, first_index = divmod(scene_code, SMALL_COUNT)
    scene_code, main_index = divmod(scene_code, MAIN_COUNT)
    edge, palette_index = divmod(scene_code, PALETTE_COUNT)
    return edge, palette_index, main_index, first_index, second_index


def _grid_from_code(scene_code):
    edge, palette_index, main_index, first_index, second_index = _decode_scene(scene_code)
    return _make_grid(
        edge,
        PALETTES[palette_index],
        MAIN_PATTERNS[main_index],
        SMALL_PATTERNS[first_index],
        SMALL_PATTERNS[second_index],
    )


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must contain at least one row"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must contain at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC colors from zero through nine"]
    return []


def _edge_from_marker(grid):
    candidates = []
    if all(value == 1 for value in grid[0]):
        candidates.append(TOP)
    if all(row[-1] == 1 for row in grid):
        candidates.append(RIGHT)
    if all(value == 1 for value in grid[-1]):
        candidates.append(BOTTOM)
    if all(row[0] == 1 for row in grid):
        candidates.append(LEFT)
    marker_count = sum(value == 1 for row in grid for value in row)
    return candidates[0] if len(candidates) == 1 and marker_count == 30 else None


def _read_pattern(grid, top, left, block_height, block_width, color):
    pattern = []
    for block_row in range(block_height):
        values = []
        for block_col in range(block_width):
            ring_top = top + 4 * block_row
            ring_left = left + 4 * block_col
            occupied = grid[ring_top][ring_left] == color
            values.append(int(occupied))
        pattern.append(tuple(values))
    return tuple(pattern)


def _recover_scene(grid):
    edge = _edge_from_marker(grid)
    if edge is None:
        return None
    colors = {value for row in grid for value in row}
    small_colors = sorted(colors - {0, 1, 8})
    if len(small_colors) != 2:
        return None
    main_at, first_at, second_at = LAYOUTS[edge]
    def region_color(position):
        top, left = position
        candidates = {
            grid[row][col]
            for row in range(top, top + 11)
            for col in range(left, left + 11)
        } - {0, 1, 8}
        return next(iter(candidates)) if len(candidates) == 1 else None

    first_color = region_color(first_at)
    second_color = region_color(second_at)
    palette = (first_color, second_color)
    palette_index = PALETTE_TO_INDEX.get(palette)
    if palette_index is None or set(palette) != set(small_colors):
        return None

    horizontal = edge in (RIGHT, LEFT)
    if horizontal:
        main_rendered = _read_pattern(grid, *main_at, 3, 7, 8)
        first_rendered = _read_pattern(grid, *first_at, 3, 3, first_color)
        second_rendered = _read_pattern(grid, *second_at, 3, 3, second_color)
        main_pattern = _transpose(main_rendered)
        first_pattern = _transpose(first_rendered)
        second_pattern = _transpose(second_rendered)
    else:
        main_pattern = _read_pattern(grid, *main_at, 7, 3, 8)
        first_pattern = _read_pattern(grid, *first_at, 3, 3, first_color)
        second_pattern = _read_pattern(grid, *second_at, 3, 3, second_color)
    main_index = MAIN_TO_INDEX.get(main_pattern)
    first_index = SMALL_TO_INDEX.get(first_pattern)
    second_index = SMALL_TO_INDEX.get(second_pattern)
    if None in (main_index, first_index, second_index):
        return None
    scene_code = _encode_scene(
        edge, palette_index, main_index, first_index, second_index
    )
    return scene_code, edge, palette, main_pattern, first_pattern, second_pattern


def _analyze_color(grid, color):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    block_height = (bottom - top + 3) // 4
    block_width = (right - left + 3) // 4
    pattern = _read_pattern(grid, top, left, block_height, block_width, color)
    return color, block_height, block_width, pattern, top, left


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical lattice compression rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    colors = sorted({value for row in grid for value in row} - {0, 1})
    infos = [_analyze_color(grid, color) for color in colors]
    main = next((info for info in infos if info[0] == 8), None)
    if main is None:
        raise ValueError("missing cyan main lattice")
    smalls = [info for info in infos if info[0] != 8]
    if not smalls:
        raise ValueError("missing small lattices")
    horizontal = main[2] > main[1]
    average_small_top = sum(info[4] for info in smalls) // len(smalls)
    average_small_left = sum(info[5] for info in smalls) // len(smalls)
    main_at_end = (
        main[4] > average_small_top if horizontal
        else main[5] > average_small_left
    )
    slice_count = main[2] if horizontal else main[1]
    slices = []
    for index in range(slice_count):
        if horizontal:
            main_count = sum(row[index] for row in main[3])
        else:
            main_count = sum(main[3][index])
        small = None
        local_index = None
        for candidate in smalls:
            offset = (
                (candidate[5] - main[5]) // 4 if horizontal
                else (candidate[4] - main[4]) // 4
            )
            extent = candidate[2] if horizontal else candidate[1]
            if offset <= index < offset + extent:
                small = candidate
                local_index = index - offset
                break
        if small is None:
            slices.append((main_count, 0, 0))
        elif horizontal:
            small_count = sum(row[local_index] for row in small[3])
            slices.append((main_count, small_count, small[0]))
        else:
            small_count = sum(small[3][local_index])
            slices.append((main_count, small_count, small[0]))
    max_height = max(main_count + small_count for main_count, small_count, _ in slices)
    stacks = []
    for main_count, small_count, small_color in slices:
        padding = [0] * (max_height - main_count - small_count)
        main_cells = [8] * main_count
        small_cells = [small_color] * small_count
        stacks.append(
            padding + small_cells + main_cells
            if main_at_end else main_cells + small_cells + padding
        )
    if horizontal:
        return [
            [stacks[col][row] for col in range(slice_count)]
            for row in range(max_height)
        ]
    return stacks


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if (height, width) != (30, 30):
        errors.append("calibrated block-stack scenes must be exactly 30x30")
    recovered = _recover_scene(grid) if not errors else None
    if recovered is None:
        errors.append("scene does not match a declared linked edge/layout/block profile")
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    scene_code, edge, palette, main_pattern, first_pattern, second_pattern = recovered
    expected = _grid_from_code(scene_code)
    if tuple(map(tuple, grid)) != tuple(map(tuple, expected)):
        errors.append("returned cells do not exactly reconstruct from scene_code")
    output = None
    try:
        output = rule_mirror(grid)
    except (IndexError, StopIteration, ValueError) as exc:
        errors.append(f"lattice compression failed: {exc}")
    facts = {
        "height": height,
        "width": width,
        "edge": edge,
        "edge_name": EDGE_NAMES[edge],
        "palette": palette,
        "main_ring_count": sum(map(sum, main_pattern)),
        "first_ring_count": sum(map(sum, first_pattern)),
        "second_ring_count": sum(map(sum, second_pattern)),
        "public_profile": PUBLIC_PROFILES[edge],
    }
    return {"errors": errors, "scene_code": scene_code, "facts": facts, "output": output}


def canonical_profile_signature(grid):
    try:
        return _CANONICAL_EXACT.get(tuple(map(tuple, grid)))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return analysis["facts"]["public_profile"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {} if analysis["errors"] else {"scene_code": analysis["scene_code"]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _public_grid(edge):
    return _make_grid(
        edge,
        PUBLIC_PALETTES[edge],
        PUBLIC_MAIN_PATTERNS[edge],
        PUBLIC_SMALL_PATTERNS[edge][0],
        PUBLIC_SMALL_PATTERNS[edge][1],
    )


_CANONICAL_EXACT = {
    tuple(map(tuple, _public_grid(edge))): PUBLIC_PROFILES[edge]
    for edge in range(4)
}

_BAND_INDEX = {None: 0, "easy": 1, "medium": 2, "hard": 3}


def _pattern_pools(patterns):
    counts = [sum(map(sum, pattern)) for pattern in patterns]
    return {
        None: tuple(range(len(patterns))),
        "easy": tuple(index for index, count in enumerate(counts) if count >= 16),
        "medium": tuple(index for index, count in enumerate(counts) if count == 15),
        "hard": tuple(index for index, count in enumerate(counts) if count <= 14),
    }


MAIN_POOLS = _pattern_pools(MAIN_PATTERNS)
SMALL_POOLS = {
    None: tuple(range(SMALL_COUNT)),
    "easy": tuple(index for index, pattern in enumerate(SMALL_PATTERNS)
                  if sum(map(sum, pattern)) >= 7),
    "medium": tuple(index for index, pattern in enumerate(SMALL_PATTERNS)
                    if 5 <= sum(map(sum, pattern)) <= 7),
    "hard": tuple(index for index, pattern in enumerate(SMALL_PATTERNS)
                  if sum(map(sum, pattern)) <= 5),
}


def _signature_groups(patterns, pool):
    grouped = {}
    for index in pool:
        signature = tuple(map(sum, patterns[index]))
        grouped.setdefault(signature, []).append(index)
    return tuple(tuple(grouped[signature]) for signature in sorted(grouped))


MAIN_GROUPS = {
    difficulty: _signature_groups(MAIN_PATTERNS, pool)
    for difficulty, pool in MAIN_POOLS.items()
}
SMALL_GROUPS = {
    difficulty: _signature_groups(SMALL_PATTERNS, pool)
    for difficulty, pool in SMALL_POOLS.items()
}


def _natural_scene_code(seed, sample_index, difficulty):
    band = _BAND_INDEX[difficulty]
    main_groups = MAIN_GROUPS[difficulty]
    small_groups = SMALL_GROUPS[difficulty]
    semantic_count = len(main_groups) * len(small_groups) ** 2
    # Put seed and sample_index in separate mixed-radix positions.  This keeps
    # multi-pair episodes distinct (seed changes between episodes while their
    # local sample indexes repeat), and also traverses cleanly when either
    # counter or both counters advance.
    counter = sample_index + (4 * PALETTE_COUNT) * seed
    rank = counter // (4 * PALETTE_COUNT)
    # The profile counter deliberately changes parity once per 168 seed
    # values.  Thus the jointly advancing mode does not remain trapped on
    # only the even (or odd) half of the palette/layout product.
    permuted = (
        sample_index + seed + seed // (4 * PALETTE_COUNT)
    ) % (4 * PALETTE_COUNT)
    edge = permuted % 4
    palette_index = permuted // 4
    # Decode the high position over semantic row-count signatures, rather
    # than raw patterns, so distinct inputs cannot collapse to duplicate
    # compressed outputs within a lane.
    semantic_rank = (997 * rank) % semantic_count
    main_group = main_groups[semantic_rank % len(main_groups)]
    semantic_rank //= len(main_groups)
    first_group = small_groups[semantic_rank % len(small_groups)]
    semantic_rank //= len(small_groups)
    second_group = small_groups[semantic_rank % len(small_groups)]
    main_index = main_group[(seed + 31 * sample_index) % len(main_group)]
    first_index = first_group[(13 * seed + sample_index) % len(first_group)]
    second_index = second_group[(17 * seed + 3 * sample_index + band) % len(second_group)]
    return _encode_scene(edge, palette_index, main_index, first_index, second_index)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _BAND_INDEX:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    requested_code = overrides.get("scene_code")
    if requested_code is not None:
        if isinstance(requested_code, bool) or not isinstance(requested_code, int):
            raise TypeError("scene_code must be a literal integer")
        if not 0 <= requested_code < SCENE_COUNT:
            raise ValueError(f"scene_code must be in 0..{SCENE_COUNT - 1}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested_code is not None:
        scene_code = ctx.draw_int("scene_code", 0, SCENE_COUNT - 1)
    else:
        scheduled = _natural_scene_code(seed, sample_index, difficulty)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    return _grid_from_code(scene_code)


# This is a finite teaching contract, not a proof of unique induction over every
# possible rule. Blue-edge-only and marker-free rules are answer-equivalent on
# the calibrated domain; neither is falsely declared a refutable shortcut.
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def strict_canonical_like(grid):
    return self_check(grid)


def _main_geometry(grid):
    main = _analyze_color(grid, 8)
    colors = sorted({value for row in grid for value in row} - {0, 1, 8})
    smalls = [_analyze_color(grid, color) for color in colors]
    if not smalls:
        raise ValueError("missing small lattices")
    horizontal = main[2] > main[1]
    axis = 4 if horizontal else 5
    main_at_end = main[axis] > sum(info[axis] for info in smalls) // len(smalls)
    return horizontal, main_at_end


def _normalized_stacks(grid):
    output = rule_mirror(grid)
    # The calibrated long axis is seven and its compressed short axis is <=6.
    horizontal = len(output) != 7
    return ([list(row) for row in zip(*output)] if horizontal else output), horizontal


def _restore_stacks(stacks, horizontal):
    return [list(row) for row in zip(*stacks)] if horizontal else stacks


def _opposite_stack_side(grid):
    stacks, horizontal = _normalized_stacks(grid)
    return _restore_stacks([row[::-1] for row in stacks], horizontal)


def _fixed_main_at_start(grid):
    stacks, horizontal = _normalized_stacks(grid)
    if stacks[0][0] != 8:
        stacks = [row[::-1] for row in stacks]
    return _restore_stacks(stacks, horizontal)


def _fixed_main_at_end(grid):
    stacks, horizontal = _normalized_stacks(grid)
    if stacks[0][-1] != 8:
        stacks = [row[::-1] for row in stacks]
    return _restore_stacks(stacks, horizontal)


def _main_only(grid):
    stacks, horizontal = _normalized_stacks(grid)
    main_at_end = stacks[0][-1] == 8
    counts = [row.count(8) for row in stacks]
    width = max(counts)
    result = []
    for count in counts:
        cells, padding = [8] * count, [0] * (width - count)
        result.append(padding + cells if main_at_end else cells + padding)
    return _restore_stacks(result, horizontal)


def _swap_small_colors(grid):
    output = rule_mirror(grid)
    colors = sorted({value for row in output for value in row} - {0, 8})
    if len(colors) != 2:
        raise ValueError("expected two small colors")
    mapping = {colors[0]: colors[1], colors[1]: colors[0]}
    return [[mapping.get(value, value) for value in row] for row in output]


def _unit_counts(grid):
    stacks, horizontal = _normalized_stacks(grid)
    main_at_end = stacks[0][-1] == 8
    result = []
    for row in stacks:
        small = next((value for value in row if value not in (0, 8)), 0)
        result.append([small, 8] if main_at_end else [8, small])
    return _restore_stacks(result, horizontal)


def _always_vertical(grid):
    stacks, _ = _normalized_stacks(grid)
    return stacks


def _always_horizontal(grid):
    stacks, _ = _normalized_stacks(grid)
    return _restore_stacks(stacks, True)


def _has_count_multiplicity(grid):
    main = _analyze_color(grid, 8)
    slices = _transpose(main[3]) if main[2] > main[1] else main[3]
    return any(sum(row) > 1 for row in slices)


SEMANTIC_RIVALS = {
    "opposite_stack_side": _opposite_stack_side,
    "fixed_main_at_start": _fixed_main_at_start,
    "fixed_main_at_end": _fixed_main_at_end,
    "main_only": _main_only,
    "swap_small_colors": _swap_small_colors,
    "unit_counts": _unit_counts,
    "always_vertical": _always_vertical,
    "always_horizontal": _always_horizontal,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "layout_top": lambda grid: _edge_from_marker(grid) == TOP,
    "layout_right": lambda grid: _edge_from_marker(grid) == RIGHT,
    "layout_bottom": lambda grid: _edge_from_marker(grid) == BOTTOM,
    "layout_left": lambda grid: _edge_from_marker(grid) == LEFT,
    "count_multiplicity": _has_count_multiplicity,
    "two_small_colors": lambda grid: len({v for row in grid for v in row} - {0, 1, 8}) == 2,
    "main_at_start": lambda grid: not _main_geometry(grid)[1],
    "main_at_end": lambda grid: _main_geometry(grid)[1],
    "horizontal": lambda grid: _main_geometry(grid)[0],
    "vertical": lambda grid: not _main_geometry(grid)[0],
}
BRANCH_WITNESSES = ("layout_top", "layout_right", "layout_bottom", "layout_left")
WITNESS_RIVALS = {
    "count_multiplicity": ["unit_counts"],
    "two_small_colors": ["main_only", "swap_small_colors"],
    "main_at_start": ["fixed_main_at_end", "opposite_stack_side"],
    "main_at_end": ["fixed_main_at_start", "opposite_stack_side"],
    "horizontal": ["always_vertical"],
    "vertical": ["always_horizontal"],
}


def lesson_identifiable(demos, query):
    """Flag only surviving named rivals that change this query's answer.

    Rival elimination uses demonstration inputs and labels only. The query's
    provided label is never accessed: the canonical mirror computes the target
    for comparing the predictions of demonstration-consistent hypotheses.
    Passing means identifiable within the declared finite rival set.
    """
    if not demos:
        return ["missing demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["missing query input"]
    if any(not isinstance(pair, dict) or "input" not in pair or "output" not in pair for pair in demos):
        return ["demonstrations require input and output"]
    target = rule_mirror(query["input"])
    reasons = []
    for name, solve in LESSON_COMPETITORS.items():
        if all(solve(pair["input"]) == pair["output"] for pair in demos):
            if solve(query["input"]) != target:
                reasons.append(f"demonstrations do not refute {name} for this query")
    return reasons
