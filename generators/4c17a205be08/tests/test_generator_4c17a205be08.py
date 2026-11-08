from __future__ import annotations

import copy
import importlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


def _load_generator():
    try:
        return importlib.import_module("puzzle_generators.per_puzzle.4c17a205be08.generator")
    except ModuleNotFoundError:
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo / "shared" / "runtime"))
        path = repo / "generators" / "4c17a205be08" / "generator.py"
        spec = importlib.util.spec_from_file_location("generator_4c17a205be08_under_test", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _canonical_pairs():
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "shared" / "data" / "canonical" / "puzzles.jsonl",
        here.parents[4] / "data" / "canonical" / "puzzles.jsonl",
    ]
    path = next(candidate for candidate in candidates if candidate.exists())
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != "4c17a205be08":
            continue
        pairs = list(row.get("train", [])) + list(row.get("test", []))
        normalized = []
        for pair in pairs:
            normalized.append({
                "input": [[int(value) for value in row] for row in pair["input"]],
                "output": [[int(value) for value in row] for row in pair["output"]],
            })
        return normalized
    raise AssertionError("canonical task not found")


gen = _load_generator()


def _transform_of(grid):
    return gen._infer_transform(grid)


def _nonbackground_components(grid):
    background = max(
        {value for row in grid for value in row},
        key=lambda value: sum(cell == value for row in grid for cell in row),
    )
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.RULE_HASH == "e3805c81bf19"


def test_generated_inputs_match_canonical_profile_and_are_decisive():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(78123, sample_index, difficulty=difficulty)
            assert (len(grid), len(grid[0])) == (5, 17)
            assert len({value for row in grid for value in row}) in {5, 6}
            assert _nonbackground_components(grid) in {6, 7}
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen._teaching_reasons(grid) == []
            observed = gen.observe_overrides(grid)
            assert observed["transform"] in gen.ALL_TRANSFORMS
            assert 4 <= observed["exemplar_cells"] <= 6
            assert 3 <= observed["query_cells"] <= 6


def test_schedule_covers_all_branches_and_every_five_window_breaks_public_family_shortcut():
    public_family = set(gen._OBSERVED_CANONICAL_FAMILY)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            six = [
                _transform_of(gen.generate(9000, index, difficulty=difficulty))
                for index in range(start, start + 6)
            ]
            assert set(six) == set(gen.ALL_TRANSFORMS)
            five = six[: gen.EXAMPLES_NEEDED]
            assert len(set(five)) == gen.EXAMPLES_NEEDED
            assert set(five) - public_family


def test_lesson_identifiable_for_every_schedule_residue():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            seed = 4242 + start
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                seed,
                start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_public_family_shortcut_fits_all_canonical_pairs_and_generated_missing_branches_refute_it():
    shortcut = gen.CANONICAL_SHORTCUTS["observed_transform_family_only"]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    for transform in ("identity", "flip_ud"):
        grid = gen.generate(
            20261002,
            7,
            difficulty="medium",
            transform=transform,
            exemplar_cells=5,
            query_cells=5,
        )
        assert gen.rule_mirror(grid) != shortcut(grid)


def test_override_axes_round_trip_and_unknown_keys_reject():
    for transform in gen.ALL_TRANSFORMS:
        for exemplar_cells in range(4, 7):
            for query_cells in range(3, 7):
                grid = gen.generate(
                    12345,
                    exemplar_cells * 100 + query_cells,
                    difficulty="hard",
                    transform=transform,
                    exemplar_cells=exemplar_cells,
                    query_cells=query_cells,
                )
                assert gen.observe_overrides(grid) == {
                    "transform": transform,
                    "exemplar_cells": exemplar_cells,
                    "query_cells": query_cells,
                }
                assert gen._teaching_reasons(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)


def test_targeted_impostors_are_rejected():
    base = gen.generate(777, 2, difficulty="medium")

    bad_separator = copy.deepcopy(base)
    bad_separator[0][5] = 0
    assert any("separator" in message for message in gen.self_check(bad_separator))

    bad_query_color = copy.deepcopy(base)
    panel_a, _, panel_c = gen._panels(base)
    a_color = next(value for row in panel_a for value in row if value)
    for r in range(5):
        for c in range(12, 17):
            if bad_query_color[r][c] != 0:
                bad_query_color[r][c] = a_color
    assert any("disjoint" in message for message in gen.self_check(bad_query_color))

    ambiguous = copy.deepcopy(base)
    symmetric = [[1, 2], [2, 1]]
    blank = [[0] * 5 for _ in range(5)]
    gen._place_crop(blank, symmetric, 1, 1)
    gen._write_panel(ambiguous, 0, blank)
    gen._write_panel(ambiguous, 1, blank)
    assert any("exactly one transform" in message for message in gen.self_check(ambiguous))

    impossible = copy.deepcopy(base)
    panel_b_start = 6
    changed = False
    for r in range(5):
        for c in range(panel_b_start, panel_b_start + 5):
            if impossible[r][c] == 0:
                impossible[r][c] = a_color
                changed = True
                break
        if changed:
            break
    assert any("transform" in message for message in gen.self_check(impossible))


def test_declared_witnesses_fire_and_refute_their_named_rivals():
    for transform in gen.ALL_TRANSFORMS:
        grid = gen.generate(
            6000,
            gen.ALL_TRANSFORMS.index(transform),
            transform=transform,
            exemplar_cells=5,
            query_cells=5,
        )
        witness_name = f"transform_{transform}_unique"
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        authoritative = gen.rule_mirror(grid)
        rivals = gen.WITNESS_RIVALS[witness_name]
        assert rivals
        assert any(gen.SEMANTIC_RIVALS[name](grid) != authoritative for name in rivals)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = gen.generate(456, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(456, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
