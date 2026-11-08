"""Behavioral regressions for request validation and three-demo lessons."""
from __future__ import annotations

from copy import deepcopy
import itertools

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("44e865b6a43e", root=ROOT)


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_request_scalars_require_literal_integers(argument, value):
    request = {"seed": 991, "sample_index": 0}
    request[argument] = value
    with pytest.raises(TypeError, match=argument):
        generator.generate(**request)


def test_sample_index_rejects_negative_values():
    with pytest.raises(ValueError, match="sample_index"):
        generator.generate(991, -1)


def test_integer_seeds_remain_deterministic_without_an_arbitrary_range_limit():
    for seed in (-1, 0, 2**80):
        assert generator.generate(seed, 0) == generator.generate(seed, 0)


@pytest.mark.parametrize("invalid", [[1], {"color": 1}, True, 1.0, "1"])
def test_self_check_reports_invalid_cells_without_crashing(invalid):
    grid = generator.generate(17, 0)
    grid[-1][1] = invalid
    reasons = generator.self_check(grid)
    assert reasons
    assert any("literal ARC colors" in reason for reason in reasons)


@pytest.mark.parametrize("pattern", ["ascending", "descending", "mixed", "repeat"])
def test_height_pattern_override_is_observable_in_the_returned_grid(pattern):
    grid = generator.generate(29, 1, n_bars=4, height_pattern=pattern)
    observed = generator.observe_overrides(grid)
    assert observed["n_bars"] == 4
    assert observed.get("height_pattern") == pattern


def test_semantic_contract_and_shortcuts_are_grounded_in_canonical_pairs():
    assert callable(getattr(generator, "lesson_identifiable", None))
    assert callable(getattr(generator, "strict_canonical_like", None))
    shortcuts = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert {"nearest_equal_height_association", "square_canvas"} <= shortcuts.keys()
    for pair in canonical_pairs("44e865b6a43e", root=ROOT, labeled_only=True):
        assert generator.strict_canonical_like(pair["input"]) == []
        for name, rival in shortcuts.items():
            assert rival(deepcopy(pair["input"])) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_small_cyclic_window_teaches_each_query_rotation(band):
    competitors = getattr(generator, "LESSON_COMPETITORS", {})
    assert len(competitors) >= 8, "a missing rival declaration is not a pass"
    assert generator.EXAMPLES_NEEDED == 3
    assert generator.LESSON_SCHEDULE_PERIOD == 4
    for seed, start in itertools.product((0, 13, 97), range(4)):
        pairs = []
        for index in range(start, start + 4):
            grid = generator.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
        for held_out in range(4):
            query = pairs[held_out]
            demos = [pair for i, pair in enumerate(pairs) if i != held_out]
            assert generator.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for name, rival in competitors.items():
                fits = all(rival(deepcopy(p["input"])) == p["output"] for p in demos)
                assert not (fits and rival(deepcopy(query["input"])) != query["output"]), (
                    band, seed, start, held_out, name
                )


def test_explicit_overrides_do_not_silently_certify_an_ambiguous_lesson():
    assert callable(getattr(generator, "lesson_identifiable", None))
    demos = []
    for index in range(3):
        grid = generator.generate(71, index, grid_h=9, n_bars=4, height_pattern="ascending")
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
    query_grid = generator.generate(71, 3, grid_h=8, n_bars=4, height_pattern="ascending")
    query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
    reasons = generator.lesson_identifiable(demos, query)
    assert any("square_canvas" in reason for reason in reasons), reasons


def test_lesson_hook_rejects_incorrect_labels_and_preserves_arguments():
    assert callable(getattr(generator, "lesson_identifiable", None))
    grid = generator.generate(43, 1)
    pair = {"input": grid, "output": generator.rule_mirror(grid)}
    demos = [deepcopy(pair)]
    demos[0]["output"][0][0] = 0
    before = deepcopy((demos, pair))
    reasons = generator.lesson_identifiable(demos, pair)
    assert reasons
    assert (demos, pair) == before
