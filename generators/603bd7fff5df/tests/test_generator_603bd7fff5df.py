from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "review_generator_603bd7fff5df", GENERATOR_ROOT / "generator.py"
)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    ledger = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _bbox_of(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    assert cells
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _semantic_regions(grid: list[list[int]]) -> dict[str, list[int]]:
    r0, c0, r1, c1 = _bbox_of(grid, 5)
    top = [grid[r0 - 1][col] for col in range(c0, c1 + 1)]
    bottom = [grid[r1 + 1][col] for col in range(c0, c1 + 1)]
    inside = [
        grid[row][col]
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if col not in (c0, c1)
    ]
    outside = [
        grid[row][col]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if not (r0 - 1 <= row <= r1 + 1 and c0 <= col <= c1)
    ]
    return {"top": top, "bottom": bottom, "inside": inside, "outside": outside}


def test_rule_pin_and_all_canonical_pairs_are_owned_and_reproduced():
    assert GEN.RULE_HASH == "539d28e25b24"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_schedule_covers_every_recoverable_axis_in_every_band():
    expected = {
        "scene_profile": set(GEN.SCENE_PROFILES),
        "placement": set(GEN.PLACEMENTS),
        "side_style": set(GEN.SIDE_STYLES),
    }
    for band in ("easy", "medium", "hard"):
        observed = {name: set() for name in expected}
        for sample_index in range(24):
            grid = GEN.generate(81723, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert {value for row in grid for value in row} == {0, 5, 8}
            values = GEN.observe_overrides(grid)
            for name in observed:
                observed[name].add(values[name])
        assert observed == expected


def test_every_axis_combination_is_exact_and_band_independent():
    for band in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            for placement in GEN.PLACEMENTS:
                for side_style in GEN.SIDE_STYLES:
                    requested = {
                        "scene_profile": profile,
                        "placement": placement,
                        "side_style": side_style,
                    }
                    grid = GEN.generate(19, 7, difficulty=band, **requested)
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == requested


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis="left_edge")
    with pytest.raises(ValueError, match="scene_profile"):
        GEN.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="placement"):
        GEN.generate(0, 0, placement="floating")
    with pytest.raises(ValueError, match="side_style"):
        GEN.generate(0, 0, side_style="full_outline")


def test_replay_returns_fresh_grids_without_touching_global_rng():
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(3, 8, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(3, 8, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_generated_scenes_make_all_four_rule_regions_observable():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = GEN.generate(seed, seed * 13 + 5, difficulty=band)
            regions = _semantic_regions(grid)
            assert 8 in regions["top"]
            assert 8 in regions["bottom"]
            assert 8 in regions["inside"]
            assert 8 in regions["outside"]


def test_declared_mutation_fixtures_are_rejected_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        frozen = copy.deepcopy(grid)
        errors = GEN.self_check(grid)
        assert errors, name
        assert grid == frozen, name


def test_self_check_rejects_minimal_impostors_and_bad_arc_grids():
    malformed = [
        [],
        [[]],
        [[0, 5], [5]],
        [[0, True], [5, 5]],
        [[0, 11], [5, 5]],
        [[0, 0, 0], [0, 5, 0], [0, 0, 0]],
        [[0, 5, 0], [0, 5, 0], [0, 5, 0]],
    ]
    for grid in malformed:
        assert GEN.self_check(grid), grid


def test_named_witnesses_fire_and_really_refute_their_named_rivals():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(36):
        grid = GEN.generate(707, sample_index, difficulty="medium")
        truth = GEN.rule_mirror(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                hits[name] += 1
                rivals = GEN.WITNESS_RIVALS[name]
                assert rivals, name
                assert all(GEN.SEMANTIC_RIVALS[rival](grid) != truth for rival in rivals)
    assert all(count > 0 for count in hits.values()), hits


def test_declared_canonical_shortcuts_fit_public_pairs_but_generated_data_breaks_them():
    for pair in _canonical_pairs():
        for shortcut in GEN.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]

    grids = [GEN.generate(31, index, difficulty="medium") for index in range(12)]
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in grids), name


def test_three_demo_windows_identify_the_rule_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in (0, 1, 11, 22, 33):
            rows = []
            for offset in range(4):
                grid = GEN.generate(1234 + start, start + offset, difficulty=band)
                rows.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(rows[:3], rows[3]) == []


def test_selected_base_authorities_match_the_canonical_rule_source():
    selected = _canonical_row()["program_solution"]
    authority_paths = (
        REPO_ROOT / "shared" / "data" / "base" / "solutions" / "training" / "3f7978a0__603bd7fff5df.json",
        REPO_ROOT / "shared" / "data" / "base" / "solutions" / "augmented" / "3f7978a0__6936031d2445.json",
    )
    for path in authority_paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        assert row["racket_target"]["target_code"] == selected, path


def test_curriculum_analyzer_reports_complete_signal_coverage():
    tool_path = GENERATOR_ROOT / "workspace" / "analyze_crop_curriculum.py"
    assert tool_path.exists(), "task-local curriculum analyzer is missing"
    spec = importlib.util.spec_from_file_location("crop_curriculum_analyzer", tool_path)
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    report = tool.analyze(draws_per_band=12, seed=20261002)
    assert report["invalid_draws"] == 0
    for band in ("easy", "medium", "hard"):
        row = report["per_band"][band]
        assert set(row["axes"]["scene_profile"]) == set(GEN.SCENE_PROFILES)
        assert set(row["axes"]["placement"]) == set(GEN.PLACEMENTS)
        assert set(row["axes"]["side_style"]) == set(GEN.SIDE_STYLES)
        assert min(row["minimum_blue_region_counts"].values()) >= 1
    assert all(count > 0 for count in report["witness_hits"].values())
    assert all(count > 0 for count in report["rival_disagreements"].values())
