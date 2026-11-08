"""Source-bound regression for the strongest canonical-fitting shortcut."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path


MODULE = importlib.import_module("puzzle_generators.per_puzzle.144582f287b5.generator")
TASK_ROOT = Path(__file__).resolve().parents[1]
COUNTEREXAMPLE = (
    TASK_ROOT
    / "counterexamples"
    / "review-013907b794c6cebd"
    / "geometric-center-rival.json"
)


def test_geometric_center_counterexample_is_lawful_source_bound_and_decisive():
    record = json.loads(COUNTEREXAMPLE.read_text(encoding="utf-8"))
    grid = record["input"]
    generator_path = TASK_ROOT / "generator.py"

    assert record["task_id"] == MODULE.TASK_ID == "144582f287b5"
    assert record["generator_sha256"] == hashlib.sha256(generator_path.read_bytes()).hexdigest()
    assert record["rule_hash"] == MODULE.RULE_HASH == "acb1a0ae5f73"
    assert record["seed"] == 5521
    assert record["sample_index"] == 2
    assert record["difficulty"] == "medium"
    assert record["profile"] == "source_halo"
    assert MODULE.self_check(copy.deepcopy(grid)) == []
    assert MODULE.generate(5521, 2, difficulty="medium") == grid
    assert MODULE.rule_mirror(copy.deepcopy(grid)) == record["intended_output"]
    assert MODULE.SEMANTIC_RIVALS["geometric_center"](copy.deepcopy(grid)) == record["rival_output"]
    assert record["rival_output"] != record["intended_output"]
    assert record["disagrees"] is True
