"""Focused regressions for the reviewed transform-analogy generator."""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


TASK_ID = "75b8cb3d5e9b"
try:
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
except ModuleNotFoundError:
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)


def _transform(grid, code):
    src = [list(row) for row in grid]
    if code == 0:
        return [row[:] for row in src]
    if code == 1:
        return [list(row) for row in zip(*src[::-1])]
    if code == 2:
        return [row[::-1] for row in src[::-1]]
    if code == 3:
        return [list(row) for row in zip(*src)][::-1]
    if code == 4:
        return [row[::-1] for row in src]
    if code == 5:
        return _transform(_transform(src, 4), 1)
    if code == 6:
        return _transform(_transform(src, 4), 2)
    if code == 7:
        return _transform(_transform(src, 4), 3)
    raise AssertionError(code)


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    assert cells
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in panel[r0 : r1 + 1]]


def _panels(grid):
    h = len(grid)
    dividers = [
        c for c in range(len(grid[0])) if all(grid[r][c] == 9 for r in range(h))
    ]
    assert len(dividers) == 2
    cuts = ((0, dividers[0]), (dividers[0] + 1, dividers[1]), (dividers[1] + 1, len(grid[0])))
    return [
        [[grid[r][c] for c in range(left, right)] for r in range(h)]
        for left, right in cuts
    ]


def _fitting_outputs(grid):
    source, target, query = map(_crop, _panels(grid))
    return {
        tuple(tuple(row) for row in _transform(query, code))
        for code in range(8)
        if _transform(source, code) == target
    }


def test_reproduced_baseline_seed_has_one_defensible_query_answer():
    """Regression for the measured 42.2% ambiguous-pair defect."""
    grid = gen.generate(1004, 4, difficulty=None)
    assert len(_fitting_outputs(grid)) == 1


def test_rule_hash_and_python_mirror_match_all_canonical_pairs():
    from reviewer_support import canonical_pairs, find_root

    assert gen.RULE_HASH == "9c9988768752"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_round_trip_in_every_band():
    cases = (
        {
            "panel_h": 3,
            "panel_w": 3,
            "transform": "r1",
            "source_cells": 4,
            "query_cells": 4,
            "source_palette_size": 1,
        },
        {
            "panel_h": 5,
            "panel_w": 5,
            "transform": "atr",
            "source_cells": 7,
            "query_cells": 7,
            "source_palette_size": 2,
        },
        {
            "panel_h": 3,
            "panel_w": 5,
            "transform": "fh",
            "source_cells": 5,
            "query_cells": 6,
            "source_palette_size": 2,
        },
    )
    for band in (None, "easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(211 + index, 31 + index, difficulty=band, **overrides)
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid) == []


def test_invalid_and_unknown_overrides_fail_loudly():
    import pytest

    invalid = (
        {"mystery_axis": 1},
        {"panel_h": 2},
        {"panel_w": 6},
        {"panel_h": True},
        {"transform": "id"},
        {"source_cells": 3},
        {"source_cells": 8},
        {"query_cells": 3},
        {"query_cells": 8},
        {"source_palette_size": 0},
        {"source_palette_size": 3},
    )
    for overrides in invalid:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(3, 5, **overrides)
    with pytest.raises(ValueError):
        gen.generate(3, 5, difficulty="expert")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_generated_census_has_unique_transform_and_discriminative_query():
    for band in (None, "easy", "medium", "hard"):
        for index in range(128):
            grid = gen.generate(7000 + index, index * 11 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            facts = gen.semantic_observables(grid)
            assert facts["transform_candidate_count"] == 1
            assert facts["query_orbit_size"] == 8
            assert len(_fitting_outputs(grid)) == 1


def test_profile_schedule_teaches_all_transforms_and_anchors_canonical_scale():
    expected = set(gen.TRANSFORMS)
    for band in (None, "easy", "medium", "hard"):
        for start in range(14):
            grids = [gen.generate(97, start + offset, difficulty=band) for offset in range(14)]
            observed = [gen.observe_overrides(grid) for grid in grids]
            assert {item["transform"] for item in observed} == expected
            assert all(
                observed[i]["transform"] != observed[(i + 1) % len(observed)]["transform"]
                for i in range(len(observed))
            )
            assert all(
                2 in (observed[i]["source_palette_size"], observed[(i + 1) % len(observed)]["source_palette_size"])
                for i in range(len(observed))
            )
            canonical_profiles = [
                grid
                for grid in grids
                if (len(grid), len(grid[0]), len({v for row in grid for v in row}))
                in {(3, 11, 3), (3, 11, 4), (3, 11, 5)}
            ]
            assert len(canonical_profiles) >= 7


def test_every_two_demo_sliding_window_is_identifiable_under_all_query_rotations():
    assert gen.EXAMPLES_NEEDED == 2
    for band in (None, "easy", "medium", "hard"):
        for start in range(28):
            pairs = [
                _pair(gen.generate(401 + i, start + i, difficulty=band))
                for i in range(3)
            ]
            for query_index in range(3):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (query_index, name)


def test_canonical_shortcut_declaration_is_exact():
    """Only rules that solve every usable canonical pair belong in this set."""
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    fitting = {
        name
        for name, rival in gen.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    assert fitting
    assert set(gen.CANONICAL_SHORTCUTS) == fitting


def test_workspace_ambiguity_probe_summarizes_every_band():
    path = Path(__file__).resolve().parents[1] / "workspace" / "transform_ambiguity_probe.py"
    spec = importlib.util.spec_from_file_location("transform_ambiguity_probe", path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.audit_generator(gen, draws_per_band=7, seed_base=9000)
    assert report["draw_count"] == 28
    assert report["ambiguous_draw_count"] == 0
    assert report["non_discriminative_query_count"] == 0
    assert report["self_check_failure_count"] == 0
    assert set(report["by_band"]) == {"default", "easy", "medium", "hard"}
    assert all(stats["draw_count"] == 7 for stats in report["by_band"].values())


def test_nuisance_profile_does_not_reveal_the_transform():
    """Every observable non-relational axis tuple must support every transform."""
    from collections import defaultdict

    expected = set(gen.TRANSFORMS)
    for band in (None, "easy", "medium", "hard"):
        by_nuisance = defaultdict(set)
        for sample_index in range(112):
            grid = gen.generate(12345, sample_index, difficulty=band)
            observed = gen.observe_overrides(grid)
            key = (
                observed["panel_h"],
                observed["panel_w"],
                observed["source_cells"],
                observed["query_cells"],
                observed["source_palette_size"],
            )
            by_nuisance[key].add(observed["transform"])
        assert by_nuisance
        assert all(transforms == expected for transforms in by_nuisance.values())
