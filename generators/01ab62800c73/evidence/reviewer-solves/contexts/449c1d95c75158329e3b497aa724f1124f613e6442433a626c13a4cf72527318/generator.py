"""Generator for ARC task 01ab62800c73: execute row-zero transforms in order.

The non-zero values in row 0 are commands, read left to right:
1 = flip left/right, 2 = flip up/down, 3 = rotate clockwise, 4 = rotate 180.
Rows 1+ are cropped to their non-zero bounding box before the commands are
applied sequentially.  Colors 1..4 below row 0 are ordinary payload.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "01ab62800c73"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6f47f78828c8"

SUMMARY = (
    "Row 0 contains an ordered sequence of transform codes: 1=flip-lr, "
    "2=flip-ud, 3=rotate-cw, 4=rotate-180. Crop the non-zero body in rows "
    "1+ and execute every command from left to right. Body colors, including "
    "1..4, are payload rather than extra commands."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_order",
    "code_payload",
    "multicolor_payload",
    "disconnected_body",
)

INVARIANTS = [
    "row 0 contains 1..4 non-zero command cells, all in {1,2,3,4}",
    "the body is rows 1+ cropped to its non-zero bounding box",
    "commands are executed in left-to-right order, not sorted or collapsed",
    "colors 1..4 in the body are payload",
    "ordinary generated bodies expose all dihedral orientations",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "code_colored_body", "multicolor_body")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 5 or difficulty-weighted 5..14",
        "valid": "5..14",
        "doc": "Input height, including the command row.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 6..7 or difficulty-weighted 6..14",
        "valid": "6..14",
        "doc": "Input width.",
    },
    "n_ops": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "1..4",
        "doc": "Number of non-zero command cells in row 0.",
    },
    "texture": {
        "type": "str",
        "default": "scheduled across all helpful textures",
        "valid": "plain|code_colored_body|multicolor_body",
        "doc": "Body palette class; command colors below row 0 remain payload.",
    },
}

MIN_STRICT_FRAC = 1.0


def _copy(grid):
    return [list(row) for row in grid]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rotate_cw(grid):
    return [list(row) for row in zip(*reversed(grid))]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _apply_commands(grid, commands):
    current = _copy(grid)
    for command in commands:
        if command == 1:
            current = _flip_lr(current)
        elif command == 2:
            current = _flip_ud(current)
        elif command == 3:
            current = _rotate_cw(current)
        elif command == 4:
            current = _rotate_180(current)
    return current


def _validated_grid(grid):
    errors = []
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["grid cells must be integer colors 0..9 (not bool)"]
    return _copy(grid), errors


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _commands(grid):
    return tuple(value for value in grid[0] if value != 0)


def rule_mirror(grid):
    """Pure-Python mirror of the pinned Racket authority."""
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    body = checked[1:]
    return _apply_commands(_crop_nonzero(body), _commands(checked))


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _dihedral_keys(grid):
    keys = []
    current = _copy(grid)
    for _ in range(4):
        keys.append(_grid_key(current))
        keys.append(_grid_key(_flip_lr(current)))
        current = _rotate_cw(current)
    return set(keys)


def _component_count(crop):
    cells = {
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while cells:
        count += 1
        stack = [cells.pop()]
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in cells:
                    cells.remove(nxt)
                    stack.append(nxt)
    return count


def _texture_of(crop):
    colors = {value for row in crop for value in row if value != 0}
    if len(colors) >= 2:
        return "multicolor_body"
    if not colors:
        return None
    color = next(iter(colors))
    return "code_colored_body" if color in (1, 2, 3, 4) else "plain"


def _strict_errors(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        return errors
    if len(checked) < 2:
        return ["grid needs a command row and at least one body row"]
    commands = _commands(checked)
    if not 1 <= len(commands) <= 4:
        errors.append(f"row 0 must contain 1..4 non-zero commands, found {len(commands)}")
    if any(command not in (1, 2, 3, 4) for command in commands):
        errors.append("every non-zero row-0 value must be a command in {1,2,3,4}")
    if not any(value != 0 for row in checked[1:] for value in row):
        errors.append("body rows 1+ must contain a non-zero payload")
    return errors


def strict_canonical_like(grid):
    """Accept the exact task manifold, including all labeled canonical inputs."""
    return _strict_errors(grid)


def _analysis(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        return {"errors": errors, "facts": {}}

    h, w = len(checked), len(checked[0])
    if not 5 <= h <= 14:
        errors.append(f"grid_h {h} outside 5..14")
    if not 6 <= w <= 14:
        errors.append(f"grid_w {w} outside 6..14")

    commands = _commands(checked)
    if not 1 <= len(commands) <= 4:
        errors.append(f"row 0 must contain 1..4 non-zero commands, found {len(commands)}")
    if any(command not in (1, 2, 3, 4) for command in commands):
        errors.append("every non-zero row-0 value must be in {1,2,3,4}")

    body = checked[1:]
    body_count = sum(value != 0 for row in body for value in row)
    if body_count < 4:
        errors.append(f"body needs at least 4 non-zero payload cells, found {body_count}")
    crop = _crop_nonzero(body)
    if crop == [[0]]:
        crop_h = crop_w = 0
        texture = None
        components = 0
    else:
        crop_h, crop_w = len(crop), len(crop[0])
        texture = _texture_of(crop)
        components = _component_count(crop)
        if crop_h < 2 or crop_w < 2:
            errors.append("cropped body must span at least two rows and two columns")
        if len(_dihedral_keys(crop)) < 4:
            errors.append("cropped body is too symmetric to expose transform semantics")
        if components not in (1, 2):
            errors.append(f"body must have one or two 4-connected components, found {components}")
        if texture not in HELPFUL_TEXTURES:
            errors.append("body texture is not one of the declared ordinary textures")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "commands": commands,
        "n_ops": len(commands),
        "body_crop": crop,
        "body_count": body_count,
        "components": components,
        "texture": texture,
        "output": _apply_commands(crop, commands) if crop != [[0]] else _apply_commands([[0]], commands),
    }
    return {"errors": sorted(set(errors)), "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_ops": facts["n_ops"],
        "texture": facts["texture"],
    }


def canonical_profile_signature(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        return None
    signature = (len(checked), len(checked[0]), len({value for row in checked for value in row}))
    return signature if signature in {(5, 6, 4), (5, 7, 4)} else None


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _rival_sorted(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return _apply_commands(_crop_nonzero(checked[1:]), sorted(_commands(checked)))


def _rival_first(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    commands = _commands(checked)
    return _apply_commands(_crop_nonzero(checked[1:]), commands[:1])


def _rival_last(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    commands = _commands(checked)
    return _apply_commands(_crop_nonzero(checked[1:]), commands[-1:])


def _rival_strip_code_payload(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    body = [
        [0 if value in (1, 2, 3, 4) else value for value in row]
        for row in checked[1:]
    ]
    return _apply_commands(_crop_nonzero(body), _commands(checked))


SEMANTIC_RIVALS = {
    "sort_commands": _rival_sorted,
    "first_command_only": _rival_first,
    "last_command_only": _rival_last,
    "strip_code_payload": _rival_strip_code_payload,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"sort_commands": _rival_sorted}


def _witness_order(grid):
    try:
        return _rival_sorted(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _witness_all_commands(grid):
    try:
        intended = rule_mirror(grid)
        return _rival_first(grid) != intended and _rival_last(grid) != intended
    except ValueError:
        return False


def _witness_code_payload(grid):
    try:
        body_has_code = any(value in (1, 2, 3, 4) for row in grid[1:] for value in row)
        return body_has_code and _rival_strip_code_payload(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _witness_multicolor(grid):
    try:
        return _texture_of(_crop_nonzero(grid[1:])) == "multicolor_body"
    except (TypeError, ValueError):
        return False


def _witness_disconnected(grid):
    try:
        return _component_count(_crop_nonzero(grid[1:])) == 2
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "ordered_sequence_visible": _witness_order,
    "all_commands_visible": _witness_all_commands,
    "body_code_colors_are_payload": _witness_code_payload,
    "multicolor_body": _witness_multicolor,
    "disconnected_body": _witness_disconnected,
}
WITNESS_RIVALS = {
    "ordered_sequence_visible": ["sort_commands"],
    "all_commands_visible": ["first_command_only", "last_command_only"],
    "body_code_colors_are_payload": ["strip_code_payload"],
}
BRANCH_WITNESSES = ("multicolor_body", "disconnected_body")


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # deterministic hook: surface malformed lesson data
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _axis_int(ctx, name, lo, hi, default_options):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(default_options))


def _axis_texture(ctx, default):
    if "texture" in ctx.overrides and ctx.overrides["texture"] is not None:
        return ctx.draw_choice("texture", HELPFUL_TEXTURES)
    return ctx.draw_choice("texture", (default,))


def _difficulty_options(difficulty, easy, medium, hard, neutral):
    if difficulty == "easy":
        return easy
    if difficulty == "medium":
        return medium
    if difficulty == "hard":
        return hard
    return neutral


def _candidate_sequences(n_ops):
    marker = [[1, 2, 3], [4, 5, 6]]
    candidates = []
    for commands in product((1, 2, 3, 4), repeat=n_ops):
        intended = _apply_commands(marker, commands)
        if intended == _apply_commands(marker, sorted(commands)):
            continue
        if intended == _apply_commands(marker, commands[:1]):
            continue
        if intended == _apply_commands(marker, commands[-1:]):
            continue
        candidates.append(commands)
    return tuple(candidates)


_ORDER_SENSITIVE_SEQUENCES = {
    n_ops: _candidate_sequences(n_ops) for n_ops in (2, 3, 4)
}


def _draw_commands(rng, n_ops, profile):
    if n_ops == 1:
        return (rng.choice((1, 2, 3, 4)),)
    if profile == "canonical_order" and n_ops == 2:
        return (3, 1)
    candidates = _ORDER_SENSITIVE_SEQUENCES[n_ops]
    if not candidates:
        raise RuntimeError(f"no order-sensitive command sequence for n_ops={n_ops}")
    return rng.choice(candidates)


def _normalize_cells(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    normalized = {(r - top, c - left) for r, c in cells}
    height = max(r for r, _ in normalized) + 1
    width = max(c for _, c in normalized) + 1
    return normalized, height, width


def _mask_from_cells(cells, height, width):
    return [[1 if (r, c) in cells else 0 for c in range(width)] for r in range(height)]


def _random_connected_cells(rng, max_h, max_w):
    target = rng.randint(5, min(10, max_h * max_w - 1))
    cells = {(0, 0)}
    while len(cells) < target:
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        nxt = (r + dr, c + dc)
        trial, height, width = _normalize_cells(cells | {nxt})
        if height <= max_h and width <= max_w:
            cells = trial
    return _normalize_cells(cells)


def _random_disconnected_cells(rng, max_h, max_w):
    height = rng.randint(3, max_h)
    width = rng.randint(3, max_w)
    area = height * width
    for _ in range(512):
        count = rng.randint(4, min(9, area - 1))
        indexes = rng.sample(range(area), count)
        cells = {(index // width, index % width) for index in indexes}
        if min(r for r, _ in cells) != 0 or max(r for r, _ in cells) != height - 1:
            continue
        if min(c for _, c in cells) != 0 or max(c for _, c in cells) != width - 1:
            continue
        mask = _mask_from_cells(cells, height, width)
        if _component_count(mask) == 2 and len(_dihedral_keys(mask)) == 8:
            return cells, height, width
    fallback = {(0, 0), (0, 1), (1, 1), (2, 2)}
    return fallback, 3, 3


def _draw_shape(rng, max_h, max_w, *, disconnected):
    max_h = max(3, min(max_h, 6))
    max_w = max(3, min(max_w, 6))
    for _ in range(512):
        if disconnected:
            cells, height, width = _random_disconnected_cells(rng, max_h, max_w)
        else:
            cells, height, width = _random_connected_cells(rng, max_h, max_w)
        if height < 2 or width < 2:
            continue
        mask = _mask_from_cells(cells, height, width)
        if len(_dihedral_keys(mask)) != 8:
            continue
        if _component_count(mask) != (2 if disconnected else 1):
            continue
        return sorted(cells), height, width
    if disconnected:
        cells = [(0, 0), (0, 1), (1, 1), (2, 2)]
    else:
        cells = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 1)]
    return cells, 3, 3


def _color_shape(rng, cells, height, width, texture):
    crop = [[0] * width for _ in range(height)]
    ordered = list(cells)
    rng.shuffle(ordered)
    if texture == "plain":
        colors = [rng.choice((5, 6, 7, 8, 9))]
    elif texture == "code_colored_body":
        colors = [rng.choice((1, 2, 3, 4))]
    elif texture == "multicolor_body":
        colors = [rng.choice((1, 2, 3, 4)), rng.choice((5, 6, 7, 8, 9))]
        extra = [value for value in range(1, 10) if value not in colors]
        if len(ordered) >= 7 and rng.random() < 0.5:
            colors.append(rng.choice(extra))
    else:
        raise ValueError(f"unknown texture {texture!r}")
    for index, (r, c) in enumerate(ordered):
        crop[r][c] = colors[index % len(colors)]
    return crop


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile in ("canonical_order", "disconnected_body"):
        h_defaults = (5,)
        w_defaults = (6, 7)
        n_defaults = (2,)
        texture_default = "plain"
    else:
        h_defaults = _difficulty_options(
            difficulty,
            (5, 6, 7, 8),
            (6, 7, 8, 9, 10, 11),
            (8, 9, 10, 11, 12, 13, 14),
            tuple(range(5, 15)),
        )
        w_defaults = _difficulty_options(
            difficulty,
            (6, 7, 8, 9),
            (7, 8, 9, 10, 11, 12),
            (9, 10, 11, 12, 13, 14),
            tuple(range(6, 15)),
        )
        n_defaults = {
            "code_payload": (3,),
            "multicolor_payload": (4,),
            "disconnected_body": (2, 3),
        }[profile]
        texture_default = {
            "code_payload": "code_colored_body",
            "multicolor_payload": "multicolor_body",
            "disconnected_body": "plain",
        }[profile]

    h = _axis_int(ctx, "grid_h", 5, 14, h_defaults)
    w = _axis_int(ctx, "grid_w", 6, 14, w_defaults)
    n_ops = _axis_int(ctx, "n_ops", 1, 4, n_defaults)
    texture = _axis_texture(ctx, texture_default)

    rng = ctx.draw_rng(f"layout:{difficulty or 'none'}")
    commands = _draw_commands(rng, n_ops, profile)
    grid = [[0] * w for _ in range(h)]
    positions = sorted(rng.sample(range(w), n_ops))
    for position, command in zip(positions, commands):
        grid[0][position] = command

    disconnected = profile == "disconnected_body"
    cells, crop_h, crop_w = _draw_shape(rng, h - 1, w, disconnected=disconnected)
    crop = _color_shape(rng, cells, crop_h, crop_w, texture)
    top = rng.randint(1, h - crop_h)
    left = rng.randint(0, w - crop_w)
    for r in range(crop_h):
        for c in range(crop_w):
            if crop[r][c] != 0:
                grid[top + r][left + c] = crop[r][c]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_ops": n_ops, "texture": texture}
    if observed != expected:
        raise RuntimeError(f"axis observer mismatch: expected {expected}, got {observed}")
    return grid
