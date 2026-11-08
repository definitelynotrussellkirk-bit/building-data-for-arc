"""Focused negative controls for the task-local authoring/export probe.

Run through ``review.py run python3 -m pytest`` so the Racket tests use the
packet's protected reference runtime. No qualification or acceptance is granted.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
IDENTITY = "(rule! (lambda (g) g))"


@pytest.fixture(scope="module")
def probe():
    source = HOME / "workspace/parametric/probe.py"
    assert source.is_file(), "The task-local protected export probe is required"
    spec = importlib.util.spec_from_file_location("_test_b197_parametric_probe", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def execute():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    with _local_imports(ROOT / "shared/runtime", HOME / "workspace/parametric"):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


def test_demonstration_only_fit_reports_first_distinguishing_demo(probe, execute):
    train = [{"input": [[1]], "output": [[1]]}, {"input": [[2]], "output": [[2]]}]
    programs = {
        "selected": IDENTITY,
        "constant_one": "(rule! (lambda (g) '((1))))",
    }
    rows, outputs = probe.fit_demonstrations(train, programs, execute)
    assert rows[0]["survives_demos"] is True
    assert rows[0]["first_distinguishing_demo"] is None
    assert rows[1]["demonstration_agreement"] == [True, False]
    assert rows[1]["first_distinguishing_demo"] == 2
    assert outputs["constant_one"] == [[[1]], [[1]]]


@pytest.mark.parametrize("body", ["(/ 1 0)", "7"])
def test_failed_or_non_grid_rival_is_not_teaching_evidence(probe, execute, body):
    programs = {"selected": IDENTITY, "invalid_rival": f"(rule! (lambda (g) {body}))"}
    with pytest.raises(probe.ProbeError, match="invalid_rival.*demonstration 1"):
        probe.fit_demonstrations([{"input": [[1]], "output": [[1]]}], programs, execute)


def test_already_refuted_rival_must_still_execute_later_demonstrations(probe, execute):
    train = [{"input": [[1]], "output": [[1]]}, {"input": [[2]], "output": [[2]]}]
    programs = {"selected": IDENTITY, "late_error":
                "(rule! (lambda (g) (if (= (first (first g)) 1) '((9)) (/ 1 0))))"}
    with pytest.raises(probe.ProbeError, match="late_error.*demonstration 2"):
        probe.fit_demonstrations(train, programs, execute)


def test_demo_survivor_disagreeing_on_query_fails_instead_of_being_fitted_out(probe, execute):
    programs = {"selected": IDENTITY, "query_only_rival": "(rule! (lambda (g) '((1))))"}
    fitted, _ = probe.fit_demonstrations([{"input": [[1]], "output": [[1]]}], programs, execute)
    assert all(row["survives_demos"] for row in fitted)
    test = [{"input": [[i]], "output": [[i]]} for i in (2, 3, 4, 5)]
    with pytest.raises(probe.ProbeError, match="query_only_rival.*query 1"):
        probe.check_queries(test, programs, fitted, execute)
    assert all(row["survives_demos"] for row in fitted), "Query checks must not refit the survivor set"


def test_public_payload_contains_only_visible_grids_and_opaque_identity(probe):
    episode = {"train": [{"input": [[1]], "output": [[2]], "hidden": "demo metadata"}],
               "test": [{"input": [[3]], "output": [[4]], "hidden": "query metadata"}],
               "settings": {"rule": "secret"}, "program_solution": "secret program", "seed": 17}
    payload, checks = probe.public_identity_checks(episode)
    assert payload == b'{"test":[{"input":[[3]]}],"train":[{"input":[[1]],"output":[[2]]}]}\n'
    assert checks["metadata_mutation_invariant"] is True
    assert checks["query_answer_mutation_invariant"] is True
    assert checks["visible_mutation_changes_id"] is True
    assert len(checks["public_id"]) == 64


def test_first_turn_check_detects_more_queries_changing_visible_first_turn(probe):
    full = {"train": [{"input": [[1]], "output": [[2]]}],
            "test": [{"input": [[i]], "output": [[i + 1]]} for i in (3, 4, 5, 6)]}
    one = {"train": copy.deepcopy(full["train"]), "test": copy.deepcopy(full["test"][:1])}
    assert probe.first_turn_check(full, one)["equal_visible_bytes"] is True
    one["train"][0]["output"] = [[9]]
    with pytest.raises(probe.ProbeError, match="first-turn"):
        probe.first_turn_check(full, one)


def test_existing_export_directory_is_refused_before_execution(probe, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve.txt"
    marker.write_text("user data")
    with pytest.raises(FileExistsError):
        probe.run_probe(output, seeds=[0, 17], demo_counts=[3])
    assert marker.read_text() == "user data"
