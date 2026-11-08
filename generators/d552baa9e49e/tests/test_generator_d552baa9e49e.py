from __future__ import annotations

import copy
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d552baa9e49e import generator
from scripts.coder_synth_verify import ProgramVerifier


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE = ROOT / "data" / "base" / "solutions" / "banks" / "63dac95f0c67" / "M114__d552baa9e49e.json"
TASK_ID = "d552baa9e49e"


def canonical_row():
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def decode(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def independent_crop(grid):
    cells = [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0 and (row, col) != (0, 0)
    ]
    row0 = min(row for row, _col, _value in cells)
    row1 = max(row for row, _col, _value in cells)
    col0 = min(col for _row, col, _value in cells)
    col1 = max(col for _row, col, _value in cells)
    crop = [[0] * (col1 - col0 + 1) for _ in range(row1 - row0 + 1)]
    for row, col, value in cells:
        crop[row - row0][col - col0] = value
    return crop


def independent_mask_key(crop):
    mask = tuple(tuple(int(value != 0) for value in row) for row in crop)

    def rotate(value):
        return tuple(tuple(row) for row in zip(*value[::-1]))

    def flip(value):
        return tuple(tuple(reversed(row)) for row in value)

    forms = set()
    current = mask
    for _ in range(4):
        forms.add(current)
        forms.add(flip(current))
        current = rotate(current)
    return min(forms)


def independent_component_count(crop):
    cells = {
        (row, col)
        for row, values in enumerate(crop)
        for col, value in enumerate(values)
        if value != 0
    }
    count = 0
    while cells:
        count += 1
        stack = [cells.pop()]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in cells:
                    cells.remove(point)
                    stack.append(point)
    return count


def python_rule(grid):
    cmd = grid[0][0]
    return generator._apply_transform(independent_crop(grid), cmd)


def strict_canonical_like(grid, canonical_keys):
    crop = independent_crop(grid)
    colors = {
        value
        for row in range(len(grid))
        for col, value in enumerate(grid[row])
        if value != 0 and (row, col) != (0, 0)
    }
    return (
        (len(grid), len(grid[0])) == (8, 9)
        and grid[0][0] in {1, 2, 3, 4}
        and (len(crop), len(crop[0])) == (3, 3)
        and len(colors) == 2
        and independent_mask_key(crop) in canonical_keys
    )


def test_rule_sources_are_synchronized_hash_pinned_and_description_corrected():
    row = canonical_row()
    base = json.loads(BASE.read_text(encoding="utf-8"))
    canonical = row["program_solution"]
    assert generator.RULE_HASH == "21cd1730c540"
    assert base["racket_target"]["raw_code"] == canonical
    assert base["racket_target"]["target_code"] == canonical
    assert "green(3) → transpose" in base["description_target"]["target_text"]


def test_all_canonical_pairs_are_accepted_and_rule_matches_with_input_purity():
    row = canonical_row()
    pairs = canonical_pairs()
    assert len(pairs) == 5
    inputs = [decode(pair["input"]) for pair in pairs]
    expected = [decode(pair["output"]) for pair in pairs]
    for grid, output in zip(inputs, expected):
        snapshot = copy.deepcopy(grid)
        assert generator.self_check(grid, meta={"canonical": True}) == []
        assert python_rule(grid) == output
        assert grid == snapshot

    with ProgramVerifier(timeout=20) as verifier:
        out_a1 = verifier.apply(row["program_solution"], inputs[0])
        out_b = verifier.apply(row["program_solution"], inputs[1])
        out_a2 = verifier.apply(row["program_solution"], inputs[0])
    assert out_a1 == expected[0]
    assert out_b == expected[1]
    assert out_a2 == out_a1
    assert inputs[0] == decode(pairs[0]["input"])
    assert inputs[1] == decode(pairs[1]["input"])


def test_canonical_mask_bank_is_derived_from_every_train_and_test_input():
    derived = {
        independent_mask_key(independent_crop(decode(pair["input"])))
        for pair in canonical_pairs()
    }
    assert derived == set(generator._CANONICAL_MASK_KEYS)


def test_exact_override_boundaries_and_observation():
    for band in ("easy", "medium", "hard"):
        for height in (8, 15):
            for width in (9, 16):
                for cmd in (1, 5):
                    for colors in (2, 4):
                        for profile in generator.MOTIF_PROFILES:
                            grid = generator.generate(
                                701,
                                19,
                                difficulty=band,
                                grid_h=height,
                                grid_w=width,
                                cmd=cmd,
                                n_distinct_colors=colors,
                                motif_profile=profile,
                            )
                            assert generator.self_check(grid, difficulty=band) == []
                            assert generator.observe_overrides(grid) == {
                                "grid_h": height,
                                "grid_w": width,
                                "cmd": cmd,
                                "n_distinct_colors": colors,
                                "motif_profile": profile,
                            }
    with pytest.raises(ValueError):
        generator.generate(1, 1, grid_h=7)
    with pytest.raises(ValueError):
        generator.generate(1, 1, grid_w=17)
    with pytest.raises(ValueError):
        generator.generate(1, 1, cmd=0)
    with pytest.raises(TypeError):
        generator.generate(1, 1, dead_axis=True)


def test_200_draw_strict_linked_semantic_census_per_band_and_stability():
    canonical_keys = {
        independent_mask_key(independent_crop(decode(pair["input"])))
        for pair in canonical_pairs()
    }
    for seed_base in (10_000, 30_000):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            counts = Counter()
            inputs = set()
            outputs = set()
            for offset in range(200):
                grid = generator.generate(
                    seed_base + band_index * 1_000 + offset,
                    offset,
                    difficulty=band,
                )
                assert generator.self_check(grid, difficulty=band) == []
                observed = generator.observe_overrides(grid)
                crop = independent_crop(grid)
                counts[f"cmd_{observed['cmd']}"] += 1
                counts[f"colors_{observed['n_distinct_colors']}"] += 1
                counts[f"profile_{observed['motif_profile']}"] += 1
                counts["square_crop"] += len(crop) == len(crop[0])
                counts["rectangular_crop"] += len(crop) != len(crop[0])
                counts["connected"] += independent_component_count(crop) == 1
                counts["disconnected"] += independent_component_count(crop) > 1
                counts["strict_canonical_like"] += strict_canonical_like(grid, canonical_keys)
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, python_rule(grid))))
            assert counts["strict_canonical_like"] == 50
            assert counts["profile_canonical_morphology"] == 50
            assert counts["profile_generalized_morphology"] == 150
            assert all(counts[f"cmd_{cmd}"] > 0 for cmd in range(1, 6))
            assert all(counts[f"colors_{n}"] > 0 for n in range(2, 5))
            assert counts["square_crop"] > 0 and counts["rectangular_crop"] > 0
            assert counts["connected"] > 0 and counts["disconnected"] > 0
            assert len(inputs) >= 198
            assert len(outputs) >= 198


def test_aligned_lessons_repeat_the_query_command_and_disambiguate_transforms():
    for band in ("easy", "medium", "hard"):
        for block in range(25):
            start = block * 4
            grids = [
                generator.generate(80_000 + block, start + offset, difficulty=band)
                for offset in range(4)
            ]
            commands = [grid[0][0] for grid in grids]
            assert len(set(commands[:3])) == 3
            assert commands[3] == commands[0]
            for grid in grids:
                crop = independent_crop(grid)
                outputs = {
                    tuple(map(tuple, generator._apply_transform(crop, cmd)))
                    for cmd in range(1, 6)
                }
                assert len(outputs) == 5
                assert tuple(map(tuple, crop)) not in outputs


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    state = random.getstate()
    first = generator.generate(77, 9, difficulty="hard")
    after = random.getstate()
    second = generator.generate(77, 9, difficulty="hard")
    assert state == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second


def test_task_local_mutation_fixtures_are_all_rejected():
    fixtures = generator.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert generator.self_check(grid), name
        with pytest.raises(ValueError):
            generator.observe_overrides(grid)


def test_negative_command_recombination_is_distribution_invalid_but_oracle_executable():
    row = canonical_row()
    grid = generator.generate(404, 7, difficulty="medium")
    motif_colors = {
        value
        for r, values in enumerate(grid)
        for c, value in enumerate(values)
        if value != 0 and (r, c) != (0, 0)
    }
    invalid = copy.deepcopy(grid)
    invalid_cmd = next(color for color in (9, 8, 7, 6) if color not in motif_colors)
    invalid[0][0] = invalid_cmd
    assert generator.self_check(invalid)
    with ProgramVerifier(timeout=20) as verifier:
        output = verifier.apply(row["program_solution"], invalid)
    assert output == generator._flip_ud(independent_crop(invalid))
