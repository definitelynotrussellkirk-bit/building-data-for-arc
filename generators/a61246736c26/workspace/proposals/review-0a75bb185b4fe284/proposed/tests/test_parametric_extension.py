"""Proposed parametric extension only; these are not canonical admission tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "a61246736c26"
ROOT = find_root(__file__)


def prototype():
    path = ROOT / "generators" / TASK / "workspace/parametric/prototype.py"
    assert path.is_file(), "The requested task-local parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("a61246736c26_parametric", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authoritative_program():
    with canonical_path(ROOT).open() as handle:
        selected = [json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK]
    assert len(selected) == 1
    return selected[0]["program_solution"]


def lawful_witness():
    pattern = [[1, 1, 1, 1], [1, 2, 8, 1], [1, 8, 8, 1], [1, 1, 1, 1]]
    grid = [[8] * 16 for _ in range(16)]
    for ri, frame in enumerate((5, 9, 0)):
        for r in range(4):
            grid[1 + ri * 5 + r][0] = frame
        for ci, fill in enumerate((3, 4, 6)):
            tile = [[1, 1, 1, 1], [1, fill, fill, 1], [1, fill, fill, 1], [1, 1, 1, 1]] if ri == ci else pattern
            for r in range(4):
                grid[1 + ri * 5 + r][1 + ci * 5:5 + ci * 5] = tile[r]
    return grid


def decode(rows):
    return [[int(value) for value in row] for row in rows]


def test_default_program_is_exact_authority_and_invalid_settings_reject():
    p = prototype()
    assert p.DEFAULT_STROKE_SYMBOL == 2
    assert p.ALLOWED_STROKE_SYMBOLS == (2, 8)
    assert p.materialize_rule() == authoritative_program()
    for bad in (True, False, 2.0, "2", 0, 1, 7, 9, None):
        with pytest.raises(ValueError, match="stroke_symbol"):
            p.materialize_rule(bad)
    alternative = p.materialize_rule(8)
    assert alternative != authoritative_program()
    assert alternative.replace("(hash 1 frame 8 fill)", "(hash 1 frame 2 fill)") == authoritative_program()


def test_literal_witness_and_all_canonical_labels_execute_in_racket():
    p = prototype()
    witness = lawful_witness()
    canonical = canonical_pairs(TASK, root=ROOT)
    result = p.execute_programs({str(value): p.materialize_rule(value) for value in (2, 8)},
                                [witness] + [pair["input"] for pair in canonical])
    assert result["engine"] == "RacketBridge"
    assert result["outputs"]["2"][0] == decode([
        "55558999980000", "53858948980680", "58858988980880", "55558999980000"])
    assert result["outputs"]["8"][0] == decode([
        "55558999980000", "52358924980260", "53358944980660", "55558999980000"])
    assert result["outputs"]["2"][1:] == [pair["output"] for pair in canonical]
    assert all(isinstance(result["wrapped_programs"][str(value)], str) for value in (2, 8))


def test_seed_selects_one_setting_for_all_pairs_and_replay_is_exact():
    p = prototype()
    assert {p.setting_from_seed(seed) for seed in range(32)} == {2, 8}
    for bad in (True, "4", 4.0):
        with pytest.raises(ValueError, match="seed"):
            p.setting_from_seed(bad)
    episode = p.generate_episode(4, difficulty="easy")
    assert episode == p.generate_episode(4, difficulty="easy")
    selected = episode["parameters"]["stroke_symbol"]
    assert selected == p.setting_from_seed(4)
    assert episode["parameter_selection"]["draw_count"] == 1
    assert episode["parameter_selection"]["sampled_once_per_episode"] is True
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    assert [pair["output"] for pair in pairs] == episode["executed_predictions"][str(selected)]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 4


def test_all_parameter_rivals_and_every_query_holdout_are_scored():
    p = prototype()
    episode = p.generate_episode(9, difficulty="medium")
    checks = episode["parameter_checks"]
    assert checks["declared_settings"] == [{"stroke_symbol": 2}, {"stroke_symbol": 8}]
    assert checks["status"] == "no_ambiguity_found"
    assert len(checks["production"]) == 2
    assert len(checks["query_rotations"]) == 4
    selected = episode["parameters"]["stroke_symbol"]
    for holdout in checks["query_rotations"]:
        assert len(holdout["rivals"]) == 2
        for rival in holdout["rivals"]:
            if rival["parameters"]["stroke_symbol"] == selected:
                assert rival["status"] == "survived_all"
            else:
                assert rival["status"] == "refuted_by_demonstrations"
                assert len(rival["refuting_demonstration_pair_indices"]) == 3
    corrupted = copy.deepcopy(episode)
    corrupted["train"][0]["output"][0][0] = 2
    with pytest.raises(ValueError, match="selected Racket labels"):
        p.check_parameter_rivals(corrupted)


def test_bundle_retains_labels_and_program_hashes_without_public_leakage(tmp_path):
    p = prototype()
    seeds = tuple(next(seed for seed in range(32) if p.setting_from_seed(seed) == value) for value in (2, 8))
    output = tmp_path / "evidence"
    report = p.build_evidence(output, seeds=seeds, difficulties=("easy",))
    assert report["status"] == "prototype_pass"
    assert report["summary"]["episodes"] == 2
    assert report["summary"]["settings_observed"] == [2, 8]
    assert report["summary"]["query_rotations"] == 8
    assert report["canonical_default"]["all_match"] is True
    assert report["distinguishing_input"]["different_outputs"] is True
    for entry in report["episodes"]:
        public = json.loads((output / entry["public_path"]).read_text())
        private = json.loads((output / entry["private_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public["train"] == private["train"]
        assert public["test"] == [{"input": pair["input"]} for pair in private["test"]]
        assert private["program_sha256"] == hashlib.sha256(private["program"].encode()).hexdigest()
    for entry in report["artifact_manifest"]:
        path = output / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    with pytest.raises(FileExistsError):
        p.build_evidence(output, seeds=seeds, difficulties=("easy",))
