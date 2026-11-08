"""Matched-input normalized-panel Boolean family for task 0261c073ae3f."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "0261c073ae3f"
BOOLEAN_OPS = ("xor", "or")
DEFAULT_BOOLEAN_OP = "xor"
HERE = Path(__file__).resolve().parent
PROGRAM_PATHS = {
    "xor": HERE / "canonical.rkt",
    "or": HERE / "or.rkt",
}
CANDIDATE_RULES = (
    "xor",
    "or",
    "and",
    "left_only",
    "right_only",
    "xnor",
    "raw_xor",
    "raw_or",
)

# Full bank is constructed before any count slicing.
# gh, gw, separator, pair-name, mixed-colors
_TRAIN_PROFILES = (
    (8, 13, 5, "lesson_l", True),
    (9, 15, 7, "lesson_t", False),
    (12, 18, 8, "dense_5x4", True),
    (15, 20, 9, "dense_7x6", False),
    (20, 24, 11, "dense_11x9", True),
    (27, 28, 13, "dense_20x12", True),
)
_TEST_PROFILES = (
    (10, 14, 6, "dense_4x4", True),
    (16, 19, 8, "dense_9x7", False),
    (25, 27, 12, "dense_18x11", True),
    (30, 30, 14, "dense_26x13", True),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_boolean_op(value: Any) -> str:
    if type(value) is not str or value not in BOOLEAN_OPS:
        raise ValueError(f"boolean_op must be one of {BOOLEAN_OPS}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"boolean_op"}:
        raise ValueError("settings must contain exactly boolean_op")
    return validate_boolean_op(settings["boolean_op"])


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)


def program_for(boolean_op: str) -> str:
    return PROGRAM_PATHS[validate_boolean_op(boolean_op)].read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors")
    return [row[:] for row in grid]


def _separator(grid: list[list[int]]) -> int:
    g = _validate_grid(grid)
    full = [c for c in range(len(g[0])) if all(row[c] == 5 for row in g)]
    if len(full) != 1 or full[0] in (0, len(g[0]) - 1):
        raise ValueError("grid must contain exactly one interior full-height color-5 separator")
    return full[0]


def _normalize_panel(panel: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [
        [1 if panel[r][c] != 0 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def normalized_masks(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    g = _validate_grid(grid)
    sep = _separator(g)
    left = [row[:sep] for row in g]
    right = [row[sep + 1 :] for row in g]
    return _normalize_panel(left), _normalize_panel(right)


def _combine(a: list[list[int]], b: list[list[int]], op: str) -> list[list[int]]:
    h = max(len(a), len(b))
    w = max(len(a[0]), len(b[0]))
    output: list[list[int]] = []
    for r in range(h):
        row: list[int] = []
        for c in range(w):
            av = int(r < len(a) and c < len(a[0]) and a[r][c] != 0)
            bv = int(r < len(b) and c < len(b[0]) and b[r][c] != 0)
            if op == "xor":
                on = av != bv
            elif op == "or":
                on = bool(av or bv)
            elif op == "and":
                on = bool(av and bv)
            elif op == "left_only":
                on = bool(av)
            elif op == "right_only":
                on = bool(bv)
            elif op == "xnor":
                on = av == bv
            else:
                raise ValueError(f"unknown Boolean operation {op}")
            row.append(7 if on else 0)
        output.append(row)
    return output


def solve(grid: list[list[int]], boolean_op: str) -> list[list[int]]:
    boolean_op = validate_boolean_op(boolean_op)
    left, right = normalized_masks(grid)
    return _combine(left, right, boolean_op)


def _raw_masks(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    g = _validate_grid(grid)
    sep = _separator(g)
    left = [[1 if value != 0 else 0 for value in row[:sep]] for row in g]
    right = [[1 if value != 0 else 0 for value in row[sep + 1 :]] for row in g]
    return left, right


def solve_candidate(grid: list[list[int]], name: str) -> list[list[int]]:
    if name in {"xor", "or"}:
        return solve(grid, name)
    if name in {"and", "left_only", "right_only", "xnor"}:
        left, right = normalized_masks(grid)
        return _combine(left, right, name)
    if name in {"raw_xor", "raw_or"}:
        left, right = _raw_masks(grid)
        return _combine(left, right, name.removeprefix("raw_"))
    raise ValueError(f"unknown candidate {name}")


def teaching_survivors(train: list[dict[str, list[list[int]]]]) -> list[str]:
    return [
        name
        for name in CANDIDATE_RULES
        if all(solve_candidate(pair["input"], name) == pair["output"] for pair in train)
    ]


def _dense_pair(h: int, w: int, variant: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    border = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    }
    left = border | {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (r + 2 * c + variant) % 3 != 2
    }
    right = border | {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (2 * r + c + variant) % 4 <= 1
    }
    # Pin one exclusive interior cell to each operand.  Formulaic densities can
    # otherwise make one mask a subset of the other on small canvases, which
    # weakens OR/one-sided teaching even though the large cases remain rich.
    left_only = (1, 1)
    right_only = (h - 2, w - 2)
    left.add(left_only)
    right.discard(left_only)
    right.add(right_only)
    left.discard(right_only)
    return left, right


def _pair(name: str) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    if name == "lesson_l":
        return (
            {(0, 0), (1, 0), (2, 0), (2, 1)},
            {(0, 0), (0, 1), (1, 1), (2, 1)},
        )
    if name == "lesson_t":
        return (
            {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)},
            {(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)},
        )
    if not name.startswith("dense_") or "x" not in name:
        raise ValueError(f"unknown mask pair {name}")
    dims = name.removeprefix("dense_").split("x")
    if len(dims) != 2:
        raise ValueError(f"invalid dense pair {name}")
    h, w = map(int, dims)
    return _dense_pair(h, w, h * 31 + w)


def _transform_common(
    pair: tuple[set[tuple[int, int]], set[tuple[int, int]]], rng: random.Random
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    left, right = (set(pair[0]), set(pair[1]))
    h = max(r for cells in (left, right) for r, _ in cells) + 1
    w = max(c for cells in (left, right) for _, c in cells) + 1
    if rng.random() < 0.5:
        left = {(h - 1 - r, c) for r, c in left}
        right = {(h - 1 - r, c) for r, c in right}
    if rng.random() < 0.5:
        left = {(r, w - 1 - c) for r, c in left}
        right = {(r, w - 1 - c) for r, c in right}
    return left, right


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _mask_shape(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = set(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _choose_distinct_offsets(
    rng: random.Random, gh: int, left_w: int, right_w: int, shape: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int]]:
    mh, mw = shape
    left_options = [(r, c) for r in range(gh - mh + 1) for c in range(left_w - mw + 1)]
    right_options = [(r, c) for r in range(gh - mh + 1) for c in range(right_w - mw + 1)]
    if not left_options or not right_options:
        raise ValueError("mask does not fit profile")
    left = rng.choice(left_options)
    right_candidates = [item for item in right_options if item != left]
    right = rng.choice(right_candidates or right_options)
    return left, right


def _paint_mask(
    grid: list[list[int]],
    cells: set[tuple[int, int]],
    offset: tuple[int, int],
    col0: int,
    colors: tuple[int, int],
    mixed: bool,
) -> None:
    r0, c0 = offset
    for r, c in cells:
        color = colors[0]
        if mixed and (r + 2 * c) % 5 == 0:
            color = colors[1]
        grid[r0 + r][col0 + c0 + c] = color


def _scene(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, int, str, bool],
) -> list[list[int]]:
    gh, gw, sep, pair_name, mixed = profile
    rng = _rng(seed, split, index)
    if not 0 < sep < gw - 1:
        raise ValueError("separator must leave two panels")
    left_cells, right_cells = _transform_common(_pair(pair_name), rng)
    shape = _mask_shape(left_cells | right_cells)
    left_w, right_w = sep, gw - sep - 1
    left_offset, right_offset = _choose_distinct_offsets(rng, gh, left_w, right_w, shape)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
    grid = [[0 for _ in range(gw)] for _ in range(gh)]
    for r in range(gh):
        grid[r][sep] = 5
    _paint_mask(grid, left_cells, left_offset, 0, (palette[0], palette[1]), mixed)
    _paint_mask(grid, right_cells, right_offset, sep + 1, (palette[2], palette[3]), mixed and index % 2 == 1)
    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid scene: {errors}")
    return grid


def self_check(grid: Any) -> list[str]:
    try:
        g = _validate_grid(grid)
        sep = _separator(g)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if any(row[c] == 5 for row in g for c in range(len(row)) if c != sep):
        errors.append("color 5 must be reserved for the separator")
    left, right = normalized_masks(g)
    left_set = {(r, c) for r, row in enumerate(left) for c, value in enumerate(row) if value}
    right_set = {(r, c) for r, row in enumerate(right) for c, value in enumerate(row) if value}
    if not left_set or not right_set:
        errors.append("both panels must contain an object")
    else:
        if left_set == right_set:
            errors.append("normalized masks must differ")
        if not left_set & right_set:
            errors.append("normalized masks need overlap to distinguish xor from or")
        if not left_set - right_set or not right_set - left_set:
            errors.append("each normalized mask needs exclusive cells")
    return errors


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    train = [_scene(seed, "train", index, profile) for index, profile in enumerate(_TRAIN_PROFILES)]
    test = [_scene(seed, "test", index, profile) for index, profile in enumerate(_TEST_PROFILES)]
    frozen = {tuple(tuple(row) for row in grid) for grid in train + test}
    if len(frozen) != 10:
        raise RuntimeError("constructed duplicate inputs")
    return {"train": train, "test": test}


def generate_episode(
    seed: int, boolean_op: str, demos: int = 2, queries: int = 4
) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    boolean_op = validate_boolean_op(boolean_op)
    bank = episode_inputs(seed)
    train = [
        {"input": grid, "output": solve(grid, boolean_op)}
        for grid in bank["train"][:demos]
    ]
    test = [
        {"input": grid, "output": solve(grid, boolean_op)}
        for grid in bank["test"][:queries]
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(boolean_op),
    }


def retranslate_and_recolor(grid: list[list[int]]) -> list[list[int]]:
    """Create a visibly different input with the same normalized binary masks."""
    g = _validate_grid(grid)
    sep = _separator(g)
    left, right = normalized_masks(g)
    left_set = {(r, c) for r, row in enumerate(left) for c, value in enumerate(row) if value}
    right_set = {(r, c) for r, row in enumerate(right) for c, value in enumerate(row) if value}
    lh, lw = len(left), len(left[0])
    rh, rw = len(right), len(right[0])
    output = [[0 for _ in row] for row in g]
    for r in range(len(g)):
        output[r][sep] = 5
    existing_left = {value for row in g for value in row[:sep] if value not in (0, 5)}
    existing_right = {value for row in g for value in row[sep + 1 :] if value not in (0, 5)}
    left_color = next(value for value in (9, 8, 6, 4, 3, 2, 1, 7) if value not in existing_left)
    right_color = next(value for value in (1, 2, 3, 4, 6, 8, 9, 7) if value not in existing_right and value != left_color)
    left_r0, left_c0 = len(g) - lh, sep - lw
    right_r0, right_c0 = 0, 0
    for r, c in left_set:
        output[left_r0 + r][left_c0 + c] = left_color
    for r, c in right_set:
        output[right_r0 + r][sep + 1 + right_c0 + c] = right_color
    if output == g:
        raise RuntimeError("retranslation failed to alter the input")
    if self_check(output):
        raise RuntimeError(f"retranslated grid invalid: {self_check(output)}")
    return output
