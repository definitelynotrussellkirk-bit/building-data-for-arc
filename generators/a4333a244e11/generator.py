"""Two-seed Manhattan Voronoi inputs for ARC task a4333a244e11.

A one-cell black margin surrounds a rectangular color-8 frame.  Exactly two
interior seeds have distinct colors.  The selected Racket authority fills each
empty interior cell with the Manhattan-nearest seed color and leaves exact ties
black.  This module samples inputs only; ``rule_mirror`` is supplementary test
and semantic-contract tooling, not the label authority.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4333a244e11"
TASK_ID = GENERATOR_ID
RULE_HASH = "d568e0e496cf"
VERSION = "3.1.0"
SUMMARY = (
    "An inset color-8 rectangle contains exactly two distinct-colored seeds. "
    "Every empty interior cell takes the color of its Manhattan-nearest seed; "
    "cells tied between the seeds remain background.  Generated lessons vary "
    "frame size, palette, seed alignment, tie parity, and seed-color ordering."
)

INVARIANTS = [
    "the canvas has a one-cell background margin around one complete color-8 frame",
    "exactly two distinct-colored non-8 seeds occur in the frame interior",
    "all other input cells are background",
    "the output uses Manhattan distance and preserves exact ties as background",
]

PALETTES = {
    "canonical": (2, 3),
    "warm": (4, 9),
    "cool": (1, 6),
    "varied": (5, 7),
}
ALIGNMENTS = ("row", "column", "diagonal")
TIE_MODES = ("present", "absent")
COLOR_ORDERS = ("ascending", "descending")

AXES = {
    "frame_h": {"type": "int", "default": "scheduled/core plus broad", "valid": "5..10"},
    "frame_w": {"type": "int", "default": "scheduled/core plus broad", "valid": "7..14"},
    "palette_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "canonical|warm|cool|varied",
    },
    "alignment": {
        "type": "str",
        "default": "scheduled",
        "valid": "row|column|diagonal",
    },
    "tie_mode": {"type": "str", "default": "scheduled", "valid": "present|absent"},
    "color_order": {
        "type": "str",
        "default": "scheduled",
        "valid": "ascending|descending",
    },
}
# Every public-axis cross-product is constructive at every advertised dimension.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "diagonal_tie_descending",
    "diagonal_no_tie_ascending",
    "row_tie_descending",
    "column_tie_descending",
)
_PROFILE_CONFIG = {
    "diagonal_tie_descending": {
        "alignment": "diagonal",
        "tie_mode": "present",
        "color_order": "descending",
        "palette_kind": "canonical",
        "dimensions": (5, 9),
    },
    "diagonal_no_tie_ascending": {
        "alignment": "diagonal",
        "tie_mode": "absent",
        "color_order": "ascending",
        "palette_kind": "warm",
        "dimensions": (6, 10),
    },
    "row_tie_descending": {
        "alignment": "row",
        "tie_mode": "present",
        "color_order": "descending",
        "palette_kind": "cool",
        "dimensions": (7, 11),
    },
    "column_tie_descending": {
        "alignment": "column",
        "tie_mode": "present",
        "color_order": "descending",
        "palette_kind": "varied",
        "dimensions": None,
    },
}
_CANONICAL_FRAME_PROFILES = {(5, 9), (6, 10), (7, 11)}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Four-cycle whose every three-member subset refutes all named rivals."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("frame_h", "frame_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer, not {type(value).__name__}")
    for name in ("palette_kind", "alignment", "tie_mode", "color_order"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"override {name!r} must be a string, not {type(value).__name__}")


def _draw_public_int(ctx, label: str, lo: int, hi: int, options, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, tuple(options))


def _draw_public_choice(ctx, label: str, options, scheduled, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(options))
    # A singleton keyed draw records the scheduled exact public axis.
    return ctx.draw_choice(label, (scheduled,))


def _broad_dimension_options(label: str, difficulty: str | None) -> tuple[int, ...]:
    if label == "frame_h":
        domain = tuple(range(5, 11))
        favored = {
            "easy": (5, 5, 6, 6, 7),
            "medium": (5, 6, 7, 8, 9),
            "hard": (7, 7, 8, 9, 10),
            None: (5, 6, 7, 8, 9, 10),
        }.get(difficulty, domain)
    else:
        domain = tuple(range(7, 15))
        favored = {
            "easy": (9, 9, 10, 10, 11),
            "medium": (9, 10, 11, 12, 13),
            "hard": (11, 11, 12, 13, 14),
            None: (7, 8, 9, 10, 11, 12, 13, 14),
        }.get(difficulty, domain)
    # Keep the whole advertised domain in every band; duplicates only bias it.
    return domain + tuple(favored) * 4


def _draw_frame(grid, top: int, left: int, bottom: int, right: int) -> None:
    for col in range(left, right + 1):
        grid[top][col] = 8
        grid[bottom][col] = 8
    for row in range(top, bottom + 1):
        grid[row][left] = 8
        grid[row][right] = 8


def _comparison(a: int, b: int) -> int:
    return -1 if a < b else 1 if a > b else 0


def _metric_disagrees(
    frame_h: int,
    frame_w: int,
    first: tuple[int, int],
    second: tuple[int, int],
) -> bool:
    for row in range(2, frame_h):
        for col in range(2, frame_w):
            l1 = _comparison(
                abs(row - first[0]) + abs(col - first[1]),
                abs(row - second[0]) + abs(col - second[1]),
            )
            l2 = _comparison(
                (row - first[0]) ** 2 + (col - first[1]) ** 2,
                (row - second[0]) ** 2 + (col - second[1]) ** 2,
            )
            if l1 != l2:
                return True
    return False


@lru_cache(maxsize=None)
def _position_pairs(
    frame_h: int, frame_w: int, alignment: str, tie_mode: str
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    interior = [(row, col) for row in range(2, frame_h) for col in range(2, frame_w)]
    result = []
    for first, second in combinations(interior, 2):
        dr = abs(first[0] - second[0])
        dc = abs(first[1] - second[1])
        observed_alignment = "row" if dr == 0 else "column" if dc == 0 else "diagonal"
        if observed_alignment != alignment:
            continue
        observed_tie = "present" if (dr + dc) % 2 == 0 else "absent"
        if observed_tie != tie_mode:
            continue
        # Diagonal lessons deliberately distinguish Manhattan from Euclidean
        # nearest-seed filling.  Every advertised size/tie combination has at
        # least one such pair; tests exhaust the cross-product.
        if alignment == "diagonal" and not _metric_disagrees(
            frame_h, frame_w, first, second
        ):
            continue
        result.append((first, second))
    if not result:
        raise ValueError(
            f"no seed pair for frame=({frame_h},{frame_w}), "
            f"alignment={alignment}, tie_mode={tie_mode}"
        )
    return tuple(result)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    config = _PROFILE_CONFIG[profile]

    scheduled_dimensions = config["dimensions"]
    if scheduled_dimensions is None:
        frame_h_options = _broad_dimension_options("frame_h", difficulty)
        frame_w_options = _broad_dimension_options("frame_w", difficulty)
    else:
        frame_h_options = (scheduled_dimensions[0],)
        frame_w_options = (scheduled_dimensions[1],)
    frame_h = _draw_public_int(ctx, "frame_h", 5, 10, frame_h_options, overrides)
    frame_w = _draw_public_int(ctx, "frame_w", 7, 14, frame_w_options, overrides)
    palette_kind = _draw_public_choice(
        ctx, "palette_kind", tuple(PALETTES), config["palette_kind"], overrides
    )
    alignment = _draw_public_choice(
        ctx, "alignment", ALIGNMENTS, config["alignment"], overrides
    )
    tie_mode = _draw_public_choice(
        ctx, "tie_mode", TIE_MODES, config["tie_mode"], overrides
    )
    color_order = _draw_public_choice(
        ctx, "color_order", COLOR_ORDERS, config["color_order"], overrides
    )

    height, width = frame_h + 2, frame_w + 2
    grid = full_grid(height, width, 0)
    _draw_frame(grid, 1, 1, frame_h, frame_w)
    pairs = _position_pairs(frame_h, frame_w, alignment, tie_mode)
    # Step through each scheduled profile's private candidate pool instead of
    # drawing with replacement.  The seed shifts the cycle, while the profile
    # occurrence index prevents avoidable duplicate lessons in ordinary runs.
    profile_occurrence = int(sample_index) // len(SCHEDULE_PROFILES)
    first, second = pairs[(int(seed) + profile_occurrence) % len(pairs)]
    low, high = sorted(PALETTES[palette_kind])
    colors = (low, high) if color_order == "ascending" else (high, low)
    grid[first[0]][first[1]] = colors[0]
    grid[second[0]][second[1]] = colors[1]
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        facts["errors"].append("grid must be a non-empty list of non-empty rows")
        return facts
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        facts["errors"].append("grid must be rectangular")
        return facts
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        facts["errors"].append("cells must be integer ARC colors 0..9")
        return facts
    height = len(grid)
    if height < 7 or width < 9:
        facts["errors"].append("canvas is too small for the framed two-seed grammar")
        return facts

    top, left, bottom, right = 1, 1, height - 2, width - 2
    frame = {
        *((top, col) for col in range(left, right + 1)),
        *((bottom, col) for col in range(left, right + 1)),
        *((row, left) for row in range(top, bottom + 1)),
        *((row, right) for row in range(top, bottom + 1)),
    }
    actual_eights = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    }
    if actual_eights != frame:
        facts["errors"].append("color 8 must be exactly the inset rectangular frame")

    if any(
        grid[row][col] != 0
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ):
        facts["errors"].append("the one-cell outer margin must remain background")

    seeds = [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] not in (0, 8)
    ]
    if len(seeds) != 2:
        facts["errors"].append(f"expected exactly two interior seeds, found {len(seeds)}")
    elif seeds[0][2] == seeds[1][2]:
        facts["errors"].append("the two seeds must have distinct colors")

    allowed = frame | {(row, col) for row, col, _ in seeds}
    if any(
        value != 0 and (row, col) not in allowed
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    ):
        facts["errors"].append("non-background cells occur outside the frame/seeds grammar")

    facts.update(
        grid=grid,
        height=height,
        width=width,
        frame_h=bottom,
        frame_w=right,
        frame=(top, left, bottom, right),
        seeds=seeds,
    )
    if len(seeds) == 2:
        ordered = sorted(seeds)
        dr = abs(ordered[0][0] - ordered[1][0])
        dc = abs(ordered[0][1] - ordered[1][1])
        facts["alignment"] = "row" if dr == 0 else "column" if dc == 0 else "diagonal"
        facts["tie_mode"] = "present" if (dr + dc) % 2 == 0 else "absent"
        facts["color_order"] = "ascending" if ordered[0][2] < ordered[1][2] else "descending"
        palette = frozenset(seed[2] for seed in seeds)
        facts["palette_kind"] = next(
            (name for name, colors in PALETTES.items() if frozenset(colors) == palette),
            None,
        )
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") or meta.get("requested_overrides") or {}
    if isinstance(requested, dict) and requested:
        try:
            actual = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"could not observe exact axes: {exc}")
        else:
            for name, expected in requested.items():
                if name in AXES and expected is not None and actual.get(name) != expected:
                    errors.append(
                        f"override {name!r} requested {expected!r}, observed {actual.get(name)!r}"
                    )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis.get("palette_kind") is None:
        raise ValueError("seed colors are outside the generated palette families")
    return {
        "frame_h": analysis["frame_h"],
        "frame_w": analysis["frame_w"],
        "palette_kind": analysis["palette_kind"],
        "alignment": analysis["alignment"],
        "tie_mode": analysis["tie_mode"],
        "color_order": analysis["color_order"],
    }


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if (analysis["frame_h"], analysis["frame_w"]) not in _CANONICAL_FRAME_PROFILES:
        return [
            "strict canonical profile requires frame dimensions "
            f"{sorted(_CANONICAL_FRAME_PROFILES)}, got "
            f"({analysis['frame_h']}, {analysis['frame_w']})"
        ]
    return []


MIN_STRICT_FRAC = 0.50


def _distance(row: int, col: int, seed, metric: str) -> int:
    if metric == "manhattan":
        return abs(row - seed[0]) + abs(col - seed[1])
    if metric == "euclidean":
        return (row - seed[0]) ** 2 + (col - seed[1]) ** 2
    raise ValueError(metric)


def _apply_rule(
    grid,
    *,
    metric: str = "manhattan",
    tie: str = "zero",
    reassign_colors: bool = False,
):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid two-seed frame: " + "; ".join(analysis["errors"]))
    output = deepcopy(grid)
    seeds = sorted(analysis["seeds"])
    if reassign_colors:
        colors = sorted(seed[2] for seed in seeds)
        seeds = [(seed[0], seed[1], color) for seed, color in zip(seeds, colors)]
    _, _, bottom, right = analysis["frame"]
    for row in range(2, bottom):
        for col in range(2, right):
            if output[row][col] != 0:
                continue
            first_distance = _distance(row, col, seeds[0], metric)
            second_distance = _distance(row, col, seeds[1], metric)
            if first_distance < second_distance:
                output[row][col] = seeds[0][2]
            elif second_distance < first_distance:
                output[row][col] = seeds[1][2]
            elif tie == "lower_color":
                output[row][col] = min(seeds[0][2], seeds[1][2])
    return output


def rule_mirror(grid):
    """Pure Python mirror for tests and semantic rivals; Racket stays authoritative."""
    return _apply_rule(grid)


def _rival_ascending_position_colors(grid):
    return _apply_rule(grid, reassign_colors=True)


def _rival_euclidean_nearest(grid):
    return _apply_rule(grid, metric="euclidean")


def _rival_lower_color_wins_ties(grid):
    return _apply_rule(grid, tie="lower_color")


def _rival_ascending_colors_on_axis_aligned(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid two-seed frame: " + "; ".join(analysis["errors"]))
    return _apply_rule(grid, reassign_colors=analysis["alignment"] != "diagonal")


def _rival_lower_color_ties_on_axis_aligned(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid two-seed frame: " + "; ".join(analysis["errors"]))
    tie = "lower_color" if analysis["alignment"] != "diagonal" else "zero"
    return _apply_rule(grid, tie=tie)


def _valid_fact(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def witness(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return witness


SEMANTIC_RIVALS = {
    "ascending_position_colors": _rival_ascending_position_colors,
    "euclidean_nearest": _rival_euclidean_nearest,
    "lower_color_wins_ties": _rival_lower_color_wins_ties,
    "ascending_colors_on_axis_aligned": _rival_ascending_colors_on_axis_aligned,
    "lower_color_ties_on_axis_aligned": _rival_lower_color_ties_on_axis_aligned,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All three official pairs put the lower-valued color at the earlier
    # row-major seed position, so canonical data alone cannot falsify this.
    "ascending_position_colors": _rival_ascending_position_colors,
}

SEMANTIC_WITNESSES = {
    "descending_position_colors": _valid_fact(
        lambda facts: facts["color_order"] == "descending"
    ),
    "tie_cells_stay_zero": lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid).get("tie_mode") == "present"
        and _rival_lower_color_wins_ties(grid) != rule_mirror(grid)
    ),
    "manhattan_not_euclidean": lambda grid: (
        not _analyze(grid)["errors"]
        and _rival_euclidean_nearest(grid) != rule_mirror(grid)
    ),
    "axis_aligned_descending_colors": lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid).get("alignment") in {"row", "column"}
        and _analyze(grid).get("color_order") == "descending"
        and _rival_ascending_colors_on_axis_aligned(grid) != rule_mirror(grid)
    ),
    "axis_aligned_ties_stay_zero": lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid).get("alignment") in {"row", "column"}
        and _analyze(grid).get("tie_mode") == "present"
        and _rival_lower_color_ties_on_axis_aligned(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "descending_position_colors": ["ascending_position_colors"],
    "tie_cells_stay_zero": ["lower_color_wins_ties"],
    "manhattan_not_euclidean": ["euclidean_nearest"],
    "axis_aligned_descending_colors": ["ascending_colors_on_axis_aligned"],
    "axis_aligned_ties_stay_zero": ["lower_color_ties_on_axis_aligned"],
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the task grammar: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the Manhattan Voronoi rule")
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the task grammar: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the Manhattan Voronoi rule")
    if reasons or len(valid_demos) != len(demos):
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but predicts a different query"
                )
    return reasons
