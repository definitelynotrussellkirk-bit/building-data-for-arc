"""Observable teaching regressions for the cyan beam task's blue-only shortcut.

These tests use the selected source tree and public authoring helpers. The ray
oracle below is independent of generator internals; the companion workspace
probe additionally checks the retained seed-8 lesson with actual Racket labels.
"""
from collections import Counter
from functools import lru_cache

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0b8ba9bb3c63"
ROOT = find_root(__file__)


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def ray_output(grid, *, only_blue=False):
    """Cell-ray oracle; restore every colored source object except red."""
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 8]
    assert cyan
    top, bottom = min(r for r, _ in cyan), max(r for r, _ in cyan)
    left, right = min(c for _, c in cyan), max(c for _, c in cyan)
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    starts = [(row, left - 1, 0, -1) for row in range(top, bottom + 1)]
    starts += [(row, right + 1, 0, 1) for row in range(top, bottom + 1)]
    starts += [(top - 1, col, -1, 0) for col in range(left, right + 1)]
    starts += [(bottom + 1, col, 1, 0) for col in range(left, right + 1)]
    for row, col, dr, dc in starts:
        while 0 <= row < height and 0 <= col < width:
            color = grid[row][col]
            blocked = color == 1 if only_blue else color not in (0, 2, 8)
            if blocked:
                break
            output[row][col] = 4
            row, col = row + dr, col + dc
    for row, cells in enumerate(grid):
        for col, color in enumerate(cells):
            if color not in (0, 2):
                output[row][col] = color
    return output


@pytest.fixture(scope="module")
def draw(generator):
    @lru_cache(maxsize=None)
    def cached(seed, index, difficulty, family=None):
        overrides = {"scene_family": family} if family else {}
        grid = generator.generate(seed, index, difficulty=difficulty, **overrides)
        assert generator.self_check(grid) == []
        expected = ray_output(grid)
        assert generator.rule_mirror(grid) == expected
        rival = ray_output(grid, only_blue=True)
        return {"input": grid, "output": expected, "rival": rival,
                "refuted": rival != expected,
                "family": generator.canonical_profile_signature(grid)}
    return cached


def test_canonical_labels_calibrate_independent_blue_only_rival():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs, "Canonical calibration must not silently test an empty population"
    for pair in pairs:
        assert ray_output(pair["input"]) == pair["output"]
        assert ray_output(pair["input"], only_blue=True) == pair["output"]


def assert_every_rotation_has_counterexample(pairs, context):
    witnesses = [pair["refuted"] for pair in pairs]
    assert sum(witnesses) >= 2, (context, "needs at least two actual blue-only counterexamples", witnesses)
    for query in range(len(pairs)):
        assert any(pair["refuted"] for i, pair in enumerate(pairs) if i != query), (context, query)


def test_seed8_ordinary_lesson_refutes_blue_only_in_every_query_rotation(draw):
    # Before the repair: public/public/public/generalized, witnesses F/F/F/T.
    pairs = [draw(8, index, None) for index in range(4)]
    assert_every_rotation_has_counterexample(pairs, "seed=8 default start=0")


@pytest.mark.parametrize("seed", [0, 8])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sampled_consecutive_lesson_has_two_counterexamples(draw, seed, difficulty):
    # Reuse eight draws for all five starting positions instead of drawing
    # twenty scenes. Every requested query rotation leaves a witness in demos.
    population = [draw(seed, index, difficulty) for index in range(8)]
    for start in range(5):
        assert_every_rotation_has_counterexample(
            population[start:start + 4], f"seed={seed} {difficulty} start={start}")


@pytest.mark.parametrize("seed", [0, 8])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_five_emitted_draws_preserve_two_public_three_generalized(draw, seed, difficulty):
    assert Counter(draw(seed, index, difficulty)["family"] for index in range(5)) == {
        "public": 2, "generalized": 3}


@pytest.mark.parametrize("seed", [0, 8])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_emitted_generalized_draw_is_an_actual_counterexample(draw, seed, difficulty):
    for index in range(8):
        pair = draw(seed, index, difficulty)
        if pair["family"] == "generalized":
            assert pair["refuted"], (seed, index, difficulty, "ineffective non-blue blocker")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_forced_public_is_blue_only_compatible(draw, difficulty):
    # Index 1 ordinarily needs a generalized witness after the repair; the
    # explicit public override must still select the public authoring manifold.
    pair = draw(0, 1, difficulty, "public")
    assert pair["family"] == "public"
    assert {color for row in pair["input"] for color in row} == {0, 1, 2, 8}
    assert not pair["refuted"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_forced_generalized_is_an_actual_blue_only_counterexample(draw, difficulty):
    pair = draw(0, 0, difficulty, "generalized")
    assert pair["family"] == "generalized"
    assert {color for row in pair["input"] for color in row} & {3, 5, 6, 7, 9}
    assert pair["refuted"], "A non-blue palette alone is not a counterexample"


def test_declared_rival_and_lesson_hook_match_the_observed_ambiguity(generator, draw):
    public = draw(0, 1, "medium", "public")
    generalized = draw(0, 0, "medium", "generalized")
    for pair in (public, generalized):
        assert generator.rival_blue_only(pair["input"]) == pair["rival"]
    demos = [{"input": public["input"], "output": public["output"]}] * 3
    query = {"input": generalized["input"], "output": generalized["output"]}
    reasons = generator.lesson_identifiable(demos, query)
    assert isinstance(reasons, list) and reasons and all(isinstance(item, str) for item in reasons)
    assert generator.lesson_identifiable([query, *demos[:2]], query) == []
    assert generator.lesson_identifiable(demos, demos[0]) == []
