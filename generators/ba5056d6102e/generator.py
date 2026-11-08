"""Input generator for Boolean intersection of two aligned panels.

The unchanged Racket authority finds the full-width color-5 divider, aligns the
same coordinates in the two equal-height panels, and emits color 8 exactly where
both panel cells are non-background.  This module generates inputs only.

The four-slot curriculum deliberately mixes one canonical-shaped draw with three
lawful generalizations.  Every draw contains all four Boolean occupancy states,
so union, xor, top-only, and bottom-only rules are visibly wrong.  Every
three-example window also contains a noncanonical palette and uses canonical
bottom color 3 in the top role, refuting literal-palette and color-role shortcuts
that otherwise fit all shipped examples.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ba5056d6102e"
TASK_ID = GENERATOR_ID
RULE_HASH = "1586ec3843ec"
VERSION = "3.1.0"
SUMMARY = (
    "Two equal-height, coordinate-aligned binary masks are separated by one "
    "full-width color-5 row. The top and bottom foreground colors are distinct "
    "non-{0,5,8} colors. Output cell (r,c) is 8 iff both aligned input cells "
    "are nonzero, otherwise 0. Every generated input exposes 00, 10, 01, and "
    "11 occupancy states; a four-profile schedule preserves canonical 5x8, "
    "colors-2/3 support while varying palette, shape, spatial texture, and "
    "foreground-color roles."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is 0 and output-only color 8 never appears in an input panel",
    "exactly one full-width color-5 row splits two equal, nonempty panels",
    "each panel uses exactly one foreground color and the two colors differ",
    "all four aligned occupancy states 00, 10, 01, and 11 occur",
    "the authoritative output is the Boolean intersection mask colored 8",
]

_COLORS = (1, 2, 3, 4, 6, 7, 9)
_STYLES = ("scattered", "clustered", "striped", "diagonal")

AXES = {
    "half_h": {
        "type": "int",
        "default": "scheduled 4..7; canonical profile uses 5",
        "valid": "4..7",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 7..14; canonical profile uses 8",
        "valid": "7..14",
    },
    "top_color": {
        "type": "color",
        "default": "scheduled non-{0,5,8}",
        "valid": "1..9 (≠5, ≠8)",
    },
    "bottom_color": {
        "type": "color",
        "default": "scheduled non-{0,5,8}, distinct from top_color",
        "valid": "1..9 (≠5, ≠8)",
    },
    "support_style": {
        "type": "str",
        "default": "scheduled spatial arrangement",
        "valid": "|".join(_STYLES),
    },
}

# Equal panel colors destroy the visible two-role grammar.  Enumerating the
# seven legal equal-color pairs makes the incompatibility machine-readable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"top_color": color, "bottom_color": color} for color in _COLORS
]

SCHEDULE_PROFILES = (
    "canonical_like",
    "palette_shift",
    "shape_shift",
    "structured",
)

_CANONICAL_SIGNATURES = {
    # (00, 10, 01, 11), measured from the four public demonstrations and query.
    (16, 10, 7, 7),
    (18, 9, 5, 8),
    (15, 4, 12, 9),
    (16, 8, 6, 10),
    (18, 6, 5, 11),
}
_CANONICAL_SIGNATURE_ORDER = tuple(sorted(_CANONICAL_SIGNATURES))

_PROFILE_DEFAULTS = {
    "canonical_like": {
        None: (5, 8, 2, 3, "scattered"),
        "easy": (5, 8, 2, 3, "scattered"),
        "medium": (5, 8, 2, 3, "scattered"),
        "hard": (5, 8, 2, 3, "scattered"),
    },
    "palette_shift": {
        None: (5, 8, 1, 9, "scattered"),
        "easy": (4, 7, 1, 9, "scattered"),
        "medium": (5, 10, 4, 6, "scattered"),
        "hard": (7, 14, 7, 1, "scattered"),
    },
    # Two of four slots put canonical bottom color 3 in the top role.  Since
    # lessons use three consecutive slots, every lesson contains this role-
    # reversal evidence while retaining canonical and other palette support.
    "shape_shift": {
        None: (6, 11, 3, 7, "clustered"),
        "easy": (4, 9, 3, 7, "clustered"),
        "medium": (6, 11, 3, 2, "clustered"),
        "hard": (7, 13, 3, 4, "clustered"),
    },
    "structured": {
        None: (6, 12, 3, 1, "diagonal"),
        "easy": (5, 10, 3, 1, "striped"),
        "medium": (6, 12, 3, 7, "diagonal"),
        "hard": (7, 14, 3, 2, "striped"),
    },
}


class IncompatibleOverrides(ValueError):
    """A deliberate rejection whose participating axes are machine-readable."""

    def __init__(self, message: str, *axes: str) -> None:
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return a call-order-independent four-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("half_h", "grid_w", "top_color", "bottom_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    style = overrides.get("support_style")
    if style is not None and not isinstance(style, str):
        raise ValueError(
            f"support_style must be a string, not {type(style).__name__}"
        )
    top = overrides.get("top_color")
    bottom = overrides.get("bottom_color")
    if top is not None and bottom is not None and top == bottom:
        raise IncompatibleOverrides(
            "top_color and bottom_color must be distinct",
            "top_color",
            "bottom_color",
        )


def _fallback_color(color: int) -> int:
    return next(candidate for candidate in _COLORS if candidate != color)


def _effective_defaults(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    profile = schedule_profile(seed, sample_index, difficulty)
    half_h, grid_w, top_color, bottom_color, style = _PROFILE_DEFAULTS[profile][
        difficulty
    ]
    defaults = {
        "half_h": half_h,
        "grid_w": grid_w,
        "top_color": top_color,
        "bottom_color": bottom_color,
        "support_style": style,
    }

    # A valid single-color pin must remain usable even when it happens to equal
    # the scheduled color of the other role. Move only the unpinned role.
    if "top_color" in overrides and "bottom_color" not in overrides:
        requested = overrides["top_color"]
        if requested == defaults["bottom_color"]:
            defaults["bottom_color"] = _fallback_color(requested)
    elif "bottom_color" in overrides and "top_color" not in overrides:
        requested = overrides["bottom_color"]
        if requested == defaults["top_color"]:
            defaults["top_color"] = _fallback_color(requested)

    defaults.update({key: value for key, value in overrides.items() if value is not None})
    return profile, defaults


def _state_counts(
    *,
    profile: str,
    half_h: int,
    grid_w: int,
    top_color: int,
    bottom_color: int,
    seed: int,
    sample_index: int,
    difficulty: str | None,
) -> dict[str, int]:
    area = half_h * grid_w
    if (
        profile == "canonical_like"
        and half_h == 5
        and grid_w == 8
        and top_color == 2
        and bottom_color == 3
    ):
        signature = _CANONICAL_SIGNATURE_ORDER[
            (int(seed) * 7 + int(sample_index)) % len(_CANONICAL_SIGNATURE_ORDER)
        ]
        return dict(zip(("00", "10", "01", "11"), signature))

    # Difficulty changes the density prior, never the declared override bounds.
    overlap_fraction = {
        None: 0.22,
        "easy": 0.16,
        "medium": 0.22,
        "hard": 0.28,
    }[difficulty]
    jitter = ((int(seed) * 13 + int(sample_index) * 7) % 5) - 2
    overlap = max(2, min(area - 6, round(area * overlap_fraction) + jitter))
    top_only = max(2, round(area * 0.20) + ((int(seed) + 1) % 3) - 1)
    bottom_only = max(2, round(area * 0.18) + ((int(sample_index) + 2) % 3) - 1)
    empty = area - overlap - top_only - bottom_only
    if empty < 2:
        # The minimum canvas is 28 cells, so shrinking the two one-sided states
        # is always sufficient and keeps every truth-table branch visible.
        deficit = 2 - empty
        take_top = min(deficit, top_only - 2)
        top_only -= take_top
        deficit -= take_top
        bottom_only -= min(deficit, bottom_only - 2)
        empty = area - overlap - top_only - bottom_only
    if min(empty, top_only, bottom_only, overlap) < 1:
        raise RuntimeError("constructive state budget lost a Boolean branch")
    return {"00": empty, "10": top_only, "01": bottom_only, "11": overlap}


def _ordered_positions(
    half_h: int,
    grid_w: int,
    style: str,
    rng,
) -> list[tuple[int, int]]:
    positions = [(r, c) for r in range(half_h) for c in range(grid_w)]
    if style == "scattered":
        rng.shuffle(positions)
        return positions
    if style == "clustered":
        center_r = (half_h - 1) / 2
        center_c = (grid_w - 1) / 2
        tie = {point: rng.random() for point in positions}
        return sorted(
            positions,
            key=lambda point: (
                abs(point[0] - center_r) + abs(point[1] - center_c),
                tie[point],
            ),
        )
    if style == "striped":
        # Column-major order turns grouped states into vertical bands.
        return sorted(positions, key=lambda point: (point[1], point[0]))
    if style == "diagonal":
        scale = (grid_w - 1) / max(1, half_h - 1)
        tie = {point: rng.random() for point in positions}
        return sorted(
            positions,
            key=lambda point: (
                abs(point[1] - point[0] * scale),
                point[0] + point[1],
                tie[point],
            ),
        )
    raise ValueError(f"unknown support style {style!r}")


def _state_sequence(counts: dict[str, int], style: str, rng) -> list[str]:
    if style == "scattered":
        states = [state for state in ("00", "10", "01", "11") for _ in range(counts[state])]
        rng.shuffle(states)
        return states
    if style == "clustered":
        order = ("11", "10", "01", "00")
    elif style == "striped":
        order = ("10", "11", "01", "00")
    else:  # diagonal
        order = ("11", "01", "10", "00")
    return [state for state in order for _ in range(counts[state])]


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile, effective = _effective_defaults(
        seed, sample_index, difficulty, overrides
    )
    if effective["top_color"] == effective["bottom_color"]:
        raise IncompatibleOverrides(
            "top_color and bottom_color must be distinct",
            "top_color",
            "bottom_color",
        )

    # Supplying scheduled defaults through GenCtx keeps every declared axis in
    # keyed-draw provenance while explicit caller values still win.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    half_h = ctx.draw_int("half_h", 4, 7)
    grid_w = ctx.draw_int("grid_w", 7, 14)
    top_color = ctx.draw_color("top_color", exclude={0, 5, 8})
    bottom_color = ctx.draw_color(
        "bottom_color", exclude={0, 5, 8, top_color}
    )
    style = ctx.draw_choice("support_style", _STYLES)

    counts = _state_counts(
        profile=profile,
        half_h=half_h,
        grid_w=grid_w,
        top_color=top_color,
        bottom_color=bottom_color,
        seed=seed,
        sample_index=sample_index,
        difficulty=difficulty,
    )
    layout_rng = ctx.draw_rng(f"layout:{profile}:{style}")
    positions = _ordered_positions(half_h, grid_w, style, layout_rng)
    states = _state_sequence(counts, style, layout_rng)
    if len(positions) != len(states):
        raise RuntimeError("state budget does not fill the panel")

    grid = full_grid(2 * half_h + 1, grid_w, 0)
    grid[half_h] = [5] * grid_w
    for (row, column), state in zip(positions, states):
        if state[0] == "1":
            grid[row][column] = top_color
        if state[1] == "1":
            grid[half_h + 1 + row][column] = bottom_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid Boolean-intersection input: {errors}")
    return [row[:] for row in grid]


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid is empty or not a list-of-lists"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged or has zero width"]}
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return {"errors": errors}

    divider_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if all(value == 5 for value in row)
    ]
    if len(divider_rows) != 1:
        return {
            "errors": [
                "expected exactly one full-width color-5 divider row, "
                f"found {len(divider_rows)}"
            ]
        }
    divider = divider_rows[0]
    if divider == 0 or divider == len(grid) - 1 or 2 * divider + 1 != len(grid):
        return {
            "errors": [
                f"divider row {divider} does not split equal nonempty panels"
            ]
        }
    top = grid[:divider]
    bottom = grid[divider + 1 :]
    top_colors = sorted({value for row in top for value in row if value != 0})
    bottom_colors = sorted({value for row in bottom for value in row if value != 0})
    if len(top_colors) != 1 or top_colors[0] in {5, 8}:
        errors.append(
            "top panel must use exactly one foreground color outside {5,8}; "
            f"found {top_colors}"
        )
    if len(bottom_colors) != 1 or bottom_colors[0] in {5, 8}:
        errors.append(
            "bottom panel must use exactly one foreground color outside {5,8}; "
            f"found {bottom_colors}"
        )
    if len(top_colors) == len(bottom_colors) == 1 and top_colors[0] == bottom_colors[0]:
        errors.append(f"panel colors must differ; both were {top_colors[0]}")

    counts = Counter({state: 0 for state in ("00", "10", "01", "11")})
    for row in range(divider):
        for column in range(width):
            counts[
                f"{int(top[row][column] != 0)}{int(bottom[row][column] != 0)}"
            ] += 1
    missing = [state for state in ("00", "10", "01", "11") if counts[state] == 0]
    if missing:
        errors.append(f"missing Boolean occupancy state(s): {missing}")

    return {
        "errors": errors,
        "half_h": divider,
        "grid_w": width,
        "top": top,
        "bottom": bottom,
        "top_color": top_colors[0] if len(top_colors) == 1 else None,
        "bottom_color": bottom_colors[0] if len(bottom_colors) == 1 else None,
        "counts": dict(counts),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the input grammar and require all Boolean branches to be visible."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not 4 <= analysis["half_h"] <= 7:
        errors.append(f"panel height {analysis['half_h']} is outside 4..7")
    if not 7 <= analysis["grid_w"] <= 14:
        errors.append(f"grid width {analysis['grid_w']} is outside 7..14")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact numeric/color axes from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    return {
        "half_h": analysis["half_h"],
        "grid_w": analysis["grid_w"],
        "top_color": analysis["top_color"],
        "bottom_color": analysis["bottom_color"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact public shape, palette roles, and density signatures."""
    errors = list(self_check(grid))
    if errors:
        return errors
    analysis = _analyze(grid)
    if (analysis["half_h"], analysis["grid_w"]) != (5, 8):
        errors.append(
            f"canonical panels are 5x8, got {analysis['half_h']}x{analysis['grid_w']}"
        )
    if (analysis["top_color"], analysis["bottom_color"]) != (2, 3):
        errors.append(
            "canonical palette roles are top=2 and bottom=3, got "
            f"{analysis['top_color']}/{analysis['bottom_color']}"
        )
    counts = analysis["counts"]
    signature = tuple(counts[state] for state in ("00", "10", "01", "11"))
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(f"occupancy signature {signature} is not public-canonical")
    return errors


def _split_panels(grid) -> tuple[list[list[int]], list[list[int]]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["top"], analysis["bottom"]


def _boolean_output(
    grid,
    predicate: Callable[[bool, bool], bool],
) -> list[list[int]]:
    top, bottom = _split_panels(grid)
    return [
        [
            8 if predicate(top[row][column] != 0, bottom[row][column] != 0) else 0
            for column in range(len(top[0]))
        ]
        for row in range(len(top))
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for probes; Racket remains authoritative."""
    return _boolean_output(grid, lambda top, bottom: top and bottom)


def _union(grid):
    return _boolean_output(grid, lambda top, bottom: top or bottom)


def _xor(grid):
    return _boolean_output(grid, lambda top, bottom: top != bottom)


def _top_only(grid):
    return _boolean_output(grid, lambda top, bottom: top)


def _bottom_only(grid):
    return _boolean_output(grid, lambda top, bottom: bottom)


def _canonical_colors_only(grid):
    """Wrong shortcut: memorize literal public colors instead of occupancy."""
    top, bottom = _split_panels(grid)
    return [
        [
            8 if top[row][column] == 2 and bottom[row][column] == 3 else 0
            for column in range(len(top[0]))
        ]
        for row in range(len(top))
    ]


def _color_3_bottom_only(grid):
    """Wrong shortcut: treat canonical bottom color 3 as invalid in the top role."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["top_color"] == 3:
        return [
            [0 for _ in range(analysis["grid_w"])]
            for _ in range(analysis["half_h"])
        ]
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "union": _union,
    "xor": _xor,
    "top_only": _top_only,
    "bottom_only": _bottom_only,
    "canonical_colors_only": _canonical_colors_only,
    "color_3_bottom_only": _color_3_bottom_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_colors_only": _canonical_colors_only,
    "color_3_bottom_only": _color_3_bottom_only,
}


def _witness_complete_truth_table(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and all(
        analysis["counts"][state] > 0 for state in ("00", "10", "01", "11")
    )


def _witness_noncanonical_palette(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and (
        analysis["top_color"], analysis["bottom_color"]
    ) != (2, 3)


def _witness_canonical_profile(grid) -> bool:
    return strict_canonical_like(grid) == []


def _witness_top_color_3(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["top_color"] == 3


def _witness_varied_shape(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and (
        analysis["half_h"], analysis["grid_w"]
    ) != (5, 8)


SEMANTIC_WITNESSES = {
    "complete_boolean_truth_table": _witness_complete_truth_table,
    "noncanonical_palette": _witness_noncanonical_palette,
    "canonical_profile": _witness_canonical_profile,
    "top_color_3": _witness_top_color_3,
    "varied_shape": _witness_varied_shape,
}
WITNESS_RIVALS = {
    "complete_boolean_truth_table": ["union", "xor", "top_only", "bottom_only"],
    "noncanonical_palette": ["canonical_colors_only"],
    "top_color_3": ["color_3_bottom_only"],
}
BRANCH_WITNESSES = {"canonical_profile", "varied_shape"}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject an episode when a declared wrong rule survives every demo."""
    reasons: list[str] = []
    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the rule domain: {exc}")
            continue
        if expected != pair.get("output"):
            reasons.append(f"pair {index} output disagrees with Boolean intersection")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(
                rival(deepcopy(pair["input"])) == pair.get("output")
                for pair in demos
            )
        except Exception as exc:  # report a broken contract instead of hiding it
            reasons.append(f"competitor {name} crashed: {type(exc).__name__}: {exc}")
            continue
        if fits:
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons
