"""Canonical-anchored generator for ARC task 7468f01a / b8aea529acfd.

Selected rule: crop the non-zero bounding rectangle, then flip that crop
left-to-right.

The official examples are not arbitrary sparse shapes.  They are padded,
fully occupied two-color rectangles: one majority color fills the body and a
minority color draws an asymmetric motif inside it.  This generator stays in
that visible grammar while varying canvas size, crop size, palette, placement,
and motif geometry. Original profile anchors alternate with compact bodies
whose accent covers an extreme edge. These witnesses distinguish cropping all
nonzero cells from cropping only the majority color, and distinguish explicit
black background from the most frequent canvas color.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8aea529acfd"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "8e26e8f07755"

SUMMARY = (
    "A black canvas contains one padded, completely filled rectangular body "
    "using exactly two foreground colors. One color is the strict majority; "
    "the minority color forms a sparse horizontally asymmetric motif. The "
    "output crops the nonzero bounding rectangle and flips that crop "
    "left-to-right. A period-8 alternating anchor/witness curriculum retains "
    "canonical profiles and teaches explicit black background and all-color cropping."
)

INVARIANTS = [
    "background is 0 and surrounds the nonzero bounding rectangle on all four sides",
    "the nonzero bounding rectangle is completely occupied",
    "exactly two nonzero colors are present and one is a strict majority",
    "the minority-color motif is sparse and horizontally asymmetric, so flip-lr is visible",
    "ordinary generated scenes also break vertical/180-degree symmetry so nearby transform rivals disagree",
    "every two consecutive ordinary draws include a dense edge witness against both canonical-fitting crop shortcuts",
]

# name, band, canvas_h, canvas_w, crop_h, crop_w, majority_color, accent_color
# The original twelve anchors retain all four official input profiles across
# the bands: 12x16 {1,4}, 10x15 {2,8}, 15x17 {3,6}, 17x17 {1,8}.
_PROFILE_ROWS = (
    ("e_12x16_5x5_4_1", "easy",   12, 16, 5, 5, 4, 1),
    ("e_10x15_4x8_8_2", "easy",   10, 15, 4, 8, 8, 2),
    ("e_11x15_4x6_6_3", "easy",   11, 15, 4, 6, 6, 3),
    ("e_12x17_5x7_9_5", "easy",   12, 17, 5, 7, 9, 5),
    ("m_15x17_4x6_6_3", "medium", 15, 17, 4, 6, 6, 3),
    ("m_13x16_5x6_7_1", "medium", 13, 16, 5, 6, 7, 1),
    ("m_14x17_5x8_5_2", "medium", 14, 17, 5, 8, 5, 2),
    ("m_16x17_6x7_9_4", "medium", 16, 17, 6, 7, 9, 4),
    ("h_17x17_7x8_1_8", "hard",   17, 17, 7, 8, 1, 8),
    ("h_16x18_6x8_2_7", "hard",   16, 18, 6, 8, 2, 7),
    ("h_17x18_7x9_3_6", "hard",   17, 18, 7, 9, 3, 6),
    ("h_18x18_8x8_4_9", "hard",   18, 18, 8, 8, 4, 9),
    ("e_dense_8x9_6x7_4_1", "easy",   8,  9, 6, 7, 4, 1),
    ("m_dense_9x10_7x8_5_2", "medium", 9, 10, 7, 8, 5, 2),
    ("h_dense_10x11_8x9_1_8", "hard", 10, 11, 8, 9, 1, 8),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {
    (row[2], row[3], row[4], row[5], row[6], row[7]): row[0]
    for row in _PROFILE_ROWS
}
_DENSE_BY_BAND = {
    "easy": "e_dense_8x9_6x7_4_1",
    "medium": "m_dense_9x10_7x8_5_2",
    "hard": "h_dense_10x11_8x9_1_8",
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS
                if row[1] == band and row[0] not in _DENSE_BY_BAND.values())
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "period-8 alternating anchor/witness curriculum for the selected difficulty band",
        "valid": "e_12x16_5x5_4_1|e_10x15_4x8_8_2|e_11x15_4x6_6_3|e_12x17_5x7_9_5|m_15x17_4x6_6_3|m_13x16_5x6_7_1|m_14x17_5x8_5_2|m_16x17_6x7_9_4|h_17x17_7x8_1_8|h_16x18_6x8_2_7|h_17x18_7x9_3_6|h_18x18_8x8_4_9|e_dense_8x9_6x7_4_1|m_dense_9x10_7x8_5_2|h_dense_10x11_8x9_1_8",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 8


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if 0.0 <= value <= 1.0:
            return "easy" if value < 1 / 3 else "medium" if value < 2 / 3 else "hard"
    raise ValueError("difficulty must be easy, medium, hard, None, or a number in [0,1]")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Rotate four anchors, each followed by an independently drawn witness.

    Every four consecutive slots contain two witnesses. Holding out any one
    pair therefore leaves a witness among the three demonstrations. Explicit
    scene-profile overrides are input controls and bypass this lesson schedule.
    """
    del seed
    band = _band(difficulty)
    index = int(sample_index)
    if index % 2:
        return _DENSE_BY_BAND[band]
    profiles = _PROFILES_BY_BAND[band]
    return profiles[(index // 2) % len(profiles)]


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
                return ["cells must be literal ARC integers 0..9"]
    return []


def _bbox(grid: list[list[int]] | tuple[tuple[int, ...], ...], background=0):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    ]
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(grid, background=0):
    box = _bbox(grid, background)
    if box is None:
        return []
    r0, c0, r1, c1 = box
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rot180(grid):
    return _flip_ud(_flip_lr(grid))


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def rule_mirror(grid):
    """Python mirror used only for semantic checks; Racket remains authority."""
    crop = _crop(grid)
    if not crop:
        raise ValueError("cannot crop an empty foreground")
    return _flip_lr(crop)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    box = _bbox(grid)
    if box is None:
        return {"errors": ["foreground is missing"], "height": height, "width": width}
    r0, c0, r1, c1 = box
    crop = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    crop_h, crop_w = len(crop), len(crop[0])
    fg = [value for row in crop for value in row if value != 0]
    colors = sorted(set(fg))
    counts = {color: fg.count(color) for color in colors}
    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    majority = sorted_counts[0][0] if sorted_counts else None
    accent = sorted_counts[-1][0] if len(sorted_counts) >= 2 else None
    majority_cells = [(r, c) for r, row in enumerate(grid)
                      for c, value in enumerate(row) if value == majority]
    majority_box = (
        min(r for r, c in majority_cells), min(c for r, c in majority_cells),
        max(r for r, c in majority_cells), max(c for r, c in majority_cells),
    )
    canvas_counts = Counter(value for row in grid for value in row)
    modal_color = min(canvas_counts, key=lambda color: (-canvas_counts[color], color))
    profile = _PROFILE_BY_SIGNATURE.get(
        (height, width, crop_h, crop_w, majority, accent)
    )
    return {
        "errors": [],
        "height": height,
        "width": width,
        "box": box,
        "crop": crop,
        "crop_h": crop_h,
        "crop_w": crop_w,
        "colors": colors,
        "counts": counts,
        "majority": majority,
        "accent": accent,
        "majority_box": majority_box,
        "majority_bbox_spans_content": majority_box == box,
        "background_is_modal": modal_color == 0,
        "scene_profile": profile,
        "filled_bbox": all(value != 0 for row in crop for value in row),
        "padded_all_sides": r0 > 0 and c0 > 0 and r1 < height - 1 and c1 < width - 1,
        "lr_asymmetric": _freeze(crop) != _freeze(_flip_lr(crop)),
        "ud_asymmetric": _freeze(crop) != _freeze(_flip_ud(crop)),
        "rot180_asymmetric": _freeze(crop) != _freeze(_rot180(crop)),
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    area = facts["crop_h"] * facts["crop_w"]
    minority_count = min(facts["counts"].values()) if facts["counts"] else 0
    return {
        "scene_profile": facts["scene_profile"],
        "canvas_h": facts["height"],
        "canvas_w": facts["width"],
        "crop_h": facts["crop_h"],
        "crop_w": facts["crop_w"],
        "fg_palette": tuple(facts["colors"]),
        "filled_bbox": facts["filled_bbox"],
        "padded_all_sides": facts["padded_all_sides"],
        "minority_count": minority_count,
        "minority_fraction": minority_count / area if area else 0.0,
        "lr_asymmetric": facts["lr_asymmetric"],
        "ud_asymmetric": facts["ud_asymmetric"],
        "rot180_asymmetric": facts["rot180_asymmetric"],
        "majority_bbox_spans_content": facts["majority_bbox_spans_content"],
        "background_is_modal": facts["background_is_modal"],
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover the sole exact axis directly from the returned grid."""
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    return {"scene_profile": facts["scene_profile"]}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs while rejecting malformed/rule-hiding scenes."""
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if not facts["padded_all_sides"]:
        errors.append("nonzero bounding rectangle must have background padding on all four sides")
    if not facts["filled_bbox"]:
        errors.append("nonzero bounding rectangle must be completely occupied")
    if len(facts["colors"]) != 2:
        errors.append(f"expected exactly two foreground colors, found {facts['colors']}")
    if len(facts["colors"]) == 2:
        values = sorted(facts["counts"].values())
        if values[0] == values[1]:
            errors.append("foreground colors must have a strict majority/minority relation")
    if not facts["lr_asymmetric"]:
        errors.append("cropped foreground is LR-symmetric; the horizontal flip would be hidden")
    observed = observe_overrides(grid)
    for axis, requested in _meta_overrides(meta).items():
        if axis in AXES and observed.get(axis) != requested:
            errors.append(
                f"override {axis}={requested!r} realized as {observed.get(axis)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked grammar shared by canonical examples and generated lessons."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analysis(grid)
    area = facts["crop_h"] * facts["crop_w"]
    minority = min(facts["counts"].values())
    if facts["crop_h"] < 4 or facts["crop_w"] < 5:
        errors.append(f"canonical crop is at least 4x5, found {facts['crop_h']}x{facts['crop_w']}")
    if facts["crop_h"] > 8 or facts["crop_w"] > 9:
        errors.append(f"canonical-anchored crop is at most 8x9, found {facts['crop_h']}x{facts['crop_w']}")
    if not 2 <= minority <= max(2, area // 3):
        errors.append(
            f"minority motif should be sparse (2..{max(2, area // 3)} cells), found {minority}"
        )
    return errors


def _accent_pattern(sh: int, sw: int, count: int, rng) -> set[tuple[int, int]]:
    cells = [(r, c) for r in range(sh) for c in range(sw)]
    for _ in range(256):
        picked = set(rng.sample(cells, count))
        lr = {(r, sw - 1 - c) for r, c in picked}
        ud = {(sh - 1 - r, c) for r, c in picked}
        rot = {(sh - 1 - r, sw - 1 - c) for r, c in picked}
        # These three inequalities make crop-only, flip-ud, and 180-degree
        # transform shortcuts observably distinct from the selected flip-lr.
        if picked != lr and picked != ud and picked != rot:
            return picked
    # Deterministic asymmetric fallback, valid for every shipped profile.
    fallback = {(0, 0), (1, min(2, sw - 1))}
    r, c = 2 % sh, max(0, sw - 2)
    while len(fallback) < count:
        fallback.add((r, c))
        c = (c + 2) % sw
        if c == 0:
            r = (r + 1) % sh
    return set(list(fallback)[:count])


def _edge_accent_pattern(sh: int, sw: int, count: int, rng, *, edge: int) -> set[tuple[int, int]]:
    """Keep an entire extreme column outside the majority-color bounding box.

    One interior accent has no vertical partner. This constructs UD asymmetry
    directly; the full edge and empty opposite edge also make LR/180 distinct.
    """
    witness_r = rng.choice((0, sh - 1))
    witness_c = rng.randrange(1, sw - 1)
    picked = {(r, edge) for r in range(sh)} | {(witness_r, witness_c)}
    forbidden = (sh - 1 - witness_r, witness_c)
    pool = [(r, c) for r in range(sh) for c in range(1, sw - 1)
            if (r, c) not in picked and (r, c) != forbidden]
    return picked | set(rng.sample(pool, count - len(picked)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    # Ordinary draws teach both canonical-fitting shortcuts in every two-demo
    # window, while retaining all four old profile anchors in each band.
    # Explicit overrides still accept any declared profile.
    effective_overrides = dict(overrides)
    if effective_overrides.get("scene_profile") is None:
        effective_overrides["scene_profile"] = schedule_profile(seed, sample_index, difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    _, h, w, sh, sw, majority, accent = _PROFILE_BY_NAME[profile]

    rng = ctx.draw_rng("layout")
    # Strict padding on all sides. Position is deliberately not an AXIS because
    # it is nuisance variation, not a semantic control callers need to pin.
    rr = rng.randint(1, h - sh - 1)
    rc = rng.randint(1, w - sw - 1)

    area = sh * sw
    lo = max(2, area // 8)
    hi = max(lo, min(area // 3, area // 4 + 1))
    dense = profile in _DENSE_BY_BAND.values()
    if dense:
        lo = max(lo, sh + 1)
    accent_count = rng.randint(lo, hi)
    # Adjacent witness slots use opposite full edges. They therefore cannot
    # collide as duplicate inputs and be skipped by the production sampler.
    edge = (sw - 1) * ((int(sample_index) // 2) % 2)
    accent_cells = (_edge_accent_pattern(sh, sw, accent_count, rng, edge=edge) if dense
                    else _accent_pattern(sh, sw, accent_count, rng))

    grid = full_grid(h, w, 0)
    for dr in range(sh):
        for dc in range(sw):
            grid[rr + dr][rc + dc] = majority
    for dr, dc in accent_cells:
        grid[rr + dr][rc + dc] = accent

    errors = strict_canonical_like(grid)
    if errors:  # Fail closed: a generator defect must not silently emit data.
        raise RuntimeError("internal generated-scene invariant failure: " + "; ".join(errors))
    return grid


def _rival_crop_only(grid):
    return _crop(grid)


def _rival_crop_flip_ud(grid):
    return _flip_ud(_crop(grid))


def _rival_crop_rot180(grid):
    return _rot180(_crop(grid))


def _rival_flip_whole_canvas(grid):
    return _flip_lr(grid)


def _rival_crop_majority_color_bbox(grid):
    facts = _analysis(grid)
    if facts["errors"]:
        return []
    r0, c0, r1, c1 = facts["majority_box"]
    return _flip_lr([list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]])


def _rival_crop_modal_background(grid):
    counts = Counter(value for row in grid for value in row)
    if not counts:
        return []
    background = min(counts, key=lambda color: (-counts[color], color))
    return _flip_lr(_crop(grid, background=background))


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "crop_only": _rival_crop_only,
    "crop_then_flip_ud": _rival_crop_flip_ud,
    "crop_then_rotate_180": _rival_crop_rot180,
    "flip_whole_canvas": _rival_flip_whole_canvas,
    "crop_majority_color_bbox": _rival_crop_majority_color_bbox,
    "crop_modal_background": _rival_crop_modal_background,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("crop_majority_color_bbox", "crop_modal_background")
}

SEMANTIC_WITNESSES = {
    "crop_required": lambda grid: _analysis(grid).get("padded_all_sides") is True,
    "flip_lr_visible": lambda grid: _analysis(grid).get("lr_asymmetric") is True,
    "filled_two_color_body": lambda grid: (
        _analysis(grid).get("filled_bbox") is True
        and len(_analysis(grid).get("colors", ())) == 2
    ),
    "ud_rival_separated": lambda grid: _analysis(grid).get("rot180_asymmetric") is True,
    "rot180_rival_separated": lambda grid: _analysis(grid).get("ud_asymmetric") is True,
    "all_foreground_bounds_required": lambda grid: (
        _analysis(grid).get("majority_bbox_spans_content") is False
    ),
    "explicit_zero_background_required": lambda grid: (
        _analysis(grid).get("background_is_modal") is False
    ),
}
WITNESS_RIVALS = {
    "crop_required": ["flip_whole_canvas"],
    "flip_lr_visible": ["crop_only"],
    "ud_rival_separated": ["crop_then_flip_ud"],
    "rot180_rival_separated": ["crop_then_rotate_180"],
    "filled_two_color_body": ["crop_only"],
    "all_foreground_bounds_required": ["crop_majority_color_bbox"],
    "explicit_zero_background_required": ["crop_modal_background"],
}


def lesson_identifiable(demos, query=None) -> list[str]:
    """Reject lessons where any named wrong rule survives the demos."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            _freeze(competitor(pair["input"])) == _freeze(pair["output"])
            for pair in demos
        )
        if not survives:
            continue
        if query is None:
            reasons.append(f"competitor {name!r} fits every demonstration")
            continue
        if _freeze(competitor(query["input"])) != _freeze(query["output"]):
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
