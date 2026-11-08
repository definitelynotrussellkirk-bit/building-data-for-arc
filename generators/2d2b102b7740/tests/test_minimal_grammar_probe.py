"""Literal shape contracts and real public-API execution for the opt-in probe."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys

import pytest


TOOL = Path(__file__).resolve().parent.parent / "workspace/probe_minimal_grammar.py"
SPEC = importlib.util.spec_from_file_location("minimal_grammar_probe_tested", TOOL)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)
TASK = "2d2b102b7740"


def test_shapes_have_literal_palette_coordinates_and_independent_rows():
    grid = [[7, 7, 7, 7, 7, 7], [7, 7, 4, 4, 7, 7], [7, 7, 7, 7, 7, 7],
            [7, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7]]
    original = deepcopy(grid)
    palette, pairs = PROBE.minimal_fixtures(grid)
    fixtures = dict(pairs)
    assert (palette["background"], palette["foreground"]) == (7, 4)
    assert list(fixtures) == ["all_background", "full_one_color", "singleton", "solid_2x2", "short_line"]
    expected_cells = {
        "all_background": set(), "full_one_color": {(r, c) for r in range(5) for c in range(6)},
        "singleton": {(2, 3)}, "solid_2x2": {(0, 0), (0, 1), (1, 0), (1, 1)},
        "short_line": {(2, 0), (2, 1), (2, 2), (2, 3)},
    }
    for name, fixture in fixtures.items():
        assert len(fixture) == 5 and all(len(row) == 6 for row in fixture)
        assert {(r, c) for r, row in enumerate(fixture) for c, color in enumerate(row) if color == 4} == expected_cells[name]
        assert {v for row in fixture for v in row} <= {4, 7}
    fixtures["short_line"][0][0] = 9
    assert fixtures["short_line"][1][0] == 7
    assert fixtures["all_background"][0][0] == 7
    assert grid == original


def test_ties_and_small_dimensions_are_explicit():
    palette, pairs = PROBE.minimal_fixtures([[8, 2]])
    assert palette["background"] == 8  # First occurrence wins the frequency tie.
    assert dict(pairs) == {"all_background": [[8, 8]], "full_one_color": [[2, 2]],
                           "singleton": [[8, 2]], "solid_2x2": [[2, 2]], "short_line": [[2, 2]]}


@pytest.mark.parametrize("grid", ([[0, 0]], [[0], [0, 1]], [[0, True]], [[0] * 31, [1] * 31]))
def test_malformed_or_uniform_inputs_fail_instead_of_inventing_a_palette(grid):
    with pytest.raises(ValueError):
        PROBE.minimal_fixtures(grid)


def test_validator_executes_hashed_source_even_when_stale_bytecode_looks_current(tmp_path):
    source = tmp_path / "generator.py"
    before = b"def self_check(grid):\n    return ['old']\n"
    after = b"def self_check(grid):\n    return ['new']\n"
    assert len(before) == len(after)
    source.write_bytes(before)
    os.utime(source, (1700000000, 1700000000))
    py_compile.compile(str(source), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    source.write_bytes(after)
    os.utime(source, (1700000000, 1700000000))
    module, source_hash = PROBE.load_generator(source, "stale_bytecode_regression")
    assert source_hash == hashlib.sha256(after).hexdigest()
    assert module.self_check([[0]]) == ["new"]


def run_cli(tmp_path, name, *, timeout="60"):
    if not (os.environ.get("RACKET_PATH") or shutil.which("racket")):
        pytest.skip("Run through the packet's Racket wrapper for real reference execution")
    grid = [[0] * 8 for _ in range(6)]
    grid[3] = [1, 1, 1, 1, 0, 0, 0, 0]
    source = tmp_path / f"{name}-input.json"
    source.write_text(json.dumps(grid), encoding="utf-8")
    output = tmp_path / f"{name}-report.json"
    command = [sys.executable, str(TOOL), "--task", TASK, "--input", str(source),
               "--out", str(output), "--timeout", timeout]
    # An unrelated working directory exercises the tool's local-root discovery.
    completed = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert output.is_file(), (completed.stdout, completed.stderr)
    return completed, json.loads(output.read_text()), command, output


def test_cli_real_racket_preserves_the_lawful_line_and_does_not_auto_exempt(tmp_path):
    completed, report, command, output = run_cli(tmp_path, "line")
    assert completed.returncode == 0, completed.stderr
    assert report["status"] == "recorded"
    assert report["semantic_verdict"] == "not_assessed"
    assert report["changes_lint_or_approval"] is False
    assert report["source_bindings_match"] is True
    assert report["sources"]["executed_rule_hash"] == "8db0d36e6e45"
    assert report["sources"]["tool_sha256"] == hashlib.sha256(TOOL.read_bytes()).hexdigest()
    cases = {case["name"]: case for case in report["cases"]}
    line = cases["short_line"]
    assert line["validator"]["status"] == "accepted"
    assert line["racket"]["status"] == "completed"
    expected = [[0] * 8 for _ in range(6)]
    expected[3] = [1, 1, 1, 1, 2, 2, 2, 2]
    assert line["racket"]["output"] == expected
    assert line["racket"]["output_sha256"] == PROBE.grid_sha256(expected)
    # The rule can also execute a rejected malformed shape. Execution alone
    # therefore cannot serve as the tool's semantic-validity decision.
    assert cases["solid_2x2"]["validator"]["status"] == "rejected"
    assert cases["solid_2x2"]["racket"]["status"] == "completed"
    retained = output.read_bytes()
    repeated = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert repeated.returncode == 2
    assert "already exists" in repeated.stderr
    assert output.read_bytes() == retained


def test_cli_real_worker_timeout_retains_failure_without_inventing_outputs(tmp_path):
    completed, report, _, _ = run_cli(tmp_path, "timeout", timeout="0.000001")
    assert completed.returncode == 2
    assert report["status"] == "reference_failed"
    assert report["reference_execution"]["status"] == "failed"
    assert report["reference_execution"]["run"]["timed_out"] is True
    assert all(case["racket"]["status"] == "not_observed" for case in report["cases"])
    assert all(case["racket"]["output"] is None for case in report["cases"])
    assert "executed_rule_hash" not in report["sources"]
