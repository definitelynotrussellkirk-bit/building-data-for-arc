"""Generator for ARC task 16491c603ea5 — border-touching growth wins.

Each red seed is hypothetically grown to its clipped 3x3 neighborhood.  Exactly
one seed lies on the input border; every other seed is a well-separated interior
decoy.  The canonical Racket rule selects the grown region that touches the
border, crops it tightly, and paints the result cyan (8).

Generated lessons deliberately keep at least one decoy and place the selected
seed on the *actual* border.  Therefore the answer is one of the three clipped
shapes 2x3, 3x2, or 2x2 rather than an uninformative full 3x3 square.  Three
consecutive sample indices schedule those three answer-shape branches.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "16491c603ea5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4a66dcca2f33"
EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = 3

TARGET_EDGES = (
    "top",
    "bottom",
    "left",
    "right",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
_EDGE_SCHEDULE = (
    ("top", "bottom"),
    ("left", "right"),
    ("top_left", "top_right", "bottom_left", "bottom_right"),
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_GLOBAL_BOUNDS = {
    "grid_h": (7, 22),
    "grid_w": (8, 24),
    "n_decoys": (1, 4),
}

SUMMARY = (
    "A black grid contains red singleton seeds. Exactly one red seed lies on "
    "the border and one to four well-separated red decoys lie at least two "
    "cells inside it. Grow every seed to its clipped 3x3 neighborhood, select "
    "the unique grown region touching the border, crop it tightly, and output "
    "that solid rectangle in color 8. Consecutive lesson samples cover the "
    "2x3 horizontal-edge, 3x2 vertical-edge, and 2x2 corner answers."
)

INVARIANTS = [
    "the input uses only black 0 and red 2",
    "exactly one red seed lies on the actual grid border",
    "one to four red decoys are at least two cells from every border",
    "all clipped 3x3 seed neighborhoods are pairwise disjoint",
    "the selected border seed yields a clipped 2x3, 3x2, or 2x2 answer, never an ambiguous full 3x3",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy cycles canonical 7..8; medium 8..14; hard 15..22",
        "valid": "7..22",
    },
    "grid_w": {
        "type": "int",
        "default": "easy anchors canonical width 8; medium 8..16; hard 16..24",
        "valid": "8..24",
    },
    "n_decoys": {
        "type": "int",
        "default": "easy 1; medium 1..3; hard 3..4",
        "valid": "1..4",
    },
    "target_edge": {
        "type": "str",
        "default": "three-sample schedule: horizontal edge, vertical edge, corner",
        "valid": "top|bottom|left|right|top_left|top_right|bottom_left|bottom_right",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    height, width = len(grid), len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _seed_points(grid: Any) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]


def _grown_cells(
    height: int, width: int, point: tuple[int, int]
) -> frozenset[tuple[int, int]]:
    row, col = point
    return frozenset(
        (rr, cc)
        for rr in range(row - 1, row + 2)
        for cc in range(col - 1, col + 2)
        if 0 <= rr < height and 0 <= cc < width
    )


def _target_edge(
    point: tuple[int, int], height: int, width: int
) -> str | None:
    row, col = point
    if row == 0 and col == 0:
        return "top_left"
    if row == 0 and col == width - 1:
        return "top_right"
    if row == height - 1 and col == 0:
        return "bottom_left"
    if row == height - 1 and col == width - 1:
        return "bottom_right"
    if row == 0:
        return "top"
    if row == height - 1:
        return "bottom"
    if col == 0:
        return "left"
    if col == width - 1:
        return "right"
    return None


def _expected_output_shape(
    point: tuple[int, int], height: int, width: int
) -> tuple[int, int]:
    row, col = point
    out_h = 2 if row in (0, height - 1) else 3
    out_w = 2 if col in (0, width - 1) else 3
    return out_h, out_w


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Return exact task-linked facts recoverable from an input grid."""
    errors, height, width = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    seeds = _seed_points(grid)
    border_seeds = [
        point for point in seeds if _target_edge(point, height, width) is not None
    ]
    grown = [_grown_cells(height, width, point) for point in seeds]
    overlaps = [
        (left, right)
        for left in range(len(grown))
        for right in range(left + 1, len(grown))
        if grown[left] & grown[right]
    ]
    grown_border_seeds = [
        point
        for point, cells in zip(seeds, grown)
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        )
    ]
    target = border_seeds[0] if len(border_seeds) == 1 else None
    return {
        "errors": [],
        "grid_h": height,
        "grid_w": width,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "seeds": tuple(seeds),
        "seed_count": len(seeds),
        "border_seeds": tuple(border_seeds),
        "border_seed_count": len(border_seeds),
        "grown_border_seeds": tuple(grown_border_seeds),
        "grown_border_seed_count": len(grown_border_seeds),
        "grown_overlap_pairs": tuple(overlaps),
        "target": target,
        "target_edge": (
            _target_edge(target, height, width) if target is not None else None
        ),
        "n_decoys": len(seeds) - 1 if target is not None else None,
        "expected_output_shape": (
            _expected_output_shape(target, height, width)
            if target is not None
            else None
        ),
    }


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("border_seed_count") != 1:
        raise ValueError("cannot observe target_edge without one border seed")
    n_decoys = facts.get("n_decoys")
    target_edge = facts.get("target_edge")
    if not isinstance(n_decoys, int) or not isinstance(target_edge, str):
        raise ValueError("cannot recover exact generator axes")
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "n_decoys": n_decoys,
        "target_edge": target_edge,
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize canonical inputs and the stronger generated teaching domain."""
    errors, height, width = _validate_grid(grid)
    if errors:
        return errors
    if height < 7 or width < 8:
        errors.append(f"expected at least 7x8, got {height}x{width}")
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC 30x30 limit: {height}x{width}")

    illegal = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 2)
    ]
    if illegal:
        errors.append(f"input must use only colors 0 and 2; saw {illegal[:3]}")

    facts = semantic_observables(grid)
    seeds = list(facts.get("seeds", ()))
    if not 2 <= len(seeds) <= 5:
        errors.append(
            f"expected one target plus 1..4 decoys, saw {len(seeds)} red seeds"
        )
    border_seeds = list(facts.get("border_seeds", ()))
    if len(border_seeds) != 1:
        errors.append(
            f"expected exactly one red seed on the border, saw {len(border_seeds)}"
        )

    if len(border_seeds) == 1:
        target = border_seeds[0]
        shape = _expected_output_shape(target, height, width)
        if shape == (3, 3):
            errors.append("selected seed must yield a clipped, non-3x3 answer")
        for point in seeds:
            if point == target:
                continue
            row, col = point
            if not (2 <= row <= height - 3 and 2 <= col <= width - 3):
                errors.append(
                    f"decoy seed {point} must be at least two cells from every border"
                )

    if facts.get("grown_border_seed_count") != 1:
        errors.append(
            "expected exactly one grown 3x3 neighborhood to touch the border, "
            f"saw {facts.get('grown_border_seed_count')}"
        )
    overlaps = facts.get("grown_overlap_pairs", ())
    if overlaps:
        errors.append(f"grown 3x3 neighborhoods overlap: {list(overlaps)[:3]}")
    return errors


# --- Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md) ---

_CANONICAL_DIMS = ((7, 8), (8, 8), (8, 9))
_HORIZONTAL_EDGES = ("top", "bottom")
_VERTICAL_EDGES = ("left", "right")
_CORNER_EDGES = ("top_left", "top_right", "bottom_left", "bottom_right")


def _rule_mirror(grid):
    """Diagnostic Python mirror of the canonical Racket rule: grow the
    border-touching seed's clipped 3x3, crop tight, paint cyan 8."""
    errors, height, width = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    for point in sorted(_seed_points(grid)):
        cells = _grown_cells(height, width, point)
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        ):
            rows_ = [row for row, _ in cells]
            cols_ = [col for _, col in cells]
            out_h = max(rows_) - min(rows_) + 1
            out_w = max(cols_) - min(cols_) + 1
            return [[8] * out_w for _ in range(out_h)]
    raise ValueError("no grown seed region touches the border")


def strict_canonical_like(grid):
    """[] iff grid sits on the strict linked canonical manifold: lawful
    grammar at a canonical scale (7x8 / 8x8 / 8x9), exactly one decoy, and
    a non-corner edge target (no canonical pair demonstrates a corner)."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    reasons = []
    dims = (facts["grid_h"], facts["grid_w"])
    if dims not in _CANONICAL_DIMS:
        reasons.append(
            f"dims {dims} are outside the canonical scales {_CANONICAL_DIMS}"
        )
    if facts["n_decoys"] != 1:
        reasons.append(
            f"canonical inputs carry exactly one decoy, found {facts['n_decoys']}"
        )
    if facts["target_edge"] not in _HORIZONTAL_EDGES + _VERTICAL_EDGES:
        reasons.append(
            "canonical inputs place the target on a non-corner edge, found "
            f"{facts['target_edge']!r}"
        )
    return reasons


def _lawful_facts(grid):
    """semantic_observables for a grammar-lawful grid, else None."""
    if self_check(grid):
        return None
    return semantic_observables(grid)


def _w_answer_2x3_horizontal_edge(grid):
    facts = _lawful_facts(grid)
    return facts is not None and facts["target_edge"] in _HORIZONTAL_EDGES


def _w_answer_3x2_vertical_edge(grid):
    facts = _lawful_facts(grid)
    return facts is not None and facts["target_edge"] in _VERTICAL_EDGES


def _w_answer_2x2_corner(grid):
    facts = _lawful_facts(grid)
    return facts is not None and facts["target_edge"] in _CORNER_EDGES


def _w_decoy_present(grid):
    facts = _lawful_facts(grid)
    return facts is not None and facts["n_decoys"] >= 1


def _w_target_not_first_in_scan_order(grid):
    """A decoy precedes the target row-major — rebuts 'expand the first seed'."""
    facts = _lawful_facts(grid)
    if facts is None:
        return False
    seeds = sorted(facts["seeds"])
    return seeds[0] != facts["target"]


SEMANTIC_WITNESSES = {
    "answer_2x3_horizontal_edge": _w_answer_2x3_horizontal_edge,
    "answer_3x2_vertical_edge": _w_answer_3x2_vertical_edge,
    "answer_2x2_corner": _w_answer_2x2_corner,
    "decoy_present": _w_decoy_present,
    "target_not_first_in_scan_order": _w_target_not_first_in_scan_order,
}


def lesson_identifiable(demos, query):
    """[] iff the demos refute the competing rules that would answer the
    query differently: a constant-shape answer and 'expand the first (or
    only) red seed'.  Off-grammar demos (no decoy, full-3x3 answer, no
    border seed) are reported instead of silently accepted."""
    reasons = []
    demo_facts = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        grid = demo["input"]
        errors = self_check(grid)
        if errors:
            return [f"demo {index} input off-grammar: {errors[0]}"]
        if demo["output"] != _rule_mirror(grid):
            return [f"demo {index} output does not match the canonical rule"]
        facts = semantic_observables(grid)
        if facts["expected_output_shape"] == (3, 3):
            return [f"demo {index} answer is an ambiguous full 3x3"]
        demo_facts.append(facts)
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    q_errors = self_check(query["input"])
    if q_errors:
        return [f"query input off-grammar: {q_errors[0]}"]
    q_facts = semantic_observables(query["input"])

    demo_shapes = {facts["expected_output_shape"] for facts in demo_facts}
    if len(demo_shapes) == 1 and q_facts["expected_output_shape"] not in demo_shapes:
        reasons.append(
            "constant-answer competitor consistent: every demo answers "
            f"{next(iter(demo_shapes))} but the query answer is "
            f"{q_facts['expected_output_shape']}"
        )
    demos_all_scan_first = all(
        sorted(facts["seeds"])[0] == facts["target"] for facts in demo_facts
    )
    if demos_all_scan_first and sorted(q_facts["seeds"])[0] != q_facts["target"]:
        reasons.append(
            "expand-the-first-seed competitor consistent: every demo target is "
            "the row-major-first seed but the query target is not"
        )
    return reasons


def _target_positions(height: int, width: int, edge: str) -> tuple[tuple[int, int], ...]:
    if edge == "top":
        return tuple((0, col) for col in range(1, width - 1))
    if edge == "bottom":
        return tuple((height - 1, col) for col in range(1, width - 1))
    if edge == "left":
        return tuple((row, 0) for row in range(1, height - 1))
    if edge == "right":
        return tuple((row, width - 1) for row in range(1, height - 1))
    corners = {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "bottom_left": (height - 1, 0),
        "bottom_right": (height - 1, width - 1),
    }
    if edge not in corners:
        raise ValueError(f"unknown target_edge: {edge!r}")
    return (corners[edge],)


def _lattice_decoys(
    height: int,
    width: int,
    target: tuple[int, int],
    row_start: int,
    col_start: int,
) -> tuple[tuple[int, int], ...]:
    target_cells = _grown_cells(height, width, target)
    points = []
    for row in range(row_start, height - 2, 3):
        for col in range(col_start, width - 2, 3):
            point = (row, col)
            if not (_grown_cells(height, width, point) & target_cells):
                points.append(point)
    return tuple(points)


@lru_cache(maxsize=None)
def _has_layout(height: int, width: int, n_decoys: int, edge: str) -> bool:
    if not (7 <= height <= 22 and 8 <= width <= 24 and 1 <= n_decoys <= 4):
        return False
    for target in _target_positions(height, width, edge):
        for row_start, col_start in product((2, 3, 4), repeat=2):
            if len(
                _lattice_decoys(
                    height, width, target, row_start, col_start
                )
            ) >= n_decoys:
                return True
    return False


def _preferred_values(difficulty: Any) -> tuple[range, range, range]:
    if difficulty == "easy":
        return range(7, 9), range(8, 10), range(1, 2)
    if difficulty == "medium":
        return range(8, 15), range(8, 17), range(1, 4)
    if difficulty == "hard":
        return range(15, 23), range(16, 25), range(3, 5)
    return range(7, 23), range(8, 25), range(1, 5)


def _profile_candidates(
    difficulty: Any,
    sample_phase: int,
    requested_h: int | None,
    requested_w: int | None,
    requested_n: int | None,
    requested_edge: str | None,
) -> tuple[tuple[int, int, int, str], ...]:
    h_pref, w_pref, n_pref = _preferred_values(difficulty)
    edge_values = (
        (requested_edge,)
        if requested_edge is not None
        else _EDGE_SCHEDULE[sample_phase]
    )

    # Easy ordinary lessons intentionally cycle the canonical scale profiles.
    if (
        difficulty == "easy"
        and requested_h is None
        and requested_w is None
        and requested_n is None
    ):
        canonical_dims = ((7, 8), (8, 8), (8, 8))
        scheduled_h, scheduled_w = canonical_dims[sample_phase]
        h_pref = range(scheduled_h, scheduled_h + 1)
        w_pref = range(scheduled_w, scheduled_w + 1)

    h_values = (requested_h,) if requested_h is not None else tuple(h_pref)
    w_values = (requested_w,) if requested_w is not None else tuple(w_pref)
    n_values = (requested_n,) if requested_n is not None else tuple(n_pref)

    def collect(hs, ws, ns):
        return tuple(
            (height, width, n_decoys, edge)
            for height in hs
            for width in ws
            for n_decoys in ns
            for edge in edge_values
            if _has_layout(height, width, n_decoys, edge)
        )

    preferred = collect(h_values, w_values, n_values)
    if preferred:
        return preferred

    # Explicit controls may require leaving the requested difficulty's normal
    # scale.  Expand only non-explicit axes; exact requests remain exact.
    if any(
        value is not None
        for value in (requested_h, requested_w, requested_n, requested_edge)
    ):
        h_values = (
            (requested_h,)
            if requested_h is not None
            else range(_GLOBAL_BOUNDS["grid_h"][0], _GLOBAL_BOUNDS["grid_h"][1] + 1)
        )
        w_values = (
            (requested_w,)
            if requested_w is not None
            else range(_GLOBAL_BOUNDS["grid_w"][0], _GLOBAL_BOUNDS["grid_w"][1] + 1)
        )
        n_values = (
            (requested_n,)
            if requested_n is not None
            else range(_GLOBAL_BOUNDS["n_decoys"][0], _GLOBAL_BOUNDS["n_decoys"][1] + 1)
        )
        return collect(h_values, w_values, n_values)
    return ()


def _record_int(ctx, label: str, value: int, explicit: bool) -> int:
    low, high = _GLOBAL_BOUNDS[label]
    return (
        ctx.draw_int(label, low, high)
        if explicit
        else ctx.draw_int(label, value, value)
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, semantically identifying lesson input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    requested_h = (
        int(overrides["grid_h"]) if overrides.get("grid_h") is not None else None
    )
    requested_w = (
        int(overrides["grid_w"]) if overrides.get("grid_w") is not None else None
    )
    requested_n = (
        int(overrides["n_decoys"])
        if overrides.get("n_decoys") is not None
        else None
    )
    requested_edge = overrides.get("target_edge")
    if requested_edge is not None and requested_edge not in TARGET_EDGES:
        raise ValueError(f"target_edge override {requested_edge!r} is invalid")

    phase = int(sample_index) % EXAMPLES_NEEDED
    profiles = _profile_candidates(
        difficulty,
        phase,
        requested_h,
        requested_w,
        requested_n,
        requested_edge,
    )
    if not profiles:
        raise ValueError(
            "requested generator axes are geometrically incompatible: "
            f"grid_h={requested_h}, grid_w={requested_w}, "
            f"n_decoys={requested_n}, target_edge={requested_edge!r}"
        )
    height, width, n_decoys, edge = ctx.draw_rng("axis_profile").choice(profiles)

    height = _record_int(ctx, "grid_h", height, requested_h is not None)
    width = _record_int(ctx, "grid_w", width, requested_w is not None)
    n_decoys = _record_int(ctx, "n_decoys", n_decoys, requested_n is not None)
    edge = (
        ctx.draw_choice("target_edge", TARGET_EDGES)
        if requested_edge is not None
        else ctx.draw_choice("target_edge", (edge,))
    )

    layouts: list[tuple[tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for target in _target_positions(height, width, edge):
        for row_start, col_start in product((2, 3, 4), repeat=2):
            decoys = _lattice_decoys(
                height, width, target, row_start, col_start
            )
            if len(decoys) >= n_decoys:
                layouts.append((target, decoys))
    if not layouts:
        raise RuntimeError("feasible profile unexpectedly had no concrete layout")

    layout_rng = ctx.draw_rng("layout")
    if edge in ("left", "right"):
        # Lesson-schedule guarantee: a vertical-edge scene always carries a
        # decoy strictly BEFORE the target in row-major order.  Without it, a
        # demo window of top-edge, low-row vertical-edge, and top-corner
        # targets is consistent with the "expand the first red seed in scan
        # order" competitor (semantic-gate lesson seed 97923397035772 hit
        # exactly that window).  Verified feasible for every in-bounds
        # (grid_h, grid_w, n_decoys, left|right) profile.
        layouts = [
            (target, pool)
            for target, pool in layouts
            if any(row < target[0] for row, _ in pool)
        ]
        if not layouts:
            raise RuntimeError(
                "no vertical-edge layout offers a row-major-earlier decoy"
            )
        target, decoy_pool = layout_rng.choice(layouts)
        preceding = [point for point in decoy_pool if point[0] < target[0]]
        anchor = layout_rng.choice(preceding)
        rest = [point for point in decoy_pool if point != anchor]
        decoys = [anchor] + layout_rng.sample(rest, n_decoys - 1)
    else:
        target, decoy_pool = layout_rng.choice(layouts)
        decoys = layout_rng.sample(list(decoy_pool), n_decoys)
    grid = full_grid(height, width, 0)
    grid[target[0]][target[1]] = 2
    for row, col in decoys:
        grid[row][col] = 2

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid lesson: {errors}")
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_decoys": n_decoys,
        "target_edge": edge,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(
            f"constructed grid does not realize keyed axes: {expected} -> {observed}"
        )
    return [list(row) for row in grid]
