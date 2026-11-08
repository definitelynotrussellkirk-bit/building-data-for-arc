"""Protected-Racket tests for the canonical/min-marker routing family."""
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
    spec = importlib.util.spec_from_file_location(f"_e6cf1120a17d_{name}", path)
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


def test_default_is_byte_exact_canonical(prototype):
    assert prototype.program({"routing": "diagonal"}) == prototype.CANONICAL_PROGRAM


def test_hand_fixture_distinguishes_both_rules(prototype, engine):
    grid = prototype.fixture_grid(
        9,
        10,
        rectangle=(2, 2, 5, 6),
        rect_color=5,
        marker_colors=(1, 4, 7, 8),
    )
    diagonal = engine.apply(prototype.program({"routing": "diagonal"}), grid)
    selected = engine.apply(prototype.program({"routing": "min_color_turn"}), grid)
    assert diagonal == prototype.python_oracle(grid, {"routing": "diagonal"})
    assert selected == prototype.python_oracle(grid, {"routing": "min_color_turn"})
    assert diagonal != selected


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_labels_teaching_and_30x30_boundary(prototype, engine, demos):
    for routing in prototype.ROUTINGS:
        episode = prototype.generate(17, {"routing": routing}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        for pair in episode["train"] + episode["test"]:
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
        certificate = prototype.check_teaching(episode["train"], episode["settings"], engine=engine)
        assert certificate["survivors"] == [routing]
    selected = prototype.generate(17, {"routing": "min_color_turn"}, demos, 4)
    branches = {prototype.analyze_input(pair["input"])["turn"] for pair in selected["train"]}
    assert branches == {"clockwise", "counterclockwise"}


def test_one_query_prefix_is_stable(prototype):
    one = prototype.generate(31, {"routing": "min_color_turn"}, 3, 1)
    four = prototype.generate(31, {"routing": "min_color_turn"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]


@pytest.mark.parametrize("settings", [
    {}, {"routing": "other"}, {"routing": True}, {"routing": "diagonal", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


@pytest.mark.parametrize("field,value", [
    ("seed", -1), ("seed", True), ("demos", 1), ("demos", 7),
    ("queries", 0), ("queries", 5), ("queries", "4"),
])
def test_invalid_numeric_requests_fail(prototype, field, value):
    args = {"seed": 0, "settings": {"routing": "diagonal"}, "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


def test_teaching_rejects_an_uninformative_duplicate_lesson(prototype, engine):
    episode = prototype.generate(9, {"routing": "diagonal"}, 2, 4)
    pair = deepcopy(episode["train"][0])
    with pytest.raises(ValueError, match="identify"):
        prototype.check_teaching([pair, pair], {"routing": "diagonal"}, engine=engine)


def test_wrong_selected_turn_changes_nondefault_output(prototype, engine):
    episode = prototype.generate(73, {"routing": "min_color_turn"}, 2, 4)
    pair = next(
        pair for pair in episode["train"] + episode["test"]
        if prototype.analyze_input(pair["input"])["turn"] == "counterclockwise"
    )
    actual = engine.apply(prototype.program({"routing": "min_color_turn"}), pair["input"])
    wrong = engine.apply(prototype.ALWAYS_CLOCKWISE_PROGRAM, pair["input"])
    assert actual == pair["output"]
    assert wrong != actual
