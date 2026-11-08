"""Semantic generator for ARC task 23ef3502f576.

A one-row header contains one, two, or three cells of one selector color.
Three equal-sized candidate panels follow, separated by full color-9 rows.
The selector count chooses candidate one, two, or three; the output preserves
that candidate's occupied cells in place and recolors them cyan (8).
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_horizontal_panels

GENERATOR_ID = "23ef3502f576"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "86a806e40780"
SUMMARY = "Count the one-row header markers, select that indexed candidate panel, and recolor its occupied cells cyan (8)."
INVARIANTS = [
    "one header and three equal-sized candidate panels are separated by complete color-9 rows",
    "the header contains exactly one selector color in one, two, or three occupied cells",
    "each candidate contains one distinct nonzero color on black and one connected allowed shape",
    "the header count selects candidate one, two, or three without using marker position, palette, or object size",
    "the output keeps the selected candidate's canvas and occupied coordinates but recolors every occupied cell to 8",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
GENERAL_PROFILES = (
    "choice_1_general",
    "choice_2_general",
    "choice_3_general",
    "equal_cell_counts",
    "duplicate_shape_decoys",
    "scattered_header",
    "varied_palette",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng over three exact public and seven generalized selector lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "7700", "9999", "2000", "2000", "2200", "0000", "9999", "0000",
        "0330", "0330", "0000", "9999", "0000", "0400", "4440", "0000",
    ),
    "public_train_2": (
        "7770", "9999", "0220", "0000", "0000", "0000", "9999", "3030",
        "3330", "0000", "0000", "9999", "0000", "4400", "0440", "0000",
    ),
    "public_test_1": (
        "7000", "9999", "2000", "2000", "2220", "0000", "9999", "0000",
        "0000", "3300", "3300", "9999", "0040", "0444", "0000", "0000",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}

# Finite connected-shape grammar. It includes every normalized canonical shape
# and several same-size alternatives so count, shape, and panel index cannot be
# collapsed into one another.
_SHAPES = {
    "horizontal_domino": ((0, 0), (0, 1)),
    "vertical_domino": ((0, 0), (1, 0)),
    "horizontal_triomino": ((0, 0), (0, 1), (0, 2)),
    "vertical_triomino": ((0, 0), (1, 0), (2, 0)),
    "ell_triomino": ((0, 0), (1, 0), (1, 1)),
    "square_tetromino": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "tee_tetromino": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "zigzag_tetromino": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "ell_tetromino": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "horizontal_tetromino": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "u_pentomino": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "ell_pentomino": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "tee_pentomino": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "pee_pentomino": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "stair_pentomino": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "rectangle_hexomino": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "stair_hexomino": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    "tee_hexomino": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1)),
}
_ALLOWED_SHAPES = tuple(sorted({tuple(sorted(shape)) for shape in _SHAPES.values()}))
_SHAPES_BY_SIZE = {
    size: tuple(shape for shape in _ALLOWED_SHAPES if len(shape) == size)
    for size in sorted({len(shape) for shape in _ALLOWED_SHAPES})
}
_CANONICAL_PALETTE = (7, (2, 3, 4))
_VARIED_PALETTES = (
    (1, (2, 4, 6)),
    (2, (1, 5, 7)),
    (3, (1, 4, 6)),
    (4, (2, 5, 7)),
    (5, (1, 3, 6)),
    (6, (2, 4, 7)),
    (7, (1, 3, 5)),
)


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions {height}x{width} exceed the ARC 1..30 bounds"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _is_contiguous(columns):
    ordered = tuple(sorted(columns))
    return bool(ordered) and ordered == tuple(range(ordered[0], ordered[-1] + 1))


def _extract_structure(grid):
    """Parse the broad rule domain and independently compute its output."""
    errors = _grid_errors(grid)
    result = {
        "errors": errors,
        "height": len(grid) if isinstance(grid, (list, tuple)) else 0,
        "width": len(grid[0]) if isinstance(grid, (list, tuple)) and grid and isinstance(grid[0], (list, tuple)) else 0,
        "choice": None,
        "selector_color": None,
        "candidate_colors": (),
        "candidate_cells": (),
        "normalized_shapes": (),
        "counts": (),
        "header_columns": (),
        "header_contiguous": False,
        "panel_height": None,
        "output": None,
    }
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    dividers = [row for row, values in enumerate(grid) if all(value == 9 for value in values)]
    if len(dividers) != 3:
        errors.append(f"expected exactly three complete color-9 divider rows, found {len(dividers)}")
        return result
    d0, d1, d2 = dividers
    if d0 != 1:
        errors.append("the first divider must follow a one-row header")
    segments = (grid[:d0], grid[d0 + 1:d1], grid[d1 + 1:d2], grid[d2 + 1:])
    if any(not segment for segment in segments):
        errors.append("header and all three candidate panels must be non-empty")
        return result
    header, *panels = segments
    panel_heights = {len(panel) for panel in panels}
    if len(panel_heights) != 1:
        errors.append("all three candidate panels must have equal height")
        return result
    panel_height = len(panels[0])
    result["panel_height"] = panel_height
    if not 4 <= panel_height <= 7 or not 4 <= width <= 10:
        errors.append(f"candidate dimensions {panel_height}x{width} are outside the supported 4..7 by 4..10 grammar")

    header_nonzero = [(0, col, value) for col, value in enumerate(header[0]) if value != 0]
    header_colors = {value for _, _, value in header_nonzero}
    if not 1 <= len(header_nonzero) <= 3:
        errors.append(f"the header must contain one, two, or three occupied cells, found {len(header_nonzero)}")
    if len(header_colors) != 1:
        errors.append("all occupied header cells must share exactly one selector color")
        selector_color = None
    else:
        selector_color = next(iter(header_colors))
        if selector_color in (8, 9):
            errors.append("the selector color cannot be output cyan (8) or divider maroon (9)")
    if any(value not in ({0} | header_colors) for value in header[0]):
        errors.append("the header may contain only black and its selector color")
    choice = len(header_nonzero) if 1 <= len(header_nonzero) <= 3 else None
    header_columns = tuple(col for _, col, _ in header_nonzero)

    candidate_colors = []
    candidate_cells = []
    normalized_shapes = []
    counts = []
    for index, panel in enumerate(panels, start=1):
        colors = {value for row in panel for value in row if value != 0}
        if len(colors) != 1:
            errors.append(f"candidate {index} must contain exactly one nonzero color, found {sorted(colors)}")
            candidate_colors.append(None)
            candidate_cells.append(())
            normalized_shapes.append(())
            counts.append(0)
            continue
        color = next(iter(colors))
        if color in (8, 9):
            errors.append(f"candidate {index} cannot use output cyan (8) or divider maroon (9)")
        cells = tuple(sorted((row, col) for row, values in enumerate(panel) for col, value in enumerate(values) if value != 0))
        if not _connected(cells):
            errors.append(f"candidate {index} occupied cells must be one 4-connected object")
        candidate_colors.append(color)
        candidate_cells.append(cells)
        normalized_shapes.append(_normalize(cells) if cells else ())
        counts.append(len(cells))

    concrete_colors = [color for color in candidate_colors if color is not None]
    if len(concrete_colors) == 3 and len(set(concrete_colors)) != 3:
        errors.append("candidate colors must be pairwise distinct")
    if selector_color is not None and selector_color in concrete_colors:
        errors.append("the selector color must differ from every candidate color")

    output = None
    if choice is not None and len(candidate_cells) == 3 and candidate_cells[choice - 1]:
        output = full_grid(panel_height, width, 0)
        for row, col in candidate_cells[choice - 1]:
            output[row][col] = 8

    result.update(
        {
            "choice": choice,
            "selector_color": selector_color,
            "candidate_colors": tuple(candidate_colors),
            "candidate_cells": tuple(candidate_cells),
            "normalized_shapes": tuple(normalized_shapes),
            "counts": tuple(counts),
            "header_columns": header_columns,
            "header_contiguous": _is_contiguous(header_columns),
            "output": output,
        }
    )
    return result


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public

    # Reserve the canonical 16x4 canvas for exact public examples. This makes
    # recombined or lightly corrupted public pieces reject instead of being
    # relabeled as a generalized lesson.
    if facts["height"] == 16 and facts["width"] == 4:
        return None

    shapes = facts["normalized_shapes"]
    counts = facts["counts"]
    if any(shape not in _ALLOWED_SHAPES for shape in shapes):
        return None
    palette = (facts["selector_color"], facts["candidate_colors"])
    canonical_palette = palette == _CANONICAL_PALETTE
    shapes_distinct = len(set(shapes)) == 3
    counts_distinct = len(set(counts)) == 3

    if not canonical_palette:
        if facts["header_contiguous"] and shapes_distinct and counts_distinct:
            return "varied_palette"
        return None
    if not facts["header_contiguous"]:
        if shapes_distinct and counts_distinct and facts["choice"] in (2, 3):
            return "scattered_header"
        return None
    if len(set(counts)) == 1 and shapes_distinct:
        return "equal_cell_counts"
    if (
        len(shapes) == 3
        and shapes[0] == shapes[1] != shapes[2]
        and facts["candidate_cells"][0] != facts["candidate_cells"][1]
    ):
        return "duplicate_shape_decoys"
    if shapes_distinct and counts_distinct and facts["choice"] in (1, 2, 3):
        return f"choice_{facts['choice']}_general"
    return None


def _analysis(grid):
    facts = _extract_structure(grid)
    errors = list(facts["errors"])
    profile = None
    if not errors:
        profile = _profile_for(grid, facts)
        if profile not in SCENE_PROFILES:
            errors.append("grid does not match an exact public or declared generalized scene profile")
        if facts["output"] is None:
            errors.append("the selector must resolve to one nonempty candidate output")
        elif facts["output"] == [list(row) for row in grid]:
            errors.append("the lesson must visibly transform into a candidate-sized cyan output")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def rule_mirror(grid):
    """Independent Python mirror used only to test the canonical Racket rule."""
    facts = _extract_structure(grid)
    if facts["errors"] or facts["output"] is None:
        raise ValueError("; ".join(facts["errors"] or ["selector did not resolve to a candidate"]))
    return [row[:] for row in facts["output"]]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def scene_profile_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if not analysis["errors"] else None


def semantic_signature(grid):
    analysis = _analysis(grid)
    facts = analysis["facts"]
    return {
        "scene_profile": analysis["scene_profile"],
        "choice": facts["choice"],
        "panel_height": facts["panel_height"],
        "panel_width": facts["width"],
        "counts": facts["counts"],
        "header_contiguous": facts["header_contiguous"],
        "palette": (facts["selector_color"], facts["candidate_colors"]),
        "shapes": facts["normalized_shapes"],
    }


def observe_overrides(grid):
    profile = scene_profile_signature(grid)
    return {"scene_profile": profile} if profile is not None else {}


def _shape_dimensions(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _placements(shape, height, width):
    shape_height, shape_width = _shape_dimensions(shape)
    return tuple(
        tuple(sorted((row0 + row, col0 + col) for row, col in shape))
        for row0 in range(height - shape_height + 1)
        for col0 in range(width - shape_width + 1)
    )


def _place_shape(shape, height, width, rng):
    placements = _placements(shape, height, width)
    if not placements:
        raise ValueError(f"shape {shape!r} does not fit in {height}x{width}")
    return rng.choice(placements)


def _distinct_count_shapes(rng):
    sizes = rng.sample(tuple(_SHAPES_BY_SIZE), 3)
    shapes = [rng.choice(_SHAPES_BY_SIZE[size]) for size in sizes]
    rng.shuffle(shapes)
    return tuple(shapes)


def _equal_count_shapes(rng):
    size = rng.choice(tuple(size for size, shapes in _SHAPES_BY_SIZE.items() if len(shapes) >= 3))
    return tuple(rng.sample(_SHAPES_BY_SIZE[size], 3))


def _duplicate_shape_set(rng):
    duplicate = rng.choice(tuple(shape for shape in _ALLOWED_SHAPES if len(_placements(shape, 4, 5)) >= 2))
    other_sizes = tuple(size for size in _SHAPES_BY_SIZE if size != len(duplicate))
    other = rng.choice(_SHAPES_BY_SIZE[rng.choice(other_sizes)])
    return duplicate, duplicate, other


def _dimensions(difficulty, rng):
    choices = {
        None: ((4, 5), (4, 6), (5, 5), (5, 7), (6, 6), (6, 8), (7, 9)),
        "easy": ((4, 5), (4, 6), (5, 5), (5, 6)),
        "medium": ((5, 6), (5, 7), (6, 6), (6, 8)),
        "hard": ((6, 8), (6, 9), (7, 8), (7, 9), (7, 10)),
    }
    return rng.choice(choices[difficulty])


def _header_columns(choice, width, rng, *, scattered):
    options = tuple(combinations(range(width), choice))
    if scattered:
        options = tuple(columns for columns in options if not _is_contiguous(columns))
    else:
        options = tuple(columns for columns in options if _is_contiguous(columns))
    if not options:
        raise ValueError(f"no {'scattered' if scattered else 'contiguous'} header layout for choice={choice}, width={width}")
    return rng.choice(options)


def _panel(height, width, cells, color):
    panel = full_grid(height, width, 0)
    for row, col in cells:
        panel[row][col] = color
    return panel


def _general_scene(difficulty, profile, rng):
    panel_height, panel_width = _dimensions(difficulty, rng)
    if profile.startswith("choice_"):
        choice = int(profile.split("_")[1])
    elif profile == "scattered_header":
        choice = rng.choice((2, 3))
    else:
        choice = rng.choice((1, 2, 3))

    if profile == "equal_cell_counts":
        shapes = _equal_count_shapes(rng)
    elif profile == "duplicate_shape_decoys":
        shapes = _duplicate_shape_set(rng)
    else:
        shapes = _distinct_count_shapes(rng)

    placed = []
    if profile == "duplicate_shape_decoys":
        duplicate_placements = _placements(shapes[0], panel_height, panel_width)
        first, second = rng.sample(duplicate_placements, 2)
        placed.extend((first, second))
        placed.append(_place_shape(shapes[2], panel_height, panel_width, rng))
    else:
        placed.extend(_place_shape(shape, panel_height, panel_width, rng) for shape in shapes)

    selector_color, candidate_colors = (
        rng.choice(_VARIED_PALETTES) if profile == "varied_palette" else _CANONICAL_PALETTE
    )
    columns = _header_columns(
        choice,
        panel_width,
        rng,
        scattered=profile == "scattered_header",
    )
    header = full_grid(1, panel_width, 0)
    for col in columns:
        header[0][col] = selector_color
    panels = [
        _panel(panel_height, panel_width, cells, color)
        for cells, color in zip(placed, candidate_colors)
    ]
    grid = assemble_horizontal_panels([header] + panels, divider=9)
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError((profile, analysis["errors"], analysis["scene_profile"], semantic_signature(grid)))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
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
    # Public scenes remain materially reachable, while generalized profiles are
    # weighted more heavily to teach invariance rather than template recall.
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
