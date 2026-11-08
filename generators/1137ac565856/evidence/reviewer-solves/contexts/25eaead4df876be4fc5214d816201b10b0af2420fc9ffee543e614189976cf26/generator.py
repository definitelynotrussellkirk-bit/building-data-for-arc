"""Generator for the smallest-enclosing-frame task.

Every input contains two to four complete, strictly nested rectangular
frames in distinct non-red colors and one red marker strictly inside the
innermost frame.  The answer is a solid rectangle whose dimensions and color
come from the smallest frame enclosing the marker.

Defaults retain complete official frame-shape profiles while varying colors,
translations, and marker placement.  The generalized branch varies canvas
size, frame count, nesting gap, outer margin, and marker position without
creating invalid or ambiguous lessons.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "1137ac565856"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "37464b163bd2"
SUMMARY = (
    "Choose the smallest complete rectangular frame that strictly encloses "
    "the red marker, then output a solid rectangle with that frame's size "
    "and color."
)

INVARIANTS = [
    "the background is color 0 and there is exactly one red marker (2)",
    "two to four complete rectangular frames use distinct non-red colors",
    "the frames are strictly nested with at least one-cell coordinate gaps",
    "the red marker is strictly inside every frame",
    "the innermost frame is at least 3x3",
]

MARKER_MODES = ("centered", "off_center")
FRAME_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted feasible draw",
        "valid": "11..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted feasible draw",
        "valid": "11..30",
    },
    "n_frames": {
        "type": "int",
        "default": "difficulty-weighted draw",
        "valid": "2..4",
    },
    "frame_gap": {
        "type": "int",
        "default": "minimum side inset between adjacent frames",
        "valid": "1..3",
    },
    "outer_margin": {
        "type": "int",
        "default": "minimum grid-edge margin around the outer frame",
        "valid": "0..3",
    },
    "marker_mode": {
        "type": "str",
        "default": "easy favors centered; hard favors off-center",
        "valid": "centered|off_center",
    },
}

_INT_DOMAINS = {
    "grid_h": range(11, 31),
    "grid_w": range(11, 31),
    "n_frames": range(2, 5),
    "frame_gap": range(1, 4),
    "outer_margin": range(0, 4),
}
_CANONICAL_PRIOR_P = 0.32

# (grid height, grid width, ordered outer-to-inner frame dimensions).
# Colors, translations inside the canvas, and marker location are nuisance
# variables; the complete linked shape tuples come from all official inputs.
_CANONICAL_PROFILES = (
    (11, 11, ((9, 9), (5, 5))),
    (11, 12, ((9, 10), (5, 5))),
    (13, 13, ((11, 11), (7, 7), (3, 3))),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _clone(grid):
    return [row[:] for row in grid]


def _border_cells(box):
    r0, c0, r1, c1 = box
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def _analysis(grid):
    """Recover all semantic and override facts from a returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a nonempty matrix"]}
    height, width = len(grid), len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return {"errors": ["grid must be rectangular"]}

    errors = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(
                    f"cell ({row},{col}) has invalid ARC value {value!r}"
                )
    if errors:
        return {"height": height, "width": width, "errors": errors}

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    marker = markers[0] if len(markers) == 1 else None
    if marker is None:
        errors.append(f"expected exactly one red marker, found {len(markers)}")

    frames = []
    colors = sorted({value for row in grid for value in row} - {0, 2})
    for color in colors:
        cells = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        }
        r0 = min(row for row, _ in cells)
        c0 = min(col for _, col in cells)
        r1 = max(row for row, _ in cells)
        c1 = max(col for _, col in cells)
        box = (r0, c0, r1, c1)
        if cells != _border_cells(box):
            errors.append(f"color {color} is not exactly one complete frame")
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            errors.append(f"color {color} frame is smaller than 3x3")
        if marker is not None and not (
            r0 < marker[0] < r1 and c0 < marker[1] < c1
        ):
            errors.append(
                f"red marker is not strictly inside frame color {color}"
            )
        frames.append({"color": color, "box": box})

    frames.sort(
        key=lambda frame: (
            (frame["box"][2] - frame["box"][0] + 1)
            * (frame["box"][3] - frame["box"][1] + 1)
        ),
        reverse=True,
    )
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected 2..4 frames, found {len(frames)}")

    side_gaps = []
    for outer, inner in zip(frames, frames[1:]):
        or0, oc0, or1, oc1 = outer["box"]
        ir0, ic0, ir1, ic1 = inner["box"]
        gaps = (ir0 - or0, ic0 - oc0, or1 - ir1, oc1 - ic1)
        if min(gaps) < 1:
            errors.append("frame bounding boxes are not strictly nested")
        side_gaps.extend(gaps)

    outer_margin = None
    frame_gap = None
    frame_shapes = ()
    marker_mode = None
    if frames:
        r0, c0, r1, c1 = frames[0]["box"]
        outer_margin = min(r0, c0, height - 1 - r1, width - 1 - c1)
        frame_shapes = tuple(
            (
                frame["box"][2] - frame["box"][0] + 1,
                frame["box"][3] - frame["box"][1] + 1,
            )
            for frame in frames
        )
    if side_gaps:
        frame_gap = min(side_gaps)
    if marker is not None and frames:
        r0, c0, r1, c1 = frames[-1]["box"]
        center = ((r0 + r1) // 2, (c0 + c1) // 2)
        marker_mode = "centered" if marker == center else "off_center"

    return {
        "height": height,
        "width": width,
        "marker": marker,
        "frames": frames,
        "frame_shapes": frame_shapes,
        "frame_gap": frame_gap,
        "outer_margin": outer_margin,
        "marker_mode": marker_mode,
        "errors": errors,
    }


def profile_signature(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    return (info["height"], info["width"], info["frame_shapes"])


def canonical_profile_signature(grid):
    signature = profile_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def observe_overrides(grid):
    """Derive every declared exact axis from the returned grid."""
    info = _analysis(grid)
    if info["errors"]:
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "n_frames": len(info["frames"]),
        "frame_gap": info["frame_gap"],
        "outer_margin": info["outer_margin"],
        "marker_mode": info["marker_mode"],
    }


def rule_mirror(grid):
    """Independent Python mirror of the smallest-enclosing-frame rule."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid enclosing-frame grid: " + "; ".join(info["errors"]))
    chosen = info["frames"][-1]
    r0, c0, r1, c1 = chosen["box"]
    return full_grid(r1 - r0 + 1, c1 - c0 + 1, chosen["color"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete nested-frame grammar observationally."""
    info = _analysis(grid)
    errors = list(info["errors"])
    if "height" not in info or "width" not in info:
        return errors

    if not 11 <= info["height"] <= 30:
        errors.append(f"grid height {info['height']} outside 11..30")
    if not 11 <= info["width"] <= 30:
        errors.append(f"grid width {info['width']} outside 11..30")
    if info.get("frame_gap") is not None and not 1 <= info["frame_gap"] <= 3:
        errors.append(f"minimum frame gap {info['frame_gap']} outside 1..3")
    if info.get("outer_margin") is not None and not 0 <= info["outer_margin"] <= 3:
        errors.append(f"minimum outer margin {info['outer_margin']} outside 0..3")

    requested = (
        (meta or {}).get("overrides", {})
        if isinstance(meta, dict)
        else {}
    )
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def _validate_requested(overrides):
    for name, value in overrides.items():
        if name in _INT_DOMAINS:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in _INT_DOMAINS[name]
            ):
                domain = _INT_DOMAINS[name]
                raise ValueError(
                    f"override {name}={value!r} outside "
                    f"{domain.start}..{domain.stop - 1}"
                )
        elif name == "marker_mode" and value not in MARKER_MODES:
            raise ValueError(f"unknown marker_mode {value!r}")


def _inner_dimensions(height, width, n_frames, gap, margin):
    shrink = 2 * margin + 2 * gap * (n_frames - 1)
    return height - shrink, width - shrink


def _plan_weight(candidate, difficulty):
    height, width, n_frames, gap, margin, marker_mode = candidate
    if difficulty == "easy":
        weight = 5 if height <= 17 and width <= 17 else 1
        weight *= 4 if n_frames == 2 else (2 if n_frames == 3 else 1)
        weight *= 3 if marker_mode == "centered" else 1
        weight *= 2 if gap == 2 else 1
        return weight
    if difficulty == "hard":
        weight = 4 if height >= 20 and width >= 20 else 1
        weight *= 4 if n_frames == 4 else (2 if n_frames == 3 else 1)
        weight *= 3 if marker_mode == "off_center" else 1
        return weight
    weight = 2 if n_frames == 3 else 1
    weight *= 2 if marker_mode == "off_center" else 1
    return weight


@lru_cache(maxsize=None)
def _candidate_pool(requested_items, difficulty):
    requested = dict(requested_items)
    candidates = []
    weights = []
    for height in _INT_DOMAINS["grid_h"]:
        if "grid_h" in requested and height != requested["grid_h"]:
            continue
        for width in _INT_DOMAINS["grid_w"]:
            if "grid_w" in requested and width != requested["grid_w"]:
                continue
            for n_frames in _INT_DOMAINS["n_frames"]:
                if "n_frames" in requested and n_frames != requested["n_frames"]:
                    continue
                for gap in _INT_DOMAINS["frame_gap"]:
                    if "frame_gap" in requested and gap != requested["frame_gap"]:
                        continue
                    for margin in _INT_DOMAINS["outer_margin"]:
                        if (
                            "outer_margin" in requested
                            and margin != requested["outer_margin"]
                        ):
                            continue
                        inner_h, inner_w = _inner_dimensions(
                            height, width, n_frames, gap, margin
                        )
                        if inner_h < 3 or inner_w < 3:
                            continue
                        for marker_mode in MARKER_MODES:
                            if (
                                "marker_mode" in requested
                                and marker_mode != requested["marker_mode"]
                            ):
                                continue
                            interior_cells = (inner_h - 2) * (inner_w - 2)
                            if marker_mode == "off_center" and interior_cells < 2:
                                continue
                            candidate = (
                                height,
                                width,
                                n_frames,
                                gap,
                                margin,
                                marker_mode,
                            )
                            candidates.append(candidate)
                            weights.append(_plan_weight(candidate, difficulty))
    return tuple(candidates), tuple(weights)


def _general_plan(rng, requested, difficulty):
    candidates, weights = _candidate_pool(
        tuple(sorted(requested.items())), difficulty
    )
    if not candidates:
        raise ValueError(
            "requested overrides cannot form two to four nested frames "
            "with a strictly interior marker"
        )
    return rng.choices(candidates, weights=weights, k=1)[0]


def _uniform_boxes(height, width, n_frames, gap, margin):
    return [
        (
            margin + index * gap,
            margin + index * gap,
            height - 1 - margin - index * gap,
            width - 1 - margin - index * gap,
        )
        for index in range(n_frames)
    ]


def _profile_boxes(rng, height, width, shapes):
    """Translate nested official frame shapes while retaining the tuple."""
    boxes = []
    parent = (0, 0, height - 1, width - 1)
    for index, (box_h, box_w) in enumerate(shapes):
        pr0, pc0, pr1, pc1 = parent
        if index == 0:
            row_choices = range(0, height - box_h + 1)
            col_choices = range(0, width - box_w + 1)
        else:
            row_choices = range(pr0 + 1, pr1 - box_h + 1)
            col_choices = range(pc0 + 1, pc1 - box_w + 1)
        row0 = rng.choice(tuple(row_choices))
        col0 = rng.choice(tuple(col_choices))
        box = (row0, col0, row0 + box_h - 1, col0 + box_w - 1)
        boxes.append(box)
        parent = box
    return boxes


def _marker_position(rng, inner_box, marker_mode):
    r0, c0, r1, c1 = inner_box
    center = ((r0 + r1) // 2, (c0 + c1) // 2)
    if marker_mode == "centered":
        return center
    choices = [
        (row, col)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
        if (row, col) != center
    ]
    if not choices:
        raise ValueError("off_center marker requested for a 3x3 inner frame")
    return rng.choice(choices)


def _axis_values_from_layout(height, width, boxes, marker):
    outer = boxes[0]
    inner = boxes[-1]
    side_gaps = []
    for first, second in zip(boxes, boxes[1:]):
        side_gaps.extend((
            second[0] - first[0],
            second[1] - first[1],
            first[2] - second[2],
            first[3] - second[3],
        ))
    center = ((inner[0] + inner[2]) // 2, (inner[1] + inner[3]) // 2)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_frames": len(boxes),
        "frame_gap": min(side_gaps),
        "outer_margin": min(
            outer[0], outer[1], height - 1 - outer[2], width - 1 - outer[3]
        ),
        "marker_mode": "centered" if marker == center else "off_center",
    }


def _record_axes(ctx, values):
    ctx.overrides.update(values)
    observed = {
        "grid_h": ctx.draw_int("grid_h", values["grid_h"], values["grid_h"]),
        "grid_w": ctx.draw_int("grid_w", values["grid_w"], values["grid_w"]),
        "n_frames": ctx.draw_int(
            "n_frames", values["n_frames"], values["n_frames"]
        ),
        "frame_gap": ctx.draw_int(
            "frame_gap", values["frame_gap"], values["frame_gap"]
        ),
        "outer_margin": ctx.draw_int(
            "outer_margin", values["outer_margin"], values["outer_margin"]
        ),
        "marker_mode": ctx.draw_choice(
            "marker_mode", (values["marker_mode"],)
        ),
    }
    if observed != values:
        raise AssertionError("axis provenance changed the planned layout")


def _render(ctx, height, width, boxes, marker):
    palette_rng = ctx.draw_rng("frame_palette")
    colors = palette_rng.sample(FRAME_COLORS, len(boxes))
    grid = full_grid(height, width, 0)
    for color, box in zip(colors, boxes):
        draw_frame(grid, *box, color)
    grid[marker[0]][marker[1]] = 2
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    _validate_requested(overrides)
    requested = dict(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    use_profile = (
        not requested
        and ctx.draw_rng("canonical_prior").random() < _CANONICAL_PRIOR_P
    )
    layout_rng = ctx.draw_rng("layout_plan")

    if use_profile:
        height, width, shapes = ctx.draw_rng("canonical_profile").choice(
            _CANONICAL_PROFILES
        )
        boxes = _profile_boxes(layout_rng, height, width, shapes)
        inner = boxes[-1]
        interior = [
            (row, col)
            for row in range(inner[0] + 1, inner[2])
            for col in range(inner[1] + 1, inner[3])
        ]
        marker = layout_rng.choice(interior)
        values = _axis_values_from_layout(height, width, boxes, marker)
    else:
        values_tuple = _general_plan(layout_rng, requested, difficulty)
        height, width, n_frames, gap, margin, marker_mode = values_tuple
        boxes = _uniform_boxes(height, width, n_frames, gap, margin)
        marker = _marker_position(layout_rng, boxes[-1], marker_mode)
        values = {
            "grid_h": height,
            "grid_w": width,
            "n_frames": n_frames,
            "frame_gap": gap,
            "outer_margin": margin,
            "marker_mode": marker_mode,
        }

    _record_axes(ctx, values)
    grid = _render(ctx, values["grid_h"], values["grid_w"], boxes, marker)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": requested},
    )
    if errors:
        raise ValueError("constructed invalid nested-frame grid: " + "; ".join(errors))
    return _clone(grid)
