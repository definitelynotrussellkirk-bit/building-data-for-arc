"""Focused control, semantic, and lesson regressions for 0a54983176e5."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "0a54983176e5"
REPO_ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator", GEN_PATH
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _norm_grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_record():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError("canonical record missing")


def _canonical_pairs():
    record = _canonical_record()
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in record["train"] + record["test"]
    ]


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "e266f9b65f93"


def test_canonical_inputs_are_owned_and_python_rule_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == original


def test_unknown_overrides_difficulty_and_removed_degenerates_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="medium", typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")
    for texture in ("no_axis", "no_content"):
        with pytest.raises(ValueError, match="texture"):
            GEN.generate(1, 0, difficulty="medium", texture=texture)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [5, 14])
@pytest.mark.parametrize("grid_w", [7, 16])
@pytest.mark.parametrize("orientation", [0, 1])
def test_dimension_and_orientation_overrides_are_total_and_observable(
    difficulty, grid_h, grid_w, orientation
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "orientation": orientation,
        "texture": "plain",
    }
    grid = GEN.generate(901, 17, difficulty=difficulty, **requested)
    assert (len(grid), len(grid[0])) == (grid_h, grid_w)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    observed = GEN.observe_overrides(grid)
    assert observed["orientation"] == orientation


def test_each_helpful_texture_is_realized_and_rule_relevant():
    for orientation in (0, 1):
        both = GEN.generate(
            101, 0, difficulty="medium", orientation=orientation, texture="both_sides"
        )
        clipped = GEN.generate(
            102, 1, difficulty="medium", orientation=orientation, texture="clip"
        )
        on_axis = GEN.generate(
            103, 2, difficulty="medium", orientation=orientation, texture="on_axis"
        )
        assert GEN.SEMANTIC_WITNESSES["occupied_target_blocks"](both)
        assert GEN.SEMANTIC_WITNESSES["markers_not_grid_center"](clipped)
        facts = GEN.semantic_observables(on_axis)
        assert facts["axis_content_cells"] >= 1
        assert GEN.rule_mirror(on_axis) != on_axis


def test_canonical_shortcuts_fit_all_canonical_pairs_but_generated_schedule_refutes_them():
    canonical = _canonical_pairs()
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "use_grid_center_axis",
        "overwrite_occupied_target",
    }
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical), name

    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = [_pair(77_000, start + offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
            query = _pair(77_000, start + GEN.EXAMPLES_NEEDED, band)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    name,
                )
            assert GEN.lesson_identifiable(demos, query) == []


def test_default_profile_support_is_canonical_scale_in_every_band():
    canonical_profiles = {(6, 11, 3), (7, 9, 4), (7, 11, 4)}
    envelope = ((6, 7), (9, 11), (3, 4))
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(24):
            grid = GEN.generate(20_000 + index, index, difficulty=band)
            profiles.append(
                (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))
            )
        assert any(profile in canonical_profiles for profile in profiles), band
        assert sum(
            envelope[0][0] <= h <= envelope[0][1]
            and envelope[1][0] <= w <= envelope[1][1]
            and envelope[2][0] <= palette <= envelope[2][1]
            for h, w, palette in profiles
        ) >= 8, (band, profiles)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_semantic_window_probe_executes_declared_rivals_and_all_requested_windows():
    tool_path = (
        REPO_ROOT
        / "generators"
        / TASK_ID
        / "workspace"
        / "semantic_window_probe.py"
    )
    tool_spec = importlib.util.spec_from_file_location("semantic_window_probe", tool_path)
    assert tool_spec and tool_spec.loader
    tool = importlib.util.module_from_spec(tool_spec)
    tool_spec.loader.exec_module(tool)

    report = tool.run_probe(
        seed_start=8800,
        seed_count=2,
        starts=range(3),
        difficulties=("easy",),
    )
    assert report["passed"] is True
    assert report["windows_checked"] == 6
    assert report["rivals_checked"] == sorted(GEN.LESSON_COMPETITORS)
    assert report["failures"] == []
