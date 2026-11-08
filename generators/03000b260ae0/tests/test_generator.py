"""Task-local regression tests for 03000b260ae0.

The oracle below independently mirrors the pinned canonical Racket traversal:
4-connected nonzero components are discovered row-major with BFS neighbor order
up, down, left, right, and the anchor is the last 9 visited in the template.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "03000b260ae0"
ROOT = find_root(__file__)
gen, GEN_PATH, GEN_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
EXPECTED_RULE_HASH = "e140a6400a02"
BANDS = (None, "easy", "medium", "hard")
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))



def _canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    ]


def _components_bfs(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            order = []
            cursor = 0
            while cursor < len(queue):
                cr, cc = queue[cursor]
                cursor += 1
                order.append((cr, cc))
                for dr, dc in DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(order)
    return components


def _analyze(grid, *, first_anchor=False):
    components = _components_bfs(grid)
    template = next(
        comp for comp in components
        if len(comp) > 1 and any(grid[r][c] == 9 for r, c in comp)
    )
    marker_cells = [
        comp[0] for comp in components
        if len(comp) == 1 and grid[comp[0][0]][comp[0][1]] == 9
    ]
    anchors = [(r, c) for r, c in template if grid[r][c] == 9]
    anchor = anchors[0] if first_anchor else anchors[-1]
    return template, marker_cells, anchor


def oracle(grid, *, first_anchor=False, cap_at_two=False, binary=False):
    template, markers, anchor = _analyze(grid, first_anchor=first_anchor)
    h, w = len(grid), len(grid[0])
    counts = [[0] * w for _ in range(h)]
    ar, ac = anchor
    for mr, mc in markers:
        for tr, tc in template:
            r, c = mr + tr - ar, mc + tc - ac
            if 0 <= r < h and 0 <= c < w:
                counts[r][c] += 1
    if binary:
        return [[2 if value else 0 for value in row] for row in counts]
    if cap_at_two:
        return [[0 if value == 0 else 2 if value == 1 else 3 for value in row]
                for row in counts]
    return [[0 if value == 0 else 2 if value == 1 else 3 if value == 2 else 4
             for value in row] for row in counts]


def max_overlap(grid):
    template, markers, anchor = _analyze(grid)
    h, w = len(grid), len(grid[0])
    counts = {}
    ar, ac = anchor
    for mr, mc in markers:
        for tr, tc in template:
            point = (mr + tr - ar, mc + tc - ac)
            if 0 <= point[0] < h and 0 <= point[1] < w:
                counts[point] = counts.get(point, 0) + 1
    return max(counts.values(), default=0)


def test_rule_hash_schedule_and_contract_declarations():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert gen.EXAMPLES_NEEDED == 4
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_anchor", "double_multi_anchor",
        "triple_multi_anchor", "triple_multicolor",
    )
    assert set(gen.CANONICAL_SHORTCUTS) >= {"binary_union", "cap_at_two"}
    assert set(gen.LESSON_COMPETITORS) >= {"binary_union", "cap_at_two"}
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.lesson_identifiable)


@pytest.mark.parametrize("index", range(5))
def test_canonical_inputs_are_lawful_and_oracle_matches(index):
    pair = _canonical_pairs()[index]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]


def test_canonical_demonstrations_leave_count_palette_shortcuts_alive():
    for pair in _canonical_pairs():
        assert oracle(pair["input"], binary=True) == pair["output"]
        assert oracle(pair["input"], cap_at_two=True) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_are_lawful_observable_and_replayable(band):
    for seed in range(40):
        sample_index = seed * 7 + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == [], (band, seed)
        observed = gen.observe_overrides(grid)
        assert set(observed) == set(gen.AXES)
        assert gen.generate(seed, sample_index, difficulty=band, **observed) == grid
        assert oracle(grid) != grid


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("grid_h,grid_w", [(8, 10), (8, 17), (14, 10), (14, 17), (11, 13)])
def test_canonical_schedule_slot_honors_exact_dimension_overrides(band, grid_h, grid_w):
    for seed in range(8):
        grid = gen.generate(seed, 0, difficulty=band, grid_h=grid_h, grid_w=grid_w)
        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == grid_h
        assert observed["grid_w"] == grid_w


@pytest.mark.parametrize("band", BANDS)
def test_exact_joint_overrides_at_domain_corners(band):
    cases = (
        dict(grid_h=8, grid_w=10, n_markers=1,
             overlap="disjoint", texture="monochrome"),
        dict(grid_h=8, grid_w=17, n_markers=2,
             overlap="double", texture="multicolor"),
        dict(grid_h=14, grid_w=10, n_markers=3,
             overlap="triple", texture="multi_anchor"),
        dict(grid_h=14, grid_w=17, n_markers=5,
             overlap="triple", texture="monochrome"),
    )
    for options, seed in itertools.product(cases, range(8)):
        grid = gen.generate(seed, 19, difficulty=band, **options)
        assert gen.self_check(grid) == [], (band, seed, options)
        assert gen.observe_overrides(grid) == options




CANONICAL_PROFILES = {(11, 13, 3), (14, 16, 3), (12, 13, 3), (13, 13, 3)}


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def _same_color_objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            cursor = 0
            while cursor < len(queue):
                r, c = queue[cursor]
                cursor += 1
                cells.append((r, c))
                for dr, dc in DIRS4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def _palette_roles(inp, out):
    before = {value for row in inp for value in row if value}
    after = {value for row in out for value in row if value}
    return {
        "preserved": len(before & after),
        "introduced": len(after - before),
        "removed": len(before - after),
    }


def test_canonical_anchor_slot_matches_profile_and_coarse_authority_structure():
    expected_roles = {"preserved": 0, "introduced": 1, "removed": 2}
    for band in BANDS:
        for seed in range(12):
            grid = gen.generate(seed, 4 * seed, difficulty=band)
            output = oracle(grid)
            observed = gen.observe_overrides(grid)
            assert _profile(grid) in CANONICAL_PROFILES
            assert observed["overlap"] == "disjoint"
            assert observed["texture"] == "monochrome"
            assert observed["n_markers"] == 2
            template, _, _ = _analyze(grid)
            assert {grid[r][c] for r, c in template if grid[r][c] != 9} == {7}
            assert {value for row in output for value in row} == {0, 2}
            assert len(_same_color_objects(grid)) in {4, 5}
            assert _palette_roles(grid, output) == expected_roles


def test_every_five_consecutive_schedule_slots_include_all_teaching_profiles():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(len(gen.SCHEDULE_PROFILES)):
        profiles = {gen.schedule_profile(0, start + offset) for offset in range(5)}
        assert profiles == expected


@pytest.mark.parametrize("sample_index,profile,overlap,texture", [
    (0, "canonical_anchor", "disjoint", "monochrome"),
    (1, "double_multi_anchor", "double", "multi_anchor"),
    (2, "triple_multi_anchor", "triple", "multi_anchor"),
    (3, "triple_multicolor", "triple", "multicolor"),
    (4, "canonical_anchor", "disjoint", "monochrome"),
    (5, "double_multi_anchor", "double", "multi_anchor"),
    (6, "triple_multi_anchor", "triple", "multi_anchor"),
    (7, "triple_multicolor", "triple", "multicolor"),
])
def test_default_schedule_realizes_profiles(sample_index, profile, overlap, texture):
    assert gen.schedule_profile(0, sample_index, "medium") == profile
    for seed in range(30):
        observed = gen.observe_overrides(gen.generate(seed, sample_index, difficulty="medium"))
        assert observed["overlap"] == overlap
        assert observed["texture"] == texture


@pytest.mark.parametrize("band", BANDS)
def test_every_five_pair_rotation_refutes_declared_count_rivals(band):
    for start in range(len(gen.SCHEDULE_PROFILES)):
        pairs = []
        for offset in range(5):
            grid = gen.generate(1000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
        for query_index in range(5):
            query = pairs[query_index]
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert not (
                    all(rival(pair["input"]) == pair["output"] for pair in demos)
                    and rival(query["input"]) != query["output"]
                ), (band, start, query_index, name)


def test_semantic_profiles_have_visible_exact_overlap_and_anchor_witnesses():
    double = gen.generate(17, 0, overlap="double", texture="multicolor", n_markers=5)
    triple = gen.generate(19, 1, overlap="triple", texture="multi_anchor", n_markers=5)
    assert max_overlap(double) == 2
    assert max_overlap(triple) == 3
    assert gen.SEMANTIC_WITNESSES["double_overlap"](double)
    assert gen.SEMANTIC_WITNESSES["triple_overlap"](triple)
    assert gen.SEMANTIC_WITNESSES["multiple_template_nines"](triple)
    assert gen.SEMANTIC_RIVALS["binary_union"](double) != oracle(double)
    assert gen.SEMANTIC_RIVALS["cap_at_two"](triple) != oracle(triple)
    assert gen.SEMANTIC_RIVALS["first_template_nine"](triple) != oracle(triple)


@pytest.mark.parametrize("kwargs", [
    {"n_markers": 1, "overlap": "double"},
    {"n_markers": 1, "overlap": "triple"},
    {"n_markers": 2, "overlap": "triple"},
])
def test_rejects_incompatible_marker_overlap_overrides(kwargs):
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, **kwargs)
    assert set(getattr(exc.value, "incompatible_axes", ())) == {"n_markers", "overlap"}


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": 1},
    {"grid_h": 7}, {"grid_h": 15}, {"grid_w": 9}, {"grid_w": 18},
    {"n_markers": 0}, {"n_markers": 6},
    {"overlap": "quadruple"}, {"texture": "no_markers"},
    {"grid_h": True}, {"n_markers": 2.0}, {"n_markers": "2"},
])
def test_rejects_invalid_overrides(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)
