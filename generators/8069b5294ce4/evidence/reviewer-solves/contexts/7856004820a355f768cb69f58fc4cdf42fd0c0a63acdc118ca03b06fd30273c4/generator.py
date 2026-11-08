"""Generator for ARC task 8069b5294ce4 — adjacency matrix of the blue cluster.

The input contains several monochrome 4-connected objects.  Treat objects as
vertices and cardinal contact between differently coloured objects as graph
edges.  The unique blue (1) object selects one connected graph component.
Sort only that component's objects by top-left cell and output its adjacency
matrix: 1 on the diagonal, 8 for touching pairs, and 0 otherwise.

The curriculum intentionally uses multi-cell objects and always includes
objects outside the blue component.  A four-sample schedule supplies a
canonical-like path, a branched graph, a branched graph beside a larger-area
non-blue component, and a cyclic graph.  Therefore every sliding four-demo
lesson refutes cell-level, all-object, path-only, and largest-area shortcuts.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8069b5294ce4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9b665edfdc5f"

SUMMARY = (
    "Find monochrome 4-connected objects and their cardinal-contact graph. "
    "The unique blue (1) object selects one connected component; sort that "
    "component by top-left cell and emit its square adjacency matrix with 1 "
    "on the diagonal, 8 for touching object pairs, and 0 otherwise."
)

INVARIANTS = [
    "background is black (0) and exactly one object is blue (1)",
    "the blue graph component contains 4..8 distinctly coloured objects",
    "at least one multi-cell object makes object extraction indispensable",
    "1..5 non-blue-component objects act as distractors",
    "the selected graph has both touching and non-touching object pairs",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted with a strong canonical 8/9/10 prior",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with a strong canonical 13/15 prior",
        "valid": "13..20",
    },
    "k_cluster": {
        "type": "int",
        "default": "difficulty-weighted; canonical-like schedule favors 4..5",
        "valid": "4..8",
    },
    "n_decoys": {
        "type": "int",
        "default": "difficulty-weighted; canonical-like schedule favors 1",
        "valid": "1..5",
    },
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.05
SCHEDULE_PROFILES = (
    "canonical_path",
    "branched",
    "larger_area_decoy",
    "cyclic",
)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AXIS_DOMAINS = {
    "grid_h": tuple(range(8, 19)),
    "grid_w": tuple(range(13, 21)),
    "k_cluster": tuple(range(4, 9)),
    "n_decoys": tuple(range(1, 6)),
}

# Compact induced graphs.  Every prefix of each family has the named topology.
_PATH_COORDS = (
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 0), (1, 3), (2, 0), (2, 1),
)
_BRANCH_COORDS = (
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 0), (1, 2), (2, 0), (2, 1),
)
_CYCLIC_BY_K = {
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
    5: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive sample indices always expose all decisive controls."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if not (8 <= len(grid) <= 18 and 13 <= width <= 20):
        return [f"grid shape must be within 8..18 x 13..20, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]
    return []


def _find_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-colour 4-connected objects in scan order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    object_list: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.pop()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            object_list.append({
                "color": color,
                "cells": tuple(cells),
                "top_left": cells[0],
            })
    return object_list


def _object_graph(
    grid: list[list[int]], object_list: list[dict[str, Any]]
) -> list[set[int]]:
    owner = {
        cell: index
        for index, obj in enumerate(object_list)
        for cell in obj["cells"]
    }
    graph = [set() for _ in object_list]
    h, w = len(grid), len(grid[0])
    for cell, index in owner.items():
        r, c = cell
        for dr, dc in _CARD:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            other = owner.get((nr, nc))
            if other is not None and other != index:
                graph[index].add(other)
    return graph


def _graph_components(graph: list[set[int]]) -> list[list[int]]:
    unseen = set(range(len(graph)))
    components: list[list[int]] = []
    while unseen:
        start = min(unseen)
        queue = [start]
        unseen.remove(start)
        component: list[int] = []
        while queue:
            node = queue.pop()
            component.append(node)
            for neighbor in graph[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _analysis(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return None, errors
    normalized = [list(row) for row in grid]
    object_list = _find_components(normalized)
    graph = _object_graph(normalized, object_list)
    seed_ids = [i for i, obj in enumerate(object_list) if obj["color"] == 1]
    if len(seed_ids) != 1:
        return None, [f"expected exactly one blue object, found {len(seed_ids)}"]
    seed = seed_ids[0]
    seed_cluster = next(c for c in _graph_components(graph) if seed in c)
    cluster_set = set(seed_cluster)
    degrees = {i: len(graph[i] & cluster_set) for i in seed_cluster}
    edge_count = sum(degrees.values()) // 2
    k = len(seed_cluster)
    if edge_count == k - 1 and max(degrees.values(), default=0) <= 2:
        graph_kind = "path"
    elif edge_count == k - 1 and max(degrees.values(), default=0) >= 3:
        graph_kind = "branch"
    elif edge_count >= k:
        graph_kind = "cyclic"
    else:
        graph_kind = "other"
    return {
        "grid": normalized,
        "object_list": object_list,
        "graph": graph,
        "seed": seed,
        "seed_cluster": seed_cluster,
        "cluster_set": cluster_set,
        "degrees": degrees,
        "edge_count": edge_count,
        "graph_kind": graph_kind,
        "decoys": [i for i in range(len(object_list)) if i not in cluster_set],
        "graph_components": _graph_components(graph),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting all canonicals."""
    del difficulty, meta
    info, errors = _analysis(grid)
    if errors:
        return errors
    assert info is not None
    object_list = info["object_list"]
    cluster = info["seed_cluster"]
    decoys = info["decoys"]
    k = len(cluster)
    if not 4 <= k <= 8:
        errors.append(f"blue component must contain 4..8 objects, found {k}")
    if not 1 <= len(decoys) <= 5:
        errors.append(f"scene must contain 1..5 outside objects, found {len(decoys)}")
    cluster_colors = [object_list[i]["color"] for i in cluster]
    if len(set(cluster_colors)) != len(cluster_colors):
        errors.append("blue-component objects must have distinct colours")
    if info["graph_kind"] not in {"path", "branch", "cyclic"}:
        errors.append("blue-component contact graph must be a path, branched tree, or cyclic graph")
    if info["edge_count"] >= k * (k - 1) // 2:
        errors.append("selected graph is complete and hides off-diagonal zero entries")
    if not any(len(object_list[i]["cells"]) > 1 for i in cluster):
        errors.append("selected graph needs at least one multi-cell object")
    if len({cell for row in grid for cell in row if cell != 0}) < 5:
        errors.append("scene needs at least five nonzero colours to avoid palette shortcuts")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Empirical canonical manifold, not merely a coarse morphology envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    info, _ = _analysis(grid)
    assert info is not None
    h, w = len(grid), len(grid[0])
    if (h, w) not in {(8, 13), (9, 13), (10, 15)}:
        errors.append(f"canonical shape must be 8x13, 9x13, or 10x15, found {h}x{w}")
    if len(info["seed_cluster"]) not in {4, 5}:
        errors.append("canonical blue component contains four or five objects")
    if len(info["decoys"]) != 1:
        errors.append("canonical scenes contain exactly one outside object")
    if info["graph_kind"] not in {"path", "branch"}:
        errors.append("canonical selected graphs are trees")
    object_list = info["object_list"]
    if len(object_list[info["seed"]]["cells"]) != 4:
        errors.append("canonical blue object is a 2x2 four-cell object")
    if len(object_list[info["decoys"][0]]["cells"]) != 4:
        errors.append("canonical outside object is a 2x2 four-cell object")
    if any(
        max(r for r, _ in obj["cells"]) - min(r for r, _ in obj["cells"]) > 1
        or max(c for _, c in obj["cells"]) - min(c for _, c in obj["cells"]) > 1
        for obj in object_list
    ):
        errors.append("canonical objects fit inside 2x2 boxes")
    palette_size = len({value for row in grid for value in row})
    expected_palette = len(info["seed_cluster"]) + 2
    if palette_size != expected_palette:
        errors.append(
            f"canonical palette size is cluster size + background + one decoy, "
            f"expected {expected_palette}, found {palette_size}"
        )
    return errors


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned scene."""
    info, errors = _analysis(grid)
    if errors or info is None:
        return {name: None for name in AXES}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "k_cluster": len(info["seed_cluster"]),
        "n_decoys": len(info["decoys"]),
    }


def _weighted_domain(label: str, preferred: Iterable[int], repeat: int) -> tuple[int, ...]:
    domain = _AXIS_DOMAINS[label]
    preferred_values = tuple(value for value in preferred if value in domain)
    return preferred_values * repeat + domain


def _draw_axes(ctx, profile: str, difficulty: str | None) -> tuple[int, int, int, int]:
    if profile == "canonical_path":
        anchor_index = ctx.sample_index // len(SCHEDULE_PROFILES)
        shapes = ((8, 13, 4), (9, 13, 4), (10, 15, 5))
        anchor_h, anchor_w, anchor_k = shapes[anchor_index % len(shapes)]
        h_opts = _weighted_domain("grid_h", (anchor_h,), 180)
        w_opts = _weighted_domain("grid_w", (anchor_w,), 180)
        k_opts = _weighted_domain("k_cluster", (anchor_k,), 180)
        n_opts = _weighted_domain("n_decoys", (1,), 180)
    else:
        if difficulty == "easy":
            h_pref, w_pref, k_pref, n_pref = (8, 9, 10), (13, 15), (4, 5), (1, 2)
        elif difficulty == "hard":
            h_pref, w_pref, k_pref, n_pref = (10, 14, 18), (15, 18, 20), (6, 7, 8), (2, 3, 4, 5)
        else:
            h_pref, w_pref, k_pref, n_pref = (9, 10, 12, 14), (13, 15, 17), (4, 5, 6, 7), (1, 2, 3)
        h_opts = _weighted_domain("grid_h", h_pref, 8)
        w_opts = _weighted_domain("grid_w", w_pref, 8)
        k_opts = _weighted_domain("k_cluster", k_pref, 8)
        n_opts = _weighted_domain("n_decoys", n_pref, 8)
    return (
        ctx.draw_choice("grid_h", h_opts),
        ctx.draw_choice("grid_w", w_opts),
        ctx.draw_choice("k_cluster", k_opts),
        ctx.draw_choice("n_decoys", n_opts),
    )


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transforms(cells: Iterable[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflect in (False, True):
        for turns in range(4):
            out = []
            for r, c in cells:
                x, y = r, -c if reflect else c
                for _ in range(turns):
                    x, y = y, -x
                out.append((x, y))
            variants.add(_normalize(out))
    return sorted(variants)


@lru_cache(maxsize=None)
def _shape_library(kind: str, k: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate compact induced grid graphs for output-topology diversity."""
    canvas = tuple((r, c) for r in range(4) for c in range(4))
    shapes: set[tuple[tuple[int, int], ...]] = set()
    for chosen in combinations(canvas, k):
        chosen_set = set(chosen)
        stack = [chosen[0]]
        seen = {chosen[0]}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in chosen_set and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(seen) != k:
            continue
        degrees = {cell: 0 for cell in chosen}
        edge_count = 0
        for r, c in chosen:
            for dr, dc in ((1, 0), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in chosen_set:
                    edge_count += 1
                    degrees[(r, c)] += 1
                    degrees[nxt] += 1
        max_degree = max(degrees.values())
        matches = (
            (kind == "path" and edge_count == k - 1 and max_degree <= 2)
            or (kind == "branch" and edge_count == k - 1 and max_degree >= 3)
            or (kind == "cyclic" and edge_count >= k)
        )
        if matches:
            shapes.add(_normalize(chosen))
    if not shapes:
        fallback = {
            "path": _PATH_COORDS[:k],
            "branch": _BRANCH_COORDS[:k],
            "cyclic": _CYCLIC_BY_K[k],
        }[kind]
        shapes.update(_transforms(fallback))
    return tuple(sorted(shapes))


def _macro_graph(kind: str, k: int, rng) -> tuple[tuple[int, int], ...]:
    if kind not in {"path", "branch", "cyclic"}:  # pragma: no cover
        raise ValueError(f"unknown graph kind: {kind}")
    return rng.choice(_shape_library(kind, k))


def _macro_neighbors(cells: tuple[tuple[int, int], ...]) -> dict[int, set[int]]:
    index = {cell: i for i, cell in enumerate(cells)}
    graph = {i: set() for i in range(len(cells))}
    for i, (r, c) in enumerate(cells):
        for dr, dc in _CARD:
            j = index.get((r + dr, c + dc))
            if j is not None:
                graph[i].add(j)
    return graph


def _tile_shape(
    directions: set[tuple[int, int]], rng, *, minimal: bool, force_full: bool
) -> tuple[tuple[int, int], ...]:
    if force_full:
        return ((0, 0), (0, 1), (1, 0), (1, 1))
    required = {(0, 0)}
    if (0, 1) in directions:
        required.add((0, 1))
    if (1, 0) in directions:
        required.add((1, 0))
    candidates = (
        {(0, 0)},
        {(0, 0), (0, 1)},
        {(0, 0), (1, 0)},
        {(0, 0), (0, 1), (1, 0)},
        {(0, 0), (0, 1), (1, 1)},
        {(0, 0), (1, 0), (1, 1)},
        {(0, 0), (0, 1), (1, 0), (1, 1)},
    )
    legal = [shape for shape in candidates if required <= shape]
    if minimal:
        chosen = min(legal, key=lambda shape: (len(shape), sorted(shape)))
    else:
        chosen = rng.choice(legal)
    return tuple(sorted(chosen))


def _cluster_colors(k: int, seed_id: int, rng) -> dict[int, int]:
    other_colors = rng.sample([2, 3, 4, 5, 6, 7, 9], k - 1)
    colors: dict[int, int] = {seed_id: 1}
    cursor = 0
    for i in range(k):
        if i == seed_id:
            continue
        colors[i] = other_colors[cursor]
        cursor += 1
    return colors


def _decoy_colors(
    n: int, cluster_colors: set[int], rng, *, allow_eight: bool
) -> list[int]:
    candidates = [2, 3, 4, 5, 6, 7, 9]
    if allow_eight:
        candidates = [8] + candidates
    unused = [color for color in candidates if color not in cluster_colors]
    rng.shuffle(unused)
    rng.shuffle(candidates)
    if allow_eight and 8 in unused:
        unused.remove(8)
        unused.insert(0, 8)
    colors: list[int] = []
    for i in range(n):
        pool = unused if unused else candidates
        choice = next(
            (color for color in pool if not colors or color != colors[-1]),
            candidates[(i + 1) % len(candidates)],
        )
        colors.append(choice)
        if choice in unused:
            unused.remove(choice)
    return colors


def _paint_cluster(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], colors: dict[int, int],
    *, row0: int, col0: int, rng, profile: str, seed_id: int,
) -> None:
    macro_graph = _macro_neighbors(cells)
    minimal = profile == "larger_area_decoy"
    for i, (mr, mc) in enumerate(cells):
        directions = {
            (cells[j][0] - mr, cells[j][1] - mc)
            for j in macro_graph[i]
        }
        shape = _tile_shape(
            directions,
            rng,
            minimal=minimal,
            force_full=(profile == "canonical_path" and i == seed_id),
        )
        for dr, dc in shape:
            grid[row0 + 2 * mr + dr][col0 + 2 * mc + dc] = colors[i]


def _paint_decoys(
    grid: list[list[int]], *, side: str, profile: str, n: int,
    colors: list[int], rng,
) -> None:
    h, w = len(grid), len(grid[0])
    c0 = 0 if side == "left" else w - 2
    if profile == "larger_area_decoy":
        # Partition the full two-column strip into n touching monochrome bands.
        # Its area is 2*h; the selected branch uses minimal tile shapes and has
        # at most 2*k-1 <= 15 cells, so this non-blue component is strictly
        # larger even at the 8-row boundary.
        base, remainder = divmod(h, n)
        row = 0
        for i in range(n):
            height = base + (1 if i < remainder else 0)
            for r in range(row, row + height):
                grid[r][c0] = colors[i]
                grid[r][c0 + 1] = colors[i]
            row += height
        return

    if profile == "canonical_path" and n == 1:
        row = rng.randint(0, h - 2)
        for dr in (0, 1):
            for dc in (0, 1):
                grid[row + dr][c0 + dc] = colors[0]
        return

    linked = profile == "branched" and n > 1
    if linked:
        row0 = rng.randint(0, h - n)
        for i in range(n):
            grid[row0 + i][c0] = colors[i]
            grid[row0 + i][c0 + 1] = colors[i]
        return

    # Diagonal checkerboard positions are pairwise non-cardinal, so up to five
    # singleton decoys fit even on the 8-row boundary.
    row0 = rng.randint(0, h - n)
    phase = rng.randrange(2)
    for i in range(n):
        grid[row0 + i][c0 + ((i + phase) % 2)] = colors[i]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; Racket remains output authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    h, w, k, n_decoys = _draw_axes(ctx, profile, difficulty)
    rng = ctx.draw_rng("layout")
    graph_kind = {
        "canonical_path": "path",
        "branched": "branch",
        "larger_area_decoy": "branch",
        "cyclic": "cyclic",
    }[profile]
    macro_cells = _macro_graph(graph_kind, k, rng)
    macro_graph = _macro_neighbors(macro_cells)

    if profile in {"branched", "larger_area_decoy"}:
        seed_id = max(macro_graph, key=lambda i: (len(macro_graph[i]), -i))
    elif profile == "canonical_path" and (sample_index // 4) % 2:
        seed_id = max(macro_graph, key=lambda i: (len(macro_graph[i]), -i))
    else:
        seed_id = rng.randrange(k)

    colors = _cluster_colors(k, seed_id, rng)
    decoy_colors = _decoy_colors(
        n_decoys, set(colors.values()), rng, allow_eight=(profile == "cyclic")
    )
    grid = full_grid(h, w, 0)

    side = "left" if rng.randrange(2) else "right"
    ph = 2 * (max(r for r, _ in macro_cells) + 1)
    pw = 2 * (max(c for _, c in macro_cells) + 1)
    row0 = rng.randint(0, h - ph)
    if side == "left":
        col0 = 3 + rng.randint(0, (w - 3) - pw)
    else:
        col0 = rng.randint(0, (w - 3) - pw)
    _paint_cluster(
        grid,
        macro_cells,
        colors,
        row0=row0,
        col0=col0,
        rng=rng,
        profile=profile,
        seed_id=seed_id,
    )
    _paint_decoys(
        grid,
        side=side,
        profile=profile,
        n=n_decoys,
        colors=decoy_colors,
        rng=rng,
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid blue-cluster scene: {errors}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract and plausible rival rules
# ---------------------------------------------------------------------------


def _matrix_for_ids(info: dict[str, Any], ids: Iterable[int]) -> list[list[int]]:
    ordered = sorted(ids, key=lambda i: info["object_list"][i]["top_left"])
    return [
        [1 if r == c else (8 if ordered[c] in info["graph"][ordered[r]] else 0)
         for c in range(len(ordered))]
        for r in range(len(ordered))
    ]


def _expected_matrix(grid) -> list[list[int]]:
    """Python test mirror; generation never uses it as output authority."""
    info, errors = _analysis(grid)
    if errors or info is None:
        return []
    return _matrix_for_ids(info, info["seed_cluster"])


def _all_objects_matrix(grid) -> list[list[int]]:
    info, errors = _analysis(grid)
    if errors or info is None:
        return []
    return _matrix_for_ids(info, range(len(info["object_list"])))


def _path_by_count(grid) -> list[list[int]]:
    info, errors = _analysis(grid)
    if errors or info is None:
        return []
    n = len(info["seed_cluster"])
    return [
        [1 if r == c else (8 if abs(r - c) == 1 else 0) for c in range(n)]
        for r in range(n)
    ]


def _largest_area_cluster(grid) -> list[list[int]]:
    info, errors = _analysis(grid)
    if errors or info is None:
        return []
    components = info["graph_components"]
    chosen = max(
        components,
        key=lambda comp: (
            sum(len(info["object_list"][i]["cells"]) for i in comp),
            len(comp),
            tuple(-x for x in min(info["object_list"][i]["top_left"] for i in comp)),
        ),
    )
    return _matrix_for_ids(info, chosen)


def _cell_level_adjacency(grid) -> list[list[int]]:
    errors = _grid_errors(grid)
    if errors:
        return []
    blue_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if not blue_cells:
        return []
    start = min(blue_cells)
    nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARD:
            nxt = (r + dr, c + dc)
            if nxt in nonzero and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    cells = sorted(seen)
    return [
        [1 if r == c else (8 if abs(cells[r][0] - cells[c][0]) + abs(cells[r][1] - cells[c][1]) == 1 else 0)
         for c in range(len(cells))]
        for r in range(len(cells))
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "cell_level_adjacency": _cell_level_adjacency,
    "all_objects_matrix": _all_objects_matrix,
    "path_by_count": _path_by_count,
    "largest_area_cluster": _largest_area_cluster,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_multicell(grid) -> bool:
    info, errors = _analysis(grid)
    return not errors and info is not None and any(
        len(info["object_list"][i]["cells"]) > 1 for i in info["seed_cluster"]
    )


def _witness_decoys(grid) -> bool:
    info, errors = _analysis(grid)
    return not errors and info is not None and bool(info["decoys"])


def _witness_non_path(grid) -> bool:
    info, errors = _analysis(grid)
    return not errors and info is not None and info["graph_kind"] != "path"


def _witness_larger_area_decoy(grid) -> bool:
    info, errors = _analysis(grid)
    if errors or info is None:
        return False
    seed_area = sum(len(info["object_list"][i]["cells"]) for i in info["seed_cluster"])
    return any(
        info["seed"] not in comp
        and sum(len(info["object_list"][i]["cells"]) for i in comp) > seed_area
        for comp in info["graph_components"]
    )


SEMANTIC_WITNESSES = {
    "multi_cell_objects": _witness_multicell,
    "seed_cluster_excludes_decoys": _witness_decoys,
    "non_path_topology": _witness_non_path,
    "larger_area_nonblue_cluster": _witness_larger_area_decoy,
}
WITNESS_RIVALS = {
    "multi_cell_objects": ["cell_level_adjacency"],
    "seed_cluster_excludes_decoys": ["all_objects_matrix"],
    "non_path_topology": ["path_by_count"],
    "larger_area_nonblue_cluster": ["largest_area_cluster"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every four-demo sliding window must kill every named plausible rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful blue-cluster grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = self_check(demo["input"])
        if input_errors:
            reasons.append(f"demo {index} input is invalid: {input_errors[0]}")
            continue
        expected = _expected_matrix(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the blue-cluster adjacency matrix")
            continue
        valid_demos.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
