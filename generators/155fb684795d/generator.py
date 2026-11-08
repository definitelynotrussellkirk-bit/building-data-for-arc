"""Generator for 155fb684795d — select by the plus-grown shape signature.

The grid contains four equal panels separated by full-height color-9 columns.
Each panel contains one monochrome, four-connected object.  Grow each object's
cells by one orthogonal (plus) step inside its panel, normalize over rotations
and reflections, and find the one grown signature occurring once.  Return that
panel's ORIGINAL object, tightly cropped and recolored 8.

The curriculum deliberately includes two kinds of examples:

* canonical anchors: three transformed dominoes versus one L triomino;
* shortcut rebuttals: the three common panels use two different RAW shapes
  (and two different cell counts) whose plus-grown signatures coincide, while
  the odd panel shares its cell count with a common panel.  Consequently,
  neither raw-shape comparison nor unique-size selection identifies the answer.

``sample_index % 4`` schedules one canonical anchor followed by three shortcut
rebuttals.  It also schedules the odd panel through all four positions, making
every 3-demo + 1-query lesson identify the intended rule rather than a fixed
position shortcut.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "155fb684795d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "76d51e40d80e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Split the four color-9-separated panels. Plus-dilate each panel's single "
    "object, compare the grown silhouettes up to rotation/reflection, and "
    "output the ORIGINAL object from the uniquely grown panel, cropped and "
    "recolored 8. Generated rebuttal examples make raw-shape and count-only "
    "selection give the wrong or an ambiguous answer."
)

INVARIANTS = [
    "exactly four equal panels separated by three full-height color-9 columns",
    "each panel contains one monochrome four-connected object with a blank margin",
    "three panels share one plus-grown dihedral signature and one panel differs",
    "the output is the original odd object, not its grown silhouette, recolored 8",
    "ordinary lessons include examples where raw-shape and cell-count shortcuts fail",
]

# Keep only axes that are exact and recoverable from the returned grid.  Four
# panels are canonical and fixed; variation lives in scale, target position,
# shapes, orientations, placement, and palette relabeling.
AXES = {
    "panel_h": {"type": "int", "default": "difficulty-aware 5..6", "valid": "5..6"},
    "panel_w": {"type": "int", "default": "difficulty-aware 5..6", "valid": "5..6"},
    "odd_index": {"type": "int", "default": "sample_index modulo 4", "valid": "0..3"},
}

_N_PANELS = 4
_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))

# Canonical branch: the official examples use transformed dominoes and an L.
_CANONICAL_COMMON = ((0, 0), (0, 1))
_CANONICAL_ODD = ((0, 0), (1, 0), (1, 1))

# Rebuttal branch.  These two raw shapes have DIFFERENT raw dihedral keys and
# cell counts (5 versus 6), but the SAME plus-grown dihedral key.  With panel
# roles A, B, A, odd(6 cells), the cell-count histogram is 5,6,5,6 and raw-key
# uniqueness has two candidates.  Only plus-growth leaves one unique panel.
_COMMON_A = ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2))
_COMMON_B = ((0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))

# Connected five- and six-cell odd motifs.  The five-cell choices make the
# six-cell common motif uniquely sized (and therefore make the size shortcut
# actively wrong); the six-cell choices make size selection ambiguous.  Every
# choice is filtered against the common grown key at runtime.
_ODD_CANDIDATES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),  # P pentomino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),  # U pentomino
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),  # T pentomino
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),  # zig pentomino
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),  # W pentomino
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),  # bent pentomino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),  # X pentomino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),  # 2x3 rectangle
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),  # staircase
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),  # U-like
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),  # skew cap
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),  # bent six
)


def _norm(cells):
    cells = list(cells)
    if not cells:
        return []
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells):
    cells = list(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rot_cw(cells):
    return _norm((c, -r) for r, c in cells)


def _all_transforms(cells):
    """All unique dihedral orientations, normalized and sorted."""
    unique = []
    current = _norm(cells)
    for _ in range(4):
        candidates = (current, _norm((r, -c) for r, c in current))
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        current = _rot_cw(current)
    return unique


def _shape_key(cells):
    return min(str(form) for form in _all_transforms(_norm(cells)))


def _grown_cells(cells, panel_h, panel_w):
    grown = {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in _PLUS
        if 0 <= r + dr < panel_h and 0 <= c + dc < panel_w
    }
    return _norm(grown)


def _grown_key(cells, panel_h, panel_w):
    """Dihedral key after plus-growth at the cells' true panel coordinates."""
    return _shape_key(_grown_cells(cells, panel_h, panel_w))


def _unclipped_grown_key(cells):
    """Dihedral plus-growth key for motifs guaranteed an empty-cell margin."""
    grown = {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in _PLUS
    }
    return _shape_key(grown)


def _component_sets(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component = {start}
        remaining.remove(start)
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _panel_bounds(grid):
    height = len(grid)
    width = len(grid[0])
    separators = [
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    boundaries = [-1] + separators + [width]
    return separators, [
        (boundaries[i] + 1, boundaries[i + 1])
        for i in range(len(boundaries) - 1)
        if boundaries[i] + 1 < boundaries[i + 1]
    ]


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    """Structural analysis shared by checking, observers, mirrors, and hooks."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], None
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["grid contains a non-ARC color"], None

    height = len(grid)
    errors = []
    if not (5 <= height <= 6):
        errors.append(f"panel height {height} outside 5..6")

    separators, bounds = _panel_bounds(grid)
    if len(separators) != _N_PANELS - 1:
        errors.append(
            f"expected exactly {_N_PANELS - 1} full-height color-9 dividers, "
            f"got {len(separators)}"
        )
    if any(b - a == 1 for a, b in zip(separators, separators[1:])):
        errors.append("adjacent divider columns create an empty panel")
    if any(
        grid[r][c] == 9 and c not in separators
        for r in range(height) for c in range(width)
    ):
        errors.append("color 9 appears outside a full-height divider")
    if len(bounds) != _N_PANELS:
        errors.append(f"expected exactly {_N_PANELS} non-empty panels, got {len(bounds)}")
        return errors, None

    panel_widths = [right - left for left, right in bounds]
    if len(set(panel_widths)) != 1:
        errors.append(f"panel widths are not equal: {panel_widths}")
    panel_w = panel_widths[0]
    if not (5 <= panel_w <= 6):
        errors.append(f"panel width {panel_w} outside 5..6")

    panel_infos = []
    for panel_index, (left, right) in enumerate(bounds):
        colored = [
            (r, c - left, grid[r][c])
            for r in range(height)
            for c in range(left, right)
            if grid[r][c] != 0
        ]
        if not colored:
            errors.append(f"panel {panel_index} has no object")
            continue
        cells = [(r, c) for r, c, _ in colored]
        components = _component_sets(cells)
        if len(components) != 1:
            errors.append(
                f"panel {panel_index} has {len(components)} disconnected objects; expected one"
            )
        colors = {value for _, _, value in colored}
        if len(colors) != 1:
            errors.append(f"panel {panel_index} object is not monochrome: {sorted(colors)}")
        if any(r in (0, height - 1) or c in (0, panel_w - 1) for r, c in cells):
            errors.append(
                f"panel {panel_index} object touches the panel boundary and clips plus-growth"
            )
        if len(cells) < 2:
            errors.append(f"panel {panel_index} object has fewer than two cells")
        normalized = _norm(cells)
        panel_infos.append({
            "index": panel_index,
            "left": left,
            "right": right,
            "cells": normalized,
            "panel_cells": cells,
            "color": next(iter(colors)) if colors else None,
            "cell_count": len(cells),
            "raw_key": _shape_key(normalized),
            "grown_key": _grown_key(cells, height, panel_w),
        })

    if len(panel_infos) == _N_PANELS:
        grown_counts = Counter(info["grown_key"] for info in panel_infos)
        if sorted(grown_counts.values()) != [1, _N_PANELS - 1]:
            errors.append(
                "expected one unique plus-grown signature and three matching "
                f"signatures; counts={sorted(grown_counts.values())}"
            )
        odd = [
            info for info in panel_infos
            if grown_counts[info["grown_key"]] == 1
        ]
    else:
        odd = []

    analysis = {
        "height": height,
        "width": width,
        "separators": separators,
        "panel_width": panel_w,
        "panels": panel_infos,
        "odd_index": odd[0]["index"] if len(odd) == 1 else None,
    }
    return errors, analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, clipped, multi-object, and semantically ambiguous scenes."""
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["odd_index"] is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "panel_h": analysis["height"],
        "panel_w": analysis["panel_width"],
        "odd_index": analysis["odd_index"],
    }


def _crop_as_eight(cells):
    normalized = _norm(cells)
    height, width = _dims(normalized)
    output = full_grid(height, width, 0)
    for r, c in normalized:
        output[r][c] = 8
    return output


def rule_mirror(grid):
    """Pure Python mirror for tests and rival-rule analysis only.

    The canonical Racket program remains the sole output authority used by the
    data pipeline and all smoke/materialization gates.
    """
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["odd_index"] is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    return _crop_as_eight(analysis["panels"][analysis["odd_index"]]["cells"])


def strict_canonical_like(grid) -> list[str]:
    """Canonical-scale semantic manifold, not merely morphology marginals."""
    reasons, analysis = _analyze_grid(grid)
    if reasons or analysis is None:
        return reasons
    if analysis["height"] != 5 or analysis["panel_width"] != 5:
        reasons.append(
            f"canonical panels are 5x5, got {analysis['height']}x{analysis['panel_width']}"
        )
    colors = {info["color"] for info in analysis["panels"]}
    if len(colors) != 1:
        reasons.append("canonical-like scenes use one shared object color across all panels")
    return reasons


def _analysis_if_valid(grid):
    errors, analysis = _analyze_grid(grid)
    return None if errors else analysis


def _witness_growth_needed(grid):
    """Raw-shape uniqueness is absent or selects a different panel."""
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    counts = Counter(info["raw_key"] for info in analysis["panels"])
    unique = [info["index"] for info in analysis["panels"] if counts[info["raw_key"]] == 1]
    return unique != [analysis["odd_index"]]


def _witness_count_only_rebuttal(grid):
    """Unique cell count is absent or points at a common panel."""
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    counts = Counter(info["cell_count"] for info in analysis["panels"])
    unique = [
        info["index"] for info in analysis["panels"]
        if counts[info["cell_count"]] == 1
    ]
    return unique != [analysis["odd_index"]]


def _witness_canonical_anchor(grid):
    return strict_canonical_like(grid) == []


def _witness_odd_index(index):
    def witness(grid):
        analysis = _analysis_if_valid(grid)
        return analysis is not None and analysis["odd_index"] == index
    return witness


def _witness_palette_relabel(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    return len({info["color"] for info in analysis["panels"]}) == 1 and analysis["panels"][0]["color"] != 2


SEMANTIC_WITNESSES = {
    "canonical_5x5_four_panel_anchor": _witness_canonical_anchor,
    "plus_growth_required_raw_shape_ambiguous": _witness_growth_needed,
    "cell_count_shortcut_rebutted": _witness_count_only_rebuttal,
    "odd_index_0": _witness_odd_index(0),
    "odd_index_1": _witness_odd_index(1),
    "odd_index_2": _witness_odd_index(2),
    "odd_index_3": _witness_odd_index(3),
    "object_palette_relabeling": _witness_palette_relabel,
}


def _competitor_raw_shape(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    counts = Counter(info["raw_key"] for info in analysis["panels"])
    candidates = [info for info in analysis["panels"] if counts[info["raw_key"]] == 1]
    return _crop_as_eight(candidates[0]["cells"]) if len(candidates) == 1 else None


def _competitor_unique_count(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    counts = Counter(info["cell_count"] for info in analysis["panels"])
    candidates = [
        info for info in analysis["panels"]
        if counts[info["cell_count"]] == 1
    ]
    return _crop_as_eight(candidates[0]["cells"]) if len(candidates) == 1 else None


def _competitor_fixed_panel(index):
    def solve(grid):
        analysis = _analysis_if_valid(grid)
        if analysis is None:
            return None
        return _crop_as_eight(analysis["panels"][index]["cells"])
    return solve


_LESSON_COMPETITORS = {
    "compare original raw shapes without plus-growth": _competitor_raw_shape,
    "select the uniquely sized object": _competitor_unique_count,
    "always select panel 0": _competitor_fixed_panel(0),
    "always select panel 1": _competitor_fixed_panel(1),
    "always select panel 2": _competitor_fixed_panel(2),
    "always select panel 3": _competitor_fixed_panel(3),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named plausible rival survives all demos."""
    reasons = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the plus-grown rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons


def _draw_axis(ctx, label, lo, hi, *, default=None):
    """Use full declared bounds for overrides, exact defaults when scheduled."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if default is not None:
        return ctx.draw_int(label, default, default)
    return ctx.draw_int(label, lo, hi)


def _orient_fit(cells, rng, panel_h, panel_w, *, avoid=None):
    forms = [
        form for form in _all_transforms(cells)
        if _dims(form)[0] <= panel_h - 2 and _dims(form)[1] <= panel_w - 2
    ]
    if avoid is not None and len(forms) > 1:
        alternatives = [form for form in forms if form != avoid]
        if alternatives:
            forms = alternatives
    if not forms:
        raise ValueError("motif does not fit with the required one-cell margin")
    return list(rng.choice(forms))


def _place(grid, panel_h, panel_w, panel_index, cells, color, rng):
    motif_h, motif_w = _dims(cells)
    top = rng.randint(1, panel_h - motif_h - 1)
    left_local = rng.randint(1, panel_w - motif_w - 1)
    panel_left = panel_index * (panel_w + 1)
    for dr, dc in cells:
        grid[top + dr][panel_left + left_local + dc] = color


def _blank_panels(panel_h, panel_w):
    width = _N_PANELS * panel_w + (_N_PANELS - 1)
    grid = full_grid(panel_h, width, 0)
    for panel_index in range(1, _N_PANELS):
        divider = panel_index * (panel_w + 1) - 1
        for row in range(panel_h):
            grid[row][divider] = 9
    return grid


def _build_canonical_anchor(rng, panel_h, panel_w, odd_index, color):
    grid = _blank_panels(panel_h, panel_w)
    previous_common = None
    for panel_index in range(_N_PANELS):
        raw = _CANONICAL_ODD if panel_index == odd_index else _CANONICAL_COMMON
        cells = _orient_fit(
            raw, rng, panel_h, panel_w,
            avoid=previous_common if panel_index != odd_index else None,
        )
        if panel_index != odd_index:
            previous_common = cells
        _place(grid, panel_h, panel_w, panel_index, cells, color, rng)
    return grid


def _build_shortcut_rebuttal(rng, panel_h, panel_w, odd_index, color):
    grid = _blank_panels(panel_h, panel_w)
    common_key = _unclipped_grown_key(_COMMON_A)
    if _unclipped_grown_key(_COMMON_B) != common_key:
        raise RuntimeError("common rebuttal motifs lost plus-grown equivalence")

    odd_candidates = [
        candidate for candidate in _ODD_CANDIDATES
        if _unclipped_grown_key(candidate) != common_key
        and _shape_key(candidate) not in {_shape_key(_COMMON_A), _shape_key(_COMMON_B)}
    ]
    if not odd_candidates:
        raise RuntimeError("no lawful odd rebuttal motif remains")
    odd_raw = rng.choice(odd_candidates)

    common_slots = [index for index in range(_N_PANELS) if index != odd_index]
    role_by_panel = {
        common_slots[0]: _COMMON_A,
        common_slots[1]: _COMMON_B,
        common_slots[2]: _COMMON_A,
        odd_index: odd_raw,
    }
    previous_a = None
    for panel_index in range(_N_PANELS):
        raw = role_by_panel[panel_index]
        cells = _orient_fit(
            raw, rng, panel_h, panel_w,
            avoid=previous_a if raw == _COMMON_A else None,
        )
        if raw == _COMMON_A:
            previous_a = cells
        _place(grid, panel_h, panel_w, panel_index, cells, color, rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_anchor = sample_index % 4 == 0

    if canonical_anchor:
        panel_h = _draw_axis(ctx, "panel_h", 5, 6, default=5)
        panel_w = _draw_axis(ctx, "panel_w", 5, 6, default=5)
    elif difficulty == "easy":
        panel_h = _draw_axis(ctx, "panel_h", 5, 6, default=5)
        panel_w = _draw_axis(ctx, "panel_w", 5, 6, default=5)
    elif difficulty == "medium":
        panel_h = _draw_axis(ctx, "panel_h", 5, 6)
        panel_w = _draw_axis(ctx, "panel_w", 5, 6, default=5)
    else:
        panel_h = _draw_axis(ctx, "panel_h", 5, 6)
        panel_w = _draw_axis(ctx, "panel_w", 5, 6)

    odd_index = _draw_axis(
        ctx, "odd_index", 0, 3, default=sample_index % _N_PANELS
    )
    color = ctx.draw_color("object_color", exclude={0, 9})
    rng = ctx.draw_rng("layout")

    if canonical_anchor:
        grid = _build_canonical_anchor(rng, panel_h, panel_w, odd_index, color)
    else:
        grid = _build_shortcut_rebuttal(rng, panel_h, panel_w, odd_index, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(errors))
    return grid
