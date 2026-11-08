"""Replay retained recipes and rivals against previously recorded Racket labels.

These tests do not execute Racket or independently relabel the fixtures.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "8096ecc43d5a"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
FIXTURES = ("sorted_codes", "deduplicate_codes", "map_cw_v_id_h")


def _counterexample_path(name):
    direct = SOURCE.parent / "counterexamples" / f"{name}.json"
    if direct.is_file():
        return direct
    manifest_path = ROOT / "RUNTIME_MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        library_path = f"generators/{TASK_ID}/counterexamples/{name}.json"
        selected = [row for row in manifest.get("files", []) if row.get("library_path") == library_path]
        if len(selected) == 1:
            relative = Path(selected[0]["runtime_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe counterexample runtime path")
            return ROOT / relative
    raise FileNotFoundError(f"No selected or manifest-bound counterexample: {name}")


@pytest.mark.parametrize("name", FIXTURES)
def test_retained_counterexample_replays(name):
    retained = json.loads(_counterexample_path(name).read_text(encoding="utf-8"))
    assert retained["schema"] == "arcpuzzles-semantic-witness-v1"
    assert retained["task_id"] == TASK_ID
    assert retained["rival"] == name
    binding = retained["source_binding"]
    assert binding["generator_sha256"] == SOURCE_SHA256
    assert binding["rule_task_id"] == TASK_ID
    assert binding["rule_source_sha256"][:12] == GEN.RULE_HASH
    assert binding["status"] == "bound"
    assert binding["errors"] == []
    assert retained["validation"]["rule_applied"] is True  # Retained provenance, not a fresh application.

    recipe = retained["recipe"]
    regenerated = GEN.generate(
        recipe["seed"], recipe["sample_index"], difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    assert regenerated == retained["input"]
    assert GEN.self_check(regenerated, difficulty=recipe["difficulty"]) == []

    rival_output = GEN.SEMANTIC_RIVALS[name](deepcopy(regenerated))
    assert rival_output == retained["rival_output"]
    assert rival_output != retained["authoritative_output"]
    assert GEN.CANONICAL_SHORTCUTS[name](deepcopy(regenerated)) == rival_output
    assert GEN.SEMANTIC_WITNESSES[retained["witness"]](deepcopy(regenerated)) is True
