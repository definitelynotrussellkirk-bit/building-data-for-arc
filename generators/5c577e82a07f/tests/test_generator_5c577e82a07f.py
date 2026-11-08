from __future__ import annotations

import copy
import importlib
import random
import pytest

from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.5c577e82a07f.generator")


def _canonical_pairs():
    return canonical_pairs(GEN.TASK_ID, root=find_root(__file__))


def _blank():
    return [[0 for _ in range(9)] for _ in range(7)]


def _corners(grid, color, r0, r1, c0, c1):
    for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        grid[r][c] = color


def test_5c577e82a07f_rule_pin_and_all_canonicals():
    assert GEN.RULE_HASH == "486ca16c83e1"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert GEN.strict_canonical_like(pair["input"]) == []


def test_5c577e82a07f_exact_override_cartesian_boundaries():
    for band in ("easy", "medium", "hard"):
        for h in (7, 15):
            for w in (9, 18):
                for n in (2, 3):
                    for palette in GEN.PALETTE_KINDS:
                        for profile in GEN.GEOMETRY_PROFILES:
                            grid = GEN.generate(
                                1301,
                                17,
                                difficulty=band,
                                grid_h=h,
                                grid_w=w,
                                n_rects=n,
                                palette_kind=palette,
                                geometry_profile=profile,
                            )
                            assert GEN.self_check(grid) == []
                            assert GEN.observe_overrides(grid) == {
                                "grid_h": h,
                                "grid_w": w,
                                "n_rects": n,
                                "palette_kind": palette,
                                "geometry_profile": profile,
                            }


def test_5c577e82a07f_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(0, 0, grid_h=6)
    with pytest.raises(ValueError, match="not in"):
        GEN.generate(0, 0, palette_kind="default")


def test_5c577e82a07f_targeted_impostors_are_rejected_without_mutation():
    short_line = _blank()
    for c in (1, 2, 3, 4):
        short_line[1][c] = 4
    _corners(short_line, 6, 3, 6, 1, 5)

    solid_2x2 = _blank()
    _corners(solid_2x2, 4, 0, 1, 0, 1)
    _corners(solid_2x2, 6, 3, 6, 3, 7)

    missing_corner = _blank()
    for r, c in ((0, 0), (0, 3), (3, 0)):
        missing_corner[r][c] = 4
    _corners(missing_corner, 6, 3, 6, 4, 8)

    crossing_borders = _blank()
    _corners(crossing_borders, 4, 0, 4, 0, 4)
    _corners(crossing_borders, 6, 2, 6, 2, 6)

    fixtures = {
        "collinear short line": short_line,
        "2x2 no-op border": solid_2x2,
        "missing fourth corner": missing_corner,
        "intersecting inferred borders": crossing_borders,
    }
    for name, grid in fixtures.items():
        frozen = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == frozen, name


def test_5c577e82a07f_three_demo_schedule_kills_every_named_rival():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            profiles = []
            for offset in range(4):
                grid = GEN.generate(901 + start, start + offset, difficulty=band)
                profiles.append(GEN.semantic_observables(grid)["geometry_profile"])
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert set(profiles[:3]) == set(GEN.GEOMETRY_PROFILES)
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_5c577e82a07f_witness_claims_are_executable_disagreements():
    grids = [GEN.generate(777, i, difficulty="medium") for i in range(18)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for rival_name in rival_names:
            rival = GEN.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != GEN.rule_mirror(grid) for grid in firing), (
                witness_name,
                rival_name,
            )


def test_5c577e82a07f_canonical_shortcuts_get_exact_counterexamples():
    for pair in _canonical_pairs():
        for shortcut in GEN.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]

    witnesses = {
        "ignore_thin_horizontal": GEN.generate(
            8,
            1,
            difficulty="medium",
            geometry_profile="with_thin_horizontal",
        ),
        "first_two_colors_only": GEN.generate(
            1701,
            4,
            difficulty="medium",
            n_rects=3,
            geometry_profile="thick_only",
        ),
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(witnesses)
    for name, grid in witnesses.items():
        assert GEN.CANONICAL_SHORTCUTS[name](grid) != GEN.rule_mirror(grid), name


def test_5c577e82a07f_replay_freshness_and_global_rng_purity():
    random.seed(424242)
    before = random.getstate()
    first = GEN.generate(31, 41, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(31, 41, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9



def _first_two_colors_only(grid):
    output = [list(row) for row in grid]
    rectangles = GEN.semantic_observables(grid).get("rectangles", ())
    for rect in rectangles[:2]:
        if rect.get("complete_corners"):
            for r, c in rect["border"]:
                output[r][c] = rect["color"]
    return output


def test_5c577e82a07f_none_overrides_are_semantically_absent():
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in range(8):
                plain = GEN.generate(seed, sample_index, difficulty=band)
                explicit_none = GEN.generate(
                    seed,
                    sample_index,
                    difficulty=band,
                    grid_h=None,
                    grid_w=None,
                    n_rects=None,
                    palette_kind=None,
                    geometry_profile=None,
                )
                assert explicit_none == plain, (band, seed, sample_index)


def test_5c577e82a07f_first_two_colors_is_executable_canonical_shortcut():
    assert "first_two_colors_only" in GEN.SEMANTIC_RIVALS
    assert "first_two_colors_only" in GEN.CANONICAL_SHORTCUTS
    for pair in _canonical_pairs():
        assert _first_two_colors_only(pair["input"]) == pair["output"]

    witness = GEN.generate(
        1701,
        4,
        difficulty="medium",
        n_rects=3,
        geometry_profile="thick_only",
    )
    assert _first_two_colors_only(witness) != GEN.rule_mirror(witness)
    assert GEN.SEMANTIC_RIVALS["first_two_colors_only"](witness) == _first_two_colors_only(witness)


def test_5c577e82a07f_medium_demos_never_hide_third_color_until_query():
    defects = []
    for seed in list(range(24)) + [2695805167]:
        for start in range(12):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(seed, start + offset, difficulty="medium")
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            if (
                all(_first_two_colors_only(pair["input"]) == pair["output"] for pair in pairs[:3])
                and _first_two_colors_only(pairs[3]["input"]) != pairs[3]["output"]
            ):
                defects.append(
                    {
                        "seed": seed,
                        "start": start,
                        "color_counts": [
                            len(GEN.semantic_observables(pair["input"])["colors"])
                            for pair in pairs
                        ],
                    }
                )
    assert defects == []


def test_5c577e82a07f_three_color_scope_witness_appears_in_every_band_window():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(6):
                counts = [
                    GEN.semantic_observables(
                        GEN.generate(seed, start + offset, difficulty=band)
                    )["n_rects"]
                    for offset in range(3)
                ]
                assert 3 in counts, (band, seed, start, counts)
