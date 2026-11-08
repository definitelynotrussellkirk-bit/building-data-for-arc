"""The task-local probe must fail closed and retain demo-only certificates."""
from copy import deepcopy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/native_probe.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("marker_native_probe_tests", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def episode():
    return {"program_solution": "chosen", "train": [
        {"input": [[1]], "output": [[2]]},
        {"input": [[5]], "output": [[6]]}],
        "test": [{"input": [[3]], "output": [[4]]}]}


def test_demo_survivor_that_harms_query_is_rejected(probe, episode):
    calls = []
    def execute(program, grid):
        calls.append((program, grid[0][0]))
        return [[9 if program == "rival" and grid == [[3]] else grid[0][0] + 1]]
    with pytest.raises(ValueError, match="surviving rival"):
        probe.audit_episode(episode, execute, {"shortcut": "rival"})
    assert calls.index(("rival", 5)) < calls.index(("rival", 3))


def test_refuted_rival_is_fitted_to_all_demos_only(probe, episode):
    calls = []
    def execute(program, grid):
        calls.append((program, grid[0][0]))
        return [[grid[0][0] + 1 if program == "chosen" else 0]]
    report = probe.audit_episode(episode, execute, {"shortcut": "rival"})
    row = report["rivals"][0]
    assert row["demo_refutations"] == [0, 1]
    assert row["query_checks"] == []
    assert ("rival", 3) not in calls
    assert report["verified_label_count"] == 3


def test_rival_runtime_error_is_not_a_refutation(probe, episode):
    def execute(program, grid):
        if program == "broken":
            raise RuntimeError("protected Racket error")
        return [[grid[0][0] + 1]]
    with pytest.raises(RuntimeError, match="protected Racket error"):
        probe.audit_episode(episode, execute, {"shortcut": "broken"})


def test_python_label_claim_must_match_execution(probe, episode):
    changed = deepcopy(episode)
    changed["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="label mismatch"):
        probe.audit_episode(changed, lambda _program, grid: [[grid[0][0] + 1]], {})


def test_export_refuses_existing_destination_before_generation(probe, tmp_path, monkeypatch):
    def forbidden(*_args):
        pytest.fail("Existing destination must be rejected before generation")
    monkeypatch.setattr(probe, "build_probe", forbidden)
    with pytest.raises(FileExistsError):
        probe.export_probe(0, 3, 4, tmp_path)


def test_witness_moves_geometry_without_changing_row_major_colors(probe):
    grids = probe.witness_inputs()
    expected = {
        "near_to_far": [[2, 1, 8, 4, 6], [2, 6, 1, 8, 4]],
        "far_to_near": [[6, 4, 8, 2, 1], [4, 8, 2, 6, 1]],
    }
    for order, sequences in expected.items():
        for grid, sequence in zip(grids, sequences):
            value = probe.intermediate_value(grid, {"marker_order": order})
            assert value["row_major_colors"] == [2, 8, 4, 6, 1]
            assert value["ranked_colors"] == sequence


def test_witness_receipt_matches_exact_admission_runtime_schema(probe, tmp_path, monkeypatch):
    """Receipt plumbing only; mocked labels are never retained as real evidence."""
    prototype = probe._prototype()
    programs = {probe.raw(setting).decode().strip(): probe.digest(prototype.native_program(setting).encode())
                for setting in probe.SETTINGS}
    qualification = tmp_path / "test-only-qualification.json"
    qualification.write_text(json.dumps({"schema": "arcpuzzles-parametric-qualification-v1",
        "status": "qualified", "task_id": probe.TASK_ID, "source_binding": {"test_only": True},
        "programs": programs}))
    identity = {"backend": "racket", "protected": True, "binary_sha256": "a" * 64}
    counts = {"evaluations": 0}
    def execute(program, grid):
        counts["evaluations"] += 1
        if "(sorted cells)" in program:
            value = probe.intermediate_value(grid, probe.SETTINGS[0])
            colors, bg = value["row_major_colors"], value["background"]
            return [[colors[min(r, c, 10-r, 10-c)] if min(r, c, 10-r, 10-c) < len(colors) else bg
                     for c in range(11)] for r in range(11)]
        order = "near_to_far" if program == prototype.native_program(probe.SETTINGS[0]) else "far_to_near"
        return prototype.python_reference(grid, marker_order=order)
    @contextmanager
    def fake_runtime():
        yield {"execute": execute, "identity": identity, "counts": counts}
    monkeypatch.setattr(probe, "protected_racket", fake_runtime)
    monkeypatch.setattr(probe, "_check_source_binding", lambda _binding: None)
    witness = probe.write_witness(qualification, tmp_path / "test-only-witness.json")
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["racket_runtime_identity"] == identity
    assert witness["racket_evaluations"] == 8
    assert len(witness["cases"]) == 4
