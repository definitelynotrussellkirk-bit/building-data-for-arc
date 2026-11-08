from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SCRIPT = HERE / "allocation_probe.py"
SEED = "9bc134f1609b62f979f7550c46c63f25f0b6c0a58e99161be9f16eaa2f665372"


def load_module():
    spec = importlib.util.spec_from_file_location("ticket_allocation_probe", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_seeded_sample_and_policy_are_pinned():
    module = load_module()
    report = module.build_report(WORK, SEED)
    assert report["sampled_ids"] == [
        "548c1010ce89",
        "6fde852adb54",
        "f3076f3858b4",
    ]
    assert report["authoring_policy"]["evaluation_focus_probability"] == {
        "numerator": 1,
        "denominator": 10,
    }
    assert report["authoring_policy"]["normal_pool_count"] == 162


def test_sample_exposes_weight_and_evidence_mismatch():
    module = load_module()
    report = module.build_report(WORK, SEED)
    rows = {row["task_id"]: row for row in report["sample"]}
    assert rows["548c1010ce89"]["dataset_sampling_weight"] == 1.0
    assert rows["548c1010ce89"]["open_audit_count"] >= 1
    assert rows["6fde852adb54"]["train_safety"] == "reviewed_safe"
    assert rows["6fde852adb54"]["dataset_sampling_weight"] == 0.0
    assert rows["f3076f3858b4"]["train_safety"] == "unverified"
    assert rows["f3076f3858b4"]["dataset_sampling_weight"] == 1.0
    assert rows["f3076f3858b4"]["open_audit_count"] >= 1


def test_alternative_is_bounded_and_preserves_focus_share():
    module = load_module()
    report = module.build_report(WORK, SEED)
    trial = report["alternative_allocation"]
    assert trial["total_assignments"] == 30
    assert trial["evaluation_focus_assignments"] == 3
    assert trial["normal_assignments"] == 27
    assert trial["targeted_normal_assignments"] == 6
    assert trial["uniform_normal_assignments"] == 21
    assert trial["adoption_rule"]["minimum_quality_per_cost_ratio"] == 1.25
    assert report["coverage_limits"]
