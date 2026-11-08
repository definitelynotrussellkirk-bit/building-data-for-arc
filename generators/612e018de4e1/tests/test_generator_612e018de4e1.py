"""Regression tests for the linked-profile rectangle-corner generator."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "612e018de4e1"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.612e018de4e1.generator"
)


def _canonical_inputs():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.extend(pair["input"] for pair in row["train"])
                rows.extend(pair["input"] for pair in row["test"])
    return rows


def test_all_canonical_inputs_define_the_pinned_linked_profiles():
    canonical = _canonical_inputs()
    assert len(canonical) == 5
    assert {GEN.canonical_profile_signature(grid) for grid in canonical} == (
        GEN._CANONICAL_SIGNATURES
    )
    assert all(GEN.self_check(copy.deepcopy(grid)) == [] for grid in canonical)


def test_every_official_profile_is_reachable_in_every_band():
    for band in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SCENE_PROFILES}
        for seed in range(600):
            grid = GEN.generate(seed, seed * 19 + 7, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            counts[GEN.observe_overrides(grid)["scene_profile"]] += 1
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_exact_override_cross_product_is_observable():
    for profile in GEN.SCENE_PROFILES:
        for missing in GEN._MISSING_CORNERS:
            for side in GEN._DISTRACTOR_SIDES:
                for palette in GEN._PALETTE_BANDS:
                    grid = GEN.generate(
                        23,
                        11,
                        difficulty="hard",
                        scene_profile=profile,
                        missing_corner=missing,
                        distractor_side=side,
                        palette_band=palette,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "scene_profile": profile,
                        "missing_corner": missing,
                        "distractor_side": side,
                        "palette_band": palette,
                    }


def test_self_check_rejects_targeted_impostors():
    base = GEN.generate(
        101,
        9,
        scene_profile="p10x10_one_l",
        missing_corner="br",
        distractor_side="top",
        palette_band="low",
    )

    no_distractor = copy.deepcopy(base)
    for r, row in enumerate(no_distractor):
        for c, value in enumerate(row):
            if value not in (0, 1):
                no_distractor[r][c] = 0

    extra_blue = copy.deepcopy(base)
    extra_blue[0][0] = 1

    red_input = copy.deepcopy(base)
    red_input[0][0] = 2

    inside_bbox = copy.deepcopy(base)
    for r, row in enumerate(inside_bbox):
        for c, value in enumerate(row):
            if value not in (0, 1):
                inside_bbox[r][c] = 0
    geometry = GEN._blue_geometry(inside_bbox)
    assert geometry is not None
    _, rows, cols, _ = geometry
    inside_bbox[rows[0] + 1][cols[0] + 1] = 4
    inside_bbox[rows[0] + 1][cols[0] + 2] = 4
    inside_bbox[rows[0] + 2][cols[0] + 1] = 4

    straight_three = copy.deepcopy(base)
    for r, row in enumerate(straight_three):
        for c, value in enumerate(row):
            if value not in (0, 1):
                straight_three[r][c] = 0
    straight_three[0][0] = 4
    straight_three[0][1] = 4
    straight_three[0][2] = 4

    for impostor in (
        no_distractor,
        extra_blue,
        red_input,
        inside_bbox,
        straight_three,
    ):
        assert GEN.self_check(impostor)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(37, 13, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(37, 13, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
