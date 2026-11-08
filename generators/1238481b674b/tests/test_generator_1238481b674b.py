from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge, RacketBridgeError
from scripts.canonical_profile_gate import canonical_pairs
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "1238481b674b"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = ROOT / "data/base/solutions/training/1478ab18__1238481b674b.json"
GEN = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if f'"task_id": "{TASK_ID}"' in line]
    assert len(rows) == 1
    return rows[0]


def _pairs() -> list[dict]:
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in canonical_pairs(TASK_ID)
    ]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_metadata_and_rule_hash_pin_current_canonical_authority() -> None:
    canonical = _canonical_row()["program_solution"]
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == _normalized_hash(canonical)
    assert GEN.EXAMPLES_NEEDED == 4
    assert "exactly four gray" in GEN.SUMMARY.lower()


def test_canonical_inputs_are_accepted_and_have_the_required_distractor() -> None:
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        facts = GEN._analyze(pair["input"])
        assert len(facts["marks"]) == 4
        assert facts["distractor_variant"] == "near_missing"
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_rule_is_exact_input_pure_and_reentrant() -> None:
    canonical = _canonical_row()["program_solution"]
    pairs = _pairs()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(canonical, pair["input"]))
            assert actual == pair["output"] == GEN.rule_mirror(pair["input"])
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(canonical, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_regression_ordinary_draws_have_four_markers_and_preserved_distractor() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(7000 + sample_index, sample_index, difficulty=band)
            facts = GEN._analyze(grid)
            assert facts["errors"] == []
            assert len(facts["marks"]) == 4
            out = GEN.rule_mirror(grid)
            r, c = facts["distractor"]
            assert grid[r][c] == out[r][c] == 5


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    state = random.getstate()
    first = GEN.generate(991, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(991, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(991, 17, difficulty="hard") == second


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_axes_are_observable_and_constraints_reject_loudly(band: str) -> None:
    cases = (
        {
            "grid_h": 8,
            "grid_w": 8,
            "side_len": 3,
            "missing_corner": "top_left",
            "row_offset": 4,
            "col_offset": 4,
            "distractor_variant": "near_missing",
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "side_len": 10,
            "missing_corner": "bottom_right",
            "row_offset": 5,
            "col_offset": 5,
            "distractor_variant": "clockwise",
        },
        {
            "grid_h": 12,
            "grid_w": 13,
            "side_len": 6,
            "missing_corner": "bottom_left",
            "row_offset": 2,
            "col_offset": 6,
            "distractor_variant": "counterclockwise",
        },
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(8100 + index, 900 + index, difficulty=band, **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides

    # Every single-axis boundary can be reached when companion axes are free.
    assert GEN.observe_overrides(GEN.generate(1, 1, difficulty=band, row_offset=12))["row_offset"] == 12
    assert GEN.observe_overrides(GEN.generate(2, 2, difficulty=band, col_offset=12))["col_offset"] == 12
    assert GEN.observe_overrides(GEN.generate(3, 3, difficulty=band, side_len=10))["side_len"] == 10

    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 2, difficulty=band, grid_h=8, side_len=7, row_offset=2)
    with pytest.raises(ValueError, match="require side_len >= 4"):
        GEN.generate(1, 2, difficulty=band, side_len=3, distractor_variant="clockwise")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, difficulty=band, texture="no_markers")


def test_self_check_rejects_task_specific_mutation_fixtures() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_negative_recombination_separates_distribution_from_oracle_domain() -> None:
    canonical = _canonical_row()["program_solution"]
    valid = GEN.generate(
        73,
        2,
        difficulty="medium",
        grid_h=12,
        grid_w=12,
        side_len=6,
        missing_corner="bottom_left",
        row_offset=2,
        col_offset=3,
        distractor_variant="counterclockwise",
    )
    facts = GEN._analyze(valid)

    # Add a second interior gray: the teaching distribution rejects it, while
    # the permissive bbox-based Racket oracle still executes deterministically.
    extra = copy.deepcopy(valid)
    for u in range(1, facts["side_len"]):
        for v in range(1, facts["side_len"]):
            if u + v <= facts["side_len"] - 1 and (u, v) != facts["distractor_local"]:
                rr, cc = GEN._local_to_grid(facts["missing_index"], facts["side_len"], u, v)
                extra[facts["r0"] + rr][facts["c0"] + cc] = 5
                break
        else:
            continue
        break
    assert GEN.self_check(extra)

    # Remove every gray cell: both the lesson checker and oracle reject/fail.
    absent = [[7 if value == 5 else value for value in row] for row in valid]
    assert GEN.self_check(absent)

    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        output = bridge.eval_text(rule_application(canonical, extra))
        assert isinstance(output, list) and output
        with pytest.raises(RacketBridgeError):
            bridge.eval_text(rule_application(canonical, absent))
    finally:
        bridge.shutdown()


def test_witnesses_fire_in_every_band_and_verified_rivals_disagree() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(20000 + i, i, difficulty=band) for i in range(80)]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (band, name)
            rivals = GEN.WITNESS_RIVALS[name]
            for grid in firing[:10]:
                official = GEN.rule_mirror(grid)
                assert any(GEN.SEMANTIC_RIVALS[rival](grid) != official for rival in rivals)


def test_every_sliding_lesson_window_refutes_named_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = [_pair(31000 + start, start + offset, band) for offset in range(4)]
            query = _pair(31000 + start, start + 4, band)
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(
                    competitor(demo["input"]) != demo["output"]
                    for demo in demos
                )


def test_rule_mirror_differs_from_solid_fill_on_scheduled_large_examples() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(44000, i, difficulty=band) for i in range(4)]
        assert any(
            GEN._rival_solid_triangle(grid) != GEN.rule_mirror(grid)
            for grid in grids
        )


def test_task_local_authorities_remain_execution_equivalent_on_samples() -> None:
    canonical = _canonical_row()["program_solution"]
    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    sources = [canonical, target["target_code"], target["raw_code"]]
    inputs = [pair["input"] for pair in _pairs()]
    inputs.extend(
        GEN.generate(51000 + seed, seed, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(5)
    )
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for grid in inputs:
            outputs = [bridge.eval_text(rule_application(source, grid)) for source in sources]
            assert outputs[1:] == outputs[:-1]
    finally:
        bridge.shutdown()
