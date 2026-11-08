from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "f06d31332595"
LIBRARY = next(
    path for path in Path(__file__).resolve().parents
    if (path / "shared/runtime").is_dir()
)
sys.path.insert(0, str(LIBRARY / "shared/runtime"))
spec = importlib.util.spec_from_file_location(
    "review_f06d31332595", LIBRARY / "generators" / TASK_ID / "generator.py"
)
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MODULE)
CANONICAL = LIBRARY / "shared/data/canonical/puzzles.jsonl"


def _canonical_pairs():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_and_python_mirror_matches_every_canonical_pair():
    assert getattr(MODULE, "RULE_HASH", None) == "2739381bfcfd"
    mirror = getattr(MODULE, "rule_mirror", None)
    assert callable(mirror)
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert mirror(source) == pair["output"]
        assert source == before


def test_axis_surface_is_small_exact_and_observable_at_both_boundaries():
    assert set(MODULE.AXES) == {"grid_h", "panel_w", "extra_right", "palette_size"}
    observer = getattr(MODULE, "observe_overrides", None)
    assert callable(observer)
    for overrides in (
        {"grid_h": 6, "panel_w": 3, "extra_right": 0, "palette_size": 2},
        {"grid_h": 16, "panel_w": 8, "extra_right": 3, "palette_size": 6},
    ):
        grid = MODULE.generate(13, 29, difficulty="hard", **overrides)
        assert MODULE.self_check(grid) == []
        assert observer(grid) == overrides


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8128)
    state = random.getstate()
    first = MODULE.generate(91, 17, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(91, 17, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == MODULE.generate(91, 17, difficulty="medium")


def test_schedule_has_one_anchor_and_two_connected_profiles_per_three_examples():
    assert MODULE.EXAMPLES_NEEDED == 3
    assert set(MODULE.SCHEDULE_PROFILES) == {
        "canonical_anchor",
        "connected_centered",
        "connected_offcenter",
    }
    for start in range(12):
        profiles = [
            MODULE.schedule_profile(7000, start + offset, "medium")
            for offset in range(MODULE.EXAMPLES_NEEDED)
        ]
        assert set(profiles) == set(MODULE.SCHEDULE_PROFILES)


def test_default_profiles_have_their_declared_structural_witnesses():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            profile = MODULE.schedule_profile(8000, sample_index, band)
            grid = MODULE.generate(8000, sample_index, difficulty=band)
            facts = MODULE.semantic_observables(grid)
            assert MODULE.self_check(grid) == []
            assert facts["right_nonzero"] == 0
            assert facts["has_far_edge_mark"]
            assert facts["mark_rows"] >= 2
            assert facts["mark_columns"] >= 2
            if profile == "canonical_anchor":
                assert MODULE.strict_canonical_like(grid)
                assert facts["extra_right"] == 0
                assert not facts["has_connected_source"]
            else:
                assert facts["has_connected_source"]
                if profile == "connected_centered":
                    assert facts["extra_right"] == 0
                else:
                    assert 1 <= facts["extra_right"] <= 3


def test_canonical_anchors_supply_exact_profiles_in_every_difficulty_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({cell for row in pair["input"] for cell in row}))
        for pair in _canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        profiles = []
        for sample_index in range(30):
            grid = MODULE.generate(20_000, sample_index, difficulty=band)
            if MODULE.schedule_profile(20_000, sample_index, band) == "canonical_anchor":
                profiles.append((
                    len(grid), len(grid[0]),
                    len({cell for row in grid for cell in row}),
                ))
        assert profiles
        assert set(profiles) <= canonical_profiles


def test_general_distribution_realizes_all_palette_sizes_and_many_shapes():
    grids = [
        MODULE.generate(30_000 + seed, seed * 17 + 2, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(40)
    ]
    facts = [MODULE.semantic_observables(grid) for grid in grids]
    assert {_freeze(grid) for grid in grids}.__len__() == len(grids)
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 12
    assert {item["palette_size"] for item in facts} == {2, 3, 4, 5, 6}
    assert sum(item["extra_right"] > 0 for item in facts) >= 30
    assert sum(item["has_connected_source"] for item in facts) >= 60


def test_self_check_rejects_structural_impostors_but_accepts_offcenter_validity():
    valid = MODULE.generate(
        404, 5, difficulty="medium",
        grid_h=9, panel_w=5, extra_right=2, palette_size=4,
    )
    assert MODULE.self_check(valid) == []
    facts = MODULE.semantic_observables(valid)
    divider = facts["panel_w"]

    no_divider = copy.deepcopy(valid)
    for row in no_divider:
        row[divider] = 0

    right_contaminated = copy.deepcopy(valid)
    right_contaminated[0][divider + 1] = 9

    extra_gray = copy.deepcopy(valid)
    target = next(
        (r, c)
        for r in range(len(valid))
        for c in range(divider)
        if valid[r][c] == 0
    )
    extra_gray[target[0]][target[1]] = 5

    truncated_right = [row[:-3] for row in valid]

    for impostor in (no_divider, right_contaminated, extra_gray, truncated_right):
        assert MODULE.self_check(impostor), impostor


def test_invalid_calls_reject_loudly():
    with pytest.raises(TypeError):
        MODULE.generate(0, 0, mystery_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="impossible")
    for name, value in (
        ("grid_h", 5),
        ("panel_w", 2),
        ("extra_right", 4),
        ("palette_size", 1),
    ):
        with pytest.raises(ValueError):
            MODULE.generate(0, 0, **{name: value})


def test_declared_shortcuts_fit_canonical_pairs_and_generated_witnesses_refute_them():
    expected = {"grid_center_axis", "isolated_markers_only"}
    assert set(MODULE.CANONICAL_SHORTCUTS) == expected
    for pair in _canonical_pairs():
        for rival in MODULE.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for start in range(18):
            grids = [
                MODULE.generate(40_000 + start, start + offset, difficulty=band)
                for offset in range(MODULE.EXAMPLES_NEEDED)
            ]
            for name, rival in MODULE.CANONICAL_SHORTCUTS.items():
                assert any(rival(grid) != MODULE.rule_mirror(grid) for grid in grids), (
                    band, start, name
                )


def test_semantic_witnesses_have_verified_named_rival_disagreements():
    assert set(MODULE.SEMANTIC_WITNESSES) == {
        "off_center_divider",
        "connected_source_motif",
    }
    assert set(MODULE.WITNESS_RIVALS) == set(MODULE.SEMANTIC_WITNESSES)
    for sample_index in range(18):
        grid = MODULE.generate(50_000, sample_index, difficulty="medium")
        truth = MODULE.rule_mirror(grid)
        profile = MODULE.schedule_profile(50_000, sample_index, "medium")
        for witness_name, witness in MODULE.SEMANTIC_WITNESSES.items():
            if witness(grid):
                assert any(
                    MODULE.SEMANTIC_RIVALS[name](grid) != truth
                    for name in MODULE.WITNESS_RIVALS[witness_name]
                ), (profile, witness_name)


def test_lesson_identifiable_names_query_changing_shortcuts():
    demos = _canonical_pairs()[:3]
    query_grid = MODULE.generate(60_000, 2, difficulty="easy")
    query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
    reasons = MODULE.lesson_identifiable(demos, query)
    for name in MODULE.CANONICAL_SHORTCUTS:
        assert any(name in reason for reason in reasons), (name, reasons)
