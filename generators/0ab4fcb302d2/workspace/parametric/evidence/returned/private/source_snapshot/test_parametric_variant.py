"""Focused tests for the separate proposed diagonal-code parametric prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "diagonal_code_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _settings(prototype):
    return set(
        itertools.product(
            prototype.ALLOWED_DIAGONAL_MAPPINGS,
            prototype.ALLOWED_BLOCK_SIZES,
        )
    )


def test_default_rule_is_exact_canonical_and_all_four_sources_are_distinct():
    prototype = _load_prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(root=ROOT) == canonical

    sources = {}
    for diagonal_mapping, block_size in sorted(_settings(prototype)):
        source = prototype.materialize_rule(
            diagonal_mapping=diagonal_mapping,
            block_size=block_size,
            root=ROOT,
        )
        sources[(diagonal_mapping, block_size)] = source
        assert source.startswith("(rule! (lambda (g)")
        assert source.endswith(")")
    assert len(set(sources.values())) == 4
    assert sources[(prototype.DEFAULT_DIAGONAL_MAPPING, prototype.DEFAULT_BLOCK_SIZE)] == canonical

    for bad in (True, 0, 1, "match", None):
        if bad == "match":
            continue
        with pytest.raises((TypeError, ValueError)):
            prototype.materialize_rule(diagonal_mapping=bad, root=ROOT)
    for bad in (True, 2, 5, 4.0, "4", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.materialize_rule(block_size=bad, root=ROOT)
    with pytest.raises(ValueError):
        prototype.materialize_rule(diagonal_mapping="sideways", root=ROOT)


def test_seed_selection_is_deterministic_once_per_episode_and_covers_settings():
    prototype = _load_prototype()
    selected = []
    for seed in range(4):
        first = prototype.parameters_for_seed(seed)
        second = prototype.parameters_for_seed(seed)
        assert first == second
        selected.append((first["diagonal_mapping"], first["block_size"]))
    assert set(selected) == _settings(prototype)
    for bad in (True, -1, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="seed"):
            prototype.parameters_for_seed(bad)


def test_complete_episodes_refute_every_other_parameter_setting_with_racket():
    prototype = _load_prototype()
    seen = set()
    with prototype.RacketBridge() as bridge:
        for seed in range(4):
            episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
            parameters = episode["parameters"]
            selected = (parameters["diagonal_mapping"], parameters["block_size"])
            seen.add(selected)

            assert episode["status"] == "proposed_unapproved"
            assert episode["approved"] is False
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert not episode["ambiguities"]
            assert len({pair["fixture_id"] for pair in episode["train"] + episode["test"]}) == 4

            demo_orientations = {
                prototype.parse_input(pair["input"])["marker_corner"] in (0, 3)
                for pair in episode["train"]
            }
            assert demo_orientations == {False, True}

            rivals = {
                (row["diagonal_mapping"], row["block_size"]): row
                for row in episode["parameter_rivals"]
            }
            assert set(rivals) == _settings(prototype)
            assert rivals[selected]["status"] == "matches_episode"
            for setting, row in rivals.items():
                if setting == selected:
                    continue
                assert row["status"] == "refuted_by_demonstrations"
                assert row["demonstration_mismatch_indices"] == [0, 1, 2]
                assert row["query_mismatch_indices"] == [0]

            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.execute_rule(
                    episode["racket_source"], pair["input"], bridge=bridge
                )
    assert seen == _settings(prototype)


def test_public_challenge_omits_hidden_parameters_rule_seed_and_query_answer():
    prototype = _load_prototype()
    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    before = copy.deepcopy(episode)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("parameters", "racket", "seed", "query_index", "block_size", "diagonal_mapping"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_retains_exact_racket_private_data_and_hashes(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence(range(4), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 4
    assert report["counts"]["settings_covered"] == 4
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["canonical_replay"]["all_match"] is True
    assert report["distinguishing_witness"]["all_four_outputs_distinct"] is True

    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        source = (out / private["racket_path"]).read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == private["racket_sha256"]
        assert public == prototype.public_challenge(private)
        assert "output" in private["test"][0]
        assert "output" not in public["test"][0]

    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence(range(4), out=out, root=ROOT)
