"""Matched-input native episode family for 0281fbec1cf2.

The canonical setting stops after blocker-aware red-ray expansion.  The
alternative recomputes zero connectivity on that intermediate, selects the
unique largest pocket enclosed by the newly painted red walls, and fills it
with the color of the adjacent blocker that caps the pocket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
from types import ModuleType
from typing import Any, Final

TASK_ID: Final = "0281fbec1cf2"
FINISHES: Final = ("rays_only", "largest_pocket")
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]


def _load_generator() -> ModuleType:
    path = (_TASK_HOME / "generator.py").resolve()
    if path.parent != _TASK_HOME or not path.is_file():
        raise ValueError("missing exact task-local generator.py")
    name = "_arc_0281fbec1cf2_generator_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load task-local generator.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()

# height, width, top, left, rectangle height, rectangle width,
# blockers: (side, lane offset, pocket length, marker color)
_TRAIN_SPECS: Final = (
    (15, 17, 5, 5, 5, 7, (("top", 2, 1, 3), ("left", 2, 2, 4), ("bottom", 4, 4, 6))),
    (18, 16, 5, 6, 7, 5, (("top", 1, 2, 8), ("bottom", 3, 1, 4), ("left", 2, 3, 1), ("right", 4, 4, 3))),
    (14, 20, 5, 5, 5, 9, (("top", 4, 4, 8), ("bottom", 6, 1, 3), ("left", 1, 2, 4), ("right", 3, 3, 6))),
    (20, 19, 6, 6, 8, 7, (("top", 2, 2, 3), ("bottom", 4, 5, 5), ("left", 5, 3, 8), ("right", 1, 4, 4))),
    (22, 22, 7, 7, 9, 9, (("top", 2, 3, 3), ("top", 6, 1, 4), ("bottom", 4, 4, 8), ("left", 2, 2, 1), ("right", 6, 5, 7))),
    (12, 14, 4, 4, 5, 5, (("top", 1, 2, 3), ("bottom", 3, 2, 6), ("left", 3, 3, 9), ("right", 1, 1, 4))),
)

_QUERY_SPECS: Final = (
    (30, 30, 9, 8, 12, 13, (("top", 2, 2, 3), ("top", 7, 4, 4), ("bottom", 4, 7, 1), ("left", 3, 3, 8), ("right", 8, 5, 5))),
    (24, 21, 7, 7, 10, 8, (("top", 2, 4, 3), ("bottom", 5, 5, 8), ("left", 3, 6, 5), ("right", 6, 4, 4))),
    (17, 26, 7, 8, 6, 10, (("top", 5, 6, 9), ("bottom", 2, 3, 4), ("left", 2, 4, 6), ("right", 4, 5, 3))),
    (19, 19, 6, 6, 7, 7, (("top", 2, 3, 8), ("bottom", 4, 4, 4), ("left", 1, 2, 6), ("right", 5, 5, 3))),
)

_DECOY_COLORS: Final = (1, 3, 4, 5, 6, 7, 8, 9)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _marker_cell(top: int, left: int, bottom: int, right: int,
                 side: str, offset: int, gap: int) -> tuple[int, int]:
    if side == "top":
        return top - gap - 1, left + offset
    if side == "bottom":
        return bottom + gap + 1, left + offset
    if side == "left":
        return top + offset, left - gap - 1
    if side == "right":
        return top + offset, right + gap + 1
    raise ValueError(f"unknown side: {side}")


def _decoy_candidates(height: int, width: int, top: int, left: int,
                      bottom: int, right: int) -> list[tuple[int, int]]:
    bands = (
        range(0, top), range(0, left),
        range(bottom + 1, height), range(right + 1, width),
    )
    candidates: list[tuple[int, int]] = []
    for rows, cols in (
        (bands[0], bands[1]),
        (bands[0], bands[3]),
        (bands[2], bands[1]),
        (bands[2], bands[3]),
    ):
        candidates.extend((row, col) for row in rows for col in cols)
    return candidates


def _build_scene(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _TRAIN_SPECS if split == "train" else _QUERY_SPECS
    height, width, top, left, rect_h, rect_w, blockers = specs[index]
    bottom, right = top + rect_h - 1, left + rect_w - 1
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            grid[row][col] = 2

    occupied: set[tuple[int, int]] = set()
    for side, offset, gap, color in blockers:
        row, col = _marker_cell(top, left, bottom, right, side, offset, gap)
        if not (0 <= row < height and 0 <= col < width):
            raise AssertionError("profile blocker escaped the grid")
        if (row, col) in occupied or grid[row][col] != 0:
            raise AssertionError("profile blocker collision")
        occupied.add((row, col))
        grid[row][col] = color

    expected_sizes = sorted(gap for _side, _offset, gap, _color in blockers)
    largest = max(expected_sizes)
    if expected_sizes.count(largest) != 1:
        raise AssertionError("profile needs a unique largest pocket")
    target_color = next(color for _side, _offset, gap, color in blockers if gap == largest)

    # Misaligned markers are canonical distractors, but two nearby distractors
    # can accidentally cap a zero cell against the newly painted rays.  Select
    # them constructively: each accepted decoy must preserve the profile's exact
    # post-Stage-A pocket signature and intended largest-pocket marker.
    rng = _rng(seed, split, index)
    candidates = [cell for cell in _decoy_candidates(height, width, top, left, bottom, right)
                  if cell not in occupied]
    rng.shuffle(candidates)
    accepted = 0
    for row, col in candidates:
        color = _DECOY_COLORS[(seed + index * 3 + accepted) % len(_DECOY_COLORS)]
        grid[row][col] = color
        try:
            candidate_facts = analyze_scene(grid)
            candidate_sizes = sorted(len(region) for region in candidate_facts["enclosed_pockets"])
            safe = (candidate_sizes == expected_sizes
                    and candidate_facts["target_marker_color"] == target_color)
        except ValueError:
            safe = False
        if safe:
            accepted += 1
            if accepted == 3:
                break
        else:
            grid[row][col] = 0
    if accepted != 3:
        raise AssertionError((split, index, "could not place three inert decoys"))

    facts = analyze_scene(grid)
    actual_sizes = sorted(len(region) for region in facts["enclosed_pockets"])
    if actual_sizes != expected_sizes:
        raise AssertionError((split, index, "unexpected pocket sizes", expected_sizes, actual_sizes))
    if facts["target_marker_color"] != target_color:
        raise AssertionError((split, index, "wrong target marker", target_color, facts["target_marker_color"]))
    return grid


def _zero_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    regions: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if grid[start_row][start_col] != 0 or start in seen:
                continue
            seen.add(start)
            queue = [start]
            region: list[tuple[int, int]] = []
            for row, col in queue:
                region.append((row, col))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = row + dr, col + dc
                    cell = (nr, nc)
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 0 and cell not in seen):
                        seen.add(cell)
                        queue.append(cell)
            regions.append(sorted(region))
    return regions


def _touches_border(region: list[tuple[int, int]], height: int, width: int) -> bool:
    return any(row in (0, height - 1) or col in (0, width - 1) for row, col in region)


def _adjacent_markers(grid: list[list[int]], region: list[tuple[int, int]]) -> list[tuple[int, int, int]]:
    cells = set(region)
    result = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            value = grid[row][col]
            if value in (0, 2):
                continue
            if any((row + dr, col + dc) in cells for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0))):
                result.append((row, col, value))
    return result


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    stage_a = _GENERATOR.rule_mirror(deepcopy(grid))
    height, width = len(stage_a), len(stage_a[0])
    regions = _zero_regions(stage_a)
    enclosed = [region for region in regions if not _touches_border(region, height, width)]
    if not enclosed:
        raise ValueError("scene must create at least one enclosed pocket after ray expansion")
    largest_size = max(map(len, enclosed))
    targets = [region for region in enclosed if len(region) == largest_size]
    if len(targets) != 1:
        raise ValueError("scene must create a unique largest enclosed pocket")
    target = targets[0]
    markers = _adjacent_markers(grid, target)
    if len(markers) != 1:
        raise ValueError("largest pocket must be capped by exactly one adjacent non-red marker")
    target_color = markers[0][2]
    output = deepcopy(stage_a)
    for row, col in target:
        output[row][col] = target_color
    return {
        "stage_a": stage_a,
        "zero_regions": regions,
        "enclosed_pockets": enclosed,
        "target_pocket": target,
        "target_marker": markers[0],
        "target_marker_color": target_color,
        "largest_pocket_output": output,
    }


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be exactly 'rays_only' or 'largest_pocket'")
    facts = analyze_scene(grid)
    value = facts["stage_a"] if finish == "rays_only" else facts["largest_pocket_output"]
    return deepcopy(value)


def program_source(finish: str) -> str:
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be exactly 'rays_only' or 'largest_pocket'")
    name = "canonical.rkt" if finish == "rays_only" else "largest_pocket.rkt"
    path = (_HOME / name).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent program resource: {name}")
    return path.read_text()


def generate_episode(seed: int, finish: str, demos: int, queries: int,
                     source: str) -> dict[str, Any]:
    train = []
    for index in range(demos):
        grid = _build_scene(seed, "train", index)
        train.append({"input": deepcopy(grid), "output": solve(grid, finish)})
    test = []
    for index in range(queries):
        grid = _build_scene(seed, "test", index)
        test.append({"input": deepcopy(grid), "output": solve(grid, finish)})
    return {"train": train, "test": test, "program_solution": source}
