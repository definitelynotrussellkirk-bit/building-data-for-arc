"""Protected-Racket tests for endpoint/longest-color run projection."""
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
    spec = importlib.util.spec_from_file_location(f"_8a761b80b11b_{name}", path)
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
    assert prototype.program({"marking": "endpoints"}) == prototype.CANONICAL_PROGRAM


def test_hand_fixture_distinguishes_both_rules(prototype, engine):
    grid = prototype.fixture_grid(
        7, 12,
        runs=[
            (0, 1, 4, 2),
            (2, 3, 9, 6),
            (4, 0, 2, 6),
            (6, 6, 10, 4),
        ],
    )
    info = prototype.analyze_input(grid)
    assert info["anchor_color"] == 6
    endpoints = engine.apply(prototype.program({"marking": "endpoints"}), grid)
    selected = engine.apply(prototype.program({"marking": "longest_color_gate"}), grid)
    assert endpoints == prototype.python_oracle(grid, {"marking": "endpoints"})
    assert selected == prototype.python_oracle(grid, {"marking": "longest_color_gate"})
    assert endpoints != selected


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_labels_teaching_branches_and_30x30_boundary(prototype, engine, demos):
    for marking in prototype.MARKINGS:
        episode = prototype.generate(17, {"marking": marking}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert [len(inputs[-1]), len(inputs[-1][0])] == [30, 30]
        assert sum(cell != 0 for row in inputs[-1] for cell in row) >= 80
        for pair in episode["train"] + episode["test"]:
            assert engine.apply(episode["program_solution"], pair["input"]) == pair["output"]
        certificate = prototype.check_teaching(episode["train"], episode["settings"], engine=engine)
        assert certificate["survivors"] == [marking]
    gated = prototype.generate(17, {"marking": "longest_color_gate"}, demos, 4)
    demo_runs = [run for pair in gated["train"] for run in prototype.analyze_input(pair["input"])["runs"]]
    assert any(run["color"] == prototype.analyze_input(pair["input"])["anchor_color"]
               for pair in gated["train"] for run in prototype.analyze_input(pair["input"])["runs"])
    non_anchor_lengths = [run["length"] for pair in gated["train"]
                          for run in prototype.analyze_input(pair["input"])["runs"]
                          if run["color"] != prototype.analyze_input(pair["input"])["anchor_color"]]
    assert any(length % 2 == 0 for length in non_anchor_lengths)
    assert any(length % 2 == 1 for length in non_anchor_lengths)


def test_one_query_prefix_is_stable(prototype):
    one = prototype.generate(31, {"marking": "longest_color_gate"}, 3, 1)
    four = prototype.generate(31, {"marking": "longest_color_gate"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]


@pytest.mark.parametrize("settings", [
    {}, {"marking": "other"}, {"marking": True}, {"marking": "endpoints", "extra": 1},
])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.program(settings)


@pytest.mark.parametrize("field,value", [
    ("seed", -1), ("seed", True), ("demos", 1), ("demos", 7),
    ("queries", 0), ("queries", 5), ("queries", "4"),
])
def test_invalid_numeric_requests_fail(prototype, field, value):
    args = {"seed": 0, "settings": {"marking": "endpoints"}, "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        prototype.generate(**args)


def test_teaching_rejects_an_uninformative_duplicate_lesson(prototype, engine):
    episode = prototype.generate(9, {"marking": "endpoints"}, 2, 4)
    pair = deepcopy(episode["train"][0])
    with pytest.raises(ValueError, match="identify"):
        prototype.check_teaching([pair, pair], {"marking": "endpoints"}, engine=engine)


def test_wrong_anchor_changes_nondefault_output(prototype, engine):
    episode = prototype.generate(73, {"marking": "longest_color_gate"}, 2, 4)
    pair = episode["test"][0]
    info = prototype.analyze_input(pair["input"])
    assert info["first_run_color"] != info["anchor_color"]
    actual = engine.apply(prototype.program({"marking": "longest_color_gate"}), pair["input"])
    wrong = engine.apply(prototype.FIRST_RUN_COLOR_GATE_PROGRAM, pair["input"])
    assert actual == pair["output"]
    assert wrong != actual
