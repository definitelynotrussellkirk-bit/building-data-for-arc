"""Opt-in direct versus running-parity encoding for local-frame occupancy.

The canonical ``direct`` setting is byte-for-byte the selected authoritative
Racket rule.  Both settings share the same inputs.  The alternate setting first
recovers the four local occupancy bits and then emits their left-to-right running
XOR, so each later output bit consumes the preceding intermediate parity.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Iterable

TASK_ID = "2fb0197be694"
ENCODINGS = ("direct", "running_parity")
CANON = ((2, 0), (0, 2), (1, 1), (2, 2))
FRAME_ORIENTATIONS = (
    ((-1, 0), (0, 1)),
    ((-1, 0), (0, -1)),
    ((1, 0), (0, 1)),
    ((1, 0), (0, -1)),
    ((0, 1), (-1, 0)),
    ((0, 1), (1, 0)),
    ((0, -1), (-1, 0)),
    ((0, -1), (1, 0)),
)
_REQUIRED = ((0, 0), (1, 0), (0, 1), *CANON)
DEMO_MASKS = (1, 6, 12, 5, 10, 15)
QUERY_MASKS = (9, 3, 14, 11)
DEMO_PROFILES = (
    (9, 9, "clean", "center"),
    (12, 10, "sparse", "free"),
    (16, 16, "bands", "free"),
    (7, 14, "components", "boundary"),
    (20, 11, "sparse", "free"),
    (6, 6, "clean", "boundary"),
)
QUERY_PROFILES = (
    (11, 17, "components", "free"),
    (21, 29, "bands", "free"),
    (30, 30, "dense", "free"),
    (6, 16, "sparse", "boundary"),
)
_DISTRACTOR_COLORS = (1, 5, 6, 7, 9)

_HERE = Path(__file__).resolve().parent
_CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
_CANONICAL_TAIL = (
    "(let* ((sf (first (find-frames g (list 2 3 4)))) "
    "(uvs (canonical-uvs (point-uvs (extract-local-points g sf (list 8) 4))))) "
    "(grid-from-fn 1 (length canon-e7) (lambda (r c) "
    "(if (member? (list-ref canon-e7 c) uvs) 8 0))))))"
)
_RUNNING_PARITY_TAIL = (
    "(let* ((sf (first (find-frames g (list 2 3 4)))) "
    "(uvs (canonical-uvs (point-uvs (extract-local-points g sf (list 8) 4)))) "
    "(b0 (if (member? (list-ref canon-e7 0) uvs) 1 0)) "
    "(b1 (if (member? (list-ref canon-e7 1) uvs) 1 0)) "
    "(b2 (if (member? (list-ref canon-e7 2) uvs) 1 0)) "
    "(b3 (if (member? (list-ref canon-e7 3) uvs) 1 0)) "
    "(p0 b0) "
    "(p1 (remainder (+ p0 b1) 2)) "
    "(p2 (remainder (+ p1 b2) 2)) "
    "(p3 (remainder (+ p2 b3) 2)) "
    "(encoded (list p0 p1 p2 p3))) "
    "(grid-from-fn 1 (length canon-e7) (lambda (r c) "
    "(if (= (list-ref encoded c) 1) 8 0))))))"
)
if _CANONICAL_PROGRAM.count(_CANONICAL_TAIL) != 1:
    raise RuntimeError("canonical authority tail changed; alternate rule must be reviewed")
_RUNNING_PARITY_PROGRAM = _CANONICAL_PROGRAM.replace(
    _CANONICAL_TAIL, _RUNNING_PARITY_TAIL
)


def _validate_settings(settings: dict) -> str:
    if not isinstance(settings, dict) or set(settings) != {"encoding"}:
        raise ValueError("settings must contain exactly the encoding key")
    encoding = settings["encoding"]
    if type(encoding) is not str or encoding not in ENCODINGS:
        raise ValueError(f"encoding must be one of {ENCODINGS}")
    return encoding


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict) -> str:
    encoding = _validate_settings(settings)
    return _CANONICAL_PROGRAM if encoding == "direct" else _RUNNING_PARITY_PROGRAM


def _rng(seed: int, role: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:running-parity-v1:{seed}:{role}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _gpos(origin, vx, vy, u, v):
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _fitting_origins(height: int, width: int, vx, vy):
    result = []
    for row in range(height):
        for col in range(width):
            origin = (row, col)
            cells = [_gpos(origin, vx, vy, u, v) for u, v in _REQUIRED]
            if all(0 <= r < height and 0 <= c < width for r, c in cells):
                result.append(origin)
    if not result:
        raise ValueError(f"no fitting frame for {height}x{width} and {(vx, vy)}")
    return result


def _choose_origin(height: int, width: int, vx, vy, mode: str, rng: random.Random):
    origins = _fitting_origins(height, width, vx, vy)
    if mode == "center":
        return min(
            origins,
            key=lambda p: (
                abs(2 * p[0] - (height - 1)) + abs(2 * p[1] - (width - 1)),
                p,
            ),
        )
    if mode == "boundary":
        def score(origin):
            cells = [_gpos(origin, vx, vy, u, v) for u, v in _REQUIRED]
            contacts = sum(
                r in {0, height - 1} or c in {0, width - 1}
                for r, c in cells
            )
            return contacts
        best = max(map(score, origins))
        options = [origin for origin in origins if score(origin) == best]
        return options[rng.randrange(len(options))]
    if mode != "free":
        raise ValueError(f"unknown origin mode {mode!r}")
    return origins[rng.randrange(len(origins))]


def _paint_rect(grid, top, left, height, width, color):
    for row in range(top, min(len(grid), top + height)):
        for col in range(left, min(len(grid[0]), left + width)):
            grid[row][col] = color


def _paint_distractors(grid, rng: random.Random, profile: str) -> None:
    height, width = len(grid), len(grid[0])
    if profile == "clean":
        for _ in range(max(2, (height * width) // 28)):
            row, col = rng.randrange(height), rng.randrange(width)
            grid[row][col] = rng.choice(_DISTRACTOR_COLORS)
        return
    if profile == "sparse":
        for index in range(max(4, (height * width) // 35)):
            rh = rng.randint(1, min(3, height))
            rw = rng.randint(1, min(4, width))
            top = rng.randrange(height - rh + 1)
            left = rng.randrange(width - rw + 1)
            _paint_rect(grid, top, left, rh, rw, _DISTRACTOR_COLORS[index % 5])
        return
    if profile == "bands":
        for row in range(0, height, 4):
            color = _DISTRACTOR_COLORS[(row // 4) % 5]
            for col in range(width):
                if (col + row) % 3 != 1:
                    grid[row][col] = color
        for col in range(2, width, 6):
            color = _DISTRACTOR_COLORS[(col // 2) % 5]
            for row in range(height):
                if (row + col) % 4 == 0:
                    grid[row][col] = color
        return
    if profile == "components":
        count = max(6, (height * width) // 45)
        for index in range(count):
            rh = rng.randint(1, min(4, height))
            rw = rng.randint(1, min(5, width))
            top = rng.randrange(height - rh + 1)
            left = rng.randrange(width - rw + 1)
            _paint_rect(grid, top, left, rh, rw, _DISTRACTOR_COLORS[index % 5])
        return
    if profile == "dense":
        salt = rng.randrange(1000)
        for row in range(height):
            for col in range(width):
                edge = row in {0, height - 1} or col in {0, width - 1}
                active = edge or ((row * 7 + col * 11 + salt) % 10 < 4)
                if active:
                    grid[row][col] = _DISTRACTOR_COLORS[
                        (row * 3 + col * 2 + salt) % len(_DISTRACTOR_COLORS)
                    ]
        return
    raise ValueError(f"unknown distractor profile {profile!r}")


def _scene(seed: int, role: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if role == "demo" else QUERY_PROFILES
    masks = DEMO_MASKS if role == "demo" else QUERY_MASKS
    height, width, clutter, origin_mode = profiles[index]
    mask = masks[index]
    rng = _rng(seed, role, index)
    vx, vy = FRAME_ORIENTATIONS[rng.randrange(len(FRAME_ORIENTATIONS))]
    origin = _choose_origin(height, width, vx, vy, origin_mode, rng)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    _paint_distractors(grid, rng, clutter)

    # Paint the single authoritative frame after clutter so the cue and all
    # queried local cells remain exact even in the dense 30x30 stress scene.
    for (u, v), color in (((0, 0), 2), ((1, 0), 3), ((0, 1), 4)):
        row, col = _gpos(origin, vx, vy, u, v)
        grid[row][col] = color
    for bit, (u, v) in enumerate(CANON):
        row, col = _gpos(origin, vx, vy, u, v)
        grid[row][col] = 8 if mask & (1 << bit) else 0
    return grid


def _single_position(grid: list[list[int]], color: int):
    found = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if len(found) != 1:
        raise ValueError(f"expected one color-{color} marker, got {len(found)}")
    return found[0]


def occupancy_bits(grid: list[list[int]]) -> tuple[int, int, int, int]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
    ):
        raise ValueError("grid must be nonempty and rectangular")
    origin = _single_position(grid, 2)
    marker_x = _single_position(grid, 3)
    marker_y = _single_position(grid, 4)
    vx = (marker_x[0] - origin[0], marker_x[1] - origin[1])
    vy = (marker_y[0] - origin[0], marker_y[1] - origin[1])
    if (vx, vy) not in FRAME_ORIENTATIONS:
        raise ValueError(f"invalid directed orthogonal frame {(vx, vy)}")
    bits = []
    for u, v in CANON:
        row, col = _gpos(origin, vx, vy, u, v)
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise ValueError("canonical local offset falls outside the grid")
        bits.append(int(grid[row][col] == 8))
    return tuple(bits)


def encode_bits(bits: Iterable[int], encoding: str) -> tuple[int, int, int, int]:
    values = tuple(bits)
    if len(values) != 4 or any(type(bit) is not int or bit not in {0, 1} for bit in values):
        raise ValueError("bits must contain four exact binary integers")
    if encoding == "direct":
        return values
    if encoding != "running_parity":
        raise ValueError(f"unknown encoding {encoding!r}")
    result = []
    state = 0
    for bit in values:
        state ^= bit
        result.append(state)
    return tuple(result)


def transform(grid: list[list[int]], encoding: str) -> list[list[int]]:
    return [[8 if bit else 0 for bit in encode_bits(occupancy_bits(grid), encoding)]]


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    encoding = _validate_settings(settings)
    exact_program = program(settings)

    train_inputs = [_scene(seed, "demo", index) for index in range(demos)]
    test_inputs = [_scene(seed, "query", index) for index in range(queries)]
    train = [
        {"input": grid, "output": transform(grid, encoding)}
        for grid in train_inputs
    ]
    test = [
        {"input": grid, "output": transform(grid, encoding)}
        for grid in test_inputs
    ]

    serialized = {
        repr(grid) for grid in train_inputs + test_inputs
    }
    if len(serialized) != demos + queries:
        raise RuntimeError("constructed episode contains duplicate inputs")
    survivors = [
        candidate
        for candidate in ENCODINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    if survivors != [encoding]:
        raise RuntimeError(
            f"constructed demonstrations do not identify {encoding}: {survivors}"
        )
    return {"train": train, "test": test, "program_solution": exact_program}
