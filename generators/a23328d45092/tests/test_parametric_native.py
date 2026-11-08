"""Native sequential parametric-family tests for a23328d45092."""
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
    spec = importlib.util.spec_from_file_location("native_a23328d45092", NATIVE_PATH)
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
            if row.get("task_id") == "a23328d45092":
                return row["program_solution"]
    raise AssertionError("missing canonical source")


def test_default_program_is_exact_and_alternative_is_distinct():
    native = _native()
    assert native.PARAMETER == "postprocess"
    assert native.SETTINGS == ("canonical", "highlight_visible_majority")
    assert native.program({"postprocess": "canonical"}) == _canonical_source()
    assert native.program({"postprocess": "highlight_visible_majority"}) != _canonical_source()


@pytest.mark.parametrize("bad", [None, {}, {"postprocess": "bad"}, {"postprocess": 1}, {"x": "canonical"}])
def test_settings_fail_closed(bad):
    native = _native()
    with pytest.raises(ValueError):
        native.program(bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_generate_honors_counts_and_labels(demos, queries):
    native = _native()
    for setting in native.SETTINGS:
        episode = native.generate(31, {"postprocess": setting}, demos=demos, queries=queries)
        assert len(episode["train"]) == demos and len(episode["test"]) == queries
        assert episode["program_solution"] == native.program({"postprocess": setting})
        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == native.solve(pair["input"], setting)


def test_each_demo_distinguishes_settings_and_last_query_is_30x30():
    native = _native()
    for setting in native.SETTINGS:
        episode = native.generate(13, {"postprocess": setting}, demos=3, queries=4)
        other = next(value for value in native.SETTINGS if value != setting)
        assert all(native.solve(pair["input"], other) != pair["output"] for pair in episode["train"])
        big = episode["test"][-1]["input"]
        assert (len(big), len(big[0])) == (30, 30)
        overlaid = native.overlay(big)
        assert sum(value != 0 for row in overlaid for value in row) >= 120


def test_wrong_order_source_majority_differs_from_visible_majority():
    native = _native()
    episode = native.generate(7, {"postprocess": "highlight_visible_majority"}, demos=3, queries=4)
    grids = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert any(
        native.source_majority(grid) != native.visible_majority(native.overlay(grid))
        and native.solve_wrong_order(grid) != native.solve(grid, "highlight_visible_majority")
        for grid in grids
    )


def test_public_turn_hides_settings_program_answers_and_future_queries():
    native = _native()
    episode = native.generate(7, {"postprocess": "highlight_visible_majority"}, demos=3, queries=4)
    view = native.public_turn(episode, 1)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    text = json.dumps(view)
    assert "postprocess" not in text and "rule!" not in text


def test_bounded_native_audit_emits_reusable_receipt(tmp_path):
    audit_path = HOME / "workspace/parametric/audit_native.py"
    assert audit_path.is_file(), "bounded native audit tool has not been implemented"
    spec = importlib.util.spec_from_file_location("audit_a23328d45092", audit_path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    receipt = audit.run_audit(2)
    assert receipt["status"] == "passed"
    assert receipt["task_id"] == "a23328d45092"
    assert receipt["seed_count"] == 2
    assert receipt["episode_count"] == 4
    assert receipt["wrong_order_differences"] >= 2
    out = tmp_path / "receipt.json"
    audit.write_receipt(receipt, out)
    assert json.loads(out.read_text()) == receipt
