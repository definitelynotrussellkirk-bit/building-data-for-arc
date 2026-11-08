"""Generator for ARC task ``0f423424b1dc``.

Read each column independently.  A column changes only when it contains exactly
two nonzero cells, those cells have the same color, and at least one zero lies
between them.  In that case the inclusive vertical segment is filled with the
endpoint color.  Mismatched pairs, blocked pairs, and singleton markers stay
unchanged.

The four-example schedule deliberately includes one canonical-shaped lesson
and three counterexamples.  Together they rule out the strongest shortcuts
left open by the published demonstrations: ignoring endpoint color, ignoring
an extra marker in the span, and extending singleton markers.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0f423424b1dc"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1e2581a2f271"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Fill a vertical span only when its column has exactly two matching "
    "nonzero endpoints with zeros between; leave mismatched, blocked, and "
    "singleton columns unchanged."
)

INVARIANTS = [
    "background is color 0 and every foreground value is an ARC color 1..9",
    "1..3 target columns each contain exactly two matching endpoints with a gap",
    "mismatched, blocked, and singleton distractor columns are optional and unchanged",
    "all structured columns are distinct, so columns can be solved independently",
    "four consecutive samples cover canonical, mismatch, blocked, and singleton profiles",
]

COUNTER_HYPOTHESES = [
    "fill between any two endpoints even when their colors differ",
    "fill between matching outer endpoints even when an extra marker blocks the span",
    "extend a singleton marker as though it implied a vertical segment",
    "copy the input unchanged or always fill every nonempty column",
]

SCHEDULE_PROFILES = ("canonical", "mismatch", "blocked", "singleton")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6..8 canonical anchor; otherwise difficulty-banded",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "6..8 canonical anchor; otherwise difficulty-banded",
        "valid": "6..12",
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "1..3",
    },
    "n_mismatched": {
        "type": "int",
        "default": "1 only in the mismatch profile",
        "valid": "0..1",
    },
    "n_blocked": {
        "type": "int",
        "default": "1 only in the blocked profile",
        "valid": "0..1",
    },
    "n_singletons": {
        "type": "int",
        "default": "1 only in the singleton profile",
        "valid": "0..1",
    },
    "edge_anchor": {
        "type": "bool",
        "default": "deterministically alternates",
        "valid": "true|false",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_INT_BOUNDS = {
    "grid_h": (6, 12),
    "grid_w": (6, 12),
    "n_targets": (1, 3),
    "n_mismatched": (0, 1),
    "n_blocked": (0, 1),
    "n_singletons": (0, 1),
}
_CANONICAL_COLORS = (2, 3, 4, 5, 7)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the deterministic four-sample curriculum branch."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, (lo, hi) in _INT_BOUNDS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")
    if "edge_anchor" in overrides and overrides["edge_anchor"] is not None:
        if type(overrides["edge_anchor"]) is not bool:
            raise ValueError("edge_anchor must be true or false")


def _draw_scheduled_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    scheduled: int,
    overrides: dict[str, Any],
) -> int:
    if label in overrides and overrides[label] is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_choice(label, [scheduled]))


def _draw_scheduled_bool(
    ctx,
    label: str,
    scheduled: bool,
    overrides: dict[str, Any],
) -> bool:
    if label in overrides and overrides[label] is not None:
        return bool(ctx.draw_choice(label, (False, True)))
    return bool(ctx.draw_choice(label, [scheduled]))


def _scheduled_defaults(
    ctx,
    *,
    seed: int,
    sample_index: int,
    band: str,
    profile: str,
) -> dict[str, int | bool]:
    rng = ctx.draw_rng("schedule_defaults")
    if profile == "canonical":
        size = (6, 7, 8)[(int(seed) + int(sample_index) // 4) % 3]
        h = w = size
    else:
        choices = {
            "easy": tuple(range(6, 9)),
            "medium": tuple(range(7, 11)),
            "hard": tuple(range(9, 13)),
        }[band]
        h = int(rng.choice(choices))
        w = int(rng.choice(choices))

    defaults: dict[str, int | bool] = {
        "grid_h": h,
        "grid_w": w,
        "n_targets": 2 + ((int(seed) + int(sample_index)) % 2),
        "n_mismatched": 0,
        "n_blocked": 0,
        "n_singletons": 0,
        "edge_anchor": bool((int(seed) + int(sample_index) // 4) % 2),
    }
    if profile == "mismatch":
        defaults["n_mismatched"] = 1
    elif profile == "blocked":
        defaults["n_blocked"] = 1
    elif profile == "singleton":
        defaults["n_singletons"] = 1
    return defaults


def _row_pairs(h: int, *, interior_only: bool) -> list[tuple[int, int]]:
    lo = 1 if interior_only else 0
    hi = h - 2 if interior_only else h - 1
    return [(a, b) for a in range(lo, hi + 1) for b in range(a + 2, hi + 1)]


def _pick_pair(rng, h: int, *, interior_only: bool) -> tuple[int, int]:
    pairs = _row_pairs(h, interior_only=interior_only)
    if not pairs:
        raise ValueError(f"no endpoint pair fits height={h}, interior_only={interior_only}")
    return tuple(rng.choice(pairs))


def _valid_arc_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _valid_arc_grid(grid)
    if errors:
        return {
            "errors": errors,
            "height": 0,
            "width": 0,
            "targets": [],
            "mismatched": [],
            "blocked": [],
            "singletons": [],
            "invalid": [],
        }

    h, w = len(grid), len(grid[0])
    groups: dict[str, list[dict[str, Any]]] = {
        "targets": [],
        "mismatched": [],
        "blocked": [],
        "singletons": [],
        "invalid": [],
    }
    for c in range(w):
        cells = [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        if not cells:
            continue
        info = {"column": c, "cells": tuple(cells)}
        if len(cells) == 1:
            groups["singletons"].append(info)
            continue
        if len(cells) == 2 and cells[1][0] - cells[0][0] >= 2:
            if cells[0][1] == cells[1][1]:
                groups["targets"].append(info)
            else:
                groups["mismatched"].append(info)
            continue
        if len(cells) == 3:
            first, middle, last = cells
            if (
                last[0] - first[0] >= 2
                and first[1] == last[1]
                and middle[1] != first[1]
                and first[0] < middle[0] < last[0]
            ):
                groups["blocked"].append(info)
                continue
        groups["invalid"].append(info)

    return {
        "errors": [],
        "height": h,
        "width": w,
        **groups,
    }


def observe_overrides(grid: Any) -> dict[str, int | bool]:
    """Recover every public axis exactly from a returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    h, w = analysis["height"], analysis["width"]
    edge_anchor = any(
        cells[0][0] == 0 or cells[-1][0] == h - 1
        for cells in (item["cells"] for item in analysis["targets"])
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "n_targets": len(analysis["targets"]),
        "n_mismatched": len(analysis["mismatched"]),
        "n_blocked": len(analysis["blocked"]),
        "n_singletons": len(analysis["singletons"]),
        "edge_anchor": edge_anchor,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate generated structure without consulting any output."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    if not 6 <= h <= 12 or not 6 <= w <= 12:
        errors.append(f"dimensions {h}x{w} outside 6..12")
    counts = observe_overrides(grid)
    if not 1 <= counts["n_targets"] <= 3:
        errors.append(f"expected 1..3 target columns, found {counts['n_targets']}")
    for label in ("n_mismatched", "n_blocked", "n_singletons"):
        if not 0 <= counts[label] <= 1:
            errors.append(f"{label} must be 0..1, found {counts[label]}")
    if analysis["invalid"]:
        columns = [item["column"] for item in analysis["invalid"]]
        errors.append(f"unclassified nonempty column(s): {columns}")
    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero * 2 >= h * w:
        errors.append("background 0 must remain strictly modal")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the canonical 6/7/8-square grammar and its scheduled anchors."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    errors.extend(self_check(grid))
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    if h != w or h not in (6, 7, 8):
        errors.append(f"canonical-like dimensions must be 6x6, 7x7, or 8x8; got {h}x{w}")
    if any(analysis[name] for name in ("mismatched", "blocked", "singletons")):
        errors.append("canonical-like grids contain only matching endpoint columns")
    colors = {
        value
        for row in grid
        for value in row
        if value != 0
    }
    if not colors <= set(_CANONICAL_COLORS):
        errors.append(f"canonical-like palette must be a subset of {_CANONICAL_COLORS}")
    if not 2 <= len(analysis["targets"]) <= 3:
        errors.append("canonical-like grids use 2..3 target columns")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the selected Racket rule."""
    errors = _valid_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for c in range(w):
        cells = [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        if (
            len(cells) == 2
            and cells[0][1] == cells[1][1]
            and cells[1][0] - cells[0][0] >= 2
        ):
            color = cells[0][1]
            for r in range(cells[0][0], cells[1][0] + 1):
                out[r][c] = color
    return out


def _rival_ignore_endpoint_color(grid: Any) -> list[list[int]]:
    """Wrongly fill any two-marker column using the upper marker's color."""
    errors = _valid_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for c in range(w):
        cells = [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        if len(cells) == 2 and cells[1][0] - cells[0][0] >= 2:
            for r in range(cells[0][0], cells[1][0] + 1):
                out[r][c] = cells[0][1]
    return out


def _rival_ignore_extra_cells(grid: Any) -> list[list[int]]:
    """Wrongly use matching outer markers even when a third marker blocks them."""
    errors = _valid_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = rule_mirror(grid)
    for c in range(w):
        cells = [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        if (
            len(cells) >= 2
            and cells[0][1] == cells[-1][1]
            and cells[-1][0] - cells[0][0] >= 2
        ):
            for r in range(cells[0][0], cells[-1][0] + 1):
                out[r][c] = cells[0][1]
    return out


def _rival_extend_singletons(grid: Any) -> list[list[int]]:
    """Wrongly extend a singleton by one cell toward the nearest interior."""
    errors = _valid_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = rule_mirror(grid)
    for c in range(w):
        cells = [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        if len(cells) == 1:
            r, color = cells[0]
            rr = r + 1 if r < h - 1 else r - 1
            out[rr][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_endpoint_color": _rival_ignore_endpoint_color,
    "ignore_extra_cells": _rival_ignore_extra_cells,
    "extend_singletons": _rival_extend_singletons,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_mismatch(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["mismatched"])


def _witness_blocked(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["blocked"])


def _witness_singleton(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["singletons"])


SEMANTIC_WITNESSES = {
    "mismatch": _witness_mismatch,
    "blocked": _witness_blocked,
    "singleton": _witness_singleton,
}
WITNESS_RIVALS = {
    "mismatch": ["ignore_endpoint_color"],
    "blocked": ["ignore_extra_cells"],
    "singleton": ["extend_singletons"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Verify that a four-demo lesson eliminates every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
            continue
        valid_demos.append(pair)

    if len(valid_demos) == len(demos):
        survivors = [
            name
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in valid_demos)
        ]
        if survivors:
            reasons.append(f"demonstrations leave rival(s) alive: {survivors}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the endpoint rule")
    return reasons


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    """Generate one deterministic lesson input with exact observable overrides."""
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(
        ctx,
        seed=seed,
        sample_index=sample_index,
        band=band,
        profile=profile,
    )

    h = _draw_scheduled_int(ctx, "grid_h", 6, 12, int(defaults["grid_h"]), overrides)
    w = _draw_scheduled_int(ctx, "grid_w", 6, 12, int(defaults["grid_w"]), overrides)
    n_targets = _draw_scheduled_int(
        ctx, "n_targets", 1, 3, int(defaults["n_targets"]), overrides
    )
    n_mismatched = _draw_scheduled_int(
        ctx, "n_mismatched", 0, 1, int(defaults["n_mismatched"]), overrides
    )
    n_blocked = _draw_scheduled_int(
        ctx, "n_blocked", 0, 1, int(defaults["n_blocked"]), overrides
    )
    n_singletons = _draw_scheduled_int(
        ctx, "n_singletons", 0, 1, int(defaults["n_singletons"]), overrides
    )
    edge_anchor = _draw_scheduled_bool(
        ctx, "edge_anchor", bool(defaults["edge_anchor"]), overrides
    )

    total_columns = n_targets + n_mismatched + n_blocked + n_singletons
    if total_columns > w:
        raise ValueError(
            f"requested {total_columns} structured columns but grid_w={w}; "
            "reduce counts or increase grid_w"
        )

    layout_rng = ctx.draw_rng("layout")
    columns = layout_rng.sample(range(w), total_columns)
    grid = full_grid(h, w, 0)

    colors = list(_CANONICAL_COLORS if total_columns <= 3 and not (n_mismatched or n_blocked or n_singletons) else range(1, 10))
    ctx.draw_rng("colors").shuffle(colors)
    color_index = 0

    target_columns = columns[:n_targets]
    cursor = n_targets
    mismatch_columns = columns[cursor: cursor + n_mismatched]
    cursor += n_mismatched
    blocked_columns = columns[cursor: cursor + n_blocked]
    cursor += n_blocked
    singleton_columns = columns[cursor: cursor + n_singletons]

    for index, c in enumerate(target_columns):
        if edge_anchor and index == 0:
            top, bottom = 0, h - 1
        else:
            top, bottom = _pick_pair(
                layout_rng,
                h,
                interior_only=not edge_anchor,
            )
        color = colors[color_index]
        color_index += 1
        grid[top][c] = color
        grid[bottom][c] = color

    for c in mismatch_columns:
        top, bottom = _pick_pair(layout_rng, h, interior_only=False)
        upper_color, lower_color = colors[color_index], colors[color_index + 1]
        color_index += 2
        grid[top][c] = upper_color
        grid[bottom][c] = lower_color

    for c in blocked_columns:
        top, bottom = _pick_pair(layout_rng, h, interior_only=False)
        middle = layout_rng.randint(top + 1, bottom - 1)
        endpoint_color, blocker_color = colors[color_index], colors[color_index + 1]
        color_index += 2
        grid[top][c] = endpoint_color
        grid[middle][c] = blocker_color
        grid[bottom][c] = endpoint_color

    for c in singleton_columns:
        row = layout_rng.randint(1, h - 2)
        color = colors[color_index]
        color_index += 1
        grid[row][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid grid: " + "; ".join(errors))
    return grid
