"""Generator for ARC task ``569aa05e004d`` (row-local exact-pair fill).

The authoritative rule starts from a fresh color-0 grid.  For each row and
for each non-zero color, if that color occurs exactly twice in that row, the
inclusive interval between those two cells is painted with the color.  All
other input marks disappear.  Consequently a row may contain two independent
fillable colors, a different-colored blocker is overwritten, and colors whose
row-local multiplicity is one or three do not survive.

Ordinary generation uses a four-sample lesson schedule: canonical-profile
anchor, combined semantic controls, combined semantic controls, canonical-
profile anchor.  Every sliding three-demonstration window therefore contains a
single scene that refutes all declared canonical-fitting shortcut rules, while
half of the stream remains on the exact public (height, width, palette-size)
profiles.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "569aa05e004d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2e54f71e3122"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "On a color-0 grid, inspect each row independently and count each non-zero "
    "color separately. If a color occurs exactly twice in that row, paint its "
    "inclusive horizontal interval in that color on a fresh zero output. "
    "Other marks vanish. Multiple disjoint exact-pair colors may fill in one "
    "row; blockers inside a qualifying span are overwritten; singleton and "
    "triple controls are erased."
)

INVARIANTS = [
    "background is color 0 and every grid is rectangular within ARC bounds",
    "every normal draw contains three to five row-local exact-pair relations",
    "qualifying spans have a visible gap and never overlap one another",
    "declared controls distinguish row-local exact multiplicity from shortcuts",
    "every declared override is finite, exact, and recoverable from the grid",
    "the canonical Racket program, not the Python mirror, is output authority",
]

_LAYOUTS: dict[str, tuple[int, int, int]] = {
    "canonical3": (6, 12, 3),
    "canonical4": (6, 12, 4),
    "compact3": (5, 9, 3),
    "medium4": (8, 13, 4),
    "large5": (10, 16, 5),
}
_TEXTURES = ("clean", "multi_pair", "blocker", "count_controls", "all_controls")
_EDGE_PROFILES = ("interior", "edge_mix")

AXES = {
    "layout": {
        "type": "enum",
        "default": "scheduled by sample_index and difficulty",
        "valid": "canonical3|canonical4|compact3|medium4|large5",
    },
    "texture": {
        "type": "enum",
        "default": "scheduled clean/all_controls",
        "valid": "clean|multi_pair|blocker|count_controls|all_controls",
    },
    "edge_profile": {
        "type": "enum",
        "default": "scheduled interior/edge_mix",
        "valid": "interior|edge_mix",
    },
    "color_reuse": {
        "type": "bool",
        "default": "scheduled false/true",
        "valid": "false|true",
    },
}

# Every Cartesian combination is intentionally supported.  Declaring the empty
# set opts this generator into the strict override-rejection policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = ("canonical_anchor", "all_controls")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the deterministic four-slot pedagogical branch."""
    del seed, difficulty
    return "canonical_anchor" if int(sample_index) % 4 in (0, 3) else "all_controls"


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("layout", "texture", "edge_profile"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
    value = overrides.get("color_reuse")
    if value is not None and type(value) is not bool:
        raise ValueError("color_reuse must be a boolean")


def _scheduled_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    slot = int(sample_index) % 4
    if slot == 0:
        return {
            "layout": "canonical3",
            "texture": "clean",
            "edge_profile": "interior",
            "color_reuse": False,
        }
    if slot == 3:
        return {
            "layout": "canonical4",
            "texture": "clean",
            "edge_profile": "edge_mix",
            "color_reuse": False,
        }
    layout = {
        "easy": "compact3",
        "hard": "large5",
    }.get(difficulty, "medium4")
    return {
        "layout": layout,
        "texture": "all_controls",
        "edge_profile": "edge_mix",
        "color_reuse": True,
    }


def _draw_choice(ctx, overrides: dict[str, Any], name: str,
                 options: tuple[Any, ...], default: Any) -> Any:
    choices = options if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, choices)


def _relation_rows(texture: str, relation_count: int,
                   selected_rows: list[int]) -> tuple[list[int], int | None, list[int]]:
    """Return relation rows, optional blocker relation index, control rows."""
    has_multi = texture in ("multi_pair", "all_controls")
    has_blocker = texture in ("blocker", "all_controls")
    has_counts = texture in ("count_controls", "all_controls")

    relation_row_count = relation_count - 1 if has_multi else relation_count
    relation_slots = selected_rows[:relation_row_count]
    rows: list[int] = []
    if has_multi:
        rows.extend((relation_slots[0], relation_slots[0]))
        rows.extend(relation_slots[1:])
    else:
        rows.extend(relation_slots)

    blocker_index = (2 if has_multi else 0) if has_blocker else None
    control_rows = selected_rows[relation_row_count:]
    if has_counts and len(control_rows) != 2:
        raise RuntimeError("count-control row allocation drifted")
    return rows, blocker_index, control_rows


def _edge_roles(relation_count: int, edge_profile: str) -> list[str]:
    if edge_profile == "interior":
        return ["interior"] * relation_count
    roles = ["left", "right", "full"]
    roles.extend("interior" for _ in range(relation_count - len(roles)))
    return roles[:relation_count]


def _span_columns(rng, width: int, relation_index: int, role: str,
                  multi_pair: bool) -> tuple[int, int]:
    """Choose non-overlapping, visible-gap spans for every generated role."""
    if role == "left":
        return 0, rng.randint(2, max(2, width // 3))
    if role == "right":
        lo = max(width * 2 // 3, 3)
        left = rng.randint(min(lo, width - 3), width - 3)
        return left, width - 1
    if role == "full":
        return 0, width - 1

    # The first two relations share a row only in multi-pair textures.  Pin
    # them to disjoint interior thirds; all other relations occupy other rows.
    if multi_pair and relation_index == 0:
        return 1, min(3, width - 5)
    if multi_pair and relation_index == 1:
        return max(5, width - 4), width - 2
    left = rng.randint(1, width - 4)
    right = rng.randint(left + 2, width - 2)
    return left, right


def _relation_colors(rng, relation_count: int, color_reuse: bool,
                     multi_pair: bool) -> list[int]:
    unique_needed = relation_count - 1 if color_reuse else relation_count
    pool = rng.sample(range(1, 10), unique_needed)
    if not color_reuse:
        return pool

    colors: list[int] = []
    if multi_pair:
        # Relations 0 and 2 are on different rows; relation 1 shares row 0 and
        # must remain a different color so both row-local counts equal two.
        colors = [pool[0], pool[1], pool[0]]
        colors.extend(pool[2:])
    else:
        colors = [pool[0], pool[0]]
        colors.extend(pool[1:])
    if len(colors) != relation_count:
        raise RuntimeError("color-reuse construction drifted")
    return colors


def _control_colors(rng, relation_colors: list[int], count: int) -> list[int]:
    available = [color for color in range(1, 10) if color not in set(relation_colors)]
    if len(available) < count:
        raise ValueError("not enough colors remain for exact semantic controls")
    return rng.sample(available, count)


def _place_count_controls(grid: list[list[int]], rows: list[int], colors: list[int],
                          rng) -> None:
    width = len(grid[0])
    triple_row, singleton_row = rows
    triple_columns = sorted(rng.sample(range(width), 3))
    for column in triple_columns:
        grid[triple_row][column] = colors[0]
    first, second = sorted(rng.sample(range(width), 2))
    grid[singleton_row][first] = colors[1]
    grid[singleton_row][second] = colors[2]


def generate(seed: int, sample_index: int, *, difficulty: Any = None,
             **overrides: Any) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(sample_index, difficulty)
    layout = _draw_choice(ctx, overrides, "layout", tuple(_LAYOUTS), defaults["layout"])
    texture = _draw_choice(ctx, overrides, "texture", _TEXTURES, defaults["texture"])
    edge_profile = _draw_choice(
        ctx, overrides, "edge_profile", _EDGE_PROFILES, defaults["edge_profile"]
    )
    color_reuse = _draw_choice(
        ctx, overrides, "color_reuse", (False, True), defaults["color_reuse"]
    )
    rng = ctx.draw_rng(f"geometry|{difficulty or 'medium'}")

    height, width, relation_count = _LAYOUTS[layout]
    has_multi = texture in ("multi_pair", "all_controls")
    has_blocker = texture in ("blocker", "all_controls")
    has_counts = texture in ("count_controls", "all_controls")
    rows_needed = relation_count - (1 if has_multi else 0) + (2 if has_counts else 0)
    if rows_needed > height:
        raise ValueError(
            f"layout={layout!r} cannot fit texture={texture!r}: "
            f"needs {rows_needed} rows in height {height}"
        )

    selected_rows = rng.sample(range(height), rows_needed)
    relation_rows, blocker_index, control_rows = _relation_rows(
        texture, relation_count, selected_rows
    )
    roles = _edge_roles(relation_count, edge_profile)
    colors = _relation_colors(rng, relation_count, color_reuse, has_multi)
    extra_color_count = (1 if has_blocker else 0) + (3 if has_counts else 0)
    controls = _control_colors(rng, colors, extra_color_count)

    grid = full_grid(height, width, 0)
    control_cursor = 0
    for index, (row, color, role) in enumerate(zip(relation_rows, colors, roles)):
        left, right = _span_columns(rng, width, index, role, has_multi)
        grid[row][left] = color
        grid[row][right] = color
        if blocker_index == index:
            blocker = controls[control_cursor]
            control_cursor += 1
            grid[row][rng.randint(left + 1, right - 1)] = blocker

    if has_counts:
        _place_count_controls(
            grid, control_rows, controls[control_cursor:control_cursor + 3], rng
        )

    observed = observe_overrides(grid)
    expected = {
        "layout": layout,
        "texture": texture,
        "edge_profile": edge_profile,
        "color_reuse": color_reuse,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed grid failed self_check: {errors}")
    return grid


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid must be rectangular and non-empty"]
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        errors.append("grid colors must be integers in 0..9")
    return grid, errors


def _row_color_positions(row: list[int]) -> dict[int, list[int]]:
    positions: dict[int, list[int]] = {}
    for column, color in enumerate(row):
        if color != 0:
            positions.setdefault(color, []).append(column)
    return positions


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    info: dict[str, Any] = {
        "errors": list(errors),
        "grid_h": 0,
        "grid_w": 0,
        "active_spans": [],
        "row_kinds": {},
    }
    if normalized is None or errors:
        return info

    height, width = len(normalized), len(normalized[0])
    info["grid_h"], info["grid_w"] = height, width
    control_colors: list[int] = []

    for row_index, row in enumerate(normalized):
        by_color = _row_color_positions(row)
        if not by_color:
            continue
        pairs = [(color, columns) for color, columns in by_color.items() if len(columns) == 2]
        triples = [(color, columns) for color, columns in by_color.items() if len(columns) == 3]
        singles = [(color, columns) for color, columns in by_color.items() if len(columns) == 1]
        other = [(color, columns) for color, columns in by_color.items()
                 if len(columns) not in (1, 2, 3)]
        if other:
            info["errors"].append(
                f"row {row_index} has unsupported color multiplicity "
                f"{[(color, len(columns)) for color, columns in other]}"
            )
            continue
        bad_gaps = [color for color, columns in pairs if columns[1] - columns[0] < 2]
        if bad_gaps:
            info["errors"].append(
                f"row {row_index} has no-op adjacent pair color(s) {bad_gaps}"
            )
            continue

        kind: str | None = None
        if len(pairs) == 1 and not triples and not singles:
            kind = "clean_pair"
        elif len(pairs) == 2 and not triples and not singles:
            spans = sorted((columns[0], columns[1], color) for color, columns in pairs)
            if spans[0][1] >= spans[1][0]:
                info["errors"].append(f"row {row_index} has overlapping pair spans")
                continue
            kind = "multi_pair"
        elif len(pairs) == 1 and not triples and len(singles) == 1:
            pair_color, columns = pairs[0]
            singleton_color, singleton_columns = singles[0]
            singleton = singleton_columns[0]
            if not columns[0] < singleton < columns[1]:
                info["errors"].append(
                    f"row {row_index} blocker color {singleton_color} is outside pair span"
                )
                continue
            if singleton_color == pair_color:
                info["errors"].append(f"row {row_index} blocker must use another color")
                continue
            kind = "blocker"
            control_colors.append(singleton_color)
        elif not pairs and len(triples) == 1 and not singles:
            kind = "triple_control"
            control_colors.append(triples[0][0])
        elif not pairs and not triples and len(singles) == 2:
            kind = "singleton_controls"
            control_colors.extend(color for color, _columns in singles)
        else:
            info["errors"].append(
                f"row {row_index} has unrecognized row-local multiplicities "
                f"{sorted((color, len(columns)) for color, columns in by_color.items())}"
            )
            continue

        info["row_kinds"][row_index] = kind
        for color, columns in pairs:
            info["active_spans"].append({
                "row": row_index,
                "color": color,
                "left": columns[0],
                "right": columns[1],
            })

    spans = info["active_spans"]
    relation_count = len(spans)
    layout = next(
        (name for name, signature in _LAYOUTS.items()
         if signature == (height, width, relation_count)),
        None,
    )
    if layout is None:
        info["errors"].append(
            f"unsupported joint layout {(height, width, relation_count)!r}"
        )
    info["layout"] = layout

    kinds = list(info["row_kinds"].values())
    counts = {name: kinds.count(name) for name in (
        "multi_pair", "blocker", "triple_control", "singleton_controls"
    )}
    if all(value == 0 for value in counts.values()):
        texture = "clean"
    elif counts == {
        "multi_pair": 1, "blocker": 0, "triple_control": 0, "singleton_controls": 0
    }:
        texture = "multi_pair"
    elif counts == {
        "multi_pair": 0, "blocker": 1, "triple_control": 0, "singleton_controls": 0
    }:
        texture = "blocker"
    elif counts == {
        "multi_pair": 0, "blocker": 0, "triple_control": 1, "singleton_controls": 1
    }:
        texture = "count_controls"
    elif counts == {
        "multi_pair": 1, "blocker": 1, "triple_control": 1, "singleton_controls": 1
    }:
        texture = "all_controls"
    else:
        texture = None
        info["errors"].append(f"unsupported control combination {counts}")
    info["texture"] = texture

    touches_left = any(span["left"] == 0 for span in spans)
    touches_right = any(span["right"] == width - 1 for span in spans)
    if spans and not touches_left and not touches_right:
        edge_profile = "interior"
    elif touches_left and touches_right:
        edge_profile = "edge_mix"
    else:
        # The public examples include clean one-sided edge support.  It is a
        # lawful canonical input but not an override value generated here.
        edge_profile = "one_sided_canonical"
    info["edge_profile"] = edge_profile

    per_color: dict[int, int] = {}
    for span in spans:
        per_color[span["color"]] = per_color.get(span["color"], 0) + 1
    repeats = sorted(per_color.values())
    if repeats and all(count == 1 for count in repeats):
        color_reuse: bool | None = False
    elif repeats and repeats.count(2) == 1 and all(count in (1, 2) for count in repeats):
        color_reuse = True
    else:
        color_reuse = None
        info["errors"].append(f"unsupported qualifying-color reuse counts {repeats}")
    info["color_reuse"] = color_reuse

    qualifying_colors = set(per_color)
    if len(control_colors) != len(set(control_colors)):
        info["errors"].append("control colors must be globally distinct")
    if qualifying_colors & set(control_colors):
        info["errors"].append("control colors must differ from qualifying colors")

    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if info["edge_profile"] not in _EDGE_PROFILES:
        raise ValueError("one-sided canonical edge profile is not an override value")
    return {name: info[name] for name in AXES}


def self_check(grid: Any, *, difficulty: Any = None,
               meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    if info["layout"] not in _LAYOUTS:
        errors.append("grid does not realize a declared layout")
    if info["texture"] not in _TEXTURES:
        errors.append("grid does not realize a declared texture")
    if info["color_reuse"] not in (False, True):
        errors.append("grid does not realize a declared color_reuse value")
    if info["edge_profile"] == "one_sided_canonical":
        if not (
            info["layout"] in ("canonical3", "canonical4")
            and info["texture"] == "clean"
            and info["color_reuse"] is False
        ):
            errors.append("one-sided edge support is reserved for clean canonical inputs")
    elif info["edge_profile"] not in _EDGE_PROFILES:
        errors.append("grid does not realize a declared edge_profile")

    output = rule_mirror(grid)
    if output == grid:
        errors.append("rule application must visibly change at least one cell")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        axis_requests = (
            {axis: value for axis, value in requested.items() if axis in AXES}
            if isinstance(requested, dict)
            else {}
        )
        if axis_requests:
            try:
                observed = observe_overrides(grid)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                for axis, value in axis_requests.items():
                    if observed.get(axis) != value:
                        errors.append(
                            f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                        )
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; canonical Racket remains authoritative."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) != 2:
                continue
            for column in range(columns[0], columns[1] + 1):
                out[row_index][column] = color
    return out


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the exact public joint profiles with clean, distinct pair rows."""
    info = _analyze(grid)
    if info["errors"]:
        return list(info["errors"])
    reasons: list[str] = []
    if info["layout"] not in ("canonical3", "canonical4"):
        reasons.append(f"layout {info['layout']!r} is not a public profile")
    if info["texture"] != "clean":
        reasons.append(f"texture {info['texture']!r} is not clean")
    if info["color_reuse"] is not False:
        reasons.append("public anchors use distinct qualifying colors")
    return reasons


def semantic_signature(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = rule_mirror(grid)
    return {
        "layout": info["layout"],
        "texture": info["texture"],
        "edge_profile": info["edge_profile"],
        "color_reuse": info["color_reuse"],
        "qualifying_relations": len(info["active_spans"]),
        "changed_cells": sum(
            before != after
            for in_row, out_row in zip(grid, output)
            for before, after in zip(in_row, out_row)
        ),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _texture_is(*names: str) -> Callable[[Any], bool]:
    return lambda grid: _analyze(grid).get("texture") in names


def _has_left(grid: Any) -> bool:
    return any(span["left"] == 0 for span in _analyze(grid)["active_spans"])


def _has_right(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["right"] == info["grid_w"] - 1 for span in info["active_spans"])


def _has_full_width(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["left"] == 0 and span["right"] == info["grid_w"] - 1
               for span in info["active_spans"])


def _has_interior(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["left"] > 0 and span["right"] < info["grid_w"] - 1
               for span in info["active_spans"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "canonical_anchor": lambda grid: not strict_canonical_like(grid),
    "multi_pair_row": _texture_is("multi_pair", "all_controls"),
    "blocker_overwritten": _texture_is("blocker", "all_controls"),
    "triple_erased": _texture_is("count_controls", "all_controls"),
    "loose_singletons_erased": _texture_is("count_controls", "all_controls"),
    "row_local_color_reuse": lambda grid: _analyze(grid).get("color_reuse") is True,
    "left_edge_span": _has_left,
    "right_edge_span": _has_right,
    "full_width_span": _has_full_width,
    "interior_span": _has_interior,
}

BRANCH_WITNESSES = {
    "canonical_anchor",
    "left_edge_span",
    "right_edge_span",
    "full_width_span",
    "interior_span",
}


def _row_total_exactly_two(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        entries = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(entries) == 2 and entries[0][1] == entries[1][1]:
            left, color = entries[0]
            right = entries[1][0]
            for column in range(left, right + 1):
                out[row_index][column] = color
    return out


def _empty_gap_only(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) == 2 and all(row[column] == 0
                                         for column in range(columns[0] + 1, columns[1])):
                for column in range(columns[0], columns[1] + 1):
                    out[row_index][column] = color
    return out


def _at_least_two_outermost(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) >= 2:
                for column in range(min(columns), max(columns) + 1):
                    out[row_index][column] = color
    return out


def _preserve_nonqualifying(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) == 2:
                for column in range(columns[0], columns[1] + 1):
                    out[row_index][column] = color
    return out


def _global_exactly_two(grid: list[list[int]]) -> list[list[int]]:
    totals: dict[int, int] = {}
    for row in grid:
        for color in row:
            if color != 0:
                totals[color] = totals.get(color, 0) + 1
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) == 2 and totals[color] == 2:
                for column in range(columns[0], columns[1] + 1):
                    out[row_index][column] = color
    return out


def _first_pair_per_row(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        pairs = sorted(
            (columns[0], columns[1], color)
            for color, columns in _row_color_positions(row).items()
            if len(columns) == 2
        )
        if pairs:
            left, right, color = pairs[0]
            for column in range(left, right + 1):
                out[row_index][column] = color
    return out


def _distinct_colors_only(grid: list[list[int]]) -> list[list[int]]:
    appearances: dict[int, int] = {}
    for row in grid:
        for color, columns in _row_color_positions(row).items():
            if len(columns) == 2:
                appearances[color] = appearances.get(color, 0) + 1
    out = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for color, columns in _row_color_positions(row).items():
            if len(columns) == 2 and appearances[color] == 1:
                for column in range(columns[0], columns[1] + 1):
                    out[row_index][column] = color
    return out


_COMPETING_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "row_total_exactly_two": _row_total_exactly_two,
    "empty_gap_only": _empty_gap_only,
    "at_least_two_outermost": _at_least_two_outermost,
    "preserve_nonqualifying": _preserve_nonqualifying,
    "global_exactly_two": _global_exactly_two,
    "first_pair_per_row": _first_pair_per_row,
    "distinct_colors_only": _distinct_colors_only,
}

SEMANTIC_RIVALS = _COMPETING_RULES
WITNESS_RIVALS = {
    "multi_pair_row": ["row_total_exactly_two", "first_pair_per_row"],
    "blocker_overwritten": ["empty_gap_only", "row_total_exactly_two"],
    "triple_erased": ["at_least_two_outermost", "preserve_nonqualifying"],
    "loose_singletons_erased": ["preserve_nonqualifying"],
    "row_local_color_reuse": ["global_exactly_two", "distinct_colors_only"],
}
LESSON_COMPETITORS = _COMPETING_RULES
CANONICAL_SHORTCUTS = _COMPETING_RULES


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a canonical-fitting competitor survives demos."""
    reasons: list[str] = []
    pairs = [("demo", index, pair) for index, pair in enumerate(demos)]
    pairs.append(("query", 0, query))
    for kind, index, pair in pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{kind} {index}: pair must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.extend(f"{kind} {index}: {error}" for error in errors)
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{kind} {index}: output does not match exact-pair row fill")
    if reasons:
        return reasons

    for name, candidate in _COMPETING_RULES.items():
        if all(candidate(pair["input"]) == pair["output"] for pair in demos):
            if candidate(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demos: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local structural impostors that ``self_check`` must reject."""
    overlapping = full_grid(6, 12, 0)
    overlapping[0][1] = overlapping[0][8] = 2
    overlapping[0][4] = overlapping[0][10] = 3
    overlapping[2][1] = overlapping[2][4] = 4

    adjacent_noop = full_grid(6, 12, 0)
    adjacent_noop[1][2] = adjacent_noop[1][3] = 2
    adjacent_noop[3][1] = adjacent_noop[3][5] = 3
    adjacent_noop[5][4] = adjacent_noop[5][9] = 4

    blocker_outside = full_grid(6, 12, 0)
    blocker_outside[1][2] = blocker_outside[1][8] = 2
    blocker_outside[1][10] = 5
    blocker_outside[3][1] = blocker_outside[3][6] = 3
    blocker_outside[5][2] = blocker_outside[5][7] = 4

    duplicated_control_color = full_grid(6, 12, 0)
    duplicated_control_color[0][1] = duplicated_control_color[0][4] = 2
    duplicated_control_color[1][2] = duplicated_control_color[1][8] = 3
    duplicated_control_color[2][1] = duplicated_control_color[2][7] = 4
    for column in (0, 5, 10):
        duplicated_control_color[3][column] = 7
    duplicated_control_color[4][2] = 7
    duplicated_control_color[4][9] = 8

    unsupported_layout = full_grid(7, 12, 0)
    unsupported_layout[1][1] = unsupported_layout[1][5] = 2
    unsupported_layout[3][2] = unsupported_layout[3][8] = 3
    unsupported_layout[5][4] = unsupported_layout[5][10] = 4

    return [
        ("overlapping_multi_pair_spans", overlapping),
        ("adjacent_noop_pair", adjacent_noop),
        ("blocker_outside_span", blocker_outside),
        ("control_color_reused", duplicated_control_color),
        ("unsupported_joint_layout", unsupported_layout),
    ]
