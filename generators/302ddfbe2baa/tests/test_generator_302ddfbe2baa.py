from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import random
import sys

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR / "workspace"))

from reference_probe import (  # noqa: E402
    audit,
    canonical_pairs,
    load_generator,
    multi_blocker_witness,
    observed,
    pass_through_witness,
    ray_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_pins_authority_and_declares_only_observable_exact_axes():
    assert GEN.RULE_HASH == "923c6879d312"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "emitter_count", "scene_kind"}
    assert tuple(GEN.SCENE_KINDS) == (
        "canonical",
        "pass_through_distractor",
        "multi_blocker",
    )
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert ray_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_schedule_cycles_through_anchor_and_both_counterexample_profiles():
    assert [GEN.schedule_profile(7, index, "medium") for index in range(6)] == [
        "canonical",
        "pass_through_distractor",
        "multi_blocker",
        "canonical",
        "pass_through_distractor",
        "multi_blocker",
    ]
    grids = [GEN.generate(7, index, difficulty="medium") for index in range(6)]
    assert [GEN.observe_overrides(grid)["scene_kind"] for grid in grids] == [
        "canonical",
        "pass_through_distractor",
        "multi_blocker",
        "canonical",
        "pass_through_distractor",
        "multi_blocker",
    ]
    assert [GEN.observe_overrides(grid)["emitter_count"] for grid in grids] == [
        3,
        4,
        1,
        3,
        5,
        2,
    ]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_kind", ["canonical", "pass_through_distractor", "multi_blocker"])
@pytest.mark.parametrize("h,w,count", [(6, 10, 1), (10, 14, 5)])
def test_exact_boundary_overrides_are_visible_in_pixels(band, scene_kind, h, w, count):
    expected = {
        "grid_h": h,
        "grid_w": w,
        "emitter_count": count,
        "scene_kind": scene_kind,
    }
    grid = GEN.generate(19, 11, difficulty=band, **expected)
    assert GEN.self_check(grid, meta={"overrides": expected}) == []
    assert GEN.observe_overrides(grid) == expected
    assert observed(grid) == expected


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 5),
        ("grid_h", 11),
        ("grid_w", 9),
        ("grid_w", 15),
        ("emitter_count", 0),
        ("emitter_count", 6),
        ("grid_h", True),
        ("emitter_count", 2.0),
        ("scene_kind", 2),
        ("scene_kind", "unknown"),
    ],
)
def test_bad_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **{key: value})


def test_pass_through_profile_refutes_nonzero_stop_and_three_emitter_shortcuts():
    expected = {"stop_at_any_nonzero", "first_three_emitters"}
    grid = GEN.generate(91, 1, scene_kind="pass_through_distractor", emitter_count=4)
    intended = ray_output(grid)
    assert GEN.SEMANTIC_WITNESSES["passes_through_non_maroon"](grid)
    assert GEN.SEMANTIC_WITNESSES["every_emitter_matters"](grid)
    for name in expected:
        assert GEN.SEMANTIC_RIVALS[name](grid) != intended

    exact = pass_through_witness()
    assert GEN.self_check(exact) == []
    assert GEN.SEMANTIC_RIVALS["stop_at_any_nonzero"](exact) != ray_output(exact)


def test_multi_blocker_profile_refutes_rightmost_and_nearest_direction_shortcuts():
    expected = {"rightmost_maroon", "toward_nearest_maroon"}
    grid = GEN.generate(92, 2, scene_kind="multi_blocker", emitter_count=3)
    intended = ray_output(grid)
    assert GEN.SEMANTIC_WITNESSES["first_right_maroon_stops"](grid)
    assert GEN.SEMANTIC_WITNESSES["rightward_not_nearest_maroon"](grid)
    for name in expected:
        assert GEN.SEMANTIC_RIVALS[name](grid) != intended

    exact = multi_blocker_witness()
    assert GEN.self_check(exact) == []
    for name in expected:
        assert GEN.SEMANTIC_RIVALS[name](exact) != ray_output(exact)


def test_every_declared_canonical_shortcut_really_fits_all_public_pairs():
    expected = {
        "stop_at_any_nonzero",
        "rightmost_maroon",
        "toward_nearest_maroon",
        "first_three_emitters",
    }
    assert expected == set(GEN.CANONICAL_SHORTCUTS)
    assert expected == set(GEN.SEMANTIC_RIVALS)
    assert expected <= set(GEN.LESSON_COMPETITORS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_every_three_consecutive_generated_demos_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for seed in (1, 91, 20261003):
            for start in range(12):
                demos = []
                for index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, index, difficulty=band)
                    demos.append({"input": grid, "output": ray_output(grid)})
                survivors = [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                assert survivors == [], (band, seed, start, survivors)


def test_lesson_hook_rejects_canonical_only_demos_and_accepts_generated_window():
    canonical = canonical_pairs()
    query_grid = multi_blocker_witness()
    assert GEN.lesson_identifiable(
        canonical[:3],
        {"input": query_grid, "output": ray_output(query_grid)},
    )

    demos = []
    for index in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(33, index, difficulty="hard")
        demos.append({"input": grid, "output": ray_output(grid)})
    query_grid = GEN.generate(33, GEN.EXAMPLES_NEEDED, difficulty="hard")
    assert GEN.lesson_identifiable(
        demos,
        {"input": query_grid, "output": ray_output(query_grid)},
    ) == []


def test_strict_schedule_hits_each_canonical_profile_and_non_strict_probes():
    expected_shapes = {
        "easy": (6, 10),
        "medium": (7, 11),
        "hard": (6, 12),
    }
    for band, shape in expected_shapes.items():
        anchor = GEN.generate(101, 0, difficulty=band)
        assert (len(anchor), len(anchor[0])) == shape
        assert GEN.strict_canonical_like(anchor) == []
        assert GEN.strict_canonical_like(GEN.generate(101, 1, difficulty=band))
        assert GEN.strict_canonical_like(GEN.generate(101, 2, difficulty=band))


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 4]],
        [[0] * 10 for _ in range(6)],
        [[0, 0, 0, 0, 4, 0, 0, 0, 0, 0], *([[0] * 10] * 5)],
        [[4] * 10 for _ in range(6)],
        [[0, 4, 0, 9, 0, 2, 0, 0, 0, 0]] * 6,
    ],
)
def test_self_check_rejects_malformed_and_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991)
    before = random.getstate()
    first = GEN.generate(2026, 11, difficulty="hard")
    second = GEN.generate(2026, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == before


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(77, 2)
    before = deepcopy(grid)
    assert GEN.rule_mirror(grid) == ray_output(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == before


def test_portable_reference_probe_reports_no_cyclic_lesson_failures():
    report = audit(GEN, starts=6, seeds=(1,))
    assert report["passed"] is True
    assert report["generator_sha256"] == hashlib.sha256(
        Path(GEN.__file__).read_bytes()
    ).hexdigest()
    assert report["rule_hash"] == GEN.RULE_HASH
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(
        row["matches"] == report["canonical_pairs"]
        for row in report["canonical_shortcuts"].values()
    )
    assert all(
        not row["lesson_contract_failures"]
        for row in report["by_band"].values()
    )
