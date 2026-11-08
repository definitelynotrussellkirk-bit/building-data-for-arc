"""Synthetic preparation failures; never open a packet's task or private data."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


REPO_SOURCE = Path(os.environ.get(
    "ARCPUZZLES_REVIEW_SOURCE", str(Path(__file__).resolve().parents[1] / "src")))
SOURCE = Path(os.environ.get(
    "PREPARE_TARGET_SOURCE", str(REPO_SOURCE / "arcpuzzles/review_solve.py")))
sys.path.insert(0, str(REPO_SOURCE))
spec = importlib.util.spec_from_file_location("arcpuzzles.prepare_diagnostics_proposal", SOURCE)
solve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve)
from arcpuzzles.runtime import GenerationFailure

SECRET = "SYNTHETIC_PRIVATE_RULE_AND_QUERY_LABELS"
ENVIRONMENT = {
    "python_executable": "/synthetic/venv/bin/python",
    "python_version": "3.12.1",
    "numpy_discoverable": True,
    "pillow_discoverable": True,
    "racket_discoverable": False,
}


@pytest.fixture
def packet(tmp_path, monkeypatch):
    # The preparation code reads only these synthetic placeholders. Catalog's
    # generation boundary is replaced before its constructor can read real data.
    source = tmp_path / "repo/generators/synthetic/generator.py"
    source.parent.mkdir(parents=True)
    source.write_text("EXAMPLES_NEEDED = 3\n")
    canonical = tmp_path / "repo/shared/data/canonical/puzzles.jsonl"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("synthetic authority placeholder\n")
    for kind, paths in solve.KINDS.items():
        contract = {
            "schema": solve.BLIND_SCHEMA if kind == "blind" else "synthetic-assignment",
            "assignment_id": "synthetic-assignment", "packet_id": "synthetic-packet",
            "task_id": "synthetic", "generator": {"generator": "generators/synthetic/generator.py"},
        }
        (tmp_path / paths["contract"]).write_text(json.dumps(contract))
    return tmp_path


def fail_generation(monkeypatch, error):
    class FailingCatalog:
        def __init__(self, root):
            pass

        def generate(self, *args, **kwargs):
            raise error

    monkeypatch.setattr(solve, "Catalog", FailingCatalog)


def probe_success(monkeypatch):
    def probe(command, cwd, **options):
        assert command[1:3] == ["-E", "-s"]
        assert options["timeout"] <= 10
        assert Path(cwd).is_dir()
        return {"exit_code": 0, "timed_out": False,
                "stdout": json.dumps(ENVIRONMENT), "stderr": ""}
    monkeypatch.setattr(solve, "run_process", probe)


@pytest.mark.parametrize("kind", ["post_repair", "blind"])
def test_blocked_cli_exposes_infrastructure_status_without_private_text(packet, monkeypatch, capsys, kind):
    run = {"exit_code": 1, "timed_out": False, "stdout": SECRET,
           "stderr": SECRET, "command": [SECRET]}
    fail_generation(monkeypatch, GenerationFailure("synthetic", run))
    probe_success(monkeypatch)
    argv = (["blind"] if kind == "blind" else []) + ["prepare"]
    assert solve.main(packet, argv) == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    visible = json.loads(captured.out)
    assert "preparation_diagnostics" in visible, "Blocked preparation loses actionable process/environment status"
    diagnostic = visible["preparation_diagnostics"]
    assert diagnostic["worker_exit_code"] == 1
    assert diagnostic["worker_timed_out"] is False
    assert diagnostic["environment_probe"] == "completed"
    assert all(diagnostic[key] == value for key, value in ENVIRONMENT.items())
    paths = solve.KINDS[kind]
    retained = json.loads((packet / paths["folder"] / "prepare-failures/0001.json").read_text())
    assert retained["preparation_diagnostics"] == diagnostic
    assert SECRET not in json.dumps(retained)
    # The old private evidence remains available to the maintainer, never to CLI.
    private = json.loads((packet / paths["private"] / "generation-error-0001.json").read_text())
    assert SECRET in private["error"]


@pytest.mark.parametrize("status", [
    {"exit_code": -15, "timed_out": True},
    {"exit_code": 130, "timed_out": False, "interrupted": True},
])
def test_worker_timeout_and_interruption_are_retained(packet, monkeypatch, status):
    fail_generation(monkeypatch, GenerationFailure("synthetic", {**status, "stdout": SECRET, "stderr": SECRET}))
    probe_success(monkeypatch)
    summary = solve.prepare_solve(packet)
    assert "preparation_diagnostics" in summary
    diagnostic = summary["preparation_diagnostics"]
    assert diagnostic["worker_exit_code"] == status["exit_code"]
    assert diagnostic["worker_timed_out"] == status["timed_out"]
    assert diagnostic["worker_interrupted"] == status.get("interrupted", False)
    assert SECRET not in json.dumps(diagnostic)


def test_failed_environment_probe_does_not_replace_original_failure(packet, monkeypatch, capsys):
    fail_generation(monkeypatch, ValueError(SECRET))
    def unavailable_probe(*args, **kwargs):
        raise OSError(SECRET)
    monkeypatch.setattr(solve, "run_process", unavailable_probe)
    assert solve.main(packet, ["prepare"]) == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    visible = json.loads(captured.out)
    assert visible["stopping_reason"] == "Episode generation blocked: ValueError"
    assert "preparation_diagnostics" in visible
    assert visible["preparation_diagnostics"]["environment_probe"] == "failed"
    assert "worker_exit_code" not in visible["preparation_diagnostics"]


def test_repeated_failure_preserves_numbered_receipts_and_same_seed(packet, monkeypatch):
    fail_generation(monkeypatch, GenerationFailure("synthetic", {
        "exit_code": 1, "timed_out": False, "stdout": "", "stderr": SECRET}))
    probe_success(monkeypatch)
    first = solve.prepare_solve(packet, "blind")
    second = solve.prepare_solve(packet, "blind")
    assert first["seed"] == second["seed"]
    assert "preparation_diagnostics" in first
    assert first["preparation_diagnostics"] == second["preparation_diagnostics"]
    failures = packet / "solve-blind/prepare-failures"
    assert sorted(path.name for path in failures.glob("*.json")) == ["0001.json", "0002.json"]


def test_public_diagnostics_drop_unrecognized_or_wrong_typed_fields(packet, monkeypatch, capsys):
    summary = {
        "status": "blocked", "stopping_reason": "Episode generation blocked: GenerationFailure",
        "preparation_diagnostics": {
            "worker_exit_code": {"private": SECRET},
            "worker_timed_out": False, "numpy_discoverable": SECRET,
            "environment_probe": "completed", "future_private_field": SECRET,
        },
    }
    monkeypatch.setattr(solve, "prepare_solve", lambda *a: summary)
    assert solve.main(packet, ["prepare"]) == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    assert json.loads(captured.out).get("preparation_diagnostics") == {
        "worker_timed_out": False, "environment_probe": "completed"}


def test_probe_does_not_echo_process_output_or_unknown_fields(packet, monkeypatch, capsys):
    fail_generation(monkeypatch, RuntimeError(SECRET))
    def probe(*args, **kwargs):
        return {"exit_code": 0, "timed_out": False, "stderr": SECRET,
                "stdout": json.dumps({**ENVIRONMENT, "unexpected": SECRET,
                                      "numpy_discoverable": {"secret": SECRET}})}
    monkeypatch.setattr(solve, "run_process", probe)
    assert solve.main(packet, ["prepare"]) == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err
    visible = json.loads(captured.out)
    assert "preparation_diagnostics" in visible
    assert "numpy_discoverable" not in visible["preparation_diagnostics"]
    assert visible["preparation_diagnostics"]["racket_discoverable"] is False


def test_real_probe_uses_isolated_interpreter_and_racket_selection(packet, monkeypatch):
    fail_generation(monkeypatch, RuntimeError(SECRET))
    monkeypatch.setenv("RACKET_PATH", str(packet / "absent-racket"))
    summary = solve.prepare_solve(packet)
    assert "preparation_diagnostics" in summary
    diagnostic = summary["preparation_diagnostics"]
    assert diagnostic["environment_probe"] == "completed"
    assert diagnostic["python_executable"] == sys.executable
    assert diagnostic["python_version"] == ".".join(map(str, sys.version_info[:3]))
    assert type(diagnostic["numpy_discoverable"]) is bool
    assert type(diagnostic["pillow_discoverable"]) is bool
    assert diagnostic["racket_discoverable"] is False
