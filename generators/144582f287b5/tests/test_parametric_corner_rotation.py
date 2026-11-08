"""Focused tests for the proposed corner-rotation rule prototype.

The prototype is authoring evidence only.  It must not alter the selected
canonical generator, rule authority, or approval state.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "the task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location(
        "parametric_corner_rotation_144582f287b5", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_default_rule_are_exact():
    prototype = load_prototype()
    assert prototype.TASK_ID == "144582f287b5"
    assert prototype.ALLOWED_QUARTER_TURNS == (0, 1, 2, 3)
    assert prototype.DEFAULT_QUARTER_TURNS == 0
    assert [prototype.choose_quarter_turns(seed) for seed in range(4)] == [0, 1, 2, 3]

    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "5ad0a3ff74fcf99b1f0242009b86e0fbd0fa6903ab8b80f06d32969224b4b7fe"
    )
    assert prototype.materialize_rule(0, root=ROOT) == canonical
    assert len({prototype.materialize_rule(value, root=ROOT) for value in range(4)}) == 4

    for bad in (True, False, -1, 4, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.materialize_rule(bad, root=ROOT)
    for bad_seed in (True, False, -1, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            prototype.choose_quarter_turns(bad_seed)


def test_real_racket_executes_all_four_corner_orders():
    prototype = load_prototype()
    grid = [
        [0, 0, 0, 0],
        [0, 1, 2, 0],
        [0, 3, 4, 0],
        [0, 0, 0, 0],
    ]
    expected = {
        0: [[1, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [3, 0, 0, 4]],
        1: [[3, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [4, 0, 0, 2]],
        2: [[4, 0, 0, 3], [0, 0, 0, 0], [0, 0, 0, 0], [2, 0, 0, 1]],
        3: [[2, 0, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 3]],
    }
    before = copy.deepcopy(grid)
    with RacketBridge(timeout=10) as bridge:
        for turns, output in expected.items():
            program = prototype.materialize_rule(turns, root=ROOT)
            assert prototype.execute_rule(program, grid, bridge=bridge) == output
            assert prototype.python_apply(grid, turns) == output
    assert grid == before


def test_episode_parameter_is_chosen_once_and_all_rivals_are_refuted():
    prototype = load_prototype()
    episodes = []
    with RacketBridge(timeout=10) as bridge:
        for seed in range(4):
            episode = prototype.build_episode(seed, root=ROOT, bridge=bridge)
            episodes.append(episode)
            assert episode["parameters"] == {"source_rotation_quarter_turns": seed}
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["ambiguities"] == []
            assert all(row["status"] == "refuted_by_demonstrations" for row in episode["parameter_rivals"])
            assert all(row["demonstration_mismatch_indices"] == [0, 1, 2] for row in episode["parameter_rivals"])
            assert all(row["query_mismatch_indices"] == [0] for row in episode["parameter_rivals"])
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.python_apply(pair["input"], seed)

    # Seeds 0..3 vary only the hidden rule; the four input witnesses are shared.
    input_sets = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes
    ]
    assert all(inputs == input_sets[0] for inputs in input_sets[1:])


def test_default_program_matches_every_canonical_pair_and_public_challenge_is_masked():
    prototype = load_prototype()
    program = prototype.materialize_rule(0, root=ROOT)
    with RacketBridge(timeout=10) as bridge:
        pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
        assert pairs
        for pair in pairs:
            assert prototype.execute_rule(program, pair["input"], bridge=bridge) == pair["output"]
        episode = prototype.build_episode(1, root=ROOT, bridge=bridge)

    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    assert "source_rotation_quarter_turns" not in encoded
    assert "racket" not in encoded.lower()
    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_retains_exact_rules_private_answers_and_hashes(tmp_path):
    prototype = load_prototype()
    out = tmp_path / "corner-rotation-evidence"
    report = prototype.write_evidence((0, 1, 2, 3), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["passed"] is True
    assert report["counts"]["settings_materialized"] == 4
    assert report["counts"]["episodes"] == 4
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] >= 3

    for row in report["programs"]:
        path = out / row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert "output" in private["test"][0]
        assert "output" not in public["test"][0]
    for row in report["files"]:
        path = out / row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1, 2, 3), out=out, root=ROOT)
