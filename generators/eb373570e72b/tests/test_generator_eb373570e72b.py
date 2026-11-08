from __future__ import annotations

import copy
import hashlib
import json
import random
import shutil
from collections import Counter

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators import base as generator_base
from puzzle_generators.per_puzzle.eb373570e72b import generator as module
from reviewer_support import canonical_path, find_root
from scripts.rule_smoke import purity_body, rule_application


TASK_ID = "eb373570e72b"
ROOT = find_root(__file__)
CANONICAL_PATH = canonical_path(ROOT)
DATA_ROOT = CANONICAL_PATH.parent.parent
AUTHORITY_PATHS = (
    DATA_ROOT / "base/solutions/training/84551f4c__eb373570e72b.json",
    DATA_ROOT / "base/solutions/augmented/84551f4c__5b85e6519cbc.json",
)


def canonical_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def canonical_pairs() -> list[dict]:
    return [
        pair
        for row in canonical_rows()
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]


def frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_every_canonical_occurrence_is_accepted_and_mirrored_exactly():
    rows = canonical_rows()
    pairs = canonical_pairs()
    assert len(rows) == 2
    assert len(pairs) == 10
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert module.self_check(source) == []
        assert module.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_rule_hash_and_all_task_local_authorities_are_exactly_synchronized():
    rows = canonical_rows()
    sources = {row["program_solution"] for row in rows}
    assert len(sources) == 1
    source = next(iter(sources))
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert module.RULE_HASH == digest == "73b10de4ceaa"
    for path in AUTHORITY_PATHS:
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["racket_target"]["raw_code"] == source
        assert record["racket_target"]["target_code"] == source


def test_exact_axes_are_literal_observable_and_cover_valid_boundaries():
    assert set(module.AXES) == {"grid_h", "grid_w", "n_chains", "scene_mode"}
    assert module.HELPFUL_TEXTURES == module.DEGENERATE_TEXTURES == ()
    cases = (
        {"scene_mode": "nonstaggered", "grid_h": 3, "grid_w": 7, "n_chains": 1},
        {"scene_mode": "nonstaggered", "grid_h": 9, "grid_w": 30, "n_chains": 5},
        {"scene_mode": "staggered", "grid_h": 6, "grid_w": 7, "n_chains": 2},
        {"scene_mode": "staggered", "grid_h": 9, "grid_w": 30, "n_chains": 5},
    )
    for index, overrides in enumerate(cases):
        grid = module.generate(70 + index, index, difficulty="hard", **overrides)
        assert module.self_check(grid) == []
        assert module.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "overrides",
    [
        {"scene_mode": "staggered", "grid_h": 3},
        {"scene_mode": "staggered", "n_chains": 1},
        {"grid_w": 7, "n_chains": 5},
        {"scene_mode": "staggered", "grid_w": 7, "n_chains": 5},
    ],
)
def test_incompatible_exact_axis_combinations_reject_loudly(overrides):
    with pytest.raises(ValueError):
        module.generate(3, 4, difficulty="medium", **overrides)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"texture": "warm"},
        {"scene_mode": "unknown"},
        {"grid_h": 2},
        {"grid_w": 31},
        {"n_chains": 0},
        {"difficulty": "expert"},
    ],
)
def test_unknown_or_out_of_domain_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        module.generate(1, 0, **kwargs)


def test_default_keyed_axis_requests_equal_observed_returned_grid_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                grid = module.generate(10_000 + seed, seed * 17 + 5, difficulty=band)
                ctx = captured[-1]
                assert set(ctx._drawn) >= set(module.AXES)
                assert module.observe_overrides(grid) == {
                    axis: ctx._drawn[axis] for axis in module.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    random.seed(9_157)
    state = random.getstate()
    first = module.generate(91, 13, difficulty="hard", scene_mode="staggered")
    assert random.getstate() == state
    second = module.generate(91, 13, difficulty="hard", scene_mode="staggered")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert module.generate(91, 13, difficulty="hard", scene_mode="staggered") == second


def test_default_distribution_fires_both_grammars_and_is_highly_variable():
    for band in ("easy", "medium", "hard"):
        grids = [
            module.generate(20_000 + seed, seed * 19 + 7, difficulty=band)
            for seed in range(240)
        ]
        analyses = [module._analysis(grid)["facts"] for grid in grids]
        modes = Counter(facts["scene_mode"] for facts in analyses)
        outputs = [module.rule_mirror(grid) for grid in grids]
        for grid, facts, output in zip(grids, analyses, outputs):
            if facts["scene_mode"] != "staggered":
                continue
            vertical = sorted(
                col for chain in facts["vertical_chains"] for col in chain
            )
            for loose in facts["loose_blue_cols"]:
                later = [col for col in vertical if col > loose]
                end = min(facts["width"] - 1, later[0] - 2) if later else min(
                    facts["width"] - 1, loose + 2
                )
                assert end >= loose
                assert all(output[-1][col] == 1 for col in range(loose, end + 1))
        assert set(modes) == set(module.SCENE_MODES)
        assert min(modes.values()) >= 20
        assert all(grid != output for grid, output in zip(grids, outputs))
        assert len({frozen(grid) for grid in grids}) >= 200
        assert len({frozen(grid) for grid in outputs}) >= 200


def test_self_check_rejects_four_structural_impostors():
    straight = module.generate(
        301,
        9,
        scene_mode="nonstaggered",
        grid_h=5,
        grid_w=18,
        n_chains=3,
    )
    straight_facts = module._analysis(straight)["facts"]
    broken_column = copy.deepcopy(straight)
    broken_column[-1][straight_facts["markers"][0]] = 0
    assert module.self_check(broken_column)

    staggered = module.generate(
        302,
        11,
        difficulty="hard",
        scene_mode="staggered",
        grid_h=9,
        grid_w=24,
        n_chains=4,
    )
    facts = module._analysis(staggered)["facts"]

    recolored_loose_suffix = copy.deepcopy(staggered)
    loose = facts["loose_blue_cols"][0]
    recolored_loose_suffix[-1][loose] = 2
    assert module.self_check(recolored_loose_suffix)

    broken_loose_suffix = copy.deepcopy(staggered)
    broken_loose_suffix[-1][loose] = 0
    assert module.self_check(broken_loose_suffix)

    foreign_early_evidence = copy.deepcopy(staggered)
    foreign_col = next(
        col
        for col in range(facts["width"])
        if col not in facts["markers"] and col not in facts["loose_blue_cols"]
    )
    foreign_early_evidence[max(0, facts["active_row"] - 1)][foreign_col] = 2
    assert module.self_check(foreign_early_evidence)


def test_nonstaggered_red_to_blue_handoff_is_a_positive_rule_branch():
    grid = module.generate(
        2,
        25,
        difficulty="hard",
        scene_mode="nonstaggered",
        grid_h=5,
        grid_w=24,
        n_chains=4,
    )
    facts = module._analysis(grid)["facts"]
    assert facts["handoffs"]
    for left, right in facts["handoffs"]:
        assert right == left + 3
        assert grid[0][left] == 2 and grid[0][right] == 1
        assert any(chain == [left] or chain[-1] == left for chain in facts["vertical_chains"])
        assert any(chain[0] == right for chain in facts["horizontal_chains"])


def test_hard_staggered_branch_witnesses_gap_closure_and_loose_blue_flooring():
    grid = module.generate(
        401,
        17,
        difficulty="hard",
        scene_mode="staggered",
        grid_h=9,
        grid_w=24,
        n_chains=4,
    )
    facts = module._analysis(grid)["facts"]
    output = module.rule_mirror(grid)
    assert facts["horizontal_chains"] and facts["vertical_chains"]
    assert facts["loose_blue_cols"]
    bottom = output[-1]
    assert any(
        grid[-1][col] == 0
        and bottom[col] == 2
        and bottom[col - 1] == bottom[col + 1] == 2
        for col in range(1, len(bottom) - 1)
    )
    assert any(
        grid[-1][col] == 1
        and col not in facts["markers"]
        and any(bottom[target] == 1 for target in range(col, min(len(bottom), col + 3)))
        for col in facts["loose_blue_cols"]
    )


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_canonical_and_generated_inputs_and_executes_rejected_recombination():
    source = canonical_rows()[0]["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=48)
    try:
        for pair in canonical_pairs():
            original = copy.deepcopy(pair["input"])
            assert bridge.eval_text(rule_application(source, original)) == pair["output"]
            assert original == pair["input"]

        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(12):
                grid = module.generate(50_000 + seed, band_index * 100 + seed, difficulty=band)
                snapshot = copy.deepcopy(grid)
                assert bridge.eval_text(rule_application(source, grid)) == module.rule_mirror(grid)
                assert grid == snapshot

        a = module.generate(60_001, 1, difficulty="hard")
        b = module.generate(60_002, 2, difficulty="hard")
        probe = bridge.eval_text(purity_body(source, a, b))
        assert probe == [module.rule_mirror(a), module.rule_mirror(a), a]

        malformed = module.generate(
            60_003,
            3,
            difficulty="hard",
            scene_mode="staggered",
            grid_h=9,
            grid_w=24,
            n_chains=4,
        )
        malformed_facts = module._analysis(malformed)["facts"]
        loose = malformed_facts["loose_blue_cols"][0]
        for row in range(malformed_facts["active_row"] + 1, len(malformed)):
            if malformed[row][loose] == 1:
                malformed[row][loose] = 2
        assert module.self_check(malformed)
        assert not any(
            malformed[row][col] == 2
            for row in range(malformed_facts["active_row"] + 1, len(malformed))
            for col in range(len(malformed[0]))
            if col not in malformed_facts["markers"] and col != loose
        )
        result = bridge.eval_text(rule_application(source, malformed))
        assert len(result) == len(malformed)
        assert all(len(row) == len(malformed[0]) for row in result)
    finally:
        bridge.shutdown()
