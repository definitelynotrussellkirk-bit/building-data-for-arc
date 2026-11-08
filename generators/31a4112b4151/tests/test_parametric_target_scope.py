from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "31a4112b4151"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("parametric_31a_adapter", "adapter.py")
PROTOTYPE = _load("parametric_31a_prototype", "prototype.py")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _frozen_inputs(episode):
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_bytes_and_alternative_is_distinct():
    canonical = _canonical_program()
    assert ADAPTER.program({"target_scope": "all_targets"}) == canonical
    assert ADAPTER.program({"target_scope": "clipped_targets"}) != canonical


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_independent_inputs_are_distinct_and_settings_are_matched(demos, queries):
    all_episode = ADAPTER.generate(27, {"target_scope": "all_targets"}, demos, queries)
    clipped_episode = ADAPTER.generate(27, {"target_scope": "clipped_targets"}, demos, queries)

    assert len(all_episode["train"]) == len(clipped_episode["train"]) == demos
    assert len(all_episode["test"]) == len(clipped_episode["test"]) == queries
    assert _frozen_inputs(all_episode) == _frozen_inputs(clipped_episode)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _frozen_inputs(all_episode)]
    assert len(serialized) == len(set(serialized))
    assert any(
        left["output"] != right["output"]
        for left, right in zip(
            [*all_episode["train"], *all_episode["test"]],
            [*clipped_episode["train"], *clipped_episode["test"]],
        )
    )


def test_four_query_bank_contains_distributed_30_by_30_stress():
    episode = ADAPTER.generate(91, {"target_scope": "all_targets"}, 3, 4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes[-1] == (30, 30)
    facts = PROTOTYPE.inspect_scene(episode["test"][-1]["input"])
    assert len(facts["targets"]) == 4
    assert len(facts["offsets"]) >= 5
    rows = [row for row, _col in facts["targets"]]
    cols = [col for _row, col in facts["targets"]]
    assert max(rows) - min(rows) >= 24
    assert max(cols) - min(cols) >= 24


def test_every_pair_has_both_clipped_and_unclipped_targets_and_settings_disagree():
    for seed in range(12):
        canonical = ADAPTER.generate(seed, {"target_scope": "all_targets"}, 2, 4)
        alternate = ADAPTER.generate(seed, {"target_scope": "clipped_targets"}, 2, 4)
        for left, right in zip(
            [*canonical["train"], *canonical["test"]],
            [*alternate["train"], *alternate["test"]],
        ):
            facts = PROTOTYPE.inspect_scene(left["input"])
            clipped = [t for t in facts["targets"] if facts["clipped_by_target"][t] > 0]
            unclipped = [t for t in facts["targets"] if facts["clipped_by_target"][t] == 0]
            assert clipped and unclipped
            assert left["output"] != right["output"]


def test_bounded_rival_audit_has_no_harmful_survivors():
    report = PROTOTYPE.bounded_audit(seeds=range(16), demos=2, queries=4)
    assert report["episodes"] == 32
    assert report["harmful_survivors"] == []


def test_dependency_trace_names_input_derived_intermediate_consumed_by_stamp():
    episode = ADAPTER.generate(5, {"target_scope": "clipped_targets"}, 2, 4)
    trace = PROTOTYPE.dependency_trace(
        episode["test"][0]["input"], {"target_scope": "clipped_targets"}
    )
    assert trace["step_a"] == "extract_template_and_select_clipped_targets"
    assert trace["step_b"] == "stamp_extracted_template_at_selected_targets"
    assert trace["intermediate"]["selected_targets"]
    assert trace["intermediate"]["template_offsets"]
    assert trace["output"] == episode["test"][0]["output"]
    assert trace["counterfactual_all_targets_output"] != trace["output"]


def test_invalid_settings_and_scalar_requests_fail_closed():
    with pytest.raises(ValueError):
        ADAPTER.program({"target_scope": "other"})
    with pytest.raises(ValueError):
        ADAPTER.program({"target_scope": "all_targets", "extra": 1})
    with pytest.raises(ValueError):
        ADAPTER.generate(True, {"target_scope": "all_targets"}, 3, 4)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, {"target_scope": "all_targets"}, 1, 4)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, {"target_scope": "all_targets"}, 3, 5)
