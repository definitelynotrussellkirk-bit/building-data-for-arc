"""Semantic generator for ARC task a55c1997c5e3.

The input contains one red 2x2 start block and cyan 2x2 node blocks.  Nodes
are adjacent when their top-left corners share a row or column and no other
node lies between them.  The oracle paints orange corridors along the longest
simple path from the red block; equal-length paths are ordered
lexicographically by direction priority right, down, left, up.

Version 2.2.1 retains the five original graph profiles and adds a compound
direction-order witness. Six demonstrations and one query follow a ten-slot
schedule: every seven-slot window contains two compound witnesses, two
endpoint-tie counterexamples, and two length-before-greedy witnesses. Any
one query holdout therefore leaves a demonstration for each distinction.
The compound witness makes the selected node-count-optimal path physically
longer than an alternative; the endpoint witness makes it physically shorter.
Neither maximizing nor minimizing corridor length replaces the tie sequence.
Labels remain canonical Racket.
"""
from __future__ import annotations

from collections import defaultdict
from functools import partial
from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid


GENERATOR_ID = "a55c1997c5e3"
TASK_ID = GENERATOR_ID
VERSION = "2.2.1"
RULE_HASH = "d24e861b64b5"

SUMMARY = (
    "Treat each exact red/cyan 2x2 block as a visibility-graph node. Starting "
    "at the unique red block, choose the longest simple orthogonal visibility "
    "path; break equal-length ties lexicographically by right, down, left, up, "
    "then paint orange corridors only between consecutive chosen nodes."
)

EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "inputs use only background 0, one red 2x2 start block, and at least two cyan 2x2 blocks",
    "every non-background component is an exact isolated 2x2 block",
    "axis-aligned node blocks are separated by at least one blank row or column",
    "visibility edges join nearest same-row or same-column blocks only",
    "the selected path is a longest simple path from red, with ties ordered right/down/left/up",
    "ordinary scenes contain a non-selected distractor node and require at least one orange corridor",
]

SCENE_PROFILES = (
    "longest_over_priority",
    "tie_right_over_down",
    "tie_down_over_left",
    "deep_lexicographic_tie",
    "branchy_unique_longest",
    "complete_direction_order",
)

# C / endpoint / length witnesses each occur at cyclic gaps 3, 3, 4.
# Any seven consecutive slots contain at least two of each category, so a
# query rotation cannot remove its only distinguishing demonstration.
SCHEDULE_PROFILES = (
    "complete_direction_order", "tie_down_over_left", "longest_over_priority",
    "complete_direction_order", "tie_down_over_left", "deep_lexicographic_tie",
    "complete_direction_order", "tie_down_over_left", "branchy_unique_longest",
    "tie_right_over_down",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed with 30% canonical-dimension anchors",
        "valid": "16..28",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed with 30% canonical-dimension anchors",
        "valid": "18..30",
    },
    "scene_profile": {
        "type": "str",
        "default": "ten-slot sample_index schedule covering all six semantic profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Abstract top-left coordinates. Actual row/column levels are independently
# stretched and translated, preserving only visibility order.
_TEMPLATES: dict[str, dict[str, Any]] = {
    # A right neighbor is locally preferred, but its branch is shorter. The
    # unique longest path begins left, proving that length outranks direction.
    "longest_over_priority": {
        "nodes": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0)),
        "start": (0, 3),
    },
    # Equal maximum paths begin right and down; right must win.
    "tie_right_over_down": {
        "nodes": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2)),
        "start": (0, 0),
    },
    # No right branch exists. Equal maximum paths begin down and left; down wins.
    "tie_down_over_left": {
        "nodes": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3)),
        "start": (0, 3),
    },
    # Equal maximum paths share the first left step and diverge later, so the
    # tie cannot be solved by looking at the first direction alone.
    "deep_lexicographic_tie": {
        "nodes": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
        "start": (0, 2),
    },
    # A larger branched graph with a unique longest path and two off-path nodes.
    "branchy_unique_longest": {
        "nodes": (
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 0), (1, 1), (2, 1),
            # A disconnected cyan pair matches the canonical task's lawful
            # isolated-distractor branch and raises object-count support to 10.
            (3, 5), (4, 5),
        ),
        "start": (0, 2),
    },
    # Three consecutive tie decisions exhibit R>D, D>L, and L>U. Its
    # selected output refutes every other constant direction permutation.
    "complete_direction_order": {
        "nodes": (
            (0, 3), (0, 4), (1, 3), (1, 4),
            (2, 4), (4, 4), (2, 2), (4, 2),
            (4, 1), (4, 0), (3, 1), (3, 0),
        ),
        "start": (0, 3),
    },
}

_CANONICAL_DIMS = ((16, 18), (26, 28), (26, 25), (26, 18), (22, 23))
_CANONICAL_ANCHOR_RATE = 0.30
_MAX_ANALYSIS_PATHS = 100_000


def _validate_call(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 16, 28), ("grid_w", 18, 30)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        if overrides["scene_profile"] not in SCENE_PROFILES:
            raise ValueError(
                "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
            )


def _sample_levels(count: int, max_top_left: int, rng) -> list[int]:
    """Choose ordered block positions with at least one blank line between."""
    if count <= 0:
        return []
    if max_top_left < 3 * (count - 1):
        raise ValueError(
            f"grid cannot fit {count} ordered 2x2 block levels with blank gaps"
        )
    candidates = list(range(max_top_left + 1))
    for _ in range(256):
        levels = sorted(rng.sample(candidates, count))
        if all(b - a >= 3 for a, b in zip(levels, levels[1:])):
            return levels
    # Deterministic fallback. Spread any residual room between translation and
    # the final gap rather than rejecting a valid boundary dimension.
    span = 3 * (count - 1)
    slack = max_top_left - span
    offset = rng.randint(0, slack)
    return [offset + 3 * i for i in range(count)]


def _sample_direction_layout(h: int, w: int, rng) -> tuple[list[int], list[int]]:
    """Stretch the compound graph while preserving a physical-distance rival.

    At its final L/U tie, the official left branch must be physically longer.
    All positions remain random; only that gap inequality is constrained.
    """
    vertical_gap = rng.randint(3, min(h - 11, w - 12))
    horizontal_gap = rng.randint(vertical_gap + 1, w - 11)
    rows = _sample_levels(4, h - 2 - vertical_gap, rng)
    rows.append(rows[-1] + vertical_gap)
    prefix = _sample_levels(4, w - 2 - horizontal_gap, rng)
    cols = [prefix[0], *(col + horizontal_gap for col in prefix)]
    return rows, cols


def _sample_endpoint_columns(w: int, rng) -> list[int]:
    """Make the endpoint rival and maximum-distance rivals disagree together.

    The alternate D,L,U,L route has the same node count as the official
    D,L,U,R route but exceeds its physical length by first_gap-second_gap.
    """
    second_gap = rng.randint(3, (w - 6) // 2)
    first_gap = rng.randint(second_gap + 1, w - 5 - second_gap)
    third_gap = rng.randint(3, w - 2 - first_gap - second_gap)
    offset = rng.randint(0, w - 2 - first_gap - second_gap - third_gap)
    return [
        offset, offset + first_gap,
        offset + first_gap + second_gap,
        offset + first_gap + second_gap + third_gap,
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    has_override = any(overrides.get(name) is not None for name in AXES)
    canonical_anchor = (
        not has_override
        and ctx.draw_rng("canonical_anchor").random() < _CANONICAL_ANCHOR_RATE
    )
    if canonical_anchor:
        h0, w0 = _CANONICAL_DIMS[
            ctx.draw_rng("canonical_dims").randrange(len(_CANONICAL_DIMS))
        ]
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
    else:
        h = ctx.draw_int_diff("grid_h", 16, 28)
        w = ctx.draw_int_diff("grid_w", 18, 30)

    template = _TEMPLATES[profile]
    abstract_nodes = tuple(template["nodes"])
    abstract_rows = sorted({r for r, _ in abstract_nodes})
    abstract_cols = sorted({c for _, c in abstract_nodes})
    rng = ctx.draw_rng("layout")
    if profile == "complete_direction_order":
        row_levels, col_levels = _sample_direction_layout(h, w, rng)
    else:
        row_levels = _sample_levels(len(abstract_rows), h - 2, rng)
        if profile == "tie_down_over_left":
            col_levels = _sample_endpoint_columns(w, rng)
        else:
            col_levels = _sample_levels(len(abstract_cols), w - 2, rng)
    row_map = dict(zip(abstract_rows, row_levels))
    col_map = dict(zip(abstract_cols, col_levels))

    start = template["start"]
    grid = full_grid(h, w, 0)
    for node in abstract_nodes:
        color = 2 if node == start else 8
        draw_rect(grid, row_map[node[0]], col_map[node[1]], 2, 2, color)
    return grid


def _component_cells(grid) -> tuple[list[tuple[int, list[tuple[int, int]]]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return [], ["empty row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return [], ["ragged grid"]
    if any(isinstance(v, bool) or not isinstance(v, int) for row in grid for v in row):
        return [], ["grid cells must be integer ARC colors"]

    h = len(grid)
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, list[tuple[int, int]]]] = []
    for sr in range(h):
        for sc in range(width):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components, []


def _extract_nodes(grid) -> tuple[list[tuple[int, int, int]], list[str]]:
    components, errors = _component_cells(grid)
    if errors:
        return [], errors
    nodes: list[tuple[int, int, int]] = []
    for color, cells in components:
        if color not in (2, 8):
            errors.append(f"unexpected input color {color}; only 0, 2, and 8 are lawful")
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if len(cells) != 4 or (r1 - r0, c1 - c0) != (1, 1) or set(cells) != expected:
            errors.append(
                f"color-{color} component at ({r0},{c0}) is not an exact isolated 2x2 block"
            )
            continue
        nodes.append((r0, c0, color))
    nodes.sort()
    return nodes, errors


def _visibility_graph(
    nodes: list[tuple[int, int, int]],
) -> dict[tuple[int, int], set[tuple[int, int]]]:
    coords = [(r, c) for r, c, _ in nodes]
    graph = {coord: set() for coord in coords}
    by_row: dict[int, list[tuple[int, int]]] = defaultdict(list)
    by_col: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for coord in coords:
        by_row[coord[0]].append(coord)
        by_col[coord[1]].append(coord)
    for line in by_row.values():
        line.sort(key=lambda p: p[1])
        for left, right in zip(line, line[1:]):
            graph[left].add(right)
            graph[right].add(left)
    for line in by_col.values():
        line.sort(key=lambda p: p[0])
        for top, bottom in zip(line, line[1:]):
            graph[top].add(bottom)
            graph[bottom].add(top)
    return graph


def _direction(a: tuple[int, int], b: tuple[int, int]) -> int:
    if a[0] == b[0]:
        return 0 if a[1] < b[1] else 2
    return 1 if a[0] < b[0] else 3


def _path_directions(path: list[tuple[int, int]]) -> tuple[int, ...]:
    return tuple(_direction(a, b) for a, b in zip(path, path[1:]))


def _maximal_paths(
    graph: dict[tuple[int, int], set[tuple[int, int]]],
    start: tuple[int, int],
) -> tuple[list[list[tuple[int, int]]], bool]:
    paths: list[list[tuple[int, int]]] = []
    overflow = False

    def walk(current, visited, path) -> None:
        nonlocal overflow
        if overflow:
            return
        choices = [node for node in graph[current] if node not in visited]
        if not choices:
            paths.append(path)
            if len(paths) > _MAX_ANALYSIS_PATHS:
                overflow = True
            return
        for node in choices:
            walk(node, visited | {node}, path + [node])

    walk(start, {start}, [start])
    return paths, overflow


def _analyze(grid) -> dict[str, Any]:
    nodes, errors = _extract_nodes(grid)
    result: dict[str, Any] = {
        "errors": list(errors),
        "nodes": nodes,
        "graph": {},
        "start": None,
        "paths": [],
        "best_path": [],
        "max_paths": [],
    }
    if errors:
        return result
    starts = [(r, c) for r, c, color in nodes if color == 2]
    cyan = [(r, c) for r, c, color in nodes if color == 8]
    if len(starts) != 1:
        result["errors"].append(f"expected exactly one red start block, found {len(starts)}")
    if len(cyan) < 2:
        result["errors"].append(f"expected at least two cyan blocks, found {len(cyan)}")
    if len(nodes) > 16:
        result["errors"].append("more than 16 nodes makes exhaustive path semantics unsafe")
    if result["errors"]:
        return result

    start = starts[0]
    graph = _visibility_graph(nodes)
    result["start"] = start
    result["graph"] = graph
    touching_edges = {
        tuple(sorted((node, neighbor)))
        for node, neighbors in graph.items()
        for neighbor in neighbors
        if abs(node[0] - neighbor[0]) + abs(node[1] - neighbor[1]) == 2
    }
    if touching_edges:
        result["errors"].append(
            "axis-aligned node blocks must leave at least one blank corridor cell"
        )
        return result
    paths, overflow = _maximal_paths(graph, start)
    if overflow:
        result["errors"].append("visibility graph has too many maximal simple paths")
        return result
    if not paths:
        result["errors"].append("red start has no executable path")
        return result
    best = min(paths, key=lambda p: (-len(p), _path_directions(p)))
    max_len = len(best)
    max_paths = [p for p in paths if len(p) == max_len]
    result["paths"] = paths
    result["best_path"] = best
    result["max_paths"] = max_paths
    if len(best) < 2:
        result["errors"].append("red start is isolated, so the transformation is identity")
    else:
        corridor_cells = sum(
            max(abs(a[0] - b[0]), abs(a[1] - b[1])) - 2
            for a, b in zip(best, best[1:])
        ) * 2
        if corridor_cells <= 0:
            result["errors"].append("selected path has no blank corridor cells to paint")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed blocks, ambiguous palette roles, and no-op scenes."""
    return _analyze(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-input predicate; it accepts all five canonical inputs."""
    return self_check(grid)


def _normalized_signature(nodes: list[tuple[int, int, int]]) -> tuple:
    rows = {r: i for i, r in enumerate(sorted({r for r, _, _ in nodes}))}
    cols = {c: i for i, c in enumerate(sorted({c for _, c, _ in nodes}))}
    return tuple(sorted((rows[r], cols[c], color) for r, c, color in nodes))


def _template_signature(profile: str) -> tuple:
    template = _TEMPLATES[profile]
    start = template["start"]
    return tuple(
        sorted((r, c, 2 if (r, c) == start else 8) for r, c in template["nodes"])
    )


_TEMPLATE_SIGNATURES = {
    _template_signature(profile): profile for profile in SCENE_PROFILES
}


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    h = len(grid) if isinstance(grid, (list, tuple)) else 0
    w = (
        len(grid[0])
        if h and isinstance(grid[0], (list, tuple))
        else 0
    )
    observed: dict[str, Any] = {"grid_h": h, "grid_w": w}
    nodes, errors = _extract_nodes(grid)
    if not errors:
        profile = _TEMPLATE_SIGNATURES.get(_normalized_signature(nodes))
        if profile is not None:
            observed["scene_profile"] = profile
    return observed


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    graph = analysis["graph"]
    best = analysis["best_path"]
    max_paths = analysis["max_paths"]
    return {
        **observe_overrides(grid),
        "valid": not analysis["errors"],
        "errors": list(analysis["errors"]),
        "node_count": len(analysis["nodes"]),
        "edge_count": sum(len(v) for v in graph.values()) // 2 if graph else 0,
        "selected_path_length": len(best),
        "max_path_tie_count": len(max_paths),
        "selected_directions": list(_path_directions(best)),
        "off_path_nodes": max(0, len(analysis["nodes"]) - len(best)),
        "branch_nodes": sum(len(neighbors) >= 3 for neighbors in graph.values()) if graph else 0,
    }


def _has_horizontal(grid) -> bool:
    best = _analyze(grid)["best_path"]
    return any(a[0] == b[0] for a, b in zip(best, best[1:]))


def _has_vertical(grid) -> bool:
    best = _analyze(grid)["best_path"]
    return any(a[1] == b[1] for a, b in zip(best, best[1:]))


def _has_off_path_distractor(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and len(analysis["nodes"]) > len(analysis["best_path"])


def _has_branch_node(grid) -> bool:
    graph = _analyze(grid)["graph"]
    return any(len(neighbors) >= 3 for neighbors in graph.values())


def _longest_beats_priority(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"] or len(analysis["best_path"]) < 2:
        return False
    best = analysis["best_path"]
    selected_dir = _direction(best[0], best[1])
    by_first: dict[int, int] = defaultdict(int)
    for path in analysis["paths"]:
        if len(path) >= 2:
            by_first[_direction(path[0], path[1])] = max(by_first[_direction(path[0], path[1])], len(path))
    return any(priority < selected_dir and length < len(best) for priority, length in by_first.items())


def _first_direction_tie(grid) -> bool:
    analysis = _analyze(grid)
    sequences = [_path_directions(path) for path in analysis["max_paths"]]
    return len({seq[0] for seq in sequences if seq}) >= 2


def _deep_direction_tie(grid) -> bool:
    analysis = _analyze(grid)
    sequences = [_path_directions(path) for path in analysis["max_paths"]]
    for i, left in enumerate(sequences):
        for right in sequences[i + 1:]:
            for depth, (a, b) in enumerate(zip(left, right)):
                if a != b:
                    if depth >= 1:
                        return True
                    break
    return False


def _complete_direction_ties(grid) -> bool:
    analysis = _analyze(grid)
    best = _path_directions(analysis["best_path"])
    distinguished = set()
    for path in analysis["max_paths"]:
        for preferred, alternative in zip(best, _path_directions(path)):
            if preferred != alternative:
                distinguished.add((preferred, alternative))
                break
    return {(0, 1), (1, 2), (2, 3)} <= distinguished


def _physical_distance_tie(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return _path_distance(analysis["best_path"]) > min(
        _path_distance(path) for path in analysis["max_paths"]
    )


def _longer_distance_tie(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return _path_distance(analysis["best_path"]) < max(
        _path_distance(path) for path in analysis["max_paths"]
    )


def _endpoint_order_tie(grid) -> bool:
    return _rival_first_step_then_endpoint(grid) != _official_python_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "horizontal_corridor": _has_horizontal,
    "vertical_corridor": _has_vertical,
    "off_path_distractor": _has_off_path_distractor,
    "branch_node": _has_branch_node,
    "longest_beats_direction_priority": _longest_beats_priority,
    "first_direction_tie_break": _first_direction_tie,
    "deep_lexicographic_tie_break": _deep_direction_tie,
    "complete_direction_order": _complete_direction_ties,
    "lexicographic_tie_beats_shorter_distance": _physical_distance_tie,
    "lexicographic_tie_beats_longer_distance": _longer_distance_tie,
    "full_tie_sequence_beats_endpoint_order": _endpoint_order_tie,
}


def _paint_edge(out, a: tuple[int, int], b: tuple[int, int], color: int = 7) -> None:
    if a[0] == b[0]:
        for row in range(a[0], a[0] + 2):
            for col in range(min(a[1], b[1]) + 2, max(a[1], b[1])):
                out[row][col] = color
    elif a[1] == b[1]:
        for row in range(min(a[0], b[0]) + 2, max(a[0], b[0])):
            for col in range(a[1], a[1] + 2):
                out[row][col] = color


def _paint_edges(grid, edges) -> list[list[int]]:
    out = [list(row) for row in grid]
    for a, b in edges:
        _paint_edge(out, a, b)
    return out


def _official_python_mirror(grid) -> list[list[int]]:
    """Test-only mirror of the canonical Racket rule; never used for labels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_edges(grid, zip(analysis["best_path"], analysis["best_path"][1:]))


def _rival_identity(grid) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_all_visible_edges(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    edges = {
        tuple(sorted((node, neighbor)))
        for node, neighbors in analysis["graph"].items()
        for neighbor in neighbors
    }
    return _paint_edges(grid, sorted(edges))


def _rival_greedy_direction(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    current = analysis["start"]
    visited = {current}
    path = [current]
    while True:
        choices = [node for node in analysis["graph"][current] if node not in visited]
        if not choices:
            break
        current = min(choices, key=lambda node: (_direction(path[-1], node), node))
        path.append(current)
        visited.add(current)
    return _paint_edges(grid, zip(path, path[1:]))


def _rival_first_edge_only(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"] or len(analysis["best_path"]) < 2:
        return [list(row) for row in grid]
    return _paint_edges(grid, [(analysis["best_path"][0], analysis["best_path"][1])])


def _rival_start_star(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    start = analysis["start"]
    return _paint_edges(grid, [(start, node) for node in analysis["graph"][start]])


def _rival_reverse_tie_priority(grid) -> list[list[int]]:
    """Choose a longest path but reverse the official direction tie order."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    best = max(analysis["max_paths"], key=_path_directions)
    return _paint_edges(grid, zip(best, best[1:]))


_RIVALS = {
    "identity_or_marker_echo": _rival_identity,
    "connect_every_visible_edge": _rival_all_visible_edges,
    "greedy_direction_priority": _rival_greedy_direction,
    "paint_only_first_connection": _rival_first_edge_only,
    "connect_only_start_neighbors": _rival_start_star,
    "reverse_longest_path_tie_priority": _rival_reverse_tie_priority,
}


def _rival_longest_with_order(grid, direction_order) -> list[list[int]]:
    """Keep node-count optimality but use another constant direction order."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    ranks = {direction: rank for rank, direction in enumerate(direction_order)}
    best = min(
        analysis["max_paths"],
        key=lambda path: tuple(ranks[d] for d in _path_directions(path)),
    )
    return _paint_edges(grid, zip(best, best[1:]))


def _rival_up_before_left(grid) -> list[list[int]]:
    return _rival_longest_with_order(grid, (0, 1, 3, 2))


def _rival_up_before_down(grid) -> list[list[int]]:
    return _rival_longest_with_order(grid, (0, 3, 1, 2))


def _rival_up_before_right(grid) -> list[list[int]]:
    return _rival_longest_with_order(grid, (3, 0, 1, 2))


_CANONICAL_UP_SHORTCUTS = {
    "longest_up_before_left": _rival_up_before_left,
    "longest_up_before_down": _rival_up_before_down,
    "longest_up_before_right": _rival_up_before_right,
}


_DIRECTION_RIVALS = dict(_CANONICAL_UP_SHORTCUTS)
for _order in permutations((0, 1, 2, 3)):
    if _order in ((0, 1, 2, 3), (0, 1, 3, 2), (0, 3, 1, 2), (3, 0, 1, 2)):
        continue
    _name = "longest_tie_order_" + "".join("RDLU"[d] for d in _order)
    _DIRECTION_RIVALS[_name] = partial(_rival_longest_with_order, direction_order=_order)


def _path_distance(path) -> int:
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(path, path[1:]))


def _rival_first_step_then_endpoint(grid) -> list[list[int]]:
    """A canonical-fit rival that discards most of the direction sequence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    best = min(
        analysis["max_paths"],
        key=lambda path: (_path_directions(path)[:1], path[-1], _path_directions(path)),
    )
    return _paint_edges(grid, zip(best, best[1:]))


def _rival_shortest_distance_tie(grid) -> list[list[int]]:
    """Keep maximum node count, then minimize physical travel distance."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    best = min(
        analysis["max_paths"],
        key=lambda path: (_path_distance(path), _path_directions(path)),
    )
    return _paint_edges(grid, zip(best, best[1:]))


def _rival_maximum_distance(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    best = min(analysis["paths"], key=lambda path: (-_path_distance(path), _path_directions(path)))
    return _paint_edges(grid, zip(best, best[1:]))


def _rival_maximum_painted_cells(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]

    def painted_count(path):
        output = _paint_edges(grid, zip(path, path[1:]))
        return sum(color == 7 for row in output for color in row)

    best = min(analysis["paths"], key=lambda path: (-painted_count(path), _path_directions(path)))
    return _paint_edges(grid, zip(best, best[1:]))


def _rival_longest_distance_tie(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    best = min(analysis["max_paths"], key=lambda path: (-_path_distance(path), _path_directions(path)))
    return _paint_edges(grid, zip(best, best[1:]))


_PHYSICAL_LENGTH_RIVALS = {
    "maximum_physical_distance": _rival_maximum_distance,
    "maximum_painted_cells": _rival_maximum_painted_cells,
    "longest_then_longest_distance": _rival_longest_distance_tie,
}


_CANONICAL_TIE_SHORTCUTS = {
    **_CANONICAL_UP_SHORTCUTS,
    "longest_first_step_then_endpoint": _rival_first_step_then_endpoint,
    "longest_then_shortest_distance": _rival_shortest_distance_tie,
}

# Contract-v1.1 semantic declarations.  These are deliberately task-local:
# the gate checks every claim against the real Racket oracle before accepting
# it, so a future topology edit cannot silently preserve a stale witness name.
SEMANTIC_RIVALS = {**_RIVALS, **_DIRECTION_RIVALS, **_CANONICAL_TIE_SHORTCUTS, **_PHYSICAL_LENGTH_RIVALS}
WITNESS_RIVALS = {
    "horizontal_corridor": ["identity_or_marker_echo"],
    "vertical_corridor": ["identity_or_marker_echo"],
    "off_path_distractor": ["connect_every_visible_edge"],
    "branch_node": [
        "connect_every_visible_edge",
        "connect_only_start_neighbors",
    ],
    "longest_beats_direction_priority": ["greedy_direction_priority"],
    "first_direction_tie_break": ["reverse_longest_path_tie_priority"],
    "deep_lexicographic_tie_break": ["reverse_longest_path_tie_priority"],
    "complete_direction_order": list(_DIRECTION_RIVALS),
    "lexicographic_tie_beats_shorter_distance": ["longest_then_shortest_distance"],
    "lexicographic_tie_beats_longer_distance": ["longest_then_longest_distance"],
    "full_tie_sequence_beats_endpoint_order": ["longest_first_step_then_endpoint"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The six original heuristic rivals fail at least one canonical pair. They
# remain useful lesson competitors. These five tie alternatives fit all five.
CANONICAL_SHORTCUTS = dict(_CANONICAL_TIE_SHORTCUTS)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic ten-slot teaching schedule to the gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def lesson_identifiable(demos, query) -> list[str]:
    """Check six visible demos against witnesses and executable named rivals."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = list(demos)
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errs = strict_canonical_like(pair["input"])
        if errs:
            reasons.append(f"demo {index} is not lawful: {errs[0]}")
            continue
        if _official_python_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the pinned Python audit mirror")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is not lawful: {query_errors[0]}")
    elif _official_python_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the pinned Python audit mirror")

    required = {
        "longest-over-priority": _longest_beats_priority,
        "first-direction tie": _first_direction_tie,
        "deep lexicographic tie": _deep_direction_tie,
        "off-path distractor": _has_off_path_distractor,
        "complete direction-order": _complete_direction_ties,
        "lexicographic tie over physical distance": _physical_distance_tie,
        "lexicographic tie over longer physical distance": _longer_distance_tie,
        "full tie sequence over endpoint order": _endpoint_order_tie,
    }
    for name, predicate in required.items():
        if not any(
            isinstance(pair, dict)
            and "input" in pair
            and predicate(pair["input"])
            for pair in pairs
        ):
            reasons.append(f"demonstrations lack {name} witness")

    for name, rival in LESSON_COMPETITORS.items():
        rejected = any(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) != pair["output"]
            for pair in pairs
        )
        if not rejected:
            if rival(query["input"]) == query["output"]:
                # Explicit answer-equivalence exception: the demos did not
                # separate this rival, but it cannot change this query answer.
                continue
            reasons.append(f"named rival remains viable on demos: {name}")
    return reasons
