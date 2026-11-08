"""Semantic generator for ARC task 4512012999bb.

Two nonzero vertical guide columns define the output height and width.  All
other nonzero cells form a crop whose bounding box is exactly two rows and two
columns smaller.  The crop is inserted between the guide columns.  It is
horizontally mirrored only when mirroring produces a strictly better match
between the crop's left/right regions and the first interior guide colors;
ties remain unmirrored.  The guide columns themselves are copied row by row.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4512012999bb"
TASK_ID = "4512012999bb"
VERSION = "3.0.0"
RULE_HASH = "dea780b8cf83"
SUMMARY = "Find paired vertical guides, orient a separately bounded crop by side-color score, and insert it between the preserved guide walls."
INVARIANTS = [
    "the selected guide columns are nonzero from their common top through bottom",
    "each guide's top and bottom cells have the same color",
    "all other nonzero cells have a bbox two rows and two columns smaller than the guide frame",
    "the crop is mirrored only when its mirrored side-color score is strictly greater",
    "guide columns are copied row by row and the crop fills the interior",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "direct_above",
    "flip_above",
    "direct_below",
    "flip_below",
    "direct_right",
    "flip_right",
    "tie_direct",
    "odd_center_ignored",
    "variegated_walls",
    "multicolor_crop",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten recoverable frame/crop lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|direct_above|flip_above|direct_below|flip_below|direct_right|flip_right|tie_direct|odd_center_ignored|variegated_walls|multicolor_crop",
    }
}

_PUBLIC_ROWS = (
    "0000000000000/0040000400000/0020000100000/0020000100000/0040000400000/0000000000000/0000000000000/0000000000000/0000000000000/0001120000000/0000122000000/0000000000000/0000000000000",
    "0000000000000/0000030808000/0000333888000/0000030808000/0000033888000/0000000808000/0400000040000/0800000030000/0800000030000/0800000030000/0800000030000/0800000030000/0400000040000",
    "0000000000000/0000040000400/0000070000300/0000070000300/0000070000300/0000040000400/0000000000000/0000000000000/0000000000000/0000077030000/0000077330000/0000007030000/0000000000000",
    "0000000000000/0000000000000/0000000000000/0022010000000/0002011100000/0002210000000/0000200000000/0000040000004/0000020000001/0000020000001/0000020000001/0000020000001/0000040000004",
    "0000000000000/0400000040000/0200000080000/0200000080000/0200000080000/0200000080000/0400000040000/0000000000000/0000000000000/0808200000000/0888222000000/0800020000000/0800022000000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["input dimensions must be between 7 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _find_candidates(grid):
    """Return valid candidates in the canonical r0,r1,cL,cR search order."""
    height, width = len(grid), len(grid[0])
    nonzero = tuple((row, col) for row in range(height) for col in range(width) if grid[row][col] != 0)
    segments = defaultdict(list)
    for row0 in range(height):
        for row1 in range(row0 + 2, height):
            for col in range(width):
                if grid[row0][col] != 0 and grid[row0][col] == grid[row1][col] and all(
                    grid[row][col] != 0 for row in range(row0, row1 + 1)
                ):
                    segments[(row0, row1)].append(col)
    candidates = []
    for row0 in range(height):
        for row1 in range(row0 + 2, height):
            for col_left, col_right in combinations(segments.get((row0, row1), ()), 2):
                crop_cells = tuple(
                    (row, col)
                    for row, col in nonzero
                    if not (row0 <= row <= row1 and col in (col_left, col_right))
                )
                if not crop_cells:
                    continue
                crop_bbox = _bbox(crop_cells)
                outer_h, outer_w = row1 - row0 + 1, col_right - col_left + 1
                crop_h = crop_bbox[2] - crop_bbox[0] + 1
                crop_w = crop_bbox[3] - crop_bbox[1] + 1
                if crop_h == outer_h - 2 and crop_w == outer_w - 2:
                    candidates.append((row0, row1, col_left, col_right, *crop_bbox))
    return tuple(candidates)


def _facts_for_candidate(grid, candidate):
    row0, row1, col_left, col_right, crop_row0, crop_col0, crop_row1, crop_col1 = candidate
    outer_h, outer_w = row1 - row0 + 1, col_right - col_left + 1
    inner_h, inner_w = outer_h - 2, outer_w - 2
    left_color, right_color = grid[row0 + 1][col_left], grid[row0 + 1][col_right]
    crop = tuple(
        tuple(grid[crop_row0 + row][crop_col0 + col] for col in range(inner_w))
        for row in range(inner_h)
    )

    def score(flipped):
        total = 0
        for row in range(inner_h):
            for col in range(inner_w):
                source_col = inner_w - 1 - col if flipped else col
                value = crop[row][source_col]
                total += (col < inner_w // 2 and value == left_color) or (
                    col >= (inner_w + 1) // 2 and value == right_color
                )
        return total

    direct_score, flip_score = score(False), score(True)
    flipped = flip_score > direct_score
    output = [[0 for _ in range(outer_w)] for _ in range(outer_h)]
    for row in range(outer_h):
        output[row][0] = grid[row0 + row][col_left]
        output[row][-1] = grid[row0 + row][col_right]
        if 0 < row < outer_h - 1:
            for col in range(inner_w):
                source_col = inner_w - 1 - col if flipped else col
                output[row][col + 1] = crop[row - 1][source_col]
    return {
        "candidate": candidate,
        "frame_bbox": (row0, col_left, row1, col_right),
        "crop_bbox": (crop_row0, crop_col0, crop_row1, crop_col1),
        "outer_height": outer_h,
        "outer_width": outer_w,
        "inner_height": inner_h,
        "inner_width": inner_w,
        "left_color": left_color,
        "right_color": right_color,
        "left_wall": tuple(grid[row][col_left] for row in range(row0, row1 + 1)),
        "right_wall": tuple(grid[row][col_right] for row in range(row0, row1 + 1)),
        "crop": crop,
        "direct_score": direct_score,
        "flip_score": flip_score,
        "flipped": flipped,
        "output": output,
    }


def _extract_facts(grid):
    candidates = _find_candidates(grid)
    if not candidates:
        return {"errors": ["no canonical guide/crop candidate exists"], "candidates": ()}
    facts = _facts_for_candidate(grid, candidates[0])
    facts["errors"] = []
    facts["candidates"] = candidates
    return facts


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _placement(facts):
    frame_row0, frame_col0, frame_row1, frame_col1 = facts["frame_bbox"]
    crop_row0, crop_col0, crop_row1, _ = facts["crop_bbox"]
    if crop_row1 < frame_row0:
        return "above"
    if crop_row0 > frame_row1:
        return "below"
    if crop_col0 > frame_col1:
        return "right"
    return None


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    interior_pairs = tuple(zip(facts["left_wall"][1:-1], facts["right_wall"][1:-1]))
    if any(pair != interior_pairs[0] for pair in interior_pairs[1:]):
        return "variegated_walls"
    if facts["direct_score"] == facts["flip_score"]:
        return "tie_direct"
    center = facts["inner_width"] // 2
    if facts["inner_width"] % 2 and any(row[center] in (facts["left_color"], facts["right_color"]) for row in facts["crop"]):
        return "odd_center_ignored"
    crop_colors = {value for row in facts["crop"] for value in row} - {0, facts["left_color"], facts["right_color"]}
    if crop_colors:
        return "multicolor_crop"
    placement = _placement(facts)
    if placement in ("above", "below", "right"):
        return ("flip_" if facts["flipped"] else "direct_") + placement
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    public = profile in PUBLIC_PROFILES
    marker_left, marker_right = facts["left_wall"][0], facts["right_wall"][0]
    if not public and len(facts["candidates"]) != 1:
        errors.append("generalized lessons require exactly one canonical candidate")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared frame/crop profile")
    if not public and _placement(facts) not in ("above", "below", "right"):
        errors.append("generalized crop must be spatially separate from the frame")
    if marker_left == 0 or marker_right == 0:
        errors.append("guide endpoints must be nonzero")
    if not public and marker_left != marker_right:
        errors.append("generalized guide endpoints must share one marker color")
    if facts["left_color"] == facts["right_color"]:
        errors.append("first interior guide colors must differ")
    if not 4 <= facts["outer_height"] <= 12 or not 5 <= facts["outer_width"] <= 12:
        errors.append("output frame dimensions must remain pedagogically substantial")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    if len({value for row in grid for value in row if value}) < 3:
        errors.append("input needs marker plus two distinct side colors")
    if profile == "tie_direct" and facts["flipped"]:
        errors.append("score ties must remain direct")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, profile, rng):
    bands = {
        None: ((4, 9), (4, 8)),
        "easy": ((4, 6), (3, 5)),
        "medium": ((5, 8), (4, 7)),
        "hard": ((7, 10), (6, 9)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    outer_h = rng.randint(h0, h1)
    inner_w = rng.randint(w0, w1)
    if profile == "odd_center_ignored":
        if inner_w % 2 == 0:
            inner_w += 1 if inner_w < w1 else -1
    elif inner_w % 2:
        inner_w += 1 if inner_w < w1 else -1
    return outer_h, inner_w


def _crop_pattern(inner_h, inner_w, left, right, accents, profile):
    rows = []
    for row in range(inner_h):
        values = []
        for col in range(inner_w):
            if (row + col) % 3 == 2:
                value = 0
            elif profile == "tie_direct":
                value = accents[(row + col) % len(accents)]
            else:
                raw_flip = profile.startswith("flip_")
                left_half = col < inner_w // 2
                right_half = col >= (inner_w + 1) // 2
                if not left_half and not right_half:
                    value = left if row % 2 == 0 else right
                else:
                    direct = left if left_half else right
                    value = right if raw_flip and left_half else left if raw_flip and right_half else direct
                if profile == "multicolor_crop" and value and (row + 2 * col) % 5 == 0:
                    value = accents[(row + col) % len(accents)]
            values.append(value)
        rows.append(values)
    # Guarantee every bbox side is represented without creating three-cell vertical runs.
    if not any(rows[0]):
        rows[0][0] = accents[0] if profile == "tie_direct" else (right if profile.startswith("flip_") else left)
    if not any(rows[-1]):
        rows[-1][-1] = accents[-1] if profile == "tie_direct" else (left if profile.startswith("flip_") else right)
    if not any(row[0] for row in rows):
        rows[0][0] = accents[0] if profile == "tie_direct" else (right if profile.startswith("flip_") else left)
    if not any(row[-1] for row in rows):
        rows[-1][-1] = accents[-1] if profile == "tie_direct" else (left if profile.startswith("flip_") else right)
    return rows


def _candidate_scene(difficulty, profile, rng, colors):
    outer_h, inner_w = _dimensions(difficulty, profile, rng)
    inner_h, outer_w = outer_h - 2, inner_w + 2
    marker, left, right, accent1, accent2 = colors
    placement = profile.rsplit("_", 1)[-1] if profile.startswith(("direct_", "flip_")) else "right"
    gap = rng.randint(1, 3)
    top, left_margin = rng.randint(1, 3), rng.randint(1, 3)
    if placement == "above":
        crop_row0, crop_col0 = top, left_margin + rng.randint(0, 2)
        frame_row0, col_left = crop_row0 + inner_h + gap, left_margin
    elif placement == "below":
        frame_row0, col_left = top, left_margin
        crop_row0, crop_col0 = frame_row0 + outer_h + gap, left_margin + rng.randint(0, 2)
    else:
        frame_row0, col_left = top, left_margin
        crop_row0, crop_col0 = frame_row0 + 1, col_left + outer_w + gap
    frame_row1, col_right = frame_row0 + outer_h - 1, col_left + outer_w - 1
    crop = _crop_pattern(inner_h, inner_w, left, right, (accent1, accent2), profile)
    height = max(frame_row1, crop_row0 + inner_h - 1) + rng.randint(2, 4)
    width = max(col_right, crop_col0 + inner_w - 1) + rng.randint(2, 4)
    if height > 30 or width > 30:
        return None
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for offset in range(outer_h):
        if offset in (0, outer_h - 1):
            left_value = right_value = marker
        elif profile == "variegated_walls" and offset > 1:
            left_value = accent1 if offset % 2 == 0 else left
            right_value = accent2 if offset % 2 == 0 else right
        else:
            left_value, right_value = left, right
        grid[frame_row0 + offset][col_left] = left_value
        grid[frame_row0 + offset][col_right] = right_value
    for row in range(inner_h):
        for col in range(inner_w):
            grid[crop_row0 + row][crop_col0 + col] = crop[row][col]
    return grid


def _general_scene(difficulty, profile, rng, colors):
    for _ in range(400):
        grid = _candidate_scene(difficulty, profile, rng, colors)
        if grid is None:
            continue
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
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    weighted = PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 6
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    colors = ctx.draw_distinct_colors("colors", n=5, exclude={0})
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"), colors)
