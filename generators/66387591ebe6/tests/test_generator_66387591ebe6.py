from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import random
from collections import deque
from pathlib import Path

import pytest


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.66387591ebe6.generator"
)


def _canonical_row():
    root = Path(os.environ["ARCPUZZLES_HOME"])
    path = root / "shared/data/canonical/puzzles.jsonl"
    return next(
        json.loads(line)
        for line in path.read_text().splitlines()
        if json.loads(line).get("task_id") == GEN.TASK_ID
    )


def _canonical_pairs():
    row = _canonical_row()
    train = row.get("train", [])
    test = row.get("test", [])
    if isinstance(train, dict):
        train = [train]
    if isinstance(test, dict):
        test = [test]
    return [*train, *test]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _foreground(grid):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9) and (r, c) != (0, 0)
    ]


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen == cells


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    canonical = _canonical_row()
    normalized = " ".join(canonical["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_override_is_exact_and_unknown_keys_reject() -> None:
    for grid_h in (9, 11):
        for grid_w in (9, 11):
            for key in (1, 2, 3, 4):
                for n_cells in (3, 4):
                    for pivot_region in GEN.PIVOT_REGIONS:
                        for texture in GEN.TEXTURES:
                            grid = GEN.generate(
                                991,
                                17,
                                difficulty="hard",
                                grid_h=grid_h,
                                grid_w=grid_w,
                                key=key,
                                n_cells=n_cells,
                                pivot_region=pivot_region,
                                texture=texture,
                            )
                            assert GEN.self_check(grid) == []
                            assert GEN.observe_overrides(grid) == {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "key": key,
                                "n_cells": n_cells,
                                "pivot_region": pivot_region,
                                "texture": texture,
                            }
    with pytest.raises(TypeError):
        GEN.generate(0, 0, unknown_axis="typo")
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="impossible")


def test_default_draws_cover_canonical_profiles_and_connected_objects() -> None:
    canonical_profiles = {(9, 9, 4), (11, 11, 4)}
    for difficulty in ("easy", "medium", "hard"):
        profiles = set()
        keys = set()
        textures = set()
        regions = set()
        for sample_index in range(20):
            grid = GEN.generate(1877, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            profiles.add(
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            )
            keys.add(observed["key"])
            textures.add(observed["texture"])
            regions.add(observed["pivot_region"])
            assert _is_connected(_foreground(grid))
            assert GEN.rule_mirror(grid) != grid
        assert profiles & canonical_profiles
        assert keys == {2, 3, 4}
        assert textures == set(GEN.TEXTURES)
        assert "center" in regions
        assert any(region != "center" for region in regions)


def test_key_one_identity_is_exact_override_only() -> None:
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "rotate_about_grid_center",
        "flatten_object_to_first_color",
    }
    assert set(GEN.EXTRAPOLATION_RIVALS) == {"keys_2_to_4_only"}

    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(
            6123,
            7,
            difficulty=difficulty,
            key=1,
            pivot_region="southeast",
            texture="multicolor",
        )
        assert GEN.observe_overrides(grid)["key"] == 1
        assert GEN.rule_mirror(grid) == grid
        assert (
            GEN.EXTRAPOLATION_RIVALS["keys_2_to_4_only"](grid)
            != GEN.rule_mirror(grid)
        )


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(81173)
    before = random.getstate()
    first = GEN.generate(13, 29, difficulty="medium")
    after = random.getstate()
    assert before == after

    pristine = copy.deepcopy(first)
    first[0][0] = 9
    second = GEN.generate(13, 29, difficulty="medium")
    assert second == pristine
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


def test_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(
        77,
        6,
        grid_h=9,
        grid_w=9,
        key=3,
        n_cells=4,
        pivot_region="center",
        texture="mono",
    )
    assert GEN.self_check(valid) == []

    impostors = {}
    impostors["all_background"] = [[0] * 9 for _ in range(9)]

    no_pivot = copy.deepcopy(valid)
    for row in no_pivot:
        for col, value in enumerate(row):
            if value == 9:
                row[col] = 0
    impostors["no_pivot"] = no_pivot

    multiple_pivots = copy.deepcopy(valid)
    multiple_pivots[1][1] = 9
    impostors["multiple_pivots"] = multiple_pivots

    bad_key = copy.deepcopy(valid)
    bad_key[0][0] = 7
    impostors["bad_key"] = bad_key

    disconnected = copy.deepcopy(valid)
    cells = _foreground(disconnected)
    r, c = cells[-1]
    color = disconnected[r][c]
    disconnected[r][c] = 0
    disconnected[1][7] = color
    impostors["disconnected_object"] = disconnected

    too_many = copy.deepcopy(valid)
    too_many[1][1] = next(
        value for row in valid for value in row if value not in (0, 9, valid[0][0])
    )
    impostors["too_many_cells"] = too_many

    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_declared_canonical_shortcuts_fit_public_pairs_and_are_generated_away() -> None:
    pairs = _canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            shortcut(GEN.generate(5000 + i, i))
            != GEN.rule_mirror(GEN.generate(5000 + i, i))
            for i in range(20)
        ), name


def test_named_rivals_are_killed_by_every_four_demo_window() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(12):
                demos = [
                    _pair(GEN.generate(seed, start + offset, difficulty=difficulty))
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    GEN.generate(
                        seed,
                        start + GEN.EXAMPLES_NEEDED,
                        difficulty=difficulty,
                    )
                )
                assert GEN.lesson_identifiable(demos, query) == []
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"]
                        for pair in demos
                    ), (difficulty, seed, start, name)


def test_semantic_witnesses_have_positive_support_in_each_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for sample_index in range(80):
            grid = GEN.generate(10000 + sample_index, sample_index, difficulty=difficulty)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                counts[name] += bool(predicate(grid))
        assert all(count > 0 for count in counts.values()), counts


def test_source_bound_lesson_probe_smoke() -> None:
    root = Path(os.environ["ARCPUZZLES_HOME"])
    probe_path = root / "generators/66387591ebe6/workspace/lesson_probe.py"
    assert probe_path.is_file()

    spec = importlib.util.spec_from_file_location("lesson_probe_66387591", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report, passed = probe.run_probe(
        repo=root,
        generator_path=root / "generators/66387591ebe6/generator.py",
        lessons_per_band=40,
        seed_base=663875910,
    )
    assert passed
    assert report["totals"]["lessons"] == 120
    assert report["totals"]["identity_pairs"] == 0
    assert all(
        count == 0
        for count in report["competitor_survivor_lessons"].values()
    )
    assert report["key_one_override_probe"]["passed"]
