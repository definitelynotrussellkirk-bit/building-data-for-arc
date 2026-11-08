"""Generator for d01b33f4a589: tile a motif by four corner commands.

The four corners are transform commands: 1 rotates clockwise, 2 rotates
180 degrees, 3 reflects left/right, and 4 reflects up/down.  Ignoring those
corner cells, crop the single central motif and apply the four commands in
reading order.  The transformed crops are packed into a 2-by-2 output.

All five demonstrated canvas/motif profiles are represented.  Generalized
draws vary motif orientation, position, color, and command order while
retaining a returned-grid-observable canonical profile.  Every four consecutive
unconstrained draws contain an asymmetric L4 with all four commands and a
non-public command order.  This identifies the command mapping rather than
merely hoping that independent examples expose each operation.
"""
from __future__ import annotations

from collections import deque
from functools import partial
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "d01b33f4a589"
TASK_ID = "d01b33f4a589"
VERSION = "3.1.0"
RULE_HASH = "0bc6b5986853"

SUMMARY = (
    "Read the four corner cells as transform commands, crop the non-corner "
    "motif, transform it once per corner in reading order, and pack the four "
    "variants into a 2-by-2 output."
)

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)
_ANCHOR_PROFILE = "l4_9x9"
_ANCHOR_COMMANDS = tuple(
    order for order in permutations((1, 2, 3, 4))
    if order != (1, 2, 3, 4)
)

INVARIANTS = [
    "zero is background and every corner command is in {1,2,3,4}",
    "the four commands form either a 1/2/3/4 permutation or 1/2/2/3",
    "one monochrome 4-connected motif lies strictly inside the canvas",
    "the motif may reuse a command color, because corners are ignored by position",
    "the motif belongs to one of the five demonstrated shape/canvas profiles",
    "symmetric motifs are valid even when multiple commands yield the same crop",
]

SCENE_PROFILES = (
    "l4_9x9",
    "stair5_10x10",
    "l3_9x9",
    "t4_10x10",
    "v5_9x9",
)

COMMAND_PROFILES = (
    "permutation",
    "repeat_two",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "one L4 anchor per four draws; otherwise difficulty-weighted",
        "valid": "l4_9x9|stair5_10x10|l3_9x9|t4_10x10|v5_9x9",
        "doc": (
            "Linked canvas size and motif dihedral class, recovered from the "
            "returned grid."
        ),
    },
    "command_profile": {
        "type": "str",
        "default": "anchor permutation; otherwise 80% permutation, 20% repeat_two",
        "valid": "permutation|repeat_two",
        "doc": (
            "The exact corner-code multiset: {1,2,3,4} or {1,2,2,3}."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PROFILE_DATA = {
    "l4_9x9": {
        "canvas": (9, 9),
        "shape": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "public_command_profile": "permutation",
        "canonical": (
            "100000002",
            "000000000",
            "000000000",
            "000200000",
            "000200000",
            "000220000",
            "000000000",
            "000000000",
            "300000004",
        ),
    },
    "stair5_10x10": {
        "canvas": (10, 10),
        "shape": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        "public_command_profile": "permutation",
        "canonical": (
            "4000000001",
            "0000000000",
            "0000000000",
            "0000000000",
            "0000500000",
            "0000550000",
            "0000055000",
            "0000000000",
            "0000000000",
            "2000000003",
        ),
    },
    "l3_9x9": {
        "canvas": (9, 9),
        "shape": ((0, 0), (0, 1), (1, 0)),
        "public_command_profile": "repeat_two",
        "canonical": (
            "200000002",
            "000000000",
            "000000000",
            "000044000",
            "000040000",
            "000000000",
            "000000000",
            "000000000",
            "300000001",
        ),
    },
    "t4_10x10": {
        "canvas": (10, 10),
        "shape": ((0, 0), (0, 1), (0, 2), (1, 1)),
        "public_command_profile": "permutation",
        "canonical": (
            "3000000004",
            "0000000000",
            "0000000000",
            "0000000000",
            "0006660000",
            "0000600000",
            "0000000000",
            "0000000000",
            "0000000000",
            "1000000002",
        ),
    },
    "v5_9x9": {
        "canvas": (9, 9),
        "shape": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        "public_command_profile": "permutation",
        "canonical": (
            "100000003",
            "000000000",
            "000000000",
            "000700000",
            "000700000",
            "000777000",
            "000000000",
            "000000000",
            "400000002",
        ),
    },
}

_PUBLIC_GRIDS = {
    profile: tuple(
        tuple(int(value) for value in row)
        for row in data["canonical"]
    )
    for profile, data in _PROFILE_DATA.items()
}

_PUBLIC_GRID_TO_PROFILE = {
    grid: profile
    for profile, grid in _PUBLIC_GRIDS.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted = []
    errors = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(
        sorted((row - row0, col - col0) for row, col in cells)
    )


def _rotate90_cells(cells):
    normalized = _normalize(cells)
    height = max(row for row, _col in normalized) + 1
    return _normalize(
        (col, height - 1 - row)
        for row, col in normalized
    )


def _reflect_rows_cells(cells):
    normalized = _normalize(cells)
    height = max(row for row, _col in normalized) + 1
    return _normalize(
        (height - 1 - row, col)
        for row, col in normalized
    )


def _dihedral_forms(cells):
    forms = set()
    current = _normalize(cells)
    for _index in range(4):
        forms.add(current)
        forms.add(_reflect_rows_cells(current))
        current = _rotate90_cells(current)
    return tuple(sorted(forms))


def _dihedral_key(cells):
    return min(_dihedral_forms(cells))


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    start = min(cells)
    remaining = cells - {start}
    queue = deque([start])
    seen = {start}
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in (
            (-1, 0),
            (0, -1),
            (0, 1),
            (1, 0),
        ):
            candidate = (row + delta_row, col + delta_col)
            if candidate in remaining:
                remaining.remove(candidate)
                seen.add(candidate)
                queue.append(candidate)
    return len(seen) == len(cells)


def _corner_values(grid):
    height = len(grid)
    width = len(grid[0])
    return (
        grid[0][0],
        grid[0][width - 1],
        grid[height - 1][0],
        grid[height - 1][width - 1],
    )


def _command_profile(values):
    ordered = sorted(values)
    if ordered == [1, 2, 3, 4]:
        return "permutation"
    if ordered == [1, 2, 2, 3]:
        return "repeat_two"
    return None


def _motif_cells_and_crop(grid):
    height = len(grid)
    width = len(grid[0])
    ignored = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    colored = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in ignored
    ]
    if not colored:
        return (), []
    row0 = min(row for row, _col, _value in colored)
    row1 = max(row for row, _col, _value in colored)
    col0 = min(col for _row, col, _value in colored)
    col1 = max(col for _row, col, _value in colored)
    crop = [
        [0 for _col in range(col0, col1 + 1)]
        for _row in range(row0, row1 + 1)
    ]
    for row, col, value in colored:
        crop[row - row0][col - col0] = value
    cells = tuple((row, col) for row, col, _value in colored)
    return cells, crop


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(original)
    width = len(original[0])
    commands = _corner_values(original)
    command_profile = _command_profile(commands)
    if command_profile is None:
        return None

    cells, crop = _motif_cells_and_crop(original)
    if not cells or not _connected(cells):
        return None
    colors = {
        original[row][col]
        for row, col in cells
    }
    if len(colors) != 1:
        return None
    if any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in cells
    ):
        return None

    shape_key = _dihedral_key(cells)
    profile = next(
        (
            name
            for name, data in _PROFILE_DATA.items()
            if data["canvas"] == (height, width)
            and _dihedral_key(data["shape"]) == shape_key
        ),
        None,
    )
    if profile is None:
        return None
    return {
        "scene_profile": profile,
        "command_profile": command_profile,
        "commands": commands,
        "motif_cells": cells,
        "motif_crop": crop,
        "motif_color": next(iter(colors)),
        "exact_public": (
            tuple(tuple(row) for row in original) in _PUBLIC_GRID_TO_PROFILE
        ),
    }


def observe_overrides(grid):
    """Recover every declared semantic control from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "command_profile": analysis["command_profile"],
    }


def canonical_profile_index(grid):
    """Return the linked demonstrated motif/canvas profile index."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def exact_public_profile_index(grid):
    """Return the public input index only for a literal demonstrated input."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    profile = _PUBLIC_GRID_TO_PROFILE.get(
        tuple(tuple(row) for row in original)
    )
    return _PROFILE_INDEX[profile] if profile is not None else None


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the calibrated five-profile input grammar."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = _analyze_scene(original)
    if analysis is None:
        return [
            "grid must contain a linked 9x9/10x10 monochrome motif "
            "profile and one valid four-corner command multiset"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for axis in AXES:
            if (
                axis in requested
                and requested[axis] is not None
                and analysis[axis] != requested[axis]
            ):
                errors.append(
                    f"{axis} requested {requested[axis]!r}, "
                    f"observed {analysis[axis]!r}"
                )
    return errors


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")
    if (
        "command_profile" in overrides
        and overrides["command_profile"] not in COMMAND_PROFILES
    ):
        raise ValueError("unknown command_profile")


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "l4_9x9",
            "l4_9x9",
            "l4_9x9",
            "l3_9x9",
            "l3_9x9",
            "l3_9x9",
            "t4_10x10",
            "stair5_10x10",
            "v5_9x9",
        )
    if difficulty == "hard":
        return (
            "l4_9x9",
            "l3_9x9",
            "t4_10x10",
            "t4_10x10",
            "stair5_10x10",
            "stair5_10x10",
            "stair5_10x10",
            "v5_9x9",
            "v5_9x9",
            "v5_9x9",
        )
    return SCENE_PROFILES


def _command_options():
    return (
        "permutation",
        "permutation",
        "permutation",
        "permutation",
        "repeat_two",
    )


def _command_values(profile, rng):
    values = (
        [1, 2, 3, 4]
        if profile == "permutation"
        else [1, 2, 2, 3]
    )
    rng.shuffle(values)
    return values


def _paint_shape(grid, shape, row0, col0, color):
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def _render_generalized(scene_profile, command_profile, rng, *, anchor=False):
    data = _PROFILE_DATA[scene_profile]
    height, width = data["canvas"]
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    commands = (
        list(rng.choice(_ANCHOR_COMMANDS))
        if anchor else _command_values(command_profile, rng)
    )
    grid[0][0] = commands[0]
    grid[0][width - 1] = commands[1]
    grid[height - 1][0] = commands[2]
    grid[height - 1][width - 1] = commands[3]

    shape = rng.choice(_dihedral_forms(data["shape"]))
    shape_height = max(row for row, _col in shape) + 1
    shape_width = max(col for _row, col in shape) + 1
    row0 = rng.randint(2, height - shape_height - 2)
    col0 = rng.randint(2, width - shape_width - 2)
    motif_color = rng.randint(1, 9)
    _paint_shape(grid, shape, row0, col0, motif_color)

    frozen = tuple(tuple(row) for row in grid)
    if frozen in _PUBLIC_GRID_TO_PROFILE:
        replacement = motif_color % 9 + 1
        for row, col in shape:
            grid[row0 + row][col0 + col] = replacement
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-phased four-draw cycle, independent of call order and global RNG.

    This describes the default schedule only. Explicit semantic overrides
    always take precedence, and intentionally need not identify a lesson.
    """
    phase_ctx = gen_ctx(
        seed=seed, sample_index=0, version=VERSION,
        task_id=TASK_ID, difficulty=difficulty,
    )
    phase = phase_ctx.draw_int("lesson_phase", 0, len(SCHEDULE_PROFILES) - 1)
    return (sample_index + phase) % len(SCHEDULE_PROFILES)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    # Create the phase context first: provenance consumers observe the last
    # context, which must be the one carrying the two exact semantic axes.
    anchor = not overrides and schedule_profile(seed, sample_index, difficulty) == 0
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice(
        "scene_profile",
        (_ANCHOR_PROFILE,) if anchor else _profile_options(difficulty),
    )
    command_profile = ctx.draw_choice(
        "command_profile",
        ("permutation",) if anchor else _command_options(),
    )
    rng = ctx.draw_rng("layout")

    public_command = _PROFILE_DATA[scene_profile][
        "public_command_profile"
    ]
    if public_command == "repeat_two":
        literal_probability = 0.25
    else:
        literal_probability = 0.0625
    # Anchors are never literal public inputs. Compensate on ordinary slots
    # to retain the original approximately 5% public-input prior overall.
    if not overrides:
        literal_probability *= 4 / 3
    literal_public = (
        not anchor
        and command_profile == public_command
        and rng.random() < literal_probability
    )
    if literal_public:
        grid = [
            list(row)
            for row in _PUBLIC_GRIDS[scene_profile]
        ]
    else:
        grid = _render_generalized(
            scene_profile,
            command_profile,
            rng,
            anchor=anchor,
        )

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: "
            + "; ".join(errors)
        )
    return grid


def _rotate_cw_grid(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180_grid(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr_grid(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud_grid(grid):
    return [row[:] for row in reversed(grid)]


def _transform_code(grid, code):
    if code == 1:
        return _rotate_cw_grid(grid)
    if code == 2:
        return _rotate_180_grid(grid)
    if code == 3:
        return _flip_lr_grid(grid)
    return _flip_ud_grid(grid)


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    commands = _corner_values(original)
    _cells, motif = _motif_cells_and_crop(original)
    if not motif:
        raise ValueError("the rule requires a non-corner motif")
    variants = [
        _transform_code(motif, code)
        for code in commands
    ]
    cell_height = max(len(variant) for variant in variants)
    cell_width = max(len(variant[0]) for variant in variants)
    output = [
        [0 for _col in range(2 * cell_width)]
        for _row in range(2 * cell_height)
    ]
    for index, variant in enumerate(variants):
        top = (index // 2) * cell_height
        left = (index % 2) * cell_width
        for row, values in enumerate(variant):
            for col, value in enumerate(values):
                if value != 0:
                    output[top + row][left + col] = value
    return output


# Task-local semantic contracts. These rivals produce predictions only; all
# training labels still come from the unchanged canonical Racket authority.
def _command_alias(grid, *, source, replacement):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    for row, col in ((0, 0), (0, -1), (-1, 0), (-1, -1)):
        if original[row][col] == source:
            original[row][col] = replacement
    return rule_mirror(original)


def _public_command_order(grid):
    """Rival: infer command order from motif profile, not corner cells.

    It fits every published pair, but is wrong on lawful recombinations.
    No public outputs or cached labels are embedded in this rival.
    """
    analysis = _analyze_scene(grid)
    if analysis is None:
        raise ValueError("public-command rival requires a lawful task input")
    original = [list(row) for row in grid]
    commands = _corner_values(_PUBLIC_GRIDS[analysis["scene_profile"]])
    for (row, col), command in zip(
        ((0, 0), (0, -1), (-1, 0), (-1, -1)), commands
    ):
        original[row][col] = command
    return rule_mirror(original)


CANONICAL_SHORTCUTS = {"public_command_order": _public_command_order}
LESSON_COMPETITORS = {
    f"command_{source}_as_{replacement}": partial(
        _command_alias, source=source, replacement=replacement
    )
    for source in (1, 2, 3, 4)
    for replacement in (1, 2, 3, 4)
    if source != replacement
}
LESSON_COMPETITORS.update(CANONICAL_SHORTCUTS)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _informative_command_scene(grid):
    analysis = _analyze_scene(grid)
    return bool(
        analysis is not None
        and analysis["scene_profile"] == _ANCHOR_PROFILE
        and analysis["command_profile"] == "permutation"
        and analysis["commands"] != (1, 2, 3, 4)
    )


SEMANTIC_WITNESSES = {"informative_command_scene": _informative_command_scene}
WITNESS_RIVALS = {"informative_command_scene": list(SEMANTIC_RIVALS)}


def strict_canonical_like(grid):
    """The generated domain remains exactly the calibrated five-profile grammar."""
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Identify the query answer relative to the declared, finite rival set.

    Query labels are deliberately unused. Surviving rivals are harmless when
    they agree on this query; no claim of uniqueness over all programs is made.
    """
    if not demos:
        return ["no demonstrations"]
    for index, demo in enumerate(demos):
        if rule_mirror(demo["input"]) != demo["output"]:
            return [f"demonstration {index} disagrees with the canonical mirror"]
    query_input = query["input"] if isinstance(query, dict) else query
    expected = rule_mirror(query_input)
    return [
        f"{name}: fits all demonstrations but changes the query answer"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in demos)
        and rival(query_input) != expected
    ]
