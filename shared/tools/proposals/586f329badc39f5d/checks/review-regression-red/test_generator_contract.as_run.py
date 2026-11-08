"""Focused, source-bound regressions for the row-translation curriculum."""

from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "8a3fe170ed27"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def profile(grid):
    active = [r for r, row in enumerate(grid) if any(row)]
    supports = [{c for c, value in enumerate(grid[r]) if value} for r in active]
    occupied = set().union(*supports)
    return active, supports, occupied


def accepts(result):
    return result is True or result == []


def test_rule_binding_and_signed_phases():
    assert [GEN._wave_shift(d) for d in range(8)] == [0, -1, 0, 1, 0, -1, 0, 1]
    assert GEN.RULE_HASH == "a5b527116538"


@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
def test_default_draws_preserve_holes_and_schedule_witnesses(difficulty):
    tail_lengths = set()
    for seed in (0, 7):
        for index in range(8):
            grid = GEN.generate(seed, index, difficulty=difficulty)
            active, supports, occupied = profile(grid)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert active == list(range(active[0], active[-1] + 1))
            assert len({value for row in grid for value in row if value}) == 1
            assert any(len(cols) < max(cols) - min(cols) + 1 for cols in supports), (
                "ordinary samples must contain holes; solid rectangles admit envelope filling"
            )
            assert len(grid) - 1 - active[-1] == index % 4 + 1
            observed = GEN.observe_overrides(grid)
            if index % 2 == 0:
                assert observed["pattern"] in ("frame", "lattice")
                assert observed["edge_mode"] == "interior"
                assert min(occupied) > 0 and max(occupied) < len(grid[0]) - 1
            else:
                assert observed["pattern"] == "irregular"
                assert len(active) >= 8 and len(active) % 2 == 0
                assert len(supports[-1]) < max(map(len, supports))
                assert len(supports[-2]) < max(map(len, supports))
                last_full = max(i for i, cols in enumerate(supports)
                                if len(cols) == max(map(len, supports)))
                tail = len(active) - 1 - last_full
                assert tail >= 2 and tail % 4 not in (0, 2)
                tail_lengths.add(tail)
                sparse = {tuple(sorted(cols)) for cols in supports
                          if len(cols) < max(map(len, supports))}
                assert len(sparse) >= 2, "row-specific detail must survive reconstruction"
                expected_edge = "left" if index % 4 == 1 else "right"
                assert observed["edge_mode"] == expected_edge
                if expected_edge == "left":
                    assert min(occupied) == 0
                else:
                    assert max(occupied) == len(grid[0]) - 1
    assert len(tail_lengths) > 1, "ordinary irregular inputs must vary their tail length"


def test_same_seed_and_index_are_deterministic():
    assert GEN.generate(19, 3, difficulty="hard") == GEN.generate(19, 3, difficulty="hard")


@pytest.mark.parametrize("pattern", ["solid", "frame", "lattice", "irregular"])
@pytest.mark.parametrize("edge_mode", ["interior", "left", "right"])
def test_exact_controls_are_visible_in_pixels(pattern, edge_mode):
    requested = dict(grid_h=20, grid_w=20, n_rows=8, n_cells_per_row=8,
                     color=3, pattern=pattern, edge_mode=edge_mode)
    grid = GEN.generate(31, 0, **requested)
    active, supports, occupied = profile(grid)
    assert len(grid) == requested["grid_h"]
    assert {len(row) for row in grid} == {requested["grid_w"]}
    assert len(active) == requested["n_rows"]
    assert max(map(len, supports)) == requested["n_cells_per_row"]
    assert {value for row in grid for value in row if value} == {requested["color"]}
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in requested} == requested
    if edge_mode == "interior":
        assert min(occupied) > 0 and max(occupied) < len(grid[0]) - 1
    elif edge_mode == "left":
        assert min(occupied) == 0
    else:
        assert max(occupied) == len(grid[0]) - 1


@pytest.mark.parametrize("requested", [
    dict(grid_h=5, grid_w=5, n_rows=2, n_cells_per_row=1,
         color=9, pattern="solid", edge_mode="interior"),
    dict(grid_h=20, grid_w=20, n_rows=18, n_cells_per_row=18,
         color=1, pattern="solid", edge_mode="interior"),
    dict(grid_h=5, grid_w=5, n_rows=3, n_cells_per_row=4,
         color=2, pattern="frame", edge_mode="left"),
    dict(grid_h=5, grid_w=5, n_rows=3, n_cells_per_row=4,
         color=2, pattern="frame", edge_mode="right"),
    dict(grid_h=5, grid_w=5, n_rows=3, n_cells_per_row=4,
         color=2, pattern="frame"),
])
def test_feasible_extreme_overrides_are_exact(requested):
    grid = GEN.generate(2, 0, **requested)
    active, supports, _ = profile(grid)
    assert (len(grid), len(grid[0]), len(active), max(map(len, supports))) == (
        requested["grid_h"], requested["grid_w"],
        requested["n_rows"], requested["n_cells_per_row"])
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in requested} == requested
    if requested["grid_w"] == 5 and requested["n_cells_per_row"] == 4:
        assert observed["edge_mode"] in ("left", "right")


@pytest.mark.parametrize("key,value", [
    ("grid_h", True), ("grid_w", 8.5), ("n_rows", "6"),
    ("n_cells_per_row", False), ("color", None), ("color", [3]),
    ("grid_h", 4), ("grid_w", 21), ("n_rows", 19),
    ("n_cells_per_row", 0), ("color", 0), ("color", 10),
    ("pattern", "unknown"), ("edge_mode", "wrap"),
])
def test_invalid_scalar_controls_are_rejected_with_the_axis_name(key, value):
    with pytest.raises((TypeError, ValueError), match=key):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("key,value", [
    ("palette_size", 1), ("palette_kind", "warm"),
    ("anchor_corner", True), ("texture", "center"),
    ("position_bias", "edge"), ("misspelled_axis", 3),
])
def test_retired_and_unknown_controls_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError), match=key):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("overrides,names", [
    (dict(grid_h=5, n_rows=18, pattern="solid"), ("grid_h", "n_rows")),
    (dict(grid_w=5, n_cells_per_row=18, pattern="solid"),
     ("grid_w", "n_cells_per_row")),
    (dict(n_rows=2, pattern="irregular"), ("n_rows", "pattern")),
    (dict(grid_w=5, n_cells_per_row=4, n_rows=3, pattern="frame", edge_mode="interior"),
     ("grid_w", "n_cells_per_row")),
])
def test_infeasible_pairs_name_the_incompatible_axes(overrides, names):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, **overrides)
    named = set(getattr(caught.value, "incompatible_axes",
                        getattr(caught.value, "axes", ())))
    assert set(names) <= named or all(name in str(caught.value) for name in names)


def test_canonical_family_and_solid_exclusion():
    assert len(CANONICAL) == 5
    for pair in CANONICAL:
        assert GEN.self_check(pair["input"]) == []
        assert accepts(GEN.strict_canonical_like(pair["input"])), (
            pair["variant"], pair["split"], pair["pair_index"])
    solid = [[0] * 8 for _ in range(8)]
    for r in range(2, 6):
        solid[r][2:6] = [4] * 4
    assert not accepts(GEN.strict_canonical_like(solid))


@pytest.mark.parametrize("bad_grid", [
    [[0, 1], [1]],
    [[0, 0, 0], [1, 0, 2], [1, 0, 2]],
])
def test_self_check_rejects_malformed_or_multicomponent_inputs(bad_grid):
    assert GEN.self_check(bad_grid)


@pytest.mark.parametrize("invalid_zero", [False, 0.0])
def test_self_check_rejects_noninteger_cells_in_an_otherwise_canonical_grid(invalid_zero):
    grid = deepcopy(CANONICAL[0]["input"])
    grid[0][0] = invalid_zero
    assert GEN.self_check(grid), "valid structure must not conceal invalid scalar types"


def test_canonical_shortcuts_have_real_full_canonical_fits():
    expected = {"last_widest_row", "shared_rails_reconstruction",
                "wrap_at_edge", "clamp_at_edge", "last_widest_plus_two"}
    assert expected <= set(GEN.CANONICAL_SHORTCUTS)
    assert expected <= set(GEN.LESSON_COMPETITORS)
    other = {"first_active_anchor", "grid_bottom_margin_one", "grid_bottom",
             "opposite_phase", "row_envelope_fill", "identity"}
    assert other <= set(GEN.LESSON_COMPETITORS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert callable(rival), name
        for pair in CANONICAL:
            original = deepcopy(pair["input"])
            supplied = deepcopy(original)
            prediction = rival(supplied)
            assert supplied == original, f"{name} mutated its input"
            assert prediction == pair["output"], (
                name, pair["variant"], pair["split"], pair["pair_index"])


def test_last_widest_plus_two_has_canonical_fit_and_default_counterexample():
    rival = GEN.CANONICAL_SHORTCUTS["last_widest_plus_two"]
    assert len(CANONICAL) == 5
    assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in CANONICAL)
    counterexamples = []
    for seed in (0, 7):
        for index in range(8):
            grid = GEN.generate(seed, index)
            assert GEN.self_check(grid) == []
            bottom = max(r for r, row in enumerate(grid) if any(row))
            # The authoritative anchor row is unchanged. This checks that
            # invariant directly, without constructing Python output labels.
            if rival(deepcopy(grid))[bottom] != grid[bottom]:
                counterexamples.append((seed, index))
    assert counterexamples, "current support must refute the last-bar-plus-two shortcut"
