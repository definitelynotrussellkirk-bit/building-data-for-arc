"""Regression for a canonical-fitting c <= anchor-column shortcut.

The exact pre-repair Racket lesson is retained in
counterexamples/left_anchor_before.json. This test regenerates its recipe so
the repaired sampler, rather than frozen old examples, must teach the rule.
"""
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator("b1972482cb43", root=ROOT)
SEED = 2943442411
DIFFICULTY = "easy"
SAMPLE_INDICES = (19, 20, 21, 22, 23)


def reflection_model(grid, *, left_half_plane_only=False):
    """Input-only model independent of the selected generator's rival code."""
    output = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    (ar, ac), = [(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value == 9]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9) or (left_half_plane_only and c > ac):
                continue
            rr, cc = 2 * ar - r, 2 * ac - c
            if 0 <= rr < h and 0 <= cc < w:
                output[rr][cc] = value
    return output


def left_of_anchor_only(grid):
    """Include the anchor column: c <= ac, not the non-fitting c < ac."""
    return reflection_model(grid, left_half_plane_only=True)


def test_left_half_plane_rule_fits_every_labeled_canonical_pair():
    pairs = canonical_pairs("b1972482cb43", root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert reflection_model(pair["input"]) == pair["output"]
        assert left_of_anchor_only(pair["input"]) == pair["output"]


def test_production_and_every_holdout_teach_both_sides_of_anchor():
    grids = [GENERATOR.generate(SEED, index, difficulty=DIFFICULTY)
             for index in SAMPLE_INDICES]
    agreements = [left_of_anchor_only(grid) == reflection_model(grid) for grid in grids]
    for heldout in range(len(grids)):
        demos_fit = all(equal for i, equal in enumerate(agreements) if i != heldout)
        query_differs = not agreements[heldout]
        assert not (demos_fit and query_differs), (
            "c <= anchor_c fits all demonstrations and changes the query: "
            f"seed={SEED}, difficulty={DIFFICULTY}, sample_indices={SAMPLE_INDICES}, "
            f"heldout_sample_index={SAMPLE_INDICES[heldout]}, agreements={agreements}"
        )
    assert agreements.count(False) >= 2, "the window must contain two distinct side-refutation witnesses"
