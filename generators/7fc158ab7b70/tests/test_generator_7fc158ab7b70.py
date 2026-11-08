from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

TASK_ID = "7fc158ab7b70"
REPO = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "shared/data/canonical/puzzles.jsonl").exists()
)
_SPEC = importlib.util.spec_from_file_location(
    f"generator_{TASK_ID}", REPO / "generators" / TASK_ID / "generator.py"
)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _canonical_row():
    return next(
        json.loads(line)
        for line in (REPO / "shared/data/canonical/puzzles.jsonl")
        .read_text()
        .splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def test_rule_hash_and_rule_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "d959c287782b"
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_selected_racket_authority_text_is_exactly_synchronized():
    canonical_row = _canonical_row()
    authority = json.loads(
        (REPO / "shared/data/base/solutions/training/"
         "ac0a08a4__7fc158ab7b70.json").read_text()
    )
    assert authority["racket_target"]["target_code"] == canonical_row["program_solution"]


def test_every_declared_exact_override_combination_round_trips():
    sample_index = 0
    for grid_n in range(3, 6):
        for n_cells in range(2, 7):
            for unique_colors in (False, True):
                for anchor_origin in (False, True):
                    grid = GEN.generate(
                        1701,
                        sample_index,
                        difficulty="hard",
                        grid_n=grid_n,
                        n_cells=n_cells,
                        unique_colors=unique_colors,
                        anchor_origin=anchor_origin,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "grid_n": grid_n,
                        "n_cells": n_cells,
                        "unique_colors": unique_colors,
                        "anchor_origin": anchor_origin,
                    }
                    sample_index += 1


def test_duplicate_color_counterexample_is_lawful_and_refutes_distinct_color_scale():
    grid = [[4, 4, 0], [0, 6, 0], [0, 0, 6]]
    assert GEN.self_check(grid) == []
    expected = GEN.rule_mirror(grid)
    shortcut = GEN.CANONICAL_SHORTCUTS["distinct_nonzero_colors"](grid)
    assert len(expected) == len(expected[0]) == 12
    assert len(shortcut) == len(shortcut[0]) == 6
    assert shortcut != expected
    assert GEN.SEMANTIC_WITNESSES["repeated_nonzero_color"](grid)


def test_every_three_demo_default_window_refutes_the_named_shortcut():
    for difficulty in ("easy", "medium", "hard"):
        for seed in (3, 41, 991):
            for start in (0, 1, 2, 17):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                    demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
                query_grid = GEN.generate(
                    seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {
                    "input": query_grid,
                    "output": GEN.rule_mirror(query_grid),
                }
                assert GEN.lesson_identifiable(demos, query) == []
                assert any(
                    GEN.SEMANTIC_WITNESSES["repeated_nonzero_color"](
                        demo["input"]
                    )
                    for demo in demos
                )
                for rival in GEN.SEMANTIC_RIVALS.values():
                    assert any(
                        rival(demo["input"]) != demo["output"]
                        for demo in demos
                    )


def test_each_band_covers_all_sizes_and_canonical_scale():
    for difficulty in ("easy", "medium", "hard"):
        sizes = {
            len(GEN.generate(812, sample_index, difficulty=difficulty))
            for sample_index in range(12)
        }
        assert sizes == {3, 4, 5}


def test_invalid_or_unknown_overrides_reject_loudly():
    invalid_calls = (
        {"difficulty": "extreme"},
        {"grid_n": 2},
        {"grid_n": 6},
        {"n_cells": 1},
        {"n_cells": 7},
        {"unique_colors": 1},
        {"anchor_origin": 0},
        {"unknown_axis": "typo"},
    )
    for kwargs in invalid_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **kwargs)


def test_determinism_fresh_returns_and_global_rng_is_untouched():
    random.seed(12345)
    state = random.getstate()
    first = GEN.generate(17, 23, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(17, 23, difficulty="medium")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_malformed_or_out_of_domain_inputs():
    bad = (
        [],
        [[0, 0], [0]],
        [[1, 0], [0, 2]],
        [[0] * 6 for _ in range(6)],
        [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 2, 3], [4, 5, 6], [7, 0, 0]],
        [[10, 1, 0], [0, 2, 0], [0, 0, 0]],
    )
    for grid in bad:
        assert GEN.self_check(grid), grid


def test_monochrome_minimal_impostors_are_excluded_but_two_cell_repeat_is_spread():
    short_line = [[0, 0, 0], [4, 4, 4], [0, 0, 0]]
    solid_2x2 = [[4, 4, 0], [4, 4, 0], [0, 0, 0]]
    assert GEN.self_check(short_line)
    assert GEN.self_check(solid_2x2)

    for anchor_origin in (False, True):
        grid = GEN.generate(
            77,
            4,
            grid_n=3,
            n_cells=2,
            unique_colors=False,
            anchor_origin=anchor_origin,
        )
        assert GEN.self_check(grid) == []
        cells = [
            (row, col)
            for row in range(3)
            for col in range(3)
            if grid[row][col] != 0
        ]
        assert len({grid[row][col] for row, col in cells}) == 1
        assert abs(cells[0][0] - cells[1][0]) + abs(cells[0][1] - cells[1][1]) > 1


def test_distribution_qualification_probe_uses_declared_rivals_and_cyclic_lessons():
    probe_path = (
        REPO / "generators" / TASK_ID / "workspace" / "qualify_distribution.py"
    )
    spec = importlib.util.spec_from_file_location(
        f"qualify_distribution_{TASK_ID}", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(lessons_per_band=6, base_seed=91000)
    assert report["generator_sha256"] == probe.source_sha256()
    assert report["lesson_assembly"]["cyclic_start_residues"] == [0, 1, 2]
    assert set(report["canonical_shortcuts_fit_canonical"]) == set(
        GEN.CANONICAL_SHORTCUTS
    )
    assert all(report["canonical_shortcuts_fit_canonical"].values())
    for band in ("easy", "medium", "hard"):
        assert report["bands"][band]["lessons_checked"] == 6
        assert report["bands"][band]["identifiable_lessons"] == 6
        assert report["bands"][band]["failures"] == []


def test_every_rolling_nine_sample_window_crosses_size_with_color_uniqueness():
    expected = {
        (grid_n, unique_colors)
        for grid_n in (3, 4, 5)
        for unique_colors in (False, True)
    }
    for difficulty in ("easy", "medium", "hard"):
        for start in range(9):
            observed = {
                (
                    axes["grid_n"],
                    axes["unique_colors"],
                )
                for sample_index in range(start, start + 9)
                for axes in [
                    GEN.observe_overrides(
                        GEN.generate(1701, sample_index, difficulty=difficulty)
                    )
                ]
            }
            assert observed == expected


def test_distribution_probe_reports_complete_size_by_uniqueness_joint_coverage():
    probe_path = (
        REPO / "generators" / TASK_ID / "workspace" / "qualify_distribution.py"
    )
    spec = importlib.util.spec_from_file_location(
        f"qualify_distribution_joint_{TASK_ID}", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(lessons_per_band=9, base_seed=93000)
    for band in ("easy", "medium", "hard"):
        coverage = report["bands"][band].get("grid_n_x_unique_colors")
        assert coverage is not None
        assert coverage["missing"] == []
        assert len(coverage["observed"]) == 6
