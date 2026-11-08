"""Semantic generator for ARC task 7447852a / bc0816632908.

The selected Racket rule treats color 2 as background, sorts every 4-connected
foreground component by its leftmost column, and recolors components 0, 3, 6,
... entirely to color 4.  The public examples use a very regular 3xN zigzag;
this generator keeps that manifold in the curriculum while adding irregular
multi-cell objects that refute fixed pixel masks, singleton-only reasoning, and
row-major ordering.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "bc0816632908"
VERSION = "3.0.0"
TASK_ID = "bc0816632908"
RULE_HASH = "6868d528f0b2"

SUMMARY = (
    "On a two-color grid, treat 2 as background and find the 4-connected "
    "color-0 components. Sort whole components by their leftmost column. "
    "Recolor every third component starting with the first (indices 0, 3, "
    "6, ...) completely to 4. The curriculum alternates the canonical 3-row "
    "zigzag with irregular multi-cell shapes and a row-order trap, so neither "
    "a fixed 3x12 pixel stencil nor 'every third black pixel' can solve it."
)

INVARIANTS = [
    "inputs use exactly colors 0 (foreground) and 2 (background)",
    "there are 6..13 distinct 4-connected color-0 components",
    "component leftmost columns are unique, so the intended sort is unambiguous",
    "at least four components are multi-cell objects",
    "indices 0, 3, 6, ... visibly require whole-component recoloring",
]

SCENE_PROFILES = (
    "canonical_zigzag",
    "shape_mix",
    "row_order_trap",
)
PROFILE_CYCLE = SCENE_PROFILES
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_WIDTHS = (10, 15, 18, 25)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "3-example deterministic cycle",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Negative fixtures do not belong to the ordinary generator domain.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25
MIN_CHANGE_RATE = 0.04

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Compact connected polyominoes.  Width <= 2 keeps 9 objects inside ARC's
# 30-column limit while still varying area, height, and topology.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0)),                         # vertical triomino
    ((0, 0), (1, 0), (1, 1)),                         # L triomino
    ((0, 0), (0, 1), (1, 1)),                         # mirrored L triomino
    ((0, 0), (1, 0), (2, 0), (2, 1)),                 # long L tetromino
    ((0, 0), (0, 1), (1, 0), (2, 0)),                 # mirrored long L
    ((0, 0), (1, 0), (1, 1), (2, 1)),                 # vertical zigzag
    ((0, 1), (1, 0), (1, 1), (2, 0)),                 # mirrored zigzag
    ((0, 0), (0, 1), (1, 0), (1, 1)),                 # square tetromino
    ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1)),         # C pentomino
    ((0, 0), (1, 0), (2, 0), (1, 1), (2, 1)),         # bent pentomino
)
_LARGE_SHAPE_INDICES = (3, 4, 5, 6, 8, 9)


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0:
        return None, ["grid rows may not be empty"]
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]
    converted: list[list[int]] = []
    for row_index, row in enumerate(grid):
        out_row: list[int] = []
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(
                    f"cell ({row_index},{col_index}) must be a literal integer"
                )
                continue
            if not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) has ARC color {value!r} outside 0..9"
                )
                continue
            out_row.append(value)
        converted.append(out_row)
    if errors:
        return None, errors
    return converted, []


def _zero_components(grid: Sequence[Sequence[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nxt = (cr + dr, cc + dc)
                    nr, nc = nxt
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return sorted(
        components,
        key=lambda cells: (
            min(col for _row, col in cells),
            min(row for row, _col in cells),
        ),
    )


def _paint_selected(
    grid: Sequence[Sequence[int]],
    components: Sequence[Sequence[tuple[int, int]]],
    selected_indices: Sequence[int],
) -> list[list[int]]:
    output = _copy_grid(grid)
    for index in selected_indices:
        for row, col in components[index]:
            output[row][col] = 4
    return output


def _canonical_zigzag(width: int) -> list[list[int]]:
    grid = full_grid(3, width, 0)
    for col in range(width):
        if col % 4 == 0:
            grid[0][col] = 2
        if col % 2 == 1:
            grid[1][col] = 2
        if col % 4 == 2:
            grid[2][col] = 2
    return grid


def _canonical_variants(width: int) -> tuple[list[list[int]], ...]:
    base = _canonical_zigzag(width)
    # Vertical reflection preserves the unique leftmost-column ordering.
    # Horizontal reflection does not for even widths: two edge fragments can
    # acquire the same leftmost column, making the canonical sort ambiguous.
    vertical = [list(row) for row in reversed(base)]
    return (base, vertical)


def _is_canonical_zigzag(grid: Sequence[Sequence[int]]) -> bool:
    if len(grid) != 3 or len(grid[0]) not in CANONICAL_WIDTHS:
        return False
    key = tuple(tuple(row) for row in grid)
    return any(
        key == tuple(tuple(row) for row in candidate)
        for candidate in _canonical_variants(len(grid[0]))
    )


def _has_top_inversion(
    components: Sequence[Sequence[tuple[int, int]]],
) -> bool:
    tops = [min(row for row, _col in cells) for cells in components]
    return any(left > right for left, right in zip(tops, tops[1:]))


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {
        "grid": converted,
        "errors": list(errors),
        "height": 0,
        "width": 0,
        "palette": set(),
        "components": [],
        "leftmost_columns": [],
        "scene_profile": None,
        "output": None,
        "changed_cells": set(),
    }
    if errors or converted is None:
        return facts

    height, width = len(converted), len(converted[0])
    palette = {value for row in converted for value in row}
    components = _zero_components(converted)
    leftmost = [min(col for _row, col in cells) for cells in components]
    selected = list(range(0, len(components), 3))
    output = _paint_selected(converted, components, selected)
    changed = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if converted[row][col] != output[row][col]
    }

    if _is_canonical_zigzag(converted):
        profile = "canonical_zigzag"
    elif _has_top_inversion(components):
        profile = "row_order_trap"
    else:
        profile = "shape_mix"

    facts.update(
        {
            "height": height,
            "width": width,
            "palette": palette,
            "components": components,
            "leftmost_columns": leftmost,
            "selected_indices": selected,
            "scene_profile": profile,
            "output": output,
            "changed_cells": changed,
        }
    )
    return facts


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival analysis."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _copy_grid(facts["output"])


def canonical_profile_signature(grid: Any) -> tuple[str, int] | None:
    facts = _analysis(grid)
    if facts["errors"] or facts["scene_profile"] != "canonical_zigzag":
        return None
    return ("canonical_zigzag", facts["width"])


def schedule_profile(
    seed: int,
    sample_index: int,
    difficulty: Any = None,
) -> str:
    del seed, difficulty
    return PROFILE_CYCLE[sample_index % len(PROFILE_CYCLE)]


def _validate_public_arguments(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in {"easy", "medium", "hard"}
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _difficulty_name(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    return difficulty


def _shape_size(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


def _profile_count(band: str, rng: Any) -> int:
    bounds = {
        "easy": (6, 7),
        "medium": (7, 8),
        "hard": (8, 9),
    }
    low, high = bounds[band]
    return rng.randint(low, high)


def _choose_shapes(count: int, rng: Any) -> list[tuple[tuple[int, int], ...]]:
    shapes: list[tuple[tuple[int, int], ...]] = []
    for index in range(count):
        pool = _LARGE_SHAPE_INDICES if index % 3 == 0 else tuple(range(len(_SHAPES)))
        chosen = _SHAPES[pool[rng.randrange(len(pool))]]
        shapes.append(chosen)
    # Ensure visible area variation rather than a repeated single template.
    if len({shape for shape in shapes}) == 1:
        shapes[-1] = _SHAPES[1]
    return shapes


def _top_rows(
    profile: str,
    shapes: Sequence[Sequence[tuple[int, int]]],
    height: int,
    rng: Any,
) -> list[int]:
    if profile == "shape_mix":
        # Monotone tops make this profile a clean control: left-to-right and
        # top-to-bottom agree here; the separate trap profile breaks that tie.
        tops: list[int] = []
        prior = 0
        for index, shape in enumerate(shapes):
            shape_h, _shape_w = _shape_size(shape)
            target = round(index * max(0, height - 3) / max(1, len(shapes) - 1))
            top = max(prior, min(target, height - shape_h))
            tops.append(top)
            prior = top
        return tops

    # The first selected component begins at row 3, column 0.  A fixed 3x12
    # pixel stencil leaves that anchor black, while the real rule recolors it.
    pattern = (3, 0, 4, 1, 3, 0, 4, 1, 3)
    tops = []
    for index, shape in enumerate(shapes):
        shape_h, _shape_w = _shape_size(shape)
        top = min(pattern[index % len(pattern)], height - shape_h)
        tops.append(max(0, top))
    # The fixed pattern is already non-monotone, but retain a deterministic
    # fallback in case a future shape bank changes height clipping.
    if not any(a > b for a, b in zip(tops, tops[1:])):
        tops[0], tops[1] = tops[1], tops[0]
    return tops


def _irregular_components(profile: str, band: str, rng: Any) -> list[list[int]]:
    count = _profile_count(band, rng)
    height = {"easy": 6, "medium": 7, "hard": 8}[band]
    shapes = _choose_shapes(count, rng)
    tops = _top_rows(profile, shapes, height, rng)

    # One mandatory background column separates neighboring components.
    # Up to two extra columns perturb the canonical six-column periodicity
    # without letting width exceed 30.
    gap_slots = list(range(1, count))
    rng.shuffle(gap_slots)
    extra_gap_slots = set(gap_slots[: min(2, max(0, count - 1))])

    placements: list[tuple[int, int, Sequence[tuple[int, int]]]] = []
    left = 0
    for index, (top, shape) in enumerate(zip(tops, shapes)):
        if index:
            left += 1 + (1 if index in extra_gap_slots else 0)
        placements.append((top, left, shape))
        _shape_h, shape_w = _shape_size(shape)
        left += shape_w
    width = left
    if width > 30:
        raise RuntimeError(f"internal layout exceeded ARC width: {width}")

    grid = full_grid(height, width, 2)
    for top, left, shape in placements:
        for dr, dc in shape:
            grid[top + dr][left + dc] = 0
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_public_arguments(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    band = _difficulty_name(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    choices = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", choices)
    rng = ctx.draw_rng("layout")

    if profile == "canonical_zigzag":
        width = CANONICAL_WIDTHS[rng.randrange(len(CANONICAL_WIDTHS))]
        variants = _canonical_variants(width)
        return _copy_grid(variants[rng.randrange(len(variants))])
    return _irregular_components(profile, band, rng)


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {"scene_profile": facts["scene_profile"]}


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: Any = None,
) -> list[str]:
    """Fail-closed structural grammar shared by generated and canonical inputs."""
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    height, width = facts["height"], facts["width"]
    components = facts["components"]
    palette = facts["palette"]
    leftmost = facts["leftmost_columns"]

    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC bounds: {height}x{width}")
    if height < 3 or width < 10:
        errors.append(f"grid is too small for this task grammar: {height}x{width}")
    if palette != {0, 2}:
        errors.append(f"input palette must be exactly {{0, 2}}, got {sorted(palette)}")
    if not 6 <= len(components) <= 13:
        errors.append(f"expected 6..13 foreground components, got {len(components)}")
    if len(leftmost) != len(set(leftmost)):
        errors.append("component leftmost columns must be unique")

    sizes = [len(component) for component in components]
    if sum(size > 1 for size in sizes) < 4:
        errors.append("at least four components must be multi-cell objects")
    if any(size > 6 for size in sizes):
        errors.append(f"component area exceeds compact task grammar: {sizes}")

    for index, component in enumerate(components):
        rows = [row for row, _col in component]
        cols = [col for _row, col in component]
        box_h = max(rows) - min(rows) + 1
        box_w = max(cols) - min(cols) + 1
        if box_h > 4 or box_w > 3:
            errors.append(
                f"component {index} has oversized bounding box {box_h}x{box_w}"
            )

    selected = [components[index] for index in range(0, len(components), 3)]
    unselected = [
        components[index]
        for index in range(len(components))
        if index % 3 != 0
    ]
    if not any(len(component) > 1 for component in selected):
        errors.append("a selected component must require multi-cell recoloring")
    if not any(len(component) > 1 for component in unselected):
        errors.append("an unselected multi-cell component must remain black")

    change_rate = len(facts["changed_cells"]) / (height * width)
    if change_rate < MIN_CHANGE_RATE:
        errors.append(
            f"intended transformation is too faint: {change_rate:.1%} < {MIN_CHANGE_RATE:.1%}"
        )

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and observed.get(axis) != requested[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as "
                        f"{observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        return errors
    if not _is_canonical_zigzag(converted):
        return [
            "not one of the authoritative 3-row zigzag profiles "
            f"with widths {CANONICAL_WIDTHS}"
        ]
    return self_check(converted)


# ---------------------------------------------------------------------------
# Plausible rival rules and falsifiable semantic witnesses
# ---------------------------------------------------------------------------


def fixed_periodic_stencil(grid: Any) -> list[list[int]]:
    """Strongest canonical shortcut: a fixed 3x12 row/column pixel mask."""
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    output = _copy_grid(converted)
    for row, values in enumerate(converted):
        for col, value in enumerate(values):
            if value != 0:
                continue
            row_phase = row % 3
            col_phase = col % 12
            selected = (
                (row_phase == 0 and col_phase in {5, 6, 7})
                or (row_phase == 1 and col % 6 == 0)
                or (row_phase == 2 and col_phase in {11, 0, 1})
            )
            if selected:
                output[row][col] = 4
    return output


def selected_anchor_only(grid: Any) -> list[list[int]]:
    """Wrong singleton shortcut: recolor one anchor, not the whole object."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = _copy_grid(facts["grid"])
    for index in range(0, len(facts["components"]), 3):
        row, col = min(facts["components"][index])
        output[row][col] = 4
    return output


def row_major_third(grid: Any) -> list[list[int]]:
    """Wrong order: sort components by top row before leftmost column."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    ordered = sorted(
        facts["components"],
        key=lambda cells: (
            min(row for row, _col in cells),
            min(col for _row, col in cells),
        ),
    )
    return _paint_selected(facts["grid"], ordered, range(0, len(ordered), 3))


def phase_one_third(grid: Any) -> list[list[int]]:
    """Wrong phase: select indices 1, 4, 7, ... instead of 0, 3, 6, ..."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _paint_selected(
        facts["grid"], facts["components"], range(1, len(facts["components"]), 3)
    )


def size_rank_third(grid: Any) -> list[list[int]]:
    """Wrong key: sort by component area, then position."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    ordered = sorted(
        facts["components"],
        key=lambda cells: (
            len(cells),
            min(col for _row, col in cells),
        ),
    )
    return _paint_selected(facts["grid"], ordered, range(0, len(ordered), 3))


def _identity(grid: Any) -> list[list[int]]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    return _copy_grid(converted)


def _whole_component_witness(grid: Any) -> bool:
    facts = _analysis(grid)
    return (
        not facts["errors"]
        and any(
            len(facts["components"][index]) > 1
            for index in range(0, len(facts["components"]), 3)
        )
        and rule_mirror(grid) != selected_anchor_only(grid)
    )


def _periodic_shortcut_witness(grid: Any) -> bool:
    facts = _analysis(grid)
    return (
        not facts["errors"]
        and facts["scene_profile"] != "canonical_zigzag"
        and rule_mirror(grid) != fixed_periodic_stencil(grid)
    )


def _row_order_witness(grid: Any) -> bool:
    facts = _analysis(grid)
    return (
        not facts["errors"]
        and facts["scene_profile"] == "row_order_trap"
        and rule_mirror(grid) != row_major_third(grid)
    )


def _phase_witness(grid: Any) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and rule_mirror(grid) != phase_one_third(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "fixed_3x12_periodic_stencil": fixed_periodic_stencil,
    "selected_anchor_only": selected_anchor_only,
    "row_major_third": row_major_third,
    "phase_one_third": phase_one_third,
    "size_rank_third": size_rank_third,
}

CANONICAL_SHORTCUTS = {
    "fixed_3x12_periodic_stencil": fixed_periodic_stencil,
}

SEMANTIC_WITNESSES = {
    "whole_component_recolor": _whole_component_witness,
    "breaks_fixed_3x12_stencil": _periodic_shortcut_witness,
    "column_order_not_row_order": _row_order_witness,
    "phase_zero_visible": _phase_witness,
}

WITNESS_RIVALS = {
    "whole_component_recolor": ["selected_anchor_only"],
    "breaks_fixed_3x12_stencil": ["fixed_3x12_periodic_stencil"],
    "column_order_not_row_order": ["row_major_third"],
    "phase_zero_visible": ["phase_one_third"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(
    demos: Sequence[dict[str, Any]],
    query: dict[str, Any],
) -> list[str]:
    """Require a three-profile lesson and prove named rivals are eliminated."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    profiles: set[str] = set()
    normalized_demos: list[tuple[Any, list[list[int]]]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo:
            return [f"demonstration {index} must contain an input grid"]
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demonstration {index} is outside the task grammar: {findings[0]}")
            continue
        official = demo.get("output")
        expected = rule_mirror(demo["input"])
        if official is not None and official != expected:
            reasons.append(f"demonstration {index} output disagrees with the selected rule")
        normalized_demos.append((demo["input"], expected if official is None else official))
        profiles.add(_analysis(demo["input"])["scene_profile"])

    missing = set(SCENE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations omit scene profile(s): {sorted(missing)}")

    query_findings = self_check(query["input"])
    if query_findings:
        reasons.append(f"query is outside the task grammar: {query_findings[0]}")
        return reasons
    query_official = query.get("output")
    if query_official is None:
        query_official = rule_mirror(query["input"])

    for name, rival in LESSON_COMPETITORS.items():
        fits_all = all(rival(grid) == official for grid, official in normalized_demos)
        if fits_all and rival(query["input"]) != query_official:
            reasons.append(
                f"plausible rival {name!r} fits every demonstration but changes the query"
            )
    return reasons
