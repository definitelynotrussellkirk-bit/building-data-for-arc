"""Generator for arc_puzzle_bank_21_set20_s:S20_E6.

Rule: crop the nonzero template left of the full-height color-9 divider,
find exact (zero-as-wildcard) copies on the right board, and emit the number
of starts in every board row.

The public axes are exact and observable from the returned grid.  Incompatible
geometry/count combinations are rejected rather than silently clamped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "860cbb625ca0"
VERSION = "1.3.1"
TASK_ID = "860cbb625ca0"
RULE_HASH = "4754a7505a36"
SUMMARY = (
    "A cropped 3x3 motif sits left of a full-height color-9 divider; the right "
    "board contains exact zero-as-wildcard copies in controlled start rows, and "
    "the output is a 1-row strip of per-start-row match counts."
)

INVARIANTS = [
    "exactly one full-height color-9 divider separates template and board",
    "the left panel crops to one 3x3 asymmetric motif",
    "the board contains the requested number of match-start rows",
    "every positive row count is the requested density count",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
POSITION_BIASES = ("top", "scattered", "bottom")
DENSITIES = ("sparse", "medium", "dense")
DEGENERATE_TEXTURES = ("no_template", "no_matches", "all_rows_match")
HELPFUL_TEXTURES = PALETTE_KINDS

# Shape is deliberately asymmetric.  Zero cells remain canonical wildcards.
TEMPLATE_MASK = [[1, 1, 1], [1, 0, 0], [1, 1, 1]]
TEMPLATE = [[6 if value else 0 for value in row] for row in TEMPLATE_MASK]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 6..16",
        "valid": "6..16",
        "doc": "Full returned input height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..30",
        "valid": "9..30",
        "doc": "Full returned input width, including template and divider.",
    },
    "palette_kind": {
        "type": "enum",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
        "doc": "Exact motif/distractor palette family.",
    },
    "n_match_rows": {
        "type": "int",
        "default": "rng 1..geometry maximum",
        "valid": "1..6 (subject to grid_h and position_bias)",
        "doc": "Number of rows with at least one exact match start.",
    },
    "palette_size": {
        "type": "int",
        "default": "same as n_distinct_colors",
        "valid": "1..2",
        "doc": "Alias of n_distinct_colors; conflicting values are rejected.",
    },
    "position_bias": {
        "type": "enum",
        "default": "rng",
        "valid": "|".join(POSITION_BIASES),
        "doc": "Whether selected match rows are the first, a crossed subset, or the last feasible rows.",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "rng 1..2",
        "valid": "1..2",
        "doc": "Number of non-background/non-divider colors in the returned grid.",
    },
    "density": {
        "type": "enum",
        "default": "rng among geometry-compatible choices",
        "valid": "|".join(DENSITIES),
        "doc": "Exact matches per selected row: sparse=1, medium=2, dense=3.",
    },
}

_DENSITY_COUNTS = {"sparse": 1, "medium": 2, "dense": 3}
_FIXED_PALETTES = {
    "default": (6, 3),
    "warm": (2, 4),
    "cool": (8, 1),
}


def _strict_int(value, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool)")
    return value


def _normalise_overrides(overrides: dict) -> tuple[dict, str | None]:
    known = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    values = dict(overrides)
    for name in ("grid_h", "grid_w", "n_match_rows", "palette_size", "n_distinct_colors"):
        if values.get(name) is not None:
            values[name] = _strict_int(values[name], name)
    texture = values.pop("texture", None)
    if texture is not None:
        if type(texture) is not str or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES + DEGENERATE_TEXTURES}")
        if texture in HELPFUL_TEXTURES:
            existing = values.get("palette_kind")
            if existing is not None and existing != texture:
                raise ValueError("helpful texture and palette_kind disagree")
            values["palette_kind"] = texture

    psize = values.get("palette_size")
    ncolors = values.get("n_distinct_colors")
    if psize is not None:
        psize = _strict_int(psize, "palette_size")
    if ncolors is not None:
        ncolors = _strict_int(ncolors, "n_distinct_colors")
    if psize is not None and ncolors is not None and psize != ncolors:
        raise ValueError("palette_size and n_distinct_colors must agree")
    if psize is not None or ncolors is not None:
        selected = psize if psize is not None else ncolors
        values["palette_size"] = selected
        values["n_distinct_colors"] = selected
    return values, texture


def _template(color: int):
    return [[color if value else 0 for value in row] for row in TEMPLATE_MASK]


def _stamp_required(board, template, row: int, col: int) -> None:
    for dr, line in enumerate(template):
        for dc, value in enumerate(line):
            if value:
                current = board[row + dr][col + dc]
                if current not in (0, value):
                    raise ValueError("incompatible stamp overlap")
                board[row + dr][col + dc] = value


def _match_at(board, template, row: int, col: int) -> bool:
    return all(
        value == 0 or board[row + dr][col + dc] == value
        for dr, line in enumerate(template)
        for dc, value in enumerate(line)
    )


def _histogram(board, template) -> list[int]:
    h, w = len(board), len(board[0])
    th, tw = len(template), len(template[0])
    counts = [0] * h
    for row in range(max(0, h - th + 1)):
        for col in range(max(0, w - tw + 1)):
            if _match_at(board, template, row, col):
                counts[row] += 1
    return counts


def _split(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 1:
        raise ValueError("expected exactly one full-height color-9 divider")
    divider = dividers[0]
    if divider == 0 or divider == w - 1:
        raise ValueError("divider must leave two nonempty panels")
    left = [row[:divider] for row in grid]
    board = [row[divider + 1 :] for row in grid]
    cells = [
        (r, c)
        for r, row in enumerate(left)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [[0]], board
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    template = [row[c0 : c1 + 1] for row in left[r0 : r1 + 1]]
    return template, board


def _palette(ctx, kind: str) -> tuple[int, int]:
    if kind in _FIXED_PALETTES:
        return _FIXED_PALETTES[kind]
    motif = ctx.draw_choice("varied_motif_color", (5, 7))
    distractor = ctx.draw_choice("varied_distractor_color", (1, 3, 4))
    return motif, distractor


def _row_schedule(h: int, n_rows: int, bias: str, rng) -> list[int]:
    minimum_candidates = n_rows + 1
    if bias == "scattered" and n_rows == 1:
        # With only two candidate rows, the sole interior choice is also the
        # bottom edge, so the requested bias would not be observable.
        minimum_candidates = 3
    all_candidates = [
        rows
        for parity in (0, 1)
        if len(rows := list(range(parity, h - 2, 2))) >= minimum_candidates
    ]
    if not all_candidates:
        raise ValueError(
            f"n_match_rows={n_rows} is not identifiable at grid_h={h}; increase grid_h"
        )
    rows = list(rng.choice(all_candidates))
    first = rows[:n_rows]
    last = rows[-n_rows:]
    if bias == "top":
        return first
    if bias == "bottom":
        return last
    if n_rows == 1:
        return [rows[len(rows) // 2]]
    selected = [rows[0], rows[-1]]
    middle = rows[1:-1]
    rng.shuffle(middle)
    selected.extend(middle[: n_rows - 2])
    selected.sort()
    if selected == first or selected == last:
        raise ValueError("scattered position profile collapsed to an edge profile")
    return selected


def _candidate_columns(board_w: int, count: int) -> list[int]:
    columns = list(range(0, board_w - 2, 4))
    if len(columns) < count:
        raise ValueError(
            f"density requires {count} separated matches per row but board width {board_w} supports {len(columns)}"
        )
    return columns


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values, texture = _normalise_overrides(overrides)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    h = ctx.draw_int_diff("grid_h", 6, 16)
    total_w = ctx.draw_int_diff("grid_w", 9, 30)
    board_w = total_w - 4
    if board_w < 5:
        raise ValueError("grid_w must leave a board at least five columns wide")

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    n_colors = ctx.draw_int_strict("n_distinct_colors", 1, 2)
    # Pin the legacy alias to the same exact value, consuming either override.
    ctx.draw_int_strict("palette_size", n_colors, n_colors)

    feasible_density = tuple(
        name
        for name, count in _DENSITY_COUNTS.items()
        if len(range(0, board_w - 2, 4)) >= count
    )
    density = ctx.draw_choice("density", feasible_density)
    matches_per_row = _DENSITY_COUNTS[density]

    max_rows = max((len(list(range(parity, h - 2, 2))) - 1 for parity in (0, 1)), default=0)
    max_rows = min(6, max_rows)
    if max_rows < 1:
        raise ValueError("grid_h leaves no identifiable match-row schedule")
    n_match_rows = ctx.draw_int_strict("n_match_rows", 1, max_rows)

    supports_scattered = any(
        len(list(range(parity, h - 2, 2))) >= (3 if n_match_rows == 1 else n_match_rows + 1)
        for parity in (0, 1)
    )
    feasible_biases = POSITION_BIASES if supports_scattered else ("top", "bottom")
    if values.get("position_bias") == "scattered" and not supports_scattered:
        raise ValueError(
            f"position_bias='scattered' is not observable at grid_h={h}, "
            f"n_match_rows={n_match_rows}"
        )
    position_bias = ctx.draw_choice("position_bias", feasible_biases)

    motif_color, distractor_color = _palette(ctx, palette_kind)
    template = _template(motif_color)
    template_panel = full_grid(h, 3, 0)
    _stamp_required(template_panel, template, 0, 0)
    board = full_grid(h, board_w, 0)

    layout_rng = ctx.draw_rng("layout")
    rows = _row_schedule(h, n_match_rows, position_bias, layout_rng)
    columns = _candidate_columns(board_w, matches_per_row)
    for row in rows:
        choices = list(columns)
        layout_rng.shuffle(choices)
        for col in sorted(choices[:matches_per_row]):
            _stamp_required(board, template, row, col)

    # A second color only supplies nuisance cells.  It cannot satisfy a required
    # motif cell, but may occupy wildcard slots exactly as the canonical rule permits.
    if n_colors == 2:
        clutter_rng = ctx.draw_rng("distractors")
        candidates = [(r, c) for r in range(h) for c in range(board_w) if board[r][c] == 0]
        clutter_rng.shuffle(candidates)
        target = min(len(candidates), 2 + n_match_rows + matches_per_row)
        for r, c in candidates[:target]:
            board[r][c] = distractor_color

    actual = _histogram(board, template)
    positive = [index for index, value in enumerate(actual) if value]
    if positive != rows or any(actual[row] != matches_per_row for row in rows):
        raise AssertionError(
            f"constructed profile drifted: expected rows={rows}, count={matches_per_row}, actual={actual}"
        )
    return assemble_vertical_panels([template_panel, board])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public axis exactly from a generated grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    template, board = _split(grid)
    if len(template) != 3 or len(template[0]) != 3:
        raise ValueError("template must crop to 3x3")
    nonzero = {value for row in grid for value in row if value not in (0, 9)}
    motif_values = {value for row in template for value in row if value}
    if len(motif_values) != 1:
        raise ValueError("template must use one motif color")
    motif = next(iter(motif_values))
    palette_kind = {6: "default", 2: "warm", 8: "cool", 5: "varied", 7: "varied"}.get(motif)
    if palette_kind is None:
        raise ValueError("unknown generated palette")

    counts = _histogram(board, template)
    match_rows = [index for index, value in enumerate(counts) if value]
    if not match_rows:
        raise ValueError("generated grid has no matches")
    positive_counts = {counts[index] for index in match_rows}
    if len(positive_counts) != 1:
        raise ValueError("generated rows do not share one density")
    count = next(iter(positive_counts))
    density = {1: "sparse", 2: "medium", 3: "dense"}.get(count)
    if density is None:
        raise ValueError("generated density is outside the declared surface")

    parity = match_rows[0] % 2
    if any(row % 2 != parity for row in match_rows):
        raise ValueError("match-row schedule left the declared parity surface")
    candidates = list(range(parity, len(grid) - 2, 2))
    n_rows = len(match_rows)
    if match_rows == candidates[:n_rows]:
        bias = "top"
    elif match_rows == candidates[-n_rows:]:
        bias = "bottom"
    else:
        bias = "scattered"

    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_kind": palette_kind,
        "n_match_rows": n_rows,
        "palette_size": len(nonzero),
        "position_bias": bias,
        "n_distinct_colors": len(nonzero),
        "density": density,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid must use exact integer colors 0..9"]
    try:
        observed = observe_overrides(grid)
    except ValueError as exc:
        return [str(exc)]
    if not (6 <= observed["grid_h"] <= 16 and 9 <= observed["grid_w"] <= 30):
        errs.append("grid dimensions fall outside the declared surface")
    if not 1 <= observed["n_match_rows"] <= 6:
        errs.append("match-row count falls outside 1..6")
    return errs


def _draw_from_degenerate(name):
    h, board_w = 8, 11
    template_panel = full_grid(h, 3, 0)
    template = _template(6)
    board = full_grid(h, board_w, 0)
    if name != "no_template":
        _stamp_required(template_panel, template, 0, 0)
    if name == "no_template":
        _stamp_required(board, template, 1, 0)
    elif name == "all_rows_match":
        for row in range(h - 2):
            _stamp_required(board, template, row, 0)
    elif name != "no_matches":
        raise ValueError(f"unknown degenerate texture: {name}")
    return assemble_vertical_panels([template_panel, board])
