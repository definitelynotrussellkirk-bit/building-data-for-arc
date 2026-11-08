"""Promotion-readiness contract for the proposed panel-threshold family."""
from __future__ import annotations

import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_priority import _prototype
from arcpuzzles.parametric_promotion import _ready
from reviewer_support import find_root


TASK_ID = "a9c4475d7cda"
ROOT = find_root(__file__)
MANIFEST = ROOT / f"generators/{TASK_ID}/workspace/parametric/evidence/manifest.json"


def test_current_inventory_binds_the_reviewed_sources_and_promotion_contract():
    """Catches a useful adapter that remains unreachable because inventory is missing/stale."""
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)

    state = _prototype(ROOT, row)
    assert state["status"] == "current"
    assert state["verification_status"] == "reviewer_reported"

    manifest = json.loads(MANIFEST.read_text())
    bound = {item["path"] for item in manifest["files"]}
    expected = {
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        f"generators/{TASK_ID}/workspace/parametric/promotion.json",
        f"generators/{TASK_ID}/workspace/parametric/README.md",
        f"generators/{TASK_ID}/tests/test_parametric_threshold.py",
        f"generators/{TASK_ID}/tests/test_parametric_inventory.py",
    }
    assert expected <= bound

    contract, binding = _ready(catalog, TASK_ID)
    assert contract == json.loads(
        (ROOT / f"generators/{TASK_ID}/workspace/parametric/promotion.json").read_text()
    )
    assert binding["task_id"] == TASK_ID
    assert binding["generator_sha256"] == row["generator_sha256"]
    assert binding["rule_hash"] == row["rule_hash"]
    binding_paths = {item["path"] for item in binding["files"]}
    assert {
        f"generators/{TASK_ID}/generator.py",
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        f"generators/{TASK_ID}/workspace/parametric/promotion.json",
    } <= binding_paths
