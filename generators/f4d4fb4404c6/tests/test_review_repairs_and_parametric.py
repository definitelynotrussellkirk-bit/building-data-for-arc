"""Review regressions for strict scalars and the copy-limit prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge


TASK_ID = "f4d4fb4404c6"
TASK_HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_HOME / "workspace"))
from reference_probe import load_generator  # noqa: E402

GENERATOR = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROTOTYPE_PATH = TASK_HOME / "workspace/parametric/prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "copy_limit prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("f4_copy_limit_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "bad_difficulty",
    ["__invalid_difficulty__", 1, True, 1.0, (), []],
)
def test_generate_rejects_invalid_difficulty_scalars(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(11, 2, difficulty=bad_difficulty)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        GENERATOR.generate(11, -1, difficulty="hard")
    with pytest.raises(ValueError, match="sample_index"):
        GENERATOR.schedule_profile(11, -1, "hard")


def test_valid_difficulty_domain_remains_deterministic_and_lawful():
    for difficulty in (None, "easy", "medium", "hard"):
        first = GENERATOR.generate(11, 2, difficulty=difficulty)
        second = GENERATOR.generate(11, 2, difficulty=difficulty)
        assert first == second
        assert GENERATOR.self_check(first) == []


def test_copy_limit_contract_and_default_authority_are_exact():
    prototype = _load_prototype()
    assert prototype.PARAMETER_NAME == "copy_limit"
    assert prototype.COPY_LIMITS == ("to_edge", "one_copy")
    assert prototype.DEFAULT_COPY_LIMIT == "to_edge"
    assert prototype.choose_parameters(0) == {"copy_limit": "to_edge"}
    assert prototype.choose_parameters(1) == {"copy_limit": "one_copy"}
    assert prototype.choose_parameters(2) == {"copy_limit": "to_edge"}
    with pytest.raises((TypeError, ValueError), match="episode seed"):
        prototype.choose_parameters(True)

    canonical = prototype.canonical_rule()
    assert prototype.instantiate_rule("to_edge") == canonical
    one_copy = prototype.instantiate_rule("one_copy")
    assert one_copy != canonical
    assert "define (extend out m)" in one_copy
    with pytest.raises(ValueError, match="copy_limit"):
        prototype.instantiate_rule("forever")


def test_episode_inputs_are_lawful_distinct_and_separate_both_settings():
    prototype = _load_prototype()
    for seed in range(4):
        inputs = prototype.generate_inputs(seed)
        assert len(inputs) == 4
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 4
        for grid in inputs:
            original = deepcopy(grid)
            assert GENERATOR.self_check(grid) == []
            to_edge = prototype.python_reference(grid, copy_limit="to_edge")
            one_copy = prototype.python_reference(grid, copy_limit="one_copy")
            assert to_edge == GENERATOR.rule_mirror(grid)
            assert to_edge != one_copy
            assert grid == original


def test_racket_labels_match_independent_references_and_rotations_refute_rival():
    prototype = _load_prototype()
    with RacketBridge() as bridge:
        for seed, setting in enumerate(prototype.COPY_LIMITS):
            episode = prototype.make_episode(
                bridge,
                101 + seed,
                copy_limit=setting,
            )
            assert episode["parameters"] == {"copy_limit": setting}
            assert len(episode["pairs"]) == 4
            for pair in episode["pairs"]:
                assert pair["output"] == prototype.python_reference(
                    pair["input"], copy_limit=setting
                )
            analysis = prototype.analyze_episode(bridge, episode)
            assert analysis["production"]["status"] == "no_ambiguity_found"
            assert all(
                row["status"] == "no_ambiguity_found"
                and row["rival"]["query_differs"]
                and row["rival"]["refuting_demonstration_indices"]
                for row in analysis["rotations"]
            )

            public = prototype.public_challenge(episode)
            assert set(public) == {"train", "test"}
            assert len(public["train"]) == 3
            assert public["test"] == [{"input": episode["pairs"][3]["input"]}]
            serialized = json.dumps(public, sort_keys=True)
            assert "copy_limit" not in serialized
            assert "racket" not in serialized.lower()
            assert episode["pairs"][3]["output"] != public["test"][0].get("output")


def test_materialized_evidence_is_hash_bound_redacted_and_replayable(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "copy-limit-evidence"
    report = prototype.materialize(out, seed=20)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["episode_labels"] == 8
    assert report["counts"]["production_ambiguities"] == 0
    assert report["counts"]["rotation_ambiguities"] == 0
    assert {row["parameters"]["copy_limit"] for row in report["episodes"]} == set(
        prototype.COPY_LIMITS
    )
    assert (out / "private/rules/copy-limit-to-edge.rkt").is_file()
    assert (out / "private/rules/copy-limit-one-copy.rkt").is_file()
    assert (out / "private/setting-difference-witness.json").is_file()
    assert (out / "manifest.json").is_file()
    verification = prototype.verify_tree(out)
    assert verification["status"] == "pass"
    assert verification["checked_labels"] >= 8
