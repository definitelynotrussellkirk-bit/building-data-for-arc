"""Focused regression tests for generator ebdf2e943f3f."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import random

import pytest

from puzzle_generators.per_puzzle.ebdf2e943f3f import generator as gen
from reviewer_support import canonical_pairs, find_root


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _canonical_inputs():
    return [pair["input"] for pair in _canonical_pairs()]


def test_canonical_inputs_are_accepted_and_outputs_match():
    for grid in _canonical_inputs():
        original = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        output = gen.rule_mirror(grid)
        assert grid == original
        assert sum(a != b for ra, rb in zip(grid, output) for a, b in zip(ra, rb)) == 2


def test_exact_boundary_overrides_are_realized():
    cases = (
        {"grid_h": 5, "grid_w": 6, "n_blocks": 4},
        {"grid_h": 14, "grid_w": 16, "n_blocks": 2},
        {"grid_h": 5, "grid_w": 16, "n_blocks": 3},
        {"grid_h": 14, "grid_w": 6, "n_blocks": 4},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, 33 + index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
        output = gen.rule_mirror(grid)
        assert sum(a != b for ra, rb in zip(grid, output) for a, b in zip(ra, rb)) == overrides["n_blocks"]


def test_self_check_rejects_targeted_impostors():
    blank = [[0] * 6 for _ in range(5)]

    full_square = [[0] * 6 for _ in range(5)]
    for row in (1, 2):
        for col in (1, 2):
            full_square[row][col] = 4

    two_corners = [[0] * 6 for _ in range(5)]
    two_corners[1][1] = 4
    two_corners[2][2] = 4

    mixed_colour_l = [[0] * 6 for _ in range(5)]
    mixed_colour_l[1][1] = 2
    mixed_colour_l[1][2] = 2
    mixed_colour_l[2][1] = 3

    stray_pixel = gen.generate(77, 9, difficulty="easy", grid_h=5, grid_w=6, n_blocks=2)
    for row in range(5):
        for col in range(6):
            if stray_pixel[row][col] == 0:
                stray_pixel[row][col] = 9
                break
        else:
            continue
        break

    for impostor in (blank, full_square, two_corners, mixed_colour_l, stray_pixel):
        assert gen.self_check(impostor), impostor


def test_four_demo_schedule_is_lesson_identifiable():
    demos = []
    for sample_index in range(4):
        grid = gen.generate(1234, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(1234, 4, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}) == []


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(481516)
    state = random.getstate()
    first = gen.generate(11, 29, difficulty="easy")
    assert random.getstate() == state
    second = gen.generate(11, 29, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_unknown_or_retired_axis_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, palette_size=9)


def test_isolated_l_shortcut_fits_every_canonical_pair():
    rival = gen.CANONICAL_SHORTCUTS["isolated_l_components_only"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_connected_pair_schedule_refutes_isolated_l_shortcut(band):
    grid = gen.generate(
        812,
        2,
        difficulty=band,
        grid_h=5,
        grid_w=6,
        n_blocks=4,
    )
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["connected_same_colour_windows"](grid)
    intended = gen.rule_mirror(grid)
    rival = gen.SEMANTIC_RIVALS["isolated_l_components_only"](grid)
    assert intended != rival
    assert sum(
        left != right
        for intended_row, rival_row in zip(intended, rival)
        for left, right in zip(intended_row, rival_row)
    ) == 2


def _separate_connected_pair(grid):
    changed = copy.deepcopy(grid)
    windows = gen._qualifying_windows(changed)
    for left_index, left in enumerate(windows):
        for right in windows[left_index + 1 :]:
            if left["color"] != right["color"]:
                continue
            if not any(
                abs(lrow - rrow) + abs(lcol - rcol) == 1
                for lrow, lcol in left["painted_cells"]
                for rrow, rcol in right["painted_cells"]
            ):
                continue
            replacement = 9 if right["color"] != 9 else 8
            for row, col in right["painted_cells"]:
                changed[row][col] = replacement
            assert gen.self_check(changed) == []
            return changed
    raise AssertionError("connected pair not found")


def test_lesson_contract_requires_a_counterexample_to_the_isolated_l_shortcut():
    demos = []
    for sample_index in range(4):
        grid = gen.generate(
            1234,
            sample_index,
            difficulty="medium",
            grid_h=5,
            grid_w=6,
            n_blocks=4,
        )
        if gen.SEMANTIC_WITNESSES["connected_same_colour_windows"](grid):
            grid = _separate_connected_pair(grid)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})

    query_grid = gen.generate(1234, 4, difficulty="medium")
    reasons = gen.lesson_identifiable(
        demos,
        {"input": query_grid, "output": gen.rule_mirror(query_grid)},
    )
    assert any("isolated" in reason.lower() for reason in reasons)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_every_five_pair_bundle_survives_every_query_rotation(band, start):
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(
            2468,
            sample_index,
            difficulty=band,
            grid_h=5,
            grid_w=6,
            n_blocks=4,
        )
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    witness = gen.SEMANTIC_WITNESSES["connected_same_colour_windows"]
    assert sum(witness(pair["input"]) for pair in pairs) >= 2

    rival = gen.LESSON_COMPETITORS["isolated_l_components_only"]
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_default_sampler_lessons_survive_every_query_rotation(band, start):
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(0, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def _load_shortcut_probe():
    test_path = Path(__file__).resolve()
    candidates = [
        test_path.parents[1] / "workspace" / "shortcut_probe.py",
        *(
            parent / "generators" / gen.TASK_ID / "workspace" / "shortcut_probe.py"
            for parent in test_path.parents
        ),
    ]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    assert path is not None, candidates
    spec = importlib.util.spec_from_file_location("ebdf2e943f3f_shortcut_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_shortcut_probe_checks_declared_rivals_and_all_query_rotations():
    probe = _load_shortcut_probe()
    report = probe.build_report(
        gen,
        canonical_pairs=_canonical_pairs(),
        seeds=(2468,),
        starts=range(8),
        bands=(None, "easy", "medium", "hard"),
    )
    assert report["status"] == "pass"
    assert set(report["canonical_shortcuts"]) == set(gen.CANONICAL_SHORTCUTS)
    assert all(
        row["status"] == "fits_all"
        for row in report["canonical_shortcuts"].values()
    )
    assert report["schedule"]["bundles_checked"] == 32
    assert report["schedule"]["rotation_failures"] == []
    assert report["schedule"]["minimum_witnesses_per_bundle"] >= 2
    witness = report["first_counterexample"]["isolated_l_components_only"]
    assert witness["differing_cells"]


def test_non_rival_witnesses_are_declared_as_branch_coverage():
    assert set(gen.BRANCH_WITNESSES) == (
        set(gen.SEMANTIC_WITNESSES) - set(gen.WITNESS_RIVALS)
    )
