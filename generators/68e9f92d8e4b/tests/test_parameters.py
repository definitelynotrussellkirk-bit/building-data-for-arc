"""Focused repair and native-family tests for 68e9f92d8e4b."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "68e9f92d8e4b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
SETTINGS = ({"fill_mode": "object_color"}, {"fill_mode": "orientation_legend"})


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_arc_68e9f92d8e4b_adapter_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _has_mixed_nonzero_component(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    while todo:
        start = min(todo)
        todo.remove(start)
        queue = deque([start])
        colors = {grid[start[0]][start[1]]}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in todo:
                    todo.remove(nxt)
                    queue.append(nxt)
                    colors.add(grid[nxt[0]][nxt[1]])
        if len(colors) > 1:
            return True
    return False


def _episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_repaired_validator_accepts_every_canonical_input():
    generator, _, _ = load_selected_generator(TASK, root=ROOT)
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    rejected = [
        (pair["split"], pair["pair_index"], generator.self_check(pair["input"]))
        for pair in pairs
        if generator.self_check(pair["input"])
    ]
    assert rejected == []


@pytest.mark.parametrize("difficulty", [None, "medium", "hard"])
def test_ordinary_generation_teaches_colored_objects_not_whole_nonzero_components(difficulty):
    generator, _, _ = load_selected_generator(TASK, root=ROOT)
    for sample_index in range(6):
        grid = generator.generate(37, sample_index, difficulty=difficulty)
        assert generator.self_check(grid, difficulty=difficulty) == []
        assert _has_mixed_nonzero_component(grid), "whole-component shortcut still fits ordinary draws"


def test_default_program_is_exact_selected_canonical_source():
    adapter = _load_adapter()
    assert adapter.program({"fill_mode": "object_color"}) == _canonical_program()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_distinctness_and_setting_identification(demos):
    adapter = _load_adapter()
    for seed in (0, 17):
        episodes = [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]
        assert _episode_inputs(episodes[0]) == _episode_inputs(episodes[1])
        for setting, episode in zip(SETTINGS, episodes, strict=True):
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(setting)
            keys = [json.dumps(grid, separators=(",", ":")) for grid in _episode_inputs(episode)]
            assert len(keys) == len(set(keys)) == demos + 4
            assert adapter.family.teaching_check(episode, setting["fill_mode"])["surviving_modes"] == [
                setting["fill_mode"]
            ]
        assert all(
            left["output"] != right["output"]
            for left, right in zip(episodes[0]["train"], episodes[1]["train"], strict=True)
        )


def test_orientation_intermediate_varies_and_four_queries_include_substantive_30x30():
    adapter = _load_adapter()
    episode = adapter.generate(29, {"fill_mode": "orientation_legend"}, 3, 4)
    indices = {
        index
        for pair in episode["train"] + episode["test"]
        for index in adapter.family.orientation_indices(pair["input"])
    }
    assert indices == {0, 1, 2, 3}
    large = episode["test"][-1]
    assert len(large["input"]) == 30 and all(len(row) == 30 for row in large["input"])
    assert sum(value != 0 for row in large["input"] for value in row) >= 70
    assert _has_mixed_nonzero_component(large["input"])
    assert large["input"] != large["output"]


def test_python_claims_match_protected_racket_for_every_setting():
    adapter = _load_adapter()
    from arcpuzzles.parametric_worker import _real_evaluator
    import arc_repl.racket_bridge as bridge_module

    runtime = Path(bridge_module.__file__).resolve().parents[1]
    evaluate, identity, bridge = _real_evaluator(runtime)
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        for setting in SETTINGS:
            episode = adapter.generate(11, setting, 2, 4)
            program = adapter.program(setting)
            for pair in episode["train"] + episode["test"]:
                assert evaluate(program, pair["input"]) == pair["output"]
    finally:
        bridge.close()


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"fill_mode": "object_color"}, 2, 4),
        (-1, {"fill_mode": "object_color"}, 2, 4),
        (0, {"fill_mode": "object_color"}, 1, 4),
        (0, {"fill_mode": "object_color"}, 7, 4),
        (0, {"fill_mode": "object_color"}, 2, 3),
        (0, {"fill_mode": "object_color"}, 2, 5),
        (0, {"fill_mode": "object_color"}, 2.0, 4),
        (0, {"fill_mode": "bogus"}, 2, 4),
        (0, {"fill_mode": "object_color", "extra": 1}, 2, 4),
    ],
)
def test_invalid_requests_fail_visibly(seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        _load_adapter().generate(seed, settings, demos, queries)


def test_bounded_self_audit_refutes_named_shortcuts():
    path = HOME / "audit.py"
    assert path.is_file(), "bounded self-audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_arc_68e9f92d8e4b_audit_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 1, 17, 29))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 8
    assert report["has_30x30"] is True
