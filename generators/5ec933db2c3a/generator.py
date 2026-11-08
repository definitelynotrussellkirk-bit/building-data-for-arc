"""Source-linked generator for repairing rotated exact-two-hole instances.

A full-height colour-9 divider separates a 3x3 two-colour template from a
board.  The selected Racket authority considers the template's four rotations,
finds every board window that is otherwise exact but is missing *exactly two*
occupied template cells, and restores those cells with their template colours.
The output is the repaired board only.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5ec933db2c3a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "009a49ded011"

SUMMARY = (
    "A colour-9 column separates a 3x3 template in colours 2 and 7 from a "
    "larger board. Consider all four rotations of the template. Complete only "
    "windows with exactly two missing occupied cells, restoring each missing "
    "cell with the corresponding template colour; leave one-hole, three-hole, "
    "wrong-colour, and extra-mark windows unchanged. Return the board alone."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input is a rectangular ARC grid using exactly colours 0, 2, 7, and 9",
    "column 3 is the sole full-height colour-9 divider",
    "the displayed template crops to 3x3 with six colour-2 cells and one colour-7 cell",
    "the right board contains at least one rotated window with exactly two missing occupied cells",
    "generated scenes also contain one-hole and three-hole negatives",
    "generated scenes require rotation and preserve the colour-7 template role",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware 7..10",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware 12..16",
        "valid": "12..16",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_BASE_TEMPLATE: tuple[tuple[int, ...], ...] = (
    (2, 7, 0),
    (2, 2, 2),
    (2, 0, 2),
)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def _valid_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and all(isinstance(row, list) and row for row in grid)
        and len({len(row) for row in grid}) == 1
        and all(
            type(value) is int and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid: list[list[int]]) -> list[list[list[int]]]:
    # The selected authority enumerates four rotations.  The task's asymmetric
    # template makes them distinct, but retain exact enumeration semantics.
    result: list[list[list[int]]] = []
    current = deepcopy(grid)
    for _ in range(4):
        result.append(deepcopy(current))
        current = _rotate_cw(current)
    return result


def _split_and_crop(
    grid: list[list[int]],
) -> tuple[list[list[int]], list[list[int]], int]:
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 1:
        raise ValueError(
            f"expected exactly one full-height colour-9 divider, got {dividers}"
        )
    divider = dividers[0]
    if divider <= 0 or divider >= w - 1:
        raise ValueError("divider must separate two nonempty panels")
    left = [row[:divider] for row in grid]
    board = [row[divider + 1 :] for row in grid]
    cells = [
        (r, c)
        for r, row in enumerate(left)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        raise ValueError("left panel has no template")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    template = [row[c0 : c1 + 1] for row in left[r0 : r1 + 1]]
    return template, board, divider


def _compatible_matches(
    grid: list[list[int]],
    *,
    use_rotations: bool = True,
) -> list[dict[str, Any]]:
    template, board, _divider = _split_and_crop(grid)
    variants = _rotations(template) if use_rotations else [template]
    matches: list[dict[str, Any]] = []
    for rotation_index, variant in enumerate(variants):
        th, tw = len(variant), len(variant[0])
        if th > len(board) or tw > len(board[0]):
            continue
        for r0 in range(len(board) - th + 1):
            for c0 in range(len(board[0]) - tw + 1):
                missing: list[tuple[int, int, int]] = []
                compatible = True
                for r, row in enumerate(variant):
                    for c, expected in enumerate(row):
                        actual = board[r0 + r][c0 + c]
                        if expected == 0:
                            if actual != 0:
                                compatible = False
                                break
                        elif actual == expected:
                            continue
                        elif actual == 0:
                            missing.append((r0 + r, c0 + c, expected))
                        else:
                            compatible = False
                            break
                    if not compatible:
                        break
                if compatible:
                    matches.append(
                        {
                            "rotation": rotation_index,
                            "row": r0,
                            "col": c0,
                            "missing": tuple(missing),
                        }
                    )
    return matches


def _repair(
    grid: list[list[int]],
    *,
    hole_counts: Iterable[int],
    use_rotations: bool = True,
    preserve_colours: bool = True,
) -> list[list[int]]:
    _template, board, _divider = _split_and_crop(grid)
    output = deepcopy(board)
    allowed = set(hole_counts)
    for match in _compatible_matches(grid, use_rotations=use_rotations):
        if len(match["missing"]) not in allowed:
            continue
        for r, c, colour in match["missing"]:
            output[r][c] = colour if preserve_colours else 2
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected Racket rule's active branch."""
    return _repair(grid, hole_counts=(2,))


def _repair_one_two_or_three_holes(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: repair every near-copy with one, two, or three holes."""
    return _repair(grid, hole_counts=(1, 2, 3))


def _repair_unrotated_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: inspect only the displayed template orientation."""
    return _repair(grid, hole_counts=(2,), use_rotations=False)


def _repair_every_hole_red(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: restore every missing cell as colour 2."""
    return _repair(grid, hole_counts=(2,), preserve_colours=False)


def _safe_witness(predicate: Callable[[list[list[int]]], bool], grid: Any) -> bool:
    try:
        return bool(_valid_grid(grid) and predicate(grid))
    except (TypeError, ValueError, IndexError):
        return False


def _exact_two_holes_witness(grid: Any) -> bool:
    def predicate(value: list[list[int]]) -> bool:
        counts = [len(match["missing"]) for match in _compatible_matches(value)]
        return (
            1 in counts
            and 3 in counts
            and _repair_one_two_or_three_holes(value) != rule_mirror(value)
        )

    return _safe_witness(predicate, grid)


def _rotation_witness(grid: Any) -> bool:
    def predicate(value: list[list[int]]) -> bool:
        return (
            any(
                match["rotation"] != 0 and len(match["missing"]) == 2
                for match in _compatible_matches(value)
            )
            and _repair_unrotated_only(value) != rule_mirror(value)
        )

    return _safe_witness(predicate, grid)


def _colour_role_witness(grid: Any) -> bool:
    def predicate(value: list[list[int]]) -> bool:
        return (
            any(
                len(match["missing"]) == 2
                and any(colour == 7 for _r, _c, colour in match["missing"])
                for match in _compatible_matches(value)
            )
            and _repair_every_hole_red(value) != rule_mirror(value)
        )

    return _safe_witness(predicate, grid)


SEMANTIC_RIVALS = {
    "repair_one_two_or_three_holes": _repair_one_two_or_three_holes,
    "repair_unrotated_only": _repair_unrotated_only,
    "repair_every_hole_red": _repair_every_hole_red,
}
SEMANTIC_WITNESSES = {
    "exactly_two_holes_only": _exact_two_holes_witness,
    "rotations_required": _rotation_witness,
    "preserve_template_colours": _colour_role_witness,
}
WITNESS_RIVALS = {
    "exactly_two_holes_only": ["repair_one_two_or_three_holes"],
    "rotations_required": ["repair_unrotated_only"],
    "preserve_template_colours": ["repair_every_hole_red"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    bounds = {"grid_h": (7, 10), "grid_w": (12, 16)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name} must be in {low}..{high}, got {value}")


def _has_override(ctx: Any, name: str) -> bool:
    return name in ctx.overrides and ctx.overrides[name] is not None


def _default_bounds(
    sample_index: int, difficulty: Any
) -> tuple[tuple[int, int], tuple[int, int]]:
    # Three out of every four draws are exact canonical profiles.  The fourth
    # expands scale while preserving the same semantics and minimum 7x8 board.
    profile = sample_index % 4
    if profile == 0:
        return (7, 7), (12, 12)
    if profile == 1:
        return (8, 8), (12, 12)
    if profile == 3:
        return (7, 8), (12, 12)
    if difficulty == "easy":
        return (7, 8), (12, 13)
    if difficulty == "hard":
        return (9, 10), (14, 16)
    return (8, 9), (13, 15)


def _draw_dimensions(ctx: Any, sample_index: int, difficulty: Any) -> tuple[int, int]:
    h_default, w_default = _default_bounds(sample_index, difficulty)
    h_bounds = (7, 10) if _has_override(ctx, "grid_h") else h_default
    w_bounds = (12, 16) if _has_override(ctx, "grid_w") else w_default
    return (
        ctx.draw_int("grid_h", *h_bounds),
        ctx.draw_int("grid_w", *w_bounds),
    )


def _paint_partial(
    board: list[list[int]],
    template: list[list[int]],
    origin: tuple[int, int],
    missing: set[tuple[int, int]],
) -> None:
    r0, c0 = origin
    for r, row in enumerate(template):
        for c, colour in enumerate(row):
            if colour and (r, c) not in missing:
                board[r0 + r][c0 + c] = colour


def _compose_input(
    h: int,
    total_w: int,
    template: list[list[int]],
    board: list[list[int]],
    template_row: int,
) -> list[list[int]]:
    grid = [[0 for _ in range(total_w)] for _ in range(h)]
    for r in range(h):
        grid[r][3] = 9
    for r, row in enumerate(template):
        for c, value in enumerate(row):
            grid[template_row + r][c] = value
    for r, row in enumerate(board):
        grid[r][4:] = row
    return grid


def _candidate_scene(
    h: int,
    total_w: int,
    template: list[list[int]],
    rng: Any,
) -> list[list[int]]:
    board_w = total_w - 4
    board = [[0 for _ in range(board_w)] for _ in range(h)]
    origins = [
        (0, 0),
        (0, board_w - 3),
        (h - 3, 0),
        (h - 3, board_w - 3),
    ]
    roles = ["rotated_target", "target", "one_hole", "three_holes"]
    rng.shuffle(roles)
    variants = _rotations(template)

    for origin, role in zip(origins, roles):
        if role == "rotated_target":
            rotation_index = rng.choice((1, 2, 3))
            hole_count = 2
        elif role == "target":
            rotation_index = rng.randrange(4)
            hole_count = 2
        elif role == "one_hole":
            rotation_index = rng.randrange(4)
            hole_count = 1
        else:
            rotation_index = rng.randrange(4)
            hole_count = 3

        variant = variants[rotation_index]
        occupied = [
            (r, c, value)
            for r, row in enumerate(variant)
            for c, value in enumerate(row)
            if value != 0
        ]
        if role == "rotated_target":
            seven = next(cell for cell in occupied if cell[2] == 7)
            other = rng.choice([cell for cell in occupied if cell != seven])
            holes = {seven[:2], other[:2]}
        else:
            holes = {cell[:2] for cell in rng.sample(occupied, hole_count)}
        _paint_partial(board, variant, origin, holes)

    template_row = rng.randint(0, h - 3)
    return _compose_input(h, total_w, template, board, template_row)


def _is_strong_generated_scene(grid: list[list[int]]) -> bool:
    try:
        exact_matches = [
            match
            for match in _compatible_matches(grid)
            if len(match["missing"]) == 2
        ]
        return (
            len(exact_matches) == 2
            and _exact_two_holes_witness(grid)
            and _rotation_witness(grid)
            and _colour_role_witness(grid)
            and rule_mirror(grid) != _split_and_crop(grid)[1]
        )
    except (TypeError, ValueError, IndexError):
        return False


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, total_w = _draw_dimensions(ctx, sample_index, difficulty)
    rng = ctx.draw_rng(f"scene_{difficulty or 'default'}")
    template = rng.choice(_rotations([list(row) for row in _BASE_TEMPLATE]))

    # Randomized construction has a high acceptance rate (~78% at the minimum
    # 7x8 board).  Validate against the exact scanner so no accidental shifted
    # two-hole window enters the curriculum; the deterministic fallback below
    # makes the return contract total rather than probabilistic.
    for _attempt in range(64):
        candidate = _candidate_scene(h, total_w, template, rng)
        if _is_strong_generated_scene(candidate):
            return candidate

    # This branch is not expected in the declared domain.  Use a separate,
    # deterministic local search rather than returning a weak/identity sample.
    for rotation in range(4):
        local_rng = ctx.draw_rng(f"fallback_{rotation}")
        fallback_template = _rotations(
            [list(row) for row in _BASE_TEMPLATE]
        )[rotation]
        for _attempt in range(256):
            candidate = _candidate_scene(h, total_w, fallback_template, local_rng)
            if _is_strong_generated_scene(candidate):
                return candidate
    raise RuntimeError("could not construct a strong exact-two-hole scene")


def observe_overrides(grid: Any) -> dict[str, int]:
    if not _valid_grid(grid):
        raise ValueError("grid must be a nonempty rectangular ARC colour grid")
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    if not _valid_grid(grid):
        return ["grid must be a nonempty rectangular ARC colour grid"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 7 <= h <= 10:
        errors.append(f"grid height must be in 7..10, got {h}")
    if not 12 <= w <= 16:
        errors.append(f"grid width must be in 12..16, got {w}")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 7, 9}:
        errors.append(f"palette must be exactly {{0,2,7,9}}, got {sorted(palette)}")

    try:
        template, board, divider = _split_and_crop(grid)
    except ValueError as exc:
        return sorted(set(errors + [str(exc)]))

    if divider != 3:
        errors.append(f"divider must be column 3, got {divider}")
    if any(value == 9 for row in grid for value in row[:divider] + row[divider + 1 :]):
        errors.append("colour 9 may appear only in the divider")
    if (len(template), len(template[0])) != (3, 3):
        errors.append(
            f"template crop must be 3x3, got {len(template)}x{len(template[0])}"
        )
    template_counts = {
        colour: sum(value == colour for row in template for value in row)
        for colour in (2, 7)
    }
    if template_counts != {2: 6, 7: 1}:
        errors.append(
            "template must contain six colour-2 cells and one colour-7 cell, "
            f"got {template_counts}"
        )
    if any(value not in (0, 2, 7) for row in board for value in row):
        errors.append("board may contain only colours 0, 2, and 7")

    if not errors:
        matches = [
            match
            for match in _compatible_matches(grid)
            if len(match["missing"]) == 2
        ]
        if not matches:
            errors.append("board has no exact-two-hole rotated template match")
        elif rule_mirror(grid) == board:
            errors.append("exact-two-hole matches do not change the board")
    return sorted(set(errors))


def strict_canonical_like(grid: Any) -> list[str]:
    """The generated grammar intentionally contains every canonical input."""
    return self_check(grid)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    del query
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError, IndexError) as exc:
            reasons.append(
                f"demonstration {index} input is invalid: {type(exc).__name__}: {exc}"
            )
            continue
        if expected != pair["output"]:
            reasons.append(f"demonstration {index} output disagrees with the rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survived = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:  # fail loud through a returned diagnostic
            reasons.append(f"declared competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survived:
            reasons.append(f"declared competitor {name} fits every demonstration")
    return reasons
