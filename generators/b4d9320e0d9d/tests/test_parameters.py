"""Focused tests for the native cascading-completion parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "b4d9320e0d9d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ROUNDS = ("one_pass", "two_pass")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _modules():
    assert (HOME / "adapter.py").is_file(), "native parametric adapter is missing"
    assert (HOME / "prototype.py").is_file(), "parametric prototype is missing"
    return (
        _load("b4_cascade_prototype_tests", HOME / "prototype.py"),
        _load("b4_cascade_adapter_tests", HOME / "adapter.py"),
    )


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_native_parametric_adapter_exists():
    _modules()


def test_contract_and_exact_canonical_default():
    prototype, adapter = _modules()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"completion_rounds": list(ROUNDS)},
        "default": {"completion_rounds": "one_pass"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/two_pass.rkt",
        ],
    }
    assert tuple(prototype.COMPLETION_ROUNDS) == ROUNDS
    assert adapter.program({"completion_rounds": "one_pass"}) == _canonical_program()
    assert prototype.program_for("one_pass") == _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 211])
def test_inputs_are_matched_and_first_demo_distinguishes_settings(seed):
    prototype, adapter = _modules()
    episodes = {
        mode: adapter.generate(seed, {"completion_rounds": mode}, demos=2, queries=4)
        for mode in ROUNDS
    }
    baseline = _inputs(episodes["one_pass"])
    assert _inputs(episodes["two_pass"]) == baseline
    assert len({json.dumps(grid, separators=(",", ":")) for grid in baseline}) == 6
    assert episodes["one_pass"]["train"][0]["output"] != episodes["two_pass"]["train"][0]["output"]
    for mode, episode in episodes.items():
        assert episode["program_solution"] == adapter.program({"completion_rounds": mode})
        assert all(
            pair["output"] == prototype.apply_rounds(pair["input"], mode)
            for pair in episode["train"] + episode["test"]
        )


@pytest.mark.parametrize("mode", ROUNDS)
@pytest.mark.parametrize("seed", [0, 17, 211])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_two_to_six_demonstrations_identify_setting(seed, demos, mode):
    prototype, adapter = _modules()
    episode = adapter.generate(seed, {"completion_rounds": mode}, demos=demos, queries=4)
    survivors = [
        candidate
        for candidate in ROUNDS
        if all(
            prototype.apply_rounds(pair["input"], candidate) == pair["output"]
            for pair in episode["train"]
        )
    ]
    assert survivors == [mode]
    certificate = prototype.teaching_certificate(episode, mode)
    assert certificate["declared_setting_survivors"] == [mode]
    assert certificate["query_changing_named_survivors"] == []


@pytest.mark.parametrize("mode", ROUNDS)
def test_counts_are_independent_prefix_stable_and_copy_isolated(mode):
    _, adapter = _modules()
    full = adapter.generate(431, {"completion_rounds": mode}, demos=6, queries=4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(431, {"completion_rounds": mode}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    first = adapter.generate(431, {"completion_rounds": mode}, demos=2, queries=1)
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(431, {"completion_rounds": mode}, demos=2, queries=1)["train"][0]["input"][0][0] != 9


def test_public_turn_reveals_exactly_one_query_without_private_fields():
    prototype, adapter = _modules()
    episode = adapter.generate(9, {"completion_rounds": "two_pass"}, demos=3, queries=4)
    for index in range(4):
        public = adapter.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": episode["test"][index]["input"]}]
        serialized = json.dumps(public, sort_keys=True)
        assert "completion_rounds" not in serialized
        assert "program_solution" not in serialized
    one = adapter.generate(9, {"completion_rounds": "two_pass"}, demos=3, queries=1)
    assert prototype.public_turn(one, 0) == adapter.public_turn(episode, 0)


def test_30x30_query_has_distributed_cascades_and_substantive_content():
    prototype, adapter = _modules()
    episode = adapter.generate(20261025, {"completion_rounds": "two_pass"}, demos=3, queries=4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = prototype.analyse_grid(grid)
    assert facts["nonzero_cells"] >= 95
    assert facts["cascade_witnesses"] >= 8
    assert facts["occupied_boundaries"] >= 3
    assert len(facts["colors"]) >= 6
    assert prototype.apply_rounds(grid, "one_pass") != prototype.apply_rounds(grid, "two_pass")


def test_source_bound_dependency_trace_changes_when_step_b_is_skipped():
    prototype, adapter = _modules()
    grid = adapter.generate(1701, {"completion_rounds": "two_pass"}, demos=2, queries=4)["test"][0]["input"]
    trace = prototype.dependency_trace(grid)
    assert trace["step_a"] == "complete every eligible original 2x2 window once"
    assert trace["intermediate"] == prototype.apply_pass(grid)
    assert trace["step_b_output"] == prototype.apply_pass(trace["intermediate"])
    assert trace["step_b_output"] != trace["skip_step_b_output"]
    assert trace["changed_cells_in_step_b"] > 0


@pytest.mark.parametrize("seed", range(16))
@pytest.mark.parametrize("mode", ROUNDS)
def test_two_demo_seed_sweep_refutes_every_named_shortcut(seed, mode):
    prototype, adapter = _modules()
    episode = adapter.generate(seed, {"completion_rounds": mode}, demos=2, queries=4)
    for name, rival in prototype.audit_rivals(mode).items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), (seed, mode, name)


@pytest.mark.parametrize("mode", ROUNDS)
def test_named_shortcuts_are_refuted_by_visible_demos_and_queries(mode):
    prototype, adapter = _modules()
    episode = adapter.generate(33, {"completion_rounds": mode}, demos=2, queries=4)
    for name, rival in prototype.audit_rivals(mode).items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), (mode, name, "demos")
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), (mode, name, "queries")


@pytest.mark.parametrize("settings", [None, {}, {"completion_rounds": True}, {"completion_rounds": "three_pass"}, {"completion_rounds": "one_pass", "extra": 1}])
def test_invalid_settings_reject(settings):
    _, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 3, True), (0, 3, 0), (0, 3, 5)])
def test_invalid_seed_and_count_controls_reject(seed, demos, queries):
    _, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.generate(seed, {"completion_rounds": "one_pass"}, demos=demos, queries=queries)


def test_racket_programs_match_python_on_dependency_witness():
    prototype, adapter = _modules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = prototype.episode_inputs(71)["train"][0]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for mode in ROUNDS:
            actual = bridge.eval_text(f"({wrap_rule(adapter.program({'completion_rounds': mode}))} {literal})")
            assert actual == prototype.apply_rounds(grid, mode)
