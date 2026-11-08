"""Semantic generator for ARC task 65084a735199.

Every closed gray frame contains one colored marker.  Recolor each complete
frame border with its own marker color, then clear that marker to black.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "65084a735199"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ec22312565dc"
SUMMARY = "Bind each gray hollow frame to its interior marker, recolor the border, and clear the marker."
INVARIANTS = [
    "the background is black and every object group contains a closed gray rectangular frame",
    "each frame contains exactly one non-black, non-gray marker",
    "marker colors are distinct so each frame-to-marker binding is visible",
    "every frame border is recolored independently and every marker is cleared",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
GENERAL_PROFILES = (
    "paired_squares",
    "wide_frames",
    "tall_frames",
    "paired_mixed",
    "triple_mixed",
    "quad_mixed",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng over exact public and generalized frame galleries",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "0000000000", "0555500000", "0500500000", "0520500000", "0555500000",
        "0000055550", "0000050050", "0000050350", "0000055550", "0000000000",
    ),
    "public_train_2": (
        "00055550000", "00050050000", "00050750000", "00050050000", "00055550000",
        "00000000000", "05555000000", "05005000000", "05035000000", "05555000000",
        "00000000000",
    ),
    "public_test_1": (
        "00000000000", "05555000000", "05005000000", "05045000000", "05555000000",
        "00000000000", "00005555000", "00005005000", "00005065000", "00005555000",
        "00000000000",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be integer ARC colors"], h, w
    return [], h, w


def _gray_components(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        components.append({"cells": frozenset(cells), "bbox": (r0, c0, r1, c1)})
    return components


def _profile_from_frames(frames):
    count = len(frames)
    if count == 3:
        return "triple_mixed"
    if count == 4:
        return "quad_mixed"
    if count != 2:
        return None
    shapes = [(f["bbox"][2] - f["bbox"][0] + 1, f["bbox"][3] - f["bbox"][1] + 1) for f in frames]
    if all(h == w for h, w in shapes):
        return "paired_squares"
    if all(h < w for h, w in shapes):
        return "wide_frames"
    if all(h > w for h, w in shapes):
        return "tall_frames"
    return "paired_mixed"


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    if sum(value == 0 for row in grid for value in row) <= h * w // 2:
        errors.append("black must be the strict modal background")
    components = _gray_components(grid)
    if len(components) < 2:
        errors.append("at least two independent gray frames are required")
    frames = []
    used = set()
    marker_colors = []
    output = [list(row) for row in grid]
    for component in components:
        r0, c0, r1, c1 = component["bbox"]
        if r1 - r0 < 3 or c1 - c0 < 3:
            errors.append(f"gray component {(r0, c0, r1, c1)} is too small for a framed marker")
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if component["cells"] != border:
            errors.append(f"gray component {(r0, c0, r1, c1)} is not a closed rectangular frame")
            continue
        markers = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5)
        ]
        if len(markers) != 1:
            errors.append(f"frame {(r0, c0, r1, c1)} has {len(markers)} markers instead of one")
            continue
        marker = markers[0]
        color = grid[marker[0]][marker[1]]
        marker_colors.append(color)
        used.update(border)
        used.add(marker)
        for r, c in border:
            output[r][c] = color
        output[marker[0]][marker[1]] = 0
        frames.append({**component, "marker": marker, "marker_color": color})
    foreground = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if foreground != used:
        errors.append("all foreground cells must belong to a frame or its marker")
    if len(marker_colors) != len(set(marker_colors)):
        errors.append("marker colors must be distinct")
    signature = tuple(map(tuple, grid))
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None and not errors:
        profile = _profile_from_frames(frames)
    if profile not in SCENE_PROFILES:
        errors.append("frame gallery does not match a declared scene profile")
    result.update({
        "frames": frames,
        "marker_colors": tuple(marker_colors),
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _frame_sizes(rng, profile):
    if profile == "paired_squares":
        return [(size, size) for size in (rng.randint(4, 6), rng.randint(4, 6))]
    if profile == "wide_frames":
        return [(rng.randint(4, 5), rng.randint(6, 8)) for _ in range(2)]
    if profile == "tall_frames":
        return [(rng.randint(6, 8), rng.randint(4, 5)) for _ in range(2)]
    if profile == "paired_mixed":
        return [(rng.randint(4, 5), rng.randint(6, 7)), (rng.randint(6, 7), rng.randint(4, 5))]
    if profile == "triple_mixed":
        square = rng.randint(4, 5)
        return [(square, square), (4, rng.randint(5, 6)), (rng.randint(5, 6), 4)]
    if profile == "quad_mixed":
        return [(rng.randint(4, 5), rng.randint(4, 5)) for _ in range(4)]
    raise ValueError(f"unknown general profile: {profile!r}")


def _general_grid(rng, profile, band):
    bounds = {"easy": (10, 13), "medium": (12, 16), "hard": (16, 20)}
    minimum = {"triple_mixed": 12, "quad_mixed": 13}.get(profile, 10)
    lo, hi = bounds[band]
    lo = max(lo, minimum)
    for _restart in range(160):
        h, w = rng.randint(lo, hi), rng.randint(lo, hi)
        sizes = _frame_sizes(rng, profile)
        rng.shuffle(sizes)
        candidates_by_size = []
        for fh, fw in sizes:
            candidates = [
                (r0, c0, r0 + fh - 1, c0 + fw - 1)
                for r0 in range(1, h - fh)
                for c0 in range(1, w - fw)
            ]
            rng.shuffle(candidates)
            candidates_by_size.append(candidates)

        def pack(index, placed):
            if index == len(candidates_by_size):
                return placed
            for box in candidates_by_size[index]:
                if all(
                    box[2] + 1 < other[0] or other[2] + 1 < box[0]
                    or box[3] + 1 < other[1] or other[3] + 1 < box[1]
                    for other in placed
                ):
                    result = pack(index + 1, placed + [box])
                    if result is not None:
                        return result
            return None

        boxes = pack(0, [])
        if boxes is None:
            continue
        grid = full_grid(h, w, 0)
        colors = [1, 2, 3, 4, 6, 7, 8, 9]
        rng.shuffle(colors)
        for index, (r0, c0, r1, c1) in enumerate(boxes):
            draw_frame(grid, r0, c0, r1, c1, 5)
            marker = (rng.randint(r0 + 1, r1 - 1), rng.randint(c0 + 1, c1 - 1))
            grid[marker[0]][marker[1]] = colors[index]
        return grid
    raise ValueError(f"could not place frame gallery for {profile}/{band}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=band, overrides=overrides,
    )
    weighted = list(PUBLIC_PROFILES) + [profile for profile in GENERAL_PROFILES for _ in range(4)]
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_grid(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    if info["errors"]:
        return list(info["errors"])
    if info["output"] == grid:
        return ["frame recoloring must change the grid"]
    return []
