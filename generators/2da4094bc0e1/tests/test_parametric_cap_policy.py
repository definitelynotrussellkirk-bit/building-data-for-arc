from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "2da4094bc0e1"
TASK_ROOT = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_ROOT / "workspace" / "parametric"
SETTINGS = ("both_sides", "cue_controlled_side")


def _load():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_parametric_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_and_alternative_is_distinct():
    p = _load()
    assert p.program({"cap_policy": "both_sides"}) == _canonical_program()
    alternative = p.program({"cap_policy": "cue_controlled_side"})
    assert alternative != _canonical_program()
    assert alternative.strip().startswith("(rule!")


def test_controls_are_strict_and_count_bounds_are_exact():
    p = _load()
    good = {"cap_policy": "both_sides"}
    for settings in (None, {}, {"cap_policy": "typo"}, {"cap_policy": True}, {"cap_policy": "both_sides", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.program(settings)
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, settings, 3, 4)
    for seed in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            p.generate(seed, good, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5), (3, True), (3, 4.0)):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, queries)
    assert len(p.generate(2**63 - 1, good, 2, 1)["test"]) == 1


@pytest.mark.parametrize("demos", range(2, 7))
def test_inputs_are_setting_neutral_deterministic_distinct_and_prefix_stable(demos):
    p = _load()
    default = p.generate(17, {"cap_policy": "both_sides"}, demos, 4)
    alternative = p.generate(17, {"cap_policy": "cue_controlled_side"}, demos, 4)
    assert _inputs(default) == _inputs(alternative)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(default)}) == demos + 4
    assert default == p.generate(17, {"cap_policy": "both_sides"}, demos, 4)
    assert all(a["output"] != b["output"] for a, b in zip(default["train"], alternative["train"]))

    maximum = p.generate(17, {"cap_policy": "both_sides"}, 6, 4)
    one_query = p.generate(17, {"cap_policy": "both_sides"}, demos, 1)
    assert default["train"] == maximum["train"][:demos]
    assert default["test"] == maximum["test"]
    assert one_query["train"] == default["train"]
    assert one_query["test"] == default["test"][:1]


def test_queries_cover_small_large_boundary_and_substantive_30_by_30():
    p = _load()
    episode = p.generate(3, {"cap_policy": "cue_controlled_side"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(10, 14), (16, 20), (24, 27), (30, 30)]
    analyses = [p.analyze(pair["input"]) for pair in episode["test"]]
    assert all(len(row["targets"]) >= 2 for row in analyses)
    assert all(sorted(run["length"] for run in row["controls"]) == [4, 5] for row in analyses)
    assert all(row["nearest_control_length"] in (4, 5) for row in analyses)
    large = analyses[-1]
    assert large["height"] == large["width"] == 30
    assert large["nonzero_count"] >= 85
    assert large["target_count"] >= 14
    assert large["decoy_count"] >= 10
    assert large["touches_boundary"] is True


def test_outputs_use_cue_selected_control_length_as_side_intermediate():
    p = _load()
    first = p.generate(29, {"cap_policy": "cue_controlled_side"}, 2, 4)
    assert p.analyze(first["train"][0]["input"])["selected_side"] == "left"
    assert p.analyze(first["train"][1]["input"])["selected_side"] == "right"
    for policy in SETTINGS:
        episode = p.generate(29, {"cap_policy": policy}, 3, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == p.apply_rule(pair["input"], policy)
    witness = p.generate(29, {"cap_policy": "cue_controlled_side"}, 3, 4)["test"][-1]
    intended = p.apply_rule(witness["input"], "cue_controlled_side")
    wrong = p.apply_rule(witness["input"], "farthest_control_side")
    assert intended != wrong
    assert p.changed_cells(intended, wrong) >= 20


def test_first_turn_projection_is_count_stable_and_private_fields_are_hidden():
    p = _load()
    four = p.generate(9, {"cap_policy": "cue_controlled_side"}, 3, 4)
    one = p.generate(9, {"cap_policy": "cue_controlled_side"}, 3, 1)
    visible_four = public_challenge_bytes({"train": four["train"], "test": [{"input": four["test"][0]["input"]}]})
    visible_one = public_challenge_bytes({"train": one["train"], "test": [{"input": one["test"][0]["input"]}]})
    assert visible_four == visible_one
    for forbidden in (b"cue_controlled_side", b"cap_policy", b"program_solution"):
        assert forbidden not in visible_four
    assert json.dumps(four["test"][0]["output"], separators=(",", ":")).encode() not in visible_four
    assert json.dumps(four["test"][1]["input"], separators=(",", ":")).encode() not in visible_four


@pytest.mark.parametrize("demos", (2, 3, 6))
def test_visible_demonstrations_reject_declared_finite_rivals(demos):
    p = _load()
    for seed in range(8):
        for policy in SETTINGS:
            episode = p.generate(seed, {"cap_policy": policy}, demos, 4)
            report = p.audit_episode(episode, policy)
            assert report["harmful_survivors"] == [], (seed, policy, demos, report)
            assert report["selected_setting"] == policy
            assert report["queries_checked"] == 4
