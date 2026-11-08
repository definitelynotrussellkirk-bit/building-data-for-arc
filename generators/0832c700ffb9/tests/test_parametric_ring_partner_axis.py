"""Prototype-only checks for a fixed-per-episode ring-partner axis."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "0832c700ffb9"
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
    return _load(GENERATOR_PATH, "parametric_parent_0832c700ffb9")


def test_parametric_prototype_file_exists():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"


@pytest.fixture(scope="module")
def proto():
    if not PROTOTYPE_PATH.is_file():
        pytest.skip("parametric prototype has not been implemented")
    return _load(PROTOTYPE_PATH, "parametric_ring_partner_axis_0832c700ffb9")


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"]
            for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return programs.pop()


def test_parameter_domain_and_episode_selection_are_bounded(proto):
    assert proto.PARAMETER_NAME == "ring_partner_axis"
    assert proto.PARAMETER_VALUES == ("row", "column")
    assert proto.DEFAULT_PARAMETER == "row"
    assert {proto.choose_parameter(seed) for seed in range(8)} == set(
        proto.PARAMETER_VALUES
    )
    for invalid in (True, 0, None, "diagonal", "rows"):
        with pytest.raises((TypeError, ValueError)):
            proto.validate_parameter(invalid)


def test_default_program_is_byte_exact_canonical_and_column_variant_is_materialized(proto):
    row = proto.racket_program("row", root=ROOT)
    column = proto.racket_program("column", root=ROOT)
    assert row == _canonical_program()
    assert column != row
    assert row.startswith("(rule!") and column.startswith("(rule!")


def test_same_lawful_inputs_support_both_settings_and_witness_them(proto, gen):
    profiles = []
    differing = []
    for pair_index in range(proto.N_TRAIN + proto.N_TEST):
        grid = proto.build_input(20261021, pair_index)
        assert gen.self_check(grid) == []
        row = proto.apply_rule(grid, "row")
        column = proto.apply_rule(grid, "column")
        assert row == gen.rule_mirror(grid)
        profiles.append(gen.schedule_profile(20261021, pair_index))
        differing.append(row != column)
    assert profiles == [
        "two_rects",
        "border_rect",
        "two_rects_border",
        "two_rects",
        "border_rect",
        "two_rects_border",
    ]
    assert differing == [True, False, True, True, False, True]


def test_each_setting_is_fixed_and_identifiable_for_every_holdout(proto):
    for setting in proto.PARAMETER_VALUES:
        episode = proto.generate_episode(20261021, ring_partner_axis=setting)
        assert episode["meta"]["ring_partner_axis"] == setting
        assert episode["meta"]["canonical_default"] is (
            setting == proto.DEFAULT_PARAMETER
        )
        all_pairs = [*episode["train"], *episode["test"]]
        assert all(
            proto.apply_rule(pair["input"], setting) == pair["output"]
            for pair in all_pairs
        )
        for query_index in range(len(all_pairs)):
            demonstrations = [
                pair for index, pair in enumerate(all_pairs) if index != query_index
            ]
            assert proto.surviving_parameter_values(demonstrations) == [setting]


def test_public_projection_hides_parameter_program_seed_and_query_answers(proto):
    episode = proto.generate_episode(
        7, ring_partner_axis="column", n_train=5, n_test=1
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    payload = json.dumps(public, sort_keys=True)
    assert "ring_partner_axis" not in payload
    assert "program" not in public and "meta" not in public
    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9
