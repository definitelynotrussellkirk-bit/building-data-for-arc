"""Keep the retained shortcut counterexample source-bound and replayable."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.22398bb29643.generator"
)
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]


def test_deduplication_counterexample_replays_exactly():
    record = json.loads(
        (TASK_DIR / "counterexamples" / "deduplicate-component-colors.json").read_text()
    )
    source_hash = hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()

    assert record["generator_sha256"] == source_hash
    assert record["rule_hash"] == GEN.RULE_HASH
    regenerated = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
    )
    assert regenerated == record["input"]
    assert GEN.rule_mirror(regenerated) == record["intended_output"]
    rival = GEN.CANONICAL_SHORTCUTS[record["rival"]]
    assert rival(regenerated) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
