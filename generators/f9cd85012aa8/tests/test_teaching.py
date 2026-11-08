"""Independent finite-rival regression checks; full labels use the Racket census."""
from __future__ import annotations

import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator("f9cd85012aa8", root=find_root(__file__))
    return module


def intended(grid):
    """Independent authoring mirror, checked against all canonical labels below."""
    six = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    assert six
    low_r, high_r = min(r for r, _ in six), max(r for r, _ in six)
    low_c, high_c = min(c for _, c in six), max(c for _, c in six)
    return [[6 if low_r <= r <= high_r and low_c <= c <= high_c else 0
             for c in range(len(grid[0]))] for r in range(len(grid))]


def rivals(generator):
    declared = getattr(generator, "CANONICAL_SHORTCUTS", None)
    assert isinstance(declared, dict) and declared, "missing executable canonical shortcut contract"
    return declared


def test_every_declared_shortcut_fits_every_labeled_canonical_pair(generator):
    pairs = canonical_pairs("f9cd85012aa8", root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert intended(pair["input"]) == pair["output"]
        for name, rival in rivals(generator).items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("seed", [0, 7, 17])
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_cyclic_window_has_redundant_refutations(generator, seed, band):
    alternatives = rivals(generator)
    period = generator.LESSON_SCHEDULE_PERIOD
    n_pairs = generator.EXAMPLES_NEEDED + 1
    assert period == 8 and n_pairs == 8
    pairs = []
    for index in range(period + n_pairs - 1):
        grid = generator.generate(seed, index, difficulty=band)
        assert not generator.self_check(grid, difficulty=band)
        pairs.append({"input": grid, "output": intended(grid)})
    for start in range(period):
        window = pairs[start:start+n_pairs]
        assert len({json.dumps(pair["input"]) for pair in window}) == n_pairs
        for name, rival in alternatives.items():
            refuting = [i for i, pair in enumerate(window)
                        if rival(pair["input"]) != pair["output"]]
            assert len(refuting) >= 2, (seed, band, start, name, refuting)
        for query_index, query in enumerate(window):
            demos = [pair for i, pair in enumerate(window) if i != query_index]
            assert generator.lesson_identifiable(demos, query) == []


def test_hook_reports_a_real_under_taught_query(generator):
    alternatives = rivals(generator)
    core_grid = generator.generate(0, 0, difficulty="medium")
    core = {"input": core_grid, "output": intended(core_grid)}
    query_grid = generator.generate(0, 1, difficulty="medium")
    query = {"input": query_grid, "output": intended(query_grid)}
    # A correct label on a single sparse color-6 example does not tell the
    # learner which differently colored distractors the rule must erase.
    ambiguous = [name for name, rival in alternatives.items()
                 if rival(core["input"]) == core["output"] and rival(query_grid) != query["output"]]
    assert ambiguous
    reasons = generator.lesson_identifiable([core], query)
    assert reasons and all(isinstance(reason, str) for reason in reasons)


def test_pixel_count_rank_does_not_determine_area_rank(generator):
    count_order, area_order = [], []
    def area(cells):
        return ((max(r for r, c in cells) - min(r for r, c in cells) + 1)
                * (max(c for r, c in cells) - min(c for r, c in cells) + 1))
    for index in (1, 3, 5, 7):
        grid = generator.generate(7, index, difficulty="hard")
        colors = {value for row in grid for value in row if value}
        objects = {color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                           if value == color] for color in colors}
        target = objects[6]
        count_order.append(sum(len(cells) < len(target) for color, cells in objects.items() if color != 6))
        area_order.append(sum(area(cells) < area(target) for color, cells in objects.items() if color != 6))
    assert count_order != area_order, "target pixel-count rank equals bbox-area rank in every rich profile"
    assert count_order[1] == count_order[3] == 1
    assert area_order[1] != area_order[3], "middle-count profiles still force the same area rank"
