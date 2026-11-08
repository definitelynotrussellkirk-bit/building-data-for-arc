"""Regression tests for strict request scalars and canonical palette roles."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator


gen, _SOURCE, _SOURCE_SHA256 = load_selected_generator(
    "c00a9bcded8e", root=find_root(__file__)
)


def test_generate_rejects_invalid_seed_and_sample_index_scalars():
    invalid_seed_values = (True, False, 1.0, 1.75, "1")
    invalid_index_values = (True, False, 1.0, 1.75, "1", -1)

    for value in invalid_seed_values:
        try:
            gen.generate(value, 0, difficulty="easy")
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"invalid seed scalar was accepted: {value!r}")

    for value in invalid_index_values:
        try:
            gen.generate(991, value, difficulty="easy")
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"invalid sample_index scalar was accepted: {value!r}")


def test_default_schedule_uses_exactly_five_target_colors_like_canonical():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = gen.generate(23100 + sample_index, sample_index, difficulty=band)
            facts, errors = gen._analyze(grid)
            assert errors == []
            assert len(facts["target_colors"]) == 5
            assert len(facts["noise_colors"]) == 2
            assert facts["target_colors"].isdisjoint(facts["noise_colors"])
