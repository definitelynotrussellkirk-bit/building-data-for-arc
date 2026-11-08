"""Native nested-frame family with a selected-frame geometry relay.

``frame_only`` is the exact canonical rule: count red markers and recolor the
matching outer-to-inner yellow frame cyan. ``center_cross`` keeps that selection,
then consumes the selected frame's bounding box to paint its strict center row
and column 9. Python outputs are claims; qualification replays every label in
protected Racket.
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
from typing import Any, Iterable

TASK_ID = "af9ade3c3e16"
VERSION = "selected-frame-center-cross-v1"
FINISHES = ("frame_only", "center_cross")
SETTINGS = tuple({"finish": value} for value in FINISHES)
DEFAULT_SETTINGS = {"finish": "frame_only"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
CANONICAL_SHA256 = "d1f13762e480bbf16e05b4ca5737ab5a2c0934e69cb8a404446a5a0a334272d8"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
SHORTCUTS = (
    "always_outer_frame",
    "always_inner_frame",
    "reverse_rank_frame",
    "outer_bbox_cross",
    "inner_bbox_cross",
    "fill_selected_interior",
    "selected_diagonals",
    "cross_without_border",
)

_DEMO_PROFILES = (
    (15, 17, 3, 2, "middle_of_three"),
    (17, 15, 3, 3, "inner_of_three"),
    (19, 21, 4, 2, "second_of_four"),
    (21, 19, 4, 4, "inner_of_four"),
    (24, 26, 5, 3, "middle_of_five"),
    (26, 24, 5, 5, "inner_of_five"),
)
_QUERY_PROFILES = (
    (18, 20, 3, 2, "rectangular_query"),
    (22, 25, 4, 3, "large_four_frame_query"),
    (27, 29, 5, 4, "large_five_frame_query"),
    (30, 30, 5, 4, "exact_30x30_boundary_stress"),
)


def _load_generator():
    body = GENERATOR_PATH.read_bytes()
    name = "_parametric_af9_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode() + body
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {GENERATOR_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(body, str(GENERATOR_PATH), "exec"), module.__dict__)
    return module


_GEN = _load_generator()


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _source(name: str, expected_sha256: str | None = None) -> str:
    raw = (HERE / name).read_bytes()
    if not raw.strip():
        raise ValueError(f"empty Racket source: {name}")
    observed = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise ValueError(f"{name} drifted: {observed}")
    return raw.decode("utf-8")


@lru_cache(maxsize=1)
def canonical_source() -> str:
    return _source("canonical.rkt", CANONICAL_SHA256)


@lru_cache(maxsize=1)
def composed_source() -> str:
    return _source("center-cross.rkt")


def program(settings: Any) -> str:
    return canonical_source() if _finish(settings) == "frame_only" else composed_source()


def counterfactual_program() -> str:
    return _source("wrong-outer-cross.rkt")


def _validated_grid(grid: Any) -> list[list[int]]:
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError("invalid nested-frame input: " + "; ".join(errors))
    return [list(row) for row in grid]


def _bbox_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _strict_cross(box: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = box
    mr, mc = (r0 + r1) // 2, (c0 + c1) // 2
    return tuple(
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if r == mr or c == mc
    )


def _strict_interior(box: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = box
    return tuple((r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1))


def _diagonals(box: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = box
    height, width = r1 - r0 - 1, c1 - c0 - 1
    cells = []
    for offset in range(min(height, width)):
        cells.append((r0 + 1 + offset, c0 + 1 + offset))
        cells.append((r0 + 1 + offset, c1 - 1 - offset))
    return tuple(sorted(set(cells)))


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    output = [row[:] for row in grid]
    for row, col in cells:
        output[row][col] = color
    return output


def intermediate(grid: Any) -> dict[str, Any]:
    checked = _validated_grid(grid)
    frames = tuple(_GEN._frame_bboxes(checked))
    rank = sum(cell == 2 for row in checked for cell in row)
    if not 1 <= rank <= len(frames):
        raise ValueError("red marker count does not select a frame")
    selected = frames[rank - 1]
    cross = _strict_cross(selected)
    if not cross:
        raise ValueError("selected frame has no strict center cross")
    return {
        "frames": [list(box) for box in frames],
        "rank": rank,
        "selected_bbox": list(selected),
        "outer_bbox": list(frames[0]),
        "center": [(selected[0] + selected[2]) // 2, (selected[1] + selected[3]) // 2],
        "cross_cells": [list(cell) for cell in cross],
    }


def solve(grid: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    checked = _validated_grid(grid)
    info = intermediate(checked)
    selected = tuple(info["selected_bbox"])
    output = _paint(checked, _bbox_cells(selected), 8)
    if finish == "center_cross":
        output = _paint(output, (tuple(cell) for cell in info["cross_cells"]), 9)
    return output


def counterfactual_transform(grid: Any) -> list[list[int]]:
    checked = _validated_grid(grid)
    info = intermediate(checked)
    output = _paint(checked, _bbox_cells(tuple(info["selected_bbox"])), 8)
    return _paint(output, _strict_cross(tuple(info["outer_bbox"])), 9)


def _solve_with_box(grid: Any, box: tuple[int, int, int, int], *, cross: bool) -> list[list[int]]:
    checked = _validated_grid(grid)
    output = _paint(checked, _bbox_cells(box), 8)
    return _paint(output, _strict_cross(box), 9) if cross else output


def shortcut_solve(grid: Any, name: str) -> list[list[int]]:
    if name not in SHORTCUTS:
        raise ValueError(f"unknown shortcut {name!r}")
    checked = _validated_grid(grid)
    info = intermediate(checked)
    frames = tuple(tuple(box) for box in info["frames"])
    selected = tuple(info["selected_bbox"])
    if name == "always_outer_frame":
        return _solve_with_box(checked, frames[0], cross=False)
    if name == "always_inner_frame":
        return _solve_with_box(checked, frames[-1], cross=False)
    if name == "reverse_rank_frame":
        reverse = frames[-info["rank"]]
        return _solve_with_box(checked, reverse, cross=False)
    output = _paint(checked, _bbox_cells(selected), 8)
    if name == "outer_bbox_cross":
        return _paint(output, _strict_cross(frames[0]), 9)
    if name == "inner_bbox_cross":
        return _paint(output, _strict_cross(frames[-1]), 9)
    if name == "fill_selected_interior":
        return _paint(output, _strict_interior(selected), 9)
    if name == "selected_diagonals":
        return _paint(output, _diagonals(selected), 9)
    return _paint(checked, _strict_cross(selected), 9)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    for row, col in _bbox_cells(box):
        if grid[row][col] != 0:
            raise AssertionError("nested frame collision")
        grid[row][col] = 4


def _triomino_candidates(grid: list[list[int]]):
    shapes = (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    )
    height, width = len(grid), len(grid[0])
    result = []
    for shape in shapes:
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for top in range(height - sh + 1):
            for left in range(width - sw + 1):
                cells = tuple((top + r, left + c) for r, c in shape)
                if all(grid[r][c] == 0 for r, c in cells):
                    result.append(cells)
    return result


def _build_scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, n_frames, rank, _tag = profiles[index]
    rng = _rng(seed, split, index)
    minimum = 4 * n_frames - 1
    min_outer_h = minimum + max(0, (height - 2 - minimum) // 2)
    min_outer_w = minimum + max(0, (width - 2 - minimum) // 2)
    outer_h = rng.randint(min_outer_h, height - 2)
    outer_w = rng.randint(min_outer_w, width - 2)
    top = rng.randint(1, height - outer_h - 1)
    left = rng.randint(1, width - outer_w - 1)
    grid = [[0] * width for _ in range(height)]
    boxes = []
    for frame_index in range(n_frames):
        inset = 2 * frame_index
        box = (top + inset, left + inset,
               top + outer_h - 1 - inset, left + outer_w - 1 - inset)
        boxes.append(box)
        _draw_frame(grid, box)

    outer = boxes[0]
    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0
        and not (outer[0] <= r <= outer[2] and outer[1] <= c <= outer[3])
    ]
    # Keep boundary contacts common, and guaranteed on the 30x30 stress profile.
    boundary = [p for p in candidates if p[0] in (0, height - 1) or p[1] in (0, width - 1)]
    if split == "test" and index == len(_QUERY_PROFILES) - 1:
        marker_cells = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
        if rank != 4 or any(cell not in candidates for cell in marker_cells):
            raise AssertionError("30x30 stress cannot place four boundary markers")
        ordered = list(marker_cells)
    else:
        rng.shuffle(boundary)
        rng.shuffle(candidates)
        boundary_set = set(boundary)
        ordered = boundary + [p for p in candidates if p not in boundary_set]
    for r, c in ordered[:rank]:
        grid[r][c] = 2

    triominoes = _triomino_candidates(grid)
    if not triominoes:
        raise AssertionError("no room for triomino")
    edge_triominoes = [
        cells for cells in triominoes
        if any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
    ]
    chosen_pool = edge_triominoes or triominoes
    for r, c in rng.choice(chosen_pool):
        grid[r][c] = 6

    errors = _GEN.self_check(grid)
    if errors:
        raise AssertionError({"profile": profiles[index], "errors": errors})
    return grid


@lru_cache(maxsize=1024)
def _scene_tuple(seed: int, split: str, index: int):
    return tuple(tuple(row) for row in _build_scene(seed, split, index))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> dict[str, list]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, *DEMO_LIMITS)
    queries = _integer("queries", queries, *QUERY_LIMITS)
    sampled = {
        "train": [_scene(seed, "train", i) for i in range(demos)],
        "test": [_scene(seed, "test", i) for i in range(queries)],
    }
    keys = [json.dumps(grid, separators=(",", ":"))
            for split in ("train", "test") for grid in sampled[split]]
    if len(keys) != len(set(keys)):
        raise AssertionError("all generated inputs must be distinct")
    return sampled


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    chosen = {"finish": finish}
    return {
        "train": [
            {"input": deepcopy(grid), "output": solve(grid, chosen)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": deepcopy(grid), "output": solve(grid, chosen)}
            for grid in sampled["test"]
        ],
        "program_solution": program(chosen),
        "settings": chosen,
        "sampler": {
            "version": VERSION,
            "demo_profiles": [row[4] for row in _DEMO_PROFILES[:demos]],
            "query_profiles": [row[4] for row in _QUERY_PROFILES[:queries]],
        },
    }


def lesson_certificate(train_pairs: Any, settings: Any) -> dict[str, Any]:
    chosen = {"finish": _finish(settings)}
    if type(train_pairs) is not list or not train_pairs:
        raise ValueError("train_pairs must be a nonempty list")
    for pair in train_pairs:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("each demonstration needs input and output")
    survivors = [
        candidate for candidate in SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train_pairs)
    ]
    shortcuts = [
        name for name in SHORTCUTS
        if all(shortcut_solve(pair["input"], name) == pair["output"] for pair in train_pairs)
    ]
    return {
        "settings": chosen,
        "demonstrations": len(train_pairs),
        "surviving_settings": survivors,
        "surviving_shortcuts": shortcuts,
        "query_outputs_used": False,
    }


def analyze(grid: Any) -> dict[str, Any]:
    checked = _validated_grid(grid)
    info = intermediate(checked)
    occupied = [(r, c) for r, row in enumerate(checked) for c, value in enumerate(row) if value]
    sides = []
    if any(r == 0 for r, _ in occupied): sides.append("top")
    if any(r == len(checked) - 1 for r, _ in occupied): sides.append("bottom")
    if any(c == 0 for _, c in occupied): sides.append("left")
    if any(c == len(checked[0]) - 1 for _, c in occupied): sides.append("right")
    return {
        "shape": [len(checked), len(checked[0])],
        "frame_count": len(info["frames"]),
        "rank": info["rank"],
        "selected_bbox": info["selected_bbox"],
        "outer_bbox": info["outer_bbox"],
        "cross_cell_count": len(info["cross_cells"]),
        "nonzero_count": len(occupied),
        "boundary_sides": sorted(sides),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
