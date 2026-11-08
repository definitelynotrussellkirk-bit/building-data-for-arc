from __future__ import annotations

import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.d8111f3f714d.generator"
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                rows.append((line_number, row))
    return rows


def _canonical_pairs():
    pairs = []
    for line_number, row in _canonical_rows():
        for split in ("train", "test"):
            values = row[split]
            if isinstance(values, dict):
                values = [values]
            for index, pair in enumerate(values):
                pairs.append((line_number, split, index, pair))
    return pairs


def _valid_vertical_scene():
    grid = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((1, 5), (10, 5), (3, 2), (7, 8)):
        grid[row][col] = 2
    assert GEN.self_check(grid) == []
    return grid


def test_rule_hash_and_all_canonical_occurrences_are_exact():
    assert GEN.RULE_HASH == "2a9d26bd68ef"
    rows = _canonical_rows()
    pairs = _canonical_pairs()
    assert [(line, row["source"]) for line, row in rows] == [
        (749, "training"),
        (1321, "augmented"),
    ]
    assert len(pairs) == 10
    assert len({json.dumps(pair, sort_keys=True) for *_meta, pair in pairs}) == 5
    for _line, _split, _index, pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_selected_task_local_racket_sources_match_canonical_exactly():
    canonical = _canonical_rows()[0][1]["program_solution"]
    paths = (
        ROOT / "data/base/solutions/training/bf89d739__d8111f3f714d.json",
        ROOT / "data/base/solutions/augmented/bf89d739__e3a5acde9846.json",
    )
    for path in paths:
        data = json.loads(path.read_text())
        assert data["racket_target"]["target_code"] == canonical
        assert data["racket_target"]["raw_code"] != canonical


def test_exact_override_boundaries_and_regression_witness():
    for index, (height, width, orientation, branches) in enumerate(
        product((10, 24), (10, 24), ("v", "h"), (1, 5))
    ):
        requested = {
            "grid_h": height,
            "grid_w": width,
            "orientation": orientation,
            "n_branches": branches,
        }
        grid = GEN.generate(100 + index, 200 + index, difficulty="easy", **requested)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested
        assert GEN.rule_mirror(grid) != grid

    witness = GEN.generate(
        0,
        3,
        difficulty="easy",
        grid_h=24,
        grid_w=24,
        orientation="v",
        n_branches=5,
    )
    assert GEN.observe_overrides(witness) == {
        "grid_h": 24,
        "grid_w": 24,
        "orientation": "v",
        "n_branches": 5,
    }


def test_sequential_schedule_covers_orientation_and_band_branch_ranges():
    expected = {
        "easy": [1, 2, 1, 2, 1, 2],
        "medium": [2, 3, 4, 2, 3, 4],
        "hard": [3, 4, 5, 3, 4, 5],
    }
    for band, branch_counts in expected.items():
        observed = [
            GEN.observe_overrides(GEN.generate(71, sample_index, difficulty=band))
            for sample_index in range(6)
        ]
        assert [item["orientation"] for item in observed] == [
            "v",
            "h",
            "v",
            "h",
            "v",
            "h",
        ]
        assert [item["n_branches"] for item in observed] == branch_counts


def test_self_check_rejects_targeted_structural_impostors():
    valid = _valid_vertical_scene()

    multiple_sharing_pairs = [row[:] for row in valid]
    multiple_sharing_pairs[3][8] = 2

    branch_outside_span = [row[:] for row in valid]
    branch_outside_span[3][2] = 0
    branch_outside_span[0][2] = 2

    invisible_adjacent_connector = [row[:] for row in valid]
    invisible_adjacent_connector[3][2] = 0
    invisible_adjacent_connector[3][4] = 2

    one_sided_multi_branch = [row[:] for row in valid]
    one_sided_multi_branch[7][8] = 0
    one_sided_multi_branch[7][1] = 2

    wrong_palette = [row[:] for row in valid]
    wrong_palette[3][2] = 4

    impostors = (
        multiple_sharing_pairs,
        branch_outside_span,
        invisible_adjacent_connector,
        one_sided_multi_branch,
        wrong_palette,
    )
    for impostor in impostors:
        assert GEN.self_check(impostor), impostor
        with pytest.raises(ValueError):
            GEN.rule_mirror(impostor)


def test_replay_returns_fresh_objects_without_touching_global_rng():
    random.seed(20260724)
    state_before = random.getstate()
    first = GEN.generate(313, 919, difficulty="hard")
    state_after = random.getstate()
    second = GEN.generate(313, 919, difficulty="hard")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_invalid_calls_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 1, made_up_axis=4)
    with pytest.raises(ValueError, match="orientation"):
        GEN.generate(1, 1, orientation="diagonal")
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 1, grid_h=True)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 1, n_branches=6)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 1, difficulty="impossible")
