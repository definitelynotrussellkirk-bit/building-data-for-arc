"""Semantic generator for ARC task 5553241d87bf.

All-zero rows and columns separate a board into cells.  The modal nonzero
color is the cell background.  The first cell in row-major order containing
a non-background, nonzero value is the template.  Copy that entire template
cell into every other cell containing at least one zero dot; preserve all
other cells and every separator.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5553241d87bf"
TASK_ID = "5553241d87bf"
VERSION = "3.0.1"
RULE_HASH = "064666b78c2e"
MIN_SYNTHETIC_CHANGE_RATE = 0.04
SUMMARY = "Infer a separator-delimited template cell and stamp it into every other cell marked by one or more zero dots."
INVARIANTS = [
    "complete all-zero rows and columns delimit the logical cells",
    "the modal nonzero color is the background",
    "the first cell containing a non-background nonzero value is the template",
    "every non-template cell containing any zero is replaced by the complete template",
    "unmarked cells, the template cell, and all separators remain unchanged",
    "template background and zero cells are copied as literally as foreground cells",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "cell3_corner_template",
    "cell3_center_template",
    "cell3_edge_template",
    "cell4_corner_template",
    "cell4_center_template",
    "cell4_edge_template",
    "cell5_corner_template",
    "cell5_center_template",
    "cell5_edge_template",
    "rectangular_cells",
    "multiple_dot_shapes",
    "template_with_zero",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and twelve recoverable self-stamping lessons",
        "valid": "public_1|public_2|public_3|cell3_corner_template|cell3_center_template|cell3_edge_template|cell4_corner_template|cell4_center_template|cell4_edge_template|cell5_corner_template|cell5_center_template|cell5_edge_template|rectangular_cells|multiple_dot_shapes|template_with_zero",
    }
}

_PUBLIC_ROWS = (
    "77777077777077777077777/77777077777077777077777/77777077077077777077777/77777077777077777077777/77777077777077777077777/00000000000000000000000/77777077777077777077777/77777077777077777077777/77777077077077777077777/77777077777077777077777/77777077777077777077777/00000000000000000000000/77777077777077799077777/77777077777077797077777/77777077777077797077077/77777077777079997077777/77777077777079777077777/00000000000000000000000/77777077777077777077777/77777077777077777077777/77077077777077777077077/77777077777077777077777/77777077777077777077777",
    "72707770777/72707770777/72707770777/00000000000/77707770777/77707070777/77707770777/00000000000/77707770777/77707070707/77707770777",
    "77777077777077477/77777077777044444/77777077777077477/77777077777074747/77777077777047774/00000000000000000/77777077777077777/77777077777077777/77777077077077777/77777077777077777/77777077777077777/00000000000000000/77777077777077777/77777077777077777/77077077777077077/77777077777077777/77777077777077777",
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
        return ["input cells must be literal integers from 0 through 9"]
    return []


def _bounds(size, separators):
    all_separators = (-1,) + tuple(separators) + (size,)
    return tuple((all_separators[index] + 1, all_separators[index + 1] - 1) for index in range(len(all_separators) - 1) if all_separators[index + 1] - all_separators[index] > 1)


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=lambda value: (counts[value], -value))
    separator_rows = tuple(row for row in range(height) if all(grid[row][col] == 0 for col in range(width)))
    separator_cols = tuple(col for col in range(width) if all(grid[row][col] == 0 for row in range(height)))
    row_bounds, col_bounds = _bounds(height, separator_rows), _bounds(width, separator_cols)
    if not separator_rows or not separator_cols or len(row_bounds) < 2 or len(col_bounds) < 2:
        return {"errors": ["at least two logical rows and columns with complete zero separators are required"]}
    cell_heights = {row1 - row0 + 1 for row0, row1 in row_bounds}
    cell_widths = {col1 - col0 + 1 for col0, col1 in col_bounds}
    if len(cell_heights) != 1 or len(cell_widths) != 1:
        return {"errors": ["all logical cells must have equal dimensions"]}
    template_index = None
    for row_index, (row0, row1) in enumerate(row_bounds):
        for col_index, (col0, col1) in enumerate(col_bounds):
            if any(grid[row][col] not in (0, background) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)):
                template_index = row_index, col_index
                break
        if template_index is not None:
            break
    if template_index is None:
        return {"errors": ["no non-background nonzero template cell found"]}
    template_rb, template_cb = row_bounds[template_index[0]], col_bounds[template_index[1]]
    pattern = tuple(tuple(grid[row][col] for col in range(template_cb[0], template_cb[1] + 1)) for row in range(template_rb[0], template_rb[1] + 1))
    targets, dot_counts = [], {}
    for row_index, (row0, row1) in enumerate(row_bounds):
        for col_index, (col0, col1) in enumerate(col_bounds):
            if (row_index, col_index) == template_index:
                continue
            zeros = sum(grid[row][col] == 0 for row in range(row0, row1 + 1) for col in range(col0, col1 + 1))
            if zeros:
                targets.append((row_index, col_index))
                dot_counts[(row_index, col_index)] = zeros
    output = [list(row) for row in grid]
    for row_index, col_index in targets:
        row0, _ = row_bounds[row_index]
        col0, _ = col_bounds[col_index]
        for drow, pattern_row in enumerate(pattern):
            for dcol, value in enumerate(pattern_row):
                output[row0 + drow][col0 + dcol] = value
    foreground = tuple((drow, dcol) for drow, pattern_row in enumerate(pattern) for dcol, value in enumerate(pattern_row) if value not in (0, background))
    pattern_zeros = tuple((drow, dcol) for drow, pattern_row in enumerate(pattern) for dcol, value in enumerate(pattern_row) if value == 0)
    return {
        "errors": [], "height": height, "width": width, "background": background,
        "separator_rows": separator_rows, "separator_cols": separator_cols,
        "row_bounds": row_bounds, "col_bounds": col_bounds, "cell_height": next(iter(cell_heights)),
        "cell_width": next(iter(cell_widths)), "template_index": template_index, "pattern": pattern,
        "foreground": foreground, "pattern_zeros": pattern_zeros, "targets": tuple(targets),
        "dot_counts": dot_counts, "output": output,
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical separator/template/stamp rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _position_category(facts):
    row, col = facts["template_index"]
    rows, cols = len(facts["row_bounds"]), len(facts["col_bounds"])
    on_row_edge, on_col_edge = row in (0, rows - 1), col in (0, cols - 1)
    if on_row_edge and on_col_edge:
        return "corner"
    if on_row_edge or on_col_edge:
        return "edge"
    return "center"


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    if facts["pattern_zeros"]:
        return "template_with_zero"
    if max(facts["dot_counts"].values(), default=0) > 1:
        return "multiple_dot_shapes"
    if facts["cell_height"] != facts["cell_width"]:
        return "rectangular_cells"
    size = facts["cell_height"]
    category = _position_category(facts)
    candidate = f"cell{size}_{category}_template"
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if facts["background"] == 0:
        errors.append("the modal cell background must be nonzero")
    if len(facts["foreground"]) < 2:
        errors.append("the template must contain at least two foreground cells")
    if len(facts["targets"]) < 2:
        errors.append("at least two non-template cells must be dot-marked targets")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared self-stamping profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    if any(facts["output"][row][col] != 0 for row in facts["separator_rows"] for col in range(facts["width"])):
        errors.append("separator rows must remain zero")
    if any(facts["output"][row][col] != 0 for col in facts["separator_cols"] for row in range(facts["height"])):
        errors.append("separator columns must remain zero")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _board_shape(difficulty, category, rng):
    if difficulty == "easy":
        return rng.choice(((3, 3), (3, 4), (4, 3)))
    if difficulty == "medium":
        return rng.choice(((3, 4), (4, 3), (4, 4)))
    if difficulty == "hard":
        return rng.choice(((4, 4), (4, 5), (5, 4)))
    return rng.choice(((3, 3), (3, 4), (4, 3), (4, 4)))


def _template_index(rows, cols, category, rng):
    if category == "corner":
        return rng.choice(((0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)))
    if category == "center":
        return rng.randint(1, rows - 2), rng.randint(1, cols - 2)
    edge = [(row, col) for row in range(rows) for col in range(cols) if (row in (0, rows - 1) or col in (0, cols - 1)) and not (row in (0, rows - 1) and col in (0, cols - 1))]
    return rng.choice(edge)


def _origin(index, size):
    return index * (size + 1)


def _general_scene(difficulty, profile, rng):
    for _ in range(100):
        if profile.startswith("cell"):
            cell_height = cell_width = int(profile[4])
            category = profile.split("_")[1]
        elif profile == "rectangular_cells":
            cell_height, cell_width = rng.choice(((3, 5), (4, 3), (4, 5), (5, 3)))
            category = rng.choice(("corner", "center", "edge"))
        else:
            cell_height = cell_width = rng.choice((3, 4, 5))
            category = rng.choice(("corner", "center", "edge"))
        rows, cols = _board_shape(difficulty, category, rng)
        if category == "center" and (rows < 3 or cols < 3):
            continue
        height, width = rows * cell_height + rows - 1, cols * cell_width + cols - 1
        if height > 30 or width > 30:
            continue
        background, color1, color2 = rng.sample(range(1, 10), 3)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for row_index in range(rows):
            for col_index in range(cols):
                row0, col0 = _origin(row_index, cell_height), _origin(col_index, cell_width)
                for row in range(row0, row0 + cell_height):
                    for col in range(col0, col0 + cell_width):
                        grid[row][col] = background
        template = _template_index(rows, cols, category, rng)
        cells = [(row, col) for row in range(cell_height) for col in range(cell_width)]
        foreground = rng.sample(cells, rng.randint(3, max(3, min(len(cells) // 2, 8))))
        template_row, template_col = _origin(template[0], cell_height), _origin(template[1], cell_width)
        for index, (drow, dcol) in enumerate(foreground):
            grid[template_row + drow][template_col + dcol] = color1 if index % 3 else color2
        if profile == "template_with_zero":
            zero_candidates = [cell for cell in cells if cell not in foreground]
            drow, dcol = rng.choice(zero_candidates)
            grid[template_row + drow][template_col + dcol] = 0
        positions = [(row, col) for row in range(rows) for col in range(cols) if (row, col) != template]
        target_count = rng.randint(2, max(2, len(positions) - 1))
        targets = rng.sample(positions, target_count)
        for row_index, col_index in targets:
            row0, col0 = _origin(row_index, cell_height), _origin(col_index, cell_width)
            dot_count = rng.randint(2, min(5, len(cells) - 1)) if profile == "multiple_dot_shapes" else 1
            for drow, dcol in rng.sample(cells, dot_count):
                grid[row0 + drow][col0 + dcol] = 0
        analysis = _analysis(grid)
        changed = sum(
            before != after
            for input_row, output_row in zip(grid, analysis["output"] or ())
            for before, after in zip(input_row, output_row)
        )
        change_rate = changed / (height * width)
        if not analysis["errors"] and analysis["scene_profile"] == profile and change_rate >= MIN_SYNTHETIC_CHANGE_RATE:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
