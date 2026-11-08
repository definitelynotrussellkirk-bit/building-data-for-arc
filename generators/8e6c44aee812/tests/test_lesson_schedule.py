"""Regression tests for separated repeats and whole-lesson coverage."""
from itertools import groupby
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "8e6c44aee812"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _separated(grid):
    active = [grid[i][i] for i in range(len(grid))]
    if active[-1] == 0:
        active.pop()
    runs = [value for value, _ in groupby(active)]
    return len(runs) > len(set(runs))


def _repeats_first_and_other_colors(grid):
    active = [grid[i][i] for i in range(len(grid))]
    if active[-1] == 0:
        active.pop()
    runs = [value for value, _ in groupby(active)]
    repeated = {value for value in runs if runs.count(value) >= 2}
    return active[0] in repeated and bool(repeated - {active[0]})


def _pair(grid):
    # A small independent expectation for fast combinatorial tests. The
    # separate public Racket probe verifies actual labels, not this mirror.
    diagonal = [grid[i][i] for i in range(len(grid))]
    if diagonal[-1] == 0:
        diagonal.pop()
    side = 2 * len(grid)
    output = [[diagonal[max(r, c) % len(diagonal)] for c in range(side)]
              for r in range(side)]
    return {"input": grid, "output": output}


def test_retained_first_run_shortcut_is_declared_and_fits_all_canonical_pairs():
    name = "first_run_per_color"
    assert name in GEN.LESSON_COMPETITORS
    assert name in GEN.CANONICAL_SHORTCUTS
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(canonical) == 4
    for pair in canonical:
        assert GEN.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]


@pytest.mark.parametrize("name", ("first_color_exempt_first_run", "other_colors_exempt_first_run"))
def test_color_role_shortcuts_are_declared_and_fit_the_canonical_labels(name):
    assert name in GEN.LESSON_COMPETITORS
    assert name in GEN.CANONICAL_SHORTCUTS
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert GEN.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]


def test_exact_retained_ambiguous_lesson_is_no_longer_accepted():
    path = (ROOT / "generators" / TASK / "counterexamples" /
            "review-35316dedd6e945e7-v0001" / "retained" / "checks" /
            "audit" / TASK / "evidence.json")
    rows = json.loads(path.read_text())["generated"]
    pairs = [{"input": row["input"], "output": row["output"]} for row in rows]
    assert all(GEN.self_check(pair["input"]) == [] for pair in pairs)
    assert GEN.lesson_identifiable(pairs[:3], pairs[3])


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", (0, 1, 17, 410000))
def test_every_six_pair_window_has_redundant_evidence_for_each_query_holdout(seed, band):
    grids = [GEN.generate(seed, i, difficulty=band) for i in range(17)]
    for start in range(12):
        window = grids[start:start + 6]
        assert sum(_separated(grid) for grid in window) >= 2, (seed, band, start)
        # Losing a single rich witness must leave evidence for both roles:
        # repeating the first diagonal color and repeating another color.
        assert sum(_repeats_first_and_other_colors(grid) for grid in window) >= 2, (
            seed, band, start
        )
        assert sum(len(grid) == 5 for grid in window) >= 2
        assert sum(len(grid) != 5 for grid in window) >= 2
        pairs = [_pair(grid) for grid in window]
        for held in range(6):
            demos = [pair for i, pair in enumerate(pairs) if i != held]
            query = pairs[held]
            assert GEN.lesson_identifiable(demos, query) == [], (seed, band, start, held)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    seed, band, start, held, name
                )


def test_declared_minimum_and_schedule_period_match_the_checked_contract():
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.LESSON_SCHEDULE_PERIOD == 12


def test_contiguous_and_separated_families_survive_with_both_padding_choices():
    observed = set()
    for seed in (0, 1):
        for index in range(24):
            grid = GEN.generate(seed, index, difficulty="medium")
            axes = GEN.observe_overrides(grid)
            observed.add((axes["pattern_class"], axes["padding"], _separated(grid)))
    for pattern in ("prefix_run", "complex_repeat"):
        for padding in ("none", "one"):
            for separated in (False, True):
                assert (pattern, padding, separated) in observed
