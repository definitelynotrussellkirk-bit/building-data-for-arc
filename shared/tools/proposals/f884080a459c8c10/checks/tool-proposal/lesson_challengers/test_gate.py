"""Boundary and teaching-semantics tests for the optional external rival gate."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("lesson_challenger_gate", Path(__file__).with_name("gate.py"))
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def lesson():
    return {"train": [{"input": [[1]], "output": [[1]]}],
            "test": [{"input": [[2]], "output": [[3]]}]}


def test_rival_that_fits_demos_and_changes_query_is_a_teaching_defect():
    result = GATE.score(lesson(), lambda grid: grid, rotate=False)
    assert result["production"]["ambiguous"] is True
    assert result["production"]["refuting_demo_positions"] == []
    assert result["production"]["rival_output"] == [[2]]
    assert result["production"]["reference_output"] == [[3]]


def test_refuting_demo_resolves_this_rival_without_universal_claim():
    data = lesson()
    data["train"].append({"input": [[4]], "output": [[5]]})
    result = GATE.score(data, lambda grid: grid, rotate=False)
    assert result["production"]["ambiguous"] is False
    assert result["production"]["refuting_demo_positions"] == [1]


def test_query_agreement_is_not_ambiguity():
    data = lesson()
    data["test"][0]["output"] = [[2]]
    result = GATE.score(data, lambda grid: grid, rotate=False)
    assert result["production"]["ambiguous"] is False


def test_rotation_policy_is_explicit_and_leaves_one_query_out():
    result = GATE.score(lesson(), lambda grid: grid, rotate=True)
    assert len(result["rotations"]) == 2
    assert [r["ambiguous"] for r in result["rotations"]] == [False, True]
    assert result["rotations"][0]["refuting_demo_positions"] == [1]


@pytest.mark.parametrize("bad", [[], [[]], [[True]], [[1.0]], [[10]], [[1, 2], [1]]])
def test_malformed_reference_grids_fail_instead_of_passing(bad):
    data = lesson()
    data["test"][0]["output"] = bad
    with pytest.raises(ValueError):
        GATE.score(data, lambda grid: grid, rotate=False)


def test_rival_execution_errors_are_not_silent_refutations():
    def broken(grid):
        raise RuntimeError("intentional test error")
    with pytest.raises(RuntimeError, match="intentional"):
        GATE.score(lesson(), broken, rotate=False)


def test_rival_cannot_mutate_the_supplied_reference_input():
    data = lesson()
    def mutate(grid):
        grid[0][0] = 9
        return grid
    GATE.score(data, mutate, rotate=False)
    assert data["train"][0]["input"] == [[1]]


def test_missing_demos_and_private_query_labels_are_errors():
    data = lesson()
    data["train"] = []
    with pytest.raises(ValueError):
        GATE.score(data, lambda grid: grid, rotate=False)
    data = lesson()
    del data["test"][0]["output"]
    with pytest.raises(ValueError):
        GATE.score(data, lambda grid: grid, rotate=False)


def test_reused_mutable_rival_output_does_not_erase_earlier_predictions():
    shared = [[0]]
    def reuse(grid):
        shared[0][0] = grid[0][0]
        return shared
    result = GATE.score(lesson(), reuse, rotate=False)
    assert result["production"]["ambiguous"] is True


def test_cli_executes_the_exact_hashed_source_despite_stale_bytecode(tmp_path):
    import hashlib
    import json
    import os
    import py_compile
    plugin = tmp_path / "rival.py"
    plugin.write_text("def predict(grid): return [[1]]\n")
    stat = plugin.stat()
    py_compile.compile(str(plugin), doraise=True)
    plugin.write_text("def predict(grid): return [[2]]\n")
    os.utime(plugin, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    data = tmp_path / "lesson.json"
    data.write_text(json.dumps(lesson()))
    output = tmp_path / "report.json"
    code = GATE.main([str(data), "--rival", str(plugin), "--out", str(output)])
    report = json.loads(output.read_text())
    assert code == 0, "new source refutes the demonstration; stale bytecode falsely flags ambiguity"
    assert report["rival_sha256"] == hashlib.sha256(plugin.read_bytes()).hexdigest()
