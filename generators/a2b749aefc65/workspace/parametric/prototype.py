#!/usr/bin/env python3
"""Episode-fixed one-step-versus-two-step family for ``a2b749aefc65``.

Stage A decodes the four border side colors into directions and assigns every
matching interior marker its direction. Stage B consumes those assignments and
moves each marker either one or two cells. The exact canonical one-step program
is the default. Inputs are shared across settings and preserve fully blocked,
partially blocked, and freely moving branches. Actual output cells are reserved
across markers and stationary distractors so neither rule relies on overwrite
order.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "a2b749aefc65"
ALLOWED_MODES = ("one_step", "two_steps")
DEFAULT_MODE = "one_step"
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
ROOT = find_root(__file__)
_SIDE_VECTORS = {
    "top": (-1, 0),
    "bottom": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def _validate_mode(travel_mode: str) -> None:
    if type(travel_mode) is not str or travel_mode not in ALLOWED_MODES:
        raise ValueError(f"travel_mode must be one of {ALLOWED_MODES}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if type(source) is not str or not source.strip():
                    raise ValueError("canonical record has no program_solution")
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected one canonical program, found {len(sources)}")
    return next(iter(sources))


def program_for(travel_mode: str = DEFAULT_MODE, *, root: Path = ROOT) -> str:
    _validate_mode(travel_mode)
    source = canonical_source(root=root)
    if travel_mode == DEFAULT_MODE:
        return source
    needle = "(let ((nr (+ r dr)) (nc (+ c dc)))"
    replacement = "(let ((nr (+ r (* 2 dr))) (nc (+ c (* 2 dc))))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches guarded travel patch")
    return source.replace(needle, replacement)


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("parametric_input", grid)
        return active.eval_text(f"({wrap_rule(program)} parametric_input)")
    finally:
        if owns_bridge:
            active.shutdown()


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if (len(grid) > 30 or width > 30
            or any(type(row) is not list or len(row) != width
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular exact colors 0..9 within 30x30")
    if len(grid) < 7 or width < 7:
        raise ValueError("grid needs a nontrivial bordered interior")
    return len(grid), width


def _background(grid) -> int:
    h, w = _validate_grid(grid)
    counts = Counter(grid[row][col] for row in range(1, h - 1) for col in range(1, w - 1))
    largest = max(counts.values())
    winners = [color for color, count in counts.items() if count == largest]
    if len(winners) != 1:
        raise ValueError("interior background must have a unique mode")
    return winners[0]


def analyze_motion(grid) -> dict[str, Any]:
    h, w = _validate_grid(grid)
    bg = _background(grid)
    side_colors = {
        "top": grid[0][w // 2],
        "bottom": grid[h - 1][w // 2],
        "left": grid[h // 2][0],
        "right": grid[h // 2][w - 1],
    }
    if len(set(side_colors.values())) != 4 or bg in side_colors.values():
        raise ValueError("four side colors must be distinct and differ from background")
    color_to_side = {color: side for side, color in side_colors.items()}
    markers = []
    distractors = []
    for row in range(1, h - 1):
        for col in range(1, w - 1):
            value = grid[row][col]
            if value == bg:
                continue
            if value not in color_to_side:
                distractors.append((row, col))
                continue
            side = color_to_side[value]
            source = (row, col)
            one = _actual_destination(source, side, 1, h, w)
            two = _actual_destination(source, side, 2, h, w)
            markers.append({
                "source": source,
                "destination_one": one,
                "destination_two": two,
                "blocked_one": one == source,
                "blocked_two": two == source,
                "color": value,
                "side": side,
            })
    if not markers:
        raise ValueError("input must contain side-colored markers")
    occupied: set[tuple[int, int]] = set()
    for marker in markers:
        cells = {
            marker["source"], marker["destination_one"], marker["destination_two"]
        }
        if cells & occupied:
            raise ValueError("actual motion reservations must be disjoint across markers")
        occupied.update(cells)
    if set(distractors) & occupied:
        raise ValueError("distractors must avoid every actual motion reservation")
    return {
        "height": h,
        "width": w,
        "background": bg,
        "side_colors": side_colors,
        "markers": markers,
        "distractors": distractors,
    }


def python_mirror(grid, *, travel_mode: str = DEFAULT_MODE):
    _validate_mode(travel_mode)
    h, w = _validate_grid(grid)
    bg = _background(grid)
    top = grid[0][w // 2]
    bottom = grid[h - 1][w // 2]
    left = grid[h // 2][0]
    right = grid[h // 2][w - 1]
    directions = {
        top: (-1, 0), bottom: (1, 0), left: (0, -1), right: (0, 1)
    }
    output = [
        [grid[row][col] if row in (0, h - 1) or col in (0, w - 1) else bg
         for col in range(w)]
        for row in range(h)
    ]
    steps = 1 if travel_mode == "one_step" else 2
    for row in range(1, h - 1):
        for col in range(1, w - 1):
            value = grid[row][col]
            if value == bg:
                continue
            dr, dc = directions.get(value, (0, 0))
            nr, nc = row + steps * dr, col + steps * dc
            if 1 <= nr <= h - 2 and 1 <= nc <= w - 2:
                output[nr][nc] = value
            else:
                output[row][col] = value
    return output


def _stable_rng(seed: int, sample_index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{sample_index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _inside_interior(cell: tuple[int, int], height: int, width: int) -> bool:
    row, col = cell
    return 1 <= row <= height - 2 and 1 <= col <= width - 2


def _actual_destination(source: tuple[int, int], side: str, steps: int,
                        height: int, width: int) -> tuple[int, int]:
    dr, dc = _SIDE_VECTORS[side]
    raw = (source[0] + steps * dr, source[1] + steps * dc)
    return raw if _inside_interior(raw, height, width) else source


def _boundary_sources(size: int) -> dict[str, tuple[tuple[int, int], tuple[int, int]]]:
    """Return one fully blocked and one two-step-only blocked source per side."""
    return {
        "top": ((1, 3), (2, 6)),
        "bottom": ((size - 2, size - 4), (size - 3, size - 7)),
        "left": ((3, 1), (6, 2)),
        "right": ((size - 4, size - 2), (size - 7, size - 3)),
    }


def _candidate_sources(size: int, side: str):
    candidates = []
    for row in range(1, size - 1):
        for col in range(1, size - 1):
            source = (row, col)
            one = _actual_destination(source, side, 1, size, size)
            two = _actual_destination(source, side, 2, size, size)
            if source != one and source != two and one != two:
                candidates.append((source, one, two))
    return candidates


def _reserve_marker(grid, side_colors: dict[str, int], side: str,
                    source: tuple[int, int], reserved: set[tuple[int, int]], markers):
    size = len(grid)
    one = _actual_destination(source, side, 1, size, size)
    two = _actual_destination(source, side, 2, size, size)
    actual_cells = {source, one, two}
    if actual_cells & reserved:
        return False
    row, col = source
    grid[row][col] = side_colors[side]
    reserved.update(actual_cells)
    markers.append((source, one, two, side))
    return True


def _place_markers(grid, side_colors: dict[str, int], marker_count: int, rng):
    if marker_count < 8:
        raise ValueError("marker_count must preserve two boundary branches per side")
    sides = list(_SIDE_VECTORS)
    rng.shuffle(sides)
    quotas = {side: 2 for side in sides}
    extras = marker_count - 8
    for index in range(extras):
        quotas[sides[index % len(sides)]] += 1

    reserved: set[tuple[int, int]] = set()
    markers = []
    anchors = _boundary_sources(len(grid))
    for side in sides:
        for source in anchors[side]:
            if not _reserve_marker(
                grid, side_colors, side, source, reserved, markers
            ):
                raise RuntimeError(f"boundary marker collision for {side} at {source}")

    for side in sides:
        candidates = _candidate_sources(len(grid), side)
        rng.shuffle(candidates)
        remaining = quotas[side] - 2
        if remaining == 0:
            continue
        placed = 0
        for source, _one, _two in candidates:
            if not _reserve_marker(
                grid, side_colors, side, source, reserved, markers
            ):
                continue
            placed += 1
            if placed == remaining:
                break
        if placed != remaining:
            raise RuntimeError(f"could not place collision-safe markers for {side}")
    return reserved, markers


def build_input(seed: int, sample_index: int, total: int, difficulty: str = "medium"):
    _validate_seed(seed)
    _validate_difficulty(difficulty)
    if type(sample_index) is not int or type(total) is not int or not 0 <= sample_index < total:
        raise ValueError("sample_index must be inside a positive total")
    final = sample_index == total - 1
    size = 30 if final else 14 + 2 * (sample_index % 5)
    marker_count = 24 if final else 8 + 2 * (sample_index % 4)
    distractor_count = 12 if final else 4 + sample_index % 5
    rng = _stable_rng(seed, sample_index)
    palette = rng.sample(range(10), 7)
    bg = palette[0]
    side_order = list(_SIDE_VECTORS)
    rng.shuffle(side_order)
    side_colors = {side: palette[index + 1] for index, side in enumerate(side_order)}
    distractor_colors = palette[5:]

    grid = [[bg for _ in range(size)] for _ in range(size)]
    for col in range(1, size - 1):
        grid[0][col] = side_colors["top"]
        grid[size - 1][col] = side_colors["bottom"]
    for row in range(1, size - 1):
        grid[row][0] = side_colors["left"]
        grid[row][size - 1] = side_colors["right"]

    reserved, _markers = _place_markers(grid, side_colors, marker_count, rng)
    available = [
        (row, col)
        for row in range(1, size - 1)
        for col in range(1, size - 1)
        if (row, col) not in reserved and grid[row][col] == bg
    ]
    rng.shuffle(available)
    if len(available) < distractor_count:
        raise RuntimeError("not enough cells for stationary distractors")
    for index, (row, col) in enumerate(available[:distractor_count]):
        grid[row][col] = distractor_colors[index % len(distractor_colors)]

    facts = analyze_motion(grid)
    if len(facts["markers"]) != marker_count or len(facts["distractors"]) != distractor_count:
        raise AssertionError("sampler count drift")
    if {marker["side"] for marker in facts["markers"]} != set(_SIDE_VECTORS):
        raise AssertionError("sampler must exercise all four decoded directions")
    if python_mirror(grid, travel_mode="one_step") == python_mirror(grid, travel_mode="two_steps"):
        raise AssertionError("sample does not distinguish travel modes")
    return grid


def grid_sha256(grid) -> str:
    _validate_grid(grid)
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def generate_claims(seed: int, *, travel_mode: str, difficulty: str = "medium",
                    demos: int = DEFAULT_DEMOS, queries: int = DEFAULT_QUERIES,
                    root: Path = ROOT) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(travel_mode)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    total = demos + queries
    inputs = [build_input(seed, index, total, difficulty) for index in range(total)]
    if len({grid_sha256(grid) for grid in inputs}) != total:
        raise AssertionError("sampler emitted duplicate visible inputs")
    pairs = [
        {"input": grid, "output": python_mirror(grid, travel_mode=travel_mode)}
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(travel_mode, root=root),
    }
