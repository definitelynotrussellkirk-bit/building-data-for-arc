"""Focused regression tests for the 0d877a4c52fd generator repair."""
from __future__ import annotations

import importlib
import random

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.0d877a4c52fd.generator")


def _blank(height: int = 9, width: int = 9) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _adjacent_authority_witness() -> list[list[int]]:
    """One 2x2 corner triple plus one conventionally spaced triple."""
    grid = _blank(6, 6)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        grid[r][c] = 2
    for r, c in ((0, 4), (4, 0), (4, 4)):
        grid[r][c] = 7
    return grid


def test_canonical_pairs_are_accepted_and_python_mirror_matches() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_and_adjacent_witness_matches_authority() -> None:
    assert gen.RULE_HASH == "bf8c9dd4f7fa"
    grid = _adjacent_authority_witness()
    assert gen.self_check(grid) == []

    expected = gen.rule_mirror(grid)
    assert expected[2][2] == 2
    shortcut = gen.SEMANTIC_RIVALS["spaced_only"](grid)
    assert shortcut[2][2] == 0
    assert shortcut != expected

    result = Catalog(find_root(__file__)).apply(gen.TASK_ID, [grid])
    assert result["rule_hash_matches_catalog"] is True
    assert result["executed_rule_hash"] == gen.RULE_HASH
    assert result["results"][0]["error"] is None
    assert result["results"][0]["output"] == expected


def test_exact_overrides_round_trip_for_every_semantic_enum() -> None:
    for count in (2, 3):
        for palette_kind in gen.PALETTE_KINDS:
            for missing_pattern in gen.MISSING_PATTERNS:
                for span_pattern in gen.SPAN_PATTERNS:
                    grid = gen.generate(
                        1701,
                        23,
                        difficulty="hard",
                        grid_h=9,
                        grid_w=9,
                        n_rects=count,
                        palette_kind=palette_kind,
                        missing_pattern=missing_pattern,
                        span_pattern=span_pattern,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": 9,
                        "grid_w": 9,
                        "n_rects": count,
                        "palette_kind": palette_kind,
                        "missing_pattern": missing_pattern,
                        "span_pattern": span_pattern,
                    }
                    assert gen.self_check(grid, difficulty="hard") == []

    for height, width in ((6, 6), (6, 12), (12, 6), (12, 12)):
        grid = gen.generate(
            1907,
            11,
            grid_h=height,
            grid_w=width,
            n_rects=3,
            palette_kind="high",
            missing_pattern="mixed",
            span_pattern="mixed",
        )
        observed = gen.observe_overrides(grid)
        assert (observed["grid_h"], observed["grid_w"], observed["n_rects"]) == (
            height,
            width,
            3,
        )


def test_unknown_and_invalid_overrides_fail_closed() -> None:
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(0, 0, typo_axis=3)
    for invalid in (True, 7.0, "7"):
        with pytest.raises(TypeError, match="integer"):
            gen.generate(0, 0, grid_h=invalid)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=5)
    with pytest.raises(ValueError, match="not in"):
        gen.generate(0, 0, missing_pattern="upper")
    with pytest.raises(ValueError, match="not in"):
        gen.generate(0, 0, span_pattern="large")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_self_check_rejects_targeted_impostors() -> None:
    assert gen.self_check([])
    assert gen.self_check([[0, 0], [0]])
    assert gen.self_check([[False]])
    assert gen.self_check(_blank())

    full_four = _blank()
    for r, c in ((1, 1), (1, 5), (5, 1), (5, 5)):
        full_four[r][c] = 2
    for r, c in ((2, 6), (2, 8), (4, 6)):
        full_four[r][c] = 7
    assert any("appears 4 times" in reason for reason in gen.self_check(full_four))

    collinear = _blank()
    for r, c in ((1, 1), (1, 3), (1, 5)):
        collinear[r][c] = 2
    for r, c in ((2, 6), (2, 8), (4, 6)):
        collinear[r][c] = 7
    assert any("two rows and two columns" in reason for reason in gen.self_check(collinear))

    shared_corner = _blank()
    for r, c in ((1, 1), (1, 4), (4, 1)):
        shared_corner[r][c] = 2
    for r, c in ((4, 4), (4, 7), (7, 4)):
        shared_corner[r][c] = 7
    errors = gen.self_check(shared_corner)
    assert any("not blank" in reason for reason in errors)
    assert any("shares implied rectangle" in reason for reason in errors)


def test_generated_samples_are_complete_lawful_and_collision_free() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(45):
            grid = gen.generate(6000 + index, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            facts = gen.semantic_observables(grid)
            assert facts["errors"] == []
            assert facts["n_rects"] in (2, 3)
            assert len(facts["rectangles"]) == facts["n_rects"]
            implied = [cell for rect in facts["rectangles"] for cell in rect["corners"]]
            assert len(implied) == len(set(implied))
            assert all(grid[r][c] == 0 for r, c in (rect["missing"] for rect in facts["rectangles"]))


def test_default_schedule_keeps_canonical_support_and_covers_axes() -> None:
    for band in ("easy", "medium", "hard"):
        seen_heights: set[int] = set()
        seen_widths: set[int] = set()
        seen_counts: set[int] = set()
        seen_palettes: set[str] = set()
        seen_missing: set[str] = set()
        seen_spans: set[str] = set()
        canonical_hits = 0
        for index in range(42):
            grid = gen.generate(8100, index, difficulty=band)
            observed = gen.observe_overrides(grid)
            seen_heights.add(observed["grid_h"])
            seen_widths.add(observed["grid_w"])
            seen_counts.add(observed["n_rects"])
            seen_palettes.add(observed["palette_kind"])
            seen_missing.add(observed["missing_pattern"])
            seen_spans.add(observed["span_pattern"])
            if (len(grid), len(grid[0])) == (9, 9):
                assert gen.strict_canonical_like(grid) == []
                canonical_hits += 1
            else:
                assert gen.strict_canonical_like(grid)
        assert seen_heights == set(range(6, 13))
        assert seen_widths == set(range(6, 13))
        assert canonical_hits > 0
        assert seen_counts == {2, 3}
        assert seen_palettes == set(gen.PALETTE_KINDS)
        assert seen_missing == set(gen.MISSING_PATTERNS)
        assert seen_spans == set(gen.SPAN_PATTERNS)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(918, 27, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(918, 27, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_every_sliding_three_demo_window_refutes_named_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                inp = gen.generate(3400 + start, sample_index, difficulty=band)
                pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_semantic_witnesses_fire_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for index in range(60):
            grid = gen.generate(7000 + index, index, difficulty=band)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hits[name] += int(witness(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)


def test_workspace_shortcut_probe_exposes_exact_adjacent_witness() -> None:
    import importlib.util
    from pathlib import Path

    root = find_root(__file__)
    path = root / "generators" / gen.TASK_ID / "workspace" / "probe_shortcuts.py"
    spec = importlib.util.spec_from_file_location("probe_shortcuts_under_test", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    grid = probe.adjacent_witness()
    assert gen.self_check(grid) == []
    intended = gen.rule_mirror(grid)
    shortcut = gen.CANONICAL_SHORTCUTS["spaced_only"](grid)
    assert intended != shortcut
    assert intended[2][2] == 2
    assert shortcut[2][2] == 0

    local = probe.build_local_report(root=root)
    assert local["canonical"]["spaced_only_matches"] == local["canonical"]["pair_count"] == 5
    assert local["witness"]["outputs_differ"] is True
    assert local["schedule"]["all_three_demo_windows_identifiable"] is True
