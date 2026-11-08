"""Generator for ARC task 7d8fc2325e02: separated-panel occupancy OR.

The 9-row input contains a 4-row top panel, one uniform nonzero separator
row, and a 4-row bottom panel.  The 4-row output is green (3) at every
aligned position occupied in either panel, and black (0) only where both
panels are empty.

Every ordinary sample contains all four Boolean occupancy relations: empty,
top-only, bottom-only, and overlap.  Consequently each example independently
refutes copy-one-panel, AND, XOR, and constant-filled shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7d8fc2325e02"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e9653f7b4ad7"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the four rows above and below the uniform separator as aligned "
    "panels. Output a 4-by-width grid containing green (3) wherever either "
    "aligned input cell is nonzero, and black (0) only where both are zero."
)

INVARIANTS = [
    "input height is exactly 9: four top rows, one separator, four bottom rows",
    "input width is 3..14 and separator row 4 is one uniform nonzero color",
    "each panel uses exactly one observable nonzero color",
    "every generated grid contains empty, top-only, bottom-only, and overlap cells",
    "output height is 4, width is unchanged, and output colors are 0 and 3",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "canonical width-5 anchors plus a complete 3..14 schedule",
        "valid": "3..14",
    },
    "top_color": {
        "type": "color",
        "default": "canonical color 2 anchors plus a deterministic palette schedule",
        "valid": "1..9",
    },
    "bot_color": {
        "type": "color",
        "default": "canonical color 1 anchors plus a deterministic palette schedule",
        "valid": "1..9",
    },
    "sep_color": {
        "type": "color",
        "default": "canonical color 4 anchors plus a deterministic palette schedule",
        "valid": "1..9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXPECTED_OUTPUT_CODOMAIN = (0, 3)

Grid = list[list[int]]
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_RELATIONS = ("neither", "top_only", "bottom_only", "both")

# Slot zero is an exact canonical profile.  The three intervening slots are
# broad samples; this four-slot cadence guarantees canonical support in every
# difficulty band without allowing a fixed-shape-only lesson.
SCHEDULE_PROFILES = ("canonical", "broad_a", "broad_b", "broad_c")

# Every band traverses all legal widths; ordering supplies only a mild
# difficulty hint.  _broad_rank removes anchor positions before indexing.
_WIDTH_CYCLES = {
    "easy": (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14),
    "medium": (7, 8, 6, 9, 5, 10, 4, 11, 3, 12, 13, 14),
    "hard": (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3),
}

# Equal colors are lawful because panel and separator roles are positional.
# Including equal-color palettes prevents accidental reliance on color identity.
_PALETTE_CYCLE = (
    (5, 8, 6),
    (9, 1, 7),
    (3, 3, 3),
    (9, 1, 9),
    (6, 2, 5),
    (1, 9, 2),
    (4, 7, 4),
    (8, 8, 2),
)

# Exact occupancy counts observed in the four canonical demonstrations and the
# held-out canonical query.  All contain the complete Boolean truth table.
_CANONICAL_COUNTS = (
    {"neither": 3, "top_only": 4, "bottom_only": 9, "both": 4},
    {"neither": 3, "top_only": 7, "bottom_only": 3, "both": 7},
    {"neither": 6, "top_only": 6, "bottom_only": 5, "both": 3},
    {"neither": 4, "top_only": 4, "bottom_only": 6, "both": 6},
    {"neither": 6, "top_only": 8, "bottom_only": 4, "both": 2},
)


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    if "grid_w" in overrides and overrides["grid_w"] is not None:
        value = overrides["grid_w"]
        if type(value) is not int or not 3 <= value <= 14:
            raise ValueError("grid_w must be an integer in 3..14")
    for name in ("top_color", "bot_color", "sep_color"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not 1 <= value <= 9:
            raise ValueError(f"{name} must be an integer color in 1..9")


def _band(difficulty: Any) -> str:
    return "medium" if difficulty is None else str(difficulty)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic four-slot curriculum branch."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("unknown difficulty")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _broad_rank(sample_index: int) -> int:
    """Dense zero-based rank among non-anchor sample indices."""
    if sample_index % 4 == 0:
        raise ValueError("anchor indices do not have a broad rank")
    return sample_index - sample_index // 4 - 1


def _forced_color(ctx, label: str, value: int) -> int:
    return int(ctx.draw_color(label, exclude=set(range(10)) - {value}))


def _draw_width(ctx, sample_index: int, band: str, overrides: dict[str, Any]) -> int:
    if overrides.get("grid_w") is not None:
        return int(ctx.draw_int_strict("grid_w", 3, 14))
    if sample_index % 4 == 0:
        return int(ctx.draw_int_strict("grid_w", 5, 5))
    default = _WIDTH_CYCLES[band][_broad_rank(sample_index) % 12]
    return int(ctx.draw_int_strict("grid_w", default, default))


def _draw_colors(ctx, sample_index: int, overrides: dict[str, Any]) -> tuple[int, int, int]:
    if sample_index % 4 == 0:
        defaults = (2, 1, 4)
    else:
        defaults = _PALETTE_CYCLE[_broad_rank(sample_index) % len(_PALETTE_CYCLE)]

    result: list[int] = []
    for name, default in zip(("top_color", "bot_color", "sep_color"), defaults):
        if overrides.get(name) is not None:
            result.append(int(ctx.draw_color_strict(name, exclude={0})))
        else:
            result.append(_forced_color(ctx, name, default))
    return result[0], result[1], result[2]


def _balanced_counts(total: int, heavy: str | None) -> dict[str, int]:
    """Construct positive counts for all four occupancy relations."""
    if total < 4:
        raise ValueError("at least four aligned cells are required")
    counts = {relation: 1 for relation in _RELATIONS}
    remaining = total - 4
    if heavy is not None:
        heavy_extra = min(remaining, max(2, (remaining + 1) // 2))
        counts[heavy] += heavy_extra
        remaining -= heavy_extra
    order = [relation for relation in _RELATIONS if relation != heavy]
    for index in range(remaining):
        counts[order[index % len(order)]] += 1
    return counts


def _relation_counts(sample_index: int, width: int) -> dict[str, int]:
    if sample_index % 4 == 0 and width == 5:
        return dict(_CANONICAL_COUNTS[(sample_index // 4) % len(_CANONICAL_COUNTS)])
    profile = (None, "top_only", "bottom_only", "both", "neither")[
        _broad_rank(sample_index) % 5 if sample_index % 4 else (sample_index // 4) % 5
    ]
    return _balanced_counts(4 * width, profile)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input that independently identifies occupancy OR."""
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

    width = _draw_width(ctx, sample_index, band, overrides)
    top_color, bottom_color, separator_color = _draw_colors(ctx, sample_index, overrides)
    counts = _relation_counts(sample_index, width)

    relations: list[str] = []
    for relation in _RELATIONS:
        relations.extend([relation] * counts[relation])
    ctx.draw_rng("relation_layout").shuffle(relations)

    grid = full_grid(9, width, 0)
    grid[4] = [separator_color] * width
    for index, relation in enumerate(relations):
        row, col = divmod(index, width)
        if relation in ("top_only", "both"):
            grid[row][col] = top_color
        if relation in ("bottom_only", "both"):
            grid[row + 5][col] = bottom_color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("constructed invalid OR lesson: " + "; ".join(errors))
    expected = {
        "grid_w": width,
        "top_color": top_color,
        "bot_color": bottom_color,
        "sep_color": separator_color,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"override observation mismatch: expected {expected}, got {observed}")
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
            if type(value) is not int or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        return normalized, [f"cells must be integer ARC colors 0..9, got {invalid}"]
    return normalized, []


def _relation_histogram(grid: Grid, width: int) -> dict[str, int]:
    counts = {relation: 0 for relation in _RELATIONS}
    for row in range(4):
        for col in range(width):
            top = grid[row][col] != 0
            bottom = grid[row + 5][col] != 0
            relation = (
                "both" if top and bottom
                else "top_only" if top
                else "bottom_only" if bottom
                else "neither"
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
    if height != 9:
        errors.append(f"input height must be 9, got {height}")
        return info, errors
    if not 3 <= width <= 14:
        errors.append(f"width must be 3..14, got {width}")

    separator_values = set(normalized[4])
    info["separator_values"] = separator_values
    if len(separator_values) != 1:
        errors.append(f"separator row must be uniform, got {sorted(separator_values)}")
        separator_color = None
    else:
        separator_color = next(iter(separator_values))
        if separator_color == 0:
            errors.append("separator color must be nonzero")
    info["sep_color"] = separator_color

    top_colors = {
        normalized[row][col]
        for row in range(4)
        for col in range(width)
        if normalized[row][col] != 0
    }
    bottom_colors = {
        normalized[row + 5][col]
        for row in range(4)
        for col in range(width)
        if normalized[row + 5][col] != 0
    }
    info.update({"top_colors": top_colors, "bottom_colors": bottom_colors})
    if len(top_colors) != 1:
        errors.append(f"top panel must use exactly one nonzero color, got {sorted(top_colors)}")
    if len(bottom_colors) != 1:
        errors.append(
            "bottom panel must use exactly one nonzero color, got "
            f"{sorted(bottom_colors)}"
        )

    counts = _relation_histogram(normalized, width)
    info["relation_counts"] = counts
    missing = [relation for relation in _RELATIONS if counts[relation] == 0]
    if missing:
        errors.append(
            "aligned occupancy truth table is incomplete; missing " + ", ".join(missing)
        )
    return info, errors


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover all exact public controls from returned pixels."""
    info, errors = _analyse(grid)
    if errors:
        return {}
    return {
        "grid_w": info["grid_w"],
        "top_color": next(iter(info["top_colors"])),
        "bot_color": next(iter(info["bottom_colors"])),
        "sep_color": info["sep_color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-collapsed teaching scenes."""
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    _, errors = _analyse(grid)
    errors = list(errors)
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """Canonical and generated examples share the same strict grammar."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def rule_mirror(grid: Any) -> Grid:
    """Independent Python audit mirror; canonical Racket remains authoritative."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized, width = info["grid"], info["grid_w"]
    return [
        [
            3
            if normalized[row][col] != 0 or normalized[row + 5][col] != 0
            else 0
            for col in range(width)
        ]
        for row in range(4)
    ]


def _rival_copy_top(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [[3 if g[row][col] != 0 else 0 for col in range(width)] for row in range(4)]


def _rival_copy_bottom(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [3 if g[row + 5][col] != 0 else 0 for col in range(width)]
        for row in range(4)
    ]


def _rival_and(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [
            3 if g[row][col] != 0 and g[row + 5][col] != 0 else 0
            for col in range(width)
        ]
        for row in range(4)
    ]


def _rival_xor(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [
            3 if bool(g[row][col]) != bool(g[row + 5][col]) else 0
            for col in range(width)
        ]
        for row in range(4)
    ]


def _rival_constant_filled(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return full_grid(4, info["grid_w"], 3)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "copy_top": _rival_copy_top,
    "copy_bottom": _rival_copy_bottom,
    "and": _rival_and,
    "xor": _rival_xor,
    "constant_filled": _rival_constant_filled,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _relation_witness(relation: str):
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["relation_counts"][relation] > 0

    return predicate


SEMANTIC_WITNESSES = {
    "top_only": _relation_witness("top_only"),
    "bottom_only": _relation_witness("bottom_only"),
    "overlap": _relation_witness("both"),
    "empty": _relation_witness("neither"),
}
WITNESS_RIVALS = {
    "top_only": ["copy_bottom", "and"],
    "bottom_only": ["copy_top", "and"],
    "overlap": ["xor"],
    "empty": ["constant_filled"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    killed = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not the separated-panel occupancy OR")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(pair["input"]) != expected:
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
