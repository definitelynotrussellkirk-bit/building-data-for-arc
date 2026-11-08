from __future__ import annotations

import copy
import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
TASK_HOME = REPO / "generators/24bb2221ca5c"
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location(
    "review_generator_24bb2221ca5c", TASK_HOME / "generator.py"
)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _canonical_row() -> dict:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"canonical row {gen.TASK_ID} not found")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _lesson_pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _closed_and_open_scene() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(8)]
    # Closed 5x5 color-3 frame.
    for c in range(1, 6):
        grid[1][c] = 3
        grid[5][c] = 3
    for r in range(1, 6):
        grid[r][1] = 3
        grid[r][5] = 3
    # Open 5x4 color-8 near-miss with one non-corner gap.
    for c in range(8, 12):
        grid[2][c] = 8
        grid[6][c] = 8
    for r in range(2, 7):
        grid[r][8] = 8
        grid[r][11] = 8
    grid[4][8] = 0
    return grid


def _corner_gap_scene() -> list[list[int]]:
    """A missing corner leaves a 4-connected hole but an 8-connected leak."""
    grid = [[0] * 9 for _ in range(8)]
    for col in range(2, 7):
        grid[1][col] = 8
        grid[5][col] = 8
    for row in range(1, 6):
        grid[row][2] = 8
        grid[row][6] = 8
    grid[1][2] = 0
    return grid


def _cavity_mass_same_color_scene() -> list[list[int]]:
    """A dense two-hole mass with an L-hole, plus a same-color ring."""
    grid = [[0] * 12 for _ in range(8)]
    for row in range(1, 5):
        for col in range(1, 6):
            grid[row][col] = 1
    # One singleton cavity and one L-shaped cavity.
    for row, col in ((2, 2), (2, 4), (3, 3), (3, 4)):
        grid[row][col] = 0
    grid[2][6] = 1  # outward spur expands the component bbox

    for col in range(8, 12):
        grid[1][col] = 1
        grid[4][col] = 1
    for row in range(1, 5):
        grid[row][8] = 1
        grid[row][11] = 1
    return grid


def _spurred_frame() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    for c in range(2, 7):
        grid[1][c] = 1
        grid[5][c] = 1
    for r in range(1, 6):
        grid[r][2] = 1
        grid[r][6] = 1
    grid[3][7] = 1
    return grid


def _multi_hole_same_color_scene() -> list[list[int]]:
    """Two same-color components; the left component has two holes and a spur."""
    grid = [[0] * 14 for _ in range(8)]

    # Left component: a 5x7 outer frame with an internal divider, making two
    # enclosed regions, plus one outward spur at (3, 8).
    for c in range(1, 8):
        grid[1][c] = 1
        grid[5][c] = 1
    for r in range(1, 6):
        grid[r][1] = 1
        grid[r][4] = 1
        grid[r][7] = 1
    grid[3][8] = 1

    # Right component: a separate closed 5x4 frame in the same color.  The
    # blank column between the components preserves the one-cell moat.
    for c in range(10, 14):
        grid[1][c] = 1
        grid[5][c] = 1
    for r in range(1, 6):
        grid[r][10] = 1
        grid[r][13] = 1
    return grid


def _same_color_rect_pair_scene() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(8)]
    for col0 in (1, 7):
        for col in range(col0, col0 + 3):
            grid[1][col] = 3
            grid[3][col] = 3
        for row in range(1, 4):
            grid[row][col0] = 3
            grid[row][col0 + 2] = 3
    return grid


def test_rule_pin_canonical_pairs_and_python_mirror_are_exact():
    assert gen.VERSION == "3.2.0"
    assert gen.RULE_HASH == "514c258ab731"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_three_profile_schedule_covers_every_consecutive_lesson_window():
    expected = {"canonical_pair", "gap_contrast", "topology_stress"}
    assert set(gen.SCHEDULE_PROFILES) == expected
    assert gen.EXAMPLES_NEEDED == 3
    for start in range(12):
        assert {
            gen.schedule_profile(2718, index, difficulty="hard")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        } == expected


def test_topology_stress_profile_guarantees_multi_hole_and_component_identity():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(2, 20, gen.EXAMPLES_NEEDED):
            grid = gen.generate(8128, sample_index, difficulty=difficulty)
            assert gen.schedule_profile(8128, sample_index, difficulty) == "topology_stress"
            assert gen.self_check(grid) == []

            components = gen._component_cells(grid)
            colors = [color for color, _ in components]
            assert len(components) == 2
            assert len(set(colors)) == 1
            assert any(
                len(gen._component_hole_regions(cells)) == 2
                for _color, cells in components
            )
            assert gen.SEMANTIC_WITNESSES["component_may_have_multiple_holes"](grid)
            assert gen.SEMANTIC_WITNESSES["same_color_components_stay_separate"](grid)
            assert gen.SEMANTIC_WITNESSES["nonrectangular_hole_fills"](grid)
            assert any(
                not gen._is_rectangular_region(region)
                for _color, cells in components
                for region in gen._component_hole_regions(cells)
            )


def test_gap_contrast_profile_guarantees_corner_gap_positive_and_side_gap_negative():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(1, 20, gen.EXAMPLES_NEEDED):
            grid = gen.generate(31415, sample_index, difficulty=difficulty)
            assert gen.schedule_profile(31415, sample_index, difficulty) == "gap_contrast"
            assert gen.self_check(grid) == []
            kinds = [
                gen._classify_component(cells)
                for _color, cells in gen._component_cells(grid)
            ]
            assert "closed_corner_gap" in kinds
            assert "open_rect" in kinds
            assert gen.SEMANTIC_WITNESSES["corner_gap_still_encloses"](grid)
            truth = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["eight_connected_holes"](grid) != truth


def test_scheduled_lesson_fires_every_witness_and_refutes_named_rivals():
    for start in range(9):
        grids = [
            gen.generate(1701, index, difficulty="hard")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        assert all(gen.self_check(copy.deepcopy(grid)) == [] for grid in grids)
        demos = [_lesson_pair(grid) for grid in grids]
        query = _lesson_pair(
            gen.generate(1701, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        )
        assert gen.lesson_identifiable(demos, query) == []

        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            witness_grid = next(
                grid
                for grid in grids
                if gen.SEMANTIC_WITNESSES[witness_name](grid)
            )
            truth = gen.rule_mirror(witness_grid)
            for rival_name in rival_names:
                assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != truth


def test_exact_override_boundaries_are_observable_and_unknown_keys_fail():
    requested = {
        "grid_h": 13,
        "grid_w": 14,
        "n_frames": 2,
        "n_open_decoys": 1,
        "palette_kind": "broad",
    }
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(991, 2, difficulty=difficulty, **requested)
        assert (len(grid), len(grid[0])) == (13, 14)
        assert gen.observe_overrides(grid) == {
            "n_frames": 2,
            "n_open_decoys": 1,
            "palette_kind": "broad",
        }
        assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, n_framez=2)


def test_topological_controls_fill_closed_and_spurred_holes_but_not_open_bbox():
    mixed = _closed_and_open_scene()
    assert gen.self_check(mixed) == []
    output = gen.rule_mirror(mixed)
    for r in range(2, 5):
        for c in range(2, 5):
            assert output[r][c] == 3
    # The open component's bbox interior remains background.
    assert output[4][9] == 0
    assert output[4][10] == 0

    spur = _spurred_frame()
    assert gen.self_check(spur) == []
    spur_output = gen.rule_mirror(spur)
    for r in range(2, 5):
        for c in range(3, 6):
            assert spur_output[r][c] == 1
    # Bbox fill would incorrectly paint these cells created by the outward spur.
    assert spur_output[2][7] == 0
    assert spur_output[4][7] == 0


def test_multi_hole_and_same_color_components_are_lawful_topology_controls():
    grid = _multi_hole_same_color_scene()
    assert gen.self_check(grid) == []

    components = gen._component_cells(grid)
    assert len(components) == 2
    assert {color for color, _ in components} == {1}
    left_cells = components[0][1]
    assert gen._classify_component(left_cells) == "closed_multi_hole_irregular"
    assert len(gen._component_hole_regions(left_cells)) == 2

    truth = gen.rule_mirror(grid)
    # Both left chambers and the separate right frame fill.
    assert truth[3][2] == 1
    assert truth[3][5] == 1
    assert truth[3][12] == 1
    # The outward spur does not turn exterior bbox cells into fill targets.
    assert truth[2][8] == 0
    assert truth[4][8] == 0

    assert gen.SEMANTIC_RIVALS["fill_one_hole_per_component"](grid) != truth
    assert gen.SEMANTIC_RIVALS["merge_same_color_bboxes"](grid) != truth


def test_corner_gap_is_closed_for_four_connected_background_only():
    grid = _corner_gap_scene()
    assert gen.self_check(grid) == []
    components = gen._component_cells(grid)
    assert len(components) == 1
    assert gen._classify_component(components[0][1]) == "closed_corner_gap"
    truth = gen.rule_mirror(grid)
    assert truth[2][3] == 8
    assert gen.SEMANTIC_RIVALS["eight_connected_holes"](grid) != truth


def test_dense_cavity_mass_fills_nonrectangular_hole_and_preserves_bbox_exterior():
    grid = _cavity_mass_same_color_scene()
    assert gen.self_check(grid) == []
    components = gen._component_cells(grid)
    assert len(components) == 2
    mass_cells = components[0][1]
    assert gen._classify_component(mass_cells) == "closed_cavity_mass_irregular"
    regions = gen._component_hole_regions(mass_cells)
    assert len(regions) == 2
    assert any(not gen._is_rectangular_region(region) for region in regions)

    truth = gen.rule_mirror(grid)
    assert truth[2][2] == 1
    assert truth[2][4] == 1
    assert truth[3][3] == 1
    assert truth[2][7] == 0
    assert truth[3][6] == 0
    assert gen.SEMANTIC_RIVALS["rectangular_holes_only"](grid) != truth


def test_strict_canonical_profile_is_scheduled_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(0, 30, gen.EXAMPLES_NEEDED):
            grid = gen.generate(881, sample_index, difficulty=difficulty)
            assert gen.schedule_profile(881, sample_index, difficulty) == "canonical_pair"
            assert gen.strict_canonical_like(grid) == []


def test_strict_canonical_profile_rejects_color_reuse_across_components():
    grid = _same_color_rect_pair_scene()
    assert gen.self_check(grid) == []
    reasons = gen.strict_canonical_like(grid)
    assert any("distinct color" in reason for reason in reasons)


def test_declared_canonical_shortcuts_fit_all_official_pairs():
    pairs = _canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(pair["input"]) == pair["output"], name


def test_self_check_rejects_structural_impostors():
    blank = [[0] * 10 for _ in range(8)]
    solid = [[0] * 10 for _ in range(8)]
    for r in range(2, 6):
        for c in range(2, 6):
            solid[r][c] = 4
    open_only = _closed_and_open_scene()
    for r in range(len(open_only)):
        for c in range(len(open_only[0])):
            if open_only[r][c] == 3:
                open_only[r][c] = 0
    two_spurs = _spurred_frame()
    two_spurs[3][8] = 1

    for grid in (blank, solid, open_only, two_spurs):
        assert gen.self_check(grid), grid


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261002)
    before = random.getstate()
    first = gen.generate(123, 17, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(123, 17, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert first != second


def test_profile_probe_emits_reproducible_curriculum_evidence(tmp_path):
    output = tmp_path / "profile-report.json"
    script = TASK_HOME / "workspace/profile_probe.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seeds",
            "2",
            "--windows",
            "2",
            "--output",
            str(output),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "arc-generator-profile-probe-v1"
    assert report["task_id"] == gen.TASK_ID
    assert report["generator_version"] == gen.VERSION
    assert report["summary"]["failures"] == 0
    assert report["summary"]["windows_checked"] == 12
    assert set(report["summary"]["profiles_seen"]) == set(gen.SCHEDULE_PROFILES)
    assert set(report["summary"]["witnesses_seen"]) == set(gen.SEMANTIC_WITNESSES)
    assert set(report["summary"]["rivals_refuted"]) == set(gen.SEMANTIC_RIVALS)
    topology = report["summary"]["topology_counts"]
    assert topology["scenes_with_multiple_holes"] > 0
    assert topology["scenes_with_reused_color"] > 0
    assert topology["scenes_with_corner_gap"] > 0
    assert topology["scenes_with_nonrectangular_hole"] > 0
    assert int(max(topology["components_by_hole_count"], key=int)) >= 2


def test_topology_counterexample_fixture_refutes_both_new_rivals():
    script = TASK_HOME / "workspace/verify_topology_counterexamples.py"
    script_spec = importlib.util.spec_from_file_location(
        "topology_counterexample_fixture", script
    )
    assert script_spec and script_spec.loader
    module = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(module)

    grid = module.counterexample_input()
    assert gen.self_check(grid) == []
    truth = gen.rule_mirror(grid)
    for rival_name in (
        "fill_one_hole_per_component",
        "merge_same_color_bboxes",
    ):
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_connectivity_shape_counterexample_fixture_refutes_new_rivals():
    script = TASK_HOME / "workspace/verify_connectivity_shape_counterexamples.py"
    assert script.is_file()
    script_spec = importlib.util.spec_from_file_location(
        "connectivity_shape_counterexample_fixture", script
    )
    assert script_spec and script_spec.loader
    module = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(module)

    cases = module.counterexample_inputs()
    assert set(cases) == {"corner_gap", "nonrectangular_cavity"}
    expected = {
        "corner_gap": "eight_connected_holes",
        "nonrectangular_cavity": "rectangular_holes_only",
    }
    for name, grid in cases.items():
        assert gen.self_check(grid) == []
        truth = gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS[expected[name]](grid) != truth
