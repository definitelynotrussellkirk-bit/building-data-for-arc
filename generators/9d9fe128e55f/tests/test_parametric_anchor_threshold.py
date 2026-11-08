from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HOME / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_racket(program: str, grid: list[list[int]], bridge: RacketBridge):
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def hand_grid() -> list[list[int]]:
    # Left panel width 8, separator column 8, one-column legend at 9.
    grid = [[0] * 10 for _ in range(8)]
    for row in grid:
        row[8] = 9
    grid[0][9], grid[1][9], grid[2][9] = 2, 4, 6
    # Size 2.
    grid[1][0] = grid[1][1] = 8
    # Size 4, and uniquely closest to the separator (right edge column 7).
    for r in (2, 3):
        for c in (6, 7):
            grid[r][c] = 8
    # Size 6.
    for r in (5, 6):
        for c in (0, 1, 2):
            grid[r][c] = 8
    return grid


CANONICAL_EXPECTED = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [2, 2, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 4, 4],
    [0, 0, 0, 0, 0, 0, 4, 4],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [6, 6, 6, 0, 0, 0, 0, 0],
    [6, 6, 6, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

THRESHOLD_EXPECTED = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 2],
    [0, 0, 0, 0, 0, 0, 2, 2],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [4, 4, 4, 0, 0, 0, 0, 0],
    [4, 4, 4, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


def test_exact_default_and_anchor_threshold_have_hand_checked_labels():
    prototype = load_module("parametric_9d9_proto_unit", "prototype.py")
    adapter = load_module("parametric_9d9_adapter_unit", "adapter.py")
    grid = hand_grid()

    assert adapter.program({"rank_policy": "all_by_size"}) == prototype.canonical_source()
    assert prototype.python_mirror(grid, "all_by_size") == CANONICAL_EXPECTED
    assert prototype.python_mirror(grid, "right_anchor_threshold") == THRESHOLD_EXPECTED
    assert prototype.anchor_size(grid) == 4

    with RacketBridge() as bridge:
        assert run_racket(prototype.program_for("all_by_size"), grid, bridge) == CANONICAL_EXPECTED
        assert (
            run_racket(prototype.program_for("right_anchor_threshold"), grid, bridge)
            == THRESHOLD_EXPECTED
        )


def test_two_demo_prefix_identifies_both_settings_and_queries_are_matched():
    prototype = load_module("parametric_9d9_proto_counts", "prototype.py")
    adapter = load_module("parametric_9d9_adapter_counts", "adapter.py")

    for seed in (0, 1, 17):
        episodes = {
            mode: adapter.generate(seed, {"rank_policy": mode}, demos=2, queries=4)
            for mode in prototype.MODES
        }
        left = episodes["all_by_size"]
        right = episodes["right_anchor_threshold"]
        assert len(left["train"]) == len(right["train"]) == 2
        assert len(left["test"]) == len(right["test"]) == 4
        assert [pair["input"] for pair in left["train"] + left["test"]] == [
            pair["input"] for pair in right["train"] + right["test"]
        ]
        assert len(left["test"][-1]["input"]) == 30
        assert len(left["test"][-1]["input"][0]) == 30
        encoded = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in left["train"] + left["test"]
        ]
        assert len(encoded) == len(set(encoded))
        for mode, episode in episodes.items():
            assert prototype.adversarial_survivors(episode["train"], mode) == []


def test_crossed_controls_vary_threshold_separately_from_nuisance_geometry():
    prototype = load_module("parametric_9d9_proto_cross", "prototype.py")
    episode = prototype.generate_claims(23, "right_anchor_threshold", demos=6, queries=4)
    analyses = [prototype.analyze_grid(pair["input"]) for pair in episode["train"]]

    # The first two demonstrations deliberately hold dimensions and the anchor's
    # right edge fixed while changing the input-derived threshold.
    assert analyses[0]["shape"] == analyses[1]["shape"]
    assert analyses[0]["anchor_right"] == analyses[1]["anchor_right"]
    assert analyses[0]["anchor_size"] != analyses[1]["anchor_size"]

    # A later pair holds the threshold fixed while changing component positions
    # and shapes, preventing a fixed motif/location shortcut.
    same_threshold = [row for row in analyses[2:] if row["anchor_size"] == analyses[0]["anchor_size"]]
    assert same_threshold
    assert any(row["component_cells"] != analyses[0]["component_cells"] for row in same_threshold)


def test_supported_count_boundaries_and_reject_malformed_requests():
    prototype = load_module("parametric_9d9_proto_validation", "prototype.py")
    adapter = load_module("parametric_9d9_adapter_validation", "adapter.py")

    for demos in (2, 3, 6):
        episode = adapter.generate(
            5,
            {"rank_policy": "right_anchor_threshold"},
            demos=demos,
            queries=4,
        )
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4

    bad_calls = [
        lambda: adapter.generate(True, {"rank_policy": "all_by_size"}, demos=2, queries=4),
        lambda: adapter.generate(0, {"rank_policy": "all_by_size"}, demos=1, queries=4),
        lambda: adapter.generate(0, {"rank_policy": "all_by_size"}, demos=7, queries=4),
        lambda: adapter.generate(0, {"rank_policy": "all_by_size"}, demos=2, queries=3),
        lambda: adapter.program({"rank_policy": "unknown"}),
        lambda: adapter.program({"rank_policy": "all_by_size", "extra": 1}),
    ]
    for call in bad_calls:
        with pytest.raises(ValueError):
            call()

    assert prototype.MODES == ("all_by_size", "right_anchor_threshold")


def test_two_demo_prefix_breaks_connectivity_and_other_query_changing_rivals():
    """A diagonal-contact lesson must kill the plausible 8-connectivity shortcut."""
    prototype = load_module("parametric_9d9_proto_extended_rivals", "prototype.py")

    for seed in (0, 5, 31, 97):
        episode = prototype.generate_claims(
            seed,
            "right_anchor_threshold",
            demos=2,
            queries=4,
        )
        survivors = [
            row
            for row in prototype.extended_rival_results(
                episode["train"], episode["test"], "right_anchor_threshold"
            )
            if row["fits_demos"] and row["query_disagreements"]
        ]
        assert survivors == []


def test_reusable_adversarial_probe_covers_promised_python_surface():
    probe = load_module("parametric_9d9_adversarial_probe", "adversarial_probe.py")
    report = probe.run_python_probe(seeds=(0, 5), demo_counts=(2, 6))

    assert report["case_count"] == 8
    assert report["bad_cases"] == []
    assert report["matched_input_checks"] == 4
    assert report["max_grid"] == [30, 30]
    assert "eight_connected" in report["rivals"]


def test_promotion_contract_qualifies_the_two_demo_minimum():
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 2
