from __future__ import annotations

import json
import importlib.util
import random
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("reviewed_c286f4a2923f", HOME / "generator.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _canonical_row():
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical task missing")


def test_rule_hash_pin_matches_assignment():
    assert gen.RULE_HASH == "496d98097154"


def test_all_canonical_inputs_pass_structural_self_check():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []


def test_boundary_overrides_are_exact_and_observable():
    cases = [
        dict(
            grid_h=8,
            grid_w=13,
            source_shape="ring_3x3",
            target_extra_h=2,
            target_extra_w=2,
            source_side="left",
        ),
        dict(
            grid_h=16,
            grid_w=20,
            source_shape="zigzag_3x3",
            target_extra_h=0,
            target_extra_w=0,
            source_side="right",
        ),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(41 + index, 7, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_sample_schedule_rebuts_count_bbox_and_fixed_side_shortcuts():
    grids = [gen.generate(77, sample_index, difficulty="medium") for sample_index in range(4)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert observed[0]["source_shape"] == "t_2x3"
    assert observed[1]["source_shape"] == "l_3x2"
    assert sum(value == 2 for row in grids[0] for value in row) == 4
    assert sum(value == 2 for row in grids[1] for value in row) == 4
    assert observed[2]["source_shape"] == "ring_3x3"
    assert {item["source_side"] for item in observed} == {"left", "right"}
    assert any(item["target_extra_h"] or item["target_extra_w"] for item in observed[:3])


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(9, 3, difficulty="easy")
    after = random.getstate()
    second = gen.generate(9, 3, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[0][0] = 9
    assert second[0][0] != 9


def test_unknown_and_out_of_range_overrides_reject_loudly():
    try:
        gen.generate(1, 0, texture="warm")
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")

    try:
        gen.generate(1, 0, grid_h=7)
    except ValueError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("out-of-range override was silently accepted")


def test_python_rule_mirror_matches_all_canonical_outputs_and_shortcuts_fit_them():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    for pair in pairs:
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert {
        "center_mask_in_target",
        "bottom_right_mask_in_target",
        "mirror_source_toward_target",
    } <= set(gen.CANONICAL_SHORTCUTS)
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_every_three_sample_window_identifies_the_rule_and_refutes_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(18):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(404, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                404, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_semantic_witnesses_fire_in_every_band_and_refute_claimed_rivals():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(808, index, difficulty=difficulty) for index in range(18)]
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            matches = [grid for grid in grids if witness(grid)]
            assert matches, (difficulty, witness_name)
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                rival = gen.SEMANTIC_RIVALS[rival_name]
                assert all(rival(grid) != gen.rule_mirror(grid) for grid in matches), (
                    difficulty,
                    witness_name,
                    rival_name,
                )


def test_canonical_grid_profiles_are_interleaved_in_every_difficulty_band():
    expected = {(8, 13), (9, 13), (9, 14)}
    for difficulty in ("easy", "medium", "hard"):
        anchored = {
            (len(grid), len(grid[0]))
            for sample_index in range(9)
            if sample_index % 3 == 0
            for grid in [gen.generate(909, sample_index, difficulty=difficulty)]
        }
        assert anchored == expected


def test_padded_target_is_an_exact_counterexample_to_center_alignment():
    grid = gen.generate(
        123,
        2,
        difficulty="medium",
        grid_h=8,
        grid_w=13,
        source_shape="ring_3x3",
        target_extra_h=2,
        target_extra_w=2,
        source_side="left",
    )
    intended = gen.rule_mirror(grid)
    rival = gen.CANONICAL_SHORTCUTS["center_mask_in_target"](grid)
    assert intended != rival
