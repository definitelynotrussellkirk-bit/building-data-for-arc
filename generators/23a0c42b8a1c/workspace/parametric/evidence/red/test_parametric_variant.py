"""Focused proposed-variant tests, separate from canonical generator coverage."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/23a0c42b8a1c/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "The proposed task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_23a0c42b8a1c", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_setting_is_exact_and_substitution_is_guarded(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "5af80c67d3907183931a179f7ff8ad18fc3c41ab97c1030589b0a4649a5ca7c7"
    )
    assert prototype.materialize_rule(8, root=ROOT) == canonical
    alternate = prototype.materialize_rule(2, root=ROOT)
    assert alternate != canonical
    assert alternate.replace("(extract-union g objs (list target) 2)",
                             "(extract-union g objs (list target) 8)") == canonical
    with pytest.raises(ValueError, match="canonical.*SHA|SHA.*canonical"):
        prototype.materialize_rule(2, source=canonical + " ")


@pytest.mark.parametrize("value", [True, False, 8.0, "8", 0, 1, 9, None])
def test_invalid_parameter_values_fail_visibly(prototype, value):
    with pytest.raises(ValueError, match="output_colour"):
        prototype.materialize_rule(value, root=ROOT)


def test_real_racket_changes_colour_and_preserves_nonrectangular_mask(prototype):
    grid = prototype.fixtures()[0]["input"]
    before = copy.deepcopy(grid)
    assert prototype.execute_rule(prototype.materialize_rule(8, root=ROOT), grid) == [[8, 8], [8, 0]]
    assert prototype.execute_rule(prototype.materialize_rule(2, root=ROOT), grid) == [[2, 2], [2, 0]]
    assert grid == before


def test_real_racket_preserves_tie_break_and_masks_foreign_cells(prototype):
    fixtures = prototype.fixtures()
    for colour in (8, 2):
        rule = prototype.materialize_rule(colour, root=ROOT)
        assert prototype.execute_rule(rule, fixtures[2]["input"]) == [[colour, colour], [colour, 0]]
        assert prototype.execute_rule(rule, fixtures[3]["input"]) == [
            [colour, colour, colour], [colour, 0, 0], [colour, colour, colour]
        ]


def test_original_rule_matches_all_labelled_canonical_pairs(prototype):
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    source = prototype.materialize_rule(8, root=ROOT)
    with prototype.RacketBridge() as bridge:
        for pair in pairs:
            assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_episode_is_deterministic_and_demonstrations_refute_parameter_rival(prototype):
    random_state = random.getstate()
    seen = set()
    for seed in (0, 1):
        episode = prototype.make_episode(seed, root=ROOT)
        assert prototype.make_episode(seed, root=ROOT) == episode
        parameter = episode["parameters"]["output_colour"]
        seen.add(parameter)
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 3 and len(episode["test"]) == 1
        assert len({prototype.grid_sha256(p["input"]) for p in episode["train"] + episode["test"]}) == 4
        for pair in episode["train"] + episode["test"]:
            assert {cell for row in pair["output"] for cell in row} - {0} == {parameter}
        rival, = [r for r in episode["parameter_rivals"] if r["output_colour"] != parameter]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0]
        assert not episode["ambiguities"]
    assert seen == {8, 2}
    assert random.getstate() == random_state


def test_public_challenge_omits_parameters_program_and_query_answers(prototype):
    episode = prototype.make_episode(0, root=ROOT)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_separates_private_answers_and_hashes_exact_racket(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_pairs_checked"] == 3
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        source = (out / private["racket_path"]).read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == private["racket_sha256"]
        assert public == prototype.public_challenge(private)
        assert "output" in private["test"][0] and "output" not in public["test"][0]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
