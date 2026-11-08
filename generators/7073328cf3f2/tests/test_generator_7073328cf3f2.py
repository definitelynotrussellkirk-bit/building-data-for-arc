from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.7073328cf3f2.generator"
)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_selected_rule_hash_is_pinned_to_task_local_authority():
    base = json.loads(
        Path("data/base/solutions/custom/3617dc99__7073328cf3f2.json").read_text()
    )
    target = base["racket_target"]["target_code"]
    actual = hashlib.sha256(" ".join(target.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == actual == "1047ef160c66"


def test_all_canonical_inputs_are_accepted_and_train_outputs_match_mirror():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        if pair.get("output") is not None:
            assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height", [7, 15])
@pytest.mark.parametrize("width", [7, 17])
@pytest.mark.parametrize("orientation", GEN.ORIENTATIONS)
@pytest.mark.parametrize("path_shape", GEN.PATH_SHAPES)
@pytest.mark.parametrize("side_mode", GEN.SIDE_MODES)
def test_every_declared_boundary_override_combination_is_exact(
    band, height, width, orientation, path_shape, side_mode
):
    grid = GEN.generate(
        314159,
        11,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        orientation=orientation,
        path_shape=path_shape,
        side_mode=side_mode,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "path_shape": path_shape,
        "side_mode": side_mode,
    }


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=123)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(23, 9, difficulty="hard")
    middle = GEN.generate(24, 10, difficulty="easy")
    second = GEN.generate(23, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert middle != first
    assert before == after


def test_self_check_rejects_targeted_structural_impostors():
    canonical = canonical_pairs(GEN.TASK_ID)
    base = GEN.generate(17, 0, difficulty="medium")

    no_red = copy.deepcopy(base)
    red = next((r, c) for r, row in enumerate(no_red) for c, v in enumerate(row) if v == 2)
    no_red[red[0]][red[1]] = 0
    assert any("red(2)" in reason for reason in GEN.self_check(no_red))

    duplicate_blue = copy.deepcopy(base)
    zero = next((r, c) for r, row in enumerate(duplicate_blue) for c, v in enumerate(row) if v == 0)
    duplicate_blue[zero[0]][zero[1]] = 1
    assert any("blue(1)" in reason for reason in GEN.self_check(duplicate_blue))

    disconnected = copy.deepcopy(base)
    traversable = GEN._analyze(disconnected)["traversable"]
    isolated = next(
        (r, c)
        for r, row in enumerate(disconnected)
        for c, value in enumerate(row)
        if value == 0 and all(n not in traversable for n in GEN._neighbors((r, c)))
    )
    disconnected[isolated[0]][isolated[1]] = 5
    assert any("one connected component" in reason for reason in GEN.self_check(disconnected))

    no_neutral = copy.deepcopy(base)
    for r, c in GEN._analyze(no_neutral)["neutral"]:
        no_neutral[r][c] = 0
    assert any("neutral" in reason for reason in GEN.self_check(no_neutral))

    cycle = copy.deepcopy(canonical[1]["input"])
    cycle[2][3] = 5
    assert any("acyclic" in reason for reason in GEN.self_check(cycle))


def test_every_four_demo_sliding_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [GEN.generate(1000 + start, start + offset, difficulty=band) for offset in range(5)]
            demos = [_pair(grid) for grid in grids[:4]]
            query = _pair(grids[4])
            assert GEN.lesson_identifiable(demos, query) == []


def test_default_schedule_covers_all_answer_roles_and_profiles():
    profiles = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = GEN.generate(9000 + sample_index, sample_index, difficulty=band)
            analysis = GEN._analyze(grid)
            assert analysis["red_side"]
            assert analysis["blue_side"]
            assert analysis["neutral"]
            profiles.add(GEN.schedule_profile(0, sample_index, band))
    assert profiles == set(GEN.PROFILE_SCHEDULE)
