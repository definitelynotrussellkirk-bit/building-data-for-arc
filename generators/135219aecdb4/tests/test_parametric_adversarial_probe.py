"""Adversarial boundary probe tests for the pass-budget prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

TASK_ID = "135219aecdb4"
ROOT = find_root(__file__)
PROBE = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "adversarial_probe.py"
)


def _load_probe():
    assert PROBE.is_file(), "parametric adversarial probe is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_adversarial_probe_135219aecdb4", PROBE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_exercises_sampler_and_export_surfaces(tmp_path):
    probe = _load_probe()
    out = tmp_path / "probe.json"
    summary = probe.run_probe(out, seed=29, max_count=8, root=ROOT)

    assert summary["status"] == "pass"
    assert summary["surfaces"] == [
        "sampler_count_retry_boundaries",
        "public_private_export_and_numeric_types",
    ]
    sampler = summary["sampler"]
    assert sampler["demo_count"] == 8
    assert sampler["query_count"] == 8
    assert sampler["unique_input_count"] == 16
    assert sampler["all_inputs_require_three_passes"] is True
    assert sampler["strict_rejections"] == {
        "pass_count": 7,
        "demo_count": 5,
        "query_count": 5,
        "seed": 4,
    }

    export = summary["export"]
    assert export["private_mutation_count"] >= 8
    assert export["all_private_mutations_preserve_id"] is True
    assert export["all_visible_mutations_change_id"] is True
    assert export["public_payload_masks_query_answers"] is True
    assert export["opaque_filename"] is True
    assert out.read_text().endswith("\n")
    assert json.loads(out.read_text()) == summary


@pytest.mark.parametrize("invalid", [True, 0, 65, 1.5, "8"])
def test_probe_rejects_non_exact_or_out_of_range_count(tmp_path, invalid):
    probe = _load_probe()
    with pytest.raises(ValueError, match="max_count"):
        probe.run_probe(tmp_path / "probe.json", max_count=invalid, root=ROOT)


def test_probe_refuses_to_overwrite_receipt(tmp_path):
    probe = _load_probe()
    out = tmp_path / "probe.json"
    out.write_text("sentinel\n")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.run_probe(out, max_count=2, root=ROOT)
