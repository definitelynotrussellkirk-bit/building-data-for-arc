"""Regression tests for after-battery blockers found in review 0c40bbcc130315b0."""
from __future__ import annotations

import hashlib

import pytest

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "888fb4310749"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize(
    "bad_index", [True, False, 1.0, 1.75, "1", -1]
)
def test_generate_rejects_invalid_sample_index_scalars(bad_index):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, bad_index, difficulty="hard")


def test_profile_floor_has_exact_canonical_support_in_every_band():
    canonical_profiles = {
        _profile(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=False)
    }
    hits = {}
    for band in ("easy", "medium", "hard"):
        band_hits = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            band_hits += _profile(grid) in canonical_profiles
        hits[band] = band_hits
    assert all(count >= 1 for count in hits.values()), hits


def test_semantic_contract_accepts_canonical_and_refutes_declared_rivals():
    expected_witnesses = {
        "periodic_stamping_changes_input",
        "complement_color_is_visible",
        "non_36_source_color",
    }
    expected_rivals = {
        "identity_no_stamping",
        "source_blocks_only",
        "fixed_3_6_complement",
    }
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.SEMANTIC_WITNESSES) == expected_witnesses
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.WITNESS_RIVALS) == expected_witnesses
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert GEN.strict_canonical_like(pair["input"]) == []

    witness_seen = {name: False for name in expected_witnesses}
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(20261023, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            truth = GEN.rule_mirror(grid)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_seen[name] = True
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival](grid) != truth
                        for rival in GEN.WITNESS_RIVALS[name]
                    )
    assert all(witness_seen.values()), witness_seen

    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(731, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
    for rival in GEN.LESSON_COMPETITORS.values():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3])


def test_lesson_hook_rejects_the_fixed_36_color_shortcut_when_it_survives_demos():
    demo_inputs = [
        GEN._rect_grid(16, 16, 3, 2, 1, 3, 3),
        GEN._rect_grid(16, 17, 6, 13, 2, 1, 6),
        GEN._rect_grid(20, 18, 6, 3, 3, 1, 3),
    ]
    query_input = GEN._rect_grid(18, 19, 4, 5, 2, 3, 1)
    demos = [
        {"input": grid, "output": GEN.rule_mirror(grid)} for grid in demo_inputs
    ]
    query = {"input": query_input, "output": GEN.rule_mirror(query_input)}

    reasons = GEN.lesson_identifiable(demos, query)

    assert any("fixed_3_6_complement" in reason for reason in reasons), reasons


def test_production_four_pair_windows_refute_all_declared_rivals_in_every_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for sample_index in range(start, start + 4):
                grid = GEN.generate(424242, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.SEMANTIC_RIVALS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (band, start, query_index, name)


def test_odd_curriculum_samples_preserve_scene_profile_draw_provenance():
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in range(30):
                grid = GEN.generate(seed, 1, difficulty=band)
                drawn = contexts[-1].axis_value("scene_profile")
                observed = GEN.observe_overrides(grid)["scene_profile"]
                assert observed == drawn, (band, seed, drawn, observed)
    finally:
        set_ctx_observer(None)
