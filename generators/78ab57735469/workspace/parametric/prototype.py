"""Phase-controlled kaleidoscope tiling with an optional sequential erasure."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "78ab57735469"
HOME = Path(__file__).resolve().parent
PHASES = ("even", "odd")
FINISHES = ("tile_only", "erase_center_component")
SETTINGS = tuple((row, column, finish) for row in PHASES for column in PHASES for finish in FINISHES)
DEFAULT_SETTING = ("even", "even", "tile_only")
DEMO_SIDES = (3, 4, 5, 6, 8, 9)
QUERY_SIDES = (4, 7, 8, 10)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _phase(value: Any, name: str) -> str:
    if type(value) is not str or value not in PHASES:
        raise ValueError(f"{name} must be one of {PHASES}")
    return value


def _finish(value: Any) -> str:
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _setting(row: Any, column: Any, finish: Any) -> tuple[str, str, str]:
    return _phase(row, "row_flip_phase"), _phase(column, "column_flip_phase"), _finish(finish)


def _canonical_program() -> str:
    return (HOME / "rules" / "canonical.rkt").read_text(encoding="utf-8")


def _phase_expr(axis: str, phase: str) -> str:
    block = "br" if axis == "row" else "bc"
    local = "lr" if axis == "row" else "lc"
    predicate = "even?" if phase == "even" else "odd?"
    return f"(if ({predicate} {block}) (- n 1 {local}) {local})"


def _generated_program(row: str, column: str, finish: str) -> str:
    row_expr = _phase_expr("row", row)
    col_expr = _phase_expr("column", column)
    if finish == "tile_only":
        return (
            "(rule! (lambda (g)\n"
            "         (let ((n (rows g)))\n"
            "           (build-grid (* 3 n)\n"
            "                       (* 3 n)\n"
            "                       (r c)\n"
            "                       (let ((br (quotient r n))\n"
            "                             (bc (quotient c n))\n"
            "                             (lr (mod r n))\n"
            "                             (lc (mod c n)))\n"
            "                         (at g\n"
            f"                             {row_expr}\n"
            f"                             {col_expr})))))))"
        )
    return (
        "(rule! (lambda (g)\n"
        "  (let* ((n (rows g))\n"
        "         (intermediate\n"
        "          (build-grid (* 3 n) (* 3 n) (r c)\n"
        "            (let ((br (quotient r n))\n"
        "                  (bc (quotient c n))\n"
        "                  (lr (mod r n))\n"
        "                  (lc (mod c n)))\n"
        "              (at g\n"
        f"                  {row_expr}\n"
        f"                  {col_expr}))))\n"
        "         (target\n"
        "          (first\n"
        "           (filter\n"
        "            (lambda (obj) (member? (list n n) (obj-cells obj)))\n"
        "            (objects intermediate 0)))))\n"
        "    (paint-cells intermediate (obj-cells target) 0))))"
    )


def program_for(row_flip_phase: str, column_flip_phase: str, finish: str) -> str:
    row, column, finish = _setting(row_flip_phase, column_flip_phase, finish)
    if (row, column, finish) == DEFAULT_SETTING:
        return _canonical_program()
    return _generated_program(row, column, finish)


def _validate_grid(grid: Any) -> int:
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a nonempty list of row lists")
    side = len(grid)
    if not 3 <= side <= 10 or any(len(row) != side for row in grid):
        raise ValueError("grid must be square with side 3..10")
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 1 <= value <= 9 for value in flat):
        raise ValueError("parametric tile colors must be exact nonzero ARC colors 1..9")
    if not 3 <= len(set(flat)) <= 5:
        raise ValueError("parametric tiles must use 3..5 colors")
    return side


def _matches(block_index: int, phase: str) -> bool:
    return block_index % 2 == (0 if phase == "even" else 1)


def tile_intermediate(grid: list[list[int]], row_flip_phase: str, column_flip_phase: str) -> list[list[int]]:
    row = _phase(row_flip_phase, "row_flip_phase")
    column = _phase(column_flip_phase, "column_flip_phase")
    side = _validate_grid(grid)
    return [
        [
            grid[
                side - 1 - (r % side) if _matches(r // side, row) else r % side
            ][
                side - 1 - (c % side) if _matches(c // side, column) else c % side
            ]
            for c in range(3 * side)
        ]
        for r in range(3 * side)
    ]


def _component(grid: list[list[int]], start: tuple[int, int]) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    color = grid[start[0]][start[1]]
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def _all_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {(r, c) for r in range(len(grid)) for c in range(len(grid[0]))}
    result = []
    while remaining:
        start = min(remaining)
        component = _component(grid, start)
        result.append(component)
        remaining -= component
    return result


def center_seam_component(intermediate: list[list[int]], side: int) -> set[tuple[int, int]]:
    if len(intermediate) != 3 * side or any(len(row) != 3 * side for row in intermediate):
        raise ValueError("intermediate shape does not match side")
    return _component(intermediate, (side, side))


def _erase(intermediate: list[list[int]], cells: set[tuple[int, int]]) -> list[list[int]]:
    out = deepcopy(intermediate)
    for row, col in cells:
        out[row][col] = 0
    return out


def solve(grid: list[list[int]], row_flip_phase: str, column_flip_phase: str, finish: str) -> list[list[int]]:
    row, column, finish = _setting(row_flip_phase, column_flip_phase, finish)
    side = _validate_grid(grid)
    intermediate = tile_intermediate(grid, row, column)
    if finish == "tile_only":
        return intermediate
    return _erase(intermediate, center_seam_component(intermediate, side))


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    raw = f"{TASK_ID}|component-v2|{seed}|{split}|{index}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big"))


def _make_candidate(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    side = (DEMO_SIDES if split == "demo" else QUERY_SIDES)[index]
    rng = _rng(seed, split, index, attempt)
    palette_size = 3 + rng.randrange(2)
    palette = rng.sample(range(1, 10), palette_size)
    corner, base, *accents = palette
    if not accents:
        accents = [palette[-1]]
    grid = [[base for _ in range(side)] for _ in range(side)]
    # Random asymmetric texture with an explicit nonzero grammar.
    for row in range(side):
        for col in range(side):
            if rng.random() < 0.42:
                grid[row][col] = rng.choice(accents)
    # All four source corners form the component selected at the central seam.
    for row, col in ((0, 0), (0, side - 1), (side - 1, 0), (side - 1, side - 1)):
        grid[row][col] = corner
    # A separated copy of the target color defeats "erase every target color".
    mid = side // 2
    grid[mid][mid] = corner
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = mid + dr, mid + dc
        if 0 <= nr < side and 0 <= nc < side:
            grid[nr][nc] = accents[(dr + 2 * dc) % len(accents)]
    # Force every palette color to appear at deterministic asymmetric cells.
    slots = [(0, 1), (1, 0), (1, side - 1), (side - 2, 0), (side - 1, side - 2)]
    for color, (row, col) in zip(palette[1:], slots):
        grid[row][col] = color
    _validate_grid(grid)
    return grid


def _largest_component(intermediate: list[list[int]]) -> set[tuple[int, int]]:
    return max(_all_components(intermediate), key=lambda cells: (len(cells), sorted(cells, reverse=True)))


def _shortcut_outputs(grid: list[list[int]], row: str, column: str) -> dict[str, list[list[int]]]:
    side = len(grid)
    intermediate = tile_intermediate(grid, row, column)
    target_color = intermediate[side][side]
    center_only = deepcopy(intermediate)
    center_only[side][side] = 0
    all_color = [[0 if value == target_color else value for value in line] for line in intermediate]
    largest = _erase(intermediate, _largest_component(intermediate))
    return {
        "erase_center_cell_only": center_only,
        "erase_all_target_color": all_color,
        "erase_largest_component": largest,
    }


def _usable(grid: list[list[int]]) -> bool:
    try:
        side = _validate_grid(grid)
        outputs = {setting: solve(grid, *setting) for setting in SETTINGS}
    except ValueError:
        return False
    if len({json.dumps(value, separators=(",", ":")) for value in outputs.values()}) != len(SETTINGS):
        return False
    for row in PHASES:
        for column in PHASES:
            intermediate = tile_intermediate(grid, row, column)
            component = center_seam_component(intermediate, side)
            if len(component) < 4:
                return False
            color = intermediate[side][side]
            if not any(intermediate[r][c] == color and (r, c) not in component for r in range(3 * side) for c in range(3 * side)):
                return False
            selected = solve(grid, row, column, "erase_center_component")
            if any(value == selected for value in _shortcut_outputs(grid, row, column).values()):
                return False
    return True


def make_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    profiles = DEMO_SIDES if split == "demo" else QUERY_SIDES if split == "query" else None
    if profiles is None:
        raise ValueError("split must be demo or query")
    _exact_int(index, "index", 0, len(profiles) - 1)
    for attempt in range(1024):
        grid = _make_candidate(seed, split, index, attempt)
        if _usable(grid):
            return grid
    raise RuntimeError(f"could not construct usable {split} input {index}")


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    train = [make_input(seed, "demo", index) for index in range(len(DEMO_SIDES))]
    test = [make_input(seed, "query", index) for index in range(len(QUERY_SIDES))]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("input bank is not distinct")
    return {"train": train, "test": test}


def generate_episode(
    seed: int,
    row_flip_phase: str,
    column_flip_phase: str,
    finish: str,
    *,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    row, column, finish = _setting(row_flip_phase, column_flip_phase, finish)
    _exact_int(demos, "demos", 3, 6)
    _exact_int(queries, "queries", 1, 4)
    inputs = episode_inputs(seed)
    train = [{"input": deepcopy(grid), "output": solve(grid, row, column, finish)} for grid in inputs["train"][:demos]]
    test = [{"input": deepcopy(grid), "output": solve(grid, row, column, finish)} for grid in inputs["test"][:queries]]
    return {"train": train, "test": test, "program_solution": program_for(row, column, finish)}


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or type(episode) is not dict:
        raise ValueError("invalid episode/query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("invalid episode/query index")
    query = {"input": deepcopy(test[query_index]["input"])}
    if query_index == 0:
        return {
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in train],
            "test": [query],
        }
    return {"test": [query]}


def rival_outputs(grid: list[list[int]], intended: tuple[str, str, str]) -> dict[str, list[list[int]]]:
    row, column, finish = _setting(*intended)
    result = {
        f"setting:{r}/{c}/{f}": solve(grid, r, c, f)
        for r, c, f in SETTINGS
        if (r, c, f) != (row, column, finish)
    }
    result.update(_shortcut_outputs(grid, row, column))
    return result


def teaching_certificate(episode: dict[str, Any], intended: tuple[str, str, str]) -> dict[str, Any]:
    intended = _setting(*intended)
    train, test = episode["train"], episode["test"]
    names = sorted(rival_outputs(train[0]["input"], intended))
    survivors = []
    query_changing = []
    for name in names:
        fits = all(rival_outputs(pair["input"], intended)[name] == pair["output"] for pair in train)
        if fits:
            survivors.append(name)
            if any(rival_outputs(pair["input"], intended)[name] != pair["output"] for pair in test):
                query_changing.append(name)
    return {
        "rivals_checked": len(names),
        "surviving_rivals": survivors,
        "query_changing_survivors": query_changing,
    }
