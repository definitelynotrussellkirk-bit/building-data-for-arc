"""Native parametric family for additive transpose, with a causal bridge stage."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "aa378df15340"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["copy_only", "copy_then_bridge"]}
DEFAULT = {"mode": "copy_only"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}

_CANONICAL_STRIPPED = CANONICAL.strip()
if not (_CANONICAL_STRIPPED.startswith("(rule!") and _CANONICAL_STRIPPED.endswith(")")):
    raise ValueError("canonical.rkt must contain one rule! expression")
_CANONICAL_BODY = _CANONICAL_STRIPPED[len("(rule!"):-1].strip()

ALTERNATIVE = f"""(rule!
  (let* ((mirrored {_CANONICAL_BODY})
         (n (rows mirrored)))
    (for*/fold ((out mirrored))
      ((r (in-range n))
       (c (in-range (+ r 1) n)))
      (let ((v (at mirrored r c)))
        (if (and (not (= v 0)) (= (at mirrored c r) v))
            (for/fold ((painted out))
              ((k (in-range (+ (- c r) 1))))
              (set-cell painted (+ r k) (- c k) v))
            out)))))"""

SKIP_A_PROGRAM = """(rule!
  (let* ((mirrored g)
         (n (rows mirrored)))
    (for*/fold ((out mirrored))
      ((r (in-range n))
       (c (in-range (+ r 1) n)))
      (let ((v (at mirrored r c)))
        (if (and (not (= v 0)) (= (at mirrored c r) v))
            (for/fold ((painted out))
              ((k (in-range (+ (- c r) 1))))
              (set-cell painted (+ r k) (- c k) v))
            out)))))"""


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if mode not in PARAMETERS["mode"] or type(mode) is not str:
        raise ValueError("mode must be copy_only or copy_then_bridge")
    return mode


def validate_grid(grid: Any) -> None:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    n = len(grid)
    if not 1 <= n <= 30 or len(grid[0]) != n:
        raise ValueError("grid must be square with side 1..30")
    if any(type(row) is not list or len(row) != n for row in grid):
        raise ValueError("grid must be square")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors 0..9")


def program(settings: Any) -> str:
    return CANONICAL if _mode(settings) == "copy_only" else ALTERNATIVE


def copy_only(grid: list[list[int]]) -> list[list[int]]:
    validate_grid(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                out[c][r] = value
    return out


def bridge_symmetric_pairs(intermediate: list[list[int]]) -> list[list[int]]:
    """Fill the anti-diagonal segment between each equal mirrored pair."""
    validate_grid(intermediate)
    out = deepcopy(intermediate)
    n = len(intermediate)
    for r in range(n):
        for c in range(r + 1, n):
            value = intermediate[r][c]
            if value != 0 and intermediate[c][r] == value:
                for k in range(c - r + 1):
                    out[r + k][c - k] = value
    return out


def copy_then_bridge(grid: list[list[int]]) -> list[list[int]]:
    return bridge_symmetric_pairs(copy_only(grid))


def _rng(seed: int, stream: str) -> random.Random:
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(size: int, count: int, rng: random.Random, *, boundary: bool = False, long: bool = False) -> list[list[int]]:
    _integer(size, 5, 30, "size")
    _integer(count, 3, 28, "count")
    grid = [[0] * size for _ in range(size)]

    forced: list[tuple[int, int]] = []
    if boundary:
        forced = [(0, size - 3), (size - 2, 0), (size - 1, 2), (3, size - 1)]
    used_orbits = {tuple(sorted(((r, c), (c, r)))) for r, c in forced}
    used_sums = {r + c for r, c in forced}

    candidates: list[tuple[int, int]] = []
    for r in range(size):
        for c in range(r + 2, size):
            orbit = tuple(sorted(((r, c), (c, r))))
            if orbit in used_orbits or r + c in used_sums:
                continue
            candidates.append((r, c))
    if long:
        candidates.sort(key=lambda rc: (-(rc[1] - rc[0]), rc[0] + rc[1], rc[0]))
        # Randomize within equal-distance buckets while preserving long spans first.
        grouped: dict[int, list[tuple[int, int]]] = {}
        for rc in candidates:
            grouped.setdefault(rc[1] - rc[0], []).append(rc)
        candidates = []
        for distance in sorted(grouped, reverse=True):
            bucket = grouped[distance]
            rng.shuffle(bucket)
            candidates.extend(bucket)
    else:
        rng.shuffle(candidates)

    selected = list(forced)
    # A distance-2/3 bridge adds only its midpoint cell(s), so a midpoint-only
    # rival can imitate it. Force one span of at least four in every scene.
    if not any(abs(c - r) >= 4 for r, c in selected):
        long_option = next((rc for rc in candidates if rc[1] - rc[0] >= 4), None)
        if long_option is None:
            raise ValueError("scene cannot support a distinguishing long bridge")
        candidates.remove(long_option)
        r, c = long_option
        selected.append((r, c) if rng.randrange(2) else (c, r))
    for r, c in candidates:
        if len(selected) >= count:
            break
        if r + c in {a + b for a, b in selected}:
            continue
        selected.append((r, c) if rng.randrange(2) else (c, r))
    if len(selected) != count:
        raise ValueError("could not construct requested distinct anti-diagonal orbits")

    # Guarantee both source orientations in ordinary scenes without changing orbits.
    if not any(r < c for r, c in selected):
        r, c = selected[0]
        selected[0] = (c, r)
    if not any(r > c for r, c in selected):
        r, c = selected[-1]
        selected[-1] = (c, r)

    palette = list(range(1, 10))
    rng.shuffle(palette)
    for index, (r, c) in enumerate(selected):
        grid[r][c] = palette[index % len(palette)]
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    specs_train = [(7, 4), (9, 5), (12, 7), (15, 9), (18, 12), (22, 14)]
    specs_test = [(6, 3), (11, 6), (24, 16), (30, 24)]
    train = [_scene(n, count, _rng(seed, f"train:{i}")) for i, (n, count) in enumerate(specs_train)]
    test = [
        _scene(n, count, _rng(seed, f"test:{i}"), boundary=(i == 3), long=(i == 3))
        for i, (n, count) in enumerate(specs_test)
    ]
    keys = [tuple(map(tuple, grid)) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return train, test


def generate(seed: int, settings: Any = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"mode": _rng(seed, "settings").choice(PARAMETERS["mode"])}
    mode = _mode(settings)
    train, test = input_bank(seed)
    solve = copy_only if mode == "copy_only" else copy_then_bridge

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": solve(grid)}

    return {
        "train": [pair(grid) for grid in train[:demos]],
        "test": [pair(grid) for grid in test[:queries]],
        "program_solution": program(settings),
    }
