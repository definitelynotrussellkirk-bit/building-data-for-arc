"""Regressions for ordinary draws silently losing a colliding endpoint."""
from collections import Counter

import pytest

from reviewer_support import find_root, load_selected_generator


@pytest.mark.parametrize(
    "difficulty, expected_counts",
    [("medium", {8: 3, 1: 3}), ("hard", {4: 4, 2: 4, 1: 4, 6: 2})],
)
def test_collision_preserves_every_sampled_endpoint(monkeypatch, difficulty, expected_counts):
    generator, _, _ = load_selected_generator(
        "84fd4bcdc53c", root=find_root(__file__)
    )
    # Retain the historical random stream even if a later release changes VERSION.
    monkeypatch.setattr(generator, "VERSION", "2.1.1")
    # The medium color-1 draw was (2, 0), (1, 7), (3, 10); its last two
    # positions coincide with color 8. The sampler must retain all three.
    grid = generator.generate(6, 0, difficulty=difficulty)
    counts = Counter(cell for row in grid for cell in row if cell)
    assert counts == expected_counts
    assert generator.self_check(grid, difficulty=difficulty) == []
