"""Canonical-fit and complete-lesson regressions for the v3.1 repair."""
from collections import Counter, deque
from copy import deepcopy
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from review_diagnostics import structural_signature

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("3e0aef964b9e", root=ROOT)


def horizontal_row_span(grid):
    """Independent rival: horizontal interpolation, without a convex hull."""
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    colors = sorted(set(counts) - {background})
    matches = []
    for target in colors:
        donor = next(color for color in colors if color != target)
        donors = {(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == donor}
        remaining = {(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == target}
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            queue = deque([start])
            component = {start}
            while queue:
                r, c = queue.popleft()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        neighbor = (r + dr, c + dc)
                        if neighbor in remaining:
                            remaining.remove(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
            missing = set()
            for r in {r for r, _ in component}:
                columns = [c for rr, c in component if rr == r]
                missing.update((r, c) for c in range(min(columns), max(columns) + 1)
                               if grid[r][c] == background)
            if missing and len(missing) == len(donors):
                matches.append((donor, donors, missing))
    output = deepcopy(grid)
    if len(matches) == 1:
        donor, donors, missing = matches[0]
        for r, c in donors:
            output[r][c] = background
        for r, c in missing:
            output[r][c] = donor
    return output


def test_every_advertised_canonical_shortcut_fits_all_labeled_pairs():
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert GEN.CANONICAL_SHORTCUTS, "Retain at least one measured canonical-fitting rival"
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        mismatches = [i for i, pair in enumerate(pairs)
                      if rival(deepcopy(pair["input"])) != pair["output"]]
        assert not mismatches, (name, mismatches)


def test_horizontal_interpolation_is_a_real_canonical_shortcut():
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
        assert horizontal_row_span(pair["input"]) == pair["output"]
    assert "horizontal_row_span" in GEN.CANONICAL_SHORTCUTS
    assert "horizontal_row_span" in GEN.LESSON_COMPETITORS


def test_three_demos_refute_row_spans_at_every_six_cycle_start_and_rotation():
    # Six starts include every hole-count/profile combination, rather than
    # testing only the three semantic-profile residues.
    for seed in (0, 313):
        for band in ("easy", "medium", "hard"):
            grids = [GEN.generate(seed, i, difficulty=band) for i in range(9)]
            matches = [horizontal_row_span(g) == GEN.rule_mirror(g) for g in grids]
            for start in range(6):
                for query in range(4):
                    demo_indices = [start + i for i in range(4) if i != query]
                    assert any(not matches[i] for i in demo_indices), (
                        seed, band, start, query, matches[start:start + 4]
                    )


def test_dense_profiles_expose_hull_cells_outside_horizontal_spans():
    for index in (0, 2):
        for holes in range(1, 7):
            grid = GEN.generate(2718, index, n_holes=holes)
            assert GEN.self_check(grid) == []
            assert horizontal_row_span(grid) != GEN.rule_mirror(grid), (index, holes)


def test_sampled_persistent_marker_support_overlaps_canonical_support():
    canonical = {structural_signature(pair)["persistent_markers"]
                 for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)}
    for band in ("easy", "medium", "hard"):
        generated = set()
        for seed in range(1, 9):
            grid = GEN.generate(seed, seed, difficulty=band)
            generated.add(structural_signature({
                "input": grid, "output": GEN.rule_mirror(grid),
            })["persistent_markers"])
        assert canonical & generated, (band, canonical, generated)


def test_registered_row_span_rival_matches_independent_implementation():
    assert "horizontal_row_span" in GEN.LESSON_COMPETITORS
    rival = GEN.LESSON_COMPETITORS["horizontal_row_span"]
    grids = [pair["input"] for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)]
    grids.extend(GEN.generate(42, i) for i in range(12))
    for grid in grids:
        before = deepcopy(grid)
        assert rival(grid) == horizontal_row_span(grid)
        assert grid == before
