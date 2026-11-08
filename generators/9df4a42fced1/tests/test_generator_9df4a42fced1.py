from __future__ import annotations

import copy
import importlib
import json
import random
from collections import Counter
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.9df4a42fced1.generator")


def _canonical_inputs():
    rows = []
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            rows.extend(pair["input"] for pair in row["train"] + row["test"])
    return rows


def test_canonical_inputs_are_owned_and_rule_hash_is_pinned():
    assert gen.RULE_HASH == "a101da2468b2"
    assert len(_canonical_inputs()) == 4
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_exact_axis_boundaries_and_observer():
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_frames"}
    for band in ("easy", "medium", "hard"):
        for kwargs in (
            {"grid_h": 11, "grid_w": 11, "n_frames": 1, "texture": "warm"},
            {"grid_h": 20, "grid_w": 22, "n_frames": 3, "texture": "cool"},
        ):
            grid = gen.generate(17, 19, difficulty=band, **kwargs)
            assert (len(grid), len(grid[0])) == (kwargs["grid_h"], kwargs["grid_w"])
            assert gen.observe_overrides(grid) == {
                "grid_h": kwargs["grid_h"],
                "grid_w": kwargs["grid_w"],
                "n_frames": kwargs["n_frames"],
            }
            assert gen.self_check(grid) == []


def test_self_check_rejects_four_structural_impostors():
    base = gen.generate(31, 5, difficulty="medium", n_frames=2)
    analysis = gen._analyze(base)
    first = analysis["frames"][0]
    r1, c1, r2, c2 = first["bbox"]
    sr, sc, _ = first["seeds"][0]

    broken_border = copy.deepcopy(base)
    broken_border[r1][c1 + 1] = 0
    assert gen.self_check(broken_border)

    no_seed = copy.deepcopy(base)
    no_seed[sr][sc] = 0
    assert gen.self_check(no_seed)

    multi_seed = copy.deepcopy(base)
    target = next(
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if (r, c) != (sr, sc) and multi_seed[r][c] == 0
    )
    multi_seed[target[0]][target[1]] = 9
    assert gen.self_check(multi_seed)

    loose_noise = copy.deepcopy(base)
    target = next(
        (r, c)
        for r, row in enumerate(loose_noise)
        for c, value in enumerate(row)
        if value == 0 and all((r, c) not in f["border"] for f in analysis["frames"])
    )
    loose_noise[target[0]][target[1]] = 9
    assert gen.self_check(loose_noise)


def test_degenerate_modes_are_rejected_by_self_check():
    for texture in gen.DEGENERATE_TEXTURES:
        assert gen.self_check(gen.generate(0, 0, texture=texture))


def test_determinism_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(991, 37, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(991, 37, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(991, 37, difficulty="hard") == second


def test_every_sequential_lesson_is_shortcut_identifiable():
    # Apply the independent mirror here; the battery separately checks the
    # sole Racket authority on the same generated inputs.
    for band in ("easy", "medium", "hard"):
        for start in range(36):
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(4000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_helpful_palette_modes_are_live_but_not_declared_semantic_axes():
    assert "texture" not in gen.AXES
    for seed in range(8):
        grids = [
            gen.generate(seed, 17, difficulty="medium", texture=name)
            for name in gen.HELPFUL_TEXTURES
        ]
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 2


def test_linked_semantic_census_and_disjoint_stability_200_per_band():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(20_000 + band_index * 1_000 + seed, seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert all(gen.rule_mirror(grid) != grid for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 195
        assert len({_frozen(gen.rule_mirror(grid)) for grid in grids}) >= 150
        counts = Counter(
            name
            for grid in grids
            for name, witness in gen.SEMANTIC_WITNESSES.items()
            if witness(grid)
        )
        assert all(counts[name] > 0 for name in gen.SEMANTIC_WITNESSES)
        assert counts["centered_seed_official_branch"] >= 80
        assert counts["off_center_seed_refutes_keep_seed_positions"] >= 80

        stable = [
            gen.generate(80_000 + band_index * 1_000 + seed, 10_000 + seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(gen.self_check(grid) == [] for grid in stable)
        assert len({_frozen(grid) for grid in stable}) >= 195
        first_set = {_frozen(grid) for grid in grids}
        stable_set = {_frozen(grid) for grid in stable}
        assert first_set != stable_set
        assert len(first_set & stable_set) <= 5


def test_semantic_witnesses_have_executable_rival_claims():
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(60):
            grid = gen.generate(90_000 + band_index, sample_index, difficulty=band)
            authoritative = gen.rule_mirror(grid)
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                rivals = gen.WITNESS_RIVALS[witness_name]
                assert rivals
                assert any(
                    gen.SEMANTIC_RIVALS[name](grid) != authoritative
                    for name in rivals
                )


def test_canonical_shortcut_is_killed_by_off_center_generation():
    shortcut = gen.CANONICAL_SHORTCUTS["erase_frames_keep_seed_positions"]
    assert all(shortcut(grid) == gen.rule_mirror(grid) for grid in _canonical_inputs())
    for band in ("easy", "medium", "hard"):
        off_center = gen.generate(77, 1, difficulty=band)
        assert gen.SEMANTIC_WITNESSES[
            "off_center_seed_refutes_keep_seed_positions"
        ](off_center)
        assert shortcut(off_center) != gen.rule_mirror(off_center)


def test_every_ordinary_draw_demonstrates_floor_center_rounding():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(60):
            if sample_index % 6 in (0, 3, 4):
                continue
            grid = gen.generate(120_000 + band_index, sample_index, difficulty=band)
            assert gen.SEMANTIC_WITNESSES["even_frame_floor_center"](grid)


def test_three_demos_cover_both_frame_count_regimes():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(60):
            counts = {
                len(gen._analyze(gen.generate(130_000 + band_index, sample_index, difficulty=band))["frames"])
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
            }
            assert counts == {2, 3}


def test_third_demo_kills_two_demo_shortcuts():
    for band in ("easy", "medium", "hard"):
        count_grids = [gen.generate(140_000, i, difficulty=band) for i in range(3)]
        assert all(
            gen.SEMANTIC_RIVALS["two_frame_only"](grid) == gen.rule_mirror(grid)
            for grid in count_grids[:2]
        )
        assert (
            gen.SEMANTIC_RIVALS["two_frame_only"](count_grids[2])
            != gen.rule_mirror(count_grids[2])
        )

        geometry_grids = [gen.generate(150_000, i, difficulty=band) for i in range(3, 6)]
        for rival_name in ("erase_frames_keep_seed_positions", "ceil_frame_centers"):
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) == gen.rule_mirror(grid) for grid in geometry_grids[:2])
            assert rival(geometry_grids[2]) != gen.rule_mirror(geometry_grids[2])
