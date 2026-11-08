"""Behavioral contract for the proposed fill-then-select native adapter."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "generators/89c85768abe1/workspace/parametric/adapter.py"


def adapter():
    assert PATH.is_file(), "Native rectangle-component adapter is not implemented"
    spec = importlib.util.spec_from_file_location("test_rectangle_component_adapter", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(*rows):
    return [[int(c) for c in row] for row in rows]


def test_component_area_requires_completion_and_preserves_colors():
    a = adapter()
    scene = grid("200300000", "002003000", "000000004", "000000000", "000000400")
    assert a.solve(scene, {"mode": "largest_component"}) == grid(
        "222333000", "222333000", "000000000", "000000000", "000000000")
    assert a.solve(scene, {"mode": "all"}) == grid(
        "222333000", "222333000", "000000444", "000000444", "000000444")


def test_default_program_is_exact_current_authority():
    a = adapter()
    from arcpuzzles.catalog import Catalog
    catalog = Catalog(ROOT)
    task = catalog.describe("89c85768abe1")
    programs = {x["program_solution"] for x in catalog._variants()[task.get("rule_task_id", task["id"]) ]}
    assert programs == {a.program({"mode": "all"})}


@pytest.mark.parametrize("seed", [0, 17, 91, 2**63 - 1])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 4)])
def test_independent_counts_determinism_unique_inputs_and_taught_rivals(seed, demos, queries):
    a = adapter()
    by_mode = {}
    for mode in ("all", "largest_component"):
        settings = {"mode": mode}
        e = a.generate(seed, settings, demos, queries)
        assert len(e["train"]) == demos and len(e["test"]) == queries
        assert e == a.generate(seed, settings, demos, queries)
        pairs = e["train"] + e["test"]
        assert len({json.dumps(p["input"]) for p in pairs}) == demos + queries
        assert a.teaching_report(e, settings)["accepted"]
        assert all(not a.validate_input(p["input"]) for p in pairs)
        assert all(p["output"] == a.solve(p["input"], settings) for p in pairs)
        by_mode[mode] = [p["input"] for p in pairs]
        if queries == 4:
            large = e["test"][3]
            assert (len(large["input"]), len(large["input"][0])) == (30, 30)
            filled = a.solve(large["input"], {"mode": "all"})
            assert sum(v != 0 for row in filled for v in row) >= 180
    assert by_mode["all"] == by_mode["largest_component"]


def test_query_prefix_and_public_first_turn_ignore_future_queries():
    a = adapter()
    one = a.generate(17, {"mode": "largest_component"}, 3, 1)
    four = a.generate(17, {"mode": "largest_component"}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert a.visible_turn(one, 0) == a.visible_turn(four, 0)
    assert set(a.visible_turn(four, 0)) == {"train", "test"}
    assert len(a.visible_turn(four, 0)["test"]) == 1
    assert set(a.visible_turn(four, 0)["test"][0]) == {"input"}


def test_public_projection_and_id_ignore_private_fields():
    a = adapter()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    e = a.generate(0, {"mode": "largest_component"}, 2, 4)
    changed = deepcopy(e)
    changed["seed"] = 999
    changed["settings"] = {"mode": "all"}
    changed["program_solution"] = "private mutation"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert a.public_challenge(e) == a.public_challenge(changed)
    payload = public_challenge_bytes(a.public_challenge(e))
    assert public_challenge_id(a.public_challenge(e)) == hashlib.sha256(payload).hexdigest()


def test_changed_query_labels_and_untaught_lesson_are_rejected():
    a = adapter()
    e = a.generate(0, {"mode": "largest_component"}, 2, 4)
    corrupted = deepcopy(e)
    corrupted["test"][0]["output"][0][0] = (corrupted["test"][0]["output"][0][0] + 1) % 10
    assert not a.teaching_report(corrupted, {"mode": "largest_component"})["accepted"]
    # A one-component lesson cannot distinguish all-fill from largest-component.
    ambiguous = {"train": [{"input": grid("200300", "002003"),
                             "output": grid("222333", "222333")},
                            {"input": grid("400500", "004005"),
                             "output": grid("444555", "444555")}],
                 "test": e["test"]}
    report = a.teaching_report(ambiguous, {"mode": "largest_component"})
    assert not report["accepted"]
    assert "demonstrations do not identify the selected declared setting" in report["errors"]


def test_teaching_rejects_boolean_query_labels_that_compare_equal_to_zero():
    a = adapter()
    episode = a.generate(0, {"mode": "largest_component"}, 2, 1)
    pair = episode["test"][0]
    pair["output"] = [[False if value == 0 else value for value in row]
                      for row in pair["output"]]
    assert not a.teaching_report(episode, {"mode": "largest_component"})["accepted"]


def test_two_demos_distinguish_total_area_from_newly_painted_area():
    a = adapter()
    for seed in (0, 17, 91):
        episode = a.generate(seed, {"mode": "largest_component"}, 2, 4)
        rebutted = False
        for pair in episode["train"]:
            before = pair["input"]
            filled = a.solve(before, {"mode": "all"})
            groups = a.components(filled)
            winner = max(groups, key=lambda c: sum(before[r][col] == 0 for r, col in c))
            wrong = [[v if (r, col) in winner else 0 for col, v in enumerate(row)]
                     for r, row in enumerate(filled)]
            rebutted |= wrong != pair["output"]
        assert rebutted, f"seed {seed} never teaches total cells versus added cells"


def test_canonical_lesson_rejects_eight_connected_selection_and_queries_vary_group_count():
    a = adapter()
    counts = set()
    for seed in range(12):
        episode = a.generate(seed, {"mode": "all"}, 2, 4)
        assert "eight_connected" not in a.teaching_report(episode, {"mode": "all"})["surviving_demo_rivals"]
        counts.update(len(a.components(pair["output"])) for pair in episode["test"])
    assert {2, 3}.issubset(counts)


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"mode": "all"}, 3, 4), (-1, {"mode": "all"}, 3, 4),
    (2**63, {"mode": "all"}, 3, 4), (0, {"mode": "all"}, True, 4),
    (0, {"mode": "all"}, 1, 4), (0, {"mode": "all"}, 7, 4),
    (0, {"mode": "all"}, 3, 0), (0, {"mode": "all"}, 3, 5),
    (0, {"mode": 0}, 3, 4), (0, {"mode": "all", "extra": 1}, 3, 4),
])
def test_invalid_requests_fail_closed(seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter().generate(seed, settings, demos, queries)


@pytest.mark.parametrize("bad", [[], [[False]], [[1.0]], [[0], [0, 2]],
    [[2, 0], [0, 3]], [[2, 2], [3, 3]], [[2, 3, 0], [0, 2, 3]]])
def test_malformed_corner_grammar_is_rejected(bad):
    a = adapter()
    assert a.validate_input(bad)
    with pytest.raises(ValueError):
        a.solve(bad, {"mode": "largest_component"})
