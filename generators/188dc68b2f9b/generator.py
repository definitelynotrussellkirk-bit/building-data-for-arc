"""Generator for ARC task 2dc579da / content hash 188dc68b2f9b.

A uniform separator row and column split the input into four regions. Exactly
one non-separator cell has a singleton color. The canonical rule emits a board
whose size is the separator's north-west coordinates and folds the singleton's
absolute position into that board with modulo ``separator_index + 1``.

The teaching schedule deliberately rotates the singleton quadrant, alternates
centered and off-center separators, and varies the singleton's local position.
That makes the demonstrations refute fixed-quadrant, centered-divider,
marker-only, modal-color, and count-only shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "188dc68b2f9b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "63b928f87f96"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Fold the unique singleton's quadrant-local position into the north-west "
    "separator-sized output canvas. Ordinary draws vary all four quadrants, "
    "centered versus off-center dividers, dimensions, colors, and local position."
)

INVARIANTS = [
    "exactly one full separator row and one full separator column share one color",
    "all non-separator cells are dominant background except one singleton cell",
    "dominant, separator, and singleton colors are pairwise distinct",
    "the separator is interior and the singleton folds to a visible output cell",
]

QUADRANTS = ("nw", "ne", "sw", "se")
SEPARATOR_LAYOUTS = ("centered", "offset")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 7..13",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 7..13",
        "valid": "7..13",
    },
    "quadrant": {
        "type": "str",
        "default": "scheduled over all four quadrants",
        "valid": "|".join(QUADRANTS),
    },
    "sep_position": {
        "type": "str",
        "default": "scheduled centered/offset",
        "valid": "|".join(SEPARATOR_LAYOUTS),
    },
}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not 7 <= value <= 13:
            raise ValueError(f"{name} must be an integer in 7..13")
    if "quadrant" in overrides and overrides["quadrant"] is not None:
        if overrides["quadrant"] not in QUADRANTS:
            raise ValueError(f"quadrant must be one of {QUADRANTS}")
    if "sep_position" in overrides and overrides["sep_position"] is not None:
        if overrides["sep_position"] not in SEPARATOR_LAYOUTS:
            raise ValueError(f"sep_position must be one of {SEPARATOR_LAYOUTS}")


def _scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    """Record a scheduled exact axis through GenCtx, while honoring overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _draw_palette(rng) -> tuple[int, int, int]:
    """Return (dominant, separator, singleton); dominant/singleton stay nonzero."""
    dominant = rng.choice(tuple(range(1, 10)))
    singleton = rng.choice(tuple(color for color in range(1, 10) if color != dominant))
    separator = rng.choice(
        tuple(color for color in range(10) if color not in (dominant, singleton))
    )
    return dominant, separator, singleton


def _offset_index(size: int, rng) -> int:
    """Choose an interior non-central separator with >=2 cells on both sides."""
    center = size // 2
    choices = [index for index in range(2, size - 2) if index != center]
    if not choices:  # ordinary generated sizes are >=7, so this is defensive only.
        raise ValueError(f"size {size} has no lawful off-center separator")
    return rng.choice(choices)


def _separator_indices(h: int, w: int, layout: str, rng) -> tuple[int, int]:
    if layout == "centered":
        return h // 2, w // 2
    return _offset_index(h, rng), _offset_index(w, rng)


def _local_capacity(size: int, separator: int, on_low_side: bool) -> int:
    if on_low_side:
        return separator
    return min(separator, size - separator - 1)


def _scheduled_local_position(local_h: int, local_w: int, sample_index: int) -> tuple[int, int]:
    """Five-way position schedule; every 3-wide window contains a non-origin cell."""
    candidates = (
        (0, 0),
        (0, local_w - 1),
        (local_h - 1, 0),
        (local_h - 1, local_w - 1),
        (local_h // 2, local_w // 2),
    )
    return candidates[sample_index % len(candidates)]


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

    # Full declared domains remain override-valid in every difficulty band;
    # difficulty changes only the default sampling density.
    h = ctx.draw_int_diff("grid_h", 7, 13)
    w = ctx.draw_int_diff("grid_w", 7, 13)
    quadrant = _scheduled_choice(
        ctx,
        "quadrant",
        QUADRANTS[sample_index % len(QUADRANTS)],
        QUADRANTS,
    )
    # C/O/O has both layouts in every length-3 sliding lesson window. Its
    # period is coprime with the four-quadrant schedule, avoiding branch aliasing.
    sep_schedule = ("centered", "offset", "offset")
    sep_position = _scheduled_choice(
        ctx,
        "sep_position",
        sep_schedule[sample_index % len(sep_schedule)],
        SEPARATOR_LAYOUTS,
    )

    palette_rng = ctx.draw_rng(f"palette_{difficulty}")
    geometry_rng = ctx.draw_rng(f"separator_geometry_{difficulty}")
    dom_color, sep_color, singleton_color = _draw_palette(palette_rng)
    sep_row, sep_col = _separator_indices(h, w, sep_position, geometry_rng)

    grid = [[dom_color for _ in range(w)] for _ in range(h)]
    for col in range(w):
        grid[sep_row][col] = sep_color
    for row in range(h):
        grid[row][sep_col] = sep_color

    is_top = quadrant in ("nw", "ne")
    is_left = quadrant in ("nw", "sw")
    local_h = _local_capacity(h, sep_row, is_top)
    local_w = _local_capacity(w, sep_col, is_left)
    if local_h < 1 or local_w < 1:
        raise AssertionError("internal separator schedule produced an empty quadrant")

    local_row, local_col = _scheduled_local_position(local_h, local_w, sample_index)
    singleton_row = local_row if is_top else sep_row + 1 + local_row
    singleton_col = local_col if is_left else sep_col + 1 + local_col
    grid[singleton_row][singleton_col] = singleton_color
    return grid


def _rectangular_arc_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_arc_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 13 or not 5 <= w <= 13:
        errors.append(f"dimensions {h}x{w} outside canonical-compatible 5..13")

    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    palette = tuple(sorted(counts))
    if len(palette) != 3:
        errors.append(f"expected exactly three colors, found {palette}")

    dom = counts.most_common(1)[0][0]
    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(singleton_colors) != 1:
        errors.append(
            f"expected exactly one singleton-frequency color, found {singleton_colors}"
        )
        singleton = None
    else:
        singleton = singleton_colors[0]

    sep_rows = [
        row
        for row in range(h)
        if len(set(grid[row])) == 1 and grid[row][0] != dom
    ]
    sep_cols = [
        col
        for col in range(w)
        if len({grid[row][col] for row in range(h)}) == 1 and grid[0][col] != dom
    ]
    if len(sep_rows) != 1 or len(sep_cols) != 1:
        errors.append(
            "expected one non-dominant full separator row/column, "
            f"found rows={sep_rows}, cols={sep_cols}"
        )
        sep_row = sep_col = None
        sep_color = None
    else:
        sep_row, sep_col = sep_rows[0], sep_cols[0]
        row_color = grid[sep_row][0]
        col_color = grid[0][sep_col]
        sep_color = row_color
        if row_color != col_color:
            errors.append(
                f"separator row/column colors disagree: {row_color} vs {col_color}"
            )
        if not 1 <= sep_row < h - 1 or not 1 <= sep_col < w - 1:
            errors.append(
                f"separator must be interior, found row={sep_row}, col={sep_col}"
            )

    singleton_pos = None
    if singleton is not None:
        positions = [
            (row, col)
            for row in range(h)
            for col in range(w)
            if grid[row][col] == singleton
        ]
        if len(positions) == 1:
            singleton_pos = positions[0]

    if (
        sep_row is not None
        and sep_col is not None
        and sep_color is not None
        and singleton is not None
        and singleton_pos is not None
    ):
        if len({dom, sep_color, singleton}) != 3:
            errors.append("dominant, separator, and singleton colors must be distinct")

        sr, sc = singleton_pos
        if sr == sep_row or sc == sep_col:
            errors.append("singleton may not overwrite the full separator cross")

        for row in range(h):
            for col in range(w):
                expected = (
                    singleton
                    if (row, col) == singleton_pos
                    else sep_color
                    if row == sep_row or col == sep_col
                    else dom
                )
                if grid[row][col] != expected:
                    errors.append(
                        "cells outside the separator/singleton roles must be dominant "
                        f"background; first mismatch at {(row, col)}"
                    )
                    row = h  # bounded message count; break both loops below
                    break
            else:
                continue
            break

        local_row = sr % (sep_row + 1)
        local_col = sc % (sep_col + 1)
        if local_row >= sep_row or local_col >= sep_col:
            errors.append(
                "singleton folds outside the visible output canvas: "
                f"local={(local_row, local_col)} canvas={sep_row}x{sep_col}"
            )
        quadrant = (
            "nw"
            if sr < sep_row and sc < sep_col
            else "ne"
            if sr < sep_row and sc > sep_col
            else "sw"
            if sr > sep_row and sc < sep_col
            else "se"
        )
        sep_position = (
            "centered"
            if sep_row == h // 2 and sep_col == w // 2
            else "offset"
        )
    else:
        local_row = local_col = None
        quadrant = None
        sep_position = None

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "palette": palette,
        "dominant": dom,
        "separator_color": sep_color,
        "singleton_color": singleton,
        "separator_row": sep_row,
        "separator_col": sep_col,
        "singleton_pos": singleton_pos,
        "local_row": local_row,
        "local_col": local_col,
        "quadrant": quadrant,
        "sep_position": sep_position,
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Recover the task-linked structural facts from returned cells only."""
    return _analysis(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact declared axis from a lawful generated grid."""
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    return {name: facts[name] for name in AXES}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical-compatible structural input grammar."""
    errors: list[str] = []
    try:
        _validate_difficulty(difficulty)
    except ValueError as exc:
        errors.append(str(exc))
    facts = _analysis(grid)
    errors.extend(facts["errors"])
    if facts["errors"]:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Strict task-linked predicate used by the semantic census."""
    return self_check(grid)


def _build_output(facts: dict[str, Any], row: int | None = None, col: int | None = None):
    height = facts["separator_row"]
    width = facts["separator_col"]
    dom = facts["dominant"]
    singleton = facts["singleton_color"]
    output = [[dom for _ in range(width)] for _ in range(height)]
    if row is not None and col is not None and 0 <= row < height and 0 <= col < width:
        output[row][col] = singleton
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror for tests; the canonical Racket remains authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid separator-fold grid: " + "; ".join(facts["errors"]))
    return _build_output(facts, facts["local_row"], facts["local_col"])


# ---------------------------------------------------------------------------
# Named plausible wrong rules and semantic witnesses.
# ---------------------------------------------------------------------------


def _rival_modal_color_echo(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid grid for modal-color rival")
    return _build_output(facts)


def _rival_marker_as_answer(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid grid for marker rival")
    return [[facts["singleton_color"]]]


def _rival_copy_nw_quadrant(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid grid for fixed-quadrant rival")
    return [
        list(row[: facts["separator_col"]])
        for row in grid[: facts["separator_row"]]
    ]


def _rival_assume_centered_divider(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid grid for centered-divider rival")
    h, w = facts["grid_h"], facts["grid_w"]
    fake_row, fake_col = h // 2, w // 2
    sr, sc = facts["singleton_pos"]
    local_row = sr % (fake_row + 1)
    local_col = sc % (fake_col + 1)
    rival_facts = dict(facts, separator_row=fake_row, separator_col=fake_col)
    return _build_output(rival_facts, local_row, local_col)


def _rival_count_only_origin(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid grid for count-only rival")
    # The singleton count is always one, so this shortcut uses that count but
    # ignores spatial evidence and always predicts the same local position.
    return _build_output(facts, 0, 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "modal_color_echo": _rival_modal_color_echo,
    "marker_as_answer": _rival_marker_as_answer,
    "copy_nw_quadrant": _rival_copy_nw_quadrant,
    "assume_centered_divider": _rival_assume_centered_divider,
    "count_only_origin": _rival_count_only_origin,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    # Every official example happens to use a centered divider. Generated
    # off-center scenes are therefore required to falsify this real ambiguity.
    "assume_centered_divider": _rival_assume_centered_divider,
}


def _quadrant_witness(name: str):
    return lambda grid: _analysis(grid).get("quadrant") == name and not _analysis(grid)["errors"]


def _witness_centered(grid: Any) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and facts["sep_position"] == "centered"


def _witness_offset(grid: Any) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and facts["sep_position"] == "offset"


def _witness_non_origin_local_position(grid: Any) -> bool:
    facts = _analysis(grid)
    return (
        not facts["errors"]
        and (facts["local_row"], facts["local_col"]) != (0, 0)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "singleton_nw": _quadrant_witness("nw"),
    "singleton_ne": _quadrant_witness("ne"),
    "singleton_sw": _quadrant_witness("sw"),
    "singleton_se": _quadrant_witness("se"),
    "centered_separator": _witness_centered,
    "off_center_separator": _witness_offset,
    "non_origin_local_position": _witness_non_origin_local_position,
}

WITNESS_RIVALS = {
    "singleton_nw": ["modal_color_echo", "marker_as_answer"],
    "singleton_ne": ["copy_nw_quadrant"],
    "singleton_sw": ["copy_nw_quadrant"],
    "singleton_se": ["copy_nw_quadrant"],
    "centered_separator": ["modal_color_echo"],
    "off_center_separator": ["assume_centered_divider"],
    "non_origin_local_position": ["count_only_origin"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require each generated lesson to refute every named plausible rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    valid_demos: list[dict[str, Any]] = []
    quadrants: set[str] = set()
    layouts: set[str] = set()
    local_positions: set[tuple[int, int]] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input outside grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the canonical mirror")
            continue
        facts = _analysis(demo["input"])
        quadrants.add(facts["quadrant"])
        layouts.add(facts["sep_position"])
        local_positions.add((facts["local_row"], facts["local_col"]))
        valid_demos.append(demo)

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input outside grammar: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the canonical mirror")

    if len(quadrants) < 2:
        reasons.append("demonstrations must cover at least two singleton quadrants")
    if layouts != set(SEPARATOR_LAYOUTS):
        reasons.append("demonstrations must include centered and off-center separators")
    if len(local_positions) < 2:
        reasons.append("demonstrations must vary the singleton's local position")

    if valid_demos and not query_errors:
        for name, rival in LESSON_COMPETITORS.items():
            try:
                survives = all(
                    rival(demo["input"]) == demo["output"] for demo in valid_demos
                )
            except Exception as exc:
                reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
                continue
            if survives:
                reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
