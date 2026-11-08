"""Focused tests for the proposed episode-level axis-mode rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "parametric prototype.py has not been implemented"
    spec = importlib.util.spec_from_file_location("axis_mode_prototype", PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_declares_three_episode_level_axis_modes_with_canonical_default():
    proto = _load_prototype()
    assert proto.AXIS_MODES == ("both", "horizontal", "vertical")
    assert proto.DEFAULT == "both"
    assert [proto.parameters(seed) for seed in range(3)] == [
        {"axis_mode": "both"},
        {"axis_mode": "horizontal"},
        {"axis_mode": "vertical"},
    ]
    with pytest.raises((TypeError, ValueError)):
        proto.parameters(True)


def test_instantiation_keeps_exact_default_and_disables_only_the_selected_rival_axis():
    proto = _load_prototype()
    root = proto.find_root(PROTOTYPE_PATH)
    canonical = proto.canonical_program(root)

    assert proto.instantiate(canonical, "both") == canonical
    horizontal = proto.instantiate(canonical, "horizontal")
    vertical = proto.instantiate(canonical, "vertical")
    assert len({canonical, horizontal, vertical}) == 3
    assert horizontal.count("(and (= c1 c2) #f)") == 1
    assert horizontal.count("(and (= r1 r2) #f)") == 0
    assert vertical.count("(and (= r1 r2) #f)") == 1
    assert vertical.count("(and (= c1 c2) #f)") == 0

    with pytest.raises(ValueError, match="axis_mode"):
        proto.instantiate(canonical, "diagonal")
    with pytest.raises(ValueError, match="guard"):
        proto.instantiate("(rule! (lambda (g) g))", "horizontal")


def test_seeded_fixtures_are_lawful_complete_diamond_inputs_with_both_axis_cues():
    proto = _load_prototype()
    for seed in range(3):
        fixtures = proto.fixture_inputs(seed)
        assert len(fixtures) == 4
        assert len({repr(grid) for grid in fixtures}) == 4
        for grid in fixtures:
            assert grid and grid[0]
            assert all(len(row) == len(grid[0]) for row in grid)
            assert {value for row in grid for value in row} <= {0, 2}
            centers = proto.diamond_centers(grid)
            assert 3 <= len(centers) <= 7
            assert proto.visible_connection_axes(grid) == {"horizontal", "vertical"}
            assert sum(value == 2 for row in grid for value in row) == 4 * len(centers)


def test_racket_labels_match_canonical_and_all_axis_modes_diverge_on_one_input():
    from arc_repl.racket_bridge import RacketBridge

    proto = _load_prototype()
    root = proto.find_root(PROTOTYPE_PATH)
    record = proto.canonical_record(root)
    canonical = record["program_solution"]
    bridge = RacketBridge()
    try:
        for pair in record["train"] + record["test"]:
            assert proto.execute(bridge, canonical, pair["input"]) == pair["output"]

        witness = proto.fixture_inputs(42)[0]
        before = json.dumps(witness)
        outputs = {
            mode: proto.execute(bridge, proto.instantiate(canonical, mode), witness)
            for mode in proto.AXIS_MODES
        }
        assert len({json.dumps(output) for output in outputs.values()}) == 3
        assert json.dumps(witness) == before
    finally:
        bridge.shutdown()


def test_complete_episodes_fix_one_mode_and_distinguish_every_parameter_rival():
    from arc_repl.racket_bridge import RacketBridge

    proto = _load_prototype()
    root = proto.find_root(PROTOTYPE_PATH)
    canonical = proto.canonical_program(root)
    bridge = RacketBridge()
    try:
        for seed, expected_mode in enumerate(proto.AXIS_MODES):
            episode = proto.episode(seed, canonical, bridge)
            assert episode["seed"] == seed
            assert episode["parameters"] == {"axis_mode": expected_mode}
            assert episode["program"] == proto.instantiate(canonical, expected_mode)
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert {row["axis_mode"] for row in episode["rivals"]} == (
                set(proto.AXIS_MODES) - {expected_mode}
            )
            assert all(row["status"] == "distinguished" for row in episode["rivals"])
            assert all(row["demo_differences"] for row in episode["rivals"])
            assert all(row["query_differs"] for row in episode["rivals"])

            public = proto.public_challenge(episode)
            assert public["train"] == episode["train"]
            assert public["test"] == [{"input": episode["test"][0]["input"]}]
            assert "parameters" not in public
            assert "program" not in public
            assert "output" not in public["test"][0]
    finally:
        bridge.shutdown()


def test_materialize_retains_racket_evidence_and_masks_public_queries(tmp_path):
    proto = _load_prototype()
    report = proto.materialize(tmp_path)

    assert report["status"] == "prototype"
    assert report["task_id"] == proto.TASK_ID
    assert report["parameter"] == {
        "axis_mode": {
            "allowed": list(proto.AXIS_MODES),
            "original_default": proto.DEFAULT,
        }
    }
    assert report["default_program_exact"] is True
    assert report["canonical_pairs_verified"] == 4
    assert report["episode_count"] == 3
    assert report["all_rivals_distinguished"] is True

    for seed, mode in enumerate(proto.AXIS_MODES):
        private = json.loads((tmp_path / "private" / f"episode-{seed}.json").read_text())
        public = json.loads((tmp_path / "public" / f"episode-{seed}.json").read_text())
        rule_bytes = (tmp_path / "private" / "rules" / f"axis-mode-{mode}.rkt").read_bytes()
        assert private["parameters"] == {"axis_mode": mode}
        assert private["program_sha256"] == proto._sha256(rule_bytes)
        assert public == proto.public_challenge(private)
        assert all("output" not in pair for pair in public["test"])
        assert all(row["status"] == "distinguished" for row in private["rivals"])

    witness = json.loads((tmp_path / "private" / "shared-input-witness.json").read_text())
    assert set(witness["outputs"]) == set(proto.AXIS_MODES)
    assert len({json.dumps(output) for output in witness["outputs"].values()}) == 3

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-prototype-evidence-v1"
    assert manifest["files"]
    for relative, digest in manifest["files"].items():
        assert proto._sha256((tmp_path / relative).read_bytes()) == digest
