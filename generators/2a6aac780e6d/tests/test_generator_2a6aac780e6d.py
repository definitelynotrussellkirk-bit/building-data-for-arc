from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from reviewer_support import canonical_path, canonical_pairs, find_root, load_selected_generator

import pytest

ROOT = find_root(__file__)
BASE_PATH = ROOT / "shared/data/base/solutions/banks/391ca7d21fbe/E10__2a6aac780e6d.json"
CANONICAL_PATH = canonical_path(ROOT)
MODULE, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator("2a6aac780e6d", root=ROOT)


def _canonical_row():
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("canonical task not found")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_task_local_sources_are_synchronized():
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text())
    assert MODULE.RULE_HASH == _normalized_hash(canonical) == "4f90f10302a9"
    assert _normalized_hash(base["racket_target"]["target_code"]) == MODULE.RULE_HASH


def test_rule_mirror_solves_every_canonical_pair():
    pairs = canonical_pairs(MODULE.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        source_copy = copy.deepcopy(source)
        assert MODULE.rule_mirror(source) == pair["output"]
        assert source == source_copy


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_exact_scene_profile_is_observable_and_valid(profile, band):
    grid = MODULE.generate(771, 19, difficulty=band, scene_profile=profile)
    assert MODULE.self_check(grid, difficulty=band) == []
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    assert MODULE.rule_mirror(grid) != grid


def test_determinism_fresh_returns_and_global_random_state():
    random.seed(918273)
    state_before = random.getstate()
    first = MODULE.generate(91, 7, difficulty="hard", scene_profile="all_guards")
    state_after = random.getstate()
    second = MODULE.generate(91, 7, difficulty="hard", scene_profile="all_guards")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(91, 7, difficulty="hard", scene_profile="all_guards") == second
    assert state_before == state_after


def test_self_check_rejects_targeted_impostors():
    base = MODULE.generate(14, 3, difficulty="medium", scene_profile="long_fill")
    info = MODULE._analysis(base)
    positive = info["qualifying"][0]
    row = positive["row"]
    left = positive["left"]
    right = positive["right"]

    all_background = [[0] * len(base[0]) for _ in base]
    singleton = copy.deepcopy(base)
    singleton[row][right] = 0
    mismatched_only = copy.deepcopy(base)
    mismatched_only[row][right] = (positive["color"] % 9) + 1
    crowded_only = copy.deepcopy(base)
    extra = next(col for col in range(len(base[0])) if col not in (left, right))
    crowded_only[row][extra] = (positive["color"] % 9) + 1
    adjacent_same = [[0] * len(base[0]) for _ in base]
    adjacent_same[row][left] = positive["color"]
    adjacent_same[row][left + 1] = positive["color"]

    for impostor in (
        all_background,
        singleton,
        mismatched_only,
        crowded_only,
        adjacent_same,
    ):
        assert MODULE.self_check(impostor)


def test_lawful_unpublished_recombination_is_calibrated_out():
    first = MODULE.generate(22, 0, scene_profile="two_distinct_fills")
    second = MODULE.generate(23, 0, scene_profile="mismatch_guard")
    recombined = copy.deepcopy(first)
    mismatch = MODULE._analysis(second)["mismatches"][0]
    target_row = next(
        index
        for index, row in enumerate(recombined)
        if not any(row)
    )
    recombined[target_row] = [0] * len(recombined[0])
    left = min(mismatch["left"], len(recombined[0]) - 3)
    right = min(max(left + 2, mismatch["right"]), len(recombined[0]) - 1)
    recombined[target_row][left] = mismatch["left_color"]
    recombined[target_row][right] = mismatch["right_color"]

    # The canonical rule is general enough to transform the two positive rows.
    assert MODULE.rule_mirror(recombined) != recombined
    # The generator checker rejects this uncalibrated 2-positive + mismatch mix.
    assert MODULE.self_check(recombined)


def test_unknown_controls_and_unknown_difficulty_fail_loudly():
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, bogus=1)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, scene_profile="not_a_profile")
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, difficulty="extreme")
