"""Prototype-only checks for the proposed stamp-transform parameter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "8de1c257a9c7"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
GENERATOR_PATH = ROOT / f"generators/{TASK_ID}/generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load(GENERATOR_PATH, "parametric_parent_8de1c257a9c7")


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    return _load(PROTOTYPE_PATH, "parametric_stamp_transform_8de1c257a9c7")


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"]
            for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return programs.pop()


def test_parameter_domain_and_seed_selection_are_bounded(proto):
    assert proto.PARAMETER_NAME == "stamp_transform"
    assert proto.PARAMETER_VALUES == ("identity", "mirror_horizontal")
    assert proto.DEFAULT_PARAMETER == "identity"
    assert {proto.choose_parameter(seed) for seed in range(32)} == set(
        proto.PARAMETER_VALUES
    )
    for invalid in (True, 0, None, "rotate", "mirror_vertical"):
        with pytest.raises((TypeError, ValueError)):
            proto.validate_parameter(invalid)


def test_default_program_is_exact_canonical_and_alternative_is_materialized(proto):
    identity = proto.racket_program("identity", root=ROOT)
    mirrored = proto.racket_program("mirror_horizontal", root=ROOT)
    assert identity == _canonical_program()
    assert mirrored != identity
    assert identity.startswith("(rule!") and mirrored.startswith("(rule!")


def test_same_lawful_inputs_support_both_distinct_settings(proto, gen):
    for pair_index in range(4):
        grid = proto.build_input(20261020, pair_index)
        assert gen.self_check(grid) == []
        identity = proto.apply_rule(grid, "identity")
        mirrored = proto.apply_rule(grid, "mirror_horizontal")
        assert identity == gen.rule_mirror(grid)
        assert identity != mirrored


def test_each_setting_is_fixed_and_identifiable_for_every_holdout(proto):
    for setting in proto.PARAMETER_VALUES:
        episode = proto.generate_episode(20261020, stamp_transform=setting)
        assert episode["meta"]["stamp_transform"] == setting
        assert episode["meta"]["canonical_default"] is (
            setting == proto.DEFAULT_PARAMETER
        )
        all_pairs = [*episode["train"], *episode["test"]]
        assert all(
            proto.apply_rule(pair["input"], setting) == pair["output"]
            for pair in all_pairs
        )
        for query_index in range(len(all_pairs)):
            demos = [
                pair for index, pair in enumerate(all_pairs) if index != query_index
            ]
            assert proto.surviving_parameter_values(demos) == [setting]


def test_public_projection_hides_parameter_program_seed_and_query_answers(proto):
    episode = proto.generate_episode(
        7, stamp_transform="mirror_horizontal", n_train=3, n_test=1
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "program" not in public and "meta" not in public
    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9
