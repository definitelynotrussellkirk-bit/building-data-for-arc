"""Generator for ARC task 69bc1c71fd5a.

The unique color-9 cell is a pivot.  Every other nonzero cell is rotated 90°
clockwise around that pivot, preserving its color, onto a fresh zero canvas;
the pivot itself is omitted.  Generated lessons interleave canonical-scale
single L-triomino scenes with multi-color, multi-motif scenes so that a
"rotate only the first object" shortcut cannot survive a three-demo window.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "69bc1c71fd5a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "79cf710548e3"

SUMMARY = (
    "Find the unique color-9 anchor. Rotate every other nonzero cell 90 degrees "
    "clockwise around that anchor, preserve each cell's color, write the result "
    "on a fresh color-0 canvas, and do not copy the anchor."
)

INVARIANTS = [
    "background is color 0 and cells are ARC colors 0..9",
    "there is exactly one color-9 rotation anchor",
    "every non-anchor color forms one 4-connected motif",
    "all rotated motif cells remain in bounds and the output is non-identity",
    "multi-motif scenes use distinct colors and separated components",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

_BASE_SHAPES = {
    "L3": ((0, 0), (1, 0), (1, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
}

# The profile is exactly recoverable from (grid shape, component count, and
# component morphology).  The first/last three profiles intentionally follow
# S,M,M,S,M,S cyclically, so every three consecutive lessons contains a
# multi-motif counterexample to the first-object-only shortcut.
_PROFILE_SPECS = {
    "canon_6x7_l3": {
        "shape": (6, 7), "motifs": ("L3",), "quadrants": (None,),
    },
    "multi_9x10_l3_t4": {
        "shape": (9, 10), "motifs": ("L3", "T4"),
        "quadrants": ("nw", "se"),
    },
    "multi_10x9_t4_p5": {
        "shape": (10, 9), "motifs": ("T4", "P5"),
        "quadrants": ("ne", "sw"),
    },
    "canon_7x7_l3": {
        "shape": (7, 7), "motifs": ("L3",), "quadrants": (None,),
    },
    "multi_12x12_l3_t4_p5": {
        "shape": (12, 12), "motifs": ("L3", "T4", "P5"),
        "quadrants": ("nw", "ne", "s"),
    },
    "canon_8x8_l3": {
        "shape": (8, 8), "motifs": ("L3",), "quadrants": (None,),
    },
}

SCHEDULE_PROFILES = tuple(_PROFILE_SPECS)
SCENE_PROFILES = SCHEDULE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic six-profile curriculum",
        "valid": "canon_6x7_l3|multi_9x10_l3_t4|multi_10x9_t4_p5|canon_7x7_l3|multi_12x12_l3_t4_p5|canon_8x8_l3",
        "doc": "Exact recoverable grid/motif profile; all six values are legal in every band.",
    }
}

_ANCHOR_CANDIDATES = {
    (6, 7): ((2, 4), (3, 2), (2, 2), (3, 4)),
    (7, 7): ((4, 2), (2, 4), (4, 4), (2, 2)),
    (8, 8): ((3, 4), (4, 3), (3, 3), (4, 5)),
    (9, 10): ((4, 4), (4, 5), (3, 4), (5, 5)),
    (10, 9): ((4, 4), (5, 3), (4, 3), (5, 5)),
    (12, 12): ((5, 6), (6, 5), (5, 5), (6, 7)),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle profiles; every length-three sliding window contains a multi scene."""
    del seed
    offset = {"easy": 0, "medium": 2, "hard": 4}[_band(difficulty)]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _d4_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    points = tuple(cells)
    variants = set()
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


def _shape_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_d4_variants(cells))


_SHAPE_VARIANTS = {name: _d4_variants(cells) for name, cells in _BASE_SHAPES.items()}
_SHAPE_SIGNATURES = {name: _shape_signature(cells) for name, cells in _BASE_SHAPES.items()}
_SIGNATURE_TO_NAME = {signature: name for name, signature in _SHAPE_SIGNATURES.items()}


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _rotate_point(r: int, c: int, anchor: tuple[int, int], clockwise: bool = True) -> tuple[int, int]:
    ar, ac = anchor
    dr, dc = r - ar, c - ac
    return (ar + dc, ac - dr) if clockwise else (ar - dc, ac + dr)


def _profile_signature(profile: str) -> tuple[int, int, tuple[str, ...]]:
    spec = _PROFILE_SPECS[profile]
    h, w = spec["shape"]
    return h, w, tuple(sorted(spec["motifs"]))


_PROFILE_BY_SIGNATURE = {
    _profile_signature(profile): profile for profile in SCENE_PROFILES
}


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor; found {len(anchors)}")
        return {"errors": errors, "height": h, "width": w, "anchors": anchors}
    anchor = anchors[0]
    colors = sorted({value for row in grid for value in row if value not in (0, 9)})
    if not colors:
        errors.append("expected at least one non-anchor colored motif")
    motif_rows = []
    for color in colors:
        cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
        comps = _components(cells)
        if len(comps) != 1:
            errors.append(f"color {color} must form one 4-connected motif; found {len(comps)}")
            continue
        component = comps[0]
        signature = _shape_signature(component)
        shape_name = _SIGNATURE_TO_NAME.get(signature)
        if shape_name is None:
            errors.append(f"color {color} has unsupported motif morphology")
        motif_rows.append({
            "color": color,
            "cells": component,
            "size": len(component),
            "shape_name": shape_name,
            "signature": signature,
        })
    profile = None
    if not errors:
        signature = (h, w, tuple(sorted(row["shape_name"] for row in motif_rows)))
        profile = _PROFILE_BY_SIGNATURE.get(signature)
        if profile is None:
            errors.append(
                "grid shape and motif morphology do not match any declared scene_profile"
            )
    rotated = []
    if len(anchors) == 1:
        for row in motif_rows:
            for r, c in row["cells"]:
                nr, nc = _rotate_point(r, c, anchor)
                rotated.append((nr, nc, row["color"]))
                if not (0 <= nr < h and 0 <= nc < w):
                    errors.append(
                        f"rotated cell {(r, c)} -> {(nr, nc)} leaves the grid"
                    )
    quadrants = set()
    ar, ac = anchor
    for row in motif_rows:
        for r, c in row["cells"]:
            if r < ar and c < ac:
                quadrants.add("nw")
            if r < ar and c > ac:
                quadrants.add("ne")
            if r > ar and c < ac:
                quadrants.add("sw")
            if r > ar and c > ac:
                quadrants.add("se")
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "anchor": anchor,
        "motifs": motif_rows,
        "motif_count": len(motif_rows),
        "profile": profile,
        "quadrants": quadrants,
        "rotated": rotated,
        "anchor_is_floor_center": anchor == (h // 2, w // 2),
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the full oracle domain; Racket is authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        raise ValueError(f"expected exactly one color-9 anchor; found {len(anchors)}")
    anchor = anchors[0]
    output = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9):
                continue
            nr, nc = _rotate_point(r, c, anchor)
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = color
    return output


def _rival_counterclockwise(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    h, w = analysis["height"], analysis["width"]
    output = full_grid(h, w, 0)
    for motif in analysis["motifs"]:
        for r, c in motif["cells"]:
            nr, nc = _rotate_point(r, c, analysis["anchor"], clockwise=False)
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = motif["color"]
    return output


def _rival_first_color_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    h, w = analysis["height"], analysis["width"]
    output = full_grid(h, w, 0)
    first = min(
        analysis["motifs"],
        key=lambda motif: min(motif["cells"]),
    )
    for r, c in first["cells"]:
        nr, nc = _rotate_point(r, c, analysis["anchor"])
        output[nr][nc] = first["color"]
    return output


def _rival_grid_center(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    h, w = analysis["height"], analysis["width"]
    center = (h // 2, w // 2)
    output = full_grid(h, w, 0)
    for motif in analysis["motifs"]:
        for r, c in motif["cells"]:
            nr, nc = _rotate_point(r, c, center)
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = motif["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "counterclockwise_rotation": _rival_counterclockwise,
    "first_color_only": _rival_first_color_only,
    "grid_center_pivot": _rival_grid_center,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"first_color_only": _rival_first_color_only}


def _valid_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis.get("errors") else analysis


def _quadrant_witness(name: str):
    def witness(grid: Any) -> bool:
        analysis = _valid_analysis(grid)
        return analysis is not None and name in analysis["quadrants"]
    return witness


SEMANTIC_WITNESSES = {
    "source_northwest": _quadrant_witness("nw"),
    "source_northeast": _quadrant_witness("ne"),
    "source_southwest": _quadrant_witness("sw"),
    "source_southeast": _quadrant_witness("se"),
    "multiple_motifs": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["motif_count"] >= 2
    ),
    "anchor_not_grid_center": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and not analysis["anchor_is_floor_center"]
    ),
    "clockwise_not_counterclockwise": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and rule_mirror(grid) != _rival_counterclockwise(grid)
    ),
}
WITNESS_RIVALS = {
    "source_northwest": ["counterclockwise_rotation"],
    "source_northeast": ["counterclockwise_rotation"],
    "source_southwest": ["counterclockwise_rotation"],
    "source_southeast": ["counterclockwise_rotation"],
    "multiple_motifs": ["first_color_only"],
    "anchor_not_grid_center": ["grid_center_pivot"],
    "clockwise_not_counterclockwise": ["counterclockwise_rotation"],
}


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the authority-valid task grammar and reject hiding scenes."""
    errors = _rectangular_errors(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    # Multi-color motifs stay visually separable; canonical single motifs may
    # touch the anchor exactly as the official examples do.
    motifs = analysis["motifs"]
    if len(motifs) > 1:
        for i, left in enumerate(motifs):
            for right in motifs[i + 1:]:
                if any(
                    max(abs(r1 - r2), abs(c1 - c2)) <= 1
                    for r1, c1 in left["cells"]
                    for r2, c2 in right["cells"]
                ):
                    errors.append("distinct motifs must have a one-cell visual buffer")

    official = rule_mirror(grid)
    input_without_anchor = [
        [0 if value == 9 else value for value in row]
        for row in grid
    ]
    if official == input_without_anchor:
        errors.append("scene is rotationally invariant and hides the clockwise operation")
    if official == _rival_counterclockwise(grid):
        errors.append("clockwise and counterclockwise rotations are answer-equivalent")
    requested = None
    if isinstance(meta, dict):
        overrides = meta.get("overrides")
        if isinstance(overrides, dict):
            requested = overrides.get("scene_profile")
    if requested is not None and requested != analysis["profile"]:
        errors.append(
            f"scene_profile override requested {requested!r}, observed {analysis['profile']!r}"
        )
    return errors


def observe_overrides(grid: Any) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis.get("errors") or analysis.get("profile") is None:
        return {}
    return {"scene_profile": analysis["profile"]}


def strict_canonical_like(grid: Any) -> list[str]:
    """Exact canonical-scale manifold: one L triomino on 6x7, 7x7, or 8x8."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = observe_overrides(grid)["scene_profile"]
    if not profile.startswith("canon_"):
        return ["not a canonical-scale single L-triomino profile"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut survives every demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # explicit handoff of malformed materialized data
            reasons.append(f"{label} is not a lawful input: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"{label} disagrees with the clockwise-anchor rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def _all_in_quadrant(cells: Iterable[tuple[int, int]], anchor: tuple[int, int], quadrant: str | None) -> bool:
    if quadrant is None:
        return True
    ar, ac = anchor
    if quadrant == "nw":
        return all(r < ar and c < ac for r, c in cells)
    if quadrant == "ne":
        return all(r < ar and c > ac for r, c in cells)
    if quadrant == "sw":
        return all(r > ar and c < ac for r, c in cells)
    if quadrant == "se":
        return all(r > ar and c > ac for r, c in cells)
    if quadrant == "s":
        return all(r > ar for r, _ in cells) and any(c < ac for _, c in cells) and any(c > ac for _, c in cells)
    raise ValueError(f"unknown quadrant constraint: {quadrant!r}")


def _candidate_placements(
    shape: tuple[tuple[int, int], ...],
    anchor: tuple[int, int],
    h: int,
    w: int,
    occupied: set[tuple[int, int]],
    quadrant: str | None,
) -> list[tuple[tuple[int, int], ...]]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    placements = []
    for r0 in range(h - sh + 1):
        for c0 in range(w - sw + 1):
            cells = tuple((r0 + r, c0 + c) for r, c in shape)
            if anchor in cells or any(cell in occupied for cell in cells):
                continue
            if not _all_in_quadrant(cells, anchor, quadrant):
                continue
            if occupied and any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in cells
                for r2, c2 in occupied
            ):
                continue
            rotated = [_rotate_point(r, c, anchor) for r, c in cells]
            if not all(0 <= r < h and 0 <= c < w for r, c in rotated):
                continue
            placements.append(cells)
    return placements


def _construct_profile(profile: str, rng) -> list[list[int]]:
    spec = _PROFILE_SPECS[profile]
    h, w = spec["shape"]
    anchors = list(_ANCHOR_CANDIDATES[(h, w)])
    rng.shuffle(anchors)
    colors = rng.sample(list(range(1, 9)), len(spec["motifs"]))

    for anchor in anchors:
        if anchor == (h // 2, w // 2):
            continue
        occupied: set[tuple[int, int]] = set()
        chosen: list[tuple[int, tuple[tuple[int, int], ...]]] = []
        success = True
        for index, (shape_name, quadrant) in enumerate(zip(spec["motifs"], spec["quadrants"])):
            variants = list(_SHAPE_VARIANTS[shape_name])
            rng.shuffle(variants)
            choices = []
            for variant in variants:
                choices.extend(
                    _candidate_placements(variant, anchor, h, w, occupied, quadrant)
                )
            if not choices:
                success = False
                break
            cells = rng.choice(choices)
            occupied.update(cells)
            chosen.append((colors[index], cells))
        if not success:
            continue
        grid = full_grid(h, w, 0)
        ar, ac = anchor
        grid[ar][ac] = 9
        for color, cells in chosen:
            for r, c in cells:
                grid[r][c] = color
        if not self_check(grid):
            return grid
    raise ValueError(f"could not construct lawful profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_SPECS:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    return _construct_profile(profile, ctx.draw_rng("layout"))
