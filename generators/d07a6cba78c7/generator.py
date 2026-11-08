"""Generator for arc_puzzle_bank_21_set5_s:S5_E3.

Rule: exactly one magenta(6) marker appears in column 0.  Its row is the
selected row; the output is that row with column 0 removed.

The canonical examples use compact 5x8 / 6x7 / 6x8 canvases and mostly
monochrome distractor rows.  Default generation therefore keeps an explicit
canonical-profile prior, while the remaining draws use equal-density,
multicolour distractor rows so row count, palette, density, and fixed-position
shortcuts cannot replace reading the magenta marker.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d07a6cba78c7"
TASK_ID = "d07a6cba78c7"
VERSION = "2.0.0"
RULE_HASH = "cf17e3a900c7"
SUMMARY = (
    "A single magenta(6) marker in column 0 selects one nonempty payload "
    "row. Output that row without the marker column. Every generated row is "
    "nonempty and payload rows are pairwise distinct, so the marker is the "
    "only stable selector."
)

INVARIANTS = [
    "grid dimensions are 5..8 rows by 7..10 columns",
    "all cells are integer ARC colors 0..9",
    "column 0 is zero except for exactly one magenta(6) selector",
    "magenta(6) occurs nowhere outside the selector cell",
    "every payload row (columns 1..) is nonempty",
    "payload rows are pairwise distinct",
    "at least two non-marker payload colors occur",
]

COUNTER_HYPOTHESES = [
    "always return a fixed row index",
    "return the densest or sparsest row",
    "return the only multicolour or only monochrome row",
    "return a row selected by its payload color rather than the magenta marker",
    "copy the full input or keep the marker column",
]

_H_LO, _H_HI = 5, 8
_W_LO, _W_HI = 7, 10
_PAYLOAD_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)
_CANONICAL_PROFILES = ((6, 7), (5, 8), (6, 8))
_CANONICAL_SLOT_MOD = 4

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 5..8; every fourth sequential sample is canonical-profile",
        "valid": "5..8",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..10; every fourth sequential sample is canonical-profile",
        "valid": "7..10",
        "doc": "Exact returned grid width.",
    },
    "marker_row": {
        "type": "int",
        "default": "sequential sample_index modulo h; exact override 0..h-1",
        "valid": "0..7",
        "doc": "Exact row containing the magenta selector.",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-aware 2..8; canonical prior uses 5 or 6",
        "valid": "2..8",
        "doc": "Exact number of distinct payload colors, excluding 0 and 6.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", _H_LO, _H_HI),
        ("grid_w", _W_LO, _W_HI),
        ("marker_row", 0, _H_HI - 1),
        ("palette_size", 2, len(_PAYLOAD_COLORS)),
    ):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lo <= value <= hi
        ):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    if (
        overrides.get("grid_h") is not None
        and overrides.get("marker_row") is not None
        and overrides["marker_row"] >= overrides["grid_h"]
    ):
        raise ValueError("marker_row must be smaller than grid_h")


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    """Explicit overrides are band-independent and use the full AXES range."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def semantic_observables(grid) -> dict:
    """Recover task-linked facts from a returned input grid."""
    h = len(grid)
    w = len(grid[0]) if grid and grid[0] else 0
    marker_rows = [r for r in range(h) if w and grid[r][0] == 6]
    marker_row = marker_rows[0] if len(marker_rows) == 1 else None
    payload_rows = [tuple(row[1:]) for row in grid] if w else []
    payload_colors = {
        value
        for row in payload_rows
        for value in row
        if value not in (0, 6)
    }
    row_color_counts = [
        len({value for value in row if value != 0}) for row in payload_rows
    ]
    return {
        "grid_h": h,
        "grid_w": w,
        "marker_row": marker_row,
        "palette_size": len(payload_colors),
        "payload_nonzero_counts": [sum(value != 0 for value in row) for row in payload_rows],
        "payload_rows_unique": len(set(payload_rows)) == len(payload_rows),
        "all_payload_rows_nonempty": all(any(value != 0 for value in row) for row in payload_rows),
        "nonmarker_rows_monochrome": (
            marker_row is not None
            and all(count == 1 for r, count in enumerate(row_color_counts) if r != marker_row)
        ),
        "marker_payload_color_count": (
            row_color_counts[marker_row] if marker_row is not None else None
        ),
        "column0_grammar": (
            marker_row is not None
            and all(grid[r][0] == (6 if r == marker_row else 0) for r in range(h))
        ),
    }


def observe_overrides(grid) -> dict:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful teaching grammar while accepting all canonical inputs."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty row"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]

    errs = []
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errs.append(f"dims {h}x{w} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errs.append("cells must be integer ARC colors in 0..9")
        return errs

    marker_rows = [r for r in range(h) if grid[r][0] == 6]
    if len(marker_rows) != 1:
        errs.append(f"expected exactly one magenta(6) selector in column 0; found {len(marker_rows)}")
        marker_row = None
    else:
        marker_row = marker_rows[0]

    if any(grid[r][0] not in (0, 6) for r in range(h)):
        errs.append("column 0 may contain only zero background and the magenta selector")
    if any(grid[r][c] == 6 for r in range(h) for c in range(1, w)):
        errs.append("magenta(6) may not occur in the payload")

    payload_rows = [tuple(row[1:]) for row in grid]
    empty_rows = [r for r, row in enumerate(payload_rows) if not any(value != 0 for value in row)]
    if empty_rows:
        errs.append(f"payload rows must be nonempty; empty rows={empty_rows}")
    if len(set(payload_rows)) != h:
        errs.append("payload rows must be pairwise distinct")
    payload_colors = {
        value for row in payload_rows for value in row if value not in (0, 6)
    }
    if len(payload_colors) < 2:
        errs.append(f"expected at least two payload colors; found {len(payload_colors)}")
    if marker_row is not None and not any(value != 0 for value in payload_rows[marker_row]):
        errs.append("selected payload row is empty")
    return errs


def _canonical_rows(h, w, marker_row, colors, rng):
    """Construct a canonical-profile scene with monochrome distractor rows."""
    payload_w = w - 1
    rows = [[0] * payload_w for _ in range(h)]

    # Assign distinct colors to the non-marker rows first.  Canonical-prior
    # draws use 5 or 6 colors on 5 or 6 rows, so every distractor can stay
    # monochrome while all requested colors remain observable.
    nonmarker_rows = [r for r in range(h) if r != marker_row]
    rng.shuffle(nonmarker_rows)
    split = min(len(colors), len(nonmarker_rows))
    for r, color in zip(nonmarker_rows, colors[:split]):
        count = rng.randint(2, min(4, payload_w - 1))
        for c in rng.sample(range(payload_w), count):
            rows[r][c] = color

    # Fill any extra distractor rows by reusing colors; this branch is mainly
    # defensive because canonical profiles currently have enough colors.
    for i, r in enumerate(nonmarker_rows[split:]):
        color = colors[i % len(colors)]
        count = rng.randint(2, min(4, payload_w - 1))
        for c in rng.sample(range(payload_w), count):
            rows[r][c] = color

    # The canonical selected row has either one payload color or four.  Preserve
    # that branch support while ensuring every color not assigned to a
    # distractor remains visible in the selected row.
    remaining = list(colors[split:])
    desired_color_count = 4 if len(remaining) > 1 or rng.random() < 0.5 else 1
    marker_colors = list(remaining)
    for color in colors:
        if color not in marker_colors and len(marker_colors) < desired_color_count:
            marker_colors.append(color)
    marker_colors = marker_colors[:desired_color_count]
    marker_cell_count = 4 if desired_color_count == 4 else rng.choice((3, 4))
    slots = rng.sample(range(payload_w), marker_cell_count)
    for i, c in enumerate(slots):
        rows[marker_row][c] = marker_colors[i % len(marker_colors)]

    # Resolve rare row collisions without changing the non-marker monochrome
    # grammar: move one occupied cell within the colliding row.
    for r in range(h):
        for _ in range(payload_w * 2):
            current = tuple(rows[r])
            if all(current != tuple(rows[q]) for q in range(r)):
                break
            occupied = [c for c, value in enumerate(rows[r]) if value]
            empty = [c for c, value in enumerate(rows[r]) if not value]
            if occupied and empty:
                src = rng.choice(occupied)
                dst = rng.choice(empty)
                rows[r][dst] = rows[r][src]
                rows[r][src] = 0
        else:
            raise RuntimeError("failed to make canonical payload rows unique")
    return rows


def _equal_density_rows(h, w, colors, rng):
    """Construct anti-shortcut rows with equal density and two colors each."""
    payload_w = w - 1
    minimum = max(2, (len(colors) + h - 1) // h)
    maximum = max(minimum, min(payload_w - 1, 5))
    cells_per_row = rng.randint(minimum, maximum)

    # Capacity is at least 2*h >= 10, larger than the eight-color payload
    # domain, so every requested color can be witnessed while each row has the
    # same exact distinct-color count.  That makes densest/sparsest and
    # most/fewest-colors selectors tie on every demonstration.
    row_colors = [set() for _ in range(h)]
    row_order = list(range(h))
    rng.shuffle(row_order)
    for i, color in enumerate(colors):
        row_colors[row_order[i % h]].add(color)
    for r in range(h):
        while len(row_colors[r]) < 2:
            row_colors[r].add(rng.choice(colors))

    for _ in range(80):
        rows = [[0] * payload_w for _ in range(h)]
        for r in range(h):
            palette = tuple(row_colors[r])
            positions = rng.sample(range(payload_w), cells_per_row)
            assignments = list(palette)
            assignments.extend(rng.choice(palette) for _ in range(cells_per_row - len(assignments)))
            rng.shuffle(assignments)
            for c, color in zip(positions, assignments):
                rows[r][c] = color
        if len(set(map(tuple, rows))) != h:
            continue
        if {value for row in rows for value in row if value} != set(colors):
            continue
        return rows
    raise RuntimeError("failed to construct unique equal-density payload rows")


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
    layout_rng = ctx.draw_rng("layout")
    band = difficulty or "medium"

    marker_override = overrides.get("marker_row")
    explicit_any = any(value is not None for value in overrides.values())
    # In a standard 3-demo + 1-query episode, sample 0 is canonical-profile
    # while samples 1..3 are anti-shortcut scenes.  The first three samples
    # therefore include the canonical visual idiom plus two demonstrations
    # that equalize density and color-count heuristics, while retaining an
    # exact 25% canonical-profile prior over sequential draws.
    canonical_draw = not explicit_any and sample_index % _CANONICAL_SLOT_MOD == 0

    if canonical_draw:
        profile_h, profile_w = layout_rng.choice(_CANONICAL_PROFILES)
        h_lo = h_hi = profile_h
        w_lo = w_hi = profile_w
        p_lo = p_hi = layout_rng.choice((5, 6))
    elif band == "easy":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 5, 6, 7, 8, 2, 4
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 7, 8, 9, 10, 5, 8
    else:
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 5, 8, 7, 10, 3, 6

    # A standalone marker-row override grows the default height envelope so
    # every globally valid marker row is realizable.  Explicit incompatible
    # grid_h + marker_row pairs fail loudly in _validate_call.
    if marker_override is not None and overrides.get("grid_h") is None:
        h_lo = max(h_lo, marker_override + 1)
        h_hi = max(h_hi, h_lo)

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)
    palette_size = _banded_int(
        ctx,
        overrides,
        "palette_size",
        p_lo,
        p_hi,
        2,
        len(_PAYLOAD_COLORS),
    )
    if overrides.get("marker_row") is not None:
        marker_row = ctx.draw_int("marker_row", 0, h - 1)
    else:
        # Sequential lesson schedule: sample indices 0,1,2,3 select four
        # different rows on every lawful canvas (h >= 5).  Later indices reach
        # every row supported by taller canvases, including row 7.  The final
        # value is still recorded under the exact axis label for v6 provenance.
        scheduled_row = sample_index % h
        marker_row = ctx.draw_int("marker_row", scheduled_row, scheduled_row)

    colors = tuple(layout_rng.sample(_PAYLOAD_COLORS, palette_size))
    if canonical_draw:
        payload_rows = _canonical_rows(h, w, marker_row, colors, layout_rng)
    else:
        payload_rows = _equal_density_rows(h, w, colors, layout_rng)

    grid = full_grid(h, w, 0)
    for r, payload in enumerate(payload_rows):
        grid[r][1:] = payload
    grid[marker_row][0] = 6

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator error: {errors}")
    return grid
