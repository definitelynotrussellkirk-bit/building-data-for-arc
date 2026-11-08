"""Semantic generator for ARC task 443eebb271d9.

The input contains one color-7 glyph.  Its bounding-box height and width set
the lattice period, with one blank row and column between copies.  The glyph
is repeated across its first lattice row; every third horizontal copy is
color 6 and is also repeated down all later lattice rows.  Everything else is
cleared.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "443eebb271d9"
TASK_ID = "443eebb271d9"
VERSION = "4.0.0"
RULE_HASH = "9a8ad7e4958a"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_connected",
    "disconnected_a",
    "general_connected",
    "disconnected_b",
)
SUMMARY = "Repeat a color-7 glyph across the top lattice row, recoloring every third column of copies to 6 and extending those columns downward."
INVARIANTS = [
    "the input has exactly one recognized color-7 glyph on a zero background",
    "the glyph bounding box determines both lattice periods, each with a one-cell gap",
    "the first lattice row contains every horizontal copy",
    "horizontal instances 2, 5, 8, ... are color 6 rather than color 7",
    "only those color-6 instance columns continue down later lattice rows",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "solid_square",
    "solid_rectangle",
    "hollow_square",
    "plus",
    "tee",
    "split_bar",
    "split_corner",
    "diagonal_cross",
    "aitch",
    "zigzag",
    "diamond",
    "stair",
    "asymmetric_branch",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
_LOW_FRAGMENTATION_PROFILES = ("split_bar", "split_corner")
_HIGH_FRAGMENTATION_PROFILES = ("public_3", "diagonal_cross", "diamond")
_DISCONNECTED_PROFILES = _LOW_FRAGMENTATION_PROFILES + _HIGH_FRAGMENTATION_PROFILES
_CONNECTED_PUBLIC_PROFILES = ("public_1", "public_2")
_CONNECTED_GENERAL_PROFILES = tuple(
    profile for profile in GENERAL_PROFILES if profile not in _DISCONNECTED_PROFILES
)
_SCHEDULE_OPTIONS = {
    "canonical_connected": _CONNECTED_PUBLIC_PROFILES,
    "disconnected_a": _LOW_FRAGMENTATION_PROFILES,
    "general_connected": _CONNECTED_GENERAL_PROFILES,
    "disconnected_b": _HIGH_FRAGMENTATION_PROFILES,
}
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and thirteen recoverable glyph lessons",
        "valid": "public_1|public_2|public_3|solid_square|solid_rectangle|hollow_square|plus|tee|split_bar|split_corner|diagonal_cross|aitch|zigzag|diamond|stair|asymmetric_branch",
    }
}

_PUBLIC_ROWS = (
    "0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0007770000000000000000000000/0007070000000000000000000000/0007770000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000",
    "0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000070700000000000000000000/0000070700000000000000000000/0000077700000000000000000000/0000070700000000000000000000/0000070700000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000",
    "0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0007000000000000000000000000/0007000000000000000000000000/0070700000000000000000000000/0007000000000000000000000000/0007000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000/0000000000000000000000000000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}

_GLYPH_ROWS = {
    "solid_square": ("11", "11"),
    "solid_rectangle": ("111", "111"),
    "hollow_square": ("111", "101", "111"),
    "plus": ("010", "111", "010"),
    "tee": ("111", "010", "010"),
    "split_bar": ("1101",),
    "split_corner": ("1100", "0001", "0001"),
    "diagonal_cross": ("101", "010", "101"),
    "aitch": ("101", "111", "101"),
    "zigzag": ("110", "011", "001"),
    "diamond": ("00100", "01010", "10001", "01010", "00100"),
    "stair": ("100", "110", "011", "001"),
    "asymmetric_branch": ("0100", "1110", "0100", "0111"),
}


def _cells_from_rows(rows):
    return tuple((row, col) for row, values in enumerate(rows) for col, value in enumerate(values) if value == "1")


_GLYPHS = {profile: _cells_from_rows(rows) for profile, rows in _GLYPH_ROWS.items()}
_NORMALIZED_PROFILES = {cells: profile for profile, cells in _GLYPHS.items()}


def _validate_call(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, string, or None)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _schedule_offset(seed):
    """Stable Gray-code seed rotation for the four-slot curriculum."""
    value = seed & ((1 << 64) - 1)
    return (value ^ (value >> 1)) % LESSON_SCHEDULE_PERIOD


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the seed-rotated deterministic four-slot curriculum branch."""
    _validate_call(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[
        (_schedule_offset(seed) + sample_index) % LESSON_SCHEDULE_PERIOD
    ]


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 11 <= len(grid) <= 30 or not 18 <= width <= 30:
        return ["input dimensions must be 11..30 rows and 18..30 columns"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 7) for row in grid for value in row):
        return ["input cells must be literal 0 or 7"]
    return []


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    cells = tuple((row, col) for row in range(height) for col in range(width) if grid[row][col] == 7)
    if not cells:
        return {"errors": ["one color-7 glyph is required"]}
    row0, col0, row1, col1 = _bbox(cells)
    glyph_h, glyph_w = row1 - row0 + 1, col1 - col0 + 1
    normalized = tuple(sorted((row - row0, col - col0) for row, col in cells))
    hstep, vstep = glyph_w + 1, glyph_h + 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(row0, height):
        for col in range(col0, width):
            rel_row, rel_col = row - row0, col - col0
            local_row, local_col = rel_row % vstep, rel_col % hstep
            instance, row_repeat = rel_col // hstep, rel_row // vstep
            if (local_row, local_col) in normalized and (row_repeat == 0 or instance % 3 == 2):
                output[row][col] = 6 if instance % 3 == 2 else 7
    return {
        "errors": [],
        "height": height,
        "width": width,
        "cells": cells,
        "bbox": (row0, col0, row1, col1),
        "glyph_height": glyph_h,
        "glyph_width": glyph_w,
        "normalized": normalized,
        "hstep": hstep,
        "vstep": vstep,
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _profile_for(grid, facts):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _NORMALIZED_PROFILES.get(facts["normalized"])


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    row0, col0, _, _ = facts["bbox"]
    if profile not in SCENE_PROFILES:
        errors.append("glyph does not match a declared semantic profile")
    if row0 < 1 or col0 < 1:
        errors.append("glyph needs a visible zero margin above and to its left")
    if col0 + 2 * facts["hstep"] + facts["glyph_width"] > facts["width"]:
        errors.append("canvas must expose the third horizontal instance")
    if row0 + facts["vstep"] + facts["glyph_height"] > facts["height"]:
        errors.append("canvas must expose a lower repeated instance")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("the lesson must visibly transform")
    output_colors = {value for row in facts["output"] for value in row}
    if not {0, 6, 7} <= output_colors:
        errors.append("output must visibly contain background, ordinary copies, and extended color-6 copies")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    return self_check(grid)


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, rng):
    bands = {
        None: ((17, 28), (22, 30)),
        "easy": ((13, 17), (20, 23)),
        "medium": ((18, 23), (24, 27)),
        "hard": ((24, 30), (28, 30)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _general_scene(difficulty, profile, rng):
    cells = _GLYPHS[profile]
    glyph_h = max(row for row, _ in cells) + 1
    glyph_w = max(col for _, col in cells) + 1
    for _ in range(100):
        height, width = _dimensions(difficulty, rng)
        max_row0 = height - (2 * glyph_h + 1)
        max_col0 = width - (3 * glyph_w + 2)
        if max_row0 < 1 or max_col0 < 1:
            continue
        row0 = rng.randint(1, max_row0)
        col0 = rng.randint(1, max_col0)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for row, col in cells:
            grid[row0 + row][col0 + col] = 7
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        profile = ctx.draw_choice(
            "scene_profile",
            _SCHEDULE_OPTIONS[schedule_profile(seed, sample_index, difficulty)],
        )
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))


# Pure competitor predictions below are never used as labels. The semantic
# gate and lesson census compare them against independently produced labels.
def _color_components(grid, color=7):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return components


def _largest_component_rival(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _color_components(grid)
    if not components:
        raise ValueError("one color-7 glyph is required")
    chosen = max(components, key=len)
    row0, col0, row1, col1 = _bbox(chosen)
    glyph_h, glyph_w = row1 - row0 + 1, col1 - col0 + 1
    normalized = {(row - row0, col - col0) for row, col in chosen}
    hstep, vstep = glyph_w + 1, glyph_h + 1
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(row0, height):
        for col in range(col0, width):
            rel_row, rel_col = row - row0, col - col0
            local = (rel_row % vstep, rel_col % hstep)
            instance, row_repeat = rel_col // hstep, rel_row // vstep
            if local in normalized and (row_repeat == 0 or instance % 3 == 2):
                output[row][col] = 6 if instance % 3 == 2 else 7
    return output


def _disconnected_source_witness(grid):
    try:
        return len(_color_components(grid)) > 1 and (
            _largest_component_rival(grid) != rule_mirror(grid)
        )
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS = {
    "largest_4_connected_component_only": _largest_component_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "disconnected_source_glyph": _disconnected_source_witness,
}
WITNESS_RIVALS = {
    "disconnected_source_glyph": ["largest_4_connected_component_only"],
}


def lesson_identifiable(demos, query):
    """Report declared rivals that fit all demonstrations but alter the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"unrefuted declared rival changes query: {name}")
    return reasons
