"""Native quarter-turn family for fa3550d200a0.

Inputs come from the approved production sampler. Labels are computed by an
independent Python transform; native qualification replays them in protected
Racket against every declared program.
"""
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
DEMO_LIMIT = 6
QUERY_LIMIT = 4
CANONICAL_PATH = Path(__file__).resolve().with_name("canonical.rkt")
GENERATOR_PATH = Path(__file__).resolve().parents[2] / "generator.py"


def _load_generator():
    name = "_fa3550d200a0_native_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode()
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load production generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()


def _settings(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"quarter_turns"}:
        raise ValueError("settings must name exactly quarter_turns")
    turns = value["quarter_turns"]
    if type(turns) is not int or turns not in PARAMETER_VALUES:
        raise ValueError("quarter_turns must be an exact integer in {0,1,2,3}")
    return {"quarter_turns": turns}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low},{high}]")
    return value


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError("canonical.rkt is not a rule program")
    return source


def _instantiate(canonical: str, turns: int) -> str:
    if turns == 0:
        return canonical
    old_row = "(nr (+ mr (- (fst cell) sr)))"
    old_col = "(nc (+ mc (- (snd cell) scc2)))"
    if canonical.count(old_row) != 1 or canonical.count(old_col) != 1:
        raise ValueError("canonical coordinate sites changed; refusing rewrite")
    row_offset, col_offset = {
        1: ("(- (snd cell) scc2)", "(- (- (fst cell) sr))"),
        2: ("(- (- (fst cell) sr))", "(- (- (snd cell) scc2))"),
        3: ("(- (- (snd cell) scc2))", "(- (fst cell) sr)"),
    }[turns]
    return canonical.replace(old_row, f"(nr (+ mr {row_offset}))").replace(
        old_col, f"(nc (+ mc {col_offset}))"
    )


def program(settings: dict[str, int]) -> str:
    chosen = _settings(settings)["quarter_turns"]
    return _instantiate(_canonical(), chosen)


def _features(grid: list[list[int]]):
    features, errors = _GENERATOR._analyze(grid)
    if errors:
        raise ValueError("input leaves production domain: " + "; ".join(errors))
    return features


def analyze_input(grid: list[list[int]]) -> dict[str, int]:
    features = _features(grid)
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "canvas_h": features["canvas_h"],
        "canvas_w": features["canvas_w"],
        "piece_count": features["piece_count"],
        "decoy_count": features["decoy_count"],
    }


def _rotated_offset(dr: int, dc: int, turns: int) -> tuple[int, int]:
    for _ in range(turns):
        dr, dc = dc, -dr
    return dr, dc


def rotation_domain_errors(grid: list[list[int]]) -> list[str]:
    try:
        features = _features(grid)
    except ValueError as error:
        return [str(error)]
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
                dr, dc = _rotated_offset(row - sr, col - sc, turns)
                target = ar + dr, ac + dc
                if not (top <= target[0] <= bottom and left <= target[1] <= right):
                    result.append(f"turn {turns}: piece {piece_index} outside canvas at {target}")
                if target in owners and owners[target] != piece_index:
                    result.append(f"turn {turns}: overlapping piece footprints at {target}")
                owners[target] = piece_index
    return sorted(set(result))


def native_transform(grid: list[list[int]], quarter_turns: int) -> list[list[int]]:
    if type(quarter_turns) is not int or quarter_turns not in PARAMETER_VALUES:
        raise ValueError("quarter_turns must be an exact integer in {0,1,2,3}")
    features = _features(grid)
    errors = rotation_domain_errors(grid)
    if errors:
        raise ValueError("input is not valid for every declared rotation: " + "; ".join(errors))
    top, left, bottom, right = features["canvas_bbox"]
    output = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    for role, marker, cells, _targets in features["piece_records"]:
        if role != "matched":
            continue
        sr, sc, _value = next(cell for cell in cells if cell[2] == marker)
        ar, ac = features["marker_positions"][marker][0]
        for row, col, value in cells:
            dr, dc = _rotated_offset(row - sr, col - sc, quarter_turns)
            output[ar + dr - top][ac + dc - left] = value
    return output


def _fingerprint(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _candidate(seed: int, sample_index: int, *, stress: bool = False) -> list[list[int]]:
    overrides = {}
    if stress:
        overrides = {
            "grid_h": 30,
            "grid_w": 30,
            "rect_h": 12,
            "rect_w": 12,
            "piece_count": 2,
            "decoy_count": 1,
        }
    return _GENERATOR.generate(seed, sample_index, difficulty="hard", **overrides)


def _build_input_pool(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    accepted: set[str] = set()
    demos: list[list[list[int]]] = []
    queries: list[list[list[int]]] = []

    sample_index = 0
    while len(demos) < DEMO_LIMIT and sample_index < 4000:
        try:
            grid = _candidate(seed, sample_index)
        except RuntimeError:
            sample_index += 1
            continue
        sample_index += 1
        fingerprint = _fingerprint(grid)
        if fingerprint in accepted or rotation_domain_errors(grid):
            continue
        outputs = [native_transform(grid, turns) for turns in PARAMETER_VALUES]
        if len({_fingerprint(output) for output in outputs}) != len(PARAMETER_VALUES):
            continue
        accepted.add(fingerprint)
        demos.append(grid)
    if len(demos) != DEMO_LIMIT:
        raise RuntimeError("could not construct six universal quarter-turn demonstrations")

    sample_index = 10000
    while len(queries) < QUERY_LIMIT - 1 and sample_index < 14000:
        try:
            grid = _candidate(seed, sample_index)
        except RuntimeError:
            sample_index += 1
            continue
        sample_index += 1
        fingerprint = _fingerprint(grid)
        if fingerprint in accepted or rotation_domain_errors(grid):
            continue
        accepted.add(fingerprint)
        queries.append(grid)
    if len(queries) != QUERY_LIMIT - 1:
        raise RuntimeError("could not construct three regular quarter-turn queries")

    sample_index = 20000
    while sample_index < 24000:
        try:
            grid = _candidate(seed, sample_index, stress=True)
        except RuntimeError:
            sample_index += 1
            continue
        sample_index += 1
        fingerprint = _fingerprint(grid)
        if fingerprint in accepted or rotation_domain_errors(grid):
            continue
        features = analyze_input(grid)
        if features["canvas_h"] < 8 or features["canvas_w"] < 8:
            continue
        accepted.add(fingerprint)
        queries.append(grid)
        break
    if len(queries) != QUERY_LIMIT:
        raise RuntimeError("could not construct the exact 30x30 quarter-turn stress query")
    return demos, queries


def generate(
    seed: int,
    settings: dict[str, int],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    turns = _settings(settings)["quarter_turns"]
    _integer("demos", demos, 2, DEMO_LIMIT)
    _integer("queries", queries, 1, QUERY_LIMIT)
    demo_inputs, query_inputs = _build_input_pool(seed)
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": native_transform(grid, turns)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": native_transform(grid, turns)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program({"quarter_turns": turns}),
    }


def teaching_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    survivors = [
        turns
        for turns in PARAMETER_VALUES
        if all(native_transform(pair["input"], turns) == pair["output"] for pair in episode["train"])
    ]
    return {"setting_survivors": survivors, "demonstrations_checked": len(episode["train"])}


def _offsets_for_first_asymmetric_piece(grid: list[list[int]], turns: int) -> list[list[int]]:
    features = _features(grid)
    for role, marker, cells, _targets in features["piece_records"]:
        if role != "matched":
            continue
        sr, sc, _value = next(cell for cell in cells if cell[2] == marker)
        base = sorted((row - sr, col - sc) for row, col, _value in cells)
        quarter_turned = sorted(_rotated_offset(dr, dc, 1) for dr, dc in base)
        if quarter_turned != base:
            requested = sorted(_rotated_offset(dr, dc, turns) for dr, dc in base)
            return [[dr, dc] for dr, dc in requested]
    raise RuntimeError("no asymmetric matched piece in dependency witness input")


def dependency_witness() -> dict[str, Any]:
    episode = generate(0, {"quarter_turns": 1}, 2, 1)
    grid = episode["train"][0]["input"]
    return {
        "settings": {"quarter_turns": 1},
        "ablation": "wrong_intermediate",
        "input": copy.deepcopy(grid),
        "intermediate_value": _offsets_for_first_asymmetric_piece(grid, 1),
        "wrong_intermediate_value": _offsets_for_first_asymmetric_piece(grid, 0),
        "output": native_transform(grid, 1),
        "counterfactual_output": native_transform(grid, 0),
        "step_a": "extract each matched piece's marker-relative payload offsets",
        "step_b": "rotate those offsets and stamp them at the matching canvas marker",
        "why_b_depends_on_a": "the target cells are computed from the rotated offset set",
    }
