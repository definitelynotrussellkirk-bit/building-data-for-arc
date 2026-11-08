"""Native parametric family for ``b83ad00fc681``.

``stamp_only`` is the exact selected canonical dictionary-stamping program.
``highlight_largest_stamped_cluster`` first executes that complete stamp, then
collapses every nonzero produced cell to binary occupancy, selects the unique
largest four-connected occupied cluster, and recolors that complete cluster 9.
The second stage therefore consumes connectivity created by dictionary lookup
and stamping; the marker grid alone contains only isolated requests.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "b83ad00fc681"
VERSION = "1.0.0"
FINISHES = ("stamp_only", "highlight_largest_stamped_cluster")
DEFAULT = {"finish": "stamp_only"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
CANONICAL_SHA256 = "46157a601fce9d70e7669dc2c4ab64f6364540d8009bc32a99cb0bad6456c781"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
RIVAL_NAMES = ("largest_same_color", "smallest_binary", "first_binary", "largest_bbox")


def _load_generator():
    body = GENERATOR_PATH.read_bytes()
    name = "_parametric_b83_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode() + body
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"finish"}
        or type(settings["finish"]) is not str
        or settings["finish"] not in FINISHES
    ):
        raise ValueError(
            "settings must be exactly {'finish': "
            "'stamp_only|highlight_largest_stamped_cluster'}"
        )
    return settings["finish"]


def _source(name: str, expected_sha256: str | None = None) -> str:
    raw = (HERE / name).read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise ValueError(f"{name} drifted: {observed}")
    if not raw.strip():
        raise ValueError(f"empty Racket source: {name}")
    return raw.decode("utf-8")


@lru_cache(maxsize=1)
def canonical_source() -> str:
    return _source("canonical.rkt", CANONICAL_SHA256)


@lru_cache(maxsize=1)
def alternate_source() -> str:
    return _source("highlight-largest-stamped-cluster.rkt")


def program(settings: Any) -> str:
    return canonical_source() if _finish(settings) == "stamp_only" else alternate_source()


def counterfactual_program() -> str:
    return _source("counterfactual-largest-same-color.rkt")


def _components(
    grid: list[list[int]], *, same_color: bool = False
) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c)):
                    if not (0 <= rr < height and 0 <= cc < width):
                        continue
                    if (rr, cc) in seen or grid[rr][cc] == 0:
                        continue
                    if same_color and grid[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    queue.append((rr, cc))
            result.append(sorted(cells))
    return result


def _paint(grid: list[list[int]], cells, color: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row, col in cells:
        result[row][col] = color
    return result


def intermediate(grid: Any) -> dict[str, Any]:
    stamped = _GEN._intended_python(grid)
    clusters = _components(stamped)
    if not clusters:
        raise ValueError("stamped output has no foreground")
    ordered = sorted(clusters, key=lambda cells: (-len(cells), cells[0]))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("largest stamped cluster must be unique")
    return {
        "stamped": stamped,
        "clusters": [[list(cell) for cell in cells] for cells in clusters],
        "cluster_sizes": [len(cells) for cells in clusters],
        "target_cells": [list(cell) for cell in ordered[0]],
    }


def solve(grid: Any, *, finish: str = "stamp_only") -> list[list[int]]:
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    info = intermediate(grid)
    if finish == "stamp_only":
        return deepcopy(info["stamped"])
    return _paint(info["stamped"], info["target_cells"], 9)


def _bbox_area(cells: list[tuple[int, int]]) -> int:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def rival_solve(grid: Any, name: str) -> list[list[int]]:
    if name not in RIVAL_NAMES:
        raise ValueError(f"unknown rival {name!r}")
    stamped = _GEN._intended_python(grid)
    binary = _components(stamped)
    if name == "largest_same_color":
        target = max(_components(stamped, same_color=True), key=lambda cells: (len(cells), tuple(cells)))
    elif name == "smallest_binary":
        target = min(binary, key=lambda cells: (len(cells), cells[0]))
    elif name == "first_binary":
        target = min(binary, key=lambda cells: cells[0])
    else:
        target = max(binary, key=lambda cells: (_bbox_area(cells), -cells[0][0], -cells[0][1]))
    return _paint(stamped, target, 9)


_PATTERN_CELLS = {
    "H": ((0, 0), (0, 1), (0, 2)),
    "V": ((0, 0), (1, 0), (2, 0)),
    "L": ((0, 0), (1, 0), (1, 1), (1, 2)),
}
_CHAIN_STEP = {"H": (0, 3), "V": (3, 0), "L": (0, 3)}

_DEMO_PROFILES = (
    {"shape": (11, 15), "target": ("H", 3), "decoy": ("L", 2), "tag": "compact_horizontal_chain"},
    {"shape": (12, 18), "target": ("L", 3), "decoy": ("H", 3), "tag": "compact_l_chain"},
    {"shape": (16, 20), "target": ("V", 3), "decoy": ("L", 2), "tag": "vertical_chain"},
    {"shape": (18, 22), "target": ("H", 4), "decoy": ("L", 2), "tag": "four_stamp_chain"},
    {"shape": (22, 24), "target": ("V", 4), "decoy": ("H", 3), "tag": "tall_four_stamp_chain"},
    {"shape": (24, 26), "target": ("L", 4), "decoy": ("H", 4), "tag": "large_l_chain"},
)
_QUERY_PROFILES = (
    {"shape": (10, 16), "target": ("H", 3), "decoy": ("L", 2), "tag": "minimum_body"},
    {"shape": (15, 21), "target": ("L", 3), "decoy": ("H", 3), "tag": "rectangular_transfer"},
    {"shape": (22, 27), "target": ("V", 4), "decoy": ("L", 2), "tag": "boundary_vertical"},
    {"shape": (30, 30), "target": ("H", 7), "decoy": ("L", 4), "tag": "exact_30x30_stress"},
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _group(kind: str, count: int) -> tuple[list[tuple[int, int]], set[tuple[int, int]], int, int]:
    dr, dc = _CHAIN_STEP[kind]
    markers = [(index * dr, index * dc) for index in range(count)]
    cells = {
        (mr + pr, mc + pc)
        for mr, mc in markers
        for pr, pc in _PATTERN_CELLS[kind]
    }
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    markers = [(r - min_r, c - min_c) for r, c in markers]
    cells = {(r - min_r, c - min_c) for r, c in cells}
    return markers, cells, 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _origins(body_h: int, body_w: int, group_h: int, group_w: int, corner: int):
    if group_h > body_h or group_w > body_w:
        return []
    candidates = [(r, c) for r in range(body_h - group_h + 1) for c in range(body_w - group_w + 1)]
    def score(item):
        r, c = item
        distances = (
            r + c,
            r + (body_w - group_w - c),
            (body_h - group_h - r) + c,
            (body_h - group_h - r) + (body_w - group_w - c),
        )
        return distances[corner], r, c
    return sorted(candidates, key=score)


def _separate(cells: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return False
        if any(neighbor in occupied for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))):
            return False
    return True


def _place_group(
    body_h: int,
    body_w: int,
    kind: str,
    count: int,
    corner: int,
    occupied: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    markers, cells, gh, gw = _group(kind, count)
    for top, left in _origins(body_h, body_w, gh, gw, corner):
        shifted = {(top + r, left + c) for r, c in cells}
        if _separate(shifted, occupied):
            occupied.update(shifted)
            return [(top + r, left + c) for r, c in markers]
    raise ValueError(f"cannot place {kind}x{count} in {body_h}x{body_w}")


def _panel_spans(width: int) -> list[tuple[int, int]]:
    content = width - 2
    base, extra = divmod(content, 3)
    widths = [base + (1 if index >= 3 - extra else 0) for index in range(3)]
    spans = []
    left = 0
    for index, panel_width in enumerate(widths):
        spans.append((left, left + panel_width))
        left += panel_width + (1 if index < 2 else 0)
    return spans


def _flip_scene(grid: list[list[int]], code: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    if code & 1:
        result = [list(reversed(row)) for row in result]
    if code & 2:
        result = [*reversed(result[:4]), result[4], *reversed(result[5:])]
    return result


def _build_profile(seed: int, split: str, index: int) -> list[list[int]]:
    spec = (_DEMO_PROFILES if split == "train" else _QUERY_PROFILES)[index]
    height, width = spec["shape"]
    body_h = height - 5
    rng = _rng(seed, split, index)
    pattern_order = list(_PATTERN_CELLS)
    rng.shuffle(pattern_order)
    keys = [1, 2, 3]
    rng.shuffle(keys)
    key_by_kind = dict(zip(pattern_order, keys, strict=True))
    decorations = [4, 5, 6, 7, 8]
    rng.shuffle(decorations)
    color_cells = {
        "H": (key_by_kind["H"], decorations[0], decorations[1]),
        "V": (key_by_kind["V"], decorations[1], decorations[2]),
        "L": (key_by_kind["L"], decorations[2], decorations[3], decorations[0]),
    }
    grid = [[0] * width for _ in range(height)]
    spans = _panel_spans(width)
    for _, right in spans[:-1]:
        for row in range(4):
            grid[row][right] = 9
    grid[4] = [9] * width
    for (left, right), kind in zip(spans, pattern_order, strict=True):
        coords = _PATTERN_CELLS[kind]
        ph = 1 + max(r for r, _ in coords)
        pw = 1 + max(c for _, c in coords)
        top = (4 - ph) // 2
        offset = (right - left - pw) // 2
        for (r, c), color in zip(coords, color_cells[kind], strict=True):
            grid[top + r][left + offset + c] = color

    occupied: set[tuple[int, int]] = set()
    target_kind, target_count = spec["target"]
    decoy_kind, decoy_count = spec["decoy"]
    isolated_kind = next(kind for kind in _PATTERN_CELLS if kind not in {target_kind, decoy_kind})
    # Keep a smaller stamped group earlier in row-major order than the true
    # winner.  This constructively refutes the tempting "highlight the first
    # produced cluster" shortcut in every two-demonstration prefix.
    groups = (
        (decoy_kind, decoy_count, 0),
        (isolated_kind, 1, 1),
        (target_kind, target_count, 3),
    )
    for kind, count, corner in groups:
        for row, col in _place_group(body_h, width, kind, count, corner, occupied):
            grid[5 + row][col] = key_by_kind[kind]
    # Horizontal reflection preserves the top-before-bottom teaching witness;
    # vertical reflection would sometimes move the true winner ahead of it.
    grid = _flip_scene(grid, rng.randrange(2))
    info = intermediate(grid)
    sizes = sorted(info["cluster_sizes"], reverse=True)
    if len(sizes) < 3 or sizes[0] == sizes[1]:
        raise AssertionError({"tag": spec["tag"], "sizes": sizes})
    if solve(grid, finish="highlight_largest_stamped_cluster") == rival_solve(grid, "largest_same_color"):
        raise AssertionError({"tag": spec["tag"], "rival": "largest_same_color"})
    return grid


@lru_cache(maxsize=4096)
def _scene_tuple(seed: int, split: str, index: int):
    return tuple(tuple(row) for row in _build_profile(seed, split, index))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> dict[str, list]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, *DEMO_LIMITS)
    queries = _integer("queries", queries, *QUERY_LIMITS)
    result = {
        "train": [_scene(seed, "train", index) for index in range(demos)],
        "test": [_scene(seed, "test", index) for index in range(queries)],
    }
    encoded = [json.dumps(grid, separators=(",", ":")) for values in result.values() for grid in values]
    if len(encoded) != len(set(encoded)):
        raise AssertionError("all generated inputs must be distinct")
    return result


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": deepcopy(grid), "output": solve(grid, finish=finish)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": deepcopy(grid), "output": solve(grid, finish=finish)}
            for grid in sampled["test"]
        ],
        "program_solution": program(settings),
        "settings": deepcopy(settings),
        "sampler": {
            "version": VERSION,
            "demo_profiles": [profile["tag"] for profile in _DEMO_PROFILES[:demos]],
            "query_profiles": [profile["tag"] for profile in _QUERY_PROFILES[:queries]],
        },
    }


def teaching_check(episode: dict[str, Any], settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    candidates = {
        "stamp_only": lambda grid: solve(grid, finish="stamp_only"),
        "highlight_largest_stamped_cluster": lambda grid: solve(
            grid, finish="highlight_largest_stamped_cluster"
        ),
        **{name: (lambda grid, n=name: rival_solve(grid, n)) for name in RIVAL_NAMES},
    }
    survivors = [
        name
        for name, candidate in candidates.items()
        if all(candidate(pair["input"]) == pair["output"] for pair in episode["train"])
    ]
    harmful = [
        name
        for name in survivors
        if any(candidates[name](pair["input"]) != pair["output"] for pair in episode["test"])
    ]
    return {
        "target": finish,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "rivals_tested": sorted(candidates),
        "fit_uses": "demonstrations_only",
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, list]:
    if not isinstance(episode, dict) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain a test list")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def describe(grid: Any, settings: Any) -> dict[str, Any]:
    info = intermediate(grid)
    return {
        "finish": _finish(settings),
        "input_shape": [len(grid), len(grid[0])],
        "output_shape": [len(info["stamped"]), len(info["stamped"][0])],
        "cluster_sizes": info["cluster_sizes"],
        "target_size": len(info["target_cells"]),
    }
