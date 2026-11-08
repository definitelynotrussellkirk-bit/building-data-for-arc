"""Behavioral regressions for the selected sampler, in either portable layout."""
from collections import Counter
from itertools import product

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator("538503abef57", root=ROOT)


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    found = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        stack, cells = [start], set()
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in remaining and grid[p[0]][p[1]] == color:
                    remaining.remove(p)
                    stack.append(p)
        found.append((color, cells))
    return found


def oracle(grid):
    """Independent test oracle only; production labels still come from Racket."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
        for r, c in cells:
            out[r0+c1-c][c0+r1-r] = color
    return out


def test_all_canonical_inputs_are_accepted_and_oracle_matches_labels():
    pairs = canonical_pairs("538503abef57", root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [[], [[]], [[0] * 8 for _ in range(8)],
                                 [[10, 0], [0, 0]], [[True, 0], [0, 0]],
                                 [[1.0, 0], [0, 0]], [[0, 0], [0]],
                                 [[1, 1, 1], [0, 0, 0], [0, 0, 0]]])
def test_validator_rejects_malformed_or_outside_square_object_domain(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize("value", [True, 9.0, "9", -1, 31])
def test_scalar_overrides_never_coerce(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, grid_h=value)


def test_unknown_override_is_an_error():
    with pytest.raises(ValueError, match="unknown"):
        GEN.generate(0, 0, typo_axis=2)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"seed": "1"},
    {"sample_index": False}, {"sample_index": -1},
    {"difficulty": True}, {"difficulty": False}, {"difficulty": 0},
    {"difficulty": 1.0}, {"difficulty": "__invalid_difficulty__"},
])
def test_call_arguments_have_a_strict_reproducible_contract(kwargs):
    args = {"seed": 0, "sample_index": 0, "difficulty": "easy", **kwargs}
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(**args)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_full_declared_size_domain_is_available_in_every_band(band):
    for h, w in product((8, 16), repeat=2):
        grid = GEN.generate(7, 3, difficulty=band, grid_h=h, grid_w=w)
        assert (len(grid), len(grid[0])) == (h, w)
        assert GEN.self_check(grid) == []


def test_joint_counts_are_realized_or_explicitly_incompatible():
    for n, colors in product(range(2, 5), range(2, 6)):
        if colors > n + 1:
            with pytest.raises(ValueError):
                GEN.generate(12, 4, n_objects=n, n_distinct_colors=colors)
            continue
        for band in ("easy", "medium", "hard"):
            grid = GEN.generate(12, 4, difficulty=band, grid_h=8, grid_w=8,
                                n_objects=n, n_distinct_colors=colors)
            assert len(components(grid)) == n
            assert len({v for row in grid for v in row}) == colors
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            assert observed["n_objects"] == n
            assert observed["n_distinct_colors"] == colors


def test_generated_components_and_their_outputs_are_preserved():
    for band, seed, index in product(("easy", "medium", "hard"), range(5), range(16)):
        grid = GEN.generate(seed, index, difficulty=band)
        assert GEN.self_check(grid) == []
        out = oracle(grid)
        assert Counter(v for row in grid for v in row) == Counter(v for row in out for v in row)
        assert len(components(grid)) == len(components(out))
        assert oracle(out) == grid
        assert grid == GEN.generate(seed, index, difficulty=band)


def test_default_lessons_refute_declared_rivals_under_every_query_rotation():
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert {"by_color", "fixed_three"} <= set(rivals)
    for band, seed, start in product(("easy", "medium", "hard"), range(5), range(6)):
        pairs = [(g, oracle(g)) for g in
                 (GEN.generate(seed, start+i, difficulty=band) for i in range(4))]
        for query in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query]
            for name, rival in rivals.items():
                assert any(rival(g) != y for g, y in demos), (name, band, seed, start, query)


def test_declared_canonical_shortcuts_fit_every_labeled_pair():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert {"by_color", "fixed_three"} <= set(rivals)
    for pair in canonical_pairs("538503abef57", root=ROOT):
        for name, rival in rivals.items():
            assert rival(pair["input"]) == pair["output"], name


def test_racket_matches_independent_oracle_on_canonical_and_generated_inputs():
    from arcpuzzles import Catalog

    inputs = [p["input"] for p in canonical_pairs("538503abef57", root=ROOT)]
    inputs += [GEN.generate(23, i, difficulty=band)
               for band in ("easy", "medium", "hard") for i in range(4)]
    receipt = Catalog(ROOT).apply("538503abef57", inputs, check_generator_domain=True)
    assert receipt["generator_sha256"] == SOURCE_SHA
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert len(receipt["results"]) == 15
    for row in receipt["results"]:
        assert row["error"] is None
        assert row["generator_domain"]["status"] == "valid"
        assert row["output"] == oracle(row["input"])
