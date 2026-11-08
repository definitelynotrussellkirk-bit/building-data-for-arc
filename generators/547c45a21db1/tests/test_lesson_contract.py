"""Finite, independently labeled checks of the declared teaching contract.

The literal witnesses' expected outputs were executed through the public Racket
apply command: checks/semantic-review/racket.json, result indices 1 and 2,
canonical rule 44ec512ed7bb.  Fixtures are embedded to keep the tests portable.
Generated labels below are test-only cardinal BFS diagnostics, cross-checked
against the canonical examples and that literal Racket result.
"""
from __future__ import annotations

from collections import deque
import copy
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_ID = "547c45a21db1"
for _ancestor in Path(__file__).resolve().parents:
    _support = next(
        (candidate for candidate in (_ancestor, _ancestor / "shared" / "runtime")
         if (candidate / "reviewer_support.py").is_file()),
        None,
    )
    if _support is not None:
        sys.path.insert(0, str(_support))
        break
else:
    raise RuntimeError("No local reviewer_support.py found")

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file()
)
_spec = importlib.util.spec_from_file_location("lesson_contract_generator", GENERATOR_PATH)
assert _spec is not None and _spec.loader is not None
GEN = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = GEN
_spec.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def cardinal_oracle(grid):
    """Derive distances directly, without generator predictors or path order."""
    active = {(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value in (1, 2, 3)}
    seeds = {color: [(r, c) for r, c in active if grid[r][c] == color]
             for color in (2, 3)}
    assert all(len(points) == 1 for points in seeds.values())

    def distances(seed):
        result = {seed: 0}
        queue = deque([seed])
        while queue:
            r, c = queue.popleft()
            for adjacent in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if adjacent in active and adjacent not in result:
                    result[adjacent] = result[(r, c)] + 1
                    queue.append(adjacent)
        assert set(result) == active
        return result

    d2, d3 = distances(seeds[2][0]), distances(seeds[3][0])
    output = copy.deepcopy(grid)
    for r, c in active:
        if grid[r][c] == 1:
            output[r][c] = 2 if d2[(r, c)] < d3[(r, c)] else 3 if d3[(r, c)] < d2[(r, c)] else 4
    return output


LITERAL_WITNESS = [
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 2, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
LITERAL_OUTPUT = [
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
    [0, 2, 0, 3, 0, 0, 0],
    [0, 2, 2, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
EVEN_LITERAL_WITNESS = [
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 2, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 0],
]
EVEN_LITERAL_OUTPUT = [
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0],
    [0, 2, 0, 3, 0, 0, 0],
    [0, 2, 2, 2, 0, 0, 0],
]
LITERAL_PAIRS = ((LITERAL_WITNESS, LITERAL_OUTPUT),
                 (EVEN_LITERAL_WITNESS, EVEN_LITERAL_OUTPUT))


def parity_raster_rival(grid, parity):
    """Use raster endpoint identity only for the selected active-length parity."""
    output = cardinal_oracle(grid)
    if sum(value != 0 for row in grid for value in row) % 2 == parity:
        seed2 = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
        seed3 = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
        if seed2 > seed3:
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == 1:
                        output[r][c] = {2: 3, 3: 2, 4: 4}[output[r][c]]
    return output


def review_rivals():
    rivals = dict(GEN.LESSON_COMPETITORS)
    # These independent rivals reproduce the parity-conditioned teaching gap
    # even if declarations accidentally lose them in a later refactor.
    rivals["review_even_raster"] = lambda grid: parity_raster_rival(grid, 0)
    rivals["review_odd_raster"] = lambda grid: parity_raster_rival(grid, 1)
    return rivals


def test_independent_oracle_matches_all_canonical_and_literal_outputs():
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        assert cardinal_oracle(pair["input"]) == pair["output"]
    for grid, output in LITERAL_PAIRS:
        assert GEN.self_check(grid) == []
        assert cardinal_oracle(grid) == output


def test_every_declared_canonical_shortcut_fits_every_canonical_pair():
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in CANONICAL:
            grid = copy.deepcopy(pair["input"])
            assert rival(grid) == pair["output"], (name, pair["split"], pair["pair_index"])
            assert grid == pair["input"], name


def test_literal_racket_witnesses_collectively_refute_every_declared_lesson_rival():
    assert GEN.LESSON_COMPETITORS
    for name, rival in GEN.LESSON_COMPETITORS.items():
        disagreements = []
        for original, expected in LITERAL_PAIRS:
            grid = copy.deepcopy(original)
            prediction = rival(grid)
            disagreements.append(prediction != expected)
            assert grid == original, name
            assert rival(copy.deepcopy(grid)) == prediction, name
        assert any(disagreements), name


@pytest.mark.parametrize("parity", (0, 1))
def test_independent_parity_raster_rivals_fit_all_canonical_pairs(parity):
    for pair in CANONICAL:
        assert parity_raster_rival(pair["input"], parity) == pair["output"]


@pytest.mark.parametrize("difficulty,start", (("easy", 1), ("medium", 11), ("hard", 3)))
def test_recorded_seed_zero_starts_have_no_parity_raster_ambiguity(difficulty, start):
    # Under the prior four-demo source, each of these exact starts produced a
    # rival-fitting lesson with a wrong query. All 15 old labels were verified
    # with Racket; see checks/code-review/conditional-rival-racket.json.
    size = GEN.EXAMPLES_NEEDED + 1
    grids = [GEN.generate(0, start + index, difficulty=difficulty) for index in range(size)]
    for parity in (0, 1):
        fits = [parity_raster_rival(grid, parity) == cardinal_oracle(grid) for grid in grids]
        for query_index in range(size):
            assert not (all(fit for index, fit in enumerate(fits) if index != query_index)
                        and not fits[query_index]), (difficulty, start, parity, query_index)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 1, 17, 314159))
def test_consecutive_pairs_retain_two_witnesses_per_rival_and_teach_all_query_rotations(difficulty, seed):
    # Exercise every declared cyclic start four times. Read the public lesson
    # size and schedule so changing either cannot silently shrink coverage.
    size = GEN.EXAMPLES_NEEDED + 1
    starts = range(len(GEN.SCHEDULE_PROFILES) * 4)
    assert starts and size > 1
    pairs = []
    fits = []
    parities = []
    assert GEN.LESSON_COMPETITORS
    rivals = review_rivals()
    base_names = [name for name in GEN.LESSON_COMPETITORS
                  if name not in ("even_raster_seed_order", "odd_raster_seed_order")]
    assert base_names
    for sample_index in range(size + len(starts) - 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        output = cardinal_oracle(grid)
        pairs.append({"input": grid, "output": output})
        parities.append(sum(value != 0 for row in grid for value in row) % 2)
        fits.append({name: rival(copy.deepcopy(grid)) == output
                     for name, rival in rivals.items()})
    for start in starts:
        window = pairs[start:start + size]
        window_fits = fits[start:start + size]
        for parity in (0, 1):
            witnesses = sum(
                parities[start + index] == parity and all(not result[name] for name in base_names)
                for index, result in enumerate(window_fits)
            )
            assert witnesses >= 2, (difficulty, seed, start, "all-base-rival-witnesses", parity)
        for name in rivals:
            assert sum(not result[name] for result in window_fits) >= 2, (difficulty, seed, start, name)
        for query_index in range(size):
            demo_indices = [index for index in range(size) if index != query_index]
            for name in rivals:
                fits_all_demos = all(window_fits[index][name] for index in demo_indices)
                assert not (fits_all_demos and not window_fits[query_index][name]), (
                    difficulty, seed, start, query_index, name,
                )
            demos = [window[index] for index in demo_indices]
            assert GEN.lesson_identifiable(demos, window[query_index]) == []
