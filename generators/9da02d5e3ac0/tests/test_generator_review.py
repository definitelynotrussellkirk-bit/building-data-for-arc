"""Regression tests for the reviewed 9da02d5e3ac0 sampler."""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from statistics import median

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "9da02d5e3ac0"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_9da02d5e3ac0", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def intended_output(grid):
    """Independent Python mirror of the selected Racket row rule."""
    result = []
    for row in grid:
        key = next((value for value in row if value != 5), None)
        result.append([
            key if value == 5 and key is not None else value
            for value in row
        ])
    return result


def fixed_key_position_output(grid):
    """Shortcut exposed by the first repaired sampler's fixed key placement."""
    result = []
    for row in grid:
        if not row:
            result.append([])
            continue
        key = row[1] if row[0] == 5 and len(row) > 1 else row[0]
        result.append([
            key if value == 5 and key != 5 else value
            for value in row
        ])
    return result


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_key_colors": len({
            value for row in grid for value in row if value not in (0, 5)
        }),
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_mirror_matches_outputs(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original




def test_selected_active_racket_authority_matches_canonical_exactly():
    root = find_root(__file__)
    canonical = None
    canonical_path = root / "shared/data/canonical/puzzles.jsonl"
    for line in canonical_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            canonical = row["program_solution"]
            break
    assert canonical is not None

    authority_path = (
        root
        / "shared/data/base/solutions/training"
        / "c9f8e694__9da02d5e3ac0.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == canonical


def test_metadata_pins_rule_and_declares_exact_observable_axes():
    assert gen.RULE_HASH == "aab70f56593c"
    assert gen.VERSION == "3.1.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_key_colors"}
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "first_column",
        "fixed_key_position",
        "first_nonzero",
    }
    assert set(gen.LESSON_COMPETITORS) >= set(gen.CANONICAL_SHORTCUTS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_observable_and_deterministic(band):
    options = {"grid_h": 8, "grid_w": 16, "n_key_colors": 4}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 15),
        ("grid_w", 7),
        ("grid_w", 17),
        ("n_key_colors", 1),
        ("n_key_colors", 5),
        ("grid_h", True),
        ("grid_w", 12.0),
        ("n_key_colors", "3"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_canonical_profile_support_and_input_diversity(band):
    profiles = set()
    inputs = set()
    exact_profile_hits = 0
    for index in range(80):
        grid = gen.generate(4100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        values = observed(grid)
        profile = (values["grid_h"], values["grid_w"], values["n_key_colors"] + 2)
        profiles.add(profile)
        inputs.add(tuple(tuple(row) for row in grid))
        exact_profile_hits += int(profile in {(12, 12, 4), (12, 12, 5)})
    assert exact_profile_hits >= 8
    assert len(profiles) >= 12
    assert len(inputs) >= 76


def test_every_generated_grid_contains_executable_shortcut_witnesses():
    for index in range(30):
        grid = gen.generate(9000 + index, index, difficulty="medium")
        expected = intended_output(grid)
        assert gen.self_check(grid) == []
        for witness in gen.SEMANTIC_WITNESSES.values():
            assert witness(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, name
        assert gen.lesson_identifiable(
            [{"input": grid, "output": expected}],
            {"input": grid, "output": expected},
        ) == []


def test_generated_family_refutes_fixed_key_position_shortcut():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(30):
            grid = gen.generate(910000 + 1000 * band_index + index, index, difficulty=band)
            assert fixed_key_position_output(grid) != intended_output(grid)


def test_declared_canonical_shortcuts_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert pairs
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


def test_self_check_rejects_malformed_and_semantically_vacuous_inputs():
    base = gen.generate(91, 7, grid_h=12, grid_w=12, n_key_colors=3)
    mutations = []

    ragged = deepcopy(base)
    ragged[-1] = ragged[-1][:-1]
    mutations.append(ragged)

    illegal = deepcopy(base)
    illegal[0][0] = 10
    mutations.append(illegal)

    no_fives = [[0 if value == 5 else value for value in row] for row in base]
    mutations.append(no_fives)

    no_zero = [[1 if value == 0 else value for value in row] for row in base]
    mutations.append(no_zero)

    one_key_color = [
        [2 if value not in (0, 5) else value for value in row]
        for row in base
    ]
    mutations.append(one_key_color)

    for grid in mutations:
        assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[False] * 8 for _ in range(8)]])
def test_self_check_reports_malformed_inputs_instead_of_raising(grid):
    assert gen.self_check(grid)


def _component_count(grid, *, same_color):
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    seen = set()
    count = 0
    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == background:
                continue
            count += 1
            color = grid[row][column]
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                current_row, current_column = queue.popleft()
                for row_step, column_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current_row + row_step, current_column + column_step)
                    nr, nc = neighbor
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if neighbor in seen or grid[nr][nc] == background:
                        continue
                    if same_color and grid[nr][nc] != color:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
    return count


def test_generated_morphology_retains_canonical_connected_blocks():
    multicolor_counts = []
    monochrome_counts = []
    for band in ("easy", "medium", "hard"):
        for index in range(18):
            grid = gen.generate(12000 + index, index, difficulty=band)
            multicolor_counts.append(_component_count(grid, same_color=False))
            monochrome_counts.append(_component_count(grid, same_color=True))

    # Canonical train inputs have 2/4 multicolor components and 8/9
    # monochrome components under the same modal-background convention.
    assert 2 <= median(multicolor_counts) <= 4
    assert 5 <= median(monochrome_counts) <= 12


def test_retained_counterexample_refutes_all_declared_rivals():
    case_path = HOME / "counterexamples" / "shortcut_witness.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))
    grid = case["input"]
    expected = case["expected_output"]
    assert gen.self_check(grid) == []
    assert intended_output(grid) == expected
    assert set(case["refutes"]) == set(gen.SEMANTIC_RIVALS)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(grid) != expected, name
