"""Adversarial sampler/export/verifier checks for the token/tie prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The test's tree does not contain reviewer_support.py")

from reviewer_support import find_root


TASK_ID = "31b8bedd699a"
ROOT = find_root(__file__)
PROBE = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "adversarial_probe.py"
)


def _load_probe():
    assert PROBE.is_file(), f"parametric adversarial probe is missing: {PROBE}"
    spec = importlib.util.spec_from_file_location(
        "parametric_token_tie_adversarial_31b8bedd699a", PROBE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_exercises_sampler_export_and_verifier_surfaces(tmp_path):
    probe = _load_probe()
    out = tmp_path / "probe.json"
    summary = probe.run_probe(out, seed=41, max_count=12, root=ROOT)

    assert summary["status"] == "pass"
    assert summary["surfaces"] == [
        "sampler_boundaries_and_deterministic_replay",
        "public_private_export_and_verifier_rejection",
    ]

    sampler = summary["sampler"]
    assert sampler["demo_count"] == 12
    assert sampler["query_count"] == 12
    assert sampler["unique_input_count"] == 24
    assert sampler["deterministic_replay"] is True
    assert sampler["episode_verifier_errors"] == []
    assert sampler["strict_rejections"] == {
        "token_size": 7,
        "tie_policy": 5,
        "demo_count": 5,
        "query_count": 5,
        "seed": 4,
    }

    export = summary["export"]
    assert export["private_mutation_count"] >= 10
    assert export["all_private_mutations_preserve_id"] is True
    assert export["all_visible_mutations_change_id"] is True
    assert export["public_payload_masks_query_answers"] is True
    assert export["public_numeric_types_are_exact_ints"] is True
    assert export["opaque_filename"] is True

    verifier = summary["verifier"]
    assert verifier["all_tampered_episodes_rejected"] is True
    assert verifier["rejections"] == {
        "wrong_program": True,
        "wrong_output": True,
        "duplicate_input": True,
        "underidentified_demos": True,
        "multiple_parameter_draws": True,
    }
    assert out.read_text().endswith("\n")
    assert json.loads(out.read_text()) == summary


@pytest.mark.parametrize("invalid", [True, 0, 65, 1.5, "12"])
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
