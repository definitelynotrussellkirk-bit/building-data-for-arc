"""Episode-level forward/reverse vector-direction family for 1b39c0e8ebc7.

The hidden setting is fixed once per episode.  Inputs are identical across the
two settings and contain targets reachable in both directions plus unmatched
sources/targets.  The canonical ``forward`` setting preserves the selected
Racket source byte-for-byte; ``reverse`` negates the marker-derived vector before
the same translate-and-intersect step.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "1b39c0e8ebc7"
PARAMETER = "vector_direction"
SETTINGS = ("forward", "reverse")
DEFAULT_SETTING = "forward"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERIES = 4
MAX_SEED = 2**63 - 1
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent

_GENERATOR_PATH = HOME.parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("_parametric_1b39c0e8ebc7_generator", _GENERATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_GENERATOR_PATH}")
_GEN = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _GEN
_SPEC.loader.exec_module(_GEN)

# Every profile is (height, width, base-vector, forward pairs, reverse pairs,
# unmatched sources, unmatched targets).  The last query is deliberately dense
# and edge-spanning rather than a padded small scene.
_DEMO_PROFILES = (
    (10, 12, (2, 3), 3, 2, 1, 2),
    (12, 14, (-2, 3), 2, 3, 2, 1),
    (14, 16, (3, -1), 4, 3, 1, 2),
    (16, 18, (-3, -2), 5, 4, 2, 2),
    (20, 22, (1, 3), 6, 5, 3, 2),
    (24, 26, (-1, -3), 7, 6, 3, 3),
)
_QUERY_PROFILES = (
    (11, 13, (1, -2), 3, 3, 2, 2),
    (17, 19, (-3, 1), 5, 4, 2, 3),
    (23, 27, (2, -3), 8, 7, 3, 3),
    (30, 30, (-3, -2), 12, 11, 4, 4),
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def canonical_source(*, root: Path = ROOT) -> str:
    values = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError("canonical record has no Racket program")
                values.append(source)
    if not values:
        raise KeyError(TASK_ID)
    if len(set(values)) != 1:
        raise ValueError("canonical variants disagree on Racket program")
    return values[0]


def program(settings: dict[str, str]) -> str:
    selected = _setting(settings)
    source = canonical_source()
    if selected == "forward":
        return source
    row_needle = "(dr (- (first p9) (first p8)))"
    col_needle = "(dc (- (second p9) (second p8)))"
    if source.count(row_needle) != 1 or source.count(col_needle) != 1:
        raise ValueError("canonical vector expressions no longer match guarded reverse patch")
    return source.replace(row_needle, "(dr (- (first p8) (first p9)))").replace(
        col_needle, "(dc (- (second p8) (second p9)))"
    )


def _transform_vector(vector: tuple[int, int], transform: int) -> tuple[int, int]:
    dr, dc = vector
    return (
        (dr, dc),
        (-dr, dc),
        (dr, -dc),
        (-dr, -dc),
        (dc, dr),
        (-dc, dr),
        (dc, -dr),
        (-dc, -dr),
    )[transform]


def _rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    raw = f"{TASK_ID}|parametric-vector-direction-v2|{seed}|{split}|{index}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _rank_shortcuts_refuted(grid: list[list[int]]) -> bool:
    """Require marker-distance rank rules to fail for both declared settings."""
    info = analyze_scene(grid)
    if info.get("errors"):
        return False
    anchor = info["marker_9"]
    targets = sorted(
        info["targets"],
        key=lambda q: (abs(q[0] - anchor[0]) + abs(q[1] - anchor[1]), q),
    )
    for key in ("forward_targets", "reverse_targets"):
        truth = set(info[key])
        count = len(truth)
        if truth == set(targets[:count]) or truth == set(targets[-count:]):
            return False
    return True


def _relocate_markers_for_rank(
    grid: list[list[int]], vector: tuple[int, int], rng: random.Random
) -> list[list[int]] | None:
    """Keep all 3/4 geometry fixed and move only the vector marker pair."""
    base = [row[:] for row in grid]
    for r, row in enumerate(base):
        for c, value in enumerate(row):
            if value in (8, 9):
                base[r][c] = 0
    height, width = len(base), len(base[0])
    candidates = []
    for r in range(height):
        for c in range(width):
            rr, cc = r + vector[0], c + vector[1]
            if (
                0 <= rr < height
                and 0 <= cc < width
                and base[r][c] == 0
                and base[rr][cc] == 0
            ):
                candidates.append(((r, c), (rr, cc)))
    rng.shuffle(candidates)
    for p8, p9 in candidates:
        candidate = [row[:] for row in base]
        candidate[p8[0]][p8[1]] = 8
        candidate[p9[0]][p9[1]] = 9
        if _rank_shortcuts_refuted(candidate):
            return candidate
    return None


@lru_cache(maxsize=4096)
def _sample_input_cached(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, base_vector, forward, reverse, source_decoys, target_decoys = profiles[index]
    vector = _transform_vector(base_vector, seed % 8)
    for attempt in range(8):
        rng = _rng(seed, split, index, attempt)
        grid = _GEN.construct_scene(
            height=height,
            width=width,
            vector=vector,
            matched_pairs=forward,
            reverse_pairs=reverse,
            source_decoys=source_decoys,
            target_decoys=target_decoys,
            rng=rng,
            spread=(split == "test" and index == len(_QUERY_PROFILES) - 1),
        )
        if split == "train":
            relocated = _relocate_markers_for_rank(grid, vector, rng)
            if relocated is None:
                continue
            grid = relocated
        return tuple(tuple(row) for row in grid)
    raise ValueError("could not construct a demonstration that refutes marker-distance rank shortcuts")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    if type(index) is not int or not 0 <= index < len(profiles):
        raise ValueError("profile index out of range")
    return [list(row) for row in _sample_input_cached(seed, split, index)]


def analyze_scene(grid):
    return _GEN.analyze_scene(grid)


def apply_with_vector(grid: list[list[int]], vector: tuple[int, int]) -> list[list[int]]:
    """Apply translate/intersect with an explicit vector, including rival vectors."""
    height, width = _GEN._strict_grid(grid)
    if type(vector) is not tuple or len(vector) != 2 or any(type(v) is not int for v in vector):
        raise TypeError("vector must contain two exact integers")
    sources = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    targets = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    output = [[0 for _ in range(width)] for _ in range(height)]
    for source in sources:
        target = (source[0] + vector[0], source[1] + vector[1])
        if target in targets:
            output[target[0]][target[1]] = 7
    return output


def apply_rule(grid: list[list[int]], direction: str) -> list[list[int]]:
    if type(direction) is not str or direction not in SETTINGS:
        raise ValueError(f"direction must be one of {SETTINGS!r}")
    info = analyze_scene(grid)
    if info.get("errors"):
        raise ValueError(f"invalid scene: {info['errors']}")
    vector = info["vector"]
    if direction == "reverse":
        vector = (-vector[0], -vector[1])
    return apply_with_vector(grid, vector)


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERIES, QUERIES)
    selected = _setting(settings)
    train = []
    for index in range(demos):
        grid = sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, selected)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, selected)})
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in [*train, *test]]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}


def grid_sha256(grid: Iterable[Iterable[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
