"""Portable regressions for override safety and finite-rival teaching support."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator("cf5ccd73cfe5", root=ROOT)
PROFILES = {(19, 22, 3), (18, 21, 3), (21, 24, 3), (24, 26, 3)}


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_integer_call_arguments(value):
    with pytest.raises(ValueError, match="seed.*integer"):
        gen.generate(value, 0, difficulty="easy")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_integer(value):
    with pytest.raises(ValueError, match="sample_index.*nonnegative integer"):
        gen.generate(991, value, difficulty="easy")


@pytest.mark.parametrize("value", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_difficulty_rejects_non_band_call_arguments(value):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(991, 0, difficulty=value)


@pytest.mark.parametrize("value", [123, None])
def test_unknown_override_is_rejected_even_when_null(value):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", __override_contract_unknown_axis__=value)


@pytest.mark.parametrize("axis,valid", [
    ("grid_h", 18), ("grid_w", 21), ("marker_h", 2),
    ("marker_w", 3), ("scale_h", 2), ("scale_w", 3),
])
@pytest.mark.parametrize("kind", ["bool", "float", "string"])
def test_exact_integer_controls_reject_coercion(axis, valid, kind):
    value = {"bool": True, "float": valid + 0.75, "string": str(valid)}[kind]
    with pytest.raises(ValueError, match="integer"):
        gen.generate(7, 1, difficulty="medium", **{axis: value})


def test_none_still_means_no_override_for_declared_axes():
    baseline = gen.generate(7, 2, difficulty="medium")
    assert gen.generate(7, 2, difficulty="medium", grid_h=None, marker_w=None) == baseline


def test_canonical_profile_support_is_present_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(0, i, difficulty=band) for i in range(20)]
        hits = sum((len(g), len(g[0]), len({x for r in g for x in r})) in PROFILES for g in grids)
        assert hits >= 5, (band, hits)


def test_strict_contract_accepts_all_canonical_inputs_and_has_generated_support():
    assert callable(getattr(gen, "strict_canonical_like", None))
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
        assert gen.strict_canonical_like(pair["input"]) == []
    for band in ("easy", "medium", "hard"):
        hits = sum(gen.strict_canonical_like(gen.generate(0, i, difficulty=band)) == []
                   for i in range(20))
        assert hits >= 5, (band, hits)


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    rivals = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert len(rivals) >= 5
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
        for name, rival in rivals.items():
            assert rival(pair["input"]) == pair["output"], name


def test_authoring_mirror_matches_saved_canonical_outputs():
    assert callable(getattr(gen, "_intended_output", None))
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
        assert gen._intended_output(pair["input"]) == pair["output"]


def test_every_cyclic_window_has_two_rival_refuting_inputs():
    assert getattr(gen, "LESSON_SCHEDULE_PERIOD", None) == 4
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(4):
                rich = 0
                for i in range(start, start + 4):
                    grid = gen.generate(seed, i, difficulty=band)
                    out = gen._intended_output(grid)
                    rich += all(rival(grid) != out for rival in gen.CANONICAL_SHORTCUTS.values())
                assert rich >= 2, (band, seed, start, rich)


def test_three_demonstrations_refute_declared_rivals_in_every_query_rotation():
    assert callable(getattr(gen, "lesson_identifiable", None))
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(4):
                pairs = []
                for i in range(start, start + 4):
                    grid = gen.generate(seed, i, difficulty=band)
                    pairs.append({"input": grid, "output": gen._intended_output(grid)})
                for qi, query in enumerate(pairs):
                    demos = [pair for j, pair in enumerate(pairs) if j != qi]
                    assert gen.lesson_identifiable(demos, query) == [], (band, seed, start, qi)
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
