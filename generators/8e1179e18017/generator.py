"""Generator for ARC task 8e1179e18017.

Find the blue components, crop each to its bounding box, sort the crops by
component area (smallest first), recolor them cyan, and pack them left-to-right
with one background column between consecutive crops.  The orange component is
a distractor and is never copied to the output.

The generated distribution is deliberately adversarial: a four-step schedule
varies blue scan order so neither forward nor reversed input order explains a
lesson; the area-4 T has a larger bounding box than the area-5 line; every
scene contains an orange distractor; and at least one blue shape is
non-rectangular.  Those properties refute plausible shortcuts without
narrowing the authority-valid input grammar in ``self_check``.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import (
    components,
    components_have_clearance,
    d4_transform,
)

GENERATOR_ID = "8e1179e18017"
TASK_ID = "8e1179e18017"
VERSION = "4.1.0"
RULE_HASH = "a7b22243a1df"

SUMMARY = (
    "Find every 4-connected blue(1) object, normalize its bounding-box crop, "
    "sort the objects by cell area from smallest to largest (normalized shape "
    "breaks an area tie), recolor the object cells cyan(8), and pack the crops "
    "left-to-right, top-aligned, with exactly one background(0) column between "
    "successive crops. Ignore the single orange(7) distractor object."
)

INVARIANTS = [
    "background is colour 0",
    "the input palette is exactly {0, 1, 7}",
    "there are 2..4 separated blue components with distinct areas",
    "there is exactly one separated orange distractor component",
    "only blue components participate in the packed cyan output",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..18 with periodic canonical anchors",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 11..20 with periodic canonical anchors",
        "valid": "11..20",
    },
    "n_blue": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "distractor_area": {
        "type": "int",
        "default": "difficulty-aware 1..8",
        "valid": "1..8",
    },
}

# The four axes are jointly realizable throughout their declared domains.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_PROFILES = {
    "easy": ((9, 11), (9, 12)),
    "medium": ((10, 12), (11, 12)),
    "hard": ((10, 12), (11, 12)),
    None: ((9, 11), (10, 12), (11, 12)),
}
SCHEDULE_PROFILES = tuple(
    f"{scale}:{order}"
    for scale in ("canonical_anchor", "broad")
    for order in ("descending", "ascending", "mixed_a", "mixed_b")
)

# The decisive area-4/area-5 pair is always present.  The T tetromino has
# bbox area 6 while the five-cell line has bbox area 5, so bbox-area ordering
# reverses their true cell-area order.  D4 transforms preserve that fact.
_BLUE_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    scale = "canonical_anchor" if sample_index % 5 == 0 else "broad"
    order = ("descending", "ascending", "mixed_a", "mixed_b")[sample_index % 4]
    return f"{scale}:{order}"


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _canonical_profile(seed: int, sample_index: int, difficulty: Any) -> tuple[int, int]:
    choices = _CANONICAL_PROFILES.get(difficulty, _CANONICAL_PROFILES[None])
    rng = stable_rng(
        seed,
        f"{TASK_ID}|{sample_index}|canonical-profile|{difficulty}",
        VERSION,
    )
    return choices[rng.randrange(len(choices))]


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(cells) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _orange_shape(area: int) -> tuple[tuple[int, int], ...]:
    """Connected compact prefix of a 3x3 raster, for exact area 1..8."""
    order = (
        (0, 0), (0, 1), (1, 0), (1, 1),
        (0, 2), (1, 2), (2, 0), (2, 1),
    )
    return _normalize(order[:area])


def _random_composition(total: int, slots: int, rng) -> list[int]:
    """Deterministically split nonnegative ``total`` across ``slots`` bins."""
    result = [0] * slots
    for _ in range(total):
        result[rng.randrange(slots)] += 1
    return result


def _shelf_pack(shapes, h: int, w: int, rng, *, random_breaks: bool):
    """Pack shapes in order with a one-cell moat and randomized slack.

    Because rows and positions preserve the supplied order, row-major component
    scan order is exactly the supplied order as well.
    """
    rows: list[list[tuple[int, tuple[tuple[int, int], ...], int, int]]] = []
    current: list[tuple[int, tuple[tuple[int, int], ...], int, int]] = []
    current_width = 0
    current_height = 0
    row_heights: list[int] = []

    for color, cells in shapes:
        sh, sw = _shape_dims(cells)
        required = sw if not current else 1 + sw
        early_break = current and random_breaks and rng.random() < 0.35
        if current and (current_width + required > w or early_break):
            rows.append(current)
            row_heights.append(current_height)
            current = []
            current_width = 0
            current_height = 0
            required = sw
        if sw > w:
            return None
        current.append((color, cells, sh, sw))
        current_width += required
        current_height = max(current_height, sh)
    if current:
        rows.append(current)
        row_heights.append(current_height)

    base_h = sum(row_heights) + max(0, len(rows) - 1)
    if base_h > h:
        return None

    vertical_slack = _random_composition(h - base_h, len(rows) + 1, rng)
    placements = []
    r0 = vertical_slack[0]
    for row_index, row in enumerate(rows):
        base_w = sum(item[3] for item in row) + max(0, len(row) - 1)
        horizontal_slack = _random_composition(w - base_w, len(row) + 1, rng)
        c0 = horizontal_slack[0]
        for item_index, (color, cells, sh, sw) in enumerate(row):
            placements.append((color, cells, r0, c0))
            c0 += sw + 1 + horizontal_slack[item_index + 1]
        r0 += row_heights[row_index] + 1 + vertical_slack[row_index + 1]
    return placements


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list grid"], "facts": {}}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged or non-list row"], "facts": {}}
    if any(type(value) is not int for row in grid for value in row):
        errors.append("all cells must be integers")
        return {"errors": errors, "facts": {}}

    palette = sorted({value for row in grid for value in row})
    invalid = [value for value in palette if value not in (0, 1, 7)]
    if invalid:
        errors.append(f"unexpected colors: {invalid}")
    if 0 not in palette:
        errors.append("background color 0 is absent")

    blue = components(grid, colors={1}, same_color=True)
    orange = components(grid, colors={7}, same_color=True)
    all_objects = components(grid, colors={1, 7}, same_color=True)
    if not (2 <= len(blue) <= 4):
        errors.append(f"expected 2..4 blue components, got {len(blue)}")
    if len(orange) != 1:
        errors.append(f"expected exactly one orange component, got {len(orange)}")
    blue_areas = [len(comp["cells"]) for comp in blue]
    if len(blue_areas) != len(set(blue_areas)):
        errors.append(f"blue component areas must be distinct, got {blue_areas}")
    if all_objects and not components_have_clearance(grid, all_objects, diagonal=False):
        errors.append("distinct objects touch cardinally")

    facts: dict[str, Any] = {
        "grid_h": len(grid),
        "grid_w": w,
        "palette": palette,
        "blue": blue,
        "orange": orange,
        "blue_areas_scan": blue_areas,
        "blue_bbox_areas_scan": [
            (comp["bbox"][2] - comp["bbox"][0] + 1)
            * (comp["bbox"][3] - comp["bbox"][1] + 1)
            for comp in blue
        ],
        "distractor_area": len(orange[0]["cells"]) if len(orange) == 1 else None,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid input grammar; curriculum witnesses live elsewhere."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_blue": len(facts["blue"]),
        "distractor_area": facts["distractor_area"],
    }


def _entry(comp) -> tuple[tuple[tuple[int, int], ...], int, int, int, str]:
    cells = _normalize(comp["cells"])
    sh, sw = _shape_dims(cells)
    return cells, sh, sw, len(cells), repr(cells)


def _pack_entries(entries) -> list[list[int]]:
    if not entries:
        return [[0]]
    out_h = max(entry[1] for entry in entries)
    out_w = sum(entry[2] for entry in entries) + len(entries) - 1
    output = full_grid(out_h, out_w, 0)
    cur_c = 0
    for cells, _sh, sw, _area, _key in entries:
        for r, c in cells:
            output[r][cur_c + c] = 8
        cur_c += sw + 1
    return output


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket is authoritative."""
    blue = components(grid, colors={1}, same_color=True)
    entries = sorted((_entry(comp) for comp in blue), key=lambda entry: (entry[3], entry[4]))
    return _pack_entries(entries)


def _scan_order_rival(grid):
    blue = components(grid, colors={1}, same_color=True)
    return _pack_entries([_entry(comp) for comp in blue])


def _reverse_scan_order_rival(grid):
    blue = components(grid, colors={1}, same_color=True)
    return _pack_entries([_entry(comp) for comp in reversed(blue)])


def _bbox_area_rival(grid):
    blue = components(grid, colors={1}, same_color=True)
    entries = [_entry(comp) for comp in blue]
    entries.sort(key=lambda entry: (entry[1] * entry[2], entry[4]))
    return _pack_entries(entries)


def _all_nonzero_rival(grid):
    participants = components(grid, colors={1, 7}, same_color=True)
    entries = sorted((_entry(comp) for comp in participants), key=lambda entry: (entry[3], entry[4]))
    return _pack_entries(entries)


def _filled_bbox_rival(grid):
    blue = components(grid, colors={1}, same_color=True)
    entries = []
    for comp in blue:
        cells, sh, sw, area, key = _entry(comp)
        filled = tuple((r, c) for r in range(sh) for c in range(sw))
        entries.append((filled, sh, sw, area, key))
    entries.sort(key=lambda entry: (entry[3], entry[4]))
    return _pack_entries(entries)


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _analyze(grid)["facts"]
    if facts["palette"] != [0, 1, 7]:
        reasons.append(f"canonical palette is [0, 1, 7], found {facts['palette']}")
    if not (9 <= facts["grid_h"] <= 18 and 11 <= facts["grid_w"] <= 20):
        reasons.append(
            f"grid profile {(facts['grid_h'], facts['grid_w'])} is outside the "
            "canonical-linked generator envelope"
        )
    return reasons


def _lawful_witness(predicate: Callable[[dict[str, Any]], bool]):
    def check(grid):
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(predicate(analysis["facts"]))

    return check


def _official_area_order(facts):
    return sorted(range(len(facts["blue"])), key=lambda i: facts["blue_areas_scan"][i])


def _bbox_area_order(facts):
    return sorted(
        range(len(facts["blue"])),
        key=lambda i: (facts["blue_bbox_areas_scan"][i], repr(facts["blue"][i]["norm"])),
    )


SEMANTIC_WITNESSES = {
    "scan_order_refutes_input_order": _lawful_witness(
        lambda facts: facts["blue_areas_scan"] != sorted(facts["blue_areas_scan"])
    ),
    "reverse_scan_order_refuted": _lawful_witness(
        lambda facts: list(reversed(facts["blue_areas_scan"]))
        != sorted(facts["blue_areas_scan"])
    ),
    "bbox_area_order_conflict": _lawful_witness(
        lambda facts: _official_area_order(facts) != _bbox_area_order(facts)
    ),
    "orange_distractor_must_be_ignored": _lawful_witness(
        lambda facts: facts["distractor_area"] is not None
    ),
    "nonrectangular_shape_refutes_filled_bbox": _lawful_witness(
        lambda facts: any(
            len(comp["cells"])
            < (comp["bbox"][2] - comp["bbox"][0] + 1)
            * (comp["bbox"][3] - comp["bbox"][1] + 1)
            for comp in facts["blue"]
        )
    ),
}

LESSON_COMPETITORS = {
    "scan_order_pack": _scan_order_rival,
    "reverse_scan_order_pack": _reverse_scan_order_rival,
    "bounding_box_area_sort": _bbox_area_rival,
    "all_nonzero_objects": _all_nonzero_rival,
    "fill_each_bounding_box": _filled_bbox_rival,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
WITNESS_RIVALS = {
    "scan_order_refutes_input_order": ["scan_order_pack"],
    "reverse_scan_order_refuted": ["reverse_scan_order_pack"],
    "bbox_area_order_conflict": ["bounding_box_area_sort"],
    "orange_distractor_must_be_ignored": ["all_nonzero_objects"],
    "nonrectangular_shape_refutes_filled_bbox": ["fill_each_bounding_box"],
}
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if self_check(demo.get("input")):
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        if rule_mirror(demo["input"]) != demo.get("output"):
            reasons.append(f"demo {index} output does not match area-sorted blue packing")
    if self_check(query.get("input")):
        reasons.append("query input is outside the task grammar")
        return reasons
    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    official = rule_mirror(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_blue": len(facts["blue"]),
        "blue_areas_scan": facts["blue_areas_scan"],
        "blue_bbox_areas_scan": facts["blue_bbox_areas_scan"],
        "distractor_area": facts["distractor_area"],
        "output_h": len(official),
        "output_w": len(official[0]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)

    effective = dict(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile.startswith("canonical_anchor:"):
        anchor_h, anchor_w = _canonical_profile(seed, sample_index, difficulty)
        effective.setdefault("grid_h", anchor_h)
        effective.setdefault("grid_w", anchor_w)

    order_profile = profile.split(":", 1)[1]
    if order_profile.startswith("mixed") and "n_blue" not in effective:
        effective["n_blue"] = 4 if difficulty == "hard" else 3

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", 9, 18)
    w = ctx.draw_int_diff("grid_w", 11, 20)
    n_blue = ctx.draw_int_diff("n_blue", 2, 4)
    distractor_area = ctx.draw_int_diff("distractor_area", 1, 8)
    rng = ctx.draw_rng("shape-orientation-and-placement")

    ascending_areas = ({2: (4, 5), 3: (3, 4, 5), 4: (3, 4, 5, 6)})[n_blue]
    if order_profile == "descending":
        blue_areas = tuple(reversed(ascending_areas))
    elif order_profile == "ascending":
        blue_areas = ascending_areas
    elif order_profile == "mixed_a":
        blue_areas = {2: (5, 4), 3: (4, 5, 3), 4: (4, 6, 3, 5)}[n_blue]
    else:
        blue_areas = {2: (4, 5), 3: (5, 3, 4), 4: (5, 3, 6, 4)}[n_blue]
    orange_base = _orange_shape(distractor_area)

    # Try varied D4 orientations first; the compact fixed orientation is a
    # deterministic last resort, so all declared override combinations return.
    for attempt in range(64):
        blue_shapes = []
        for index, area in enumerate(blue_areas):
            code = rng.randrange(8) if attempt < 63 else 0
            blue_shapes.append((1, d4_transform(_BLUE_SHAPES[area], code)))
        orange_code = rng.randrange(8) if attempt < 63 else 0
        orange = (7, d4_transform(orange_base, orange_code))
        insert_at = rng.randrange(len(blue_shapes) + 1) if attempt < 63 else len(blue_shapes)
        shapes = blue_shapes[:insert_at] + [orange] + blue_shapes[insert_at:]
        placements = _shelf_pack(
            shapes, h, w, rng, random_breaks=attempt < 63
        )
        if placements is None:
            continue
        grid = full_grid(h, w, 0)
        for color, cells, r0, c0 in placements:
            for dr, dc in cells:
                grid[r0 + dr][c0 + dc] = color
        errors = self_check(grid)
        if not errors:
            return grid

    raise ValueError(
        f"could not realize lawful layout for h={h}, w={w}, "
        f"n_blue={n_blue}, distractor_area={distractor_area}"
    )
