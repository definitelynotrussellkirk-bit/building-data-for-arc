"""Focused contract tests for the native chamber-legend parametric adapter."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "67a09b7f6b66"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "Native parametric adapter is not implemented"
    name = "_test_67a09_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def visible_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_canonical_default_matches_exact_authority_byte_for_byte():
    adapter = load_adapter()
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).open(encoding="utf-8")
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    assert adapter.program({"legend_mapping": "absolute_count"}) == next(iter(programs))
    assert adapter.program({"legend_mapping": "anchor_cycle"}) not in programs


@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_counts_matched_inputs_distinctness_and_size_stress(demos, queries):
    adapter = load_adapter()
    canonical = adapter.generate(17, {"legend_mapping": "absolute_count"}, demos, queries)
    composed = adapter.generate(17, {"legend_mapping": "anchor_cycle"}, demos, queries)

    assert len(canonical["train"]) == len(composed["train"]) == demos
    assert len(canonical["test"]) == len(composed["test"]) == queries
    assert visible_inputs(canonical) == visible_inputs(composed)
    assert len({json.dumps(grid) for grid in visible_inputs(canonical)}) == demos + queries
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], composed["train"], strict=True)
    )

    for grid in visible_inputs(canonical):
        facts = adapter.analyze(grid)
        assert 1 <= facts["height"] <= 30
        assert 1 <= facts["width"] <= 30
        assert facts["counts"] == sorted(facts["counts"])
        assert facts["anchor_count"] in {1, 2, 3}
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)

    if queries == 4:
        stress = canonical["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        facts = adapter.analyze(stress)
        assert facts["chamber_widths"] == [8, 9, 9]
        assert facts["anchor_count"] == 3
        assert sum(value == 8 for row in stress for value in row) >= 130
        assert sum(value != 0 for row in composed["test"][-1]["output"] for value in row) >= 700


def test_two_demos_teach_a_changing_input_derived_anchor_count():
    adapter = load_adapter()
    episode = adapter.generate(0, {"legend_mapping": "anchor_cycle"}, 2, 4)
    analyses = [adapter.analyze(pair["input"]) for pair in episode["train"]]
    assert [item["anchor_count"] for item in analyses] == [2, 3]
    assert len({item["anchor_chamber"] for item in analyses}) >= 1
    assert all(
        pair["output"] == adapter.transform(pair["input"], "anchor_cycle")
        for pair in episode["train"] + episode["test"]
    )


def test_generation_is_deterministic_prefix_stable_and_rng_private():
    import random

    adapter = load_adapter()
    random.seed(123456)
    state = random.getstate()
    small = adapter.generate(23, {"legend_mapping": "anchor_cycle"}, 2, 1)
    large = adapter.generate(23, {"legend_mapping": "anchor_cycle"}, 6, 4)
    again = adapter.generate(23, {"legend_mapping": "anchor_cycle"}, 6, 4)
    assert random.getstate() == state
    assert large == again
    assert small["train"] == large["train"][:2]
    assert small["test"][0] == large["test"][0]


def test_public_turn_hides_settings_program_answers_and_future_queries():
    adapter = load_adapter()
    episode = adapter.generate(17, {"legend_mapping": "anchor_cycle"}, 3, 4)
    before = deepcopy(episode)
    first = adapter.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    assert episode == before

    changed = deepcopy(episode)
    changed["seed"] = 999
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "PRIVATE CHANGED PROGRAM"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn(changed, 0) == first
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    assert public_challenge_id(episode) == public_challenge_id(changed)


@pytest.mark.parametrize("index", [-1, 4, True, False, 1.0, "0", None])
def test_public_turn_rejects_non_current_query_indices(index):
    adapter = load_adapter()
    episode = adapter.generate(17, {"legend_mapping": "anchor_cycle"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.public_turn(episode, index)


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"legend_mapping": "unknown"}, 3, 4),
        ({"legend_mapping": True}, 3, 4),
        ({"legend_mapping": "absolute_count", "extra": 1}, 3, 4),
        ({"legend_mapping": "absolute_count"}, 1, 4),
        ({"legend_mapping": "absolute_count"}, 7, 4),
        ({"legend_mapping": "absolute_count"}, 3, 0),
        ({"legend_mapping": "absolute_count"}, 3, 5),
        ({"legend_mapping": "absolute_count"}, True, 4),
    ],
)
def test_invalid_contract_requests_fail_closed(settings, demos, queries):
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos, queries)


def test_rival_programs_are_declared_and_python_rivals_are_refuted_by_demos():
    adapter = load_adapter()
    assert set(adapter.RIVALS) == {
        "position_only",
        "occupied_rows",
        "fixed_anchor_1",
        "fixed_anchor_2",
        "fixed_anchor_3",
    }
    relevant = {
        "absolute_count": {"position_only", "occupied_rows", "fixed_anchor_2", "fixed_anchor_3"},
        "anchor_cycle": set(adapter.RIVALS),
    }
    for setting in ("absolute_count", "anchor_cycle"):
        episode = adapter.generate(11, {"legend_mapping": setting}, 3, 4)
        expected = [pair["output"] for pair in episode["train"]]
        for rival in relevant[setting]:
            outputs = [adapter.rival_transform(pair["input"], rival) for pair in episode["train"]]
            assert outputs != expected, (setting, rival)


def test_selected_programs_match_claimed_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    adapter = load_adapter()
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for mapping in ("absolute_count", "anchor_cycle"):
            episode = adapter.generate(0, {"legend_mapping": mapping}, 2, 4)
            for pair in (episode["train"][0], episode["test"][-1]):
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(
                    f"({wrap_rule(episode['program_solution'])} {literal})"
                )
                assert actual == pair["output"]
