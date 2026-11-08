"""Smoke tests for the task-local replay helpers shipped with the repair."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HOME = Path(__file__).resolve().parents[1]
WORKSPACE = HOME / "workspace"
PROBE = WORKSPACE / "reference_probe.py"
QUALIFY = WORKSPACE / "qualify.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_probe_replays_canonical_labels_and_counterexample() -> None:
    assert PROBE.is_file(), "workspace/reference_probe.py is missing"
    probe = _load(PROBE, "prototype_dictionary_reference_probe")
    generator = probe.load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    pairs = probe.canonical_pairs()
    assert len(pairs) == 3
    assert all(probe.intended_output(pair["input"]) == pair["output"] for pair in pairs)
    witness = probe.witness_input()
    assert generator.self_check(witness) == []
    assert probe.intended_output(witness) != probe.deduplicate_query_output(witness)


def test_qualify_cli_emits_a_machine_readable_pass_report() -> None:
    assert QUALIFY.is_file(), "workspace/qualify.py is missing"
    env = dict(os.environ)
    if "GENERATOR_UNDER_TEST" not in env:
        env["GENERATOR_UNDER_TEST"] = str(HOME / "generator.py")
    run = subprocess.run(
        [sys.executable, str(QUALIFY), "--json"],
        cwd=WORKSPACE,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(run.stdout)
    assert report["status"] == "pass"
    assert report["canonical_pairs"] == 3
    assert report["generated_draws"] >= 192
    assert report["shortcut_counterexamples"] == report["generated_draws"]
