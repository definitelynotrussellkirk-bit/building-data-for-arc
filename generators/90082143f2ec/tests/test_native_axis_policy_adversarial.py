"""Independent, bounded semantic checks for the native axis-policy adapter.

The oracle below uses only grid values.  It does not import the production
generator, either historical prototype, or the adapter's observable helpers.
Protected Racket remains the authority for the retained program labels.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper, wrap_rule


TASK_HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = TASK_HOME / "workspace" / "parametric" / "adapter.py"
POLICIES = ("more_coherent", "less_coherent")

# Start with AABBCC = 991155 and change five cells, one in each of five
# different rows/columns.  Row 2 stays tied at two occurrences of 1, 5 and 9.
# Its lowest-color mode is 1, while first-seen and highest-color ties choose 9.
TIED_INPUT = [
    [1, 9, 1, 1, 5, 5],
    [9, 9, 5, 1, 5, 5],
    [9, 9, 1, 1, 5, 5],
    [9, 1, 1, 1, 5, 5],
    [9, 9, 1, 5, 5, 5],
    [9, 9, 1, 1, 5, 9],
]
HAND_ROW_MODES = [1, 5, 1, 1, 5, 9]
HAND_COLUMN_MODES = [9, 9, 1, 1, 5, 5]
HAND_ANSWERS = {
    "more_coherent": [HAND_COLUMN_MODES[:] for _ in range(6)],
    "less_coherent": [[color] * 6 for color in HAND_ROW_MODES],
}


def _line_mode(values, *, highest_tie=False):
    counts = Counter(values)
    top_count = max(counts.values())
    candidates = [value for value, count in counts.items() if count == top_count]
    return max(candidates) if highest_tie else min(candidates)


def _axis_answers(grid, *, highest_tie=False):
    """Construct both hypotheses independently, including modal tie order."""
    height, width = len(grid), len(grid[0])
    row_modes = [_line_mode(row, highest_tie=highest_tie) for row in grid]
    column_modes = [
        _line_mode(column, highest_tie=highest_tie) for column in zip(*grid)
    ]
    answers = {
        "rows": [[color] * width for color in row_modes],
        "columns": [column_modes[:] for _ in range(height)],
    }
    scores = {
        axis: sum(
            actual == proposed
            for row, prediction in zip(grid, answer)
            for actual, proposed in zip(row, prediction)
        )
        for axis, answer in answers.items()
    }
    return answers, scores


def _oracle(grid, policy, *, highest_tie=False):
    answers, scores = _axis_answers(grid, highest_tie=highest_tie)
    if policy == "more_coherent":
        axis = "columns" if scores["columns"] > scores["rows"] else "rows"
    else:
        axis = "columns" if scores["columns"] < scores["rows"] else "rows"
    return answers[axis]


def _callable(source):
    # Both admitted sources are callable lambda/let expressions.  Use the
    # shared source helpers, as the historical sibling's Racket runner does.
    return strip_rule_wrapper(strip_line_comments(source))


def _racket_output(bridge, source, grid):
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {literal})")


@pytest.fixture(scope="module")
def adapter():
    spec = importlib.util.spec_from_file_location(
        "native_axis_policy_independent_adversarial_adapter", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as active:
        identity = active.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        yield active


@pytest.fixture(scope="module")
def episodes(adapter):
    return {
        policy: adapter.generate(
            17, {"axis_policy": policy}, demos=2, queries=4
        )
        for policy in POLICIES
    }


@pytest.mark.parametrize("policy", POLICIES)
def test_literal_tie_fixture_has_hand_checked_modes_and_answer(adapter, policy):
    answers, scores = _axis_answers(TIED_INPUT)
    assert scores == {"rows": 17, "columns": 31}
    assert [row[0] for row in answers["rows"]] == HAND_ROW_MODES
    assert answers["columns"][0] == HAND_COLUMN_MODES
    assert _oracle(TIED_INPUT, policy) == HAND_ANSWERS[policy]
    assert adapter.solve(TIED_INPUT, {"axis_policy": policy}) == HAND_ANSWERS[policy]
    assert _oracle(TIED_INPUT, "less_coherent", highest_tie=True)[2] == [9] * 6
    assert HAND_ANSWERS["less_coherent"][2] == [1] * 6


@pytest.mark.parametrize("policy", POLICIES)
def test_literal_tie_fixture_has_protected_racket_parity(adapter, bridge, policy):
    actual = _racket_output(
        bridge, adapter.program({"axis_policy": policy}), TIED_INPUT
    )
    assert actual == HAND_ANSWERS[policy]


def test_wrong_order_erases_information_with_protected_racket_labels(adapter, bridge):
    more = adapter.program({"axis_policy": "more_coherent"})
    less = adapter.program({"axis_policy": "less_coherent"})
    wrong_order = f"(rule! (lambda (g) ({_callable(less)} ({_callable(more)} g))))"
    intended = _racket_output(bridge, less, TIED_INPUT)
    reordered = _racket_output(bridge, wrong_order, TIED_INPUT)
    assert intended == HAND_ANSWERS["less_coherent"]
    assert reordered == [[1] * 6 for _ in range(6)]
    assert intended != reordered


def test_two_small_demonstrations_teach_axis_and_lowest_color_ties(episodes):
    more = episodes["more_coherent"]
    less = episodes["less_coherent"]
    assert len(more["train"]) == len(less["train"]) == 2
    assert len(more["test"]) == len(less["test"]) == 4
    more_inputs = [pair["input"] for pair in more["train"] + more["test"]]
    less_inputs = [pair["input"] for pair in less["train"] + less["test"]]
    assert more_inputs == less_inputs
    assert len({tuple(map(tuple, grid)) for grid in more_inputs}) == 6

    dominant_axes = []
    tie_witnesses = 0
    for pair in less["train"]:
        grid = pair["input"]
        assert (len(grid), len(grid[0])) == (6, 6)
        _, scores = _axis_answers(grid)
        assert scores["rows"] != scores["columns"]
        dominant_axes.append(max(scores, key=scores.get))
        assert len({cell for row in pair["output"] for cell in row}) >= 3
        tie_witnesses += (
            _oracle(grid, "less_coherent", highest_tie=True) != pair["output"]
        )
    assert set(dominant_axes) == {"rows", "columns"}
    assert tie_witnesses >= 1


@pytest.mark.parametrize("policy", POLICIES)
def test_generated_labels_match_source_independent_coherence_oracle(episodes, policy):
    episode = episodes[policy]
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == _oracle(pair["input"], policy)


def test_demonstrations_eliminate_fixed_axes_global_fill_and_wrong_order(episodes):
    for policy, episode in episodes.items():
        for axis in ("rows", "columns"):
            assert any(
                _axis_answers(pair["input"])[0][axis] != pair["output"]
                for pair in episode["train"]
            ), (policy, axis)
        assert all(
            len({cell for row in pair["output"] for cell in row}) > 1
            for pair in episode["train"]
        ), policy

    for pair in episodes["less_coherent"]["train"]:
        wrong_order = _oracle(
            _oracle(pair["input"], "more_coherent"), "less_coherent"
        )
        assert wrong_order != pair["output"]


@pytest.mark.parametrize("policy", POLICIES)
def test_generated_small_and_30_square_cases_have_protected_racket_parity(
    adapter, bridge, episodes, policy
):
    episode = episodes[policy]
    large = [
        pair for pair in episode["test"]
        if (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    ]
    assert len(large) == 1
    source = adapter.program({"axis_policy": policy})
    for pair in episode["train"] + large:
        actual = _racket_output(bridge, source, pair["input"])
        assert actual == pair["output"] == _oracle(pair["input"], policy)
