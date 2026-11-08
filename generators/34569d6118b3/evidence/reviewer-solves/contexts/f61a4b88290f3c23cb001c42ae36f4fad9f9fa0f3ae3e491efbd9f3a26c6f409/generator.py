"""Semantic generator for ARC task 34569d6118b3.

The header contains ordered color swatches and the same number of ordered
gray (5) template masks.  The first all-zero row ends that header.  A dense
layout below it uses only swatch colors.  Each layout cell is expanded to the
corresponding gray mask, with gray replaced by that cell's color and every
other template value replaced by zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "34569d6118b3"
TASK_ID = "34569d6118b3"
VERSION = "4.0.0"
RULE_HASH = "e2b81b5e525c"
SUMMARY = "Pair ordered color swatches with ordered gray masks, then expand a lower color layout through those masks."
INVARIANTS = [
    "the first all-zero row separates the header from the lower layout",
    "uniform non-gray row-0 runs are distinct ordered swatches",
    "uniform gray row-0 runs bound equally sized ordered template masks",
    "the dense layout uses every swatch color and no unknown color",
    "layout cell color chooses a template by swatch/template order",
    "gray template cells become the layout color and all other cells become zero",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "compact_two_color",
    "three_color_square",
    "four_color_square",
    "tall_templates",
    "wide_templates",
    "large_layout",
    "rectangular_layout",
    "four_color_medium",
    "dense_templates",
    "sparse_templates",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten recoverable swatch-template-layout lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|compact_two_color|three_color_square|four_color_square|tall_templates|wide_templates|large_layout|rectangular_layout|four_color_medium|dense_templates|sparse_templates",
    }
}

_PUBLIC_ROWS = (
    "11033022055505550555/11033022050500500500/00000000055505550555/00000000000000000000/00000000000000000000/00000000000000000000/00012312000000000000/00021321000000000000/00033333000000000000/00012312000000000000/00021321000000000000/00000000000000000000/00000000000000000000/00000000000000000000/00000000000000000000",
    "22044055555055555/22044050000050005/00000050555050555/00000050000050550/00000055555055500/00000000000000000/00000000000000000/00004242000000000/00002242000000000/00004442000000000/00002222000000000/00000000000000000/00000000000000000/00000000000000000/00000000000000000",
    "88011055555055555/88011050005050005/00000050505050505/00000050555055505/00000050000000005/00000000000000000/00818181000000000/00181818000000000/00818181000000000/00181818000000000/00818181000000000/00181818000000000/00000000000000000/00000000000000000/00000000000000000",
    "110220330880555055505550555/110220330880500000505050050/000000000000555055505550555/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000002218883000000000000000/000002118213000000000000000/000001188213000000000000000/000008882218000000000000000/000008222118000000000000000/000008111182000000000000000/000003338822000000000000000/000000000000000000000000000/000000000000000000000000000",
    "11044088055555505555550555555/11044088050000505000050500005/00000000050550505055050505505/00000000050550505055550505505/00000000050500505000000500005/00000000050555505555550555555/00000000000000000000000000000/00000000000000000000000000000/00000000000000000000000000000/00004141400000000000000000000/00008888800000000000000000000/00001414100000000000000000000/00008888800000000000000000000/00004141400000000000000000000/00000000000000000000000000000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_SWATCH_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


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


def _row0_runs(grid):
    runs = []
    col = 0
    while col < len(grid[0]):
        if grid[0][col] == 0:
            col += 1
            continue
        start = col
        while col < len(grid[0]) and grid[0][col] != 0:
            col += 1
        runs.append((start, col - 1, grid[0][start]))
    return tuple(runs)


def _parse_scene(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    try:
        separator = next(row for row in range(height) if all(value == 0 for value in grid[row]))
    except StopIteration:
        return {"errors": ["missing first all-zero separator row"]}
    if separator < 2:
        errors.append("template header must be at least two rows tall")
    runs = _row0_runs(grid)
    for start, end, color in runs:
        if any(grid[0][col] != color for col in range(start, end + 1)):
            errors.append("every row-0 run must have one uniform color")
    swatch_runs = tuple(run for run in runs if run[2] != 5)
    template_runs = tuple(run for run in runs if run[2] == 5)
    if not 2 <= len(swatch_runs) <= 4:
        errors.append("header must contain two to four swatch runs")
    if len(template_runs) != len(swatch_runs):
        errors.append("swatch and template run counts must match")
    swatch_colors = tuple(run[2] for run in swatch_runs)
    if len(set(swatch_colors)) != len(swatch_colors) or any(color in (0, 5) for color in swatch_colors):
        errors.append("swatch colors must be distinct and exclude zero and gray")
    template_widths = {end - start + 1 for start, end, _ in template_runs}
    if len(template_widths) != 1:
        errors.append("all template runs must have the same positive width")
    template_width = next(iter(template_widths), 0)
    templates = tuple(
        tuple(tuple(grid[row][col] for col in range(start, end + 1)) for row in range(separator))
        for start, end, _ in template_runs
    )
    if any(value not in (0, 5) for template in templates for row in template for value in row):
        errors.append("template matrices may contain only zero and gray")
    if any(any(value != 5 for value in template[0]) for template in templates):
        errors.append("each template's complete first row must be gray")
    if len(set(templates)) != len(templates):
        errors.append("ordered templates must be visually distinct")
    if separator and any(
        all(template[row][col] == 0 for template in templates for col in range(template_width))
        for row in range(separator)
    ):
        errors.append("every header row before the separator must contain template content")
    layout_cells = [
        (row, col, grid[row][col])
        for row in range(separator, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not layout_cells:
        errors.append("layout must contain nonzero cells below the separator")
        row0 = row1 = separator
        col0 = col1 = 0
    else:
        row0 = min(row for row, _, _ in layout_cells)
        row1 = max(row for row, _, _ in layout_cells)
        col0 = min(col for _, col, _ in layout_cells)
        col1 = max(col for _, col, _ in layout_cells)
    layout = tuple(
        tuple(grid[row][col] for col in range(col0, col1 + 1))
        for row in range(row0, row1 + 1)
    )
    if layout and any(value == 0 for row in layout for value in row):
        errors.append("layout bounding rectangle must be dense because zero has no template mapping")
    layout_colors = {value for row in layout for value in row}
    unknown = layout_colors - set(swatch_colors)
    unused = set(swatch_colors) - layout_colors
    if unknown:
        errors.append(f"layout contains colors without swatches: {sorted(unknown)}")
    if unused:
        errors.append(f"every swatch/template mapping must occur in the layout: {sorted(unused)}")
    layout_h, layout_w = len(layout), len(layout[0]) if layout else 0
    if separator * layout_h > 30 or template_width * layout_w > 30:
        errors.append("expanded output dimensions must not exceed 30x30")
    density = (
        sum(value == 5 for template in templates for row in template for value in row)
        / (len(templates) * separator * template_width)
        if templates and separator and template_width
        else 0.0
    )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "separator": separator,
        "template_h": separator,
        "template_w": template_width,
        "runs": runs,
        "swatch_runs": swatch_runs,
        "template_runs": template_runs,
        "swatch_colors": swatch_colors,
        "templates": templates,
        "layout_bbox": (row0, col0, row1, col1),
        "layout": layout,
        "layout_h": layout_h,
        "layout_w": layout_w,
        "template_density": density,
    }


def _render(parsed):
    mapping = dict(zip(parsed["swatch_colors"], parsed["templates"]))
    output = []
    for layout_row in parsed["layout"]:
        for template_row in range(parsed["template_h"]):
            row = []
            for color in layout_row:
                row.extend(color if value == 5 else 0 for value in mapping[color][template_row])
            output.append(row)
    return output


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    parsed = _parse_scene(grid)
    if parsed["errors"]:
        raise ValueError("; ".join(parsed["errors"]))
    return _render(parsed)


def _profile_for(grid, parsed):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    signature = (
        len(parsed["swatch_colors"]),
        parsed["template_h"],
        parsed["template_w"],
        parsed["layout_h"],
        parsed["layout_w"],
    )
    fixed = {
        (2, 2, 2, 3, 4): "compact_two_color",
        (3, 3, 3, 4, 4): "three_color_square",
        (4, 3, 3, 4, 5): "four_color_square",
        (3, 5, 3, 4, 4): "tall_templates",
        (3, 3, 5, 4, 4): "wide_templates",
        (2, 3, 3, 7, 7): "large_layout",
        (3, 3, 4, 4, 6): "rectangular_layout",
        (4, 4, 3, 5, 5): "four_color_medium",
    }
    if signature in fixed:
        return fixed[signature]
    if signature == (3, 4, 4, 5, 5):
        if parsed["template_density"] >= 0.70:
            return "dense_templates"
        if parsed["template_density"] <= 0.45:
            return "sparse_templates"
    return None


def _analysis(grid):
    parsed = _parse_scene(grid)
    if parsed["errors"]:
        return {"errors": parsed["errors"], "facts": parsed, "scene_profile": None, "output": None}
    profile = _profile_for(grid, parsed)
    errors = []
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared swatch-template-layout profile")
    output = _render(parsed)
    if not any(value == 0 for row in output for value in row):
        errors.append("expanded output must retain mask zeros rather than collapse to color blocks")
    if len({tuple(row) for row in output}) < 2:
        errors.append("expanded output must contain at least two distinct row patterns")
    facts = dict(parsed)
    facts.update(
        {
            "scene_profile": profile,
            "output_h": len(output),
            "output_w": len(output[0]),
            "output": output,
        }
    )
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _profile_spec(profile):
    return {
        "compact_two_color": (2, 2, 2, 3, 4, "balanced"),
        "three_color_square": (3, 3, 3, 4, 4, "balanced"),
        "four_color_square": (4, 3, 3, 4, 5, "balanced"),
        "tall_templates": (3, 5, 3, 4, 4, "balanced"),
        "wide_templates": (3, 3, 5, 4, 4, "balanced"),
        "large_layout": (2, 3, 3, 7, 7, "balanced"),
        "rectangular_layout": (3, 3, 4, 4, 6, "balanced"),
        "four_color_medium": (4, 4, 3, 5, 5, "balanced"),
        "dense_templates": (3, 4, 4, 5, 5, "dense"),
        "sparse_templates": (3, 4, 4, 5, 5, "sparse"),
    }[profile]


def _template_masks(count, height, width, density_kind, rng):
    total = height * width
    if density_kind == "dense":
        low, high = max(width + 1, (7 * total + 9) // 10), total - 1
    elif density_kind == "sparse":
        low, high = width + 1, max(width + 1, (45 * total) // 100)
    else:
        low, high = width + 1, max(width + 1, min(total - 1, (3 * total) // 4))
    templates = []
    for index in range(count):
        for _ in range(200):
            target = rng.randint(low, high)
            cells = [(row, col) for row in range(1, height) for col in range(width)]
            rng.shuffle(cells)
            mask = [[5] * width] + [[0] * width for _ in range(height - 1)]
            for row, col in cells[: target - width]:
                mask[row][col] = 5
            frozen = tuple(map(tuple, mask))
            if frozen not in templates:
                templates.append(frozen)
                break
        else:
            raise AssertionError("could not construct distinct template masks")
    for row in range(1, height):
        if all(template[row][col] == 0 for template in templates for col in range(width)):
            choice = rng.randrange(count)
            mutable = [list(values) for values in templates[choice]]
            mutable[row][rng.randrange(width)] = 5
            replacement = tuple(map(tuple, mutable))
            if replacement in templates:
                other = (choice + 1) % count
                mutable = [list(values) for values in templates[other]]
                mutable[row][rng.randrange(width)] = 5
                templates[other] = tuple(map(tuple, mutable))
            else:
                templates[choice] = replacement
    return tuple(templates)


def _general_scene(profile, rng):
    count, template_h, template_w, layout_h, layout_w, density_kind = _profile_spec(profile)
    colors = rng.sample(_SWATCH_COLORS, count)
    templates = _template_masks(count, template_h, template_w, density_kind, rng)
    swatch_width = rng.randint(1, 2)
    swatch_gap = 1 if count == 4 else rng.randint(1, 2)
    template_gap = 1 if count == 4 else rng.randint(1, 2)
    swatch_zone_w = count * swatch_width + (count - 1) * swatch_gap
    template_zone_w = count * template_w + (count - 1) * template_gap
    header_w = swatch_zone_w + 1 + template_zone_w
    left_margin = rng.randint(0, min(2, 30 - header_w))
    width = max(header_w + left_margin + rng.randint(0, min(2, 30 - header_w - left_margin)), layout_w + 2)
    separator = template_h
    layout_gap = rng.randint(1, 3)
    layout_row0 = separator + layout_gap
    height = layout_row0 + layout_h + rng.randint(0, 2)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    col = left_margin
    for color in colors:
        for offset in range(swatch_width):
            grid[0][col + offset] = color
        col += swatch_width + swatch_gap
    template_col = left_margin + swatch_zone_w + 1
    for template in templates:
        for row in range(template_h):
            for offset in range(template_w):
                grid[row][template_col + offset] = template[row][offset]
        template_col += template_w + template_gap
    layout_col0 = rng.randint(0, width - layout_w)
    cells = [(row, col) for row in range(layout_h) for col in range(layout_w)]
    rng.shuffle(cells)
    values = list(colors)
    while len(values) < len(cells):
        values.append(rng.choice(colors))
    rng.shuffle(values)
    for (row, col), color in zip(cells, values):
        grid[layout_row0 + row][layout_col0 + col] = color
    return grid


def _validated_general_scene(profile, rng):
    for _ in range(200):
        grid = _general_scene(profile, rng)
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
    if difficulty == "easy":
        weighted = (
            PUBLIC_PROFILES
            + GENERAL_PROFILES
            + ("compact_two_color",) * 10
            + ("three_color_square",) * 8
            + ("four_color_square",) * 4
            + ("rectangular_layout",) * 4
            + ("sparse_templates",) * 4
        )
    elif difficulty == "hard":
        weighted = (
            PUBLIC_PROFILES
            + ("tall_templates", "wide_templates", "large_layout") * 6
            + ("four_color_medium",) * 7
            + ("dense_templates", "sparse_templates") * 5
            + ("four_color_square", "rectangular_layout") * 3
            + ("compact_two_color", "three_color_square") * 2
        )
    else:
        weighted = PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 6
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _validated_general_scene(profile, ctx.draw_rng("scene"))
