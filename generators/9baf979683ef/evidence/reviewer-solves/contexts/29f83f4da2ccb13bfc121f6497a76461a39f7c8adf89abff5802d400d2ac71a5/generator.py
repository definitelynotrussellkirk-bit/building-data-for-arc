"""Generator for ARC task 9baf979683ef: mirror across a colour-5 divider.

The canonical examples make two accidental rules look correct: the divider is
always the geometric midpoint and every input contains exactly five source
cells.  Production scenes therefore retain canonical dimensions/palettes while
moving the divider one column off centre and using six to eight source cells.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9baf979683ef"
TASK_ID = "9baf979683ef"
VERSION = "3.0.0"
RULE_HASH = "1fce392f92a1"

SUMMARY = (
    "A 0-background grid contains exactly one full-height grey (5) divider. "
    "All coloured source cells begin left of that divider. Copy every source "
    "cell to the same row at the equal-distance position on the right, keeping "
    "its colour and preserving the input. Production lessons include canonical "
    "7x11, 8x9, and 7x13 profiles plus larger profiles, and deliberately vary "
    "connected/scattered geometry, palette size, source count, and an off-centre "
    "divider so midpoint and exactly-five-cell shortcuts cannot solve a lesson."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all grid values are ARC colours 0..9",
    "there is exactly one full-height colour-5 divider and no stray 5",
    "all non-background, non-divider source cells lie left of the divider",
    "every reflected target is in bounds and empty in the input",
    "source geometry spans at least two divider distances",
]

PROFILE_SHAPES = {
    "canonical_7x11": (7, 11),
    "canonical_8x9": (8, 9),
    "canonical_7x13": (7, 13),
    "expanded_9x12": (9, 12),
    "expanded_10x15": (10, 15),
}

AXES = {
    "profile_kind": {
        "type": "str",
        "default": "weighted keyed draw with canonical profiles emphasized",
        "valid": "canonical_7x11|canonical_8x9|canonical_7x13|expanded_9x12|expanded_10x15",
    },
    "divider_side": {
        "type": "str",
        "default": "keyed left/right draw",
        "valid": "left|right",
    },
    "source_scale": {
        "type": "str",
        "default": "difficulty-weighted keyed draw",
        "valid": "six|seven|eight",
    },
    "source_palette": {
        "type": "str",
        "default": "weighted keyed draw; two colours emphasized",
        "valid": "mono|two|three|four",
    },
    "layout_kind": {
        "type": "str",
        "default": "keyed connected/scattered/mixed draw",
        "valid": "connected|scattered|mixed",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SOURCE_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_SOURCE_COUNTS = {"six": 6, "seven": 7, "eight": 8}
_PALETTE_COUNTS = {"mono": 1, "two": 2, "three": 3, "four": 4}
_COUNT_TO_SCALE = {value: key for key, value in _SOURCE_COUNTS.items()}
_COUNT_TO_PALETTE = {value: key for key, value in _PALETTE_COUNTS.items()}

_PROFILE_WEIGHTS = {
    "easy": (
        "canonical_7x11", "canonical_7x11", "canonical_7x11",
        "canonical_8x9", "canonical_8x9", "canonical_8x9",
        "canonical_7x13", "canonical_7x13", "canonical_7x13",
        "expanded_9x12", "expanded_10x15",
    ),
    "medium": (
        "canonical_7x11", "canonical_7x11", "canonical_7x11",
        "canonical_8x9", "canonical_8x9", "canonical_8x9",
        "canonical_7x13", "canonical_7x13", "canonical_7x13",
        "expanded_9x12", "expanded_9x12",
        "expanded_10x15", "expanded_10x15",
    ),
    "hard": (
        "canonical_7x11", "canonical_7x11",
        "canonical_8x9", "canonical_8x9",
        "canonical_7x13", "canonical_7x13",
        "expanded_9x12", "expanded_9x12", "expanded_9x12",
        "expanded_10x15", "expanded_10x15", "expanded_10x15",
    ),
}

_SCALE_WEIGHTS = {
    "easy": ("six", "six", "six", "seven", "eight"),
    "medium": ("six", "six", "seven", "seven", "eight", "eight"),
    "hard": ("six", "seven", "eight", "eight", "eight"),
}

_PALETTE_WEIGHTS = (
    "mono",
    "two", "two", "two", "two", "two", "two",
    "three",
    "four",
)
_LAYOUT_WEIGHTS = ("connected", "connected", "scattered", "scattered", "mixed", "mixed")

_CONNECTED_TEMPLATES = {
    6: ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    7: ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)),
    8: ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2), (4, 2)),
}


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _DIR4:
                nxt = row + drow, col + dcol
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _layout_name(cells: set[tuple[int, int]]) -> str | None:
    if not cells:
        return None
    components = _components(cells)
    if len(components) == 1:
        return "connected"
    if all(len(component) == 1 for component in components):
        return "scattered"
    return "mixed"


def _profile_name(height: int, width: int) -> str | None:
    for name, shape in PROFILE_SHAPES.items():
        if shape == (height, width):
            return name
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colours 0..9")

    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        errors.append(
            f"expected exactly one full-height colour-5 divider, got {divider_columns}"
        )
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "palette": {value for row in grid for value in row},
        }
    divider = divider_columns[0]
    stray_fives = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5 and col != divider
    ]
    if stray_fives:
        errors.append(f"colour 5 occurs outside the divider: {stray_fives[:4]}")

    source = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    }
    right_source = sorted((row, col) for row, col in source if col > divider)
    divider_source = sorted((row, col) for row, col in source if col == divider)
    if right_source:
        errors.append(f"source cells occur right of the divider: {right_source[:4]}")
    if divider_source:
        errors.append(f"non-divider colours occur in the divider column: {divider_source[:4]}")
    if not 5 <= len(source) <= 8:
        errors.append(f"source must contain 5-8 cells, got {len(source)}")

    source_colors = {grid[row][col] for row, col in source}
    if not 1 <= len(source_colors) <= 4:
        errors.append(f"source must use 1-4 colours, got {sorted(source_colors)}")
    if source and len({col for _, col in source}) < 2:
        errors.append("source must span at least two reflection distances")

    mirror_cells: set[tuple[int, int]] = set()
    for row, col in source:
        target_col = 2 * divider - col
        if not 0 <= target_col < width:
            errors.append(f"source reflection is out of bounds at {(row, target_col)}")
            continue
        target = row, target_col
        mirror_cells.add(target)
        if grid[row][target_col] != 0:
            errors.append(
                f"source reflection target {target} is not empty "
                f"(found {grid[row][target_col]})"
            )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": {value for row in grid for value in row},
        "divider": divider,
        "source": source,
        "source_colors": source_colors,
        "mirror_cells": mirror_cells,
        "layout_kind": _layout_name(source),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    candidate = nested if isinstance(nested, dict) else meta
    return {name: value for name, value in candidate.items() if name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concrete invariant violations; [] means a lawful task input."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str]:
    """Recover every declared exact axis directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    divider = analysis["divider"]
    midpoint = analysis["width"] // 2
    divider_side = "center"
    if divider < midpoint:
        divider_side = "left"
    elif divider > midpoint:
        divider_side = "right"
    return {
        "profile_kind": _profile_name(analysis["height"], analysis["width"]) or "other",
        "divider_side": divider_side,
        "source_scale": _COUNT_TO_SCALE.get(len(analysis["source"]), "five"),
        "source_palette": _COUNT_TO_PALETTE.get(len(analysis["source_colors"]), "other"),
        "layout_kind": analysis["layout_kind"],
    }


def rule_mirror(grid):
    """Independent Python oracle for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid divider-reflection scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["source"]:
        output[row][2 * divider - col] = grid[row][col]
    return output


def strict_canonical_like(grid) -> list[str]:
    """Lawful teaching manifold containing all canonical and generated inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if _profile_name(analysis["height"], analysis["width"]) is None:
        reasons.append("grid shape is outside the retained canonical/expanded profiles")
    if abs(analysis["divider"] - analysis["width"] // 2) > 1:
        reasons.append("divider is more than one column from the geometric midpoint")
    if not 3 <= len(analysis["palette"]) <= 6:
        reasons.append("input palette should contain background, divider, and 1-4 source colours")
    return reasons


def _rival_midpoint(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    midpoint = analysis["width"] // 2
    for row, col in analysis["source"]:
        target_col = 2 * midpoint - col
        if 0 <= target_col < analysis["width"]:
            output[row][target_col] = grid[row][col]
    return output


def _rival_first_five(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    divider = analysis["divider"]
    for row, col in sorted(analysis["source"])[:5]:
        output[row][2 * divider - col] = grid[row][col]
    return output


def _witness_off_center(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["divider"] != analysis["width"] // 2


def _witness_more_than_five(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["source"]) > 5


def _witness_multiple_distances(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len({col for _, col in analysis["source"]}) >= 2


SEMANTIC_WITNESSES = {
    "off_center_divider": _witness_off_center,
    "more_than_five_source_cells": _witness_more_than_five,
    "multiple_reflection_distances": _witness_multiple_distances,
}

SEMANTIC_RIVALS = {
    "mirror_about_geometric_midpoint": _rival_midpoint,
    "mirror_only_first_five_sources": _rival_first_five,
}

WITNESS_RIVALS = {
    "off_center_divider": ("mirror_about_geometric_midpoint",),
    "more_than_five_source_cells": ("mirror_only_first_five_sources",),
    "multiple_reflection_distances": (
        "mirror_about_geometric_midpoint",
        "mirror_only_first_five_sources",
    ),
}

CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a canonical-fitting shortcut survives its demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match divider reflection")
    query_input = query["input"]
    query_answer = rule_mirror(query_input)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match divider reflection")
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair.get("output") for pair in demos)
        if survives and rival(query_input) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _connected_layout(
    height: int,
    legal_cols: tuple[int, ...],
    count: int,
    rng,
) -> set[tuple[int, int]]:
    template = _CONNECTED_TEMPLATES[count]
    template_height = max(row for row, _ in template) + 1
    template_width = max(col for _, col in template) + 1
    if len(legal_cols) < template_width or height < template_height:
        raise ValueError("profile is too small for connected source template")
    cells = list(template)
    if rng.randrange(2):
        cells = [(template_height - 1 - row, col) for row, col in cells]
    if rng.randrange(2):
        cells = [(row, template_width - 1 - col) for row, col in cells]
    top = rng.randrange(height - template_height + 1)
    left_index = rng.randrange(len(legal_cols) - template_width + 1)
    left = legal_cols[left_index]
    return {(top + row, left + col) for row, col in cells}


def _scattered_layout(
    height: int,
    legal_cols: tuple[int, ...],
    count: int,
    rng,
) -> set[tuple[int, int]]:
    for parity in (rng.randrange(2), 1 - rng.randrange(2)):
        candidates = [
            (row, col)
            for row in range(height)
            for col in legal_cols
            if (row + col) % 2 == parity
        ]
        if len(candidates) >= count:
            cells = set(rng.sample(candidates, count))
            if len({col for _, col in cells}) >= 2:
                return cells
    raise ValueError("profile is too small for scattered source layout")


def _mixed_layout(
    height: int,
    legal_cols: tuple[int, ...],
    count: int,
    rng,
) -> set[tuple[int, int]]:
    if height < 5 or len(legal_cols) < 2:
        raise ValueError("profile is too small for mixed source layout")
    remaining = count - 3
    attempts = []
    for at_top in (True, False):
        for at_left in (True, False):
            for parity in (0, 1):
                attempts.append((at_top, at_left, parity))
    rng.shuffle(attempts)
    for at_top, at_left, parity in attempts:
        top = 0 if at_top else height - 2
        left_index = 0 if at_left else len(legal_cols) - 2
        left = legal_cols[left_index]
        motif = {(top, left), (top + 1, left), (top + 1, left + 1)}
        candidates = [
            (row, col)
            for row in range(height)
            for col in legal_cols
            if (row, col) not in motif
            and (row + col) % 2 == parity
            and all(abs(row - mr) + abs(col - mc) > 1 for mr, mc in motif)
        ]
        if len(candidates) < remaining:
            continue
        isolated = set(rng.sample(candidates, remaining))
        cells = motif | isolated
        if _layout_name(cells) == "mixed" and len({col for _, col in cells}) >= 2:
            return cells
    raise ValueError("profile is too small for mixed source layout")


def _source_layout(
    kind: str,
    height: int,
    legal_cols: tuple[int, ...],
    count: int,
    rng,
) -> set[tuple[int, int]]:
    if kind == "connected":
        return _connected_layout(height, legal_cols, count, rng)
    if kind == "scattered":
        return _scattered_layout(height, legal_cols, count, rng)
    if kind == "mixed":
        return _mixed_layout(height, legal_cols, count, rng)
    raise ValueError(f"unknown layout kind: {kind!r}")


def _weighted_options(difficulty: str, table: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return table[difficulty]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile_kind", _weighted_options(band, _PROFILE_WEIGHTS))
    divider_side = ctx.draw_choice("divider_side", ("left", "right"))
    source_scale = ctx.draw_choice("source_scale", _weighted_options(band, _SCALE_WEIGHTS))
    source_palette = ctx.draw_choice("source_palette", _PALETTE_WEIGHTS)
    layout_kind = ctx.draw_choice("layout_kind", _LAYOUT_WEIGHTS)

    height, width = PROFILE_SHAPES[profile]
    divider = width // 2 + (-1 if divider_side == "left" else 1)
    legal_min = max(0, 2 * divider - (width - 1))
    legal_cols = tuple(range(legal_min, divider))
    count = _SOURCE_COUNTS[source_scale]
    color_count = _PALETTE_COUNTS[source_palette]

    layout_rng = ctx.draw_rng("source-layout")
    color_rng = ctx.draw_rng("source-colors")
    cells = _source_layout(layout_kind, height, legal_cols, count, layout_rng)

    colors = list(_SOURCE_COLORS)
    color_rng.shuffle(colors)
    colors = colors[:color_count]
    ordered_cells = sorted(cells)
    color_rng.shuffle(ordered_cells)
    assignments = colors + [color_rng.choice(colors) for _ in range(count - color_count)]
    color_rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5
    for (row, col), color in zip(ordered_cells, assignments, strict=True):
        grid[row][col] = color

    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise ValueError("internal generator invariant failure: " + "; ".join(errors))
    return grid
