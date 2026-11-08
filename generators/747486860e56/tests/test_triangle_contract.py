"""Independent regressions for the selected all-residual-cell triangle rule.

The oracle below deliberately shares no generator implementation helpers.
Canonical labels verify it before generated inputs are diagnosed with it.
"""
from collections import Counter
from copy import deepcopy

import pytest


def facts(grid):
    """Flood fill all nonzero colors together with eight-neighbor adjacency."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending, cells = [start], {start}
        while pending:
            r, c = pending.pop()
            adjacent = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)} & unseen
            unseen.difference_update(adjacent)
            cells.update(adjacent)
            pending.extend(adjacent)
        components.append(cells)
    main = max(components, key=len)
    residual = sorted(set().union(*components) - main)
    counts = Counter(grid[r][c] for r, c in residual)
    # Stable first occurrence is a cell-level row-major tie break.
    winner = max(counts, key=counts.get)
    corner_coords = {(0, 0): "tl", (0, w - 1): "tr", (h - 1, 0): "bl", (h - 1, w - 1): "br"}
    corner = next(corner_coords[rc] for rc in residual if rc in corner_coords)
    leg = len(residual) - 1
    triangle = set()
    for r in range(h):
        for c in range(w):
            rr = r if corner[0] == "t" else h - 1 - r
            cc = c if corner[1] == "l" else w - 1 - c
            if rr + cc < leg:
                triangle.add((r, c))
    return dict(h=h, w=w, components=components, main=main, residual=residual,
                counts=counts, winner=winner, corner=corner, leg=leg, triangle=triangle)


def reference(grid):
    observed = facts(grid)
    out = [[0] * observed["w"] for _ in range(observed["h"])]
    for r, c in observed["main"]:
        out[r][c] = grid[r][c]
    for r, c in observed["triangle"]:
        out[r][c] = observed["winner"]
    return out


def test_independent_reference_reproduces_every_canonical_label(pairs):
    assert {p["variant"] for p in pairs} == {0, 1}
    for pair in pairs:
        assert reference(pair["input"]) == pair["output"], (pair["variant"], pair["split"], pair["pair_index"])


def test_self_check_accepts_every_canonical_variant(generator, pairs):
    errors = [(p["variant"], p["split"], p["pair_index"], generator.self_check(p["input"])) for p in pairs]
    assert all(not row[3] for row in errors), errors


def test_strict_canonical_contract_accepts_all_variants(generator, pairs):
    for pair in pairs:
        assert not generator.strict_canonical_like(pair["input"])


@pytest.mark.parametrize("grid", [
    None, 1, "012", {}, (), [], [[]], [[0, 0], [0]], [None], [[True]], [[1.0]], [["1"]], [[-1]], [[10]],
    [[0] * 31 for _ in range(6)], [[0] * 6 for _ in range(31)],
])
def test_malformed_grids_are_reported_even_with_old_degenerate_metadata(generator, grid):
    # Metadata cannot turn invalid public input into a successful self-check.
    for meta in (None, {"texture": "no_pattern"}, {"texture": "no_markers"}, {"texture": "full_grid"}):
        assert generator.self_check(grid, meta=meta), (grid, meta)
    assert generator.strict_canonical_like(grid)


@pytest.mark.parametrize("band,h,w,n", [
    ("easy", 24, 6, 3), ("hard", 6, 24, 6), ("medium", 7, 7, 8),
    (None, 6, 6, 7), ("easy", 6, 6, 3), ("hard", 24, 24, 8),
])
@pytest.mark.parametrize("corner", ["tl", "tr", "bl", "br"])
def test_exact_size_corner_and_residual_count_across_bands(generator, band, h, w, n, corner):
    kwargs = dict(difficulty=band, grid_h=h, grid_w=w, n_markers=n, corner=corner)
    grid = generator.generate(19, 1, **kwargs)
    assert len(grid) == h and all(len(row) == w for row in grid)
    assert not generator.self_check(grid)
    observed = facts(grid)
    assert observed["corner"] == corner
    assert len(observed["residual"]) == n
    assert grid == generator.generate(19, 1, **kwargs)
    public = generator.observe_overrides(grid)
    assert {k: public[k] for k in ("grid_h", "grid_w", "corner", "n_markers")} == {
        "grid_h": h, "grid_w": w, "corner": corner, "n_markers": n,
    }


@pytest.mark.parametrize("kwargs", [
    {"grid_h": True}, {"grid_h": 6.0}, {"grid_h": "6"}, {"grid_h": 5}, {"grid_h": 25},
    {"grid_w": False}, {"grid_w": 12.0}, {"grid_w": "12"}, {"grid_w": 5}, {"grid_w": 25},
    {"n_markers": True}, {"n_markers": 3.0}, {"n_markers": "3"}, {"n_markers": 2}, {"n_markers": 9},
    {"corner": "north"}, {"corner": 1}, {"corner": False},
    {"palette_kind": "warm"}, {"anchor_corner": True}, {"asymmetry_force": True},
    {"palette_size": 4}, {"position_bias": "fixed"}, {"n_distinct_colors": 4},
    {"texture": "tl"}, {"texture": "no_pattern"}, {"stair_len": 7}, {"n_iso": 3}, {"unknown": 1},
    {"grid_h": 6, "grid_w": 24, "n_markers": 8},
])
def test_invalid_obsolete_and_unrealizable_overrides_fail_explicitly(generator, kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, 0, **kwargs)


@pytest.mark.parametrize("seed", [True, 1.5, "7", None])
def test_generate_rejects_non_integer_seed(generator, seed):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, -1, 1.5, "0", None])
def test_generate_and_schedule_reject_invalid_sample_index(generator, sample_index):
    with pytest.raises((TypeError, ValueError)):
        generator.schedule_profile(7, sample_index, "easy")
    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, sample_index, difficulty="easy")


@pytest.mark.parametrize("difficulty", [True, False, 1, 1.5, "__invalid_difficulty__", object()])
def test_generate_and_schedule_reject_invalid_difficulty(generator, difficulty):
    with pytest.raises((TypeError, ValueError)):
        generator.schedule_profile(7, 0, difficulty)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, 0, difficulty=difficulty)


def test_none_controls_retain_shared_no_override_convention(generator):
    for band in ("easy", "medium", "hard"):
        for index in range(3):
            baseline = generator.generate(7, index, difficulty=band)
            for axis in ("grid_h", "grid_w", "corner", "n_markers"):
                assert generator.generate(7, index, difficulty=band, **{axis: None}) == baseline
            assert generator.generate(7, index, difficulty=band,
                                      grid_h=None, grid_w=None, corner=None, n_markers=None) == baseline


def test_every_residual_count_and_schedule_profile_has_small_grid_support(generator):
    for n in range(3, 9):
        side = max(6, n - 1)
        for index in range(3):
            for corner in ("tl", "tr", "bl", "br"):
                grid = generator.generate(23, index, difficulty="hard", grid_h=side,
                                          grid_w=side, n_markers=n, corner=corner)
                observed = facts(grid)
                assert observed["h"] == observed["w"] == side
                assert len(observed["residual"]) == n
                assert observed["corner"] == corner
                assert not generator.strict_canonical_like(grid)


def test_default_generation_is_replayable_nonmutating_and_varied(generator):
    grids = []
    for band in ("easy", "medium", "hard"):
        for index in range(6):
            grid = generator.generate(31, index, difficulty=band)
            old = deepcopy(grid)
            assert not generator.self_check(grid, difficulty=band)
            reference(grid)
            assert grid == old
            assert grid == generator.generate(31, index, difficulty=band)
            grids.append(grid)
    assert len({str(g) for g in grids}) >= 12


def test_canonical_palette_and_shape_profiles_have_actual_generated_support(generator, pairs):
    canonical_profiles = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row})) for p in pairs}
    generated_profiles = set()
    for seed in range(12):
        for index in range(6):
            grid = generator.generate(seed, index, difficulty="medium")
            generated_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert canonical_profiles <= generated_profiles, canonical_profiles - generated_profiles


def test_declared_teaching_budget_and_schedule(generator):
    assert generator.EXAMPLES_NEEDED == 6
    assert generator.LESSON_SCHEDULE_PERIOD == 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_contains_core_and_both_numeric_tie_witnesses(generator, band):
    core_counts = set()
    episode_styles = set()
    for seed in range(12):
        seed_main_styles, seed_corner_roles = set(), set()
        for index in range(6):
            grid = generator.generate(seed, index, difficulty=band)
            observed = facts(grid)
            assert not generator.strict_canonical_like(grid)
            main_colors = {grid[r][c] for r, c in observed["main"]}
            seed_main_styles.add("mono" if len(main_colors) == 1 else "multi")
            all_colors = {v for row in grid for v in row}
            counts = observed["counts"]
            corners = {(0, 0), (0, len(grid[0]) - 1), (len(grid) - 1, 0), (len(grid) - 1, len(grid[0]) - 1)}
            corner_cell = next(rc for rc in observed["residual"] if rc in corners)
            corner_color = grid[corner_cell[0]][corner_cell[1]]
            without_corner = Counter(grid[r][c] for r, c in observed["residual"] if (r, c) != corner_cell)
            if index % 3 == 0:
                n = len(observed["residual"])
                core_counts.add(n)
                assert n in (3, 5, 6, 7)
                assert len(all_colors) == (4 if n % 2 else 6)
                if n % 2:
                    assert sorted(counts.values()) == [n // 2, n // 2 + 1]
                    assert counts[observed["winner"]] == n // 2 + 1
                else:
                    assert counts[observed["winner"]] == 2
                    assert sorted(counts.values()) == [1, 1, 1, 1, 2]
                    assert main_colors <= set(counts) - {observed["winner"]}
                critical = corner_color == observed["winner"]
                seed_corner_roles.add("critical" if critical else "neutral")
                assert (max(without_corner, key=without_corner.get) != observed["winner"]) == critical
            else:
                assert len(observed["residual"]) == 6
                assert sorted(counts.values()) == [1, 1, 2, 2]
                assert len(all_colors) == 6
                modes = sorted(color for color in counts if counts[color] == 2)
                assert observed["winner"] == modes[0 if index % 3 == 1 else -1]
                first_r, first_c = observed["residual"][0]
                assert counts[grid[first_r][first_c]] == 1
                assert counts[corner_color] == 1
                assert max(without_corner, key=without_corner.get) == observed["winner"]
                assert any(len(component) > 1 for component in observed["components"] if component is not observed["main"])
                assert observed["main"] & observed["triangle"]
        assert len(seed_main_styles) == len(seed_corner_roles) == 1
        episode_styles.add((next(iter(seed_main_styles)), next(iter(seed_corner_roles))))
    assert core_counts == {3, 5, 6, 7}
    assert episode_styles == {("mono", "critical"), ("mono", "neutral"), ("multi", "critical"), ("multi", "neutral")}


def test_lawful_residual_contact_multicolor_main_and_overwrite_semantics(generator):
    # Main cells connect diagonally, with different colors. Two residual cells
    # also connect diagonally; all six residual cells still vote and determine
    # leg5. The tied colors7/2 choose7 because its first cell appears first.
    grid = [[0] * 12 for _ in range(12)]
    for i, rc in enumerate(((0, 4), (1, 3), (2, 2), (3, 1), (4, 0))):
        grid[rc[0]][rc[1]] = (8, 9)[i % 2]
    for r, c, color in ((0, 0, 7), (2, 5, 7), (3, 6, 2), (6, 0, 2), (7, 1, 3), (9, 2, 4)):
        grid[r][c] = color
    observed = facts(grid)
    assert len(observed["main"]) == 5
    assert observed["winner"] == 7 and observed["leg"] == 5
    assert len(observed["main"] & observed["triangle"]) == 5
    out = reference(grid)
    assert out[2][2] == 7  # the triangle overwrites a main cell
    assert out[3][6] == 0  # the non-singleton residual is removed
    assert not generator.self_check(grid)
    assert not generator.strict_canonical_like(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_cyclic_lesson_and_each_single_pair_holdout_separates_declared_rivals(generator, band):
    required = {"exclude_corner_vote", "monochrome_main", "preserve_on_top", "largest_color_tie", "smallest_color_tie", "monochrome_corner_else_first"}
    assert required <= set(generator.LESSON_COMPETITORS)
    for start in range(3):
        lesson = [generator.generate(0, index, difficulty=band) for index in range(start, start + 7)]
        answers = [reference(grid) for grid in lesson]
        for name, rival in generator.LESSON_COMPETITORS.items():
            predictions = [rival(deepcopy(grid)) for grid in lesson]
            refuted = {i for i, (prediction, answer) in enumerate(zip(predictions, answers)) if prediction != answer}
            # A rival that agrees on the complete episode changes no query.
            # A disagreeing rival must remain refuted after any single holdout.
            assert not refuted or len(refuted) >= 2, (band, start, name, refuted)
        for held_out in range(7):
            demos = [{"input": g, "output": out} for i, (g, out) in enumerate(zip(lesson, answers)) if i != held_out]
            query = {"input": lesson[held_out], "output": answers[held_out]}
            assert not generator.lesson_identifiable(demos, query)


@pytest.mark.parametrize("seed,index,band,side,n,corner", [
    (5, 2, "hard", 6, 7, "tl"), (5, 2, "hard", 6, 7, "tr"),
    (5, 1, "hard", 7, 8, "tr"), (6, 2, "easy", 7, 8, "tr"),
])
def test_touching_residuals_cannot_steal_the_selected_main(generator, seed, index, band, side, n, corner):
    grid = generator.generate(seed, index, difficulty=band, grid_h=side, grid_w=side,
                              n_markers=n, corner=corner)
    assert len(facts(grid)["residual"]) == n


def test_monochrome_objects_do_not_imply_corner_color(generator):
    seen = False
    for seed in range(12):
        for index in range(6):
            grid = generator.generate(seed, index, difficulty="medium")
            observed = facts(grid)
            main_colors = {grid[r][c] for r, c in observed["main"]}
            r = 0 if observed["corner"][0] == "t" else len(grid)-1
            c = 0 if observed["corner"][1] == "l" else len(grid[0])-1
            seen |= len(main_colors) == 1 and grid[r][c] != observed["winner"]
    assert seen, "sampler teaches the spurious mono-object => corner-color implication"
