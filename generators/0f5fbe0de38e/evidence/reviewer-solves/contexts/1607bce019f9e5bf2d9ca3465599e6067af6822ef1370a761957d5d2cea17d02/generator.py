"""Faithful generator for ARC task 0f5fbe0de38e (source slug 6aa20dc0).

A 3x3 multicolor template contains a majority fill color and two distinct
single-cell marker ports at opposite corners.  Outside the template, solid
same-size square objects in the two marker colors occur in greedy-nearest
pairs.  Each pair occupies the two corresponding corners of a scaled 3x3
footprint, either on the template's diagonal or the opposite diagonal.  The
Racket oracle chooses the first compatible D4 placement and paints every
scaled fill cell while leaving the marker blocks and template unchanged.

The canonical corpus exercises one to three pairs, square scales 1..3,
non-zero modal backgrounds, four different sparse template masks, and both
diagonal relations.  This generator deliberately schedules those branches
across consecutive sample_index values so a downstream lesson cannot hide the
scale or transform rule behind singleton-only demonstrations.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0f5fbe0de38e"
TASK_ID = GENERATOR_ID
RULE_HASH = "41d149922ac6"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "4.0.0"  # canonical 3x3 templates + scaled greedy pairs + honest overrides
EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 19..22 grid has one sparse 3x3 multicolor template: a majority fill "
    "color plus two distinct marker-port cells at opposite corners. One to "
    "three greedy-nearest pairs of solid marker-colored squares (scales 1..3) "
    "occupy corresponding corners of scaled 3x3 footprints. The Racket rule "
    "chooses the compatible D4 placement and paints the scaled template fill "
    "cells. Consecutive sample_index values cover unit, scale-2, scale-3, "
    "multi-pair, mixed-scale, same-diagonal, and opposite-diagonal lessons."
)

INVARIANTS = [
    "exactly one 8-connected 3x3 template containing three non-background colors",
    "the template mode is the fill color; the two other colors occur once at opposite corners",
    "all external marker objects are solid 1x1, 2x2, or 3x3 squares",
    "greedy nearest-different-color pairing recovers every intended pair exactly once",
    "each pair defines an in-bounds scaled template whose fill targets are background",
]

# Symbols: F=fill, A/B=the two marker roles, .=background hole.
TEMPLATE_PROFILES: dict[str, tuple[str, str, str]] = {
    "ring6_anti": ("FFB", "F.F", "AFF"),
    "wedge5_main": ("AFF", "FF.", "F.B"),
    "plus5_main": ("AF.", "FFF", ".FB"),
    "cross4_anti": (".FB", "F.F", "AF."),
}
TEMPLATE_PROFILE_NAMES = tuple(TEMPLATE_PROFILES)

LESSON_SCALES: dict[str, tuple[int, ...]] = {
    "unit_single": (1,),
    "scaled2_single": (2,),
    "scaled3_single": (3,),
    "unit_double": (1, 1),
    "mixed_1_2": (1, 2),
    "mixed_1_2_3": (1, 2, 3),
}
LESSON_PROFILE_NAMES = tuple(LESSON_SCALES)
DEFAULT_ORIENTATION_BY_LESSON = {
    "unit_single": "same",
    "scaled2_single": "opposite",
    "scaled3_single": "same",
    "unit_double": "opposite",
    "mixed_1_2": "mixed",
    "mixed_1_2_3": "mixed",
}
ORIENTATION_PROFILES = ("same", "opposite", "mixed")

DEGENERATE_TEXTURES = (
    "no_template",
    "no_markers",
    "broken_marker",
    "ambiguous_pairing",
)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded rng", "valid": "19..22"},
    "grid_w": {"type": "int", "default": "difficulty-banded rng", "valid": "19..22"},
    "bg_color": {"type": "int", "default": "rng", "valid": "0..9"},
    "fill_color": {"type": "int", "default": "rng distinct", "valid": "0..9"},
    "marker_a_color": {"type": "int", "default": "rng distinct", "valid": "0..9"},
    "marker_b_color": {"type": "int", "default": "rng distinct", "valid": "0..9"},
    "template_profile": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "ring6_anti|wedge5_main|plus5_main|cross4_anti",
    },
    "lesson_profile": {
        "type": "str",
        "default": "six-step sample_index schedule",
        "valid": "unit_single|scaled2_single|scaled3_single|unit_double|mixed_1_2|mixed_1_2_3",
    },
    "orientation_profile": {
        "type": "str",
        "default": "lesson-linked schedule",
        "valid": "same|opposite|mixed",
    },
}

_COLOR_AXES = ("bg_color", "fill_color", "marker_a_color", "marker_b_color")
_D4 = tuple(range(8))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = _DIR4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _mode_color(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    return counts.most_common(1)[0][0]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components_non_bg_8(grid: list[list[int]], bg: int) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.pop(0)
                cells.append((cr, cc))
                for dr, dc in _DIR8:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r1, c1, r2, c2 = _bbox(cells)
            result.append(
                {
                    "cells": tuple(cells),
                    "cell_set": frozenset(cells),
                    "bbox": (r1, c1, r2, c2),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                    "size": len(cells),
                    "colors": tuple(sorted({grid[x][y] for x, y in cells})),
                }
            )
    return result


def _components_same_color_4(grid: list[list[int]], bg: int) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.pop(0)
                cells.append((cr, cc))
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r1, c1, r2, c2 = _bbox(cells)
            result.append(
                {
                    "cells": tuple(cells),
                    "cell_set": frozenset(cells),
                    "bbox": (r1, c1, r2, c2),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                    "size": len(cells),
                    "color": color,
                }
            )
    return result


def _template_spec(profile: str) -> dict[str, Any]:
    rows = TEMPLATE_PROFILES[profile]
    fill = []
    markers: dict[str, tuple[int, int]] = {}
    holes = []
    for r, row in enumerate(rows):
        for c, symbol in enumerate(row):
            if symbol == "F":
                fill.append((r, c))
            elif symbol in ("A", "B"):
                markers[symbol] = (r, c)
            else:
                holes.append((r, c))
    marker_diag = "main" if markers["A"][1] == markers["A"][0] else "anti"
    return {
        "profile": profile,
        "rows": rows,
        "fill": tuple(fill),
        "marker_a": markers["A"],
        "marker_b": markers["B"],
        "marker_diag": marker_diag,
        "holes": tuple(holes),
    }


def _xform(pos: tuple[int, int], transform: int, h: int = 3, w: int = 3) -> tuple[int, int]:
    r, c = pos
    if transform == 0:
        return r, c
    if transform == 1:
        return c, h - 1 - r
    if transform == 2:
        return h - 1 - r, w - 1 - c
    if transform == 3:
        return w - 1 - c, r
    if transform == 4:
        return r, w - 1 - c
    if transform == 5:
        return h - 1 - r, c
    if transform == 6:
        return c, r
    return w - 1 - c, h - 1 - r


def _gap_dist(a: dict[str, Any], b: dict[str, Any]) -> int:
    row_gap = max(0, max(a["r1"], b["r1"]) - min(a["r2"], b["r2"]) - 1)
    col_gap = max(0, max(a["c1"], b["c1"]) - min(a["c2"], b["c2"]) - 1)
    return row_gap + col_gap


def _greedy_pairs(items: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    ordered = sorted(items, key=lambda obj: 1000 * obj["r1"] + obj["c1"])
    candidates: list[tuple[int, int, int]] = []
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            if ordered[i]["color"] != ordered[j]["color"]:
                candidates.append((_gap_dist(ordered[i], ordered[j]), i, j))
    candidates.sort(key=lambda row: row[0])  # stable: matches Racket sort-by first
    used: set[int] = set()
    pairs = []
    for _gap, i, j in candidates:
        if i in used or j in used:
            continue
        used.update((i, j))
        pairs.append((ordered[i], ordered[j]))
    return pairs


def _first_placement(
    marker_positions: tuple[tuple[int, int], tuple[int, int]],
    a: dict[str, Any],
    b: dict[str, Any],
) -> dict[str, int] | None:
    if a["h"] != b["h"] or a["w"] != b["w"]:
        return None
    sh, sw = a["h"], a["w"]
    for transform in _D4:
        transformed = tuple(_xform(pos, transform) for pos in marker_positions)
        for first, second in ((a, b), (b, a)):
            sr1 = first["r1"] - transformed[0][0] * sh
            sc1 = first["c1"] - transformed[0][1] * sw
            sr2 = second["r1"] - transformed[1][0] * sh
            sc2 = second["c1"] - transformed[1][1] * sw
            if (sr1, sc1) == (sr2, sc2):
                return {"sr": sr1, "sc": sc1, "transform": transform, "sh": sh, "sw": sw}
    return None


def _profile_from_template(
    grid: list[list[int]], template: dict[str, Any], fill_color: int
) -> tuple[str | None, int | None, int | None]:
    r1, c1, _, _ = template["bbox"]
    fill_positions = {
        (r - r1, c - c1)
        for r, c in template["cells"]
        if grid[r][c] == fill_color
    }
    non_fill = [
        (r - r1, c - c1, grid[r][c])
        for r, c in template["cells"]
        if grid[r][c] != fill_color
    ]
    if len(non_fill) != 2 or non_fill[0][2] == non_fill[1][2]:
        return None, None, None
    for name in TEMPLATE_PROFILE_NAMES:
        spec = _template_spec(name)
        if fill_positions != set(spec["fill"]):
            continue
        color_at = {(r, c): color for r, c, color in non_fill}
        if set(color_at) != {spec["marker_a"], spec["marker_b"]}:
            continue
        return name, color_at[spec["marker_a"]], color_at[spec["marker_b"]]
    return None, None, None


def _lesson_profile(scales: Iterable[int]) -> str | None:
    signature = tuple(sorted(int(scale) for scale in scales))
    for name, values in LESSON_SCALES.items():
        if tuple(sorted(values)) == signature:
            return name
    return None


def _pair_relation(template_diag: str, a: dict[str, Any], b: dict[str, Any]) -> str | None:
    dr, dc = b["r1"] - a["r1"], b["c1"] - a["c1"]
    scale = a["h"]
    if abs(dr) != 2 * scale or abs(dc) != 2 * scale:
        return None
    pair_diag = "main" if dr * dc > 0 else "anti"
    return "same" if pair_diag == template_diag else "opposite"


def _analyze_uncached(grid: list[list[int]]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return None, ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["grid values must be integer ARC colors 0..9"]

    h, w = len(grid), width
    bg = _mode_color(grid)
    multicolor = _components_non_bg_8(grid, bg)
    candidates = [obj for obj in multicolor if len(obj["colors"]) >= 3]
    if not candidates:
        return None, ["no multicolor template component with at least three colors"]
    candidates.sort(key=lambda obj: 1000 * obj["size"] + 30 * obj["r1"] + obj["c1"])
    template = candidates[0]
    if len(candidates) != 1:
        errors.append(f"expected exactly one multicolor template, found {len(candidates)}")
    if (template["h"], template["w"]) != (3, 3):
        errors.append(f"template bbox must be 3x3, got {template['h']}x{template['w']}")
    template_counts = Counter(grid[r][c] for r, c in template["cells"])
    fill_color, fill_count = template_counts.most_common(1)[0]
    if list(template_counts.values()).count(fill_count) != 1:
        errors.append("template fill color must be a unique mode")
    if len(template_counts) != 3:
        errors.append(f"template must contain exactly three colors, got {sorted(template_counts)}")
    marker_counts = {color: count for color, count in template_counts.items() if color != fill_color}
    if sorted(marker_counts.values()) != [1, 1]:
        errors.append(f"template marker colors must each occur once, got {marker_counts}")

    profile, marker_a, marker_b = _profile_from_template(grid, template, fill_color)
    if profile is None:
        errors.append("template mask is not one of the four canonical 3x3 profiles")
        return None, errors
    spec = _template_spec(profile)
    marker_colors = {marker_a, marker_b}
    template_cells = template["cell_set"]

    same_color = _components_same_color_4(grid, bg)
    marker_objects = [
        obj
        for obj in same_color
        if obj["color"] in marker_colors and template_cells.isdisjoint(obj["cell_set"])
    ]
    unrelated = [
        obj
        for obj in same_color
        if template_cells.isdisjoint(obj["cell_set"]) and obj["color"] not in marker_colors
    ]
    if unrelated:
        errors.append(f"unexpected non-template objects in colors {[obj['color'] for obj in unrelated]}")
    if not marker_objects:
        errors.append("no external marker objects")
        return None, errors
    for obj in marker_objects:
        if obj["h"] != obj["w"] or obj["h"] not in (1, 2, 3):
            errors.append(
                f"marker object at {(obj['r1'], obj['c1'])} must be a 1..3 solid square, "
                f"got {obj['h']}x{obj['w']}"
            )
        if obj["size"] != obj["h"] * obj["w"]:
            errors.append(f"marker object at {(obj['r1'], obj['c1'])} is not solid")

    pairs = _greedy_pairs(marker_objects)
    if len(pairs) * 2 != len(marker_objects):
        errors.append(
            f"greedy pairing leaves {len(marker_objects) - 2 * len(pairs)} marker object(s) unused"
        )
    pair_facts: list[dict[str, Any]] = []
    paint_cells: list[tuple[int, int]] = []
    marker_positions = (spec["marker_a"], spec["marker_b"])
    for index, (a, b) in enumerate(pairs):
        placement = _first_placement(marker_positions, a, b)
        if placement is None:
            errors.append(
                f"greedy pair {index} at {(a['r1'], a['c1'])}/{(b['r1'], b['c1'])} "
                "does not anchor a common scaled template"
            )
            continue
        relation = _pair_relation(spec["marker_diag"], a, b)
        if relation is None:
            errors.append(f"greedy pair {index} is not separated by exactly two scale units diagonally")
            continue
        targets: list[tuple[int, int]] = []
        blocks: list[tuple[tuple[int, int], ...]] = []
        for fill_pos in spec["fill"]:
            tr, tc = _xform(fill_pos, placement["transform"])
            block = tuple(
                (r, c)
                for r in range(
                    placement["sr"] + tr * placement["sh"],
                    placement["sr"] + (tr + 1) * placement["sh"],
                )
                for c in range(
                    placement["sc"] + tc * placement["sw"],
                    placement["sc"] + (tc + 1) * placement["sw"],
                )
            )
            blocks.append(block)
            targets.extend(block)
        if any(not (0 <= r < h and 0 <= c < w) for r, c in targets):
            errors.append(f"greedy pair {index} produces out-of-bounds fill targets")
        occupied_targets = [(r, c) for r, c in targets if 0 <= r < h and 0 <= c < w and grid[r][c] != bg]
        if occupied_targets:
            errors.append(f"greedy pair {index} has {len(occupied_targets)} non-background fill targets")
        paint_cells.extend(targets)
        pair_facts.append(
            {
                "a": a,
                "b": b,
                "scale": a["h"],
                "relation": relation,
                "placement": placement,
                "targets": tuple(targets),
                "blocks": tuple(blocks),
                "footprint": (
                    placement["sr"],
                    placement["sc"],
                    placement["sr"] + 3 * placement["sh"] - 1,
                    placement["sc"] + 3 * placement["sw"] - 1,
                ),
            }
        )

    duplicate_targets = len(paint_cells) - len(set(paint_cells))
    if duplicate_targets:
        errors.append(f"pair footprints overlap on {duplicate_targets} fill target cells")
    scales = tuple(pair["scale"] for pair in pair_facts)
    lesson_profile = _lesson_profile(scales)
    if lesson_profile is None:
        errors.append(f"scale multiset {tuple(sorted(scales))} is outside the lesson profile catalog")
    relations = tuple(pair["relation"] for pair in pair_facts)
    if relations:
        orientation_profile = relations[0] if len(set(relations)) == 1 else "mixed"
    else:
        orientation_profile = None

    facts = {
        "grid_h": h,
        "grid_w": w,
        "bg_color": bg,
        "fill_color": fill_color,
        "marker_a_color": marker_a,
        "marker_b_color": marker_b,
        "template_profile": profile,
        "lesson_profile": lesson_profile,
        "orientation_profile": orientation_profile,
        "template": template,
        "template_spec": spec,
        "marker_objects": tuple(marker_objects),
        "pairs": tuple(pair_facts),
        "pair_count": len(pair_facts),
        "scales": scales,
        "relations": relations,
        "paint_cells": tuple(paint_cells),
        "changed_cells": len(set(paint_cells)),
    }
    return facts, errors


_ANALYZE_CACHE: tuple[
    tuple[tuple[int, ...], ...],
    tuple[dict[str, Any] | None, list[str]],
] | None = None


def _analyze(grid: list[list[int]]) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse one grid, reusing the immediately repeated public-hook analysis.

    The override contract intentionally calls ``observe_overrides`` twice and
    ``self_check`` once for the same immutable returned grid.  A one-entry,
    content-keyed cache avoids doing the complete component/placement parse
    three times without retaining the checker's large stream of prior grids.
    Invalid or ragged inputs bypass the cache and preserve the diagnostic path.
    """
    global _ANALYZE_CACHE
    if (
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int) and 0 <= value <= 9
            for row in grid
            for value in row
        )
    ):
        key = tuple(tuple(row) for row in grid)
        cached = _ANALYZE_CACHE
        if cached is not None and cached[0] == key:
            return cached[1]
        result = _analyze_uncached(grid)
        _ANALYZE_CACHE = (key, result)
        return result
    return _analyze_uncached(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural gate for the exact template/greedy-pair teaching grammar."""
    _facts, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons = []
    if not (19 <= facts["grid_h"] <= 22 and 19 <= facts["grid_w"] <= 22):
        reasons.append("grid dimensions fall outside the canonical 19..22 envelope")
    if len({value for row in grid for value in row}) != 4:
        reasons.append("canonical inputs use exactly four colors including background")
    if facts["pair_count"] not in (1, 2, 3):
        reasons.append("canonical inputs contain one to three marker pairs")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {key: facts[key] for key in AXES}


def _facts_or_none(grid):
    facts, errors = _analyze(grid)
    return None if errors else facts


def _witness_unit(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and 1 in facts["scales"])


def _witness_scaled(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and any(scale > 1 for scale in facts["scales"]))


def _witness_multi_pair(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and facts["pair_count"] >= 2)


def _witness_mixed_scale(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and len(set(facts["scales"])) >= 2)


def _witness_same_diagonal(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and "same" in facts["relations"])


def _witness_opposite_diagonal(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and "opposite" in facts["relations"])


def _witness_three_pairs(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and facts["pair_count"] == 3)


SEMANTIC_WITNESSES = {
    "unit_scale": _witness_unit,
    "scaled_blocks": _witness_scaled,
    "multiple_pairs": _witness_multi_pair,
    "mixed_scales": _witness_mixed_scale,
    "same_diagonal": _witness_same_diagonal,
    "opposite_diagonal": _witness_opposite_diagonal,
    "three_pairs": _witness_three_pairs,
}


def _predict(grid: list[list[int]], mode: str) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    bg, fill = facts["bg_color"], facts["fill_color"]
    pairs = list(facts["pairs"])
    if mode == "identity":
        return out
    if mode == "first_pair_only":
        pairs = pairs[:1]
    elif mode == "first_two_pairs_only":
        pairs = pairs[:2]
    elif mode == "unit_scale_only":
        pairs = [pair for pair in pairs if pair["scale"] == 1]
    elif mode == "scaled_only":
        pairs = [pair for pair in pairs if pair["scale"] > 1]
    elif mode == "same_diagonal_only":
        pairs = [pair for pair in pairs if pair["relation"] == "same"]
    elif mode == "opposite_diagonal_only":
        pairs = [pair for pair in pairs if pair["relation"] == "opposite"]

    if mode == "full_footprint":
        for pair in pairs:
            r1, c1, r2, c2 = pair["footprint"]
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    if out[r][c] == bg:
                        out[r][c] = fill
        return out

    paint_color = facts["marker_a_color"] if mode == "marker_as_answer" else fill
    for pair in pairs:
        if mode == "unit_stamp":
            targets = [block[0] for block in pair["blocks"]]
        else:
            targets = pair["targets"]
        for r, c in targets:
            if out[r][c] == bg:
                out[r][c] = paint_color
    return out


def _rival_solver(mode: str):
    def solve(grid):
        return _predict(grid, mode)

    solve.__name__ = f"rival_{mode}"
    return solve


LESSON_COMPETITORS = {
    mode: _rival_solver(mode)
    for mode in (
        "identity",
        "full_footprint",
        "unit_stamp",
        "marker_as_answer",
        "first_pair_only",
        "first_two_pairs_only",
        "unit_scale_only",
        "scaled_only",
        "same_diagonal_only",
        "opposite_diagonal_only",
    )
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
WITNESS_RIVALS = {
    "unit_scale": ["scaled_only"],
    "scaled_blocks": ["unit_scale_only"],
    "multiple_pairs": ["first_pair_only"],
    "mixed_scales": ["unit_scale_only", "scaled_only"],
    "same_diagonal": ["opposite_diagonal_only"],
    "opposite_diagonal": ["same_diagonal_only"],
    "three_pairs": ["first_two_pairs_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave any declared rival answer-ambiguous."""
    reasons: list[str] = []
    all_rows = list(demos) + [query]
    for index, row in enumerate(all_rows):
        try:
            canonical = _predict(row["input"], "canonical")
        except Exception as exc:
            reasons.append(f"row {index} is outside the teaching grammar: {exc}")
            continue
        if canonical != row["output"]:
            reasons.append(f"row {index} output disagrees with the task-linked Python audit mirror")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        demo_match = all(competitor(row["input"]) == row["output"] for row in demos)
        if demo_match and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not rule out shortcut: {name}")
    return reasons


def _validate_scalar_inputs(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")

    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")

    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")

    for axis, spec in AXES.items():
        value = overrides.get(axis)
        if value is None:
            continue
        expected = int if spec["type"] == "int" else str
        if type(value) is not expected:
            raise ValueError(f"{axis} must be a {spec['type']} scalar")

    texture = overrides.get("texture")
    if texture is not None and type(texture) is not str:
        raise ValueError("texture must be a str scalar")


def _effective_overrides(sample_index: int, overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    effective = dict(overrides)
    texture = effective.pop("texture", None)
    if texture in DEGENERATE_TEXTURES:
        return effective, texture
    if texture is not None:
        if texture not in TEMPLATE_PROFILE_NAMES:
            raise ValueError(f"unknown texture {texture!r}")
        if effective.get("template_profile") not in (None, texture):
            raise ValueError(
                f"texture={texture!r} conflicts with template_profile={effective['template_profile']!r}"
            )
        effective["template_profile"] = texture

    phase = sample_index % len(LESSON_PROFILE_NAMES)
    if "lesson_profile" not in effective:
        scheduled_lesson = LESSON_PROFILE_NAMES[phase]
        if (
            effective.get("orientation_profile") == "mixed"
            and len(LESSON_SCALES[scheduled_lesson]) < 2
        ):
            multi_lessons = ("unit_double", "mixed_1_2", "mixed_1_2_3")
            scheduled_lesson = multi_lessons[sample_index % len(multi_lessons)]
        effective["lesson_profile"] = scheduled_lesson
    effective.setdefault("template_profile", TEMPLATE_PROFILE_NAMES[sample_index % len(TEMPLATE_PROFILE_NAMES)])
    lesson = effective["lesson_profile"]
    if lesson not in LESSON_SCALES:
        raise ValueError(f"unknown lesson_profile {lesson!r}")
    effective.setdefault("orientation_profile", DEFAULT_ORIENTATION_BY_LESSON[lesson])
    return effective, None


def _draw_colors(ctx) -> tuple[int, int, int, int]:
    selected: dict[str, int] = {}
    forced = [
        label
        for label in _COLOR_AXES
        if label in ctx.overrides and ctx.overrides[label] is not None
    ]
    order = forced + [label for label in _COLOR_AXES if label not in forced]
    for label in order:
        selected[label] = ctx.draw_color(label, exclude=set(selected.values()))
    return tuple(selected[label] for label in _COLOR_AXES)


def _rect_conflict(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int], margin: int = 1
) -> bool:
    ar, ac, ah, aw = a
    br, bc, bh, bw = b
    return not (
        ar + ah - 1 + margin < br
        or br + bh - 1 + margin < ar
        or ac + aw - 1 + margin < bc
        or bc + bw - 1 + margin < ac
    )


def _pack_rectangles(
    h: int,
    w: int,
    rectangles: list[tuple[str, int, int]],
    rng,
) -> dict[str, tuple[int, int]] | None:
    order = sorted(rectangles, key=lambda row: row[1] * row[2], reverse=True)
    for _attempt in range(300):
        placed: list[tuple[int, int, int, int]] = []
        result: dict[str, tuple[int, int]] = {}
        failed = False
        for name, rh, rw in order:
            candidates = [
                (r, c)
                for r in range(h - rh + 1)
                for c in range(w - rw + 1)
                if all(not _rect_conflict((r, c, rh, rw), prior) for prior in placed)
            ]
            if not candidates:
                failed = True
                break
            r, c = rng.choice(candidates)
            result[name] = (r, c)
            placed.append((r, c, rh, rw))
        if not failed:
            return result
    return None


def _relations_for(profile: str, count: int) -> tuple[str, ...]:
    if profile == "same":
        return ("same",) * count
    if profile == "opposite":
        return ("opposite",) * count
    if count < 2:
        raise ValueError("orientation_profile='mixed' requires at least two marker pairs")
    return tuple("same" if index % 2 == 0 else "opposite" for index in range(count))


def _marker_offsets(template_diag: str, relation: str, scale: int) -> tuple[tuple[int, int], tuple[int, int]]:
    pair_diag = template_diag if relation == "same" else ("anti" if template_diag == "main" else "main")
    if pair_diag == "main":
        return (0, 0), (2 * scale, 2 * scale)
    return (0, 2 * scale), (2 * scale, 0)


def _build_scene(
    h: int,
    w: int,
    bg: int,
    fill: int,
    marker_a: int,
    marker_b: int,
    template_profile: str,
    scales: tuple[int, ...],
    orientation_profile: str,
    rng,
) -> list[list[int]]:
    spec = _template_spec(template_profile)
    relations = _relations_for(orientation_profile, len(scales))
    rectangles = [("template", 3, 3)] + [
        (f"pair_{index}", 3 * scale, 3 * scale)
        for index, scale in enumerate(scales)
    ]

    for _attempt in range(800):
        placements = _pack_rectangles(h, w, rectangles, rng)
        if placements is None:
            break
        marker_objects: list[dict[str, Any]] = []
        intended: set[frozenset[int]] = set()
        pair_cells: list[tuple[int, int, int, int, int]] = []
        next_id = 0
        for index, (scale, relation) in enumerate(zip(scales, relations)):
            top, left = placements[f"pair_{index}"]
            first_offset, second_offset = _marker_offsets(spec["marker_diag"], relation, scale)
            if rng.random() < 0.5:
                role_rows = ((first_offset, marker_a), (second_offset, marker_b))
            else:
                role_rows = ((first_offset, marker_b), (second_offset, marker_a))
            pair_ids = []
            for (dr, dc), color in role_rows:
                r1, c1 = top + dr, left + dc
                obj = {
                    "r1": r1,
                    "c1": c1,
                    "r2": r1 + scale - 1,
                    "c2": c1 + scale - 1,
                    "h": scale,
                    "w": scale,
                    "size": scale * scale,
                    "color": color,
                    "pair_id": index,
                    "object_id": next_id,
                }
                next_id += 1
                marker_objects.append(obj)
                pair_ids.append(obj["object_id"])
                pair_cells.append((r1, c1, scale, color, index))
            intended.add(frozenset(pair_ids))
        recovered = {
            frozenset((a["object_id"], b["object_id"]))
            for a, b in _greedy_pairs(marker_objects)
        }
        if recovered != intended:
            continue

        grid = full_grid(h, w, bg)
        tr, tc = placements["template"]
        symbols = TEMPLATE_PROFILES[template_profile]
        color_for = {"F": fill, "A": marker_a, "B": marker_b}
        for r, row in enumerate(symbols):
            for c, symbol in enumerate(row):
                if symbol != ".":
                    grid[tr + r][tc + c] = color_for[symbol]
        for r1, c1, scale, color, _pair_index in pair_cells:
            for r in range(r1, r1 + scale):
                for c in range(c1, c1 + scale):
                    grid[r][c] = color
        return grid
    raise ValueError(
        "could not place the requested template/pair profile without greedy cross-pairing; "
        f"grid={h}x{w}, scales={scales}, orientation={orientation_profile}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_scalar_inputs(seed, sample_index, difficulty, overrides)
    effective, degenerate = _effective_overrides(sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    if degenerate is not None:
        return _draw_from_degenerate(degenerate, ctx.draw_rng("degenerate"))

    band_ranges = {
        "easy": (19, 20),
        "medium": (20, 21),
        "hard": (21, 22),
    }
    default_lo, default_hi = band_ranges.get(difficulty, (19, 22))
    h_lo, h_hi = (19, 22) if "grid_h" in effective else (default_lo, default_hi)
    w_lo, w_hi = (19, 22) if "grid_w" in effective else (default_lo, default_hi)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    bg, fill, marker_a, marker_b = _draw_colors(ctx)
    template_profile = ctx.draw_choice("template_profile", TEMPLATE_PROFILE_NAMES)
    lesson_profile = ctx.draw_choice("lesson_profile", LESSON_PROFILE_NAMES)
    orientation_profile = ctx.draw_choice("orientation_profile", ORIENTATION_PROFILES)
    scales = LESSON_SCALES[lesson_profile]
    if orientation_profile == "mixed" and len(scales) < 2:
        raise ValueError(
            f"orientation_profile='mixed' is incompatible with lesson_profile={lesson_profile!r}"
        )

    grid = _build_scene(
        h,
        w,
        bg,
        fill,
        marker_a,
        marker_b,
        template_profile,
        scales,
        orientation_profile,
        ctx.draw_rng("layout"),
    )
    return grid


def _draw_from_degenerate(name: str, rng) -> list[list[int]]:
    grid = full_grid(19, 19, 0)
    if name == "no_template":
        grid[4][4] = 2
        grid[6][6] = 3
        return grid
    if name == "no_markers":
        for r, row in enumerate(TEMPLATE_PROFILES["plus5_main"]):
            for c, symbol in enumerate(row):
                if symbol != ".":
                    grid[2 + r][2 + c] = {"F": 8, "A": 2, "B": 3}[symbol]
        return grid
    if name == "broken_marker":
        grid = _build_scene(19, 19, 0, 8, 2, 3, "plus5_main", (2,), "same", rng)
        facts, errors = _analyze(grid)
        if errors:
            return grid
        obj = facts["marker_objects"][0]
        grid[obj["r1"]][obj["c1"]] = 0
        return grid
    if name == "ambiguous_pairing":
        # Four singleton markers at square corners: nearest cross-pairs tie and
        # consume objects in a way that does not encode one intended footprint.
        for r, row in enumerate(TEMPLATE_PROFILES["plus5_main"]):
            for c, symbol in enumerate(row):
                if symbol != ".":
                    grid[2 + r][2 + c] = {"F": 8, "A": 2, "B": 3}[symbol]
        for r, c, color in ((10, 10, 2), (10, 12, 3), (12, 10, 3), (12, 12, 2)):
            grid[r][c] = color
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
