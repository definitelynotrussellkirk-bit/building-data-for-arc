from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

try:
    from reviewer_support import canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    for parent in Path(__file__).resolve().parents:
        runtime = parent / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "083ba0fc4534"
REPO_ROOT = find_root(__file__)
MODULE_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
if not MODULE_PATH.is_file():
    MODULE_PATH = REPO_ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_083ba0fc4534", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=REPO_ROOT, labeled_only=True)


def _selected_rule_hash() -> str:
    with canonical_path(REPO_ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                normalized = " ".join(row["program_solution"].split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError(f"selected canonical rule {TASK_ID} not found")


def _panels(grid: list[list[int]]):
    height = len(grid)
    divider_cols = [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 5 for row in range(height))
    ]
    assert len(divider_cols) == 2
    d1, d2 = divider_cols
    panel_w = d1
    assert d2 == 2 * panel_w + 1
    return [
        [[grid[row][base + col] for col in range(panel_w)] for row in range(height)]
        for base in (0, d1 + 1, d2 + 1)
    ]


def _reference_output(grid: list[list[int]]) -> list[list[int]]:
    left, middle, right = _panels(grid)
    output = []
    for row in range(len(grid)):
        out_row = []
        for col in range(len(left[0])):
            a, b, x = left[row][col], middle[row][col], right[row][col]
            if a != 0 and (a == b or a == x):
                out_row.append(a)
            elif b != 0 and b == x:
                out_row.append(b)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def _cell_kind_counts(grid: list[list[int]]) -> Counter:
    left, middle, right = _panels(grid)
    counts = Counter()
    for row in range(len(grid)):
        for col in range(len(left[0])):
            a, b, x = left[row][col], middle[row][col], right[row][col]
            nonzero = [value for value in (a, b, x) if value != 0]
            if a != 0 and a == b == x:
                kind = "abc"
            elif a != 0 and a == b and x != a:
                kind = "ab"
            elif a != 0 and a == x and b != a:
                kind = "ax"
            elif b != 0 and b == x and a != b:
                kind = "bx"
            elif not nonzero:
                kind = "empty"
            elif len(nonzero) >= 2 and len(set(nonzero)) == len(nonzero):
                kind = "conflict"
            elif len(nonzero) == 1:
                kind = "lone"
            else:
                kind = "other"
            counts[kind] += 1
    return counts


def _first_nonzero_if_two_occupied(grid: list[list[int]]) -> list[list[int]]:
    left, middle, right = _panels(grid)
    out = []
    for row in range(len(grid)):
        out_row = []
        for col in range(len(left[0])):
            values = (left[row][col], middle[row][col], right[row][col])
            nonzero = [value for value in values if value != 0]
            out_row.append(nonzero[0] if len(nonzero) >= 2 else 0)
        out.append(out_row)
    return out


def test_declares_authority_and_matches_every_canonical_pair():
    assert GEN.RULE_HASH == _selected_rule_hash() == "076637306d69"
    for pair in _canonical_pairs():
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert _reference_output(grid) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_observable_and_band_independent(band):
    cases = (
        {"grid_h": 4, "panel_w": 4, "palette_size": 2, "n_conflicts": 1},
        {"grid_h": 5, "panel_w": 5, "palette_size": 3, "n_conflicts": 3},
        {"grid_h": 4, "panel_w": 5, "palette_size": 3, "n_conflicts": 2},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(100 + index, 70 + index, difficulty=band, **overrides)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.strict_canonical_like(grid) == []
        observed = GEN.observe_overrides(grid)
        assert {name: observed[name] for name in overrides} == overrides


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("grid_h", 3),
        ("grid_h", 6),
        ("panel_w", 3),
        ("panel_w", 6),
        ("palette_size", 1),
        ("palette_size", 4),
        ("n_conflicts", 0),
        ("n_conflicts", 4),
        ("grid_h", True),
        ("panel_w", 4.0),
        ("palette_size", "2"),
        ("typo_axis", 1),
        ("texture", "plain"),
    ],
)
def test_invalid_unknown_and_retired_overrides_fail_loudly(name, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **{name: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_sparse_canonical_profiled_and_teaches_every_branch(band):
    profiles = set()
    seen = {name: set() for name in ("grid_h", "panel_w", "palette_size", "n_conflicts")}
    for seed in range(80):
        grid = GEN.generate(seed, seed * 13 + 7, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == _reference_output(grid)

        kinds = _cell_kind_counts(grid)
        for required in ("ab", "ax", "bx", "abc", "conflict"):
            assert kinds[required] >= 1
        assert kinds["lone"] == 0
        assert 5 <= sum(kinds[k] for k in kinds if k != "empty") <= 7

        observed = GEN.observe_overrides(grid)
        for name in seen:
            seen[name].add(observed[name])
        palette = {value for row in grid for value in row}
        assert len(palette - {0, 5}) == observed["palette_size"]
        assert kinds["conflict"] == observed["n_conflicts"]
        profiles.add((len(grid), len(grid[0]), len(palette)))

        expected = _reference_output(grid)
        for competitor in GEN.LESSON_COMPETITORS.values():
            assert competitor(grid) != expected

    assert {(4, 14, 5), (4, 17, 5), (5, 17, 4)} <= profiles
    assert seen["grid_h"] == {4, 5}
    assert seen["panel_w"] == {4, 5}
    assert seen["palette_size"] == {2, 3}
    assert seen["n_conflicts"] == {1, 2, 3}


def test_generated_conflict_refutes_a_shortcut_that_fits_all_canonical_labels():
    assert all(
        _first_nonzero_if_two_occupied(pair["input"]) == pair["output"]
        for pair in _canonical_pairs()
    )
    assert "first_nonzero_if_two_occupied" in GEN.CANONICAL_SHORTCUTS
    for index in range(64):
        grid = GEN.generate(900 + index, index)
        assert GEN.CANONICAL_SHORTCUTS["first_nonzero_if_two_occupied"](grid) != _reference_output(grid)


def test_semantic_contract_is_executable_and_lessons_are_identifiable():
    expected = {
        "first_nonzero_if_two_occupied",
        "left_middle_only",
        "left_right_only",
        "middle_right_only",
        "unanimous_only",
        "copy_left",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected
    assert set(GEN.LESSON_COMPETITORS) == expected
    assert GEN.WITNESS_RIVALS
    assert all(GEN.WITNESS_RIVALS.values())
    assert GEN.EXAMPLES_NEEDED in range(1, 33)

    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(500 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": _reference_output(grid)})
            query_grid = GEN.generate(500 + start, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": _reference_output(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(competitor(demo["input"]) != demo["output"] for demo in demos)


def test_self_check_rejects_structural_impostors_and_malformed_inputs():
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(4)]):
        assert GEN.self_check(malformed)

    grid = GEN.generate(44, 9, grid_h=4, panel_w=4, palette_size=3, n_conflicts=2)
    mutations = []

    missing_divider = copy.deepcopy(grid)
    missing_divider[0][4] = 0
    mutations.append(missing_divider)

    stray_divider = copy.deepcopy(grid)
    stray_divider[0][0] = 5
    mutations.append(stray_divider)

    too_many_colors = copy.deepcopy(grid)
    for col, color in enumerate((1, 2, 3, 4)):
        too_many_colors[0][col] = color
    mutations.append(too_many_colors)

    no_consensus = [[0] * len(grid[0]) for _ in grid]
    for row in range(len(no_consensus)):
        no_consensus[row][4] = 5
        no_consensus[row][9] = 5
    mutations.append(no_consensus)

    assert all(GEN.self_check(mutated) for mutated in mutations)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(23, 11, difficulty="medium") == second
