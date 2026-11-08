"""Focused regressions for Solid Square Recolor generator 6237039401ed."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "6237039401ed"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE = ROOT / "data/base/solutions/banks/e352836528da/E5__6237039401ed.json"


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical task {TASK_ID} missing")


def test_rule_hash_and_all_task_local_sources_are_exactly_synchronized():
    source = canonical_row()["program_solution"]
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    base = json.loads(BASE.read_text())
    assert expected == GEN.RULE_HASH == "cb03ad6318a1"
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source


def test_canonical_pairs_are_accepted_and_match_both_oracles():
    row = canonical_row()
    pairs = row["train"] + row["test"]
    bridge = RacketBridge(timeout=20)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            assert GEN.self_check(pair["input"]) == []
            assert GEN.rule_mirror(pair["input"]) == pair["output"]
            assert bridge.eval_text(
                rule_application(row["program_solution"], pair["input"])
            ) == pair["output"]
            assert pair["input"] == before
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_consecutive_samples_cover_every_decisive_profile(band):
    target_profiles = set()
    distractor_profiles = set()
    for sample_index in range(4):
        grid = GEN.generate(913, sample_index, difficulty=band)
        observed = GEN.observe_overrides(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        target_profiles.add(observed["target_shape"])
        distractor_profiles.add(observed["distractor_shape"])
    assert target_profiles == set(GEN.TARGET_SHAPES)
    assert distractor_profiles == set(GEN.DISTRACTOR_SHAPES)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_override_boundaries_and_all_profiles_are_exactly_observable(band):
    for grid_h in (8, 18):
        for grid_w in (8, 18):
            for n_targets in (2, 3):
                for target_shape in GEN.TARGET_SHAPES:
                    for distractor_shape in GEN.DISTRACTOR_SHAPES:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_targets": n_targets,
                            "target_shape": target_shape,
                            "distractor_shape": distractor_shape,
                        }
                        grid = GEN.generate(
                            317,
                            911,
                            difficulty=band,
                            **requested,
                        )
                        assert GEN.observe_overrides(grid) == requested
                        assert GEN.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": requested},
                        ) == []



def _quadrant(component, h, w):
    mean_r = sum(r for r, _ in component) / len(component)
    mean_c = sum(c for _, c in component) / len(component)
    return ("top" if mean_r < h / 2 else "bottom") + "_" + (
        "left" if mean_c < w / 2 else "right"
    )


def test_target_and_distractor_roles_each_visit_every_quadrant():
    target_quadrants = set()
    distractor_quadrants = set()
    for seed in range(160):
        grid = GEN.generate(seed, seed % 4, difficulty="medium", n_targets=2)
        target_cells = GEN._target_cells(grid)
        for component in GEN._color5_components(grid):
            quadrant = _quadrant(component, len(grid), len(grid[0]))
            if component & target_cells:
                target_quadrants.add(quadrant)
            else:
                distractor_quadrants.add(quadrant)
    expected = {"top_left", "top_right", "bottom_left", "bottom_right"}
    assert target_quadrants == expected
    assert distractor_quadrants == expected

def test_target_profiles_rebut_exact_component_size_shortcut():
    changed_counts = {}
    for index, target_shape in enumerate(GEN.TARGET_SHAPES):
        grid = GEN.generate(
            41,
            index,
            difficulty="medium",
            grid_h=12,
            grid_w=12,
            n_targets=2,
            target_shape=target_shape,
            distractor_shape="l_tromino",
        )
        output = GEN.rule_mirror(grid)
        changed = sum(
            before != after
            for before_row, after_row in zip(grid, output)
            for before, after in zip(before_row, after_row)
        )
        changed_counts[target_shape] = changed
        # The near-miss gray distractor survives every profile.
        assert any(
            before == after == 5
            for before_row, after_row in zip(grid, output)
            for before, after in zip(before_row, after_row)
        )
    assert changed_counts == {
        "isolated_2x2": 8,
        "wide_2x3": 12,
        "tall_3x2": 12,
        "solid_3x3": 18,
    }


def test_declared_mutation_fixtures_are_rejected():
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    malformed = [[0] * 8 for _ in range(8)]
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1), (6, 6), (6, 7), (7, 6), (7, 7)):
        malformed[r][c] = 5
    malformed[0][2] = 5  # unique tail; absent from every remaining scene part
    assert GEN.self_check(malformed)
    expected = GEN.rule_mirror(malformed)
    bridge = RacketBridge(timeout=20)
    try:
        actual = bridge.eval_text(
            rule_application(canonical_row()["program_solution"], malformed)
        )
    finally:
        bridge.shutdown()
    assert actual == expected
    assert actual[0][2] == 5


def test_deterministic_replay_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = GEN.generate(7331, 29, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(7331, 29, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
