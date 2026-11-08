"""Behavioral tests for the proposed causal scale-map family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The assigned runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("causal_scale_map_test_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


@pytest.fixture(scope="module")
def reference(p):
    with p.Reference() as runtime:
        yield runtime


def test_runnable_prototype_exists():
    load_prototype()


def test_default_is_exact_canonical_program(p):
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == "ecd1058990ce"}
    assert sources == {p.program({"scale_mode": "fixed_outer"})}


def test_fixed_outer_has_hand_derived_scale_map_and_racket_parity(p, reference):
    grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    want = [
        [1, 1, 2, 3, 3],
        [1, 1, 2, 3, 3],
        [4, 4, 5, 6, 6],
        [7, 7, 8, 9, 9],
        [7, 7, 8, 9, 9],
    ]
    settings = {"scale_mode": "fixed_outer"}
    assert p.transform(grid, settings) == want
    assert reference.apply(p.program(settings), grid) == want


def test_row_expansion_changes_the_column_consumed_by_step_b(p, reference):
    # Wrong-order counting sees a leftmost tie in the original grid. Step A gives
    # the second column twice the target mass, so the real Step B must choose it.
    grid = [[1, 1, 2], [2, 1, 1], [1, 2, 3]]
    state = p.target_weighted_state(grid)
    assert state["target"] == 1
    assert state["row_scales"] == [10, 10, 1]
    assert state["original_column_counts"] == [2, 2, 1]
    assert state["intermediate_column_counts"] == [11, 20, 10]
    assert state["selected_column"] == 1
    assert len(state["intermediate"]) == 21
    assert len(state["intermediate"][0]) == 3

    settings = {"scale_mode": "target_weighted"}
    output = p.transform(grid, settings)
    wrong = p.transform_wrong_order(grid)
    assert len(output) == 21 and all(len(row) == 30 for row in output)
    assert output != wrong
    assert reference.apply(p.program(settings), grid) == output
    assert reference.apply(p.hypotheses(settings)["wrong_order"], grid) == wrong


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_and_demo_only_identifiability(p, reference, demos):
    for scale_mode in ("fixed_outer", "target_weighted"):
        settings = {"scale_mode": scale_mode}
        episode = p.generate(17, settings, demos, 4)
        certificate = p.verify_episode(episode, reference)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert certificate["survivors"] == ["setting:" + scale_mode]
        assert len(certificate["query_checks"]) == 4
        assert all(item["identified_from_demonstrations"] for item in certificate["query_checks"])


def test_inputs_are_setting_independent_and_first_turn_is_count_independent(p):
    fixed = p.generate(23, {"scale_mode": "fixed_outer"}, 3, 4)
    weighted = p.generate(23, {"scale_mode": "target_weighted"}, 3, 4)
    one = p.generate(23, {"scale_mode": "target_weighted"}, 3, 1)
    for split in ("train", "test"):
        assert [pair["input"] for pair in fixed[split]] == [pair["input"] for pair in weighted[split]]
    assert fixed["train"] != weighted["train"]
    first = {"train": weighted["train"], "test": [{"input": weighted["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(one)


def test_four_queries_cover_size_and_causal_surfaces(p, reference):
    episode = p.generate(0, {"scale_mode": "target_weighted"}, 2, 4)
    outputs = [pair["output"] for pair in episode["test"]]
    assert [(len(grid), len(grid[0])) for grid in outputs] == [(30, 30), (21, 30), (12, 30), (3, 30)]
    largest = outputs[0]
    assert len({cell for row in largest for cell in row}) >= 3
    for r0 in (0, 15):
        for c0 in (0, 15):
            assert len({cell for row in largest[r0:r0 + 15] for cell in row[c0:c0 + 15]}) >= 2
    for pair in episode["test"]:
        assert reference.apply(episode["program_solution"], pair["input"]) == pair["output"]


def test_heavy_rows_only_shortcut_is_rejected_by_two_demos(p, reference):
    settings = {"scale_mode": "target_weighted"}
    episode = p.generate(8, settings, 2, 4)
    programs = p.hypotheses(settings)
    assert "heavy_rows_only" in programs
    fit = p.fit_demonstrations(episode["train"], settings, reference)
    assert "heavy_rows_only" in fit["rejected_by_demo"]
    assert any(
        reference.apply(programs["heavy_rows_only"], pair["input"]) != pair["output"]
        for pair in episode["test"]
    )


def test_wrong_order_and_fixed_location_bypasses_are_rejected_by_demos(p, reference):
    settings = {"scale_mode": "target_weighted"}
    episode = p.generate(8, settings, 2, 4)
    fit = p.fit_demonstrations(episode["train"], settings, reference)
    assert fit["survivors"] == ["setting:target_weighted"]
    for name in ("wrong_order", "always_left", "always_middle", "always_right"):
        assert name in fit["rejected_by_demo"]
    programs = p.hypotheses(settings)
    assert any(
        reference.apply(programs["wrong_order"], pair["input"]) != pair["output"]
        for pair in episode["test"]
    )


@pytest.mark.parametrize("kwargs", [
    {"demos": 1}, {"demos": 7}, {"demos": True},
    {"queries": 0}, {"queries": 5}, {"queries": 1.0}, {"seed": True},
    {"settings": {"scale_mode": "wrong"}},
    {"settings": {"scale_mode": "fixed_outer", "unknown": 1}},
])
def test_invalid_requests_are_rejected(p, kwargs):
    request = {"seed": 0, "settings": {"scale_mode": "fixed_outer"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        p.generate(**request)


def test_verifier_rejects_corruption_repetition_and_underteaching(p, reference):
    original = p.generate(8, {"scale_mode": "target_weighted"}, 2, 4)
    changes = []
    bad = deepcopy(original)
    bad["test"][0]["output"][0][0] = (bad["test"][0]["output"][0][0] + 1) % 10
    changes.append(bad)
    bad = deepcopy(original)
    bad["test"][0]["input"][0][0] = True
    changes.append(bad)
    bad = deepcopy(original)
    bad["test"][0] = deepcopy(bad["train"][0])
    changes.append(bad)
    bad = deepcopy(original)
    bad["program_solution"] = p.program({"scale_mode": "fixed_outer"})
    changes.append(bad)
    bad = deepcopy(original)
    # A single monochrome-like contrast-free lesson cannot identify the setting.
    grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    bad["train"] = [{"input": grid, "output": p.transform(grid, {"scale_mode": "target_weighted"})}] * 2
    changes.append(bad)
    for candidate in changes:
        with pytest.raises(ValueError):
            p.verify_episode(candidate, reference)


def test_native_adapter_loads_adjacent_implementation_not_cached_module(p):
    import sys
    import types

    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        spec = importlib.util.spec_from_file_location(
            "causal_scale_native_adapter_test", HOME / "workspace/parametric/adapter.py"
        )
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        settings = {"scale_mode": "target_weighted"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(6, settings, 2, 4) == p.generate(6, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_bounded_probe_reports_source_bound_racket_results(p, reference):
    probe_path = HOME / "workspace/parametric/probe.py"
    assert probe_path.is_file(), "The bounded reusable authoring probe is missing"
    spec = importlib.util.spec_from_file_location("causal_scale_probe_test", probe_path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.build_report(p, reference)
    assert report["schema"] == "causal-scale-map-probe-v1"
    assert report["status"] == "passed"
    assert report["task_id"] == "ecd1058990ce"
    assert report["failures"] == []
    assert report["case_count"] == 12
    assert report["causal_case"]["wrong_order_changes_output"] is True
    assert report["shortcut_case"]["heavy_rows_only_rejected_by_demo"] is True
    assert report["shortcut_case"]["heavy_rows_only_query_disagreement"] is True
    assert report["boundary"]["target_weighted_query_shapes"] == [
        [30, 30], [21, 30], [12, 30], [3, 30]
    ]
    assert report["source_sha256"] == p.source_bindings()
