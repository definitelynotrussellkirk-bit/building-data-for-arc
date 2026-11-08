"""Behavioral contract for the separate projection-depth family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"


def load(name: str = "adapter"):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"test_d660_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_authority():
    adapter = load()
    canonical = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row.get("task_id") == "d6607fc42bcc"
    }
    assert canonical == {adapter.program({"projection_depth": "one"})}
    assert adapter.program({"projection_depth": "dot_offset"}) not in canonical


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_prefix_distinctness_and_matched_setting_inputs(demos, queries):
    adapter = load()
    one = adapter.generate(17, {"projection_depth": "one"}, demos, queries)
    dot = adapter.generate(17, {"projection_depth": "dot_offset"}, demos, queries)
    full = adapter.generate(17, {"projection_depth": "one"}, demos, 4)

    assert len(one["train"]) == demos
    assert len(one["test"]) == queries
    assert one["train"] == full["train"]
    assert one["test"] == full["test"][:queries]
    assert episode_inputs(one) == episode_inputs(dot)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in episode_inputs(one)]
    assert len(serialized) == len(set(serialized))
    assert one["program_solution"] == adapter.program({"projection_depth": "one"})
    assert dot["program_solution"] == adapter.program({"projection_depth": "dot_offset"})


@pytest.mark.parametrize("setting", ["one", "dot_offset"])
def test_every_supported_demo_prefix_identifies_setting_against_declared_rivals(setting):
    prototype = load("prototype")
    for demos in range(2, 7):
        episode = prototype.generate(29, {"projection_depth": setting}, demos, 4)
        certificate = prototype.teaching_certificate(episode)
        assert certificate["survivors"] == [{"projection_depth": setting}]
        assert certificate["query_answers_used"] is False
        assert certificate["shortcut_survivors"] == []


def test_dot_offset_rule_uses_dot_distance_to_choose_projection_depth():
    prototype = load("prototype")
    grid = [[0] * 9 for _ in range(10)]
    # Frame rows 3..8, columns 2..6, top notch at (3,4), dot at (5,4).
    # The dot is two rows from the notched edge, so the alternate must paint
    # both exterior rows 1 and 2; the canonical default paints only row 2.
    for c in range(2, 7):
        grid[3][c] = 1
        grid[8][c] = 1
    for r in range(4, 8):
        grid[r][2] = 1
        grid[r][6] = 1
    grid[3][4] = 0
    grid[5][4] = 7

    canonical = prototype.claimed_output(deepcopy(grid), {"projection_depth": "one"})
    alternate = prototype.claimed_output(deepcopy(grid), {"projection_depth": "dot_offset"})

    assert canonical[1][2:7] == [0, 0, 0, 0, 0]
    assert canonical[2][2:7] == [7, 7, 7, 7, 7]
    assert alternate[1][2:7] == [7, 7, 7, 7, 7]
    assert alternate[2][2:7] == [7, 7, 7, 7, 7]
    assert alternate[3][4] == 7
    assert all(alternate[r][c] == 7 for r in range(4, 8) for c in range(3, 6))


def test_fourth_query_is_substantive_30x30_and_settings_disagree():
    adapter = load()
    one = adapter.generate(91, {"projection_depth": "one"}, 3, 4)
    dot = adapter.generate(91, {"projection_depth": "dot_offset"}, 3, 4)
    pair_one = one["test"][3]
    pair_dot = dot["test"][3]

    assert (len(pair_one["input"]), len(pair_one["input"][0])) == (30, 30)
    assert pair_one["input"] == pair_dot["input"]
    assert pair_one["output"] != pair_dot["output"]
    nonzero_input = sum(value != 0 for row in pair_one["input"] for value in row)
    changed = sum(
        a != b
        for input_row, output_row in zip(pair_dot["input"], pair_dot["output"])
        for a, b in zip(input_row, output_row)
    )
    assert nonzero_input >= 70
    assert changed >= 120


def test_visible_turn_has_no_future_queries_or_private_setting():
    prototype = load("prototype")
    episode = prototype.generate(7, {"projection_depth": "dot_offset"}, 3, 4)
    first = prototype.generate(7, {"projection_depth": "dot_offset"}, 3, 1)
    visible = prototype.visible_turn(episode, 0)

    assert visible == public_challenge_bytes(first)
    parsed = json.loads(visible)
    assert len(parsed["test"]) == 1
    assert "output" not in parsed["test"][0]
    text = visible.decode("utf-8")
    assert "projection_depth" not in text
    assert "dot_offset" not in text


@pytest.mark.parametrize(
    "changes",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"settings": {}},
        {"settings": {"projection_depth": "two"}},
        {"settings": {"projection_depth": "one", "extra": 1}},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
    ],
)
def test_invalid_controls_are_rejected(changes):
    adapter = load()
    kwargs = dict(seed=17, settings={"projection_depth": "one"}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        adapter.generate(**kwargs)


def test_executable_racket_shortcuts_match_independent_python_predictions_and_lose_on_demos():
    """A wrong depth formula must be both executable and visibly rejected."""
    prototype = load("prototype")
    rivals = load("rivals")
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    expected_names = {
        "fixed_two",
        "no_exterior_bar",
        "bar_only",
        "opposite_edge_distance",
        "interior_height",
        "nearest_edge_distance",
    }
    episode = prototype.generate(0, {"projection_depth": "dot_offset"}, 2, 1)
    materialized = rivals.programs(prototype.program({"projection_depth": "dot_offset"}))
    assert set(materialized) == expected_names
    assert len(set(materialized.values())) == len(expected_names)

    runtime = ROOT / "shared" / "runtime"
    bridge = None
    try:
        with _local_imports(runtime, PARAMETRIC):
            apply, identity, bridge = _real_evaluator(runtime)
            assert identity["backend"] == "racket"
            assert identity["protected"] is True
            for name, rival_program in materialized.items():
                actual = [_grid(apply(rival_program, pair["input"])) for pair in episode["train"]]
                expected = [prototype.shortcut_output(pair["input"], name) for pair in episode["train"]]
                assert actual == expected
                assert any(output != pair["output"] for output, pair in zip(actual, episode["train"]))
    finally:
        if bridge is not None:
            bridge.close()


def test_bounded_audit_executes_reference_and_rivals_without_using_query_answers():
    """The reusable audit must prove its finite claims with protected Racket."""
    audit = load("audit")
    report = audit.run_bounded(
        sampler_seeds=range(2), execution_seeds=(0,), demos=2, queries=1
    )

    assert report["status"] == "passed"
    assert report["query_answers_used_for_rival_selection"] is False
    assert report["runtime"]["backend"] == "racket"
    assert report["runtime"]["protected"] is True
    assert report["sampler_requests"] == 4
    assert report["racket_evaluations"] >= 30
    for mode in ("one", "dot_offset"):
        assert set(report["rivals"][mode]) == {
            "fixed_two",
            "no_exterior_bar",
            "bar_only",
            "opposite_edge_distance",
            "interior_height",
            "nearest_edge_distance",
        }
        assert all(
            item["mismatch_demo_indices"]
            and item["python_prediction_matches_racket"] is True
            for item in report["rivals"][mode].values()
        )
