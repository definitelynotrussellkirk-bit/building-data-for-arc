"""Focused tests for the native motif-anchor parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "87aae821984d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ANCHORS = ("bottom_right", "top_left")


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
        _load("anchor_repeat_prototype_tests", HOME / "prototype.py"),
        _load("anchor_repeat_adapter_tests", HOME / "adapter.py"),
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
        "parameters": {"tile_anchor": list(ANCHORS)},
        "default": {"tile_anchor": "bottom_right"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/top_left.rkt",
        ],
    }
    assert tuple(prototype.TILE_ANCHORS) == ANCHORS
    assert adapter.program({"tile_anchor": "bottom_right"}) == _canonical_program()
    assert prototype.program_for("bottom_right") == _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 211])
def test_inputs_are_matched_and_first_two_demos_distinguish_settings(seed):
    prototype, adapter = _modules()
    episodes = {
        anchor: adapter.generate(seed, {"tile_anchor": anchor}, demos=2, queries=4)
        for anchor in ANCHORS
    }
    baseline = _inputs(episodes["bottom_right"])
    assert _inputs(episodes["top_left"]) == baseline
    assert len({json.dumps(grid, separators=(",", ":")) for grid in baseline}) == 6
    for index in (0, 1):
        assert episodes["bottom_right"]["train"][index]["output"] != episodes["top_left"]["train"][index]["output"]
    for anchor, episode in episodes.items():
        assert all(
            pair["output"] == prototype.solve(pair["input"], anchor)
            for pair in episode["train"] + episode["test"]
        )


@pytest.mark.parametrize("anchor", ANCHORS)
@pytest.mark.parametrize("seed", [0, 17, 211])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_two_to_six_demonstrations_identify_setting(seed, demos, anchor):
    prototype, adapter = _modules()
    episode = adapter.generate(seed, {"tile_anchor": anchor}, demos=demos, queries=4)
    survivors = [
        candidate
        for candidate in ANCHORS
        if all(prototype.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    assert survivors == [anchor]
    certificate = prototype.teaching_certificate(episode, anchor)
    assert certificate["declared_setting_survivors"] == [anchor]
    assert certificate["query_changing_named_survivors"] == []


@pytest.mark.parametrize("anchor", ANCHORS)
def test_counts_are_independent_prefix_stable_and_public_turn_is_masked(anchor):
    prototype, adapter = _modules()
    full = adapter.generate(431, {"tile_anchor": anchor}, demos=6, queries=4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = adapter.generate(431, {"tile_anchor": anchor}, demos=demos, queries=queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]
    for index in range(4):
        public = adapter.public_turn(full, index)
        assert public == {"train": full["train"], "test": [{"input": full["test"][index]["input"]}]}
        assert "tile_anchor" not in json.dumps(public, sort_keys=True)
        assert "program_solution" not in json.dumps(public, sort_keys=True)
    one = adapter.generate(431, {"tile_anchor": anchor}, demos=6, queries=1)
    assert prototype.public_turn(one, 0) == adapter.public_turn(full, 0)


def test_30x30_query_has_exact_30_wide_output_and_real_distractor_density():
    prototype, adapter = _modules()
    episode = adapter.generate(20261025, {"tile_anchor": "top_left"}, demos=3, queries=4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = prototype.analyse(grid)
    assert facts["counter_cells"] == 10
    assert facts["motif_bbox"] in ([2, 2], [2, 3], [3, 2])
    assert facts["nonzero_cells"] >= 250
    assert facts["distractor_cells"] >= 220
    assert facts["occupied_boundaries"] == 4
    assert (len(pair["output"]), len(pair["output"][0])) == (3, 30)
    assert sum(value == 8 for row in pair["output"] for value in row) >= 40


def test_dependency_intermediate_is_consumed_by_count_based_repetition():
    prototype, adapter = _modules()
    grid = adapter.generate(1701, {"tile_anchor": "bottom_right"}, demos=2, queries=4)["test"][0]["input"]
    trace = prototype.dependency_trace(grid, "bottom_right")
    assert trace["step_a"] == "extract the color-8 motif into an anchor-normalized 3x3 tile"
    assert trace["intermediate_tile"] == prototype.extract_tile(grid, "bottom_right")
    assert trace["step_b_output"] == prototype.repeat_tile(trace["intermediate_tile"], trace["counter_cells"])
    wrong = prototype.extract_tile(grid, "top_left")
    assert wrong != trace["intermediate_tile"]
    assert prototype.repeat_tile(wrong, trace["counter_cells"]) != trace["step_b_output"]


@pytest.mark.parametrize("anchor", ANCHORS)
def test_named_shortcuts_are_refuted_by_visible_demos_and_queries(anchor):
    prototype, adapter = _modules()
    episode = adapter.generate(33, {"tile_anchor": anchor}, demos=2, queries=4)
    for name, rival in prototype.audit_rivals(anchor).items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), (anchor, name, "demos")
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), (anchor, name, "queries")


@pytest.mark.parametrize("settings", [None, {}, {"tile_anchor": True}, {"tile_anchor": "center"}, {"tile_anchor": "bottom_right", "extra": 1}])
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
        adapter.generate(seed, {"tile_anchor": "bottom_right"}, demos=demos, queries=queries)


def test_racket_programs_match_python_on_anchor_witness():
    prototype, adapter = _modules()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    grid = prototype.episode_inputs(71)["train"][0]
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for anchor in ANCHORS:
            actual = bridge.eval_text(f"({wrap_rule(adapter.program({'tile_anchor': anchor}))} {literal})")
            assert actual == prototype.solve(grid, anchor)
