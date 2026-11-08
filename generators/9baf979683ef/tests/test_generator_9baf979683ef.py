from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9baf979683ef"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _demo(grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _source_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    divider = next(
        col
        for col in range(len(grid[0]))
        if all(row[col] == 5 for row in grid)
    )
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values[:divider])
        if value not in (0, 5)
    ]


def test_rule_pin_and_python_oracle_match_every_canonical_pair():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "1fce392f92a1"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_axes_round_trip_and_unknown_keys_fail_loudly():
    expected_axes = {
        "profile_kind",
        "divider_side",
        "source_scale",
        "source_palette",
        "layout_kind",
    }
    assert set(GEN.AXES) == expected_axes

    values = {
        "profile_kind": tuple(GEN.PROFILE_SHAPES),
        "divider_side": ("left", "right"),
        "source_scale": ("six", "seven", "eight"),
        "source_palette": ("mono", "two", "three", "four"),
        "layout_kind": ("connected", "scattered", "mixed"),
    }
    for difficulty in ("easy", "medium", "hard"):
        for axis, axis_values in values.items():
            for index, value in enumerate(axis_values):
                grid = GEN.generate(
                    1100 + index,
                    index,
                    difficulty=difficulty,
                    **{axis: value},
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid)[axis] == value

        combined = {
            "profile_kind": "canonical_8x9",
            "divider_side": "right",
            "source_scale": "eight",
            "source_palette": "four",
            "layout_kind": "mixed",
        }
        grid = GEN.generate(1300, 19, difficulty=difficulty, **combined)
        assert GEN.observe_overrides(grid) == combined

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="left")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, profile_kind="not-a-profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_default_distribution_has_canonical_anchors_and_counterexamples_in_every_band():
    canonical_profiles = {(7, 11, 4), (8, 9, 4), (7, 13, 4)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(7000 + index, index, difficulty=difficulty)
            for index in range(60)
        ]
        observations = [GEN.observe_overrides(grid) for grid in grids]

        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert set(obs["divider_side"] for obs in observations) == {"left", "right"}
        assert set(obs["source_scale"] for obs in observations) == {"six", "seven", "eight"}
        assert set(obs["source_palette"] for obs in observations) == {
            "mono",
            "two",
            "three",
            "four",
        }
        assert set(obs["layout_kind"] for obs in observations) == {
            "connected",
            "scattered",
            "mixed",
        }
        assert set(obs["profile_kind"] for obs in observations) == set(GEN.PROFILE_SHAPES)

        realized_profiles = {
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        }
        assert realized_profiles & canonical_profiles

        for grid in grids:
            divider = next(
                col
                for col in range(len(grid[0]))
                if all(row[col] == 5 for row in grid)
            )
            sources = _source_cells(grid)
            assert divider != len(grid[0]) // 2
            assert len(sources) in (6, 7, 8)
            assert len({col for _, col, _ in sources}) >= 2

        assert len({tuple(map(tuple, grid)) for grid in grids}) >= 55


def test_canonical_shortcuts_fit_public_pairs_but_every_generated_scene_refutes_them():
    pairs = _pairs()
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "mirror_about_geometric_midpoint",
        "mirror_only_first_five_sources",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = GEN.generate(8800, sample_index, difficulty=difficulty)
            truth = GEN.rule_mirror(grid)
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                assert rival(grid) != truth, (difficulty, sample_index, name)


def test_each_sliding_lesson_window_is_identifiable_and_rivals_are_named():
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.CANONICAL_SHORTCUTS)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                GEN.generate(9900 + start, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [_demo(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = {"input": grids[-1]}
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_witnesses_fire_and_named_rivals_disagree():
    grids = [GEN.generate(4200, index, difficulty="medium") for index in range(24)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        matching = [grid for grid in grids if witness(grid)]
        assert matching, witness_name
        for grid in matching[:3]:
            truth = GEN.rule_mirror(grid)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(777, 13, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(777, 13, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 9
    assert first != second


def test_self_check_rejects_nearest_structural_mutations():
    valid = GEN.generate(222, 4, difficulty="medium")
    mutations: list[list[list[int]]] = []

    no_divider = copy.deepcopy(valid)
    divider = next(
        col
        for col in range(len(valid[0]))
        if all(row[col] == 5 for row in valid)
    )
    no_divider[0][divider] = 0
    mutations.append(no_divider)

    right_source = copy.deepcopy(valid)
    source_row, source_col, source_value = _source_cells(valid)[0]
    right_source[source_row][2 * divider - source_col] = source_value
    mutations.append(right_source)

    stray_five = copy.deepcopy(valid)
    stray_five[0][0] = 5
    mutations.append(stray_five)

    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    mutations.append(ragged)

    bad_value = copy.deepcopy(valid)
    bad_value[0][0] = 10
    mutations.append(bad_value)

    boolean_value = copy.deepcopy(valid)
    boolean_value[0][0] = True
    mutations.append(boolean_value)

    for grid in mutations:
        assert GEN.self_check(grid), grid


def test_workspace_audit_probe_reports_distribution_and_cyclic_lessons():
    audit_path = ROOT / "generators" / TASK_ID / "workspace" / "audit_distribution.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", audit_path)
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)

    report = audit.run_audit(per_band=6, cyclic_windows=2)
    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"]
    assert report["canonical_shortcuts"] == {
        "mirror_about_geometric_midpoint": {"pairs": 3, "fits": 3, "status": "fits_all"},
        "mirror_only_first_five_sources": {"pairs": 3, "fits": 3, "status": "fits_all"},
    }
    assert all(band["invalid"] == 0 for band in report["bands"].values())
    assert all(band["strict_rejections"] == 0 for band in report["bands"].values())
    assert report["cyclic_lessons"]["rotations_tested"] == 24
    assert report["cyclic_lessons"]["ambiguous"] == 0
