from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "d83ca4e3fa19"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/50e2f7e22580"
    / "easy_45_draw_border_from_corners__d83ca4e3fa19.json"
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _norm_grid(grid) -> list[list[int]]:
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    pairs = list(row["train"]) + (list(test) if isinstance(test, list) else [test])
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in pairs
    ]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _profile_key(grid) -> tuple[int, int, int, int]:
    observed = MODULE.observe_overrides(grid)
    return (
        observed["grid_h"],
        observed["grid_w"],
        observed["rect_h"],
        observed["rect_w"],
    )


def test_metadata_rule_hash_and_selected_task_authority_are_exact() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]

    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "5e968529140e"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert target["target_code"] == canonical
    # raw_code is a deliberately retained, execution-equivalent archival body.
    assert target["raw_code"] != canonical


def test_all_five_canonical_pairs_are_accepted_and_mirrored_exactly() -> None:
    pairs = _all_pairs()
    assert len(pairs) == 5
    assert {_profile_key(pair["input"]) for pair in pairs} == set(
        MODULE._CANONICAL_PROFILES
    )
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    source = _canonical_row()["program_solution"]
    pairs = _all_pairs()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(source, pair["input"]))
            assert actual == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(difficulty: str) -> None:
    cases = [
        {"grid_h": 6, "grid_w": 8, "rect_h": 3, "rect_w": 5, "corner_color": 1},
        {"grid_h": 9, "grid_w": 11, "rect_h": 7, "rect_w": 9, "corner_color": 9},
        {"grid_h": 6, "rect_h": 6, "corner_color": 4},
        {"grid_w": 8, "rect_w": 8, "corner_color": 7},
        {"rect_h": 7, "rect_w": 9, "corner_color": 2},
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            10_000 + index,
            500 + index,
            difficulty=difficulty,
            **overrides,
        )
        observed = MODULE.observe_overrides(grid)
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []
        for name, requested in overrides.items():
            assert observed[name] == requested

    with pytest.raises(ValueError, match="cannot fit"):
        MODULE.generate(1, 2, difficulty=difficulty, grid_h=6, rect_h=7)
    with pytest.raises(ValueError, match="cannot fit"):
        MODULE.generate(1, 2, difficulty=difficulty, grid_w=8, rect_w=9)


def test_unknown_invalid_and_wrong_typed_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, obsolete_axis=3)
    with pytest.raises(ValueError, match="must be an integer"):
        MODULE.generate(1, 2, corner_color="4")
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, corner_color=0)
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(1, 2, difficulty="expert")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(123_456_789)
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    replay = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(replay, first))
    replay[0][0] = 9 if replay[0][0] != 9 else 8
    assert MODULE.generate(901, 17, difficulty="hard") == first


def test_linked_semantic_census_200_per_band_and_disjoint_stability() -> None:
    expected_profiles = set(MODULE._CANONICAL_PROFILES)
    expected_modes = set(MODULE._PLACEMENT_MODES)

    for band in ("easy", "medium", "hard"):
        grids = [
            MODULE.generate(20_000 + seed, seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(MODULE.self_check(grid) == [] for grid in grids)
        assert all(MODULE.strict_canonical_like(grid) == [] for grid in grids)
        assert all(MODULE.rule_mirror(grid) != grid for grid in grids)
        assert {_profile_key(grid) for grid in grids} == expected_profiles
        assert len({_frozen(grid) for grid in grids}) >= 150
        assert len({_frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 150
        assert {MODULE.observe_overrides(grid)["corner_color"] for grid in grids} == set(range(1, 10))

        analyses = [MODULE._analyze(grid) for grid in grids]
        fired_modes = set()
        for item in analyses:
            if item["top"] == 0:
                fired_modes.add("top")
            if item["bottom"] == item["height"] - 1:
                fired_modes.add("bottom")
            if item["left"] == 0:
                fired_modes.add("left")
            if item["right"] == item["width"] - 1:
                fired_modes.add("right")
            if (
                item["top"] > 0
                and item["bottom"] < item["height"] - 1
                and item["left"] > 0
                and item["right"] < item["width"] - 1
            ):
                fired_modes.add("interior")
        assert fired_modes == expected_modes

        # Disjoint seeds must preserve variation and the complete linked support.
        later = [
            MODULE.generate(80_000 + seed, seed + 1_000, difficulty=band)
            for seed in range(200)
        ]
        assert all(MODULE.strict_canonical_like(grid) == [] for grid in later)
        assert {_profile_key(grid) for grid in later} == expected_profiles
        assert len({_frozen(grid) for grid in later}) >= 150
        assert {_frozen(grid) for grid in grids} != {_frozen(grid) for grid in later}


def test_three_demo_schedule_rebuts_size_aspect_color_and_identity_shortcuts() -> None:
    for seed in range(30):
        pairs = []
        for sample_index in range(4):
            grid = MODULE.generate(seed, sample_index)
            pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []
        analyses = [MODULE._analyze(pair["input"]) for pair in pairs[:3]]
        assert len({(item["rect_h"], item["rect_w"]) for item in analyses}) == 3
        assert any(item["rect_h"] > item["rect_w"] for item in analyses)
        assert any(item["rect_w"] > item["rect_h"] for item in analyses)
        assert len({item["color"] for item in analyses}) == 3
        assert all(pair["input"] != pair["output"] for pair in pairs[:3])


def test_self_check_rejects_five_targeted_structural_impostors() -> None:
    valid = MODULE.generate(312, 4, difficulty="medium")
    analysis = MODULE._analyze(valid)
    assert not analysis["errors"]
    corners = [(row, col) for row, col, _ in analysis["cells"]]

    only_three = copy.deepcopy(valid)
    row, col = corners[0]
    only_three[row][col] = 0
    assert any("exactly four" in error for error in MODULE.self_check(only_three))

    mismatched_color = copy.deepcopy(valid)
    row, col = corners[1]
    mismatched_color[row][col] = 9 if analysis["color"] != 9 else 8
    assert any("share one" in error for error in MODULE.self_check(mismatched_color))

    non_corner_fourth = copy.deepcopy(valid)
    row, col = corners[0]
    non_corner_fourth[row][col] = 0
    non_corner_fourth[analysis["top"]][analysis["left"] + 1] = analysis["color"]
    assert any(
        "two rows and two columns" in error or "exactly the rectangle corners" in error
        for error in MODULE.self_check(non_corner_fourth)
    )

    stray_fifth = copy.deepcopy(valid)
    spot = next(
        (row, col)
        for row, line in enumerate(stray_fifth)
        for col, value in enumerate(line)
        if value == 0 and row not in (analysis["top"], analysis["bottom"])
    )
    stray_fifth[spot[0]][spot[1]] = analysis["color"]
    assert any("exactly four" in error for error in MODULE.self_check(stray_fifth))

    too_narrow = copy.deepcopy(valid)
    for row, col in corners:
        too_narrow[row][col] = 0
    for row, col in (
        (analysis["top"], analysis["left"]),
        (analysis["top"], analysis["left"] + 3),
        (analysis["bottom"], analysis["left"]),
        (analysis["bottom"], analysis["left"] + 3),
    ):
        too_narrow[row][col] = analysis["color"]
    assert any("width must be" in error for error in MODULE.self_check(too_narrow))


def test_negative_recombination_is_rejected_while_racket_still_executes() -> None:
    grid = MODULE.generate(717, 3, difficulty="hard")
    analysis = MODULE._analyze(grid)
    used = {value for row in grid for value in row}
    foreign = next(color for color in range(1, 10) if color not in used)
    row, col, _ = analysis["cells"][-1]
    recombined = copy.deepcopy(grid)
    recombined[row][col] = foreign

    errors = MODULE.self_check(recombined)
    assert errors
    assert any("share one" in error for error in errors)
    assert foreign not in {
        value
        for rr, line in enumerate(grid)
        for cc, value in enumerate(line)
        if (rr, cc) != (row, col)
    }

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(
            rule_application(_canonical_row()["program_solution"], recombined)
        )
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(recombined)
    assert all(len(line) == len(recombined[0]) for line in output)


def test_semantic_witnesses_all_fire_in_each_band() -> None:
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for seed in range(200):
            grid = MODULE.generate(50_000 + seed, seed, difficulty=band)
            for name, witness in MODULE.SEMANTIC_WITNESSES.items():
                counts[name] += int(witness(grid))
        assert set(counts) == set(MODULE.SEMANTIC_WITNESSES)
        assert min(counts.values()) > 0
