"""Prototype-only tests for hidden Boolean-combination rule variants.

These tests execute the real included Racket bridge. They do not approve the
prototype for production or alter the canonical AND authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "79353e95283d"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators" / TASK / "workspace/parametric/prototype.py"
WITNESS = [
    [0, 0, 1, 5, 0, 1, 0],  # 00, 01, 10
    [1, 0, 0, 5, 1, 0, 0],  # 11, 00, 00
]


def load_prototype():
    assert PROTOTYPE.is_file(), "the runnable parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("and_panel_parametric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def racket():
    with RacketBridge() as bridge:
        yield bridge


@pytest.mark.parametrize("operation,expected", [
    ("and", [[0, 0, 0], [2, 0, 0]]),
    ("or", [[0, 2, 2], [2, 0, 0]]),
    ("xor", [[0, 2, 2], [0, 0, 0]]),
])
def test_each_declared_operation_executes_full_truth_table(prototype, racket, operation, expected):
    parameters = prototype.Parameters(operation)
    program = prototype.emit_program(parameters)
    assert prototype.execute_program(program, [WITNESS], bridge=racket) == [expected]


@pytest.mark.parametrize("operation", ["nand", "AND", "", True, 3])
def test_parameter_bounds_reject_unsupported_operations(prototype, operation):
    with pytest.raises(ValueError):
        prototype.Parameters(operation)


def test_canonical_and_setting_matches_every_usable_canonical_label(prototype, racket):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    actual = prototype.execute_program(
        prototype.emit_program(prototype.DEFAULT),
        [pair["input"] for pair in pairs],
        bridge=racket,
    )
    assert actual == [pair["output"] for pair in pairs]


def test_seed_selection_covers_all_operations_and_is_reproducible(prototype):
    seeds = prototype.covering_seeds(0)
    assert len(seeds) == 3
    assert [prototype.sample_parameters(seed).operation for seed in seeds] == ["and", "or", "xor"]
    assert seeds == prototype.covering_seeds(0)
    assert prototype.sample_parameters(2**256) == prototype.sample_parameters(2**256)


@pytest.mark.parametrize("seed", [-1, True, 1.0, "1"])
def test_invalid_episode_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.sample_parameters(seed)


def test_episode_uses_one_seed_selected_rule_and_unique_demonstrations(prototype, racket):
    episode = prototype.make_episode(42, bridge=racket)
    assert episode["parameters"] == prototype.sample_parameters(42).as_dict()
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    generator = load_selected_generator(TASK, root=ROOT)[0]
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
    assert prototype.execute_program(
        episode["program"], [pair["input"] for pair in pairs], bridge=racket
    ) == [pair["output"] for pair in pairs]
    assert episode["identifiability"]["survivors"] == [episode["parameters"]]
    assert episode["identifiability"]["unique"] is True
    assert len(episode["identifiability"]["rivals"]) == 3
    assert prototype.make_episode(42, bridge=racket) == episode


def test_public_challenge_omits_hidden_rule_and_query_answers(prototype, racket):
    episode = prototype.make_episode(17, bridge=racket)
    original = deepcopy(episode)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    challenge["train"][0]["input"][0][0] = 99
    assert episode == original


def test_demo_only_checker_retains_and_or_ambiguity_honestly(prototype, racket):
    # A demonstration containing only state 11 cannot distinguish AND from OR.
    train = [{"input": [[1, 1, 1, 5, 1, 1, 1]], "output": [[2, 2, 2]]}]
    report = prototype.check_identifiability(train, bridge=racket)
    assert report["unique"] is False
    assert report["survivors"] == [
        {"operation": "and"},
        {"operation": "or"},
    ]


def test_lawful_four_state_witness_separates_all_settings(prototype, racket):
    witness = prototype.distinct_witness(bridge=racket)
    generator = load_selected_generator(TASK, root=ROOT)[0]
    assert generator.self_check(witness["input"]) == []
    assert len(witness["outputs"]) == 3
    assert len({json.dumps(row["output"]) for row in witness["outputs"]}) == 3
    assert witness["all_settings_distinct"] is True


def test_episode_cli_materializes_private_public_and_program_files(prototype, tmp_path):
    out = tmp_path / "episode"
    command = [sys.executable, str(PROTOTYPE), "episode", "--seed", "17", "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    private = json.loads((out / "episode.private.json").read_text())
    public = json.loads((out / "challenge.public.json").read_text())
    assert public == prototype.public_challenge(private)
    assert (out / "program.rkt").read_text() == private["program"]
    receipt = json.loads((out / "command.json").read_text())
    assert receipt["exit_code"] == 0 and receipt["cwd"] == str(ROOT)
    again = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert again.returncode != 0
    assert "already exists" in again.stderr


def test_audit_cli_materializes_all_three_settings_and_clean_public_rows(prototype, tmp_path):
    out = tmp_path / "audit"
    command = [sys.executable, str(PROTOTYPE), "audit", "--seed-start", "0", "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((out / "report.json").read_text())
    assert report["passed"] is True
    assert report["settings_requested"] == report["episodes_completed"] == 3
    assert report["canonical_pairs_checked"] >= 4
    private = [json.loads(line) for line in (out / "episodes.private.jsonl").read_text().splitlines()]
    public = [json.loads(line) for line in (out / "challenges.public.jsonl").read_text().splitlines()]
    assert len(private) == len(public) == 3
    assert public == [prototype.public_challenge(episode) for episode in private]
    assert all("parameters" not in challenge and all("output" not in pair for pair in challenge["test"])
               for challenge in public)
