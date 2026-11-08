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
    # Direct source-tree pytest does not automatically add the copied runtime.
    for parent in Path(__file__).resolve().parents:
        runtime = parent / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "8f10b83435aa"
REPO_ROOT = find_root(__file__)
MODULE_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
if not MODULE_PATH.is_file():
    MODULE_PATH = (
        REPO_ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SPEC = importlib.util.spec_from_file_location("review_generator_8f10b83435aa", MODULE_PATH)
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


def _panels(grid: list[list[int]]) -> list[list[list[int]]]:
    return [
        [[grid[row][base + col] for col in range(4)] for row in range(len(grid))]
        for base in (0, 5, 10)
    ]


def _occupancy_counts(grid: list[list[int]]) -> list[list[int]]:
    panels = _panels(grid)
    return [
        [sum(panel[row][col] != 0 for panel in panels) for col in range(4)]
        for row in range(len(grid))
    ]


def _reference_output(grid: list[list[int]]) -> list[list[int]]:
    counts = _occupancy_counts(grid)
    return [[8 if value >= 2 else 0 for value in row] for row in counts]


def _union_output(grid: list[list[int]]) -> list[list[int]]:
    counts = _occupancy_counts(grid)
    return [[8 if value >= 1 else 0 for value in row] for row in counts]


def _all_three_output(grid: list[list[int]]) -> list[list[int]]:
    counts = _occupancy_counts(grid)
    return [[8 if value == 3 else 0 for value in row] for row in counts]


def _copy_panel_output(grid: list[list[int]], panel_index: int) -> list[list[int]]:
    panel = _panels(grid)[panel_index]
    return [[8 if value != 0 else 0 for value in row] for row in panel]


def test_declares_rule_authority_and_matches_every_canonical_pair():
    assert GEN.RULE_HASH == _selected_rule_hash() == "bd5f126e874d"
    for pair in _canonical_pairs():
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]
        assert _reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_observable_and_band_independent(band):
    cases = (
        {"panel_h": 6, "n_majority": 6, "n_singletons": 3, "n_triples": 1},
        {"panel_h": 7, "n_majority": 10, "n_singletons": 9, "n_triples": 3},
        {"panel_h": 7, "n_majority": 8, "n_singletons": 5, "n_triples": 2},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(100 + index, 70 + index, difficulty=band, **overrides)
        assert GEN.self_check(grid, difficulty=band) == []
        observed = GEN.observe_overrides(grid)
        assert {name: observed[name] for name in overrides} == overrides


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("panel_h", 5),
        ("panel_h", 8),
        ("n_majority", 5),
        ("n_majority", 11),
        ("n_singletons", 2),
        ("n_singletons", 10),
        ("n_triples", 0),
        ("n_triples", 4),
        ("panel_h", True),
        ("n_majority", 7.5),
        ("n_singletons", "3"),
        ("typo_axis", 1),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(name, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **{name: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_example_teaches_the_majority_boundary_and_refutes_shortcuts(band):
    seen_heights = set()
    seen_majorities = set()
    seen_singletons = set()
    seen_triples = set()
    for seed in range(80):
        grid = GEN.generate(seed, seed * 13 + 7, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.strict_canonical_like(grid) == []
        counts = Counter(value for row in _occupancy_counts(grid) for value in row)
        assert counts[1] >= 3
        assert counts[2] >= 3
        assert counts[3] >= 1

        expected = _reference_output(grid)
        assert GEN.rule_mirror(grid) == expected
        assert _union_output(grid) != expected
        assert _all_three_output(grid) != expected
        for panel_index in range(3):
            assert _copy_panel_output(grid, panel_index) != expected

        observed = GEN.observe_overrides(grid)
        seen_heights.add(observed["panel_h"])
        seen_majorities.add(observed["n_majority"])
        seen_singletons.add(observed["n_singletons"])
        seen_triples.add(observed["n_triples"])

    # Difficulty may bias draws, but it must not collapse an advertised axis.
    assert seen_heights == {6, 7}
    assert seen_majorities == set(range(6, 11))
    assert seen_singletons == set(range(3, 10))
    assert seen_triples == {1, 2, 3}


def test_semantic_contract_is_executable_and_each_generated_lesson_is_identifiable():
    assert GEN.EXAMPLES_NEEDED in range(1, 33)
    expected_rivals = {
        "union_any",
        "all_three_only",
        "copy_panel_0",
        "copy_panel_1",
        "copy_panel_2",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals

    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(500 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": _reference_output(grid)})
            query_grid = GEN.generate(
                500 + start,
                start + GEN.EXAMPLES_NEEDED,
                difficulty=band,
            )
            query = {"input": query_grid, "output": _reference_output(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(competitor(demo["input"]) != demo["output"] for demo in demos)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert GEN.generate(23, 11, difficulty="medium") == second


def test_difficulty_changes_default_schedule_without_narrowing_override_domains():
    differing = 0
    for seed in range(30):
        outputs = {
            band: GEN.generate(seed, seed * 17 + 3, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        differing += len({repr(grid) for grid in outputs.values()}) > 1
    assert differing >= 20
