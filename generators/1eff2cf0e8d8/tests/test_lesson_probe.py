"""Focused tests for the reusable large-lesson evidence probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load(HOME / "generator.py", "probe_test_generator")


def test_probe_helpers_are_source_bound_and_score_declared_competitors():
    probe = _load(HOME / "workspace" / "lesson_probe.py", "lesson_probe_under_test")
    assert probe.derive_seed("easy", 0) == probe.derive_seed("easy", 0)
    assert probe.derive_seed("easy", 0) != probe.derive_seed("hard", 0)
    assert len(probe.source_sha256(HOME / "generator.py")) == 64

    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(8100, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(8100, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}

    result = probe.score_lesson(gen, demos, query)
    assert result["identifiability_reasons"] == []
    assert result["survived_demos"] == []
    assert set(result["competitor_demo_disagreements"]) == set(gen.LESSON_COMPETITORS)
    assert all(count >= 1 for count in result["competitor_demo_disagreements"].values())


def test_probe_loads_generator_with_clean_pythonpath(tmp_path):
    import os
    import subprocess

    script = HOME / "workspace" / "lesson_probe.py"
    code = f"""
import importlib.util
from pathlib import Path
path = Path({str(script)!r})
spec = importlib.util.spec_from_file_location('standalone_probe', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
loaded = module._load_generator()
assert loaded.TASK_ID == '1eff2cf0e8d8'
print(module.REPO)
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = ""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(REPO)


def test_probe_builds_selected_canonical_bundle_without_installed_generator_copy():
    probe = _load(HOME / "workspace" / "lesson_probe.py", "bundle_probe_under_test")
    loaded = probe._load_generator()
    bundle = probe._selected_bundle(loaded)
    assert bundle.generator_module is loaded
    assert bundle.task_id == "1eff2cf0e8d8"
    assert bundle.rule_task_id == "1eff2cf0e8d8"
    assert bundle.rule_file == "shared/data/canonical/puzzles.jsonl"
    assert probe.normalized_rule_hash(bundle.rule_source) == loaded.RULE_HASH
