"""Generator for S11_H3 — select an object's boundary by header hole count.

The number of blue cells in row 0 is ``k``.  Scan the distinct-colored body
components in row-major order and choose the first component with exactly
``k`` enclosed background regions.  Return only that component's boundary,
tightly cropped and recolored cyan (8).

The first canonical training pair contains two one-hole matches with different
answers, so ordered tie-breaking is part of the rule rather than a degenerate
case.  Generated lessons schedule that branch once every four samples.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4dd0b3ed33ee"
TASK_ID = "4dd0b3ed33ee"
VERSION = "3.0.0"
RULE_HASH = "a404f37f28fc"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid has 1..3 blue count markers anywhere in row 0. "
    "Rows below contain 2..5 isolated, distinctly colored components. Count "
    "the enclosed 0-regions in each component, scan components in row-major "
    "order, and select the first component whose hole count equals the blue "
    "marker count. Crop to that component's bounding box, erase every "
    "non-boundary component cell, and recolor the retained boundary cyan (8). "
    "Some lessons contain two matching components with different boundary "
    "masks, so the canonical first-match tie rule is observable."
)

INVARIANTS = [
    "row 0 contains only 0 and exactly 1..3 blue(1) count markers",
    "the body contains 2..5 cardinally separated components in distinct non-{0,1,8} colors",
    "one or two components have hole count equal to the header count",
    "when two components match, their cyan boundary crops differ and the row-major first match wins",
    "the output is the selected component's tight cyan boundary crop, not its whole filled crop",
]

# Only exact quantities recoverable from the returned grid are declared.  The
# previous palette/texture/density aliases were dead metadata and made the
# override matrix claim dimensions the generator did not actually honor.
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 5..14", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 15..22", "valid": "15..22"},
    "n_ones": {"type": "int", "default": "difficulty-weighted 1..3", "valid": "1..3"},
}

# Every Cartesian combination of the declared axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BODY_COLORS = (2, 3, 4, 5, 6, 7, 9)
Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _boundary_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cell_set = set(cells)
    return tuple(
        sorted(
            (r, c)
            for r, c in cell_set
            if any((r + dr, c + dc) not in cell_set for dr, dc in _CARD)
        )
    )


def _hole_count(cells: Iterable[tuple[int, int]]) -> int:
    """Count background components enclosed inside the object's tight bbox."""
    cell_set = set(cells)
    if not cell_set:
        return 0
    rows = [r for r, _ in cell_set]
    cols = [c for _, c in cell_set]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    background = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cell_set
    }
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in sorted(background):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        touches_edge = False
        while queue:
            r, c = queue.popleft()
            if r in (r0, r1) or c in (c0, c1):
                touches_edge = True
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in background and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_edge:
            holes += 1
    return holes


def _shape_output(shape: Shape) -> list[list[int]]:
    h, w = _shape_dims(shape)
    out = full_grid(h, w, 0)
    for r, c in _boundary_cells(shape):
        out[r][c] = 8
    return out


def _build_shape_bank() -> dict[int, tuple[Shape, ...]]:
    """Build a compact deterministic bank for 0..3-hole components.

    Earlier repair drafts enumerated every legal hole combination, which made
    import-time validation needlessly expensive.  A small, deliberately varied
    sample per rectangle is enough to exercise topology, crop shape, area, and
    ordered-tie semantics while keeping every validator fast.
    """
    bank: dict[int, set[Shape]] = {0: set(), 1: set(), 2: set(), 3: set()}

    zero_shapes = (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
    )
    for shape in zero_shapes:
        bank[0].add(_normalize(shape))
    for rh in range(2, 6):
        for rw in range(2, 8):
            bank[0].add(tuple((r, c) for r in range(rh) for c in range(rw)))

    for rh in range(3, 8):
        for rw in range(3, 10):
            all_cells = {(r, c) for r in range(rh) for c in range(rw)}
            interior = [(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)]
            for holes in (1, 2, 3):
                chosen: set[tuple[tuple[int, int], ...]] = set()
                for parity in (0, 1):
                    candidates = [p for p in interior if (p[0] + p[1]) % 2 == parity]
                    if len(candidates) < holes:
                        continue
                    combos = combinations(candidates, holes)
                    for removed in combos:
                        chosen.add(tuple(removed))
                        if len(chosen) >= 8:
                            break
                    chosen.add(tuple(candidates[:holes]))
                    chosen.add(tuple(candidates[-holes:]))
                    if holes == 1:
                        chosen.add((candidates[len(candidates) // 2],))
                    elif len(candidates) >= holes + 2:
                        step = (len(candidates) - 1) / (holes - 1)
                        spread = tuple(candidates[round(i * step)] for i in range(holes))
                        chosen.add(spread)
                for removed in chosen:
                    shape = tuple(sorted(all_cells - set(removed)))
                    if _hole_count(shape) == holes:
                        bank[holes].add(shape)

    return {
        holes: tuple(
            sorted(
                shapes,
                key=lambda shape: (_shape_dims(shape), len(shape), _shape_output(shape)),
            )
        )
        for holes, shapes in bank.items()
    }


_SHAPES = _build_shape_bank()


def _weighted_axis(ctx, label: str, all_values: Iterable[int], preferred: Iterable[int]) -> int:
    values = tuple(all_values)
    preferred = tuple(preferred)
    if ctx.difficulty == "easy":
        options = preferred * 7 + values
    elif ctx.difficulty == "hard":
        options = preferred * 2 + values * 2
    else:
        options = preferred * 4 + values
    return int(ctx.draw_choice(label, options))


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    """Return same-color body components in row-major order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for r0 in range(1, h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color in (0, 1) or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells_t = tuple(sorted(cells))
            rows = [r for r, _ in cells_t]
            cols = [c for _, c in cells_t]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            local = _normalize(cells_t)
            components.append(
                {
                    "color": color,
                    "cells": cells_t,
                    "local": local,
                    "bbox": bbox,
                    "holes": _hole_count(local),
                    "boundary": _boundary_cells(cells_t),
                    "output": _shape_output(local),
                }
            )
    components.sort(key=lambda obj: min(obj["cells"]))
    return components


def _analysis(grid: list[list[int]]) -> tuple[int, list[dict[str, object]], list[dict[str, object]]]:
    k = sum(value == 1 for value in grid[0])
    components = _components(grid)
    matches = [obj for obj in components if obj["holes"] == k]
    return k, components, matches


def oracle_output(grid: list[list[int]]) -> list[list[int]]:
    """Python diagnostic mirror; the canonical Racket program is authoritative."""
    _, _, matches = _analysis(grid)
    if not matches:
        raise ValueError("no body component has the header hole count")
    return [row[:] for row in matches[0]["output"]]


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_ones": sum(value == 1 for value in grid[0]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    h = len(grid)
    errors: list[str] = []
    if not (5 <= h <= 14 and 15 <= w <= 22):
        errors.append(f"grid dimensions {h}x{w} are outside the task envelope")
    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 may contain only background and blue count markers")
    k = sum(value == 1 for value in grid[0])
    if not 1 <= k <= 3:
        errors.append(f"row 0 must contain 1..3 blue markers, got {k}")
    if any(grid[r][c] == 1 for r in range(1, h) for c in range(w)):
        errors.append("blue count-marker cells may not appear in the body")
    if any(grid[r][c] == 8 for r in range(1, h) for c in range(w)):
        errors.append("cyan is reserved for the output and may not leak into the body")

    components = _components(grid)
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 body components, got {len(components)}")
    colors = [int(obj["color"]) for obj in components]
    if len(colors) != len(set(colors)):
        errors.append("body components must use distinct colors")
    if any(color in (0, 1, 8) for color in colors):
        errors.append("body component colors must exclude 0, 1, and 8")

    # Different colors remain separate components in the Racket runtime, but
    # touching them creates a task-extraneous segmentation shortcut.  Require a
    # cardinal gap between every pair.
    for left in range(len(components)):
        a = set(components[left]["cells"])
        for right in range(left + 1, len(components)):
            b = set(components[right]["cells"])
            if any((r + dr, c + dc) in b for r, c in a for dr, dc in _CARD):
                errors.append("different body components may not touch cardinally")
                break

    hole_counts = [int(obj["holes"]) for obj in components]
    if any(not 0 <= holes <= 3 for holes in hole_counts):
        errors.append(f"body hole counts must stay in 0..3, got {hole_counts}")
    matches = [obj for obj in components if obj["holes"] == k]
    if len(matches) not in (1, 2):
        errors.append(f"expected one or two k={k} hole matches, got {len(matches)}")
    elif len(matches) == 2 and matches[0]["output"] == matches[1]["output"]:
        errors.append("two-match branch must give first and last matches different answers")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _candidate_output(grid: list[list[int]], mode: str):
    _, components, matches = _analysis(grid)
    if not components:
        return None
    selected = matches[0] if matches else None
    if mode == "official":
        return selected["output"] if selected else None
    if mode == "last_match":
        return matches[-1]["output"] if matches else None
    if mode == "first_object":
        return components[0]["output"]
    if mode == "largest_area":
        return max(components, key=lambda obj: len(obj["cells"]))["output"]
    if mode == "smallest_area":
        return min(components, key=lambda obj: len(obj["cells"]))["output"]
    if mode == "leftmost":
        return min(components, key=lambda obj: min(c for _, c in obj["cells"]))["output"]
    if mode == "rightmost":
        return max(components, key=lambda obj: max(c for _, c in obj["cells"]))["output"]
    if mode == "lowest_color":
        return min(components, key=lambda obj: obj["color"])["output"]
    if mode == "highest_color":
        return max(components, key=lambda obj: obj["color"])["output"]
    if mode == "whole_object":
        if selected is None:
            return None
        local = selected["local"]
        sh, sw = _shape_dims(local)
        out = full_grid(sh, sw, 0)
        for r, c in local:
            out[r][c] = 8
        return out
    raise ValueError(mode)


_RIVAL_NAMES = (
    "last_match",
    "first_object",
    "largest_area",
    "smallest_area",
    "leftmost",
    "rightmost",
    "lowest_color",
    "highest_color",
    "whole_object",
)

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]] | None]] = {
    name: (lambda grid, mode=name: _candidate_output(grid, mode))
    for name in _RIVAL_NAMES
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "last_match": SEMANTIC_RIVALS["last_match"],
    "first_object": SEMANTIC_RIVALS["first_object"],
    "largest_area": SEMANTIC_RIVALS["largest_area"],
    "whole_object": SEMANTIC_RIVALS["whole_object"],
}


def _selected(grid):
    _, components, matches = _analysis(grid)
    return components, matches, (matches[0] if matches else None)


def _w_unique(grid) -> bool:
    return len(_analysis(grid)[2]) == 1


def _w_ordered_tie(grid) -> bool:
    matches = _analysis(grid)[2]
    return len(matches) == 2 and matches[0]["output"] != matches[1]["output"]


def _w_not_first(grid) -> bool:
    components, _, selected = _selected(grid)
    return bool(
        selected
        and selected is not components[0]
        and components[0]["output"] != selected["output"]
    )


def _w_not_largest(grid) -> bool:
    components, _, selected = _selected(grid)
    return bool(
        selected
        and any(
            len(obj["cells"]) > len(selected["cells"])
            and obj["output"] != selected["output"]
            for obj in components
        )
    )


def _w_not_smallest(grid) -> bool:
    components, _, selected = _selected(grid)
    return bool(
        selected
        and any(
            len(obj["cells"]) < len(selected["cells"])
            and obj["output"] != selected["output"]
            for obj in components
        )
    )


def _w_middle_color(grid) -> bool:
    components, _, selected = _selected(grid)
    if not selected or len(components) < 3:
        return False
    low = min(components, key=lambda obj: obj["color"])
    high = max(components, key=lambda obj: obj["color"])
    return bool(
        selected not in (low, high)
        and (low["output"] != selected["output"] or high["output"] != selected["output"])
    )


def _w_has_interior(grid) -> bool:
    _, _, selected = _selected(grid)
    return bool(selected and len(selected["cells"]) > len(selected["boundary"]))


def _w_all_boundary(grid) -> bool:
    _, _, selected = _selected(grid)
    return bool(selected and len(selected["cells"]) == len(selected["boundary"]))


def _w_k(expected: int):
    return lambda grid: sum(value == 1 for value in grid[0]) == expected


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "header_k_1": _w_k(1),
    "header_k_2": _w_k(2),
    "header_k_3": _w_k(3),
    "unique_match": _w_unique,
    "two_matches_first_wins": _w_ordered_tie,
    "selected_not_first_object": _w_not_first,
    "selected_not_largest": _w_not_largest,
    "selected_not_smallest": _w_not_smallest,
    "selected_color_not_extreme": _w_middle_color,
    "selected_has_nonboundary_interior": _w_has_interior,
    "selected_all_cells_are_boundary": _w_all_boundary,
}

WITNESS_RIVALS = {
    "two_matches_first_wins": ["last_match"],
    "selected_not_first_object": ["first_object", "leftmost"],
    "selected_not_largest": ["largest_area"],
    "selected_not_smallest": ["smallest_area"],
    "selected_color_not_extreme": ["lowest_color", "highest_color"],
    "selected_has_nonboundary_interior": ["whole_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    official_query = _candidate_output(query["input"], "official")
    errors: list[str] = []
    for rival in _RIVAL_NAMES:
        if all(_candidate_output(demo["input"], rival) == demo["output"] for demo in demos):
            rival_query = _candidate_output(query["input"], rival)
            if rival_query != official_query:
                errors.append(f"demos do not rule out rival operation {rival}")
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % 4


SCHEDULE_PROFILES = (0, 1, 2, 3)


def _feasible_shapes(holes: int, body_h: int, width: int) -> list[Shape]:
    return [
        shape
        for shape in _SHAPES[holes]
        if _shape_dims(shape)[0] <= body_h and _shape_dims(shape)[1] <= width
    ]


def _pick(rng, choices: Iterable[Shape]) -> Shape:
    choices = tuple(choices)
    if not choices:
        raise ValueError("no feasible shape for requested semantic role")
    return choices[rng.randrange(len(choices))]


def _partition_shelves(shapes: list[Shape], body_h: int, width: int):
    """Enumerate contiguous shelf partitions that preserve row-major order."""
    n = len(shapes)
    feasible = []
    for mask in range(1 << max(0, n - 1)):
        shelves: list[list[Shape]] = [[]]
        for index, shape in enumerate(shapes):
            shelves[-1].append(shape)
            if index < n - 1 and mask & (1 << index):
                shelves.append([])
        widths = [sum(_shape_dims(s)[1] for s in shelf) + len(shelf) - 1 for shelf in shelves]
        heights = [max(_shape_dims(s)[0] for s in shelf) for shelf in shelves]
        if max(widths) <= width and sum(heights) + len(shelves) - 1 <= body_h:
            feasible.append((shelves, widths, heights))
    return feasible


def _spread_slack(slack: int, slots: int, rng) -> list[int]:
    buckets = [0] * slots
    for _ in range(slack):
        buckets[rng.randrange(slots)] += 1
    return buckets


def _pack_ordered(shapes: list[Shape], body_h: int, width: int, rng):
    feasible = _partition_shelves(shapes, body_h, width)
    if not feasible:
        return None
    shelves, shelf_widths, shelf_heights = feasible[rng.randrange(len(feasible))]
    row_slack = body_h - (sum(shelf_heights) + len(shelves) - 1)
    row_extra = _spread_slack(row_slack, len(shelves) + 1, rng)
    placements: list[tuple[int, int, Shape]] = []
    row = row_extra[0]
    for shelf_index, shelf in enumerate(shelves):
        col_slack = width - shelf_widths[shelf_index]
        col_extra = _spread_slack(col_slack, len(shelf) + 1, rng)
        col = col_extra[0]
        for index, shape in enumerate(shelf):
            placements.append((row, col, shape))
            col += _shape_dims(shape)[1] + 1 + col_extra[index + 1]
        row += shelf_heights[shelf_index] + 1 + row_extra[shelf_index + 1]
    return placements


def _shape_with_property(candidates: list[Shape], rng, property_name: str) -> Shape:
    if property_name == "all_boundary":
        preferred = [shape for shape in candidates if len(shape) == len(_boundary_cells(shape))]
    elif property_name == "has_interior":
        preferred = [shape for shape in candidates if len(shape) > len(_boundary_cells(shape))]
    elif property_name == "small":
        min_area = min(map(len, candidates))
        preferred = [shape for shape in candidates if len(shape) <= min_area + 2]
    elif property_name == "large":
        max_area = max(map(len, candidates))
        preferred = [shape for shape in candidates if len(shape) >= max_area - 2]
    else:
        preferred = candidates
    return _pick(rng, preferred or candidates)


def _decoy_candidates(k: int, body_h: int, width: int) -> list[Shape]:
    return [
        shape
        for holes in (0, 1, 2, 3)
        if holes != k
        for shape in _feasible_shapes(holes, body_h, width)
    ]


def _candidate_order(candidates: Iterable[Shape], rng, *, compact_limit: int = 72) -> list[Shape]:
    """Return a varied but bounded candidate list, biased toward packability."""
    ordered = sorted(
        set(candidates),
        key=lambda shape: (
            _shape_dims(shape)[0] * _shape_dims(shape)[1],
            _shape_dims(shape),
            len(shape),
            _shape_output(shape),
        ),
    )
    compact_n = max(1, compact_limit - min(12, compact_limit // 3))
    window = ordered[:compact_n]
    # Retain a few large-area alternatives so anti-shortcut profiles can put a
    # larger decoy beside a compact selected component.  Deduplication keeps
    # the domain bounded and import/generation costs predictable.
    for shape in sorted(ordered, key=lambda item: (len(item), _shape_dims(item)), reverse=True)[: compact_limit - compact_n]:
        if shape not in window:
            window.append(shape)
    rng.shuffle(window)
    return window


def _try_scenes(scene_candidates: Iterable[list[Shape]], body_h: int, width: int, layout_rng):
    for shapes in scene_candidates:
        placements = _pack_ordered(shapes, body_h, width, layout_rng)
        if placements is not None:
            return shapes, placements
    return None


def _choose_scene(profile: int, k: int, body_h: int, width: int, rng, layout_rng):
    """Choose a useful scene with a bounded, early-exit pack search."""
    all_targets = _feasible_shapes(k, body_h, width)
    all_decoys = _decoy_candidates(k, body_h, width)
    targets = _candidate_order(all_targets, rng, compact_limit=48)
    decoys = _candidate_order(all_decoys, rng, compact_limit=48)
    if not targets or not decoys:
        raise ValueError("declared dimensions cannot fit the task's required shapes")

    if profile == 0:
        # Leading decoy + two distinct matches teaches both header selection and
        # row-major first-match tie-breaking.
        for first in targets[:16]:
            seconds = [s for s in targets[:32] if _shape_output(s) != _shape_output(first)]
            for second in seconds[:8]:
                for lead in decoys[:8]:
                    shapes = [lead, first, second]
                    placements = _pack_ordered(shapes, body_h, width, layout_rng)
                    if placements is not None:
                        return shapes, placements, 1
    elif profile == 1:
        preferred = [s for s in targets if len(s) == len(_boundary_cells(s))] or targets
        preferred = _candidate_order(preferred, rng, compact_limit=24)
        for target in preferred[:12]:
            larger = [s for s in decoys if len(s) > len(target)] or decoys
            smaller = [s for s in decoys if len(s) < len(target)] or decoys
            for a in larger[:8]:
                for b in smaller[:8]:
                    shapes = [target, a, b]
                    placements = _pack_ordered(shapes, body_h, width, layout_rng)
                    if placements is not None:
                        return shapes, placements, 0
    elif profile == 2:
        preferred = [s for s in targets if len(s) > len(_boundary_cells(s))] or targets
        preferred = _candidate_order(preferred, rng, compact_limit=24)
        for target in preferred[:12]:
            smaller = [s for s in decoys if len(s) < len(target)] or decoys
            larger = [s for s in decoys if len(s) > len(target)] or decoys
            for a in smaller[:8]:
                for b in larger[:8]:
                    shapes = [a, target, b]
                    placements = _pack_ordered(shapes, body_h, width, layout_rng)
                    if placements is not None:
                        return shapes, placements, 1
    else:
        preferred = sorted(targets[:32], key=len, reverse=True)
        for target in preferred[:12]:
            smaller = [s for s in decoys if len(s) < len(target)] or decoys
            for a in smaller[:8]:
                for b in (smaller[8:16] or smaller[:8]):
                    shapes = [a, b, target]
                    placements = _pack_ordered(shapes, body_h, width, layout_rng)
                    if placements is not None:
                        return shapes, placements, 2

    # Exact-axis fallback retains the rule but may omit an optional decoy on
    # the smallest legal canvas.
    if profile == 0:
        for first in targets:
            for second in targets:
                if _shape_output(second) == _shape_output(first):
                    continue
                shapes = [first, second]
                placements = _pack_ordered(shapes, body_h, width, layout_rng)
                if placements is not None:
                    return shapes, placements, 0
    else:
        if profile == 1:
            fallback_targets = [s for s in all_targets if len(s) == len(_boundary_cells(s))] or all_targets
        elif profile == 2:
            fallback_targets = [s for s in all_targets if len(s) > len(_boundary_cells(s))] or all_targets
        else:
            fallback_targets = sorted(all_targets, key=len, reverse=True)
        fallback_targets = sorted(
            fallback_targets,
            key=lambda shape: (_shape_dims(shape)[0] * _shape_dims(shape)[1], _shape_dims(shape), len(shape)),
        )
        for target in fallback_targets:
            if profile in (1, 2):
                # Preserve the crucial anti-shortcut lesson even when the
                # smallest canvas can fit only two components: the selected
                # component must not be the largest one.
                fallback_decoys = [s for s in all_decoys if len(s) > len(target)] or all_decoys
            else:
                fallback_decoys = [s for s in all_decoys if len(s) < len(target)] or all_decoys
            fallback_decoys = sorted(
                fallback_decoys,
                key=lambda shape: (_shape_dims(shape)[0] * _shape_dims(shape)[1], _shape_dims(shape), len(shape)),
            )
            for decoy in fallback_decoys:
                shapes = [target, decoy] if profile == 1 else [decoy, target]
                selected_index = 0 if profile == 1 else 1
                placements = _pack_ordered(shapes, body_h, width, layout_rng)
                if placements is not None:
                    return shapes, placements, selected_index

    raise ValueError(f"grid_h={body_h + 1}, grid_w={width}, n_ones={k} cannot pack a valid scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h_pref, w_pref, k_pref = (5, 6, 7), (15, 16, 18), (1,)
    elif difficulty == "hard":
        h_pref, w_pref, k_pref = (10, 12, 14), (18, 20, 22), (3,)
    else:
        h_pref, w_pref, k_pref = (5, 6, 8, 10), (15, 18, 20), (1, 2, 3)

    h = _weighted_axis(ctx, "grid_h", range(5, 15), h_pref)
    w = _weighted_axis(ctx, "grid_w", range(15, 23), w_pref)
    k = _weighted_axis(ctx, "n_ones", range(1, 4), k_pref)
    profile = sample_index % 4

    shape_rng = ctx.draw_rng("shapes")
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    shapes, placements, selected_index = _choose_scene(
        profile, k, h - 1, w, shape_rng, layout_rng
    )

    colors = sorted(palette_rng.sample(list(_BODY_COLORS), len(shapes)))
    assigned = list(colors)
    if len(shapes) >= 3:
        # Make the selected component's color non-extreme, independently of
        # shape/order, so color-based rivals receive explicit counterexamples.
        assigned[selected_index], assigned[1] = assigned[1], assigned[selected_index]

    grid = full_grid(h, w, 0)
    for col in layout_rng.sample(range(w), k):
        grid[0][col] = 1
    for (row0, col0, shape), color in zip(placements, assigned):
        for dr, dc in shape:
            grid[1 + row0 + dr][col0 + dc] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failure: {errors}")
    return grid
