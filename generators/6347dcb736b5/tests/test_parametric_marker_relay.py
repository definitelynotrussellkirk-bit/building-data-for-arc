from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "6347dcb736b5"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing planned parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules():
    prototype = _load("bbox_marker_relay_test_prototype", PARAMETRIC / "prototype.py")
    adapter = _load("bbox_marker_relay_test_adapter", PARAMETRIC / "adapter.py")
    return prototype, adapter


def canonical_program() -> str:
    ledger = canonical_path(ROOT)
    programs = set()
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _outline(boxes, height, width):
    output = [[0] * width for _ in range(height)]
    for r1, c1, r2, c2, color in boxes:
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if row in (r1, r2) or col in (c1, c2):
                    output[row][col] = color
    return output


def test_adapter_exposes_byte_exact_canonical_default_and_distinct_relay_program():
    _prototype, adapter = modules()
    canonical = adapter.program({"outline_scope": "all_objects"})
    relay = adapter.program({"outline_scope": "marker_relay"})
    assert canonical == canonical_program()
    assert canonical.encode() == (PARAMETRIC / "rules" / "all_objects.rkt").read_bytes()
    assert relay == (PARAMETRIC / "rules" / "marker_relay.rkt").read_text(encoding="utf-8")
    assert relay != canonical
    assert relay.strip().startswith("(rule!")


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"outline_scope": "all_objects", "extra": 1},
        {"outline_scope": "unknown"},
        {"outline_scope": True},
    ],
)
def test_adapter_rejects_undeclared_settings(settings):
    _prototype, adapter = modules()
    with pytest.raises((TypeError, ValueError), match="outline_scope|settings"):
        adapter.program(settings)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"seed": True, "demos": 2, "queries": 4}, "seed"),
        ({"seed": -1, "demos": 2, "queries": 4}, "seed"),
        ({"seed": 0, "demos": 1, "queries": 4}, "demos"),
        ({"seed": 0, "demos": 7, "queries": 4}, "demos"),
        ({"seed": 0, "demos": 2, "queries": 1}, "queries"),
        ({"seed": 0, "demos": 2, "queries": 5}, "queries"),
    ],
)
def test_episode_count_and_seed_boundaries(kwargs, message):
    _prototype, adapter = modules()
    with pytest.raises((TypeError, ValueError), match=message):
        adapter.generate(settings={"outline_scope": "all_objects"}, **kwargs)


def test_hand_derived_marker_relay_fixture_uses_new_corner_color_to_select_remote_partner():
    prototype, _adapter = modules()
    grid = [[0] * 12 for _ in range(9)]
    # Selected color 2: source box 2:4 x 1:3, remote payload 5:8 x 8:11.
    for row, col in [(2, 2), (3, 1), (3, 2), (3, 3), (4, 2)]:
        grid[row][col] = 2
    for row, col in [(5, 9), (6, 8), (6, 9), (6, 10), (6, 11), (7, 9), (8, 9)]:
        grid[row][col] = 2
    # Distractor repeated color 5.
    for row, col in [(0, 8), (1, 7), (1, 8), (1, 9), (2, 8)]:
        grid[row][col] = 5
    for row, col in [(5, 1), (6, 0), (6, 1), (6, 2), (6, 3), (7, 1), (8, 1)]:
        grid[row][col] = 5
    grid[1][1] = 9

    analysis = prototype.analyze_scene(grid)
    assert prototype.validate_scene(grid) == []
    assert analysis["relay_cell"] == (2, 1)
    assert grid[2][1] == 0
    assert analysis["relay_color"] == 2
    assert analysis["selected_component_count"] == 2
    expected = _outline(
        [(2, 1, 4, 3, 2), (5, 8, 8, 11, 2)],
        height=9,
        width=12,
    )
    assert prototype.output_for(grid, "marker_relay") == expected
    assert prototype.output_for(grid, "all_objects") != expected


@pytest.mark.parametrize("seed", [0, 17, 2**31 + 9])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generated_episodes_are_deterministic_distinct_setting_matched_and_semantically_valid(seed, demos):
    prototype, adapter = modules()
    all_objects = adapter.generate(seed, {"outline_scope": "all_objects"}, demos, 4)
    again = adapter.generate(seed, {"outline_scope": "all_objects"}, demos, 4)
    relay = adapter.generate(seed, {"outline_scope": "marker_relay"}, demos, 4)
    assert all_objects == again
    pairs_a = all_objects["train"] + all_objects["test"]
    pairs_b = relay["train"] + relay["test"]
    assert [pair["input"] for pair in pairs_a] == [pair["input"] for pair in pairs_b]
    assert len({prototype.grid_digest(pair["input"]) for pair in pairs_a}) == demos + 4
    for pair_a, pair_b in zip(pairs_a, pairs_b, strict=True):
        assert pair_a["output"] != pair_b["output"]
        assert prototype.validate_scene(pair_a["input"]) == []
        analysis = prototype.analyze_scene(pair_a["input"])
        assert pair_a["input"][analysis["relay_cell"][0]][analysis["relay_cell"][1]] == 0
        assert analysis["selected_component_count"] == 2
        assert analysis["distractor_repeated_component_count"] == 2
        assert analysis["marker_neighbor_hits"] == 1
        assert pair_a["output"] == prototype.output_for(pair_a["input"], "all_objects")
        assert pair_b["output"] == prototype.output_for(pair_b["input"], "marker_relay")


def test_query_schedule_has_real_minimum_intermediate_large_and_30x30_stress():
    prototype, adapter = modules()
    episode = adapter.generate(23, {"outline_scope": "marker_relay"}, 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(8, 12), (14, 18), (22, 26), (30, 30)]
    stress = episode["test"][-1]["input"]
    analysis = prototype.analyze_scene(stress)
    assert len(analysis["objects_without_marker"]) == 8
    assert sum(value != 0 for row in stress for value in row) >= 90
    assert {0, 29} <= {
        coordinate
        for obj in analysis["objects_without_marker"]
        for coordinate in (obj["bbox"][0], obj["bbox"][2])
    }
    assert {0, 29} <= {
        coordinate
        for obj in analysis["objects_without_marker"]
        for coordinate in (obj["bbox"][1], obj["bbox"][3])
    }


def test_two_demo_teaching_core_refutes_declared_program_and_shortcut_rivals():
    prototype, adapter = modules()
    expected = {
        "all_objects": {
            "marker_relay",
            "fill_all_boxes",
            "merge_same_color_boxes",
            "omit_marker",
        },
        "marker_relay": {
            "all_objects",
            "source_only",
            "smallest_repeated_color",
            "largest_repeated_color",
            "smallest_pair_area",
            "largest_pair_area",
            "fixed_first_demo_color",
            "include_marker",
        },
    }
    for seed in range(12):
        for scope in ("all_objects", "marker_relay"):
            episode = adapter.generate(seed, {"outline_scope": scope}, 2, 4)
            audit = prototype.audit_teaching_set(episode["train"], scope)
            assert audit["setting_survivors"] == [scope]
            assert set(audit["rivals"]) == expected[scope]
            assert all(row["refuted"] for row in audit["rivals"].values())


def test_promotion_contract_declares_two_settings_two_to_six_demos_and_four_queries():
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/6347dcb736b5/workspace/parametric/adapter.py",
        "parameters": {"outline_scope": ["all_objects", "marker_relay"]},
        "default": {"outline_scope": "all_objects"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/6347dcb736b5/workspace/parametric/prototype.py",
            "generators/6347dcb736b5/workspace/parametric/rules/all_objects.rkt",
            "generators/6347dcb736b5/workspace/parametric/rules/marker_relay.rkt",
        ],
    }


def test_public_turn_reveals_one_query_and_is_invariant_to_private_fields():
    prototype, adapter = modules()
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(31, {"outline_scope": "marker_relay"}, 3, 4)
    episode["settings"] = {"outline_scope": "marker_relay"}
    episode["seed"] = 31
    turn = prototype.public_turn(episode, 2)
    assert set(turn) == {"train", "test"}
    assert turn["train"] == episode["train"]
    assert turn["test"] == [{"input": episode["test"][2]["input"]}]
    mutated = dict(episode)
    mutated["settings"] = {"outline_scope": "private-change"}
    mutated["seed"] = 999
    mutated["program_solution"] = "private-change"
    assert public_challenge_bytes(prototype.public_turn(mutated, 2)) == public_challenge_bytes(turn)
    assert public_challenge_id(prototype.public_turn(mutated, 2)) == public_challenge_id(turn)
    assert public_challenge_id(turn) == hashlib.sha256(public_challenge_bytes(turn)).hexdigest()


def test_evidence_builder_runs_protected_racket_finite_audit_and_public_projection(tmp_path):
    verifier = _load("bbox_marker_relay_test_verify", PARAMETRIC / "verify.py")
    summary = verifier.build_evidence(tmp_path, seeds=(0, 17), demos=3)
    assert summary["status"] == "passed"
    assert summary["settings"] == ["all_objects", "marker_relay"]
    assert summary["seeds"] == [0, 17]
    assert summary["demonstrations"] == 3
    assert summary["queries_per_episode"] == 4
    assert summary["protected_racket_evaluations"] == 28
    assert summary["public_files"] == 16
    assert summary["finite_audit"]["jobs"] == 72
    assert summary["finite_audit"]["failures"] == []
    assert summary["protected_execution"]["failures"] == []
    public_files = sorted((tmp_path / "public").glob("*.json"))
    assert len(public_files) == 16
    assert all(path.stem == hashlib.sha256(path.read_bytes()).hexdigest() for path in public_files)
    index = json.loads((tmp_path / "projection-index.json").read_text(encoding="utf-8"))
    assert len(index["projections"]) == 16
    assert all(set(row) == {"public_id", "filename", "seed", "outline_scope", "query_index"}
               for row in index["projections"])
