"""Curriculum for S12_H1: find articulation objects in the contact graph.

An object is a monochromatic four-connected component.  Two objects are graph
neighbors when any of their cells touch cardinally.  The labeler paints every
object whose removal increases the graph's connected-component count cyan (8)
on a blank grid of the same size.

Ordinary lessons use a four-slot star/cycle/triangle/cycle schedule so every
three-demonstration query rotation retains a biconnected contrast.  The final profile is a deliberate contrast: target,
maximum-degree, largest-area, and input-color-2 heuristics no longer agree.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a7a47f5cee60"
TASK_ID = GENERATOR_ID
VERSION = "3.0.2"
RULE_HASH = "2c1f4bbab8e6"

SUMMARY = (
    "Build a contact graph of differently colored four-connected objects and "
    "paint only its unique articulation object cyan on a blank same-size grid. "
    "Disconnected distractors and a scheduled biconnected contrast refute "
    "color, area, and maximum-degree shortcuts."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("star", "triangle", "cycle")
_LESSON_SCHEDULE = ("star", "cycle", "triangle", "cycle")
HELPFUL_TEXTURES = SCHEDULE_PROFILES
DEGENERATE_TEXTURES = ("no_articulation", "multiple_articulations", "empty")
_CANONICAL_SIZES = ((9, 11), (10, 12), (10, 13))
_MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))

INVARIANTS = [
    "background is 0 and foreground cells are ARC colors 1..9",
    "objects are monochromatic four-connected components",
    "ordinary inputs have exactly one articulation object of area at least two",
    "ordinary inputs include at least one disconnected distractor object",
    "ordinary inputs use a distinct color for every object and color 2 is a decoy",
    "cyan 8 appears in roughly 10% of inputs, only on the disconnected distractor",
]
AXES = {
    "grid_h": {
        "type": "int",
        "default": "45% canonical-scale, else difficulty-scaled 9..18",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "45% canonical-scale, else difficulty-scaled 11..22",
        "valid": "11..22",
    },
    "texture": {
        "type": "str",
        "default": "four-slot star|cycle|triangle|cycle lesson schedule",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Symbolic components.  T is the true articulation object.  These are compact
# topology certificates; dihedral transforms and translation provide geometry.
_TEMPLATES = {
    # Graph: A-T-B and T-C (a degree-three star).
    "star": {
        "A": ((0, 2),),
        "B": ((1, 1),),
        "C": ((1, 4),),
        "T": ((1, 2), (1, 3), (2, 2), (2, 3)),
    },
    # Graph: leaf A--T, with T-B-C-T forming a triangle.
    "triangle": {
        "A": ((0, 1),),
        "T": ((1, 0), (1, 1), (2, 0), (2, 1)),
        "B": ((1, 2), (1, 3), (2, 3)),
        "C": ((2, 2),),
    },
    # Core is K4 minus T-C: edges TB, TD, BD, BC, DC.  A is a leaf on T.
    # T, B, and D tie at degree three; B and D are larger than T, but only T
    # disconnects A.  This makes the rule identifiable rather than correlated.
    "cycle": {
        "A": ((0, 0),),
        "T": ((0, 1), (1, 1)),
        "B": ((0, 2), (0, 3), (1, 3)),
        "D": ((1, 2), (2, 1), (2, 2)),
        "C": ((2, 3),),
    },
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four-pair lesson keeps a cycle contrast after any query rotation."""
    del seed, difficulty
    return _LESSON_SCHEDULE[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _valid_difficulty(value):
    if value in (None, "easy", "medium", "hard"):
        return True
    return type(value) in (int, float) and not isinstance(value, bool) and 0 <= value <= 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"Unknown override axis/axes: {unknown}; supported: {sorted(AXES)}")
    if not _valid_difficulty(difficulty):
        raise ValueError("difficulty must be None, easy, medium, hard, or a number in [0, 1]")
    for key, lo, hi in (("grid_h", 9, 18), ("grid_w", 11, 22)):
        value = overrides.get(key)
        if value is not None and type(value) is not int:
            raise ValueError(f"{key} must be a Python integer in [{lo}, {hi}]")
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{key} must be a Python integer in [{lo}, {hi}]")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scale_rng = ctx.draw_rng("scale_profile")
    canonical_scale = scale_rng.random() < 0.45
    preferred_h, preferred_w = scale_rng.choice(_CANONICAL_SIZES)

    def dimension(key, lo, hi, preferred):
        if overrides.get(key) is not None:
            return ctx.draw_int_strict(key, lo, hi)
        if canonical_scale:
            return ctx.draw_choice(key, (preferred,))
        return ctx.draw_int_diff(key, lo, hi)

    h = dimension("grid_h", 9, 18, preferred_h)
    w = dimension("grid_w", 11, 22, preferred_w)

    if overrides.get("texture") is None:
        choices = (schedule_profile(seed, sample_index, difficulty),)
    else:
        choices = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
    texture = ctx.draw_choice("texture", choices)
    if texture in DEGENERATE_TEXTURES:
        return _draw_degenerate(texture, h, w)

    template = _transform_template(_TEMPLATES[texture], ctx.draw_rng("orientation").randrange(8))
    labels = sorted(template)
    all_labels = labels + ["X"]  # X is a disconnected 2x2 distractor.
    include_input_eight = ctx.draw_rng("input_eight").random() < 0.10
    colors = _assign_colors(all_labels, ctx.draw_rng("palette"), include_input_eight)

    template_h = 1 + max(r for cells in template.values() for r, _ in cells)
    template_w = 1 + max(c for cells in template.values() for _, c in cells)
    if template_h > h or template_w > w:
        raise ValueError(f"profile {texture!r} does not fit requested shape {(h, w)}")

    layout_rng = ctx.draw_rng("layout")
    for _ in range(128):
        grid = full_grid(h, w, 0)
        top = layout_rng.randrange(h - template_h + 1)
        left = layout_rng.randrange(w - template_w + 1)
        for label, cells in template.items():
            for r, c in cells:
                grid[top + r][left + c] = colors[label]

        candidates = _placements(grid, ((0, 0), (0, 1), (1, 0), (1, 1)))
        if not candidates:
            continue
        dr, dc = layout_rng.choice(candidates)
        for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
            grid[dr + r][dc + c] = colors["X"]
        # This assertion is intentionally local and cheap.  The public
        # self_check and task tests use a separate complete validation path.
        if not self_check(grid):
            return grid
    raise RuntimeError(
        f"could not place profile={texture} with distractor in shape={(h, w)} "
        f"for seed={seed}, sample_index={sample_index}"
    )


def _assign_colors(labels, rng, include_input_eight):
    """Give every object a unique color while preserving semantic decoys.

    Color 2 always marks a wrong candidate.  Output color 8 is normally absent
    and, on a small explicit minority, appears only on disconnected distractor X;
    this covers the canonical test palette without erasing the output-marker cue.
    """
    if "T" not in labels or "X" not in labels or len(labels) > 9:
        raise ValueError("palette assignment requires T/X and at most nine objects")
    target_color = rng.choice((1, 3, 4, 5, 6, 7, 9))
    non_targets = [label for label in labels if label != "T"]
    result = {"T": target_color}
    if include_input_eight:
        result["X"] = 8
    color_two_candidates = [label for label in non_targets if label not in result]
    color_two_label = rng.choice(color_two_candidates)
    result[color_two_label] = 2
    remaining_labels = [label for label in non_targets if label not in result]
    remaining_colors = [c for c in (1, 3, 4, 5, 6, 7, 9) if c != target_color]
    rng.shuffle(remaining_colors)
    result.update(zip(remaining_labels, remaining_colors))
    return result


def _transform_template(template, transform):
    """Apply one of eight dihedral transforms and normalize to the origin."""
    points = {label: list(cells) for label, cells in template.items()}
    height = 1 + max(r for cells in points.values() for r, _ in cells)
    width = 1 + max(c for cells in points.values() for _, c in cells)
    if transform >= 4:
        points = {label: [(r, width - 1 - c) for r, c in cells]
                  for label, cells in points.items()}
    for _ in range(transform % 4):
        points = {label: [(c, height - 1 - r) for r, c in cells]
                  for label, cells in points.items()}
        height, width = width, height
    min_r = min(r for cells in points.values() for r, _ in cells)
    min_c = min(c for cells in points.values() for _, c in cells)
    return {
        label: tuple(sorted((r - min_r, c - min_c) for r, c in cells))
        for label, cells in points.items()
    }


def _placements(grid, shape):
    """All placements whose cells and cardinal halo are currently empty."""
    h, w = len(grid), len(grid[0])
    sh = 1 + max(r for r, _ in shape)
    sw = 1 + max(c for _, c in shape)
    result = []
    for top in range(h - sh + 1):
        for left in range(w - sw + 1):
            cells = {(top + r, left + c) for r, c in shape}
            if any(grid[r][c] != 0 for r, c in cells):
                continue
            halo = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _MOVES
                if 0 <= r + dr < h and 0 <= c + dc < w
            }
            if any(grid[r][c] != 0 for r, c in halo - cells):
                continue
            result.append((top, left))
    return result


def _draw_degenerate(name, h, w):
    grid = full_grid(h, w, 0)
    if name == "empty":
        return grid
    if name == "no_articulation":
        for r in (1, 2):
            for c in (1, 2):
                grid[r][c] = 1
        for r in (h - 3, h - 2):
            for c in (w - 3, w - 2):
                grid[r][c] = 3
        return grid
    if name == "multiple_articulations":
        row, col = h // 2, max(1, w // 2 - 2)
        for offset, color in enumerate((1, 2, 3, 4, 5)):
            grid[row][col + offset] = color
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")


def _grid_error(grid):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not all(isinstance(row, (list, tuple)) for row in grid)
            or not grid[0] or any(len(row) != len(grid[0]) for row in grid)):
        return "expected a nonempty rectangular grid"
    if not (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30):
        return "grid dimensions must be 1..30"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be Python integer ARC colors 0..9"
    return None


def _foreground_components(grid):
    """Return monochromatic four-connected nonzero components in scan order."""
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _MOVES:
                point = (r + dr, c + dc)
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append({"color": color, "cells": frozenset(cells)})
    return components


def _contact_graph(grid):
    components = _foreground_components(grid)
    owner = {cell: i for i, obj in enumerate(components) for cell in obj["cells"]}
    edges = [set() for _ in components]
    for (r, c), i in owner.items():
        for dr, dc in _MOVES:
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                edges[i].add(j)
                edges[j].add(i)
    return components, edges


def _graph_components(edges, skip=None):
    remaining = set(range(len(edges)))
    if skip is not None:
        remaining.discard(skip)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        comp, stack = {start}, [start]
        while stack:
            i = stack.pop()
            for j in sorted(edges[i]):
                if j in remaining:
                    remaining.remove(j)
                    comp.add(j)
                    stack.append(j)
        components.append(comp)
    return components


def _articulation_indices(grid):
    _, edges = _contact_graph(grid)
    base = len(_graph_components(edges))
    return [i for i in range(len(edges)) if len(_graph_components(edges, i)) > base]


def _paint_foreground_components(grid, indices):
    components, _ = _contact_graph(grid)
    output = full_grid(len(grid), len(grid[0]), 0)
    for i in sorted(set(indices)):
        for r, c in components[i]["cells"]:
            output[r][c] = 8
    return output


def _rule_mirror(grid):
    """Diagnostic Python mirror only; the Racket program remains label authority."""
    return _paint_foreground_components(grid, _articulation_indices(grid))


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the ordinary curriculum and all canonical inputs."""
    del difficulty, meta
    malformed = _grid_error(grid)
    if malformed:
        return [malformed]
    components, edges = _contact_graph(grid)
    errors = []
    if len(components) < 4:
        errors.append(f"expected at least four foreground objects, got {len(components)}")
    articulations = _articulation_indices(grid)
    if len(articulations) != 1:
        errors.append(f"expected exactly one articulation object, got {len(articulations)}")
    elif len(components[articulations[0]]["cells"]) < 2:
        errors.append("articulation object must contain at least two cells")
    clusters = _graph_components(edges)
    if len(clusters) < 2:
        errors.append("expected at least one disconnected distractor object")
    if max((len(cluster) for cluster in clusters), default=0) < 3:
        errors.append("touching structure must contain at least three objects")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _input_color_two_rival(grid):
    components, _ = _contact_graph(grid)
    return _paint_foreground_components(grid, [i for i, obj in enumerate(components) if obj["color"] == 2])


def _max_degree_rival(grid):
    _, edges = _contact_graph(grid)
    if not edges:
        return full_grid(len(grid), len(grid[0]), 0)
    maximum = max(map(len, edges))
    return _paint_foreground_components(grid, [i for i, neighbors in enumerate(edges) if len(neighbors) == maximum])


def _largest_in_main_cluster_rival(grid):
    components, edges = _contact_graph(grid)
    if not components:
        return full_grid(len(grid), len(grid[0]), 0)
    clusters = _graph_components(edges)
    maximum_vertices = max(map(len, clusters))
    main = set().union(*(cluster for cluster in clusters if len(cluster) == maximum_vertices))
    maximum_area = max(len(components[i]["cells"]) for i in main)
    return _paint_foreground_components(
        grid,
        [i for i in main if len(components[i]["cells"]) == maximum_area],
    )


def _color_witness(grid):
    return _input_color_two_rival(grid) != _rule_mirror(grid)


def _degree_witness(grid):
    return _max_degree_rival(grid) != _rule_mirror(grid)


def _area_witness(grid):
    return _largest_in_main_cluster_rival(grid) != _rule_mirror(grid)


SEMANTIC_RIVALS = {
    "input_color_two": _input_color_two_rival,
    "max_degree": _max_degree_rival,
    "largest_in_main_cluster": _largest_in_main_cluster_rival,
}
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "color_decoy": _color_witness,
    "degree_tie": _degree_witness,
    "area_decoy": _area_witness,
}
WITNESS_RIVALS = {
    "color_decoy": ["input_color_two"],
    "degree_tie": ["max_degree"],
    "area_decoy": ["largest_in_main_cluster"],
}
