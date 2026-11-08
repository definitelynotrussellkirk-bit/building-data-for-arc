"""Portable tests of the proposed stamp-orientation prototype only.

Run through review.py run (or with shared/runtime on PYTHONPATH).
These tests do not certify or import the selected production generator.
"""
from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root
from arc_repl.racket_bridge import RacketBridge


TASK_ID = "144c5d002191"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "workspace/parametric/stamp_orientation.py"


def _load_prototype():
    assert SOURCE.is_file(), "stamp-orientation prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("stamp_orientation_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10, startup_timeout=60) as result:
        yield result


def test_default_is_exact_canonical_program_and_all_four_labels(bridge):
    proto = _load_prototype()
    with canonical_path(ROOT).open() as handle:
        canonical = [json.loads(line) for line in handle if line.strip()
                     and json.loads(line).get("task_id") == TASK_ID]
    assert len(canonical) == 1
    program = proto.materialize_program(root=ROOT)
    assert program == canonical[0]["program_solution"]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert proto.execute_program(bridge, program, pair["input"]) == pair["output"]


def test_mirror_changes_template_only_on_exact_lawful_witness(proto, bridge):
    grid = [[0] * 7 for _ in range(6)]
    grid[0][0] = grid[1][0] = grid[1][1] = 5
    grid[3][4] = 2
    assert proto.input_constraints(grid) == []
    identity = proto.execute_program(bridge, proto.materialize_program(root=ROOT), grid)
    mirror = proto.execute_program(bridge, proto.materialize_program("horizontal_mirror", root=ROOT), grid)
    expected_identity = [[0] * 7 for _ in range(6)]
    expected_identity[3][4] = expected_identity[4][4] = expected_identity[4][5] = 2
    expected_mirror = [[0] * 7 for _ in range(6)]
    expected_mirror[3][5] = expected_mirror[4][4] = expected_mirror[4][5] = 2
    assert identity == expected_identity
    assert mirror == expected_mirror
    assert identity != mirror


def test_input_sampling_is_deterministic_bounded_and_legal(proto):
    grids = []
    for seed in range(12):
        for sample_index in range(3):
            grid = proto.generate_input(seed, sample_index)
            assert grid == proto.generate_input(seed, sample_index)
            assert proto.input_constraints(grid) == []
            assert 10 <= len(grid) <= 14
            assert 10 <= len(grid[0]) <= 15
            grids.append(json.dumps(grid))
    assert len(set(grids)) == 36


@pytest.mark.parametrize("orientation", ["identity", "horizontal_mirror"])
def test_episode_uses_one_rule_and_demo_identifies_all_query_rotations(proto, bridge, orientation):
    episode = proto.generate_episode(23, orientation=orientation, root=ROOT, bridge=bridge)
    assert episode["parameters"] == {"stamp_orientation": orientation}
    assert len(episode["train"]) == 2 and len(episode["test"]) == 1
    assert episode["program"] == proto.materialize_program(orientation, root=ROOT)
    for index, pair in enumerate(episode["train"] + episode["test"]):
        assert pair["input"] == proto.generate_input(23, index)
        assert proto.execute_program(bridge, episode["program"], pair["input"]) == pair["output"]
    assessment = proto.assess_episode(episode, root=ROOT, bridge=bridge)
    assert assessment["production"]["parameter_identifiable"]
    assert assessment["production"]["query_identifiable"]
    assert assessment["production"]["surviving_parameters"] == [orientation]
    assert len(assessment["rotations"]) == 3
    assert all(item["parameter_identifiable"] and item["query_identifiable"]
               for item in assessment["rotations"])


def test_seeded_parameter_selection_is_once_per_episode_and_covers_both(proto, bridge):
    selections = [proto.choose_orientation(seed, "seeded") for seed in range(16)]
    assert set(selections) == set(proto.ORIENTATIONS)
    assert selections == [proto.choose_orientation(seed, "seeded") for seed in range(16)]
    seed = selections.index("horizontal_mirror")
    episode = proto.generate_episode(seed, orientation="seeded", root=ROOT, bridge=bridge)
    assert episode["parameters"]["stamp_orientation"] == "horizontal_mirror"
    assert episode["parameter_selection"] == "seeded"
    assert episode["program"] == proto.materialize_program("horizontal_mirror", root=ROOT)


def test_symmetric_demonstrations_report_ambiguity_when_query_needs_orientation(proto, bridge):
    symmetric = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[2]
    query = proto.generate_input(12, 2)
    program = proto.materialize_program(root=ROOT)
    episode = {"parameters": {"stamp_orientation": "identity"},
               "program": program, "train": [symmetric, symmetric],
               "test": [{"input": query, "output": proto.execute_program(bridge, program, query)}]}
    assessment = proto.assess_episode(episode, root=ROOT, bridge=bridge)
    assert not assessment["production"]["parameter_identifiable"]
    assert not assessment["production"]["query_identifiable"]
    assert assessment["production"]["surviving_parameters"] == list(proto.ORIENTATIONS)
    assert assessment["production"]["query_disagreeing_survivors"] == ["horizontal_mirror"]


def test_public_challenge_contains_only_demonstrations_and_query_inputs(proto, bridge):
    episode = proto.generate_episode(7, orientation="horizontal_mirror", root=ROOT, bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public["test"][0]["input"] == episode["test"][0]["input"]
    public["train"][0]["input"][0][0] = 99
    assert episode["train"][0]["input"][0][0] != 99


@pytest.mark.parametrize("value", ["rotate", "Identity", "", None, True, 1])
def test_unsupported_orientation_is_rejected(proto, value):
    with pytest.raises(ValueError):
        proto.materialize_program(value, root=ROOT)


@pytest.mark.parametrize("seed", [True, -1, 1.5, "1", 2**63])
def test_invalid_seed_is_rejected(proto, seed):
    with pytest.raises(ValueError):
        proto.generate_input(seed, 0)


@pytest.mark.parametrize("grid", [[], [[]], [[0, 1], [2]], [[False]], [[10]]])
def test_malformed_inputs_are_reported(proto, grid):
    assert proto.input_constraints(grid)


def test_evidence_export_keeps_public_files_clean_and_refuses_overwrite(proto, tmp_path):
    output = tmp_path / "fresh-evidence"
    report = proto.build_evidence(output, seed=31, root=ROOT)
    assert report["status"] == "pass"
    assert report["canonical_default"]["matched_pairs"] == 4
    assert report["witness"]["outputs_differ"] is True
    assert len(report["episodes"]) == 2
    for record in report["episodes"]:
        public = json.loads((output / record["public_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
        private = json.loads((output / record["private_path"]).read_text())
        assert proto.sha256_text(private["program"]) == private["program_sha256"]
        assert private["parameter_selection"] == "seeded"
        assert proto.choose_orientation(private["seed"], "seeded") == private["parameters"]["stamp_orientation"]
    with pytest.raises(FileExistsError):
        proto.build_evidence(output, seed=31, root=ROOT)
