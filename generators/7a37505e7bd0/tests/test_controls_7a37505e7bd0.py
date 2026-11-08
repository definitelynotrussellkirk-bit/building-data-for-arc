"""Public call-contract regressions; no source-layout assumptions."""
import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("7a37505e7bd0", root=find_root(__file__))


@pytest.mark.parametrize("band", ["easy", None, "hard"])
@pytest.mark.parametrize("value", [True, False, "1", "5", 1.0, 1.75, 5.0, 5.75, -1, 0, 6])
def test_color_count_rejects_invalid_scalar_without_coercion(band, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, 0, difficulty=band, color_count=value)


@pytest.mark.parametrize("field,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "__invalid_difficulty__"),
    ("difficulty", []), ("difficulty", {}),
])
def test_invalid_call_scalars_fail_at_the_public_boundary(field, value):
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": "medium"}
    kwargs[field] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_valid_integer_controls_and_none_sentinel_remain_supported(band):
    for seed in (-7, 0, 991, 2**63):
        assert GEN.generate(seed, 3, difficulty=band, color_count=None) == GEN.generate(
            seed, 3, difficulty=band
        )
        for count in range(1, 6):
            grid = GEN.generate(seed, 3, difficulty=band, color_count=count)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"color_count": count}


def test_declared_semantic_schedule_period_matches_all_observables():
    period = getattr(GEN, "LESSON_SCHEDULE_PERIOD", None)
    assert period == 5
    for band in ("easy", "medium", "hard"):
        for seed in range(9):
            for start in range(period):
                first = GEN.generate(seed, start, difficulty=band)
                repeated = GEN.generate(seed, start + period, difficulty=band)
                assert GEN.semantic_observables(first) == GEN.semantic_observables(repeated)
