from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = HERE / "refresh_parametric_receipts.py"


def load_module():
    spec = importlib.util.spec_from_file_location("refresh_parametric_receipts", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_export_verifier_checks_sequential_projection_and_rejects_corruption():
    tool = load_module()
    stats = tool.verify_export("d07a6cba78c7")
    assert stats["episodes"] == 2
    assert stats["controller_queries"] == [4, 4]
    assert stats["public_turns"] == 8
    assert stats["one_query_per_public_turn"] is True
    assert stats["first_turn_bytes_match_single_query"] is True
    assert tool.negative_corruption_probe("d07a6cba78c7") is True


def test_receipt_uses_fresh_task_counts_and_bounded_probe():
    tool = load_module()
    receipt = tool.build_receipt("bb75d495c809")
    assert receipt["task_tests"]["counts"]["passed"] == 9
    assert receipt["bounded_adversarial_probe"]["pair_labels_checked"] == 32
    assert receipt["racket_example"]["sequential_export"]["public_turns"] == 8
    assert receipt["export_verifier"]["negative_corruption_rejected"] is True
