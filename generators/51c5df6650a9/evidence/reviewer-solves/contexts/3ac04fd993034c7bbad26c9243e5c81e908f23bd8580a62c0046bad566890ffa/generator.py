"""Generator for the canonical ``Legend-Ordered Pack`` ARC task.

The nonzero cells in row 0 form an ordered color legend.  Rows 2+ contain
one separated component for each legend color.  The selected Racket rule
crops those components and packs the crops left-to-right, beginning at output
row 1, in *legend* order rather than body scan order.

Only controls that are exactly recoverable from returned pixels are exposed:
the canonical grid profile, legend count, and legend layout.  Construction is
slot based, so every ordinary draw has a blank separator row and every legend
color has exactly one body-only component; no rejection loop can silently drop
or merge an object.
"""
from __future__ import annotations

from collections import deque
from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "51c5df6650a9"
TASK_ID = GENERATOR_ID
RULE_HASH = "4ec427a9d6d9"
VERSION = "3.0.0"
SUMMARY = (
    "Read the distinct nonzero colors in the top row from left to right. "
    "For each color, tightly crop its separated body component, then pack "
    "the crops left-to-right from output row 1 with one blank column between "
    "adjacent crops."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "the input has one of the five exact canonical height/width profiles",
    "row 1 is blank and row 0 contains 2..4 distinct legend colors in a supported layout",
    "rows 2+ contain exactly one separated 3..8-cell component per legend color",
    "the packed crops fit in the original width",
    "body scan order differs from legend order on every generated input",
    "default legend layouts refute the canonical fixed-columns shortcut",
]

_PROFILE_SPECS = {
    "h10_w13": (10, 13),
    "h11_w14": (11, 14),
    "h10_w12": (10, 12),
    "h12_w14": (12, 14),
    "h11_w13": (11, 13),
}
_PROFILE_NAMES = tuple(_PROFILE_SPECS)

_LEGEND_POSITIONS = {
    2: {
        "contiguous": (0, 1),
        "shifted": (1, 2),
        "canonical": (0, 2),
    },
    3: {
        "contiguous": (0, 1, 2),
        "shifted": (1, 3, 5),
        "canonical": (0, 2, 4),
    },
    4: {
        "contiguous": (0, 1, 2, 3),
        "shifted": (1, 3, 5, 7),
        "canonical": (0, 2, 4, 6),
    },
}
_DEFAULT_LAYOUTS = ("contiguous", "shifted")
_LAYOUT_NAMES = _DEFAULT_LAYOUTS + ("canonical",)

AXES = {
    "profile": {
        "type": "str",
        "default": "uniform over the five exact canonical height/width profiles",
        "valid": "h10_w13|h11_w14|h10_w12|h12_w14|h11_w13",
    },
    "n_legend": {
        "type": "int",
        "default": "uniform 2..4",
        "valid": "2..4",
    },
    "legend_layout": {
        "type": "str",
        "default": "uniform contiguous|shifted (canonical is override-only)",
        "valid": "contiguous|shifted|canonical",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize_shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(cells):
    """Return all unique rotations and reflections of a small polyomino."""
    variants = set()
    base = tuple(cells)
    for reflected in (False, True):
        shape = tuple((r, -c if reflected else c) for r, c in base)
        for _ in range(4):
            variants.add(_normalize_shape(shape))
            shape = tuple((c, -r) for r, c in shape)
    return variants


_BASE_MOTIFS = (
    ((0, 0), (1, 0), (1, 1)),                         # L triomino
    ((0, 0), (0, 1), (0, 2)),                         # line triomino
    ((0, 0), (0, 1), (1, 0), (1, 1)),                 # square tetromino
    ((0, 0), (1, 0), (2, 0), (2, 1)),                 # L tetromino
    ((0, 1), (1, 0), (1, 1), (1, 2)),                 # T tetromino
    ((0, 0), (1, 0), (1, 1), (2, 1)),                 # zig-zag tetromino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),         # P pentomino
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),         # V pentomino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),         # plus pentomino
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),         # W pentomino
)
_MOTIFS = tuple(sorted({variant for base in _BASE_MOTIFS for variant in _shape_variants(base)}))


def _shape_height(shape):
    return max(r for r, _ in shape) + 1


def _shape_width(shape):
    return max(c for _, c in shape) + 1


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    profile = overrides.get("profile")
    if profile is not None:
        if type(profile) is not str:
            raise ValueError("profile must be a string")
        if profile not in _PROFILE_SPECS:
            raise ValueError(f"unsupported profile {profile!r}")

    n_legend = overrides.get("n_legend")
    if n_legend is not None:
        if type(n_legend) is not int:
            raise ValueError("n_legend must be an integer (not bool)")
        if n_legend not in (2, 3, 4):
            raise ValueError("n_legend must be 2, 3, or 4")

    layout = overrides.get("legend_layout")
    if layout is not None:
        if type(layout) is not str:
            raise ValueError("legend_layout must be a string")
        if layout not in _LAYOUT_NAMES:
            raise ValueError(f"unsupported legend_layout {layout!r}")


def _choose_motifs(ctx, n, difficulty):
    """Choose crops that always fit the packed output and body slots."""
    max_width = 2 if n == 4 else 3
    if difficulty == "easy":
        sizes = {3}
    elif difficulty == "medium":
        sizes = {3, 4}
    elif difficulty == "hard":
        sizes = {4, 5}
    else:
        sizes = {3, 4, 5}
    pool = tuple(
        motif
        for motif in _MOTIFS
        if len(motif) in sizes and _shape_width(motif) <= max_width and _shape_height(motif) <= 3
    )
    if not pool:
        raise RuntimeError("motif pool unexpectedly empty")
    rng = ctx.draw_rng("component_shapes")
    return tuple(rng.choice(pool) for _ in range(n))


def _edge_column(rng, width, shape_width, side):
    if side == "left":
        return rng.randint(0, min(2, width - shape_width))
    low = max(0, width - shape_width - 2)
    return rng.randint(low, width - shape_width)


def _slot_origins(ctx, height, width, motifs):
    """Construct mutually separated body slots; no placement retry is needed."""
    rng = ctx.draw_rng("component_positions")
    n = len(motifs)
    origins = []
    if n == 2:
        first_h, first_w = _shape_height(motifs[0]), _shape_width(motifs[0])
        second_h, second_w = _shape_height(motifs[1]), _shape_width(motifs[1])
        del first_h
        origins.append((2, _edge_column(rng, width, first_w, "left")))
        origins.append((height - second_h, _edge_column(rng, width, second_w, "right")))
        return tuple(origins)

    if n == 3:
        for index, motif in enumerate(motifs):
            shape_h, shape_w = _shape_height(motif), _shape_width(motif)
            if index == 0:
                origins.append((2, _edge_column(rng, width, shape_w, "left")))
            elif index == 1:
                origins.append((2, _edge_column(rng, width, shape_w, "right")))
            else:
                center = (width - shape_w) // 2
                low = max(0, center - 1)
                high = min(width - shape_w, center + 1)
                origins.append((height - shape_h, rng.randint(low, high)))
        return tuple(origins)

    if n == 4:
        for index, motif in enumerate(motifs):
            shape_h, shape_w = _shape_height(motif), _shape_width(motif)
            top = index < 2
            left = index % 2 == 0
            row = 2 if top else height - shape_h
            column = _edge_column(rng, width, shape_w, "left" if left else "right")
            origins.append((row, column))
        return tuple(origins)

    raise ValueError(f"unsupported legend count {n}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", _PROFILE_NAMES)
    n_legend = ctx.draw_int_strict("n_legend", 2, 4)
    layout_options = _LAYOUT_NAMES if overrides.get("legend_layout") is not None else _DEFAULT_LAYOUTS
    legend_layout = ctx.draw_choice("legend_layout", layout_options)
    height, width = _PROFILE_SPECS[profile]

    colors = tuple(ctx.draw_rng("legend_colors").sample(range(1, 10), n_legend))
    grid = full_grid(height, width, 0)
    for column, color in zip(_LEGEND_POSITIONS[n_legend][legend_layout], colors):
        grid[0][column] = color

    motifs = _choose_motifs(ctx, n_legend, difficulty)
    origins = _slot_origins(ctx, height, width, motifs)
    derangements = tuple(
        order
        for order in permutations(range(n_legend))
        if all(index != order[index] for index in range(n_legend))
    )
    body_order = ctx.draw_rng("body_order").choice(derangements)
    physical_colors = tuple(colors[index] for index in body_order)

    for motif, (row, column), color in zip(motifs, origins, physical_colors):
        for dr, dc in motif:
            target_r, target_c = row + dr, column + dc
            if not (2 <= target_r < height and 0 <= target_c < width):
                raise RuntimeError("constructive component slot escaped the grid")
            if grid[target_r][target_c] != 0:
                raise RuntimeError("constructive component slots unexpectedly overlap")
            grid[target_r][target_c] = color
    return grid


def _rectangular_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    return None


def _legend_entries(grid):
    return [(column, value) for column, value in enumerate(grid[0]) if value != 0]


def _layout_name(n, positions):
    return next(
        (name for name, expected in _LEGEND_POSITIONS.get(n, {}).items() if tuple(positions) == expected),
        None,
    )


def _profile_name(grid):
    signature = (len(grid), len(grid[0]))
    return next((name for name, dims in _PROFILE_SPECS.items() if dims == signature), None)


def _same_color_components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(2, height):
        for column in range(width):
            if grid[row][column] != color or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        2 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return sorted(components, key=min)


def _nonzero_components(grid):
    """Racket-compatible body components, connected through any nonzero cell."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(2, height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        2 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return sorted(components, key=min)


def _component_crop(grid, cells):
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(column for _, column in cells)
    c1 = max(column for _, column in cells)
    cell_set = set(cells)
    return [
        [grid[row][column] if (row, column) in cell_set else 0 for column in range(c0, c1 + 1)]
        for row in range(r0, r1 + 1)
    ]


def _pack_full(grid, components):
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    left = 0
    for cells in components:
        part = _component_crop(grid, cells)
        part_width = len(part[0])
        for row, values in enumerate(part, start=1):
            for column, value in enumerate(values, start=left):
                if row < height and column < width and value:
                    output[row][column] = value
        left += part_width + 1
    return output


def _legend_colors(grid):
    seen = set()
    colors = []
    for value in grid[0]:
        if value and value not in seen:
            seen.add(value)
            colors.append(value)
    return colors


def reference_output(grid):
    """Independent Python mirror for tests; the selected Racket remains authority."""
    ordered = []
    for color in _legend_colors(grid):
        components = _same_color_components(grid, color)
        if not components:
            raise ValueError(f"legend color {color} has no body component")
        ordered.append(components[0])
    return _pack_full(grid, ordered)


def _body_scan_order_rival(grid):
    """Wrong rule: ignore the legend and pack body objects in reading order."""
    return _pack_full(grid, _nonzero_components(grid))


def _fixed_columns_rival(grid):
    """Wrong canonical-fitting rule: read only legend columns 0, 2, and 4."""
    colors = []
    for column in (0, 2, 4):
        if column < len(grid[0]):
            value = grid[0][column]
            if value and value not in colors:
                colors.append(value)
    ordered = []
    for color in colors:
        components = _same_color_components(grid, color)
        if components:
            ordered.append(components[0])
    return _pack_full(grid, ordered)


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the strict canonical-profile teaching manifold."""
    del difficulty, meta
    malformed = _rectangular_grid_error(grid)
    if malformed:
        return [malformed]

    height, width = len(grid), len(grid[0])
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    profile = _profile_name(grid)
    if profile is None:
        errors.append(f"(height,width)=({height},{width}) is not a canonical profile")
    if height < 3:
        return errors + ["grid needs a legend row, blank separator row, and body"]
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be blank")

    entries = _legend_entries(grid)
    positions = [column for column, _ in entries]
    colors = [color for _, color in entries]
    n_legend = len(colors)
    if n_legend not in (2, 3, 4):
        errors.append(f"row 0 must contain 2..4 legend entries, got {n_legend}")
    layout = _layout_name(n_legend, positions)
    if layout is None:
        errors.append(f"legend positions {positions} are not a supported layout")
    if len(set(colors)) != n_legend:
        errors.append("legend colors must be distinct")

    allowed = set(colors)
    foreign = next(
        (
            value
            for row in grid[2:]
            for value in row
            if value != 0 and value not in allowed
        ),
        None,
    )
    if foreign is not None:
        errors.append(f"body color {foreign} is absent from the legend")

    touching = False
    for row in range(2, height):
        for column in range(width):
            value = grid[row][column]
            if not value:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, column + dc
                if nr < height and nc < width and grid[nr][nc] not in (0, value):
                    touching = True
                    break
            if touching:
                break
        if touching:
            break
    if touching:
        errors.append("different body colors may not touch orthogonally")

    color_components = {}
    packed_width = max(0, n_legend - 1)
    for color in colors:
        components = _same_color_components(grid, color)
        color_components[color] = components
        if len(components) != 1:
            errors.append(f"legend color {color} has {len(components)} body components, expected 1")
            continue
        cells = components[0]
        if not 3 <= len(cells) <= 8:
            errors.append(f"legend color {color} component has {len(cells)} cells, expected 3..8")
        packed_width += max(column for _, column in cells) - min(column for _, column in cells) + 1
    if packed_width > width:
        errors.append(f"packed crops need width {packed_width}, exceeding grid width {width}")

    if colors and len(set(colors)) == len(colors) and all(len(color_components.get(color, ())) == 1 for color in colors):
        components = _nonzero_components(grid)
        if len(components) != len(colors):
            errors.append("body components do not realize the legend colors exactly once")
        else:
            scan = [grid[cells[0][0]][cells[0][1]] for cells in components]
            if sorted(scan) != sorted(colors):
                errors.append("body components do not realize the legend colors exactly once")
            if scan == colors:
                errors.append("body scan order must differ from legend order")
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    entries = _legend_entries(grid)
    return {
        "profile": _profile_name(grid),
        "n_legend": len(entries),
        "legend_layout": _layout_name(len(entries), [column for column, _ in entries]),
    }


def strict_canonical_like(grid):
    return self_check(grid)


CANONICAL_SHORTCUTS = {
    # All five canonical demonstrations put their three legend cells at 0,2,4.
    "fixed_columns_0_2_4": _fixed_columns_rival,
}
SEMANTIC_RIVALS = {
    "body_scan_order": _body_scan_order_rival,
    **CANONICAL_SHORTCUTS,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "legend_order_changes_answer": lambda grid: reference_output(grid) != _body_scan_order_rival(grid),
    "fixed_columns_are_insufficient": lambda grid: reference_output(grid) != _fixed_columns_rival(grid),
}
WITNESS_RIVALS = {
    "legend_order_changes_answer": ["body_scan_order"],
    "fixed_columns_are_insufficient": ["fixed_columns_0_2_4"],
}


def lesson_identifiable(demos, query):
    """Require correct labels and demonstrations that refute named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{label} is outside the strict grammar: {errors[0]}")
            continue
        if pair["output"] != reference_output(pair["input"]):
            reasons.append(f"{label} output disagrees with the selected rule")
    if reasons:
        return reasons

    truth = reference_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query["input"]) != truth:
            reasons.append(f"named rival {name!r} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    """Task-linked near misses that a meaningful strict check must reject."""
    base = generate(
        51_665,
        0,
        difficulty="medium",
        profile="h10_w13",
        n_legend=3,
        legend_layout="canonical",
    )
    entries = _legend_entries(base)
    first_column, first_color = entries[0]
    second_column, _ = entries[1]

    separator_contact = [row[:] for row in base]
    separator_contact[1][first_column] = first_color

    duplicate_legend = [row[:] for row in base]
    duplicate_legend[0][second_column] = first_color

    missing_body = [row[:] for row in base]
    for row in range(2, len(missing_body)):
        for column in range(len(missing_body[0])):
            if missing_body[row][column] == first_color:
                missing_body[row][column] = 0

    unsupported_layout = [row[:] for row in base]
    row0_colors = [color for _, color in entries]
    unsupported_layout[0] = [0] * len(unsupported_layout[0])
    for column, color in zip((0, 3, 4), row0_colors):
        unsupported_layout[0][column] = color

    foreign_body = [row[:] for row in base]
    foreign_color = next(color for color in range(1, 10) if color not in row0_colors)
    blank = next(
        (row, column)
        for row in range(2, len(foreign_body))
        for column in range(len(foreign_body[0]))
        if foreign_body[row][column] == 0
    )
    foreign_body[blank[0]][blank[1]] = foreign_color

    ragged = [row[:] for row in base]
    ragged[-1].pop()

    bool_cell = [row[:] for row in base]
    bool_cell[-1][-1] = True

    return [
        ("legend_touches_body_through_separator", separator_contact),
        ("duplicate_legend_color", duplicate_legend),
        ("missing_body_component", missing_body),
        ("unsupported_legend_layout", unsupported_layout),
        ("foreign_body_color", foreign_body),
        ("ragged_grid", ragged),
        ("boolean_cell", bool_cell),
    ]
