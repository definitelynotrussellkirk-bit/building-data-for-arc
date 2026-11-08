"""Contract tests for the native set-result largest-component relay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root


TASK_ID = "c5a80b7a3acc"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = HERE / "prototype.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load("c5a80b7a3acc_parametric_prototype_test", PROTOTYPE_PATH)
adapter = _load("c5a80b7a3acc_parametric_adapter_test", HERE / "adapter.py")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _outputs(episode):
    return [pair["output"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_authority():
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"result_policy": "direct"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest().startswith("db99a498afde")


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_supported_counts_are_exact_distinct_deterministic_and_setting_neutral(demos, queries):
    settings = [
        {"result_policy": "direct"},
        {"result_policy": "largest_component"},
    ]
    episodes = [adapter.generate(17, setting, demos, queries) for setting in settings]
    assert [len(ep["train"]) for ep in episodes] == [demos, demos]
    assert [len(ep["test"]) for ep in episodes] == [queries, queries]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    assert len({json.dumps(value, separators=(",", ":")) for value in _inputs(episodes[0])}) == demos + queries
    assert episodes[0] == adapter.generate(17, settings[0], demos, queries)
    assert episodes[1] == adapter.generate(17, settings[1], demos, queries)
    assert episodes[0]["program_solution"] == adapter.program(settings[0])
    assert episodes[1]["program_solution"] == adapter.program(settings[1])


@pytest.mark.parametrize("seed", [0, 1, 17, 91])
def test_two_demo_prefix_identifies_both_settings_against_declared_rivals(seed):
    for policy in prototype.RESULT_POLICIES:
        episode = adapter.generate(seed, {"result_policy": policy}, 2, 4)
        certificate = prototype.teaching_certificate(episode["train"], [p["input"] for p in episode["test"]])
        assert certificate["survivors"] == [policy]
        assert certificate["queries"] == 4
        assert set(certificate["declared_hypotheses"]) == set(prototype.HYPOTHESES)


def test_claimed_labels_match_independent_python_semantics():
    for seed in (0, 17):
        for policy in prototype.RESULT_POLICIES:
            episode = adapter.generate(seed, {"result_policy": policy}, 6, 4)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.predict(pair["input"], policy)
                state = prototype.observe(pair["input"])
                assert state["source_components"] == {"2": 1, "3": 1}
                assert state["operation"] in {"intersection", "xor"}
                assert state["result_component_sizes"]
                assert state["result_component_sizes"][0] > state["result_component_sizes"][1]


def test_first_two_demonstrations_cover_both_header_operations_and_nontrivial_stage_b():
    episode = adapter.generate(0, {"result_policy": "largest_component"}, 2, 4)
    states = [prototype.observe(pair["input"]) for pair in episode["train"]]
    assert [state["operation"] for state in states] == ["intersection", "xor"]
    assert all(len(state["result_component_sizes"]) >= 2 for state in states)
    assert all(pair["output"] != prototype.predict(pair["input"], "direct") for pair in episode["train"])


def test_query_bank_contains_boundary_and_substantive_30x30_stress():
    episode = adapter.generate(0, {"result_policy": "largest_component"}, 2, 4)
    queries = episode["test"]
    assert len(queries[2]["input"]) == 14 and len(queries[2]["input"][0]) == 20
    assert any(value != 0 for value in queries[2]["input"][0])
    assert any(value != 0 for value in queries[2]["input"][-1])
    stress = queries[3]["input"]
    assert len(stress) == len(stress[0]) == 30
    assert sum(value in {2, 3} for row in stress for value in row) >= 120
    assert prototype.observe(stress)["result_component_sizes"][:3] == [46, 30, 4]


def test_wrong_union_intermediate_changes_stage_b_selection():
    episode = adapter.generate(0, {"result_policy": "largest_component"}, 2, 4)
    witness_input = episode["test"][0]["input"]
    correct = prototype.predict(witness_input, "largest_component")
    counterfactual = prototype.predict(witness_input, "union_largest")
    assert correct != counterfactual
    state = prototype.observe(witness_input)
    assert state["result_component_sizes"][0] > state["result_component_sizes"][1]


@pytest.mark.parametrize("bad", [
    {}, {"result_policy": "unknown"}, {"result_policy": 1},
    {"result_policy": "direct", "extra": 1}, None,
])
def test_invalid_settings_are_rejected(bad):
    with pytest.raises(ValueError):
        adapter.program(bad)
    with pytest.raises(ValueError):
        adapter.generate(0, bad, 2, 4)


@pytest.mark.parametrize("args", [
    (-1, {"result_policy": "direct"}, 2, 4),
    (True, {"result_policy": "direct"}, 2, 4),
    (0, {"result_policy": "direct"}, 1, 4),
    (0, {"result_policy": "direct"}, 7, 4),
    (0, {"result_policy": "direct"}, 2, 0),
    (0, {"result_policy": "direct"}, 2, 5),
])
def test_invalid_count_and_seed_requests_are_rejected(args):
    with pytest.raises(ValueError):
        adapter.generate(*args)


def test_reusable_audit_tool_reports_clean_structural_sweep():
    audit = _load("c5a80b7a3acc_parametric_audit_test", HERE / "audit.py")
    report = audit.structural_stress(3)
    assert report["seed_count"] == 3
    assert report["episodes"] == 3 * 5 * 2
    assert report["failures"] == []
    assert report["finite_rival_certificates"] == report["episodes"]
