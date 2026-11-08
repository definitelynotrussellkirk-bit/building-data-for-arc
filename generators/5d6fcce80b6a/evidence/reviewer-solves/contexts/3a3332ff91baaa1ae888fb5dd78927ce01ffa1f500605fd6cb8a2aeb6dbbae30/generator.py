"""Generator for ARC task fb791726 / content hash 5d6fcce80b6a.

The authoritative rule doubles the canvas in both dimensions.  It copies the
input into the top-left and bottom-right quadrants, leaves the off-diagonal
quadrants zero, and replaces every all-zero source row at or before the last
non-zero row with a full-width row of colour 3 in both vertical halves.
Rows after the last non-zero row remain zero.

The canonical examples do not distinguish leading blank rows from internal
blank rows.  This generator follows the selected Racket authority exactly and
includes leading-row controls so the emitted lessons identify that authority
rather than the weaker "strictly between coloured rows" shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d6fcce80b6a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "652672c3e3c3"

SUMMARY = (
    "Double the input to a 2x2 canvas, copy it only on the main block diagonal, "
    "and paint colour-3 rows for every empty source row at or before the last "
    "non-empty row.  Empty rows after the last non-empty row stay blank."
)

INVARIANTS = [
    "generated inputs are rectangular 3..8 by 3..8 ARC grids",
    "input colour 3 is reserved for the output and never appears in an input",
    "every input has at least two non-empty rows and at least one qualifying empty row",
    "scene_profile is exactly recoverable from leading/internal/trailing empty-row counts",
    "palette_profile is exactly recoverable from the set of non-zero input colours",
    "four consecutive sample indices cover internal, leading, trailing, and multiple-separator controls",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCENE_PROFILES = (
    "internal_anchor",
    "leading_control",
    "trailing_control",
    "multiple_control",
)
PALETTE_PROFILES = (
    "single_4",
    "single_7",
    "single_8",
    "single_9",
    "pair_12",
    "pair_56",
    "triple_149",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic internal/leading/trailing/multiple by sample_index",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_profile": {
        "type": "str",
        "default": "canonical single colours plus scheduled multicolour controls",
        "valid": "|".join(PALETTE_PROFILES),
    },
}

_PALETTES = {
    "single_4": (4,),
    "single_7": (7,),
    "single_8": (8,),
    "single_9": (9,),
    "pair_12": (1, 2),
    "pair_56": (5, 6),
    "triple_149": (1, 4, 9),
}
_PALETTE_BY_SET = {frozenset(colors): name for name, colors in _PALETTES.items()}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the exact structural profile used by the ordinary schedule."""
    _band(difficulty)
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_palette(seed: int, sample_index: int) -> str:
    residue = sample_index % 4
    block = (sample_index // 4 + int(seed)) % 4
    if residue == 0:
        return ("single_8", "single_4", "single_7", "single_9")[block]
    if residue == 1:
        return "pair_12"
    if residue == 2:
        return ("single_9", "single_7", "single_4", "single_8")[block]
    return "pair_56" if block % 2 == 0 else "triple_149"


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: str, values: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, list(values))
    return ctx.draw_choice(name, [scheduled])


def _row_mask(profile: str, band: str, sample_index: int) -> tuple[int, int, tuple[bool, ...]]:
    """Return (h, w, nonempty-row mask) for one exact semantic profile."""
    variant = (sample_index // 4) % 2
    if profile == "internal_anchor":
        if band == "easy":
            h, w = (3, 3) if variant == 0 else (4, 5)
        elif band == "medium":
            h, w = (5, 5) if variant == 0 else (6, 6)
        else:
            h, w = (7, 7) if variant == 0 else (8, 7)
        sep = 1 if h <= 4 else 1 + variant
        mask = tuple(r != sep for r in range(h))
        return h, w, mask

    if profile == "leading_control":
        if band == "easy":
            h, w, leading = 4, 5, 1
        elif band == "medium":
            h, w, leading = 5, 6, 1 + variant
        else:
            h, w, leading = 7, 8, 2
        mask = tuple(r >= leading for r in range(h))
        return h, w, mask

    if profile == "trailing_control":
        if band == "easy":
            h, w, trailing = 4, 4, 1
        elif band == "medium":
            h, w, trailing = 6, 6, 2 if variant else 1
        else:
            h, w, trailing = 7, 7, 4 if variant == 0 else 2
        last_colored = h - trailing - 1
        sep = 1
        mask = tuple(r <= last_colored and r != sep for r in range(h))
        return h, w, mask

    if profile == "multiple_control":
        if band == "easy":
            h, w = 5, 5
            empty = {1, 3}
        elif band == "medium":
            h, w = 6, 6
            empty = {1, 4}
        else:
            h, w = 8, 7
            empty = {1, 3, 6}
        mask = tuple(r not in empty for r in range(h))
        return h, w, mask

    raise ValueError(f"unknown scene_profile: {profile!r}")


def _paint_content(
    h: int,
    w: int,
    nonempty_mask: tuple[bool, ...],
    palette: tuple[int, ...],
    rng,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    content_rows = [r for r, nonempty in enumerate(nonempty_mask) if nonempty]
    if len(content_rows) < 2:
        raise RuntimeError("scene profile must provide at least two content rows")

    # Give every content row a distinct, asymmetric footprint.  At least one
    # row has multiple cells, so singleton-marker and fixed-column shortcuts
    # cannot fit an ordinary four-example lesson.
    used_positions: list[tuple[int, int]] = []
    for index, r in enumerate(content_rows):
        count = min(w, 1 + (index % 3))
        columns = rng.sample(range(w), count)
        for offset, c in enumerate(columns):
            grid[r][c] = palette[(index + offset) % len(palette)]
            used_positions.append((r, c))

    # Ensure every declared palette colour is visibly present even on the
    # smallest profile, then add sparse independent texture for variation.
    palette_positions = [(r, c) for r in content_rows for c in range(w)]
    for color, (r, c) in zip(palette, rng.sample(palette_positions, len(palette))):
        grid[r][c] = color
        used_positions.append((r, c))

    for r in content_rows:
        for c in range(w):
            if grid[r][c] == 0 and rng.random() < 0.18:
                grid[r][c] = rng.choice(palette)

    # A pathological overwrite cannot empty a row, but keep the invariant
    # explicit and deterministic for future edits.
    for index, r in enumerate(content_rows):
        if not any(grid[r]):
            grid[r][(index * 3) % w] = palette[index % len(palette)]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    profile = _draw_axis(
        ctx,
        overrides,
        "scene_profile",
        schedule_profile(seed, sample_index, band),
        SCENE_PROFILES,
    )
    palette_profile = _draw_axis(
        ctx,
        overrides,
        "palette_profile",
        _scheduled_palette(seed, sample_index),
        PALETTE_PROFILES,
    )
    h, w, mask = _row_mask(profile, band, sample_index)
    grid = _paint_content(h, w, mask, _PALETTES[palette_profile], ctx.draw_rng("content"))

    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError("generator produced an invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {"scene_profile": profile, "palette_profile": palette_profile}
    if observed != requested:
        raise RuntimeError(f"axis realization drift: requested={requested}, observed={observed}")
    return grid


def _validate_grid(grid: Any) -> tuple[int, int, list[list[int]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, [], ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, [], ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, [], ["grid must be rectangular"]
    normalized = [list(row) for row in grid]
    if not (3 <= h <= 8):
        errors.append(f"height must be 3..8, got {h}")
    if not (3 <= w <= 8):
        errors.append(f"width must be 3..8, got {w}")
    for r, row in enumerate(normalized):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC colour: {value!r}")
                return h, w, normalized, errors
    return h, w, normalized, errors


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, normalized, errors = _validate_grid(grid)
    info: dict[str, Any] = {"h": h, "w": w}
    if errors:
        return info, errors

    if any(3 in row for row in normalized):
        errors.append("input colour 3 is reserved for separator rows in the output")

    palette = frozenset(value for row in normalized for value in row if value != 0)
    if not palette:
        errors.append("input must contain non-zero content")
    if len(palette) > 4:
        errors.append(f"input palette must contain at most four non-zero colours, got {len(palette)}")

    nonempty = tuple(any(value != 0 for value in row) for row in normalized)
    colored_rows = [r for r, present in enumerate(nonempty) if present]
    if len(colored_rows) < 2:
        errors.append(f"input must contain at least two non-empty rows, got {len(colored_rows)}")
        info.update({"palette": palette, "nonempty_rows": nonempty})
        return info, errors

    first_colored, last_colored = colored_rows[0], colored_rows[-1]
    leading = sum(not nonempty[r] for r in range(first_colored))
    internal = sum(not nonempty[r] for r in range(first_colored + 1, last_colored))
    trailing = sum(not nonempty[r] for r in range(last_colored + 1, h))
    qualifying_rows = tuple(r for r in range(last_colored + 1) if not nonempty[r])
    if not qualifying_rows:
        errors.append("input must contain at least one empty row at or before the last non-empty row")

    if leading >= 1 and internal == 0 and trailing == 0:
        scene_profile = "leading_control"
    elif leading == 0 and internal == 1 and trailing == 0:
        scene_profile = "internal_anchor"
    elif leading == 0 and internal == 1 and trailing >= 1:
        scene_profile = "trailing_control"
    elif internal >= 2 or (leading >= 1 and internal >= 1):
        scene_profile = "multiple_control"
    else:
        scene_profile = None
        errors.append(
            "empty-row geometry is outside the declared teaching profiles "
            f"(leading={leading}, internal={internal}, trailing={trailing})"
        )

    palette_profile = _PALETTE_BY_SET.get(palette)
    if palette_profile is None:
        errors.append(f"non-zero palette {sorted(palette)} is outside the declared palette profiles")

    row_widths = tuple(sum(value != 0 for value in row) for row in normalized)
    info.update(
        {
            "grid": normalized,
            "palette": palette,
            "palette_profile": palette_profile,
            "nonempty_rows": nonempty,
            "colored_rows": tuple(colored_rows),
            "first_colored": first_colored,
            "last_colored": last_colored,
            "leading_blank_rows": leading,
            "internal_blank_rows": internal,
            "trailing_blank_rows": trailing,
            "qualifying_rows": qualifying_rows,
            "scene_profile": scene_profile,
            "row_widths": row_widths,
        }
    )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "scene_profile": info["scene_profile"],
        "palette_profile": info["palette_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    _band(difficulty)
    return list(_analyse(grid)[1])


def strict_canonical_like(grid: Any) -> list[str]:
    return list(_analyse(grid)[1])


def _render_rule(
    grid: Any,
    *,
    separator_predicate: Callable[[int, tuple[bool, ...], int, int], bool],
    tile_mode: str = "diagonal",
    recolor_copies: bool = False,
) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = info["grid"]
    h, w = info["h"], info["w"]
    nonempty = info["nonempty_rows"]
    first, last = info["first_colored"], info["last_colored"]
    modal = Counter(value for row in source for value in row if value != 0).most_common(1)[0][0]
    out = full_grid(2 * h, 2 * w, 0)
    for r in range(2 * h):
        tr, br = r % h, r // h
        for c in range(2 * w):
            tc, bc = c % w, c // w
            if separator_predicate(tr, nonempty, first, last):
                out[r][c] = 3
            elif tile_mode == "diagonal" and br == bc:
                value = source[tr][tc]
                out[r][c] = modal if recolor_copies and value != 0 else value
            elif tile_mode == "all":
                value = source[tr][tc]
                out[r][c] = modal if recolor_copies and value != 0 else value
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: not nonempty[r] and r <= last,
    )


def _rival_all_blank_rows_green(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: not nonempty[r],
    )


def _rival_strictly_between_colored_rows(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: not nonempty[r] and first < r < last,
    )


def _rival_first_separator_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    first_separator = min(info["qualifying_rows"])
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: r == first_separator,
    )


def _rival_no_green_rows(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: False,
    )


def _rival_copy_all_quadrants(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: not nonempty[r] and r <= last,
        tile_mode="all",
    )


def _rival_modal_color_echo(grid: Any) -> list[list[int]]:
    return _render_rule(
        grid,
        separator_predicate=lambda r, nonempty, first, last: not nonempty[r] and r <= last,
        recolor_copies=True,
    )


def _rival_copy_only_leftmost_nonzero_per_row(grid: Any) -> list[list[int]]:
    """Copy one marker per content row while preserving the separator rule."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = info["grid"]
    h, w = info["h"], info["w"]
    nonempty = info["nonempty_rows"]
    last = info["last_colored"]
    leftmost = {
        r: next(c for c, value in enumerate(source[r]) if value != 0)
        for r in info["colored_rows"]
    }
    out = full_grid(2 * h, 2 * w, 0)
    for r in range(2 * h):
        tr, br = r % h, r // h
        for c in range(2 * w):
            tc, bc = c % w, c // w
            if not nonempty[tr] and tr <= last:
                out[r][c] = 3
            elif br == bc and leftmost.get(tr) == tc:
                out[r][c] = source[tr][tc]
    return out


def _rival_assume_square_output_width_from_height(grid: Any) -> list[list[int]]:
    """Use the input height as both block dimensions, cropping/padding columns."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = info["grid"]
    h, w = info["h"], info["w"]
    nonempty = info["nonempty_rows"]
    last = info["last_colored"]
    out = full_grid(2 * h, 2 * h, 0)
    for r in range(2 * h):
        tr, br = r % h, r // h
        for c in range(2 * h):
            tc, bc = c % h, c // h
            if not nonempty[tr] and tr <= last:
                out[r][c] = 3
            elif br == bc and tc < w:
                out[r][c] = source[tr][tc]
    return out


def _witness_leading(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["leading_blank_rows"] >= 1


def _witness_trailing(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["trailing_blank_rows"] >= 1


def _witness_multiple(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(info["qualifying_rows"]) >= 2


def _witness_multicolor(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(info["palette"]) >= 2


def _witness_rectangular(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["h"] != info["w"]


def _witness_multi_cell_rows(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(width >= 2 for width in info["row_widths"])


def _witness_separator_rows(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["qualifying_rows"])


def _witness_off_diagonal_blank(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["colored_rows"])


SEMANTIC_WITNESSES = {
    "leading_blank_rows_follow_selected_authority": _witness_leading,
    "trailing_blank_rows_stay_blank": _witness_trailing,
    "multiple_separator_rows_are_all_painted": _witness_multiple,
    "multicolor_content_is_copied_exactly": _witness_multicolor,
    "rectangular_canvas_is_doubled": _witness_rectangular,
    "non_singleton_content_is_preserved": _witness_multi_cell_rows,
    "separator_rows_are_inserted": _witness_separator_rows,
    "off_diagonal_quadrants_stay_blank": _witness_off_diagonal_blank,
}

SEMANTIC_RIVALS = {
    "green_every_blank_row": _rival_all_blank_rows_green,
    "green_only_strictly_between_colored_rows": _rival_strictly_between_colored_rows,
    "green_only_first_separator": _rival_first_separator_only,
    "diagonal_tiling_without_green_rows": _rival_no_green_rows,
    "copy_input_to_all_four_quadrants": _rival_copy_all_quadrants,
    "replace_copied_content_with_modal_color": _rival_modal_color_echo,
    "copy_only_leftmost_nonzero_per_row": _rival_copy_only_leftmost_nonzero_per_row,
    "assume_square_output_width_from_height": _rival_assume_square_output_width_from_height,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "green_every_blank_row": _rival_all_blank_rows_green,
    "green_only_strictly_between_colored_rows": _rival_strictly_between_colored_rows,
    "copy_input_to_all_four_quadrants": _rival_copy_all_quadrants,
    "copy_only_leftmost_nonzero_per_row": _rival_copy_only_leftmost_nonzero_per_row,
    "assume_square_output_width_from_height": _rival_assume_square_output_width_from_height,
}
WITNESS_RIVALS = {
    "leading_blank_rows_follow_selected_authority": ["green_only_strictly_between_colored_rows"],
    "trailing_blank_rows_stay_blank": ["green_every_blank_row"],
    "multiple_separator_rows_are_all_painted": ["green_only_first_separator"],
    "multicolor_content_is_copied_exactly": ["replace_copied_content_with_modal_color"],
    "rectangular_canvas_is_doubled": ["assume_square_output_width_from_height"],
    "non_singleton_content_is_preserved": ["copy_only_leftmost_nonzero_per_row"],
    "separator_rows_are_inserted": ["diagonal_tiling_without_green_rows"],
    "off_diagonal_quadrants_stay_blank": ["copy_input_to_all_four_quadrants"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    profiles: set[str] = set()
    saw_multicolor = False
    saw_rectangular = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected Racket authority")
        profiles.add(info["scene_profile"])
        saw_multicolor = saw_multicolor or len(info["palette"]) >= 2
        saw_rectangular = saw_rectangular or info["h"] != info["w"]

    missing = set(SCENE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations miss semantic scene profiles: {sorted(missing)}")
    if not saw_multicolor:
        reasons.append("demonstrations lack a multicolor copy-exactly control")
    if not saw_rectangular:
        reasons.append("demonstrations lack a rectangular sizing/tiling control")

    valid_pairs = [
        pair
        for pair in demos
        if isinstance(pair, dict) and "input" in pair and "output" in pair
        and not _analyse(pair["input"])[1]
    ]
    for rival_name, rival in LESSON_COMPETITORS.items():
        try:
            survives = bool(valid_pairs) and all(
                rival(pair["input"]) == pair["output"] for pair in valid_pairs
            )
        except (TypeError, ValueError, IndexError):
            survives = False
        if survives:
            reasons.append(f"declared competitor survives demonstrations: {rival_name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the selected Racket authority")
    return reasons
