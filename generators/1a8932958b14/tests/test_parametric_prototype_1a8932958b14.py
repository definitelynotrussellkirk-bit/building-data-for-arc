"""Focused tests for the proposed task-local parametric rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK_ID = "1a8932958b14"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "_parametric_prototype_1a8932958b14", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parametric_contract_and_seed_choice_are_bounded_and_deterministic():
    proto = _load_prototype()
    spec = proto.PARAMETERS["vector_multiplier"]
    assert spec["allowed"] == (1, 2)
    assert spec["default"] == 1
    assert "in bounds" in spec["input_constraint"].lower()

    assert proto.choose_parameters(0) == proto.choose_parameters(0)
    assert proto.choose_parameters(1) == proto.choose_parameters(1)
    for seed in range(20):
        assert proto.choose_parameters(seed)["vector_multiplier"] in (1, 2)


def test_complete_episode_uses_one_parameter_and_each_demo_refutes_the_other_setting():
    proto = _load_prototype()
    for multiplier in (1, 2):
        episode = proto.generate_episode(20261019 + multiplier, vector_multiplier=multiplier)
        assert episode["meta"]["vector_multiplier"] == multiplier
        assert episode["meta"]["parameter_draw_count"] == 1
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["program"] == proto.racket_program(multiplier)

        opposite = 3 - multiplier
        all_pairs = [*episode["train"], *episode["test"]]
        assert all(
            pair["output"] == proto.apply_python(pair["input"], multiplier)
            for pair in all_pairs
        )
        assert all(
            proto.apply_python(pair["input"], opposite) != pair["output"]
            for pair in episode["train"]
        )


def test_default_setting_preserves_canonical_rule_and_alternative_changes_execution():
    proto = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = proto.generate_episode(9901, vector_multiplier=1)

    changed = 0
    for pair in [*episode["train"], *episode["test"]]:
        assert generator.self_check(pair["input"]) == []
        assert proto.apply_python(pair["input"], 1) == generator.rule_mirror(pair["input"])
        if proto.apply_python(pair["input"], 1) != proto.apply_python(pair["input"], 2):
            changed += 1
    assert changed == 4


def test_public_challenge_omits_hidden_parameter_program_and_query_answer():
    proto = _load_prototype()
    episode = proto.generate_episode(777)
    public = proto.public_challenge(episode)

    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "meta" not in public
    assert "program" not in public
