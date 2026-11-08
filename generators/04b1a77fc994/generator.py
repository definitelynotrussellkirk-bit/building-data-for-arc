"""Task-local generator for ARC task 04b1a77fc994.

Rule: identify each monochromatic 4-connected nonzero object and recolor the
whole object by the number of outer grid borders it touches: 0->1, 1->2,
2->3, and 3 or 4->4.  The generator uses linked scene profiles so object
shape, border role, color equality, and placement cannot drift independently.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "04b1a77fc994"
VERSION = "4.0.0"
RULE_HASH = "20e8206868a6"
SUMMARY = (
    "Four to seven monochromatic objects are recolored solely by the number "
    "of grid borders touched: 0=blue(1), 1=red(2), 2=green(3), 3+=yellow(4)."
)
EXAMPLES_NEEDED = 4
INVARIANTS = [
    "background is 0 and every nonzero cell belongs to a monochromatic 4-connected object",
    "every ordinary four-pair lesson witnesses touch counts 0, 1, 2, and at least one of 3 or 4",
    "input colors are nuisance variables and may be shared by disconnected objects",
    "the selected linked scene profile is exactly recoverable from the returned grid",
]
SCENE_PROFILES = (
    "public_1", "public_2", "public_3", "public_4",
    "full3_same_size", "full4_same_color", "span_vs_corner", "many_objects_high4",
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic eight-profile lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Linked whole-scene morphology, border-role, and color-equality profile.",
    },
}
_COLORS = tuple(range(1, 10))
_PUBLIC = [[[0, 0, 4, 0, 0, 0, 0, 3, 0, 0], [0, 0, 4, 0, 0, 0, 0, 3, 0, 0], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0], [0, 0, 4, 0, 7, 7, 0, 0, 0, 0], [0, 0, 4, 0, 7, 0, 0, 0, 0, 0], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0], [9, 0, 4, 0, 0, 0, 0, 0, 0, 0], [9, 9, 4, 0, 0, 0, 0, 0, 0, 0]], [[5, 5, 0, 0, 0, 0, 2, 0, 0], [5, 0, 0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 2, 0, 6], [0, 0, 0, 0, 0, 0, 2, 0, 6], [0, 0, 0, 0, 8, 8, 2, 0, 6], [0, 0, 0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 2, 0, 0]], [[4, 4, 0, 0, 0, 0, 0, 0, 0, 8], [4, 0, 0, 0, 0, 0, 0, 0, 8, 8], [4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 3, 0, 0, 0, 0], [4, 0, 0, 0, 0, 3, 3, 0, 0, 0], [4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 0, 0, 0, 0, 0], [4, 0, 0, 7, 7, 0, 0, 0, 0, 0]], [[0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 2], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 2], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 4, 0, 0, 6, 0, 0, 0, 0, 0], [0, 0, 4, 0, 0, 6, 6, 0, 0, 0, 0], [0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0], [9, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0], [9, 9, 4, 0, 0, 0, 0, 0, 0, 0, 0]]]


def _blank(h, w):
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(h, w, components):
    grid = _blank(h, w)
    for color, cells in components:
        for r, c in cells:
            if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                raise AssertionError("invalid static profile")
            grid[r][c] = color
    return grid


def _contrast_profiles():
    h, w = 10, 12
    full3_same_size = _paint(h, w, [
        (1, [(1, c) for c in range(w)] + [(0, 0)]),
        (2, [(4, 5), (4, 6), (5, 5)]),
        (3, [(h - 1, 6), (h - 1, 7), (h - 2, 6)]),
        (4, [(h - 2, 0), (h - 1, 0), (h - 1, 1)]),
    ])

    h, w = 12, 14
    snake = ([(0, c) for c in range(5)]
             + [(r, 4) for r in range(1, h)]
             + [(h - 1, c) for c in range(5, w)])
    full4_same_color = _paint(h, w, [
        (1, snake),
        (2, [(5, 8), (5, 9), (6, 8)]),
        (2, [(2, w - 1), (3, w - 1), (3, w - 2)]),
        (2, [(h - 2, 0), (h - 1, 0), (h - 1, 1)]),
    ])

    h, w = 11, 13
    span_vs_corner = _paint(h, w, [
        (1, [(1, c) for c in range(w)] + [(0, w - 1)]),
        (2, [(h - 2, c) for c in range(w)]),
        (3, [(4, 5), (4, 6), (5, 5)]),
        (4, [(h - 1, 5), (h - 1, 6)]),
    ])

    h, w = 14, 16
    snake = ([(0, c) for c in range(6)]
             + [(r, 5) for r in range(1, h)]
             + [(h - 1, c) for c in range(6, w)])
    many_objects_high4 = _paint(h, w, [
        (1, snake),
        (2, [(5, 9), (5, 10), (6, 9)]),
        (3, [(8, 11), (8, 12), (9, 12)]),
        (4, [(4, 0), (5, 0), (5, 1)]),
        (5, [(4, w - 1), (5, w - 1), (5, w - 2)]),
        (6, [(h - 2, 0), (h - 1, 0), (h - 1, 1)]),
        (7, [(0, w - 1), (1, w - 1), (1, w - 2)]),
    ])
    return {
        "full3_same_size": full3_same_size,
        "full4_same_color": full4_same_color,
        "span_vs_corner": span_vs_corner,
        "many_objects_high4": many_objects_high4,
    }


_BASE_GRIDS = {f"public_{i + 1}": [row[:] for row in grid]
               for i, grid in enumerate(_PUBLIC)}
_BASE_GRIDS.update(_contrast_profiles())


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _d4(grid):
    variants = []
    current = [row[:] for row in grid]
    for _ in range(4):
        variants.append([row[:] for row in current])
        variants.append(_flip_lr(current))
        current = _rot90(current)
    unique = []
    seen = set()
    for candidate in variants:
        key = tuple(tuple(row) for row in candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _normalize_colors(grid):
    mapping = {}
    next_color = 1
    rows = []
    for row in grid:
        out = []
        for value in row:
            if value == 0:
                out.append(0)
            else:
                if value not in mapping:
                    mapping[value] = next_color
                    next_color += 1
                out.append(mapping[value])
        rows.append(tuple(out))
    return tuple(rows)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            touches = sum((
                any(rr == 0 for rr, _ in cells),
                any(rr == h - 1 for rr, _ in cells),
                any(cc == 0 for _, cc in cells),
                any(cc == w - 1 for _, cc in cells),
            ))
            result.append({"color": color, "cells": tuple(sorted(cells)),
                           "touch_count": touches})
    return result


def profile_signature(grid):
    """Exact whole-scene signature modulo D4 and nuisance color renaming."""
    candidates = []
    for variant in _d4(grid):
        normalized = _normalize_colors(variant)
        candidates.append((len(normalized), len(normalized[0]), normalized))
    return min(candidates)


def _scene_fingerprint(grid):
    """Profile invariants that component translations must preserve exactly."""
    grouped = {}
    for component in _components(grid):
        grouped.setdefault(component["color"], []).append(
            (len(component["cells"]), component["touch_count"])
        )
    color_groups = tuple(sorted(tuple(sorted(items)) for items in grouped.values()))
    return (len(grid), len(grid[0]), color_groups)


def _translated_scenes(grid):
    """Yield one-component translations without changing any semantic role."""
    h, w = len(grid), len(grid[0])
    baseline = _scene_fingerprint(grid)
    components = _components(grid)
    occupied = {(r, c) for row in components for r, c in row["cells"]}
    offsets = ((-2, 0), (-1, 0), (1, 0), (2, 0),
               (0, -2), (0, -1), (0, 1), (0, 2))
    for component in components:
        source = set(component["cells"])
        occupied_other = occupied - source
        for dr, dc in offsets:
            target = {(r + dr, c + dc) for r, c in source}
            if any(not (0 <= r < h and 0 <= c < w) for r, c in target):
                continue
            if target & occupied_other:
                continue
            candidate = [row[:] for row in grid]
            for r, c in source:
                candidate[r][c] = 0
            for r, c in target:
                candidate[r][c] = component["color"]
            if _scene_fingerprint(candidate) == baseline:
                yield candidate


def _build_profile_variants(limit=30):
    by_profile = {}
    claimed = {}
    for profile, base in _BASE_GRIDS.items():
        variants = []
        queue = [[row[:] for row in base]]
        local_seen = set()
        while queue and len(variants) < limit:
            candidate = queue.pop(0)
            signature = profile_signature(candidate)
            if signature in local_seen:
                continue
            owner = claimed.get(signature)
            if owner is not None and owner != profile:
                continue
            local_seen.add(signature)
            claimed[signature] = profile
            variants.append(candidate)
            queue.extend(_translated_scenes(candidate))
        if len(variants) < 9:
            raise AssertionError(f"insufficient layout variants for {profile}: {len(variants)}")
        by_profile[profile] = tuple(variants)
    return by_profile, claimed


_PROFILE_VARIANTS, _PROFILE_BY_SIGNATURE = _build_profile_variants()


def observe_overrides(grid):
    profile = _PROFILE_BY_SIGNATURE.get(profile_signature(grid))
    return {"scene_profile": profile} if profile is not None else {}


def profile_facts(grid):
    components = _components(grid)
    counts = [obj["touch_count"] for obj in components]
    return {
        "scene_profile": observe_overrides(grid).get("scene_profile"),
        "dimensions": f"{len(grid)}x{len(grid[0])}",
        "object_count": len(components),
        "touch_histogram": {str(k): counts.count(k) for k in range(5)},
        "touch_counts": tuple(sorted(counts)),
        "same_color_object_groups": sorted(
            sum(1 for obj in components if obj["color"] == color)
            for color in sorted({obj["color"] for obj in components})
        ),
    }


def rule_mirror(grid):
    out = _blank(len(grid), len(grid[0]))
    for obj in _components(grid):
        color = (1 if obj["touch_count"] == 0 else
                 2 if obj["touch_count"] == 1 else
                 3 if obj["touch_count"] == 2 else 4)
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-list grid"]
    width = len(grid[0])
    errors = []
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be literal ARC color integers 0..9")
    profile = observe_overrides(grid).get("scene_profile")
    if profile is None:
        errors.append("whole-scene morphology is not one declared linked profile")
    components = _components(grid)
    counts = {component["touch_count"] for component in components}
    if 0 not in counts:
        errors.append("at least one interior object is required to witness output color 1")
    if 2 not in counts:
        errors.append("at least one two-border object is required")
    if len(components) < 4:
        errors.append("at least four objects are required")
    if rule_mirror(grid) == grid:
        errors.append("ordinary input must not be an identity example")
    return errors


def _recolor_nuisance(grid, rng):
    labels = []
    for row in grid:
        for value in row:
            if value and value not in labels:
                labels.append(value)
    colors = rng.sample(_COLORS, len(labels))
    mapping = dict(zip(labels, colors))
    out = [[mapping.get(value, 0) for value in row] for row in grid]
    if rule_mirror(out) == out:
        colors = colors[1:] + colors[:1]
        mapping = dict(zip(labels, colors))
        out = [[mapping.get(value, 0) for value in row] for row in grid]
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"undeclared override(s): {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if "scene_profile" in overrides:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    band_index = {None: 1, "easy": 0, "medium": 1, "hard": 2}.get(difficulty)
    if band_index is None:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    rng = ctx.draw_rng("nuisance")
    layouts = _PROFILE_VARIANTS[profile][band_index::3]
    layout = layouts[rng.randrange(len(layouts))]
    orientations = _d4(layout)
    grid = orientations[rng.randrange(len(orientations))]
    return _recolor_nuisance(grid, rng)
