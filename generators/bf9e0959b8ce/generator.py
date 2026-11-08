"""Generator for ``bf9e0959b8ce`` — separator-keyed dot routing.

A full separator row or column divides a sparse source region from an aligned
key.  Each source dot is moved along its own column/row: a dot whose color
matches the aligned key cell goes to the edge next to the separator; a dot
whose color does not match goes to the far outer edge.  The source cell is
cleared to the source background.

The ordinary six-profile schedule contains exact anchors for all three
canonical ``(height, width, palette-size)`` profiles and alternates row/column
lessons so every three consecutive demonstrations cover both orientations.
Every generated input contains both matching and non-matching dots, and the
source dots span at least two source-side rows/columns so the canonical-only
"all dots form one source line" shortcut is explicitly refuted.  The schedule
strictly alternates row/column orientation; every four-pair lesson block is
therefore 2+2, so any one held-out query still leaves both orientations taught.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf9e0959b8ce"
TASK_ID = "bf9e0959b8ce"
VERSION = "2.2.0"
RULE_HASH = "5fa488301c04"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.80

SUMMARY = (
    "A full separator row or column divides a sparse source side from an "
    "aligned key row or column. Matching source dots move to the edge next "
    "to the separator; non-matching dots move to the far outer edge."
)

INVARIANTS = [
    "exactly one non-background full-height or full-width separator",
    "source dots occupy distinct aligned columns/rows",
    "every source dot has a non-background aligned key value",
    "both matching and non-matching routing branches are present",
    "source dots span at least two movement-axis rows/columns",
    "the transformation is non-identity",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-shaped",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-shaped",
        "valid": "8..20",
    },
    "orientation": {
        "type": "str",
        "default": "six-profile row/column schedule",
        "valid": "row|col",
    },
    "n_dots": {
        "type": "int",
        "default": "scheduled anchor or difficulty-shaped",
        "valid": "2..8",
    },
}

# Every combination of declared exact axes is constructible, including both
# 8x8/n_dots=8 boundary orientations (those draws simply omit a decorative
# frame so all aligned rows/columns remain available).
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCHEDULE_PROFILES = tuple(range(6))

# Three exact canonical-profile anchors.  The remaining profiles broaden size
# and palette support while retaining the same semantic grammar.
_ANCHORS: dict[int, dict[str, Any]] = {
    0: {
        "grid_h": 16,
        "grid_w": 16,
        "orientation": "row",
        "n_dots": 7,
        "palette_size": 5,
        "key_bg_distinct": False,
    },
    1: {
        "grid_h": 8,
        "grid_w": 8,
        "orientation": "col",
        "n_dots": 5,
        "palette_size": 6,
        "key_bg_distinct": True,
    },
    3: {
        "grid_h": 16,
        "grid_w": 16,
        "orientation": "col",
        "n_dots": 7,
        "palette_size": 7,
        "key_bg_distinct": False,
    },
}

# Strict alternation makes every four consecutive pairs 2 row + 2 column.
# Moving the third exact anchor from profile 2 to profile 3 preserves its
# canonical column orientation while making every held-out query rotation
# retain at least one demonstration of each orientation.
_PROFILE_ORIENTATIONS = ("row", "col", "row", "col", "row", "col")


def _validate_public_arguments(seed: int, sample_index: int, difficulty) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, string, or None)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the deterministic six-profile curriculum schedule."""
    _validate_public_arguments(seed, sample_index, difficulty)
    return sample_index % len(SCHEDULE_PROFILES)


def _axis_was_overridden(overrides: dict[str, Any], axis: str) -> bool:
    return axis in overrides and overrides[axis] is not None


def _draw_axis_int(ctx, overrides: dict[str, Any], axis: str, lo: int, hi: int,
                   scheduled: int | None) -> int:
    if _axis_was_overridden(overrides, axis):
        return ctx.draw_int_strict(axis, lo, hi)
    if scheduled is not None:
        return ctx.draw_int_strict(axis, scheduled, scheduled)
    return ctx.draw_int_diff(axis, lo, hi)


def _draw_axis_choice(ctx, overrides: dict[str, Any], axis: str,
                      options: tuple[str, ...], scheduled: str) -> str:
    if _axis_was_overridden(overrides, axis):
        return ctx.draw_choice(axis, options)
    return ctx.draw_choice(axis, (scheduled,))


def _palette_plan(ctx, *, n_dots: int, anchor: dict[str, Any] | None,
                  can_frame: bool, orientation: str) -> tuple[int, int, int, tuple[int, ...], bool]:
    """Return source bg, separator, key bg, signal colors, and frame flag."""
    if anchor is not None:
        palette_size = int(anchor["palette_size"])
        key_bg_distinct = bool(anchor["key_bg_distinct"] and can_frame)
    else:
        # A distinct key-side field is canonical for the column variant.  Row
        # scenes keep the source background on both sides so the selected
        # Racket rule's `(mode g)` (which ignores color 0) cannot mistake a
        # full source row for the separator.
        key_bg_distinct = bool(
            orientation == "col"
            and can_frame
            and ctx.draw_choice("key_bg_mode", ("shared", "distinct")) == "distinct"
        )
        # At most n_dots+1 signal colors can be guaranteed visible across the
        # dot/key pairs.  This keeps the declared palette honest for n=2.
        max_signals = min(5, n_dots + 1)
        signal_count = ctx.draw_int("signal_color_count", 2, max_signals)
        palette_size = 2 + int(key_bg_distinct) + signal_count

    signal_count = palette_size - 2 - int(key_bg_distinct)
    # The canonical Racket prelude's `(mode g)` ignores color 0 by default.
    # Therefore color 0 is legal as a dot/key value but never as the source
    # background; otherwise an earlier uniform source column can be mistaken
    # for the separator.
    source_bg = ctx.draw_color("source_bg_color", exclude=(0,))
    colors = ctx.draw_distinct_colors(
        "scene_colors",
        n=1 + int(key_bg_distinct) + signal_count,
        exclude=(source_bg,),
    )
    separator = colors[0]
    offset = 1
    key_bg = colors[offset] if key_bg_distinct else source_bg
    offset += int(key_bg_distinct)
    signals = tuple(colors[offset:])
    return source_bg, separator, key_bg, signals, key_bg_distinct


def _dot_and_key_colors(signals: tuple[int, ...], n_dots: int) -> tuple[list[int], list[int]]:
    """Build visible colors with alternating matching/non-matching branches."""
    dot_colors = [signals[index % len(signals)] for index in range(n_dots)]
    key_colors: list[int] = []
    missing = [color for color in signals if color not in dot_colors]
    for index, dot in enumerate(dot_colors):
        if index % 2 == 0:
            key_colors.append(dot)
            continue
        if missing:
            candidate = missing.pop(0)
            if candidate == dot:
                candidate = next(color for color in signals if color != dot)
            key_colors.append(candidate)
        else:
            key_colors.append(next(color for color in signals if color != dot))
    return dot_colors, key_colors


def _choose_aligned_positions(rng, count: int, extent: int, framed: bool) -> list[int]:
    legal = list(range(1, extent - 1)) if framed else list(range(extent))
    if count > len(legal):
        raise ValueError(f"cannot place {count} unique aligned positions in extent {extent}")
    return sorted(rng.sample(legal, count))


def _choose_source_positions(rng, count: int, legal: list[int]) -> list[int]:
    """Choose movement-axis positions with at least two represented lines."""
    if count < 2:
        raise ValueError("at least two source dots are required")
    if len(legal) < 2:
        raise ValueError("at least two legal source rows/columns are required")
    first, second = rng.sample(legal, 2)
    positions = [first, second]
    positions.extend(rng.choice(legal) for _ in range(count - 2))
    rng.shuffle(positions)
    return positions


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile = schedule_profile(seed, sample_index, difficulty)
    anchor = _ANCHORS.get(profile)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _draw_axis_int(
        ctx, overrides, "grid_h", 8, 18,
        None if anchor is None else int(anchor["grid_h"]),
    )
    width = _draw_axis_int(
        ctx, overrides, "grid_w", 8, 20,
        None if anchor is None else int(anchor["grid_w"]),
    )
    orientation = _draw_axis_choice(
        ctx, overrides, "orientation", ("row", "col"),
        str(anchor["orientation"]) if anchor is not None
        else _PROFILE_ORIENTATIONS[profile],
    )
    n_dots = _draw_axis_int(
        ctx, overrides, "n_dots", 2, 8,
        None if anchor is None else int(anchor["n_dots"]),
    )

    # A frame mirrors the canonical key-side border.  It is decorative and is
    # omitted only when an exact n_dots override consumes every aligned slot.
    aligned_extent = width if orientation == "row" else height
    can_frame = n_dots <= aligned_extent - 2
    source_bg, separator, key_bg, signals, framed = _palette_plan(
        ctx,
        n_dots=n_dots,
        anchor=anchor,
        can_frame=can_frame,
        orientation=orientation,
    )
    dot_colors, key_colors = _dot_and_key_colors(signals, n_dots)

    grid = full_grid(height, width, source_bg)
    layout_rng = ctx.draw_rng("layout")
    aligned = _choose_aligned_positions(layout_rng, n_dots, aligned_extent, framed)

    if orientation == "row":
        # Source is above; leave at least one non-destination source row and at
        # least two rows on the key side.
        sep_row = layout_rng.randint(max(3, height // 2), height - 3)
        for col in range(width):
            grid[sep_row][col] = separator
        key_row = sep_row + 1
        if framed:
            for row in range(key_row, height):
                for col in range(width):
                    grid[row][col] = key_bg
                grid[row][0] = separator
                grid[row][width - 1] = separator
        elif key_bg != source_bg:  # defensive; _palette_plan avoids this case
            raise AssertionError("distinct key background requires a frame")

        source_rows = list(range(1, sep_row - 1))
        source_positions = _choose_source_positions(
            layout_rng, n_dots, source_rows
        )
        for index, col in enumerate(aligned):
            row = source_positions[index]
            grid[row][col] = dot_colors[index]
            grid[key_row][col] = key_colors[index]
    else:
        # Key is left, source is right; keep one interior source column so all
        # generated dots visibly move away from their original position.
        # Keep at least two interior source columns so generated scenes refute
        # the canonical-only single-source-line shortcut.
        sep_col = layout_rng.randint(2, min(width // 2, width - 5))
        for row in range(height):
            grid[row][sep_col] = separator
        key_col = sep_col - 1
        if framed:
            for row in range(height):
                for col in range(sep_col):
                    grid[row][col] = key_bg
            for col in range(sep_col):
                grid[0][col] = separator
                grid[height - 1][col] = separator
        elif key_bg != source_bg:
            raise AssertionError("distinct key background requires a frame")

        source_cols = list(range(sep_col + 2, width - 1))
        source_positions = _choose_source_positions(
            layout_rng, n_dots, source_cols
        )
        for index, row in enumerate(aligned):
            col = source_positions[index]
            grid[row][col] = dot_colors[index]
            grid[row][key_col] = key_colors[index]

    findings = self_check(grid)
    if findings:
        raise AssertionError("generator constructed an invalid grid: " + "; ".join(findings))
    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if requested is not None and observed[axis] != requested:
            raise AssertionError(
                f"constructed {axis}={observed[axis]!r}, requested {requested!r}"
            )
    return grid


def _mode(values: list[int]) -> int:
    if not values:
        raise ValueError("cannot take mode of an empty sequence")
    return Counter(values).most_common(1)[0][0]


def _analysis(grid: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"errors": []}
    errors: list[str] = base["errors"]
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty row sequence")
        return base
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        errors.append("every grid row must be a non-empty sequence")
        return base
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return base
    height = len(grid)
    base.update(height=height, width=width)
    if not (8 <= height <= 18):
        errors.append(f"height {height} outside 8..18")
    if not (8 <= width <= 20):
        errors.append(f"width {width} outside 8..20")
    cells = [value for row in grid for value in row]
    if any(type(value) is not int or not (0 <= value <= 9) for value in cells):
        errors.append("grid colors must be integers in 0..9")
        return base
    if errors:
        return base

    def candidate(orientation: str, separator_index: int) -> dict[str, Any]:
        trial: dict[str, Any] = {
            "errors": [], "height": height, "width": width,
            "orientation": orientation, "separator_index": separator_index,
            "global_bg": _mode(cells),
        }
        trial_errors: list[str] = trial["errors"]
        if orientation == "row":
            if not (2 <= separator_index <= height - 2):
                trial_errors.append("row separator leaves no lawful source/key regions")
                return trial
            separator_color = grid[separator_index][0]
            source_values = [
                grid[row][col]
                for row in range(separator_index)
                for col in range(width)
            ]
            source_bg = _mode(source_values)
            dots = [
                (row, col, grid[row][col])
                for row in range(separator_index)
                for col in range(width)
                if grid[row][col] != source_bg
            ]
            aligned_values = [grid[separator_index + 1][col] for _, col, _ in dots]
            aligned_coords = [col for _, col, _ in dots]
            near, far = separator_index - 1, 0
            # The aligned key row itself may contain no background cell when
            # n_dots == grid_w, so infer the key-side background from the
            # region beyond that row first (canonical frames live there too).
            key_side_values = [
                grid[row][col]
                for row in range(separator_index + 2, height)
                for col in range(width)
                if grid[row][col] != separator_color
            ]
            if not key_side_values:
                key_side_values = [
                    grid[separator_index + 1][col]
                    for col in range(width)
                    if grid[separator_index + 1][col] != separator_color
                ]
        else:
            if not (2 <= separator_index <= width - 3):
                trial_errors.append("column separator leaves no lawful key/source regions")
                return trial
            separator_color = grid[0][separator_index]
            source_values = [
                grid[row][col]
                for row in range(height)
                for col in range(separator_index + 1, width)
            ]
            source_bg = _mode(source_values)
            dots = [
                (row, col, grid[row][col])
                for row in range(height)
                for col in range(separator_index + 1, width)
                if grid[row][col] != source_bg
            ]
            aligned_values = [grid[row][separator_index - 1] for row, _, _ in dots]
            aligned_coords = [row for row, _, _ in dots]
            near, far = separator_index + 1, width - 1
            # Likewise, infer the key-side background from columns beyond
            # the aligned key column; the key column can be completely filled.
            key_side_values = [
                grid[row][col]
                for row in range(height)
                for col in range(separator_index - 1)
                if grid[row][col] != separator_color
            ]
            if not key_side_values:
                key_side_values = [
                    grid[row][separator_index - 1]
                    for row in range(height)
                    if grid[row][separator_index - 1] != separator_color
                ]

        trial.update(
            separator_color=separator_color,
            source_bg=source_bg,
            dots=dots,
            near=near,
            far=far,
        )
        if separator_color == source_bg:
            trial_errors.append("separator color equals source background")
        if source_bg == 0:
            trial_errors.append(
                "source background 0 is unsupported because selected Racket mode ignores 0"
            )
        if not (2 <= len(dots) <= 8):
            trial_errors.append(f"source dot count {len(dots)} outside 2..8")
        if len(set(aligned_coords)) != len(aligned_coords):
            trial_errors.append("multiple source dots share an aligned row/column")
        if not key_side_values:
            trial_errors.append("key side has no non-separator cells")
            return trial
        key_bg = _mode(key_side_values)
        trial["key_bg"] = key_bg
        if any(value == key_bg for value in aligned_values):
            trial_errors.append("a source dot is aligned with key background rather than a key value")

        matches = []
        nonmatches = []
        for dot, key_value in zip(dots, aligned_values):
            (matches if dot[2] == key_value else nonmatches).append(dot)
        trial.update(
            aligned_values=aligned_values,
            match_dots=matches,
            nonmatch_dots=nonmatches,
            match_count=len(matches),
            nonmatch_count=len(nonmatches),
            n_dots=len(dots),
        )
        if not matches:
            trial_errors.append("matching routing branch is absent")
        if not nonmatches:
            trial_errors.append("non-matching routing branch is absent")
        return trial

    uniform_rows = [
        row for row in range(height)
        if all(grid[row][col] == grid[row][0] for col in range(width))
    ]
    uniform_cols = [
        col for col in range(width)
        if all(grid[row][col] == grid[0][col] for row in range(height))
    ]
    trials = (
        [candidate("row", row) for row in uniform_rows]
        + [candidate("col", col) for col in uniform_cols]
    )
    lawful = [trial for trial in trials if not trial["errors"]]
    if len(lawful) == 1:
        return lawful[0]
    if len(lawful) > 1:
        base["errors"].append(
            "multiple separator lines satisfy the task grammar: "
            + ", ".join(
                f"{trial['orientation']}={trial['separator_index']}"
                for trial in lawful
            )
        )
        return base

    # Prefer diagnostics from candidates that came closest to the grammar.
    ranked = sorted(trials, key=lambda trial: len(trial["errors"]))
    if ranked:
        best = ranked[0]
        base["errors"].append(
            f"no uniform line satisfies separator grammar; closest "
            f"{best['orientation']}={best['separator_index']}: "
            + "; ".join(best["errors"][:3])
        )
    else:
        base["errors"].append("grid has no uniform row or column separator candidate")
    return base


def _route(grid: list[list[int]], destination: Callable[[dict[str, Any], tuple[int, int, int], int], int] | None,
           *, place: bool = True) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [list(row) for row in grid]
    for dot, key_value in zip(info["dots"], info["aligned_values"]):
        row, col, color = dot
        out[row][col] = info["source_bg"]
        if not place:
            continue
        dest = destination(info, dot, key_value) if destination else (
            info["near"] if color == key_value else info["far"]
        )
        if info["orientation"] == "row":
            out[dest][col] = color
        else:
            out[row][dest] = color
    return out


def _apply_rule(grid: list[list[int]]) -> list[list[int]]:
    """Python audit mirror of the selected canonical Racket rule."""
    return _route(grid, None)


rule_mirror = _apply_rule


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    info = _analysis(grid)
    findings = list(info["errors"])
    if findings:
        return findings
    try:
        if _apply_rule(grid) == [list(row) for row in grid]:
            findings.append("separator-keyed routing is identity")
    except Exception as exc:
        findings.append(f"rule mirror raised {type(exc).__name__}: {exc}")
    return findings


def strict_canonical_like(grid) -> list[str]:
    """Accept precisely the task's lawful two-branch input grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "orientation": info["orientation"],
        "n_dots": info["n_dots"],
    }


def profile_signature(grid) -> tuple[int, int, int]:
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def _lawful_info(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


def _identity(grid):
    return [list(row) for row in grid]


def _always_near(grid):
    return _route(grid, lambda info, dot, key: info["near"])


def _always_far(grid):
    return _route(grid, lambda info, dot, key: info["far"])


def _erase_source(grid):
    return _route(grid, None, place=False)


def _row_only(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _apply_rule(grid) if info["orientation"] == "row" else _identity(grid)


def _col_only(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _apply_rule(grid) if info["orientation"] == "col" else _identity(grid)


def _motion_coordinate(info: dict[str, Any], dot: tuple[int, int, int]) -> int:
    return dot[0] if info["orientation"] == "row" else dot[1]


def _single_source_line(grid):
    """Canonical-fitting rival: route only the densest source row/column.

    Every labeled canonical pair puts all source dots on one movement-axis
    line.  A solver can therefore mistake that line for the source object and
    ignore markers on other source rows/columns.  To make the rival total on
    generated inputs, ties choose the earliest densest source line.
    """
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    counts = Counter(_motion_coordinate(info, dot) for dot in info["dots"])
    peak = max(counts.values())
    selected_line = min(line for line, count in counts.items() if count == peak)
    out = [list(row) for row in grid]
    for dot, key_value in zip(info["dots"], info["aligned_values"]):
        if _motion_coordinate(info, dot) != selected_line:
            continue
        row, col, color = dot
        out[row][col] = info["source_bg"]
        destination = info["near"] if color == key_value else info["far"]
        if info["orientation"] == "row":
            out[destination][col] = color
        else:
            out[row][destination] = color
    return out


SEMANTIC_RIVALS = {
    "identity": _identity,
    "always_near": _always_near,
    "always_far": _always_far,
    "erase_source": _erase_source,
    "row_only": _row_only,
    "col_only": _col_only,
    "single_source_line": _single_source_line,
}

SEMANTIC_WITNESSES = {
    "matching_dot_routes_near": lambda grid: _witness(
        grid,
        lambda info: any(
            dot[0] != info["near"] if info["orientation"] == "row" else dot[1] != info["near"]
            for dot in info["match_dots"]
        ),
    ),
    "nonmatching_dot_routes_far": lambda grid: _witness(
        grid,
        lambda info: any(
            dot[0] != info["far"] if info["orientation"] == "row" else dot[1] != info["far"]
            for dot in info["nonmatch_dots"]
        ),
    ),
    "row_orientation": lambda grid: _witness(grid, lambda info: info["orientation"] == "row"),
    "column_orientation": lambda grid: _witness(grid, lambda info: info["orientation"] == "col"),
    "multiple_source_lines": lambda grid: _witness(
        grid,
        lambda info: len(
            {_motion_coordinate(info, dot) for dot in info["dots"]}
        ) >= 2,
    ),
    "non_identity": lambda grid: _witness(grid, lambda info: _apply_rule(grid) != grid),
}

WITNESS_RIVALS = {
    "matching_dot_routes_near": ["identity", "always_far", "erase_source"],
    "nonmatching_dot_routes_far": ["identity", "always_near", "erase_source"],
    "row_orientation": ["col_only"],
    "column_orientation": ["row_only"],
    "multiple_source_lines": ["single_source_line"],
    "non_identity": ["identity", "erase_source"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"single_source_line": _single_source_line}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named plausible routing rule alive."""
    reasons: list[str] = []
    episodes = [*demos, query]
    demo_orientations: set[str] = set()
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{role} input is malformed: {findings[:2]}")
            continue
        if _apply_rule(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with separator-keyed routing")
            continue
        if index < len(demos):
            demo_orientations.add(observe_overrides(episode["input"])["orientation"])
    if reasons:
        return reasons
    if demo_orientations != {"row", "col"}:
        reasons.append(
            "demonstrations do not cover both row and column separator orientations"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"demos do not falsify shortcut {name!r}")
        except Exception as exc:
            reasons.append(f"shortcut {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
