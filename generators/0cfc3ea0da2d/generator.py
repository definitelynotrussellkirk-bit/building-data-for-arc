"""Generator for v0_original:medium_05 — recolor by global frequency rank.

The canonical transformation is global and geometry-independent:

1. Count every nonzero color over the whole grid.
2. Sort colors by descending total count; break ties by the smaller color.
3. Recolor rank 1 to 1, rank 2 to 2, and so on, preserving every position.

The curriculum deliberately includes four scheduled lesson profiles.  Four
consecutive examples therefore expose all decisive semantics: the canonical
4/2/1 profile, a top-frequency tie, an all-frequency tie, and a split-color
counterexample where total frequency disagrees with largest component size.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "0cfc3ea0da2d"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d3e7de6ab51b"  # sha256[:12] of normalized canonical program_solution
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains 2..5 nonzero colors. The global total cell "
    "counts follow one of four explicit frequency profiles, including ties. "
    "Rank colors by descending total count, breaking ties by smaller color, "
    "then replace every cell of rank k with k. Geometry and component count "
    "are distractors: one scheduled profile splits the most frequent color "
    "into two components so largest-component ranking gives the wrong answer."
)

INVARIANTS = [
    "background 0 is present",
    "2..5 distinct nonzero colors are present",
    "the frequency profile is one of the four declared observable profiles",
    "the rank mapping changes at least one cell (ordinary lessons are not identity)",
    "component geometry never changes the global-frequency rule",
]

FREQUENCY_PATTERNS = (
    "canonical_desc",
    "top_tie",
    "all_tie",
    "split_trap",
)
COMPONENT_PATTERNS = ("single", "split_top")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 4..11; scheduled canonical profile uses 4",
        "valid": "4..11",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 5..13; scheduled canonical profile uses 5 or 6",
        "valid": "5..13",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware 2..5; scheduled canonical profile uses 3",
        "valid": "2..5",
    },
    "frequency_pattern": {
        "type": "str",
        "default": "sample_index schedule over all four profiles",
        "valid": "|".join(FREQUENCY_PATTERNS),
    },
    "component_pattern": {
        "type": "str",
        "default": "single except scheduled split_trap profile",
        "valid": "|".join(COMPONENT_PATTERNS),
    },
}

# The five axes are independent.  An explicit empty declaration is different
# from an undeclared legacy policy: the override checker may falsify this claim
# if any Cartesian combination is ever refused.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Four consecutive sample indexes cover every semantic profile."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _scheduled_defaults(sample_index: int, seed: int) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index)
    if profile == 0:
        return {
            "grid_h": 4,
            "grid_w": 5 + ((seed + sample_index) & 1),
            "n_colors": 3,
            "frequency_pattern": "canonical_desc",
            "component_pattern": "single",
        }
    if profile == 1:
        return {
            "frequency_pattern": "top_tie",
            "component_pattern": "single",
        }
    if profile == 2:
        return {
            "frequency_pattern": "all_tie",
            "component_pattern": "single",
        }
    return {
        "frequency_pattern": "split_trap",
        "component_pattern": "split_top",
    }


def _frequency_counts(pattern: str, n_colors: int) -> list[int]:
    if pattern == "canonical_desc":
        table = {
            2: [3, 1],
            3: [4, 2, 1],
            4: [4, 3, 2, 1],
            5: [5, 4, 3, 2, 1],
        }
    elif pattern == "top_tie":
        table = {
            2: [3, 3],
            3: [4, 4, 1],
            4: [4, 4, 2, 1],
            5: [4, 4, 3, 2, 1],
        }
    elif pattern == "all_tie":
        table = {n: [2] * n for n in range(2, 6)}
    elif pattern == "split_trap":
        # The top total is split into components of at most 3 cells while the
        # second color remains one 4-cell component. Largest-component ranking
        # therefore puts the wrong color first.
        table = {
            2: [6, 4],
            3: [6, 4, 1],
            4: [6, 4, 2, 1],
            5: [6, 4, 3, 2, 1],
        }
    else:  # validated before use; retain a loud defensive branch.
        raise ValueError(f"unknown frequency_pattern {pattern!r}")
    return list(table[n_colors])


def _snake_cells(h: int, w: int, rng) -> list[tuple[int, int]]:
    rows = list(range(h))
    if rng.random() < 0.5:
        rows.reverse()
    cells: list[tuple[int, int]] = []
    reverse_first = rng.random() < 0.5
    for index, r in enumerate(rows):
        cols = list(range(w))
        if bool(index & 1) ^ reverse_first:
            cols.reverse()
        cells.extend((r, c) for c in cols)
    if rng.random() < 0.5:
        cells.reverse()
    return cells


def _choose_palette(rng, n_colors: int, pattern: str) -> list[int]:
    palette = list(random_palette(rng, n_colors))

    # Ensure at least one source color lies outside 1..n, which makes an
    # accidental identity mapping impossible without sacrificing low colors.
    if set(palette) == set(range(1, n_colors + 1)):
        replacement = next(c for c in range(n_colors + 1, 10) if c not in palette)
        palette[-1] = replacement

    if pattern == "top_tie":
        # The tied colors appear in the opposite order from the mandated
        # smaller-color tiebreak, refuting a reading-order tie resolution.
        if palette[0] < palette[1]:
            palette[0], palette[1] = palette[1], palette[0]
    elif pattern == "all_tie":
        if palette == sorted(palette):
            palette[0], palette[1] = palette[1], palette[0]
    else:
        # Distinct frequencies must not collapse to a color-value ranking.
        if palette == sorted(palette):
            palette[0], palette[1] = palette[1], palette[0]
    return palette


def _ranked_colors_from_counts(counts: Counter[int]) -> list[int]:
    return sorted(counts, key=lambda color: (-counts[color], color))


def _component_cells(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        q = deque([start])
        cells = [start]
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    q.append(nxt)
                    cells.append(nxt)
        components.append(cells)
    return components


def _paint_profile(
    h: int,
    w: int,
    palette: list[int],
    counts: list[int],
    component_pattern: str,
    rng,
) -> list[list[int]]:
    total = sum(counts)
    capacity = h * w
    if total >= capacity:
        raise ValueError(
            f"frequency profile needs {total} colored cells but {h}x{w} "
            "must retain at least one background cell"
        )

    path = _snake_cells(h, w, rng)
    grid = full_grid(h, w, 0)

    if component_pattern == "single":
        cursor = 0
        for color, count in zip(palette, counts):
            for r, c in path[cursor : cursor + count]:
                grid[r][c] = color
            cursor += count
        return grid

    if component_pattern != "split_top":
        raise ValueError(f"unknown component_pattern {component_pattern!r}")

    totals = Counter(dict(zip(palette, counts)))
    top_color = _ranked_colors_from_counts(totals)[0]
    top_index = palette.index(top_color)
    top_count = counts[top_index]
    first_count = top_count // 2
    second_count = top_count - first_count
    first_cells = path[:first_count]
    second_cells = path[-second_count:]
    for r, c in first_cells + second_cells:
        grid[r][c] = top_color

    middle = path[first_count : capacity - second_count]
    cursor = 0
    for index, (color, count) in enumerate(zip(palette, counts)):
        if index == top_index:
            continue
        for r, c in middle[cursor : cursor + count]:
            grid[r][c] = color
        cursor += count
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    effective = _scheduled_defaults(sample_index, seed)
    effective.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h = ctx.draw_int_diff("grid_h", 4, 11)
    w = ctx.draw_int_diff("grid_w", 5, 13)
    n_colors = ctx.draw_int_diff("n_colors", 2, 5)
    frequency_pattern = ctx.draw_choice("frequency_pattern", FREQUENCY_PATTERNS)
    component_pattern = ctx.draw_choice("component_pattern", COMPONENT_PATTERNS)

    counts = _frequency_counts(frequency_pattern, n_colors)
    palette = _choose_palette(ctx.draw_rng("palette"), n_colors, frequency_pattern)
    grid = _paint_profile(
        h,
        w,
        palette,
        counts,
        component_pattern,
        ctx.draw_rng("layout"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced an invalid lesson: " + "; ".join(errors))
    return grid


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]
    normalized: list[list[int]] = []
    for row in grid:
        normalized_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 9):
                return None, [f"cell value {value!r} is not an ARC color 0..9"]
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized, []


def _infer_frequency_pattern(counts: Counter[int]) -> str | None:
    n_colors = len(counts)
    if n_colors not in range(2, 6):
        return None
    observed = sorted(counts.values(), reverse=True)
    for pattern in FREQUENCY_PATTERNS:
        if observed == sorted(_frequency_counts(pattern, n_colors), reverse=True):
            return pattern
    return None


def semantic_observables(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    h = len(normalized)
    w = len(normalized[0])
    counts = Counter(v for row in normalized for v in row if v != 0)
    colors = sorted(counts)
    if not counts:
        return {
            "errors": ["no nonzero colors"],
            "grid_h": h,
            "grid_w": w,
            "n_colors": 0,
        }

    ranked = _ranked_colors_from_counts(counts)
    first_seen: list[int] = []
    for row in normalized:
        for value in row:
            if value != 0 and value not in first_seen:
                first_seen.append(value)

    components = {color: _component_cells(normalized, color) for color in colors}
    component_counts = {color: len(parts) for color, parts in components.items()}
    largest_components = {
        color: max((len(part) for part in parts), default=0)
        for color, parts in components.items()
    }
    if all(value == 1 for value in component_counts.values()):
        component_pattern = "single"
    elif component_counts.get(ranked[0], 0) >= 2 and all(
        component_counts[color] == 1 for color in colors if color != ranked[0]
    ):
        component_pattern = "split_top"
    else:
        component_pattern = None

    mapping = {color: rank for rank, color in enumerate(ranked, start=1)}
    output = [
        [0 if value == 0 else mapping[value] for value in row]
        for row in normalized
    ]
    return {
        "errors": [],
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "n_colors": len(colors),
        "colors": colors,
        "counts": dict(counts),
        "ranked_colors": ranked,
        "first_seen_colors": first_seen,
        "component_counts": component_counts,
        "largest_components": largest_components,
        "frequency_pattern": _infer_frequency_pattern(counts),
        "component_pattern": component_pattern,
        "rule_output": output,
        "identity": output == normalized,
        "has_background": any(value == 0 for row in normalized for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    obs = semantic_observables(grid)
    errors = list(obs.get("errors", []))
    if errors:
        return errors
    if not (4 <= obs["grid_h"] <= 11 and 5 <= obs["grid_w"] <= 13):
        errors.append(
            f"grid dimensions {obs['grid_h']}x{obs['grid_w']} outside 4..11 by 5..13"
        )
    if not obs["has_background"]:
        errors.append("background 0 is absent")
    if not (2 <= obs["n_colors"] <= 5):
        errors.append(f"need 2..5 nonzero colors, got {obs['n_colors']}")
    if obs["frequency_pattern"] is None:
        errors.append(
            "nonzero frequency multiset is outside the declared teaching profiles"
        )
    if obs["component_pattern"] is None:
        errors.append(
            "same-color components are neither all single nor a split of only the top-ranked color"
        )
    if obs["identity"]:
        errors.append("frequency-rank recoloring would be an identity transformation")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted lesson is a direct instance of the canonical global rule."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(obs["errors"]))
    return {
        "grid_h": obs["grid_h"],
        "grid_w": obs["grid_w"],
        "n_colors": obs["n_colors"],
        "frequency_pattern": obs["frequency_pattern"],
        "component_pattern": obs["component_pattern"],
    }


def _recolor_by_order(grid: Any, ordered_colors: list[int]) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if errors or normalized is None:
        raise ValueError("; ".join(errors))
    mapping = {color: rank for rank, color in enumerate(ordered_colors, start=1)}
    return [
        [0 if value == 0 else mapping[value] for value in row]
        for row in normalized
    ]


def rule_mirror(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return [row[:] for row in obs["rule_output"]]


def _identity(grid: Any) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if errors or normalized is None:
        raise ValueError("; ".join(errors))
    return [row[:] for row in normalized]


def _rank_by_color_value(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return _recolor_by_order(grid, sorted(obs["colors"]))


def _rank_by_first_seen(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return _recolor_by_order(grid, list(obs["first_seen_colors"]))


def _rank_by_largest_component(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    ordered = sorted(
        obs["colors"],
        key=lambda color: (-obs["largest_components"][color], color),
    )
    return _recolor_by_order(grid, ordered)


def _rank_ascending_frequency(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    ordered = sorted(obs["colors"], key=lambda color: (obs["counts"][color], color))
    return _recolor_by_order(grid, ordered)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "rank_by_color_value": _rank_by_color_value,
    "rank_by_first_seen": _rank_by_first_seen,
    "rank_by_largest_component": _rank_by_largest_component,
    "rank_ascending_frequency": _rank_ascending_frequency,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid: Any, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _canonical_421(grid: Any) -> bool:
    obs = semantic_observables(grid)
    return (
        not obs.get("errors")
        and obs["grid_h"] == 4
        and obs["grid_w"] in (5, 6)
        and sorted(obs["counts"].values(), reverse=True) == [4, 2, 1]
    )


SEMANTIC_WITNESSES = {
    "canonical_421_refutes_identity": lambda grid: (
        _canonical_421(grid) and _rival_differs(grid, "identity")
    ),
    "frequency_refutes_color_value_order": lambda grid: _rival_differs(
        grid, "rank_by_color_value"
    ),
    "tie_break_refutes_first_seen": lambda grid: (
        len(set(semantic_observables(grid).get("counts", {}).values()))
        < semantic_observables(grid).get("n_colors", 0)
        and _rival_differs(grid, "rank_by_first_seen")
    ),
    "total_frequency_refutes_largest_component": lambda grid: _rival_differs(
        grid, "rank_by_largest_component"
    ),
    "descending_rank_refutes_ascending_rank": lambda grid: _rival_differs(
        grid, "rank_ascending_frequency"
    ),
}

WITNESS_RIVALS = {
    "canonical_421_refutes_identity": ["identity"],
    "frequency_refutes_color_value_order": ["rank_by_color_value"],
    "tie_break_refutes_first_seen": ["rank_by_first_seen"],
    "total_frequency_refutes_largest_component": ["rank_by_largest_component"],
    "descending_rank_refutes_ascending_rank": ["rank_ascending_frequency"],
}

# Every canonical pair has one component per color and introduces colors in
# descending-frequency order, so these wrong rules fit all canonical examples.
# Generated scheduled counterexamples above are therefore required evidence.
CANONICAL_SHORTCUTS = {
    "rank_by_first_seen": _rank_by_first_seen,
    "rank_by_largest_component": _rank_by_largest_component,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        check = self_check(demo["input"])
        if check:
            reasons.append(f"demo {index} is outside the teaching grammar: {check}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with global frequency rank")
    query_check = self_check(query["input"])
    if query_check:
        reasons.append(f"query is outside the teaching grammar: {query_check}")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
            else:
                reasons.append(
                    f"competitor {name!r} survives every demo and the query"
                )
    return reasons
