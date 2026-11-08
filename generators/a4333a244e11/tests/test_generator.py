"""Task-local regression suite for the two-seed Manhattan Voronoi sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path
import random
import shutil
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    ascending_position_rival,
    axis_aligned_ascending_rival,
    axis_aligned_lower_color_tie_rival,
    canonical_pairs,
    canonical_rule_hash,
    euclidean_rival,
    load_generator,
    lower_color_tie_rival,
    observed,
    racket_outputs,
    rule_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

from reviewer_support import canonical_path, find_root  # noqa: E402


def labelled(grid):
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_authority_is_pinned_and_python_oracle_matches_every_canonical_pair():
    assert GEN.RULE_HASH == canonical_rule_hash() == "d568e0e496cf"
    assert len(canonical_pairs()) == 3
    for pair in canonical_pairs():
        before = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        # Framework canonical checks pass an empty metadata mapping; that must
        # not trigger generated-only public-axis observation.
        assert GEN.self_check(pair["input"], meta={}) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert rule_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_reference_probe_finds_canonical_data_after_relocation(tmp_path):
    runtime = tmp_path / "portable-runtime"
    canonical = runtime / "data" / "canonical" / "puzzles.jsonl"
    canonical.parent.mkdir(parents=True)
    source_root = find_root(__file__)
    shutil.copy2(canonical_path(source_root), canonical)

    relocated = runtime / "nested" / "workspace" / "reference_probe.py"
    relocated.parent.mkdir(parents=True)
    shutil.copy2(HOME / "workspace" / "reference_probe.py", relocated)
    spec = importlib.util.spec_from_file_location("relocated_reference_probe", relocated)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.canonical_rule_hash() == "d568e0e496cf"
    assert len(module.canonical_pairs()) == 3


def test_public_axes_are_real_and_have_no_declared_incompatibilities():
    assert set(GEN.AXES) == {
        "frame_h",
        "frame_w",
        "palette_kind",
        "alignment",
        "tie_mode",
        "color_order",
    }
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("frame_h,frame_w", [(5, 7), (5, 14), (10, 7), (10, 14)])
def test_dimension_boundary_overrides_are_exact_in_every_band(band, frame_h, frame_w):
    requested = {
        "frame_h": frame_h,
        "frame_w": frame_w,
        "palette_kind": "varied",
        "alignment": "diagonal",
        "tie_mode": "present",
        "color_order": "descending",
    }
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "palette_kind,alignment,tie_mode,color_order",
    itertools.product(
        ("canonical", "warm", "cool", "varied"),
        ("row", "column", "diagonal"),
        ("present", "absent"),
        ("ascending", "descending"),
    ),
)
def test_every_semantic_axis_cross_product_is_constructive(
    band, palette_kind, alignment, tie_mode, color_order
):
    requested = {
        "frame_h": 5,
        "frame_w": 7,
        "palette_kind": palette_kind,
        "alignment": alignment,
        "tie_mode": tie_mode,
        "color_order": color_order,
    }
    grid = GEN.generate(73, 4, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observed(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"texture": "warm"},
        {"frame_h": 4},
        {"frame_h": 11},
        {"frame_h": True},
        {"frame_h": 5.0},
        {"frame_w": 6},
        {"frame_w": 15},
        {"palette_kind": "unknown"},
        {"alignment": "horizontal"},
        {"tie_mode": "sometimes"},
        {"color_order": "random"},
    ],
)
def test_invalid_retired_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError), match="override|axis|frame|palette|alignment|tie|color"):
        GEN.generate(0, 0, **overrides)


def test_default_four_profile_schedule_makes_every_three_demo_rotation_identifiable():
    assert GEN.EXAMPLES_NEEDED == 3
    assert len(GEN.SCHEDULE_PROFILES) == 4
    assert {
        GEN.schedule_profile(0, index, "medium") for index in range(4)
    } == set(GEN.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [
                labelled(GEN.generate(900 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, pairs[query_index]) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert not all(rival(pair["input"]) == pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_default_schedule_refutes_axis_conditional_shortcuts_in_every_rotation():
    rivals = {
        "ascending_colors_on_axis_aligned": axis_aligned_ascending_rival,
        "lower_color_ties_on_axis_aligned": axis_aligned_lower_color_tie_rival,
    }
    assert set(rivals) <= set(GEN.SEMANTIC_RIVALS)
    assert set(rivals) <= set(GEN.LESSON_COMPETITORS)
    assert {
        "axis_aligned_descending_colors",
        "axis_aligned_ties_stay_zero",
    } <= set(GEN.SEMANTIC_WITNESSES)
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [
                labelled(GEN.generate(1900 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for name, rival in rivals.items():
                    assert not all(rival(pair["input"]) == pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_canonical_color_order_shortcut_fits_canonical_and_generated_schedule_refutes_it():
    name = "ascending_position_colors"
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.LESSON_COMPETITORS
    assert all(ascending_position_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for start in range(4):
        grids = [GEN.generate(211, start + offset, difficulty="medium") for offset in range(3)]
        assert any(ascending_position_rival(grid) != rule_output(grid) for grid in grids)
        assert any(GEN.SEMANTIC_WITNESSES["descending_position_colors"](grid) for grid in grids)


def test_declared_tie_and_metric_witnesses_are_real_counterexamples():
    grids = [GEN.generate(712, index, difficulty="hard") for index in range(4)]
    assert any(lower_color_tie_rival(grid) != rule_output(grid) for grid in grids)
    assert any(euclidean_rival(grid) != rule_output(grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["tie_cells_stay_zero"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["manhattan_not_euclidean"](grid) for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_diverse_and_covers_profiles(band):
    profiles = set()
    shapes = set()
    inputs = set()
    values = {name: set() for name in GEN.AXES}
    for index in range(80):
        grid = GEN.generate(5000 + index, index, difficulty=band)
        assert grid == GEN.generate(5000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == rule_output(grid)
        stats = observed(grid)
        for name, value in stats.items():
            values[name].add(value)
        profiles.add(GEN.schedule_profile(5000 + index, index, band))
        shapes.add((len(grid), len(grid[0])))
        inputs.add(tuple(map(tuple, grid)))
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert len(inputs) >= 75
    assert len(shapes) >= 6
    assert values["palette_kind"] == {"canonical", "warm", "cool", "varied"}
    assert values["alignment"] == {"row", "column", "diagonal"}
    assert values["tie_mode"] == {"present", "absent"}
    assert values["color_order"] == {"ascending", "descending"}


def test_validator_rejects_destructive_mutations():
    original = GEN.generate(31, 0, frame_h=6, frame_w=10)
    mutations = []
    missing_frame = deepcopy(original)
    missing_frame[1][1] = 0
    mutations.append(missing_frame)
    extra_seed = deepcopy(original)
    extra_seed[2][2] = next(color for color in range(1, 10) if color not in (8, *[v for row in original for v in row if v not in (0, 8)]))
    mutations.append(extra_seed)
    outer_noise = deepcopy(original)
    outer_noise[0][0] = 9
    mutations.append(outer_noise)
    same_seed_color = deepcopy(original)
    seeds = [(r, c) for r, row in enumerate(same_seed_color) for c, value in enumerate(row) if value not in (0, 8)]
    same_seed_color[seeds[1][0]][seeds[1][1]] = same_seed_color[seeds[0][0]][seeds[0][1]]
    mutations.append(same_seed_color)
    for grid in mutations:
        assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(7)], [[10] * 11 for _ in range(7)]],
)
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    before = deepcopy(grid)
    assert GEN.self_check(grid)
    assert grid == before


def test_generation_does_not_touch_global_random_state_and_returns_fresh_rows():
    random.seed(1234)
    state = random.getstate()
    first = GEN.generate(823, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(823, 103, difficulty="hard")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_real_racket_authority_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [GEN.generate(404 + index, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(12)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
