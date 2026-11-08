"""Proposed parametric extension for ARC task 1a8932958b14.

The canonical task moves the payload by exactly one red-to-green marker vector.
This isolated prototype adds one episode-level parameter, ``vector_multiplier``:
move by either one or two copies of that vector.  The parameter is selected once
per episode and shared by every demonstration and query.  It does not alter the
selected production generator or its canonical Racket authority.
"""
from __future__ import annotations

import copy
import hashlib
import random
from typing import Any


TASK_ID = "1a8932958b14"
PROTOTYPE_VERSION = "1.0.0"
PARAMETERS = {
    "vector_multiplier": {
        "allowed": (1, 2),
        "default": 1,
        "meaning": "multiply the red-to-green displacement before moving the payload",
        "input_constraint": (
            "Every payload cell shifted by vector_multiplier times the red-to-green "
            "vector must stay in bounds."
        ),
    }
}

# Compact connected payloads.  Placement and color assignment vary by pair.
_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
)
_VECTORS = ((1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (2, 0))
_COLORS = (1, 4, 5, 6, 7, 8, 9)


def _require_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    return seed


def _require_multiplier(value: Any) -> int:
    allowed = PARAMETERS["vector_multiplier"]["allowed"]
    if type(value) is not int or value not in allowed:
        raise ValueError(f"vector_multiplier must be one of {allowed}")
    return value


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose the hidden rule once from a stable seed-derived digest."""
    seed = _require_seed(seed)
    token = f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}".encode("utf-8")
    selected = PARAMETERS["vector_multiplier"]["allowed"][
        hashlib.sha256(token).digest()[0] % 2
    ]
    return {"vector_multiplier": selected}


def racket_program(vector_multiplier: int) -> str:
    """Materialize the exact Racket rule for one parameter setting."""
    m = _require_multiplier(vector_multiplier)
    return f"""(rule!
  ;; Proposed variant: move by {m} copy/copies of the red-to-green vector.
  (let* ((src (first (find-color g 2)))
         (dst (first (find-color g 3)))
         (dr (* {m} (- (first dst) (first src))))
         (dc (* {m} (- (second dst) (second src)))))
    (foldl (lambda (cell out)
             (let* ((r (first cell))
                    (c (second cell))
                    (v (third cell))
                    (nr (+ r dr))
                    (nc (+ c dc)))
               (if (and (not (= v 0))
                        (not (= v 2))
                        (not (= v 3))
                        (in-bounds? nr nc (rows g) (cols g)))
                   (set-cell out nr nc v)
                   out)))
           (empty-grid (rows g) (cols g) 0)
           (grid-cells g))))"""


def _analyze(grid: Any) -> tuple[int, int, tuple[int, int], tuple[int, int], list[tuple[int, int, int]]]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid values must be integer ARC colors 0..9")
    h, w = len(grid), width
    red = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    green = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    payload = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 2, 3)
    ]
    if len(red) != 1 or len(green) != 1 or not payload:
        raise ValueError("expected one red marker, one green marker, and a payload")
    return h, w, red[0], green[0], payload


def apply_python(grid: list[list[int]], vector_multiplier: int) -> list[list[int]]:
    """Independent mirror used only for authoring checks; Racket remains evidence authority."""
    m = _require_multiplier(vector_multiplier)
    h, w, source, destination, payload = _analyze(grid)
    dr = m * (destination[0] - source[0])
    dc = m * (destination[1] - source[1])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for row, col, value in payload:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < h and 0 <= nc < w):
            raise ValueError(
                "input violates the selected vector_multiplier in-bounds constraint"
            )
        out[nr][nc] = value
    return out


def _stable_rng(seed: int, pair_index: int) -> random.Random:
    token = f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:pair:{pair_index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(token).digest()[:16], "big"))


def _candidate_tops(h: int, shape: tuple[tuple[int, int], ...], dr: int) -> list[int]:
    sh = max(r for r, _ in shape) + 1
    result = []
    for top in range(h - sh + 1):
        if all(0 <= top + r + m * dr < h for r, _ in shape for m in (1, 2)):
            result.append(top)
    return result


def _candidate_lefts(w: int, shape: tuple[tuple[int, int], ...], dc: int) -> list[int]:
    sw = max(c for _, c in shape) + 1
    result = []
    for left in range(w - sw + 1):
        if all(0 <= left + c + m * dc < w for _, c in shape for m in (1, 2)):
            result.append(left)
    return result


def _build_input(seed: int, pair_index: int) -> list[list[int]]:
    rng = _stable_rng(seed, pair_index)
    h = 11 + rng.randrange(4)
    w = 11 + rng.randrange(4)
    shape = _SHAPES[(pair_index + rng.randrange(len(_SHAPES))) % len(_SHAPES)]
    dr, dc = _VECTORS[(pair_index + rng.randrange(len(_VECTORS))) % len(_VECTORS)]

    tops = _candidate_tops(h, shape, dr)
    lefts = _candidate_lefts(w, shape, dc)
    if not tops or not lefts:
        raise RuntimeError("prototype scene catalog could not satisfy both parameter settings")
    top = rng.choice(tops)
    left = rng.choice(lefts)
    payload_cells = {(top + r, left + c) for r, c in shape}
    shifted_cells = {
        (top + r + m * dr, left + c + m * dc)
        for r, c in shape
        for m in (1, 2)
    }

    marker_options = []
    blocked = payload_cells | shifted_cells
    for sr in range(h):
        for sc in range(w):
            destination = (sr + dr, sc + dc)
            if not (0 <= destination[0] < h and 0 <= destination[1] < w):
                continue
            if (sr, sc) in blocked or destination in blocked or destination == (sr, sc):
                continue
            marker_options.append(((sr, sc), destination))
    if not marker_options:
        raise RuntimeError("prototype could not place nonoverlapping markers")
    source, destination = rng.choice(marker_options)

    palette_size = 2 + (pair_index % 2)
    palette = rng.sample(_COLORS, palette_size)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for offset, (r, c) in enumerate(shape):
        grid[top + r][left + c] = palette[offset % palette_size]
    grid[source[0]][source[1]] = 2
    grid[destination[0]][destination[1]] = 3
    return grid


def generate_episode(
    seed: int,
    *,
    vector_multiplier: int | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Build one complete episode with a single shared hidden parameter."""
    seed = _require_seed(seed)
    if type(n_train) is not int or n_train < 2:
        raise ValueError("n_train must be an integer >= 2")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be an integer >= 1")

    # One and only one episode-level selection.  Explicit settings are for
    # authoring/evidence; the normal path is deterministic seed selection.
    selected = (
        choose_parameters(seed)["vector_multiplier"]
        if vector_multiplier is None
        else _require_multiplier(vector_multiplier)
    )
    pairs = []
    for pair_index in range(n_train + n_test):
        inp = _build_input(seed, pair_index)
        pairs.append({"input": inp, "output": apply_python(inp, selected)})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": racket_program(selected),
        "meta": {
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            "vector_multiplier": selected,
            "parameter_draw_count": 1,
            "parameter_source": "seed" if vector_multiplier is None else "explicit_evidence_setting",
            "input_constraint": PARAMETERS["vector_multiplier"]["input_constraint"],
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demonstrations plus masked queries, omitting hidden rule metadata."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }
