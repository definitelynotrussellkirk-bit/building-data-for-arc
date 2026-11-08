from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "b6f34233d788"
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


def test_base_exact_controls_and_semantic_self_check():
    generator = _generator()
    with pytest.raises(ValueError):
        generator.generate(17, 3, unknown_axis="accepted")
    grid = generator.generate(17, 3, difficulty="medium", grid_h=14, grid_w=17, n=4)
    assert (len(grid), len(grid[0])) == (14, 17)
    assert generator.observe_overrides(grid) == {"grid_h": 14, "grid_w": 17, "n": 4}
    assert generator.self_check(grid) == []

    invalid = [[0] * 12 for _ in range(10)]
    invalid[1][1] = invalid[1][2] = 2
    invalid[5][5] = invalid[5][6] = 2  # repeated color and disconnected object
    invalid[8][8] = 9
    errors = generator.self_check(invalid)
    assert any("distinct" in error or "component" in error for error in errors)
    assert any("hole" in error for error in errors)


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_base_sampler_satisfies_repaired_contract(difficulty):
    generator = _generator()
    for seed in range(8):
        for sample_index in range(4):
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []


def test_contract_and_exact_canonical_default():
    adapter = _adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"ranking": ["holes_then_area", "area_then_holes"]},
        "default": {"ranking": "holes_then_area"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }
    assert adapter.program({"ranking": "holes_then_area"}) == _canonical_program()
    assert adapter.program({"ranking": "area_then_holes"}) != _canonical_program()


def test_strict_settings_counts_and_seed_types():
    adapter = _adapter()
    for bad in ({}, {"ranking": "holes_then_area", "extra": 1}, {"ranking": "left_to_right"}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for seed, demos, queries in ((True, 2, 4), (1, 1, 4), (1, 7, 4), (1, 2, 0), (1, 2, 5), (1, True, 4), (1, 2, False)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"ranking": "holes_then_area"}, demos, queries)


def test_inputs_are_setting_independent_prefix_stable_distinct_and_identifying():
    adapter = _adapter()
    proto = _prototype()
    holes = adapter.generate(23, {"ranking": "holes_then_area"}, 6, 4)
    area = adapter.generate(23, {"ranking": "area_then_holes"}, 6, 4)
    assert _inputs(holes) == _inputs(area)
    serial = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(holes)]
    assert len(serial) == len(set(serial)) == 10
    assert adapter.generate(23, {"ranking": "holes_then_area"}, 2, 1)["train"] == holes["train"][:2]
    assert adapter.generate(23, {"ranking": "holes_then_area"}, 2, 1)["test"] == holes["test"][:1]
    for mode, episode in (("holes_then_area", holes), ("area_then_holes", area)):
        rival = "area_then_holes" if mode == "holes_then_area" else "holes_then_area"
        assert all(proto.transform(pair["input"], mode) == pair["output"] for pair in episode["train"])
        assert all(proto.transform(pair["input"], rival) != pair["output"] for pair in episode["train"][:2])
        assert proto.teaching_check(episode["train"][:2], mode)["survivors"] == [mode]


def test_four_queries_cover_topology_boundary_and_30x30_stress():
    adapter = _adapter()
    proto = _prototype()
    episode = adapter.generate(41, {"ranking": "area_then_holes"}, 2, 4)
    assert len(episode["test"]) == 4
    shapes = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert (30, 30) in shapes
    stress = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    metrics = proto.input_metrics(stress)
    assert metrics["objects"] >= 5
    assert metrics["foreground_cells"] >= 60
    assert max(metrics["hole_counts"]) >= 2
    assert 0 in metrics["hole_counts"]
    assert len(metrics["boundary_sides"]) >= 2


def test_public_turn_hides_private_fields_and_is_first_turn_count_agnostic():
    adapter = _adapter()
    episode = adapter.generate(71, {"ranking": "area_then_holes"}, 3, 4)
    turn = adapter.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    raw = public_challenge_bytes(turn)
    assert public_challenge_id(turn) == hashlib.sha256(raw).hexdigest()
    assert b"ranking" not in raw and b"program_solution" not in raw and b"area_then_holes" not in raw
    hidden = copy.deepcopy(episode)
    hidden["test"][0]["output"][0][0] = (hidden["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(adapter.public_turn(hidden, 0)) == public_challenge_id(turn)


def test_generation_is_deterministic_fresh_and_wrong_intermediate_changes_order():
    adapter = _adapter()
    proto = _prototype()
    first = adapter.generate(89, {"ranking": "area_then_holes"}, 3, 4)
    second = adapter.generate(89, {"ranking": "area_then_holes"}, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(89, {"ranking": "area_then_holes"}, 3, 4) == second
    witness = second["train"][0]["input"]
    descriptors = proto.intermediate(witness)
    assert any(row["holes"] > other["holes"] and row["area"] < other["area"] for row in descriptors for other in descriptors)
    assert proto.transform(witness, "holes_then_area") != proto.transform(witness, "area_then_holes")


def test_reusable_bounded_audit_report_without_racket():
    audit = _load(PARAMETRIC / "audit.py", f"test_{TASK_ID}_audit")
    report = audit.build_report(seeds=2, racket_seeds=())
    assert report["status"] == "passed"
    assert report["task_id"] == TASK_ID
    assert report["settings"] == ["holes_then_area", "area_then_holes"]
    assert report["episodes"] == 2 * 5 * 4 * 2
    assert report["racket_evaluations"] == 0
    assert report["rival_survivors"] == []
    assert report["stress_30x30_checks"] == 2
    assert report["training_admitted"] is False


def test_all_private_grids_stay_within_arc_30_by_30_limit():
    adapter = _adapter()
    for seed in range(16):
        for ranking in ("holes_then_area", "area_then_holes"):
            episode = adapter.generate(seed, {"ranking": ranking}, 6, 4)
            for pair in episode["train"] + episode["test"]:
                for grid in (pair["input"], pair["output"]):
                    assert 1 <= len(grid) <= 30
                    assert 1 <= len(grid[0]) <= 30
