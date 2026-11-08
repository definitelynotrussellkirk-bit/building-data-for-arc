from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
TASK_ID = "70abd9105769"
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
PROMOTION = HOME / "promotion.json"
PROBE = HOME / "adversarial_probe.py"
SWEEP = HOME / "semantic_sweep.py"


def _load(name: str, path: Path):
    assert path.is_file(), path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


@pytest.fixture(scope="module")
def p():
    return _load("parametric_70abd9105769", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_70abd9105769_adapter", ADAPTER)


def test_required_artifacts_and_exact_canonical_default(p):
    required = (
        PROTOTYPE,
        ADAPTER,
        PROMOTION,
        PROBE,
        SWEEP,
        HOME / "canonical.rkt",
        HOME / "majority_frame.rkt",
        HOME / "skip_stage_a.rkt",
    )
    for path in required:
        assert path.is_file(), path
    canonical = _canonical_program()
    assert p.program({"mode": "canonical"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == p.CANONICAL_SHA256
    assert p.program({"mode": "majority_frame"}) != canonical


def test_strict_settings_counts_and_grid_validation(p, adapter):
    for bad in ({}, {"mode": "bad"}, {"mode": True}, {"mode": "canonical", "extra": 1}):
        with pytest.raises(ValueError):
            p.program(bad)
    for kwargs in (
        {"seed": True, "settings": p.DEFAULT, "demos": 3, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 1, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 7, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 3},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 5},
    ):
        with pytest.raises(ValueError):
            adapter.generate(**kwargs)
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]], [[0, 1], [0, 2]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_scene_has_real_stage_dependency_and_crossed_decoys(p):
    scene = p.build_scene(17, 0, 20, 24, profile="demo_a")
    grid = scene["grid"]
    facts = p.scene_facts(grid)
    assert facts["target_color"] == scene["target_color"]
    assert facts["object_majority_color"] == scene["target_color"]
    assert facts["pixel_majority_color"] == scene["pixel_decoy_color"]
    assert facts["pixel_majority_color"] != facts["object_majority_color"]
    assert facts["target_center_bbox"] != facts["all_center_bbox"]
    assert facts["object_counts"][scene["target_color"]] > facts["object_counts"][scene["pixel_decoy_color"]]
    assert facts["pixel_counts"][scene["target_color"]] < facts["pixel_counts"][scene["pixel_decoy_color"]]

    canonical = p.transform(grid, {"mode": "canonical"})
    framed = p.transform(grid, {"mode": "majority_frame"})
    skipped = p.skip_stage_a_transform(grid)
    assert canonical == p.stage_a_grid(grid)
    assert framed != canonical
    assert skipped != framed
    assert p.frame_cells(canonical, scene["target_color"])
    assert p.changed_cells(canonical, framed, old=0, new=9) >= 4


def test_generation_is_deterministic_setting_neutral_and_two_demo_identifiable(p):
    random.seed(4001)
    state = random.getstate()
    canonical = p.generate(101, {"mode": "canonical"}, demos=2, queries=4)
    assert random.getstate() == state
    assert canonical == p.generate(101, {"mode": "canonical"}, demos=2, queries=4)
    framed = p.generate(101, {"mode": "majority_frame"}, demos=2, queries=4)
    assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
        pair["input"] for pair in framed["train"] + framed["test"]
    ]
    assert canonical["certificate"]["survivors"] == [{"mode": "canonical"}]
    assert framed["certificate"]["survivors"] == [{"mode": "majority_frame"}]
    assert all(framed["certificate"]["shortcut_refutations"].values())
    assert len({p.grid_sha256(pair["input"]) for pair in framed["train"] + framed["test"]}) == 6
    maximum = p.generate(101, {"mode": "majority_frame"}, demos=6, queries=4)
    assert len(maximum["train"]) == 6 and len(maximum["test"]) == 4


def test_fourth_query_is_substantive_30x30_boundary_crossing_stress(p):
    episode = p.generate(303, {"mode": "majority_frame"}, demos=2, queries=4)
    grid = episode["test"][-1]["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 180
    assert {int(r >= 15) * 2 + int(c >= 15) for r, c in nonzero} == {0, 1, 2, 3}
    assert min(r for r, _ in nonzero) == 0
    assert max(r for r, _ in nonzero) == 29
    assert min(c for _, c in nonzero) == 0
    assert max(c for _, c in nonzero) == 29


def test_racket_replays_both_rules_and_skip_a_witness(p):
    scene = p.build_scene(44, 1, 21, 25, profile="demo_b")
    grid = scene["grid"]
    with p.RacketRunner() as execute:
        for settings in p.SETTINGS:
            assert execute(p.program(settings), grid) == p.transform(grid, settings)
        skipped = execute(p.skip_stage_a_program(), grid)
        framed = execute(p.program({"mode": "majority_frame"}), grid)
        assert skipped == p.skip_stage_a_transform(grid)
        assert skipped != framed


def test_public_projection_and_first_turn_hide_private_and_future_data(p):
    episode = p.generate(77, {"mode": "majority_frame"}, demos=3, queries=4)
    body = public_challenge_bytes(episode)
    visible = json.loads(body)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert len(visible["test"]) == 4

    public_id = public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"mode": "canonical"}
    changed["program_solution"] = "private replacement"
    changed["test"][0]["output"][0][0] ^= 1
    assert public_challenge_id(changed) == public_id

    first = p.public_turn_bytes(episode, 0)
    future = copy.deepcopy(episode)
    future["test"][2]["input"][2][2] ^= 1
    future["test"][3]["output"][3][3] ^= 1
    future["program_solution"] = "changed"
    assert p.public_turn_bytes(future, 0) == first
    now = copy.deepcopy(episode)
    now["test"][0]["input"][2][2] ^= 1
    assert p.public_turn_bytes(now, 0) != first


def test_promotion_contract_and_adapter_are_strict(p, adapter, monkeypatch):
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/70abd9105769/workspace/parametric/adapter.py",
        "parameters": {"mode": ["canonical", "majority_frame"]},
        "default": {"mode": "canonical"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/70abd9105769/workspace/parametric/prototype.py",
            "generators/70abd9105769/workspace/parametric/canonical.rkt",
            "generators/70abd9105769/workspace/parametric/majority_frame.rkt",
            "generators/70abd9105769/workspace/parametric/skip_stage_a.rkt",
        ],
    }
    assert adapter.program({"mode": "canonical"}) == _canonical_program()
    monkeypatch.setattr(p, "RacketRunner", lambda: pytest.fail("adapter generation must be Racket-free"))
    claims = adapter.generate(9, {"mode": "majority_frame"}, 2, 4)
    assert set(claims) == {"train", "test", "program_solution"}


def test_bounded_semantic_sweep_finds_no_surviving_shortcut(p):
    sweep = _load("semantic_sweep_70abd", SWEEP)
    result = sweep.run(range(20), demos=2)
    assert result["episodes"] == 40
    assert result["ambiguous_episodes"] == 0
    assert result["surviving_rivals"] == {}
    assert result["crossed_controls"]["target_colors"] >= 5
    assert result["crossed_controls"]["target_center_bboxes"] >= 8
    assert result["crossed_controls"]["pixel_decoy_colors"] >= 5


def test_protected_racket_rival_bank_is_total(p):
    probe = _load("adversarial_probe_70abd_totality", PROBE)
    banks = probe.racket_rivals()
    with p.RacketRunner() as execute:
        for mode, bank in banks.items():
            episode = p.generate(0, {"mode": mode}, demos=2, queries=4)
            for name, source in bank.items():
                output = execute(source, episode["train"][0]["input"])
                assert len(output) == len(episode["train"][0]["input"]), name
                assert len(output[0]) == len(episode["train"][0]["input"][0]), name


def test_minimum_lesson_crosses_numeric_rank_geometry_and_size_profiles(p):
    first = p.build_scene(23, 0, 20, 24, profile="demo_a")
    second = p.build_scene(23, 1, 21, 25, profile="demo_b")
    assert first["target_color"] != second["target_color"]
    assert first["target_center_bbox"] != second["target_center_bbox"]
    assert first["target_count"] != second["target_count"]
    assert first["target_pixel_count"] != second["target_pixel_count"]
    assert first["pixel_decoy_color"] != second["pixel_decoy_color"]


def test_certificate_rejects_forged_program_labels_duplicates_and_pair_shape(p):
    episode = p.generate(88, {"mode": "majority_frame"}, demos=2, queries=4)

    forged_program = copy.deepcopy(episode)
    forged_program["program_solution"] = p.program({"mode": "canonical"})
    with pytest.raises(ValueError, match="program"):
        p.certify(forged_program)

    forged_label = copy.deepcopy(episode)
    forged_label["train"][0]["output"][0][0] = (forged_label["train"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        p.certify(forged_label)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    with pytest.raises(ValueError, match="distinct"):
        p.certify(duplicate)

    extra_field = copy.deepcopy(episode)
    extra_field["train"][0]["private"] = True
    with pytest.raises(ValueError, match="exactly input and output"):
        p.certify(extra_field)
