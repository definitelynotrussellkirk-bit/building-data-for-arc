"""Input sampler for ARC task fe0dc9f32b7b, Nested Palette Fill.

The selected Racket rule reads distinct palette colors from column 0.  A
color-8 connected component qualifies as a frame when its bounding box is at
least 3x3 and its component size equals that box's perimeter.  Each zero cell
strictly inside N qualifying boxes is filled with palette[N-1]; depths beyond
the palette stay zero.

The sampler deliberately includes clean nested frames, a third depth beyond a
two-color palette, overfilled nested color-8 objects that fail the selected
size predicate, and a connected non-hollow object whose size still equals its
bounding-box perimeter.  Those cases distinguish the authority from four
plausible shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "fe0dc9f32b7b"
TASK_ID = GENERATOR_ID
RULE_HASH = "5f1e925f80ea"
VERSION = "3.1.0"
SUMMARY = (
    "Column 0 is a top-to-bottom palette. In the body, color-8 objects whose "
    "component size equals their bounding-box perimeter count as rectangular "
    "frames; overfilled lookalikes do not. Fill each zero cell by its number "
    "of strictly containing qualifying frames, leaving depths beyond the "
    "palette unchanged."
)

INVARIANTS = [
    "column 0 begins with two or three distinct non-0/non-8 palette colors and then zeros",
    "column 1 is a zero gap; input palette colors occur nowhere outside column 0",
    "the body is one nested chain: two clean frames, three clean frames, one clean frame around one overfilled non-frame, or one clean frame around one count-qualified warped object",
    "a warped qualifying object swaps one perimeter cell for one interior cell while preserving connectivity, bounding box, and perimeter-sized component count",
    "an optional malformed object contains its complete perimeter plus interior cells and therefore fails the authority's size predicate",
    "all generated scene, dimension, and palette overrides are exact and observable from returned pixels",
]

SCENE_KINDS = ("two_clean", "three_clean", "malformed_inner", "warped_inner")
SCHEDULE_PROFILES = (
    "nested_depth",
    "malformed_object_filter",
    "palette_exhaustion",
)
_SCHEDULE_SCENES = {
    "nested_depth": "warped_inner",
    "malformed_object_filter": "malformed_inner",
    "palette_exhaustion": "three_clean",
}
AXES = {
    "grid_h": {
        "type": "int",
        "default": "11..15; difficulty weights canonical dimensions",
        "valid": "11..15",
    },
    "grid_w": {
        "type": "int",
        "default": "13..17; difficulty weights canonical dimensions",
        "valid": "13..17",
    },
    "palette_size": {
        "type": "int",
        "default": "2..3; palette-exhaustion schedule entries pin 2",
        "valid": "2..3",
    },
    "scene_kind": {
        "type": "str",
        "default": "three-entry lesson schedule spanning all decisive scene families",
        "valid": "|".join(SCENE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0

_ALLOWED_PALETTE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_PROFILES = {
    "c12x14p2": (12, 14, 2),
    "c13x13p3": (13, 13, 3),
    "c14x15p3": (14, 15, 3),
}


def _profile_options(difficulty) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("c12x14p2",) * 6 + ("c13x13p3",) * 2 + ("c14x15p3",)
    if difficulty == "hard":
        return ("c14x15p3",) * 6 + ("c13x13p3",) * 2 + ("c12x14p2",)
    return ("c12x14p2",) * 4 + ("c13x13p3",) * 4 + ("c14x15p3",) * 2


def _weighted_axis(ctx, name: str, values: Iterable, anchor, weight: int):
    options = tuple(values) + (anchor,) * weight
    return ctx.draw_choice(name, options)


def _validate_override_types(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "palette_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
    value = overrides.get("scene_kind")
    if value is not None and type(value) is not str:
        raise ValueError(
            f"scene_kind must be a string, not {type(value).__name__}"
        )


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the deterministic semantic branch for an ordinary draw.

    Lesson assembly consumes consecutive sample indexes.  Cycling the three
    decisive profiles therefore guarantees that every three-demo lesson
    contains a nested-depth example, a malformed-object filter example, and a
    palette-exhaustion example, independent of its starting offset.  Explicit
    axis overrides still take precedence in :func:`generate`.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scene(grid, scene_kind: str, rng) -> None:
    h, w = len(grid), len(grid[0])
    if scene_kind == "three_clean":
        outer_h = outer_w = 11
    elif scene_kind == "malformed_inner":
        outer_h = rng.choice(list(range(9, min(11, h) + 1)))
        outer_w = rng.choice(list(range(9, min(11, w - 2) + 1)))
    else:
        outer_h = rng.choice(list(range(8, min(11, h) + 1)))
        outer_w = rng.choice(list(range(8, min(11, w - 2) + 1)))

    top = rng.randint(0, h - outer_h)
    left = rng.randint(2, w - outer_w)
    bottom = top + outer_h - 1
    right = left + outer_w - 1
    draw_frame(grid, top, left, bottom, right, 8)

    inner = (top + 2, left + 2, bottom - 2, right - 2)
    draw_frame(grid, *inner, 8)
    if scene_kind == "three_clean":
        draw_frame(
            grid,
            top + 4,
            left + 4,
            bottom - 4,
            right - 4,
            8,
        )
    elif scene_kind == "malformed_inner":
        ir0, ic0, ir1, ic1 = inner
        middle = (ir0 + ir1) // 2
        for c in range(ic0 + 1, ic1):
            grid[middle][c] = 8
    elif scene_kind == "warped_inner":
        ir0, ic0, ir1, ic1 = inner
        swaps = (
            ((ir0, ic0 + 1), (ir0 + 1, ic0 + 1)),
            ((ir0, ic1 - 1), (ir0 + 1, ic1 - 1)),
            ((ir1, ic0 + 1), (ir1 - 1, ic0 + 1)),
            ((ir1, ic1 - 1), (ir1 - 1, ic1 - 1)),
            ((ir0 + 1, ic0), (ir0 + 1, ic0 + 1)),
            ((ir1 - 1, ic0), (ir1 - 1, ic0 + 1)),
            ((ir0 + 1, ic1), (ir0 + 1, ic1 - 1)),
            ((ir1 - 1, ic1), (ir1 - 1, ic1 - 1)),
        )
        removed, added = rng.choice(swaps)
        grid[removed[0]][removed[1]] = 0
        grid[added[0]][added[1]] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_name = ctx.draw_choice("curriculum_profile", _profile_options(difficulty))
    target_h, target_w, target_palette = _CANONICAL_PROFILES[profile_name]
    h = _weighted_axis(ctx, "grid_h", range(11, 16), target_h, 20)
    w = _weighted_axis(ctx, "grid_w", range(13, 18), target_w, 20)
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    if "palette_size" not in overrides and scheduled_profile == "palette_exhaustion":
        palette_size = ctx.draw_choice("palette_size", (2,))
    else:
        palette_size = _weighted_axis(
            ctx, "palette_size", range(2, 4), target_palette, 8
        )

    scene_options = list(SCENE_KINDS)
    if difficulty == "easy":
        scene_options += ["two_clean"] * 2
    elif difficulty == "hard":
        scene_options += ["three_clean", "malformed_inner"] * 2
    if "scene_kind" in overrides:
        scene_kind = ctx.draw_choice("scene_kind", tuple(scene_options))
    else:
        scene_kind = ctx.draw_choice(
            "scene_kind", (_SCHEDULE_SCENES[scheduled_profile],)
        )

    grid = full_grid(h, w, 0)
    palette_colors = ctx.draw_rng("palette_colors").sample(
        list(_ALLOWED_PALETTE_COLORS), palette_size
    )
    for row, color in enumerate(palette_colors):
        grid[row][0] = color
    _draw_scene(grid, scene_kind, ctx.draw_rng("scene_layout"))
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _palette(grid) -> list[int]:
    return [row[0] for row in grid if row[0] not in (0, 8)]


def _color8_components(grid) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            component: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                component.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(component)
    return components


def _bbox(component: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(component)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _authority_frame(component: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = _bbox(component)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    return (
        height >= 3
        and width >= 3
        and len(component) == 2 * (height + width) - 4
    )


def _clean_frame(component: set[tuple[int, int]]) -> bool:
    return _authority_frame(component) and component == _perimeter(_bbox(component))


def _single_inward_swap(component: set[tuple[int, int]]) -> bool:
    """Recognize the calibrated non-hollow authority-positive component."""
    if not _authority_frame(component) or _clean_frame(component):
        return False
    box = _bbox(component)
    perimeter = _perimeter(box)
    missing = perimeter - component
    added = component - perimeter
    if len(missing) != 1 or len(added) != 1:
        return False
    r0, c0, r1, c1 = box
    r, c = next(iter(added))
    return r0 < r < r1 and c0 < c < c1


def _strictly_contains(
    outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]
) -> bool:
    or0, oc0, or1, oc1 = outer
    ir0, ic0, ir1, ic1 = inner
    return or0 < ir0 and oc0 < ic0 and ir1 < or1 and ic1 < oc1


def _scene_kind(grid) -> str:
    components = _color8_components(grid)
    qualifying = [component for component in components if _authority_frame(component)]
    malformed = [component for component in components if not _authority_frame(component)]
    if len(qualifying) == 2 and not malformed:
        nonclean = [component for component in qualifying if not _clean_frame(component)]
        if not nonclean:
            return "two_clean"
        if len(nonclean) == 1:
            return "warped_inner"
    if len(qualifying) == 3 and not malformed and all(
        _clean_frame(component) for component in qualifying
    ):
        return "three_clean"
    if len(qualifying) == 1 and len(malformed) == 1:
        return "malformed_inner"
    return "other"


def observe_overrides(grid):
    shape = _shape(grid)
    if shape is None:
        raise ValueError("cannot observe axes from a malformed grid")
    return {
        "grid_h": shape[0],
        "grid_w": shape[1],
        "palette_size": len(_palette(grid)),
        "scene_kind": _scene_kind(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    h, w = shape
    errors: list[str] = []
    if not (11 <= h <= 15 and 12 <= w <= 17):
        errors.append("grid dimensions must stay in the canonical 11..15 by 12..17 envelope")
    if any(
        type(value) is not int or not (0 <= value <= 9)
        for row in grid
        for value in row
    ):
        return errors + ["every cell must be an integer ARC color 0..9"]

    column = [row[0] for row in grid]
    palette: list[int] = []
    first_zero = len(column)
    for index, value in enumerate(column):
        if value == 0:
            first_zero = index
            break
        palette.append(value)
    if any(value != 0 for value in column[first_zero:]):
        errors.append("column-0 palette must be contiguous from the top")
    if not (2 <= len(palette) <= 3):
        errors.append("column 0 must begin with exactly two or three palette colors")
    if any(value in (0, 8) for value in palette):
        errors.append("palette colors must exclude 0 and 8")
    if len(set(palette)) != len(palette):
        errors.append("palette colors must be distinct")
    if any(row[1] != 0 for row in grid):
        errors.append("column 1 must remain a zero gap")

    palette_set = set(palette)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if c == 0:
                continue
            if value not in (0, 8):
                if value in palette_set:
                    errors.append("input palette colors may occur only in column 0")
                else:
                    errors.append(f"unexpected body color {value}")
                break
        if errors and errors[-1].startswith(("input palette", "unexpected body")):
            break

    components = _color8_components(grid)
    if not components:
        return errors + ["expected nested color-8 objects"]
    qualifying = [component for component in components if _authority_frame(component)]
    malformed = [component for component in components if not _authority_frame(component)]
    for component in components:
        box = _bbox(component)
        if box[1] < 2:
            errors.append("color-8 objects must stay right of the gap column")
    qualifying_boxes = sorted(
        (_bbox(component) for component in qualifying),
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    if any(
        not _strictly_contains(outer, inner)
        for outer, inner in zip(qualifying_boxes, qualifying_boxes[1:])
    ):
        errors.append("qualifying frames must form one strictly nested chain")

    scene = _scene_kind(grid)
    if scene == "other":
        errors.append(
            "scene must be two clean frames, three clean frames, one clean frame around one malformed object, or one clean frame around one warped qualifying object"
        )
    if scene == "malformed_inner":
        component = malformed[0]
        box = _bbox(component)
        wanted = _perimeter(box)
        if not wanted < component:
            errors.append("malformed object must contain its full perimeter plus interior cells")
        if not qualifying_boxes or not _strictly_contains(qualifying_boxes[0], box):
            errors.append("malformed object must lie strictly inside the clean frame")
    elif malformed:
        errors.append("clean-frame scenes may not contain malformed color-8 objects")
    if scene == "warped_inner":
        warped = [component for component in qualifying if not _clean_frame(component)]
        clean = [component for component in qualifying if _clean_frame(component)]
        if len(warped) != 1 or not _single_inward_swap(warped[0]):
            errors.append(
                "warped qualifying object must swap exactly one perimeter cell for one interior cell"
            )
        if len(clean) != 1 or not _strictly_contains(
            _bbox(clean[0]), _bbox(warped[0])
        ):
            errors.append("warped qualifying object must lie strictly inside one clean frame")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _apply_rule(
    grid,
    *,
    outermost_only: bool = False,
    include_malformed_bboxes: bool = False,
    clamp_palette: bool = False,
    exact_perimeter_only: bool = False,
):
    source = [list(row) for row in grid]
    palette = _palette(source)
    components = _color8_components(source)
    if include_malformed_bboxes:
        boxes = []
        for component in components:
            box = _bbox(component)
            if box[2] - box[0] + 1 >= 3 and box[3] - box[1] + 1 >= 3:
                boxes.append(box)
    elif exact_perimeter_only:
        boxes = [
            _bbox(component)
            for component in components
            if _clean_frame(component)
        ]
    else:
        boxes = [
            _bbox(component)
            for component in components
            if _authority_frame(component)
        ]
    if outermost_only and boxes:
        boxes = [
            max(
                boxes,
                key=lambda box: (box[2] - box[0] + 1)
                * (box[3] - box[1] + 1),
            )
        ]
    boxes.sort()

    output = deepcopy(source)
    for r, row in enumerate(source):
        for c, value in enumerate(row):
            if value != 0:
                continue
            depth = sum(
                r0 < r < r1 and c0 < c < c1
                for r0, c0, r1, c1 in boxes
            )
            if 0 < depth <= len(palette):
                output[r][c] = palette[depth - 1]
            elif depth > len(palette) and palette and clamp_palette:
                output[r][c] = palette[-1]
    return output


def rule_mirror(grid):
    """Supplemental Python mirror of the selected Racket rule."""
    return _apply_rule(grid)


def _outermost_only(grid):
    return _apply_rule(grid, outermost_only=True)


def _all_color8_bboxes(grid):
    return _apply_rule(grid, include_malformed_bboxes=True)


def _clamp_palette(grid):
    return _apply_rule(grid, clamp_palette=True)


def _exact_perimeter_only(grid):
    return _apply_rule(grid, exact_perimeter_only=True)


def _nested_depth_witness(grid) -> bool:
    return (
        _scene_kind(grid) in {"two_clean", "warped_inner"}
        and rule_mirror(grid) != _outermost_only(grid)
    )


def _malformed_filter_witness(grid) -> bool:
    return (
        _scene_kind(grid) == "malformed_inner"
        and rule_mirror(grid) != _all_color8_bboxes(grid)
    )


def _palette_exhaustion_witness(grid) -> bool:
    return (
        _scene_kind(grid) == "three_clean"
        and len(_palette(grid)) == 2
        and rule_mirror(grid) != _clamp_palette(grid)
    )


def _size_equals_perimeter_witness(grid) -> bool:
    return (
        _scene_kind(grid) == "warped_inner"
        and rule_mirror(grid) != _exact_perimeter_only(grid)
    )


SEMANTIC_WITNESSES = {
    "nested_depth": _nested_depth_witness,
    "malformed_object_filter": _malformed_filter_witness,
    "palette_exhaustion": _palette_exhaustion_witness,
    "size_equals_perimeter": _size_equals_perimeter_witness,
}
SEMANTIC_RIVALS = {
    "outermost_only": _outermost_only,
    "all_color8_bboxes": _all_color8_bboxes,
    "clamp_palette": _clamp_palette,
    "exact_perimeter_only": _exact_perimeter_only,
}
WITNESS_RIVALS = {
    "nested_depth": ["outermost_only"],
    "malformed_object_filter": ["all_color8_bboxes"],
    "palette_exhaustion": ["clamp_palette"],
    "size_equals_perimeter": ["exact_perimeter_only"],
}
CANONICAL_SHORTCUTS = {
    "exact_perimeter_only": _exact_perimeter_only,
    "clamp_palette": _clamp_palette,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return the declared wrong rules still able to alter the query answer.

    A rival is harmless for one lesson when a demonstration already refutes it
    or when it happens to agree with the authority on that lesson's query.  A
    surviving rival that changes the query is an actual identifiability defect.
    """
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} survives every demonstration and changes the query answer"
                )
    return reasons
