from __future__ import annotations

import importlib.util
import copy
import pytest
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "4ca8a7b38652"
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "count-scope parametric prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_count_scope_4ca8a7b38652", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rule_is_exact_canonical_and_alternative_changes_count_scope() -> None:
    prototype = _load_prototype()
    root = find_root(__file__)
    canonical = prototype.canonical_source(root=root)
    assert prototype.materialize_rule("nonzero", root=root) == canonical
    alternative = prototype.materialize_rule("all", root=root)
    assert alternative != canonical
    assert "(filter (lambda (v) (!= v 0))" in canonical
    assert "(filter (lambda (v) (!= v 0))" not in alternative


def test_episode_setting_is_chosen_once_and_demonstrations_refute_the_other_setting() -> None:
    prototype = _load_prototype()
    root = find_root(__file__)
    for seed, expected in ((0, "nonzero"), (1, "all")):
        episode = prototype.make_episode(seed, root=root, verify_racket=False)
        assert episode["meta"]["count_scope"] == expected
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 4
        rival = "all" if expected == "nonzero" else "nonzero"
        assert any(
            prototype.apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )
        assert any(0 in {v for row in pair["input"] for v in row} for pair in episode["train"])
        assert any(0 not in {v for row in pair["input"] for v in row} for pair in episode["train"])


def test_public_challenge_hides_parameter_program_and_query_answers() -> None:
    prototype = _load_prototype()
    episode = prototype.make_episode(1, root=find_root(__file__), verify_racket=False)
    public = prototype.public_challenge(episode)
    assert "meta" not in public
    assert "program" not in public
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_requested_demo_and_query_counts_are_independent() -> None:
    prototype = _load_prototype()
    episode = prototype.make_episode(
        6, train_count=6, test_count=3, root=find_root(__file__), verify_racket=False
    )
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 3
    assert episode["meta"]["train_count"] == 6
    assert episode["meta"]["test_count"] == 3
    pairs = episode["train"] + episode["test"]
    inputs = {tuple(map(tuple, pair["input"])) for pair in pairs}
    assert len(inputs) == 9
    # A wrong per-pair setting changes every zero-present output's dimensions.
    for pair in pairs:
        colors = {v for row in pair["input"] for v in row} - {0}
        factor = len(colors)
        assert len(pair["output"]) == 3 * factor
        assert all(len(row) == 3 * factor for row in pair["output"])
        for r in range(3 * factor):
            for c in range(3 * factor):
                assert pair["output"][r][c] == pair["input"][r // factor][c // factor]


@pytest.mark.parametrize("argument", ["train_count", "test_count"])
@pytest.mark.parametrize("bad", [True, False, 1.5, "4", 0, -1])
def test_invalid_counts_fail_before_sampling(argument, bad) -> None:
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError), match=argument):
        prototype.make_episode(0, verify_racket=False, **{argument: bad})


def test_pair_budget_is_explicit() -> None:
    prototype = _load_prototype()
    with pytest.raises(ValueError, match="64"):
        prototype.make_episode(0, train_count=61, test_count=4, verify_racket=False)


def test_repeated_candidate_stream_fails_instead_of_emitting_duplicate_queries(monkeypatch) -> None:
    prototype = _load_prototype()
    repeated = [[0, 1, 0], [1, 2, 0], [0, 2, 0]]
    monkeypatch.setattr(prototype, "build_input", lambda *args, **kwargs: copy.deepcopy(repeated))
    with pytest.raises(RuntimeError, match="unique"):
        prototype.make_episode(0, root=find_root(__file__), verify_racket=False)


def test_each_query_has_its_own_demo_only_rival_check() -> None:
    prototype = _load_prototype()
    episode = prototype.make_episode(1, root=find_root(__file__), verify_racket=False)
    audit = episode["meta"]["query_identifiability"]
    assert audit["consistent_settings"] == ["all"]
    assert len(audit["queries"]) == 4
    for index, query in enumerate(audit["queries"]):
        assert query["query_index"] == index
        assert query["identified_from_demonstrations"] is True
        assert set(query["rivals"]) == {"nonzero"}
        assert query["rivals"]["nonzero"]["fits_demonstrations"] is False
        assert query["rivals"]["nonzero"]["ambiguous"] is False
    assert audit["rivals"]["nonzero"]["refuting_demo_indices"]
    assert all(index < 4 for index in audit["rivals"]["nonzero"]["refuting_demo_indices"])


def _fixture_scale(grid, factor):
    return [[grid[r // factor][c // factor] for c in range(3 * factor)]
            for r in range(3 * factor)]


def test_query_answers_cannot_refute_a_demo_fitting_setting() -> None:
    prototype = _load_prototype()
    assess = getattr(prototype, "_assess_query_identifiability", None)
    assert callable(assess), "per-query demo-only identifiability assessment is missing"
    zero_free = [[1, 2, 2], [2, 1, 2], [1, 1, 2]]
    zero_present = [[0, 1, 0], [1, 2, 0], [0, 2, 0]]
    demo_output = _fixture_scale(zero_free, 2)
    demonstrations = [{"input": zero_free, "output": demo_output}]
    predictions = {
        "nonzero": [demo_output, _fixture_scale(zero_present, 2), _fixture_scale(zero_free, 2)],
        "all": [demo_output, _fixture_scale(zero_present, 3), _fixture_scale(zero_free, 2)],
    }
    audit = assess(demonstrations, predictions, "nonzero")
    assert audit["consistent_settings"] == ["nonzero", "all"]
    assert audit["rivals"]["all"]["fits_demonstrations"] is True
    assert audit["rivals"]["all"]["refuting_demo_indices"] == []
    assert audit["queries"][0]["identified_from_demonstrations"] is False
    assert audit["queries"][0]["rivals"]["all"]["ambiguous"] is True
    assert audit["queries"][1]["identified_from_demonstrations"] is True
    # Even a changed earlier query prediction cannot prune a demo-fitting rule.
    changed = copy.deepcopy(predictions)
    changed["all"][1] = changed["nonzero"][1]
    second_audit = assess(demonstrations, changed, "nonzero")
    assert second_audit["consistent_settings"] == audit["consistent_settings"]
    assert second_audit["queries"][1] == audit["queries"][1]
