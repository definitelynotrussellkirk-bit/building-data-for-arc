"""Racket-backed regressions for the intersection/parity-transform family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"_729429f8ea2c_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype")


@pytest.fixture(scope="module")
def engine(prototype):
    with prototype.RacketEngine() as runtime:
        yield runtime


ODD_FIXTURE = [[0] * 12 for _ in range(10)]
for row, col in ((1, 1), (2, 1), (2, 2), (3, 1)):
    ODD_FIXTURE[row][col] = 2
ODD_FIXTURE[8][0] = 2
for row, col in ((4, 7), (5, 7), (5, 8), (5, 9)):
    ODD_FIXTURE[row][col] = 3
ODD_FIXTURE[0][11] = 3


def test_default_is_exact_selected_canonical_program(prototype):
    from reviewer_support import canonical_path, find_root

    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row["task_id"] == "729429f8ea2c"}
    assert programs == {prototype.program({"mode": "intersection"})}


def test_hand_fixture_executes_intersection_then_odd_rotation(prototype, engine):
    assert prototype.intermediate(ODD_FIXTURE) == {
        "cells": [[0, 0], [1, 0], [1, 1]],
        "count": 3,
        "parity": "odd",
    }
    assert engine.apply(prototype.program({"mode": "intersection"}), ODD_FIXTURE) == [
        [8, 0],
        [8, 8],
    ]
    assert engine.apply(prototype.program({"mode": "parity_transform"}), ODD_FIXTURE) == [
        [8, 8],
        [8, 0],
    ]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_labels_teaching_and_30x30(prototype, engine, demos):
    episodes = [prototype.generate(17, {"mode": mode}, demos, 4)
                for mode in prototype.MODES]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        for pair in episode["train"] + episode["test"]:
            assert prototype.validate_input(pair["input"]) == pair["input"]
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
        certificate = prototype.check_teaching(
            episode["train"], episode["settings"], engine=engine
        )
        assert certificate["survivors"] == [episode["settings"]["mode"]]
        assert certificate["fit_scope"] == "demonstrations_only"
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [
            pair["input"] for pair in episodes[1][split]
        ]
    assert episodes[0]["test"][0]["output"] != episodes[1]["test"][0]["output"]


def test_two_demo_lesson_covers_both_control_branches(prototype):
    episode = prototype.generate(29, {"mode": "parity_transform"}, 2, 4)
    assert [prototype.intermediate(pair["input"])["parity"]
            for pair in episode["train"]] == ["odd", "even"]


def test_one_query_and_four_query_requests_share_first_turn(prototype):
    one = prototype.generate(31, {"mode": "parity_transform"}, 3, 1)
    four = prototype.generate(31, {"mode": "parity_transform"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]


@pytest.mark.parametrize("field,value", [
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", "4"),
    ("seed", -1), ("seed", True),
])
def test_invalid_numeric_requests_fail(prototype, field, value):
    arguments = {"seed": 0, "settings": {"mode": "intersection"},
                 "demos": 3, "queries": 4}
    arguments[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**arguments)


@pytest.mark.parametrize("settings", [
    {}, {"mode": "unknown"}, {"mode": True},
    {"mode": "intersection", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_demonstration_checker_rejects_one_branch_lesson(prototype, engine):
    episode = prototype.generate(41, {"mode": "parity_transform"}, 2, 1)
    with pytest.raises(ValueError, match="identify"):
        prototype.check_teaching(
            episode["train"][:1],
            {"mode": "parity_transform"},
            engine=engine,
        )


def test_nondefault_causal_counterfactual_changes_output(prototype, engine):
    episode = prototype.generate(73, {"mode": "parity_transform"}, 2, 4)
    pair = episode["test"][1]
    assert prototype.intermediate(pair["input"])["parity"] == "even"
    actual = engine.apply(prototype.program({"mode": "parity_transform"}), pair["input"])
    skip_control = engine.apply(prototype.rival_programs()["always_rotate"], pair["input"])
    assert actual == pair["output"]
    assert skip_control != actual
