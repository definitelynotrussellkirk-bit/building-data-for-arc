"""Focused tests for the proposed order/palette episode prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "task_71e2e99645f4_parametric_prototype")


def _generator():
    return _load(GENERATOR_PATH, "task_71e2e99645f4_parametric_generator")


def test_default_rule_is_exact_canonical_and_all_variants_are_guarded_final_expression_changes():
    prototype = _prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(root=ROOT) == canonical

    sources = {}
    for order in prototype.ALLOWED_SECTION_ORDERS:
        for palette in prototype.ALLOWED_PALETTES:
            source = prototype.materialize_rule(order, palette, root=ROOT)
            sources[(order, palette)] = source
            assert source.count(prototype.CANONICAL_FINAL_EXPRESSION) == (
                1 if (order, palette) == (prototype.DEFAULT_SECTION_ORDER, prototype.DEFAULT_PALETTE) else 0
            )
    assert len(set(sources.values())) == 4

    for bad in (True, 0, 1.0, "inside_out", None):
        with pytest.raises(ValueError, match="section_order"):
            prototype.materialize_rule(bad, prototype.DEFAULT_PALETTE, root=ROOT)
    for bad in (True, 0, 1.0, "rainbow", None):
        with pytest.raises(ValueError, match="palette"):
            prototype.materialize_rule(prototype.DEFAULT_SECTION_ORDER, bad, root=ROOT)


def test_controlled_inputs_are_lawful_and_all_four_settings_disagree():
    prototype = _prototype()
    generator = _generator()
    inputs = prototype.episode_inputs(37)
    assert len(inputs) == 4

    with prototype.RacketBridge() as bridge:
        for grid in inputs:
            before = copy.deepcopy(grid)
            assert generator.self_check(grid) == []
            outputs = {
                setting: prototype.execute_rule(
                    prototype.materialize_rule(*setting, root=ROOT),
                    grid,
                    bridge=bridge,
                )
                for setting in prototype.PARAMETER_SETTINGS
            }
            assert len({json.dumps(value) for value in outputs.values()}) == 4
            assert grid == before


def test_complete_episodes_choose_one_setting_and_refute_every_parameter_rival():
    prototype = _prototype()
    seen = set()
    with prototype.RacketBridge() as bridge:
        for seed in prototype.COVERAGE_SEEDS:
            episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
            assert prototype.make_episode(seed, root=ROOT, bridge=bridge) == episode
            selected = (
                episode["parameters"]["section_order"],
                episode["parameters"]["palette"],
            )
            seen.add(selected)
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["status"] == "proposed_unapproved"
            assert episode["approved"] is False
            assert episode["ambiguities"] == []
            assert {
                (row["section_order"], row["palette"])
                for row in episode["parameter_rivals"]
            } == set(prototype.PARAMETER_SETTINGS) - {selected}
            for rival in episode["parameter_rivals"]:
                assert rival["status"] == "refuted_by_demonstrations"
                assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
                assert rival["query_mismatch_indices"] == [0]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.execute_rule(
                    episode["racket_source"], pair["input"], bridge=bridge
                )
    assert seen == set(prototype.PARAMETER_SETTINGS)


def test_public_challenge_omits_parameters_seed_rule_rivals_and_query_answer():
    prototype = _prototype()
    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(prototype.COVERAGE_SEEDS[0], root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_retains_exact_rules_private_answers_hashes_and_canonical_replay(tmp_path):
    prototype = _prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence(prototype.COVERAGE_SEEDS, out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 4,
        "settings_covered": 4,
        "ambiguous_parameter_rivals": 0,
        "canonical_pairs_checked": 5,
    }
    assert report["canonical_replay"]["status"] == "pass"
    assert len(set(report["shared_witness"]["outputs_sha256"].values())) == 4

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
        prototype.write_evidence(prototype.COVERAGE_SEEDS, out=out, root=ROOT)
