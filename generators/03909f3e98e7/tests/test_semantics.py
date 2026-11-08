"""Portable semantic regressions using an independent coordinate oracle.

Canonical labels are authoring data. These tests neither run Racket nor claim
universal identifiability; they check the explicitly declared rival population.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    support = next((p for p in (ancestor, ancestor / "shared" / "runtime")
                    if (p / "reviewer_support.py").is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support))
        break
else:
    raise ImportError("No local public reviewer_support module")

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "03909f3e98e7"
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")
SHORTCUTS = {"floor_mass", "fixed_width_three", "compact_empty_axes",
             "largest_eight_component", "center_eight_components"}
EXTRAS = {"identity", "crop_only", "ceil_row", "ceil_col"}


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def occupied(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value != 0]


def bounds(grid):
    points = occupied(grid)
    return (min(r for r, c in points), min(c for r, c in points),
            max(r for r, c in points), max(c for r, c in points))


def oracle(grid, *, ceil_row=False, ceil_col=False):
    """Translate original foreground coordinates; never call generator helpers."""
    height, width = len(grid), len(grid[0])
    result = [[0] * width for _ in range(height)]
    points = occupied(grid)
    if not points:
        return result
    r0, c0, r1, c1 = bounds(grid)
    row_margin, col_margin = height - (r1 - r0 + 1), width - (c1 - c0 + 1)
    dr = (row_margin + int(ceil_row)) // 2 - r0
    dc = (col_margin + int(ceil_col)) // 2 - c0
    for r, c in points:
        result[r + dr][c + dc] = grid[r][c]
    return result


def profile(grid):
    r0, c0, r1, c1 = bounds(grid)
    points = occupied(grid)
    return (len(grid), len(grid[0]), r1 - r0 + 1, c1 - c0 + 1,
            len(points), len({grid[r][c] for r, c in points}))


def predict(solve, grid):
    original = deepcopy(grid)
    argument = deepcopy(grid)
    answer = solve(argument)
    assert argument == original, "declared rival mutated its input"
    assert isinstance(answer, list) and answer and all(isinstance(row, list) for row in answer)
    assert answer[0] and all(len(row) == len(answer[0]) for row in answer)
    assert all(type(value) is int and 0 <= value <= 9 for row in answer for value in row)
    return answer


def rival_inventory(module):
    rivals = getattr(module, "LESSON_COMPETITORS", None)
    assert isinstance(rivals, dict), "missing executable LESSON_COMPETITORS contract"
    assert set(rivals) == SHORTCUTS | EXTRAS
    assert all(callable(solve) for solve in rivals.values())
    return rivals


def rich_fixture(reflected=False):
    points = [(0, 0), (0, 1), (0, 4), (1, 0), (1, 1), (3, 4)]
    if reflected:
        points = [(3 - r, 4 - c) for r, c in points]
    grid = [[0] * 10 for _ in range(9)]
    for i, (r, c) in enumerate(points):
        grid[r][c] = 2 + i % 2
    return grid


def test_independent_oracle_reproduces_every_canonical_label(canonical):
    assert len(canonical) == 5
    for pair in canonical:
        assert oracle(pair["input"]) == pair["output"], (pair["split"], pair["pair_index"])


def test_all_declared_shortcuts_fit_every_canonical_pair(generator, canonical):
    shortcuts = getattr(generator, "CANONICAL_SHORTCUTS", None)
    assert isinstance(shortcuts, dict), "missing executable CANONICAL_SHORTCUTS"
    assert set(shortcuts) == SHORTCUTS
    rivals = rival_inventory(generator)
    for name, solve in shortcuts.items():
        assert callable(solve)
        assert rivals[name] is solve, "namespace aliases should share the exact callable"
        for pair in canonical:
            assert predict(solve, pair["input"]) == pair["output"], (
                name, pair["variant"], pair["split"], pair["pair_index"])


def test_strict_contract_accepts_every_canonical_input(generator, canonical):
    strict = getattr(generator, "strict_canonical_like", None)
    assert callable(strict), "missing strict_canonical_like hook"
    for pair in canonical:
        argument = deepcopy(pair["input"])
        assert strict(argument) in ([], True)
        assert argument == pair["input"]


@pytest.mark.parametrize("reflected", (False, True))
def test_exact_gap_and_mass_counterexamples_refute_all_declared_rules(generator, reflected):
    grid = rich_fixture(reflected)
    answer = oracle(grid)
    assert bounds(answer)[:2] == (2, 2)
    assert oracle(grid, ceil_row=True) != answer
    assert oracle(grid, ceil_col=True) != answer
    for name, solve in rival_inventory(generator).items():
        assert predict(solve, grid) != answer, name


def test_scheduled_core_and_rich_draws_have_their_promised_geometry(generator, canonical):
    schedule = getattr(generator, "schedule_profile", None)
    assert callable(schedule), "missing schedule_profile"
    assert generator.EXAMPLES_NEEDED == 3
    assert generator.LESSON_SCHEDULE_PERIOD == 4
    assert set(generator.SCHEDULE_PROFILES) == {"core", "witness", "free"}
    canonical_profiles = {profile(pair["input"]) for pair in canonical}
    rivals = rival_inventory(generator)
    witnesses = getattr(generator, "SEMANTIC_WITNESSES", None)
    assert isinstance(witnesses, dict) and SHORTCUTS <= set(witnesses)
    claims = getattr(generator, "WITNESS_RIVALS", None)
    assert isinstance(claims, dict) and SHORTCUTS <= set(claims)
    for band in BANDS:
        for seed in range(8):
            for index in range(4):
                branch = schedule(seed, index, difficulty=band)
                grid = generator.generate(seed, index, difficulty=band)
                if index % 2:
                    assert branch == "witness"
                    assert profile(grid)[:4] == (9, 10, 4, 5)
                    assert 6 <= len(occupied(grid)) <= 8
                    for name, solve in rivals.items():
                        assert predict(solve, grid) != oracle(grid), (band, seed, index, name)
                    for name in SHORTCUTS:
                        assert witnesses[name](deepcopy(grid)) is True
                        named = claims[name]
                        named = [named] if isinstance(named, str) else named
                        assert name in named
                elif index % 4 == 0:
                    assert branch == "core"
                    assert profile(grid) in canonical_profiles
                    assert generator.strict_canonical_like(deepcopy(grid)) in ([], True)
                else:
                    assert branch == "free"


def test_every_default_window_and_query_rotation_refutes_divergent_competitors(generator):
    rivals = rival_inventory(generator)
    hook = getattr(generator, "lesson_identifiable", None)
    assert callable(hook), "missing lesson_identifiable hook"
    for band in BANDS:
        for seed in range(8):
            for start in range(4):
                pairs = [{"input": generator.generate(seed, index, difficulty=band)}
                         for index in range(start, start + 4)]
                for pair in pairs:
                    pair["output"] = oracle(pair["input"])
                predictions = {name: [predict(solve, pair["input"]) for pair in pairs]
                               for name, solve in rivals.items()}
                for query_index in range(4):
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    query = pairs[query_index]
                    demos_copy, query_copy = deepcopy(demos), deepcopy(query)
                    assert hook(demos_copy, query_copy) == [], (band, seed, start, query_index)
                    assert demos_copy == demos and query_copy == query
                    for name, answers in predictions.items():
                        fitting = all(answers[i] == pair["output"] for i, pair in enumerate(pairs)
                                      if i != query_index)
                        assert not (fitting and answers[query_index] != query["output"]), (
                            band, seed, start, query_index, name)


def test_lesson_hook_rejects_canonical_only_ambiguity_but_allows_query_agreement(generator, canonical):
    hook = getattr(generator, "lesson_identifiable", None)
    assert callable(hook), "missing lesson_identifiable hook"
    demos = [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
             for pair in canonical[:3]]
    rich = rich_fixture()
    reasons = hook(deepcopy(demos), {"input": rich, "output": oracle(rich)})
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) and reason for reason in reasons)
    canonical_query = {"input": canonical[-1]["input"], "output": canonical[-1]["output"]}
    assert hook(deepcopy(demos), deepcopy(canonical_query)) == []
