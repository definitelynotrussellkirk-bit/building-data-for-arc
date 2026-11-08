from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.089c14df9952.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "089c14df9952"
AUGMENTED = ROOT / "data/base/solutions/augmented/36d67576__46637446c942.json"


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _copy(grid):
    return [row[:] for row in grid]


def test_canonical_pairs_and_selected_authority_are_exact():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    canonical_source = None
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical_source = row["program_solution"]
                break
    assert canonical_source is not None
    target = json.loads(AUGMENTED.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == canonical_source
    assert target["raw_code"] != target["target_code"]


def test_every_sliding_four_example_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(20):
            examples = [
                _pair(gen.generate(1701, start + offset, difficulty=difficulty))
                for offset in range(5)
            ]
            assert gen.lesson_identifiable(examples[:4], examples[4]) == []
            observed = [gen.observe_overrides(item["input"]) for item in examples[:4]]
            assert {item["texture"] for item in observed} == {"plain", "hint", "clip"}
            assert {item["target_count"] for item in observed} == {1, 2, 3}


def test_boundary_overrides_are_exact_observable_and_band_safe():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (11, 20):
            for grid_w in (12, 20):
                for target_count in (1, 3):
                    for texture in ("plain", "hint", "clip"):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "target_count": target_count,
                            "texture": texture,
                        }
                        grid = gen.generate(
                            25000 + case,
                            case % 17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested
                        case += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260727)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_semantic_branches_are_positive_and_answer_unique():
    grids = {
        texture: gen.generate(
            3300 + index,
            index,
            difficulty="medium",
            texture=texture,
            target_count=3,
        )
        for index, texture in enumerate(("plain", "hint", "clip"))
    }
    assert gen.SEMANTIC_WITNESSES["plain_unique_shape_match"](grids["plain"])
    assert gen.SEMANTIC_WITNESSES["red_hint_answer_decisive"](grids["hint"])
    assert gen.SEMANTIC_WITNESSES["partial_edge_clipping"](grids["clip"])
    for grid in grids.values():
        assert gen.SEMANTIC_WITNESSES["all_targets_have_one_answer"](grid)
        assert gen.rule_mirror(grid) != grid


def test_clip_branch_mixes_target_cues_and_refutes_scene_level_hint_policy():
    grid = gen.generate(
        4201,
        2,
        difficulty="medium",
        grid_h=16,
        grid_w=17,
        texture="clip",
        target_count=3,
    )
    facts = gen._analyze(grid)
    assert facts["errors"] == []
    assert {bool(target["red"]) for target in facts["targets"]} == {False, True}
    assert any(
        target["clipped_count"] and not target["red"]
        for target in facts["targets"]
    )
    assert gen.observe_overrides(grid)["texture"] == "clip"
    assert gen.SEMANTIC_WITNESSES["mixed_target_cues"](grid)
    assert (
        gen.SEMANTIC_RIVALS["scene_uniform_hint_policy"](grid)
        != gen.rule_mirror(grid)
    )


def test_canonical_shortcuts_fit_public_pairs_and_have_generated_counterexamples():
    expected = {
        "hinted_targets_only",
        "scene_uniform_hint_policy",
        "skip_clipped_targets",
    }
    assert set(gen.CANONICAL_SHORTCUTS) == expected
    assert expected <= set(gen.SEMANTIC_RIVALS)
    assert expected <= set(gen.LESSON_COMPETITORS)

    for pair in canonical_pairs(TASK_ID):
        for shortcut in gen.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]

    plain = gen.generate(
        5101,
        1,
        difficulty="medium",
        texture="plain",
        target_count=1,
    )
    mixed_clip = gen.generate(
        5102,
        2,
        difficulty="medium",
        texture="clip",
        target_count=3,
    )
    assert (
        gen.SEMANTIC_RIVALS["hinted_targets_only"](plain)
        != gen.rule_mirror(plain)
    )
    assert (
        gen.SEMANTIC_RIVALS["scene_uniform_hint_policy"](mixed_clip)
        != gen.rule_mirror(mixed_clip)
    )
    assert (
        gen.SEMANTIC_RIVALS["skip_clipped_targets"](mixed_clip)
        != gen.rule_mirror(mixed_clip)
    )
    assert gen.WITNESS_RIVALS["plain_unique_shape_match"] == [
        "hinted_targets_only"
    ]
    assert gen.WITNESS_RIVALS["mixed_target_cues"] == [
        "scene_uniform_hint_policy"
    ]
    assert gen.WITNESS_RIVALS["partial_edge_clipping"] == [
        "skip_clipped_targets"
    ]


def test_default_schedule_is_named_for_semantic_census_tools():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "hint-2",
        "plain-1",
        "clip-mixed-3",
        "hint-3",
    )
    assert [gen.schedule_profile(99, index, difficulty="hard") for index in range(8)] == [
        "hint-2",
        "plain-1",
        "clip-mixed-3",
        "hint-3",
        "hint-2",
        "plain-1",
        "clip-mixed-3",
        "hint-3",
    ]


def test_shape_matcher_normalizes_each_d4_orientation_once(monkeypatch):
    yellow = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
    original_tf = gen._tf
    target = gen._norm(original_tf(yellow, 3))
    calls = 0

    def counted_tf(cells, index):
        nonlocal calls
        calls += 1
        return original_tf(cells, index)

    monkeypatch.setattr(gen, "_tf", counted_tf)
    assert gen._shape_matches(yellow, target)
    assert calls <= 8


def test_generate_runs_one_structural_analysis_for_a_successful_scene(monkeypatch):
    original_analyze = gen._analyze
    calls = 0

    def counted_analyze(grid):
        nonlocal calls
        calls += 1
        return original_analyze(grid)

    monkeypatch.setattr(gen, "_analyze", counted_analyze)
    gen.generate(
        6101,
        1,
        difficulty="medium",
        grid_h=20,
        grid_w=20,
        texture="plain",
        target_count=1,
    )
    assert calls == 1


def test_equal_grid_analysis_reuses_the_content_cache(monkeypatch):
    grid = gen.generate(
        6201,
        1,
        difficulty="medium",
        grid_h=20,
        grid_w=20,
        texture="plain",
        target_count=1,
    )
    original_components = gen._nonzero_components
    calls = 0

    def counted_components(value):
        nonlocal calls
        calls += 1
        return original_components(value)

    monkeypatch.setattr(gen, "_nonzero_components", counted_components)
    gen._analysis_cache_clear()
    assert gen._analyze(grid)["errors"] == []
    assert gen._analyze(_copy(grid))["errors"] == []
    assert calls == 1


def test_scene_search_materializes_only_candidates_it_examines(monkeypatch):
    original_materialize = gen._materialize_target_candidate
    calls = 0

    def counted_materialize(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original_materialize(*args, **kwargs)

    monkeypatch.setattr(gen, "_materialize_target_candidate", counted_materialize)
    grid = gen.generate(
        6301,
        1,
        difficulty="medium",
        grid_h=20,
        grid_w=20,
        texture="plain",
        target_count=1,
    )
    assert gen.self_check(grid) == []
    assert calls < 32


def test_structural_mutations_are_rejected():
    grid = gen.generate(8801, 0, difficulty="medium", texture="hint", target_count=2)
    facts = gen._analyze(grid)
    assert facts["errors"] == []

    # 1. An out-of-grammar palette value must not be silently accepted.
    bad_palette = _copy(grid)
    r, c = next((r, c) for r, c in facts["base"] if bad_palette[r][c] == 1)
    bad_palette[r][c] = 5

    # 2. A target may use red only as its orientation hint.
    bad_hint_color = _copy(grid)
    target = next(target for target in facts["targets"] if target["red"])
    ar, ac = target["anchor"]
    rr, rc = target["red"][0]
    bad_hint_color[ar + rr][ac + rc] = 3

    # 3. Breaking one target skeleton destroys D4 equivalence.
    bad_shape = _copy(grid)
    yellow_r, yellow_c = facts["components"][1][0]
    if bad_shape[yellow_r][yellow_c] != 4:
        yellow_r, yellow_c = next(
            (r, c) for r, c in facts["components"][1] if bad_shape[r][c] == 4
        )
    bad_shape[yellow_r][yellow_c] = 0

    # 4. Removing a base color destroys the unique three-color base cue.
    bad_base_cue = _copy(grid)
    for r, c in facts["base"]:
        if bad_base_cue[r][c] == 3:
            bad_base_cue[r][c] = 1

    for name, mutated in {
        "bad_palette": bad_palette,
        "bad_hint_color": bad_hint_color,
        "bad_shape": bad_shape,
        "bad_base_cue": bad_base_cue,
    }.items():
        assert gen.self_check(mutated), name
