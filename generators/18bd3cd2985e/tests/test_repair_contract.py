"""Regression checks for actual grid behavior, portable across packet runtimes."""
import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "18bd3cd2985e"

@pytest.fixture(scope="module")
def gen():
    return load_selected_generator(TASK, root=find_root(__file__))[0]


def components(grid):
    seen = set()
    result = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]; seen.add((r, c)); cells = []
            while todo:
                y, x = todo.pop(); cells.append((y, x))
                for yy, xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if (0 <= yy < len(grid) and 0 <= xx < len(row)
                            and (yy, xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy, xx)); todo.append((yy, xx))
            result.append((color, cells))
    return result


def shape_counts(grid):
    capacities = []
    singles = {}
    for color, cells in components(grid):
        if len(cells) == 1:
            singles[color] = singles.get(color, 0) + 1
        else:
            h = max(r for r,c in cells) - min(r for r,c in cells) + 1
            w = max(c for r,c in cells) - min(c for r,c in cells) + 1
            assert len(cells) == 2*h + 2*w - 4
            capacities.append(((h-2)*(w-2)+1)//2)
    return capacities, singles


def frame_grid():
    g = [[0] * 12 for _ in range(12)]
    for r in range(1, 4):
        for c in range(1, 4):
            if r in (1,3) or c in (1,3): g[r][c] = 2
    g[8][2] = 6
    g[9][3] = 6  # diagonal neighbors are separate four-connected singles
    return g


def test_dimensions_and_frame_count_are_honored(gen):
    g = gen.generate(0, 3, difficulty="easy", grid_h=30, grid_w=12, n_frames=3)
    assert (len(g), len(g[0])) == (30, 12)
    assert len(shape_counts(g)[0]) == 3


@pytest.mark.parametrize("mode", ["all", "partial", "none"])
def test_exact_matching_modes(gen, mode):
    g = gen.generate(7, 2, n_frames=3, match_mode=mode)
    capacities, singles = shape_counts(g)
    matched = sum(n in singles.values() for n in capacities)
    assert matched == {"all": 3, "partial": 2, "none": 0}[mode]
    observed = gen.observe_overrides(g)
    assert observed["match_mode"] == mode
    assert observed["n_frames"] == 3


@pytest.mark.parametrize("key", ["typo_axis", "frame_size", "palette_size", "position_bias", "texture"])
def test_unknown_and_retired_controls_fail_loudly(gen, key):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: 1})


@pytest.mark.parametrize("bad", [[], [[0], [0,1]], [[10]], [[-1]], [[True]], [[1.0]], [[2,2,0],[2,0,0]]])
def test_invalid_grid_is_rejected_without_crashing(gen, bad):
    assert gen.self_check(bad)


def test_diagonal_singletons_and_unmatched_counts_are_lawful(gen):
    assert gen.self_check(frame_grid()) == []


def test_canonical_inputs_remain_in_strict_domain(gen):
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_one_frame_cannot_be_partly_matched(gen):
    with pytest.raises(ValueError) as caught:
        gen.generate(0, 0, n_frames=1, match_mode="partial")
    assert set(caught.value.incompatible_axes) == {"n_frames", "match_mode"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_finite_sampler_domain_and_replay(gen, band):
    distinct = set()
    for seed in range(10):
        for index in range(6):
            g = gen.generate(seed, index, difficulty=band)
            assert gen.self_check(g) == []
            capacities, singles = shape_counts(g)
            assert len(capacities) in (2,3)
            assert len(capacities) == len(set(capacities)) == len(singles)
            assert len(set(singles.values())) == len(singles)
            expected_mode = ("all", "partial", "all", "partial", "all", "none")[index]
            matched = sum(n in singles.values() for n in capacities)
            assert matched == {"all":len(capacities), "partial":len(capacities)-1, "none":0}[expected_mode]
            assert g == gen.generate(seed, index, difficulty=band)
            distinct.add(tuple(map(tuple, g)))
    assert len(distinct) >= 55


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_profile_support_has_floor_in_every_band(gen, band):
    profiles = {(20,20,5), (18,23,5), (12,20,5), (22,26,7)}
    exact = 0
    for index in range(20):
        g = gen.generate(0, index, difficulty=band)
        profile = (len(g), len(g[0]), len({v for row in g for v in row}))
        exact += profile in profiles
    assert exact >= 10


@pytest.mark.parametrize("index", [0, 1, 5])
def test_grid_shape_does_not_reveal_matching_mode(gen, index):
    canonical_shapes = {(20,20), (18,23), (12,20), (22,26)}
    observations = set()
    for seed in range(24):
        g = gen.generate(seed, index, difficulty="hard")
        observations.add((len(g), len(g[0])) in canonical_shapes)
    assert observations == {False, True}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("mode", ["partial", "none"])
def test_every_unmatched_scene_has_a_too_small_group(gen, band, mode):
    # Such a group must be erased: a smallest-fitting-frame rule would paint it.
    for seed in range(12):
        g = gen.generate(seed, 0, difficulty=band, match_mode=mode)
        capacities, singles = shape_counts(g)
        assert any(n not in capacities and n < max(capacities)
                   for n in singles.values())


def test_largest_canonical_capacity_is_reachable_in_its_grid_shape(gen):
    capacities_seen = set()
    for seed in range(60):
        g = gen.generate(seed, 0, difficulty="hard", grid_h=22, grid_w=26,
                         n_frames=3, match_mode="all")
        capacities_seen.update(shape_counts(g)[0])
    assert 27 in capacities_seen


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("n_frames", [2, 3])
def test_partial_scene_also_refutes_discarding_surplus_groups(gen, band, n_frames):
    # Keeping the largest exact pair makes >= greedy pairing incorrectly consume
    # it for the missing smaller frame. Both inequality directions then disagree.
    for seed in range(12):
        g = gen.generate(seed, 0, difficulty=band, n_frames=n_frames,
                         match_mode="partial")
        capacities, singles = shape_counts(g)
        assert max(capacities) in singles.values()
