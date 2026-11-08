"""Generator for arc_additional_puzzle_bank_volume3:E18.

Lawful inputs contain at least two cardinally isolated red (2) singleton
cells.  Every target has an empty in-bounds cell immediately to its right.
The rule moves each target right by one cell and clears its old position.
Non-red distractors and multi-cell red components are preserved.

The five-sample schedule is deliberate: canonical-like, both distractors,
red-blob distractor, both distractors, then plain generalized. Every three
consecutive scenes therefore include shortcut-rebutting distractors.  A normal
three-demo lesson therefore rebuts copy-instead-of-move, move-all-colours, and
move-all-red shortcuts before its query.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e58953aee67a"
VERSION = "3.0.0"
TASK_ID = "e58953aee67a"
RULE_HASH = "cd1152500732"

SUMMARY = (
    "On a black background, every cardinally isolated red (2) singleton with "
    "an empty in-bounds right neighbour moves exactly one column right. "
    "Multi-cell red components and non-red distractors stay fixed. Default "
    "lessons deliberately include canonical-only and shortcut-rebutting scenes."
)

INVARIANTS = [
    "background is 0",
    "every isolated red singleton has an empty in-bounds right destination",
    "at least two movable red singleton targets are present",
    "red multi-cell components and non-red cells are distractors, not targets",
    "simultaneous target moves cannot collide",
]

# Only exact, recoverable properties are public axes.  The older palette_kind,
# palette_size, position_bias, density, and texture entries were inert metadata.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "4..20"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "4..20"},
    "n_singletons": {"type": "int", "default": "difficulty-aware", "valid": "2..12"},
}

CANONICAL_PROFILES = ((7, 8), (7, 9), (8, 9))
MIN_STRICT_FRAC = 0.15
EXAMPLES_NEEDED = 3
_SCENE_SCHEDULE = ("canonical", "both", "red_blob", "both", "plain")
_NONRED_COLORS = (1, 4, 8)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (7, 10), (8, 11), (2, 5)
    if difficulty == "hard":
        return (12, 20), (12, 20), (7, 12)
    return (9, 14), (9, 14), (4, 8)


def _target_capacity(height: int, width: int) -> int:
    """Capacity of the parity lattice used for isolated movable targets."""
    return sum(
        1
        for row in range(height)
        for col in range(width - 1)
        if (row + col) % 2 == 0
    )


def _minimum_height(width: int, targets: int) -> int:
    for height in range(4, 21):
        if _target_capacity(height, width) >= targets:
            return height
    return 21


def _minimum_width(height: int, targets: int) -> int:
    for width in range(4, 21):
        if _target_capacity(height, width) >= targets:
            return width
    return 21


def _draw_geometry(ctx, difficulty: Any, overrides: dict[str, Any], sample_index: int):
    exact = {
        name
        for name in AXES
        if name in overrides and overrides[name] is not None
    }
    canonical_scene = not exact and sample_index % len(_SCENE_SCHEDULE) == 0
    if canonical_scene:
        profile = ctx.draw_choice("canonical_profile", CANONICAL_PROFILES)
        height = ctx.draw_int("grid_h", profile[0], profile[0])
        width = ctx.draw_int("grid_w", profile[1], profile[1])
        targets = ctx.draw_int("n_singletons", 5, 5)
        return height, width, targets, "canonical"

    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _band_ranges(difficulty)
    requested_targets = (
        int(overrides["n_singletons"])
        if "n_singletons" in overrides and overrides["n_singletons"] is not None
        else None
    )

    if "grid_h" in exact:
        height = ctx.draw_int("grid_h", 4, 20)
    elif "grid_w" in exact and requested_targets is not None:
        requested_width = int(overrides["grid_w"])
        needed = _minimum_height(requested_width, requested_targets)
        if needed > 20:
            raise ValueError(
                f"grid_w={requested_width} cannot host n_singletons={requested_targets}"
            )
        height = ctx.draw_int("grid_h", max(h_lo, needed), max(h_hi, needed))
    else:
        height = ctx.draw_int("grid_h", h_lo, h_hi)

    if "grid_w" in exact:
        width = ctx.draw_int("grid_w", 4, 20)
    elif requested_targets is not None:
        needed = _minimum_width(height, requested_targets)
        if needed > 20:
            raise ValueError(
                f"grid_h={height} cannot host n_singletons={requested_targets}"
            )
        width = ctx.draw_int("grid_w", max(w_lo, needed), max(w_hi, needed))
    else:
        width = ctx.draw_int("grid_w", w_lo, w_hi)

    capacity = _target_capacity(height, width)
    if requested_targets is not None:
        targets = ctx.draw_int("n_singletons", 2, 12)
        if targets > capacity:
            raise ValueError(
                f"grid {height}x{width} has isolated-target capacity {capacity}, "
                f"below n_singletons={targets}"
            )
    else:
        high = min(n_hi, capacity, 12)
        if high < 2:
            raise ValueError(f"grid {height}x{width} cannot host two movable singletons")
        low = min(max(2, n_lo), high)
        targets = ctx.draw_int("n_singletons", low, high)

    scene = _SCENE_SCHEDULE[sample_index % len(_SCENE_SCHEDULE)]
    if scene == "canonical":
        scene = "plain"
    return height, width, targets, scene


def _blob_candidates(height: int, width: int, rng) -> list[set[tuple[int, int]]]:
    # Every blob must have a one-column right margin.  A blob flush against
    # the right edge is observationally inert under the plausible "move every
    # red cell right when possible" rival, so it cannot teach singleton-only
    # selection.
    max_anchor_col = width - 3
    anchors = list(dict.fromkeys([
        (0, 0),
        (max(0, height - 2), 0),
        (max(0, height // 2 - 1), min(max_anchor_col, max(0, width // 2 - 1))),
        (0, max_anchor_col),
        (max(0, height - 2), max_anchor_col),
    ]))
    rng.shuffle(anchors)
    out: list[set[tuple[int, int]]] = []
    for row, col in anchors:
        cells = {
            (row, col),
            (row + 1, col),
            (row, col + 1),
            (row + 1, col + 1),
        }
        if all(0 <= r < height and 0 <= c < width for r, c in cells):
            out.append(cells)
    return out


def _target_candidates(
    height: int,
    width: int,
    blob: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    forbidden = set(blob)
    for row, col in blob:
        forbidden.update((row + dr, col + dc) for dr, dc in _CARDINAL)
    candidates = []
    for row in range(height):
        for col in range(width - 1):
            if (row + col) % 2:
                continue
            if (row, col) in forbidden or (row, col + 1) in blob:
                continue
            candidates.append((row, col))
    return candidates


def _choose_targets(candidates: list[tuple[int, int]], count: int, rng):
    if len(candidates) < count:
        raise ValueError(f"only {len(candidates)} legal target cells for requested {count}")
    remaining = list(candidates)
    rng.shuffle(remaining)
    selected = [remaining.pop()]
    while len(selected) < count:
        best_score = max(
            min(abs(r - rr) + abs(c - cc) for rr, cc in selected)
            for r, c in remaining
        )
        best = [
            cell
            for cell in remaining
            if min(abs(cell[0] - rr) + abs(cell[1] - cc) for rr, cc in selected)
            == best_score
        ]
        choice = rng.choice(best)
        selected.append(choice)
        remaining.remove(choice)
    return selected


def _add_nonred_distractors(grid, forbidden: set[tuple[int, int]], rng) -> None:
    height, width = len(grid), len(grid[0])
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
        if grid[row][col] == 0
        and (row, col) not in forbidden
        and (row, col + 1) not in forbidden
        and grid[row][col + 1] == 0
    ]
    rng.shuffle(candidates)
    used: list[tuple[int, int]] = []
    for color in _NONRED_COLORS[: min(2, len(candidates))]:
        choices = [
            cell
            for cell in candidates
            if all(abs(cell[0] - r) + abs(cell[1] - c) > 1 for r, c in used)
        ]
        if not choices:
            break
        cell = choices[0]
        grid[cell[0]][cell[1]] = color
        used.append(cell)
        candidates.remove(cell)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, target_count, scene = _draw_geometry(
        ctx, difficulty, overrides, sample_index
    )
    rng = ctx.draw_rng("layout")

    want_blob = scene in ("red_blob", "both")
    blob: set[tuple[int, int]] = set()
    if want_blob:
        for candidate in _blob_candidates(height, width, rng):
            if len(_target_candidates(height, width, candidate)) >= target_count:
                blob = candidate
                break

    candidates = _target_candidates(height, width, blob)
    targets = _choose_targets(candidates, target_count, rng)
    grid = full_grid(height, width, 0)
    for row, col in targets:
        grid[row][col] = 2
    for row, col in blob:
        grid[row][col] = 2

    if scene in ("nonred", "both"):
        forbidden = set(targets) | {(r, c + 1) for r, c in targets} | blob
        _add_nonred_distractors(grid, forbidden, rng)
    return grid


def _components_of_color(grid, color: int) -> list[set[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        components.append(component)
    return components


def _analysis(grid) -> dict[str, Any]:
    if not grid or not grid[0]:
        return {"errors": ["empty grid"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    height = len(grid)
    errors = []
    bad = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        errors.append("grid values must be ARC colours 0..9")
    red_components = _components_of_color(grid, 2) if not bad else []
    singletons = [next(iter(component)) for component in red_components if len(component) == 1]
    blobs = [component for component in red_components if len(component) > 1]
    movable = []
    for row, col in singletons:
        if col >= width - 1:
            errors.append(f"isolated red singleton at {(row, col)} is on the right edge")
        elif grid[row][col + 1] != 0:
            errors.append(
                f"isolated red singleton at {(row, col)} has blocked right destination"
            )
        else:
            movable.append((row, col))
    if len(movable) < 2:
        errors.append(f"too few movable isolated red singletons ({len(movable)})")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "red_components": red_components,
        "singletons": singletons,
        "movable": movable,
        "blobs": blobs,
        "nonred": [
            (row, col, grid[row][col])
            for row in range(height)
            for col in range(width)
            if grid[row][col] not in (0, 2)
        ],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return {name: value for name, value in nested.items() if name in AXES}
    return {name: value for name, value in meta.items() if name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/rule-hiding scenes and verify exact requested axes."""
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


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_singletons": len(analysis["movable"]),
    }


def rule_mirror(grid):
    """Python mirror of the current Racket program; Racket stays authoritative."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    components = _components_of_color(grid, 2)
    singletons = [next(iter(component)) for component in components if len(component) == 1]
    output = [list(row) for row in grid]
    for row, col in singletons:
        output[row][col] = 0
    for row, col in singletons:
        target = col + 1
        if target < width and grid[row][target] == 0:
            output[row][target] = 2
    return output


def strict_canonical_like(grid) -> list[str]:
    """Exact linked empirical manifold of the three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) not in CANONICAL_PROFILES:
        reasons.append("dimensions are not one of canonical 7x8, 7x9, or 8x9")
    if analysis["palette"] != (0, 2):
        reasons.append("canonical palette is exactly {0,2}")
    if len(analysis["movable"]) != 5:
        reasons.append("canonical inputs contain exactly five movable red singletons")
    if analysis["blobs"]:
        reasons.append("canonical inputs contain no multi-cell red component")
    return reasons


def _witness_canonical_profile(grid) -> bool:
    return not strict_canonical_like(grid)


def _witness_nonred_distractor(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["nonred"])


def _witness_red_blob(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and bool(analysis["blobs"])
        and _competitor_move_all_red(grid) != rule_mirror(grid)
    )


def _witness_border_and_spread(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    rows = {row for row, _ in analysis["movable"]}
    cols = {col for _, col in analysis["movable"]}
    return (
        len(rows) >= 2
        and len(cols) >= 2
        and any(col in (0, analysis["width"] - 2) for _, col in analysis["movable"])
    )


SEMANTIC_WITNESSES = {
    "exact_canonical_profile": _witness_canonical_profile,
    "nonred_distractor_rebuts_move_all_colours": _witness_nonred_distractor,
    "red_blob_rebuts_move_all_red": _witness_red_blob,
    "targets_span_rows_columns_and_reach_horizontal_border": _witness_border_and_spread,
}


def _competitor_copy_targets(grid):
    output = [list(row) for row in grid]
    for row, col in _analysis(grid)["movable"]:
        output[row][col + 1] = 2
    return output


def _competitor_shift_left(grid):
    analysis = _analysis(grid)
    output = [list(row) for row in grid]
    for row, col in analysis["movable"]:
        output[row][col] = 0
        if col > 0 and grid[row][col - 1] == 0:
            output[row][col - 1] = 2
    return output


def _competitor_move_all_nonzero(grid):
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            target = col + 1 if col + 1 < width and grid[row][col + 1] == 0 else col
            output[row][target] = value
    return output


def _competitor_move_all_red(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    red = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2]
    for row, col in red:
        output[row][col] = 0
    for row, col in red:
        target = col + 1
        if target < width and grid[row][target] == 0:
            output[row][target] = 2
        else:
            output[row][col] = 2
    return output


_LESSON_COMPETITORS = {
    "copy each target instead of moving it": _competitor_copy_targets,
    "move isolated targets left instead of right": _competitor_shift_left,
    "move every nonzero cell right": _competitor_move_all_nonzero,
    "move every red cell, including red blobs": _competitor_move_all_red,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a materialized lesson when a plausible rival changes the query."""
    reasons: list[str] = []
    if len(demos) < 3:
        return ["need three sequential demonstrations for the scheduled lesson"]
    for index, pair in enumerate(demos):
        if pair.get("output") != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} does not match the isolated-red move rule")
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the isolated-red move rule")
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
