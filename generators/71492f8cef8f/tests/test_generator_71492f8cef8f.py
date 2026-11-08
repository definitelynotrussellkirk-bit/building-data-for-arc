from __future__ import annotations

import copy
import importlib
import random
import json
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "71492f8cef8f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _lesson(seed: int, start: int, band: str) -> tuple[list[dict], dict]:
    pairs = []
    for offset in range(3):
        grid = GEN.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:2], pairs[2]


def test_rule_pin_and_all_canonical_pairs_are_exact() -> None:
    assert GEN.RULE_HASH == "f88bd76ccafc"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_scene_profile_is_observable_and_teaches_all_core_branches() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index, profile in enumerate(GEN.SCENE_PROFILES):
            grid = GEN.generate(
                10_000 + 100 * band_index + profile_index,
                20_000 + profile_index,
                difficulty=band,
                scene_profile=profile,
            )
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}
            analysis = GEN._analysis(grid)
            assert analysis["qualifying_count"] >= 2
            assert analysis["empty_count"] >= 1
            assert analysis["multi_count"] >= 1
            assert analysis["same_color_multi_count"] >= 1
            if profile in GEN.OPEN_EDGE_PROFILES:
                assert analysis["edge_unique_count"] >= 1
            else:
                assert analysis["edge_unique_count"] == 0


def test_default_schedule_covers_profiles_profile_floor_and_identifiable_windows() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = []
        profiles = []
        for sample_index in range(20):
            grid = GEN.generate(30_000 + band_index, sample_index, difficulty=band)
            observed.append(grid)
            profiles.append(GEN.observe_overrides(grid)["scene_profile"])
        assert set(profiles) == set(GEN.SCENE_PROFILES)
        assert any(
            (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            == (7, 9, 4)
            for grid in observed
        )

        for start in range(4):
            demos, query = _lesson(40_000 + band_index, start, band)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(copy.deepcopy(demo["input"])) != demo["output"]
                    for demo in demos
                ), (band, start, name)


def test_canonical_shortcuts_fit_examples_and_generated_witnesses_refute_rivals() -> None:
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(
            rival(copy.deepcopy(pair["input"])) == pair["output"]
            for pair in _pairs()
        ), name

    for profile_index, profile in enumerate(GEN.SCENE_PROFILES):
        grid = GEN.generate(50_000 + profile_index, profile_index, scene_profile=profile)
        expected = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](copy.deepcopy(grid)) != expected


def test_exactly_one_seed_cell_not_one_distinct_seed_color() -> None:
    grid = GEN.generate(61, 7, scene_profile="cross_closed")
    analysis = GEN._analysis(grid)
    output = GEN.rule_mirror(grid)
    saw_same_color_conflict = False
    for cells, seeds in zip(analysis["chambers"], analysis["seed_cells"]):
        if len(seeds) == 1:
            color = seeds[0][2]
            assert all(output[r][c] == color for r, c in cells)
        else:
            assert all(output[r][c] == grid[r][c] for r, c in cells)
        if len(seeds) > 1 and len({value for _, _, value in seeds}) == 1:
            saw_same_color_conflict = True
            assert any(grid[r][c] == 0 and output[r][c] == 0 for r, c in cells)
    assert saw_same_color_conflict


def test_unknown_controls_determinism_freshness_and_global_rng_purity() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, invented_axis="accepted")
    with pytest.raises(ValueError, match="scene_profile"):
        GEN.generate(1, 2, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")

    random.seed(20261003)
    state = random.getstate()
    first = GEN.generate(777, 999, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 999, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert first != second


def test_malformed_and_non_teaching_inputs_are_rejected() -> None:
    cases = [
        [],
        [[0], []],
        [[True]],
        [[10]],
        [[0, 0], [0, 0]],
        [[5, 5, 5], [5, 0, 5], [5, 5, 5]],
    ]
    for case in cases:
        assert GEN.self_check(case), case


def test_workspace_probe_exercises_every_cyclic_lesson_window(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "workspace" / "lesson_window_probe.py"
    report_path = tmp_path / "lesson-window-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seeds-per-start",
            "2",
            "--out",
            str(report_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(report_path.read_text())
    expected_windows = 3 * len(GEN.SCHEDULE_PROFILES) * 2
    assert report["status"] == "pass"
    assert report["windows_total"] == expected_windows
    assert report["failures"] == []
    assert set(report["rival_refuted_in_demos"]) == set(GEN.LESSON_COMPETITORS)
    assert set(report["witness_present_in_demos"]) == set(GEN.SEMANTIC_WITNESSES)
    assert set(report["rival_refuted_in_demos"].values()) == {expected_windows}
    assert set(report["witness_present_in_demos"].values()) == {expected_windows}
