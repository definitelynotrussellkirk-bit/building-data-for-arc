"""Racket-backed tests for the isolated scale-factor prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
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

TASK_ID = "2dacb90452ce"


@lru_cache(maxsize=1)
def prototype():
    root = find_root(__file__)
    load_selected_generator(TASK_ID, root=root)
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), "The proposed scale-factor prototype must be runnable."
    spec = importlib.util.spec_from_file_location("scale_factor_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


@pytest.mark.parametrize("value", [True, False, 0, 1, 4, 2.0, 3.0, "2", None])
def test_invalid_scale_factor_values_are_rejected_without_coercion(value):
    module, _ = prototype()
    with pytest.raises(ValueError, match="scale_factor"):
        module.validate_scale_factor(value)
    with pytest.raises(ValueError, match="scale_factor"):
        module.program_for_scale_factor(value)


@pytest.mark.parametrize(
    "demo_count,query_count",
    [(0, 4), (2, 0), (-1, 4), (2, -1), (True, 4), (2, False), (2.0, 4), (2, "4")],
)
def test_invalid_demo_and_query_counts_are_rejected(demo_count, query_count):
    module, _ = prototype()
    with pytest.raises(ValueError, match="demo_count|query_count"):
        module.validate_pair_counts(demo_count, query_count)


@pytest.mark.parametrize("seed", [True, False, -1, 1.0, "1", None])
def test_invalid_episode_seeds_are_rejected(seed):
    module, _ = prototype()
    with pytest.raises(ValueError, match="seed"):
        module.choose_scale_factor(seed)
    with pytest.raises(ValueError, match="seed"):
        module.generate_inputs(seed)


def test_default_program_is_byte_for_byte_canonical_and_variant_changes_one_count():
    module, root = prototype()
    assert module.SCALE_FACTORS == (2, 3)
    assert module.DEFAULT_SCALE_FACTOR == 2
    assert module.DEFAULT_DEMO_COUNT == 2
    assert module.DEFAULT_QUERY_COUNT == 4
    canonical = module.canonical_rule(root=root)
    assert canonical == "(rule! (lambda (g) (upscale g 2)))"
    assert module.program_for_scale_factor(2, root=root) == canonical
    assert module.program_for_scale_factor(3, root=root) == "(rule! (lambda (g) (upscale g 3)))"


def test_default_program_reproduces_every_canonical_label_through_racket(bridge):
    module, root = prototype()
    program = module.program_for_scale_factor(2, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert module.evaluate(bridge, program, pair["input"]) == pair["output"]


def test_both_programs_execute_and_match_a_hand_checked_shared_witness(bridge):
    module, root = prototype()
    grid = [[1, 2], [3, 4]]
    expected_two = [
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 4, 4],
        [3, 3, 4, 4],
    ]
    expected_three = [
        [1, 1, 1, 2, 2, 2],
        [1, 1, 1, 2, 2, 2],
        [1, 1, 1, 2, 2, 2],
        [3, 3, 3, 4, 4, 4],
        [3, 3, 3, 4, 4, 4],
        [3, 3, 3, 4, 4, 4],
    ]
    assert module.evaluate(bridge, module.program_for_scale_factor(2, root=root), grid) == expected_two
    assert module.evaluate(bridge, module.program_for_scale_factor(3, root=root), grid) == expected_three


def test_seed_selects_one_factor_deterministically_without_touching_global_rng():
    module, _ = prototype()
    random.seed(20261023)
    before = random.getstate()
    assert module.choose_scale_factor(0) == 2
    assert module.choose_scale_factor(1) == 3
    assert module.choose_scale_factor(2) == 2
    assert random.getstate() == before


def test_six_inputs_are_repeatable_distinct_setting_independent_and_production_lawful():
    module, root = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    random.seed(314159)
    before = random.getstate()
    first = module.generate_inputs(71, demo_count=2, query_count=4, root=root)
    second = module.generate_inputs(71, demo_count=2, query_count=4, root=root)
    assert first == second
    assert random.getstate() == before
    assert len(first) == 6
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 6
    for grid in first:
        assert generator.self_check(grid) == []
        assert 2 <= len(grid) == len(grid[0]) <= 5
        assert len(grid) * 3 <= 30
        assert len(grid[0]) * 3 <= 30


def test_episode_keeps_one_factor_and_all_six_labels_come_from_its_racket_program(bridge):
    module, root = prototype()
    episode_two = module.generate_episode(
        bridge, 88, scale_factor=2, demo_count=2, query_count=4, root=root
    )
    episode_three = module.generate_episode(
        bridge, 88, scale_factor=3, demo_count=2, query_count=4, root=root
    )
    assert episode_two["parameters"] == {"scale_factor": 2}
    assert episode_three["parameters"] == {"scale_factor": 3}
    assert episode_two["counts"] == {"demonstrations": 2, "queries": 4}
    assert episode_three["counts"] == {"demonstrations": 2, "queries": 4}
    assert [pair["input"] for pair in episode_two["pairs"]] == [
        pair["input"] for pair in episode_three["pairs"]
    ]
    for episode in (episode_two, episode_three):
        factor = episode["parameters"]["scale_factor"]
        program = module.program_for_scale_factor(factor, root=root)
        assert episode["racket_program"] == program
        assert len(episode["pairs"]) == 6
        for pair in episode["pairs"]:
            assert pair["output"] == module.evaluate(bridge, program, pair["input"])


def test_each_query_is_identifiable_from_demonstrations_against_the_other_factor(bridge):
    module, root = prototype()
    for factor in module.SCALE_FACTORS:
        episode = module.generate_episode(
            bridge, 93, scale_factor=factor, demo_count=2, query_count=4, root=root
        )
        analysis = module.analyze_episode(bridge, episode, root=root)
        assert analysis["status"] == "no_ambiguity_found"
        assert len(analysis["queries"]) == 4
        for row in analysis["queries"]:
            assert row["rival_scale_factor"] == (3 if factor == 2 else 2)
            assert row["rival_fits_demonstrations"] is False
            assert row["query_differs"] is True
            assert row["refuting_demonstration_indices"] == [0, 1]


def test_public_projection_has_two_labeled_demos_four_unlabeled_queries_and_stable_id(bridge):
    module, root = prototype()
    episode = module.generate_episode(
        bridge, 101, scale_factor=3, demo_count=2, query_count=4, root=root
    )
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 2
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = public_challenge_bytes(public).decode("utf-8")
    for forbidden in ("seed", "scale_factor", "racket", "sha256", "parameters", "rival"):
        assert forbidden not in serialized
    original_id = public_challenge_id(public)
    assert module.public_filename(episode) == f"challenge-{original_id}.json"

    altered_private = copy.deepcopy(episode)
    altered_private["seed"] = 999999
    altered_private["parameters"]["scale_factor"] = 2
    for pair in altered_private["pairs"][2:]:
        pair["output"] = [[9]]
    assert public_challenge_id(module.public_challenge(altered_private)) == original_id
    assert module.public_filename(altered_private) == f"challenge-{original_id}.json"


def test_evidence_builder_retains_both_settings_and_separates_public_private_data(bridge, tmp_path):
    module, root = prototype()
    out = tmp_path / "scale-factor-v1"
    report = module.build_evidence(
        out,
        seed=20261022,
        demo_count=2,
        query_count=4,
        bridge=bridge,
        root=root,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["parameters"] == {
        "name": "scale_factor",
        "allowed_values": [2, 3],
        "default": 2,
    }
    assert report["counts"] == {
        "canonical_labels_checked": 4,
        "canonical_labels_passed": 4,
        "episodes": 2,
        "demonstrations": 4,
        "queries": 8,
        "episode_labels": 12,
        "counterfactual_labels": 12,
        "ambiguous_queries": 0,
    }
    assert {row["parameters"]["scale_factor"] for row in report["episodes"]} == {2, 3}
    assert (out / "private/rules/scale-factor-2.rkt").read_text() == module.program_for_scale_factor(2, root=root)
    assert (out / "private/rules/scale-factor-3.rkt").read_text() == module.program_for_scale_factor(3, root=root)

    public_ids = set()
    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        assert public_path.name == f"challenge-{public_challenge_id(public)}.json"
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert public_path.parent.name == "public"
        assert set(public["test"][0]) == {"input"}
        assert private["parameters"] == row["parameters"]
        assert len(private["pairs"][:2]) == 2
        assert len(private["pairs"][2:]) == 4
        assert all("output" in pair for pair in private["pairs"])
        assert len(row["analysis"]["queries"]) == 4
        assert all(not q["rival_fits_demonstrations"] for q in row["analysis"]["queries"])
        public_ids.add(row["public_id"])
    assert len(public_ids) == 2
    assert report["setting_witness"]["outputs"]["2"] != report["setting_witness"]["outputs"]["3"]


def test_evidence_builder_refuses_to_overwrite_existing_directory(bridge, tmp_path):
    module, root = prototype()
    with pytest.raises(FileExistsError):
        module.build_evidence(tmp_path, seed=0, bridge=bridge, root=root)
