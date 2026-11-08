"""Focused semantic and regression tests for generator 2fb0197be694."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter

from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "2fb0197be694"
ROOT = find_root(__file__)
GEN, GEN_SOURCE_PATH, GEN_SOURCE_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _catalog_row():
    with (ROOT / "catalog/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("id") == TASK_ID:
                return row
    raise AssertionError("catalog task row missing")


def _canonical_pairs():
    return read_canonical_pairs(TASK_ID, root=ROOT)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _census(seed_start: int, sample_start: int):
    result = {}
    pooled_masks = set()
    for band in ("easy", "medium", "hard"):
        masks = Counter()
        profiles = Counter()
        orientations = Counter()
        strict = 0
        position_support = [{0: 0, 1: 0} for _ in range(4)]
        grids = set()
        for index in range(200):
            grid = GEN.generate(
                seed_start + index,
                sample_start + index,
                difficulty=band,
            )
            assert GEN.self_check(grid, difficulty=band) == []
            facts = GEN._analyze(grid)
            mask = facts["motif_mask"]
            masks[mask] += 1
            pooled_masks.add(mask)
            profiles[facts["layout_profile"]] += 1
            orientations[facts["frame_orientation"]] += 1
            strict += GEN.canonical_profile_signature(grid) is not None
            grids.add(_grid_key(grid))
            for bit in range(4):
                position_support[bit][int(bool(mask & (1 << bit)))] += 1
        result[band] = {
            "strict": strict,
            "masks": masks,
            "profiles": profiles,
            "orientations": orientations,
            "position_support": position_support,
            "distinct_grids": len(grids),
        }
    return result, pooled_masks


def test_version_rule_hash_and_selected_authority_are_current():
    row = _canonical_row()
    catalog = _catalog_row()
    assert GEN_SOURCE_PATH.is_file()
    assert GEN.VERSION == catalog["version"] == "3.0.0"
    assert GEN_SOURCE_SHA256 == catalog["reviewed_generator_sha256"]
    assert GEN.RULE_HASH == catalog["reviewed_rule_hash"]
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])
    assert GEN.RULE_HASH == "eb3e8f5d9da4"


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    signatures = set()
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        signatures.add(GEN.canonical_profile_signature(pair["input"]))
        assert pair["input"] == original
    assert signatures == {
        (9, 9, "centered_frame", 2),
        (9, 9, "centered_frame", 3),
    }


def test_every_declared_axis_is_exact_and_observable():
    for band in ("easy", "medium", "hard"):
        for profile in ("centered_9x9", "free_rectangular"):
            grid = GEN.generate(1, 7, difficulty=band, layout_profile=profile)
            assert GEN.observe_overrides(grid)["layout_profile"] == profile
        for motif_mask in range(1, 16):
            grid = GEN.generate(2, 11, difficulty=band, motif_mask=motif_mask)
            assert GEN.observe_overrides(grid)["motif_mask"] == motif_mask
            assert GEN.rule_mirror(grid) == [[
                8 if motif_mask & (1 << bit) else 0 for bit in range(4)
            ]]
        for orientation in GEN.FRAME_ORIENTATIONS:
            grid = GEN.generate(
                3,
                13,
                difficulty=band,
                frame_orientation=orientation,
            )
            assert GEN.observe_overrides(grid)["frame_orientation"] == orientation


def test_three_demo_schedule_identifies_every_strip_position():
    checked = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(15):
                masks = [
                    GEN.observe_overrides(
                        GEN.generate(seed, start + offset, difficulty=band)
                    )["motif_mask"]
                    for offset in range(4)
                ]
                assert len(set(masks)) == 4
                for bit in range(4):
                    assert {
                        int(bool(mask & (1 << bit))) for mask in masks[:3]
                    } == {0, 1}
                checked += 1
    assert checked == 540


def test_linked_semantic_census_and_disjoint_stability_census():
    tuning, tuning_masks = _census(seed_start=1000, sample_start=2000)
    stability, stability_masks = _census(seed_start=10000, sample_start=20000)
    for census in (tuning, stability):
        for band, facts in census.items():
            assert facts["strict"] >= 10, band
            assert set(facts["profiles"]) == {
                "centered_9x9",
                "free_rectangular",
            }
            assert set(facts["orientations"]) == set(GEN.FRAME_ORIENTATIONS)
            assert facts["distinct_grids"] >= 180
            for support in facts["position_support"]:
                assert support[0] > 0 and support[1] > 0
    assert tuning_masks == set(range(1, 16))
    assert stability_masks == set(range(1, 16))


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(
        9,
        0,
        difficulty="medium",
        layout_profile="centered_9x9",
        frame_orientation="south_east",
        motif_mask=1,
    )
    facts = GEN._analyze(base)
    assert facts["errors"] == []

    outside_motif = copy.deepcopy(base)
    occupied = facts["canon_cells"][0]
    outside_motif[occupied[0]][occupied[1]] = 0
    outside_motif[0][0] = 8

    duplicate_origin = copy.deepcopy(base)
    duplicate_origin[0][0] = 2

    missing_axis_marker = copy.deepcopy(base)
    r4, c4 = next(
        (r, c)
        for r, row in enumerate(missing_axis_marker)
        for c, value in enumerate(row)
        if value == 4
    )
    missing_axis_marker[r4][c4] = 0

    diagonal_frame = copy.deepcopy(base)
    r3, c3 = next(
        (r, c)
        for r, row in enumerate(diagonal_frame)
        for c, value in enumerate(row)
        if value == 3
    )
    diagonal_frame[r3][c3] = 0
    orow, ocol = facts["origin"]
    diagonal_frame[orow + 1][ocol + 1] = 3

    empty_motif = copy.deepcopy(base)
    for r, c in facts["canon_cells"]:
        if empty_motif[r][c] == 8:
            empty_motif[r][c] = 0

    absent_replacement_feature = copy.deepcopy(base)
    absent_replacement_feature[occupied[0]][occupied[1]] = 7

    for impostor in (
        outside_motif,
        duplicate_origin,
        missing_axis_marker,
        diagonal_frame,
        empty_motif,
        absent_replacement_feature,
    ):
        assert GEN.self_check(impostor)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(44, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(44, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    replay = GEN.generate(44, 17, difficulty="hard")
    assert replay == second
