"""Generator for arc_puzzle_bank_ninth21:H57 — infer A→B, apply to C.

The input is one row of three equally sized square panels separated by full
maroon (9) columns.  Panel B is exactly one non-identity transform of panel A;
the same transform must be applied to panel C.

The teaching distribution deliberately mirrors the canonical demonstrations:
A/B and C use disjoint multi-object palettes, each panel has two or three
separated colored objects, and the A→B transform is answer-unique.  This rules
out the previous one-color shortcut and ambiguous symmetric motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a31a33585cc"
TASK_ID = "7a31a33585cc"
VERSION = "3.1.0"  # source-synchronized true rot270 branch
RULE_HASH = "dc0383bfad5f"

SUMMARY = (
    "Three equal square panels separated by full-height color-9 columns. "
    "Panel B is one uniquely identifiable non-identity geometric transform "
    "of panel A; apply that transform to the independently arranged panel C."
)

INVARIANTS = [
    "background is 0 and the only color-9 cells are two one-column full-height separators",
    "the input contains exactly three equal square panels",
    "A, B, and C each contain the same count of two or three separated single-color objects",
    "A/B colors match while C uses a disjoint palette",
    "exactly one supported non-identity transform maps A to B",
    "the inferred transform changes C and its output is not a copied input panel",
]

TRANSFORMS = ("rot90", "rot180", "rot270", "flip_h", "flip_v", "transpose", "anti")
COMPONENT_PROFILES = ("canonical_mixed", "polyomino")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 5..7",
        "valid": "5..7",
    },
    "objects_per_panel": {
        "type": "int",
        "default": "band rng 2..3",
        "valid": "2..3",
    },
    "transform": {
        "type": "str",
        "default": "uniform supported non-identity transform",
        "valid": "|".join(TRANSFORMS),
    },
    "component_profile": {
        "type": "str",
        "default": "rng canonical_mixed|polyomino",
        "valid": "|".join(COMPONENT_PROFILES),
    },
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _transform(grid, kind):
    """Apply one non-identity D4 transform supported by the synced rule."""
    g = _copy_grid(grid)
    if kind == "rot90":
        return [list(row) for row in zip(*g[::-1])]
    if kind == "rot180":
        return [row[::-1] for row in g[::-1]]
    if kind == "rot270":
        return [list(row) for row in zip(*g)][::-1]
    if kind == "flip_h":
        return [row[::-1] for row in g]
    if kind == "flip_v":
        return [row[:] for row in g[::-1]]
    if kind == "transpose":
        return [list(row) for row in zip(*g)]
    if kind == "anti":
        h, w = len(g), len(g[0])
        return [
            [g[h - 1 - c][w - 1 - r] for c in range(h)]
            for r in range(w)
        ]
    raise ValueError(f"unknown transform {kind!r}")


def _matching_transforms(a, b):
    return [kind for kind in TRANSFORMS if _transform(a, kind) == b]


def _normalize_cells(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _random_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((r + dr, c + dc))
    return _normalize_cells(cells)


def _component_sizes(profile, count, rng):
    if profile == "canonical_mixed":
        # The canonical panels pair one salient multi-cell object with a tiny
        # distractor.  Three-object variants add a second small object.
        sizes = [rng.randint(3, 5), 1]
        if count == 3:
            sizes.insert(1, 2)
        return sizes
    if profile == "polyomino":
        return [rng.randint(2, 4) for _ in range(count)]
    raise ValueError(f"unknown component_profile {profile!r}")


def _can_place(cells, occupied, h):
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < h) or (r, c) in occupied:
            return False
        # Keep different-colored objects 4-disconnected, matching the
        # canonical object layout and making object count visually recoverable.
        if any(
            (r + dr, c + dc) in occupied
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        ):
            return False
    return True


def _build_panel(rng, h, colors, profile):
    sizes = _component_sizes(profile, len(colors), rng)
    for _restart in range(160):
        panel = full_grid(h, h, 0)
        occupied = set()
        placed_all = True
        for color, size in zip(colors, sizes):
            placed = False
            for _attempt in range(240):
                shape = _random_polyomino(rng, size)
                sh = max(r for r, _ in shape) + 1
                sw = max(c for _, c in shape) + 1
                if sh > h or sw > h:
                    continue
                top = rng.randint(0, h - sh)
                left = rng.randint(0, h - sw)
                cells = {(top + r, left + c) for r, c in shape}
                if not _can_place(cells, occupied, h):
                    continue
                for r, c in cells:
                    panel[r][c] = color
                occupied.update(cells)
                placed = True
                break
            if not placed:
                placed_all = False
                break
        if placed_all:
            return panel
    return None


def _compose_panels(panels):
    h = len(panels[0])
    out = full_grid(h, 3 * h + 2, 0)
    for index, panel in enumerate(panels):
        left = index * (h + 1)
        if index:
            for r in range(h):
                out[r][left - 1] = 9
        for r in range(h):
            out[r][left:left + h] = list(panel[r])
    return out


def _split_panels(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular matrix"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["grid rows must be lists or tuples"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return None, ["grid must be rectangular and nonempty"]
    h = len(grid)
    w = next(iter(widths))
    errors = []
    if not (5 <= h <= 7):
        errors.append(f"height {h} outside declared 5..7 range")
    if w != 3 * h + 2:
        errors.append(f"width {w} must equal 3*height+2 ({3 * h + 2})")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return None, errors
    if errors:
        return None, errors

    expected = [h, 2 * h + 1]
    full_nines = [
        c for c in range(w)
        if all(grid[r][c] == 9 for r in range(h))
    ]
    if full_nines != expected:
        errors.append(
            f"full-height color-9 separators are {full_nines}, expected {expected}"
        )
    if any(
        grid[r][c] == 9
        for r in range(h)
        for c in range(w)
        if c not in expected
    ):
        errors.append("color 9 may appear only in the two separator columns")
    if errors:
        return None, errors
    panels = []
    for left in (0, h + 1, 2 * h + 2):
        panels.append([list(row[left:left + h]) for row in grid])
    return panels, []


def _color_objects(panel):
    h, w = len(panel), len(panel[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = panel[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and panel[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": cells, "size": len(cells)})
    return components


def _analysis(grid):
    panels, errors = _split_panels(grid)
    if errors:
        return {"errors": errors, "facts": None}
    a, b, c = panels
    panel_objects_by_panel = [_color_objects(panel) for panel in panels]
    color_sets = [
        {value for row in panel for value in row if value != 0}
        for panel in panels
    ]

    if any(not panel_objects for panel_objects in panel_objects_by_panel):
        errors.append("all three panels must be nonempty")
    counts = [len(panel_objects) for panel_objects in panel_objects_by_panel]
    if not (counts[0] == counts[1] == counts[2] and counts[0] in (2, 3)):
        errors.append(
            f"panel object counts must be equal and in {{2,3}}, got {counts}"
        )
    for label, panel_objects, colors in zip("ABC", panel_objects_by_panel, color_sets):
        if len(colors) != len(panel_objects):
            errors.append(
                f"panel {label} must contain exactly one connected object per color"
            )
        occupied = sum(obj["size"] for obj in panel_objects)
        if occupied >= len(a) * len(a) / 2:
            errors.append(f"panel {label} is too dense ({occupied} occupied cells)")
    if color_sets[0] != color_sets[1]:
        errors.append("panels A and B must use exactly the same colors")
    if color_sets[0] & color_sets[2]:
        errors.append("panel C colors must be disjoint from the A/B palette")
    if a == b:
        errors.append("A and B must not be identical (identity lessons are forbidden)")

    candidates = _matching_transforms(a, b)
    if len(candidates) != 1:
        errors.append(
            f"A→B must identify exactly one supported transform, got {candidates}"
        )
        transform = None
        output = None
    else:
        transform = candidates[0]
        output = _transform(c, transform)
        if output == c:
            errors.append("the inferred transform must visibly change panel C")
        if output in (a, b):
            errors.append("the answer must not be a copied A or B panel")

    facts = {
        "height": len(grid),
        "panels": panels,
        "panel_objects": panel_objects_by_panel,
        "object_counts": counts,
        "colors": color_sets,
        "transform": transform,
        "output": output,
        "component_sizes": [
            tuple(sorted((obj["size"] for obj in panel_objects), reverse=True))
            for panel_objects in panel_objects_by_panel
        ],
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-prone, or rule-hiding scenes."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    component_sizes = facts["component_sizes"]
    profile = (
        "canonical_mixed"
        if all(1 in sizes for sizes in component_sizes)
        else "polyomino"
    )
    return {
        "grid_h": facts["height"],
        "objects_per_panel": facts["object_counts"][0],
        "transform": facts["transform"],
        "component_profile": profile,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        h_bounds = (5, 5)
        object_bounds = (2, 2)
        default_profiles = ("canonical_mixed",)
    elif difficulty == "hard":
        h_bounds = (6, 7)
        object_bounds = (2, 3)
        default_profiles = COMPONENT_PROFILES
    else:
        h_bounds = (5, 6)
        object_bounds = (2, 3)
        default_profiles = COMPONENT_PROFILES

    h = ctx.draw_int(
        "grid_h", *( (5, 7) if overrides.get("grid_h") is not None else h_bounds)
    )
    object_count = ctx.draw_int(
        "objects_per_panel",
        *( (2, 3) if overrides.get("objects_per_panel") is not None else object_bounds),
    )
    transform = ctx.draw_choice("transform", TRANSFORMS)
    profile_options = (
        COMPONENT_PROFILES
        if overrides.get("component_profile") is not None
        else default_profiles
    )
    profile = ctx.draw_choice("component_profile", profile_options)

    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(list(range(1, 9)), 2 * object_count)
    a_colors = tuple(colors[:object_count])
    c_colors = tuple(colors[object_count:])
    a_rng = ctx.draw_rng("panel_a")
    c_rng = ctx.draw_rng("panel_c")

    for _attempt in range(240):
        a = _build_panel(a_rng, h, a_colors, profile)
        if a is None:
            continue
        b = _transform(a, transform)
        if _matching_transforms(a, b) != [transform]:
            continue
        c = _build_panel(c_rng, h, c_colors, profile)
        if c is None:
            continue
        output = _transform(c, transform)
        if output == c or output in (a, b):
            continue
        grid = _compose_panels((a, b, c))
        errors = self_check(grid)
        if not errors:
            return grid

    raise ValueError(
        "could not construct a unique, non-degenerate panel-transform lesson "
        f"for h={h}, objects={object_count}, transform={transform}, "
        f"component_profile={profile}"
    )
