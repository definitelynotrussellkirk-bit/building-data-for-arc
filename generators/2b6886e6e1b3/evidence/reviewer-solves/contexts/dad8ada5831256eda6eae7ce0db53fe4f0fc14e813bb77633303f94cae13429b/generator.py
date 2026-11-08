"""Generator for ``2b6886e6e1b3`` — command-transform overlap.

The canonical task has two monochrome 3x3 occupancy masks separated by a
zero column.  A command cell above the separator selects how the RIGHT mask is
transformed before intersecting it with the LEFT mask.  Generated lessons keep
that morphology, cycle through all four commands in every four-sample window,
and reject mask pairs for which a wrong transform gives the same answer.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b6886e6e1b3"
TASK_ID = "2b6886e6e1b3"
VERSION = "4.1.0"
RULE_HASH = "860b011c178c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A fixed 4x7 zero-background input contains a command at (0,3), a "
    "connected monochrome five-cell LEFT 3x3 motif in rows 1..3 / cols 0..2, and a "
    "connected monochrome five-cell RIGHT 3x3 motif in rows 1..3 / cols 4..6. Command "
    "1 keeps the right mask unchanged, 2 rotates it 90 degrees clockwise, 3 "
    "flips it left-right, and 4 rotates it 180 degrees. The 3x3 output paints "
    "8 exactly on the occupancy intersection of LEFT and transformed RIGHT. "
    "Ordinary draws force a nonempty proper intersection and make the selected "
    "transform disagree with every other command transform."
)

INVARIANTS = [
    "input is 4x7 with the only top-row nonzero at command position (0,3)",
    "rows 1..3 contain two nonempty 3x3 panels separated by a zero column",
    "ordinary generated panels are connected monochrome five-cell motifs, matching canonical morphology",
    "commands 1..4 mean identity, clockwise-90, left-right flip, and 180 rotation",
    "ordinary generated output overlap is nonempty, proper, and transform-disambiguating",
]

AXES = {
    "cmd": {
        "type": "int",
        "default": "four-step lesson schedule",
        "valid": "1..4",
    },
    "overlap_size": {
        "type": "int",
        "default": "difficulty-aware 1..4",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (1, 2, 3, 4)
_DIFFICULTY_BANDS = (None, "easy", "medium", "hard")
_ALL_CELLS = tuple((r, c) for r in range(3) for c in range(3))


def _is_connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, column = frontier.pop()
        for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + delta_row, column + delta_column)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return seen == cells


_CONNECTED_FIVE_CELL_MASKS = tuple(
    frozenset(cells)
    for cells in combinations(_ALL_CELLS, 5)
    if _is_connected(cells)
)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _turn_cw(cells):
    return {(c, 2 - r) for r, c in cells}


def _turn_180(cells):
    return {(2 - r, 2 - c) for r, c in cells}


def _mirror_lr(cells):
    return {(r, 2 - c) for r, c in cells}


def _apply_cmd(cells, cmd):
    cells = set(cells)
    if cmd == 1:
        return cells
    if cmd == 2:
        return _turn_cw(cells)
    if cmd == 3:
        return _mirror_lr(cells)
    if cmd == 4:
        return _turn_180(cells)
    raise ValueError(f"unsupported command {cmd!r}")


def _scene(grid):
    """Extract command and occupancy masks from a structurally valid 4x7 grid."""
    cmd = grid[0][3]
    left = {(r, c) for r in range(3) for c in range(3) if grid[1 + r][c] != 0}
    right = {(r, c) for r in range(3) for c in range(3) if grid[1 + r][4 + c] != 0}
    return cmd, left, right


def _candidate_outputs(left, right):
    return {cmd: set(left) & _apply_cmd(right, cmd) for cmd in SCHEDULE_PROFILES}


def _mask_grid(cells):
    out = full_grid(3, 3, 0)
    for r, c in cells:
        out[r][c] = 8
    return out


def _apply_rule(grid):
    """Pure Python mirror used only for semantic rivals/tests; Racket remains authority."""
    cmd, left, right = _scene(grid)
    return _mask_grid(left & _apply_cmd(right, cmd))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible input grammar without curriculum-only constraints."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    if len(grid) != 4 or len(grid[0]) != 7:
        return [f"expected 4x7 grid, got {len(grid)}x{len(grid[0])}"]

    cmd = grid[0][3]
    if cmd not in SCHEDULE_PROFILES:
        errors.append(f"expected command 1..4 at (0,3), got {cmd}")

    stray_top = [(0, c) for c in range(7) if c != 3 and grid[0][c] != 0]
    if stray_top:
        errors.append(f"top row must be zero outside the command cell: {stray_top[:3]}")

    stray_separator = [(r, 3) for r in range(1, 4) if grid[r][3] != 0]
    if stray_separator:
        errors.append(f"separator column must stay zero below the command: {stray_separator[:3]}")

    _, left, right = _scene(grid)
    if not left:
        errors.append("left 3x3 panel must contain at least one nonzero cell")
    if not right:
        errors.append("right 3x3 panel must contain at least one nonzero cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the linked morphology shared by every canonical input and normal draw."""
    errors = self_check(grid)
    if errors:
        return errors

    cmd, left, right = _scene(grid)
    if len(left) != 5:
        errors.append(f"canonical left motif has five occupied cells, found {len(left)}")
    if len(right) != 5:
        errors.append(f"canonical right motif has five occupied cells, found {len(right)}")

    left_colors = {grid[1 + r][c] for r, c in left}
    right_colors = {grid[1 + r][4 + c] for r, c in right}
    if len(left_colors) != 1:
        errors.append(f"canonical left motif is monochrome, found colors {sorted(left_colors)}")
    if len(right_colors) != 1:
        errors.append(f"canonical right motif is monochrome, found colors {sorted(right_colors)}")

    if not _is_connected(left):
        errors.append("canonical-like left motif must be four-connected")
    if not _is_connected(right):
        errors.append("canonical-like right motif must be four-connected")

    overlap = left & _apply_cmd(right, cmd)
    if not (1 <= len(overlap) <= 4):
        errors.append(
            "canonical-like teaching scenes require a nonempty proper overlap; "
            f"found {len(overlap)} occupied output cells"
        )
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive samples contain each command exactly once."""
    return 1 + ((int(seed) + int(sample_index)) % 4)


def _default_overlap_bounds(difficulty):
    # A smaller overlap leaves more distractor occupancy and is visually harder.
    if difficulty == "easy":
        return 3, 4
    if difficulty == "hard":
        return 1, 2
    if difficulty == "medium":
        return 2, 3
    return 1, 4


def _choose_masks(rng, cmd: int, overlap_size: int):
    """Find two five-cell masks whose selected transform is answer-unique."""
    for _ in range(2000):
        left = set(rng.choice(_CONNECTED_FIVE_CELL_MASKS))
        right = set(rng.choice(_CONNECTED_FIVE_CELL_MASKS))
        outputs = _candidate_outputs(left, right)
        target = outputs[cmd]
        if len(target) != overlap_size:
            continue
        if any(target == outputs[other] for other in SCHEDULE_PROFILES if other != cmd):
            continue
        return left, right
    raise RuntimeError(
        f"unable to sample transform-disambiguating masks for cmd={cmd}, "
        f"overlap_size={overlap_size}"
    )


def _panel_colors(rng, cmd: int, seed: int, sample_index: int):
    """Stay on canonical 3/4-color profiles and show command color is positional."""
    share_command = (int(seed) + int(sample_index)) % 4 == 0
    if share_command:
        other = rng.choice([color for color in range(1, 10) if color != cmd])
        if rng.randrange(2):
            return cmd, other
        return other, cmd
    left, right = rng.sample([color for color in range(1, 10) if color != cmd], 2)
    return left, right


def observe_overrides(grid) -> dict[str, int]:
    cmd, left, right = _scene(grid)
    return {
        "cmd": cmd,
        "overlap_size": len(left & _apply_cmd(right, cmd)),
    }


def _rival_fixed_transform(grid, fixed_cmd: int):
    _, left, right = _scene(grid)
    return _mask_grid(left & _apply_cmd(right, fixed_cmd))


def _rival_identity(grid):
    return _rival_fixed_transform(grid, 1)


def _rival_cw90(grid):
    return _rival_fixed_transform(grid, 2)


def _rival_flip_lr(grid):
    return _rival_fixed_transform(grid, 3)


def _rival_180(grid):
    return _rival_fixed_transform(grid, 4)


def _rival_left_mask(grid):
    _, left, _ = _scene(grid)
    return _mask_grid(left)


def _rival_transformed_right_mask(grid):
    cmd, _, right = _scene(grid)
    return _mask_grid(_apply_cmd(right, cmd))


def _rival_union(grid):
    cmd, left, right = _scene(grid)
    return _mask_grid(left | _apply_cmd(right, cmd))


def _command_witness(grid, expected_cmd: int) -> bool:
    if self_check(grid):
        return False
    cmd, left, right = _scene(grid)
    if cmd != expected_cmd:
        return False
    outputs = _candidate_outputs(left, right)
    target = outputs[cmd]
    return bool(target) and all(
        target != outputs[other] for other in SCHEDULE_PROFILES if other != cmd
    )


def _has_cmd_1_witness(grid):
    return _command_witness(grid, 1)


def _has_cmd_2_witness(grid):
    return _command_witness(grid, 2)


def _has_cmd_3_witness(grid):
    return _command_witness(grid, 3)


def _has_cmd_4_witness(grid):
    return _command_witness(grid, 4)


def _has_partial_intersection(grid):
    if self_check(grid):
        return False
    cmd, left, right = _scene(grid)
    overlap = left & _apply_cmd(right, cmd)
    return 0 < len(overlap) < min(len(left), len(right))


SEMANTIC_WITNESSES = {
    "cmd_identity_disambiguated": _has_cmd_1_witness,
    "cmd_cw90_disambiguated": _has_cmd_2_witness,
    "cmd_flip_lr_disambiguated": _has_cmd_3_witness,
    "cmd_180_disambiguated": _has_cmd_4_witness,
    "proper_intersection_not_whole_mask": _has_partial_intersection,
}

SEMANTIC_RIVALS = {
    "fixed_identity": _rival_identity,
    "fixed_cw90": _rival_cw90,
    "fixed_flip_lr": _rival_flip_lr,
    "fixed_180": _rival_180,
    "copy_left_mask": _rival_left_mask,
    "copy_transformed_right_mask": _rival_transformed_right_mask,
    "union_instead_of_intersection": _rival_union,
}

WITNESS_RIVALS = {
    "cmd_identity_disambiguated": ["fixed_cw90", "fixed_flip_lr", "fixed_180"],
    "cmd_cw90_disambiguated": ["fixed_identity", "fixed_flip_lr", "fixed_180"],
    "cmd_flip_lr_disambiguated": ["fixed_identity", "fixed_cw90", "fixed_180"],
    "cmd_180_disambiguated": ["fixed_identity", "fixed_cw90", "fixed_flip_lr"],
    "proper_intersection_not_whole_mask": [
        "copy_left_mask",
        "copy_transformed_right_mask",
        "union_instead_of_intersection",
    ],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """A four-demo lesson must establish every command and kill named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    commands: set[int] = set()
    survivors = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        strict_errors = strict_canonical_like(grid)
        if strict_errors:
            errors.append(f"demo {index} is outside the teaching grammar: {strict_errors[0]}")
            continue
        commands.add(grid[0][3])
        authoritative = _apply_rule(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    missing = sorted(set(SCHEDULE_PROFILES) - commands)
    if missing:
        errors.append(f"demonstrations do not establish command(s): {missing}")

    query_grid = query["input"]
    query_errors = strict_canonical_like(query_grid)
    if query_errors:
        errors.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif query_grid[0][3] not in commands:
        errors.append(f"query command {query_grid[0][3]} was not demonstrated")
    if "output" in query and not query_errors and query["output"] != _apply_rule(query_grid):
        errors.append("query output disagrees with the selected rule")

    if survivors:
        errors.append("demonstrations leave rival rule(s) alive: " + ", ".join(sorted(survivors)))
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, override-exact, shortcut-rebutting input grid."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _DIFFICULTY_BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_cmd = schedule_profile(seed, sample_index, difficulty)
    if "cmd" in overrides:
        cmd = ctx.draw_int_strict("cmd", 1, 4)
    else:
        cmd = ctx.draw_int("cmd", scheduled_cmd, scheduled_cmd)

    if "overlap_size" in overrides:
        overlap_size = ctx.draw_int_strict("overlap_size", 1, 4)
    else:
        lo, hi = _default_overlap_bounds(difficulty)
        overlap_size = ctx.draw_int("overlap_size", lo, hi)

    rng = ctx.draw_rng("layout")
    left, right = _choose_masks(rng, cmd, overlap_size)
    left_color, right_color = _panel_colors(rng, cmd, seed, sample_index)

    grid = full_grid(4, 7, 0)
    grid[0][3] = cmd
    for r, c in left:
        grid[1 + r][c] = left_color
    for r, c in right:
        grid[1 + r][4 + c] = right_color
    return grid
