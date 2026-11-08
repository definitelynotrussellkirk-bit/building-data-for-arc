"""Regressions for the native direction-parametric marker rotation family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "ffcd7510821d"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)


def load(name: str):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing parametric source: {path}"
    module_name = f"_{TASK_ID}_{name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_record():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical record not found")


def all_pairs(episode):
    return episode["train"] + episode["test"]


def nonzero_body_cells(grid):
    return [(r, c, value) for r, row in enumerate(grid[2:], 2)
            for c, value in enumerate(row) if value]


def test_default_program_is_byte_exact_canonical_and_mirror_matches_canonical_pairs():
    prototype = load("prototype.py")
    record = canonical_record()
    assert prototype.program_for("clockwise") == record["program_solution"]
    assert prototype.CANONICAL_PROGRAM == record["program_solution"]
    assert prototype.program_for("counterclockwise") != record["program_solution"]
    assert hashlib.sha256(prototype.program_for("clockwise").encode()).hexdigest() == (
        "77da9e97370c0d2e1fa7cad46a1bc45e4087320926f1bf71d1d252a2c21eafcb"
    )
    for pair in record["train"] + record["test"]:
        assert prototype.apply_rule(pair["input"], "clockwise") == pair["output"]


@pytest.mark.parametrize("seed", [0, 1, 17, 2**31 - 1])
@pytest.mark.parametrize("demos", range(2, 7))
def test_settings_share_inputs_and_every_request_has_four_distinct_queries(seed, demos):
    prototype = load("prototype.py")
    clockwise = prototype.generate_episode(seed, direction="clockwise", demos=demos, queries=4)
    counter = prototype.generate_episode(seed, direction="counterclockwise", demos=demos, queries=4)
    assert [p["input"] for p in all_pairs(clockwise)] == [p["input"] for p in all_pairs(counter)]
    assert len(clockwise["train"]) == demos
    assert len(clockwise["test"]) == 4
    serialized = [json.dumps(p["input"], separators=(",", ":")) for p in all_pairs(clockwise)]
    assert len(serialized) == len(set(serialized))
    assert any(a["output"] != b["output"] for a, b in zip(clockwise["train"], counter["train"]))
    assert all(pair["output"] == prototype.apply_rule(pair["input"], "clockwise")
               for pair in all_pairs(clockwise))
    assert all(pair["output"] == prototype.apply_rule(pair["input"], "counterclockwise")
               for pair in all_pairs(counter))


@pytest.mark.parametrize("direction", ["clockwise", "counterclockwise"])
@pytest.mark.parametrize("demos", range(2, 7))
def test_visible_demos_reject_declared_query_changing_shortcuts(direction, demos):
    prototype = load("prototype.py")
    for seed in (0, 17, 91):
        episode = prototype.generate_episode(seed, direction=direction, demos=demos, queries=4)
        report = prototype.audit_episode(episode)
        assert report["chosen"] == direction
        assert report["setting_survivors"] == [direction]
        assert report["ambiguous_query_changers"] == []
        assert report["surviving_equivalent_rivals"] == []


def test_structural_profiles_include_real_large_grid_stress_and_all_turn_classes():
    prototype = load("prototype.py")
    episode = prototype.generate_episode(23, direction="clockwise", demos=6, queries=4)
    inputs = [pair["input"] for pair in all_pairs(episode)]
    assert [grid[0].count(9) for grid in inputs[:6]] == [1, 3, 2, 4, 1, 3]
    assert [grid[0].count(9) for grid in inputs[6:]] == [2, 4, 1, 3]
    for grid in inputs:
        assert all(value in (0, 9) for value in grid[0])
        assert not any(grid[1])
        assert all(9 not in row for row in grid[1:])
        assert nonzero_body_cells(grid)
        assert prototype.orbit_size(prototype.content_crop(grid)) == 4
    large = inputs[-1]
    assert (len(large), len(large[0])) == (30, 30)
    body = nonzero_body_cells(large)
    assert len(body) >= 48
    quadrants = {
        (r >= 16, c >= 15)
        for r, c, _ in body
    }
    assert quadrants == {(False, False), (False, True), (True, False), (True, True)}
    assert {r for r, _, _ in body} & {2, 29}
    assert {c for _, c, _ in body} & {0, 29}
    assert len({value for _, _, value in body}) == 4


def test_public_projection_masks_every_private_field_and_has_visible_byte_identity():
    prototype = load("prototype.py")
    episode = prototype.generate_episode(7, direction="counterclockwise", demos=3, queries=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    raw = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()

    changed = copy.deepcopy(episode)
    changed["settings"] = {"direction": "private-change"}
    changed["seed"] = 999
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_bytes(prototype.public_challenge(changed)) == raw


@pytest.mark.parametrize("direction", ["clockwise", "counterclockwise"])
def test_wrong_count_intermediate_changes_output_on_same_input(direction):
    prototype = load("prototype.py")
    episode = prototype.generate_episode(13, direction=direction, demos=2, queries=4)
    grid = episode["train"][0]
    turns = prototype.marker_turns(grid["input"])
    assert turns == 1
    correct = prototype.apply_rule(grid["input"], direction)
    wrong = prototype.apply_with_forced_turns(grid["input"], direction, 2)
    assert correct != wrong
    assert prototype.fixed_turn_program(direction, 2) != prototype.program_for(direction)


def test_adapter_and_promotion_contract_are_strict():
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"direction": ["clockwise", "counterclockwise"]},
        "default": {"direction": "clockwise"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    for direction in ("clockwise", "counterclockwise"):
        settings = {"direction": direction}
        assert adapter.program(settings) == prototype.program_for(direction)
        episode = adapter.generate(5, settings, 3, 4)
        assert episode["settings"] == settings
        assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    for bad in ({}, {"direction": "clockwise", "extra": 1},
                {"direction": "sideways"}, {"direction": True}, None):
        with pytest.raises(ValueError):
            adapter.program(bad)


@pytest.mark.parametrize("kwargs", [
    {"seed": True, "direction": "clockwise", "demos": 3, "queries": 4},
    {"seed": -1, "direction": "clockwise", "demos": 3, "queries": 4},
    {"seed": 2**63, "direction": "clockwise", "demos": 3, "queries": 4},
    {"seed": 0, "direction": "sideways", "demos": 3, "queries": 4},
    {"seed": 0, "direction": "clockwise", "demos": 1, "queries": 4},
    {"seed": 0, "direction": "clockwise", "demos": 7, "queries": 4},
    {"seed": 0, "direction": "clockwise", "demos": 3, "queries": 3},
    {"seed": 0, "direction": "clockwise", "demos": 3, "queries": True},
])
def test_request_validation_is_exact(kwargs):
    prototype = load("prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_bounded_sampler_stress_has_no_retries_or_duplicate_inputs():
    prototype = load("prototype.py")
    seen_large = 0
    for seed in range(64):
        for direction in ("clockwise", "counterclockwise"):
            episode = prototype.generate_episode(seed, direction=direction, demos=6, queries=4)
            inputs = [pair["input"] for pair in all_pairs(episode)]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 10
            assert prototype.audit_episode(episode)["ambiguous_query_changers"] == []
            assert all(prototype.orbit_size(prototype.content_crop(grid)) == 4 for grid in inputs)
            seen_large += (len(inputs[-1]) == 30 and len(inputs[-1][0]) == 30)
    assert seen_large == 128


def test_evidence_helpers_bind_causal_schema_and_visible_file_identity(tmp_path):
    prototype = load("prototype.py")
    evidence = load("build_evidence.py")
    episode = prototype.generate_episode(3, direction="clockwise", demos=2, queries=4)
    case = {
        "input": episode["train"][0]["input"],
        "settings": {"direction": "clockwise"},
        "intermediate_value": {"turns_mod4": 1, "cropped_object": [[1]]},
        "program": prototype.program_for("clockwise"),
        "output": episode["train"][0]["output"],
        "ablation": "wrong_intermediate",
        "counterfactual_program": prototype.fixed_turn_program("clockwise", 2),
        "counterfactual_output": prototype.apply_with_forced_turns(
            episode["train"][0]["input"], "clockwise", 2
        ),
    }
    document = evidence.witness_document({"task_id": TASK_ID}, [case])
    assert document["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert document["step_a"] and document["intermediate"] and document["step_b"]
    assert document["cases"] == [case]
    with pytest.raises(ValueError):
        evidence.witness_document({}, [case])
    with pytest.raises(ValueError):
        evidence.witness_document({"task_id": TASK_ID}, [])

    public_path = evidence.write_public_episode(episode, tmp_path)
    raw = public_challenge_bytes(prototype.public_challenge(episode))
    assert public_path.name == f"challenge-{hashlib.sha256(raw).hexdigest()}.json"
    assert public_path.read_bytes() == raw


def test_stress_tool_reports_expected_counts(tmp_path):
    stress = load("stress.py")
    report = stress.run(3)
    assert report["status"] == "passed"
    assert report["seeds"] == 3
    assert report["scenes"] == 30
    assert report["episodes"] == 12
    assert report["max_shape"] == [30, 30]
    path = tmp_path / "stress.json"
    stress.write_report(path, report)
    assert json.loads(path.read_text(encoding="utf-8")) == report
