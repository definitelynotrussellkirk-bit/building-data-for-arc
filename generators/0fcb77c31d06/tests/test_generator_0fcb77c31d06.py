from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.0fcb77c31d06.generator"
)


def _pairs():
    return canonical_pairs(
        gen.TASK_ID,
        root=find_root(__file__),
        labeled_only=True,
    )


def _pair(grid):
    return {"input": grid, "output": gen.oracle_output(grid)}


def test_rule_pin_and_python_oracle_match_every_labeled_canonical_pair():
    pairs = _pairs()
    assert len(pairs) >= 5
    assert gen.RULE_HASH == "c515fc7de0cf"
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_only_exact_observable_axes_are_declared_and_round_trip_in_every_band():
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    for band in ("easy", "medium", "hard"):
        for h in (9, 10, 11, 12):
            for w in (10, 11, 12, 13, 14):
                grid = gen.generate(
                    700 + h + w,
                    h * 100 + w,
                    difficulty=band,
                    grid_h=h,
                    grid_w=w,
                )
                assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                assert gen.teaching_check(grid) == []


@pytest.mark.parametrize("bad", [True, False, 9.0, "9", -1])
def test_strict_scalar_controls_reject_coercions_and_negative_sample_index(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 3, grid_h=bad)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 3, grid_w=bad)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, bad)


def test_unknown_controls_and_unknown_difficulty_reject():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 1, difficulty="expert")


def test_generated_inputs_always_teach_frequency_and_largest_component_steps():
    seen_palette_sizes = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(36):
            grid = gen.generate(10_000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.teaching_check(grid) == []
            info = gen._analysis(grid)
            seen_palette_sizes.add(len(info["legend_counts"]))

            assert info["leftmost_legend_color"] != info["key"]
            assert len(info["key_components"]) == 2
            key_sizes = sorted((len(cells) for cells in info["key_components"]), reverse=True)
            assert key_sizes[0] > key_sizes[1]
            assert info["top_left_key_component"] != info["selected_key_component"]
            assert max(len(cells) for _color, cells in info["body_components"]) > key_sizes[0]
            assert gen._selected_crop_has_background(grid)

            official = gen.oracle_output(grid)
            for rival in gen.LESSON_COMPETITORS.values():
                assert rival(grid) != official

    assert seen_palette_sizes == {3, 4}


def test_declared_canonical_shortcuts_really_fit_canonical_and_generated_witnesses_refute_them():
    pairs = _pairs()
    assert set(gen.CANONICAL_SHORTCUTS) >= {
        "leftmost_legend_then_top_left_key",
        "frequency_then_top_left_key",
        "frequency_then_all_key_bbox",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name

    for sample_index in range(12):
        grid = gen.generate(4242, sample_index, difficulty="medium")
        official = gen.oracle_output(grid)
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(grid) != official, name


def test_three_demo_lessons_are_identifiable_against_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(81_000 + start, start + offset, difficulty=band) for offset in range(4)]
            demos = [_pair(grid) for grid in grids[:3]]
            query = _pair(grids[3])
            assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_missing_legend_and_missing_second_key_component():
    grid = gen.generate(123, 7, difficulty="medium", grid_h=10, grid_w=12)
    assert gen.self_check(grid) == []

    no_legend = copy.deepcopy(grid)
    no_legend[0] = [0] * len(no_legend[0])
    assert gen.self_check(no_legend)

    one_key = copy.deepcopy(grid)
    info = gen._analysis(one_key)
    for r, c in info["top_left_key_component"]:
        one_key[r][c] = 0
    # One key object is canonical-valid (all public examples have one), but it
    # is not a sufficient generated teaching instance for the shortcut repair.
    assert gen.strict_canonical_like(one_key) == []
    errors = gen.teaching_check(one_key)
    assert errors
    assert any("two key-color components" in error for error in errors)


def test_retained_canonical_shortcut_counterexample_replays_exactly():
    counterexample_path = (
        find_root(__file__)
        / "generators"
        / gen.TASK_ID
        / "counterexamples"
        / "canonical-shortcuts.json"
    )
    case = json.loads(counterexample_path.read_text())
    source_sha256 = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    assert case["generator_sha256"] == source_sha256
    assert case["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(case["input"]) == []
    assert gen.teaching_check(case["input"]) == []
    assert gen.oracle_output(case["input"]) == case["official_racket_output"]
    assert case["racket_matches_python_mirror"] is True
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert rival(case["input"]) == case["rival_outputs"][name]
        assert rival(case["input"]) != case["official_racket_output"]


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(31415, 8, difficulty="hard", grid_h=10, grid_w=12)
    assert random.getstate() == state
    second = gen.generate(31415, 8, difficulty="hard", grid_h=10, grid_w=12)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(31415, 8, difficulty="hard", grid_h=10, grid_w=12)
