"""Generator for ``caa7a75c44ad`` (column span fill).

The canonical rule is local to each column.  When a column contains exactly
 two cells of one non-zero color and every cell strictly between them is zero,
paint the inclusive vertical span with that color.  Other columns are left
unchanged.

Ordinary lessons deliberately include both positive spans and two lawful
negative controls: differently-colored endpoints and a same-colored pair with
a non-zero blocker.  A four-sample schedule puts both controls in every
three-demo lesson while retaining two canonical-profile anchors.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "caa7a75c44ad"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6877fd432f60"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "A 0-background grid contains 2..5 independent vertical endpoint pairs. "
    "A fillable pair is exactly two equal non-zero cells in one column with "
    "one or more zeros between them; the output fills that inclusive span in "
    "the endpoint color. Optional negative-control columns contain either "
    "different endpoint colors or a non-zero blocker and therefore remain "
    "unchanged."
)

INVARIANTS = [
    "background is color 0",
    "every normal draw contains at least two fillable same-color vertical spans",
    "every fillable span has at least one zero cell strictly between its endpoints",
    "at most one negative-control column is present, and it is not fillable",
    "the canonical Racket rule, not this module's Python mirror, is output authority",
]

_GAP_PROFILES = ("short", "mixed", "long")
_EDGE_PROFILES = ("interior", "top", "bottom", "both")
_COLOR_MODES = ("distinct", "reused")
_DISTRACTOR_MODES = ("none", "mixed_endpoints", "blocked_span")
_CANONICAL_PROFILES = ((7, 10), (8, 9), (8, 11), (9, 8))

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/band draw", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "scheduled/band draw", "valid": "8..11"},
    "span_count": {"type": "int", "default": "scheduled/band draw", "valid": "2..5"},
    "gap_profile": {
        "type": "enum",
        "default": "scheduled",
        "valid": "short|mixed|long",
    },
    "edge_profile": {
        "type": "enum",
        "default": "scheduled",
        "valid": "interior|top|bottom|both",
    },
    "color_mode": {
        "type": "enum",
        "default": "scheduled",
        "valid": "distinct|reused",
    },
    "distractor_mode": {
        "type": "enum",
        "default": "scheduled",
        "valid": "none|mixed_endpoints|blocked_span",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "span_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("gap_profile", "edge_profile", "color_mode", "distractor_mode"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _band_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (7, 8), (8, 9), (2, 3)
    if difficulty == "hard":
        return (10, 12), (10, 11), (4, 5)
    return (8, 10), (9, 10), (3, 4)


def _draw_int(ctx, overrides: dict[str, Any], name: str, default: tuple[int, int],
              valid: tuple[int, int]) -> int:
    """Use the full declared domain for an exact override on every band."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid[0], valid[1])
    return ctx.draw_int(name, default[0], default[1])


def _draw_choice(ctx, overrides: dict[str, Any], name: str,
                 options: tuple[str, ...], defaults: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, defaults)


def _scheduled_defaults(sample_index: int, rng) -> dict[str, Any]:
    """Four consecutive samples: anchor, blocker, mixed endpoints, anchor."""
    slot = sample_index % 4
    if slot in (0, 3):
        h, w = _CANONICAL_PROFILES[(rng.randrange(len(_CANONICAL_PROFILES)) + slot) % 4]
        return {
            "grid_h": h,
            "grid_w": w,
            "span_count": 3,
            "gap_profile": "mixed" if slot == 0 else "long",
            "edge_profile": "both",
            "color_mode": "distinct",
            "distractor_mode": "none",
        }
    if slot == 1:
        return {
            "grid_h": 8 + rng.randrange(3),
            "grid_w": 9 + rng.randrange(2),
            "span_count": 3 + rng.randrange(2),
            "gap_profile": "mixed",
            "edge_profile": "top",
            "color_mode": "reused",
            "distractor_mode": "blocked_span",
        }
    return {
        "grid_h": 8 + rng.randrange(3),
        "grid_w": 9 + rng.randrange(2),
        "span_count": 3 + rng.randrange(2),
        "gap_profile": "long",
        "edge_profile": "bottom",
        "color_mode": "distinct",
        "distractor_mode": "mixed_endpoints",
    }


def _edge_roles(span_count: int, edge_profile: str) -> list[str]:
    roles = ["interior"] * span_count
    if edge_profile == "top":
        roles[0] = "top"
    elif edge_profile == "bottom":
        roles[0] = "bottom"
    elif edge_profile == "both":
        roles[0] = "top"
        roles[1] = "bottom"
    return roles


def _gap_categories(span_count: int, gap_profile: str) -> list[str]:
    if gap_profile == "short":
        return ["short"] * span_count
    if gap_profile == "long":
        return ["long"] * span_count
    return ["short", "long"] + ["short" if i % 2 == 0 else "long"
                                for i in range(span_count - 2)]


def _choose_gap(rng, h: int, role: str, category: str) -> int:
    max_gap = h - 3 if role == "interior" else h - 2
    lo, hi = (2, min(3, max_gap)) if category == "short" else (4, max_gap)
    if hi < lo:
        raise ValueError(
            f"cannot place {category} gap with edge role {role} in height {h}"
        )
    return rng.randint(lo, hi)


def _choose_rows(rng, h: int, role: str, gap: int) -> tuple[int, int]:
    if role == "top":
        return 0, gap
    if role == "bottom":
        return h - gap - 1, h - 1
    r1 = rng.randint(1, h - gap - 2)
    return r1, r1 + gap


def _active_colors(rng, span_count: int, mode: str) -> list[int]:
    if mode == "reused":
        return [rng.choice(range(1, 10))] * span_count
    return rng.sample(range(1, 10), span_count)


def _fresh_color(rng, excluded: set[int]) -> int:
    choices = [color for color in range(1, 10) if color not in excluded]
    if not choices:
        raise ValueError("no color remains for distractor construction")
    return rng.choice(choices)


def _place_distractor(grid: list[list[int]], col: int, mode: str, rng,
                      used_colors: set[int]) -> None:
    h = len(grid)
    if mode == "none":
        return
    r1 = rng.randint(0, 1)
    r2 = rng.randint(h - 2, h - 1)
    if r2 - r1 < 2:
        r1, r2 = 0, h - 1
    if mode == "mixed_endpoints":
        top = _fresh_color(rng, used_colors)
        bottom = _fresh_color(rng, used_colors | {top})
        grid[r1][col] = top
        grid[r2][col] = bottom
        return
    endpoint = _fresh_color(rng, used_colors)
    blocker = _fresh_color(rng, used_colors | {endpoint})
    mid = rng.randint(r1 + 1, r2 - 1)
    grid[r1][col] = endpoint
    grid[mid][col] = blocker
    grid[r2][col] = endpoint


def _column_entries(grid: list[list[int]], col: int) -> list[tuple[int, int]]:
    return [(row, grid[row][col]) for row in range(len(grid)) if grid[row][col] != 0]


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "errors": [],
        "active_spans": [],
        "distractor_columns": [],
        "grid_h": 0,
        "grid_w": 0,
    }
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular and non-empty")
        return info
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        info["errors"].append("grid colors must be integers in 0..9")
        return info

    h, w = len(grid), width
    info["grid_h"], info["grid_w"] = h, w
    for col in range(w):
        entries = _column_entries(grid, col)
        if not entries:
            continue
        active = None
        if len(entries) == 2:
            (r1, color1), (r2, color2) = entries
            if color1 == color2 and r2 - r1 >= 2 and all(
                grid[row][col] == 0 for row in range(r1 + 1, r2)
            ):
                active = {"col": col, "r1": r1, "r2": r2,
                          "gap": r2 - r1, "color": color1}
        if active is not None:
            info["active_spans"].append(active)
        else:
            info["distractor_columns"].append({"col": col, "entries": entries})

    spans = info["active_spans"]
    gaps = [span["gap"] for span in spans]
    short = any(gap <= 3 for gap in gaps)
    long = any(gap >= 4 for gap in gaps)
    info["gap_profile"] = "mixed" if short and long else ("short" if short else "long")
    top = any(span["r1"] == 0 for span in spans)
    bottom = any(span["r2"] == h - 1 for span in spans)
    info["edge_profile"] = (
        "both" if top and bottom else "top" if top else "bottom" if bottom else "interior"
    )
    colors = [span["color"] for span in spans]
    info["color_mode"] = "distinct" if len(colors) == len(set(colors)) else "reused"
    info["span_count"] = len(spans)

    distractors = info["distractor_columns"]
    mode = "none"
    if len(distractors) == 1:
        entries = distractors[0]["entries"]
        if len(entries) == 2 and entries[0][1] != entries[1][1] and entries[1][0] - entries[0][0] >= 2:
            mode = "mixed_endpoints"
        elif len(entries) == 3:
            (r1, c1), (_, middle), (r2, c2) = entries
            if c1 == c2 and middle != c1 and r2 - r1 >= 2:
                mode = "blocked_span"
        if mode == "none":
            info["errors"].append("unrecognized negative-control column")
    elif len(distractors) > 1:
        info["errors"].append("more than one negative-control column")
    info["distractor_mode"] = mode
    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {name: info[name] for name in AXES}


def self_check(grid: Any, *, difficulty: Any = None,
               meta: dict[str, Any] | None = None) -> list[str]:
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    h, w = info["grid_h"], info["grid_w"]
    if not 7 <= h <= 12:
        errors.append(f"height {h} outside 7..12")
    if not 8 <= w <= 11:
        errors.append(f"width {w} outside 8..11")
    if not 2 <= info["span_count"] <= 5:
        errors.append(f"fillable span count {info['span_count']} outside 2..5")
    if info["distractor_mode"] not in _DISTRACTOR_MODES:
        errors.append("invalid distractor mode")
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; the Racket rule remains authoritative."""
    out = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for col in range(len(grid[0])):
        for color in colors:
            rows = [row for row in range(len(grid)) if grid[row][col] == color]
            if len(rows) != 2:
                continue
            r1, r2 = rows
            if all(grid[row][col] == 0 for row in range(r1 + 1, r2)):
                for row in range(r1, r2 + 1):
                    out[row][col] = color
    return out


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analyze(grid)
    reasons = list(info["errors"])
    if reasons:
        return reasons
    palette_size = len({value for row in grid for value in row})
    if (info["grid_h"], info["grid_w"]) not in _CANONICAL_PROFILES:
        reasons.append("dimensions are outside the four canonical profiles")
    if info["span_count"] != 3:
        reasons.append("canonical scenes contain exactly three fillable spans")
    if info["distractor_mode"] != "none":
        reasons.append("canonical scenes contain no negative-control column")
    if info["color_mode"] != "distinct":
        reasons.append("canonical span colors are pairwise distinct")
    if info["edge_profile"] != "both":
        reasons.append("canonical scenes witness both top and bottom boundary contact")
    if palette_size != 4:
        reasons.append("canonical palette is background plus three span colors")
    return reasons


def _has_top(grid: Any) -> bool:
    return any(span["r1"] == 0 for span in _analyze(grid)["active_spans"])


def _has_bottom(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["r2"] == info["grid_h"] - 1 for span in info["active_spans"])


def _has_interior(grid: Any) -> bool:
    info = _analyze(grid)
    return any(span["r1"] > 0 and span["r2"] < info["grid_h"] - 1
               for span in info["active_spans"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "top_edge_span": _has_top,
    "bottom_edge_span": _has_bottom,
    "interior_span": _has_interior,
    "short_gap": lambda grid: any(span["gap"] <= 3 for span in _analyze(grid)["active_spans"]),
    "long_gap": lambda grid: any(span["gap"] >= 4 for span in _analyze(grid)["active_spans"]),
    "reused_active_color": lambda grid: _analyze(grid)["color_mode"] == "reused",
    "mixed_endpoint_distractor": lambda grid: _analyze(grid)["distractor_mode"] == "mixed_endpoints",
    "blocked_span_distractor": lambda grid: _analyze(grid)["distractor_mode"] == "blocked_span",
}


def _fill_any_two_nonzeros(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for col in range(len(grid[0])):
        entries = _column_entries(grid, col)
        if len(entries) == 2:
            r1, color = entries[0]
            r2 = entries[1][0]
            for row in range(r1, r2 + 1):
                out[row][col] = color
    return out


def _fill_same_color_ignoring_blockers(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for col in range(len(grid[0])):
        by_color: dict[int, list[int]] = {}
        for row, color in _column_entries(grid, col):
            by_color.setdefault(color, []).append(row)
        for color, rows in by_color.items():
            if len(rows) == 2:
                for row in range(rows[0], rows[1] + 1):
                    if out[row][col] == 0:
                        out[row][col] = color
    return out


def _edge_only(grid: list[list[int]], edge: str) -> list[list[int]]:
    out = deepcopy(grid)
    info = _analyze(grid)
    for span in info["active_spans"]:
        eligible = span["r1"] == 0 if edge == "top" else span["r2"] == info["grid_h"] - 1
        if eligible:
            for row in range(span["r1"], span["r2"] + 1):
                out[row][span["col"]] = span["color"]
    return out


def _distinct_colors_only(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    if info["color_mode"] != "distinct":
        return deepcopy(grid)
    return rule_mirror(grid)


_COMPETING_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_between_any_two_nonzeros": _fill_any_two_nonzeros,
    "ignore_nonzero_blockers": _fill_same_color_ignoring_blockers,
    "top_anchored_only": lambda grid: _edge_only(grid, "top"),
    "bottom_anchored_only": lambda grid: _edge_only(grid, "bottom"),
    "distinct_span_colors_only": _distinct_colors_only,
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a concrete shortcut survives and changes the query."""
    reasons: list[str] = []
    for name, candidate in _COMPETING_RULES.items():
        if all(candidate(pair["input"]) == pair["output"] for pair in demos):
            if candidate(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demos: {name}")
    return reasons


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
    rng = ctx.draw_rng(f"layout|{difficulty or 'medium'}")

    if not overrides:
        scheduled = _scheduled_defaults(sample_index, rng)
        h = ctx.draw_int("grid_h", scheduled["grid_h"], scheduled["grid_h"])
        w = ctx.draw_int("grid_w", scheduled["grid_w"], scheduled["grid_w"])
        span_count = ctx.draw_int("span_count", scheduled["span_count"], scheduled["span_count"])
        gap_profile = ctx.draw_choice("gap_profile", [scheduled["gap_profile"]])
        edge_profile = ctx.draw_choice("edge_profile", [scheduled["edge_profile"]])
        color_mode = ctx.draw_choice("color_mode", [scheduled["color_mode"]])
        distractor_mode = ctx.draw_choice(
            "distractor_mode", [scheduled["distractor_mode"]]
        )
    else:
        hrange, wrange, srange = _band_ranges(difficulty)
        h = _draw_int(ctx, overrides, "grid_h", hrange, (7, 12))
        w = _draw_int(ctx, overrides, "grid_w", wrange, (8, 11))
        span_count = _draw_int(ctx, overrides, "span_count", srange, (2, 5))
        gap_profile = _draw_choice(
            ctx, overrides, "gap_profile", _GAP_PROFILES,
            ("short", "mixed") if difficulty == "easy" else
            ("mixed", "long") if difficulty == "hard" else _GAP_PROFILES,
        )
        edge_profile = _draw_choice(
            ctx, overrides, "edge_profile", _EDGE_PROFILES, _EDGE_PROFILES,
        )
        color_mode = _draw_choice(
            ctx, overrides, "color_mode", _COLOR_MODES, _COLOR_MODES,
        )
        distractor_mode = _draw_choice(
            ctx, overrides, "distractor_mode", _DISTRACTOR_MODES,
            _DISTRACTOR_MODES,
        )

    distractor_count = 0 if distractor_mode == "none" else 1
    if span_count + distractor_count > w:
        raise ValueError(
            f"span_count={span_count} plus distractor does not fit grid_w={w}"
        )

    grid = full_grid(h, w, 0)
    columns = rng.sample(range(w), span_count + distractor_count)
    active_columns = columns[:span_count]
    colors = _active_colors(rng, span_count, color_mode)
    roles = _edge_roles(span_count, edge_profile)
    categories = _gap_categories(span_count, gap_profile)
    for col, color, role, category in zip(active_columns, colors, roles, categories):
        gap = _choose_gap(rng, h, role, category)
        r1, r2 = _choose_rows(rng, h, role, gap)
        grid[r1][col] = color
        grid[r2][col] = color

    if distractor_count:
        _place_distractor(
            grid,
            columns[-1],
            distractor_mode,
            rng,
            set(colors),
        )

    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "span_count": span_count,
        "gap_profile": gap_profile,
        "edge_profile": edge_profile,
        "color_mode": color_mode,
        "distractor_mode": distractor_mode,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed grid failed self_check: {errors}")
    return grid
