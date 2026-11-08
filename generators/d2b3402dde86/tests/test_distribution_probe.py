"""Exercise the reusable authoring probe through its real CLI."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "d2b3402dde86"


def selected_path():
    root = find_root(__file__)
    for relative in (f"generators/{TASK_ID}", f"puzzle_generators/per_puzzle/{TASK_ID}"):
        home = root / relative
        if (home / "generator.py").is_file():
            return root, home
    raise AssertionError("selected task generator not found")


def run_probe(*args):
    root, home = selected_path()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in
        (root / "src", root / "shared/runtime", root))
    return subprocess.run([sys.executable, str(home / "workspace/probe_distribution.py"),
                           *map(str, args)], cwd=root, env=env, text=True,
                          capture_output=True, timeout=60)


def test_real_cli_counts_dynamic_declarations_and_label_basis(tmp_path):
    output = tmp_path / "probe.json"
    result = run_probe("--samples-per-band", 8, "--window-starts", 4,
                       "--seed", 17, "--out", output)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text())
    assert report["label_basis"] == "python_rule_mirror_diagnostic_only"
    assert report["status"] == "PASS"
    assert report["failures"] == []
    assert report["canonical"]["all_pair_count"] == 3
    assert report["canonical"]["train_demo_count"] == 2
    root, home = selected_path()
    spec = importlib.util.spec_from_file_location("probe_test_selected", home / "generator.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    assert report["declarations"]["canonical_shortcuts"] == sorted(generator.CANONICAL_SHORTCUTS)
    assert report["declarations"]["lesson_competitors"] == sorted(generator.LESSON_COMPETITORS)
    assert report["source"]["generator_sha256"]
    assert report["source"]["canonical_sha256"]
    assert report["source"]["rule_hash"] == generator.RULE_HASH
    for band in ("easy", "medium", "hard"):
        sample = report["bands"][band]
        assert sample["draw_count"] == sample["accepted_count"] == 8
        assert 0 < sample["unique_accepted_inputs"] <= 8
        assert sum(sample["input_shapes"].values()) == 8
        assert sum(sample["output_shapes"].values()) == 8
        assert sum(sample["observable_extents"].values()) == 8
        assert 0 <= sample["strict_fraction"] <= 1
        windows = report["windows"][band]
        assert windows["starts"] == list(range(4))
        assert windows["window_count"] == 4
        assert windows["holdout_count"] == 16
        assert {item["query_position"] for item in windows["holdouts"]} == {0, 1, 2, 3}
        assert windows["ambiguity_count"] == 0
        assert all(set(item["differing_query_rivals"]) <= set(item["surviving_rivals"])
                   for item in windows["holdouts"])


@pytest.mark.parametrize("flag,value", [("--samples-per-band", "0"),
                                       ("--window-starts", "-1"),
                                       ("--samples-per-band", "999999")])
def test_invalid_counts_fail_before_writing(tmp_path, flag, value):
    output = tmp_path / "invalid.json"
    result = run_probe(flag, value, "--out", output)
    assert result.returncode == 2
    assert "must be between" in result.stderr
    assert not output.exists()


def test_existing_output_is_preserved(tmp_path):
    output = tmp_path / "existing.json"
    output.write_text("keep me\n")
    result = run_probe("--samples-per-band", 1, "--window-starts", 1,
                       "--out", output)
    assert result.returncode == 2
    assert "already exists" in result.stderr
    assert output.read_text() == "keep me\n"


def test_rejected_inputs_emit_a_failure_report_and_nonzero_exit(tmp_path):
    # A disposable authoring tree simulates a later generator regression.
    # The real selected source is never changed.
    root, home = selected_path()
    fake_home = tmp_path / "generators" / TASK_ID
    (fake_home / "workspace").mkdir(parents=True)
    ledger = tmp_path / "data/canonical/puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(canonical_path(root).read_bytes())
    (fake_home / "generator.py").write_text((home / "generator.py").read_text() +
        '\n\ndef self_check(grid, **kwargs):\n    return ["injected rejection"]\n')
    tool = fake_home / "workspace/probe_distribution.py"
    tool.write_bytes((home / "workspace/probe_distribution.py").read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env["PYTHONPATH"] = os.pathsep.join(map(str, (root / "src", root / "shared/runtime", root)))
    output = tmp_path / "failed.json"
    result = subprocess.run([sys.executable, str(tool), "--samples-per-band", "1",
                             "--window-starts", "1", "--out", str(output)],
                            env=env, text=True, capture_output=True, timeout=60)
    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads(output.read_text())
    assert report["status"] == "FAIL"
    assert report["failure_count"] > 0
    assert any("injected rejection" in failure for failure in report["failures"])
    for band in ("easy", "medium", "hard"):
        assert report["bands"][band]["accepted_count"] == 0
        assert report["windows"][band]["error_holdout_count"] == 4
