from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK = "cae2423a6477"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK}", REPO / "generators" / TASK / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(ch) for ch in row] for row in rows]


def canonical_pairs() -> list[dict]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK:
                continue
            test = row["test"]
            pairs = list(row["train"]) + ([test] if isinstance(test, dict) else list(test))
            return [
                {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                for pair in pairs
            ]
    raise AssertionError("canonical task row missing")


def test_metadata_and_single_honest_axis_contract():
    assert GEN.RULE_HASH == "1f6f97325987"
    assert GEN.VERSION == "3.1.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCENE_PROFILES) == (
        "canonical_small",
        "large_open",
        "hollow_irregular",
    )
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.AXES["scene_profile"]["valid"] == "|".join(GEN.SCENE_PROFILES)


def test_every_canonical_pair_is_accepted_and_mirror_exact():
    for pair in canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_three_demo_window_covers_every_profile(band):
    for start in (0, 11, 22, 37):
        grids = [GEN.generate(700 + start, start + i, difficulty=band) for i in range(3)]
        assert {GEN.observe_overrides(grid)["scene_profile"] for grid in grids} == set(
            GEN.SCENE_PROFILES
        )
        assert all(GEN.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile", ["canonical_small", "large_open", "hollow_irregular"]
)
def test_profile_override_is_exact_observable_and_semantically_distinct(band, profile):
    for seed in range(8):
        grid = GEN.generate(seed, seed * 13 + 2, difficulty=band, scene_profile=profile)
        analysis = GEN.analyze_grid(grid)
        assert GEN.self_check(grid, difficulty=band, meta={"scene_profile": profile}) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["exact_frame_count"] >= 1
        assert analysis["nonframe_count"] >= 1
        assert GEN.rule_mirror(grid) != grid
        assert any(3 in row for row in GEN.rule_mirror(grid))

        if profile == "canonical_small":
            assert analysis["hollow_nonframe_count"] == 0
            assert analysis["large_nonframe_count"] == 0
        elif profile == "large_open":
            assert analysis["large_nonframe_count"] >= 1
            assert analysis["hollow_nonframe_count"] == 0
            assert GEN.SEMANTIC_RIVALS["size_at_least_8"](grid) != GEN.rule_mirror(grid)
            assert GEN.SEMANTIC_RIVALS["bbox_at_least_3x3"](grid) != GEN.rule_mirror(grid)
        else:
            assert analysis["hollow_nonframe_count"] >= 2
            assert analysis["hollow_irregular_count"] == 1
            assert analysis["nubbed_rectangular_hole_count"] == 1
            assert analysis["closed_unbranched_nonframe_count"] >= 1
            assert analysis["rectangular_hole_nonframe_count"] >= 1
            assert GEN.SEMANTIC_RIVALS["any_object_with_hole"](grid) != GEN.rule_mirror(grid)
            assert (
                GEN.SEMANTIC_RIVALS["closed_unbranched_loop"](grid)
                != GEN.rule_mirror(grid)
            )
            assert (
                GEN.SEMANTIC_RIVALS["rectangular_hole"](grid)
                != GEN.rule_mirror(grid)
            )


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, texture="noise")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not-a-profile")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(9182)
    before = random.getstate()
    first = GEN.generate(77, 9, difficulty="hard", scene_profile="hollow_irregular")
    assert random.getstate() == before
    second = GEN.generate(77, 9, difficulty="hard", scene_profile="hollow_irregular")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(77, 9, difficulty="hard", scene_profile="hollow_irregular") == second


def test_self_check_rejects_structural_impostors():
    base = GEN.generate(314, 7, difficulty="medium", scene_profile="hollow_irregular")

    blank = [[0 for _ in row] for row in base]

    absent_target_color = copy.deepcopy(base)
    absent_target_color[0][0] = 8

    no_negative_branch = GEN.rule_mirror(base)
    no_negative_branch = [[7 if value == 3 else value for value in row] for row in no_negative_branch]

    split_row = copy.deepcopy(base)
    split_row.insert(len(split_row) // 2, list(split_row[len(split_row) // 2]))

    for impostor in (blank, absent_target_color, no_negative_branch, split_row):
        assert GEN.self_check(impostor)


def test_lesson_identifiable_rejects_each_declared_competitor():
    seed = 808
    demos = []
    for sample_index in range(3):
        inp = GEN.generate(seed, sample_index, difficulty="medium")
        demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
    query = GEN.generate(seed, 3, difficulty="medium")
    assert GEN.lesson_identifiable(demos, {"input": query, "output": GEN.rule_mirror(query)}) == []
    for name, competitor in GEN.LESSON_COMPETITORS.items():
        assert any(competitor(demo["input"]) != demo["output"] for demo in demos), name


def test_closed_unbranched_loop_shortcut_is_canonical_but_refuted_by_lessons():
    """A non-rectangular simple loop must stay green.

    The public examples alone cannot distinguish exact rectangular frames from
    arbitrary closed, unbranched one-cell-wide loops.  The generated curriculum
    therefore needs an explicit witness against that plausible rival.
    """

    rival = GEN.SEMANTIC_RIVALS["closed_unbranched_loop"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            demos = []
            for sample_index in range(GEN.EXAMPLES_NEEDED):
                inp = GEN.generate(seed, sample_index, difficulty=band)
                demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
            assert any(rival(demo["input"]) != demo["output"] for demo in demos)


def test_self_check_rejects_first_row_copied_over_last_row():
    applicable = 0
    rejected = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            grid = GEN.generate(seed, seed, difficulty=band)
            if grid[0] == grid[-1]:
                continue
            applicable += 1
            mutated = copy.deepcopy(grid)
            mutated[-1] = list(mutated[0])
            rejected += bool(GEN.self_check(mutated, difficulty=band))

    # Some destructive edits map one supported tiny decoy to another (for
    # example, a 2x2 block to a domino), so universal rejection is impossible
    # without rejecting valid inputs.  Measure a broad deterministic sample
    # instead of relying on five seeds to happen to touch a populated edge.
    assert applicable >= 60
    assert rejected * 10 >= applicable * 9


def test_rectangular_hole_shortcut_is_canonical_but_refuted_by_lessons():
    """A non-frame may enclose a rectangular hole and must stay green.

    The public examples alone cannot distinguish exact rectangular frames from
    arbitrary objects whose enclosed background component is rectangular.  A
    generated lesson therefore needs an explicit witness against that rival.
    """

    rival = GEN.SEMANTIC_RIVALS["rectangular_hole"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            demos = []
            for sample_index in range(GEN.EXAMPLES_NEEDED):
                inp = GEN.generate(seed, sample_index, difficulty=band)
                demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
            assert any(rival(demo["input"]) != demo["output"] for demo in demos)
