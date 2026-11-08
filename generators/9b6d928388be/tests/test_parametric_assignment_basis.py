"""Focused contract and semantic tests for the keyed-frame parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> str:
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "9b6d928388be":
            return row["program_solution"]
    raise AssertionError("canonical source missing")


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_default_program_is_exact_canonical_and_settings_fail_closed():
    adapter = _load(PARAM / "adapter.py", "p9b_adapter_contract")
    assert adapter.program({"assignment_basis": "holes"}) == _canonical()
    assert (PARAM / "canonical.rkt").read_bytes() == _canonical().encode()
    for bad in (None, {}, {"assignment_basis": "bogus"},
                {"assignment_basis": True},
                {"assignment_basis": "holes", "extra": 1}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def test_inputs_are_matched_counts_independent_and_public_turn_hides_future():
    adapter = _load(PARAM / "adapter.py", "p9b_adapter_counts")
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        episodes = {
            basis: adapter.generate(17, {"assignment_basis": basis}, demos, queries)
            for basis in ("holes", "area_rank")
        }
        assert [p["input"] for p in episodes["holes"]["train"]] == [
            p["input"] for p in episodes["area_rank"]["train"]
        ]
        assert [p["input"] for p in episodes["holes"]["test"]] == [
            p["input"] for p in episodes["area_rank"]["test"]
        ]
        for episode in episodes.values():
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            visible = adapter.public_turn(copy.deepcopy(episode), 0)
            assert visible == {
                "train": episode["train"],
                "test": [{"input": episode["test"][0]["input"]}],
            }
            assert "program_solution" not in repr(visible)
            if queries > 1:
                extended = copy.deepcopy(episode)
                extended["test"][1]["input"][0][0] = (
                    extended["test"][1]["input"][0][0] + 1
                ) % 10
                assert adapter.public_turn(extended, 0) == visible


def test_racket_labels_teach_basis_and_include_substantive_30x30_stress():
    adapter = _load(PARAM / "adapter.py", "p9b_adapter_racket")
    episodes = {
        basis: adapter.generate(0, {"assignment_basis": basis}, 2, 4)
        for basis in ("holes", "area_rank")
    }
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
               for pair in episodes["holes"]["test"])
    assert [p["input"] for p in episodes["holes"]["train"]] == [
        p["input"] for p in episodes["area_rank"]["train"]
    ]
    programs = {basis: adapter.program({"assignment_basis": basis}) for basis in episodes}
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for basis, episode in episodes.items():
            for pair in (*episode["train"], *episode["test"]):
                assert _apply(bridge, programs[basis], pair["input"]) == pair["output"]
        for basis, episode in episodes.items():
            rival = "area_rank" if basis == "holes" else "holes"
            assert any(
                _apply(bridge, programs[rival], pair["input"]) != pair["output"]
                for pair in episode["train"]
            )


def test_area_rank_intermediate_is_input_dependent_and_wrong_rank_changes_output():
    prototype = _load(PARAM / "prototype.py", "p9b_prototype_dependency")
    first = prototype.scene(0, 0)
    second = prototype.scene(0, 1)
    a = prototype.assignment_intermediate(first, "area_rank")
    b = prototype.assignment_intermediate(second, "area_rank")
    assert a != b
    correct = prototype.transform(first, "area_rank")
    wrong = prototype.transform(first, "area_rank", rank_order="descending")
    assert correct != wrong


def test_named_rivals_execute_and_no_query_only_survivor_remains():
    adapter = _load(PARAM / "adapter.py", "p9b_adapter_rivals")
    rivals = adapter.rival_programs()
    assert {"area_descending", "source_order", "color_order"} <= set(rivals)
    with RacketBridge() as bridge:
        for basis in ("holes", "area_rank"):
            episode = adapter.generate(29, {"assignment_basis": basis}, 2, 4)
            chosen = adapter.program({"assignment_basis": basis})
            for name, rival in rivals.items():
                demo_outputs = [_apply(bridge, rival, pair["input"])
                                for pair in episode["train"]]
                query_outputs = [_apply(bridge, rival, pair["input"])
                                 for pair in episode["test"]]
                demo_agree = all(out == pair["output"]
                                 for out, pair in zip(demo_outputs, episode["train"]))
                query_agree = all(out == pair["output"]
                                  for out, pair in zip(query_outputs, episode["test"]))
                assert not (demo_agree and not query_agree), (basis, name)
            assert all(_apply(bridge, chosen, pair["input"]) == pair["output"]
                       for pair in (*episode["train"], *episode["test"]))
