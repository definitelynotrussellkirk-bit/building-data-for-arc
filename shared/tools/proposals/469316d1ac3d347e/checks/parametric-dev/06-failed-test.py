"""Prototype-only contracts: executed rules, episode teaching, and public output.

These tests deliberately use the real included Racket bridge. They do not
approve the parameterized rules for production or broaden canonical coverage.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
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

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK = "af0ae766e671"
ROOT = find_root(__file__)
# Public task_tests snapshots preserve this task home, including workspace/.
PROTOTYPE = ROOT / "generators" / TASK / "workspace/parametric/prototype.py"
WITNESS = [[0, 0, 9, 9], [0, 4, 0, 4]]


def load_prototype():
    # A missing artifact should fail a behavioral prerequisite, not collection.
    assert PROTOTYPE.is_file(), "the runnable parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("selected_parametric_prototype", PROTOTYPE)
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


@pytest.mark.parametrize("operation,bits", [
    ("xor", (0, 1, 1, 0)), ("and", (0, 0, 0, 1)), ("or", (0, 1, 1, 1)),
])
@pytest.mark.parametrize("color", range(1, 10))
def test_each_declared_rule_executes_its_full_truth_table(racket, operation, bits, color):
    # Changing an operation branch or using a fixed output color breaks this.
    prototype = load_prototype()
    parameters = prototype.Parameters(operation, color)
    source = prototype.emit_program(parameters)
    actual = prototype.execute_program(source, [WITNESS], bridge=racket)
    assert actual == [[[color if bit else 0 for bit in bits]]]


@pytest.mark.parametrize("operation,color", [
    ("nand", 6), ("XOR", 6), (False, 6), ("xor", 0), ("xor", 10),
    ("xor", True), ("xor", 6.0), ("xor", "6"),
])
def test_parameter_bounds_reject_unsupported_rules(prototype, operation, color):
    with pytest.raises(ValueError):
        prototype.Parameters(operation, color)


def test_canonical_setting_matches_every_usable_canonical_label(prototype, racket):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    actual = prototype.execute_program(prototype.emit_program(prototype.DEFAULT),
                                       [pair["input"] for pair in pairs], bridge=racket)
    assert actual == [pair["output"] for pair in pairs]


def test_seed_coverage_contains_all_27_settings_and_is_reproducible(prototype):
    seeds = prototype.covering_seeds(0)
    expected = {(operation, color) for operation in ("xor", "and", "or") for color in range(1, 10)}
    assert len(seeds) == 27
    assert {(prototype.sample_parameters(seed).operation,
             prototype.sample_parameters(seed).output_color) for seed in seeds} == expected
    assert seeds == prototype.covering_seeds(0)
    assert prototype.sample_parameters(2**256) == prototype.sample_parameters(2**256)


@pytest.mark.parametrize("seed", [-1, True, 1.0, "1"])
def test_invalid_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.sample_parameters(seed)


def test_episode_uses_one_rule_for_complete_demos_and_query(prototype, racket):
    episode = prototype.make_episode(42, bridge=racket)
    assert episode["parameters"] == prototype.sample_parameters(42).as_dict()
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    generator = load_selected_generator(TASK, root=ROOT)[0]
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
    assert prototype.execute_program(episode["program"], [pair["input"] for pair in pairs],
                                     bridge=racket) == [pair["output"] for pair in pairs]
    assert episode["identifiability"]["survivors"] == [episode["parameters"]]
    assert episode["identifiability"]["unique"] is True
    assert len(episode["identifiability"]["rivals"]) == 27
    assert prototype.make_episode(42, bridge=racket) == episode


def test_public_challenge_contains_only_demos_and_query_inputs(prototype, racket):
    episode = prototype.make_episode(17, bridge=racket)
    original = deepcopy(episode)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    challenge["train"][0]["input"][0][0] = 99
    assert episode == original


def test_demo_only_checker_retains_ambiguity_honestly(prototype, racket):
    # A demo with only both-occupied cells cannot distinguish AND from OR.
    report = prototype.check_identifiability([
        {"input": [[9, 9, 9, 9], [4, 4, 4, 4]], "output": [[3, 3, 3, 3]]}
    ], bridge=racket)
    assert report["unique"] is False
    assert report["survivors"] == [
        {"operation": "and", "output_color": 3},
        {"operation": "or", "output_color": 3},
    ]


def test_lawful_witness_separates_all_settings(prototype, racket):
    witness = prototype.distinct_witness(bridge=racket)
    generator = load_selected_generator(TASK, root=ROOT)[0]
    assert generator.self_check(witness["input"]) == []
    assert len(witness["outputs"]) == 27
    assert len({json.dumps(row["output"]) for row in witness["outputs"]}) == 27


def test_cli_materializes_reviewable_private_and_clean_public_files(prototype, tmp_path):
    out = tmp_path / "episode"
    command = [sys.executable, str(PROTOTYPE), "episode", "--seed", "17", "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    private = json.loads((out / "episode.private.json").read_text())
    public = json.loads((out / "challenge.public.json").read_text())
    assert public == prototype.public_challenge(private)
    receipt = json.loads((out / "command.json").read_text())
    assert receipt["exit_code"] == 0 and receipt["cwd"] == str(ROOT)
    assert (out / "program.rkt").read_text() == private["program"]
    again = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert again.returncode != 0
    assert "already exists" in again.stderr


def test_episode_selects_rule_once_when_it_owns_the_bridge(prototype, monkeypatch):
    selected = []
    original = prototype.sample_parameters

    def observed_selection(seed):
        selected.append(seed)
        return original(seed)

    monkeypatch.setattr(prototype, "sample_parameters", observed_selection)
    prototype.make_episode(17)
    assert selected == [17]


def test_audit_failure_retains_correct_public_private_row_indices(prototype, racket, monkeypatch, tmp_path):
    # Only the first selected-input failure is injected; every surviving episode
    # and its labels still use the real implementation and protected Racket.
    original = prototype.make_episode
    seeds = prototype.covering_seeds(0)

    def first_failure(seed, **kwargs):
        if seed == seeds[0]:
            raise ValueError("intentional first-episode regression fixture")
        return original(seed, **kwargs)

    monkeypatch.setattr(prototype, "make_episode", first_failure)
    report = prototype._audit(tmp_path, 0, racket)
    assert report["passed"] is False
    assert report["failures"][0].get("line_index") is None
    private = [json.loads(line) for line in (tmp_path / "episodes.private.jsonl").read_text().splitlines()]
    public = [json.loads(line) for line in (tmp_path / "challenges.public.jsonl").read_text().splitlines()]
    assert len(private) == len(public) == 26
    for line_index, summary in enumerate(report["episodes"]):
        assert summary["line_index"] == line_index
        assert summary["attempt_index"] == line_index + 1
        assert private[line_index]["seed"] == summary["seed"]
        assert public[line_index] == prototype.public_challenge(private[line_index])
