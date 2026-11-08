"""Semantic generator for ARC task a0c6005765ee (bank source M4).

Complete color-5 rectangle frames react to color-7 markers exactly one cell
outside an edge.  A top or bottom marker paints its interior column color 3;
a left or right marker paints its interior row color 3.  Multiple frames and
markers contribute the union of their projected stripes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "a0c6005765ee"
TASK_ID = "a0c6005765ee"
VERSION = "3.0.0"
RULE_HASH = "dd8e67797905"
SUMMARY = "Project each external color-7 marker through its complete color-5 frame as an interior color-3 stripe."
INVARIANTS = [
    "calibrated inputs contain one or two separate complete color-5 rectangle frames",
    "each color-7 marker is exactly one cell outside one frame edge and aligned with a strict-interior row or column",
    "top and bottom markers paint interior columns while left and right markers paint interior rows",
    "multiple marker projections combine as a union of color-3 stripes",
    "background, frame, and marker cells are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = ("single_large", "double_varied", "two_stripes", "cross_stripes")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three complete official frame families plus four controlled frame/stripe contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "0000000000", "0000700000", "0005555000", "0005005000",
        "0005005000", "0005005000", "0005555000", "0000000000",
        "0000000000", "0000000000",
    ),
    "public_2": (
        "00000000000", "00000000000", "00555500000", "00500500000",
        "07500500000", "00500500000", "00555500000", "00000000000",
        "00000000000", "00000000000", "00000000000",
    ),
    "public_3": (
        "000000000000", "000000700000", "000005555000", "000005005000",
        "000005005000", "000005005000", "000005555000", "000000000000",
        "000000555500", "000000500570", "000000500500", "000000555500",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _components4(grid, color):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components = []
    while cells:
        queue = [cells.pop()]
        component = []
        for row, col in queue:
            component.append((row, col))
            for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if other in cells:
                    cells.remove(other)
                    queue.append(other)
        components.append(component)
    return sorted(components, key=lambda component: min(component))


def _bbox(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(row0, col0, row1, col1):
    return {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }


def _complete_frames(grid):
    frames = []
    for component in _components4(grid, 5):
        row0, col0, row1, col1 = _bbox(component)
        if _perimeter(row0, col0, row1, col1) <= set(component):
            frames.append({
                "cells": tuple(sorted(component)),
                "bbox": (row0, col0, row1, col1),
                "height": row1 - row0 + 1,
                "width": col1 - col0 + 1,
            })
    return frames


def _frame_markers(grid, frame):
    height, width = len(grid), len(grid[0])
    row0, col0, row1, col1 = frame["bbox"]
    markers = []
    if row0 > 0:
        markers.extend(("top", col - col0, row0 - 1, col) for col in range(col0 + 1, col1) if grid[row0 - 1][col] == 7)
    if row1 < height - 1:
        markers.extend(("bottom", col - col0, row1 + 1, col) for col in range(col0 + 1, col1) if grid[row1 + 1][col] == 7)
    if col0 > 0:
        markers.extend(("left", row - row0, row, col0 - 1) for row in range(row0 + 1, row1) if grid[row][col0 - 1] == 7)
    if col1 < width - 1:
        markers.extend(("right", row - row0, row, col1 + 1) for row in range(row0 + 1, row1) if grid[row][col1 + 1] == 7)
    return markers


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    frames = _complete_frames(grid)
    result = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            for frame in frames:
                row0, col0, row1, col1 = frame["bbox"]
                if not (row0 < row < row1 and col0 < col < col1):
                    continue
                projected = (
                    (row0 > 0 and grid[row0 - 1][col] == 7)
                    or (row1 < height - 1 and grid[row1 + 1][col] == 7)
                    or (col0 > 0 and grid[row][col0 - 1] == 7)
                    or (col1 < width - 1 and grid[row][col1 + 1] == 7)
                )
                if projected:
                    result[row][col] = 3
                    break
    return result


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 24 or not 8 <= width <= 24:
        errors.append("calibrated canvas dimensions must be eight through twenty-four")
    if set(value for row in grid for value in row) != {0, 5, 7}:
        errors.append("calibrated input palette must be exactly zero, five, and seven")
    color5 = {cell for component in _components4(grid, 5) for cell in component}
    frames = _complete_frames(grid)
    if not 1 <= len(frames) <= 2:
        errors.append(f"expected one or two complete color-5 frames, got {len(frames)}")
    if frames and color5 != {cell for frame in frames for cell in frame["cells"]}:
        errors.append("every color-5 cell must belong to a complete frame component")
    marker_owners = {}
    for index, frame in enumerate(frames):
        row0, col0, row1, col1 = frame["bbox"]
        expected = _perimeter(row0, col0, row1, col1)
        if set(frame["cells"]) != expected:
            errors.append(f"frame {index} must contain exactly its rectangular perimeter")
        if not 4 <= frame["height"] <= 9 or not 4 <= frame["width"] <= 9:
            errors.append(f"frame {index} sides must be four through nine")
        markers = _frame_markers(grid, frame)
        frame["markers"] = tuple(markers)
        frame["marker_count"] = len(markers)
        frame["normalized_dims"] = tuple(sorted((frame["height"], frame["width"])))
        frame["touches_border"] = any((
            row0 == 0,
            col0 == 0,
            row1 == height - 1,
            col1 == width - 1,
        ))
        for side, offset, row, col in markers:
            marker_owners.setdefault((row, col), []).append((index, side, offset))
    all_markers = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    }
    if set(marker_owners) != all_markers:
        errors.append("every marker must sit one cell outside a strict-interior frame coordinate")
    if any(len(owners) != 1 for owners in marker_owners.values()):
        errors.append("each marker must belong to exactly one frame")
    dims = tuple(sorted(frame["normalized_dims"] for frame in frames))
    counts = tuple(sorted(frame.get("marker_count", 0) for frame in frames))
    profile = None
    single_marker_geometry = None
    if len(frames) == 1 and counts == (1,):
        side, offset, _, _ = frames[0]["markers"][0]
        edge_length = frames[0]["width"] if side in ("top", "bottom") else frames[0]["height"]
        corner_distance = min(offset, edge_length - 1 - offset)
        single_marker_geometry = (edge_length, corner_distance)
    if dims == ((4, 5),) and single_marker_geometry == (4, 1):
        profile = "public_1"
    elif dims == ((4, 5),) and single_marker_geometry == (5, 2):
        profile = "public_2"
    elif counts == (1, 1) and dims == ((4, 4), (4, 5)):
        profile = "public_3"
    elif counts == (1,) and dims and max(dims[0]) >= 6:
        profile = "single_large"
    elif counts == (1, 1):
        profile = "double_varied"
    elif counts == (2,):
        profile = "two_stripes"
    elif counts == (4,):
        sides = {marker[0] for marker in frames[0]["markers"]}
        if sides == {"top", "bottom", "left", "right"}:
            profile = "cross_stripes"
    if profile is None and not errors:
        errors.append(f"unsupported calibrated frame/marker signature dims={dims!r}, counts={counts!r}")
    output = rule_mirror(grid)
    if not errors and output == [list(row) for row in grid]:
        errors.append("calibrated marker projections must visibly change the frame interior")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "frames": frames,
            "frame_count": len(frames),
            "dimensions": dims,
            "marker_counts": counts,
            "markers": marker_owners,
        },
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _limits(difficulty):
    if difficulty == "easy":
        return 9, 13
    if difficulty == "medium":
        return 10, 16
    if difficulty == "hard":
        return 13, 19
    return 10, 16


def _stripe_key(side, offset):
    return ("col", offset) if side in ("top", "bottom") else ("row", offset)


def _random_markers(frame_height, frame_width, count, rng, all_sides=False):
    if all_sides:
        sides = ["top", "bottom", "left", "right"]
    else:
        sides = rng.sample(["top", "bottom", "left", "right"], count)
    markers = []
    used = set()
    for side in sides:
        maximum = frame_width - 2 if side in ("top", "bottom") else frame_height - 2
        offsets = list(range(1, maximum + 1))
        rng.shuffle(offsets)
        for offset in offsets:
            key = _stripe_key(side, offset)
            if key not in used:
                used.add(key)
                markers.append((side, offset))
                break
        else:
            raise AssertionError("could not choose distinct projected stripes")
    return markers


def _spec(frame_height, frame_width, marker_count, rng, all_sides=False):
    return {
        "height": frame_height,
        "width": frame_width,
        "markers": _random_markers(frame_height, frame_width, marker_count, rng, all_sides),
    }


def _footprint(spec):
    sides = {side for side, _ in spec["markers"]}
    top_pad = int("top" in sides)
    bottom_pad = int("bottom" in sides)
    left_pad = int("left" in sides)
    right_pad = int("right" in sides)
    return {
        **spec,
        "top_pad": top_pad,
        "bottom_pad": bottom_pad,
        "left_pad": left_pad,
        "right_pad": right_pad,
        "foot_height": spec["height"] + top_pad + bottom_pad,
        "foot_width": spec["width"] + left_pad + right_pad,
    }


def _render_specs(height, width, specs, rng):
    grid = [[0] * width for _ in range(height)]
    boxes = []
    indexed = sorted(enumerate((_footprint(spec) for spec in specs)), key=lambda item: item[1]["foot_height"] * item[1]["foot_width"], reverse=True)
    placements = {}
    for index, spec in indexed:
        candidates = [
            (row, col)
            for row in range(height - spec["foot_height"] + 1)
            for col in range(width - spec["foot_width"] + 1)
        ]
        rng.shuffle(candidates)
        for foot_row, foot_col in candidates:
            foot_row1 = foot_row + spec["foot_height"] - 1
            foot_col1 = foot_col + spec["foot_width"] - 1
            if any(
                not (
                    foot_row1 + 1 < other_row0
                    or other_row1 + 1 < foot_row
                    or foot_col1 + 1 < other_col0
                    or other_col1 + 1 < foot_col
                )
                for other_row0, other_col0, other_row1, other_col1 in boxes
            ):
                continue
            boxes.append((foot_row, foot_col, foot_row1, foot_col1))
            placements[index] = (foot_row, foot_col, spec)
            break
        else:
            raise AssertionError("could not pack separated marker-frame footprints")
    for index in range(len(specs)):
        foot_row, foot_col, spec = placements[index]
        row0 = foot_row + spec["top_pad"]
        col0 = foot_col + spec["left_pad"]
        row1 = row0 + spec["height"] - 1
        col1 = col0 + spec["width"] - 1
        for row, col in _perimeter(row0, col0, row1, col1):
            grid[row][col] = 5
        for side, offset in spec["markers"]:
            if side == "top":
                row, col = row0 - 1, col0 + offset
            elif side == "bottom":
                row, col = row1 + 1, col0 + offset
            elif side == "left":
                row, col = row0 + offset, col0 - 1
            else:
                row, col = row0 + offset, col1 + 1
            grid[row][col] = 7
    return grid


def _profile_specs(profile, difficulty, rng):
    if profile == "public_1":
        if rng.random() < 0.5:
            return [{"height": 5, "width": 4, "markers": [(rng.choice(("top", "bottom")), rng.choice((1, 2)))]}]
        return [{"height": 4, "width": 5, "markers": [(rng.choice(("left", "right")), rng.choice((1, 2)))]}]
    if profile == "public_2":
        if rng.random() < 0.5:
            return [{"height": 5, "width": 4, "markers": [(rng.choice(("left", "right")), 2)]}]
        return [{"height": 4, "width": 5, "markers": [(rng.choice(("top", "bottom")), 2)]}]
    if profile == "public_3":
        first = _profile_specs("public_1", difficulty, rng)[0]
        return [first, _spec(4, 4, 1, rng)]
    if difficulty == "easy":
        side_low, side_high = 4, 6
    elif difficulty == "hard":
        side_low, side_high = 6, 9
    else:
        side_low, side_high = 5, 7
    if profile == "single_large":
        height = rng.randint(max(6, side_low), side_high)
        width = rng.randint(max(6, side_low), side_high)
        return [_spec(height, width, 1, rng)]
    if profile == "double_varied":
        for _ in range(100):
            dims = [
                (rng.randint(side_low, side_high), rng.randint(side_low, side_high))
                for _ in range(2)
            ]
            normalized = tuple(sorted(tuple(sorted(value)) for value in dims))
            if normalized != ((4, 4), (4, 5)):
                return [_spec(height, width, 1, rng) for height, width in dims]
        raise AssertionError("could not choose generalized double-frame dimensions")
    if profile == "two_stripes":
        height = rng.randint(max(5, side_low), side_high)
        width = rng.randint(max(5, side_low), side_high)
        return [_spec(height, width, 2, rng)]
    if profile == "cross_stripes":
        height = rng.randint(max(5, side_low), side_high)
        width = rng.randint(max(5, side_low), side_high)
        return [_spec(height, width, 4, rng, all_sides=True)]
    raise ValueError(f"unknown scene profile: {profile!r}")


def _random_scene(profile, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(300):
        specs = _profile_specs(profile, difficulty, rng)
        height, width = rng.randint(low, high), rng.randint(low, high)
        try:
            grid = _render_specs(height, width, specs, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct frame lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _random_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid frame-stripe lesson: " + "; ".join(errors))
    return grid
