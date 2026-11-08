"""Focused checks for the proposed episode-level connectivity prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "eefadafb2b7b"
ROOT = find_root(__file__)
TASK_DIR = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "eefadafb2b7b_parametric_connectivity", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_connectivity_contract_is_bounded_and_default_is_exact_canonical():
    proto = _load_prototype()
    assert proto.CONNECTIVITIES == (8, 4)
    assert proto.DEFAULT_CONNECTIVITY == 8
    assert proto.PARAMETERS["connectivity"]["allowed"] == (8, 4)
    assert proto.PARAMETERS["connectivity"]["default"] == 8
    assert proto.render_program(8, root=ROOT) == proto.canonical_program(root=ROOT)
    alternative = proto.render_program(4, root=ROOT)
    assert alternative != proto.canonical_program(root=ROOT)
    assert alternative.count("(objects cyan-mask 0)") == 1
    assert "(objects-8 cyan-mask 0)" not in alternative
    assert proto.choose_parameters(0) == {"connectivity": 8}
    assert proto.choose_parameters(1) == {"connectivity": 4}


def test_parameter_independent_inputs_preserve_family_and_teach_connectivity():
    proto = _load_prototype()
    grids = proto.fixture_inputs(20261020, root=ROOT)
    assert grids == proto.fixture_inputs(20261020, root=ROOT)
    assert len(grids) == 4
    assert proto.FIXTURE_PROFILES == (
        "diagonal_bridge",
        "bbox_decoy",
        "small_bridge",
        "diagonal_bridge",
    )
    for grid in grids:
        assert GENERATOR.self_check(grid) == []
        assert proto.apply_python(grid, 8) == GENERATOR.rule_mirror(grid)

    outputs8 = [proto.apply_python(grid, 8) for grid in grids]
    outputs4 = [proto.apply_python(grid, 4) for grid in grids]
    refuting_demos = [i for i in range(3) if outputs8[i] != outputs4[i]]
    assert refuting_demos
    assert outputs8[3] != outputs4[3]


def test_complete_episode_binds_one_setting_and_public_file_hides_it():
    proto = _load_prototype()
    for connectivity in proto.CONNECTIVITIES:
        episode = proto.generate_episode_python(
            1234,
            connectivity=connectivity,
            root=ROOT,
        )
        assert episode["parameters"] == {"connectivity": connectivity}
        assert episode["parameter_draw_count"] == 1
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["rival"]["status"] == "distinguished"
        assert episode["rival"]["refuting_demonstration_indices"]
        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert "connectivity" not in serialized
        assert "program" not in serialized


def test_materialized_evidence_executes_both_rules_with_real_racket(tmp_path: Path):
    proto = _load_prototype()
    out = tmp_path / "connectivity-evidence"
    report = proto.materialize(out, base_seed=20261020)
    assert report["status"] == "prototype"
    assert report["default_program_exact_canonical"] is True
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_episode_demonstrations_distinguish_rival"] is True
    assert report["canonical_labels_checked"] == report["canonical_labels_passed"] == 8
    assert report["complete_episodes"] == 2
    assert report["cross_setting_witness"]["query_outputs_differ"] is True

    episodes = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((out / "private" / "episodes").glob("*.json"))
    ]
    assert {row["parameters"]["connectivity"] for row in episodes} == {4, 8}
    for path in sorted((out / "public").glob("*.json")):
        public = json.loads(path.read_text(encoding="utf-8"))
        assert all(set(pair) == {"input"} for pair in public["test"])
