from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"


def load_adapter():
    name = "_test_eb_parametric_" + hashlib.sha256(str(ADAPTER_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def flatten_pairs(episode):
    return episode["train"] + episode["test"]


def test_default_program_is_byte_exact_canonical_and_variant_is_distinct():
    adapter = load_adapter()
    canonical = CANONICAL_PATH.read_text(encoding="utf-8")
    assert adapter.program({"prototype_policy": "matching"}) == canonical
    opposite = adapter.program({"prototype_policy": "opposite_shape"})
    assert opposite != canonical
    assert opposite.startswith("(rule!")


def test_episode_counts_are_prefix_stable_and_setting_neutral():
    adapter = load_adapter()
    short = adapter.generate(17, {"prototype_policy": "matching"}, 2, 1)
    full = adapter.generate(17, {"prototype_policy": "matching"}, 6, 4)
    opposite = adapter.generate(17, {"prototype_policy": "opposite_shape"}, 6, 4)

    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert [pair["input"] for pair in flatten_pairs(full)] == [
        pair["input"] for pair in flatten_pairs(opposite)
    ]
    assert full["program_solution"] == adapter.program({"prototype_policy": "matching"})
    assert opposite["program_solution"] == adapter.program({"prototype_policy": "opposite_shape"})


def test_python_labels_match_policy_and_every_demo_distinguishes_settings():
    adapter = load_adapter()
    matching = adapter.generate(991, {"prototype_policy": "matching"}, 6, 4)
    opposite = adapter.generate(991, {"prototype_policy": "opposite_shape"}, 6, 4)
    for a, b in zip(flatten_pairs(matching), flatten_pairs(opposite)):
        assert a["input"] == b["input"]
        assert a["output"] == adapter.native_transform(a["input"], "matching")
        assert b["output"] == adapter.native_transform(b["input"], "opposite_shape")
        assert a["output"] != b["output"]


def test_scene_bank_has_distinct_inputs_seed_erasure_and_dense_30x30_query():
    adapter = load_adapter()
    episode = adapter.generate(3, {"prototype_policy": "matching"}, 6, 4)
    pairs = flatten_pairs(episode)
    fingerprints = {repr(pair["input"]) for pair in pairs}
    assert len(fingerprints) == 10

    assert any(pair["input"][0][0] == 0 for pair in pairs)
    assert any(pair["input"][0][4] == 0 for pair in pairs)

    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    seeds = [
        value
        for row in stress[4:]
        for value in row
        if value in (2, 3)
    ]
    assert len(seeds) >= 40
    assert set(seeds) == {2, 3}


def test_invalid_contract_arguments_are_rejected():
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.program({"prototype_policy": "unknown"})
    with pytest.raises(ValueError):
        adapter.generate(-1, {"prototype_policy": "matching"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"prototype_policy": "matching"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"prototype_policy": "matching"}, 2, 5)


def test_bounded_named_rival_audit_passes():
    path = PARAMETRIC / "audit.py"
    name = "_test_eb_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 17, 991))
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["findings"] == []
    assert report["has_30x30"] is True
