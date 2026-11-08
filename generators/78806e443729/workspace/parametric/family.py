"""Deterministic matched-input family for horizontal beams and dominant relay."""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "78806e443729"
BEAM_MODES = ("horizontal_only", "dominant_relay")
DEFAULT_BEAM_MODE = "horizontal_only"
HERE = Path(__file__).resolve().parent

DEMO_SPECS = (
    {"height": 7, "width": 10, "rows": (1, 3, 5), "target": 1, "side": "right", "blocker": None},
    {"height": 8, "width": 12, "rows": (0, 3, 7), "target": 1, "side": "left", "blocker": "above"},
    {"height": 10, "width": 14, "rows": (1, 5, 8), "target": 1, "side": "right", "blocker": "below"},
    {"height": 12, "width": 16, "rows": (0, 4, 8, 11), "target": 2, "side": "left", "blocker": None},
    {"height": 15, "width": 18, "rows": (2, 6, 10, 14), "target": 1, "side": "right", "blocker": "above"},
    {"height": 18, "width": 20, "rows": (1, 7, 12, 17), "target": 2, "side": "left", "blocker": "below"},
)
QUERY_SPECS = (
    {"height": 30, "width": 30, "rows": (0, 9, 20, 29), "target": 2, "side": "right", "blocker": None},
    {"height": 24, "width": 27, "rows": (2, 8, 15, 23), "target": 1, "side": "left", "blocker": "above"},
    {"height": 21, "width": 23, "rows": (0, 6, 13, 20), "target": 2, "side": "right", "blocker": "below"},
    {"height": 27, "width": 25, "rows": (1, 10, 18, 26), "target": 1, "side": "left", "blocker": None},
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str or value not in BEAM_MODES:
        raise ValueError("beam_mode must be exactly 'horizontal_only' or 'dominant_relay'")
    return value


@lru_cache(maxsize=4)
def _canonical_authority_cached(root_text: str) -> str:
    root = Path(root_text)
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one exact canonical program authority")
    return next(iter(programs))


@lru_cache(maxsize=1)
def _default_root() -> Path:
    return find_root(__file__)


@lru_cache(maxsize=8)
def _program_text_cached(mode: str, root_text: str) -> str:
    root = Path(root_text)
    path = HERE / "programs" / f"{mode}.rkt"
    source = path.read_text(encoding="utf-8")
    canonical = _canonical_authority_cached(root_text)
    materialized_default = (HERE / "programs" / "horizontal_only.rkt").read_text(encoding="utf-8")
    if materialized_default != canonical:
        raise ValueError("materialized default program differs from canonical authority")
    if mode == DEFAULT_BEAM_MODE and source != canonical:
        raise ValueError("default program must preserve canonical bytes")
    if mode == "dominant_relay" and source.count("(mode base 0)") != 1:
        raise ValueError("dominant relay selector is missing or duplicated")
    return source


def program_text(beam_mode: str, *, root: Path | None = None) -> str:
    mode = _mode(beam_mode)
    resolved = _default_root() if root is None else Path(root).resolve()
    return _program_text_cached(mode, str(resolved))


def _stable_rng(seed: int, slot: int) -> random.Random:
    digest = hashlib.sha256(f"beam-relay-v1:{seed}:{slot}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _candidate_lefts(width: int, side: str) -> list[int]:
    low, high = ((2, width - 4) if side == "right" else (3, width - 5))
    if low > high:
        raise ValueError("width too small for a unique dominant segment")
    values = list(range(low, high + 1))
    middle = values[len(values) // 2]
    ordered = []
    for value in (values[0], middle, values[-1], *values):
        if value not in ordered:
            ordered.append(value)
    return ordered


def _choose_right(left: int, width: int, forbidden: int, offset: int) -> int:
    legal = [col for col in range(left + 2, width - 1) if col != forbidden]
    if not legal:
        raise ValueError("no legal separated right seed column")
    return legal[offset % len(legal)]


def _layout(spec: dict[str, Any]) -> tuple[list[tuple[int, int, int]], int]:
    height = int(spec["height"])
    width = int(spec["width"])
    rows = tuple(int(row) for row in spec["rows"])
    target_index = int(spec["target"])
    side = str(spec["side"])
    if side == "right":
        target_left, target_right = 1, width - 3
        target_anchor = target_right
    elif side == "left":
        target_left, target_right = width - 4, width - 2
        target_anchor = target_left
    else:
        raise ValueError("unknown target side")
    blocker_index = None
    blocker = spec.get("blocker")
    if blocker == "above":
        above = [i for i, row in enumerate(rows) if row < rows[target_index]]
        blocker_index = above[-1] if above else None
    elif blocker == "below":
        below = [i for i, row in enumerate(rows) if row > rows[target_index]]
        blocker_index = below[0] if below else None
    elif blocker is not None:
        raise ValueError("unknown blocker direction")

    lefts = _candidate_lefts(width, side)
    triples: list[tuple[int, int, int]] = []
    cursor = 0
    for index, row in enumerate(rows):
        if index == target_index:
            triples.append((row, target_left, target_right))
            continue
        left = lefts[cursor % len(lefts)]
        cursor += 1
        if blocker_index == index:
            if left + 1 >= target_anchor:
                left = next(value for value in lefts if value + 1 < target_anchor)
            right = target_anchor
        else:
            right = _choose_right(left, width, target_anchor, index + target_index)
        if not (0 <= row < height and 1 <= left < right - 1 < width - 1):
            raise ValueError("constructed seed layout is outside grammar")
        triples.append((row, left, right))
    return triples, target_anchor


def build_input(seed: int, slot: int, spec: dict[str, Any]) -> list[list[int]]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("slot", slot, 0, 9)
    height, width = int(spec["height"]), int(spec["width"])
    triples, _anchor = _layout(spec)
    target_index = int(spec["target"])
    target_side = str(spec["side"])
    positions = [(row, left, "left") for row, left, _right in triples]
    positions += [(row, right, "right") for row, _left, right in triples]
    positions.sort()
    target_row, target_left, target_right = triples[target_index]
    target_col = target_left if target_side == "left" else target_right
    target_position = (target_row, target_col, target_side)

    rng = _stable_rng(seed, slot)
    target_color = (4, 5, 6)[(seed + slot) % 3]
    available = [color for color in range(1, 10) if color != target_color]
    rng.shuffle(available)
    assignments: dict[tuple[int, int, str], int] = {target_position: target_color}
    remaining_positions = [position for position in positions if position != target_position]
    if remaining_positions:
        assignments[remaining_positions[0]] = 1 if target_color != 1 else 2
    if len(remaining_positions) > 1:
        assignments[remaining_positions[-1]] = 9 if target_color != 9 else 8
    used = set(assignments.values())
    pool = [color for color in available if color not in used]
    rng.shuffle(pool)
    for position in remaining_positions:
        if position not in assignments:
            assignments[position] = pool.pop()

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for position, color in assignments.items():
        row, col, _side = position
        grid[row][col] = color
    facts = analyze_input(grid)
    if facts["dominant_seed"] != [target_row, target_col]:
        raise AssertionError("constructed target is not the unique dominant beam")
    return grid


def horizontal_output(grid: list[list[int]]) -> list[list[int]]:
    original = [list(row) for row in grid]
    output = [list(row) for row in grid]
    height, width = len(original), len(original[0])
    for row in range(height):
        for col in range(width):
            color = original[row][col]
            if color == 0:
                continue
            left = col - 1
            while left >= 0 and original[row][left] == 0:
                output[row][left] = color
                left -= 1
            right = col + 1
            while right < width and original[row][right] == 0:
                output[row][right] = color
                right += 1
    return output


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC integers")
    seeds = [(r, c, grid[r][c]) for r in range(len(grid)) for c in range(width) if grid[r][c] != 0]
    colors = [color for _r, _c, color in seeds]
    if len(colors) < 4 or len(colors) != len(set(colors)):
        raise ValueError("parametric grammar requires globally distinct seed colors")
    active_rows = sorted({r for r, _c, _color in seeds})
    if any(sum(grid[r][c] != 0 for c in range(width)) != 2 for r in active_rows):
        raise ValueError("each active row must contain exactly two seeds")
    for row in active_rows:
        cols = [c for c in range(width) if grid[row][c] != 0]
        if cols[0] == 0 or cols[-1] == width - 1 or cols[1] - cols[0] <= 1:
            raise ValueError("seed pairs must be separated and interior")
    base = horizontal_output(grid)
    counts = {color: sum(cell == color for row in base for cell in row) for color in colors}
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
        raise ValueError("dominant beam must be unique")
    dominant, dominant_count = ranked[0]
    seed = next((r, c) for r, c, color in seeds if color == dominant)
    row_seed_cols = [c for r, c, _color in seeds if r == seed[0]]
    side = "left" if seed[1] == min(row_seed_cols) else "right"
    blockers = []
    for delta, name in ((-1, "above"), (1, "below")):
        rr = seed[0] + delta
        while 0 <= rr < len(grid) and grid[rr][seed[1]] == 0:
            rr += delta
        if 0 <= rr < len(grid):
            blockers.append({"direction": name, "position": [rr, seed[1]], "color": grid[rr][seed[1]]})
    return {
        "height": len(grid),
        "width": width,
        "active_rows": active_rows,
        "seed_count": len(seeds),
        "counts": counts,
        "dominant_color": dominant,
        "dominant_count": dominant_count,
        "runner_up_count": ranked[1][1],
        "dominant_seed": [seed[0], seed[1]],
        "dominant_side": side,
        "vertical_blockers": blockers,
    }


def dominant_relay_output(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze_input(grid)
    output = horizontal_output(grid)
    row, col = facts["dominant_seed"]
    color = facts["dominant_color"]
    rr = row - 1
    while rr >= 0 and grid[rr][col] == 0:
        output[rr][col] = color
        rr -= 1
    rr = row + 1
    while rr < len(grid) and grid[rr][col] == 0:
        output[rr][col] = color
        rr += 1
    return output


def output_for(grid: list[list[int]], beam_mode: str) -> list[list[int]]:
    mode = _mode(beam_mode)
    return horizontal_output(grid) if mode == "horizontal_only" else dominant_relay_output(grid)


def generate_episode(seed: int, beam_mode: str, demos: int, queries: int, program: str) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    _plain_int("queries", queries, 1, 4)
    mode = _mode(beam_mode)
    demo_inputs = [build_input(seed, index, spec) for index, spec in enumerate(DEMO_SPECS)]
    query_inputs = [build_input(seed, 6 + index, spec) for index, spec in enumerate(QUERY_SPECS)]
    train = [{"input": copy.deepcopy(grid), "output": output_for(grid, mode)} for grid in demo_inputs[:demos]]
    test = [{"input": copy.deepcopy(grid), "output": output_for(grid, mode)} for grid in query_inputs[:queries]]
    all_inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in [*train, *test]]
    if len(all_inputs) != len(set(all_inputs)):
        raise RuntimeError("episode inputs are not distinct")
    return {"train": train, "test": test, "program_solution": program}


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _plain_int("query_index", query_index, 0, len(episode["test"]) - 1)
    public = public_challenge(episode)
    return {"train": public["train"], "test": [public["test"][query_index]]}


def public_filename(episode: dict[str, Any]) -> str:
    return "challenge-" + hashlib.sha256(public_challenge_bytes(public_challenge(episode))).hexdigest() + ".json"


def rival_program(selector: str) -> str:
    selectors = {
        "shortest_relay": "(minority base 0)",
        "smallest_color_relay": "(apply min (grid-colors base 0))",
        "largest_color_relay": "(apply max (grid-colors base 0))",
        "first_seed_relay": "(third (first (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells g))))",
    }
    if selector not in selectors:
        raise ValueError("unknown rival selector")
    source = program_text("dominant_relay")
    if source.count("(mode base 0)") != 1:
        raise ValueError("relay selector replacement is ambiguous")
    return source.replace("(mode base 0)", selectors[selector], 1)
