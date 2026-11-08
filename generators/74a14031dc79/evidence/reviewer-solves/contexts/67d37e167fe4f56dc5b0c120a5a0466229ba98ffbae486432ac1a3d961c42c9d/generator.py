"""Generator for ARC task e133d23d / 74a14031dc79.

The input has two aligned 3-column panels separated by one solid column.  For
each aligned cell, the output is blue (2) when either panel cell is nonzero and
black (0) only when both are zero.

Every ordinary sample contains all four aligned occupancy relations (00, 10,
01, 11).  Thus one-panel copy rules, XOR, AND, and solid-fill rules fail inside
each example instead of relying on chance across a lesson.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "74a14031dc79"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "582367af483f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read two aligned 3-column panels on either side of a solid separator. "
    "Output blue (2) wherever either aligned panel cell is nonzero; otherwise "
    "output black (0)."
)

INVARIANTS = [
    "input width is 7: 3-column left panel, solid separator, 3-column right panel",
    "height is 3..12; each panel and the separator use one distinct nonzero non-blue color",
    "every generated input contains 00, left-only, right-only, and overlap relations",
    "output shape is grid_h by 3 and output colors are a subset of {0,2}",
    "every four-sample schedule cycle includes a canonical 3x7 / colors 6,4,8 anchor",
]

RELATION_PROFILES = (
    "balanced",
    "left_heavy",
    "right_heavy",
    "overlap_heavy",
    "empty_heavy",
)
SCHEDULE_PROFILES = tuple(range(4))
_SLOT_RELATION = RELATION_PROFILES[:4]
_RELATIONS = ("00", "10", "01", "11")
_LEGAL_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_ROLE_NAMES = ("left_color", "right_color", "sep_color")
_CANONICAL_ROLE_COLORS = {
    "left_color": 6,
    "right_color": 8,
    "sep_color": 4,
}

# All public controls are exact and recoverable from returned pixels.  The old
# density/pattern/or_target controls were removed: they were distribution hints,
# not observable contracts, and their degenerate aliases admitted invalid grids.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "3 on two schedule slots; otherwise difficulty-banded 4..12",
        "valid": "3..12",
    },
    "left_color": {
        "type": "color",
        "default": "canonical anchor plus independent keyed draws",
        "valid": "1|3..9",
    },
    "right_color": {
        "type": "color",
        "default": "canonical anchor plus independent keyed draws, distinct from left",
        "valid": "1|3..9",
    },
    "sep_color": {
        "type": "color",
        "default": "canonical anchor plus independent keyed draws, distinct from panels",
        "valid": "1|3..9",
    },
    "relation_profile": {
        "type": "str",
        "default": "four-slot balanced/left/right/overlap schedule; empty-heavy overrideable",
        "valid": "|".join(RELATION_PROFILES),
    },
}

# Equal role colors are the only incompatible exact public combinations.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = tuple(
    {first: color, second: color}
    for first, second in (
        ("left_color", "right_color"),
        ("left_color", "sep_color"),
        ("right_color", "sep_color"),
    )
    for color in _LEGAL_COLORS
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


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    grid_h = overrides.get("grid_h")
    if grid_h is not None:
        if type(grid_h) is not int:
            raise ValueError("grid_h must be an integer")
        if not 3 <= grid_h <= 12:
            raise ValueError("grid_h must be in 3..12")

    for name in _ROLE_NAMES:
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer color")
        if value not in _LEGAL_COLORS:
            raise ValueError(f"{name} must be one of {_LEGAL_COLORS}")

    requested_colors = [overrides[name] for name in _ROLE_NAMES if overrides.get(name) is not None]
    if len(requested_colors) != len(set(requested_colors)):
        raise ValueError("left, right, and separator colors must be distinct")

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


def _draw_height(ctx, slot: int, band: str, overrides: dict[str, Any]) -> int:
    if overrides.get("grid_h") is not None:
        return int(ctx.draw_int("grid_h", 3, 12))
    # Two of four schedule positions retain canonical 3-row scale.  This
    # clears the pinned 25% canonical-profile floor in every difficulty band
    # while the other two slots preserve substantial off-canonical variation.
    if slot in (0, 1):
        return int(ctx.draw_int("grid_h", 3, 3))
    lo, hi = {
        "easy": (4, 5),
        "medium": (6, 8),
        "hard": (9, 12),
    }[band]
    return int(ctx.draw_int("grid_h", lo, hi))


def _forced_color(ctx, label: str, value: int) -> int:
    return int(ctx.draw_color(label, exclude=set(range(10)) - {value}))


def _draw_colors(ctx, slot: int, overrides: dict[str, Any]) -> tuple[int, int, int]:
    chosen: dict[str, int] = {}
    preference_order = (6, 8, 4, 1, 3, 5, 7, 9)

    for index, name in enumerate(_ROLE_NAMES):
        requested = overrides.get(name)
        used = set(chosen.values())
        future_requested = {
            int(overrides[future])
            for future in _ROLE_NAMES[index + 1 :]
            if overrides.get(future) is not None
        }
        if requested is not None:
            chosen[name] = int(ctx.draw_color(name, exclude={0, 2} | used))
            continue

        if slot == 0:
            preferred = _CANONICAL_ROLE_COLORS[name]
            candidates = (preferred,) + tuple(
                color for color in preference_order if color != preferred
            )
            value = next(
                color
                for color in candidates
                if color not in used and color not in future_requested
            )
            chosen[name] = _forced_color(ctx, name, value)
            continue

        excluded = {0, 2} | used | future_requested
        # Keep non-anchor defaults off the exact canonical role palette.  Exact
        # overrides may intentionally request it and remain fully supported.
        if (
            name == "sep_color"
            and chosen.get("left_color") == 6
            and chosen.get("right_color") == 8
        ):
            excluded.add(4)
        chosen[name] = int(ctx.draw_color(name, exclude=excluded))

    values = tuple(chosen[name] for name in _ROLE_NAMES)
    if len(set(values)) != 3:
        raise ValueError("left, right, and separator colors must be distinct")
    return values


def _draw_relation_profile(ctx, slot: int, overrides: dict[str, Any]) -> str:
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
        "left_heavy": "10",
        "right_heavy": "01",
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
    _validate_call(difficulty, overrides)
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
    height = _draw_height(ctx, slot, band, overrides)
    left_color, right_color, sep_color = _draw_colors(ctx, slot, overrides)
    relation_profile = _draw_relation_profile(ctx, slot, overrides)

    labels: list[str] = []
    for relation, count in _relation_counts(height * 3, relation_profile).items():
        labels.extend([relation] * count)
    ctx.draw_rng("relation_layout").shuffle(labels)

    grid = full_grid(height, 7, 0)
    for row in range(height):
        grid[row][3] = sep_color
    for index, relation in enumerate(labels):
        row, col = divmod(index, 3)
        if relation[0] == "1":
            grid[row][col] = left_color
        if relation[1] == "1":
            grid[row][col + 4] = right_color

    errors = strict_canonical_like(grid)
    if not errors:
        info, _ = _analyse(grid)
        errors = _teaching_profile_errors(info)
    if errors:
        raise AssertionError("constructed invalid side-OR lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "left_color": left_color,
        "right_color": right_color,
        "sep_color": sep_color,
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


def _relation_histogram(grid: Grid) -> dict[str, int]:
    counts = {relation: 0 for relation in _RELATIONS}
    for row in range(len(grid)):
        for col in range(3):
            relation = f"{int(grid[row][col] != 0)}{int(grid[row][col + 4] != 0)}"
            counts[relation] += 1
    return counts


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    normalized, errors = _normalize_grid(grid)
    info: dict[str, Any] = {"grid": normalized}
    if normalized is None or errors:
        return info, errors

    height, width = len(normalized), len(normalized[0])
    info.update({"grid_h": height, "grid_w": width})
    if width != 7:
        errors.append(f"input width must be 7, got {width}")
        return info, errors
    if not 3 <= height <= 12:
        errors.append(f"input height must be 3..12, got {height}")

    left_colors = {
        normalized[row][col]
        for row in range(height)
        for col in range(3)
        if normalized[row][col] != 0
    }
    right_colors = {
        normalized[row][col]
        for row in range(height)
        for col in range(4, 7)
        if normalized[row][col] != 0
    }
    separator_colors = {normalized[row][3] for row in range(height)}
    info.update(
        {
            "left_colors": left_colors,
            "right_colors": right_colors,
            "separator_colors": separator_colors,
        }
    )

    if len(left_colors) != 1:
        errors.append(
            f"left panel must use exactly one nonzero color, got {sorted(left_colors)}"
        )
    if len(right_colors) != 1:
        errors.append(
            f"right panel must use exactly one nonzero color, got {sorted(right_colors)}"
        )
    if len(separator_colors) != 1 or 0 in separator_colors:
        errors.append(
            "separator column must be solid and nonzero, got "
            f"{sorted(separator_colors)}"
        )

    role_colors = left_colors | right_colors | separator_colors
    if 2 in role_colors:
        errors.append("input role colors cannot use output color 2")
    if len(left_colors) == len(right_colors) == len(separator_colors) == 1:
        exact_roles = (
            next(iter(left_colors)),
            next(iter(right_colors)),
            next(iter(separator_colors)),
        )
        info.update(
            {
                "left_color": exact_roles[0],
                "right_color": exact_roles[1],
                "sep_color": exact_roles[2],
            }
        )
        if len(set(exact_roles)) != 3:
            errors.append("left, right, and separator colors must be distinct")

    info["relation_counts"] = _relation_histogram(normalized)
    return info, errors


def _teaching_profile_errors(info: dict[str, Any]) -> list[str]:
    """Return stronger lesson-quality errors for generated grids only.

    Canonical task inputs are lawful even when one Boolean relation is absent;
    generated lessons deliberately require all four relations so the OR rule is
    identifiable against left-only, right-only, XOR, and AND shortcuts.
    """
    counts = info.get("relation_counts")
    if not isinstance(counts, dict):
        return ["relation histogram is unavailable"]
    missing = [relation for relation in _RELATIONS if counts.get(relation, 0) == 0]
    if missing:
        return [
            "generated teaching truth table is incomplete; missing "
            + ", ".join(missing)
        ]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    """Validate lawful task inputs without executing the answer rule."""
    del difficulty, meta
    _, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None):
    """Validate the shared structural domain of generated and canonical inputs."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def _profile_from_counts(counts: dict[str, int]) -> str:
    values = list(counts.values())
    if max(values) - min(values) <= 1:
        return "balanced"
    leaders = [relation for relation in _RELATIONS if counts[relation] == max(values)]
    if len(leaders) != 1:
        raise ValueError(f"relation counts do not identify one profile: {counts}")
    return {
        "10": "left_heavy",
        "01": "right_heavy",
        "11": "overlap_heavy",
        "00": "empty_heavy",
    }[leaders[0]]


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact public axis from a returned generated grid."""
    info, errors = _analyse(grid)
    errors.extend(_teaching_profile_errors(info))
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "left_color": info["left_color"],
        "right_color": info["right_color"],
        "sep_color": info["sep_color"],
        "relation_profile": _profile_from_counts(info["relation_counts"]),
    }


def rule_mirror(grid: Any) -> Grid:
    """Python audit mirror; the canonical Racket program remains authoritative."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized = info["grid"]
    return [
        [
            2 if normalized[row][col] != 0 or normalized[row][col + 4] != 0 else 0
            for col in range(3)
        ]
        for row in range(info["grid_h"])
    ]


def _rival_left_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g = info["grid"]
    return [[2 if g[row][col] != 0 else 0 for col in range(3)] for row in range(info["grid_h"])]


def _rival_right_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g = info["grid"]
    return [[2 if g[row][col + 4] != 0 else 0 for col in range(3)] for row in range(info["grid_h"])]


def _rival_xor(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g = info["grid"]
    return [
        [2 if bool(g[row][col]) != bool(g[row][col + 4]) else 0 for col in range(3)]
        for row in range(info["grid_h"])
    ]


def _rival_and(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g = info["grid"]
    return [
        [
            2 if g[row][col] != 0 and g[row][col + 4] != 0 else 0
            for col in range(3)
        ]
        for row in range(info["grid_h"])
    ]


def _rival_constant_blue(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return full_grid(info["grid_h"], 3, 2)


def _rival_input_blue_echo(grid: Any) -> Grid:
    """Wrong rule: preserve only panel cells already colored blue."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g = info["grid"]
    return [
        [2 if g[row][col] == 2 or g[row][col + 4] == 2 else 0 for col in range(3)]
        for row in range(info["grid_h"])
    ]


def _rival_fixed_shape_3x7(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["grid_h"] == 3 and info["grid_w"] == 7:
        return rule_mirror(grid)
    return full_grid(info["grid_h"], 3, 0)


def _rival_fixed_palette_684(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if (info["left_color"], info["right_color"], info["sep_color"]) == (6, 8, 4):
        return rule_mirror(grid)
    return full_grid(info["grid_h"], 3, 0)


def _rival_canonical_shape_and_palette(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if (
        info["grid_h"] == 3
        and (info["left_color"], info["right_color"], info["sep_color"])
        == (6, 8, 4)
    ):
        return rule_mirror(grid)
    return full_grid(info["grid_h"], 3, 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "left_panel_only": _rival_left_only,
    "right_panel_only": _rival_right_only,
    "occupancy_xor": _rival_xor,
    "occupancy_and": _rival_and,
    "constant_blue_rectangle": _rival_constant_blue,
    "input_blue_echo": _rival_input_blue_echo,
    "fixed_shape_3x7": _rival_fixed_shape_3x7,
    "fixed_palette_684": _rival_fixed_palette_684,
    "canonical_shape_and_palette_only": _rival_canonical_shape_and_palette,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_shape_3x7": _rival_fixed_shape_3x7,
    "fixed_palette_684": _rival_fixed_palette_684,
    "canonical_shape_and_palette_only": _rival_canonical_shape_and_palette,
}


def _relation_witness(relation: str):
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["relation_counts"][relation] > 0

    return predicate


def _off_canonical_shape(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and (info["grid_h"], info["grid_w"]) != (3, 7)


def _off_canonical_palette(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and (
        info["left_color"],
        info["right_color"],
        info["sep_color"],
    ) != (6, 8, 4)


def _blue_absent_from_input(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and all(2 not in row for row in info["grid"])


SEMANTIC_WITNESSES = {
    "both_empty_relation": _relation_witness("00"),
    "left_only_relation": _relation_witness("10"),
    "right_only_relation": _relation_witness("01"),
    "overlap_relation": _relation_witness("11"),
    "off_canonical_shape": _off_canonical_shape,
    "off_canonical_palette": _off_canonical_palette,
    "output_blue_absent_from_input": _blue_absent_from_input,
}
WITNESS_RIVALS = {
    "both_empty_relation": ["constant_blue_rectangle"],
    "left_only_relation": ["right_panel_only", "occupancy_and"],
    "right_only_relation": ["left_panel_only", "occupancy_and"],
    "overlap_relation": ["occupancy_xor"],
    "off_canonical_shape": ["fixed_shape_3x7", "canonical_shape_and_palette_only"],
    "off_canonical_palette": ["fixed_palette_684", "canonical_shape_and_palette_only"],
    "output_blue_absent_from_input": ["input_blue_echo"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to refute every declared competitor."""
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
