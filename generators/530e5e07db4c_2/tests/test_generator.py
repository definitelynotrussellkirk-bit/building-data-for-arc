"""Focused regression and semantic-curriculum tests for 530e5e07db4c_2."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib
import itertools

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "530e5e07db4c_2"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _component(grid, start, allowed=(2, 3, 5)):
    h, w = len(grid), len(grid[0])
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and grid[nr][nc] in allowed
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def oracle(grid):
    """Independent mirror of the selected connected-component rule."""
    out = deepcopy(grid)
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    greens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(reds) != 1 or len(greens) != 1:
        return out
    reached = _component(grid, reds[0])
    if greens[0] in reached:
        for r, c in reached:
            if grid[r][c] == 5:
                out[r][c] = 4
    return out


def _off_main_components(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    main = _component(grid, red)
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v == 5 and (r, c) not in main
    }
    groups = []
    while remaining:
        start = next(iter(remaining))
        group = _component(grid, start, allowed=(5,)) & remaining
        groups.append(group)
        remaining -= group
    return groups


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, turns, reflect):
    out = deepcopy(grid)
    if reflect:
        out = [row[::-1] for row in out]
    for _ in range(turns):
        out = _rot90(out)
    return out


def test_contract_is_small_exact_and_authority_pinned():
    assert gen.RULE_HASH == "646a78ec371e"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "endpoint",
        "green_interior",
        "branch",
        "cycle_tail",
    )


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("dims", [(7, 8), (7, 10), (14, 8), (14, 14)])
def test_exact_dimension_overrides_are_honored_in_every_band(band, dims):
    h, w = dims
    grid = gen.generate(917, 13, difficulty=band, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == dims
    assert gen.self_check(grid) == []
    assert grid == gen.generate(917, 13, difficulty=band, grid_h=h, grid_w=w)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"texture": "no_path"},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": 7},
        {"grid_w": 15},
        {"grid_h": True},
        {"grid_h": 7.0},
        {"grid_w": "8"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_lawful_visible_and_has_multicell_decoys(band):
    seen = set()
    shapes = set()
    for index in range(96):
        grid = gen.generate(3100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert oracle(grid) != grid
        assert oracle(grid) == gen.rule_mirror(grid)
        decoys = _off_main_components(grid)
        assert decoys
        assert all(len(component) >= 2 for component in decoys)
        assert grid == gen.generate(3100 + index, index, difficulty=band)
        seen.add(tuple(tuple(row) for row in grid))
        shapes.add((len(grid), len(grid[0])))
    assert len(seen) >= 90
    assert len(shapes) >= 4


def test_every_three_demo_window_refutes_every_declared_competitor():
    assert set(gen.LESSON_COMPETITORS) == {
        "recolor_all_gray",
        "recolor_nonisolated_gray",
        "shortest_path_only",
        "stop_at_green",
    }
    for band in ("easy", "medium", "hard"):
        for seed in (19, 901, 4401):
            grids = [gen.generate(seed, index, difficulty=band) for index in range(16)]
            pairs = [{"input": grid, "output": oracle(grid)} for grid in grids]
            for start in range(13):
                demos = pairs[start : start + 3]
                query = pairs[start + 3]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        seed,
                        start,
                        name,
                    )


def test_schedule_is_cyclic_and_all_profiles_are_realized():
    for start in range(8):
        expected = [gen.SCHEDULE_PROFILES[i % 4] for i in range(start, start + 4)]
        assert [gen.schedule_profile(0, i) for i in range(start, start + 4)] == expected
    realized = {
        gen.classify_profile(gen.generate(73, index, grid_h=7, grid_w=10))
        for index in range(12)
    }
    assert realized == set(gen.SCHEDULE_PROFILES)


def test_semantic_witnesses_have_real_counterexamples():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    firings = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(16):
        grid = gen.generate(508, index, grid_h=7, grid_w=10)
        answer = oracle(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                firings[name] += 1
                assert any(
                    gen.SEMANTIC_RIVALS[rival](grid) != answer
                    for rival in gen.WITNESS_RIVALS[name]
                ), name
    assert all(count > 0 for count in firings.values())


def test_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in _pairs()
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in canonical_profiles
        assert hits >= 1, (band, hits)


def test_validator_rejects_structural_mutations():
    base = gen.generate(44, 2, grid_h=7, grid_w=10)

    no_green = deepcopy(base)
    for row in no_green:
        for c, value in enumerate(row):
            if value == 3:
                row[c] = 0
    assert gen.self_check(no_green)

    unknown_color = deepcopy(base)
    unknown_color[0][0] = 9
    assert gen.self_check(unknown_color)

    no_decoy = deepcopy(base)
    red = next((r, c) for r, row in enumerate(no_decoy) for c, v in enumerate(row) if v == 2)
    main = _component(no_decoy, red)
    for r, row in enumerate(no_decoy):
        for c, value in enumerate(row):
            if value == 5 and (r, c) not in main:
                no_decoy[r][c] = 0
    assert gen.self_check(no_decoy)

    singleton_decoy = deepcopy(base)
    decoy = _off_main_components(singleton_decoy)[0]
    for r, c in list(decoy)[1:]:
        singleton_decoy[r][c] = 0
    assert gen.self_check(singleton_decoy)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True]], [[10]]])
def test_malformed_grids_return_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("turns,reflect", itertools.product(range(4), (False, True)))
def test_rule_and_validator_are_dihedrally_equivariant(turns, reflect):
    for index in range(8):
        grid = gen.generate(812, index, grid_h=10, grid_w=10)
        transformed = _transform(grid, turns, reflect)
        assert gen.self_check(transformed) == []
        assert oracle(transformed) == _transform(oracle(grid), turns, reflect)
        assert gen.rule_mirror(transformed) == oracle(transformed)


def test_every_profile_reaches_canonical_gray_object_scale():
    """Canonical max-object median is 12; generated support must reach tolerance."""
    for index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(6041, index, grid_h=7, grid_w=8)
        remaining = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 5
        }
        sizes = []
        while remaining:
            start = next(iter(remaining))
            group = _component(grid, start, allowed=(5,)) & remaining
            sizes.append(len(group))
            remaining -= group
        assert max(sizes) >= 10, (profile, sizes)
