from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.2b6886e6e1b3.generator")

ROOT = find_root(__file__)
TASK_ID = "2b6886e6e1b3"


def _canonical_record():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical record for {TASK_ID}")


def _lesson(seed: int, start: int, difficulty: str):
    grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    demos = [{"input": grid, "output": gen._apply_rule(grid)} for grid in grids]
    query_grid = gen.generate(seed, start + 4, difficulty=difficulty)
    return grids, demos, {"input": query_grid, "output": gen._apply_rule(query_grid)}


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    assert gen.VERSION == "4.1.0"
    record = _canonical_record()
    normalized_rule = " ".join(record["program_solution"].split())
    canonical_hash = hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == canonical_hash == "860b011c178c"

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._apply_rule(pair["input"]) == pair["output"]


def test_every_sliding_four_sample_window_teaches_all_commands_and_kills_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 991):
            for start in range(8):
                grids, demos, query = _lesson(seed, start, difficulty)
                assert {grid[0][3] for grid in grids} == {1, 2, 3, 4}
                assert gen.lesson_identifiable(demos, query) == []

                for grid in grids:
                    answer = gen._apply_rule(grid)
                    cmd, left, right = gen._scene(grid)
                    candidates = gen._candidate_outputs(left, right)
                    assert candidates[cmd] == {
                        (r, c)
                        for r in range(3)
                        for c in range(3)
                        if answer[r][c] == 8
                    }
                    assert all(candidates[cmd] != candidates[other] for other in (1, 2, 3, 4) if other != cmd)


def test_override_full_boundaries_are_exact_observable_and_band_safe():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for cmd in (1, 2, 3, 4):
            for overlap_size in (1, 2, 3, 4):
                requested = {"cmd": cmd, "overlap_size": overlap_size}
                grid = gen.generate(
                    20_000 + case_index,
                    case_index % 13,
                    difficulty=difficulty,
                    **requested,
                )
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                assert gen.observe_overrides(grid) == requested
                case_index += 1

    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError):
        gen.generate(1, 2, cmd=5)
    with pytest.raises(ValueError):
        gen.generate(1, 2, overlap_size=0)


def test_generated_morphology_is_canonical_linked_and_transform_disambiguating():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(50):
            grid = gen.generate(31_000 + index, index * 7 + 3, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            cmd, left, right = gen._scene(grid)
            assert len(left) == len(right) == 5
            assert len({grid[1 + r][c] for r, c in left}) == 1
            assert len({grid[1 + r][4 + c] for r, c in right}) == 1
            outputs = gen._candidate_outputs(left, right)
            assert 1 <= len(outputs[cmd]) <= 4
            assert all(outputs[cmd] != outputs[other] for other in (1, 2, 3, 4) if other != cmd)


def test_structural_impostors_are_rejected_without_overconstraining_oracle_grammar():
    source = gen.generate(41_001, 5, difficulty="medium")

    stray_top = copy.deepcopy(source)
    stray_top[0][0] = 9
    stray_separator = copy.deepcopy(source)
    stray_separator[2][3] = 9
    missing_left = copy.deepcopy(source)
    for r in range(1, 4):
        for c in range(3):
            missing_left[r][c] = 0
    missing_right = copy.deepcopy(source)
    for r in range(1, 4):
        for c in range(4, 7):
            missing_right[r][c] = 0
    bad_command = copy.deepcopy(source)
    bad_command[0][3] = 9
    bad_shape = source[:-1]

    for name, grid in {
        "stray_top": stray_top,
        "stray_separator": stray_separator,
        "missing_left": missing_left,
        "missing_right": missing_right,
        "bad_command": bad_command,
        "bad_shape": bad_shape,
    }.items():
        assert gen.self_check(grid), name

    # Authority grammar may execute a four-cell motif, but the teaching
    # distribution must reject it because every linked/canonical motif has five.
    recombined = copy.deepcopy(source)
    occupied = [(r, c) for r in range(1, 4) for c in range(3) if recombined[r][c] != 0]
    r, c = occupied[0]
    recombined[r][c] = 0
    assert gen.self_check(recombined) == []
    assert gen.strict_canonical_like(recombined)
    assert gen._apply_rule(recombined)  # Python mirror remains defined on authority-valid grammar.


def test_replay_is_fresh_deterministic_and_process_global_rng_pure():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


@pytest.mark.parametrize("axis", ("cmd", "overlap_size"))
@pytest.mark.parametrize("invalid", (True, 2.5, "2"))
def test_integer_overrides_reject_coercible_non_integer_scalars(axis, invalid):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(52_001, 7, difficulty="medium", **{axis: invalid})


def _is_four_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, column = frontier.pop()
        for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + delta_row, column + delta_column)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return seen == cells


def test_normal_draws_use_connected_five_cell_panel_motifs():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(123_456 + index, index * 7 + 3, difficulty=difficulty)
            _, left, right = gen._scene(grid)
            assert _is_four_connected(left), (difficulty, index, "left", grid)
            assert _is_four_connected(right), (difficulty, index, "right", grid)


def test_strict_teaching_grammar_rejects_disconnected_five_cell_panels():
    grid = gen.generate(61_001, 9, difficulty="medium")
    left_color = next(value for row in grid[1:] for value in row[:3] if value)
    disconnected = {(0, 0), (0, 2), (1, 0), (1, 1), (2, 2)}
    for row in range(3):
        for column in range(3):
            grid[1 + row][column] = left_color if (row, column) in disconnected else 0

    assert gen.self_check(grid) == []
    errors = gen.strict_canonical_like(grid)
    assert any("connected" in error for error in errors), errors


@pytest.mark.parametrize("invalid", ("__invalid_difficulty__", True, 0.5, 7))
def test_unknown_or_non_band_difficulty_is_rejected(invalid):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(72_001, 3, difficulty=invalid)

@pytest.mark.parametrize("invalid", (True, False, 1.0, 1.75, "1"))
def test_seed_rejects_coercible_non_integer_scalars(invalid):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(invalid, 3, difficulty="medium")


@pytest.mark.parametrize("invalid", (True, False, 1.0, 1.75, "1", -1))
def test_sample_index_requires_a_literal_nonnegative_integer(invalid):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(72_002, invalid, difficulty="medium")
