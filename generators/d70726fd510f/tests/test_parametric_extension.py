"""Prototype-only contracts for proposed occupancy-rule variants.

These tests use the real included Racket bridge. They do not modify or approve
canonical production behavior.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

for _ancestor in Path(__file__).resolve().parents:
    _helper = _ancestor / "shared/runtime"
    if (_helper / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_helper))
        break
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK = "d70726fd510f"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators" / TASK / "workspace/parametric/prototype.py"
# One row, four aligned states in order 00, 01, 10, 11.
WITNESS = [[0, 0, 9, 9, 4, 0, 7, 0, 7]]


def load_prototype():
    assert PROTOTYPE.is_file(), "the runnable parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("d707_parametric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def racket():
    with RacketBridge() as bridge:
        yield bridge


@pytest.mark.parametrize(
    "operation,bits",
    [("xor", (0, 1, 1, 0)), ("and", (0, 0, 0, 1)), ("or", (0, 1, 1, 1))],
)
@pytest.mark.parametrize("color", range(1, 10))
def test_each_declared_rule_executes_full_truth_table(racket, operation, bits, color):
    prototype = load_prototype()
    parameters = prototype.Parameters(operation, color)
    program = prototype.emit_program(parameters)
    actual = prototype.execute_program(program, [WITNESS], bridge=racket)
    assert actual == [[[color if bit else 0 for bit in bits]]]


@pytest.mark.parametrize(
    "operation,color",
    [
        ("nand", 2),
        ("XOR", 2),
        (False, 2),
        ("xor", 0),
        ("xor", 10),
        ("xor", True),
        ("xor", 2.0),
        ("xor", "2"),
    ],
)
def test_parameter_bounds_reject_unsupported_rules(prototype, operation, color):
    with pytest.raises(ValueError):
        prototype.Parameters(operation, color)


def test_canonical_default_matches_all_labeled_canonical_pairs(prototype, racket):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    actual = prototype.execute_program(
        prototype.emit_program(prototype.DEFAULT),
        [pair["input"] for pair in pairs],
        bridge=racket,
    )
    assert actual == [pair["output"] for pair in pairs]


from copy import deepcopy
import json


@pytest.fixture(scope="module")
def generator_bundle():
    """Load this task mirror without replacing a cached local runtime package."""
    source = ROOT / "generators" / TASK / "generator.py"
    assert source.is_file()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("d707_parametric_generator", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, source, digest


@pytest.fixture(scope="module")
def generator(generator_bundle):
    return generator_bundle[0]


def test_seed_coverage_contains_all_27_settings_and_is_reproducible(prototype):
    seeds = prototype.covering_seeds(0)
    expected = {
        (operation, color)
        for operation in ("xor", "and", "or")
        for color in range(1, 10)
    }
    assert len(seeds) == 27
    assert {
        (
            prototype.sample_parameters(seed).operation,
            prototype.sample_parameters(seed).output_color,
        )
        for seed in seeds
    } == expected
    assert seeds == prototype.covering_seeds(0)


@pytest.mark.parametrize("seed", [-1, True, 1.0, "1"])
def test_invalid_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.sample_parameters(seed)


def test_episode_uses_one_rule_for_demos_and_query(prototype, racket, generator_bundle, generator):
    episode = prototype.make_episode(42, bridge=racket, generator_bundle=generator_bundle)
    assert episode["parameters"] == prototype.sample_parameters(42).as_dict()
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
    assert prototype.execute_program(
        episode["program"], [pair["input"] for pair in pairs], bridge=racket
    ) == [pair["output"] for pair in pairs]
    assert episode["identifiability"]["survivors"] == [episode["parameters"]]
    assert episode["identifiability"]["unique"] is True
    assert len(episode["identifiability"]["rivals"]) == 27
    assert prototype.make_episode(42, bridge=racket, generator_bundle=generator_bundle) == episode


def test_public_challenge_contains_only_visible_demos_and_query_inputs(prototype, racket, generator_bundle):
    episode = prototype.make_episode(17, bridge=racket, generator_bundle=generator_bundle)
    original = deepcopy(episode)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = json.dumps(challenge)
    assert "parameters" not in serialized and "seed" not in serialized and "program" not in serialized
    challenge["train"][0]["input"][0][0] = 99
    assert episode == original


def test_demo_only_checker_retains_ambiguity_honestly(prototype, racket):
    # Only state 11 appears, so AND and OR with the same color are indistinguishable.
    report = prototype.check_identifiability(
        [{"input": [[9, 9, 4, 7, 7]], "output": [[3, 3]]}], bridge=racket
    )
    assert report["unique"] is False
    assert report["survivors"] == [
        {"operation": "and", "output_color": 3},
        {"operation": "or", "output_color": 3},
    ]


def test_lawful_witness_separates_all_settings(prototype, racket, generator):
    witness = prototype.distinct_witness(bridge=racket, generator=generator)
    assert generator.self_check(witness["input"]) == []
    assert witness["state_order"] == ["00", "01", "10", "11"]
    assert len(witness["outputs"]) == 27
    assert len({json.dumps(row["output"]) for row in witness["outputs"]}) == 27
    assert witness["all_settings_distinct"] is True


def test_episode_selects_rule_once_when_it_owns_bridge(prototype, monkeypatch, generator_bundle):
    selected = []
    original = prototype.sample_parameters

    def observed(seed):
        selected.append(seed)
        return original(seed)

    monkeypatch.setattr(prototype, "sample_parameters", observed)
    prototype.make_episode(17, generator_bundle=generator_bundle)
    assert selected == [17]


import subprocess


def test_canonical_parity_report_is_source_bound(prototype, racket):
    report = prototype.canonical_parity(bridge=racket)
    assert report["parameters"] == prototype.DEFAULT.as_dict()
    assert report["pairs_checked"] == 5
    assert report["passed"] is True
    assert all(pair["passed"] for pair in report["pairs"])


def test_cli_materializes_private_and_clean_public_episode(prototype, tmp_path):
    out = tmp_path / "episode"
    command = [sys.executable, str(PROTOTYPE), "episode", "--seed", "17", "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
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


def test_cli_audit_materializes_all_settings_with_aligned_rows(prototype, tmp_path):
    out = tmp_path / "audit"
    command = [sys.executable, str(PROTOTYPE), "audit", "--seed-start", "0", "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((out / "report.json").read_text())
    private = [json.loads(line) for line in (out / "episodes.private.jsonl").read_text().splitlines()]
    public = [json.loads(line) for line in (out / "challenges.public.jsonl").read_text().splitlines()]
    programs = json.loads((out / "programs.json").read_text())
    assert report["passed"] is True
    assert report["settings_requested"] == report["episodes_completed"] == 27
    assert len(private) == len(public) == len(programs) == 27
    assert all(public[i] == prototype.public_challenge(private[i]) for i in range(27))
    assert [row["line_index"] for row in report["episodes"]] == list(range(27))
    assert json.loads((out / "canonical-parity.json").read_text())["passed"] is True
    assert json.loads((out / "witness.json").read_text())["all_settings_distinct"] is True
    ambiguity = json.loads((out / "ambiguity.json").read_text())
    assert ambiguity["identifiability"]["survivors"] == [
        {"operation": "and", "output_color": 3},
        {"operation": "or", "output_color": 3},
    ]
