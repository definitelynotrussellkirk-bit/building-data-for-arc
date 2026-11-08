"""Focused regressions for generator 907bb29fbac5."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

GEN = importlib.import_module("puzzle_generators.per_puzzle.907bb29fbac5.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        for split in ("train", "test"):
            for index, pair in enumerate(row[split]):
                yield split, index, pair["input"], pair["output"]


def _tiles(output):
    return [
        [
            [row[col * 5 : col * 5 + 4] for row in output[r * 5 : r * 5 + 4]]
            for col in range(3)
        ]
        for r in range(3)
    ]


def test_metadata_and_all_canonical_pairs():
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "edb7f73552a9"
    signatures = []
    for split, index, grid, expected in _canonical_pairs():
        assert GEN.self_check(grid) == [], (split, index, GEN.self_check(grid))
        assert GEN.rule_mirror(grid) == expected
        signatures.append(GEN.canonical_profile_signature(grid))
    assert signatures == ["train_0", "train_1", "train_2", "train_3", "test_0"]


def test_canonical_disconnected_and_subset_panels_remain_accepted():
    pairs = list(_canonical_pairs())
    disconnected = pairs[1][2]
    subset_pair = pairs[2][2]
    assert GEN.canonical_profile_signature(disconnected) == "train_1"
    assert GEN.canonical_profile_signature(subset_pair) == "train_2"
    assert GEN.self_check(disconnected) == []
    assert GEN.self_check(subset_pair) == []


def test_exact_axes_observable_at_every_boundary_and_band():
    for band in ("easy", "medium", "hard"):
        for count in (4, 7):
            for profile in ("balanced", "shared_core"):
                grid = GEN.generate(
                    177,
                    23,
                    difficulty=band,
                    grid_h=4,
                    grid_w=14,
                    panel_cell_count=count,
                    overlap_profile=profile,
                )
                assert GEN.observe_overrides(grid) == {
                    "grid_h": 4,
                    "grid_w": 14,
                    "panel_cell_count": count,
                    "overlap_profile": profile,
                }
                assert GEN.self_check(grid) == []


def test_generated_pairs_expose_complete_xor_truth_table():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        inputs = set()
        outputs = set()
        profiles = set()
        counts = set()
        for offset in range(200):
            grid = GEN.generate(20_000 + 10_000 * band_index + offset, offset * 17 + 3,
                                difficulty=band)
            assert GEN.self_check(grid) == []
            facts = GEN.semantic_observables(grid)
            counts.add(facts["panel_counts"][0])
            profiles.add(facts["overlap_profile"])
            for truth in facts["pair_truth_counts"].values():
                assert all(truth[name] > 0 for name in ("both", "left_only", "right_only", "neither"))
            output = GEN.rule_mirror(grid)
            inputs.add(json.dumps(grid, separators=(",", ":")))
            outputs.add(json.dumps(output, separators=(",", ":")))
        assert profiles == {"balanced", "shared_core"}
        assert len(inputs) >= 180
        assert len(outputs) >= 180
        if band == "easy":
            assert counts == {4}
        elif band == "medium":
            assert counts == {5, 6}
        else:
            assert counts == {7}


def test_output_relation_matrix_grammar():
    for profile in ("balanced", "shared_core"):
        grid = GEN.generate(8128, 77, difficulty="hard", overlap_profile=profile)
        output = GEN.rule_mirror(grid)
        assert len(output) == 14 and all(len(row) == 14 for row in output)
        assert all(output[row][gap] == 0 for row in range(14) for gap in (4, 9))
        assert all(output[gap][col] == 0 for gap in (4, 9) for col in range(14))
        tiles = _tiles(output)
        blank = [[0] * 4 for _ in range(4)]
        assert tiles[0][0] == tiles[1][1] == tiles[2][2] == blank
        assert tiles[0][1] == tiles[1][0]
        assert tiles[0][2] == tiles[2][0]
        assert tiles[1][2] == tiles[2][1]
        assert tiles[0][1] != blank and tiles[0][2] != blank and tiles[1][2] != blank


def test_targeted_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_determinism_freshness_and_global_rng_state():
    random.seed(918273)
    before = random.getstate()
    first = GEN.generate(1234, 5678, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(1234, 5678, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_invalid_overrides_reject_loudly():
    for kwargs in (
        {"grid_h": 3},
        {"grid_w": 13},
        {"panel_cell_count": 3},
        {"panel_cell_count": 8},
        {"overlap_profile": "unknown"},
        {"bogus": 1},
    ):
        try:
            GEN.generate(1, 2, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"override should reject loudly: {kwargs}")
    try:
        GEN.generate(1, 2, difficulty="extreme")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown difficulty should reject loudly")
