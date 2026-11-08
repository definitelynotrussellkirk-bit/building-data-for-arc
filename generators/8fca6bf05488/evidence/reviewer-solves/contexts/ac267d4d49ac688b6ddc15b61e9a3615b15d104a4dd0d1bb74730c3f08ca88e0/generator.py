"""Generator for ARC task 8fca6bf05488 (cast vertical rays downward).

Every nonzero input cell is a ray source.  The selected Racket rule scans the
input in row-major order and paints each source from its row through the bottom
edge.  When two sources share a column, the lower source is encountered later
and overwrites the lower suffix.

The four-example curriculum cycles through:

* ``canonical``: source-like distinct columns, unique colors, no bottom source;
* ``stacked``: two differently colored sources share one column;
* ``bottom_boundary``: one source is already on the bottom edge;
* ``repeated_color``: two distinct-column sources reuse one color.

Together these profiles distinguish the intended rule from canonical-fitting
shortcuts that keep only the top source per column, ignore repeated colors, or
drop zero-length bottom-edge rays.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8fca6bf05488"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "fe26cc0d2dfe"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Every colored source paints down to the bottom edge. Scheduled stacked, "
    "bottom-boundary, and repeated-color profiles teach overwrite and boundary "
    "behavior that the canonical distinct-column examples do not expose."
)

INVARIANTS = [
    "background is 0 and ordinary colors are 1..9",
    "ordinary lessons contain 2..4 visible ray sources on at least two rows",
    "canonical/repeated/bottom profiles use distinct columns",
    "a stacked lesson has exactly one two-source column and distinct source colors",
]

SCHEDULE_PROFILES = (
    "canonical",
    "stacked",
    "bottom_boundary",
    "repeated_color",
)
HELPFUL_TEXTURES = SCHEDULE_PROFILES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

PALETTES = {
    "low": (1, 2, 3, 4),
    "high": (6, 7, 8, 9),
}
_CANONICAL_ANCHORS = ((6, 10), (7, 8), (9, 7))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile/difficulty-aware with canonical anchors",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "profile/difficulty-aware with canonical anchors",
        "valid": "7..12",
    },
    "emitters": {
        "type": "int",
        "default": "2 canonical; 2/3/4 by difficulty otherwise",
        "valid": "2..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform low|high",
        "valid": "low|high",
    },
    "profile": {
        "type": "str",
        "default": "four-example deterministic schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}

# Every Cartesian product of the advertised domains is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle all rule branches in every consecutive four-example window."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    values = dict(overrides)
    texture = values.pop("texture", None)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        if "profile" in values and values["profile"] != texture:
            raise ValueError("texture and profile overrides disagree")
        values["profile"] = texture

    unknown = sorted(set(values) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "emitters"):
        value = values.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    for name in ("palette_kind", "profile"):
        value = values.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
    return values


def _difficulty_bounds(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (7, 9)
    if difficulty in (None, "medium"):
        return (7, 10), (8, 11)
    if difficulty == "hard":
        return (9, 12), (10, 12)
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_profile(ctx, values: dict[str, Any], seed: int, sample_index: int, difficulty) -> str:
    if "profile" in values:
        return ctx.draw_choice("profile", SCHEDULE_PROFILES)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return ctx.draw_choice("profile", (scheduled,))


def _draw_dimensions(ctx, values: dict[str, Any], profile: str, difficulty) -> tuple[int, int]:
    if "grid_h" not in values and "grid_w" not in values and profile == "canonical":
        anchor_rng = ctx.draw_rng("canonical_anchor")
        h, w = _CANONICAL_ANCHORS[anchor_rng.randrange(len(_CANONICAL_ANCHORS))]
        return ctx.draw_int("grid_h", h, h), ctx.draw_int("grid_w", w, w)

    (h_lo, h_hi), (w_lo, w_hi) = _difficulty_bounds(difficulty)
    h = ctx.draw_int("grid_h", 6, 12) if "grid_h" in values else ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", 7, 12) if "grid_w" in values else ctx.draw_int("grid_w", w_lo, w_hi)
    return h, w


def _draw_emitters(ctx, values: dict[str, Any], profile: str, difficulty) -> int:
    if "emitters" in values:
        return ctx.draw_int("emitters", 2, 4)
    if profile == "canonical":
        return ctx.draw_int("emitters", 2, 2)
    target = {"easy": 2, "hard": 4}.get(difficulty, 3)
    return ctx.draw_int("emitters", target, target)


def _varied_rows(rng, allowed_rows: tuple[int, ...], count: int) -> list[int]:
    first, second = rng.sample(list(allowed_rows), 2)
    rows = [first, second]
    rows.extend(rng.choice(allowed_rows) for _ in range(count - 2))
    rng.shuffle(rows)
    return rows


def _build_scene(
    h: int,
    w: int,
    emitters: int,
    palette_kind: str,
    profile: str,
    rng,
) -> list[list[int]]:
    palette = PALETTES[palette_kind]
    grid = full_grid(h, w, 0)

    if profile == "stacked":
        stack_column = rng.randrange(w)
        upper, lower = sorted(rng.sample(range(h - 1), 2))
        positions = [(upper, stack_column), (lower, stack_column)]
        extra_columns = rng.sample([c for c in range(w) if c != stack_column], emitters - 2)
        positions.extend((rng.randrange(h - 1), c) for c in extra_columns)
        colors = rng.sample(list(palette), emitters)

    elif profile == "bottom_boundary":
        columns = rng.sample(range(w), emitters)
        positions = [(h - 1, columns[0])]
        rows = _varied_rows(rng, tuple(range(h - 1)), emitters - 1) if emitters > 2 else [rng.randrange(h - 1)]
        positions.extend(zip(rows, columns[1:]))
        colors = rng.sample(list(palette), emitters)

    else:
        columns = rng.sample(range(w), emitters)
        rows = _varied_rows(rng, tuple(range(h - 1)), emitters)
        positions = list(zip(rows, columns))
        if profile == "canonical":
            colors = rng.sample(list(palette), emitters)
        elif profile == "repeated_color":
            repeated = rng.choice(palette)
            colors = [repeated, repeated]
            colors.extend(rng.sample([c for c in palette if c != repeated], emitters - 2))
            rng.shuffle(colors)
        else:  # Defensive guard; _draw_profile validates ordinary calls.
            raise ValueError(f"unknown profile {profile!r}")

    for (row, column), color in zip(positions, colors):
        if grid[row][column] != 0:
            raise RuntimeError("constructive source placement collided")
        grid[row][column] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _normalize_overrides(overrides)
    _difficulty_bounds(difficulty)  # validate even when both dimensions are overridden
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    profile = _draw_profile(ctx, values, seed, sample_index, difficulty)
    h, w = _draw_dimensions(ctx, values, profile, difficulty)
    emitters = _draw_emitters(ctx, values, profile, difficulty)
    palette_kind = ctx.draw_choice("palette_kind", tuple(PALETTES))
    return _build_scene(h, w, emitters, palette_kind, profile, ctx.draw_rng("layout"))


def _emitters(grid) -> list[tuple[int, int, int]]:
    return [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]


def rule_mirror(grid):
    """Python test mirror; the selected canonical Racket rule is authoritative."""
    out = [row[:] for row in grid]
    h = len(grid)
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color == 0:
                continue
            for target_row in range(row, h):
                out[target_row][column] = color
    return out


def semantic_observables(grid) -> dict[str, Any]:
    h = len(grid) if isinstance(grid, list) else 0
    w = len(grid[0]) if h and isinstance(grid[0], list) else 0
    cells = _emitters(grid) if h and all(isinstance(row, list) and len(row) == w for row in grid) else []
    column_counts = Counter(column for _, column, _ in cells)
    color_counts = Counter(color for _, _, color in cells)
    stacked_columns = sum(count > 1 for count in column_counts.values())
    bottom_emitters = sum(row == h - 1 for row, _, _ in cells) if h else 0
    repeated_colors = sum(count > 1 for count in color_counts.values())

    profile = None
    if cells and stacked_columns == 1 and max(column_counts.values()) == 2 and bottom_emitters == 0 and repeated_colors == 0:
        profile = "stacked"
    elif cells and stacked_columns == 0 and bottom_emitters == 1 and repeated_colors == 0:
        profile = "bottom_boundary"
    elif (
        cells
        and stacked_columns == 0
        and bottom_emitters == 0
        and repeated_colors == 1
        and sorted(color_counts.values()).count(2) == 1
        and max(color_counts.values()) == 2
    ):
        profile = "repeated_color"
    elif cells and stacked_columns == 0 and bottom_emitters == 0 and repeated_colors == 0:
        profile = "canonical"

    palette_kind = None
    colors = set(color_counts)
    for name, palette in PALETTES.items():
        if colors and colors <= set(palette):
            palette_kind = name
            break

    return {
        "grid_h": h,
        "grid_w": w,
        "emitters": len(cells),
        "palette_kind": palette_kind,
        "profile": profile,
        "stacked_columns": stacked_columns,
        "bottom_emitters": bottom_emitters,
        "repeated_colors": repeated_colors,
        "source_rows": tuple(sorted({row for row, _, _ in cells})),
        "source_columns": tuple(sorted(column_counts)),
        "source_colors": tuple(sorted(color_counts)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected teaching manifold, including canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty 2D list"]
    if any(not isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    h = len(grid)
    if not 6 <= h <= 12:
        errors.append(f"grid height must be in 6..12, got {h}")
    if not 7 <= width <= 12:
        errors.append(f"grid width must be in 7..12, got {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
    if errors:
        return errors

    facts = semantic_observables(grid)
    if not 2 <= facts["emitters"] <= 4:
        errors.append(f"expected 2..4 visible sources, got {facts['emitters']}")
    if len(facts["source_rows"]) < 2:
        errors.append("sources must occupy at least two rows")
    if facts["profile"] not in SCHEDULE_PROFILES:
        errors.append("grid does not match a declared teaching profile")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = semantic_observables(grid)
    if facts["palette_kind"] is None or facts["profile"] is None:
        raise ValueError("generated axes are not observable")
    return {axis: facts[axis] for axis in AXES}


def _identity(grid):
    return [row[:] for row in grid]


def cast_upward(grid):
    out = [row[:] for row in grid]
    for row, column, color in _emitters(grid):
        for target_row in range(0, row + 1):
            out[target_row][column] = color
    return out


def fill_full_columns(grid):
    out = [row[:] for row in grid]
    for _, column, color in _emitters(grid):
        for target_row in range(len(grid)):
            out[target_row][column] = color
    return out


def topmost_per_column(grid):
    """Canonical-fitting shortcut: ignore every lower source in a column."""
    out = [row[:] for row in grid]
    by_column: dict[int, list[tuple[int, int]]] = {}
    for row, column, color in _emitters(grid):
        by_column.setdefault(column, []).append((row, color))
    for column, sources in by_column.items():
        row, color = min(sources)
        for target_row in range(row, len(grid)):
            out[target_row][column] = color
    return out


def unique_colors_only(grid):
    """Canonical-fitting shortcut: cast only colors occurring once globally."""
    out = [row[:] for row in grid]
    counts = Counter(color for _, _, color in _emitters(grid))
    for row, column, color in _emitters(grid):
        if counts[color] != 1:
            continue
        for target_row in range(row, len(grid)):
            out[target_row][column] = color
    return out


def drop_bottom_sources(grid):
    """Canonical-fitting construction bug: erase zero-length bottom rays."""
    out = [row[:] for row in grid]
    last = len(grid) - 1
    for row, column, color in _emitters(grid):
        if row == last:
            out[row][column] = 0
            continue
        for target_row in range(row, len(grid)):
            out[target_row][column] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "cast_upward": cast_upward,
    "fill_full_columns": fill_full_columns,
    "topmost_per_column": topmost_per_column,
    "unique_colors_only": unique_colors_only,
    "drop_bottom_sources": drop_bottom_sources,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("topmost_per_column", "unique_colors_only", "drop_bottom_sources")
}


def _profile_witness(profile: str):
    return lambda grid: not self_check(grid) and semantic_observables(grid)["profile"] == profile


def _positive_witness(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != grid


SEMANTIC_WITNESSES = {
    "downward_to_bottom": _positive_witness,
    "stacked_overwrite": _profile_witness("stacked"),
    "bottom_source_preserved": _profile_witness("bottom_boundary"),
    "repeated_color_sources": _profile_witness("repeated_color"),
}
WITNESS_RIVALS = {
    "downward_to_bottom": ["identity", "cast_upward", "fill_full_columns"],
    "stacked_overwrite": ["topmost_per_column"],
    "bottom_source_preserved": ["drop_bottom_sources"],
    "repeated_color_sources": ["unique_colors_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives demos but changes the query."""
    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], dict[str, list[list[int]]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        prepared.append(
            (
                pair["output"],
                {
                    name: competitor(pair["input"])
                    for name, competitor in LESSON_COMPETITORS.items()
                },
            )
        )
    if reasons:
        return sorted(set(reasons))

    if not isinstance(query, dict) or "input" not in query:
        return ["query is malformed"]
    query_errors = self_check(query["input"])
    if query_errors:
        return ["query input is invalid: " + "; ".join(query_errors)]

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(outputs[name] == expected for expected, outputs in prepared)
        if survives and competitor(query["input"]) != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but changes the query"
            )
    return sorted(reasons)
