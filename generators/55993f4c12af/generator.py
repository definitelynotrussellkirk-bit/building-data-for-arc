"""Generator for ARC task 55993f4c12af: aligned half-height occupancy OR.

The input is an even-height grid with one foreground color in the top half and
another in the bottom half.  The output overlays aligned cells: yellow (4)
where either half is nonzero, black (0) where both are zero.

Every ordinary sample contains all four aligned occupancy relations (00, 10,
01, 11).  This makes one-panel copy rules, XOR, AND, and solid-fill rules fail
inside each example instead of relying on luck across a lesson.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "55993f4c12af"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ce2dee847896"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Split the even-height input into equal top and bottom halves. For each "
    "aligned cell, output yellow (4) when either half is nonzero; output black "
    "(0) only when both aligned cells are black."
)

INVARIANTS = [
    "input height is even and equals 2*half_h, with half_h in 3..7",
    "top and bottom halves each use exactly one distinct nonzero non-yellow color",
    "every generated grid contains 00, top-only, bottom-only, and overlap relations",
    "output shape is half_h by grid_w and output colors are exactly a subset of {0,4}",
    "every four-sample schedule cycle includes a canonical 12x4 / colors 3,5 anchor",
]

RELATION_PROFILES = (
    "balanced",
    "top_heavy",
    "bottom_heavy",
    "overlap_heavy",
    "empty_heavy",
)
SCHEDULE_PROFILES = tuple(range(4))
_SLOT_RELATION = RELATION_PROFILES[:4]
_RELATIONS = ("00", "10", "01", "11")
_LEGAL_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# The public controls are exact and recoverable from the returned grid.  The
# previous density/pattern/texture/or_target controls were removed: they were
# either unobservable distribution hints or admitted invalid fixtures as lawful
# values.  relation_profile is the exact replacement for support composition.
AXES = {
    "half_h": {
        "type": "int",
        "default": "6 on schedule anchors; otherwise difficulty-banded 3..7",
        "valid": "3..7",
    },
    "grid_w": {
        "type": "int",
        "default": "4 on schedule anchors; otherwise difficulty-banded 5..14",
        "valid": "3..14",
    },
    "top_color": {
        "type": "color",
        "default": "canonical anchor plus independent keyed draws",
        "valid": "1..3|5..9",
    },
    "bot_color": {
        "type": "color",
        "default": "canonical anchor plus independent keyed draws, distinct from top_color",
        "valid": "1..3|5..9",
    },
    "relation_profile": {
        "type": "str",
        "default": "four-slot balanced/top/bottom/overlap schedule; empty-heavy is overrideable",
        "valid": "|".join(RELATION_PROFILES),
    },
}

# Exact pairwise color requests with equal colors are the only incompatible
# public combinations.  Declaring them keeps the override matrix strict rather
# than treating ordinary bugs as intentional rejections.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = (
    {"top_color": 1, "bot_color": 1},
    {"top_color": 2, "bot_color": 2},
    {"top_color": 3, "bot_color": 3},
    {"top_color": 5, "bot_color": 5},
    {"top_color": 6, "bot_color": 6},
    {"top_color": 7, "bot_color": 7},
    {"top_color": 8, "bot_color": 8},
    {"top_color": 9, "bot_color": 9},
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("half_h", "grid_w", "top_color", "bot_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")

    if "half_h" in overrides and overrides["half_h"] is not None:
        if not 3 <= overrides["half_h"] <= 7:
            raise ValueError("half_h must be in 3..7")
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        if not 3 <= overrides["grid_w"] <= 14:
            raise ValueError("grid_w must be in 3..14")
    for name in ("top_color", "bot_color"):
        value = overrides.get(name)
        if value is not None and value not in _LEGAL_COLORS:
            raise ValueError(f"{name} must be one of {_LEGAL_COLORS}")
    if (
        overrides.get("top_color") is not None
        and overrides.get("bot_color") is not None
        and overrides["top_color"] == overrides["bot_color"]
    ):
        raise ValueError("top_color and bot_color must be distinct")

    profile = overrides.get("relation_profile")
    if profile is not None:
        if type(profile) is not str:
            raise ValueError("relation_profile must be a string")
        if profile not in RELATION_PROFILES:
            raise ValueError(
                "relation_profile must be one of " + ", ".join(RELATION_PROFILES)
            )


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Return the deterministic four-slot curriculum position."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _draw_dimension(
    ctx,
    label: str,
    slot: int,
    band: str,
    overrides: dict[str, Any],
) -> int:
    if label == "half_h":
        full_lo, full_hi = 3, 7
        anchor = 6
        ranges = {"easy": (3, 4), "medium": (4, 6), "hard": (6, 7)}
    else:
        full_lo, full_hi = 3, 14
        anchor = 4
        # Non-anchor widths deliberately exclude 4, so fixed-canonical-shape
        # shortcuts are refuted in every sliding three-example lesson.
        ranges = {"easy": (5, 7), "medium": (8, 10), "hard": (11, 14)}

    if overrides.get(label) is not None:
        return int(ctx.draw_int(label, full_lo, full_hi))
    if slot == 0:
        return int(ctx.draw_int(label, anchor, anchor))
    lo, hi = ranges[band]
    return int(ctx.draw_int(label, lo, hi))


def _forced_color(ctx, label: str, value: int) -> int:
    return int(ctx.draw_color(label, exclude=set(range(10)) - {value}))


def _draw_colors(ctx, slot: int, overrides: dict[str, Any]) -> tuple[int, int]:
    requested_top = overrides.get("top_color")
    requested_bottom = overrides.get("bot_color")

    # The anchor is exact.  Non-anchor palettes are independent keyed draws,
    # not paired aliases; the sole default exclusion prevents accidentally
    # reproducing the canonical (3, 5) palette outside the anchor slot.
    if slot == 0 and requested_top is None:
        top_choice = 3 if requested_bottom != 3 else 5
        top = _forced_color(ctx, "top_color", top_choice)
    elif requested_top is not None:
        top = int(ctx.draw_color("top_color", exclude={0, 4}))
    else:
        top_exclude = {0, 4}
        if requested_bottom is not None:
            top_exclude.add(int(requested_bottom))
            if requested_bottom == 5:
                top_exclude.add(3)
        top = int(ctx.draw_color("top_color", exclude=top_exclude))

    if slot == 0 and requested_bottom is None:
        bottom_choice = 5 if top != 5 else 1
        bottom = _forced_color(ctx, "bot_color", bottom_choice)
    elif requested_bottom is not None:
        bottom = int(ctx.draw_color("bot_color", exclude={0, 4, top}))
    else:
        bottom_exclude = {0, 4, top}
        if top == 3:
            bottom_exclude.add(5)
        bottom = int(ctx.draw_color("bot_color", exclude=bottom_exclude))

    if top == bottom:
        raise ValueError("top_color and bot_color must be distinct")
    return top, bottom


def _draw_relation_profile(
    ctx, slot: int, overrides: dict[str, Any]
) -> str:
    if overrides.get("relation_profile") is not None:
        return str(ctx.draw_choice("relation_profile", RELATION_PROFILES))
    return str(ctx.draw_choice("relation_profile", (_SLOT_RELATION[slot],)))


def _relation_counts(total: int, profile: str) -> dict[str, int]:
    """Return exact counts while keeping all four truth-table rows live."""
    if total < 4:
        raise ValueError("at least four aligned cells are required")
    if profile == "balanced":
        base, remainder = divmod(total, 4)
        return {
            relation: base + int(index < remainder)
            for index, relation in enumerate(_RELATIONS)
        }

    heavy_relation = {
        "top_heavy": "10",
        "bottom_heavy": "01",
        "overlap_heavy": "11",
        "empty_heavy": "00",
    }[profile]
    counts = {relation: 1 for relation in _RELATIONS}
    remaining = total - 4
    heavy_extra = min(remaining, max(2, (remaining + 1) // 2))
    counts[heavy_relation] += heavy_extra
    remaining -= heavy_extra
    others = [relation for relation in _RELATIONS if relation != heavy_relation]
    for index in range(remaining):
        counts[others[index % len(others)]] += 1
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, semantically identifying input grid."""
    _validate_call(seed, sample_index, difficulty, overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, band)
    half_h = _draw_dimension(ctx, "half_h", slot, band, overrides)
    width = _draw_dimension(ctx, "grid_w", slot, band, overrides)
    top_color, bottom_color = _draw_colors(ctx, slot, overrides)
    relation_profile = _draw_relation_profile(ctx, slot, overrides)

    relation_labels: list[str] = []
    for relation, count in _relation_counts(half_h * width, relation_profile).items():
        relation_labels.extend([relation] * count)
    ctx.draw_rng("relation_layout").shuffle(relation_labels)

    grid = full_grid(2 * half_h, width, 0)
    for index, relation in enumerate(relation_labels):
        row, col = divmod(index, width)
        if relation[0] == "1":
            grid[row][col] = top_color
        if relation[1] == "1":
            grid[half_h + row][col] = bottom_color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("constructed invalid OR lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "half_h": half_h,
        "grid_w": width,
        "top_color": top_color,
        "bot_color": bottom_color,
        "relation_profile": relation_profile,
    }
    if observed != expected:
        raise AssertionError(
            f"override observation mismatch: expected {expected}, got {observed}"
        )
    return grid


def _normalize_grid(grid: Any) -> tuple[Grid | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    normalized = [list(row) for row in grid]
    invalid = sorted(
        {
            value
            for row in normalized
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        return normalized, [f"cells must be integer ARC colors 0..9, got {invalid}"]
    return normalized, []


def _relation_histogram(grid: Grid, half_h: int, width: int) -> dict[str, int]:
    counts = {relation: 0 for relation in _RELATIONS}
    for row in range(half_h):
        for col in range(width):
            relation = (
                f"{int(grid[row][col] != 0)}"
                f"{int(grid[half_h + row][col] != 0)}"
            )
            counts[relation] += 1
    return counts


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    normalized, errors = _normalize_grid(grid)
    info: dict[str, Any] = {"grid": normalized}
    if normalized is None or errors:
        return info, errors

    height, width = len(normalized), len(normalized[0])
    info.update({"grid_h": height, "grid_w": width})
    if height % 2:
        errors.append(f"input height must be even, got {height}")
        return info, errors
    half_h = height // 2
    info["half_h"] = half_h
    if not 3 <= half_h <= 7:
        errors.append(f"half-height must be 3..7, got {half_h}")
    if not 3 <= width <= 14:
        errors.append(f"width must be 3..14, got {width}")

    top_colors = {
        normalized[row][col]
        for row in range(half_h)
        for col in range(width)
        if normalized[row][col] != 0
    }
    bottom_colors = {
        normalized[half_h + row][col]
        for row in range(half_h)
        for col in range(width)
        if normalized[half_h + row][col] != 0
    }
    info.update({"top_colors": top_colors, "bottom_colors": bottom_colors})
    if len(top_colors) != 1:
        errors.append(
            f"top half must use exactly one nonzero color, got {sorted(top_colors)}"
        )
    if len(bottom_colors) != 1:
        errors.append(
            "bottom half must use exactly one nonzero color, got "
            f"{sorted(bottom_colors)}"
        )
    if top_colors & {4}:
        errors.append("top foreground color cannot be output color 4")
    if bottom_colors & {4}:
        errors.append("bottom foreground color cannot be output color 4")
    if top_colors and bottom_colors and top_colors == bottom_colors:
        errors.append("top and bottom foreground colors must be distinct")

    counts = _relation_histogram(normalized, half_h, width)
    info["relation_counts"] = counts
    missing = [relation for relation in _RELATIONS if counts[relation] == 0]
    if missing:
        errors.append(
            "aligned occupancy truth table is incomplete; missing " + ", ".join(missing)
        )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the ordinary teaching domain without executing the answer rule."""
    del difficulty, meta
    _, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None):
    """All generated and canonical examples are inside the strict domain."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def _profile_from_counts(counts: dict[str, int]) -> str:
    values = list(counts.values())
    if max(values) - min(values) <= 1:
        return "balanced"
    leaders = [relation for relation in _RELATIONS if counts[relation] == max(values)]
    if len(leaders) != 1:
        raise ValueError(f"relation counts do not identify one profile: {counts}")
    return {
        "10": "top_heavy",
        "01": "bottom_heavy",
        "11": "overlap_heavy",
        "00": "empty_heavy",
    }[leaders[0]]


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact public axis from a returned generated grid."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if len(info["top_colors"]) != 1 or len(info["bottom_colors"]) != 1:
        raise ValueError("panel colors are not uniquely observable")
    return {
        "half_h": info["half_h"],
        "grid_w": info["grid_w"],
        "top_color": next(iter(info["top_colors"])),
        "bot_color": next(iter(info["bottom_colors"])),
        "relation_profile": _profile_from_counts(info["relation_counts"]),
    }


def rule_mirror(grid: Any) -> Grid:
    """Python audit mirror; the canonical Racket program remains authoritative."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized = info["grid"]
    half_h, width = info["half_h"], info["grid_w"]
    return [
        [
            4
            if normalized[row][col] != 0
            or normalized[half_h + row][col] != 0
            else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _rival_top_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, half_h, width = info["grid"], info["half_h"], info["grid_w"]
    return [[4 if g[row][col] != 0 else 0 for col in range(width)] for row in range(half_h)]


def _rival_bottom_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, half_h, width = info["grid"], info["half_h"], info["grid_w"]
    return [
        [4 if g[half_h + row][col] != 0 else 0 for col in range(width)]
        for row in range(half_h)
    ]


def _rival_xor(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, half_h, width = info["grid"], info["half_h"], info["grid_w"]
    return [
        [
            4 if bool(g[row][col]) != bool(g[half_h + row][col]) else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _rival_and(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, half_h, width = info["grid"], info["half_h"], info["grid_w"]
    return [
        [
            4 if g[row][col] != 0 and g[half_h + row][col] != 0 else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _rival_constant_yellow(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return full_grid(info["half_h"], info["grid_w"], 4)


def _rival_input_yellow_echo(grid: Any) -> Grid:
    """Wrong rule: preserve only input cells already colored yellow."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, half_h, width = info["grid"], info["half_h"], info["grid_w"]
    return [
        [
            4 if g[row][col] == 4 or g[half_h + row][col] == 4 else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _rival_fixed_shape_12x4(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["grid_h"] == 12 and info["grid_w"] == 4:
        return rule_mirror(grid)
    return full_grid(info["half_h"], info["grid_w"], 0)


def _rival_fixed_palette_35(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    top = next(iter(info["top_colors"]))
    bottom = next(iter(info["bottom_colors"]))
    if (top, bottom) == (3, 5):
        return rule_mirror(grid)
    return full_grid(info["half_h"], info["grid_w"], 0)


def _rival_canonical_shape_and_palette(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    top = next(iter(info["top_colors"]))
    bottom = next(iter(info["bottom_colors"]))
    if info["grid_h"] == 12 and info["grid_w"] == 4 and (top, bottom) == (3, 5):
        return rule_mirror(grid)
    return full_grid(info["half_h"], info["grid_w"], 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "top_half_only": _rival_top_only,
    "bottom_half_only": _rival_bottom_only,
    "occupancy_xor": _rival_xor,
    "occupancy_and": _rival_and,
    "constant_yellow_rectangle": _rival_constant_yellow,
    "input_yellow_echo": _rival_input_yellow_echo,
    "fixed_shape_12x4": _rival_fixed_shape_12x4,
    "fixed_palette_35": _rival_fixed_palette_35,
    "canonical_shape_and_palette_only": _rival_canonical_shape_and_palette,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_shape_12x4": _rival_fixed_shape_12x4,
    "fixed_palette_35": _rival_fixed_palette_35,
    "canonical_shape_and_palette_only": _rival_canonical_shape_and_palette,
}


def _relation_witness(relation: str):
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["relation_counts"][relation] > 0

    return predicate


def _off_canonical_shape(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and (info["grid_h"], info["grid_w"]) != (12, 4)


def _off_canonical_palette(grid: Any) -> bool:
    info, errors = _analyse(grid)
    if errors:
        return False
    return (
        next(iter(info["top_colors"])),
        next(iter(info["bottom_colors"])),
    ) != (3, 5)


def _yellow_absent_from_input(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and all(4 not in row for row in info["grid"])


SEMANTIC_WITNESSES = {
    "both_empty_relation": _relation_witness("00"),
    "top_only_relation": _relation_witness("10"),
    "bottom_only_relation": _relation_witness("01"),
    "overlap_relation": _relation_witness("11"),
    "off_canonical_shape": _off_canonical_shape,
    "off_canonical_palette": _off_canonical_palette,
    "output_yellow_absent_from_input": _yellow_absent_from_input,
}
WITNESS_RIVALS = {
    "both_empty_relation": ["constant_yellow_rectangle"],
    "top_only_relation": ["bottom_half_only", "occupancy_and"],
    "bottom_only_relation": ["top_half_only", "occupancy_and"],
    "overlap_relation": ["occupancy_xor"],
    "off_canonical_shape": ["fixed_shape_12x4", "canonical_shape_and_palette_only"],
    "off_canonical_palette": ["fixed_palette_35", "canonical_shape_and_palette_only"],
    "output_yellow_absent_from_input": ["input_yellow_echo"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every sliding lesson to refute every declared competitor."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        grid = pair["input"]
        errors = strict_canonical_like(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(grid)
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not the aligned occupancy OR")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(grid) != expected:
                killed[name] = True

    survivors = sorted(name for name, was_killed in killed.items() if not was_killed)
    if survivors:
        reasons.append(f"named competitors survive every demonstration: {survivors}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative OR transform")
    return reasons
