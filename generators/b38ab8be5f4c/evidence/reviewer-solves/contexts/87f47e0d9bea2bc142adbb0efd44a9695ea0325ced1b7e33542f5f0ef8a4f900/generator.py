"""Generator for ``Guide-Color Crop`` (task ``b38ab8be5f4c``).

The first non-zero value in row 0 is a guide color.  In rows 1+, that
color identifies one of three connected colored objects.  The authoritative
Racket rule returns the *raw* tight bounding-box crop of all guide-colored body
cells; it does not mask other colors that happen to lie inside that box.

The four-sample schedule deliberately makes the lesson identifiable:

* marker columns cycle through 0 and non-zero positions;
* target zones cycle left/center/right;
* one role-swapped sample makes the marker select ``p5`` while a larger,
  higher-priority ``ring8`` distractor is present, refuting both
  "pick the largest" and marker-free fixed-morphology shortcuts;
* one sample puts another color inside the target bbox (refuting masking).

Most ordinary samples retain an exact canonical role/morphology signature.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b38ab8be5f4c"
TASK_ID = GENERATOR_ID
RULE_HASH = "439c1e733337"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.08

SUMMARY = (
    "Exactly one non-zero top-row marker supplies guide color G. Rows 1+ "
    "contain three distinct-color connected objects, exactly one colored G. "
    "Return the raw tight bounding-box crop of all body cells colored G. "
    "Non-guide cells inside that box remain in the output."
)

INVARIANTS = [
    "background is color 0",
    "row 0 has exactly one non-zero marker and row 1 is blank",
    "rows 1+ contain exactly three distinct non-zero colors",
    "each body color forms exactly one 4-connected component",
    "the guide color occurs in exactly one non-degenerate body object",
    "the last row is blank and at least one distractor lies outside the target bbox",
]

# Normalized 4-connected shapes mined from all five canonical inputs.
SHAPE_PROFILES: dict[str, tuple[tuple[int, int], ...]] = {
    "tri_l3": ((0, 0), (0, 1), (1, 0)),
    "zig4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "left_l4": ((0, 0), (0, 1), (0, 2), (1, 0)),
    "right_l4": ((0, 0), (0, 1), (0, 2), (1, 2)),
    "tee4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "cross5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "c5": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    "p5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "stair5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "ring8": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
    # Generalized anti-shortcut distractor, never part of strict canonical shape support.
    "solid9": tuple((r, c) for r in range(3) for c in range(3)),
    "singleton1": ((0, 0),),
}
TARGET_SHAPES = ("tee4", "c5", "p5", "stair5", "ring8")
TARGET_SHAPE_SET = set(TARGET_SHAPES)
CANONICAL_DISTRACTOR_SHAPES = {
    "tri_l3", "zig4", "square4", "left_l4", "right_l4", "tee4", "cross5", "c5"
}
CANONICAL_DIMENSIONS = ((8, 10), (9, 12), (10, 11), (8, 13))
TARGET_ZONES = ("left", "center", "right")
MORPHOLOGY_PRIORITY = ("ring8", "stair5", "p5", "c5", "tee4")
MORPHOLOGY_PRIORITY_RANK = {
    shape: index for index, shape in enumerate(MORPHOLOGY_PRIORITY)
}

# Exact linked role signatures observed in the canonical train/test set.
CANONICAL_ROLE_SIGNATURES = {
    ("c5", ("tri_l3", "zig4")),
    ("tee4", ("left_l4", "square4")),
    ("p5", ("cross5", "tri_l3")),
    ("ring8", ("right_l4", "square4")),
    ("stair5", ("c5", "tee4")),
}
CANONICAL_DISTRACTORS_BY_TARGET = {
    "c5": ("tri_l3", "zig4"),
    "tee4": ("square4", "left_l4"),
    "p5": ("cross5", "tri_l3"),
    "ring8": ("right_l4", "square4"),
    "stair5": ("tee4", "c5"),
}

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "10..13"},
    "marker_col": {"type": "int", "default": "four-sample schedule", "valid": "0..9"},
    "guide": {"type": "color", "default": "cyclic non-zero color", "valid": "1..9"},
    "target_shape": {
        "type": "enum",
        "default": "canonical target-shape schedule",
        "valid": "tee4|c5|p5|stair5|ring8",
    },
    "target_zone": {"type": "enum", "default": "left/center/right cycle", "valid": "left|center|right"},
    "bbox_intruder": {"type": "bool", "default": "true once per four samples", "valid": "true|false"},
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        return []
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                return []
            result.append([int(ch) for ch in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            return []
    return result


def _grid_errors(grid) -> list[str]:
    grid = _coerce_grid(grid)
    if not grid or not grid[0]:
        return ["grid must be a non-empty rectangle"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["grid values must be literal ARC integers 0..9"]
    return []


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_name(cells: Iterable[tuple[int, int]]) -> str | None:
    normalized = _normalize(cells)
    return next((name for name, shape in SHAPE_PROFILES.items() if shape == normalized), None)


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _connected_4(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _zone_for_bbox(bb: tuple[int, int, int, int], width: int) -> str:
    center = (bb[1] + bb[3]) / 2.0
    if center < width / 3.0:
        return "left"
    if center >= 2.0 * width / 3.0:
        return "right"
    return "center"


def _components_for_color(grid: list[list[int]], color: int, *, body_only: bool) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    allowed = {
        (r, c)
        for r in range(1 if body_only else 0, h)
        for c in range(w)
        if grid[r][c] == color
    }
    result = []
    while allowed:
        start = next(iter(allowed))
        allowed.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIR4:
                nxt = (r + dr, c + dc)
                if nxt in allowed:
                    allowed.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(tuple(sorted(component)))
    return result


def _different_color_adjacency(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(1, h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < h and cc < w and grid[rr][cc] not in (0, value):
                    return True
    return False


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    g = _coerce_grid(grid)
    h, w = len(g), len(g[0])
    if not (8 <= h <= 10 and 10 <= w <= 13):
        errors.append(f"dimensions must be within 8..10 x 10..13, found {h}x{w}")

    markers = [(c, g[0][c]) for c in range(w) if g[0][c] != 0]
    guide = markers[0][1] if len(markers) == 1 else None
    marker_col = markers[0][0] if len(markers) == 1 else None
    if len(markers) != 1:
        errors.append(f"expected exactly one non-zero top-row marker, found {len(markers)}")

    body_colors = sorted({value for row in g[1:] for value in row if value != 0})
    if len(body_colors) != 3:
        errors.append(f"expected exactly three body colors, found {body_colors}")
    if guide is not None and guide not in body_colors:
        errors.append(f"guide color {guide} is absent from the body")

    body_objects: dict[int, dict[str, Any]] = {}
    for color in body_colors:
        components = _components_for_color(g, color, body_only=True)
        if len(components) != 1:
            errors.append(f"body color {color} must form one 4-connected component; found {len(components)}")
            continue
        cells = components[0]
        body_objects[color] = {
            "color": color,
            "cells": cells,
            "cell_count": len(cells),
            "bbox": _bbox(cells),
            "shape": _shape_name(cells),
        }

    target = body_objects.get(guide) if guide is not None else None
    if target is not None:
        r1, c1, r2, c2 = target["bbox"]
        target["zone"] = _zone_for_bbox(target["bbox"], w)
        target["bbox_intruder"] = any(
            g[r][c] not in (0, guide)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        )
        target["raw_crop"] = [list(row[c1:c2 + 1]) for row in g[r1:r2 + 1]]

    return {
        "errors": errors,
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "guide": guide,
        "marker_col": marker_col,
        "body_colors": body_colors,
        "body_objects": body_objects,
        "target": target,
        "different_color_adjacency": _different_color_adjacency(g),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    target = facts["target"]
    if target is None or target["shape"] not in TARGET_SHAPE_SET:
        raise ValueError("guide-selected body object is not a declared target_shape")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "marker_col": facts["marker_col"],
        "guide": facts["guide"],
        "target_shape": target["shape"],
        "target_zone": target["zone"],
        "bbox_intruder": target["bbox_intruder"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    g = facts["grid"]
    target = facts["target"]
    if any(value != 0 for value in g[1]):
        errors.append("row 1 must remain blank below the guide strip")
    if any(value != 0 for value in g[-1]):
        errors.append("last row must remain blank")
    if target is None:
        errors.append("missing guide-selected target object")
    else:
        r1, c1, r2, c2 = target["bbox"]
        if r2 == r1 or c2 == c1:
            errors.append("target bbox must span at least two rows and two columns")
        if target["shape"] not in TARGET_SHAPE_SET:
            errors.append(f"target shape {target['shape']!r} is outside the declared target bank")
        outside = [
            obj for color, obj in facts["body_objects"].items()
            if color != facts["guide"]
            and any(not (r1 <= r <= r2 and c1 <= c <= c2) for r, c in obj["cells"])
        ]
        if not outside:
            errors.append("at least one distractor must extend outside the target bbox")
        if len(target["raw_crop"]) >= facts["grid_h"] and len(target["raw_crop"][0]) >= facts["grid_w"]:
            errors.append("target crop must be smaller than the input")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    if requested and not errors:
        observed = observe_overrides(g)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    facts = _analyze(grid)
    reasons = self_check(grid)
    if reasons:
        return reasons
    target = facts["target"]
    assert target is not None
    if (facts["grid_h"], facts["grid_w"]) not in CANONICAL_DIMENSIONS:
        reasons.append("dimension pair is outside the four observed canonical profiles")
    if facts["marker_col"] != 0:
        reasons.append("canonical guide markers occupy column 0")
    if target["bbox_intruder"]:
        reasons.append("canonical target bboxes contain no other color")
    distractor_shapes = tuple(sorted(
        obj["shape"] for color, obj in facts["body_objects"].items()
        if color != facts["guide"]
    ))
    if target["shape"] not in TARGET_SHAPE_SET:
        reasons.append("target morphology is outside canonical target support")
    if any(shape not in CANONICAL_DISTRACTOR_SHAPES for shape in distractor_shapes):
        reasons.append(f"distractor morphology is outside canonical support: {distractor_shapes}")
    signature = (target["shape"], distractor_shapes)
    if signature not in CANONICAL_ROLE_SIGNATURES:
        reasons.append(f"linked role/morphology signature {signature!r} was not demonstrated")
    if facts["different_color_adjacency"]:
        reasons.append("canonical objects are separated by background")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"] or facts["target"] is None:
        raise ValueError("invalid guide-color crop scene: " + "; ".join(facts["errors"]))
    return deepcopy(facts["target"]["raw_crop"])


def _crop_for_color(grid, color: int, *, mask_other: bool = False) -> list[list[int]]:
    g = _coerce_grid(grid)
    cells = [(r, c) for r in range(1, len(g)) for c in range(len(g[0])) if g[r][c] == color]
    if not cells:
        return [[0]]
    r1, c1, r2, c2 = _bbox(cells)
    crop = [list(row[c1:c2 + 1]) for row in g[r1:r2 + 1]]
    if mask_other:
        return [[value if value == color else 0 for value in row] for row in crop]
    return crop


def _object_rival(grid, key) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"] or not facts["body_objects"]:
        return [[0]]
    obj = key(list(facts["body_objects"].values()))
    return _crop_for_color(facts["grid"], obj["color"])


def _rival_leftmost(grid):
    return _object_rival(grid, lambda objs: min(objs, key=lambda obj: (obj["bbox"][1], obj["bbox"][0], obj["color"])))


def _rival_topmost(grid):
    return _object_rival(grid, lambda objs: min(objs, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"])))


def _rival_largest(grid):
    return _object_rival(grid, lambda objs: max(objs, key=lambda obj: (obj["cell_count"], -obj["color"])))


def _rival_mask_non_guide(grid):
    facts = _analyze(grid)
    if facts["guide"] is None:
        return [[0]]
    return _crop_for_color(facts["grid"], facts["guide"], mask_other=True)


def _rival_column_zero_guide(grid):
    g = _coerce_grid(grid)
    return _crop_for_color(g, g[0][0]) if g and g[0] and g[0][0] != 0 else [[0]]


def _rival_marker_cell(grid):
    facts = _analyze(grid)
    return [[facts["guide"] or 0]]


def _rival_whole_body_bbox(grid):
    g = _coerce_grid(grid)
    cells = [(r, c) for r in range(1, len(g)) for c in range(len(g[0])) if g[r][c] != 0]
    if not cells:
        return [[0]]
    r1, c1, r2, c2 = _bbox(cells)
    return [list(row[c1:c2 + 1]) for row in g[r1:r2 + 1]]


def _rival_shape_priority(grid):
    facts = _analyze(grid)
    if facts["errors"] or not facts["body_objects"]:
        return [[0]]
    ranked = [
        (MORPHOLOGY_PRIORITY_RANK[obj["shape"]], obj["color"])
        for obj in facts["body_objects"].values()
        if obj["shape"] in MORPHOLOGY_PRIORITY_RANK
    ]
    if not ranked:
        return [[0]]
    _, color = min(ranked)
    return _crop_for_color(facts["grid"], color)


SEMANTIC_RIVALS = {
    "leftmost_object": _rival_leftmost,
    "topmost_object": _rival_topmost,
    "largest_object": _rival_largest,
    "mask_non_guide_inside_bbox": _rival_mask_non_guide,
    "guide_only_from_column_zero": _rival_column_zero_guide,
    "return_marker_cell": _rival_marker_cell,
    "crop_all_body_objects": _rival_whole_body_bbox,
    "shape_priority_morphology": _rival_shape_priority,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "mask_non_guide_inside_bbox": _rival_mask_non_guide,
    "guide_only_from_column_zero": _rival_column_zero_guide,
    "shape_priority_morphology": _rival_shape_priority,
}


def _safe_facts(grid) -> dict[str, Any]:
    try:
        return _analyze(grid)
    except Exception:
        return {"errors": ["analysis failed"], "target": None, "body_objects": {}}


def _target_not_largest(grid) -> bool:
    facts = _safe_facts(grid)
    target = facts.get("target")
    if facts.get("errors") or not target:
        return False
    return target["cell_count"] < max(obj["cell_count"] for obj in facts["body_objects"].values())


def _target_not_leftmost(grid) -> bool:
    facts = _safe_facts(grid)
    target = facts.get("target")
    if facts.get("errors") or not target:
        return False
    return target["bbox"][1] > min(obj["bbox"][1] for obj in facts["body_objects"].values())


def _target_not_topmost(grid) -> bool:
    facts = _safe_facts(grid)
    target = facts.get("target")
    if facts.get("errors") or not target:
        return False
    return target["bbox"][0] > min(obj["bbox"][0] for obj in facts["body_objects"].values())


def _target_not_shape_priority(grid) -> bool:
    facts = _safe_facts(grid)
    target = facts.get("target")
    if facts.get("errors") or not target:
        return False
    ranked = [
        (MORPHOLOGY_PRIORITY_RANK[obj["shape"]], obj["color"])
        for obj in facts["body_objects"].values()
        if obj["shape"] in MORPHOLOGY_PRIORITY_RANK
    ]
    return bool(ranked and min(ranked)[1] != facts.get("guide"))


SEMANTIC_WITNESSES = {
    "marker_not_column_zero": lambda grid: (_safe_facts(grid).get("marker_col") not in (None, 0)),
    "bbox_contains_other_color": lambda grid: bool(
        _safe_facts(grid).get("target") and _safe_facts(grid)["target"]["bbox_intruder"]
    ),
    "target_not_largest": _target_not_largest,
    "target_not_leftmost": _target_not_leftmost,
    "target_not_topmost": _target_not_topmost,
    "target_not_shape_priority": _target_not_shape_priority,
}
WITNESS_RIVALS = {
    "marker_not_column_zero": ["guide_only_from_column_zero"],
    "bbox_contains_other_color": ["mask_non_guide_inside_bbox"],
    "target_not_largest": ["largest_object"],
    "target_not_leftmost": ["leftmost_object"],
    "target_not_topmost": ["topmost_object"],
    "target_not_shape_priority": ["shape_priority_morphology"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} input is invalid: {exc}")
            continue
        if expected != _coerce_grid(pair["output"]):
            reasons.append(f"pair {index} output disagrees with the guide-color crop rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == _coerce_grid(pair["output"]) for pair in demos):
            if rival(query["input"]) != _coerce_grid(query["output"]):
                reasons.append(f"demonstrations permit named rival {name!r} on the query")
            else:
                reasons.append(f"named rival {name!r} survives the entire lesson")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % 12


SCHEDULE_PROFILES = tuple(range(12))


def _scheduled_target_shape(sample_index: int) -> str:
    # Every four consecutive examples include tee4; ring8 remains reachable
    # at a measured 1/20 default rate in every band.
    if sample_index % 20 == 19:
        return "ring8"
    return ("tee4", "c5", "p5", "stair5")[sample_index % 4]


def _target_position(height: int, width: int, shape_name: str, zone: str, sample_index: int) -> tuple[int, int]:
    shape_h, shape_w = _shape_dims(SHAPE_PROFILES[shape_name])
    top = min(2 + (sample_index % 3), height - shape_h - 1)
    if zone == "left":
        left = 1
    elif zone == "center":
        left = (width - shape_w) // 2
    elif zone == "right":
        left = width - shape_w - 1
    else:
        raise ValueError(f"unknown target zone {zone!r}")
    if _zone_for_bbox((top, left, top + shape_h - 1, left + shape_w - 1), width) != zone:
        raise ValueError(f"cannot realize target_zone={zone!r} in {height}x{width}")
    return top, left


def _cells_at(shape_name: str, top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + dr, left + dc) for dr, dc in SHAPE_PROFILES[shape_name])


def _place_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for r, c in cells:
        if grid[r][c] != 0:
            raise ValueError(f"placement overlap at {(r, c)}")
        grid[r][c] = color


def _placement_candidates(
    height: int,
    width: int,
    shape_name: str,
    occupied: set[tuple[int, int]],
    target_bbox: tuple[int, int, int, int],
) -> list[tuple[int, int, tuple[tuple[int, int], ...]]]:
    shape_h, shape_w = _shape_dims(SHAPE_PROFILES[shape_name])
    candidates = []
    for top in range(2, height - shape_h):  # preserve row 1 and the last row
        for left in range(0, width - shape_w + 1):
            cells = _cells_at(shape_name, top, left)
            if any(cell in occupied for cell in cells):
                continue
            if any(
                target_bbox[0] <= r <= target_bbox[2]
                and target_bbox[1] <= c <= target_bbox[3]
                for r, c in cells
            ):
                continue
            candidates.append((top, left, cells))
    return candidates


def _choose_external_placement(
    height: int,
    width: int,
    shape_name: str,
    occupied: set[tuple[int, int]],
    target_bbox: tuple[int, int, int, int],
    desired: tuple[int, int],
    rng,
) -> tuple[tuple[int, int], ...]:
    candidates = _placement_candidates(height, width, shape_name, occupied, target_bbox)
    if not candidates:
        raise ValueError(f"no lawful placement for distractor shape {shape_name!r}")
    rng.shuffle(candidates)
    top, left, cells = min(
        candidates,
        key=lambda item: (abs(item[0] - desired[0]) + abs(item[1] - desired[1]), item[0], item[1]),
    )
    del top, left
    return cells


def _validate_call(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    """Reject coercible metadata and controls before they reach ``gen_ctx``."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    expected_types = {"int": int, "color": int, "enum": str, "bool": bool}
    for axis, value in overrides.items():
        expected = expected_types[AXES[axis]["type"]]
        if type(value) is not expected:
            raise TypeError(
                f"{axis} must be a literal {expected.__name__}, not {type(value).__name__}"
            )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule owns output."""
    _validate_call(seed, sample_index, difficulty, overrides)
    user_overrides = dict(overrides)

    phase_ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=f"{TASK_ID}::schedule",
        difficulty=difficulty,
        overrides={},
    )
    dim_phase = phase_ctx.draw_int("dim_phase", 0, len(CANONICAL_DIMENSIONS) - 1)
    color_phase = phase_ctx.draw_int("color_phase", 0, 8)
    zone_phase = phase_ctx.draw_int("zone_phase", 0, 2)

    scheduled_h, scheduled_w = CANONICAL_DIMENSIONS[(dim_phase + sample_index) % len(CANONICAL_DIMENSIONS)]
    band_offset = {"easy": 0, "medium": 3, "hard": 6}.get(difficulty, 0)
    scheduled = {
        "grid_h": scheduled_h,
        "grid_w": scheduled_w,
        "marker_col": (0, 2, 5, 9)[sample_index % 4],
        "guide": 1 + ((color_phase + sample_index + band_offset) % 9),
        "target_shape": _scheduled_target_shape(sample_index),
        "target_zone": TARGET_ZONES[(zone_phase + sample_index) % 3],
        "bbox_intruder": sample_index % 4 == 3,
    }
    effective = {**scheduled, **user_overrides}

    # Construct this context last: override/default provenance audits inspect
    # the most recent GenCtx and every declared exact axis is recorded here.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 8, 10)
    width = ctx.draw_int("grid_w", 10, 13)
    marker_col = ctx.draw_int("marker_col", 0, 9)
    guide = ctx.draw_color("guide", exclude={0})
    target_shape = ctx.draw_choice("target_shape", TARGET_SHAPES)
    target_zone = ctx.draw_choice("target_zone", TARGET_ZONES)
    bbox_intruder = ctx.draw_choice("bbox_intruder", (False, True))

    grid = full_grid(height, width, 0)
    grid[0][marker_col] = guide
    top, left = _target_position(height, width, target_shape, target_zone, sample_index)
    target_cells = _cells_at(target_shape, top, left)
    _place_cells(grid, target_cells, guide)
    occupied = set(target_cells)
    target_bbox = _bbox(target_cells)

    color_rng = ctx.draw_rng("distractor_colors")
    distractor_colors = [color for color in range(1, 10) if color != guide]
    color_rng.shuffle(distractor_colors)
    color_a, color_b = distractor_colors[:2]
    layout_rng = ctx.draw_rng("distractor_layout")

    if bbox_intruder:
        empty_in_bbox = [
            (r, c)
            for r in range(target_bbox[0], target_bbox[2] + 1)
            for c in range(target_bbox[1], target_bbox[3] + 1)
            if (r, c) not in occupied
        ]
        if not empty_in_bbox:
            raise ValueError(f"target_shape={target_shape!r} has no empty bbox cell for bbox_intruder")
        intruder = empty_in_bbox[layout_rng.randrange(len(empty_in_bbox))]
        _place_cells(grid, (intruder,), color_a)
        occupied.add(intruder)
        outside_shape = "cross5"
        desired = (2, 0 if target_zone != "left" else width - 3)
        outside_cells = _choose_external_placement(
            height, width, outside_shape, occupied, target_bbox, desired, layout_rng
        )
        _place_cells(grid, outside_cells, color_b)
    else:
        shape_a, shape_b = CANONICAL_DISTRACTORS_BY_TARGET[target_shape]
        # Every four-example lesson role-swaps morphology and color: the guide
        # selects p5 while a higher-priority ring8 distractor is present.  This
        # also remains a decisive count-based counterexample.
        if sample_index % 4 == 2:
            shape_a = "ring8"
        desired_a = (2, 0 if target_zone != "left" else width - 3)
        cells_a = _choose_external_placement(
            height, width, shape_a, occupied, target_bbox, desired_a, layout_rng
        )
        _place_cells(grid, cells_a, color_a)
        occupied.update(cells_a)
        desired_b = (height - 4, width - 3 if target_zone != "right" else 0)
        cells_b = _choose_external_placement(
            height, width, shape_b, occupied, target_bbox, desired_b, layout_rng
        )
        _place_cells(grid, cells_b, color_b)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": user_overrides})
    if errors:
        raise ValueError("constructed invalid guide-color scene: " + "; ".join(errors))
    return [row[:] for row in grid]
