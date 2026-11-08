"""Racket-backed regressions for the forward/reverse stencil family."""
from __future__ import annotations

from copy import deepcopy
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
    spec = importlib.util.spec_from_file_location(f"_e5477d32d98b_{name}", path)
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


FIXTURE = [
    [2, 2, 2, 5, 2, 2, 2, 5, 6, 6, 6],
    [0, 2, 2, 5, 0, 0, 2, 5, 0, 0, 6],
    [0, 0, 2, 5, 0, 2, 2, 5, 0, 0, 6],
    [0, 0, 2, 5, 0, 2, 2, 5, 0, 0, 6],
]


def test_default_is_exact_selected_canonical_program(prototype):
    from reviewer_support import canonical_path, find_root

    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row["task_id"] == "e5477d32d98b"}
    assert programs == {prototype.program({"direction": "forward"})}


def test_forward_and_reverse_execute_hand_derived_labels(prototype, engine):
    assert engine.apply(prototype.program({"direction": "forward"}), FIXTURE) == [
        [6, 6, 6],
        [0, 0, 6],
        [0, 6, 6],
        [0, 6, 6],
    ]
    assert engine.apply(prototype.program({"direction": "reverse"}), FIXTURE) == [
        [6, 6, 6],
        [0, 6, 6],
        [0, 0, 6],
        [0, 0, 6],
    ]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_labels_and_boundary(prototype, engine, demos):
    episodes = [prototype.generate(17, {"direction": direction}, demos, 4)
                for direction in prototype.DIRECTIONS]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 29]
        for pair in episode["train"] + episode["test"]:
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
        certificate = prototype.check_teaching(episode["train"], episode["settings"], engine=engine)
        assert certificate["survivors"] == [episode["settings"]["direction"]]
        assert certificate["fit_scope"] == "demonstrations_only"
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [pair["input"] for pair in episodes[1][split]]
    assert episodes[0]["test"][0]["output"] != episodes[1]["test"][0]["output"]


def test_one_query_and_four_query_requests_share_first_turn(prototype):
    one = prototype.generate(31, {"direction": "reverse"}, 3, 1)
    four = prototype.generate(31, {"direction": "reverse"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]


@pytest.mark.parametrize("field,value", [
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", "4"),
    ("seed", -1), ("seed", True),
])
def test_invalid_numeric_requests_fail(prototype, field, value):
    arguments = {"seed": 0, "settings": {"direction": "forward"}, "demos": 3, "queries": 4}
    arguments[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**arguments)


@pytest.mark.parametrize("settings", [
    {}, {"direction": "sideways"}, {"direction": True},
    {"direction": "forward", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


def test_demonstration_checker_rejects_uninformative_lesson(prototype, engine):
    query = [row[8:] for row in FIXTURE]
    uninformative = deepcopy(FIXTURE)
    for row in uninformative:
        row[4:7] = row[:3]
    with pytest.raises(ValueError, match="identify"):
        prototype.check_teaching(
            [{"input": uninformative, "output": query}, {"input": uninformative, "output": query}],
            {"direction": "forward"},
            engine=engine,
        )


def test_nondefault_causal_counterfactual_changes_output(prototype, engine):
    episode = prototype.generate(73, {"direction": "reverse"}, 2, 4)
    pair = episode["test"][0]
    actual = engine.apply(prototype.program({"direction": "reverse"}), pair["input"])
    wrong_intermediate = engine.apply(prototype.program({"direction": "forward"}), pair["input"])
    assert actual == pair["output"]
    assert wrong_intermediate != actual
