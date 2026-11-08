#!/usr/bin/env python3
"""Rebuild the two audit probes without mutating either audit target."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_l_tromino_windows(grid: list[list[int]]) -> int:
    count = 0
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            block = (
                grid[row][col],
                grid[row][col + 1],
                grid[row + 1][col],
                grid[row + 1][col + 1],
            )
            nonzero = [value for value in block if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                count += 1
    return count


def turn(delta: tuple[int, int], quarter_turns: int) -> tuple[int, int]:
    row, col = delta
    return (
        (row, col),
        (col, -row),
        (-row, -col),
        (-col, row),
    )[quarter_turns]


def canvas_center_rival(grid: list[list[int]]) -> list[list[int]]:
    """Rotate source around canvas center while treating the gray cell as decoration."""
    height, width = len(grid), len(grid[0])
    legend = tuple(grid[0][:4])
    pivots = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    if len(pivots) != 1:
        raise ValueError("expected one gray pivot")
    pivot = pivots[0]
    source = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    center = (height // 2, width // 2)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for col, color in enumerate(legend):
        output[0][col] = color
    output[pivot[0]][pivot[1]] = 5
    for quarter_turns, color in enumerate(legend):
        for row, col in source:
            delta = (row - center[0], col - center[1])
            delta_row, delta_col = turn(delta, quarter_turns)
            target = (center[0] + delta_row, center[1] + delta_col)
            if 0 <= target[0] < height and 0 <= target[1] < width:
                output[target[0]][target[1]] = color
    return output


def load_racket(task_id: str) -> dict[str, Any]:
    path = ROOT / "checks" / "audit" / task_id / "racket.json"
    return json.loads(path.read_text())


def canonical_center_facts(task_id: str) -> list[dict[str, Any]]:
    catalog = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    row = None
    for line in catalog.read_text().splitlines():
        candidate = json.loads(line)
        if candidate.get("task_id") == task_id:
            row = candidate
            break
    if row is None:
        raise RuntimeError(f"canonical row not found: {task_id}")

    facts: list[dict[str, Any]] = []
    for split in ("train", "test"):
        pairs = row.get(split, [])
        if isinstance(pairs, dict):
            pairs = [pairs]
        for index, pair in enumerate(pairs):
            raw = pair["input"]
            grid = [[int(value) for value in line] for line in raw] if raw and isinstance(raw[0], str) else raw
            pivots = [
                (r, c)
                for r in range(1, len(grid))
                for c in range(len(grid[0]))
                if grid[r][c] == 5
            ]
            facts.append(
                {
                    "split": split,
                    "index": index,
                    "shape": [len(grid), len(grid[0])],
                    "pivot": list(pivots[0]) if len(pivots) == 1 else None,
                    "canvas_center": [len(grid) // 2, len(grid[0]) // 2],
                    "pivot_equals_canvas_center": len(pivots) == 1
                    and pivots[0] == (len(grid) // 2, len(grid[0]) // 2),
                }
            )
    return facts


def build_0d() -> None:
    task_id = "0d655a5e1a2d"
    module, generator_path = load_generator(task_id)
    racket = load_racket(task_id)
    single_l = json.loads((ROOT / "checks" / "audit" / task_id / "input.json").read_text())
    seed, sample_index = "audit-n-l", 0
    one = module.generate(seed, sample_index, n_l=1)
    four = module.generate(seed, sample_index, n_l=4)
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "classification": "reproduced defect",
        "generator_path": f"repo/generators/{task_id}/generator.py",
        "generator_sha256": sha256(generator_path),
        "rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "documented_invariant": "at least 2 L-tromino patterns",
        "input": single_l,
        "passes_target_validator": module.self_check(single_l) == [],
        "validator_errors": module.self_check(single_l),
        "belongs_documented_generator_domain": False,
        "observed_l_tromino_windows": count_l_tromino_windows(single_l),
        "actual_racket_output": racket["results"][0]["output"],
        "actual_racket_output_valid": racket["results"][0]["valid_output"],
        "override_probe": {
            "seed": seed,
            "sample_index": sample_index,
            "overrides_a": {"n_l": 1},
            "overrides_b": {"n_l": 4},
            "outputs_equal": one == four,
            "observed_l_tromino_windows_a": count_l_tromino_windows(one),
            "observed_l_tromino_windows_b": count_l_tromino_windows(four),
        },
        "racket_command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "-m",
            "arcpuzzles",
            "apply",
            task_id,
            "--input",
            f"../checks/audit/{task_id}/input.json",
            "--out",
            f"../checks/audit/{task_id}/racket.json",
        ],
        "racket_command_cwd": "packet_root",
        "probe_command": ["python3", "checks/audit_probe.py"],
        "probe_command_cwd": "packet_root",
    }
    path = ROOT / "checks" / "audit" / task_id / "counterexample.json"
    path.write_text(json.dumps(report, indent=2) + "\n")


def build_a02() -> None:
    task_id = "a02bd9f85082"
    module, generator_path = load_generator(task_id)
    racket = load_racket(task_id)
    grid = json.loads((ROOT / "checks" / "audit" / task_id / "input.json").read_text())
    rival = canvas_center_rival(grid)
    actual = racket["results"][0]["output"]
    differences = [
        [row, col, actual[row][col], rival[row][col]]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if actual[row][col] != rival[row][col]
    ]
    pivots = [
        (row, col)
        for row in range(1, len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 5
    ]
    canonical = canonical_center_facts(task_id)
    generated = []
    for scene_family in ("linked", "generalized"):
        for sample_index in range(10):
            sample = module.generate(0, sample_index, scene_family=scene_family)
            sample_pivots = [
                (row, col)
                for row in range(1, len(sample))
                for col in range(len(sample[0]))
                if sample[row][col] == 5
            ]
            generated.append(
                {
                    "seed": 0,
                    "sample_index": sample_index,
                    "scene_family": scene_family,
                    "shape": [len(sample), len(sample[0])],
                    "pivot": list(sample_pivots[0]),
                    "canvas_center": [len(sample) // 2, len(sample[0]) // 2],
                    "pivot_equals_canvas_center": sample_pivots[0]
                    == (len(sample) // 2, len(sample[0]) // 2),
                }
            )
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "classification": "suspected shortcut / domain gap",
        "generator_path": f"repo/generators/{task_id}/generator.py",
        "generator_sha256": sha256(generator_path),
        "rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "reproducer_origin": {
            "seed": 0,
            "sample_index": 0,
            "overrides": {"scene_family": "generalized"},
            "transformation": "translate pivot and source one cell left; keep legend and canvas fixed",
        },
        "input": grid,
        "passes_target_validator": module.self_check(grid) == [],
        "validator_errors": module.self_check(grid),
        "belongs_documented_generator_domain": True,
        "canvas_center": [len(grid) // 2, len(grid[0]) // 2],
        "gray_pivot": list(pivots[0]),
        "actual_racket_output": actual,
        "rival_name": "rotate around canvas center and ignore gray pivot location",
        "rival_output": rival,
        "difference_count": len(differences),
        "difference_examples": differences[:24],
        "canonical_pivot_probe": {
            "pairs_checked": len(canonical),
            "all_pivots_at_canvas_center": all(
                item["pivot_equals_canvas_center"] for item in canonical
            ),
            "pairs": canonical,
        },
        "generated_pivot_probe": {
            "samples_checked": len(generated),
            "seed": 0,
            "sample_indices": list(range(10)),
            "scene_families": ["linked", "generalized"],
            "all_pivots_at_canvas_center": all(
                item["pivot_equals_canvas_center"] for item in generated
            ),
            "samples": generated,
        },
        "racket_command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "-m",
            "arcpuzzles",
            "apply",
            task_id,
            "--input",
            f"../checks/audit/{task_id}/input.json",
            "--out",
            f"../checks/audit/{task_id}/racket.json",
        ],
        "racket_command_cwd": "packet_root",
        "probe_command": ["python3", "checks/audit_probe.py"],
        "probe_command_cwd": "packet_root",
    }
    path = ROOT / "checks" / "audit" / task_id / "counterexample.json"
    path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    build_0d()
    build_a02()
    print("wrote audit counterexamples for 0d655a5e1a2d and a02bd9f85082")
