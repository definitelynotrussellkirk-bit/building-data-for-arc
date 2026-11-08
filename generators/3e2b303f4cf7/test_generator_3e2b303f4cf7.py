"""Focused contract and semantic regressions for task 3e2b303f4cf7."""
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module("puzzle_generators.per_puzzle.3e2b303f4cf7.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_rule() -> str:
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_rule_hash_and_all_canonical_pairs() -> None:
    actual = hashlib.sha256(" ".join(_canonical_rule().split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        input_snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == input_snapshot


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(9, 10), (14, 18)])
@pytest.mark.parametrize("bar_count", [2, 3])
@pytest.mark.parametrize("layout", gen.LAYOUTS)
@pytest.mark.parametrize("decoy_kind", gen.DECOY_KINDS)
def test_override_boundaries_are_exact_and_observable(
    band: str,
    h: int,
    w: int,
    bar_count: int,
    layout: str,
    decoy_kind: str,
) -> None:
    grid = gen.generate(
        751,
        17,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        bar_count=bar_count,
        layout=layout,
        decoy_kind=decoy_kind,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "bar_count": bar_count,
        "layout": layout,
        "decoy_kind": decoy_kind,
    }


def test_unknown_and_invalid_calls_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=8)
    with pytest.raises(ValueError, match="bar_count"):
        gen.generate(1, 0, bar_count=4)
    with pytest.raises(ValueError, match="layout"):
        gen.generate(1, 0, layout="diagonal")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(92831)
    state = random.getstate()
    first = gen.generate(71, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(71, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second != gen.generate(72, 9, difficulty="medium")
    assert second != gen.generate(71, 10, difficulty="medium")


def test_every_sliding_three_demo_window_kills_all_rivals() -> None:
    assert tuple(gen.schedule_profile(0, i) for i in range(4)) == gen.SCHEDULE_PROFILES
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(4401, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            qgrid = gen.generate(4401, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": qgrid, "output": gen.rule_mirror(qgrid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_crossing_and_off_axis_shortcut_killers() -> None:
    crossing = gen.generate(
        91,
        0,
        difficulty="hard",
        layout="mixed_crossing",
        decoy_kind="none",
        bar_count=3,
    )
    assert gen._has_crossing(crossing)
    assert gen.rule_mirror(crossing) != gen._rival_vertical_over_horizontal(crossing)

    off_axis = gen.generate(
        92,
        0,
        difficulty="hard",
        layout="mixed_separate",
        decoy_kind="off_axis_pair",
        bar_count=2,
    )
    assert gen._has_off_axis_decoy(off_axis)
    assert gen.rule_mirror(off_axis) != gen._rival_fill_any_same_color_bbox(off_axis)


def test_self_check_rejects_targeted_impostors_and_mutations() -> None:
    all_background = [[0] * 10 for _ in range(10)]
    full_one_color = [[8] * 10 for _ in range(10)]
    short_line = [[0] * 10 for _ in range(10)]
    short_line[1][1:3] = [8, 8]
    solid_2x2 = [[0] * 10 for _ in range(10)]
    for r in (1, 2):
        for c in (1, 2):
            solid_2x2[r][c] = 8
    off_axis_only = copy.deepcopy(solid_2x2)
    for r in (6, 7):
        for c in (7, 8):
            off_axis_only[r][c] = 8
    for name, grid in {
        "all_background": all_background,
        "full_one_color": full_one_color,
        "short_line": short_line,
        "solid_2x2": solid_2x2,
        "off_axis_only": off_axis_only,
    }.items():
        assert gen.self_check(grid), name

    valid = gen.generate(51, 1)
    broken = copy.deepcopy(valid)
    color, row, col = gen._solid_blocks(broken)[0]
    assert color != 0
    broken[row][col] = 0
    assert gen.self_check(broken)


def test_negative_recombination_rejected_but_oracle_remains_defined() -> None:
    grid = gen.generate(1337, 0, layout="mixed_crossing", decoy_kind="off_axis_pair")
    mutated = copy.deepcopy(grid)
    _color, row, col = gen._solid_blocks(mutated)[0]
    mutated[row][col] = 0
    assert gen.self_check(mutated)
    output = gen.rule_mirror(mutated)
    assert len(output) == len(mutated)
    assert len(output[0]) == len(mutated[0])
