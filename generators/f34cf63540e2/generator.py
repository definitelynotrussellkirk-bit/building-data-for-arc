"""Semantic generator for ARC task f34cf63540e2.

Read nonzero command codes from row zero from left to right, crop the first
nonzero component wholly below row zero, then apply the coded transforms to
that crop in sequence.  The crop is taken from the original grid, so detached
nonzero cells inside the chosen component's bounding box remain visible.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "f34cf63540e2"
TASK_ID = "f34cf63540e2"
VERSION = "3.0.0"
RULE_HASH = "1157bcb457e5"
SUMMARY = "Apply row-zero transform commands left-to-right to the first lower nonzero component's rectangular crop."
INVARIANTS = [
    "literal zero is background and row zero contains command codes 2 through 6",
    "commands are read by column order, not by color order or motif palette",
    "2 rotates clockwise, 3 rotates 180 degrees, 4 transposes, 5 flips left-right, and 6 flips up-down",
    "all commands are applied sequentially to the evolving crop",
    "the chosen source is the first color-blind 4-connected nonzero region wholly below row zero",
    "the rectangular crop preserves zeros and any detached nonzero cells enclosed by the chosen bounding box",
    "a lawful command composition may return the source crop unchanged",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "single_rotate_cw",
    "single_rotate_180",
    "single_transpose",
    "single_flip_lr",
    "single_flip_ud",
    "ordered_cw_then_lr",
    "ordered_lr_then_cw",
    "triple_disjoint_palette",
    "composed_identity",
    "first_region_with_decoy",
    "embedded_bbox_decoy",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and twelve observable transform-composition lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|single_rotate_cw|single_rotate_180|single_transpose|single_flip_lr|single_flip_ud|ordered_cw_then_lr|ordered_lr_then_cw|triple_disjoint_palette|composed_identity|first_region_with_decoy|embedded_bbox_decoy",
    }
}

_PUBLIC_ROWS = (
    ("02050000000000/00000000000000/00000000000000/00000000000000/00000020000000/00000023400000/00000004000000/00000000000000/00000000000000/00000000000000"),
    ("040602000000000/000000000000000/000000000000000/000000000000000/000000000000000/000000050600000/000000056000000/000000006600000/000000000000000/000000000000000/000000000000000"),
    ("03050000000000/00000000000000/00000000000000/00000000000000/00000708000000/00000788000000/00000080000000/00000000000000/00000000000000/00000000000000"),
    ("060202000000000/000000000000000/000000000000000/000000000000000/000000000000000/000000220000000/000000034000000/000000040000000/000000000000000/000000000000000/000000000000000"),
    ("05040200000000/00000000000000/00000000000000/00000000000000/00000005000000/00000055600000/00000006000000/00000000000000/00000000000000/00000000000000"),
)


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_STEPS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COMMANDS = {
    "single_rotate_cw": (2,),
    "single_rotate_180": (3,),
    "single_transpose": (4,),
    "single_flip_lr": (5,),
    "single_flip_ud": (6,),
    "ordered_cw_then_lr": (2, 5),
    "ordered_lr_then_cw": (5, 2),
    "triple_disjoint_palette": (2, 4, 5),
    "composed_identity": (5, 4, 2),
    "first_region_with_decoy": (3, 6),
    "embedded_bbox_decoy": (4, 2),
}


def _rotate_cw(grid):
    return [list(line) for line in zip(*grid[::-1])]


def _rotate_180(grid):
    return [line[::-1] for line in grid[::-1]]


def _transpose(grid):
    return [list(line) for line in zip(*grid)]


def _flip_lr(grid):
    return [line[::-1] for line in grid]


def _flip_ud(grid):
    return [line[:] for line in grid[::-1]]


def _apply_commands(grid, commands):
    result = [line[:] for line in grid]
    for command in commands:
        if command == 2:
            result = _rotate_cw(result)
        elif command == 3:
            result = _rotate_180(result)
        elif command == 4:
            result = _transpose(result)
        elif command == 5:
            result = _flip_lr(result)
        elif command == 6:
            result = _flip_ud(result)
        else:
            raise ValueError(f"unsupported command: {command!r}")
    return result


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(line, (list, tuple)) or len(line) != width for line in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for line in grid for value in line):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _bounds(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _nonzero_regions(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    regions = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        frontier = [start]
        cells = []
        while frontier:
            row, col = frontier.pop()
            cells.append((row, col))
            for delta_row, delta_col in _STEPS4:
                cell = row + delta_row, col + delta_col
                if cell in unseen:
                    unseen.remove(cell)
                    frontier.append(cell)
        regions.append(sorted(cells))
    return regions


def _rule_facts(grid):
    commands = tuple(value for value in grid[0] if value != 0)
    command_columns = tuple(col for col, value in enumerate(grid[0]) if value != 0)
    regions = _nonzero_regions(grid)
    lower = [cells for cells in regions if _bounds(cells)[0] > 0]
    lower.sort(key=lambda cells: (_bounds(cells)[0], _bounds(cells)[1]))
    if not lower:
        raise ValueError("no nonzero region wholly below row zero")
    chosen = lower[0]
    top, left, height, width = _bounds(chosen)
    source_crop = [list(line[left:left + width]) for line in grid[top:top + height]]
    chosen_set = set(chosen)
    enclosed_extras = {
        (row, col)
        for row in range(top, top + height)
        for col in range(left, left + width)
        if grid[row][col] != 0 and (row, col) not in chosen_set
    }
    outside_lower = [cells for cells in lower[1:] if not any(cell in enclosed_extras for cell in cells)]
    output = _apply_commands(source_crop, commands)
    return {
        "commands": commands,
        "command_columns": command_columns,
        "regions": regions,
        "lower_regions": lower,
        "chosen_region": chosen,
        "chosen_bounds": (top, left, height, width),
        "source_crop": source_crop,
        "source_colors": {value for line in source_crop for value in line if value != 0},
        "enclosed_extras": enclosed_extras,
        "outside_lower_regions": outside_lower,
        "output": output,
        "identity": output == source_crop,
    }


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts):
    commands = facts["commands"]
    reverse = {value: name for name, value in _COMMANDS.items()}
    profile = reverse.get(commands)
    if not profile:
        return None
    lower_count = len(facts["lower_regions"])
    embedded = bool(facts["enclosed_extras"])
    external = bool(facts["outside_lower_regions"])
    if profile == "first_region_with_decoy":
        return profile if lower_count >= 2 and external and not embedded else None
    if profile == "embedded_bbox_decoy":
        return profile if lower_count >= 2 and embedded else None
    if lower_count != 1 or embedded or external:
        return None
    if profile == "triple_disjoint_palette":
        return profile if not (set(commands) & facts["source_colors"]) else None
    if profile == "composed_identity":
        return profile if facts["identity"] else None
    if facts["identity"] or not (set(commands) & facts["source_colors"]):
        return None
    return profile


def _analysis(grid):
    errors = _valid_grid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 7 or width < 9:
        errors.append("training grids must be at least 7x9")
    if sum(value == 0 for line in grid for value in line) <= height * width * 3 // 4:
        errors.append("literal zero must occupy more than three quarters of the canvas")
    commands = [value for value in grid[0] if value != 0]
    if not 1 <= len(commands) <= 3:
        errors.append("row zero must contain one to three commands")
    if any(value not in (2, 3, 4, 5, 6) for value in commands):
        errors.append("row-zero nonzero values must be command codes 2..6")
    if height > 1 and any(grid[1]):
        errors.append("row one must separate commands from the lower scene")
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return result
    top, left, crop_height, crop_width = facts["chosen_bounds"]
    if not 2 <= crop_height <= 6 or not 2 <= crop_width <= 6:
        errors.append("chosen crop dimensions must each be in 2..6")
    if not 4 <= len(facts["chosen_region"]) <= 20:
        errors.append("chosen connected region must contain 4..20 cells")
    if len(facts["source_colors"]) < 2:
        errors.append("chosen rectangular crop must expose at least two nonzero colors")
    if len(facts["lower_regions"]) > 3:
        errors.append("training scenes use at most three lower nonzero regions")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match one declared transform-composition profile")
    result.update({"facts": facts, "output": facts["output"], "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(f"scene profile drifted from {requested} to {analysis['scene_profile']}")
    return errors


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _dimensions(difficulty, rng):
    ranges = {
        None: ((9, 14), (12, 18)),
        "easy": ((8, 10), (10, 13)),
        "medium": ((10, 14), (13, 18)),
        "hard": ((14, 20), (17, 24)),
    }
    row_range, col_range = ranges[difficulty]
    return rng.randint(*row_range), rng.randint(*col_range)


def _connected_patch(rng, patch_height, patch_width, commands, *, disjoint=False):
    moves = [(1, 0)] * (patch_height - 1) + [(0, 1)] * (patch_width - 1)
    rng.shuffle(moves)
    row = col = 0
    cells = {(row, col)}
    for delta_row, delta_col in moves:
        row += delta_row
        col += delta_col
        cells.add((row, col))
    candidates = [
        (row, col)
        for row in range(patch_height)
        for col in range(patch_width)
        if (row, col) not in cells and any((row + dr, col + dc) in cells for dr, dc in _STEPS4)
    ]
    rng.shuffle(candidates)
    maximum = patch_height * patch_width - (1 if patch_height * patch_width > 4 else 0)
    target = rng.randint(len(cells), min(maximum, len(cells) + max(2, patch_height + patch_width // 2)))
    for cell in candidates:
        if len(cells) >= target:
            break
        if any((cell[0] + dr, cell[1] + dc) in cells for dr, dc in _STEPS4):
            cells.add(cell)
    legal = [color for color in range(1, 10) if not disjoint or color not in commands]
    palette_size = rng.randint(2, min(5, len(cells), len(legal)))
    if disjoint:
        palette = rng.sample(legal, palette_size)
    else:
        reused = rng.choice(tuple(commands))
        palette = [reused] + rng.sample([color for color in legal if color != reused], palette_size - 1)
    assignments = palette[:] + [rng.choice(palette) for _ in range(len(cells) - len(palette))]
    rng.shuffle(assignments)
    patch = [[0] * patch_width for _ in range(patch_height)]
    for cell, color in zip(sorted(cells), assignments):
        patch[cell[0]][cell[1]] = color
    return patch


def _paint_patch(canvas, patch, top, left):
    for row, line in enumerate(patch):
        for col, value in enumerate(line):
            if value:
                canvas[top + row][left + col] = value


def _general_scene(ctx, profile, rng):
    commands = _COMMANDS[profile]
    for _ in range(500):
        height, width = _dimensions(ctx.difficulty, rng)
        canvas = [[0] * width for _ in range(height)]
        columns = sorted(rng.sample(range(width), len(commands)))
        for col, command in zip(columns, commands):
            canvas[0][col] = command

        if profile == "embedded_bbox_decoy":
            patch_height = patch_width = 5
            border_cells = {(row, col) for row in range(5) for col in range(5) if row in (0, 4) or col in (0, 4)}
            palette = rng.sample(range(1, 10), rng.randint(3, 5))
            values = palette[:] + [rng.choice(palette) for _ in range(len(border_cells) - len(palette))]
            rng.shuffle(values)
            patch = [[0] * 5 for _ in range(5)]
            for cell, value in zip(sorted(border_cells), values):
                patch[cell[0]][cell[1]] = value
            patch[2][2] = rng.choice(range(1, 10))
        else:
            limits = {None: (2, 5), "easy": (2, 4), "medium": (3, 5), "hard": (3, 6)}
            low, high = limits[ctx.difficulty]
            patch_height = rng.randint(low, high)
            patch_width = rng.randint(low, high)
            patch = _connected_patch(rng, patch_height, patch_width, commands, disjoint=profile == "triple_disjoint_palette")

        extra_rows = 2 if profile == "first_region_with_decoy" else 0
        if height - patch_height - extra_rows < 2:
            continue
        top = rng.randint(2, height - patch_height - extra_rows)
        left = rng.randint(0, width - patch_width)
        _paint_patch(canvas, patch, top, left)
        if profile == "first_region_with_decoy":
            decoy_row = top + patch_height + 1
            decoy_col = rng.randint(0, width - 2)
            canvas[decoy_row][decoy_col] = rng.randint(1, 9)
            if rng.choice((False, True)):
                canvas[decoy_row][decoy_col + 1] = rng.randint(1, 9)

        analysis = _analysis(canvas)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return canvas
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile in PUBLIC_PROFILES:
        return [line[:] for line in _PUBLIC_INPUTS[profile]]
    canvas = _general_scene(ctx, profile, ctx.draw_rng("geometry"))
    analysis = _analysis(canvas)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return canvas
