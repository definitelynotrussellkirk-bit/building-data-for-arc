"""Deterministic reflection-policy episodes for ARC task b8aea529acfd.

The task's canonical program remains the exact default.  Nearby episode-fixed
policies vary only which reflection follows the crop.  The conditional
policies deliberately select their reflection from the *cropped body's*
aspect ratio so the family contains a genuine crop -> measure -> transform
causal chain.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from typing import Any, Iterable

TASK_ID = "b8aea529acfd"
SCHEMA = "b8aea529acfd-reflection-policy-parametric-v1"
POLICIES = ("left_right", "top_bottom", "long_dimension", "short_dimension")
DEFAULT_POLICY = "left_right"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1

CANONICAL_PROGRAM = "(rule! (lambda (g) (flip-lr (crop-to-content g))))"
PROGRAMS = {
    "left_right": CANONICAL_PROGRAM,
    "top_bottom": "(rule! (lambda (g) (flip-ud (crop-to-content g))))",
    "long_dimension": (
        "(rule! (lambda (g) (let ((body (crop-to-content g))) "
        "(if (>= (cols body) (rows body)) (flip-lr body) (flip-ud body))))))"
    ),
    "short_dimension": (
        "(rule! (lambda (g) (let ((body (crop-to-content g))) "
        "(if (>= (cols body) (rows body)) (flip-ud body) (flip-lr body))))))"
    ),
}

# (canvas rows, canvas cols, body rows, body cols).  The first two are
# intentionally aspect-mismatched: a wide body lives on a tall canvas and a
# tall body on a wide canvas.  This prevents a canvas-aspect shortcut from
# fitting all demonstrations.
_DEMO_PROFILES = (
    (16, 12, 5, 9),
    (12, 16, 9, 5),
    (15, 19, 7, 11),
    (19, 15, 11, 7),
    (24, 18, 9, 15),
    (18, 24, 15, 9),
)
_QUERY_PROFILES = (
    (30, 30, 15, 24),
    (30, 30, 24, 15),
    (22, 29, 11, 21),
    (29, 22, 21, 11),
)
_PALETTES = (
    (4, 1),
    (8, 2),
    (6, 3),
    (9, 5),
    (7, 1),
    (3, 8),
    (2, 5),
    (1, 9),
    (5, 7),
    (8, 4),
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _policy(value: Any) -> str:
    if not isinstance(value, str) or value not in POLICIES:
        raise ValueError(f"reflection_policy must be one of {POLICIES}")
    return value


def _rectangular_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    width = len(grid[0])
    result: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        copied: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise ValueError("grid cells must be literal integers 0..9")
            copied.append(value)
        result.append(copied)
    return result


def crop(grid: Any) -> list[list[int]]:
    """Crop to the bounding rectangle of every nonzero cell."""
    checked = _rectangular_grid(grid)
    cells = [
        (row_index, col_index)
        for row_index, row in enumerate(checked)
        for col_index, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("cannot crop a grid without foreground")
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [row[col0 : col1 + 1] for row in checked[row0 : row1 + 1]]


def flip_lr(grid: Any) -> list[list[int]]:
    return [list(reversed(row)) for row in _rectangular_grid(grid)]


def flip_ud(grid: Any) -> list[list[int]]:
    return [list(row) for row in reversed(_rectangular_grid(grid))]


def analyze_input(grid: Any) -> dict[str, Any]:
    checked = _rectangular_grid(grid)
    body = crop(checked)
    body_rows = len(body)
    body_cols = len(body[0])
    if body_rows == body_cols:
        aspect = "square"
    elif body_cols > body_rows:
        aspect = "wide"
    else:
        aspect = "tall"
    return {
        "canvas_rows": len(checked),
        "canvas_cols": len(checked[0]),
        "crop_rows": body_rows,
        "crop_cols": body_cols,
        "aspect": aspect,
    }


def program_for(reflection_policy: Any) -> str:
    return PROGRAMS[_policy(reflection_policy)]


def apply_policy(grid: Any, reflection_policy: Any) -> list[list[int]]:
    policy = _policy(reflection_policy)
    body = crop(grid)
    if policy == "left_right":
        return flip_lr(body)
    if policy == "top_bottom":
        return flip_ud(body)
    wide = len(body[0]) >= len(body)
    use_lr = wide if policy == "long_dimension" else not wide
    return flip_lr(body) if use_lr else flip_ud(body)


def _rng(seed: int, slot: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:reflection-policy-v1:{seed}:{slot}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _frozen(grid: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _asymmetric_accent_cells(
    body_rows: int,
    body_cols: int,
    count: int,
    rng: random.Random,
) -> set[tuple[int, int]]:
    cells = [(row, col) for row in range(body_rows) for col in range(body_cols)]
    for _ in range(512):
        selected = set(rng.sample(cells, count))
        lr = {(row, body_cols - 1 - col) for row, col in selected}
        ud = {(body_rows - 1 - row, col) for row, col in selected}
        rot = {
            (body_rows - 1 - row, body_cols - 1 - col)
            for row, col in selected
        }
        # These inequalities make crop-only, LR, UD, and 180-degree outputs
        # observably distinct while preserving a strict majority color.
        if selected != lr and selected != ud and selected != rot and lr != ud:
            return selected
    raise RuntimeError("failed to draw an asymmetric minority motif")


def _build_input(
    seed: int,
    slot: int,
    profile: tuple[int, int, int, int],
) -> list[list[int]]:
    canvas_rows, canvas_cols, body_rows, body_cols = profile
    if body_rows + 2 > canvas_rows or body_cols + 2 > canvas_cols:
        raise RuntimeError("profile cannot retain one-cell padding")
    rng = _rng(seed, slot)
    majority, accent = _PALETTES[(seed + slot) % len(_PALETTES)]
    top = rng.randint(1, canvas_rows - body_rows - 1)
    left = rng.randint(1, canvas_cols - body_cols - 1)

    area = body_rows * body_cols
    accent_count = max(4, area // 5)
    accent_cells = _asymmetric_accent_cells(
        body_rows, body_cols, accent_count, rng
    )

    grid = [[0 for _ in range(canvas_cols)] for _ in range(canvas_rows)]
    for row in range(body_rows):
        for col in range(body_cols):
            grid[top + row][left + col] = majority
    for row, col in accent_cells:
        grid[top + row][left + col] = accent
    return grid


def episode_inputs(seed: Any, *, demos: Any = 3, queries: Any = 4) -> list[list[list[int]]]:
    seed = _literal_int("seed", seed, 0, MAX_SEED)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    profiles = _DEMO_PROFILES[:demos] + _QUERY_PROFILES[:queries]
    grids = [_build_input(seed, slot, profile) for slot, profile in enumerate(profiles)]
    if len({_frozen(grid) for grid in grids}) != len(grids):
        raise RuntimeError("internal input schedule produced a duplicate grid")
    return grids


def generate_episode(
    seed: Any,
    *,
    reflection_policy: Any = DEFAULT_POLICY,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    policy = _policy(reflection_policy)
    inputs = episode_inputs(seed, demos=demos, queries=queries)
    demo_count = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    query_count = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    pairs = [
        {"input": copy.deepcopy(grid), "output": apply_policy(grid, policy)}
        for grid in inputs
    ]
    return {
        "schema": SCHEMA,
        "status": "proposed",
        "task_id": TASK_ID,
        "seed": seed,
        "reflection_policy": policy,
        "train": pairs[:demo_count],
        "test": pairs[demo_count : demo_count + query_count],
        "program_solution": program_for(policy),
    }


def public_payload(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demonstrations and query inputs without private labels/settings."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def first_turn_payload(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the exact first-query view used for sequential evaluation."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--policy", choices=POLICIES, default=DEFAULT_POLICY)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument(
        "--public",
        action="store_true",
        help="omit the private policy, program, and all query outputs",
    )
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        reflection_policy=args.policy,
        demos=args.demos,
        queries=args.queries,
    )
    payload = public_payload(episode) if args.public else episode
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
