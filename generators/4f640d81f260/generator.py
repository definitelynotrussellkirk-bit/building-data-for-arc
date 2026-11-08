"""Semantic generator for ARC task 9f27f097 / 4f640d81f260.

A solid multicolor source rectangle and an equal-sized all-zero destination
rectangle lie on a modal nonzero background.  Copy the source into the zero
rectangle after reversing every source row (a left-right reflection).
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f640d81f260"
TASK_ID = "4f640d81f260"
VERSION = "3.0.0"
RULE_HASH = "bddf313b5517"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Find the solid multicolor template rectangle and the equal-sized solid "
    "zero rectangle on the modal nonzero background. Reflect the template "
    "left-to-right and write that reflected rectangle into the zero target; "
    "leave every other cell unchanged."
)

INVARIANTS = [
    "the modal background is nonzero",
    "all zero cells form exactly one filled rectangular target",
    "all non-background nonzero cells form exactly one filled rectangular template",
    "template and target rectangles have identical dimensions and do not overlap",
    "ordinary generated templates are horizontally asymmetric and use at least two colors",
    "the output changes only the target rectangle, which becomes the template's horizontal reflection",
]

TEMPLATE_SIZES = ("3x4", "4x4", "4x6", "5x5")
COLUMN_ROLES = ("left", "center", "right")
TARGET_RELATIONS = ("above", "below")
CANONICAL_BACKGROUNDS = (1, 2, 8)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot schedule anchored at 12 and broadened by difficulty",
        "valid": "12..16",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot schedule anchored at 12 and broadened by difficulty",
        "valid": "12..16",
    },
    "template_size": {
        "type": "str",
        "default": "four-slot schedule covers every canonical size",
        "valid": "|".join(TEMPLATE_SIZES),
    },
    "background_color": {
        "type": "color",
        "default": "canonical 1/2/8 on anchored slots; any nonzero color otherwise",
        "valid": "1..9",
    },
    "template_palette_size": {
        "type": "int",
        "default": "2 on anchored slots and 3 on broadened slots",
        "valid": "2..3",
    },
    "target_relation": {
        "type": "str",
        "default": "alternates above/below in every four-example lesson",
        "valid": "|".join(TARGET_RELATIONS),
    },
    "template_column": {
        "type": "str",
        "default": "scheduled left/center/right roles",
        "valid": "|".join(COLUMN_ROLES),
    },
    "target_column": {
        "type": "str",
        "default": "scheduled left/center/right roles",
        "valid": "|".join(COLUMN_ROLES),
    },
}


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed ARC 30x30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _rect_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    row1, col1, row2, col2 = box
    return {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
    }


def _scene(grid) -> dict:
    counts = Counter(value for row in grid for value in row)
    modal_count = max(counts.values())
    modal_colors = [color for color, count in counts.items() if count == modal_count]
    if len(modal_colors) != 1:
        raise ValueError("background/modal color must be unique")
    background = modal_colors[0]
    if background == 0:
        raise ValueError("background must be nonzero")

    target_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    ]
    if not target_cells:
        raise ValueError("zero target is missing")
    target_box = _bbox(target_cells)
    if set(target_cells) != _rect_cells(target_box):
        raise ValueError("zero target must be one filled rectangle")

    template_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, background)
    ]
    if not template_cells:
        raise ValueError("template is missing")
    template_box = _bbox(template_cells)
    if set(template_cells) != _rect_cells(template_box):
        raise ValueError("template must be one filled rectangle")

    target_h = target_box[2] - target_box[0] + 1
    target_w = target_box[3] - target_box[1] + 1
    template_h = template_box[2] - template_box[0] + 1
    template_w = template_box[3] - template_box[1] + 1
    if (target_h, target_w) != (template_h, template_w):
        raise ValueError("template and target rectangles must have identical dimensions")

    if target_box[2] < template_box[0]:
        relation = "above"
    elif template_box[2] < target_box[0]:
        relation = "below"
    else:
        raise ValueError("template and target must be vertically separated")

    template = [
        list(grid[template_box[0] + row][template_box[1] : template_box[3] + 1])
        for row in range(template_h)
    ]
    palette = sorted({value for row in template for value in row})
    return {
        "background": background,
        "target_box": target_box,
        "template_box": template_box,
        "height": template_h,
        "width": template_w,
        "relation": relation,
        "template": template,
        "palette": palette,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority-valid rectangular grammar; reject structural impostors."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    try:
        _scene(grid)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _column_for(role: str, grid_w: int, rect_w: int) -> int:
    positions = {
        "left": 1,
        "center": (grid_w - rect_w) // 2,
        "right": grid_w - rect_w - 1,
    }
    return positions[role]


def _column_role(col: int, grid_w: int, rect_w: int) -> str:
    positions = {
        "left": 1,
        "center": (grid_w - rect_w) // 2,
        "right": grid_w - rect_w - 1,
    }
    matches = [role for role, expected in positions.items() if col == expected]
    return matches[0] if len(matches) == 1 else "other"


def _draw_int_axis(ctx, overrides, label: str, scheduled, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, tuple(scheduled)))


def _draw_choice_axis(ctx, overrides, label: str, scheduled, legal):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(legal))
    return ctx.draw_choice(label, tuple(scheduled))


def _draw_color_axis(ctx, overrides, label: str, scheduled) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_color(label, exclude=(0,))
    return int(ctx.draw_choice(label, tuple(scheduled)))


def _pattern(height: int, width: int, colors: tuple[int, ...], rng) -> list[list[int]]:
    pattern = [
        [colors[rng.randrange(len(colors))] for _ in range(width)]
        for _ in range(height)
    ]
    # Every palette color is observable.
    for index, color in enumerate(colors):
        pattern[index // width][index % width] = color
    # These corners make copy, vertical-flip, and rotate-180 rivals all differ
    # from the required horizontal reflection at the target's top-left cell.
    pattern[0][0] = colors[0]
    pattern[0][-1] = colors[1]
    pattern[-1][0] = colors[0]
    pattern[-1][-1] = colors[0]
    return pattern


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = "medium" if difficulty is None else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    slot = int(sample_index) % EXAMPLES_NEEDED
    rng = ctx.draw_rng("pattern")

    height_schedules = {
        "easy": ((12,), (12,), (12, 13), (13,)),
        "medium": ((12,), (12,), (13, 14), (14, 15)),
        "hard": ((12,), (12,), (15, 16), (16,)),
    }
    width_schedules = {
        "easy": ((12,), (12,), (12, 13), (13,)),
        "medium": ((12,), (12,), (13, 14), (14, 15)),
        "hard": ((12,), (12,), (15, 16), (16,)),
    }
    size_schedule = (("5x5",), ("4x4",), ("4x6",), ("3x4",))
    palette_schedule = ((2,), (2,), (3,), (3,))
    relation_schedule = (("above",), ("below",), ("above",), ("below",))
    template_column_schedule = (("left",), ("right",), ("center",), ("left",))
    target_column_schedule = (("center",), ("left",), ("right",), ("right",))

    grid_h = _draw_int_axis(
        ctx, overrides, "grid_h", height_schedules[band][slot], 12, 16
    )
    grid_w = _draw_int_axis(
        ctx, overrides, "grid_w", width_schedules[band][slot], 12, 16
    )
    size_text = str(
        _draw_choice_axis(
            ctx, overrides, "template_size", size_schedule[slot], TEMPLATE_SIZES
        )
    )
    template_h, template_w = (int(value) for value in size_text.split("x"))
    background = _draw_color_axis(
        ctx,
        overrides,
        "background_color",
        CANONICAL_BACKGROUNDS if slot < 2 else tuple(range(1, 10)),
    )
    palette_size = _draw_int_axis(
        ctx, overrides, "template_palette_size", palette_schedule[slot], 2, 3
    )
    relation = str(
        _draw_choice_axis(
            ctx, overrides, "target_relation", relation_schedule[slot], TARGET_RELATIONS
        )
    )
    template_column = str(
        _draw_choice_axis(
            ctx,
            overrides,
            "template_column",
            template_column_schedule[slot],
            COLUMN_ROLES,
        )
    )
    target_column = str(
        _draw_choice_axis(
            ctx,
            overrides,
            "target_column",
            target_column_schedule[slot],
            COLUMN_ROLES,
        )
    )

    colors = ctx.draw_distinct_colors(
        "template_colors", n=palette_size, exclude=(0, background)
    )
    template = _pattern(template_h, template_w, colors, rng)

    if relation == "above":
        target_row = 0
        template_row = grid_h - template_h - 1
    else:
        template_row = 1
        target_row = grid_h - template_h
    template_col = _column_for(template_column, grid_w, template_w)
    target_col = _column_for(target_column, grid_w, template_w)

    grid = full_grid(grid_h, grid_w, background)
    for row in range(template_h):
        for col in range(template_w):
            grid[template_row + row][template_col + col] = template[row][col]
            grid[target_row + row][target_col + col] = 0

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation invariant failed: " + "; ".join(errors))
    if template == [list(reversed(row)) for row in template]:
        raise ValueError("internal generation invariant failed: symmetric template")
    return grid


def observe_overrides(grid) -> dict[str, object]:
    scene = _scene(grid)
    template_box = scene["template_box"]
    target_box = scene["target_box"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": f"{scene['height']}x{scene['width']}",
        "background_color": scene["background"],
        "template_palette_size": len(scene["palette"]),
        "target_relation": scene["relation"],
        "template_column": _column_role(
            template_box[1], len(grid[0]), scene["width"]
        ),
        "target_column": _column_role(target_box[1], len(grid[0]), scene["width"]),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival analysis."""
    scene = _scene(grid)
    output = [list(row) for row in grid]
    target_row, target_col, _, _ = scene["target_box"]
    for row, values in enumerate(scene["template"]):
        for col, value in enumerate(reversed(values)):
            output[target_row + row][target_col + col] = value
    return output


def _rival_from_transform(grid, transform: Callable[[list[list[int]]], list[list[int]]]):
    scene = _scene(grid)
    output = [list(row) for row in grid]
    target_row, target_col, _, _ = scene["target_box"]
    transformed = transform(scene["template"])
    for row, values in enumerate(transformed):
        for col, value in enumerate(values):
            output[target_row + row][target_col + col] = value
    return output


def _copy_rival(grid):
    return _rival_from_transform(grid, lambda template: [list(row) for row in template])


def _vertical_flip_rival(grid):
    return _rival_from_transform(grid, lambda template: [list(row) for row in reversed(template)])


def _rotate_180_rival(grid):
    return _rival_from_transform(
        grid, lambda template: [list(reversed(row)) for row in reversed(template)]
    )


def _modal_fill_rival(grid):
    scene = _scene(grid)
    fill = Counter(value for row in scene["template"] for value in row).most_common(1)[0][0]
    return _rival_from_transform(
        grid,
        lambda template: [[fill for _ in row] for row in template],
    )


def _target_above(grid) -> bool:
    return _scene(grid)["relation"] == "above"


def _target_below(grid) -> bool:
    return _scene(grid)["relation"] == "below"


def _copy_refuted(grid) -> bool:
    return rule_mirror(grid) != _copy_rival(grid)


def _vertical_refuted(grid) -> bool:
    return rule_mirror(grid) != _vertical_flip_rival(grid)


def _rotate_refuted(grid) -> bool:
    return rule_mirror(grid) != _rotate_180_rival(grid)


def _modal_fill_refuted(grid) -> bool:
    return rule_mirror(grid) != _modal_fill_rival(grid)


def _off_center_target(grid) -> bool:
    return observe_overrides(grid)["target_column"] != "center"


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    scene = _scene(grid)
    palette = {value for row in grid for value in row}
    if (len(grid), len(grid[0])) != (12, 12):
        reasons.append("canonical grids are 12x12")
    if len(palette) != 4:
        reasons.append("canonical inputs have four total colors")
    if scene["background"] not in CANONICAL_BACKGROUNDS:
        reasons.append("background is outside the observed canonical set 1/2/8")
    if f"{scene['height']}x{scene['width']}" not in TEMPLATE_SIZES:
        reasons.append("template dimensions are outside the canonical size set")
    return reasons


SEMANTIC_RIVALS = {
    "copy_without_flip": _copy_rival,
    "vertical_flip": _vertical_flip_rival,
    "rotate_180": _rotate_180_rival,
    "modal_template_fill": _modal_fill_rival,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "target_above": _target_above,
    "target_below": _target_below,
    "copy_rival_refuted": _copy_refuted,
    "vertical_flip_rival_refuted": _vertical_refuted,
    "rotate_180_rival_refuted": _rotate_refuted,
    "modal_fill_rival_refuted": _modal_fill_refuted,
    "off_center_target": _off_center_target,
}

WITNESS_RIVALS = {
    "target_above": ["copy_without_flip"],
    "target_below": ["copy_without_flip"],
    "off_center_target": ["copy_without_flip"],
    "copy_rival_refuted": ["copy_without_flip"],
    "vertical_flip_rival_refuted": ["vertical_flip"],
    "rotate_180_rival_refuted": ["rotate_180"],
    "modal_fill_rival_refuted": ["modal_template_fill"],
}

SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    return int(sample_index) % EXAMPLES_NEEDED


def lesson_identifiable(demos, query) -> list[str]:
    """Every four-consecutive-example window must identify horizontal reflection."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    relations: set[str] = set()
    sizes: set[str] = set()
    template_columns: set[str] = set()
    target_columns: set[str] = set()
    rivals_refuted = {name: False for name in LESSON_COMPETITORS}

    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        official = rule_mirror(grid)
        if output != official:
            reasons.append(f"demo {index} output disagrees with horizontal reflection")
        observed = observe_overrides(grid)
        relations.add(str(observed["target_relation"]))
        sizes.add(str(observed["template_size"]))
        template_columns.add(str(observed["template_column"]))
        target_columns.add(str(observed["target_column"]))
        for name, competitor in LESSON_COMPETITORS.items():
            rivals_refuted[name] |= official != competitor(grid)

    if relations != {"above", "below"}:
        reasons.append("demonstrations do not show both target-above and target-below layouts")
    if len(sizes) < 4:
        reasons.append("demonstrations do not cover all four canonical template sizes")
    if len(template_columns) < 3:
        reasons.append("template column does not vary across left/center/right roles")
    if len(target_columns) < 3:
        reasons.append("target column does not vary across left/center/right roles")
    for name, refuted in rivals_refuted.items():
        if not refuted:
            reasons.append(f"demonstrations do not refute competitor {name}")

    query_grid = query.get("input")
    query_output = query.get("output")
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query answer disagrees with horizontal reflection")
    return reasons
