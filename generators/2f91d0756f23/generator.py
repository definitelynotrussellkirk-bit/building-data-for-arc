"""Generator for “Paint the counted quarter-turn orbit”.

The canonical Racket authority is identified by :data:`RULE_HASH`.  Inputs have
four pieces of information:

* row 0 contains ``k`` blue (1) count markers, where ``1 <= k <= 4``;
* rows 1+ contain one maroon (9) anchor;
* rows 1+ contain one to five distinctly coloured orbit seeds near the anchor;
* the answer is a fresh grid containing the anchor and the first ``k``
  quarter-turn positions of every orbit seed, using the authority's exact
  row/column transform ``(dr, dc) -> (dc, -dr)``.

The four-slot curriculum schedule deliberately covers k=1,2,3,4 in every four
consecutive samples.  It also emits canonical-profile 8x8 and 9x9 examples,
while the other slots refute two shortcuts left ambiguous by the public ARC
pairs: “the count markers must be a left prefix” and “there are only two orbit
seeds”.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f91d0756f23"
TASK_ID = GENERATOR_ID
RULE_HASH = "dc9e50b0f1e3"
VERSION = "3.0.0"

SUMMARY = (
    "Count the color-1 markers in row 0. Around the unique color-9 anchor, "
    "paint each coloured seed at its original offset and its first k-1 "
    "quarter-turn offsets under (dr,dc)->(dc,-dr); discard the header."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "row 0 contains exactly 1..4 color-1 count markers and otherwise zeros",
    "rows 1+ contain exactly one color-9 anchor with a two-cell rotation margin",
    "rows 1+ contain 1..5 distinctly coloured orbit seeds within Chebyshev radius 2",
    "orbit seeds occupy distinct quarter-turn equivalence classes, so colours never collide",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/weighted 5..14", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "scheduled/weighted 5..16", "valid": "5..16"},
    "k": {"type": "int", "default": "sample_index mod 4 + 1", "valid": "1..4"},
    "n_orbits": {"type": "int", "default": "scheduled 1..5", "valid": "1..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Every tuple below is one complete orbit under (dr,dc)->(dc,-dr).  Selecting
# at most one input cell from each class prevents differently coloured outputs
# from overwriting each other under any k in 1..4.
_ORBIT_CLASSES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 1), (1, 0), (0, -1), (-1, 0)),
    ((1, 1), (1, -1), (-1, -1), (-1, 1)),
    ((0, 2), (2, 0), (0, -2), (-2, 0)),
    ((1, 2), (2, -1), (-1, -2), (-2, 1)),
    ((1, -2), (-2, -1), (-1, 2), (2, 1)),
    ((2, 2), (2, -2), (-2, -2), (-2, 2)),
)

SCHEDULE_PROFILES = (
    "canonical8_k1",
    "sparse_nonprefix_k2",
    "canonical9_k3",
    "dense_nonprefix_k4",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared four-slot teaching profile for a sample."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _rotation_class(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    turns = []
    for _ in range(4):
        turns.append((dr, dc))
        dr, dc = dc, -dr
    return min(turns)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (5, 14),
        "grid_w": (5, 16),
        "k": (1, 4),
        "n_orbits": (1, 5),
    }
    for name, value in overrides.items():
        if type(value) is not int:  # bool is intentionally rejected.
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _broad_default(ctx, label: str, difficulty, lo: int, hi: int) -> int:
    """Difficulty-skewed default while preserving the full override domain."""
    if label == "grid_h":
        pools = {
            "easy": tuple(range(5, 9)),
            "medium": tuple(range(7, 12)),
            "hard": tuple(range(10, 15)),
        }
    else:
        pools = {
            "easy": tuple(range(5, 10)),
            "medium": tuple(range(8, 14)),
            "hard": tuple(range(12, 17)),
        }
    pool = pools.get(difficulty, tuple(range(lo, hi + 1)))
    return ctx.draw_rng(f"{label}_scheduled_default").choice(pool)


def _scheduled_defaults(ctx, sample_index: int, difficulty) -> dict[str, int]:
    slot = int(sample_index) % 4
    if slot == 0:
        return {"grid_h": 8, "grid_w": 8, "k": 1, "n_orbits": 2}
    if slot == 2:
        return {"grid_h": 9, "grid_w": 9, "k": 3, "n_orbits": 2}

    h = _broad_default(ctx, "grid_h", difficulty, 5, 14)
    w = _broad_default(ctx, "grid_w", difficulty, 5, 16)
    if slot == 1:
        return {"grid_h": h, "grid_w": w, "k": 2, "n_orbits": 1}
    dense = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
    return {"grid_h": h, "grid_w": w, "k": 4, "n_orbits": dense}


def _draw_axes(ctx, defaults: dict[str, int], user_overrides: dict[str, int]):
    # GenCtx's typed draws are the provenance authority.  Insert only missing
    # schedule defaults into this instance's private override input; explicit
    # caller values always win and every advertised axis is still drawn through
    # its complete legal domain.
    for name, value in defaults.items():
        if name not in user_overrides:
            ctx.overrides[name] = value
    h = ctx.draw_choice("grid_h", tuple(range(5, 15)))
    w = ctx.draw_choice("grid_w", tuple(range(5, 17)))
    k = ctx.draw_choice("k", (1, 2, 3, 4))
    n_orbits = ctx.draw_choice("n_orbits", (1, 2, 3, 4, 5))
    return h, w, k, n_orbits


def _marker_columns(ctx, w: int, k: int, slot: int) -> list[int]:
    if slot == 0:
        # One canonical-shaped schedule cell keeps the public left-prefix form.
        return list(range(k))
    # Every other schedule cell is a constructive counterexample to the
    # left-prefix shortcut.  w>=5 and k<=4, so columns 1..w-1 always suffice.
    return sorted(ctx.draw_rng("marker_columns").sample(range(1, w), k))


def _place_orbits(ctx, grid, anchor: tuple[int, int], n_orbits: int) -> None:
    ar, ac = anchor
    classes = list(_ORBIT_CLASSES)
    ctx.draw_rng("orbit_classes").shuffle(classes)
    selected = classes[:n_orbits]
    colors = ctx.draw_rng("orbit_palette").sample(list(range(2, 9)), n_orbits)
    orientation_rng = ctx.draw_rng("orbit_orientations")

    for orbit_class, color in zip(selected, colors):
        candidates = [
            (dr, dc)
            for dr, dc in orbit_class
            if 1 <= ar + dr < len(grid)
            and 0 <= ac + dc < len(grid[0])
            and grid[ar + dr][ac + dc] == 0
        ]
        if not candidates:
            raise RuntimeError("no lawful orientation for selected orbit class")
        dr, dc = orientation_rng.choice(candidates)
        grid[ar + dr][ac + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, override-honest input grid."""
    _validate_overrides(overrides)
    user_overrides = dict(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(user_overrides),
    )
    slot = int(sample_index) % 4
    h, w, k, n_orbits = _draw_axes(
        ctx, _scheduled_defaults(ctx, sample_index, difficulty), user_overrides
    )

    grid = full_grid(h, w, 0)
    for col in _marker_columns(ctx, w, k, slot):
        grid[0][col] = 1

    anchor_r = ctx.draw_int("anchor_r", 2, h - 3)
    anchor_c = ctx.draw_int("anchor_c", 2, w - 3)
    grid[anchor_r][anchor_c] = 9
    _place_orbits(ctx, grid, (anchor_r, anchor_c), n_orbits)
    return grid


def _anchor_and_cells(grid: Sequence[Sequence[int]]):
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if not anchors:
        raise ValueError("grid has no color-9 anchor")
    anchor = anchors[0]
    cells = [
        (r, c, value)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value not in (0, 9)
    ]
    return anchor, cells


def _solve_with(
    grid: Sequence[Sequence[int]],
    *,
    k: int | None = None,
    cell_limit: int | None = None,
    turn: Callable[[int, int], tuple[int, int]] | None = None,
) -> list[list[int]]:
    """Pure Python mirror/rival engine; never used to create labels."""
    h, w = len(grid), len(grid[0])
    anchor, cells = _anchor_and_cells(grid)
    if cell_limit is not None:
        cells = cells[:cell_limit]
    if k is None:
        k = sum(value == 1 for value in grid[0])
    if turn is None:
        turn = lambda dr, dc: (dc, -dr)

    out = full_grid(h, w, 0)
    ar, ac = anchor
    out[ar][ac] = 9
    for row, col, color in cells:
        dr, dc = row - ar, col - ac
        for _ in range(k):
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = color
            dr, dc = turn(dr, dc)
    return out


def _solve_official(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    return _solve_with(grid)


def _left_prefix_count(grid):
    k = 0
    for value in grid[0]:
        if value != 1:
            break
        k += 1
    return _solve_with(grid, k=k)


def _first_two_orbits_only(grid):
    return _solve_with(grid, cell_limit=2)


def _opposite_rotation(grid):
    return _solve_with(grid, turn=lambda dr, dc: (-dc, dr))


def _always_four_turns(grid):
    return _solve_with(grid, k=4)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis directly from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "k": sum(value == 1 for value in grid[0]),
        "n_orbits": sum(
            value not in (0, 1, 9)
            for row in grid[1:]
            for value in row
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete constructive manifold, not just coarse counts."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    h, w = len(grid), width
    errors: list[str] = []
    if not 5 <= h <= 14:
        errors.append(f"grid_h={h} outside [5,14]")
    if not 5 <= w <= 16:
        errors.append(f"grid_w={w} outside [5,16]")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 may contain only background 0 and count marker 1")
    k = sum(value == 1 for value in grid[0])
    if not 1 <= k <= 4:
        errors.append(f"row 0 has {k} color-1 markers (expect 1..4)")
    if any(value == 1 for row in grid[1:] for value in row):
        errors.append("color-1 count markers must not occur below row 0")

    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        errors.append(f"grid has {len(anchors)} color-9 anchors (expect exactly 1)")
        return errors
    ar, ac = anchors[0]
    if not (2 <= ar <= h - 3 and 2 <= ac <= w - 3):
        errors.append("color-9 anchor must have a two-cell rotation margin")

    orbit = [
        (r, c, value)
        for r in range(1, h)
        for c, value in enumerate(grid[r])
        if value not in (0, 1, 9)
    ]
    if not 1 <= len(orbit) <= 5:
        errors.append(f"grid has {len(orbit)} orbit seeds (expect 1..5)")
    colors = [value for _, _, value in orbit]
    if len(set(colors)) != len(colors):
        errors.append("orbit seed colors must be distinct")

    classes: list[tuple[int, int]] = []
    for row, col, _ in orbit:
        dr, dc = row - ar, col - ac
        if (dr, dc) == (0, 0) or max(abs(dr), abs(dc)) > 2:
            errors.append("every orbit seed must be a nonzero offset within radius 2")
            continue
        classes.append(_rotation_class((dr, dc)))
    if len(set(classes)) != len(classes):
        errors.append("orbit seeds must occupy distinct quarter-turn rotation classes")
    return errors


def strict_canonical_like(grid):
    """A lawful instance of this task's declared semantic manifold."""
    return self_check(grid)


SEMANTIC_RIVALS = {
    "left_prefix_count": _left_prefix_count,
    "first_two_orbits_only": _first_two_orbits_only,
    "opposite_rotation": _opposite_rotation,
    "always_four_turns": _always_four_turns,
}
CANONICAL_SHORTCUTS = {
    "left_prefix_count": _left_prefix_count,
    "first_two_orbits_only": _first_two_orbits_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _differs_from(rival_name: str):
    def witness(grid) -> bool:
        return SEMANTIC_RIVALS[rival_name](grid) != _solve_official(grid)

    return witness


SEMANTIC_WITNESSES = {
    "nonprefix_header": _differs_from("left_prefix_count"),
    "more_than_two_orbits": _differs_from("first_two_orbits_only"),
    "rotation_direction": _differs_from("opposite_rotation"),
    "count_controls_turns": _differs_from("always_four_turns"),
}
WITNESS_RIVALS = {
    "nonprefix_header": ["left_prefix_count"],
    "more_than_two_orbits": ["first_two_orbits_only"],
    "rotation_direction": ["opposite_rotation"],
    "count_controls_turns": ["always_four_turns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that a four-demo lesson determines this query against named rivals."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demos, got {len(demos)}")

    observed_k: set[int] = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        issues = self_check(grid)
        if issues:
            reasons.append(f"demo {index} is outside the manifold: {issues[0]}")
            continue
        observed_k.add(observe_overrides(grid)["k"])
        if _solve_official(grid) != output:
            reasons.append(f"demo {index} output disagrees with the pinned rule mirror")

    if observed_k != {1, 2, 3, 4}:
        reasons.append(f"demos cover k={sorted(observed_k)}, expected [1, 2, 3, 4]")

    query_grid = query.get("input")
    query_output = query.get("output")
    query_issues = self_check(query_grid)
    if query_issues:
        reasons.append(f"query is outside the manifold: {query_issues[0]}")
        return reasons
    official_query = _solve_official(query_grid)
    if official_query != query_output:
        reasons.append("query output disagrees with the pinned rule mirror")

    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query_grid) != query_output
        except Exception as exc:  # contract surfaces rival defects, never hides them
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
