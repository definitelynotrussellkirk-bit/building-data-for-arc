"""Generator for ARC task f76d97a5 / ef02aedbac38.

A lawful input is a two-color pattern: color 5 and one other ARC color X.
The oracle copies the positions occupied by 5, recolors those positions X, and
writes 0 everywhere else.  A deterministic 30% schedule emits the four linked
canonical pattern morphologies (up to D4 symmetry and color renaming) in every
difficulty band.  The remaining draws use controlled multi-component patterns;
every four-sample window contains both sparse and dense novel color-5 masks, so
the curriculum rebuts literal-mask, density-role, fixed-color, count-only, and
largest-component shortcuts without changing the rule.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef02aedbac38"
TASK_ID = "ef02aedbac38"
VERSION = "4.1.0"
RULE_HASH = "0e568f927b22"

SUMMARY = (
    "Create a rectangular 3..25 grid containing color 5 and exactly one other "
    "nonzero color X.  Both colors occupy at least two cells and the binary "
    "pattern has at least three 4-connected color components, excluding "
    "rule-hiding monochrome, singleton, and single-bar scenes.  The output "
    "places X exactly where the input contains 5 and places 0 everywhere "
    "else.  Thirty percent of default draws reproduce a canonical pattern "
    "morphology up to rotation/reflection and color renaming; the remainder "
    "are controlled multi-component generalizations whose four-sample windows "
    "contain both sparse and dense novel color-5 masks."
)

INVARIANTS = [
    "grid is rectangular with height and width in 3..25",
    "palette is exactly {5, X}, where X is in 1..9 and X != 5",
    "each color appears at least twice",
    "the two-color scene has at least three 4-connected color components",
    "each color spans at least two rows and two columns",
]

# Only answer-bearing values that can be recovered exactly from a returned
# grid are declared as axes.  Pattern morphology is an internal curriculum
# schedule, not a caller-visible override.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "30% canonical profile; otherwise difficulty-aware",
        "valid": "3..25",
    },
    "grid_w": {
        "type": "int",
        "default": "30% canonical profile; otherwise difficulty-aware",
        "valid": "3..25",
    },
    "other_color": {
        "type": "color",
        "default": "sample-index schedule over legal colors",
        "valid": "1..4,6..9",
    },
}

MIN_STRICT_FRAC = 0.20
EXAMPLES_NEEDED = 4

# Every official input, encoded only by the positions of color 5.  Color is a
# lawful nuisance variable.  The morphology comparison below quotients by the
# task-preserving D4 symmetries but not by translation or arbitrary reshaping.
_CANONICAL_MASK_ROWS = (
    (
        "##...",
        ".##..",
        "..##.",
        "...##",
        "#...#",
    ),
    (
        ".#.",
        "###",
        ".#.",
    ),
    (
        ".#...",
        "..##.",
        ".#...",
        "..#..",
        "...##",
    ),
    (
        "...#.",
        ".#...",
        ".##.#",
        "...#.",
        "###..",
    ),
)
_LEGAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CANONICAL_RESIDUES = (0, 4, 8)


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer (not bool), got {seed!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError(
            "sample_index must be a non-negative integer (not bool), "
            f"got {sample_index!r}"
        )
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard', "
            f"got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "other_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and not 3 <= value <= 25:
            raise ValueError(f"{name} must be in 3..25")
    color = overrides.get("other_color")
    if color is not None and color not in _LEGAL_COLORS:
        raise ValueError("other_color must be one of 1,2,3,4,6,7,8,9")


def _rows_to_mask(rows: tuple[str, ...]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(rows)
        for col, value in enumerate(values)
        if value == "#"
    }


def _transform_cell(row: int, col: int, size: int, code: int) -> tuple[int, int]:
    """Apply one of the eight D4 transforms to a square-grid coordinate."""
    if code >= 4:
        col = size - 1 - col  # reflect vertically, then rotate
        code -= 4
    for _ in range(code):
        row, col = col, size - 1 - row
    return row, col


def _transform_mask(
    mask: set[tuple[int, int]], size: int, code: int
) -> set[tuple[int, int]]:
    return {_transform_cell(row, col, size, code) for row, col in mask}


def _mask_bits(mask: set[tuple[int, int]], height: int, width: int) -> tuple[int, ...]:
    return tuple(
        int((row, col) in mask)
        for row in range(height)
        for col in range(width)
    )


def _orbit_signature(mask: set[tuple[int, int]], size: int) -> tuple[int, ...]:
    return min(_mask_bits(_transform_mask(mask, size, code), size, size) for code in range(8))


_CANONICAL_SIGNATURES = {
    (len(rows), _orbit_signature(_rows_to_mask(rows), len(rows)))
    for rows in _CANONICAL_MASK_ROWS
}


def _neighbors(row: int, col: int, height: int, width: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _component_sets(
    cells: set[tuple[int, int]], height: int, width: int
) -> list[set[tuple[int, int]]]:
    unseen = set(cells)
    out: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        comp = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for nxt in _neighbors(row, col, height, width):
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        out.append(comp)
    return out


def _grid_facts(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"error": "grid must be a non-empty sequence of rows"}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"error": "rows must be non-empty sequences"}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"error": "grid must be rectangular"}
    height = len(grid)
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        return {"error": "cells must be integer ARC colors in 0..9"}
    values = set(flat)
    others = sorted(value for value in values if value != 5)
    other = others[0] if len(others) == 1 else None
    five_cells = {
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if value == 5
    }
    other_cells = {
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if other is not None and value == other
    }
    five_components = _component_sets(five_cells, height, width) if five_cells else []
    other_components = _component_sets(other_cells, height, width) if other_cells else []
    return {
        "height": height,
        "width": width,
        "values": values,
        "other": other,
        "five_cells": five_cells,
        "other_cells": other_cells,
        "five_components": five_components,
        "other_components": other_components,
        "component_total": len(five_components) + len(other_components),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed and rule-hiding scenes outside the maintained grammar."""
    facts = _grid_facts(grid)
    if "error" in facts:
        return [facts["error"]]
    errors = []
    height, width = facts["height"], facts["width"]
    if not 3 <= height <= 25 or not 3 <= width <= 25:
        errors.append("grid dimensions must both be in 3..25")
    if facts["values"] != {5, facts["other"]} or facts["other"] not in _LEGAL_COLORS:
        errors.append("palette must be exactly {5, X} with X in 1,2,3,4,6,7,8,9")
        return errors
    if len(facts["five_cells"]) < 2 or len(facts["other_cells"]) < 2:
        errors.append("each color must occupy at least two cells")
    if facts["component_total"] < 3:
        errors.append(
            "scene must contain at least three 4-connected color components; "
            "singletons and one-bar partitions hide the intended pattern rule"
        )
    for name, cells in (("color 5", facts["five_cells"]), ("other color", facts["other_cells"])):
        if cells:
            rows = {row for row, _ in cells}
            cols = {col for _, col in cells}
            if len(rows) < 2 or len(cols) < 2:
                errors.append(f"{name} must span at least two rows and two columns")
    return errors


def _draw_other_color(ctx, seed: int, sample_index: int) -> int:
    if ctx.overrides.get("other_color") is not None:
        return ctx.draw_color("other_color", exclude={0, 5})
    color = _LEGAL_COLORS[(seed + sample_index) % len(_LEGAL_COLORS)]
    return ctx.draw_choice("other_color", [color])


def _record_fixed_dimension(ctx, label: str, value: int) -> int:
    return ctx.draw_int(label, value, value)


def _mask_partition_errors(
    mask: set[tuple[int, int]], height: int, width: int
) -> list[str]:
    probe = full_grid(height, width, 1)
    for row, col in mask:
        probe[row][col] = 5
    return self_check(probe)


def _canonical_mask(seed: int, sample_index: int, rng) -> tuple[int, set[tuple[int, int]]]:
    rows = _CANONICAL_MASK_ROWS[(seed + sample_index) % len(_CANONICAL_MASK_ROWS)]
    size = len(rows)
    mask = _rows_to_mask(rows)
    return size, _transform_mask(mask, size, rng.randrange(8))


def _general_mask(height: int, width: int, rng, sample_index: int) -> set[tuple[int, int]]:
    """Build 2..5 separated components, growing some without merging them."""
    max_components = max(2, min(5, (height * width - 2 + 1) // 2))
    target = min(2 + sample_index % 4, max_components)
    candidates = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(candidates)
    components: list[set[tuple[int, int]]] = []
    occupied: set[tuple[int, int]] = set()

    for _ in range(target):
        seed_cell = next(
            (
                cell
                for cell in candidates
                if cell not in occupied
                and all(neighbor not in occupied for neighbor in _neighbors(*cell, height, width))
            ),
            None,
        )
        if seed_cell is None:
            seed_cell = next((cell for cell in candidates if cell not in occupied), None)
        if seed_cell is None:
            break
        component = {seed_cell}
        occupied.add(seed_cell)
        components.append(component)

    # Grow selected components by at most two cells.  A candidate may touch its
    # own component but never another one, preserving the intended component
    # count and keeping the morphology interpretable.
    max_five = max(2, height * width - 2)
    for index, component in enumerate(components):
        steps = (sample_index + index) % 3
        for _ in range(steps):
            if len(occupied) >= max_five:
                break
            frontier = []
            for row, col in sorted(component):
                for cell in _neighbors(row, col, height, width):
                    if cell in occupied:
                        continue
                    touches_other = any(
                        neighbor in occupied and neighbor not in component
                        for neighbor in _neighbors(*cell, height, width)
                    )
                    if not touches_other:
                        frontier.append(cell)
            if not frontier:
                break
            cell = rng.choice(sorted(set(frontier)))
            component.add(cell)
            occupied.add(cell)

    mask = set().union(*components) if components else set()
    if len(mask) < 2:
        mask = {(0, 0), (height - 1, width - 1)}
    # A one-row or one-column mark is a rule-hiding bar. Add a separated
    # witness cell so both coordinates visibly matter.
    rows = {row for row, _ in mask}
    cols = {col for _, col in mask}
    if len(rows) < 2 or len(cols) < 2:
        anchor_row, anchor_col = next(iter(mask))
        repair = (
            height - 1 if anchor_row == 0 else 0,
            width - 1 if anchor_col == 0 else 0,
        )
        mask.add(repair)
    if height * width - len(mask) < 2:
        # This can only matter on the smallest grids; remove deterministic
        # interior-most cells until two X cells remain.
        for cell in sorted(mask, key=lambda rc: (abs(rc[0] - height / 2) + abs(rc[1] - width / 2), rc), reverse=True):
            if height * width - len(mask) >= 2:
                break
            mask.remove(cell)

    # The mask-side span repair above is not sufficient by itself: on a 3x3
    # grid it can leave the complement as a complete single row or column.
    # Repair the two-color partition, not merely one side of it.  A one-cell
    # move preserves almost all sampled morphology; the fixed fallback is a
    # total, lawful construction for every supported size.
    if _mask_partition_errors(mask, height, width):
        all_cells = {
            (row, col) for row in range(height) for col in range(width)
        }
        for cell in sorted(mask):
            candidate = mask - {cell}
            if not _mask_partition_errors(candidate, height, width):
                return candidate
        for cell in sorted(all_cells - mask):
            candidate = mask | {cell}
            if not _mask_partition_errors(candidate, height, width):
                return candidate
        fallback = {(0, 0), (0, 1), (height - 1, width - 1)}
        fallback_errors = _mask_partition_errors(fallback, height, width)
        if fallback_errors:
            raise AssertionError(
                f"cannot construct a lawful general partition: {fallback_errors}"
            )
        return fallback
    return mask


def _orient_general_mask(
    mask: set[tuple[int, int]],
    height: int,
    width: int,
    *,
    dense: bool,
) -> set[tuple[int, int]]:
    """Choose which side of a lawful partition is color 5.

    General examples deliberately alternate the foreground/background density
    role.  Complementing a mask preserves the partition geometry and every
    symmetric self-check invariant.  Exact half-and-half partitions need one
    deterministic cell move before they can express a strict role.
    """
    all_cells = {(row, col) for row in range(height) for col in range(width)}
    area = height * width

    if 2 * len(mask) == area:
        bases = (mask, all_cells - mask)
        for base in bases:
            movable = sorted(all_cells - base) if dense else sorted(base)
            for cell in movable:
                candidate = base | {cell} if dense else base - {cell}
                if not _mask_partition_errors(candidate, height, width):
                    mask = candidate
                    break
            else:
                continue
            break
        else:
            raise AssertionError("cannot orient an equal-density lawful partition")

    is_dense = 2 * len(mask) > area
    if is_dense != dense:
        mask = all_cells - mask
    return mask


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    pattern_rng = ctx.draw_rng("pattern")

    # Spaced residues make the canonical prior stable in every 200-draw band
    # and in disjoint seed ranges.  Any explicit override exits this branch so
    # a requested value is never silently ignored.
    if not overrides and sample_index % 10 in _CANONICAL_RESIDUES:
        size, mask = _canonical_mask(seed, sample_index, pattern_rng)
        height = _record_fixed_dimension(ctx, "grid_h", size)
        width = _record_fixed_dimension(ctx, "grid_w", size)
    else:
        band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
        ranges = {"easy": (3, 5), "medium": (4, 6), "hard": (5, 7)}
        lo, hi = ranges[band]
        if ctx.overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", 3, 25)
        else:
            h_residue = sample_index % 20
            h_default = 25 if h_residue == 1 else 3 if h_residue == 2 else pattern_rng.randint(lo, hi)
            height = _record_fixed_dimension(ctx, "grid_h", h_default)
        if ctx.overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", 3, 25)
        else:
            w_residue = sample_index % 20
            w_default = 25 if w_residue == 3 else 3 if w_residue == 5 else pattern_rng.randint(lo, hi)
            width = _record_fixed_dimension(ctx, "grid_w", w_default)
        mask = _general_mask(height, width, pattern_rng, sample_index)
        # Odd residue 1 never collides with the even canonical residues.  Thus
        # every four consecutive samples contain one dense novel mask (r=1)
        # and one sparse novel mask (r=3), independent of seed or band.
        mask = _orient_general_mask(
            mask,
            height,
            width,
            dense=sample_index % 4 == 1,
        )

    other = _draw_other_color(ctx, seed, sample_index)
    grid = full_grid(height, width, other)
    for row, col in mask:
        grid[row][col] = 5

    # Defensive construction assertion: a source change must fail at the point
    # of generation rather than leak an off-grammar training example.
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator error: {errors}")
    return grid


def observe_overrides(grid):
    """Recover every exact declared axis from the returned grid itself."""
    facts = _grid_facts(grid)
    if "error" in facts:
        return {}
    observed = {"grid_h": facts["height"], "grid_w": facts["width"]}
    if facts["other"] in _LEGAL_COLORS:
        observed["other_color"] = facts["other"]
    return observed


def _rule_mirror(grid):
    facts = _grid_facts(grid)
    if facts.get("other") not in _LEGAL_COLORS:
        raise ValueError("rule mirror requires exactly one legal non-5 color")
    other = facts["other"]
    return [[other if value == 5 else 0 for value in row] for row in grid]


def strict_canonical_like(grid):
    """[] iff morphology matches an official input up to D4 and color rename."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _grid_facts(grid)
    if facts["height"] != facts["width"] or facts["height"] not in (3, 5):
        return ["canonical inputs are square with side length 3 or 5"]
    signature = (
        facts["height"],
        _orbit_signature(facts["five_cells"], facts["height"]),
    )
    if signature not in _CANONICAL_SIGNATURES:
        return ["color-5 morphology is not in the four official D4 orbits"]
    return []


def _rival_fixed_six(grid):
    return [[6 if value == 5 else 0 for value in row] for row in grid]


def _rival_row_major_count(grid):
    facts = _grid_facts(grid)
    other = facts["other"]
    count = len(facts["five_cells"])
    width = facts["width"]
    return [
        [other if row * width + col < count else 0 for col in range(width)]
        for row in range(facts["height"])
    ]


def _rival_largest_five_component(grid):
    facts = _grid_facts(grid)
    other = facts["other"]
    components = facts["five_components"]
    largest = max(components, key=lambda comp: (len(comp), sorted(comp)), default=set())
    return [
        [other if (row, col) in largest else 0 for col in range(facts["width"])]
        for row in range(facts["height"])
    ]


def _rival_four_mask_lookup(grid):
    # A deliberately plausible archival shortcut: memorize the four official
    # mask orbits and emit all-zero output for every unseen morphology.
    if not strict_canonical_like(grid):
        return _rule_mirror(grid)
    facts = _grid_facts(grid)
    return full_grid(facts["height"], facts["width"], 0)


def _rival_sparse_or_canonical_lookup(grid):
    """Generalize the official rule only to sparse color-5 masks.

    This fits every canonical pair: three masks are sparse and the one dense
    mask is an official morphology that can be memorized.  It disagrees only
    on dense, noncanonical masks, the counterexample class added in v4.1.
    """
    facts = _grid_facts(grid)
    is_sparse_or_tied = len(facts["five_cells"]) <= len(facts["other_cells"])
    is_official_morphology = not strict_canonical_like(grid)
    if is_sparse_or_tied or is_official_morphology:
        return _rule_mirror(grid)
    return full_grid(facts["height"], facts["width"], 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_output_color_6": _rival_fixed_six,
    "row_major_count_only": _rival_row_major_count,
    "largest_five_component_only": _rival_largest_five_component,
    "four_canonical_mask_lookup": _rival_four_mask_lookup,
    "sparse_or_canonical_lookup": _rival_sparse_or_canonical_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "four_canonical_mask_lookup": _rival_four_mask_lookup,
    "sparse_or_canonical_lookup": _rival_sparse_or_canonical_lookup,
}


def _lawful_disagreement(grid, rival):
    return not self_check(grid) and rival(grid) != _rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "kills_fixed_output_color_6": lambda grid: _lawful_disagreement(grid, _rival_fixed_six),
    "kills_row_major_count_only": lambda grid: _lawful_disagreement(grid, _rival_row_major_count),
    "kills_largest_component_only": lambda grid: _lawful_disagreement(grid, _rival_largest_five_component),
    "kills_four_mask_lookup": lambda grid: _lawful_disagreement(grid, _rival_four_mask_lookup),
    "kills_sparse_or_canonical_lookup": lambda grid: _lawful_disagreement(
        grid, _rival_sparse_or_canonical_lookup
    ),
}
WITNESS_RIVALS = {
    "kills_fixed_output_color_6": ["fixed_output_color_6"],
    "kills_row_major_count_only": ["row_major_count_only"],
    "kills_largest_component_only": ["largest_five_component_only"],
    "kills_four_mask_lookup": ["four_canonical_mask_lookup"],
    "kills_sparse_or_canonical_lookup": ["sparse_or_canonical_lookup"],
}


def lesson_identifiable(demos, query):
    """Require every query-relevant rival to be killed by at least one demo."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson must contain at least one demonstration"]
    checked = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        if self_check(demo["input"]):
            return [f"demo {index} input is off-grammar"]
        expected = _rule_mirror(demo["input"])
        if demo["output"] != expected:
            return [f"demo {index} output does not match the canonical rule"]
        checked.append(demo)
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    if self_check(query["input"]):
        return ["query input is off-grammar"]
    authoritative_query = _rule_mirror(query["input"])

    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if competitor(query["input"]) == authoritative_query:
            continue
        if not any(competitor(demo["input"]) != demo["output"] for demo in checked):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
