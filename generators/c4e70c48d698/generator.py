"""Generator for c4e70c48d698 — color components by graph distance.

A zero-background input contains exactly one blue (1) seed component.  Treat
all monochrome 4-connected components as graph vertices and connect two
vertices when their cells touch cardinally.  Repaint the seed-connected graph
by shortest-path layer: distance 0 -> 2, distance 1 -> 3, distance 2 -> 4,
and every distance >= 3 -> 6.  Components outside that connected graph vanish.

The teaching distribution deliberately breaks fixed-color, linear-order,
Manhattan-distance, exact-depth-palette, object-size, and keep-all shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c4e70c48d698"
TASK_ID = "c4e70c48d698"
VERSION = "3.0.0"
RULE_HASH = "a99ffbd8452c"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "u_path_7",
    "u_path_8",
    "branch_6",
    "star_tail_7",
    "cycle_tail_7",
    "double_branch_9",
)
SCHEDULE_PROFILES = SCENE_PROFILES

SUMMARY = (
    "A 0-background grid contains one blue seed, a seed-connected contact graph "
    "with explicit distance-0/1/2/3+ layers, and at least one detached object. "
    "Six replayable graph profiles cover long bent paths, branches, and a cycle. "
    "Component colors are assigned independently of distance, including the same "
    "input color at different output layers, while rotations, reflections, padding, "
    "palette size, and detached-object placement vary."
)

INVARIANTS = [
    "exactly one color-1 seed component",
    "the seed-connected component graph contains distances 0, 1, 2, and 3+",
    "at least one nonzero component is disconnected from the seed graph",
    "different touching components always have different input colors",
    "ordinary draws reuse an input color across different graph-distance layers",
    "all components are recolored only by seed-graph distance; detached components disappear",
]

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "sample_index schedule cycling through every profile",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Core component coordinates.  Cardinally adjacent coordinates are graph edges.
# The rendered component for every coordinate is a 2x2 monochrome block, so the
# component graph is exactly the grid-adjacency graph below while object size is
# visibly nontrivial.
_PROFILE_COORDS: dict[str, tuple[tuple[int, int], ...]] = {
    # Long U paths make a graph-far endpoint physically close to the seed.
    "u_path_7": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0)),
    "u_path_8": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1)),
    # One degree-3 branch with a depth-4 tail.
    "branch_6": ((1, 0), (1, 1), (1, 2), (0, 2), (2, 2), (2, 3)),
    # A degree-4 hub plus a tail; distinct from the smaller branch signature.
    "star_tail_7": ((1, 0), (1, 1), (1, 2), (0, 2), (2, 2), (1, 3), (1, 4)),
    # Tail into a four-cycle, then another tail.
    "cycle_tail_7": ((1, 0), (1, 1), (1, 2), (0, 2), (0, 3), (1, 3), (2, 3)),
    # Two separated degree-3 branch points.
    "double_branch_9": (
        (1, 0), (1, 1), (1, 2), (0, 2), (2, 2),
        (1, 3), (1, 4), (0, 4), (2, 4),
    ),
}

_CANONICAL_PROFILES = ((9, 12, 6), (10, 13, 7), (10, 14, 8))
_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DISTANCE_COLORS = {0: 2, 1: 3, 2: 4}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Replayable profile schedule; seed/difficulty only affect within-profile form."""
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _normalize_coords(coords: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in coords)
    min_c = min(c for _, c in coords)
    return tuple((r - min_r, c - min_c) for r, c in coords)


def _coord_variants(coords: tuple[tuple[int, int], ...]) -> list[tuple[tuple[int, int], ...]]:
    """All unique dihedral transforms, preserving component IDs/order."""
    transforms: tuple[Callable[[int, int], tuple[int, int]], ...] = (
        lambda r, c: (r, c),
        lambda r, c: (r, -c),
        lambda r, c: (-r, c),
        lambda r, c: (-r, -c),
        lambda r, c: (c, r),
        lambda r, c: (c, -r),
        lambda r, c: (-c, r),
        lambda r, c: (-c, -r),
    )
    out: list[tuple[tuple[int, int], ...]] = []
    seen: set[tuple[tuple[int, int], ...]] = set()
    for transform in transforms:
        variant = _normalize_coords(tuple(transform(r, c) for r, c in coords))
        if variant not in seen:
            seen.add(variant)
            out.append(variant)
    return out


def _coord_graph(coords: tuple[tuple[int, int], ...]) -> list[set[int]]:
    by_pos = {pos: i for i, pos in enumerate(coords)}
    graph = [set() for _ in coords]
    for i, (r, c) in enumerate(coords):
        for dr, dc in _DIR4:
            j = by_pos.get((r + dr, c + dc))
            if j is not None:
                graph[i].add(j)
    return graph


def _graph_distances(graph: list[set[int]], seed: int = 0) -> dict[int, int]:
    distances = {seed: 0}
    queue: deque[int] = deque([seed])
    while queue:
        i = queue.popleft()
        for j in graph[i]:
            if j not in distances:
                distances[j] = distances[i] + 1
                queue.append(j)
    return distances


def _graph_signature(graph: list[set[int]], nodes: set[int] | None = None) -> tuple[Any, ...]:
    selected = set(range(len(graph))) if nodes is None else set(nodes)
    degrees = sorted(sum(j in selected for j in graph[i]) for i in selected)
    edges = sum(degrees) // 2
    return len(selected), edges, tuple(degrees)


_PROFILE_SIGNATURES = {
    name: _graph_signature(_coord_graph(coords))
    for name, coords in _PROFILE_COORDS.items()
}
if len(set(_PROFILE_SIGNATURES.values())) != len(_PROFILE_SIGNATURES):
    raise RuntimeError("scene profiles must have unique component-graph signatures")
_SIGNATURE_TO_PROFILE = {signature: name for name, signature in _PROFILE_SIGNATURES.items()}


def _block_footprint(coords: tuple[tuple[int, int], ...], block: int = 2) -> tuple[int, int]:
    return (max(r for r, _ in coords) + 1) * block, (max(c for _, c in coords) + 1) * block


def _paint_rect(grid: list[list[int]], r0: int, c0: int, rh: int, cw: int, color: int) -> None:
    for r in range(r0, r0 + rh):
        for c in range(c0, c0 + cw):
            grid[r][c] = color


def _free_with_buffer(grid: list[list[int]], r0: int, c0: int, rh: int, cw: int) -> bool:
    h, w = len(grid), len(grid[0])
    if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + cw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + cw + 1)):
            if grid[r][c] != 0:
                return False
    return True


def _assign_component_colors(
    graph: list[set[int]],
    distances: dict[int, int],
    palette_size: int,
    detached_count: int,
    rng,
) -> tuple[list[int], list[int]]:
    """Properly color the graph while forcing one color across d=1 and d>=3."""
    other_count = palette_size - 2  # exclude background 0 and fixed seed 1
    if not 2 <= other_count <= 8:
        raise ValueError(f"unsupported palette size: {palette_size}")
    colors = rng.sample([c for c in range(3, 10)], other_count)

    distance_one = [i for i, d in distances.items() if d == 1]
    distance_far = [i for i, d in distances.items() if d >= 3]
    if not distance_one or not distance_far:
        raise ValueError("profile lacks required distance-1/distance-3+ layers")
    reuse_a = distance_one[0]
    reuse_b = max(distance_far, key=lambda i: (distances[i], i))
    if reuse_b in graph[reuse_a]:
        raise ValueError("reused-color witness nodes unexpectedly touch")

    assigned: dict[int, int] = {0: 1, reuse_a: colors[0], reuse_b: colors[0]}
    missing = list(colors[1:])
    order = sorted((i for i in distances if i not in assigned), key=lambda i: (distances[i], i))
    for node in order:
        forbidden = {assigned[j] for j in graph[node] if j in assigned}
        preferred = [c for c in missing if c not in forbidden]
        fallback = [c for c in colors if c not in forbidden]
        if not fallback:
            raise ValueError("could not assign distinct colors to touching components")
        color = preferred[0] if preferred else rng.choice(fallback)
        assigned[node] = color
        if color in missing:
            missing.remove(color)

    detached_colors: list[int] = []
    for _ in range(detached_count):
        if missing:
            color = missing.pop(0)
        else:
            color = rng.choice(colors)
        detached_colors.append(color)

    if missing:
        raise ValueError("not enough components to realize requested palette")
    return [assigned[i] for i in range(len(graph))], detached_colors


def _place_detached(
    grid: list[list[int]], colors: list[int], rng,
) -> list[tuple[tuple[int, int], ...]]:
    placed: list[tuple[tuple[int, int], ...]] = []
    shape_options = ((2, 2), (1, 2), (2, 1), (1, 1))
    for color in colors:
        candidates: list[tuple[int, int, int, int]] = []
        for rh, cw in shape_options:
            for r0 in range(len(grid) - rh + 1):
                for c0 in range(len(grid[0]) - cw + 1):
                    if _free_with_buffer(grid, r0, c0, rh, cw):
                        candidates.append((r0, c0, rh, cw))
            if candidates:
                break
        if not candidates:
            raise ValueError("could not place detached component with a one-cell buffer")
        r0, c0, rh, cw = rng.choice(candidates)
        _paint_rect(grid, r0, c0, rh, cw, color)
        placed.append(tuple((r, c) for r in range(r0, r0 + rh) for c in range(c0, c0 + cw)))
    return placed


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides) -> list[list[int]]:
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
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    rng = ctx.draw_rng("layout")

    base_coords = _PROFILE_COORDS[profile]
    variants = _coord_variants(base_coords)
    canonical_anchor = sample_index % 3 == 0
    if canonical_anchor:
        h, w, palette_size = _CANONICAL_PROFILES[(sample_index // 3) % len(_CANONICAL_PROFILES)]
        fitting = [v for v in variants if _block_footprint(v)[0] + 2 <= h and _block_footprint(v)[1] + 2 <= w]
        if not fitting:
            raise ValueError(f"profile {profile} does not fit canonical anchor {h}x{w}")
        coords = rng.choice(fitting)
    else:
        coords = rng.choice(variants)
        footprint_h, footprint_w = _block_footprint(coords)
        limits = {
            "easy": (9, 13, 12, 17),
            "medium": (10, 16, 13, 21),
            "hard": (12, 19, 15, 25),
        }.get(difficulty, (9, 17, 12, 23))
        h_lo, h_hi, w_lo, w_hi = limits
        h_lo = max(h_lo, footprint_h + 2)
        w_lo = max(w_lo, footprint_w + 2)
        h_hi = max(h_hi, h_lo)
        w_hi = max(w_hi, w_lo)
        h = rng.randint(h_lo, h_hi)
        w = rng.randint(w_lo, w_hi)
        palette_size = rng.choice((6, 7, 8))

    footprint_h, footprint_w = _block_footprint(coords)
    r0 = rng.randint(1, h - footprint_h - 1)
    c0 = rng.randint(1, w - footprint_w - 1)

    graph = _coord_graph(coords)
    distances = _graph_distances(graph)
    other_count = palette_size - 2
    max_unique_reachable = len(graph) - 2  # forced d1/d3+ color reuse
    detached_count = max(1, other_count - max_unique_reachable)
    if not canonical_anchor and difficulty == "hard" and sample_index % 2:
        detached_count = max(detached_count, 2)

    node_colors, detached_colors = _assign_component_colors(
        graph, distances, palette_size, detached_count, rng
    )
    grid = full_grid(h, w, 0)
    for node, (core_r, core_c) in enumerate(coords):
        _paint_rect(grid, r0 + 2 * core_r, c0 + 2 * core_c, 2, 2, node_colors[node])
    _place_detached(grid, detached_colors, rng)

    errors = self_check(grid, difficulty=difficulty, meta={"scene_profile": profile})
    if errors:
        raise ValueError(f"generated invalid scene: {errors}")
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise ValueError(f"scene profile was not recoverable: requested={profile!r}, observed={observed!r}")
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _adjacent(a: dict[str, Any], b: dict[str, Any]) -> bool:
    b_cells = set(b["cells"])
    return any((r + dr, c + dc) in b_cells for r, c in a["cells"] for dr, dc in _DIR4)


def _shape_key(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _analysis(grid: list[list[int]]) -> dict[str, Any]:
    components = _components(grid)
    graph = [set() for _ in components]
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            if _adjacent(components[i], components[j]):
                graph[i].add(j)
                graph[j].add(i)
    seeds = [i for i, component in enumerate(components) if component["color"] == 1]
    distances = _graph_distances(graph, seeds[0]) if len(seeds) == 1 else {}
    reachable = set(distances)
    disconnected = set(range(len(components))) - reachable
    signature = _graph_signature(graph, reachable) if reachable else None

    seed_cells = components[seeds[0]]["cells"] if len(seeds) == 1 else ()
    detour = False
    if seed_cells:
        for i, distance in distances.items():
            if distance < 3:
                continue
            manhattan = min(
                abs(r - sr) + abs(c - sc)
                for r, c in components[i]["cells"]
                for sr, sc in seed_cells
            )
            if manhattan < distance:
                detour = True
                break

    roles_by_color: dict[int, set[int | None]] = {}
    for i, component in enumerate(components):
        roles_by_color.setdefault(component["color"], set()).add(distances.get(i))
    color_reused_across_layers = any(
        len({role for role in roles if role is not None}) >= 2
        for color, roles in roles_by_color.items()
        if color != 1
    )

    shapes_by_layer: dict[tuple[tuple[int, int], ...], set[int]] = {}
    for i in reachable:
        shapes_by_layer.setdefault(_shape_key(components[i]["cells"]), set()).add(distances[i])
    same_shape_different_layers = any(len(layers) >= 2 for layers in shapes_by_layer.values())

    return {
        "components": components,
        "graph": graph,
        "seeds": seeds,
        "distances": distances,
        "reachable": reachable,
        "disconnected": disconnected,
        "signature": signature,
        "profile": _SIGNATURE_TO_PROFILE.get(signature),
        "has_cycle": bool(reachable) and sum(len(graph[i] & reachable) for i in reachable) // 2 >= len(reachable),
        "has_branch": any(len(graph[i] & reachable) >= 3 for i in reachable),
        "detour": detour,
        "color_reused_across_layers": color_reused_across_layers,
        "same_shape_different_layers": same_shape_different_layers,
        "has_multicell": any(len(component["cells"]) > 1 for component in components),
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    analysis = _analysis(grid)
    if len(analysis["seeds"]) != 1:
        raise ValueError("cannot observe scene_profile without exactly one seed")
    profile = analysis["profile"]
    if profile is None:
        raise ValueError(f"unrecognized reachable graph signature: {analysis['signature']!r}")
    return {"scene_profile": profile}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    analysis = _analysis(grid)
    errors: list[str] = []
    if len(analysis["seeds"]) != 1:
        errors.append(f"expected exactly one color-1 seed component, got {len(analysis['seeds'])}")
        return errors
    distances = set(analysis["distances"].values())
    if len(analysis["reachable"]) < 4:
        errors.append(f"seed graph must contain at least four components, got {len(analysis['reachable'])}")
    for required in (0, 1, 2):
        if required not in distances:
            errors.append(f"seed graph is missing distance layer {required}")
    if not distances or max(distances) < 3:
        errors.append("seed graph must contain a distance-3-or-more component")
    if not analysis["disconnected"]:
        errors.append("expected at least one detached component to exercise disappearance")
    if len(analysis["components"]) > 14:
        errors.append("too many components for the intended compact graph lesson")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 24 and 8 <= w <= 30):
        reasons.append(f"grid dimensions {h}x{w} fall outside the canonical-like envelope")
    palette_size = len({value for row in grid for value in row})
    if not 6 <= palette_size <= 8:
        reasons.append(f"expected 6..8 total colors, got {palette_size}")
    analysis = _analysis(grid)
    if not analysis["has_multicell"]:
        reasons.append("canonical scenes contain at least one multi-cell component")
    return reasons


def _distance_color(distance: int) -> int:
    return _DISTANCE_COLORS.get(distance, 6)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror only; the Racket rule remains the output authority."""
    analysis = _analysis(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for i, distance in analysis["distances"].items():
        color = _distance_color(distance)
        for r, c in analysis["components"][i]["cells"]:
            out[r][c] = color
    return out


def _rival_color_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: one output color per input color, learned from first use."""
    analysis = _analysis(grid)
    mapping: dict[int, int] = {}
    for i, component in enumerate(analysis["components"]):
        role = analysis["distances"].get(i)
        proposed = 0 if role is None else _distance_color(role)
        mapping.setdefault(component["color"], proposed)
    return [[0 if value == 0 else mapping[value] for value in row] for row in grid]


def _rival_manhattan_layers(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: use pixel Manhattan distance to the seed, not graph distance."""
    analysis = _analysis(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    if len(analysis["seeds"]) != 1:
        return out
    seed_cells = analysis["components"][analysis["seeds"][0]]["cells"]
    for i in analysis["reachable"]:
        cells = analysis["components"][i]["cells"]
        if i == analysis["seeds"][0]:
            distance = 0
        else:
            distance = min(abs(r - sr) + abs(c - sc) for r, c in cells for sr, sc in seed_cells)
        color = _distance_color(distance)
        for r, c in cells:
            out[r][c] = color
    return out


def _rival_no_erasure(grid: list[list[int]]) -> list[list[int]]:
    out = rule_mirror(grid)
    analysis = _analysis(grid)
    for i in analysis["disconnected"]:
        color = analysis["components"][i]["color"]
        for r, c in analysis["components"][i]["cells"]:
            out[r][c] = color
    return out


def _rival_exact_depth_palette(grid: list[list[int]]) -> list[list[int]]:
    palette = (2, 3, 4, 6, 5, 7, 8, 9)
    analysis = _analysis(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for i, distance in analysis["distances"].items():
        color = palette[min(distance, len(palette) - 1)]
        for r, c in analysis["components"][i]["cells"]:
            out[r][c] = color
    return out


def _rival_all_connected_magenta(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for i, distance in analysis["distances"].items():
        color = 2 if distance == 0 else 6
        for r, c in analysis["components"][i]["cells"]:
            out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "one_output_per_input_color": _rival_color_only,
    "pixel_manhattan_layers": _rival_manhattan_layers,
    "keep_detached_objects": _rival_no_erasure,
    "one_color_per_exact_depth": _rival_exact_depth_palette,
    "all_connected_nonseed_magenta": _rival_all_connected_magenta,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _has_distance(grid, distance: int) -> bool:
    return distance in set(_analysis(grid)["distances"].values())


def _has_distance_3plus(grid) -> bool:
    distances = _analysis(grid)["distances"].values()
    return bool(distances) and max(distances) >= 3


def _has_distance_4plus(grid) -> bool:
    distances = _analysis(grid)["distances"].values()
    return bool(distances) and max(distances) >= 4


SEMANTIC_WITNESSES = {
    "distance_0_seed": lambda grid: _has_distance(grid, 0),
    "distance_1_layer": lambda grid: _has_distance(grid, 1),
    "distance_2_layer": lambda grid: _has_distance(grid, 2),
    "distance_3plus_layer": _has_distance_3plus,
    "distance_cap_3plus": _has_distance_4plus,
    "detached_erasure": lambda grid: bool(_analysis(grid)["disconnected"]),
    "branched_contact_graph": lambda grid: _analysis(grid)["has_branch"],
    "cyclic_contact_graph": lambda grid: _analysis(grid)["has_cycle"],
    "graph_detour": lambda grid: _analysis(grid)["detour"],
    "color_reused_across_layers": lambda grid: _analysis(grid)["color_reused_across_layers"],
    "same_shape_different_layers": lambda grid: _analysis(grid)["same_shape_different_layers"],
}

WITNESS_RIVALS = {
    "distance_1_layer": ["all_connected_nonseed_magenta"],
    "distance_2_layer": ["all_connected_nonseed_magenta"],
    "distance_cap_3plus": ["one_color_per_exact_depth"],
    "detached_erasure": ["keep_detached_objects"],
    "graph_detour": ["pixel_manhattan_layers"],
    "color_reused_across_layers": ["one_output_per_input_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    del query
    survivors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    if survivors:
        return [f"plausible rival(s) survive every demonstration: {', '.join(sorted(survivors))}"]
    return []
