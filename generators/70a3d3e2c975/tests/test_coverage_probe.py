"""Regression tests for the task-local coverage probe's concrete blind spots."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest


SPEC = importlib.util.spec_from_file_location(
    "task_coverage_probe", Path(__file__).resolve().parents[1] / "workspace" / "coverage_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_topology_does_not_split_touching_unlike_colors():
    grid = [[0, 0, 0, 9, 0, 0, 0] for _ in range(5)]
    grid[0][0] = grid[1][0] = 2
    grid[1][1] = 3
    grid[4][0] = 7
    result = PROBE.topology(grid)
    assert result["signature"] == [2, 1, 1, 3]
    assert result["scaffold_errors"] == []


def test_actual_new_declarations_and_colliding_names_keep_their_namespaces():
    identity = lambda grid: grid
    fresh = SimpleNamespace(SEMANTIC_RIVALS={"new_rival": identity},
                            LESSON_COMPETITORS={"new_rival": identity},
                            CANONICAL_SHORTCUTS={"another_new_rival": identity})
    rules, declarations, errors = PROBE.declared_rules(fresh)
    assert not errors
    assert len(rules) == 3
    assert "SEMANTIC_RIVALS/new_rival" in rules
    assert "LESSON_COMPETITORS/new_rival" in rules
    assert declarations["CANONICAL_SHORTCUTS"]["names"] == ["another_new_rival"]


def test_all_cyclic_query_roles_are_checked_and_denominators_remain_distinct():
    name = "LESSON_COMPETITORS/last_input_counterexample"
    samples = [{"index": i, "seed": 0, "band": "easy",
                "rules": {name: {"matches_output": i != 3, "error": None}}} for i in range(4)]
    windows = PROBE.cyclic_windows(samples, 4, [name])
    assert len(windows) == 4
    assert sorted(w["query"] for w in windows) == list(range(4))
    assert sum(name in w["query_discriminates"] for w in windows) == 1
    assert sum(name in w["refuted"] for w in windows) == 3
    assert sum(len(w["demos"]) + 1 for w in windows) == 16


def test_mutating_or_malformed_rivals_do_not_corrupt_inputs_or_count_as_refuted():
    original = [[1]]

    def mutate(grid):
        grid[0][0] = 2
        return grid

    assert PROBE.rule_agreement(mutate, original, [[2]])["matches_output"] is True
    assert original == [[1]]
    invalid = PROBE.rule_agreement(lambda grid: [[True]], original, [[1]])
    assert invalid["matches_output"] is None
    assert invalid["error"]


def test_relocated_runtime_replays_source_bound_final_census(tmp_path):
    """Exercise real relocation when final evidence and Racket are available.

    ARCPUZZLES_TASK_COVERAGE_REFERENCE selects the source-bound census directory.
    Set ARCPUZZLES_TASK_COVERAGE_REPLAY_OUT to a new checks directory to retain
    the small replay, its actual process receipt, and the source/hash comparison.
    """
    reference_dir = Path(os.environ.get("ARCPUZZLES_TASK_COVERAGE_REFERENCE",
                        str(PROBE.ROOT.parent / "checks" / "coverage_after"))).resolve()
    if not (reference_dir / "report.json").is_file() or not shutil.which("racket"):
        pytest.skip("requires final coverage_after evidence and Racket on PATH")
    reference = json.loads((reference_dir / "report.json").read_text())
    assert reference["status"] == "pass"
    generator = PROBE.ROOT / "generators" / PROBE.TASK_ID / "generator.py"
    assert PROBE.file_digest(generator) == reference["source"]["generator_sha256"]
    sys.path.insert(0, str(PROBE.ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime

    staging = tmp_path / "staging"
    prepare_runtime(Catalog(PROBE.ROOT), staging, PROBE.TASK_ID)
    relocated = tmp_path / "unrelated" / "runtime"
    relocated.parent.mkdir()
    staging.rename(relocated)
    copied_probe = tmp_path / "isolated_repo" / "generators" / PROBE.TASK_ID / "workspace" / "coverage_probe.py"
    copied_probe.parent.mkdir(parents=True)
    shutil.copy2(SPEC.origin, copied_probe)
    foreign_cwd = tmp_path / "foreign_cwd"
    foreign_cwd.mkdir()
    output = Path(os.environ.get("ARCPUZZLES_TASK_COVERAGE_REPLAY_OUT", str(tmp_path / "replay"))).resolve()
    command = [sys.executable, str(copied_probe), "--runtime", str(relocated),
               "--seed-count", "1", "--bands", "medium", "--output", str(output)]
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "ARCPUZZLES_HOME"):
        environment.pop(key, None)
    run = subprocess.run(command, cwd=foreign_cwd, env=environment,
                         capture_output=True, text=True, timeout=90)
    output.mkdir(parents=True, exist_ok=True)
    PROBE.json_file(output / "execution.json", {"argv": command, "cwd": str(foreign_cwd),
                    "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                    "removed_environment": ["PYTHONPATH", "PYTHONHOME", "ARCPUZZLES_HOME"]})
    assert run.returncode == 0, run.stdout + run.stderr
    replay = json.loads((output / "report.json").read_text())
    assert replay["source"] == reference["source"]
    load_samples = lambda folder: [json.loads(line) for line in (folder / "samples.jsonl").read_text().splitlines()]
    expected = {s["sample_index"]: (s["input_sha256"], s["output_sha256"])
                for s in load_samples(reference_dir) if s["seed"] == 0 and s["band"] == "medium"}
    observed = {s["sample_index"]: (s["input_sha256"], s["output_sha256"]) for s in load_samples(output)}
    assert len(expected) == 4 and observed == expected
    for folder, report in ((reference_dir, reference), (output, replay)):
        for name, sha256 in report["artifacts"].items():
            assert PROBE.file_digest(folder / name) == sha256
        for sample in load_samples(folder):
            assert PROBE.digest(sample["input"]) == sample["input_sha256"]
            assert PROBE.digest(sample["output"]) == sample["output_sha256"]
    PROBE.json_file(output / "replay_binding.json", {
        "reference_report": str(reference_dir / "report.json"),
        "reference_report_sha256": PROBE.file_digest(reference_dir / "report.json"),
        "source_hashes_equal": True, "replay_hashes_equal": True,
        "artifact_hashes_verified": True, "input_output_hashes_verified": True,
        "replayed_band": "medium", "replayed_seed": 0, "replayed_sample_count": len(observed)})
