"""Task-local regression suite for 1a92a12bac06."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    ceil_half_rival,
    grid_bottom_anchor_rival,
    intended_output,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def test_canonical_examples_are_accepted_and_independently_reproduced():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert grid_bottom_anchor_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=7, grid_w=9, n_bars=3, texture="bottom_aligned"),
        dict(grid_h=14, grid_w=13, n_bars=4, texture="top_aligned"),
        dict(grid_h=9, grid_w=12, n_bars=3, texture="floating"),
        dict(grid_h=11, grid_w=10, n_bars=4, texture="mixed_anchors"),
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, options):
    grid = gen.generate(211, 17, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert {key: observed(grid)[key] for key in options} == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 8),
        ("grid_w", 14),
        ("n_bars", 2),
        ("n_bars", 5),
        ("texture", "no_bars"),
        ("grid_h", True),
        ("grid_w", "9"),
        ("n_bars", 3.0),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(0, bad_index)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="non-negative"):
        gen.generate(0, -1)


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_generate_rejects_invalid_difficulty(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty=bad_difficulty)


def test_default_schedule_guarantees_all_profiles_and_canonical_support():
    textures = []
    strict_indices = []
    for index in range(16):
        grid = gen.generate(991, index, difficulty="hard")
        info = observed(grid)
        textures.append(info["texture"])
        assert gen.schedule_profile(991, index, difficulty="hard") == info["texture"]
        if gen.strict_canonical_like(grid) == []:
            strict_indices.append(index)
            assert (info["grid_h"], info["grid_w"], info["n_bars"]) in {
                (7, 9, 4),
                (8, 9, 4),
                (9, 9, 4),
                (11, 9, 4),
            }
    assert set(textures) == set(gen.SCHEDULE_PROFILES)
    assert strict_indices == [0, 4, 8, 12]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_lawful_deterministic_and_visible(band):
    shapes = set()
    for index in range(80):
        grid = gen.generate(4100 + index, index, difficulty=band)
        assert grid == gen.generate(4100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        info = observed(grid)
        assert any(height % 2 for height in info["heights"])
        assert any(height % 2 == 0 for height in info["heights"])
        output = intended_output(grid)
        changed = sum(
            before != after
            for in_row, out_row in zip(grid, output)
            for before, after in zip(in_row, out_row)
        )
        assert changed / (len(grid) * len(grid[0])) >= 0.02
        shapes.add((len(grid), len(grid[0])))
    assert len(shapes) >= 8


def test_declared_rivals_have_real_counterexamples():
    off_bottom = gen.generate(77, 1, texture="floating")
    assert gen.SEMANTIC_WITNESSES["off_bottom"](off_bottom)
    assert gen.SEMANTIC_RIVALS["grid_bottom_anchor"](off_bottom) == grid_bottom_anchor_rival(off_bottom)
    assert grid_bottom_anchor_rival(off_bottom) != intended_output(off_bottom)

    odd = gen.generate(78, 2, texture="mixed_anchors")
    assert gen.SEMANTIC_WITNESSES["odd_height"](odd)
    assert gen.SEMANTIC_RIVALS["ceil_half"](odd) == ceil_half_rival(odd)
    assert ceil_half_rival(odd) != intended_output(odd)


def test_every_four_pair_window_remains_identifiable_under_query_rotation():
    for start in range(20):
        lesson = [_pair(gen.generate(600 + start, start + offset)) for offset in range(4)]
        for query_index in range(4):
            query = lesson[query_index]
            demos = lesson[:query_index] + lesson[query_index + 1 :]
            assert gen.lesson_identifiable(demos, query) == []
            for competitor in gen.LESSON_COMPETITORS.values():
                fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
                changes_query = competitor(query["input"]) != query["output"]
                assert not (fits and changes_query)


def test_validator_rejects_destructive_mutations():
    base = gen.generate(18, 2, grid_h=11, grid_w=9, n_bars=4, texture="mixed_anchors")

    unknown = deepcopy(base)
    unknown[0][0] = 9
    assert gen.self_check(unknown)

    singleton = deepcopy(base)
    for row in range(len(singleton)):
        singleton[row][1] = 0
    singleton[3][1] = 2
    assert gen.self_check(singleton)

    merged = deepcopy(base)
    # Bridge the first two separated bars into one non-vertical component.
    parts = observed(merged)["columns"]
    left, right = parts[:2]
    row = next(r for r in range(len(merged)) if merged[r][left] == 2)
    for col in range(left + 1, right):
        merged[row][col] = 2
    assert gen.self_check(merged)


@pytest.mark.parametrize("malformed", [None, [], [[]], [[0], [0, 0]], [[True] * 9 for _ in range(7)]])
def test_malformed_grid_is_diagnostic_not_exception(malformed):
    assert gen.self_check(malformed)


def test_oracles_and_generation_do_not_mutate_inputs():
    grid = gen.generate(98, 3)
    original = deepcopy(grid)
    assert intended_output(grid)
    assert gen.SEMANTIC_RIVALS["grid_bottom_anchor"](grid)
    assert grid == original


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(700 + i, i) for i in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_contract_report_finds_replayable_witnesses_for_declared_rivals():
    from reference_probe import build_contract_report

    report = build_contract_report(gen, seeds=range(4), sample_indices=range(8))
    shortcut = report["canonical_shortcuts"]["grid_bottom_anchor"]
    assert shortcut["fits_all_canonical"] is True
    assert shortcut["witness"] is not None
    assert gen.self_check(shortcut["witness"]["input"]) == []
    assert shortcut["witness"]["intended_output"] != shortcut["witness"]["rival_output"]
    assert shortcut["witness"]["different_cells"]

    for name in gen.LESSON_COMPETITORS:
        witness = report["lesson_competitors"][name]["witness"]
        assert witness is not None
        assert witness["intended_output"] != witness["rival_output"]


def test_retained_grid_bottom_anchor_counterexample_replays():
    data = json.loads((HOME / "counterexamples/grid_bottom_anchor.json").read_text())
    grid = data["input"]
    assert gen.self_check(grid) == []
    assert intended_output(grid) == data["intended_output"]
    assert grid_bottom_anchor_rival(grid) == data["rival_output"]
    assert data["different_cells"]
    assert data["intended_output"] != data["rival_output"]


def test_schedule_probe_covers_every_cyclic_start_and_rotation():
    from schedule_probe import build_schedule_report

    report = build_schedule_report(gen, seeds=range(2), difficulties=("easy",))
    assert report["summary"] == {
        "lessons": 8,
        "rotations": 32,
        "ambiguous_rotations": 0,
        "hook_failures": 0,
    }
    assert report["starts"] == [0, 1, 2, 3]
    assert report["counterexamples"] == []
