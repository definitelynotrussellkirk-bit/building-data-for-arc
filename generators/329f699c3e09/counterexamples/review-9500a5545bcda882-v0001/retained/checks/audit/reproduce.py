#!/usr/bin/env python3
"""Replay the two source-bound audit findings in this review return.

Run from the packet root with:
    python3 review.py run python3 ../checks/audit/reproduce.py

The script replays generator/validator behavior and verifies the retained Racket
apply receipts. It does not modify either audited task.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPO = Path.cwd()
CHECKS = REPO.parent / "checks" / "audit"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_receipt(task_id: str, probe: dict[str, Any]) -> dict[str, Any]:
    receipt = read_json(CHECKS / task_id / "racket.json")
    result = receipt["results"][0]
    authority = probe["authority"]
    assert receipt["task_id"] == task_id
    assert receipt["generator_sha256"] == probe["generator_sha256"]
    assert receipt["executed_rule_hash"] == authority["executed_rule_hash"]
    assert receipt["rule_text_sha256"] == authority["rule_text_sha256"]
    assert result["input_sha256"] == authority["input_sha256"]
    assert result["output_sha256"] == authority["output_sha256"]
    assert result["output"] == authority["output"]
    return receipt


def replay_8586() -> None:
    task_id = "8586bc0f2889"
    probe = read_json(CHECKS / task_id / "probe.json")
    path, generator = load_generator(task_id)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == probe["generator_sha256"]

    forced = probe["forced_generation"]
    grid = generator.generate(
        forced["seed"],
        forced["sample_index"],
        difficulty=forced["difficulty"],
        **forced["overrides"],
    )
    assert grid == forced["input"]
    assert generator.self_check(grid) == []
    colors = sorted({cell for row in grid for cell in row if cell})
    assert colors == forced["nonzero_colors"] == [1, 8]

    try:
        generator.generate(0, 0, grid_h=5, grid_w=5)
    except ValueError as exc:
        assert str(exc) in probe["advertised_dimension_probe"]["exception"]
    else:
        raise AssertionError("advertised 5x5 dimension unexpectedly succeeded")

    blob = probe["validator_counterexample"]["input"]
    assert generator.self_check(blob) == []
    verify_receipt(task_id, probe)
    print(f"PASS {task_id}: ignored controls, dimension mismatch, and blob validator hole reproduced")


def preserve_occupied_rival(grid: list[list[int]]) -> list[list[int]]:
    result = [row[:] for row in grid]
    divider_rows = [r for r, row in enumerate(grid) if row and all(cell == 7 for cell in row)]
    assert len(divider_rows) == 1
    divider = divider_rows[0]
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != 6:
                continue
            target = 2 * divider - r
            if 0 <= target < len(grid) and result[target][c] == 0:
                result[target][c] = 8
    return result


def replay_329f() -> None:
    task_id = "329f699c3e09"
    probe = read_json(CHECKS / task_id / "probe.json")
    path, generator = load_generator(task_id)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == probe["generator_sha256"]

    grid = generator.generate(
        probe["seed"], probe["sample_index"], difficulty=probe["difficulty"]
    )
    assert grid == probe["input"]
    assert generator.self_check(grid) == []
    assert probe["collisions"] == [
        {"source": [0, 3], "destination": [6, 3], "occupied_color": 4}
    ]

    receipt = verify_receipt(task_id, probe)
    authority = receipt["results"][0]["output"]
    rival = preserve_occupied_rival(grid)
    assert rival == probe["rival"]["output"]
    assert probe["rival"]["canonical_pairs_checked"] == 5
    assert probe["rival"]["canonical_pairs_matched"] == 5
    assert authority[6][3] == 8 and rival[6][3] == 4
    assert probe["difference_cells"] == [[6, 3, 8, 4]]
    print(f"PASS {task_id}: occupied reflection collision and canonical-fitting rival reproduced")


def main() -> None:
    replay_8586()
    replay_329f()


if __name__ == "__main__":
    main()
