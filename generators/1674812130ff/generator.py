"""Generator for ARC task e729b7be / 1674812130ff.

The official scenes contain a colored figure on the left of a vertical
color-4 axis.  Color-8 anchors mark the axis centre and the two ends of the
centre row.  The right half is blank (color 7).  The oracle preserves every
non-7 cell and fills each 7 cell from its 180-degree counterpart, completing
rotational symmetry without overwriting the axis or anchors.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1674812130ff"
TASK_ID = "1674812130ff"
VERSION = "3.0.0"  # canonical one-sided grammar, honest overrides, structural checker
RULE_HASH = "e1a503d2431f"  # sha256[:12] of whitespace-normalized canonical rule

BACKGROUND = 7
DIVIDER = 4
ANCHOR = 8
SOURCE_COLORS = (0, 1, 2, 3, 5, 6, 9)
GRID_SIZES = (13, 15, 17, 19, 21)
LAYOUTS = ("terraced", "wedge", "hourglass", "mosaic")

SUMMARY = (
    "An odd square color-7 grid has a full vertical color-4 axis through its "
    "middle column.  The axis centre and both ends of the middle row are "
    "color 8.  A connected, multi-color figure occupies only the left side "
    "and touches the axis on every active row; the matching right-side cells "
    "are blank.  Preserve non-7 cells and copy each non-7 cell into a blank "
    "cell at its 180-degree rotational counterpart, thereby completing the "
    "figure while leaving the axis and anchors unchanged."
)

INVARIANTS = [
    "odd square size 13..21 with color 7 as the background",
    "middle column is color 4 except for a color-8 centre anchor",
    "the middle-row endpoints are the only other color-8 anchors",
    "a contiguous multi-row source figure lies only left of the axis",
    "every active source row touches the axis and uses 2..7 non-marker colors",
    "the right target half is blank except for its endpoint anchor",
    "180-degree completion changes the grid and differs from horizontal reflection",
]

EXAMPLES_NEEDED = 4

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware with a 25% canonical-profile prior",
        "valid": "13|15|17|19|21",
    },
    "fg_palette_size": {
        "type": "int",
        "default": "difficulty-aware with canonical values 3, 4, 4, and 7",
        "valid": "2..7",
    },
    "shape_width": {
        "type": "int",
        "default": "difficulty-aware maximum source width",
        "valid": "3..7",
    },
    "layout": {
        "type": "str",
        "default": "rng over canonical-like connected profiles",
        "valid": "|".join(LAYOUTS),
    },
}

# Linked morphology extracted from all three official train inputs and the held-
# out test input.  These are parameter profiles, not copied grids: placement,
# row widths, colors, and cell assignments remain keyed-random.
_CANONICAL_PROFILES: tuple[dict[str, Any], ...] = (
    {"grid_size": 17, "fg_palette_size": 4, "shape_width": 6, "layout": "terraced"},
    {"grid_size": 15, "fg_palette_size": 3, "shape_width": 5, "layout": "wedge"},
    {"grid_size": 17, "fg_palette_size": 4, "shape_width": 6, "layout": "mosaic"},
    {"grid_size": 19, "fg_palette_size": 7, "shape_width": 7, "layout": "hourglass"},
)


def _draw_int_axis(ctx, name: str, lo: int, hi: int, profile_value: int | None) -> int:
    """Draw an exact integer axis while preserving full-domain overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    if profile_value is not None:
        return ctx.draw_int(name, profile_value, profile_value)
    return ctx.draw_int_diff(name, lo, hi)


def _draw_scene_axes(ctx, profile: dict[str, Any] | None) -> tuple[int, int, int, str]:
    """Resolve jointly feasible axes without silently clamping overrides."""
    size_override = ctx.overrides.get("grid_size") is not None
    width_override = ctx.overrides.get("shape_width") is not None

    if size_override:
        size = ctx.draw_choice("grid_size", GRID_SIZES)
        max_width = min(7, size // 2 - 2)
        if width_override:
            shape_width = ctx.draw_int("shape_width", 3, 7)
            if shape_width > max_width:
                raise ValueError(
                    f"grid_size={size} supports shape_width at most {max_width}, "
                    f"not {shape_width}"
                )
        else:
            shape_width = ctx.draw_int_diff("shape_width", 3, max_width)
    else:
        profile_width = None if profile is None else int(profile["shape_width"])
        shape_width = _draw_int_axis(ctx, "shape_width", 3, 7, profile_width)
        legal_sizes = tuple(size for size in GRID_SIZES if size // 2 - 2 >= shape_width)
        if profile is not None:
            profile_size = int(profile["grid_size"])
            if profile_size not in legal_sizes:
                raise ValueError("canonical profile has incompatible size and width")
            size = ctx.draw_choice("grid_size", (profile_size,))
        else:
            band_sizes = {
                "easy": (13, 15, 17),
                "medium": (15, 17, 19),
                "hard": (17, 19, 21),
            }.get(ctx.difficulty, GRID_SIZES)
            choices = tuple(size for size in band_sizes if size in legal_sizes) or legal_sizes
            size = ctx.draw_choice("grid_size", choices)

    profile_palette = None if profile is None else int(profile["fg_palette_size"])
    palette_size = _draw_int_axis(ctx, "fg_palette_size", 2, 7, profile_palette)

    if ctx.overrides.get("layout") is not None:
        layout = ctx.draw_choice("layout", LAYOUTS)
    elif profile is not None:
        layout = ctx.draw_choice("layout", (str(profile["layout"]),))
    else:
        layout = ctx.draw_choice("layout", LAYOUTS)
    return size, palette_size, shape_width, layout


def _active_rows(size: int, layout: str, rng) -> list[int]:
    """Choose one contiguous, asymmetric vertical support interval."""
    centre = size // 2
    min_span = max(7, size - 8)
    max_span = size - 4
    span = rng.randint(min_span, max_span)
    top_lo = 1
    top_hi = size - 1 - span
    top = rng.randint(top_lo, top_hi)
    rows = list(range(top, top + span))

    # A source support centred perfectly around the middle row can make a
    # horizontal reflection rival harder to falsify.  Shift it when possible.
    if rows[0] + rows[-1] == 2 * centre:
        if rows[-1] + 1 < size - 1:
            rows = [r + 1 for r in rows]
        elif rows[0] - 1 > 0:
            rows = [r - 1 for r in rows]
    return rows


def _row_widths(layout: str, rows: list[int], max_width: int, rng) -> list[int]:
    """Return connected row widths, always realizing the requested maximum."""
    count = len(rows)
    if layout == "terraced":
        pivot = max(1, min(count - 2, count // 2 + rng.choice((-2, -1, 1))))
        widths = [
            1 + round((max_width - 1) * (1 - abs(i - pivot) / max(pivot, count - 1 - pivot)))
            for i in range(count)
        ]
    elif layout == "wedge":
        pivot = max(2, min(count - 2, count // 2 + rng.choice((-1, 0, 1))))
        widths = [
            1 + round((max_width - 1) * min(i / pivot, 1.0))
            if i <= pivot
            else max(1, max_width - (i - pivot + 1) // 2)
            for i in range(count)
        ]
    elif layout == "hourglass":
        pivot = max(1, min(count - 2, count // 2 + rng.choice((-1, 1))))
        widths = []
        for i in range(count):
            distance = abs(i - pivot) / max(pivot, count - 1 - pivot)
            widths.append(1 + round((max_width - 1) * (0.35 + 0.65 * distance)))
    else:  # mosaic: bounded random walk with one deliberately broad row
        current = rng.randint(1, max_width)
        widths = []
        for _ in rows:
            current = max(1, min(max_width, current + rng.choice((-2, -1, 0, 1, 2))))
            widths.append(current)

    widths = [max(1, min(max_width, int(width))) for width in widths]
    broad_index = rng.randrange(count)
    widths[broad_index] = max_width
    # Avoid a vertically palindromic support, which would weaken the 180-vs-
    # horizontal-reflection distinction even before colors are considered.
    if widths == list(reversed(widths)):
        idx = 0 if widths[0] < max_width else count - 1
        widths[idx] = widths[idx] + 1 if widths[idx] < max_width else widths[idx] - 1
    # Every declared layout must remain a substantive lesson even at the
    # smallest easy boundary.  Raise narrow rows without changing max_width.
    cursor = count // 2
    while sum(widths) < 12:
        if widths[cursor] < max_width:
            widths[cursor] += 1
        cursor = (cursor + 1) % count
    return widths


def _paint_source(
    grid,
    rows: list[int],
    widths: list[int],
    palette: tuple[int, ...],
    layout: str,
    rng,
) -> None:
    """Paint canonical-scale regions with both large and separated components."""
    centre = len(grid) // 2
    ordered_palette = list(palette)
    rng.shuffle(ordered_palette)
    count = len(rows)

    if layout in {"mosaic", "hourglass"}:
        # Two-by-two-ish blocks reproduce the official task's many separated
        # same-color components.  A three-row dominant band supplies the
        # canonical large-component scale at the same time.
        band_start = max(0, count // 2 - 1)
        band_stop = min(count, band_start + 3)
        phase = rng.randrange(len(ordered_palette))
        for index, (row, width) in enumerate(zip(rows, widths)):
            for col in range(centre - width, centre):
                depth = centre - 1 - col
                if band_start <= index < band_stop:
                    color = ordered_palette[0]
                else:
                    block_row = index // 2
                    block_col = depth // 2
                    color = ordered_palette[(block_row + block_col + phase) % len(ordered_palette)]
                grid[row][col] = color
    else:
        # Broader row bands cover the simpler official profiles while small
        # two-cell notches stop every color from collapsing into one component.
        for index, (row, width) in enumerate(zip(rows, widths)):
            color_index = min(
                len(ordered_palette) - 1,
                index * len(ordered_palette) // count,
            )
            color = ordered_palette[color_index]
            for col in range(centre - width, centre):
                grid[row][col] = color
            if width >= 4 and index % 3 == 1:
                notch_color = ordered_palette[(color_index + 1) % len(ordered_palette)]
                grid[row][centre - width] = notch_color
                grid[row][centre - width + 1] = notch_color

    # Guarantee every declared palette color survives any block coincidences.
    cells = [
        (row, col)
        for row, width in zip(rows, widths)
        for col in range(centre - width, centre)
    ]
    rng.shuffle(cells)
    from collections import Counter
    counts = Counter(grid[row][col] for row, col in cells)
    for color in ordered_palette:
        if counts[color]:
            continue
        donor = next(
            (row, col)
            for row, col in cells
            if counts[grid[row][col]] > 1
        )
        old_color = grid[donor[0]][donor[1]]
        grid[donor[0]][donor[1]] = color
        counts[old_color] -= 1
        counts[color] += 1


def _source_rival_delta(grid) -> int:
    """Right-half cells where 180 fill and horizontal fill would disagree."""
    size = len(grid)
    centre = size // 2
    return sum(
        grid[row][col] != grid[size - 1 - row][col]
        for row in range(size)
        for col in range(1, centre)
    )


def _ensure_rival_distinction(grid, palette: tuple[int, ...]) -> None:
    """Force at least four witnesses without deleting a palette singleton."""
    if _source_rival_delta(grid) >= 4:
        return
    from collections import Counter
    size = len(grid)
    centre = size // 2
    counts = Counter(
        grid[row][col]
        for row in range(size)
        for col in range(1, centre)
        if grid[row][col] in palette
    )
    for row in range(size):
        mirror_row = size - 1 - row
        if row >= mirror_row:
            continue
        for col in range(1, centre):
            left = grid[row][col]
            mirrored_left = grid[mirror_row][col]
            if left == mirrored_left and left in palette and counts[left] > 1:
                replacement = next(color for color in palette if color != left)
                grid[row][col] = replacement
                counts[left] -= 1
                counts[replacement] += 1
            elif left == mirrored_left and mirrored_left in palette and counts[mirrored_left] > 1:
                replacement = next(color for color in palette if color != mirrored_left)
                grid[mirror_row][col] = replacement
                counts[mirrored_left] -= 1
                counts[replacement] += 1
            if _source_rival_delta(grid) >= 4:
                return
    raise ValueError("could not construct a palette-preserving rival witness")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = None
    if not overrides and int(sample_index) % 4 == 0:
        profile = _CANONICAL_PROFILES[(int(sample_index) // 4) % len(_CANONICAL_PROFILES)]

    size, palette_size, shape_width, layout = _draw_scene_axes(ctx, profile)
    centre = size // 2
    grid = full_grid(size, size, BACKGROUND)
    for row in range(size):
        grid[row][centre] = DIVIDER
    grid[centre][centre] = ANCHOR
    grid[centre][0] = ANCHOR
    grid[centre][size - 1] = ANCHOR

    layout_rng = ctx.draw_rng("source_geometry")
    rows = _active_rows(size, layout, layout_rng)
    widths = _row_widths(layout, rows, shape_width, layout_rng)
    palette = ctx.draw_distinct_colors(
        "source_palette", n=palette_size, exclude={BACKGROUND, DIVIDER, ANCHOR}
    )
    _paint_source(grid, rows, widths, palette, layout, ctx.draw_rng("source_colors"))
    _ensure_rival_distinction(grid, palette)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": dict(overrides)})
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid


def rule_mirror(grid):
    """Pure Python mirror used only for focused tests; Racket is authoritative."""
    source = deepcopy(grid)
    if not source or not source[0]:
        return source
    h, w = len(source), len(source[0])
    return [
        [
            source[r][c]
            if source[r][c] != BACKGROUND
            else (
                source[h - 1 - r][w - 1 - c]
                if source[h - 1 - r][w - 1 - c] != BACKGROUND
                else BACKGROUND
            )
            for c in range(w)
        ]
        for r in range(h)
    ]


def _horizontal_fill(grid):
    h, w = len(grid), len(grid[0])
    return [
        [
            grid[r][c]
            if grid[r][c] != BACKGROUND
            else (grid[r][w - 1 - c] if grid[r][w - 1 - c] != BACKGROUND else BACKGROUND)
            for c in range(w)
        ]
        for r in range(h)
    ]


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return facts, ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    size = len(grid)
    facts["grid_size"] = size
    if size != width or size not in GRID_SIZES:
        errors.append(f"grid must be an odd square with size in {GRID_SIZES}, got {size}x{width}")
        return facts, errors

    centre = size // 2
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(f"invalid ARC color {value!r} at ({r},{c})")

    expected_axis = [DIVIDER] * size
    expected_axis[centre] = ANCHOR
    actual_axis = [grid[r][centre] for r in range(size)]
    if actual_axis != expected_axis:
        errors.append("middle column must be all color 4 except a color-8 centre")

    anchors = {(r, c) for r in range(size) for c in range(size) if grid[r][c] == ANCHOR}
    expected_anchors = {(centre, 0), (centre, centre), (centre, size - 1)}
    if anchors != expected_anchors:
        errors.append(f"expected exactly the three canonical color-8 anchors, found {sorted(anchors)}")

    right_intrusions = [
        (r, c, grid[r][c])
        for r in range(size)
        for c in range(centre + 1, size)
        if (r, c) != (centre, size - 1) and grid[r][c] != BACKGROUND
    ]
    if right_intrusions:
        errors.append("right target half must be blank color 7 except for its endpoint anchor")

    source_cells = [
        (r, c, grid[r][c])
        for r in range(size)
        for c in range(1, centre)
        if grid[r][c] not in (BACKGROUND, DIVIDER, ANCHOR)
    ]
    source_palette = sorted({value for _, _, value in source_cells})
    facts["fg_palette_size"] = len(source_palette)
    facts["source_cell_count"] = len(source_cells)
    facts["source_palette"] = source_palette
    if not (2 <= len(source_palette) <= 7):
        errors.append(f"source figure must use 2..7 colors, found {len(source_palette)}")
    if len(source_cells) < 12:
        errors.append(f"source figure is too small ({len(source_cells)} cells)")

    active_rows = sorted({r for r, _, _ in source_cells})
    facts["active_rows"] = active_rows
    if len(active_rows) < 7:
        errors.append(f"source figure must span at least 7 rows, found {len(active_rows)}")
    if active_rows and active_rows != list(range(active_rows[0], active_rows[-1] + 1)):
        errors.append("source figure rows must form one contiguous interval")
    for row in active_rows:
        if grid[row][centre - 1] in (BACKGROUND, DIVIDER, ANCHOR):
            errors.append(f"active source row {row} does not touch the divider")
            break

    extents = [
        centre - min(c for rr, c, _ in source_cells if rr == row)
        for row in active_rows
    ] if active_rows else []
    facts["shape_width"] = max(extents, default=0)
    if facts["shape_width"] < 3:
        errors.append(f"source figure must reach at least 3 cells left of the divider")
    if any(c == 0 for _, c, _ in source_cells):
        errors.append("source figure must not merge with the left endpoint anchor")

    if not errors:
        completed = rule_mirror(grid)
        changed = sum(
            grid[r][c] != completed[r][c]
            for r in range(size)
            for c in range(size)
        )
        facts["changed_cells"] = changed
        if changed < 12:
            errors.append(f"180-degree completion changes too few cells ({changed})")
        if completed != [list(reversed(row)) for row in reversed(completed)]:
            errors.append("oracle completion is not 180-degree symmetric")
        rival_delta = _source_rival_delta(grid)
        facts["horizontal_rival_delta"] = rival_delta
        if rival_delta < 4:
            errors.append("scene does not distinguish 180-degree completion from horizontal reflection")

    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, or shortcut-prone teaching scenes."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact semantic axis from a returned scene."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "fg_palette_size": int(facts["fg_palette_size"]),
        "shape_width": int(facts["shape_width"]),
    }
