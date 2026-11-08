"""Focused regression tests for contour-cell-rank recolouring task 901c6034f67e."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "901c6034f67e"
LIBRARY = next(
    (parent for parent in Path(__file__).resolve().parents
     if (parent / "shared/runtime/puzzle_generators").is_dir()),
    None,
)
if LIBRARY is not None:
    ROOT = LIBRARY / "shared"
    sys.path.insert(0, str(ROOT / "runtime"))
    path = LIBRARY / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("contour_rank_generator", path)
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)
else:
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return [*row["train"], *test]
    raise AssertionError("canonical row missing")


def contour_length(cells):
    cells = set(cells)
    return sum(
        any((row + dr, col + dc) not in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        for row, col in cells
    )


def bbox_area(cells):
    rows, cols = zip(*cells)
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def bbox_perimeter(cells):
    rows, cols = zip(*cells)
    return 2 * ((max(rows) - min(rows) + 1) + (max(cols) - min(cols) + 1))


def recolor_by(grid, key):
    out = [[0] * len(grid[0]) for _ in grid]
    components = GEN._components(grid)
    for rank, cells in enumerate(sorted(components, key=lambda c: (key(c), min(c)))):
        for row, col in cells:
            out[row][col] = (2, 3, 4, 6, 7, 8, 9)[rank]
    return out


def area_counterexample():
    """Contour order and occupied-area order swap the final two objects."""
    grid = [[0] * 20 for _ in range(12)]
    for row, col in ((1, 1), (1, 2), (1, 3)):
        grid[row][col] = 5                         # area/contour 3
    for row in range(7, 10):
        for col in range(1, 5):
            grid[row][col] = 6                    # area 12, contour 10
    for col in range(8, 19):
        grid[3][col] = 7                          # area/contour 11
    return grid


def bbox_counterexample():
    """Contour order swaps the last two objects versus both bbox metrics."""
    grid = [[0] * 18 for _ in range(13)]
    for row, col in ((1, 1), (1, 2), (1, 3)):
        grid[row][col] = 5                         # contour 3
    for row, col in (
        (4, 1), (5, 1), (6, 1), (7, 1),
        (7, 2), (7, 3), (7, 4),
    ):
        grid[row][col] = 6                         # contour 7, bbox 4x4
    for row in range(8, 11):
        for col in range(11, 15):
            grid[row][col] = 7                    # contour 10, bbox 3x4
    return grid


def test_rule_pin_and_all_canonical_pairs_follow_contour_rank():
    assert getattr(GEN, "RULE_HASH", None) == "3646fc9eedbe"
    assert callable(getattr(GEN, "rule_mirror", None))
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_public_profile_bank_is_derived_from_every_canonical_input():
    signatures = {GEN._linked_signature(pair["input"]) for pair in canonical_pairs()}
    assert set(GEN._PUBLIC_SIGNATURES) == signatures
    assert set(GEN._PUBLIC_SIGNATURES.values()) == set(GEN.PUBLIC_PROFILES)


def test_exact_area_and_bbox_shortcut_counterexamples():
    area_grid = area_counterexample()
    assert GEN.self_check(area_grid) == []
    assert GEN.observe_overrides(area_grid)["scene_profile"] == "area_inversion"
    intended = GEN.rule_mirror(area_grid)
    assert recolor_by(area_grid, len) != intended
    assert recolor_by(area_grid, contour_length) == intended

    bbox_grid = bbox_counterexample()
    assert GEN.self_check(bbox_grid) == []
    assert GEN.observe_overrides(bbox_grid)["scene_profile"] == "bbox_inversion"
    intended = GEN.rule_mirror(bbox_grid)
    assert recolor_by(bbox_grid, bbox_area) != intended
    assert recolor_by(bbox_grid, bbox_perimeter) != intended
    assert recolor_by(bbox_grid, contour_length) == intended


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", [
    "canonical_train_0", "canonical_train_1", "canonical_train_2",
    "canonical_test_0", "area_inversion", "bbox_inversion",
])
@pytest.mark.parametrize("palette_mode", ["shared", "distinct", "rank_colors"])
def test_exact_overrides_are_observable(band, profile, palette_mode):
    grid = GEN.generate(
        991,
        17,
        difficulty=band,
        scene_profile=profile,
        palette_mode=palette_mode,
    )
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": profile,
        "palette_mode": palette_mode,
    }


def test_default_schedule_has_a_strict_canonical_profile_in_each_twenty_draw_band():
    for band in ("easy", "medium", "hard"):
        strict = []
        profiles = []
        for index in range(20):
            grid = GEN.generate(2718, index, difficulty=band)
            strict.append(not GEN.strict_canonical_like(grid))
            profiles.append(GEN.observe_overrides(grid)["scene_profile"])
        assert any(strict), (band, profiles)
        assert "area_inversion" in profiles
        assert "bbox_inversion" in profiles


def test_generated_scenes_have_three_distinct_contours_and_exact_rule_output():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = GEN.generate(seed, seed % 11, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            components = GEN._components(grid)
            contours = [GEN._contour_length(cells) for cells in components]
            assert len(components) == 3
            assert len(set(contours)) == 3
            assert GEN.rule_mirror(grid) != grid


def test_every_rotated_three_demo_window_rebuts_declared_competitors():
    for offset in range(9):
        pairs = []
        for sample_index in range(offset, offset + 4):
            grid = GEN.generate(200, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        demos, query = pairs[:3], pairs[3]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_canonical_shortcuts_fit_all_public_pairs_but_fail_generated_diagnostics():
    pairs = canonical_pairs()
    assert {"area", "bbox_area", "bbox_perimeter"} <= set(GEN.CANONICAL_SHORTCUTS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    diagnostic_grids = [
        GEN.generate(77, 1, scene_profile="area_inversion", palette_mode="distinct"),
        GEN.generate(77, 2, scene_profile="bbox_inversion", palette_mode="distinct"),
    ]
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != GEN.rule_mirror(grid) for grid in diagnostic_grids), name


def test_semantic_witnesses_are_bound_to_rivals_or_branch_coverage():
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS) | set(GEN.BRANCH_WITNESSES)
    for seed in range(60):
        grid = GEN.generate(seed, seed % 7)
        for witness_name, rivals in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[witness_name](grid):
                for rival_name in rivals:
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)


def test_self_check_rejects_contour_ties_and_malformed_inputs():
    tied = [[0] * 14 for _ in range(10)]
    for row, col in ((1, 1), (1, 2), (2, 1)):
        tied[row][col] = 5
    for row, col in ((1, 8), (1, 9), (2, 8)):
        tied[row][col] = 6
    for row in range(6, 9):
        for col in range(5, 9):
            tied[row][col] = 7
    assert any("contour" in reason.lower() and "distinct" in reason.lower()
               for reason in GEN.self_check(tied))
    assert GEN.self_check([])
    assert GEN.self_check([[0], [0, 0]])


def test_deterministic_replay_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="hard")
    assert second == first
    assert second is not first
    assert all(row1 is not row2 for row1, row2 in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 5, difficulty="hard") == second


def test_workspace_probe_checks_cyclic_windows_and_declared_rivals():
    if LIBRARY is None:
        pytest.skip("workspace source is not present in installed runtime layout")
    probe_path = LIBRARY / "generators" / TASK_ID / "workspace" / "probe_lessons.py"
    spec = importlib.util.spec_from_file_location("contour_rank_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(seed=4242, starts=6, bands=("easy",))
    assert report["all_windows_identifiable"] is True
    assert report["errors"] == []
    assert set(report["rivals"]) == set(GEN.LESSON_COMPETITORS)
    assert report["bands"]["easy"]["windows"] == 6
    assert report["bands"]["easy"]["identifiable_windows"] == 6
    assert all(count == 6 for count in report["bands"]["easy"]["rival_refuted_windows"].values())


def color_blind_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    groups = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            groups.append(tuple(sorted(cells)))
    return groups


def test_nonshared_canonical_anchors_refute_color_blind_connectivity():
    rival_name = "color_blind_connectivity"
    assert rival_name in GEN.LESSON_COMPETITORS
    assert "different_colours_touch" in GEN.WITNESS_RIVALS
    assert rival_name in GEN.WITNESS_RIVALS["different_colours_touch"]
    for band in ("easy", "medium", "hard"):
        for profile in GEN.PUBLIC_PROFILES:
            for palette_mode in ("distinct", "rank_colors"):
                grid = GEN.generate(
                    731,
                    9,
                    difficulty=band,
                    scene_profile=profile,
                    palette_mode=palette_mode,
                )
                assert len(GEN._components(grid)) == 3
                assert len(color_blind_components(grid)) < 3
                assert GEN.SEMANTIC_WITNESSES["different_colours_touch"](grid)
                assert GEN.LESSON_COMPETITORS[rival_name](grid) != GEN.rule_mirror(grid)


def test_default_sampler_preserves_canonical_introduction_of_rank_color_two():
    """Mirror defect-lint's 20 seeds x 3 bands transformation fingerprint.

    Every canonical demonstration introduces output color 2.  More than half of
    the default generated inputs should likewise omit 2 so the curriculum keeps
    that visible transformation relation, while the explicit rank_colors mode
    remains available to defeat input-color/identity shortcuts.
    """
    inputs = [
        GEN.generate(seed, seed, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(1, 21)
    ]
    introduced = sum(
        2 not in {value for row in grid for value in row}
        for grid in inputs
    )
    assert introduced > len(inputs) / 2, introduced
