"""Native admission tests for the sequential 156bae9e7b79 family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

HOME = Path(__file__).resolve().parents[1]
NATIVE_PATH = HOME / "workspace/parametric/native_family.py"


def _native():
    assert NATIVE_PATH.is_file(), "native parametric family has not been implemented"
    spec = importlib.util.spec_from_file_location("native_156bae9e7b79", NATIVE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    path = find_root(__file__) / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "156bae9e7b79":
                return row["program_solution"]
    raise AssertionError("missing canonical source")


def test_default_program_is_exact_and_alternative_is_distinct():
    native = _native()
    assert native.PARAMETER == "postprocess"
    assert native.SETTINGS == ("canonical", "highlight_projected_majority")
    assert native.program({"postprocess": "canonical"}) == _canonical_source()
    assert native.program({"postprocess": "highlight_projected_majority"}) != _canonical_source()


@pytest.mark.parametrize("bad", [None, {}, {"postprocess": "bad"}, {"postprocess": True}, {"x": "canonical"}])
def test_settings_fail_closed(bad):
    native = _native()
    with pytest.raises(ValueError):
        native.program(bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_generate_honors_independent_counts_and_all_inputs_are_distinct(demos, queries):
    native = _native()
    for setting in native.SETTINGS:
        episode = native.generate(17, {"postprocess": setting}, demos=demos, queries=queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == native.program({"postprocess": setting})
        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == native.solve(pair["input"], setting)


def test_every_demo_identifies_the_setting_and_queries_include_substantive_30x30():
    native = _native()
    for setting in native.SETTINGS:
        episode = native.generate(23, {"postprocess": setting}, demos=3, queries=4)
        other = next(value for value in native.SETTINGS if value != setting)
        assert all(
            native.solve(pair["input"], other) != pair["output"]
            for pair in episode["train"]
        )
        big = episode["test"][-1]["input"]
        assert (len(big), len(big[0])) == (30, 30)
        projected = native.project(big)
        assert sum(value != 5 for row in projected for value in row) >= 250


def test_wrong_order_key_majority_differs_from_projected_majority_on_retained_witness():
    native = _native()
    episode = native.generate(41, {"postprocess": "highlight_projected_majority"}, demos=3, queries=4)
    witnesses = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert any(
        native.key_row_majority(grid) != native.projected_majority(native.project(grid))
        and native.solve_wrong_order(grid) != native.solve(grid, "highlight_projected_majority")
        for grid in witnesses
    )


def test_public_turn_contains_only_visible_single_query_bytes():
    native = _native()
    episode = native.generate(9, {"postprocess": "highlight_projected_majority"}, demos=3, queries=4)
    view = native.public_turn(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    text = json.dumps(view)
    assert "postprocess" not in text and "rule!" not in text


def test_bounded_native_audit_emits_reusable_receipt(tmp_path):
    audit_path = HOME / "workspace/parametric/audit_native.py"
    assert audit_path.is_file(), "bounded native audit tool has not been implemented"
    spec = importlib.util.spec_from_file_location("audit_156bae9e7b79", audit_path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    receipt = audit.run_audit(2)
    assert receipt["status"] == "passed"
    assert receipt["task_id"] == "156bae9e7b79"
    assert receipt["seed_count"] == 2
    assert receipt["episode_count"] == 4
    assert receipt["wrong_order_differences"] >= 2
    out = tmp_path / "receipt.json"
    audit.write_receipt(receipt, out)
    assert json.loads(out.read_text()) == receipt
