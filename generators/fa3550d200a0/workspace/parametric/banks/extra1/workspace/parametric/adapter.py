"""Native finite quarter-turn family for ARC task fa3550d200a0."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "fa3550d200a0"
PARAMETER_VALUES = (0, 1, 2, 3)
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")


def _load_generator():
    path = _TASK_HOME / "generator.py"
    name = "_parametric_source_fa3550d200a0"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()


def _turns(settings: dict[str, Any]) -> int:
    if type(settings) is not dict or set(settings) != {"quarter_turns"}:
        raise ValueError("settings must name exactly quarter_turns")
    value = settings["quarter_turns"]
    if type(value) is not int or value not in PARAMETER_VALUES:
        raise ValueError("quarter_turns must be an exact integer in {0,1,2,3}")
    return value


def program(settings: dict[str, Any]) -> str:
    """Materialize the exact canonical rule or one reviewed offset rotation."""
    turns = _turns(settings)
    if turns == 0:
        return _CANONICAL
    old_row = "(nr (+ mr (- (fst cell) sr)))"
    old_col = "(nc (+ mc (- (snd cell) scc2)))"
    if _CANONICAL.count(old_row) != 1 or _CANONICAL.count(old_col) != 1:
        raise RuntimeError("canonical coordinate sites changed; refusing unsafe rewrite")
    row_offset, col_offset = {
        1: ("(- (snd cell) scc2)", "(- (- (fst cell) sr))"),
        2: ("(- (- (fst cell) sr))", "(- (- (snd cell) scc2))"),
        3: ("(- (- (snd cell) scc2))", "(- (fst cell) sr)"),
    }[turns]
    return _CANONICAL.replace(old_row, f"(nr (+ mr {row_offset}))").replace(
        old_col, f"(nc (+ mc {col_offset}))"
    )


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def _digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _rotate(dr: int, dc: int, turns: int) -> tuple[int, int]:
    for _ in range(turns):
        dr, dc = dc, -dr
    return dr, dc


def _rotation_domain_errors(grid: list[list[int]]) -> list[str]:
    features, errors = _GENERATOR._analyze(grid)
    if errors:
        return ["canonical domain: " + error for error in errors]
    top, left, bottom, right = features["canvas_bbox"]
    result: list[str] = []
    for turns in PARAMETER_VALUES:
        owners: dict[tuple[int, int], int] = {}
        for piece_index, (role, marker, cells, _targets) in enumerate(features["piece_records"]):
            if role != "matched":
                continue
            sr, sc, _value = next(cell for cell in cells if cell[2] == marker)
            ar, ac = features["marker_positions"][marker][0]
            for row, col, _value in cells:
                dr, dc = _rotate(row - sr, col - sc, turns)
                target = (ar + dr, ac + dc)
                if not (top <= target[0] <= bottom and left <= target[1] <= right):
                    result.append(f"turn {turns}: piece {piece_index} outside canvas at {target}")
                prior = owners.get(target)
                if prior is not None and prior != piece_index:
                    result.append(f"turn {turns}: overlapping piece footprints at {target}")
                owners[target] = piece_index
    return sorted(set(result))


def _predict(grid: list[list[int]], turns: int) -> list[list[int]]:
    features, errors = _GENERATOR._analyze(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    top, left, bottom, right = features["canvas_bbox"]
    out = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    for role, marker, cells, _targets in features["piece_records"]:
        if role != "matched":
            continue
        sr, sc, _value = next(cell for cell in cells if cell[2] == marker)
        ar, ac = features["marker_positions"][marker][0]
        for row, col, value in cells:
            dr, dc = _rotate(row - sr, col - sc, turns)
            nr, nc = ar + dr - top, ac + dc - left
            if not (0 <= nr < len(out) and 0 <= nc < len(out[0])):
                raise ValueError("rotated stamp left the accepted canvas domain")
            out[nr][nc] = value
    return out


_DEMO_PROFILES = (
    dict(grid_h=24, grid_w=26, piece_count=5, decoy_count=1, rect_h=12, rect_w=12, canvas_side="left"),
    dict(grid_h=26, grid_w=28, piece_count=5, decoy_count=0, rect_h=12, rect_w=12, canvas_side="right"),
    dict(grid_h=22, grid_w=24, piece_count=4, decoy_count=1, rect_h=10, rect_w=12, canvas_side="left"),
    dict(grid_h=28, grid_w=30, piece_count=5, decoy_count=1, rect_h=11, rect_w=12, canvas_side="right"),
    dict(grid_h=20, grid_w=24, piece_count=4, decoy_count=0, rect_h=10, rect_w=12, canvas_side="left"),
    dict(grid_h=30, grid_w=28, piece_count=5, decoy_count=1, rect_h=12, rect_w=12, canvas_side="right"),
)

_QUERY_PROFILES = (
    dict(grid_h=30, grid_w=30, piece_count=5, decoy_count=1, rect_h=12, rect_w=12, canvas_side="left"),
    dict(grid_h=16, grid_w=18, piece_count=2, decoy_count=0, rect_h=6, rect_w=8, canvas_side="right"),
    dict(grid_h=24, grid_w=26, piece_count=4, decoy_count=1, rect_h=10, rect_w=12, canvas_side="right"),
    dict(grid_h=28, grid_w=24, piece_count=3, decoy_count=0, rect_h=11, rect_w=12, canvas_side="left"),
)


def _draw(seed: int, sample_index: int, profile: dict[str, Any]) -> list[list[int]]:
    return _GENERATOR.generate(seed, sample_index, **profile)


def _distinct_turn_outputs(grid: list[list[int]]) -> bool:
    return len({_digest(_predict(grid, turns)) for turns in PARAMETER_VALUES}) == len(PARAMETER_VALUES)


def _accepted_input(
    *, seed: int, profile: dict[str, Any], slot: int, demo: bool, seen: set[str]
) -> list[list[int]]:
    # Even indices retain the generator's endpoint/diagonal teaching schedule.
    base = (0 if demo else 1_000_000) + slot * 10_000
    for attempt in range(2_000):
        sample_index = base + attempt * 2
        try:
            grid = _draw(seed, sample_index, profile)
        except RuntimeError:
            continue
        digest = _digest(grid)
        if digest in seen or _rotation_domain_errors(grid):
            continue
        if demo and not _distinct_turn_outputs(grid):
            continue
        seen.add(digest)
        return grid
    phase = "demonstration" if demo else "query"
    raise RuntimeError(f"bounded {phase} sampling exhausted for slot {slot}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Build deterministic setting-independent inputs and setting-private labels."""
    turns = _turns(settings)
    _validate_request(seed, demos, queries)
    seen: set[str] = set()
    train = []
    for slot, profile in enumerate(_DEMO_PROFILES[:demos]):
        grid = _accepted_input(seed=seed, profile=profile, slot=slot, demo=True, seen=seen)
        train.append({"input": copy.deepcopy(grid), "output": _predict(grid, turns)})
    test = []
    for slot, profile in enumerate(_QUERY_PROFILES):
        grid = _accepted_input(seed=seed, profile=profile, slot=slot, demo=False, seen=seen)
        test.append({"input": copy.deepcopy(grid), "output": _predict(grid, turns)})
    return {"train": train, "test": test, "program_solution": program(settings)}
