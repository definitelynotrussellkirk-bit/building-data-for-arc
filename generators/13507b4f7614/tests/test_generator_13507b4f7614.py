"""Focused regressions for the rectangle-to-center-cross generator."""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "13507b4f7614"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _labeled(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_axes_assignment_is_a_static_literal_for_repository_lint():
    tree = ast.parse(GENERATOR_PATH.read_text())
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    ]
    assert len(assignments) == 1
    assert ast.literal_eval(assignments[0].value) == GEN.AXES


def test_rule_pin_and_honest_public_surface():
    assert GEN.RULE_HASH == "812105731900"
    assert set(GEN.AXES) == {"grid_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "odd_two",
        "mixed_two",
        "odd_three",
        "mixed_three",
    )


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = _pairs()
    assert len(pairs) == 3
    shortcut = GEN.CANONICAL_SHORTCUTS["reduce_even_rectangles_too"]
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_grid_profile_is_exact_constructive_and_observable(band):
    for index, profile in enumerate(GEN.GRID_PROFILES):
        grid = GEN.generate(7100 + index, index, difficulty=band, grid_profile=profile)
        assert GEN.self_check(grid, meta={"overrides": {"grid_profile": profile}}) == []
        assert GEN.observe_overrides(grid) == {"grid_profile": profile}
        assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"texture": "hollow_rect"},
        {"n_rects": 3},
        {"palette_kind": "warm"},
        {"grid_profile": "unknown"},
        {"grid_profile": 3},
        {"unknown_axis": 1},
    ],
)
def test_invalid_or_retired_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty="medium", **kwargs)


def test_schedule_teaches_the_even_dimension_branch_under_every_rotation():
    rival = GEN.LESSON_COMPETITORS["reduce_even_rectangles_too"]
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            lesson = [
                _labeled(GEN.generate(8100 + start, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            assert {
                GEN.schedule_profile(0, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            } == set(GEN.SCHEDULE_PROFILES)
            for query_index, query in enumerate(lesson):
                demos = [item for index, item in enumerate(lesson) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                assert any(rival(item["input"]) != item["output"] for item in demos)


def test_even_witness_is_a_real_counterexample_to_the_named_rival():
    witness = GEN.SEMANTIC_WITNESSES["even_rectangle_unchanged"]
    rival = GEN.SEMANTIC_RIVALS["reduce_even_rectangles_too"]
    hits = 0
    for index in range(20):
        grid = GEN.generate(9100, index, difficulty="hard")
        if witness(grid):
            hits += 1
            assert rival(grid) != GEN.rule_mirror(grid)
    assert hits >= 10


def test_self_check_rejects_structural_impostors_from_the_retained_audit():
    grid = GEN.generate(17, 2, difficulty="medium", grid_profile="canonical_11x11")
    assert GEN.self_check(grid) == []

    blank = [[0] * 11 for _ in range(11)]
    assert GEN.self_check(blank)

    hollow = [[0] * 11 for _ in range(11)]
    for col in range(2, 7):
        hollow[2][col] = 4
        hollow[6][col] = 4
    for row in range(2, 7):
        hollow[row][2] = 4
        hollow[row][6] = 4
    assert GEN.self_check(hollow)

    bad_palette = deepcopy(grid)
    bad_palette[0][0] = 8
    assert GEN.self_check(bad_palette)

    punctured = deepcopy(grid)
    changed = False
    for row in range(1, len(punctured) - 1):
        for col in range(1, len(punctured[0]) - 1):
            if punctured[row][col] == 4:
                punctured[row][col] = 0
                changed = True
                break
        if changed:
            break
    assert changed and GEN.self_check(punctured)


def test_pinned_profile_floor_has_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    total = 0
    per_band = {}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            hits += _profile(grid) in canonical_profiles
        per_band[band] = hits
        total += hits
    assert all(hits > 0 for hits in per_band.values()), per_band
    assert total >= 15


def test_defaults_cover_all_scene_profiles_and_are_deterministic_fresh_and_rng_pure():
    random.seed(20261008)
    state = random.getstate()
    seen = set()
    for index in range(24):
        first = GEN.generate(444, index, difficulty="medium")
        assert random.getstate() == state
        second = GEN.generate(444, index, difficulty="medium")
        assert first == second
        assert first is not second
        assert all(left is not right for left, right in zip(first, second))
        assert GEN.self_check(first) == []
        seen.add(GEN.schedule_profile(444, index, difficulty="medium"))
    assert seen == set(GEN.SCHEDULE_PROFILES)


def test_task_local_qualification_probe_covers_the_declared_contract():
    probe_path = HOME / "workspace" / "qualification_probe.py"
    assert probe_path.is_file()
    spec = importlib.util.spec_from_file_location(
        f"qualification_probe_{TASK_ID}", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.qualify(per_band=8, generator_path=GENERATOR_PATH)
    assert report["errors"] == []
    assert report["canonical_shortcuts"]["reduce_even_rectangles_too"] == {
        "matches": 3,
        "pairs": 3,
        "fits_all": True,
    }
    assert report["rotations"]["checked"] == 48
    assert report["rotations"]["failures"] == []
    assert report["exact_overrides"]["failures"] == []
    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert set(row["scene_counts"]) == set(GEN.SCHEDULE_PROFILES)
        assert row["self_check_failures"] == []
        assert row["witness_hits"]["even_rectangle_unchanged"] > 0
