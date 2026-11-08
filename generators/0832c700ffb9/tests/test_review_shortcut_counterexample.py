"""Source-bound regression for the strongest canonical-fitting shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

try:
    from reviewer_support import find_root
except ModuleNotFoundError:  # direct source-tree pytest
    find_root = lambda path: Path(path).resolve().parents[3]

TASK_ID = "0832c700ffb9"
ASSIGNMENT_ID = "review-4c10bb8a426de6a4"
ROOT = find_root(__file__)
TASK_ROOT = ROOT / f"generators/{TASK_ID}"
RUNTIME_GENERATOR = ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
GENERATOR_PATH = RUNTIME_GENERATOR if RUNTIME_GENERATOR.is_file() else TASK_ROOT / "generator.py"
COUNTEREXAMPLE = (
    TASK_ROOT
    / "counterexamples"
    / ASSIGNMENT_ID
    / "first_rectangle_only.json"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "review_shortcut_generator_0832c700ffb9", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_sha256(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def test_first_rectangle_only_counterexample_is_lawful_replayable_and_decisive():
    assert COUNTEREXAMPLE.is_file(), "retained shortcut counterexample is missing"
    gen = _load_generator()
    record = json.loads(COUNTEREXAMPLE.read_text(encoding="utf-8"))
    grid = record["input"]
    intended = record["intended_output"]
    rival = record["rival_output"]

    assert record["schema"] == "arc-generator-counterexample-v1"
    assert record["assignment_id"] == ASSIGNMENT_ID
    assert record["task_id"] == gen.TASK_ID == TASK_ID
    assert record["rival_name"] == "first_rectangle_only"
    assert record["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert record["rule_hash"] == gen.RULE_HASH == "781d2d53fe4d"
    assert record["input_sha256"] == _grid_sha256(grid)
    assert record["intended_output_sha256"] == _grid_sha256(intended)
    assert record["rival_output_sha256"] == _grid_sha256(rival)

    assert gen.self_check(grid) == []
    assert gen.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
        **record["overrides"],
    ) == grid
    assert gen.observe_overrides(grid) == record["observed"]
    assert gen.rule_mirror(grid) == intended
    assert gen.SEMANTIC_RIVALS[record["rival_name"]](grid) == rival
    assert intended != rival

    computed_diffs = [
        [row, col]
        for row, (expected_row, rival_row) in enumerate(zip(intended, rival))
        for col, (expected_cell, rival_cell) in enumerate(zip(expected_row, rival_row))
        if expected_cell != rival_cell
    ]
    assert computed_diffs == record["differing_cells"]
    assert record["racket_check"]["valid_output"] is True
    assert record["racket_check"]["output_sha256"] == record["intended_output_sha256"]
    assert record["generator_emits_case"] is True
