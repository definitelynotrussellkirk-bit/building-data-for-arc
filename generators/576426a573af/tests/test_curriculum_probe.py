"""Regression for the task-local cyclic curriculum auditor."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PROBE = HOME / "workspace/curriculum_probe.py"
spec = importlib.util.spec_from_file_location("probe_576426a573af", PROBE)
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)


def test_probe_certifies_every_requested_cyclic_window():
    report = probe.audit(seed=17, starts=range(8), bands=("easy", "medium"))
    assert report["windows"] == 16
    assert report["failures"] == []
    # Authentic canonical anchors may repeat across difficulty bands. Each
    # individual lesson must still contain distinct inputs (checked below).
    assert 12 <= report["unique_inputs"] <= 24
    assert set(report["competitors"]) == set(probe.gen.LESSON_COMPETITORS)
    assert all(count == 16 for count in report["refuted_windows"].values())
    assert all(count == 16 for count in report["witness_windows"].values())
    assert report["rotations"] == 80
    assert report["rotation_failures"] == []
    assert all(count == 80 for count in report["rotation_refuted"].values())
    assert report["four_query_checks"] == 64
    assert 15 <= report["four_query_unique_inputs"] <= 30
    assert report["four_query_failures"] == []
    assert all(count == 64 for count in report["four_query_refuted"].values())
    assert report["measured_inputs"] == 30
    assert len(report["generator_sha256"]) == 64
    assert len(report["probe_sha256"]) == 64


@pytest.mark.parametrize("scenario", ["edit_after_import", "same_timestamp_cache"])
def test_probe_hash_identifies_executed_source_bytes(tmp_path, scenario):
    """A live file edit or stale bytecode must not mislabel executed source."""
    import reviewer_support

    runtime_source = Path(reviewer_support.__file__).resolve().parent
    runtime = tmp_path / "shared/runtime"
    runtime.mkdir(parents=True)
    shutil.copy2(runtime_source / "reviewer_support.py", runtime / "reviewer_support.py")
    shutil.copytree(runtime_source / "puzzle_generators", runtime / "puzzle_generators",
                    ignore=shutil.ignore_patterns("__pycache__"))
    canonical = tmp_path / "shared/data/canonical/puzzles.jsonl"
    canonical.parent.mkdir(parents=True)
    canonical.write_text('{"task_id":"576426a573af","train":[]}\n')
    selected = tmp_path / "generators/576426a573af"
    (selected / "workspace").mkdir(parents=True)
    shutil.copy2(HOME / "generator.py", selected / "generator.py")
    shutil.copy2(PROBE, selected / "workspace/curriculum_probe.py")
    script = r'''
from pathlib import Path
import hashlib, importlib.util, os, py_compile, re, sys
home = Path(sys.argv[1])
scenario = sys.argv[2]
source = home / "generator.py"
body = source.read_bytes()
original_hash = hashlib.sha256(body).hexdigest()
original_version = re.search(rb'VERSION = "([^"]+)"', body).group(1).decode()
if scenario == "same_timestamp_cache":
    stamp = source.stat()
    py_compile.compile(str(source), doraise=True)
    replacement = original_version[:-1] + ("9" if original_version[-1] != "9" else "8")
    source.write_bytes(body.replace(original_version.encode(), replacement.encode(), 1))
    os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    expected_version = replacement
else:
    expected_hash, expected_version = original_hash, original_version
spec = importlib.util.spec_from_file_location("isolated_probe", home / "workspace/curriculum_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
if scenario == "edit_after_import":
    source.write_bytes(body + b"\n# later source edit\n")
report = probe.audit(seed=17, starts=range(1), bands=("easy",))
assert report["generator_version"] == expected_version, report["generator_version"]
assert report["generator_sha256"] == expected_hash, (report["generator_sha256"], expected_hash)
'''
    result = subprocess.run([sys.executable, "-c", script, str(selected), scenario],
                            cwd=tmp_path, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_task_bootstraps_share_the_selected_runtime_layout(tmp_path):
    """Portable snapshots contain execution dependencies and repository mirrors."""
    import reviewer_support

    runtime_source = Path(reviewer_support.__file__).resolve().parent
    for runtime in (tmp_path, tmp_path / "shared/runtime"):
        runtime.mkdir(parents=True, exist_ok=True)
        shutil.copy2(runtime_source / "reviewer_support.py", runtime / "reviewer_support.py")
        shutil.copytree(runtime_source / "puzzle_generators", runtime / "puzzle_generators",
                        ignore=shutil.ignore_patterns("__pycache__"))
    canonical = tmp_path / "data/canonical/puzzles.jsonl"
    canonical.parent.mkdir(parents=True)
    canonical.write_text('{"task_id":"576426a573af","train":[]}\n')
    selected = tmp_path / "generators/576426a573af"
    (selected / "workspace").mkdir(parents=True)
    (selected / "tests").mkdir()
    shutil.copy2(HOME / "generator.py", selected / "generator.py")
    shutil.copy2(PROBE, selected / "workspace/curriculum_probe.py")
    test_names = ("test_conflict_multiplicity.py", "test_generator_576426a573af.py",
                  "test_morphology_support.py")
    for name in test_names:
        shutil.copy2(HOME / "tests" / name, selected / "tests" / name)
    execution_source = tmp_path / "puzzle_generators/per_puzzle/576426a573af/generator.py"
    execution_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOME / "generator.py", execution_source)
    (tmp_path / "RUNTIME_MANIFEST.json").write_text(json.dumps({"files": [{
        "library_path": "generators/576426a573af/generator.py",
        "runtime_path": "puzzle_generators/per_puzzle/576426a573af/generator.py",
    }]}))
    script = r'''
from pathlib import Path
import hashlib, importlib.util, sys
root = Path(sys.argv[1])
home = root / "generators/576426a573af"
for index, name in enumerate(sys.argv[2:]):
    spec = importlib.util.spec_from_file_location(f"isolated_test_{index}", home / "tests" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
spec = importlib.util.spec_from_file_location("isolated_probe", home / "workspace/curriculum_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
import puzzle_generators.base, reviewer_support
assert Path(puzzle_generators.base.__file__).resolve() == root / "puzzle_generators/base.py"
assert Path(reviewer_support.__file__).resolve() == root / "reviewer_support.py"
expected = root / "puzzle_generators/per_puzzle/576426a573af/generator.py"
assert probe.GENERATOR_SOURCE == expected
assert probe.GENERATOR_SHA256 == hashlib.sha256(expected.read_bytes()).hexdigest()
'''
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), *test_names],
                            cwd=tmp_path, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
