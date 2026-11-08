"""Finite-rival lesson properties; labels are independently checked by Racket gates."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("8096ecc43d5a", root=ROOT)


def test_eight_declared_shortcuts_fit_all_canonical_labels():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert len(shortcuts) == 8
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
        for name, rival in shortcuts.items():
            assert rival(pair["input"]) == pair["output"], name


def test_authoring_diagnostic_matches_canonical_sequential_outputs():
    assert callable(getattr(GEN, "_prediction", None))
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
        assert GEN._prediction(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_cyclic_start_and_query_position_refutes_declared_rivals(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert len(rivals) == 12
    # Includes period boundaries and independently randomized schedule offsets.
    for seed in range(16):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(11)]
        labels = [GEN._prediction(grid) for grid in grids]
        for start in range(8):
            for query in range(4):
                demos = [start + j for j in range(4) if j != query]
                for name, rival in rivals.items():
                    assert any(rival(grids[j]) != labels[j] for j in demos), (seed, start, query, name)


def test_rivals_are_pure_and_repeatable():
    rivals = getattr(GEN, "SEMANTIC_RIVALS", {})
    assert rivals
    grid = GEN.generate(28, 3)
    for rival in rivals.values():
        original = deepcopy(grid)
        predicted = rival(grid)
        assert grid == original
        assert rival(grid) == predicted


def test_default_support_includes_symmetry_color_overlap_and_all_script_lengths():
    assert callable(getattr(GEN, "observe_overrides", None))
    lengths, colors, orbits = set(), set(), set()
    overlap = False
    for index in range(300):
        grid = GEN.generate(901, index, difficulty="hard")
        observed = GEN.observe_overrides(grid)
        lengths.add(observed["n_codes"])
        colors.add(observed["motif_color"])
        overlap |= observed["motif_color"] in grid[0]
        cells = [(r, c) for r, row in enumerate(grid[2:]) for c, v in enumerate(row) if v]
        orbits.add(GEN._orbit_size(cells))
    assert lengths == set(range(1, 7))
    assert colors == set(range(1, 10))
    assert overlap
    assert 8 in orbits and any(n < 8 for n in orbits)


@pytest.mark.parametrize("size", range(4, 13))
def test_constructive_fallback_preserves_size_connectivity_and_asymmetry(size):
    class StraightGrowth:
        def choice(self, candidates):
            return candidates[0]

    cells = GEN._motif_cells(StraightGrowth(), size, 5, 8, True)
    assert len(set(cells)) == size
    assert max(r for r, _ in cells) < 5
    assert max(c for _, c in cells) < 8
    assert GEN._orbit_size(cells) == 8
    grid = [[0] * 8 for _ in range(7)]
    grid[0][0] = 1
    for r, c in cells:
        grid[r + 2][c] = 8
    assert GEN.self_check(grid) == []
