"""Constructive generator for ARC task a3a85fedfec1 (Priority Sprouts).

The first row is a left-to-right priority legend.  Every nonzero body cell is
an isolated seed that grows a Manhattan-radius-one plus in the output after the
legend row is removed.  Where pluses overlap, the earlier legend color wins.

Ordinary generated inputs contain an explicit chain of conflicts between every
adjacent pair of priority ranks.  Alternating sample indices reverse both the
numeric priority order and the body scan order, preventing three-example
lessons from being solved by numeric-min/max or row-first/last shortcuts.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3a85fedfec1"
TASK_ID = GENERATOR_ID
RULE_HASH = "f96ecacc4b71"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
MIN_STRICT_FRAC = 0.04

SUMMARY = (
    "A top-row legend orders two or three colors; isolated body seeds grow "
    "radius-one pluses after the legend is dropped, and overlaps are painted "
    "by legend priority. Every generated scene exposes each adjacent priority "
    "comparison, while alternating samples reverse plausible scan/numeric "
    "shortcuts."
)

INVARIANTS = [
    "background is 0 and every cell is a literal ARC integer color 0..9",
    "row 0 contains 2 or 3 distinct nonzero colors whose column order is priority order",
    "the body contains 3..6 nonzero seeds, all colored from the priority legend",
    "every priority color appears in the body",
    "no two body seeds are Manhattan-adjacent",
    "each adjacent pair of priority ranks has seeds at Manhattan distance 2",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware full-domain draw",
        "valid": "8..12",
        "doc": "Full input-grid height, including the priority row.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware full-domain draw",
        "valid": "9..13",
        "doc": "Full input-grid width.",
    },
    "n_priority": {
        "type": "int",
        "default": "difficulty-aware 2..3",
        "valid": "2..3",
        "doc": "Number of distinct priority colors in row 0.",
    },
    "n_seeds": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
        "doc": "Number of nonzero body seeds.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = ("ascending_scan_forward", "descending_scan_reverse")

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_BOUNDS = {
    "grid_h": (8, 12),
    "grid_w": (9, 13),
    "n_priority": (2, 3),
    "n_seeds": (3, 6),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Report the shortcut-breaking parity profile for audit tooling."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(
    seed: int,
    sample_index: int,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be a literal integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _priority_colors(ctx, n_priority: int, sample_index: int) -> list[int]:
    """Choose a color set, then schedule ascending/descending priority."""
    rng = ctx.draw_rng("priority_colors")
    colors = sorted(rng.sample(range(1, 10), n_priority))
    if sample_index % LESSON_SCHEDULE_PERIOD:
        colors.reverse()
    return colors


def _chain_positions(
    *,
    body_h: int,
    width: int,
    n_priority: int,
    sample_index: int,
    rng,
) -> list[tuple[int, int]]:
    """Return output-coordinate positions spaced exactly two cells apart.

    Even samples place rank 0 first in row-major order; odd samples place rank
    0 last.  Orientation alternates every two samples for geometric variety.
    """
    vertical = (sample_index // LESSON_SCHEDULE_PERIOD) % 2 == 1
    span = 2 * (n_priority - 1)
    if vertical:
        start_row = rng.randint(1, body_h - 2 - span)
        col = rng.randint(1, width - 2)
        scan_order = [(start_row + 2 * rank, col) for rank in range(n_priority)]
    else:
        row = rng.randint(1, body_h - 2)
        start_col = rng.randint(1, width - 2 - span)
        scan_order = [(row, start_col + 2 * rank) for rank in range(n_priority)]
    return scan_order if sample_index % LESSON_SCHEDULE_PERIOD == 0 else list(reversed(scan_order))


def _extra_positions(
    *,
    body_h: int,
    width: int,
    occupied: list[tuple[int, int]],
    count: int,
    rng,
) -> list[tuple[int, int]]:
    """Construct `count` seeds at distance >=3 from all existing seeds."""
    if count == 0:
        return []
    candidates = [
        (row, col)
        for row in range(1, body_h - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)

    def search(
        remaining: list[tuple[int, int]],
        chosen: list[tuple[int, int]],
    ) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return chosen
        need = count - len(chosen)
        for index, cell in enumerate(remaining):
            if len(remaining) - index < need:
                break
            if all(
                abs(cell[0] - other[0]) + abs(cell[1] - other[1]) >= 3
                for other in (*occupied, *chosen)
            ):
                result = search(remaining[index + 1 :], [*chosen, cell])
                if result is not None:
                    return result
        return None

    found = search(candidates, [])
    if found is None:
        raise ValueError(
            f"could not place {count} extra seeds in {body_h}x{width} body"
        )
    return found


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic input grid; the runner applies the Racket rule."""
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", *_AXIS_BOUNDS["grid_h"])
    width = ctx.draw_int_diff("grid_w", *_AXIS_BOUNDS["grid_w"])
    n_priority = ctx.draw_int_diff("n_priority", *_AXIS_BOUNDS["n_priority"])
    n_seeds = ctx.draw_int_diff("n_seeds", *_AXIS_BOUNDS["n_seeds"])
    if n_seeds < n_priority:  # Defensive if bounds are edited independently.
        raise ValueError("n_seeds must be at least n_priority")

    priority = _priority_colors(ctx, n_priority, sample_index)
    header_rng = ctx.draw_rng("header_columns")
    header_columns = sorted(header_rng.sample(range(width), n_priority))

    body_h = height - 1
    layout_rng = ctx.draw_rng("teaching_layout")
    positions = _chain_positions(
        body_h=body_h,
        width=width,
        n_priority=n_priority,
        sample_index=sample_index,
        rng=layout_rng,
    )
    extras = _extra_positions(
        body_h=body_h,
        width=width,
        occupied=positions,
        count=n_seeds - n_priority,
        rng=layout_rng,
    )

    grid = full_grid(height, width, 0)
    for column, color in zip(header_columns, priority):
        grid[0][column] = color
    for (row, column), color in zip(positions, priority):
        grid[row + 1][column] = color
    for extra_index, (row, column) in enumerate(extras):
        color_rng = ctx.draw_rng(f"extra_color_{extra_index}")
        grid[row + 1][column] = color_rng.choice(priority)

    errors = teaching_check(grid)
    if errors:  # Constructive generation should make this unreachable.
        raise AssertionError("constructed invalid priority-sprouts grid: " + "; ".join(errors))
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any, *, require_teaching: bool = True) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not _AXIS_BOUNDS["grid_h"][0] <= height <= _AXIS_BOUNDS["grid_h"][1]:
        errors.append(f"grid_h={height} outside [8, 12]")
    if not _AXIS_BOUNDS["grid_w"][0] <= width <= _AXIS_BOUNDS["grid_w"][1]:
        errors.append(f"grid_w={width} outside [9, 13]")

    priority = [value for value in grid[0] if value != 0]
    if not 2 <= len(priority) <= 3:
        errors.append(f"priority row must contain 2 or 3 colors, found {len(priority)}")
    if len(priority) != len(set(priority)):
        errors.append("priority row colors must be distinct")
    priority_set = set(priority)
    ranks = {color: rank for rank, color in enumerate(priority)}

    seeds = [
        (row - 1, col, grid[row][col])
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not 3 <= len(seeds) <= 6:
        errors.append(f"body must contain 3..6 seeds, found {len(seeds)}")
    unknown = sorted({color for _row, _col, color in seeds} - priority_set)
    if unknown:
        errors.append(f"body uses colors absent from priority row: {unknown}")
    missing = [color for color in priority if color not in {seed[2] for seed in seeds}]
    if missing:
        errors.append(f"priority colors missing from body: {missing}")

    adjacency_pairs: list[tuple[int, int]] = []
    rank_edges: set[tuple[int, int]] = set()
    for left_index, left in enumerate(seeds):
        for right_index, right in enumerate(seeds[left_index + 1 :], left_index + 1):
            distance = abs(left[0] - right[0]) + abs(left[1] - right[1])
            if distance <= 1:
                adjacency_pairs.append((left_index, right_index))
            if (
                distance == 2
                and left[2] != right[2]
                and left[2] in ranks
                and right[2] in ranks
            ):
                rank_edges.add(tuple(sorted((ranks[left[2]], ranks[right[2]]))))
    if adjacency_pairs:
        errors.append("body seeds must not be Manhattan-adjacent")

    required_edges = {
        (rank, rank + 1) for rank in range(max(0, len(priority) - 1))
    }
    missing_edges = sorted(required_edges - rank_edges)
    if require_teaching and missing_edges:
        errors.append(
            "missing visible conflict(s) between adjacent priority ranks: "
            + ", ".join(f"{left}-{right}" for left, right in missing_edges)
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "priority": priority,
        "ranks": ranks,
        "seeds": seeds,
        "rank_edges": rank_edges,
        "required_edges": required_edges,
        "missing_edges": missing_edges,
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    facts = _analysis(grid, require_teaching=False)
    if facts["errors"]:
        return {}
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_priority": len(facts["priority"]),
        "n_seeds": len(facts["seeds"]),
        "priority": tuple(facts["priority"]),
        "rank_edges": tuple(sorted(facts["rank_edges"])),
        "complete_priority_chain": not facts["missing_edges"],
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    facts = semantic_observables(grid)
    return {axis: facts[axis] for axis in AXES} if facts else {}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful task domain, including every canonical input."""
    del difficulty
    facts = _analysis(grid, require_teaching=False)
    errors = list(facts["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if requested is not None and name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def teaching_check(grid) -> list[str]:
    """Apply curriculum-only requirements beyond structural task validity."""
    return list(_analysis(grid, require_teaching=True)["errors"])

_CANONICAL_PROFILES = {
    (8, 9, 3, 3),
    (9, 10, 3, 4),
    (10, 9, 3, 4),
    (9, 11, 3, 4),
    (10, 10, 3, 4),
}


def strict_canonical_like(grid) -> list[str]:
    """Recognize the complete structural/profile envelope of the five examples."""
    facts = _analysis(grid, require_teaching=False)
    errors = list(facts["errors"])
    if errors:
        return errors
    profile = (
        facts["height"],
        facts["width"],
        len(facts["priority"]),
        len(facts["seeds"]),
    )
    height, width, n_priority, n_seeds = profile
    if not (
        8 <= height <= 10
        and 9 <= width <= 11
        and n_priority == 3
        and 3 <= n_seeds <= 4
    ):
        errors.append(f"profile {profile} is outside the canonical envelope")
    return errors


def _output_with_choice(grid, chooser) -> list[list[int]]:
    facts = _analysis(grid, require_teaching=False)
    if facts["errors"]:
        raise ValueError("invalid priority-sprouts grid: " + "; ".join(facts["errors"]))
    output = full_grid(facts["height"] - 1, facts["width"], 0)
    for row in range(facts["height"] - 1):
        for col in range(facts["width"]):
            covering = [
                seed
                for seed in facts["seeds"]
                if abs(seed[0] - row) + abs(seed[1] - col) <= 1
            ]
            if covering:
                output[row][col] = chooser(covering, facts["ranks"])
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket authority."""
    return _output_with_choice(
        grid,
        lambda covering, ranks: min(covering, key=lambda seed: ranks[seed[2]])[2],
    )


def _row_major_first_hit(grid) -> list[list[int]]:
    return _output_with_choice(grid, lambda covering, _ranks: covering[0][2])


def _row_major_last_hit(grid) -> list[list[int]]:
    return _output_with_choice(grid, lambda covering, _ranks: covering[-1][2])


def _numeric_min_color(grid) -> list[list[int]]:
    return _output_with_choice(
        grid, lambda covering, _ranks: min(seed[2] for seed in covering)
    )


def _numeric_max_color(grid) -> list[list[int]]:
    return _output_with_choice(
        grid, lambda covering, _ranks: max(seed[2] for seed in covering)
    )


SEMANTIC_RIVALS = {
    "row_major_first_hit": _row_major_first_hit,
    "row_major_last_hit": _row_major_last_hit,
    "numeric_min_color": _numeric_min_color,
    "numeric_max_color": _numeric_max_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of the four compact rivals fits all five canonical pairs.  They remain
# important lesson-level competitors because each can fit an unlucky subset.
CANONICAL_SHORTCUTS: dict[str, object] = {}


def _refutes(grid, rival_name: str) -> bool:
    try:
        return teaching_check(grid) == [] and rule_mirror(grid) != SEMANTIC_RIVALS[rival_name](grid)
    except (TypeError, ValueError, IndexError, KeyError):
        return False


SEMANTIC_WITNESSES = {
    "priority_not_row_major_first": lambda grid: _refutes(grid, "row_major_first_hit"),
    "priority_not_row_major_last": lambda grid: _refutes(grid, "row_major_last_hit"),
    "priority_not_numeric_min": lambda grid: _refutes(grid, "numeric_min_color"),
    "priority_not_numeric_max": lambda grid: _refutes(grid, "numeric_max_color"),
}
WITNESS_RIVALS = {
    "priority_not_row_major_first": ["row_major_first_hit"],
    "priority_not_row_major_last": ["row_major_last_hit"],
    "priority_not_numeric_min": ["numeric_min_color"],
    "priority_not_numeric_max": ["numeric_max_color"],
}


def _pair_errors(pair: Any, *, label: str, require_output: bool) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} is not an input/output pair"]
    if require_output and "output" not in pair:
        return [f"{label} has no output"]
    facts = _analysis(pair["input"], require_teaching=False)
    if facts["errors"]:
        return [f"{label} invalid: {'; '.join(facts['errors'])}"]
    if "output" in pair and rule_mirror(pair["input"]) != pair["output"]:
        return [f"{label} output disagrees with authority mirror"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that fit every demo but change the query output."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, label=f"demonstration {index}", require_output=True))
    errors.extend(_pair_errors(query, label="query", require_output=False))
    if errors:
        return errors

    query_output = query.get("output", rule_mirror(query["input"]))
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query_output:
            errors.append(
                f"competitor {name!r} fits every demo but changes the query"
            )
    return errors
