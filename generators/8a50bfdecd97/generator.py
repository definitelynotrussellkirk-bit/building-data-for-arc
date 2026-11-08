"""Semantic generator for ARC task 8a50bfdecd97.

Two color-4 brackets occupy diagonal corners of a color-7 canvas.  A colored
shape is moved into the missing fourth corner: its destination row is aligned
to the bracket on the shape's horizontal side, while its destination columns
are the open interior columns of the opposite-side bracket.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "8a50bfdecd97"
TASK_ID = GENERATOR_ID
VERSION = "4.2.0"
RULE_HASH = "f2d83965d9c2"
SUMMARY = "Move a colored pattern to the missing corner using one diagonal bracket for row alignment and the other bracket for interior-column alignment."
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
INVARIANTS = [
    "the background is color 7 and exactly two disconnected three-sided brackets are color 4",
    "the brackets occupy diagonally opposite top/bottom and left/right positions",
    "exactly one other color forms the movable pattern",
    "the pattern keeps its bitmap while its original cells become background",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
GENERAL_MASKS = {
    "pattern_pixel": ("1",),
    "pattern_hbar3": ("111",),
    "pattern_vbar3": ("1", "1", "1"),
    "pattern_block2": ("11", "11"),
    "pattern_tee_right": ("10", "11", "10"),
    "pattern_ell": ("10", "10", "11"),
    "pattern_cross": ("010", "111", "010"),
    "pattern_stair": ("110", "011"),
    "pattern_hollow3": ("111", "101", "111"),
}
GENERAL_PROFILES = tuple(GENERAL_MASKS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index parity alternates transparent-bitmap and solid-bitmap profile pools",
        "valid": "public_train_1|public_train_2|public_train_3|public_test_1|pattern_pixel|pattern_hbar3|pattern_vbar3|pattern_block2|pattern_tee_right|pattern_ell|pattern_cross|pattern_stair|pattern_hollow3",
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "444477777", "477477777", "777777777", "777777777", "777777117",
        "777777117", "777777777", "777774774", "777774444",
    ),
    "public_train_2": (
        "77777444", "72777474", "72777777", "72777777",
        "77777777", "77777777", "47477777", "44477777",
    ),
    "public_train_3": (
        "777774444", "777774774", "787777777", "788777777", "787777777",
        "777777777", "777777777", "477477777", "444477777",
    ),
    "public_test_1": (
        "77777444", "77777474", "77777777", "77777777",
        "77377777", "77777777", "74747777", "74447777",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}


def _shape_signature(grid):
    colors = {value for row in grid for value in row} - {4, 7}
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    if not cells:
        return None
    row1 = min(row for row, _col in cells)
    col1 = min(col for _row, col in cells)
    row2 = max(row for row, _col in cells)
    col2 = max(col for _row, col in cells)
    mask = tuple(
        "".join(
            "1" if (row, col) in cells else "0"
            for col in range(col1, col2 + 1)
        )
        for row in range(row1, row2 + 1)
    )
    return len(grid), len(grid[0]), mask


_PUBLIC_FAMILY_SIGNATURES = {
    _shape_signature(grid): name for name, grid in _PUBLIC_INPUTS.items()
}
_MASK_TO_PROFILE = {mask: name for name, mask in GENERAL_MASKS.items()}

# Four-pair production lessons use three demonstrations and one query.  Every
# consecutive window of four sample indices therefore contains two profiles
# from each pool.  The even-index pool guarantees an interior-zero bitmap, so
# removing any one pair still leaves a demonstration that refutes the tempting
# "move the filled bounding box" shortcut.
TRANSPARENT_PROFILES = (
    "public_train_3",
    "pattern_tee_right",
    "pattern_ell",
    "pattern_cross",
    "pattern_stair",
    "pattern_hollow3",
)
SOLID_PROFILES = tuple(
    profile for profile in SCENE_PROFILES if profile not in TRANSPARENT_PROFILES
)


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        todo = [min(remaining)]
        component = set()
        while todo:
            cell = todo.pop()
            if cell not in remaining:
                continue
            remaining.remove(cell)
            component.add(cell)
            r, c = cell
            todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
        result.append(component)
    return sorted(result, key=lambda component: min(component))


def _bbox(cells):
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _bracket(component):
    r1, c1, r2, c2 = _bbox(component)
    if r2 <= r1 or c2 - c1 < 2:
        return None
    top_expected = {(r1, c) for c in range(c1, c2 + 1)} | {
        (r, c) for r in range(r1 + 1, r2 + 1) for c in (c1, c2)
    }
    bottom_expected = {(r2, c) for c in range(c1, c2 + 1)} | {
        (r, c) for r in range(r1, r2) for c in (c1, c2)
    }
    if component == top_expected:
        orientation = "top"
    elif component == bottom_expected:
        orientation = "bottom"
    else:
        return None
    return {"bbox": (r1, c1, r2, c2), "cells": component, "orientation": orientation}


def _side(center, midpoint):
    return "left" if center < midpoint else "right"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    colors = {value for row in grid for value in row}
    shape_colors = colors - {4, 7}
    if len(shape_colors) != 1:
        errors.append(f"expected exactly one movable color, found {sorted(shape_colors)}")
        return result
    shape_color = next(iter(shape_colors))
    shape_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == shape_color}
    if not shape_cells:
        errors.append("missing movable pattern")
        return result
    sr1, sc1, sr2, sc2 = _bbox(shape_cells)
    sh, sw = sr2 - sr1 + 1, sc2 - sc1 + 1
    mask = tuple(
        "".join("1" if (r, c) in shape_cells else "0" for c in range(sc1, sc2 + 1))
        for r in range(sr1, sr2 + 1)
    )
    if any("1" not in row for row in mask) or any(
        all(row[index] == "0" for row in mask) for index in range(sw)
    ):
        errors.append("movable pattern bbox has an empty edge")

    four_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    components = _components(four_cells)
    if len(components) != 2:
        errors.append(f"expected two color-4 bracket objects, found {len(components)}")
        return result
    brackets = [_bracket(component) for component in components]
    if any(bracket is None for bracket in brackets):
        errors.append("color-4 objects must be exact three-sided brackets")
        return result
    top = [bracket for bracket in brackets if bracket["orientation"] == "top"]
    bottom = [bracket for bracket in brackets if bracket["orientation"] == "bottom"]
    if len(top) != 1 or len(bottom) != 1:
        errors.append("expected one downward-opening top bracket and one upward-opening bottom bracket")
        return result
    midpoint = w / 2.0
    for bracket in brackets:
        r1, c1, r2, c2 = bracket["bbox"]
        bracket["side"] = _side((c1 + c2) / 2.0, midpoint)
    if top[0]["side"] == bottom[0]["side"]:
        errors.append("brackets must occupy diagonally opposite sides")
        return result
    if (sum(top[0]["bbox"][::2]) / 2.0) >= h / 2.0 or (sum(bottom[0]["bbox"][::2]) / 2.0) <= h / 2.0:
        errors.append("top and bottom brackets must lie on opposite vertical halves")

    shape_side = _side((sc1 + sc2) / 2.0, midpoint)
    row_brackets = [bracket for bracket in brackets if bracket["side"] == shape_side]
    column_brackets = [bracket for bracket in brackets if bracket["side"] != shape_side]
    if len(row_brackets) != 1 or len(column_brackets) != 1:
        errors.append("movable pattern must be horizontally aligned with exactly one bracket")
        return result
    row_bracket, column_bracket = row_brackets[0], column_brackets[0]
    rr1, rc1, rr2, rc2 = row_bracket["bbox"]
    cr1, cc1, cr2, cc2 = column_bracket["bbox"]
    interior_columns = [
        c for c in range(cc1, cc2 + 1)
        if any((r, c) not in column_bracket["cells"] for r in range(cr1, cr2 + 1))
    ]
    if len(interior_columns) < sw:
        errors.append("movable pattern is wider than the opposite bracket interior")
        return result
    nr = rr2 - sh + 1 if (rr1 + rr2) / 2.0 > h / 2.0 else rr1
    nc = max(interior_columns) - sw + 1 if (cc1 + cc2) / 2.0 > midpoint else min(interior_columns)
    if nr < 0 or nc < 0 or nr + sh > h or nc + sw > w:
        errors.append("computed destination falls outside the canvas")
        return result
    destination_bbox = (nr, nc, nr + sh - 1, nc + sw - 1)
    source_bbox = (sr1, sc1, sr2, sc2)
    source_and_destination = shape_cells & {
        (nr + r, nc + c)
        for r, row in enumerate(mask) for c, value in enumerate(row) if value == "1"
    }
    if source_and_destination:
        errors.append("source and destination pattern cells must be disjoint")

    output = []
    for r, row in enumerate(grid):
        out_row = []
        for c, value in enumerate(row):
            if nr <= r < nr + sh and nc <= c < nc + sw:
                source_value = grid[sr1 + r - nr][sc1 + c - nc]
                out_row.append(shape_color if source_value == shape_color else value)
            elif value == shape_color:
                out_row.append(7)
            else:
                out_row.append(value)
        output.append(out_row)

    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None and not errors:
        profile = _PUBLIC_FAMILY_SIGNATURES.get((h, w, mask))
    if profile is None and not errors:
        profile = _MASK_TO_PROFILE.get(mask)
    if profile not in SCENE_PROFILES:
        errors.append(f"movable bitmap {mask!r} does not match a declared profile")
    result.update({
        "shape_color": shape_color,
        "shape_cells": shape_cells,
        "shape_bbox": source_bbox,
        "shape_mask": mask,
        "shape_side": shape_side,
        "brackets": brackets,
        "row_bracket": row_bracket,
        "column_bracket": column_bracket,
        "destination_bbox": destination_bbox,
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def strict_canonical_like(grid):
    """Executable definition of the generator's reviewed semantic domain."""
    return self_check(grid)


def _copy_instead_of_move(grid):
    """Wrong rival: place the bitmap correctly but retain its source cells."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["output"]]
    color = analysis["shape_color"]
    for row, col in analysis["shape_cells"]:
        output[row][col] = color
    return output


def _solid_bbox(grid):
    """Wrong rival: move a filled rectangle instead of the transparent bitmap."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["output"]]
    row1, col1, row2, col2 = analysis["destination_bbox"]
    color = analysis["shape_color"]
    for row in range(row1, row2 + 1):
        for col in range(col1, col2 + 1):
            output[row][col] = color
    return output


def _source_erasure_witness(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["shape_cells"])


def _transparent_bitmap_witness(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        "0" in row for row in analysis["shape_mask"]
    )


SEMANTIC_RIVALS = {
    "copy_instead_of_move": _copy_instead_of_move,
    "solid_bbox": _solid_bbox,
}
SEMANTIC_WITNESSES = {
    "source_erasure": _source_erasure_witness,
    "transparent_bitmap": _transparent_bitmap_witness,
}
WITNESS_RIVALS = {
    "source_erasure": ["copy_instead_of_move"],
    "transparent_bitmap": ["solid_bbox"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report a declared wrong rule that fits all demos but changes the query."""
    reasons = []
    query_output = query.get("output") if isinstance(query, dict) else None
    if query_output is None and isinstance(query, dict):
        query_output = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        fits = all(
            rival(deepcopy(demo["input"])) == demo["output"]
            for demo in demos
        )
        if fits and query_output is not None:
            prediction = rival(deepcopy(query["input"]))
            if prediction != query_output:
                reasons.append(
                    f"{name} fits every demonstration but changes the query"
                )
    return reasons


def _draw_bracket(grid, r1, c1, height, width, orientation):
    r2, c2 = r1 + height - 1, c1 + width - 1
    edge = r1 if orientation == "top" else r2
    for c in range(c1, c2 + 1):
        grid[edge][c] = 4
    for r in range(r1, r2 + 1):
        grid[r][c1] = 4
        grid[r][c2] = 4


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _general(rng, profile, band):
    mask = GENERAL_MASKS[profile]
    sh, sw = len(mask), len(mask[0])
    # Two minimum-width brackets fit on opposite sides with one center column.
    # Keeping the easy band this compact makes canonical 8x8/9x9 scale a
    # structural property instead of relying on an exact-public draw appearing
    # in a small audit seed window.
    minimum_width = 2 * (sw + 2) + 1
    # Keep generalized canvases near the canonical 8x8/9x9 scale while still
    # separating the three difficulty bands and varying both dimensions.
    width_offsets = {"easy": (0, 1), "medium": (1, 3), "hard": (3, 6)}
    lo, hi = width_offsets[band]
    w = min(30, minimum_width + rng.randint(lo, hi))
    # Leave a guaranteed background row band between the largest jittered
    # four-row brackets, even for three-row movable patterns.
    minimum_height = max(10, sh + 8)
    height_offsets = {"easy": (0, 0), "medium": (1, 3), "hard": (3, 6)}
    lo, hi = height_offsets[band]
    h = min(30, minimum_height + rng.randint(lo, hi))
    grid = [[7] * w for _ in range(h)]

    minimum_bracket_width = sw + 2
    maximum_bracket_width = min(minimum_bracket_width + 2, (w - 1) // 2)
    left_width = rng.randint(minimum_bracket_width, maximum_bracket_width)
    right_width = rng.randint(minimum_bracket_width, maximum_bracket_width)
    top_height, bottom_height = rng.randint(2, 3), rng.randint(2, 3)
    left_col = rng.randint(0, 1)
    right_col = w - right_width - rng.randint(0, 1)
    top_row = rng.randint(0, 1)
    bottom_end = h - 1 - rng.randint(0, 1)
    bottom_row = bottom_end - bottom_height + 1
    top_side = rng.choice(("left", "right"))
    if top_side == "left":
        top_col, top_width = left_col, left_width
        bottom_col, bottom_width = right_col, right_width
    else:
        top_col, top_width = right_col, right_width
        bottom_col, bottom_width = left_col, left_width
    _draw_bracket(grid, top_row, top_col, top_height, top_width, "top")
    _draw_bracket(grid, bottom_row, bottom_col, bottom_height, bottom_width, "bottom")

    source_side = rng.choice((top_side, "right" if top_side == "left" else "left"))
    source_row = rng.randint(top_row + top_height, bottom_row - sh)
    if source_side == "left":
        source_col = rng.randint(0, (w - 1) // 2 - sw + 1)
    else:
        source_col = rng.randint((w + 1) // 2, w - sw)
    shape_color = rng.choice((0, 1, 2, 3, 5, 6, 8, 9))
    for dr, row in enumerate(mask):
        for dc, value in enumerate(row):
            if value == "1":
                grid[source_row + dr][source_col + dc] = shape_color
    return grid


def _public_variant(grid, rng):
    """Vary a canonical-scale scene without changing its structural rule.

    Exact public overrides remain byte-for-byte canonical.  Default draws use
    mostly reflected/recolored/source-relocated variants so the canonical
    8x8/9x9 profile floor does not collapse input diversity to four grids.
    """
    original = [row[:] for row in grid]
    if rng.randrange(8) == 0:
        return original

    reflections = (
        original,
        original[::-1],
        [row[::-1] for row in original],
        [row[::-1] for row in original[::-1]],
    )
    lawful_reflections = [
        reflected for reflected in reflections if not _analysis(reflected)["errors"]
    ]
    if not lawful_reflections:
        raise AssertionError("canonical scene has no lawful reflection")
    candidate = [row[:] for row in rng.choice(lawful_reflections)]
    analysis = _analysis(candidate)
    color = analysis["shape_color"]
    mask = analysis["shape_mask"]
    without_shape = [row[:] for row in candidate]
    for row, col in analysis["shape_cells"]:
        without_shape[row][col] = 7

    placements = []
    shape_h, shape_w = len(mask), len(mask[0])
    for top in range(len(candidate) - shape_h + 1):
        for left in range(len(candidate[0]) - shape_w + 1):
            placed = [row[:] for row in without_shape]
            for dr, mask_row in enumerate(mask):
                for dc, value in enumerate(mask_row):
                    if value == "1":
                        placed[top + dr][left + dc] = color
            if not _analysis(placed)["errors"]:
                placements.append(placed)
    if not placements:
        raise AssertionError("canonical-scale scene has no lawful source relocation")
    candidate = rng.choice(placements)

    analysis = _analysis(candidate)
    replacement = rng.choice(
        tuple(value for value in range(10) if value not in (4, 7, analysis["shape_color"]))
    )
    for row, col in analysis["shape_cells"]:
        candidate[row][col] = replacement
    errors = self_check(candidate)
    if errors:
        raise AssertionError(
            "canonical-scale variant left the reviewed domain: " + "; ".join(errors)
        )
    return candidate


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
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
    if requested is not None:
        weighted = SCENE_PROFILES
    elif sample_index % LESSON_SCHEDULE_PERIOD == 0:
        weighted = TRANSPARENT_PROFILES
    else:
        weighted = SOLID_PROFILES
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile in PUBLIC_PROFILES:
        if requested is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        return _public_variant(_PUBLIC_INPUTS[profile], ctx.draw_rng("layout"))
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
