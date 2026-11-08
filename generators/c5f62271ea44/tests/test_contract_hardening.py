"""Public-contract regressions for review-a3b91596a2979911.

These tests detect argument aliasing and canonical-shortcut overclaims; labels
are the repository's stored canonical observations, not a Python rule mirror.
"""
import copy
import json
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("c5f62271ea44", root=ROOT)


@pytest.mark.parametrize("entry_point", ["generate", "schedule_profile"])
@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_seed_and_index_reject_aliasing_scalars(entry_point, difficulty):
    call = getattr(GEN, entry_point)
    for name, values in {
        "seed": (True, False, 1.0, 1.75, "1", None),
        "sample_index": (True, False, 1.0, 1.75, "1", None, -1),
    }.items():
        for value in values:
            arguments = {"seed": 991, "sample_index": 0, "difficulty": difficulty}
            arguments[name] = value
            with pytest.raises((TypeError, ValueError), match=name):
                call(**arguments)


@pytest.mark.parametrize("seed", [0, -7, 2**80 + 19])
def test_integer_seed_domain_and_nonnegative_index_remain_reproducible(seed):
    for index in (0, 1, 2**48 + 3):
        first = GEN.generate(seed, index, difficulty="medium")
        assert first == GEN.generate(seed, index, difficulty="medium")
        assert GEN.self_check(first) == []
        assert GEN.observe_overrides(first)["symmetry"] == GEN.schedule_profile(seed, index)


def test_every_declared_canonical_shortcut_fits_every_stored_pair_without_mutation():
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            assert rival(grid) == pair["output"], (name, pair["variant"], pair["split"], pair["pair_index"])
            assert grid == pair["input"], name


def test_noncanonical_heuristics_remain_available_as_lesson_competitors():
    for name in ("always_identity", "corner_code_only", "always_flip_ud"):
        assert name in GEN.LESSON_COMPETITORS
        assert name in GEN.SEMANTIC_RIVALS
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT, labeled_only=True)
    for name in ("always_identity", "corner_code_only", "always_flip_ud"):
        assert any(GEN.LESSON_COMPETITORS[name](pair["input"]) != pair["output"] for pair in pairs)


def test_blue_corner_reflection_is_declared_with_a_real_counterexample():
    name = "blue_corner_reflection"
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.LESSON_COMPETITORS
    rival = GEN.CANONICAL_SHORTCUTS[name]
    for symmetry in GEN.SYMMETRIES:
        grid = GEN.generate(0, 0, symmetry=symmetry, profile_kind="canonical_1")
        agrees = rival(grid) == GEN.rule_mirror(grid)
        assert agrees == (symmetry in {"flip_lr", "flip_ud", "transpose", "anti_transpose"})


def _assert_five_pair_window_teaches_after_any_holdout(order):
    swapping = {"transpose", "anti_transpose", "rot_cw", "rot_ccw"}
    quarters = {"rot_cw", "rot_ccw"}
    assert len(order) == 16
    assert set(order) == set(GEN.SYMMETRIES)
    counts = Counter(order)
    assert counts["rot_cw"] + counts["rot_ccw"] == 7
    assert sorted((counts["rot_cw"], counts["rot_ccw"])) == [3, 4]
    assert counts["transpose"] == counts["anti_transpose"] == 1
    for start in range(len(order)):
        window = [order[(start + offset) % len(order)] for offset in range(5)]
        for query_index in range(5):
            demos = set(window[:query_index] + window[query_index + 1:])
            assert len(demos) >= 3, (start, query_index, window, "insufficient transform variety")
            assert demos & swapping, (start, query_index, window, "no swapped axes")
            assert demos - swapping, (start, query_index, window, "no preserved axes")
            assert demos & quarters, (start, query_index, window, "inverse transform survives")


def test_all_cyclic_windows_and_query_rotations_teach_both_canonical_rivals():
    for seed in range(128):
        order = [GEN.schedule_profile(seed, i, "medium") for i in range(16)]
        _assert_five_pair_window_teaches_after_any_holdout(order)
    assert GEN.LESSON_SCHEDULE_PERIOD == 16


def test_bounded_schedule_fallback_has_the_same_teaching_guarantee(monkeypatch):
    class FixedRandom:
        def __init__(self, offset):
            self.offset = offset

        def shuffle(self, order):
            pass

        def choice(self, values):
            return values[0]

        def randrange(self, length):
            return self.offset % length

    class Context:
        def __init__(self, offset):
            self.rng = FixedRandom(offset)

        def draw_rng(self, label):
            return self.rng

    # Force every proposed random order to be rejected; check fallback behavior
    # independently rather than using the generator's validity predicate.
    monkeypatch.setattr(GEN, "_teaching_order_valid", lambda order: False)
    for offset in range(16):
        monkeypatch.setattr(GEN, "gen_ctx", lambda **kwargs: Context(offset))
        order = [GEN.schedule_profile(0, i) for i in range(16)]
        _assert_five_pair_window_teaches_after_any_holdout(order)


def test_full_key_inverse_is_declared_and_only_disagrees_on_quarter_turns():
    name = "inverse_transform"
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.LESSON_COMPETITORS
    rival = GEN.CANONICAL_SHORTCUTS[name]
    for symmetry in GEN.SYMMETRIES:
        grid = GEN.generate(17, 0, symmetry=symmetry, profile_kind="canonical_1")
        assert (rival(grid) != GEN.rule_mirror(grid)) == (symmetry in {"rot_cw", "rot_ccw"})


@pytest.mark.parametrize("query_kind", ["production", "rotation"])
def test_racket_labeled_interim_inverse_counterexample_is_now_rejected(query_kind):
    path = ROOT / "generators/c5f62271ea44/counterexamples/inverse_transform_lesson.json"
    evidence = json.loads(path.read_text())
    witness = evidence["witnesses"][query_kind]
    pairs = witness["pairs"]
    demos = [pairs[i] for i in witness["demo_positions"]]
    query = pairs[witness["query_position"]]
    rival = GEN.CANONICAL_SHORTCUTS["inverse_transform"]
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert rival(pair["input"]) == pair["inverse_output"]
    assert all(pair["output"] == pair["inverse_output"] for pair in demos)
    assert query["output"] != query["inverse_output"]
    assert witness["old_hook_errors"] == []
    errors = GEN.lesson_identifiable(demos, query)
    assert any("inverse" in message for message in errors), errors


def test_lesson_hook_rejects_reflection_only_demonstrations():
    demos = []
    for i, symmetry in enumerate(("flip_lr", "anti_transpose", "flip_ud", "transpose")):
        grid = GEN.generate(0, i, symmetry=symmetry, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    grid = GEN.generate(0, 5, symmetry="identity", difficulty="medium")
    errors = GEN.lesson_identifiable(demos, {"input": grid, "output": GEN.rule_mirror(grid)})
    assert any("blue" in message and "reflection" in message for message in errors), errors


@pytest.mark.parametrize("query_kind", ["production", "rotation"])
def test_retained_racket_labeled_before_counterexample_is_now_rejected(query_kind):
    path = ROOT / "generators/c5f62271ea44/counterexamples/blue_corner_reflection_lesson.json"
    evidence = json.loads(path.read_text())
    rival = GEN.CANONICAL_SHORTCUTS["blue_corner_reflection"]
    demos = evidence["demos"]
    query = next(row for row in evidence["queries"] if row["kind"] == query_kind)
    for pair in demos + [query["pair"]]:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert all(rival(pair["input"]) == pair["output"] for pair in demos)
    assert rival(query["pair"]["input"]) == query["rival_output"]
    assert query["rival_output"] != query["pair"]["output"]
    assert query["baseline_hook_errors"] == []
    assert GEN.lesson_identifiable(demos, query["pair"])
