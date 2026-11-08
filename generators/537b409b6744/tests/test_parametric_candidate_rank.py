"""Focused tests for the task-local candidate-rank rule prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "537b409b6744"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "candidate-rank prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_candidate_rank_537b409b6744", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_rule() -> str:
    root = find_root(__file__)
    with (root / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"canonical row {TASK_ID} not found")


def test_parameter_contract_and_materialized_rules_are_exact(monkeypatch, tmp_path):
    prototype = _load_prototype()
    assert prototype.PARAMETER_SPEC == {
        "name": "candidate_rank",
        "values": ("nearest", "farthest"),
        "default": "nearest",
    }
    canonical = _canonical_rule()
    assert prototype.materialize_rule("nearest") == canonical
    farthest = prototype.materialize_rule("farthest")
    assert farthest == prototype.expected_farthest_rule(canonical)
    assert farthest != canonical
    with pytest.raises(ValueError):
        prototype.materialize_rule("largest")

    stale_dir = tmp_path / "rules"
    stale_dir.mkdir()
    (stale_dir / "nearest.rkt").write_text(canonical)
    (stale_dir / "farthest.rkt").write_text(farthest + "\n;; stale")
    monkeypatch.setattr(prototype, "RULE_DIR", stale_dir)
    with pytest.raises(RuntimeError, match="farthest prototype rule"):
        prototype.materialize_rule("farthest")


def test_farthest_python_mirror_preserves_larger_wall_tiebreak_in_racket():
    prototype = _load_prototype()
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 2, 4, 4, 4, 4],
        [0, 2, 2, 2, 2, 2, 4, 4, 4, 4],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    probe = prototype._load_reference_probe()
    candidates = probe.ranked_candidates(grid)
    assert [(row["gap"], row["wall_size"]) for row in candidates] == [
        (1, 10),
        (1, 8),
    ]
    assert prototype.apply_python(grid, "farthest") == prototype.apply_racket(
        grid, "farthest"
    )


def test_parameter_is_episode_scoped_deterministic_and_strict():
    prototype = _load_prototype()
    assert prototype.choose_candidate_rank(0) == "nearest"
    assert prototype.choose_candidate_rank(1) == "farthest"
    assert prototype.choose_candidate_rank(8) == "nearest"
    assert prototype.choose_candidate_rank(9) == "farthest"
    with pytest.raises(TypeError):
        prototype.choose_candidate_rank(True)
    with pytest.raises(TypeError):
        prototype.choose_candidate_rank(1.0)


@pytest.mark.parametrize("rank", ["nearest", "farthest"])
def test_complete_episode_has_three_demos_four_distinct_queries_and_refutes_other_setting(rank):
    prototype = _load_prototype()
    episode = prototype.build_episode(
        seed=23,
        candidate_rank=rank,
        difficulty="medium",
        start_index=1,
        n_train=3,
        n_test=4,
    )
    assert episode["meta"]["parameters"] == {"candidate_rank": rank}
    assert episode["meta"]["parameter_scope"] == "chosen once per episode"
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = [*episode["train"], *episode["test"]]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 7
    rival = "farthest" if rank == "nearest" else "nearest"
    assert all(
        pair["output"] == prototype.apply_python(pair["input"], rank)
        for pair in pairs
    )
    assert all(
        pair["output"] != prototype.apply_python(pair["input"], rival)
        for pair in pairs
    )
    assert prototype.parameter_rival_findings(episode) == []


def test_episode_builder_rejects_duplicate_and_nonidentifying_inputs(monkeypatch):
    prototype = _load_prototype()
    real_grid = prototype._load_generator().generate(5, 0, difficulty="easy")

    class DuplicateGenerator:
        VERSION = "duplicate-test"

        @staticmethod
        def generate(seed, sample_index, *, difficulty):
            del seed, sample_index, difficulty
            return copy.deepcopy(real_grid)

    monkeypatch.setattr(prototype, "_load_generator", lambda: DuplicateGenerator)
    with pytest.raises(RuntimeError, match="episode inputs must be distinct"):
        prototype.build_episode(seed=0, n_train=1, n_test=1)

    class NonidentifyingGenerator:
        VERSION = "nonidentifying-test"

        @staticmethod
        def generate(seed, sample_index, *, difficulty):
            del seed, difficulty
            return [[sample_index]]

    monkeypatch.setattr(prototype, "_load_generator", lambda: NonidentifyingGenerator)
    with pytest.raises(RuntimeError, match="does not distinguish candidate_rank"):
        prototype.build_episode(seed=0, n_train=1, n_test=1)


def test_evidence_requires_at_least_four_queries():
    prototype = _load_prototype()
    with pytest.raises(ValueError, match="at least four query inputs"):
        prototype.build_evidence(seeds=[0, 1], n_train=3, n_test=3)


def test_public_view_masks_hidden_state_and_verifier_rejects_leaks_and_bad_cells():
    prototype = _load_prototype()
    episode = prototype.build_episode(seed=0, n_train=3, n_test=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert prototype.verify_public_challenge(public) == []

    leaked = copy.deepcopy(public)
    leaked["test"][0]["output"] = episode["test"][0]["output"]
    assert "test pair 0 exposes an output" in prototype.verify_public_challenge(leaked)

    metadata_leak = copy.deepcopy(public)
    metadata_leak["meta"] = {"candidate_rank": "nearest"}
    assert "public challenge has forbidden top-level keys: ['meta']" in prototype.verify_public_challenge(metadata_leak)

    invalid_numeric = copy.deepcopy(public)
    invalid_numeric["test"][0]["input"][0][0] = True
    assert any(
        "exact integer colors 0..9" in finding
        for finding in prototype.verify_public_challenge(invalid_numeric)
    )


def test_public_identity_uses_exact_visible_bytes_not_private_state_or_query_answers():
    prototype = _load_prototype()
    episode = prototype.build_episode(seed=0, n_train=3, n_test=4)
    public = prototype.public_challenge(episode)
    expected_id = public_challenge_id(public)
    assert prototype.public_filename(public) == f"challenge-{expected_id}.json"

    private_change = copy.deepcopy(episode)
    private_change["meta"]["seed"] = 999999
    private_change["meta"]["parameters"]["candidate_rank"] = "farthest"
    private_change["test"][0]["output"][0][0] = (
        private_change["test"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_filename(
        prototype.public_challenge(private_change)
    ) == prototype.public_filename(public)

    visible_change = copy.deepcopy(public)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert prototype.public_filename(visible_change) != prototype.public_filename(public)

    with pytest.raises(ValueError, match="duplicate visible public challenge ID"):
        prototype.sorted_unique_public_records(
            [
                {"public_id": expected_id},
                {"public_id": expected_id},
            ]
        )


def test_bounded_evidence_executes_both_racket_rules_and_all_query_rotations():
    prototype = _load_prototype()
    report = prototype.build_evidence(
        seeds=[1, 0],
        difficulty="easy",
        start_index=0,
        n_train=3,
        n_test=4,
    )
    assert report["status"] == "proposed"
    assert report["completion_state"] == "complete"
    assert report["passed"] is True
    assert report["canonical_authority_changed"] is False
    assert report["default_program_byte_identical"] is True
    assert report["counts"] == {
        "settings_materialized": 2,
        "episodes": 2,
        "distinct_settings_demonstrated": 2,
        "canonical_pairs": 8,
        "canonical_passed": 8,
        "racket_label_executions": 14,
        "python_parity_passed": 14,
        "production_lessons": 2,
        "production_identifiable": 2,
        "query_pairs": 8,
        "queries_changed_by_rival": 8,
        "query_rotations": 14,
        "rotations_identifiable": 14,
        "public_challenges": 2,
        "public_verifier_passed": 2,
    }
    assert report["setting_difference_witness"]["different_cell_count"] > 0
    assert all(not record["parameter_rival_findings"] for record in report["episodes"])
    public_ids = [record["public_id"] for record in report["episodes"]]
    assert public_ids == sorted(public_ids)
    assert len(public_ids) == len(set(public_ids))


def test_evidence_writer_rejects_overlapping_private_and_public_trees(tmp_path):
    prototype = _load_prototype()
    shared = tmp_path / "shared"
    with pytest.raises(ValueError, match="must not overlap"):
        prototype.write_evidence(
            out_dir=shared,
            public_dir=shared / "public",
            seeds=[0, 1],
            difficulty="easy",
            start_index=0,
            n_train=3,
            n_test=4,
        )
    assert not shared.exists()


def test_written_artifacts_are_source_bound_masked_and_refuse_overwrite(tmp_path):
    prototype = _load_prototype()
    private_dir = tmp_path / "private"
    public_dir = tmp_path / "public"
    report = prototype.write_evidence(
        out_dir=private_dir,
        public_dir=public_dir,
        seeds=[0, 1],
        difficulty="easy",
        start_index=0,
        n_train=3,
        n_test=4,
    )
    assert report["passed"] is True
    assert (private_dir / "report.json").is_file()
    assert (private_dir / "manifest.json").is_file()
    assert (private_dir / "setting-difference-witness.json").is_file()
    public_paths = sorted(public_dir.iterdir())
    assert len(public_paths) == 2
    assert [record["public_id"] for record in report["episodes"]] == sorted(
        record["public_id"] for record in report["episodes"]
    )
    assert {path.name for path in public_paths} == {
        record["public_filename"] for record in report["episodes"]
    }
    assert not any(
        rank in path.name
        for path in public_paths
        for rank in prototype.PARAMETER_SPEC["values"]
    )
    for path in public_paths:
        challenge = json.loads(path.read_text())
        assert path.name == prototype.public_filename(challenge)
        assert path.read_bytes() == public_challenge_bytes(challenge)
        assert prototype.verify_public_challenge(challenge) == []
        assert all("output" not in pair for pair in challenge["test"])
    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            out_dir=private_dir,
            public_dir=public_dir,
            seeds=[0, 1],
            difficulty="easy",
            start_index=0,
            n_train=3,
            n_test=4,
        )


def test_evidence_writer_leaves_no_new_trees_when_validation_fails(tmp_path):
    prototype = _load_prototype()
    private_dir = tmp_path / "private"
    public_dir = tmp_path / "public"
    with pytest.raises(ValueError, match="both candidate_rank settings"):
        prototype.write_evidence(
            out_dir=private_dir,
            public_dir=public_dir,
            seeds=[0, 2],
            difficulty="easy",
            start_index=0,
            n_train=3,
            n_test=4,
        )
    assert not private_dir.exists()
    assert not public_dir.exists()
