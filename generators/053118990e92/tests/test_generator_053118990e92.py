"""Semantic, override, and regression tests for Voronoi-inside-the-frame."""
from __future__ import annotations

import copy
import importlib
import random
from collections import Counter

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.053118990e92.generator"
)


def _pair(seed: int, sample_index: int, band: str) -> dict[str, list[list[int]]]:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _seed_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    eights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    r1 = min(r for r, _ in eights)
    c1 = min(c for _, c in eights)
    r2 = max(r for r, _ in eights)
    c2 = max(c for _, c in eights)
    return [
        (r, c, grid[r][c])
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if grid[r][c] not in (0, 8)
    ]


def test_rule_hash_canonical_ownership_and_declared_shortcuts():
    assert gen.RULE_HASH == "a2e9b991269f"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        for shortcut in gen.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_axis_boundary_is_observable_in_every_band(band):
    for height in (9, 14):
        for width in (11, 16):
            for n_seeds in (2, 4):
                for frame_style in ("ring", "corners"):
                    for seed_color_mode in ("distinct", "duplicate_pair"):
                        requested = {
                            "grid_h": height,
                            "grid_w": width,
                            "n_seeds": n_seeds,
                            "frame_style": frame_style,
                            "seed_color_mode": seed_color_mode,
                        }
                        grid = gen.generate(
                            3127,
                            44,
                            difficulty=band,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs,exc",
    [
        ({"misspelled_axis": 1}, TypeError),
        ({"grid_h": 8}, ValueError),
        ({"grid_h": 15}, ValueError),
        ({"grid_w": 10}, ValueError),
        ({"grid_w": 17}, ValueError),
        ({"n_seeds": 1}, ValueError),
        ({"n_seeds": 5}, ValueError),
        ({"frame_style": "broken"}, ValueError),
        ({"seed_color_mode": "random"}, ValueError),
        ({"n_seeds": True}, ValueError),
    ],
)
def test_invalid_overrides_are_rejected(kwargs, exc):
    with pytest.raises(exc):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="expert")


def test_four_profile_schedule_teaches_every_declared_semantic_branch():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_ring",
        "different_color_tie",
        "same_color_tie",
        "corners_manhattan",
    )
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(8):
                demos = [
                    _pair(seed, sample_index, band)
                    for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
                ]
                query = _pair(seed, start + gen.EXAMPLES_NEEDED, band)
                assert gen.lesson_identifiable(demos, query) == []
                assert {
                    gen.schedule_profile(seed, sample_index, band)
                    for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
                } == set(gen.SCHEDULE_PROFILES)
                for rival in gen.LESSON_COMPETITORS.values():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    )
                for witness in gen.SEMANTIC_WITNESSES.values():
                    assert any(witness(pair["input"]) for pair in demos)


def test_each_scheduled_witness_is_concrete_and_answer_changing():
    different = gen.generate(73, 1, difficulty="easy")
    same = gen.generate(73, 2, difficulty="easy")
    corners = gen.generate(73, 3, difficulty="easy")

    assert gen.SEMANTIC_WITNESSES["different_color_nearest_tie"](different)
    assert (
        gen.SEMANTIC_RIVALS["resolve_different_ties"](different)
        != gen.rule_mirror(different)
    )

    assert gen.SEMANTIC_WITNESSES["same_color_nearest_tie"](same)
    assert (
        gen.SEMANTIC_RIVALS["ties_always_blank"](same)
        != gen.rule_mirror(same)
    )

    assert gen.SEMANTIC_WITNESSES["corners_only_frame"](corners)
    assert (
        gen.SEMANTIC_RIVALS["requires_full_ring"](corners)
        != gen.rule_mirror(corners)
    )
    assert gen.SEMANTIC_WITNESSES["manhattan_not_euclidean"](corners)
    assert (
        gen.SEMANTIC_RIVALS["euclidean_distance"](corners)
        != gen.rule_mirror(corners)
    )


def test_canonical_anchor_hits_strict_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        strict = [
            gen.generate(9001, index, difficulty=band)
            for index in range(20)
            if gen.strict_canonical_like(
                gen.generate(9001, index, difficulty=band)
            )
            == []
        ]
        assert strict
        assert any(
            (len(grid), len(grid[0]), len(_seed_cells(grid))) == (10, 12, 2)
            for grid in strict
        )


def test_self_check_rejects_structural_impostors():
    base = gen.generate(
        314,
        0,
        difficulty="easy",
        grid_h=10,
        grid_w=12,
        n_seeds=2,
        frame_style="ring",
        seed_color_mode="distinct",
    )
    assert gen.self_check(base) == []

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert gen.self_check(ragged)

    bad_cell = copy.deepcopy(base)
    bad_cell[0][0] = True
    assert gen.self_check(bad_cell)

    missing_ring_cell = copy.deepcopy(base)
    eights = [
        (r, c)
        for r, row in enumerate(base)
        for c, value in enumerate(row)
        if value == 8
    ]
    missing_ring_cell[eights[0][0]][eights[0][1]] = 0
    assert gen.self_check(missing_ring_cell)

    interior_eight = copy.deepcopy(base)
    seed_r, seed_c, _ = _seed_cells(base)[0]
    interior_eight[seed_r][seed_c] = 8
    assert gen.self_check(interior_eight)

    outside_seed = copy.deepcopy(base)
    outside = next(
        (r, c)
        for r, row in enumerate(base)
        for c, value in enumerate(row)
        if value == 0
        and (r == 0 or c == 0 or r == len(base) - 1 or c == len(base[0]) - 1)
    )
    outside_seed[outside[0]][outside[1]] = 4
    assert gen.self_check(outside_seed)

    one_seed = copy.deepcopy(base)
    for r, c, _ in _seed_cells(base)[1:]:
        one_seed[r][c] = 0
    assert gen.self_check(one_seed)

    five_seeds = copy.deepcopy(base)
    existing = {(r, c) for r, c, _ in _seed_cells(base)}
    eights = [(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value == 8]
    r1, r2 = min(r for r, _ in eights), max(r for r, _ in eights)
    c1, c2 = min(c for _, c in eights), max(c for _, c in eights)
    additions = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if (r, c) not in existing and five_seeds[r][c] == 0
    ][:3]
    for color, (r, c) in zip((4, 5, 6), additions):
        five_seeds[r][c] = color
    assert len(_seed_cells(five_seeds)) == 5
    assert gen.self_check(five_seeds)

    triple_duplicate = gen.generate(
        17,
        9,
        n_seeds=4,
        seed_color_mode="distinct",
    )
    seeds = _seed_cells(triple_duplicate)
    for r, c, _ in seeds[:3]:
        triple_duplicate[r][c] = 2
    assert Counter(value for _, _, value in _seed_cells(triple_duplicate))[2] == 3
    assert gen.self_check(triple_duplicate)


def test_determinism_fresh_returns_input_purity_and_global_rng():
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(2026, 8, difficulty="medium")
    assert random.getstate() == state
    snapshot = copy.deepcopy(first)
    second = gen.generate(2026, 8, difficulty="medium")
    assert first == second == snapshot
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 1
    replay = gen.generate(2026, 8, difficulty="medium")
    assert replay == snapshot
    before = copy.deepcopy(replay)
    gen.rule_mirror(replay)
    gen.self_check(replay)
    gen.strict_canonical_like(replay)
    gen.observe_overrides(replay)
    for fn in gen.SEMANTIC_RIVALS.values():
        fn(replay)
    for fn in gen.SEMANTIC_WITNESSES.values():
        fn(replay)
    assert replay == before
    assert random.getstate() == state

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_query_rotation_keeps_declared_rivals_refuted(band):
    """A five-pair window stays identifiable whichever pair becomes the query."""
    for seed in range(3):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = [
                _pair(seed, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_offset, query in enumerate(pairs):
                demos = [
                    pair for offset, pair in enumerate(pairs)
                    if offset != query_offset
                ]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    seed,
                    start,
                    query_offset,
                    gen.schedule_profile(seed, start + query_offset, band),
                    gen.lesson_identifiable(demos, query),
                )


def test_cyclic_probe_uses_live_declarations_and_reports_source_identity():
    import hashlib
    import importlib.util
    import json
    import os
    from pathlib import Path

    root = Path(os.environ["ARCPUZZLES_HOME"])
    probe_path = (
        root
        / "generators"
        / gen.TASK_ID
        / "workspace"
        / "cyclic_lesson_probe.py"
    )
    spec = importlib.util.spec_from_file_location("cyclic_lesson_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(
        gen,
        bands=("easy",),
        seed_start=0,
        seeds=2,
        starts=range(len(gen.SCHEDULE_PROFILES)),
        canonical_path=root / "shared/data/canonical/puzzles.jsonl",
    )
    expected_sha = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    assert report["passed"] is True
    assert report["generator_sha256"] == expected_sha
    assert report["declarations"]["lesson_competitors"] == sorted(
        gen.LESSON_COMPETITORS
    )
    assert report["declarations"]["canonical_shortcuts"] == sorted(
        gen.CANONICAL_SHORTCUTS
    )
    assert report["declarations"]["semantic_witnesses"] == sorted(
        gen.SEMANTIC_WITNESSES
    )
    assert report["totals"]["rotations"] == 40
    assert report["totals"]["ambiguous_rotations"] == 0
    assert report["canonical_shortcut_check"]["usable_pairs"] == 5
    assert report["canonical_shortcut_check"]["failures"] == []
    json.dumps(report)


def test_default_canonical_profile_varies_across_seeds_without_leaving_profile():
    grids = [gen.generate(seed, 0) for seed in range(40)]
    distinct = {
        tuple(tuple(row) for row in grid)
        for grid in grids
    }
    assert len(distinct) >= 12
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
    assert all(
        gen.SEMANTIC_WITNESSES["different_color_nearest_tie"](grid)
        and gen.SEMANTIC_WITNESSES["manhattan_not_euclidean"](grid)
        for grid in grids
    )
