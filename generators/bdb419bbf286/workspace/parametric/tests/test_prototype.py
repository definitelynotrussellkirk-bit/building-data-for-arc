from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK = "bdb419bbf286"
HERE = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def load_module():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("parametric_bdb419bbf286", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError(TASK)


def test_default_program_is_exact_canonical():
    module = load_module()
    assert module.program({"repeat_rule": "fixed_three"}) == canonical_program()


def test_counts_distinctness_and_setting_neutral_inputs():
    module = load_module()
    for seed in (0, 17):
        for demos in (2, 3, 6):
            fixed = module.generate(seed, {"repeat_rule": "fixed_three"}, demos, 4)
            boundary = module.generate(seed, {"repeat_rule": "to_boundary"}, demos, 4)
            assert len(fixed["train"]) == demos
            assert len(fixed["test"]) == 4
            assert [p["input"] for p in fixed["train"] + fixed["test"]] == [
                p["input"] for p in boundary["train"] + boundary["test"]
            ]
            inputs = [json.dumps(p["input"], separators=(",", ":")) for p in fixed["train"] + fixed["test"]]
            assert len(inputs) == len(set(inputs))


def test_every_scene_exposes_repeat_and_first_marker_choices():
    module = load_module()
    for seed in (0, 3, 17, 99):
        fixed = module.generate(seed, {"repeat_rule": "fixed_three"}, 6, 4)
        boundary = module.generate(seed, {"repeat_rule": "to_boundary"}, 6, 4)
        for fp, bp in zip(fixed["train"] + fixed["test"], boundary["train"] + boundary["test"]):
            facts = module.analyze(fp["input"])
            assert len(facts["marker_3"]) == 2
            assert len(facts["marker_4"]) == 2
            assert facts["last_vector"] != facts["first_vector"]
            assert facts["boundary_copy_count"] >= 5
            assert fp["output"] != bp["output"]
            assert module.finish_python(fp["input"], {"repeat_rule": "last_marker_fixed_three"}) != fp["output"]
            assert module.finish_python(bp["input"], {"repeat_rule": "last_marker_to_boundary"}) != bp["output"]


def test_first_two_demonstrations_reject_declared_shortcuts():
    module = load_module()
    rivals = (
        "fixed_one",
        "fixed_two",
        "fixed_four",
        "fixed_five",
        "fixed_six",
        "last_marker_fixed_three",
        "last_marker_to_boundary",
    )
    for selected in ({"repeat_rule": "fixed_three"}, {"repeat_rule": "to_boundary"}):
        for seed in range(24):
            episode = module.generate(seed, selected, 2, 4)
            candidates = [
                setting
                for setting in ({"repeat_rule": "fixed_three"}, {"repeat_rule": "to_boundary"})
                if all(module.finish_python(p["input"], setting) == p["output"] for p in episode["train"])
            ]
            assert candidates == [selected]
            for rival in rivals:
                assert any(
                    module.finish_python(p["input"], {"repeat_rule": rival}) != p["output"]
                    for p in episode["train"]
                ), (selected, seed, rival)


def test_query_bank_contains_substantive_30_by_30_case():
    module = load_module()
    episode = module.generate(5, {"repeat_rule": "to_boundary"}, 3, 4)
    large = next(p for p in episode["test"] if len(p["input"]) == 30 and len(p["input"][0]) == 30)
    foreground = sum(value != 0 for row in large["input"] for value in row)
    output = sum(value == 8 for row in large["output"] for value in row)
    facts = module.analyze(large["input"])
    assert foreground >= 60
    assert output >= 100
    assert facts["boundary_copy_count"] >= 12
    assert any(8 in row for row in (large["output"][0], large["output"][-1])) or any(
        row[0] == 8 or row[-1] == 8 for row in large["output"]
    )


def test_strict_argument_validation():
    module = load_module()
    with pytest.raises(ValueError):
        module.generate(True, {"repeat_rule": "fixed_three"}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"repeat_rule": "bad"}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"repeat_rule": "fixed_three", "extra": 1}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"repeat_rule": "fixed_three"}, 1, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"repeat_rule": "fixed_three"}, 3, 5)


def test_bounded_audit_rejects_declared_shortcuts():
    path = HERE / "audit.py"
    spec = importlib.util.spec_from_file_location("audit_bdb419bbf286", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.run_audit(seeds=range(8), demo_counts=(2, 3, 6))
    assert report["status"] == "pass"
    assert report["jobs"] == 48
    assert report["pairs"] == 368
    assert report["settings_survivors"] == 48
    assert report["rival_survivors"] == {}
    assert report["last_marker_failures"] >= 300
    assert report["max_lawful_canvas"] == [30, 30]
