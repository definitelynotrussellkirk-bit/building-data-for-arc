"""Generator for "Make a Boolean Panel from Two Templates" (81d29e66f427).

The first row is an ordered list of operation keys.  Below it, two equal
colour-5 frames contain binary masks A (colour 2) and B (colour 3).  For each
key, the unchanged Racket authority emits one colour-8 panel: key 2 is A OR B,
key 3 is A AND B, and every other non-zero key is A XOR B.

This sampler keeps a canonical-layout component in every difficulty band and a
broader component for size/gap/key-count variation.  Default masks realize all
four binary truth states, and the three-example schedule includes both key 4
and a non-4 XOR key so lessons distinguish the actual "anything else" branch
from the canonical-only shortcut "only key 4 means XOR".
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import color_rect_frames, rect_border_cells

GENERATOR_ID = "81d29e66f427"
TASK_ID = GENERATOR_ID
RULE_HASH = "dfc8cc699169"
VERSION = "3.0.0"

SUMMARY = (
    "Ordered top-row keys request Boolean panels from two equal colour-5 framed "
    "masks: 2=OR, 3=AND, every other key=XOR. Canonical geometry is anchored in "
    "every band; broader dimensions, gaps, key counts, key order, and masks vary."
)

INVARIANTS = [
    "row 0 contains 1..5 distinct non-zero operation keys in output order",
    "two equal colour-5 frames sit side by side; left interior uses 0/2 and right uses 0/3",
    "default masks contain 00, 10, 01, and 11 cells so OR/AND/XOR are distinguishable",
]

# Every advertised exact control can be recovered from the returned pixels.
AXES = {
    "interior_h": {"type": "int", "default": "5 canonical / 3..6 broad", "valid": "3..6"},
    "interior_w": {"type": "int", "default": "4..6 canonical / 3..6 broad", "valid": "3..6"},
    "n_keys": {"type": "int", "default": "3 canonical / 3..5 broad", "valid": "1..5"},
    "gap": {"type": "int", "default": "1 canonical / 1..4 broad", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_KEY_CHOICES = (2, 3, 4, 6, 7, 9)  # 2=OR, 3=AND, all other listed keys=XOR
_XOR_KEYS = (4, 6, 7, 9)
SCHEDULE_PROFILES = ("canonical_key4", "canonical_other_xor", "broad")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.10


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic three-position curriculum; every consecutive triple covers it."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _axis_int(ctx, name: str, lo: int, hi: int, defaults: tuple[int, ...]) -> int:
    """Use strict full-domain validation for overrides and profile defaults otherwise."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _broad_defaults(difficulty) -> dict[str, tuple[int, ...]]:
    if difficulty == "easy":
        return {
            "interior_h": (3, 3, 4),
            "interior_w": (3, 4, 4),
            "n_keys": (3,),
            "gap": (1, 1, 2),
        }
    if difficulty == "hard":
        return {
            "interior_h": (4, 5, 6, 6),
            "interior_w": (4, 5, 6, 6),
            "n_keys": (4, 4, 5),
            "gap": (2, 3, 4, 4),
        }
    return {
        "interior_h": (3, 4, 5, 6),
        "interior_w": (3, 4, 5, 6),
        "n_keys": (3, 4, 5),
        "gap": (1, 2, 3, 4),
    }


def _draw_dimensions(ctx, profile: str, difficulty) -> tuple[int, int, int, int]:
    if profile in ("canonical_key4", "canonical_other_xor"):
        defaults = {
            "interior_h": (5,),
            "interior_w": (4, 5, 6),
            "n_keys": (3,),
            "gap": (1,),
        }
    else:
        defaults = _broad_defaults(difficulty)
    ih = _axis_int(ctx, "interior_h", 3, 6, defaults["interior_h"])
    iw = _axis_int(ctx, "interior_w", 3, 6, defaults["interior_w"])
    n_keys = _axis_int(ctx, "n_keys", 1, 5, defaults["n_keys"])
    gap = _axis_int(ctx, "gap", 1, 4, defaults["gap"])
    return ih, iw, n_keys, gap


def _draw_mask_pair(rng, ih: int, iw: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Construct masks containing every 00/10/01/11 truth state at least once."""
    cells = [(r, c) for r in range(ih) for c in range(iw)]
    rng.shuffle(cells)
    states = [(False, False), (True, False), (False, True), (True, True)]
    assignment = list(states)
    assignment.extend(rng.choice(states) for _ in range(len(cells) - len(states)))
    rng.shuffle(assignment)
    mask_a: set[tuple[int, int]] = set()
    mask_b: set[tuple[int, int]] = set()
    for cell, (in_a, in_b) in zip(cells, assignment):
        if in_a:
            mask_a.add(cell)
        if in_b:
            mask_b.add(cell)
    return mask_a, mask_b


def _operation_code(key: int) -> int:
    return 2 if key == 2 else 3 if key == 3 else 4


def _draw_keys(rng, n_keys: int, profile: str) -> list[int]:
    if profile == "canonical_key4":
        primary_xor = 4
    elif profile == "canonical_other_xor":
        primary_xor = rng.choice((6, 7, 9))
    else:
        # The broad profile always demonstrates the generalized XOR branch.
        primary_xor = rng.choice((6, 7, 9))

    semantic = [2, 3, primary_xor]
    if n_keys < 3:
        plan = rng.sample(semantic, n_keys)
    else:
        extras = [key for key in _XOR_KEYS if key != primary_xor]
        plan = semantic + rng.sample(extras, n_keys - 3)
        rng.shuffle(plan)
        # Refute the plausible fixed OR/AND/XOR panel-order shortcut in every
        # normal example.  For 4+ keys that shortcut already disagrees at panel 4.
        if n_keys == 3 and [_operation_code(k) for k in plan] == [2, 3, 4]:
            plan[0], plan[1] = plan[1], plan[0]
    return plan


def _put_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    for r, c in rect_border_cells(*box):
        grid[r][c] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    ih, iw, n_keys, gap = _draw_dimensions(ctx, profile, difficulty)

    # Canonical placement: row 0 keys, row 1 blank, frames start at row 2;
    # left frame is flush left, bottoms are flush, and two blank columns trail.
    outer_h, outer_w = ih + 2, iw + 2
    frame_top = 2
    left_col = 0
    right_col = left_col + outer_w + gap
    height = frame_top + outer_h
    width = right_col + outer_w + 2
    grid = full_grid(height, width, 0)
    left = (frame_top, left_col, height - 1, left_col + outer_w - 1)
    right = (frame_top, right_col, height - 1, right_col + outer_w - 1)
    _put_frame(grid, left)
    _put_frame(grid, right)

    mask_a, mask_b = _draw_mask_pair(ctx.draw_rng("masks"), ih, iw)
    for r, c in mask_a:
        grid[frame_top + 1 + r][left_col + 1 + c] = 2
    for r, c in mask_b:
        grid[frame_top + 1 + r][right_col + 1 + c] = 3

    key_rng = ctx.draw_rng("keys")
    key_plan = _draw_keys(key_rng, n_keys, profile)
    columns = sorted(key_rng.sample(range(width), n_keys))
    for column, key in zip(columns, key_plan):
        grid[0][column] = key
    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _parse(grid) -> dict:
    frames = sorted(
        color_rect_frames(grid, 5, min_outer_h=5, min_outer_w=5),
        key=lambda box: box[1],
    )
    if len(frames) != 2:
        raise ValueError(f"expected exactly two color-5 frames, found {len(frames)}")
    left, right = frames
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    left_dims = (lr2 - lr1 - 1, lc2 - lc1 - 1)
    right_dims = (rr2 - rr1 - 1, rc2 - rc1 - 1)
    if left_dims != right_dims:
        raise ValueError(f"frame interior dimensions differ: {left_dims} vs {right_dims}")
    mask_a = {
        (r - lr1 - 1, c - lc1 - 1)
        for r in range(lr1 + 1, lr2)
        for c in range(lc1 + 1, lc2)
        if grid[r][c] == 2
    }
    mask_b = {
        (r - rr1 - 1, c - rc1 - 1)
        for r in range(rr1 + 1, rr2)
        for c in range(rc1 + 1, rc2)
        if grid[r][c] == 3
    }
    return {
        "frames": frames,
        "left": left,
        "right": right,
        "interior_h": left_dims[0],
        "interior_w": left_dims[1],
        "gap": rc1 - lc2 - 1,
        "keys": [value for value in grid[0] if value != 0],
        "mask_a": mask_a,
        "mask_b": mask_b,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    errors = []
    try:
        info = _parse(grid)
    except ValueError as exc:
        return [str(exc)]

    left, right = info["left"], info["right"]
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    keys = info["keys"]
    if not 1 <= len(keys) <= 5:
        errors.append(f"expected 1..5 operation keys, found {len(keys)}")
    if any(key not in _KEY_CHOICES for key in keys):
        errors.append(f"operation keys must be chosen from {_KEY_CHOICES}")
    if len(set(keys)) != len(keys):
        errors.append("operation keys must be distinct")

    ih, iw, gap = info["interior_h"], info["interior_w"], info["gap"]
    if not 3 <= ih <= 6:
        errors.append(f"interior_h={ih} outside 3..6")
    if not 3 <= iw <= 6:
        errors.append(f"interior_w={iw} outside 3..6")
    if not 1 <= gap <= 4:
        errors.append(f"gap={gap} outside 1..4")
    if (lr1, rr1) != (2, 2) or (lr2, rr2) != (h - 1, h - 1):
        errors.append("frames must start at row 2 and be bottom-flush")
    if lc1 != 0:
        errors.append("left frame must be flush with the left edge")
    if rc1 <= lc2:
        errors.append("frames must be non-overlapping and ordered left to right")
    if w - rc2 - 1 != 2:
        errors.append("right frame must have exactly two trailing blank columns")
    if any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be blank")

    frame_cells = rect_border_cells(*left) | rect_border_cells(*right)
    actual_fives = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    if actual_fives != frame_cells:
        errors.append("color 5 must occur only on the two complete frame borders")

    left_interior = {
        (r, c)
        for r in range(lr1 + 1, lr2)
        for c in range(lc1 + 1, lc2)
    }
    right_interior = {
        (r, c)
        for r in range(rr1 + 1, rr2)
        for c in range(rc1 + 1, rc2)
    }
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r == 0 or (r, c) in frame_cells:
                continue
            if (r, c) in left_interior:
                if value not in (0, 2):
                    errors.append("left frame interior may contain only 0 and 2")
                    break
            elif (r, c) in right_interior:
                if value not in (0, 3):
                    errors.append("right frame interior may contain only 0 and 3")
                    break
            elif value != 0:
                errors.append("non-background cell appears outside keys, frames, or mask interiors")
                break
        if errors and errors[-1].startswith(("left frame", "right frame", "non-background")):
            break
    if not info["mask_a"]:
        errors.append("left color-2 mask is empty")
    if not info["mask_b"]:
        errors.append("right color-3 mask is empty")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from pixels rather than draw metadata."""
    problems = self_check(grid)
    if problems:
        raise ValueError("; ".join(problems))
    info = _parse(grid)
    return {
        "interior_h": info["interior_h"],
        "interior_w": info["interior_w"],
        "n_keys": len(info["keys"]),
        "gap": info["gap"],
    }


def strict_canonical_like(grid):
    problems = self_check(grid)
    if problems:
        return problems
    info = _parse(grid)
    reasons = []
    if info["interior_h"] != 5:
        reasons.append("canonical interior height is 5")
    if info["interior_w"] not in (4, 5, 6):
        reasons.append("canonical interior width is 4, 5, or 6")
    if info["gap"] != 1:
        reasons.append("canonical frame gap is 1")
    if len(info["keys"]) not in (2, 3) or any(key not in (2, 3, 4) for key in info["keys"]):
        reasons.append("canonical examples use two or three keys drawn from 2, 3, and 4")
    return reasons


def _cells_for_key(a: set[tuple[int, int]], b: set[tuple[int, int]], key: int):
    if key == 2:
        return a | b
    if key == 3:
        return a & b
    return a ^ b


def _gallery(grid, key_for_panel: Callable[[int, int], int | None] | None = None):
    info = _parse(grid)
    ih, iw = info["interior_h"], info["interior_w"]
    keys = info["keys"]
    output = full_grid(ih, len(keys) * iw + len(keys) - 1, 0)
    for index, actual_key in enumerate(keys):
        key = actual_key if key_for_panel is None else key_for_panel(index, actual_key)
        cells = set() if key is None else _cells_for_key(info["mask_a"], info["mask_b"], key)
        for r, c in cells:
            output[r][index * (iw + 1) + c] = 8
    return output


def _all_or(grid):
    return _gallery(grid, lambda _index, _key: 2)


def _all_and(grid):
    return _gallery(grid, lambda _index, _key: 3)


def _all_xor(grid):
    return _gallery(grid, lambda _index, _key: 4)


def _fixed_order(grid):
    cycle = (2, 3, 4)
    return _gallery(grid, lambda index, _key: cycle[index % len(cycle)])


def _key4_only_xor(grid):
    return _gallery(grid, lambda _index, key: key if key in (2, 3, 4) else None)


def _keys(grid) -> list[int]:
    return _parse(grid)["keys"]


def _has_or(grid) -> bool:
    return 2 in _keys(grid)


def _has_and(grid) -> bool:
    return 3 in _keys(grid)


def _has_xor(grid) -> bool:
    return any(key not in (2, 3) for key in _keys(grid))


def _has_non4_xor(grid) -> bool:
    return any(key not in (2, 3, 4) for key in _keys(grid))


def _has_key_order_counterexample(grid) -> bool:
    keys = _keys(grid)
    fixed = (2, 3, 4)
    return any(_operation_code(key) != fixed[index % 3] for index, key in enumerate(keys))


SEMANTIC_WITNESSES = {
    "or_branch": _has_or,
    "and_branch": _has_and,
    "xor_branch": _has_xor,
    "key_order": _has_key_order_counterexample,
    "non4_xor_key": _has_non4_xor,
}
SEMANTIC_RIVALS = {
    "all_or": _all_or,
    "all_and": _all_and,
    "all_xor": _all_xor,
    "fixed_order": _fixed_order,
    "key4_only_xor": _key4_only_xor,
}
WITNESS_RIVALS = {
    "or_branch": ["all_and", "all_xor"],
    "and_branch": ["all_or", "all_xor"],
    "xor_branch": ["all_or", "all_and"],
    "key_order": ["fixed_order"],
    "non4_xor_key": ["key4_only_xor"],
}
CANONICAL_SHORTCUTS = {"key4_only_xor": _key4_only_xor}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report declared rivals that fit every demo but change the held-out answer."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons
