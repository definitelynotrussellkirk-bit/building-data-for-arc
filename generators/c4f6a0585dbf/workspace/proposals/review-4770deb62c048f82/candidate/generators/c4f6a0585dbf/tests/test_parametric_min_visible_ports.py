"""Racket-backed tests for the isolated minimum-visible-port prototype."""
from __future__ import annotations

import importlib.util
import json
import re
from functools import lru_cache
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "c4f6a0585dbf"


@lru_cache(maxsize=1)
def prototype():
    root = find_root(Path(__file__))
    load_selected_generator(TASK_ID, root=root)
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), "The proposed minimum-visible-port prototype must be runnable."
    spec = importlib.util.spec_from_file_location("c4f6_min_visible_ports", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


@pytest.mark.parametrize("value", [True, False, 0, 1, 4, 2.0, 3.0, "2", None])
def test_invalid_min_visible_port_settings_are_rejected(value):
    module, _ = prototype()
    with pytest.raises(ValueError, match="min_visible_ports"):
        module.validate_setting(value)
    with pytest.raises(ValueError, match="min_visible_ports"):
        module.program_for_min_visible_ports(value)


def test_default_program_is_byte_for_byte_canonical_and_alternative_changes_one_guard():
    module, root = prototype()
    canonical = module.canonical_rule(root=root)
    default = module.program_for_min_visible_ports(2, root=root)
    strict = module.program_for_min_visible_ports(3, root=root)
    assert module.DEFAULT_MIN_VISIBLE_PORTS == 2
    assert default == canonical
    assert strict != canonical
    assert canonical.count("(>= (length placed4) 2)") == 1
    assert strict.count("(>= (length placed4) 3)") == 1
    assert strict == canonical.replace(
        "(>= (length placed4) 2)",
        "(>= (length placed4) 3)",
        1,
    )


def test_default_program_reproduces_all_selected_canonical_labels(bridge):
    module, root = prototype()
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(pairs) == 10
    program = module.program_for_min_visible_ports(2, root=root)
    for pair in pairs:
        assert module.evaluate(bridge, program, pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed, expected", [(0, 2), (1, 3), (8, 2), (9, 3)])
def test_episode_chooses_one_setting_and_has_three_demos_plus_four_queries(
    bridge, seed, expected
):
    module, root = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    episode = module.generate_episode(bridge, seed)
    assert episode["parameters"] == {"min_visible_ports": expected}
    assert episode["demo_count"] == 3
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    input_texts = {json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}
    assert len(input_texts) == 7
    program = module.program_for_min_visible_ports(expected, root=root)
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.observe_overrides(pair["input"])["n_ports"] == 3
        assert pair["output"] == module.evaluate(bridge, program, pair["input"])


def test_same_input_seed_is_shared_across_the_two_settings(bridge):
    module, _ = prototype()
    permissive = module.generate_episode(bridge, 0)
    strict = module.generate_episode(bridge, 1)
    assert permissive["input_seed"] == strict["input_seed"] == 0
    assert [pair["input"] for pair in permissive["train"] + permissive["test"]] == [
        pair["input"] for pair in strict["train"] + strict["test"]
    ]
    assert all(
        a["output"] != b["output"]
        for a, b in zip(
            permissive["train"] + permissive["test"],
            strict["train"] + strict["test"],
            strict=True,
        )
    )


@pytest.mark.parametrize("seed", [0, 1, 18, 19])
def test_demonstrations_refute_the_other_setting_before_all_four_queries(bridge, seed):
    module, _ = prototype()
    episode = module.generate_episode(bridge, seed)
    analysis = module.analyze_episode(bridge, episode)
    assert analysis["demonstration_refutations"] == [0, 1, 2]
    assert len(analysis["queries"]) == 4
    for row in analysis["queries"]:
        assert row["status"] == "no_ambiguity_found"
        assert row["rival_fits_demonstrations"] is False
        assert row["query_differs"] is True


def test_public_projection_masks_settings_programs_and_four_query_answers(bridge):
    module, _ = prototype()
    episode = module.generate_episode(bridge, 0)
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "seed",
        "min_visible_ports",
        "racket",
        "sha256",
        "parameters",
        "rival",
    ):
        assert forbidden not in serialized


def test_evidence_build_records_both_settings_racket_labels_and_opaque_public_names(
    bridge, tmp_path
):
    module, root = prototype()
    out = tmp_path / "evidence"
    report = module.build_evidence(out, seed=0, bridge=bridge)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "canonical_labels_checked": 10,
        "canonical_labels_passed": 10,
        "episodes": 2,
        "demonstrations": 6,
        "queries": 8,
        "intended_labels": 14,
        "rival_labels": 14,
        "ambiguous_queries": 0,
        "unique_episode_inputs": 7,
    }
    assert {row["parameters"]["min_visible_ports"] for row in report["episodes"]} == {
        2,
        3,
    }
    _, _, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    assert report["source_hashes"]["generator.py"] == generator_sha256
    assert report["setting_witness"]["differing_cells"] > 0
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    for row in report["episodes"]:
        public_rel = row["public_path"]
        assert re.fullmatch(r"public/episode-[0-9a-f]{64}\.json", public_rel)
        public_path = out / public_rel
        public = json.loads(public_path.read_text())
        assert row["public_id"] == public_challenge_id(public)
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
        private = json.loads((out / row["private_path"]).read_text())
        assert private["parameters"] == row["parameters"]
        assert all("output" in pair for pair in private["test"])
    for setting in (2, 3):
        rule_path = out / "private" / "rules" / f"min-visible-ports-{setting}.rkt"
        assert rule_path.read_text() == module.program_for_min_visible_ports(setting)


def test_public_record_preparation_rejects_duplicate_visible_challenges(bridge):
    module, _ = prototype()
    episode = module.generate_episode(bridge, 0)
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        module.prepare_public_records([episode, episode])


def test_evidence_build_refuses_to_overwrite_existing_directory(bridge, tmp_path):
    module, _ = prototype()
    with pytest.raises(FileExistsError):
        module.build_evidence(tmp_path, seed=0, bridge=bridge)
