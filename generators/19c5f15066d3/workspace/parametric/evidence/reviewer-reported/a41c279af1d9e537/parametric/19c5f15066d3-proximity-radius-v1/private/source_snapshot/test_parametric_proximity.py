"""Focused tests for the proposed proximity-radius prototype.

These tests are deliberately separate from the selected canonical generator.
The prototype is proposed/unapproved and must not alter production authority.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_id,
)


TASK_ID = "19c5f15066d3"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_SOURCE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
VERIFY_SOURCE = TASK_HOME / "workspace" / "parametric" / "verify.py"
CANONICAL_SHA256 = "ed64ca10036251fa97fee353aa573bf2f3abc62f77cacc4992c5a765b7f48579"


def _load(path: Path, name: str):
    assert path.is_file(), f"required proposed prototype file is missing: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE_SOURCE, "parametric_proximity_19c5f15066d3")


@pytest.fixture(scope="module")
def selected_generator():
    module, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _json_sha(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _object_line_distance(item, info) -> int:
    values = []
    for row, col in item["cells"]:
        values.extend(abs(col - line) for line in info["vcols"])
        values.extend(abs(row - line) for line in info["hrows"])
    assert values
    return min(values)


def test_default_rule_is_exact_and_parameter_values_are_strict(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.materialize_rule(1, root=ROOT) == canonical
    assert prototype.normalized_program_hash(1, root=ROOT) == "1ffa1234962c"
    assert prototype.materialize_rule(0, root=ROOT) != canonical
    assert prototype.materialize_rule(2, root=ROOT) != canonical

    for invalid in (True, False, -1, 3, 1.0, "1", None):
        with pytest.raises(ValueError, match="proximity_radius"):
            prototype.materialize_rule(invalid, root=ROOT)
    with pytest.raises(ValueError, match="canonical.*SHA|SHA.*canonical"):
        prototype.materialize_rule(0, source=canonical + " ")


def test_default_python_rule_matches_selected_generator_and_canonical_pairs(
    prototype, selected_generator
):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.solve(pair["input"], proximity_radius=1) == pair["output"]
        assert selected_generator.rule_mirror(pair["input"]) == pair["output"]


def test_distinguishing_inputs_are_lawful_unique_and_witness_all_thresholds(
    prototype, selected_generator
):
    before = random.getstate()
    grids = prototype.distinguishing_inputs(17, 7)
    assert random.getstate() == before
    assert len(grids) == 7
    assert len({_json_sha(grid) for grid in grids}) == 7

    for grid in grids:
        assert selected_generator.self_check(grid) == []
        info = selected_generator._analysis(grid)
        distances = sorted(_object_line_distance(item, info) for item in info["red_objects"])
        assert distances == [0, 1, 2, 4]
        outputs = [prototype.solve(grid, proximity_radius=value) for value in (0, 1, 2)]
        assert len({_json_sha(output) for output in outputs}) == 3


def test_episode_fixes_one_radius_and_exposes_three_demos_four_queries(prototype):
    before = random.getstate()
    for radius in prototype.ALLOWED_PROXIMITY_RADII:
        episode = prototype.make_episode(
            100 + radius,
            proximity_radius=radius,
            n_train=3,
            n_test=4,
            root=ROOT,
        )
        assert prototype.make_episode(
            100 + radius,
            proximity_radius=radius,
            n_train=3,
            n_test=4,
            root=ROOT,
        ) == episode
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert episode["parameters"] == {"proximity_radius": radius}
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({_json_sha(pair["input"]) for pair in pairs}) == 7
        assert all(
            pair["output"]
            == prototype.solve(pair["input"], proximity_radius=radius)
            for pair in pairs
        )

        rivals = {row["proximity_radius"]: row for row in episode["parameter_rivals"]}
        assert set(rivals) == set(prototype.ALLOWED_PROXIMITY_RADII)
        assert rivals[radius]["status"] == "matches_episode"
        for rival_radius, row in rivals.items():
            if rival_radius == radius:
                continue
            assert row["status"] == "refuted_by_demonstrations"
            assert row["demonstration_mismatch_indices"] == [0, 1, 2]
            assert row["query_mismatch_indices"] == [0, 1, 2, 3]
        assert episode["ambiguities"] == []
    assert random.getstate() == before


@pytest.mark.parametrize(
    "kwargs",
    (
        {"n_train": 0},
        {"n_test": 0},
        {"n_train": True},
        {"n_test": 1.0},
        {"n_train": 9, "n_test": 8},
    ),
)
def test_episode_counts_are_bounded_exact_integers(prototype, kwargs):
    with pytest.raises(ValueError, match="n_train|n_test|pair count"):
        prototype.make_episode(0, root=ROOT, **kwargs)


def test_public_challenge_is_allowlisted_deep_copy(prototype):
    episode = prototype.make_episode(5, n_train=3, n_test=4, root=ROOT)
    before = copy.deepcopy(episode)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(public["test"]) == 4
    assert "proximity_radius" not in json.dumps(public)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_real_racket_matches_python_for_every_radius(prototype):
    grid = prototype.distinguishing_inputs(23, 1)[0]
    for radius in prototype.ALLOWED_PROXIMITY_RADII:
        program = prototype.materialize_rule(radius, root=ROOT)
        assert prototype.execute_rule(program, grid) == prototype.solve(
            grid, proximity_radius=radius
        )


def test_evidence_report_checks_all_pairs_and_uses_opaque_public_ids(tmp_path):
    verifier = _load(VERIFY_SOURCE, "verify_parametric_proximity_19c5f15066d3")
    out = tmp_path / "evidence"
    report = verifier.build_report(out)

    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 3,
        "demonstrations": 9,
        "queries": 12,
        "retained_pairs": 21,
        "canonical_pairs_checked": 4,
    }
    assert report["all_racket_exact"] is True
    assert report["all_rival_racket_exact"] is True
    assert report["all_rivals_refuted_by_every_demo"] is True
    assert report["all_queries_setting_sensitive"] is True
    assert report["all_public_challenges_masked"] is True
    assert report["all_public_ids_visible_only"] is True

    public_names = []
    public_ids = [row["public_challenge_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    for row in report["episodes"]:
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_text())
        expected_id = public_challenge_id(public)
        assert public_path.name == f"challenge-{expected_id}.json"
        assert all("output" not in pair for pair in public["test"])
        public_names.append(public_path.name)
    assert len(set(public_names)) == 3


def test_evidence_writer_sorts_and_rejects_duplicate_visible_ids():
    verifier = _load(VERIFY_SOURCE, "verify_parametric_ordering_19c5f15066d3")
    rows = [
        {"public_challenge_id": "b", "payload": 2},
        {"public_challenge_id": "a", "payload": 1},
    ]
    ordered = verifier._sorted_unique_episode_artifacts(rows)
    assert [row["public_challenge_id"] for row in ordered] == ["a", "b"]
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        verifier._sorted_unique_episode_artifacts([rows[0], copy.deepcopy(rows[0])])
