"""Native two-setting family for selecting objects by dilation-hole behavior.

The canonical setting selects the object whose enclosed-hole count decreases
under one 3x3 dilation.  The alternative selects the unique holed object whose
hole persists.  Inputs are matched across settings and always contain one of
each class plus solid distractors.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_SOURCE = _TASK_HOME / "generator.py"
_NAME = "_arc_615496fbe17b_production_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load production generator: {_SOURCE}")
_PRODUCTION = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PRODUCTION
_SPEC.loader.exec_module(_PRODUCTION)

SETTINGS = ({"hole_behavior": "sealed"}, {"hole_behavior": "persistent"})
DEFAULT = SETTINGS[0]
_PROGRAMS = {
    "sealed": (_HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "persistent": (_HOME / "persistent.rkt").read_text(encoding="utf-8"),
}
_COLORS = tuple(range(1, 10))
_DIMS = (
    (16, 22),
    (16, 22),
    (18, 22),
    (18, 24),
    (20, 24),
    (20, 26),
    (22, 24),
    (24, 26),
    (26, 28),
    (30, 30),
)


def _setting(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"hole_behavior"}:
        raise ValueError("settings must contain exactly hole_behavior")
    value = settings["hole_behavior"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("hole_behavior must be sealed or persistent")
    return {"hole_behavior": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _mix(seed: int, stream: str, index: int) -> int:
    payload = f"615496fbe17b:{seed}:{stream}:{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC integers 0..9")
    return deepcopy(grid)


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_setting(settings)["hole_behavior"]]


def dependency_intermediate(grid: Any, settings: dict[str, Any]) -> dict[str, Any]:
    normalized = _validate_grid(grid)
    behavior = _setting(settings)["hole_behavior"]
    base = _PRODUCTION.selection_intermediate(normalized)
    metrics = deepcopy(base["object_metrics"])
    if behavior == "sealed":
        candidates = [item["index"] for item in metrics if item["holes_before"] > item["holes_after"]]
    else:
        candidates = [
            item["index"]
            for item in metrics
            if item["holes_before"] > 0 and item["holes_before"] == item["holes_after"]
        ]
    if len(candidates) != 1:
        raise ValueError(f"expected one {behavior} object, found {len(candidates)}")
    return {
        "hole_behavior": behavior,
        "object_metrics": metrics,
        "selected_index": candidates[0],
    }


def _crop_metric(metric: dict[str, Any]) -> list[list[int]]:
    row_min, col_min, row_max, col_max = metric["bbox"]
    output = [[0] * (col_max - col_min + 1) for _ in range(row_max - row_min + 1)]
    for row, col in metric["cells"]:
        output[row - row_min][col - col_min] = 8
    return output


def solve_from_intermediate(grid: Any, intermediate: dict[str, Any]) -> list[list[int]]:
    normalized = _validate_grid(grid)
    if type(intermediate) is not dict:
        raise ValueError("intermediate must be a dictionary")
    fresh_metrics = _PRODUCTION.selection_intermediate(normalized)["object_metrics"]
    if intermediate.get("object_metrics") != fresh_metrics:
        raise ValueError("intermediate object metrics do not belong to this grid")
    selected = intermediate.get("selected_index")
    if type(selected) is not int or not 0 <= selected < len(fresh_metrics):
        raise ValueError("selected_index is invalid")
    return _crop_metric(fresh_metrics[selected])


def solve(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return solve_from_intermediate(grid, dependency_intermediate(grid, settings))


def _ring(
    outer_height: int,
    outer_width: int,
    hole_height: int,
    hole_width: int,
    hole_top: int,
    hole_left: int,
) -> tuple[tuple[int, int], ...]:
    if not (
        1 <= hole_top
        and 1 <= hole_left
        and hole_top + hole_height < outer_height
        and hole_left + hole_width < outer_width
    ):
        raise ValueError("hole must be strictly interior")
    return tuple(
        (row, col)
        for row in range(outer_height)
        for col in range(outer_width)
        if not (
            hole_top <= row < hole_top + hole_height
            and hole_left <= col < hole_left + hole_width
        )
    )


def _solid_mask(kind: int, size: int) -> tuple[tuple[int, int], ...]:
    if kind % 5 == 0:
        return tuple((0, col) for col in range(size))
    if kind % 5 == 1:
        return tuple((row, 0) for row in range(size))
    if kind % 5 == 2:
        return tuple(sorted({*( (0, col) for col in range(size) ), *( (row, 0) for row in range(1, size) )}))
    if kind % 5 == 3:
        return tuple((row, col) for row in range(2) for col in range(max(2, size // 2)))
    cells = {(0, 0)}
    row = col = 0
    for step in range(1, size):
        if step % 2:
            col += 1
        else:
            row += 1
        cells.add((row, col))
    return tuple(sorted(cells))


def _place(
    grid: list[list[int]],
    mask: tuple[tuple[int, int], ...],
    top: int,
    left: int,
    color: int,
    occupied: set[tuple[int, int]],
) -> bool:
    height, width = len(grid), len(grid[0])
    cells = {(top + row, left + col) for row, col in mask}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    for row, col in cells:
        if any((row + dr, col + dc) in occupied for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            return False
    for row, col in cells:
        grid[row][col] = color
    occupied.update(cells)
    return True


def _random_place(
    rng: random.Random,
    grid: list[list[int]],
    mask: tuple[tuple[int, int], ...],
    color: int,
    occupied: set[tuple[int, int]],
) -> None:
    height, width = len(grid), len(grid[0])
    mask_height = max(row for row, _ in mask) + 1
    mask_width = max(col for _, col in mask) + 1
    for _ in range(1200):
        top = rng.randint(0, height - mask_height)
        left = rng.randint(0, width - mask_width)
        if _place(grid, mask, top, left, color, occupied):
            return
    raise RuntimeError("failed to place a separated parametric object")


def _mask_extent(mask: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in mask) + 1, max(col for _, col in mask) + 1


def _packing_priority(item: tuple[tuple[tuple[int, int], ...], int]) -> tuple[int, int, int]:
    """Pack spatially demanding objects before small flexible distractors."""
    mask, _color = item
    height, width = _mask_extent(mask)
    return height * width, len(mask), max(height, width)


def _pack_random_scene(
    rng: random.Random,
    height: int,
    width: int,
    objects: list[tuple[tuple[tuple[int, int], ...], int]],
) -> tuple[list[list[int]], set[tuple[int, int]]]:
    """Retry a complete packing instead of leaving late objects marooned.

    A failed late placement is evidence that the earlier anchors were unlucky,
    not that the requested scene is impossible.  Restarting the complete scene
    keeps generation deterministic while avoiding seed-specific dead ends.
    """
    ordered = sorted(objects, key=_packing_priority, reverse=True)
    for _packing_attempt in range(160):
        candidate_grid = [[0] * width for _ in range(height)]
        candidate_occupied: set[tuple[int, int]] = set()
        try:
            for mask, color in ordered:
                _random_place(rng, candidate_grid, mask, color, candidate_occupied)
        except RuntimeError:
            continue
        return candidate_grid, candidate_occupied
    raise RuntimeError("failed to pack a complete separated parametric scene")


def _target_masks(index: int, rng: random.Random):
    if index == 0:
        sealed = _ring(8, 9, 2, 5, 3, 2)
        persistent = _ring(5, 5, 3, 3, 1, 1)
        return sealed, persistent
    if index == 1:
        sealed = _ring(4, 4, 1, 1, 1, 2)
        persistent = _ring(9, 10, 5, 6, 2, 2)
        return sealed, persistent
    sealed_specs = (
        (5, 8, 2, 4),
        (7, 7, 1, 4),
        (6, 9, 2, 5),
        (8, 8, 2, 2),
        (7, 10, 1, 6),
        (9, 8, 2, 4),
        (8, 11, 2, 6),
    )
    persistent_specs = (
        (6, 6, 3, 3),
        (7, 8, 3, 5),
        (8, 7, 4, 3),
        (9, 9, 5, 4),
        (8, 10, 3, 6),
        (10, 8, 6, 3),
        (9, 11, 4, 7),
    )
    sealed_spec = sealed_specs[(index - 2) % len(sealed_specs)]
    persistent_spec = persistent_specs[(index + 1) % len(persistent_specs)]
    sh, sw, hh, hw = sealed_spec
    ph, pw, qh, qw = persistent_spec
    sealed = _ring(sh, sw, hh, hw, rng.randint(1, sh - hh - 1), rng.randint(1, sw - hw - 1))
    persistent = _ring(ph, pw, qh, qw, rng.randint(1, ph - qh - 1), rng.randint(1, pw - qw - 1))
    return sealed, persistent


def _stress_scene(seed: int) -> list[list[int]]:
    rng = random.Random(_mix(seed, "scene", 9))
    grid = [[0] * 30 for _ in range(30)]
    occupied: set[tuple[int, int]] = set()
    colors = rng.sample(_COLORS, 4)
    sealed = _ring(10, 12, 2, 6, 4, 3)
    persistent = _ring(12, 13, 6, 7, 3, 3)
    if not _place(grid, sealed, 0, 0, colors[0], occupied):
        raise AssertionError("failed fixed stress sealed placement")
    if not _place(grid, persistent, 18, 17, colors[1], occupied):
        raise AssertionError("failed fixed stress persistent placement")
    if not _place(grid, _solid_mask(0, 7), 0, 20, colors[2], occupied):
        raise AssertionError("failed fixed stress top distractor")
    if not _place(grid, _solid_mask(2, 5), 25, 0, colors[3], occupied):
        raise AssertionError("failed fixed stress bottom distractor")
    return grid


def _scene(seed: int, index: int) -> list[list[int]]:
    if index == 9:
        return _stress_scene(seed)
    height, width = _DIMS[index]
    rng = random.Random(_mix(seed, "scene", index))
    sealed, persistent = _target_masks(index, rng)
    distractor_count = 2 + index % 3
    if index in (0, 1):
        colors = [1, 9, *rng.sample(tuple(range(2, 9)), distractor_count)]
    else:
        colors = rng.sample(_COLORS, 2 + distractor_count)

    distractors = [
        (_solid_mask(index + number, 3 + ((index + number) % 4)), colors[2 + number])
        for number in range(distractor_count)
    ]

    if index == 0:
        grid = [[0] * width for _ in range(height)]
        occupied: set[tuple[int, int]] = set()
        placements = ((sealed, 0, 0, colors[0]), (persistent, 11, 17, colors[1]))
    elif index == 1:
        grid = [[0] * width for _ in range(height)]
        occupied = set()
        placements = ((persistent, 0, 0, colors[0]), (sealed, 12, 18, colors[1]))
    else:
        grid, occupied = _pack_random_scene(
            rng,
            height,
            width,
            [(sealed, colors[0]), (persistent, colors[1]), *distractors],
        )
        placements = ()
    for mask, top, left, color in placements:
        if not _place(grid, mask, top, left, color, occupied):
            raise RuntimeError(f"failed fixed target placement for profile {index}")

    if index in (0, 1):
        # Fixed teaching targets are part of the contrast set.  Retry the
        # flexible distractor packing around those fixed anchors as a unit.
        base_grid = deepcopy(grid)
        base_occupied = set(occupied)
        for _packing_attempt in range(80):
            candidate_grid = deepcopy(base_grid)
            candidate_occupied = set(base_occupied)
            try:
                for mask, color in sorted(distractors, key=_packing_priority, reverse=True):
                    _random_place(rng, candidate_grid, mask, color, candidate_occupied)
            except RuntimeError:
                continue
            grid, occupied = candidate_grid, candidate_occupied
            break
        else:
            raise RuntimeError(f"failed to pack fixed teaching profile {index}")

    # Validate the intended two classes before exposing the scene.
    sealed_info = dependency_intermediate(grid, {"hole_behavior": "sealed"})
    persistent_info = dependency_intermediate(grid, {"hole_behavior": "persistent"})
    if sealed_info["selected_index"] == persistent_info["selected_index"]:
        raise AssertionError("hole classes must select different objects")
    return grid


@lru_cache(maxsize=128)
def _input_banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    scenes = [_scene(seed, index) for index in range(10)]
    return scenes[:6], scenes[6:]


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    selected = _setting(settings)
    demo_inputs, query_inputs = _input_banks(seed)

    def pairs(inputs: list[list[list[int]]]) -> list[dict[str, list[list[int]]]]:
        return [{"input": deepcopy(grid), "output": solve(grid, selected)} for grid in inputs]

    episode = {
        "settings": deepcopy(selected),
        "train": pairs(demo_inputs[:demos]),
        "test": pairs(query_inputs[:queries]),
        "program_solution": program(selected),
    }
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["train"] + episode["test"]]
    if len(keys) != len(set(keys)):
        raise AssertionError("generated inputs must be distinct")
    return episode


def first_turn_bytes(episode: dict[str, Any]) -> bytes:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    public = {
        "train": [
            {"input": _validate_grid(pair["input"]), "output": _validate_grid(pair["output"])}
            for pair in train
        ],
        "test": [{"input": _validate_grid(test[0]["input"])}],
    }
    return (json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _rival_selectors() -> dict[str, Callable[[list[dict[str, Any]]], int]]:
    def choose(key: Callable[[dict[str, Any]], Any], reverse: bool = False):
        return lambda metrics: sorted(metrics, key=lambda item: (key(item), item["index"]), reverse=reverse)[0]["index"]

    return {
        "leftmost": choose(lambda item: item["bbox"][1]),
        "rightmost": choose(lambda item: item["bbox"][3], True),
        "topmost": choose(lambda item: item["bbox"][0]),
        "bottommost": choose(lambda item: item["bbox"][2], True),
        "smallest_area": choose(lambda item: item["area"]),
        "largest_area": choose(lambda item: item["area"], True),
        "smallest_bbox": choose(lambda item: item["bbox_height"] * item["bbox_width"]),
        "largest_bbox": choose(lambda item: item["bbox_height"] * item["bbox_width"], True),
        "lowest_color": choose(lambda item: item["color"]),
        "highest_color": choose(lambda item: item["color"], True),
        "first_holed": lambda metrics: next(item["index"] for item in metrics if item["holes_before"]),
        "last_holed": lambda metrics: next(item["index"] for item in reversed(metrics) if item["holes_before"]),
        "smallest_void": choose(lambda item: item["bbox_height"] * item["bbox_width"] - item["area"]),
        "largest_void": choose(lambda item: item["bbox_height"] * item["bbox_width"] - item["area"], True),
    }


def audit_episode(episode: dict[str, Any], behavior: str) -> list[str]:
    _setting({"hole_behavior": behavior})
    demos = episode.get("train")
    if type(demos) is not list or len(demos) < 2:
        return ["at least two demonstrations are required"]
    survivors = []
    for name, selector in _rival_selectors().items():
        fits = True
        for pair in demos:
            metrics = _PRODUCTION.selection_intermediate(pair["input"])["object_metrics"]
            try:
                predicted = _crop_metric(metrics[selector(metrics)])
            except (StopIteration, IndexError):
                fits = False
                break
            if predicted != pair["output"]:
                fits = False
                break
        if fits:
            survivors.append(f"rival {name} fits every visible demonstration")
    return survivors
