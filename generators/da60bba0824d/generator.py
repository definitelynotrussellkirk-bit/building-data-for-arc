"""Generator for ``da60bba0824d`` — keep the largest green component.

The input contains two to four 4-connected color-3 components with distinct
cell counts.  The canonical Racket rule selects the unique largest component,
paints its cells color 9 on a fresh background-0 grid, and erases every other
component.

The distribution deliberately varies component count, canvas size, component
shape, reading-order rank, edge contact, diagonal-only contact, singleton
decoys, and bounding-box-area decoys.  Those cases rebut fixed-position,
8-connectivity, fixed-size, and largest-bounding-box shortcuts while keeping
the output authority exclusively in the canonical Racket program.
"""
from __future__ import annotations

import copy
from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da60bba0824d"
TASK_ID = "da60bba0824d"
VERSION = "2.0.0"
RULE_HASH = "881e1dbb1e82"

SUMMARY = (
    "Select the unique largest 4-connected color-3 component, recolor it 9, "
    "and erase every other component."
)

INVARIANTS = [
    "the grid is rectangular, uses only background 0 and component color 3, and keeps 0 modal",
    "there are 2-4 four-connected color-3 components with pairwise-distinct cell counts",
    "the unique largest component may occur at any reading-order rank and may touch an edge",
    "different components may touch diagonally but never orthogonally",
    "component size, not bounding-box area or position, determines the selected object",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng: easy 7..9, medium 8..10, hard 8..10",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng: easy 9..11, medium 10..12, hard 10..12",
        "valid": "9..14",
    },
    "n_motifs": {
        "type": "int",
        "default": "band rng: easy 2, medium 2..3, hard 3..4",
        "valid": "2..4",
    },
}

_VALID_H = (7, 12)
_VALID_W = (9, 14)
_VALID_N = (2, 4)
_BRANCH_COUNT = 7
EXAMPLES_NEEDED = _BRANCH_COUNT
MIN_STRICT_FRAC = 1.0

# Each base shape is 4-connected and fits in a 3x3 box.  D4 transforms below
# provide orientation diversity without making placement feasibility fragile.
_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
}


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(cells):
    variants = set()
    points = tuple(cells)
    for reflect in (False, True):
        for turns in range(4):
            transformed = []
            for r, c in points:
                x, y = r, -c if reflect else c
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _components(grid, color=3):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _bbox(component):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(component):
    r0, c0, r1, c1 = _bbox(component)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _reading_order(components):
    return sorted(components, key=lambda comp: min(comp))


def _touches_edge(component, h, w):
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in component)


def _has_diagonal_only_contact(components):
    cell_to_component = {
        cell: index for index, component in enumerate(components) for cell in component
    }
    for (r, c), index in cell_to_component.items():
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            other = cell_to_component.get((r + dr, c + dc))
            if other is not None and other != index:
                return True
    return False


def _analysis(grid):
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    components = _components(grid)
    ordered = _reading_order(components)
    largest = max(components, key=len)
    largest_rank = ordered.index(largest)
    largest_area = _bbox_area(largest)
    return {
        "errors": [],
        "components": components,
        "sizes": sorted(len(component) for component in components),
        "largest": largest,
        "largest_rank": largest_rank,
        "largest_first": largest_rank == 0,
        "largest_last": largest_rank == len(ordered) - 1,
        "largest_not_first": largest_rank > 0,
        "largest_not_last": largest_rank < len(ordered) - 1,
        "singleton_decoy": any(len(component) == 1 for component in components),
        "diagonal_only_contact": _has_diagonal_only_contact(components),
        "bbox_area_decoy": any(
            len(component) < len(largest) and _bbox_area(component) > largest_area
            for component in components
        ),
        "edge_largest": _touches_edge(largest, len(grid), len(grid[0])),
        "interior_largest": not _touches_edge(largest, len(grid), len(grid[0])),
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact semantic AXES value from the returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_motifs": len(_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding inputs while accepting all canonicals."""
    del difficulty, meta
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]

    h, w = len(grid), len(grid[0])
    errors = []
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")

    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or value not in (0, 3)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"palette must be exactly within {{0, 3}}, got {bad_values}")
        return errors

    components = _components(grid)
    if not (_VALID_N[0] <= len(components) <= _VALID_N[1]):
        errors.append(
            f"expected {_VALID_N[0]}..{_VALID_N[1]} green components, "
            f"found {len(components)}"
        )
    sizes = [len(component) for component in components]
    if any(size < 1 or size > 8 for size in sizes):
        errors.append(f"component sizes must lie in 1..8, got {sorted(sizes)}")
    if len(sizes) != len(set(sizes)):
        errors.append(f"component sizes must be pairwise distinct, got {sorted(sizes)}")
    if sizes and sizes.count(max(sizes)) != 1:
        errors.append("the largest component must be unique")

    nonzero = sum(sizes)
    if nonzero * 2 >= h * w:
        errors.append("background 0 must be strictly modal")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This teaching grammar is deliberately a strict canonical extension."""
    return self_check(grid)


def _branch_name(sample_index: int) -> str:
    return (
        "singleton_decoy",
        "largest_first",
        "largest_last",
        "diagonal_only_contact",
        "bbox_area_decoy",
        "edge_largest",
        "interior_largest",
    )[sample_index % _BRANCH_COUNT]


def _choose_sizes(rng, n_motifs, branch):
    if branch == "bbox_area_decoy":
        return {
            2: [5, 6],
            3: [1, 5, 6],
            4: [1, 3, 5, 6],
        }[n_motifs]

    largest = rng.randint(max(5, n_motifs + 1), 8)
    pool = list(range(1, min(largest, 5)))
    if branch == "singleton_decoy":
        chosen = [1]
        remaining = [value for value in pool if value != 1]
        chosen.extend(rng.sample(remaining, n_motifs - 2))
    else:
        chosen = rng.sample(pool, n_motifs - 1)
    return sorted(chosen + [largest])


def _shape_for(rng, size, branch):
    if branch == "bbox_area_decoy" and size == 5:
        base = _BASE_SHAPES[5][0]  # 3x3 L: area 9 with only five cells.
    elif branch == "bbox_area_decoy" and size == 6:
        base = _BASE_SHAPES[6][0]  # compact 2x3: area 6, but more cells.
    else:
        base = rng.choice(_BASE_SHAPES[size])
    return rng.choice(_shape_variants(base))


def _orthogonally_clear(cells, occupied):
    for r, c in cells:
        if (r, c) in occupied:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in occupied:
                return False
    return True


def _diagonally_adjacent(cells, occupied):
    return any(
        (r + dr, c + dc) in occupied
        for r, c in cells
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )


def _translated_candidates(shape, h, w, rng, *, edge=None, diagonal_to=None):
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    candidates = []
    for r0 in range(h - shape_h + 1):
        for c0 in range(w - shape_w + 1):
            cells = tuple((r0 + r, c0 + c) for r, c in shape)
            touches = _touches_edge(cells, h, w)
            if edge is True and not touches:
                continue
            if edge is False and touches:
                continue
            if diagonal_to is not None and not _diagonally_adjacent(cells, diagonal_to):
                continue
            candidates.append(cells)
    rng.shuffle(candidates)
    return candidates


def _layout(rng, h, w, sizes, branch):
    largest_size = max(sizes)
    for _ in range(160):
        shapes = {size: _shape_for(rng, size, branch) for size in sizes}
        order = list(sizes)
        rng.shuffle(order)
        occupied = set()
        placed = []

        for index, size in enumerate(order):
            edge = None
            if size == largest_size and branch == "edge_largest":
                edge = True
            elif size == largest_size and branch == "interior_largest":
                edge = False

            diagonal_to = occupied if branch == "diagonal_only_contact" and index == 1 else None
            candidates = _translated_candidates(
                shapes[size], h, w, rng, edge=edge, diagonal_to=diagonal_to
            )
            chosen = next(
                (cells for cells in candidates if _orthogonally_clear(cells, occupied)),
                None,
            )
            if chosen is None:
                break
            occupied.update(chosen)
            placed.append(chosen)
        else:
            grid = full_grid(h, w, 0)
            for component in placed:
                for r, c in component:
                    grid[r][c] = 3
            analysis = _analysis(grid)
            if analysis["errors"]:
                continue
            if branch == "largest_first" and not analysis["largest_first"]:
                continue
            if branch == "largest_last" and not analysis["largest_last"]:
                continue
            if branch in analysis and not analysis[branch]:
                continue
            return grid
    raise RuntimeError(
        f"could not place branch={branch!r}, dims={h}x{w}, sizes={sizes}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    if band == "easy":
        h_range, w_range, n_range = (7, 9), (9, 11), (2, 2)
    elif band == "hard":
        h_range, w_range, n_range = (8, 10), (10, 12), (3, 4)
    else:
        h_range, w_range, n_range = (8, 10), (10, 12), (2, 3)

    h = (
        ctx.draw_int("grid_h", *_VALID_H)
        if "grid_h" in overrides
        else ctx.draw_int("grid_h", *h_range)
    )
    w = (
        ctx.draw_int("grid_w", *_VALID_W)
        if "grid_w" in overrides
        else ctx.draw_int("grid_w", *w_range)
    )
    n_motifs = (
        ctx.draw_int("n_motifs", *_VALID_N)
        if "n_motifs" in overrides
        else ctx.draw_int("n_motifs", *n_range)
    )

    rng = ctx.draw_rng("layout")
    branch = _branch_name(sample_index)
    sizes = _choose_sizes(rng, n_motifs, branch)
    grid = _layout(rng, h, w, sizes, branch)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _selected_cells(pair):
    return {
        (r, c)
        for r, row in enumerate(pair["output"])
        for c, value in enumerate(row)
        if value == 9
    }


def _candidate_prediction(grid, selector):
    components = _components(grid)
    ordered = _reading_order(components)
    if selector == "first":
        return set(ordered[0])
    if selector == "last":
        return set(ordered[-1])
    if selector == "smallest":
        return set(min(components, key=len))
    if selector == "largest_bbox":
        return set(max(components, key=lambda component: (_bbox_area(component), min(component))))
    if selector == "all":
        return {cell for component in components for cell in component}
    raise ValueError(selector)


def lesson_identifiable(demos, query) -> list[str]:
    """Falsify a concrete family of plausible shortcut selectors.

    The seven-example schedule includes a largest-first case, a largest-last
    case, and a bounding-box-area decoy, so no listed rival should remain
    consistent with every demonstration while disagreeing on the query.
    """
    rivals = ("first", "last", "smallest", "largest_bbox", "all")
    reasons = []
    for rival in rivals:
        if all(
            _candidate_prediction(pair["input"], rival) == _selected_cells(pair)
            for pair in demos
        ):
            predicted = _candidate_prediction(query["input"], rival)
            if predicted != _selected_cells(query):
                reasons.append(
                    f"rival selector {rival!r} fits every demonstration but "
                    "predicts a different query component"
                )
    return reasons


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


SEMANTIC_WITNESSES = {
    "singleton_decoy": _witness("singleton_decoy"),
    "largest_first": _witness("largest_first"),
    "largest_last": _witness("largest_last"),
    "largest_not_first": _witness("largest_not_first"),
    "largest_not_last": _witness("largest_not_last"),
    "diagonal_only_contact": _witness("diagonal_only_contact"),
    "bbox_area_decoy": _witness("bbox_area_decoy"),
    "edge_largest": _witness("edge_largest"),
    "interior_largest": _witness("interior_largest"),
}


def _copy_for_test(grid):
    """Task-local tests use this to make mutation intent explicit."""
    return copy.deepcopy(grid)
