"""Independent checks of realizable axes, lawful inputs and declared teaching rivals."""
from copy import deepcopy
from itertools import product
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace"))
from review_support import (declared_rivals, load_generator, observed, pairs,
                            row_oracle, score_window, witness_grid)

gen = load_generator()


def test_canonical_authority_and_actual_shortcut_fit():
    canonical = pairs()
    assert len(canonical) == 3
    assert gen.RULE_HASH == "1130750019d1"
    for pair in canonical:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) in ([], True)
        assert row_oracle(pair["input"]) == pair["output"]
    for name, rival in declared_rivals(gen).items():
        for pair in canonical:
            original = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == original, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_complete_legal_joint_axis_domain(band):
    checked = 0
    for index, (h, w, colors, density) in enumerate(product(
            range(5, 13), range(7, 17), range(4, 11), ("low", "med", "high"))):
        requested = dict(grid_h=h, grid_w=w, n_distinct_colors=colors, marker_density=density)
        grid = gen.generate(831, index, difficulty=band, **requested)
        assert gen.self_check(grid) == [], (band, index, requested)
        assert observed(grid) == requested, (band, index, requested)
        assert gen.observe_overrides(grid) == requested
        assert row_oracle(grid) != grid
        checked += 1
    assert checked == 1680


@pytest.mark.parametrize("axis,value", [
    ("unknown_axis", 3), ("grid_h", 4), ("grid_h", 13), ("grid_w", 6), ("grid_w", 17),
    ("n_distinct_colors", 3), ("n_distinct_colors", 11), ("marker_density", "dense"),
    ("grid_h", True), ("grid_w", False), ("grid_h", 6.0), ("grid_h", "6"),
    ("n_distinct_colors", 4.2), ("n_distinct_colors", True), ("marker_density", 1),
    ("marker_density", ["low"]),
])
def test_invalid_or_unknown_override_types(axis, value):
    with pytest.raises(ValueError):
        gen.generate(7, 3, **{axis: value})


def test_minimum_canvas_full_palette_capacity_across_ten_thousand_seeds():
    requested = dict(grid_h=5, grid_w=7, n_distinct_colors=10, marker_density="high")
    for seed in range(10000):
        grid = gen.generate(seed, 1, **requested)
        assert gen.self_check(grid) == [], seed
        assert observed(grid) == requested, seed


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0], [0, 1]], [[True, 8], [2, 8]], [[2, 8.0]], [[2, "8"]],
    [[2, 10]], [[2, -1]], [None], [3], "28", [[2, 0]], [[0, 8]], [[8, 8]],
])
def test_malformed_or_unproductive_is_diagnostic(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(e, str) for e in errors)


def test_lawful_witness_and_real_declared_rival_claims():
    grid = witness_grid()
    assert gen.self_check(grid) == []
    expected = row_oracle(grid)
    assert expected[0][3] == 8  # zero header preserves marker despite spectator first
    assert expected[1][1] == 4  # foreign spectator is preserved
    assert expected[2][3] == 8  # header 8 is legal, and acts as an identity on markers
    assert expected[1][9] == 2  # rule reaches beyond canonical width
    for name, rival in declared_rivals(gen).items():
        assert rival(deepcopy(grid)) != expected, name
    assert gen.SEMANTIC_WITNESSES
    firings = 0
    for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
        if not predicate(deepcopy(grid)):
            continue
        claims = gen.WITNESS_RIVALS.get(witness_name, [])
        if isinstance(claims, str):
            claims = [claims]
        if not claims:
            assert witness_name in getattr(gen, "BRANCH_WITNESSES", ())
            continue
        assert any(gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected for name in claims)
        firings += 1
    assert firings > 0


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_determinism_and_nonmutation(band):
    grids = [gen.generate(12391, index, difficulty=band) for index in range(32)]
    gen.generate(999, 500, difficulty="hard")
    for index in reversed(range(32)):
        grid = grids[index]
        assert gen.generate(12391, index, difficulty=band) == grid
        original = deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == observed(grid)
        assert gen.strict_canonical_like(grid) in ([], True)
        assert row_oracle(grid) != grid
        for rival in declared_rivals(gen).values():
            rival(grid)
            assert grid == original
        assert gen.schedule_profile(12391, index, difficulty=band) == ("core" if index % 2 == 0 else "rich")
        keyed = [(r, row[0]) for r, row in enumerate(grid)
                 if row[0] not in (0, 8) and 8 in row[1:]]
        assert any(r % 2 != s % 2 and a != b for r, a in keyed for s, b in keyed)
        assert any(row[0] == 0 and any(value not in (0, 8) and 8 in row[c + 1:]
                                     for c, value in enumerate(row[1:], start=1)) for row in grid)
        assert any(row[0] not in (0, 8) and any(value not in (0, 8, row[0])
                                              for value in row[1:]) for row in grid)
        if index % 2:
            assert observed(grid)["marker_density"] == "high"
            assert len(grid[0]) >= 10
            assert any(row[0] == 8 and any(value not in (0, 8) for value in row[1:])
                       for row in grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("n_queries", [1, 2])
def test_every_cyclic_three_demo_window_teaches_declared_rivals(band, n_queries):
    rivals = declared_rivals(gen)
    for seed in (13, 917, 22104):
        for start in range(8):
            lesson = []
            for index in range(start, start + 3 + n_queries):
                grid = gen.generate(seed, index, difficulty=band)
                lesson.append({"input": grid, "output": row_oracle(grid)})
            assert len({str(pair["input"]) for pair in lesson}) == len(lesson)
            for rotation in range(len(lesson)):
                rotated = lesson[rotation:] + lesson[:rotation]
                scores = score_window(rivals, rotated[:3], rotated[3:])
                assert "ambiguous" not in scores.values(), (band, seed, start, rotation, scores)
                if hasattr(gen, "lesson_identifiable"):
                    for query in rotated[3:]:
                        assert gen.lesson_identifiable(rotated[:3], query) == []
