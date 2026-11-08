"""Focused tests for the isolated extension-mode rule prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import sys

import pytest


TASK = "2d2b102b7740"
MODULE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    if not MODULE_PATH.exists():
        pytest.fail("parametric prototype.py has not been implemented")
    spec = importlib.util.spec_from_file_location("parametric_2d2b102b7740", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sample_grid() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(10)]
    for row, col in ((4, 3), (5, 5), (6, 7)):
        grid[row][col] = 1
    return grid


def test_parameter_choice_is_episode_deterministic_and_covers_both_modes():
    proto = load_prototype()
    assert proto.choose_parameters(17) == proto.choose_parameters(17)
    observed = {proto.choose_parameters(seed)[proto.PARAMETER_NAME] for seed in range(64)}
    assert observed == set(proto.ALLOWED_EXTENSION_MODES)


def test_default_forward_setting_matches_canonical_and_both_adds_backward_cells():
    proto = load_prototype()
    grid = sample_grid()
    forward = proto.python_reference(grid, extension_mode="forward")
    both = proto.python_reference(grid, extension_mode="both")

    assert forward[7][9] == forward[8][11] == 2
    assert forward[3][1] == 0
    assert both[7][9] == both[8][11] == 2
    assert both[3][1] == 2
    assert all(
        both[row][col] == forward[row][col]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) != (3, 1)
    )


def test_episode_inputs_are_lawful_and_distinguish_the_two_settings():
    proto = load_prototype()
    inputs = proto.episode_inputs(23)
    assert len(inputs) == 4
    assert len({tuple(map(tuple, grid)) for grid in inputs}) == 4
    for grid in inputs:
        assert proto.input_errors(grid) == []
        assert proto.python_reference(grid, extension_mode="forward") != proto.python_reference(
            grid, extension_mode="both"
        )


def test_default_racket_program_is_bound_to_the_canonical_rule_hash():
    proto = load_prototype()
    source = proto.racket_program({proto.PARAMETER_NAME: proto.DEFAULT_EXTENSION_MODE})
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert digest == "8db0d36e6e45"
    assert source.lstrip().startswith("(rule! (lambda (g)")


def test_public_challenge_omits_hidden_setting_source_seed_and_query_answer():
    proto = load_prototype()
    grid = sample_grid()
    output = proto.python_reference(grid, extension_mode="both")
    episode = {
        "seed": 7,
        "parameters": {proto.PARAMETER_NAME: "both"},
        "racket_program": proto.racket_program({proto.PARAMETER_NAME: "both"}),
        "demos": [{"input": grid, "output": output}],
        "query": {"input": grid, "output": output},
    }
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"schema", "task_id", "demos", "query"}
    assert challenge["query"] == {"input": grid}
    serialized = repr(challenge).lower()
    for forbidden in ("extension_mode", "racket", "seed", "'output':"):
        if forbidden == "'output':":
            assert forbidden in repr(challenge["demos"])  # demonstration labels stay public
            assert forbidden not in repr(challenge["query"])
        else:
            assert forbidden not in serialized


def test_builder_executes_both_racket_rules_and_writes_redacted_public_episodes(tmp_path):
    script = MODULE_PATH.with_name("build_prototype.py")
    if not script.exists():
        pytest.fail("parametric build_prototype.py has not been implemented")
    out = tmp_path / "evidence"
    completed = subprocess.run(
        [sys.executable, str(script), "--out-dir", str(out)],
        cwd=script.parent,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    summary = json.loads((out / "summary.json").read_text())
    assert summary["passed"] is True
    assert summary["settings_covered"] == ["both", "forward"]
    assert summary["canonical_default_rule_hash"] == "8db0d36e6e45"
    for item in summary["episodes"]:
        public = json.loads((out / "public" / item["public_challenge"]).read_text())
        assert "output" not in public["query"]
        assert "parameters" not in public and "racket_program" not in public
