from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
PROBE = HERE / "allocation_probe.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("allocation_probe", PROBE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load allocation_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ticket_seed_samples_expected_records():
    probe = load_probe()
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
    assert probe.seeded_sample(manifest, probe.SEED, 3) == [
        "80271cb9b303",
        "59a7762bc6da",
        "548c1010ce89",
    ]


def test_policy_summary_reads_actual_draw_pools():
    probe = load_probe()
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
    summary = probe.policy_summary(manifest)
    assert summary["all_ids"] == 300
    assert summary["main_ids"] == 164
    assert summary["normal_ids"] == 162
    assert summary["focus_probability"] == {"numerator": 1, "denominator": 10}
    assert summary["focus_anchors"] == 120
    assert summary["focus_anchors_with_related_generators"] == 1
    assert summary["focus_unique_related_generators"] == 2


def test_pinned_ticket_source_is_unchanged():
    probe = load_probe()
    result = probe.verify_pinned_source(WORK)
    assert result["match"] is True
    assert result["actual_sha256"] == probe.PINNED_SOURCE_SHA256
