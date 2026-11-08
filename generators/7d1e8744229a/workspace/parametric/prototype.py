"""Cue-directed symbolic expansion with a source-faithful canonical default."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

TASK_ID = "7d1e8744229a"
HOME = Path(__file__).resolve().parent
ROOT = next(
    parent for parent in HOME.parents
    if (parent / "generators" / TASK_ID / "generator.py").is_file()
    and (parent / "shared" / "runtime").is_dir()
)
MODES = ("canonical", "cue_rotate_erase")
CUE_POSITIONS = ((0, 2), (2, 4), (4, 2), (2, 0))
DEMO_CUES = CUE_POSITIONS + CUE_POSITIONS[:2]
QUERY_CUES = ((4, 2), (2, 0), (0, 2), (2, 4))


def _load_base():
    path = ROOT / "generators" / TASK_ID / "generator.py"
    name = "_arc_7d_base_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return value


def program_for(mode: str) -> str:
    mode = _mode(mode)
    name = "canonical.rkt" if mode == "canonical" else "cue_rotate_erase.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def _validate_input(grid: Any) -> tuple[int, int, int, tuple[int, int]]:
    base = _load_base()
    if type(grid) is not list or len(grid) != 5 or any(type(row) is not list or len(row) != 5 for row in grid):
        raise ValueError("input must be an exact 5x5 list grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    zeros = [(r, c) for r in range(5) for c in range(5) if grid[r][c] == 0]
    if len(zeros) != 1 or zeros[0] not in CUE_POSITIONS:
        raise ValueError("input needs exactly one zero cue at an allowed edge midpoint")
    roles = (grid[0][0], grid[0][1], grid[2][2])
    if any(value == 0 for value in roles) or len(set(roles)) != 3:
        raise ValueError("three anchor roles must be distinct nonzero colors")
    cue = zeros[0]
    for r, row in enumerate(base.INPUT_TEMPLATE):
        for c, symbol in enumerate(row):
            if (r, c) == cue:
                continue
            if grid[r][c] != roles[symbol]:
                raise ValueError("non-cue cells must match the canonical symbolic seed")
    return (*roles, cue)


def canonical_expand(grid: list[list[int]]) -> list[list[int]]:
    a, b, c, _ = _validate_input(grid)
    colors = (a, b, c)
    return [[colors[symbol] for symbol in row] for row in _load_base().OUTPUT_TEMPLATE]


def cue_turns(grid: list[list[int]]) -> int:
    *_, cue = _validate_input(grid)
    return CUE_POSITIONS.index(cue)


def _rotate_cw(grid: list[list[int]], turns: int) -> list[list[int]]:
    out = deepcopy(grid)
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def rotated_intermediate(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_cw(canonical_expand(grid), cue_turns(grid))


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


def north_component(intermediate: list[list[int]]) -> set[tuple[int, int]]:
    if len(intermediate) != 10 or any(len(row) != 10 for row in intermediate):
        raise ValueError("intermediate must be 10x10")
    return _component(intermediate, (0, 1))


def _erase_component(intermediate: list[list[int]], component: set[tuple[int, int]]) -> list[list[int]]:
    out = deepcopy(intermediate)
    for row, col in component:
        out[row][col] = 0
    return out


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = _mode(mode)
    if mode == "canonical":
        return canonical_expand(grid)
    intermediate = rotated_intermediate(grid)
    return _erase_component(intermediate, north_component(intermediate))


def _digest(seed: int, split: str, index: int, attempt: int) -> int:
    raw = f"{TASK_ID}|cue-v1|{seed}|{split}|{index}|{attempt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & 0x7FFFFFFF


def _candidate(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    base = _load_base()
    cue = (DEMO_CUES if split == "demo" else QUERY_CUES)[index]
    generated = base.generate(
        _digest(seed, split, index, attempt),
        index + attempt * 17,
        difficulty=("easy", "medium", "hard")[(index + attempt) % 3],
    )
    grid = deepcopy(generated)
    grid[cue[0]][cue[1]] = 0
    _validate_input(grid)
    return grid


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    seen: set[str] = set()
    result: dict[str, list[list[list[int]]]] = {"train": [], "test": []}
    for split, count in (("demo", len(DEMO_CUES)), ("query", len(QUERY_CUES))):
        key = "train" if split == "demo" else "test"
        for index in range(count):
            for attempt in range(256):
                grid = _candidate(seed, split, index, attempt)
                digest = json.dumps(grid, separators=(",", ":"))
                if digest in seen:
                    continue
                seen.add(digest)
                result[key].append(grid)
                break
            else:
                raise RuntimeError("could not construct distinct cue input")
    return result


def generate_episode(seed: int, mode: str, *, demos: int = 4, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    mode = _mode(mode)
    _exact_int(demos, "demos", 4, 6)
    _exact_int(queries, "queries", 1, 4)
    inputs = episode_inputs(seed)
    train = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["train"][:demos]]
    test = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["test"][:queries]]
    return {"train": train, "test": test, "program_solution": program_for(mode)}


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


def _rotate_only(grid: list[list[int]]) -> list[list[int]]:
    return rotated_intermediate(grid)


def _erase_anchor_cell_only(grid: list[list[int]]) -> list[list[int]]:
    out = rotated_intermediate(grid)
    out[0][1] = 0
    return out


def _erase_all_target_color(grid: list[list[int]]) -> list[list[int]]:
    intermediate = rotated_intermediate(grid)
    color = intermediate[0][1]
    return [[0 if value == color else value for value in row] for row in intermediate]


def _ccw_then_erase(grid: list[list[int]]) -> list[list[int]]:
    intermediate = _rotate_cw(canonical_expand(grid), -cue_turns(grid))
    return _erase_component(intermediate, north_component(intermediate))


def _fixed_then_erase(grid: list[list[int]]) -> list[list[int]]:
    intermediate = canonical_expand(grid)
    return _erase_component(intermediate, north_component(intermediate))


def rival_outputs(grid: list[list[int]], intended_mode: str) -> dict[str, list[list[int]]]:
    intended_mode = _mode(intended_mode)
    other = MODES[1] if intended_mode == MODES[0] else MODES[0]
    return {
        f"other_setting:{other}": solve(grid, other),
        "rotate_only": _rotate_only(grid),
        "erase_anchor_cell_only": _erase_anchor_cell_only(grid),
        "erase_all_target_color": _erase_all_target_color(grid),
        "counterclockwise_then_erase": _ccw_then_erase(grid),
        "fixed_no_rotation_then_erase": _fixed_then_erase(grid),
    }


def teaching_certificate(episode: dict[str, Any], intended_mode: str) -> dict[str, Any]:
    intended_mode = _mode(intended_mode)
    train, test = episode["train"], episode["test"]
    names = sorted(rival_outputs(train[0]["input"], intended_mode))
    survivors = []
    query_changing = []
    for name in names:
        fits = all(rival_outputs(pair["input"], intended_mode)[name] == pair["output"] for pair in train)
        if fits:
            survivors.append(name)
            if any(rival_outputs(pair["input"], intended_mode)[name] != pair["output"] for pair in test):
                query_changing.append(name)
    return {
        "rivals_checked": len(names),
        "surviving_rivals": survivors,
        "query_changing_survivors": query_changing,
    }
