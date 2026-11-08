"""Generator for ``Extract the Seed's Contact Cluster`` (366cda05b486).

The input contains two disconnected *contact clusters*.  Each object is a
monochromatic 4-connected component; objects in the same cluster touch along a
cardinal edge.  The unique blue (1) object identifies the cluster to crop and
recolour cyan (8). Cyan can occur in either, both, or neither input cluster.
Diagonal-only contacts distinguish cardinal connectivity from an eight-way
flood fill. Racket remains the label authority; Python rivals audit lessons.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "366cda05b486"
TASK_ID = "366cda05b486"
VERSION = "2.1.0"
RULE_HASH = "f50313901f96"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find the unique blue (1) monochromatic object, follow cardinal contacts "
    "between differently coloured objects to its whole contact cluster, crop "
    "that union tightly, and recolour every selected cell cyan (8)."
)

INVARIANTS = [
    "background is 0; objects are monochromatic cardinal components",
    "there are exactly two disconnected object-contact clusters",
    "the unique blue object is a leaf of a 3-to-5-object selected cluster",
    "the distractor cluster contains 2-to-4 touching objects; cyan is not a selection cue",
    "clusters do not touch cardinally; diagonal-only contact is lawful",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9 or 10 mixed with difficulty-aware 9..18",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 12 or 13 mixed with difficulty-aware 12..20",
        "valid": "12..20",
    },
    "cluster_components": {
        "type": "int",
        "default": "canonical 3 or 4 mixed with difficulty-aware 3..5",
        "valid": "3..5",
    },
    "distractor_components": {
        "type": "int",
        "default": "canonical 2 mixed with difficulty-aware 2..4",
        "valid": "2..4",
    },
    "seed_size": {
        "type": "int",
        "default": "difficulty-aware 1..4",
        "valid": "1..4",
    },
    "orientation": {
        "type": "enum",
        "default": "rng over D4",
        "valid": [
            "identity",
            "rot90",
            "rot180",
            "rot270",
            "flip_h",
            "flip_v",
            "transpose",
            "anti_transpose",
        ],
    },
    "palette_kind": {
        "type": "enum",
        "default": "rng default|warm|cool|varied",
        "valid": ["default", "warm", "cool", "varied"],
    },
}

_ORIENTATIONS = tuple(AXES["orientation"]["valid"])
_PALETTE_KINDS = tuple(AXES["palette_kind"]["valid"])
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Normalized connected polyominoes. D4 variants are generated at runtime.
_BASE_SHAPES = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, canonical-like teaching input."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and AXES[name]["type"] == "int" and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Alternate cluster-count reversals: every four-pair lesson has two,
    # so holding out any one pair still leaves a demonstration witness.
    # Otherwise the blue cluster's greater object count is a perfect shortcut.
    inverse_count = (sample_index + seed // 16) % 2 == 1
    modes = ("inverse_count",) if inverse_count else ("canonical",) * 3 + ("broad",)
    core = ctx.draw_choice("curriculum_profile", modes) == "canonical"
    profile = ctx.draw_choice("canonical_profile", ((9, 12, 3, 2), (10, 13, 4, 2)))
    h = _draw_count(ctx, "grid_h", 9, 18, profile[0] if core else None)
    w = _draw_count(ctx, "grid_w", 12, 20, profile[1] if core else None)
    cluster_components = _draw_count(ctx, "cluster_components", 3, 5,
                                     3 if inverse_count else profile[2] if core else None)
    distractor_components = _draw_count(ctx, "distractor_components", 2, 4,
                                        4 if inverse_count else profile[3] if core else None)
    seed_size = ctx.draw_int_diff("seed_size", 1, 4)
    # Sequential samples deliberately alternate the graph branch whenever a
    # true fan is possible; three-object clusters are necessarily paths.
    topology = "fan" if cluster_components >= 4 and sample_index % 2 else "chain"
    orientation = ctx.draw_choice("orientation", _ORIENTATIONS)
    palette_kind = ctx.draw_choice("palette_kind", _PALETTE_KINDS)
    cyan_role = ("absent", "distractor", "selected", "both")[(sample_index + seed) % 4]
    diagonal_contact = (sample_index + seed // 4) % 2 == 0
    # Alternate an explicit area counterexample with unrestricted shapes.
    # Some exact overrides cannot realize a smaller selected cluster; they
    # retain their exact counts instead of silently changing the request.
    smaller_selected = (
        (sample_index + seed // 8) % 2 == 0
        and seed_size + cluster_components - 1 < 4 * distractor_components
    )

    selected_rng = ctx.draw_rng("selected_cluster")
    distractor_rng = ctx.draw_rng("distractor_cluster")
    placement_rng = ctx.draw_rng("placement")
    palette_rng = ctx.draw_rng("palette")

    for _ in range(256):
        selected = _build_contact_cluster(
            selected_rng,
            cluster_components,
            topology=topology,
            first_size=seed_size,
            max_component_size=(2 if seed_size + cluster_components - 1 < 4 else 1)
            if smaller_selected else 4,
            canvas_size=8,
        )
        if selected is None:
            continue
        selected = _orient_components(selected, orientation)
        if not _selected_footprint_ok(selected):
            continue

        distractor = _build_contact_cluster(
            distractor_rng,
            distractor_components,
            topology="chain",
            first_size=4 if smaller_selected else distractor_rng.randint(1, 4),
            max_component_size=4,
            canvas_size=7,
        )
        if distractor is None:
            continue
        if smaller_selected and sum(map(len, selected)) >= sum(map(len, distractor)):
            continue
        distractor = _orient_components(
            distractor, distractor_rng.choice(_ORIENTATIONS)
        )

        placements = _place_two_clusters(
            h, w, selected, distractor, placement_rng,
            diagonal_contact=diagonal_contact,
        )
        if placements is None:
            continue
        selected_cells, distractor_cells = placements

        selected_colors, distractor_colors = _component_colors(
            cluster_components,
            distractor_components,
            palette_kind,
            palette_rng,
            cyan_role=cyan_role,
        )
        grid = full_grid(h, w, 0)
        _paint_components(grid, selected_cells, selected_colors)
        _paint_components(grid, distractor_cells, distractor_colors)
        errors = _structure_errors(grid)
        if not errors:
            return grid

    raise ValueError(
        "unable to place two separated canonical contact clusters for the "
        "requested override combination"
    )


def _draw_count(ctx, name, low, high, anchor):
    """Anchor defaults without clipping or replacing any explicit control."""
    if anchor is not None and ctx.overrides.get(name) is None:
        return ctx.draw_choice(name, (anchor,))
    return ctx.draw_int_diff(name, low, high)


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact count axes from the returned grid."""
    analysis = _analyze_grid(grid)
    if analysis["seed_index"] is None:
        return {}
    seed_cluster = analysis["clusters"][analysis["seed_cluster_index"]]
    seed_component = analysis["objects"][analysis["seed_index"]]
    distractor_components = sum(
        len(cluster)
        for index, cluster in enumerate(analysis["clusters"])
        if index != analysis["seed_cluster_index"]
    )
    return {
        "cluster_components": len(seed_cluster),
        "distractor_components": distractor_components,
        "seed_size": len(seed_component["cells"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons and accept every authoritative canonical input."""
    basic = _basic_grid_errors(grid)
    if basic:
        return basic
    errors = _structure_errors(grid)

    requested = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for axis in ("cluster_components", "distractor_components", "seed_size"):
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        observed = observe_overrides(grid)
        for axis in ("cluster_components", "distractor_components", "seed_size"):
            if axis in requested and observed.get(axis) != int(requested[axis]):
                errors.append(
                    f"{axis} requested {int(requested[axis])}, observed "
                    f"{observed.get(axis)!r}"
                )
    return errors


def expected_output(grid):
    """Python mirror used only for tests/inspection; Racket remains authority."""
    analysis = _analyze_grid(grid)
    if analysis["seed_index"] is None:
        raise ValueError("grid has no unique blue seed object")
    selected_ids = analysis["clusters"][analysis["seed_cluster_index"]]
    cells = {
        cell
        for object_id in selected_ids
        for cell in analysis["objects"][object_id]["cells"]
    }
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    return [
        [8 if (min_r + r, min_c + c) in cells else 0 for c in range(max_c - min_c + 1)]
        for r in range(max_r - min_r + 1)
    ]


def profile_signature(grid) -> tuple:
    """Strict linked semantic profile for canonical/generated census evidence."""
    analysis = _analyze_grid(grid)
    if analysis["seed_index"] is None or analysis["seed_cluster_index"] is None:
        return ("invalid",)
    selected = analysis["clusters"][analysis["seed_cluster_index"]]
    distractors = [
        cluster
        for index, cluster in enumerate(analysis["clusters"])
        if index != analysis["seed_cluster_index"]
    ]
    output = expected_output(grid)
    degrees = sorted(
        sum(1 for other in selected if other in analysis["adjacency"][object_id])
        for object_id in selected
    )
    return (
        len(grid),
        len(grid[0]),
        len(selected),
        tuple(sorted(len(analysis["objects"][i]["cells"]) for i in selected)),
        tuple(degrees),
        tuple(sorted(len(cluster) for cluster in distractors)),
        len(output),
        len(output[0]),
        sum(value != 0 for row in output for value in row),
        tuple(sorted({value for row in grid for value in row if value != 0})),
    )


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be ARC colours 0..9"]
    return []


def _structure_errors(grid) -> list[str]:
    analysis = _analyze_grid(grid)
    parts = analysis["objects"]
    clusters = analysis["clusters"]
    errors: list[str] = []

    if analysis["blue_object_count"] != 1:
        errors.append(
            f"expected exactly one blue object, got {analysis['blue_object_count']}"
        )
        return errors
    if len(clusters) != 2:
        errors.append(f"expected exactly two contact clusters, got {len(clusters)}")
        return errors

    seed_cluster_index = analysis["seed_cluster_index"]
    seed_cluster = clusters[seed_cluster_index]
    distractor_cluster = clusters[1 - seed_cluster_index]
    if not 3 <= len(seed_cluster) <= 5:
        errors.append(
            f"seed contact cluster must contain 3..5 objects, got {len(seed_cluster)}"
        )
    if not 2 <= len(distractor_cluster) <= 4:
        errors.append(
            "distractor contact cluster must contain 2..4 objects, got "
            f"{len(distractor_cluster)}"
        )

    seed_index = analysis["seed_index"]
    seed_degree = len(analysis["adjacency"][seed_index] & set(seed_cluster))
    if seed_degree != 1:
        errors.append(f"blue seed object must be a contact-graph leaf, degree={seed_degree}")

    selected_cells = {
        cell for i in seed_cluster for cell in parts[i]["cells"]
    }
    distractor_cells = {
        cell for i in distractor_cluster for cell in parts[i]["cells"]
    }
    if _touching(selected_cells, distractor_cells, include_diagonal=False):
        errors.append("selected and distractor clusters must be cardinally disconnected")

    try:
        output = expected_output(grid)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if len(output) < 2 or len(output[0]) < 2:
            errors.append("selected crop is too small to teach crop-and-preserve geometry")
        if sum(value == 8 for row in output for value in row) < 4:
            errors.append("selected cluster must contain at least four cells")
        if all(value == 8 for row in output for value in row):
            errors.append("selected crop must contain at least one background hole/corner")
    return errors


def _component_colors(n_selected, n_distractor, palette_kind, rng, *, cyan_role):
    orders = {
        "default": [3, 4, 6, 7, 2, 5, 9],
        "warm": [2, 3, 4, 7, 6, 9, 5],
        "cool": [6, 7, 5, 4, 3, 9, 2],
        "varied": [2, 3, 4, 5, 6, 7, 9],
    }
    pool = list(orders[palette_kind])
    if palette_kind == "varied":
        rng.shuffle(pool)
    selected_cyan = cyan_role in ("selected", "both")
    distractor_cyan = cyan_role in ("distractor", "both")
    selected_extra = n_selected - 1 - int(selected_cyan)
    distractor_extra = n_distractor - int(distractor_cyan)
    selected = [1, *pool[:selected_extra]]
    # Reuse a colour only across the two disconnected clusters when needed.
    # Within each cluster distinct colours preserve exact component counts.
    remaining = pool[selected_extra:] + pool[:selected_extra]
    distractor = remaining[:distractor_extra]
    if selected_cyan:
        selected.insert(rng.randrange(1, len(selected) + 1), 8)
    if distractor_cyan:
        distractor.insert(rng.randrange(len(distractor) + 1), 8)
    return selected, distractor


def _build_contact_cluster(
    rng,
    n_components: int,
    *,
    topology: str,
    first_size: int,
    max_component_size: int,
    canvas_size: int,
):
    for _ in range(96):
        first_variants = list(_shape_variants(first_size))
        rng.shuffle(first_variants)
        first = first_variants[0]
        fh, fw = _dims(first)
        offset = ((canvas_size - fh) // 2, (canvas_size - fw) // 2)
        components = [
            {(r + offset[0], c + offset[1]) for r, c in first}
        ]

        complete = True
        for index in range(1, n_components):
            parent = index - 1 if topology == "chain" else (0 if index == 1 else 1)
            shapes = []
            sizes = list(range(1, max_component_size + 1))
            rng.shuffle(sizes)
            for size in sizes:
                variants = list(_shape_variants(size))
                rng.shuffle(variants)
                shapes.extend(variants)
            candidates = []
            for shape in shapes:
                for parent_cell in components[parent]:
                    for dr, dc in _CARDINAL:
                        attach = (parent_cell[0] + dr, parent_cell[1] + dc)
                        for shape_cell in shape:
                            rr = attach[0] - shape_cell[0]
                            cc = attach[1] - shape_cell[1]
                            candidates.append((shape, rr, cc))
            placed = None
            # Draw a random permutation lazily. Most attachments succeed after
            # a few candidates; shuffling and allocating every rejected shape
            # made the full exact-override matrix exceed its stage time limit.
            while candidates:
                candidate_index = rng.randrange(len(candidates))
                shape, rr, cc = candidates[candidate_index]
                candidates[candidate_index] = candidates[-1]
                candidates.pop()
                cells = {(r + rr, c + cc) for r, c in shape}
                if _legal_component_placement(cells, components, parent, canvas_size):
                    placed = cells
                    break
            if placed is None:
                complete = False
                break
            components.append(placed)
        if not complete:
            continue
        normalized = _normalize_components(components)
        if _contact_graph_connected(normalized):
            return normalized
    return None


def _legal_component_placement(cells, components, parent, canvas_size):
    if any(not (0 <= r < canvas_size and 0 <= c < canvas_size) for r, c in cells):
        return False
    occupied = set().union(*components)
    if cells & occupied:
        return False
    adjacent_components = {
        index
        for index, component in enumerate(components)
        if _touching(cells, component, include_diagonal=False)
    }
    return adjacent_components == {parent}


@lru_cache(maxsize=4)
def _shape_variants(size: int):
    variants = set()
    for base in _BASE_SHAPES[size]:
        for orientation in _ORIENTATIONS:
            variants.add(tuple(sorted(_orient_cells(base, orientation))))
    return tuple(sorted(variants))


def _orient_components(components, orientation):
    transformed = [
        {_transform_point(r, c, orientation) for r, c in component}
        for component in components
    ]
    return _normalize_components(transformed)


def _orient_cells(cells: Iterable[tuple[int, int]], orientation: str):
    transformed = [_transform_point(r, c, orientation) for r, c in cells]
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return {(r - min_r, c - min_c) for r, c in transformed}


def _transform_point(r: int, c: int, orientation: str) -> tuple[int, int]:
    if orientation == "identity":
        return r, c
    if orientation == "rot90":
        return c, -r
    if orientation == "rot180":
        return -r, -c
    if orientation == "rot270":
        return -c, r
    if orientation == "flip_h":
        return r, -c
    if orientation == "flip_v":
        return -r, c
    if orientation == "transpose":
        return c, r
    if orientation == "anti_transpose":
        return -c, -r
    raise ValueError(f"unknown orientation: {orientation}")


def _normalize_components(components):
    all_cells = set().union(*components)
    min_r = min(r for r, _ in all_cells)
    min_c = min(c for _, c in all_cells)
    return [
        {(r - min_r, c - min_c) for r, c in component}
        for component in components
    ]


def _selected_footprint_ok(components):
    cells = set().union(*components)
    h, w = _dims(cells)
    return h <= 7 and w <= 8 and h >= 2 and w >= 2 and len(cells) >= 4 and len(cells) < h * w


def _place_two_clusters(h, w, selected, distractor, rng, *, diagonal_contact=False):
    sh, sw = _dims(set().union(*selected))
    dh, dw = _dims(set().union(*distractor))
    selected_origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    distractor_origins = [(r, c) for r in range(h - dh + 1) for c in range(w - dw + 1)]
    rng.shuffle(selected_origins)
    rng.shuffle(distractor_origins)
    for sr, sc in selected_origins:
        selected_cells = [
            {(r + sr, c + sc) for r, c in component}
            for component in selected
        ]
        selected_union = set().union(*selected_cells)
        for dr, dc in distractor_origins:
            distractor_cells = [
                {(r + dr, c + dc) for r, c in component}
                for component in distractor
            ]
            distractor_union = set().union(*distractor_cells)
            if _touching(selected_union, distractor_union, include_diagonal=False):
                continue
            touches_diagonally = _touching(selected_union, distractor_union, include_diagonal=True)
            if touches_diagonally != diagonal_contact:
                continue
            return selected_cells, distractor_cells
    return None


def _paint_components(grid, components, colors):
    for component, color in zip(components, colors):
        for r, c in component:
            grid[r][c] = color


def _analyze_grid(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    parts = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                cell = queue.popleft()
                cells.add(cell)
                rr, cc = cell
                for dr, dc in _CARDINAL:
                    nxt = (rr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            parts.append({"color": color, "cells": cells})

    adjacency = {index: set() for index in range(len(parts))}
    cell_owner = {
        cell: index
        for index, obj in enumerate(parts)
        for cell in obj["cells"]
    }
    for cell, owner in cell_owner.items():
        r, c = cell
        for dr, dc in _CARDINAL:
            other = cell_owner.get((r + dr, c + dc))
            if other is not None and other != owner:
                adjacency[owner].add(other)
                adjacency[other].add(owner)

    clusters = []
    remaining = set(range(len(parts)))
    while remaining:
        start = min(remaining)
        queue = [start]
        cluster = set()
        while queue:
            current = queue.pop()
            if current in cluster:
                continue
            cluster.add(current)
            queue.extend(adjacency[current] - cluster)
        remaining -= cluster
        clusters.append(tuple(sorted(cluster)))

    blue_ids = [index for index, obj in enumerate(parts) if obj["color"] == 1]
    seed_index = blue_ids[0] if len(blue_ids) == 1 else None
    seed_cluster_index = None
    if seed_index is not None:
        seed_cluster_index = next(
            index for index, cluster in enumerate(clusters) if seed_index in cluster
        )
    return {
        "objects": parts,
        "adjacency": adjacency,
        "clusters": clusters,
        "blue_object_count": len(blue_ids),
        "seed_index": seed_index,
        "seed_cluster_index": seed_cluster_index,
    }


def _contact_graph_connected(components) -> bool:
    adjacency = {index: set() for index in range(len(components))}
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            if _touching(components[left], components[right], include_diagonal=False):
                adjacency[left].add(right)
                adjacency[right].add(left)
    reached = {0}
    queue = [0]
    while queue:
        current = queue.pop()
        for nxt in adjacency[current] - reached:
            reached.add(nxt)
            queue.append(nxt)
    return len(reached) == len(components)


def _touching(left, right, *, include_diagonal: bool) -> bool:
    if left & right:
        return True
    deltas = (
        tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
        if include_diagonal
        else _CARDINAL
    )
    return any((r + dr, c + dc) in right for r, c in left for dr, dc in deltas)


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def strict_canonical_like(grid):
    """The same task domain for canonical data, generated data, and probes."""
    return self_check(grid)


def _crop_cells(cells):
    if not cells:
        return [[0]]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]


def _cluster_cells(analysis):
    return [{cell for index in cluster for cell in analysis["objects"][index]["cells"]}
            for cluster in analysis["clusters"]]


def _largest_cluster(grid):
    return _crop_cells(max(_cluster_cells(_analyze_grid(grid)), key=len))


def _noncyan_cluster(grid):
    groups = _cluster_cells(_analyze_grid(grid))
    candidates = [cells for cells in groups if all(grid[r][c] != 8 for r, c in cells)]
    return _crop_cells(max(candidates or groups, key=len))


def _most_objects(grid):
    analysis = _analyze_grid(grid)
    groups = analysis["clusters"]
    # A plausible shortcut uses the seed only to break object-count ties.
    selected = max(range(len(groups)), key=lambda index: (
        len(groups[index]), index == analysis["seed_cluster_index"]))
    return _crop_cells(_cluster_cells(analysis)[selected])


def _eight_connected(grid):
    start = next((r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 1)
    reached, queue = {start}, [start]
    while queue:
        r, c = queue.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                        and grid[nr][nc] != 0 and (nr, nc) not in reached):
                    reached.add((nr, nc))
                    queue.append((nr, nc))
    return _crop_cells(reached)


def _seed_only(grid):
    analysis = _analyze_grid(grid)
    return _crop_cells(analysis["objects"][analysis["seed_index"]]["cells"])


def _one_hop(grid):
    analysis = _analyze_grid(grid)
    seed = analysis["seed_index"]
    ids = {seed} | analysis["adjacency"][seed]
    return _crop_cells({cell for index in ids for cell in analysis["objects"][index]["cells"]})


def _solid_bbox(grid):
    output = expected_output(grid)
    return [[8] * len(output[0]) for _ in output]


SEMANTIC_RIVALS = {
    "largest_cluster": _largest_cluster,
    "noncyan_cluster": _noncyan_cluster,
    "most_objects": _most_objects,
    "eight_connected": _eight_connected,
    "seed_only": _seed_only,
    "one_hop": _one_hop,
    "solid_bbox": _solid_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in ("largest_cluster", "noncyan_cluster", "most_objects", "eight_connected")}


def _rival_differs(grid, name):
    return SEMANTIC_RIVALS[name](grid) != expected_output(grid)


# These are executable disagreement claims. The shared semantic gate checks
# the selected Racket output, rather than trusting this Python mirror.
SEMANTIC_WITNESSES = {
    name: (lambda grid, name=name: _rival_differs(grid, name))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Reject measured query ambiguity against these seven declared rivals.

    This is a finite rival contract, not a claim of unique induction. The
    production materializer owns Racket labels and fails explicitly if this
    final lesson check finds a surviving rival; it does not repair the demos.
    """
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(demo["input"]) == demo["output"] for demo in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
