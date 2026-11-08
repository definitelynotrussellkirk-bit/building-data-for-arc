"""Generator for ARC task ce4f8723 / content hash 9c26c4b2c305.

The input contains two 4-row panels separated by one solid row.  The output is
the cellwise occupancy OR of the aligned panels, recolored green (3).  Ordinary
four-example windows deliberately expose all four aligned occupancy relations
(00, 10, 01, 11), canonical and noncanonical widths, canonical and shifted
palettes, an equal-panel-color palette, and inputs both with and without green.
This makes the intended OR rule distinguishable from top-only, bottom-only,
XOR, AND, color-conditional XOR, color-echo, solid-fill, fixed-width, and
fixed-palette shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c26c4b2c305"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "e9653f7b4ad7"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Split the 9-row input at its solid middle row into aligned 4-row top and "
    "bottom panels. For every aligned cell, output green (3) when either panel "
    "cell is nonzero; output black (0) only when both cells are black."
)

INVARIANTS = [
    "input height is 9: four top rows, one solid separator, four bottom rows",
    "each panel uses black plus one panel color and the separator is uniform nonzero",
    "ordinary lessons contain 00, top-only, bottom-only, and overlap relations",
    "the output is a nonempty, nonsolid 4-by-width occupancy OR mask in color 3",
    "every four consecutive samples cover all relation profiles, canonical/noncanonical cues, and equal panel colors",
]

RELATION_PROFILES = ("balanced", "top_heavy", "bottom_heavy", "overlap_heavy")
PALETTES = {
    "canonical_124": (1, 2, 4),
    "high_789": (7, 8, 9),
    "same_color_779": (7, 7, 9),
    "green_top_348": (3, 4, 8),
    "full_range_256": (2, 5, 6),
}
PALETTE_PROFILES = tuple(PALETTES)
SCHEDULE_PROFILES = (0, 1, 2, 3)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_w": {
        "type": "int",
        "default": "4 on schedule anchors; otherwise difficulty-banded 5..14",
        "valid": "4..14",
    },
    "relation_profile": {
        "type": "str",
        "default": "four-example balanced/top-heavy/bottom-heavy/overlap-heavy schedule",
        "valid": "balanced|top_heavy|bottom_heavy|overlap_heavy",
    },
    "palette_profile": {
        "type": "str",
        "default": "four-example canonical/same-color/green-top/full-range schedule",
        "valid": "canonical_124|high_789|same_color_779|green_top_348|full_range_256",
    },
}

Grid = list[list[int]]
_RELATIONS = ("00", "10", "01", "11")
_SLOT_RELATION = RELATION_PROFILES
_SLOT_PALETTE = ("canonical_124", "same_color_779", "green_top_348", "full_range_256")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Return the deterministic residue in the four-example lesson schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _draw_width(ctx, slot: int, band: str, overrides: dict[str, Any]) -> int:
    if overrides.get("grid_w") is not None:
        return ctx.draw_int_strict("grid_w", 4, 14)
    if slot in (0, 2):
        return int(ctx.draw_choice("grid_w", (4,)))
    ranges = {
        "easy": tuple(range(5, 8)),
        "medium": tuple(range(8, 11)),
        "hard": tuple(range(11, 15)),
    }
    return int(ctx.draw_choice("grid_w", ranges[band]))


def _draw_scheduled_choice(
    ctx, label: str, options: tuple[str, ...], scheduled: str, overrides: dict[str, Any]
) -> str:
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _relation_counts(width: int, profile: str) -> dict[str, int]:
    """Exact observable relation counts; every profile keeps every branch live."""
    total = 4 * width
    if profile == "balanced":
        base, remainder = divmod(total, 4)
        return {
            relation: base + (index < remainder)
            for index, relation in enumerate(_RELATIONS)
        }
    heavy = {
        "top_heavy": "10",
        "bottom_heavy": "01",
        "overlap_heavy": "11",
    }[profile]
    counts = {relation: 1 for relation in _RELATIONS}
    remaining = total - 4
    heavy_extra = max(1, remaining // 2)
    counts[heavy] += heavy_extra
    remaining -= heavy_extra
    others = [relation for relation in _RELATIONS if relation != heavy]
    for index in range(remaining):
        counts[others[index % len(others)]] += 1
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, semantically identifying input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

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
    width = _draw_width(ctx, slot, band, overrides)
    relation_profile = _draw_scheduled_choice(
        ctx,
        "relation_profile",
        RELATION_PROFILES,
        _SLOT_RELATION[slot],
        overrides,
    )
    palette_profile = _draw_scheduled_choice(
        ctx,
        "palette_profile",
        PALETTE_PROFILES,
        _SLOT_PALETTE[slot],
        overrides,
    )
    top_color, bottom_color, separator_color = PALETTES[palette_profile]

    relation_labels: list[str] = []
    for relation, count in _relation_counts(width, relation_profile).items():
        relation_labels.extend([relation] * count)
    rng = ctx.draw_rng("relation_layout")
    rng.shuffle(relation_labels)

    grid = full_grid(9, width, 0)
    grid[4] = [separator_color] * width
    for index, relation in enumerate(relation_labels):
        row, col = divmod(index, width)
        if relation[0] == "1":
            grid[row][col] = top_color
        if relation[1] == "1":
            grid[5 + row][col] = bottom_color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("constructed invalid OR lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_w": width,
        "relation_profile": relation_profile,
        "palette_profile": palette_profile,
    }
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
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        return normalized, [f"cells must be integer ARC colors 0..9, got {invalid}"]
    return normalized, []


def _panel_nonzero_colors(grid: Grid, rows: range) -> set[int]:
    return {grid[row][col] for row in rows for col in range(len(grid[0])) if grid[row][col]}


def _relation_histogram(grid: Grid) -> dict[str, int]:
    width = len(grid[0])
    counts = {relation: 0 for relation in _RELATIONS}
    for row in range(4):
        for col in range(width):
            relation = f"{int(grid[row][col] != 0)}{int(grid[5 + row][col] != 0)}"
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
        errors.append(f"expected height 9, got {height}")
        return info, errors
    if not 1 <= width <= 30:
        errors.append(f"width must be 1..30, got {width}")

    separator_values = set(normalized[4])
    if len(separator_values) != 1:
        errors.append(f"separator row must be uniform, got {sorted(separator_values)}")
        separator_color = None
    else:
        separator_color = next(iter(separator_values))
        if separator_color == 0:
            errors.append("separator row must be nonzero")

    top_colors = _panel_nonzero_colors(normalized, range(0, 4))
    bottom_colors = _panel_nonzero_colors(normalized, range(5, 9))
    if len(top_colors) != 1:
        errors.append(f"top panel must use exactly one nonzero color, got {sorted(top_colors)}")
    if len(bottom_colors) != 1:
        errors.append(f"bottom panel must use exactly one nonzero color, got {sorted(bottom_colors)}")

    counts = _relation_histogram(normalized)
    if counts["10"] + counts["01"] + counts["11"] == 0:
        errors.append("occupancy OR mask must contain at least one positive cell")
    if counts["00"] == 0:
        errors.append("occupancy OR mask must contain at least one negative cell")

    info.update(
        {
            "separator_color": separator_color,
            "top_colors": top_colors,
            "bottom_colors": bottom_colors,
            "relation_counts": counts,
        }
    )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the structural task grammar without assuming curriculum metadata."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    """Require the canonical structure plus all four rule-disambiguating relations."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    if not 4 <= info["grid_w"] <= 14:
        errors.append(f"lesson width must be 4..14, got {info['grid_w']}")
    missing = [name for name, count in info["relation_counts"].items() if count == 0]
    if missing:
        errors.append(f"lesson must expose all occupancy relations; missing {missing}")
    return errors


def _profile_from_counts(counts: dict[str, int]) -> str:
    values = list(counts.values())
    if max(values) - min(values) <= 1:
        return "balanced"
    leaders = [relation for relation in ("10", "01", "11") if counts[relation] == max(values)]
    if len(leaders) != 1:
        raise ValueError(f"relation counts do not identify one profile: {counts}")
    return {"10": "top_heavy", "01": "bottom_heavy", "11": "overlap_heavy"}[leaders[0]]


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if len(info["top_colors"]) != 1 or len(info["bottom_colors"]) != 1:
        raise ValueError("panel colors are not uniquely observable")
    palette = (
        next(iter(info["top_colors"])),
        next(iter(info["bottom_colors"])),
        info["separator_color"],
    )
    matching = [name for name, value in PALETTES.items() if value == palette]
    if len(matching) != 1:
        raise ValueError(f"palette tuple {palette} is not a declared palette profile")
    return {
        "grid_w": info["grid_w"],
        "relation_profile": _profile_from_counts(info["relation_counts"]),
        "palette_profile": matching[0],
    }


def rule_mirror(grid: Any) -> Grid:
    """Python audit mirror; the canonical Racket program remains authoritative."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized = info["grid"]
    width = info["grid_w"]
    return [
        [3 if normalized[row][col] or normalized[5 + row][col] else 0 for col in range(width)]
        for row in range(4)
    ]


def _rival_top_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [[3 if g[row][col] else 0 for col in range(width)] for row in range(4)]


def _rival_bottom_only(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [[3 if g[5 + row][col] else 0 for col in range(width)] for row in range(4)]


def _rival_xor(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [3 if bool(g[row][col]) != bool(g[5 + row][col]) else 0 for col in range(width)]
        for row in range(4)
    ]


def _rival_same_color_xor_otherwise_or(grid: Any) -> Grid:
    """Canonical-fitting shortcut: XOR only when both panels share a color."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    top_color = next(iter(info["top_colors"]))
    bottom_color = next(iter(info["bottom_colors"]))
    if top_color == bottom_color:
        return _rival_xor(grid)
    return rule_mirror(grid)


def _rival_and(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [3 if g[row][col] and g[5 + row][col] else 0 for col in range(width)]
        for row in range(4)
    ]


def _rival_constant_three(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return full_grid(4, info["grid_w"], 3)


def _rival_color_three_echo(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    g, width = info["grid"], info["grid_w"]
    return [
        [3 if g[row][col] == 3 or g[5 + row][col] == 3 else 0 for col in range(width)]
        for row in range(4)
    ]


def _rival_fixed_width_four(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["grid_w"] == 4:
        return rule_mirror(grid)
    return full_grid(4, info["grid_w"], 0)


def _rival_fixed_palette_124(grid: Any) -> Grid:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette = (
        next(iter(info["top_colors"])),
        next(iter(info["bottom_colors"])),
        info["separator_color"],
    )
    if palette == PALETTES["canonical_124"]:
        return rule_mirror(grid)
    return full_grid(4, info["grid_w"], 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "top_panel_only": _rival_top_only,
    "bottom_panel_only": _rival_bottom_only,
    "occupancy_xor": _rival_xor,
    "same_color_xor_otherwise_or": _rival_same_color_xor_otherwise_or,
    "occupancy_and": _rival_and,
    "constant_green_rectangle": _rival_constant_three,
    "input_green_echo": _rival_color_three_echo,
    "fixed_width_four": _rival_fixed_width_four,
    "fixed_palette_124": _rival_fixed_palette_124,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_width_four": _rival_fixed_width_four,
    "fixed_palette_124": _rival_fixed_palette_124,
    "same_color_xor_otherwise_or": _rival_same_color_xor_otherwise_or,
}


def _relation_witness(name: str):
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info["relation_counts"][name] > 0

    return predicate


def _off_width(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["grid_w"] != 4


def _off_palette(grid: Any) -> bool:
    try:
        return observe_overrides(grid)["palette_profile"] != "canonical_124"
    except ValueError:
        return False


def _same_panel_color(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["top_colors"] == info["bottom_colors"]


def _green_absent(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and all(3 not in row for row in info["grid"])


SEMANTIC_WITNESSES = {
    "top_only_relation": _relation_witness("10"),
    "bottom_only_relation": _relation_witness("01"),
    "overlap_relation": _relation_witness("11"),
    "both_empty_relation": _relation_witness("00"),
    "off_canonical_width": _off_width,
    "off_canonical_palette": _off_palette,
    "same_panel_color": _same_panel_color,
    "output_green_absent_from_input": _green_absent,
}
WITNESS_RIVALS = {
    "top_only_relation": ["bottom_panel_only", "occupancy_and"],
    "bottom_only_relation": ["top_panel_only", "occupancy_and"],
    "overlap_relation": ["occupancy_xor"],
    "both_empty_relation": ["constant_green_rectangle"],
    "off_canonical_width": ["fixed_width_four"],
    "off_canonical_palette": ["fixed_palette_124"],
    "same_panel_color": ["same_color_xor_otherwise_or"],
    "output_green_absent_from_input": ["input_green_echo"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to kill every named shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    widths: set[int] = set()
    palettes: set[str] = set()
    green_absent = False
    same_panel_color = False
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
        observed = observe_overrides(grid)
        widths.add(observed["grid_w"])
        palettes.add(observed["palette_profile"])
        green_absent = green_absent or _green_absent(grid)
        same_panel_color = same_panel_color or _same_panel_color(grid)
        for name, rival in LESSON_COMPETITORS.items():
            if rival(grid) != expected:
                killed[name] = True

    if 4 not in widths or not any(width != 4 for width in widths):
        reasons.append(f"demonstrations must include width 4 and a non-4 width, got {sorted(widths)}")
    if "canonical_124" not in palettes or len(palettes) < 2:
        reasons.append(f"demonstrations must include canonical and shifted palettes, got {sorted(palettes)}")
    if not green_absent:
        reasons.append("demonstrations need one positive output whose input contains no green")
    if not same_panel_color:
        reasons.append("demonstrations need one example whose panels use the same nonzero color")
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
