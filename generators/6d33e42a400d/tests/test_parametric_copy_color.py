"""Racket-backed tests for the proposed copy-color-role extension."""
from __future__ import annotations

import importlib.util
import json
from functools import lru_cache

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "6d33e42a400d"


@lru_cache(maxsize=1)
def loaded():
    root = find_root(__file__)
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), "copy-color-role prototype must be runnable"
    spec = importlib.util.spec_from_file_location("copy_color_role_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, generator, root


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def test_default_rule_is_exact_canonical_and_matches_all_labels(bridge):
    module, _, root = loaded()
    source = module.instantiate_rule("paint", root=root)
    assert source == module.canonical_rule(root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(pairs) >= 3
    for pair in pairs:
        assert module.evaluate(bridge, source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("value", [True, False, 0, 1, 1.0, None, "painted", "SOURCE"])
def test_invalid_parameter_values_are_rejected(value):
    module, _, _ = loaded()
    with pytest.raises(ValueError, match="copy_color_role"):
        module.instantiate_rule(value)


def test_parameter_changes_only_reflected_copy_color(bridge):
    module, generator, _ = loaded()
    inputs = module.generate_inputs(17)
    assert len(inputs) == 4
    for grid in inputs:
        paint = module.evaluate(bridge, module.instantiate_rule("paint"), grid)
        source = module.evaluate(bridge, module.instantiate_rule("source"), grid)
        assert paint == generator.solve_python(grid)
        assert source == generator._copy_in_source_color(grid)
        assert paint != source


def test_seed_chooses_one_rule_for_entire_episode_and_preserves_inputs(bridge):
    module, _, _ = loaded()
    paint = module.make_episode(bridge, 0)
    source = module.make_episode(bridge, 1)
    assert paint["parameters"] == {"copy_color_role": "paint"}
    assert source["parameters"] == {"copy_color_role": "source"}
    assert len(paint["pairs"]) == len(source["pairs"]) == 4

    overridden = module.make_episode(bridge, 0, copy_color_role="source")
    assert [pair["input"] for pair in overridden["pairs"]] == [
        pair["input"] for pair in paint["pairs"]
    ]
    assert all(
        first["output"] != second["output"]
        for first, second in zip(paint["pairs"], overridden["pairs"])
    )


def test_public_projection_hides_parameter_program_and_query_answer(bridge):
    module, _, _ = loaded()
    episode = module.make_episode(bridge, 0)
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    dumped = json.dumps(public)
    assert "copy_color_role" not in dumped
    assert "racket" not in dumped.lower()
    public["test"][0]["input"][0][0] = 99
    assert episode["pairs"][3]["input"][0][0] != 99


def test_other_parameter_is_refuted_before_every_query_rotation(bridge):
    module, _, _ = loaded()
    for seed in (0, 1):
        episode = module.make_episode(bridge, seed)
        analysis = module.analyze_episode(bridge, episode)
        for score in [analysis["production"], *analysis["rotations"]]:
            assert score["status"] == "no_ambiguity_found"
            rival = score["rival"]
            assert not rival["fits_demonstrations"]
            assert rival["query_differs"]
            assert rival["refuting_demonstration_indices"] == score["demonstration_indices"]
        assert [row["query_index"] for row in analysis["rotations"]] == [0, 1, 2, 3]


def test_materialized_tree_is_self_verifying_and_separates_public_data(bridge, tmp_path):
    module, _, _ = loaded()
    out = tmp_path / "copy-color-evidence"
    report = module.materialize(out, seed=0, bridge=bridge)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "canonical_labels_checked": 6,
        "canonical_labels_passed": 6,
        "episodes": 2,
        "demonstrations": 6,
        "queries": 2,
        "episode_labels": 8,
        "counterfactual_labels": 8,
        "production_ambiguities": 0,
        "rotation_ambiguities": 0,
        "query_rotations": 8,
        "unique_episode_inputs": 8,
    }
    verification = module.verify_tree(out, bridge=bridge)
    assert verification["status"] == "pass"
    assert verification["failures"] == []
    for episode in report["episodes"]:
        public = json.loads((out / episode["public_path"]).read_text())
        private = json.loads((out / episode["private_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert set(public["test"][0]) == {"input"}
        assert "parameters" in private
        assert "output" in private["pairs"][3]


def test_materialization_refuses_to_overwrite(bridge, tmp_path):
    module, _, _ = loaded()
    with pytest.raises(FileExistsError):
        module.materialize(tmp_path, seed=0, bridge=bridge)
