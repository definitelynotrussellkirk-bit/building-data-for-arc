"""Semantic generator for ARC task 2d2455d1008d.

Every complete 4-connected yellow (4) hollow rectangle is considered
independently.  When its interior contains exactly one distinct color other
than background (0) and yellow, the rule fills only the remaining background
interior cells with that color.  Existing marker cells are preserved.  Empty
frames, frames with multiple marker colors, incomplete yellow shapes, and
objects outside frames are unchanged.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2d2455d1008d"
TASK_ID = "2d2455d1008d"
VERSION = "3.0.0"
RULE_HASH = "cfe81ed70c6a"
SUMMARY = "Fill zero cells inside each complete yellow frame that contains exactly one distinct marker color."
INVARIANTS = [
    "background is color 0 and frame borders are color 4",
    "only complete 4-connected hollow rectangular yellow components are frames",
    "each frame is evaluated independently from the original input",
    "one distinct nonzero non-yellow interior color licenses the fill, even when repeated",
    "only zero-valued interior cells are recolored; markers, frames, and distractors are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "single_frame_single_marker",
    "single_frame_repeated_marker",
    "mixed_marked_empty",
    "mixed_marked_multicolor",
    "external_distractors",
    "broken_frame_decoy",
    "varied_frame_sizes",
    "edge_frame",
    "many_marked_frames",
    "yellow_interior_obstacle",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten independently recoverable frame-filling lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|single_frame_single_marker|single_frame_repeated_marker|mixed_marked_empty|mixed_marked_multicolor|external_distractors|broken_frame_decoy|varied_frame_sizes|edge_frame|many_marked_frames|yellow_interior_obstacle",
    }
}

_PUBLIC_ROWS = (
    "00000000000000/00000000444444/00000000400034/07000000444444/77044440000000/00040340444400/00044440402400/00000000444400/00000000000000/00000000000000",
    "0000000004444/0444440004004/0410040004004/0444440004024/0000000004444/0044440000000/0042046600000/0040046000000/0040040000000/0044440000000/0000000000000/0000000000000",
    "000004444000/000004204000/000004444000/000000000000/000000000000/444400000000/400400000000/444404444000/000004104000/007704004000/007704004000/000004444000",
    "00000000000000/00004444440000/00004001040000/00004000040000/00004444440000/00000000000000/00000000000000/04444044444000/04204040004000/04444042004000/00600040004000/06600044444000",
    "00000000007700/00044444407000/00040000400000/00040300400000/00044444400000/00000000000000/44440444400000/40140403400000/44440400400000/00000444400000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MARKER_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return ["input dimensions must be between 3 and 30 on both axes"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _yellow_components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    }
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(sorted(components, key=lambda cells: cells[0]))


def _border(row0, col0, row1, col1):
    return {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }


def _frame_records(grid):
    height, width = len(grid), len(grid[0])
    frames, invalid = [], []
    for component in _yellow_components(grid):
        row0 = min(row for row, _ in component)
        row1 = max(row for row, _ in component)
        col0 = min(col for _, col in component)
        col1 = max(col for _, col in component)
        if row1 - row0 < 2 or col1 - col0 < 2 or set(component) != _border(row0, col0, row1, col1):
            invalid.append(component)
            continue
        interior = tuple(
            (row, col)
            for row in range(row0 + 1, row1)
            for col in range(col0 + 1, col1)
        )
        marker_cells = tuple(
            (row, col)
            for row, col in interior
            if grid[row][col] not in (0, 4)
        )
        marker_colors = tuple(sorted({grid[row][col] for row, col in marker_cells}))
        frames.append(
            {
                "bbox": (row0, col0, row1, col1),
                "interior": interior,
                "interior_area": len(interior),
                "marker_cells": marker_cells,
                "marker_count": len(marker_cells),
                "marker_colors": marker_colors,
                "zero_count": sum(grid[row][col] == 0 for row, col in interior),
                "yellow_inside": sum(grid[row][col] == 4 for row, col in interior),
                "touches_edge": row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1,
            }
        )
    return tuple(frames), tuple(invalid)


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    frames, _ = _frame_records(grid)
    for frame in frames:
        if len(frame["marker_colors"]) != 1:
            continue
        fill = frame["marker_colors"][0]
        for row, col in frame["interior"]:
            if output[row][col] == 0:
                output[row][col] = fill
    return output


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    frames, invalid = _frame_records(grid)
    eligible = tuple(frame for frame in frames if len(frame["marker_colors"]) == 1)
    empty = tuple(frame for frame in frames if not frame["marker_colors"])
    ambiguous = tuple(frame for frame in frames if len(frame["marker_colors"]) >= 2)
    framed_interiors = {cell for frame in frames for cell in frame["interior"]}
    outside_markers = tuple(
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 4) and (row, col) not in framed_interiors
    )
    output = rule_mirror(grid)
    changed = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if output[row][col] != grid[row][col]
    )
    flat = [value for row in grid for value in row]
    zero_is_unique_mode = flat.count(0) > max(
        (flat.count(color) for color in set(flat) if color != 0),
        default=0,
    )
    facts = {
        "height": height,
        "width": width,
        "frames": frames,
        "frame_count": len(frames),
        "eligible": eligible,
        "eligible_count": len(eligible),
        "empty_count": len(empty),
        "ambiguous_count": len(ambiguous),
        "invalid_yellow_count": len(invalid),
        "outside_markers": outside_markers,
        "outside_marker_count": len(outside_markers),
        "changed": changed,
        "changed_count": len(changed),
        "zero_is_unique_mode": zero_is_unique_mode,
        "output": output,
    }
    facts["scene_profile"] = _profile_for(grid, facts)
    return facts


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    eligible = facts["eligible"]
    if not eligible:
        return None
    if any(frame["yellow_inside"] for frame in eligible):
        return "yellow_interior_obstacle"
    if facts["invalid_yellow_count"]:
        return "broken_frame_decoy"
    if facts["outside_marker_count"]:
        return "external_distractors"
    if facts["ambiguous_count"]:
        return "mixed_marked_multicolor"
    if facts["empty_count"]:
        return "mixed_marked_empty"
    if facts["frame_count"] >= 4:
        return "many_marked_frames"
    if any(frame["touches_edge"] for frame in eligible):
        return "edge_frame"
    if len(eligible) >= 2 and len({frame["interior_area"] for frame in eligible}) >= 2:
        return "varied_frame_sizes"
    if len(eligible) == 1 and eligible[0]["marker_count"] >= 2:
        return "single_frame_repeated_marker"
    if len(eligible) == 1 and eligible[0]["marker_count"] == 1:
        return "single_frame_single_marker"
    return None


def _profile_errors(facts):
    profile = facts["scene_profile"]
    if profile in PUBLIC_PROFILES:
        return []
    errors = []
    if not facts["zero_is_unique_mode"]:
        errors.append("generated lesson requires zero to be the unique modal background")
    if facts["changed_count"] < 2:
        errors.append("generated lesson must expose the fill by changing at least two interior zeros")
    if any(frame["zero_count"] == 0 for frame in facts["eligible"]):
        errors.append("eligible frames must retain at least one background fill target")
    if profile == "single_frame_single_marker" and not (
        facts["frame_count"] == facts["eligible_count"] == 1
        and facts["eligible"][0]["marker_count"] == 1
    ):
        errors.append("single-frame profile requires one eligible frame and one marker cell")
    if profile == "single_frame_repeated_marker" and not (
        facts["frame_count"] == facts["eligible_count"] == 1
        and facts["eligible"][0]["marker_count"] >= 2
    ):
        errors.append("repeated-marker profile requires one frame with repeated cells of one color")
    if profile == "mixed_marked_empty" and not (
        facts["eligible_count"] >= 1 and facts["empty_count"] >= 1 and not facts["ambiguous_count"]
    ):
        errors.append("marked-empty profile requires both an eligible and an empty frame")
    if profile == "mixed_marked_multicolor" and not (
        facts["eligible_count"] >= 1 and facts["ambiguous_count"] >= 1
    ):
        errors.append("multicolor profile requires both an eligible and a two-color frame")
    if profile == "external_distractors" and not facts["outside_marker_count"]:
        errors.append("external-distractor profile requires colored content outside all frames")
    if profile == "broken_frame_decoy" and not facts["invalid_yellow_count"]:
        errors.append("broken-frame profile requires a nonrectangular yellow component")
    if profile == "varied_frame_sizes" and not (
        facts["eligible_count"] >= 2
        and len({frame["interior_area"] for frame in facts["eligible"]}) >= 2
    ):
        errors.append("varied-size profile requires differently sized eligible interiors")
    if profile == "edge_frame" and not any(frame["touches_edge"] for frame in facts["eligible"]):
        errors.append("edge-frame profile requires a complete frame touching the canvas edge")
    if profile == "many_marked_frames" and facts["eligible_count"] < 4:
        errors.append("many-frame profile requires at least four eligible frames")
    if profile == "yellow_interior_obstacle" and not any(
        frame["yellow_inside"] for frame in facts["eligible"]
    ):
        errors.append("yellow-obstacle profile requires preserved yellow inside an eligible frame")
    return errors


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["scene_profile"] not in SCENE_PROFILES:
        errors.append("grid does not match a declared observable yellow-frame lesson")
    else:
        errors.extend(_profile_errors(facts))
    return {
        "errors": errors,
        "facts": facts,
        "scene_profile": facts["scene_profile"],
        "output": facts["output"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(grid, row0, col0, frame_h, frame_w):
    row1, col1 = row0 + frame_h - 1, col0 + frame_w - 1
    for row, col in _border(row0, col0, row1, col1):
        grid[row][col] = 4
    return tuple(
        (row, col)
        for row in range(row0 + 1, row1)
        for col in range(col0 + 1, col1)
    )


def _put_markers(grid, interior, colors, rng):
    cells = list(interior)
    rng.shuffle(cells)
    for (row, col), color in zip(cells, colors):
        grid[row][col] = color


def _dimensions(difficulty, rng, minimum=(8, 10)):
    bands = {
        None: ((10, 22), (12, 24)),
        "easy": ((8, 12), (10, 15)),
        "medium": ((12, 18), (14, 21)),
        "hard": ((18, 27), (20, 29)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    h0, w0 = max(h0, minimum[0]), max(w0, minimum[1])
    h1, w1 = max(h0, h1), max(w0, w1)
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _single_scene(difficulty, profile, rng):
    height, width = _dimensions(difficulty, rng)
    grid = _blank(height, width)
    frame_h = rng.randint(4, min(8, height - 2))
    frame_w = rng.randint(4, min(9, width - 2))
    row0 = rng.randint(1, height - frame_h - 1)
    col0 = rng.randint(1, width - frame_w - 1)
    interior = _draw_frame(grid, row0, col0, frame_h, frame_w)
    color = rng.choice(_MARKER_COLORS)
    count = rng.randint(2, min(4, len(interior) - 2)) if profile == "single_frame_repeated_marker" else 1
    _put_markers(grid, interior, [color] * count, rng)
    return grid


def _two_frame_scene(difficulty, profile, rng):
    height, width = _dimensions(difficulty, rng, minimum=(10, 15))
    grid = _blank(height, width)
    if profile == "varied_frame_sizes":
        dims = ((4, 4), (rng.randint(5, min(7, height - 2)), rng.randint(5, min(7, (width - 3) // 2))))
    else:
        dims = (
            (rng.randint(4, min(6, height - 2)), rng.randint(4, min(6, (width - 3) // 2))),
            (rng.randint(4, min(6, height - 2)), rng.randint(4, min(6, (width - 3) // 2))),
        )
    (h1, w1), (h2, w2) = dims
    row1, row2 = rng.randint(1, height - h1 - 1), rng.randint(1, height - h2 - 1)
    left = _draw_frame(grid, row1, 1, h1, w1)
    right = _draw_frame(grid, row2, width - w2 - 1, h2, w2)
    colors = rng.sample(_MARKER_COLORS, 3)
    _put_markers(grid, left, [colors[0]], rng)
    if profile == "mixed_marked_empty":
        pass
    elif profile == "mixed_marked_multicolor":
        _put_markers(grid, right, colors[1:3], rng)
    else:
        _put_markers(grid, right, [colors[1]], rng)
    return grid


def _external_scene(difficulty, rng):
    grid = _single_scene(difficulty, "single_frame_single_marker", rng)
    height, width = len(grid), len(grid[0])
    color = rng.choice(_MARKER_COLORS)
    candidates = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    row, col = rng.choice([cell for cell in candidates if grid[cell[0]][cell[1]] == 0])
    grid[row][col] = color
    if rng.random() < 0.7:
        neighbor = (row + (1 if row == 0 else -1), col)
        if grid[neighbor[0]][neighbor[1]] == 0:
            grid[neighbor[0]][neighbor[1]] = color
    return grid


def _broken_scene(difficulty, rng):
    height, width = _dimensions(difficulty, rng, minimum=(12, 16))
    grid = _blank(height, width)
    frame_h = rng.randint(4, min(7, height - 2))
    frame_w = rng.randint(4, 6)
    interior = _draw_frame(
        grid,
        rng.randint(1, height - frame_h - 1),
        rng.randint(0, 1),
        frame_h,
        frame_w,
    )
    _put_markers(grid, interior, [rng.choice(_MARKER_COLORS)], rng)
    arm_h, arm_w = rng.randint(3, 5), rng.randint(3, 6)
    row0 = rng.randint(0, height - arm_h)
    col0 = rng.randint(max(8, width // 2), width - arm_w)
    vertical_col = col0 if rng.random() < 0.5 else col0 + arm_w - 1
    horizontal_row = row0 if rng.random() < 0.5 else row0 + arm_h - 1
    for col in range(col0, col0 + arm_w):
        grid[horizontal_row][col] = 4
    for row in range(row0, row0 + arm_h):
        grid[row][vertical_col] = 4
    if rng.random() < 0.5:
        spur_col = vertical_col + (1 if vertical_col == col0 else -1)
        grid[row0 + arm_h // 2][spur_col] = 4
    return grid


def _edge_scene(difficulty, rng):
    height, width = _dimensions(difficulty, rng)
    grid = _blank(height, width)
    frame_h = rng.randint(4, min(7, height - 1))
    frame_w = rng.randint(4, min(8, width - 2))
    col0 = rng.randint(1, width - frame_w - 1)
    interior = _draw_frame(grid, 0, col0, frame_h, frame_w)
    _put_markers(grid, interior, [rng.choice(_MARKER_COLORS)], rng)
    return grid


def _many_scene(difficulty, rng):
    height, width = _dimensions(difficulty, rng, minimum=(12, 14))
    grid = _blank(height, width)
    positions = ((1, 1), (1, width - 5), (height - 5, 1), (height - 5, width - 5))
    colors = rng.sample(_MARKER_COLORS, 4)
    for (row0, col0), color in zip(positions, colors):
        interior = _draw_frame(grid, row0, col0, 4, 4)
        _put_markers(grid, interior, [color], rng)
    return grid


def _yellow_obstacle_scene(difficulty, rng):
    height, width = _dimensions(difficulty, rng, minimum=(10, 12))
    grid = _blank(height, width)
    frame_h = rng.randint(6, min(9, height - 2))
    frame_w = rng.randint(6, min(9, width - 2))
    row0 = rng.randint(1, height - frame_h - 1)
    col0 = rng.randint(1, width - frame_w - 1)
    interior = _draw_frame(grid, row0, col0, frame_h, frame_w)
    obstacle = (row0 + 2, col0 + 2)
    grid[obstacle[0]][obstacle[1]] = 4
    marker_choices = [cell for cell in interior if cell != obstacle and abs(cell[0] - obstacle[0]) + abs(cell[1] - obstacle[1]) > 1]
    _put_markers(grid, marker_choices, [rng.choice(_MARKER_COLORS)], rng)
    return grid


def _candidate_scene(difficulty, profile, rng):
    if profile in {"single_frame_single_marker", "single_frame_repeated_marker"}:
        return _single_scene(difficulty, profile, rng)
    if profile in {"mixed_marked_empty", "mixed_marked_multicolor", "varied_frame_sizes"}:
        return _two_frame_scene(difficulty, profile, rng)
    if profile == "external_distractors":
        return _external_scene(difficulty, rng)
    if profile == "broken_frame_decoy":
        return _broken_scene(difficulty, rng)
    if profile == "edge_frame":
        return _edge_scene(difficulty, rng)
    if profile == "many_marked_frames":
        return _many_scene(difficulty, rng)
    if profile == "yellow_interior_obstacle":
        return _yellow_obstacle_scene(difficulty, rng)
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _general_scene(difficulty, profile, rng):
    for _ in range(200):
        grid = _candidate_scene(difficulty, profile, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    ordinary_profiles = (
        PUBLIC_PROFILES * 2
        + ("single_frame_single_marker",) * 4
        + ("single_frame_repeated_marker",) * 7
        + ("mixed_marked_empty",) * 12
        + ("mixed_marked_multicolor",) * 9
        + ("external_distractors",) * 8
        + ("broken_frame_decoy",) * 7
        + ("varied_frame_sizes",) * 12
        + ("edge_frame",) * 6
        + ("many_marked_frames",) * 8
        + ("yellow_interior_obstacle",) * 7
    )
    profile = ctx.draw_choice("scene_profile", ordinary_profiles)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("geometry"))
