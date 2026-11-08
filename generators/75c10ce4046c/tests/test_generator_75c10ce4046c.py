from __future__ import annotations

from reviewer_support import canonical_pairs, find_root, load_selected_generator
import pytest

TASK = "75c10ce4046c"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK, root=ROOT)


def _components(grid, colors=None):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (colors is not None and color not in colors) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _facts(grid):
    source = _components(grid, {2})
    candidates = _components(grid, {3, 4, 5, 6})
    assert len(source) == 1
    signature = _norm(source[0][1])
    matches = sum(_norm(cells) == signature for _, cells in candidates)
    return len(source[0][1]), len(candidates), matches


def test_all_canonical_inputs_are_accepted_including_pentomino_sources_and_distractors():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    sizes = set()
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        sizes.update(len(cells) for _, cells in _components(pair["input"]))
    assert sizes == {4, 5}


@pytest.mark.parametrize("source_size", [4, 5])
def test_source_size_and_exact_matching_candidate_override_are_honored(source_size):
    grid = GEN.generate(
        700 + source_size,
        2,
        height=18,
        width=22,
        candidate_count=6,
        matching_candidates=3,
        source_size=source_size,
    )
    assert GEN.self_check(grid) == []
    assert _facts(grid) == (source_size, 6, 3)


def test_requested_match_count_is_not_resampled():
    observed = set()
    for requested in (1, 2, 3, 4, 5):
        grid = GEN.generate(
            811,
            requested,
            height=18,
            width=22,
            candidate_count=6,
            matching_candidates=requested,
            source_size=5,
        )
        observed.add(_facts(grid)[2])
    assert observed == {1, 2, 3, 4, 5}


def test_invalid_count_combinations_and_unknown_source_size_fail_closed():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, candidate_count=6, matching_candidates=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, candidate_count=6, matching_candidates=6)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, source_size=6)


def test_deterministic_fresh_returns():
    kwargs = dict(height=18, width=22, candidate_count=5, matching_candidates=2, source_size=5)
    first = GEN.generate(919, 4, **kwargs)
    second = GEN.generate(919, 4, **kwargs)
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 8
    assert GEN.generate(919, 4, **kwargs) == second
