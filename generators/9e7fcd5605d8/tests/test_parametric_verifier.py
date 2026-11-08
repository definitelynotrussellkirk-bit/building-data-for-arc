"""Focused failure-policy and public-boundary tests for the task verifier."""
import importlib.util
from pathlib import Path
import sys

import pytest


VERIFY = Path(__file__).resolve().parents[1] / "workspace/parametric/verify.py"


def verifier():
    assert VERIFY.is_file(), "the task-local verifier has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_topology_verifier", VERIFY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[1.0]], [[10]], [[-1]],
                                  [[1], [1, 2]], [(1,)], [[1]] * 31])
def test_strict_grid_rejects_invalid_arc_values(grid):
    with pytest.raises(ValueError):
        verifier().strict_grid(grid)


def test_strict_grid_returns_an_independent_exact_grid():
    source = [[0, 9], [4, 8]]
    result = verifier().strict_grid(source)
    source[0][0] = 1
    assert result == [[0, 9], [4, 8]]


@pytest.mark.parametrize("identity", [{"backend": "python", "protected": True},
                                      {"backend": "racket", "protected": False}])
def test_executor_rejects_nonprotected_or_nonracket_backend(identity):
    with pytest.raises(ValueError):
        verifier().Executor(lambda program, grid: grid, identity)


def test_executor_caches_actual_results_without_sharing_mutable_grids():
    module = verifier()
    execute = module.Executor(lambda program, grid: [[4]],
                              {"backend": "racket", "protected": True})
    first = execute("(rule! g)", [[2]])
    first[0][0] = 9
    assert execute("(rule! g)", [[2]]) == [[4]]
    assert execute.stats()["executions"] == 1
    assert execute.stats()["cache_hits"] == 1


def test_materialization_compares_claims_with_actual_outputs():
    module = verifier()
    episode = {"program_solution": "(rule! g)",
               "train": [{"input": [[2]], "output": [[8]]},
                         {"input": [[3]], "output": [[4]]}],
               "test": [{"input": [[5]], "output": [[4]]}]}
    actual, comparisons = module.label_episode(
        episode, 2, 1, "(rule! g)", lambda program, grid: [[4]])
    assert actual["train"][0]["output"] == [[4]]
    assert [row["matches"] for row in comparisons] == [False, True, True]


def test_duplicate_input_and_missing_claim_are_rejected():
    module = verifier()
    pair = {"input": [[2]], "output": [[4]]}
    episode = {"program_solution": "p", "train": [pair, pair],
               "test": [{"input": [[3]], "output": [[4]]}]}
    with pytest.raises(ValueError):
        module.normalize_episode(episode, 2, 1, "p")
    episode["train"] = [pair, {"input": [[5]]}]
    with pytest.raises(ValueError):
        module.normalize_episode(episode, 2, 1, "p")


def test_failed_rival_execution_is_not_counted_as_refutation():
    module = verifier()
    episode = {"train": [{"input": [[2]], "output": [[4]]}],
               "test": [{"input": [[3]], "output": [[4]]}]}
    def unavailable(program, grid):
        raise RuntimeError("reference execution failed")
    rows = module.audit_rivals(episode, {"broken": "invalid"}, unavailable)
    assert rows[0]["status"] == "execution_failed"
    assert rows[0]["refuted"] is False
    assert rows[0]["survived_demos"] is False
    assert rows[0]["errors"]


def test_demo_surviving_wrong_query_is_retained_as_a_failure():
    module = verifier()
    episode = {"train": [{"input": [[2]], "output": [[4]]}],
               "test": [{"input": [[3]], "output": [[8]]}]}
    rows = module.audit_rivals(episode, {"shortcut": "rival"},
                               lambda program, grid: [[4]])
    assert rows[0]["survived_demos"] is True
    assert rows[0]["query_disagreements"] == [0]
    assert rows[0]["status"] == "wrong_query_survivor"


def test_public_projection_has_one_query_and_ignores_private_fields():
    module = verifier()
    episode = {"train": [{"input": [[2]], "output": [[4]]}],
               "test": [{"input": [[3]], "output": [[8]]},
                        {"input": [[9]], "output": [[4]]}],
               "settings": {"min_holes": 1}, "seed": 17,
               "program_solution": "private"}
    payload, identity = module.public_projection(episode)
    assert payload == b'{"test":[{"input":[[3]]}],"train":[{"input":[[2]],"output":[[4]]}]}\n'
    episode["settings"] = {"secret": 55}
    episode["seed"] = -1
    episode["program_solution"] = "different private text"
    episode["test"][0]["output"] = [[7]]
    episode["test"][1]["input"] = [[6]]
    assert module.public_projection(episode) == (payload, identity)


def test_existing_output_directory_is_never_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        verifier().run(tmp_path, [0])
