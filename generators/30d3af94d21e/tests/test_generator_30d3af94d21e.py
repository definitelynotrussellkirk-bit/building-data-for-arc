from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy
from pathlib import Path


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.30d3af94d21e.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        for pair in row.get("train", []):
            yield pair["input"], pair["output"]
        for pair in row.get("test", []):
            yield pair["input"], pair.get("output")


def test_canonical_inputs_pass_and_mirror_matches_known_outputs():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 6
    for grid, expected in pairs:
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        if expected is not None:
            assert GEN._rule_mirror(grid) == expected


def test_scheduled_profiles_cover_every_semantic_branch():
    grids = [GEN.generate(314159, index, difficulty="medium") for index in range(6)]
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert GEN._rule_mirror(grid) != grid

    for name, predicate in GEN.SEMANTIC_WITNESSES.items():
        assert any(predicate(grid) for grid in grids), name

    demos = [
        {"input": grid, "output": GEN._rule_mirror(grid)}
        for grid in grids[:3]
    ]
    query = {"input": grids[3], "output": GEN._rule_mirror(grids[3])}
    assert GEN.lesson_identifiable(demos, query) == []



def test_racket_mode_background_regression_across_smoke_matrix():
    # A broad-palette draw once selected modal color 0 at seed 17.  The
    # canonical Racket `(mode g)` primitive ignores 0, causing three mirror
    # mismatches and one identity output in rule_smoke.  Exercise that exact
    # smoke matrix so the authority-compatible palette contract stays pinned.
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 41):
            grid = GEN.generate(seed, seed, difficulty=band)
            facts, errors = GEN._analyze(grid)
            assert errors == [], (band, seed, errors)
            assert facts["background"] != 0, (band, seed)
            assert GEN._rule_mirror(grid) != grid, (band, seed)

def test_exact_overrides_are_observable_without_clamping():
    grid = GEN.generate(
        17,
        3,
        difficulty="hard",
        height=9,
        width=14,
        palette_kind="warm",
        top_span_kind="bounded",
        bottom_span_kind="bounded",
        marker_row_count=6,
        seed_on_marker_row=True,
        asymmetry_force=True,
    )
    observed = GEN.observe_overrides(grid)
    assert len(grid) == 9
    assert len(grid[0]) == 14
    assert observed == {
        "top_span_kind": "bounded",
        "bottom_span_kind": "bounded",
        "marker_row_count": 6,
        "seed_on_marker_row": True,
        "asymmetry_force": True,
    }

    symmetric = GEN.generate(
        19,
        1,
        top_span_kind="left_open",
        bottom_span_kind="left_open",
        asymmetry_force=False,
        seed_on_marker_row=False,
    )
    observed_symmetric = GEN.observe_overrides(symmetric)
    assert observed_symmetric["top_span_kind"] == "left_open"
    assert observed_symmetric["bottom_span_kind"] == "left_open"
    assert observed_symmetric["asymmetry_force"] is False
    assert observed_symmetric["seed_on_marker_row"] is False


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(2718, 4, difficulty="easy")
    middle = random.getstate()
    second = GEN.generate(2718, 4, difficulty="easy")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after

    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_boundary_mutations():
    grid = GEN.generate(42, 0)
    facts, errors = GEN._analyze(grid)
    assert errors == []

    ragged = deepcopy(grid)
    ragged[0].pop()
    assert "rectangular" in " ".join(GEN.self_check(ragged))

    no_seed = deepcopy(grid)
    sr, sc = facts["seed"]
    no_seed[sr][sc] = facts["background"]
    assert GEN.self_check(no_seed)

    two_seeds = deepcopy(grid)
    for r, row in enumerate(two_seeds):
        for c, value in enumerate(row):
            if value == facts["background"]:
                two_seeds[r][c] = facts["fill"]
                break
        else:
            continue
        break
    assert GEN.self_check(two_seeds)

    too_few_markers = deepcopy(grid)
    marker_cells = [
        (r, c)
        for r, row in enumerate(too_few_markers)
        for c, value in enumerate(row)
        if value == facts["marker"]
    ]
    for r, c in marker_cells[3:]:
        too_few_markers[r][c] = facts["background"]
    assert "at least four marker cells" in " ".join(GEN.self_check(too_few_markers))
