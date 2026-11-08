"""Focused tests for the separate peak-repetition prototype, not approval."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "67e9e17efb62"


def prototype():
    path = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    assert path.is_file(), "The task-local peak-repetition prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("peak_repetition_prototype_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def fixture_grid():
    grid = [[0] * 8 for _ in range(5)]
    grid[0][:4] = [7] * 4
    return grid


def nonzero_run_lengths(grid):
    flat = [value for row in grid for value in row]
    lengths = []
    current = 0
    for value in flat:
        if value:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def canonical_sources():
    sources = set()
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    return sources


def test_default_is_exact_canonical_program_and_executes_canonical_labels():
    mod = prototype()
    assert canonical_sources() == {mod.render_program(1, root=ROOT)}
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            actual = mod.execute(bridge, mod.render_program(1, root=ROOT), pair["input"])
            assert actual == pair["output"]


def test_second_setting_repeats_only_the_peak_run():
    mod = prototype()
    grid = fixture_grid()
    with RacketBridge() as bridge:
        once = mod.execute(bridge, mod.render_program(1, root=ROOT), grid)
        twice = mod.execute(bridge, mod.render_program(2, root=ROOT), grid)
    assert nonzero_run_lengths(once) == [1, 2, 3, 4, 3, 2, 1]
    assert nonzero_run_lengths(twice) == [1, 2, 3, 4, 4, 3, 2, 1]
    assert once != twice


def test_complete_episodes_fix_one_setting_and_refute_the_other():
    mod = prototype()
    seeds = mod.example_seeds()
    assert {mod.choose_peak_repetitions(seed) for seed in seeds} == {1, 2}
    with RacketBridge() as bridge:
        for seed in seeds:
            setting = mod.choose_peak_repetitions(seed)
            assert mod.episode_inputs(seed) == mod.episode_inputs(seed)
            episode = mod.generate_episode(seed, bridge=bridge, root=ROOT)
            assert episode["parameters"] == {"peak_repetitions": setting}
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            rival = episode["parameter_rivals"]
            assert rival["status"] == "refuted_on_demonstrations"
            assert rival["refuting_demonstrations"]
            assert rival["query_disagreements"] == [0]
            assert all(not mod.input_issues(pair["input"]) for pair in episode["train"] + episode["test"])

            public = mod.public_episode(episode)
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            serialized = json.dumps(public, sort_keys=True)
            assert "peak_repetitions" not in serialized
            assert "program" not in serialized


@pytest.mark.parametrize("value", [-1, 0, 3, True, 1.0, "1", None])
def test_parameter_rejects_unsupported_and_coerced_values(value):
    mod = prototype()
    with pytest.raises(ValueError):
        mod.render_program(value, root=ROOT)
