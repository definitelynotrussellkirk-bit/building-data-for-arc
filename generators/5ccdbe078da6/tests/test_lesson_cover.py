"""Exact finite-rival witness selection, not a claim of universal identifiability."""
import importlib.util
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
# The source and staged generator layouts both put workspace beside tests.
spec = importlib.util.spec_from_file_location("lesson_cover", HOME / "workspace/lesson_cover.py")
cover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cover)


def test_exact_cover_beats_greedy():
    coverage = [set("abcd"), set("abe"), set("cdf")]
    assert cover.minimum_cover(coverage, set("abcdef"), max_demos=2) == [1, 2]


def test_cover_is_deterministic_and_lexicographic():
    assert cover.minimum_cover([{"a"}, {"b"}, {"a"}, {"b"}], {"a", "b"}, max_demos=2) == [0, 1]


def test_missing_rival_is_not_silently_ignored():
    with pytest.raises(cover.CoverageError, match="missing"):
        cover.minimum_cover([{"a"}], {"a", "b"}, max_demos=5)


def test_insufficient_demo_budget_is_explicit():
    with pytest.raises(cover.CoverageError, match="budget"):
        cover.minimum_cover([{"a"}, {"b"}], {"a", "b"}, max_demos=1)


def test_empty_rival_registry_does_not_certify_anything():
    with pytest.raises(ValueError, match="rival"):
        cover.minimum_cover([set()], set(), max_demos=2)


def test_query_inputs_not_outputs_are_the_only_query_argument():
    demos = [{"input": [[1]], "output": [[2]]}, {"input": [[3]], "output": [[4]]}]
    rivals = {"identity": lambda g: g}
    assert cover.select_demos(demos, rivals, query_inputs=[[[3]]], max_demos=2) == [0]


def test_duplicate_demo_inputs_with_inconsistent_labels_fail():
    demos = [{"input": [[1]], "output": [[2]]}, {"input": [[1]], "output": [[3]]}]
    with pytest.raises(ValueError, match="inconsistent"):
        cover.select_demos(demos, {"identity": lambda g: g}, query_inputs=[], max_demos=2)


def test_no_input_mutation_from_untrusted_rival():
    demos = [{"input": [[1]], "output": [[2]]}]
    def mutating(g):
        g[0][0] = 9
        return g
    assert cover.select_demos(demos, {"mutating": mutating}, query_inputs=[], max_demos=2) == [0]
    assert demos[0]["input"] == [[1]]


@pytest.mark.parametrize("budget", [0, -1, True, 2.5])
def test_invalid_budget_rejected(budget):
    with pytest.raises(ValueError):
        cover.minimum_cover([{"a"}], {"a"}, max_demos=budget)
