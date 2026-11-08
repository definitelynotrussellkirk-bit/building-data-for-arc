from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "1b6b40a92e4f"
TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load(PARAMETRIC / "adapter.py", f"test_{TASK_ID}_adapter")


def _prototype():
    return _load(PARAMETRIC / "prototype.py", f"test_{TASK_ID}_prototype")


def _generator():
    return _load(TASK_HOME / "generator.py", f"test_{TASK_ID}_generator")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_controls_are_exact_unknown_keys_rejected_and_self_check_is_semantic():
    generator = _generator()
    with pytest.raises(ValueError):
        generator.generate(17, 3, difficulty="medium", unknown_axis="accepted")
    grid = generator.generate(17, 3, difficulty="medium", grid_h=9, grid_w=10)
    assert (len(grid), len(grid[0])) == (9, 10)
    assert generator.observe_overrides(grid) == {"grid_h": 9, "grid_w": 10}
    assert generator.self_check(grid) == []

    invalid = [[0] * 10 for _ in range(9)]
    invalid[0][0] = invalid[2][2] = 2
    invalid[5][5] = 3
    invalid[8][9] = 9
    errors = generator.self_check(invalid)
    assert any("color" in error for error in errors)
    assert any("connected" in error for error in errors)


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_base_sampler_always_satisfies_repaired_contract(difficulty):
    generator = _generator()
    for seed in range(8):
        for sample_index in range(4):
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []


def test_contract_and_default_program_are_exact_canonical_bytes():
    adapter = _adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"green_pose": ["as_is", "rotate_cw"]},
        "default": {"green_pose": "as_is"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }
    assert adapter.program({"green_pose": "as_is"}) == _canonical_program()
    assert adapter.program({"green_pose": "rotate_cw"}) != _canonical_program()


def test_strict_settings_counts_and_seed_types():
    adapter = _adapter()
    for bad in ({}, {"green_pose": "as_is", "extra": 1}, {"green_pose": "ccw"}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for seed, demos, queries in ((True, 2, 4), (1, 1, 4), (1, 7, 4), (1, 2, 0), (1, 2, 5), (1, True, 4), (1, 2, False)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"green_pose": "as_is"}, demos, queries)


def test_inputs_are_setting_independent_prefix_stable_distinct_and_identifying():
    adapter = _adapter()
    proto = _prototype()
    canonical = adapter.generate(23, {"green_pose": "as_is"}, 6, 4)
    rotated = adapter.generate(23, {"green_pose": "rotate_cw"}, 6, 4)
    assert _inputs(canonical) == _inputs(rotated)
    serial = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serial) == len(set(serial)) == 10
    assert adapter.generate(23, {"green_pose": "as_is"}, 2, 1)["train"] == canonical["train"][:2]
    assert adapter.generate(23, {"green_pose": "as_is"}, 2, 1)["test"] == canonical["test"][:1]
    for mode, episode in (("as_is", canonical), ("rotate_cw", rotated)):
        rival = "rotate_cw" if mode == "as_is" else "as_is"
        assert all(proto.transform(pair["input"], mode) == pair["output"] for pair in episode["train"])
        assert all(proto.transform(pair["input"], rival) != pair["output"] for pair in episode["train"][:2])
        assert proto.teaching_check(episode["train"][:2], mode)["survivors"] == [mode]


def test_four_queries_cover_boundary_and_substantive_30x30_stress():
    adapter = _adapter()
    proto = _prototype()
    episode = adapter.generate(41, {"green_pose": "rotate_cw"}, 2, 4)
    assert len(episode["test"]) == 4
    shapes = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert (30, 30) in shapes
    stress = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    metrics = proto.input_metrics(stress)
    assert metrics["foreground_cells"] >= 70
    assert len(metrics["boundary_sides"]) >= 2
    assert metrics["red_components"] == metrics["green_components"] == 1


def test_public_turn_hides_program_setting_future_queries_and_answers():
    adapter = _adapter()
    episode = adapter.generate(71, {"green_pose": "rotate_cw"}, 3, 4)
    turn = adapter.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    raw = public_challenge_bytes(turn)
    assert public_challenge_id(turn) == hashlib.sha256(raw).hexdigest()
    assert b"green_pose" not in raw and b"program_solution" not in raw and b"rotate_cw" not in raw
    hidden = copy.deepcopy(episode)
    hidden["test"][0]["output"][0][0] = (hidden["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(adapter.public_turn(hidden, 0)) == public_challenge_id(turn)


def test_generation_is_deterministic_fresh_and_counterfactual_changes_output():
    adapter = _adapter()
    proto = _prototype()
    first = adapter.generate(89, {"green_pose": "rotate_cw"}, 3, 4)
    second = adapter.generate(89, {"green_pose": "rotate_cw"}, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(89, {"green_pose": "rotate_cw"}, 3, 4) == second
    witness = second["train"][0]["input"]
    assert proto.intermediate(witness, "rotate_cw") != proto.intermediate(witness, "as_is")
    assert proto.transform(witness, "rotate_cw") != proto.transform(witness, "as_is")


def test_reusable_bounded_audit_report_without_racket():
    audit = _load(PARAMETRIC / "audit.py", f"test_{TASK_ID}_audit")
    report = audit.build_report(seeds=2, racket_seeds=())
    assert report["status"] == "passed"
    assert report["task_id"] == TASK_ID
    assert report["settings"] == ["as_is", "rotate_cw"]
    assert report["episodes"] == 2 * 5 * 4 * 2
    assert report["racket_evaluations"] == 0
    assert report["rival_survivors"] == []
    assert report["stress_30x30_checks"] == 2
    assert report["training_admitted"] is False
