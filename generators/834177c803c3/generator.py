"""Generator for arc_puzzle_bank_twentieth21:M137 — use a binary mask.

The input contains two equal panels separated by one full cyan (8) column.
The left panel is a 0/1 mask and the right panel is a nonzero color bank.
The output keeps each right-panel color exactly where the aligned mask cell is
1 and writes 0 everywhere else.

The default four-slot curriculum spends three slots on the three linked
canonical shape/palette profiles and one slot on a difficulty-scaled broader
profile.  Every ordinary draw also contains direct counterexamples to common
shortcuts: colors 1 and 8 are valid payloads, at least one payload color occurs
under both mask states, and every row mixes kept and discarded cells.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "834177c803c3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "dd611594bfa8"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "Split an odd-width grid at its full cyan (8) center column. The left "
    "panel is a binary 0/1 mask and the equal-size right panel is a bank of "
    "nonzero ARC colors, including 1 and 8 as ordinary payload colors. Output "
    "the right value at each aligned cell whose left value is 1; output 0 "
    "where the left value is 0. The four-slot schedule includes all three "
    "canonical linked shape/palette profiles plus a difficulty-scaled broad "
    "profile, and every ordinary draw refutes color- and row-based shortcuts."
)

INVARIANTS = [
    "the input is a rectangular 3..6 by (2*panel_w+1) ARC grid",
    "the center column is entirely color 8 and separates equal-width panels",
    "the left panel contains only 0 and 1, with both values in every row",
    "the right panel contains only nonzero ARC colors 1..9",
    "ordinary draws keep and discard colors 1 and 8 and repeat a payload color across both mask states",
    "the output is a fresh grid shaped like one panel and applies the mask cell by cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "3..6",
    },
    "panel_w": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "3..6",
    },
    "n_right_colors": {
        "type": "int",
        "default": "four-slot canonical/broad schedule",
        "valid": "6..9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_3x4_palette9",
    "canonical_4x3_palette10",
    "canonical_4x4_palette9",
    "broad",
)

# (height, panel width, full input palette size, number of mask ones).
# These are extracted from the two train inputs and one held-out test input.
_CANONICAL_LINKED_SIGNATURES = {
    (3, 4, 9, 6),
    (4, 3, 10, 6),
    (4, 4, 9, 8),
}

_CANONICAL_DEFAULTS = {
    "canonical_3x4_palette9": {
        "grid_h": 3,
        "panel_w": 4,
        "n_right_colors": 8,
        "mask_ones": 6,
    },
    "canonical_4x3_palette10": {
        "grid_h": 4,
        "panel_w": 3,
        "n_right_colors": 9,
        "mask_ones": 6,
    },
    "canonical_4x4_palette9": {
        "grid_h": 4,
        "panel_w": 4,
        "n_right_colors": 8,
        "mask_ones": 8,
    },
}

_BROAD_DEFAULTS = {
    "easy": {"grid_h": 3, "panel_w": 3, "n_right_colors": 6},
    "medium": {"grid_h": 5, "panel_w": 5, "n_right_colors": 7},
    "hard": {"grid_h": 6, "panel_w": 6, "n_right_colors": 8},
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the declared semantic slot; seed/band do not alias the cycle."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile in _CANONICAL_DEFAULTS:
        return {
            key: int(value)
            for key, value in _CANONICAL_DEFAULTS[profile].items()
            if key in AXES
        }
    band = difficulty if difficulty in _BROAD_DEFAULTS else "medium"
    return dict(_BROAD_DEFAULTS[band])


def _normalize_grid(grid: Any) -> tuple[Grid | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]

    normalized: Grid = []
    for row_index, row in enumerate(grid):
        normalized_row: list[int] = []
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized, []


def _split_panels(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], list[list[int]]]:
    panel_w = (len(grid[0]) - 1) // 2
    left = [list(row[:panel_w]) for row in grid]
    right = [list(row[panel_w + 1 :]) for row in grid]
    return left, right


def _full_palette_size(grid: Sequence[Sequence[int]]) -> int:
    return len({value for row in grid for value in row})


def _mask_ones(grid: Sequence[Sequence[int]]) -> int:
    left, _right = _split_panels(grid)
    return sum(value == 1 for row in left for value in row)


def canonical_profile_signature(grid: Any) -> tuple[int, int, int, int] | None:
    normalized, errors = _normalize_grid(grid)
    if errors:
        return None
    assert normalized is not None
    width = len(normalized[0])
    if width < 3 or width % 2 == 0:
        return None
    return (
        len(normalized),
        (width - 1) // 2,
        _full_palette_size(normalized),
        _mask_ones(normalized),
    )


def observe_overrides(grid: Any) -> dict[str, int]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    assert normalized is not None
    width = len(normalized[0])
    if width < 3 or width % 2 == 0:
        raise ValueError(f"cannot observe panels from width {width}")
    panel_w = (width - 1) // 2
    _left, right = _split_panels(normalized)
    return {
        "grid_h": len(normalized),
        "panel_w": panel_w,
        "n_right_colors": len({value for row in right for value in row}),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the authority-compatible input grammar and exact overrides."""
    del difficulty
    normalized, errors = _normalize_grid(grid)
    if errors:
        return errors
    assert normalized is not None

    height, width = len(normalized), len(normalized[0])
    if not 3 <= height <= 6:
        errors.append(f"height {height} outside declared envelope 3..6")
    if width % 2 == 0:
        errors.append(f"width {width} must be odd for two equal panels plus one separator")
        return errors
    panel_w = (width - 1) // 2
    if not 3 <= panel_w <= 6:
        errors.append(f"panel width {panel_w} outside declared envelope 3..6")
        return errors

    if any(row[panel_w] != 8 for row in normalized):
        errors.append("center separator column must be entirely color 8")

    left, right = _split_panels(normalized)
    bad_left = sorted({value for row in left for value in row if value not in (0, 1)})
    if bad_left:
        errors.append(f"left panel must be binary 0/1; found {bad_left}")
    for row_index, row in enumerate(left):
        if 0 not in row or 1 not in row:
            errors.append(
                f"left row {row_index} must contain both selected (1) and unselected (0) cells"
            )

    bad_right = sorted({value for row in right for value in row if value == 0})
    if bad_right:
        errors.append("right panel payload cells must all be nonzero")
    right_palette = {value for row in right for value in row}
    if len(right_palette) < 2:
        errors.append("right panel must contain at least two distinct payload colors")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        observed = observe_overrides(normalized)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(
                    f"override {key} requested {value!r}, observed {observed.get(key)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept exactly the three linked empirical canonical profiles."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_LINKED_SIGNATURES:
        reasons.append(f"linked canonical signature not observed: {signature!r}")
    return reasons


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent test mirror; the selected Racket program remains authority."""
    left, right = _split_panels(grid)
    return [
        [right[r][c] if left[r][c] == 1 else 0 for c in range(len(left[0]))]
        for r in range(len(left))
    ]


def _rival_drop_special_colors(grid: Sequence[Sequence[int]]) -> Grid:
    output = rule_mirror(grid)
    return [[0 if value in (1, 8) else value for value in row] for row in output]


def _rival_keep_any_selected_color(grid: Sequence[Sequence[int]]) -> Grid:
    left, right = _split_panels(grid)
    selected_colors = {
        right[r][c]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] == 1
    }
    return [
        [right[r][c] if right[r][c] in selected_colors else 0 for c in range(len(left[0]))]
        for r in range(len(left))
    ]


def _rival_copy_active_rows(grid: Sequence[Sequence[int]]) -> Grid:
    left, right = _split_panels(grid)
    return [
        list(right[r]) if any(value == 1 for value in left[r]) else [0] * len(left[r])
        for r in range(len(left))
    ]


def _rival_inverse_mask(grid: Sequence[Sequence[int]]) -> Grid:
    left, right = _split_panels(grid)
    return [
        [right[r][c] if left[r][c] == 0 else 0 for c in range(len(left[0]))]
        for r in range(len(left))
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "drop_special_colors": _rival_drop_special_colors,
    "keep_any_selected_color": _rival_keep_any_selected_color,
    "copy_active_rows": _rival_copy_active_rows,
    "inverse_mask": _rival_inverse_mask,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# The two canonical demonstrations never keep a 1 or an 8, so this is the
# strongest training-demo shortcut even though the held-out canonical query
# refutes it. Generated demonstrations must refute it directly.
CANONICAL_SHORTCUTS = {"drop_special_colors": _rival_drop_special_colors}


def _selected_payloads(grid: Sequence[Sequence[int]]) -> set[int]:
    left, right = _split_panels(grid)
    return {
        right[r][c]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] == 1
    }


def _unselected_payloads(grid: Sequence[Sequence[int]]) -> set[int]:
    left, right = _split_panels(grid)
    return {
        right[r][c]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] == 0
    }


def _has_selected_special_colors(grid: Sequence[Sequence[int]]) -> bool:
    return {1, 8} <= _selected_payloads(grid)


def _has_same_color_both_mask_states(grid: Sequence[Sequence[int]]) -> bool:
    return bool(_selected_payloads(grid) & _unselected_payloads(grid))


def _has_mixed_mask_in_every_row(grid: Sequence[Sequence[int]]) -> bool:
    left, _right = _split_panels(grid)
    return all(0 in row and 1 in row for row in left)


def _has_nontrivial_inverse_choice(grid: Sequence[Sequence[int]]) -> bool:
    left, right = _split_panels(grid)
    return (
        any(value == 1 for row in left for value in row)
        and any(value == 0 for row in left for value in row)
        and all(value != 0 for row in right for value in row)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "selected_special_colors": _has_selected_special_colors,
    "same_color_both_mask_states": _has_same_color_both_mask_states,
    "mixed_mask_in_every_row": _has_mixed_mask_in_every_row,
    "nontrivial_inverse_choice": _has_nontrivial_inverse_choice,
}
WITNESS_RIVALS = {
    "selected_special_colors": ["drop_special_colors"],
    "same_color_both_mask_states": ["keep_any_selected_color"],
    "mixed_mask_in_every_row": ["copy_active_rows"],
    "nontrivial_inverse_choice": ["inverse_mask"],
}


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Require every named shortcut to be eliminated by the demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"]

    for index, pair in enumerate(demos):
        if "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} lacks input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the pinned mask rule")

    if "input" not in query:
        reasons.append("query lacks input")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append("query input is outside the generator grammar: " + "; ".join(query_errors))

    for name, rival in LESSON_COMPETITORS.items():
        if not any(
            "input" in pair
            and "output" in pair
            and rival(pair["input"]) != pair["output"]
            for pair in demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def _build_mask(rng: Any, height: int, panel_w: int, target_ones: int) -> list[list[int]]:
    cells = height * panel_w
    if not height <= target_ones <= cells - height:
        raise ValueError(
            f"mask target {target_ones} cannot leave both states in every row of {height}x{panel_w}"
        )

    mask = full_grid(height, panel_w, 0)
    reserved_zero: set[tuple[int, int]] = set()
    selected: set[tuple[int, int]] = set()
    for row in range(height):
        columns = list(range(panel_w))
        rng.shuffle(columns)
        selected.add((row, columns[0]))
        reserved_zero.add((row, columns[1]))

    available = [
        (row, column)
        for row in range(height)
        for column in range(panel_w)
        if (row, column) not in selected and (row, column) not in reserved_zero
    ]
    rng.shuffle(available)
    selected.update(available[: target_ones - len(selected)])
    for row, column in selected:
        mask[row][column] = 1
    return mask


def _semantic_right_assignment(
    mask: Sequence[Sequence[int]], palette: Sequence[int], rng: Any
) -> list[list[int]]:
    height, panel_w = len(mask), len(mask[0])
    selected = [
        (row, column)
        for row in range(height)
        for column in range(panel_w)
        if mask[row][column] == 1
    ]
    unselected = [
        (row, column)
        for row in range(height)
        for column in range(panel_w)
        if mask[row][column] == 0
    ]
    rng.shuffle(selected)
    rng.shuffle(unselected)
    all_positions = selected + unselected
    assignment: dict[tuple[int, int], int] = {}

    # The ordinary schedule always has at least len(palette)+3 cells, which is
    # exactly enough to show 1, 8, and a third color under BOTH mask states and
    # still realize every requested palette color. The compact 3x3/palette-9
    # explicit override is lawful but cannot carry all three duplicate witnesses;
    # it falls back to exact palette realization rather than lying about support.
    if (
        len(all_positions) >= len(palette) + 3
        and len(selected) >= 3
        and len(unselected) >= 3
    ):
        cross_color = next(color for color in palette if color not in (1, 8))
        forced = [
            (selected[0], 1),
            (selected[1], 8),
            (selected[2], cross_color),
            (unselected[0], 1),
            (unselected[1], 8),
            (unselected[2], cross_color),
        ]
        for position, color in forced:
            assignment[position] = color

        unused_positions = [position for position in all_positions if position not in assignment]
        rng.shuffle(unused_positions)
        missing_colors = [color for color in palette if color not in assignment.values()]
        for position, color in zip(unused_positions, missing_colors):
            assignment[position] = color
        for position in unused_positions[len(missing_colors) :]:
            assignment[position] = rng.choice(list(palette))
    else:
        positions = list(all_positions)
        rng.shuffle(positions)
        # Put the two special payload colors on selected cells when possible;
        # then realize every other color exactly once before filling leftovers.
        ordered_positions = list(selected[:2]) + [p for p in positions if p not in selected[:2]]
        ordered_colors = [1, 8] + [color for color in palette if color not in (1, 8)]
        for position, color in zip(ordered_positions, ordered_colors):
            assignment[position] = color
        for position in ordered_positions[len(ordered_colors) :]:
            assignment[position] = rng.choice(list(palette))

    right = full_grid(height, panel_w, 0)
    for (row, column), color in assignment.items():
        right[row][column] = color
    return right


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile = schedule_profile(seed, sample_index, difficulty)
    effective = dict(overrides)
    for key, value in _scheduled_defaults(seed, sample_index, difficulty).items():
        effective.setdefault(key, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 3, 6)
    panel_w = ctx.draw_int("panel_w", 3, 6)
    n_right_colors = ctx.draw_int("n_right_colors", 6, 9)
    mask_rng = ctx.draw_rng("mask")
    palette_rng = ctx.draw_rng("palette")
    payload_rng = ctx.draw_rng("payload")

    canonical = _CANONICAL_DEFAULTS.get(profile)
    if canonical and (height, panel_w) == (canonical["grid_h"], canonical["panel_w"]):
        target_ones = int(canonical["mask_ones"])
    else:
        cells = height * panel_w
        target_ones = round(cells * mask_rng.uniform(0.42, 0.58))
        target_ones = max(height, min(cells - height, target_ones))

    mask = _build_mask(mask_rng, height, panel_w, target_ones)
    candidates = [2, 3, 4, 5, 6, 7, 9]
    palette = [1, 8] + palette_rng.sample(candidates, n_right_colors - 2)
    palette_rng.shuffle(palette)
    right = _semantic_right_assignment(mask, palette, payload_rng)

    grid = full_grid(height, 2 * panel_w + 1, 0)
    for row in range(height):
        for column in range(panel_w):
            grid[row][column] = mask[row][column]
            grid[row][panel_w + 1 + column] = right[row][column]
        grid[row][panel_w] = 8

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator produced invalid scene: " + "; ".join(errors))

    # Curriculum-only obligations: they are not part of the authority-valid
    # self_check grammar, but every ordinary draw must teach the rivals away.
    compact_override = height * panel_w < n_right_colors + 3
    if not compact_override:
        missing = [name for name, pred in SEMANTIC_WITNESSES.items() if not pred(grid)]
        if missing:
            raise AssertionError("generator hid required semantic witness(es): " + ", ".join(missing))
    return grid
