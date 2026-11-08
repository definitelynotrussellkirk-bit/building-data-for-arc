"""Focused regressions for the clockwise icon-color curriculum."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module("puzzle_generators.per_puzzle.a4863798ed70.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 8
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", gen.PROFILE_NAMES)
def test_every_profile_override_is_exact_and_observable(band, profile):
    grid = gen.generate(901, 17, difficulty=band, scene_profile=profile)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_and_invalid_calls_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="not_a_profile")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4863798)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_every_three_demo_window_eliminates_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(14):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(4401, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            qgrid = gen.generate(4401, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": qgrid, "output": gen.rule_mirror(qgrid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_mutations_reject_min_max_and_task_specific_impostors():
    valid = gen.generate(
        71,
        0,
        difficulty="medium",
        scene_profile="canonical_3x5_20x22",
    )
    frames, errors = gen._frame_facts(valid)
    assert errors == []
    first, second = frames[:2]

    too_few = copy.deepcopy(valid)
    for r, c in sorted(first["icon_cells"])[2:]:
        too_few[r][c] = 0

    too_many = copy.deepcopy(valid)
    r1, c1, r2, c2 = first["bbox"]
    blanks = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if too_many[r][c] == 0
    ]
    for r, c in blanks[: max(0, 6 - len(first["icon_cells"]))]:
        too_many[r][c] = first["icon_color"]

    broken_frame = copy.deepcopy(valid)
    r1, c1, _, _ = first["bbox"]
    broken_frame[r1][c1] = 0

    duplicate_icon_color = copy.deepcopy(valid)
    for r, c in second["icon_cells"]:
        duplicate_icon_color[r][c] = first["icon_color"]

    stray_icon = copy.deepcopy(valid)
    stray = next(
        (r, c)
        for r, row in enumerate(stray_icon)
        for c, value in enumerate(row)
        if value == 0 and all(not (f["bbox"][0] <= r <= f["bbox"][2] and f["bbox"][1] <= c <= f["bbox"][3]) for f in frames)
    )
    stray_icon[stray[0]][stray[1]] = first["icon_color"]

    disconnected = copy.deepcopy(valid)
    for r, row in enumerate(disconnected):
        for c, value in enumerate(row):
            if value == 1:
                disconnected[r][c] = 0

    for name, grid in {
        "icon_min_minus_one": too_few,
        "icon_max_plus_one": too_many,
        "broken_red_frame": broken_frame,
        "duplicate_icon_color": duplicate_icon_color,
        "stray_icon_color": stray_icon,
        "disconnected_scene": disconnected,
    }.items():
        assert gen.self_check(grid), name
