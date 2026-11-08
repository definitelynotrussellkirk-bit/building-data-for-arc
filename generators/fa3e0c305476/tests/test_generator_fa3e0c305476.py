"""Focused regression tests for the fa3e0c305476 hole-count generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "fa3e0c305476"
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
DATA_ROOT = CANONICAL.parent.parent
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _task_local_base() -> dict:
    return json.loads(
        (
            DATA_ROOT
            / "base/solutions/custom/33997447__fa3e0c305476.json"
        ).read_text()
    )


def test_rule_hash_and_task_local_authorities_are_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    expected_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash == "c89e9c00a1d3"

    base = _task_local_base()
    target = base["racket_target"]
    assert target["target_code"] == canonical
    assert target["raw_code"] == canonical


def test_all_canonical_inputs_are_accepted():
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            original = copy.deepcopy(pair["input"])
            assert GEN.self_check(pair["input"]) == []
            assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_pair_schedule_teaches_every_branch_before_query(band: str):
    expected_profiles = (
        "lesson_zero_12",
        "lesson_34",
        "lesson_156",
        "query_234",
    )
    for seed in range(20):
        signatures = [
            GEN.semantic_signature(
                GEN.generate(seed, sample_index, difficulty=band)
            )
            for sample_index in range(4)
        ]
        assert tuple(sig["profile"] for sig in signatures) == expected_profiles
        demonstrated = {
            count
            for sig in signatures[:3]
            for count in sig["hole_counts"]
        }
        query_counts = set(signatures[3]["hole_counts"])
        assert demonstrated == set(range(7))
        assert query_counts == {2, 3, 4}
        assert query_counts <= demonstrated


def test_boundary_overrides_are_exactly_observable():
    accepted = (
        {"grid_h": 6},
        {"grid_h": 18},
        {"grid_w": 6},
        {"grid_w": 30},
        {"profile": "lesson_zero_12"},
        {"profile": "lesson_34"},
        {"profile": "lesson_156"},
        {"profile": "query_234"},
        {"geometry_style": "compact"},
        {"geometry_style": "mixed_scale"},
    )
    for i, case in enumerate(accepted):
        grid = GEN.generate(10_000 + i, 3, difficulty="medium", **case)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        for axis, expected in case.items():
            assert observed[axis] == expected


def test_incompatible_override_combinations_reject_loudly():
    for case in (
        {"grid_h": 6, "grid_w": 6},
        {"grid_h": 6, "grid_w": 12, "profile": "lesson_156"},
        {"grid_h": 6, "grid_w": 13, "profile": "query_234"},
        {"grid_h": 7, "grid_w": 6, "geometry_style": "mixed_scale"},
        {"profile": "not-a-profile"},
        {"geometry_style": "not-a-style"},
        {"unknown_axis": 1},
    ):
        with pytest.raises(ValueError):
            GEN.generate(7, 3, difficulty="easy", **case)


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(912345)
    before = random.getstate()
    first = GEN.generate(17, 5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(17, 5, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    frozen = copy.deepcopy(first)
    second[0][0] = 9
    assert first == frozen


def test_self_check_rejects_four_targeted_impostors():
    base = GEN.generate(
        44,
        0,
        difficulty="medium",
        profile="lesson_zero_12",
        geometry_style="compact",
    )
    facts = GEN._analyze(base)["facts"]["objects"]

    wrong_palette = copy.deepcopy(base)
    r, c = next(
        (r, c)
        for r, row in enumerate(wrong_palette)
        for c, value in enumerate(row)
        if value == 8
    )
    wrong_palette[r][c] = 4

    singleton = copy.deepcopy(base)
    r, c = next(
        (r, c)
        for r, row in enumerate(singleton)
        for c, value in enumerate(row)
        if value == 0
        and all(
            not (0 <= r + dr < len(singleton) and 0 <= c + dc < len(singleton[0]))
            or singleton[r + dr][c + dc] == 0
            for dr, dc in GEN._CARD
        )
    )
    singleton[r][c] = 8

    open_frame = copy.deepcopy(base)
    frame = next(f for f in facts if f["hole_count"] == 2)
    r0, c0, r1, c1 = frame["bbox"]
    open_frame[r0][(c0 + c1) // 2] = 0

    merged = copy.deepcopy(base)
    left, right = sorted(facts, key=lambda f: f["bbox"][1])[:2]
    lr = (left["bbox"][0] + left["bbox"][2]) // 2
    rr = (right["bbox"][0] + right["bbox"][2]) // 2
    row = min(lr, rr)
    for col in range(left["bbox"][3] + 1, right["bbox"][1]):
        merged[row][col] = 8

    for impostor in (wrong_palette, singleton, open_frame, merged):
        assert GEN.self_check(impostor), impostor


def test_negative_recombination_uses_absent_replacement_feature():
    grid = GEN.generate(99, 1, difficulty="medium", geometry_style="compact")
    facts = GEN._analyze(grid)["facts"]["objects"]
    target = facts[0]["bbox"]
    mutation = copy.deepcopy(grid)
    r0, c0, r1, c1 = target
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if mutation[r][c] == 8:
                mutation[r][c] = 4
    remaining_values = {
        value
        for r, row in enumerate(mutation)
        for c, value in enumerate(row)
        if not (r0 <= r <= r1 and c0 <= c <= c1)
    }
    assert 4 not in remaining_values
    assert GEN.self_check(mutation)
