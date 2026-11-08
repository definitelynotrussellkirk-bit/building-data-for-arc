"""Regression tests for the current 537b409b6744 review."""
from __future__ import annotations

from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "537b409b6744"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "sample_index": 0},
        {"seed": 1.0, "sample_index": 0},
        {"seed": "1", "sample_index": 0},
        {"seed": 1, "sample_index": True},
        {"seed": 1, "sample_index": 1.0},
        {"seed": 1, "sample_index": "1"},
        {"seed": 1, "sample_index": -1},
        {"seed": 1, "sample_index": 0, "difficulty": True},
        {"seed": 1, "sample_index": 0, "difficulty": 0},
        {"seed": 1, "sample_index": 0, "difficulty": 1.0},
        {"seed": 1, "sample_index": 0, "difficulty": "__invalid_difficulty__"},
    ],
)
def test_generate_rejects_invalid_call_scalars(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(**kwargs)


def test_smallest_mover_is_an_exact_canonical_shortcut():
    rival = gen.CANONICAL_SHORTCUTS["smallest_mover"]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert rival(pair["input"]) == pair["output"]


def test_generated_larger_near_mover_refutes_smallest_mover_shortcut():
    grid = gen.generate(
        1,
        17,
        grid_h=10,
        grid_w=10,
        direction="down",
        mover_span=2,
        mover_depth=2,
        wall_extra=2,
        wall_depth=3,
        gap=1,
        distractor_kind="solid",
    )
    rival = gen.CANONICAL_SHORTCUTS["smallest_mover"]
    assert gen._rule_output(grid) != rival(grid)
    assert gen.SEMANTIC_WITNESSES["smallest_mover"](grid) is True
    assert gen.WITNESS_RIVALS["smallest_mover"] == ["smallest_mover"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_each_four_pair_window_refutes_smallest_mover_under_every_rotation(difficulty):
    rival = gen.CANONICAL_SHORTCUTS["smallest_mover"]
    for start in range(8):
        grids = [
            gen.generate(1, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        refutes = [gen._rule_output(grid) != rival(grid) for grid in grids]
        for held_out in range(4):
            assert any(
                refutes[index] for index in range(4) if index != held_out
            ), (difficulty, start, held_out, refutes)


def test_reference_probe_independently_reproduces_smallest_mover_shortcut():
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("independent_reference_probe", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    rival = gen.CANONICAL_SHORTCUTS["smallest_mover"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert probe.smallest_candidate_output(pair["input"]) == pair["output"]
        assert probe.smallest_candidate_output(pair["input"]) == rival(pair["input"])


def test_retained_smallest_mover_counterexample_replays_exactly():
    import json

    path = (
        Path(__file__).resolve().parents[1]
        / "counterexamples"
        / "smallest-mover-shortcut.json"
    )
    record = json.loads(path.read_text())
    replay = gen.generate(
        record["replay"]["seed"],
        record["replay"]["sample_index"],
        **record["replay"]["overrides"],
    )
    assert replay == record["input"]
    assert gen._rule_output(replay) == record["intended_output"]
    assert gen.CANONICAL_SHORTCUTS["smallest_mover"](replay) == record[
        "shortcut_output"
    ]
    assert record["intended_output"] != record["shortcut_output"]
    assert record["racket_intended_matches_python"] is True
