"""Focused regression coverage for bbox-outline task 6c0ee2a97246."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

TASK_ID = "6c0ee2a97246"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [
                    pair
                    for split in ("train", "test")
                    for pair in row[split]
                ]
    raise AssertionError("canonical task row not found")


def _paint(grid, cells, color):
    for row, col in cells:
        grid[row][col] = color


def test_rule_hash_summary_and_single_self_check_are_synchronized():
    assert GEN.RULE_HASH == "ae8cc57061a0"
    text = ((GEN.__doc__ or "") + " " + GEN.SUMMARY).lower()
    assert "bounding box" in text or "bbox" in text
    assert "touch-degree" not in text


def test_all_canonical_train_and_test_pairs_are_accepted_and_solved():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_default_schedule_exposes_add_delete_small_large_and_palette_branches():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(500 + index, index, difficulty=band) for index in range(4)]
        signatures = [GEN.semantic_signature(grid) for grid in grids]
        assert all(item["added_border_cells"] > 0 for item in signatures)
        assert any(item["deleted_interior_cells"] > 0 for item in signatures)
        assert any(
            any(sig[1] >= 3 and sig[2] >= 3 for sig in item["object_signatures"])
            for item in signatures
        )
        assert any(item["strict_canonical_like"] for item in signatures)
        assert any(item["distinct_nonzero_colors"] < item["component_count"] for item in signatures)


def test_four_consecutive_demos_identify_every_query_residue():
    for start in range(4):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(800 + sample_index, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_override_boundaries_are_exact_and_observable_in_every_band():
    cases = (
        {"grid_h": 8},
        {"grid_h": 14},
        {"grid_w": 9},
        {"grid_w": 18},
        {"n_components": 3},
        {"n_components": 5},
        {"palette_mode": "distinct"},
        {"palette_mode": "repeated"},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(1200 + index, 9 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            if "grid_h" in case:
                assert observed["grid_h"] == case["grid_h"]
            if "grid_w" in case:
                assert observed["grid_w"] == case["grid_w"]
            if "n_components" in case:
                assert observed["n_components"] == case["n_components"]
            assert GEN.self_check(grid, meta={"overrides": case}) == []


def test_deterministic_fresh_returns_input_purity_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    intervening = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert intervening != first
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_self_check_rejects_four_structural_impostor_classes():
    # 1. A one-dimensional object cannot express a 2-D bbox outline.
    line = [[0] * 9 for _ in range(8)]
    _paint(line, ((1, 1), (1, 2), (1, 3)), 1)
    _paint(line, ((4, 1), (4, 2), (5, 2)), 2)
    _paint(line, ((1, 6), (1, 7), (2, 7)), 3)
    assert any("both dimensions" in error for error in GEN.self_check(line))

    # 2. An already-complete frame hides the transformation.
    already_frame = [[0] * 9 for _ in range(8)]
    _paint(
        already_frame,
        ((1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)),
        1,
    )
    _paint(already_frame, ((5, 1), (5, 2), (6, 2)), 2)
    _paint(already_frame, ((5, 6), (5, 7), (6, 7)), 3)
    assert any("already its bbox perimeter" in error for error in GEN.self_check(already_frame))

    # 3. A solid rectangle is a no-op and admits the fill-box shortcut.
    solid = [[0] * 9 for _ in range(8)]
    _paint(solid, ((1, 1), (1, 2), (2, 1), (2, 2)), 1)
    _paint(solid, ((5, 1), (5, 2), (6, 2)), 2)
    _paint(solid, ((5, 6), (5, 7), (6, 7)), 3)
    assert GEN.self_check(solid)

    # 4. Overlapping object bboxes make paint order answer-bearing.
    overlap = [[0] * 9 for _ in range(8)]
    _paint(overlap, ((1, 1), (1, 2), (2, 2), (2, 3), (3, 3)), 1)
    _paint(overlap, ((2, 5), (2, 4), (3, 4), (4, 4), (4, 3)), 2)
    _paint(overlap, ((6, 6), (6, 7), (7, 7)), 3)
    assert any("overlapping bbox" in error for error in GEN.self_check(overlap))


def test_negative_recombination_is_rejected_but_oracle_mirror_can_execute():
    grid = GEN.generate(222, 0, difficulty="easy")
    analysis = GEN._analyze(grid)
    component = analysis["components"][0]
    mutated = copy.deepcopy(grid)
    for row, col in component["cells"]:
        mutated[row][col] = 0
    r0, c0, r1, c1 = component["bbox"]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            mutated[row][col] = component["color"]

    assert GEN.self_check(mutated)
    output = GEN.rule_mirror(mutated)
    assert len(output) == len(mutated)
    assert len(output[0]) == len(mutated[0])
