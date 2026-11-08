"""Behavioral checks for the proposed, nonproduction rectangle parameter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "42a152269589"


@pytest.fixture(scope="module")
def prototype():
    _, selected_source, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    path = selected_source.parent / "workspace" / "parametric" / "prototype.py"
    if not path.is_file():
        # The portable manifest places workspace sources at their library path.
        path = find_root(__file__) / "generators" / TASK_ID / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("rectangle_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def common_witness():
    grid = [[0] * 10 for _ in range(10)]
    for r in (0, 1):
        for c in (0, 1, 2):
            grid[r][c] = 1
    for c in (0, 1, 2):
        grid[4][c] = 2
    for r in (6, 7, 8):
        grid[r][7] = 3
    return grid


@pytest.mark.parametrize("rows,expected", [
    (3, [[1, 1, 1, 3], [1, 1, 1, 3], [2, 2, 2, 3]]),
    (2, [[1, 1, 1, 2, 2, 2], [1, 1, 1, 3, 3, 3]]),
])
def test_common_lawful_input_changes_packing_geometry(prototype, rows, expected):
    assert prototype.pack(common_witness(), rows) == expected


def test_default_rule_preserves_all_canonical_outputs(prototype):
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert prototype.pack(pair["input"], 3) == pair["output"]
    assert prototype.render_rule(3) == prototype.canonical_rule()


@pytest.mark.parametrize("bad", [True, 2.0, "2", 0, 4])
def test_parameter_values_are_bounded_integers(prototype, bad):
    with pytest.raises((TypeError, ValueError)):
        prototype.pack(common_witness(), bad)


@pytest.mark.parametrize("rows", [2, 3])
def test_complete_episode_has_fixed_parameter_and_three_solver_depths(prototype, rows):
    episode = prototype.generate_episode(17, target_rows=rows)
    assert episode == prototype.generate_episode(17, target_rows=rows)
    assert episode["parameters"] == {"target_rows": rows}
    assert [prototype.solver_depth(p["input"], rows) for p in episode["train"]] == [0, 1, 2]
    for pair in episode["train"] + episode["test"]:
        assert len(pair["output"]) == rows
        assert all(len(row) == 12 // rows for row in pair["output"])
        assert all(cell != 0 for row in pair["output"] for cell in row)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in json.dumps(public)


def test_seed_selects_rule_once_for_whole_episode(prototype):
    episode = prototype.generate_episode(4)
    assert episode == prototype.generate_episode(4)
    rows = episode["parameters"]["target_rows"]
    assert rows in (2, 3)
    assert all(len(pair["output"]) == rows for pair in episode["train"] + episode["test"])


def test_emitted_racket_checks_both_settings_on_witness_and_episodes(prototype):
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=20.0) as bridge:
        for rows in (2, 3):
            bridge.eval_text(f"(define parameter_rule {prototype.callable_rule(rows)})")
            episode = prototype.generate_episode(17, target_rows=rows)
            pairs = [{"input": common_witness(), "output": prototype.pack(common_witness(), rows)}]
            pairs += episode["train"] + episode["test"]
            for pair in pairs:
                bridge.define_grid("parameter_input", pair["input"])
                assert bridge.eval_text("(parameter_rule parameter_input)") == pair["output"]
