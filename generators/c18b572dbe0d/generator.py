"""Generator for ARC task 30f42897 (task id c18b572dbe0d).

A monochrome segment lies on the cyclic outer-border ring of an 8-background
rectangle.  The output keeps that source segment and repeats its exact cyclic
shape every ``2 * N`` ring positions, where ``N`` is the segment length.

The four-profile schedule deliberately includes the canonical dimensions and
all decisive cases: long and short segments, straight and corner-crossing
segments, vertical and horizontal placements, and the previously unseen
``N == 3`` case used by the canonical query.  That last case is essential:
"solve the observed lengths but do nothing for length three" fits every public
training pair while changing the public test answer.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c18b572dbe0d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "17b5a481a416"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An 8-background rectangle contains one monochrome cyclic segment on its "
    "outer-border ring.  Keep the source segment and repeat it around the ring "
    "at stride 2N, where N is the number of colored cells."
)

INVARIANTS = [
    "background is color 8",
    "exactly one non-background color is present",
    "the non-background cells form one cyclically consecutive perimeter segment",
    "the authoritative output retains the source and repeats it every 2N ring cells",
    "all declared axes are exactly recoverable from the returned input grid",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware 3..9",
        "valid": "3..9",
        "doc": "Exact returned-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware 8..14",
        "valid": "8..14",
        "doc": "Exact returned-grid width.",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 2..5; profile 3 is always 3",
        "valid": "2..5",
        "doc": "Exact length N of the single cyclic border segment.",
    },
    "color": {
        "type": "color",
        "default": "rng from 1..7 or 9",
        "valid": "1..7|9",
        "doc": "Exact non-background segment color; cyan 8 is reserved as background.",
    },
    "corner_crossing": {
        "type": "bool",
        "default": "scheduled false/true",
        "valid": "true|false",
        "doc": "Whether the segment crosses at least one perimeter-corner transition.",
    },
}

SCHEDULE_PROFILES = (0, 1, 2, 3)
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_DIMENSIONS = (
    (7, 10, 5, False),
    (4, 10, 4, True),
    (7, 9, 2, False),
    (3, 14, 3, False),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive lesson rows visit all four semantic profiles."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _ring_coords(height: int, width: int) -> list[tuple[int, int]]:
    """Clockwise ring order used by the canonical Racket authority."""
    return (
        [(0, col) for col in range(width)]
        + [(row, width - 1) for row in range(1, height)]
        + [(height - 1, col) for col in range(width - 2, -1, -1)]
        + [(row, 0) for row in range(height - 2, 0, -1)]
    )


def _corner_transition_positions(height: int, width: int) -> set[int]:
    """Ring positions whose successor crosses top-right/bottom-right/etc."""
    ring_len = 2 * height + 2 * width - 4
    return {
        width - 1,
        width + height - 2,
        2 * width + height - 3,
        ring_len - 1,
    }


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty list of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be nonempty"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if len(grid) < 2 or width < 2:
        return "grid must have at least two rows and two columns"
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return "cells must be literal ARC integer colors 0..9"
    return None


def _cyclic_run_start(colored: set[int], ring_len: int) -> int | None:
    starts = [pos for pos in colored if (pos - 1) % ring_len not in colored]
    return starts[0] if len(starts) == 1 else None


def _analyze(grid: Any) -> dict[str, Any]:
    shape_error = _shape_error(grid)
    if shape_error:
        return {"errors": [shape_error]}

    height, width = len(grid), len(grid[0])
    ring = _ring_coords(height, width)
    ring_index = {cell: index for index, cell in enumerate(ring)}
    errors: list[str] = []

    non_bg_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 8
    ]
    if not non_bg_cells:
        return {"errors": ["at least one non-8 perimeter cell is required"]}

    interior = [cell for cell in non_bg_cells if cell not in ring_index]
    if interior:
        errors.append(f"{len(interior)} non-8 cell(s) lie in the interior")

    colors = {grid[row][col] for row, col in non_bg_cells}
    if len(colors) != 1:
        errors.append(f"exactly one non-background color is required, got {sorted(colors)}")
    color = next(iter(colors)) if len(colors) == 1 else None

    colored_positions = {ring_index[cell] for cell in non_bg_cells if cell in ring_index}
    n_cells = len(colored_positions)
    if not 2 <= n_cells <= 6:
        errors.append(f"segment length must be 2..6, got {n_cells}")

    start = _cyclic_run_start(colored_positions, len(ring)) if colored_positions else None
    if start is None:
        errors.append("non-8 perimeter cells must form one cyclically consecutive segment")
    else:
        expected = {(start + offset) % len(ring) for offset in range(n_cells)}
        if colored_positions != expected:
            errors.append("non-8 perimeter cells contain a gap or a second segment")

    crossing = False
    if start is not None:
        transitions = _corner_transition_positions(height, width)
        crossing = any(
            (start + offset) % len(ring) in transitions
            for offset in range(max(0, n_cells - 1))
        )

    analysis = {
        "errors": errors,
        "height": height,
        "width": width,
        "ring": ring,
        "ring_len": len(ring),
        "colored_positions": colored_positions,
        "run_start": start,
        "n_cells": n_cells,
        "color": color,
        "corner_crossing": crossing,
    }
    if not errors:
        output = _apply_stride(grid, stride=2 * n_cells)
        analysis["output"] = output
        analysis["added_cells"] = sum(
            before == 8 and after != 8
            for before_row, after_row in zip(grid, output)
            for before, after in zip(before_row, after_row)
        )
        if output == [list(row) for row in grid]:
            analysis["errors"].append("the canonical rule would leave this input unchanged")
    return analysis


def _apply_stride(grid: Any, *, stride: int) -> list[list[int]]:
    """Apply the authority's ring replication with an explicit stride."""
    height, width = len(grid), len(grid[0])
    ring = _ring_coords(height, width)
    colored = [
        pos for pos, (row, col) in enumerate(ring) if grid[row][col] != 8
    ]
    if not colored:
        return [list(row) for row in grid]
    color = grid[ring[colored[0]][0]][ring[colored[0]][1]]
    first_colored = colored[0]
    offsets = [pos - first_colored for pos in colored]
    ring_len = len(ring)
    output = [list(row) for row in grid]
    # The Racket authority maps k=0..floor(ring_len/stride), takes modulo, and
    # paints all source offsets.  This is equivalent to one complete traversal,
    # with a harmless duplicate start when the stride divides the ring length.
    for k in range(ring_len // stride + 1):
        start = (first_colored + k * stride) % ring_len
        for offset in offsets:
            row, col = ring[(start + offset) % ring_len]
            output[row][col] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror; canonical Racket remains the output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["output"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analyze(grid)
    if not 3 <= analysis["height"] <= 9:
        reasons.append(f"height {analysis['height']} is outside the teaching envelope 3..9")
    if not 8 <= analysis["width"] <= 14:
        reasons.append(f"width {analysis['width']} is outside the teaching envelope 8..14")
    if not 2 <= analysis["n_cells"] <= 5:
        reasons.append(f"segment length {analysis['n_cells']} is outside the canonical 2..5 range")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_cells": analysis["n_cells"],
        "color": analysis["color"],
        "corner_crossing": analysis["corner_crossing"],
    }


def _segment_orientation(analysis: dict[str, Any]) -> str:
    cells = [analysis["ring"][pos] for pos in analysis["colored_positions"]]
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1:
        return "horizontal"
    if len(cols) == 1:
        return "vertical"
    return "corner"


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output_non_bg = sum(value != 8 for row in analysis["output"] for value in row)
    return {
        **observe_overrides(grid),
        "orientation": _segment_orientation(analysis),
        "run_start": analysis["run_start"],
        "ring_len": analysis["ring_len"],
        "added_cells": analysis["added_cells"],
        "output_non_background_cells": output_non_bg,
        "wraps_ring_origin": 0 in analysis["colored_positions"]
        and analysis["ring_len"] - 1 in analysis["colored_positions"],
    }


def _draw_int_axis(ctx, label: str, lo: int, hi: int, scheduled: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_choice_axis(ctx, label: str, choices: tuple, scheduled: Any | None):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    if scheduled is not None:
        return ctx.draw_choice(label, (scheduled,))
    return ctx.draw_choice(label, choices)


def _candidate_starts(
    height: int,
    width: int,
    n_cells: int,
    *,
    corner_crossing: bool,
    profile: int,
) -> list[int]:
    ring_len = 2 * height + 2 * width - 4
    transitions = _corner_transition_positions(height, width)
    candidates = []
    for start in range(ring_len):
        crosses = any(
            (start + offset) % ring_len in transitions
            for offset in range(n_cells - 1)
        )
        if crosses != corner_crossing:
            continue
        cells = [_ring_coords(height, width)[(start + k) % ring_len] for k in range(n_cells)]
        rows = {row for row, _ in cells}
        cols = {col for _, col in cells}
        orientation = "horizontal" if len(rows) == 1 else "vertical" if len(cols) == 1 else "corner"
        if profile == 0 and not corner_crossing and orientation != "vertical":
            continue
        if profile == 3 and not corner_crossing and orientation != "horizontal":
            continue
        candidates.append(start)
    if candidates:
        return candidates
    # Explicit overrides can make profile-preferred orientation impossible
    # (e.g. height=3, N=5, non-corner).  The axis contract is still satisfiable:
    # fall back to any placement with the requested corner status.
    for start in range(ring_len):
        crosses = any(
            (start + offset) % ring_len in transitions
            for offset in range(n_cells - 1)
        )
        if crosses == corner_crossing:
            candidates.append(start)
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    # Every other four-row cycle is a canonical-dimension anchor.  The other
    # cycles widen dimensions while keeping the same semantic branch schedule.
    anchor = (int(sample_index) // len(SCHEDULE_PROFILES)) % 2 == 0
    canonical_h, canonical_w, canonical_n, canonical_corner = _CANONICAL_DIMENSIONS[profile]

    height = _draw_int_axis(ctx, "grid_h", 3, 9, canonical_h if anchor else None)
    width = _draw_int_axis(ctx, "grid_w", 8, 14, canonical_w if anchor else None)
    # The four-profile lesson schedule always demonstrates N=5,4,2,3 in
    # order.  Explicit overrides still accept the full 2..5 domain in every
    # difficulty band.  Keeping the default lengths fixed is what kills both
    # the public-train overfit (skip N=3) and fixed-stride shortcuts.
    n_cells = _draw_int_axis(ctx, "n_cells", 2, 5, canonical_n)
    color = _draw_choice_axis(ctx, "color", _COLORS, None)
    scheduled_corner = canonical_corner if anchor else (profile == 1)
    corner_crossing = bool(
        _draw_choice_axis(ctx, "corner_crossing", (False, True), scheduled_corner)
    )

    candidates = _candidate_starts(
        height,
        width,
        n_cells,
        corner_crossing=corner_crossing,
        profile=profile,
    )
    if not candidates:
        raise AssertionError("no lawful segment placement for declared axes")
    start = ctx.draw_rng("placement").choice(candidates)
    ring = _ring_coords(height, width)
    grid = full_grid(height, width, 8)
    for offset in range(n_cells):
        row, col = ring[(start + offset) % len(ring)]
        grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_cells": n_cells,
        "color": color,
        "corner_crossing": corner_crossing,
    }
    if observed != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Adversarial curriculum contracts
# ---------------------------------------------------------------------------


def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis is not None and predicate(analysis))


SEMANTIC_WITNESSES = {
    "straight_segment": lambda grid: _witness(grid, lambda a: not a["corner_crossing"]),
    "corner_crossing_segment": lambda grid: _witness(grid, lambda a: a["corner_crossing"]),
    "vertical_segment": lambda grid: _witness(grid, lambda a: _segment_orientation(a) == "vertical"),
    "horizontal_segment": lambda grid: _witness(grid, lambda a: _segment_orientation(a) == "horizontal"),
    "query_only_length_three": lambda grid: _witness(grid, lambda a: a["n_cells"] == 3),
    "long_segment": lambda grid: _witness(grid, lambda a: a["n_cells"] >= 4),
    "multiple_new_copies": lambda grid: _witness(grid, lambda a: a["added_cells"] > a["n_cells"]),
    "wraps_ring_origin": lambda grid: _witness(
        grid,
        lambda a: 0 in a["colored_positions"] and a["ring_len"] - 1 in a["colored_positions"],
    ),
}


def _rival_single_extra_copy(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    ring = analysis["ring"]
    colored = sorted(analysis["colored_positions"])
    first = colored[0]
    offsets = [pos - first for pos in colored]
    output = [list(row) for row in grid]
    start = (first + 2 * analysis["n_cells"]) % analysis["ring_len"]
    for offset in offsets:
        row, col = ring[(start + offset) % analysis["ring_len"]]
        output[row][col] = analysis["color"]
    return output


def _rival_repeat_every_n(grid):
    analysis = _lawful_analysis(grid)
    return None if analysis is None else _apply_stride(grid, stride=analysis["n_cells"])


def _rival_fixed_stride_six(grid):
    analysis = _lawful_analysis(grid)
    return None if analysis is None else _apply_stride(grid, stride=6)


def _rival_move_one_block(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    output = [list(row) for row in grid]
    for pos in analysis["colored_positions"]:
        row, col = analysis["ring"][pos]
        output[row][col] = 8
    colored = sorted(analysis["colored_positions"])
    first = colored[0]
    offsets = [pos - first for pos in colored]
    start = (first + 2 * analysis["n_cells"]) % analysis["ring_len"]
    for offset in offsets:
        row, col = analysis["ring"][(start + offset) % analysis["ring_len"]]
        output[row][col] = analysis["color"]
    return output


def _rival_ignore_corner_crossing(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    return [list(row) for row in grid] if analysis["corner_crossing"] else rule_mirror(grid)


def _rival_skip_unseen_length_three(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    return [list(row) for row in grid] if analysis["n_cells"] == 3 else rule_mirror(grid)


SEMANTIC_RIVALS = {
    "single_extra_copy": _rival_single_extra_copy,
    "repeat_every_n_instead_of_2n": _rival_repeat_every_n,
    "fixed_stride_six": _rival_fixed_stride_six,
    "move_one_block_instead_of_retain_and_repeat": _rival_move_one_block,
    "ignore_corner_crossing_segments": _rival_ignore_corner_crossing,
    "skip_unseen_length_three": _rival_skip_unseen_length_three,
}

WITNESS_RIVALS = {
    "corner_crossing_segment": ["ignore_corner_crossing_segments"],
    "query_only_length_three": ["skip_unseen_length_three", "fixed_stride_six"],
    "long_segment": ["fixed_stride_six", "repeat_every_n_instead_of_2n"],
    "multiple_new_copies": ["single_extra_copy", "move_one_block_instead_of_retain_and_repeat"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # This rival exactly fits the three public demonstrations (N=5,4,2) and
    # disagrees only on the public N=3 query.  Generated four-demo lessons must
    # include an N=3 witness or they do not identify the intended rule.
    "skip_unseen_length_three": _rival_skip_unseen_length_three,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with 2N ring replication")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with 2N ring replication")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes that structural self_check must reject."""
    valid = generate(7001, 2, difficulty="medium", n_cells=4, corner_crossing=False)
    analysis = _analyze(valid)

    blank = full_grid(len(valid), len(valid[0]), 8)

    interior_cell = copy.deepcopy(valid)
    interior_cell[1][1] = analysis["color"]

    second_color = copy.deepcopy(valid)
    row, col = analysis["ring"][next(iter(analysis["colored_positions"]))]
    second_color[row][col] = 9 if analysis["color"] != 9 else 7

    broken_run = copy.deepcopy(valid)
    run_positions = [
        (analysis["run_start"] + offset) % analysis["ring_len"]
        for offset in range(analysis["n_cells"])
    ]
    row, col = analysis["ring"][run_positions[len(run_positions) // 2]]
    broken_run[row][col] = 8

    two_segments = copy.deepcopy(valid)
    occupied = set(analysis["colored_positions"])
    extra_pos = next(
        pos
        for pos in range(analysis["ring_len"])
        if pos not in occupied
        and (pos - 1) % analysis["ring_len"] not in occupied
        and (pos + 1) % analysis["ring_len"] not in occupied
    )
    row, col = analysis["ring"][extra_pos]
    two_segments[row][col] = analysis["color"]

    full_ring = full_grid(len(valid), len(valid[0]), 8)
    for row, col in analysis["ring"]:
        full_ring[row][col] = analysis["color"]

    return [
        ("blank_grid", blank),
        ("interior_colored_cell", interior_cell),
        ("mixed_segment_colors", second_color),
        ("gap_inside_segment", broken_run),
        ("two_disconnected_segments", two_segments),
        ("full_ring_not_a_segment", full_ring),
    ]
