from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.6ecd8be24495.generator"
)
ROOT = find_root(__file__)
BASE_PATH = next(
    path
    for path in (
        ROOT / "shared/data/base/solutions/banks/8edfaf6db623/M104__6ecd8be24495.json",
        ROOT / "data/base/solutions/banks/8edfaf6db623/M104__6ecd8be24495.json",
    )
    if path.is_file()
)


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _unused_seed_color(grid):
    used = {value for row in grid for value in row}
    return next(value for value in range(1, 10) if value not in used and value != 5)


def test_rule_hash_source_sync_and_all_canonical_pairs():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert gen.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]

    base = json.loads(BASE_PATH.read_text())
    assert base["racket_target"]["raw_code"] == row["program_solution"]
    assert base["racket_target"]["target_code"] == row["program_solution"]

    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.expected_output(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_observable_in_every_band():
    cases = [
        {"grid_h": 9},
        {"grid_h": 18},
        {"grid_w": 9},
        {"grid_w": 18},
        {"n_chambers": 2},
        {"n_chambers": 4},
        {"winner_rank": 0},
        {"winner_rank": 3},
        {"n_seed_colors": 2},
        {"n_seed_colors": 4},
        {"majority_margin": 1},
        {"majority_margin": 3},
        {
            "grid_h": 9,
            "grid_w": 9,
            "n_chambers": 4,
            "winner_rank": 3,
            "n_seed_colors": 4,
            "majority_margin": 3,
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(2000 + index, 19, difficulty=band, **overrides)
            assert gen.self_check(grid, difficulty=band) == []
            observed = {
                "grid_h": len(grid),
                "grid_w": len(grid[0]),
                **gen.observe_overrides(grid),
            }
            for axis, expected in overrides.items():
                assert observed[axis] == expected, (band, overrides, observed)

    with pytest.raises(ValueError, match="requires at least 4 chambers"):
        gen.generate(1, 0, n_chambers=2, winner_rank=3)
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, density="sparse")


def test_four_chamber_episode_schedule_exposes_every_winner_position():
    for seed in range(30):
        ranks = []
        for sample_index in range(4):
            grid = gen.generate(
                seed,
                sample_index,
                difficulty="medium",
                n_chambers=4,
            )
            ranks.append(gen.observe_overrides(grid)["winner_rank"])
        assert ranks == [0, 1, 2, 3]


def test_strict_linked_semantic_support_in_each_band():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        support = defaultdict(set)
        distinct_inputs = set()
        distinct_outputs = set()
        stronger_losing_pile = 0
        draws = 240
        for offset in range(draws):
            seed = 100_000 * (band_index + 1) + offset
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            obs = gen.semantic_observables(grid)
            distinct_inputs.add(tuple(map(tuple, grid)))
            distinct_outputs.add(tuple(map(tuple, gen.expected_output(grid))))
            support["layout"].add(obs["layout"])
            support["n_chambers"].add(obs["n_chambers"])
            support["winner_rank"].add(obs["winner_rank"])
            support["chamber_winner_pair"].add((obs["n_chambers"], obs["winner_rank"]))
            support["n_seed_colors"].add(obs["n_seed_colors"])
            support["majority_margin"].add(obs["majority_margin"])
            assert 1 <= len(obs["winner_color_counts"]) <= obs["n_seed_colors"]
            if obs["n_seed_colors"] >= 3 and obs["n_chambers"] >= 3:
                assert len(obs["winner_color_counts"]) == 2
            assert max(obs["seed_totals"]) == obs["seed_totals"][obs["winner_rank"]]
            assert obs["seed_totals"].count(max(obs["seed_totals"])) == 1
            if obs["n_seed_colors"] >= 3:
                assert obs["losing_peak_exceeds_winner_majority"]
                stronger_losing_pile += 1

        assert support["layout"] == {"rows", "columns", "t", "cross"}
        assert support["n_chambers"] == {2, 3, 4}
        assert support["winner_rank"] == {0, 1, 2, 3}
        assert support["chamber_winner_pair"] == {
            (2, 0), (2, 1),
            (3, 0), (3, 1), (3, 2),
            (4, 0), (4, 1), (4, 2), (4, 3),
        }
        assert support["n_seed_colors"] == {2, 3, 4}
        assert support["majority_margin"] == {1, 2, 3}
        assert stronger_losing_pile >= 100
        assert len(distinct_inputs) >= 235
        assert len(distinct_outputs) >= 235


def test_only_winner_blanks_change_to_local_majority():
    for seed in range(120):
        grid = gen.generate(seed, seed + 7, difficulty=("easy", "medium", "hard")[seed % 3])
        analysis = gen._analysis(grid)
        output = gen.expected_output(grid)
        winner = analysis["chambers"][analysis["winner_rank"]]
        winner_cells = set(winner["cells"])
        changed = {
            (r, c)
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if grid[r][c] != output[r][c]
        }
        assert changed
        assert changed <= winner_cells
        assert all(grid[r][c] == 0 for r, c in changed)
        assert {output[r][c] for r, c in changed} == {analysis["majority_color"]}
        for r, c in winner_cells - changed:
            assert output[r][c] == grid[r][c]


def test_self_check_rejects_targeted_structural_impostors():
    fixtures = dict(gen.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    # Negative recombination: introduce a color absent everywhere else by
    # replacing one winner-majority seed, making the local majority ambiguous.
    grid = gen.generate(
        77,
        2,
        n_chambers=4,
        winner_rank=2,
        n_seed_colors=2,
        majority_margin=1,
    )
    analysis = gen._analysis(grid)
    winner = analysis["chambers"][analysis["winner_rank"]]
    majority = analysis["majority_color"]
    replacement = _unused_seed_color(grid)
    bad = copy.deepcopy(grid)
    r, c = next(
        (r, c) for r, c in winner["cells"] if grid[r][c] == majority
    )
    bad[r][c] = replacement
    assert replacement not in {
        bad[rr][cc]
        for index, chamber in enumerate(analysis["chambers"])
        if index != analysis["winner_rank"]
        for rr, cc in chamber["cells"]
    }
    assert gen.self_check(bad)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(81357)
    state = random.getstate()
    first = gen.generate(1234, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(1234, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert first != second
    assert gen.generate(1234, 9, difficulty="hard") == second


def test_integer_axes_reject_non_exact_values():
    invalid = [
        {"grid_h": "9"},
        {"grid_w": 9.8},
        {"n_chambers": True},
        {"winner_rank": 1.9},
        {"n_seed_colors": "3"},
        {"majority_margin": 2.7},
    ]
    for overrides in invalid:
        with pytest.raises(TypeError, match="exact integer"):
            gen.generate(11, 3, **overrides)


def test_four_demo_lesson_refutes_first_max_distinct_color_proxy():
    for seed in range(12):
        disagreements = []
        for sample_index in range(4):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            analysis = gen._analysis(grid)
            distinct = [len(record["counts"]) for record in analysis["chambers"]]
            proxy_rank = distinct.index(max(distinct))
            disagreements.append(proxy_rank != analysis["winner_rank"])
        assert any(disagreements), seed
