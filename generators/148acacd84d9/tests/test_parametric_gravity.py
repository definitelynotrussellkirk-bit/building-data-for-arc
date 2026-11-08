"""Native rotate-then-marker-gravity parametric contract regressions."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_148_parametric_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("adapter")
prototype = _load("prototype")
rules = _load("rules")

CANONICAL = "(rule! (rotate-cw g))"
SETTINGS = (
    {"post_rotation": "none"},
    {"post_rotation": "marker_relay"},
)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_source():
    assert adapter.program(SETTINGS[0]) == CANONICAL
    assert (PARAMETRIC / "canonical.rkt").read_text() == CANONICAL


@pytest.mark.parametrize("settings", [
    {},
    {"post_rotation": "gravity"},
    {"post_rotation": "none", "extra": 1},
    {"post_rotation": 1},
    None,
])
def test_settings_are_strict(settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("name,value", [
    ("seed", -1), ("seed", 2**63), ("seed", True),
    ("demos", 1), ("demos", 7), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", False),
])
def test_seed_and_count_limits_are_exact(name, value):
    args = {"seed": 0, "settings": SETTINGS[0], "demos": 3, "queries": 4}
    args[name] = value
    with pytest.raises(ValueError):
        adapter.generate(**args)


def test_setting_neutral_inputs_are_distinct_and_outputs_diverge():
    canonical = adapter.generate(17, SETTINGS[0], demos=6, queries=4)
    gravity = adapter.generate(17, SETTINGS[1], demos=6, queries=4)
    assert _inputs(canonical) == _inputs(gravity)
    assert len({repr(grid) for grid in _inputs(canonical)}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(
        canonical["train"] + canonical["test"],
        gravity["train"] + gravity["test"],
    ))
    assert canonical["program_solution"] == CANONICAL
    assert gravity["program_solution"] == adapter.program(SETTINGS[1])


def test_demo_and_query_prefixes_are_stable():
    short_demo = adapter.generate(29, SETTINGS[1], demos=2, queries=4)
    long_demo = adapter.generate(29, SETTINGS[1], demos=6, queries=4)
    one_query = adapter.generate(29, SETTINGS[1], demos=3, queries=1)
    four_queries = adapter.generate(29, SETTINGS[1], demos=3, queries=4)
    assert short_demo["train"] == long_demo["train"][:2]
    assert one_query["train"] == four_queries["train"]
    assert one_query["test"] == four_queries["test"][:1]


def test_public_turn_reveals_one_query_without_private_hints():
    episode = adapter.generate(41, SETTINGS[1], demos=3, queries=4)
    visible = prototype.public_turn(episode, 2)
    assert set(visible) == {"train", "test"}
    assert visible["train"] == episode["train"]
    assert visible["test"] == [{"input": episode["test"][2]["input"]}]
    visible["train"][0]["input"][0][0] = 8
    assert visible["train"] != episode["train"], "projection must deep-copy public grids"
    for bad in (-1, 4, True):
        with pytest.raises(ValueError):
            prototype.public_turn(episode, bad)


def test_fourth_query_is_substantive_30_by_30_stress():
    episode = adapter.generate(7, SETTINGS[1], demos=3, queries=4)
    grid = episode["test"][3]["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    occupied = [(r, c, value) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value != 0]
    assert len(occupied) >= 60
    assert len({value for _, _, value in occupied}) >= 7
    assert len({r for r, _, _ in occupied}) >= 15
    assert len({c for _, c, _ in occupied}) >= 15
    assert sum(value == 9 for _, _, value in occupied) == 1


_BORDER_CASES = [
    (
        [[0, 0, 9, 0, 0],
         [0, 3, 0, 4, 0],
         [5, 0, 1, 0, 6],
         [0, 7, 0, 8, 0],
         [0, 0, 0, 0, 0]],
        [[0, 0, 0, 7, 5],
         [0, 0, 0, 1, 3],
         [0, 0, 0, 8, 9],
         [0, 0, 0, 0, 4],
         [0, 0, 0, 0, 6]],
    ),
    (
        [[0, 0, 0, 0, 0],
         [0, 3, 0, 4, 0],
         [5, 0, 6, 2, 9],
         [0, 7, 0, 8, 0],
         [0, 0, 0, 0, 0]],
        [[0, 0, 0, 0, 0],
         [5, 0, 0, 0, 0],
         [6, 0, 0, 0, 0],
         [7, 2, 3, 0, 0],
         [8, 4, 9, 0, 0]],
    ),
    (
        [[0, 0, 0, 0, 0],
         [0, 3, 0, 4, 0],
         [5, 0, 6, 0, 7],
         [0, 8, 1, 0, 0],
         [0, 0, 9, 0, 0]],
        [[5, 3, 6, 0, 0],
         [8, 1, 0, 0, 0],
         [9, 0, 0, 0, 0],
         [4, 0, 0, 0, 0],
         [7, 0, 0, 0, 0]],
    ),
    (
        [[0, 0, 0, 0, 0],
         [0, 3, 0, 4, 0],
         [9, 2, 6, 0, 7],
         [0, 8, 0, 5, 0],
         [0, 0, 0, 0, 0]],
        [[8, 3, 9, 0, 0],
         [5, 2, 4, 0, 0],
         [6, 0, 0, 0, 0],
         [7, 0, 0, 0, 0],
         [0, 0, 0, 0, 0]],
    ),
]


@pytest.mark.parametrize("grid,expected", _BORDER_CASES)
def test_python_marker_relay_matches_literal_border_cases(grid, expected):
    assert rules.python_apply(grid, "marker_relay") == expected
    assert rules.python_apply(grid, "none") != expected


def _racket_apply(program, grid):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import normalize_grid

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {literal})"))


@pytest.mark.parametrize("grid,expected", _BORDER_CASES)
def test_protected_racket_marker_relay_matches_literal_border_cases(grid, expected):
    program = rules.program({"post_rotation": "marker_relay"})
    assert _racket_apply(program, grid) == expected


def test_relay_intermediate_records_contact_cue_and_second_edge():
    grid, _ = _BORDER_CASES[0]
    trace = rules.relay_trace(grid)
    assert trace["first_edge"] == "right"
    assert trace["contact_color"] == 1
    assert trace["second_edge"] == "top"
    assert trace["marker"] == [2, 4]


def test_wrong_intermediate_and_wrong_order_change_the_final_output():
    grid, expected = _BORDER_CASES[0]
    correct = _racket_apply(rules.program({"post_rotation": "marker_relay"}), grid)
    assert correct == expected
    wrong_intermediate = _racket_apply(rules.counterfactual_program("wrong_intermediate"), grid)
    wrong_order = _racket_apply(rules.counterfactual_program("wrong_order"), grid)
    assert wrong_intermediate != correct
    assert wrong_order != correct


def test_adapter_uses_exact_rules_module_program_and_claims():
    episode = adapter.generate(53, SETTINGS[1], demos=3, queries=4)
    assert episode["program_solution"] == rules.program(SETTINGS[1])
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == rules.python_apply(pair["input"], "marker_relay")


def test_two_demo_protected_racket_audit_refutes_every_harmful_rival(tmp_path):
    audit_module = _load("self_audit")
    out = tmp_path / "self-audit.json"
    report = audit_module.audit(out, seeds=(0,), demos=2, queries=4)

    assert out.is_file()
    assert report == __import__("json").loads(out.read_text())
    assert report["status"] == "pass"
    assert report["failure_count"] == 0
    assert report["queries"] == 4
    assert report["demo_counts"] == [2]
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["racket_evaluations"] > 0
    assert len(report["jobs"]) == 2

    relay_job = next(job for job in report["jobs"]
                     if job["settings"] == {"post_rotation": "marker_relay"})
    statuses = {row["rival"]: row for row in relay_job["rivals"]}
    assert statuses["declared_marker_relay"]["status"] == "selected"
    for name in (
        "declared_none",
        "skip_a",
        "skip_b",
        "wrong_order",
        "wrong_intermediate",
        "opposite_second_edge",
        "always_top",
        "always_left",
    ):
        assert statuses[name]["status"] == "refuted"
        assert statuses[name]["refuting_demo_indices"]
    assert all(row["query_count"] == 4 for row in relay_job["rivals"])
