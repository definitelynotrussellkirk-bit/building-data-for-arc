from __future__ import annotations

import hashlib
import importlib
import json

from reviewer_support import find_root

TASK_ID = "4e79c276ce9d"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
COUNTEREXAMPLE = ROOT / "generators" / TASK_ID / "counterexamples" / "bbox_area_rival.json"


def test_retained_bbox_area_counterexample_is_source_bound_and_reproducible():
    record = json.loads(COUNTEREXAMPLE.read_text())
    generator_path = ROOT / "generators" / TASK_ID / "generator.py"
    assert record["generator_sha256"] == hashlib.sha256(generator_path.read_bytes()).hexdigest()
    assert record["rule_hash"] == GEN.RULE_HASH
    grid = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
        **record["overrides"],
    )
    assert grid == record["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == record["actual_racket_output"]
    assert GEN.CANONICAL_SHORTCUTS[record["rival_name"]](grid) == record["rival_output"]
    assert record["actual_racket_output"] != record["rival_output"]
