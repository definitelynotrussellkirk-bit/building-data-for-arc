"""Focused tests of the unapproved, task-local parametric prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest


PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def test_requested_prototype_exists():
    assert PROTOTYPE.is_file(), "the requested parametric prototype is not implemented"


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE.is_file(), "the requested parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("parametric_806425ca81b3", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runtime(proto):
    with proto.reference_runtime() as running:
        yield running


def test_default_parameters_and_transformation_preserve_existing_colors(proto):
    grid = [[2, 0, 7, 0, 2, 0, 3, 0, 3, 0, 3]]
    original = copy.deepcopy(grid)
    assert proto.validate_parameters() == {"axis": "row", "min_anchors": 2}
    assert proto.mirror(grid) == [[2, 2, 7, 2, 2, 0, 3, 3, 3, 3, 3]]
    assert proto.mirror(grid, {"min_anchors": 3}) == [[2, 0, 7, 0, 2, 0, 3, 3, 3, 3, 3]]
    assert grid == original
    assert proto.mirror(list(map(list, zip(*grid))), {"axis": "column"}) == list(
        map(list, zip(*proto.mirror(grid)))
    )


@pytest.mark.parametrize("params", [
    [], "row", {"axes": "row"}, {"axis": "diagonal"}, {"axis": None},
    {"min_anchors": True}, {"min_anchors": 2.0}, {"min_anchors": "2"},
    {"min_anchors": 1}, {"min_anchors": 4}, {"min_anchors": None},
])
def test_malformed_parameters_are_rejected(proto, params):
    with pytest.raises(ValueError):
        proto.validate_parameters(params)
    with pytest.raises(ValueError):
        proto.materialize_rule(params)


@pytest.mark.parametrize("seed", [True, 1.5, "17", None])
def test_noninteger_seeds_are_rejected(proto, seed):
    with pytest.raises(ValueError):
        proto.sample_parameters(seed)
    with pytest.raises(ValueError):
        proto.make_inputs(seed)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 1]], [[True]], [[10]], [[1.0]], [["1"]]])
def test_malformed_grids_are_rejected_before_reference_execution(proto, grid):
    with pytest.raises(ValueError):
        proto.mirror(grid)


def test_parameter_sampling_and_inputs_are_deterministic_and_rng_pure(proto):
    random.seed(901)
    initial = random.getstate()
    settings = {tuple(proto.sample_parameters(seed).items()) for seed in range(64)}
    assert len(settings) == 4
    for params in proto.SETTINGS:
        first = proto.make_inputs(7103, params)
        assert first == proto.make_inputs(7103, params)
        assert first != proto.make_inputs(7104, params)
        assert len(first["train"]) == 3 and len(first["test"]) == 1
        for grid in first["train"] + first["test"]:
            assert proto.input_errors(grid, params) == []
        query = first["test"][0]
        assert len(query) == len(query[0]) == 30
        oriented = query if params["axis"] == "row" else list(map(list, zip(*query)))
        assert sum(any(line) for line in oriented) == 24
        changed = sum(a != b for row_a, row_b in zip(query, proto.mirror(query, params))
                      for a, b in zip(row_a, row_b))
        assert changed >= 100, "large queries must add semantic work, not just padding"
    assert random.getstate() == initial


def test_materialized_default_is_exact_canonical_text_and_matches_labels(proto, runtime):
    canonical = proto.canonical_record()
    assert proto.materialize_rule() == canonical["program_solution"]
    pairs = canonical["train"] + canonical["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert runtime.apply(proto.materialize_rule(), pair["input"]) == pair["output"]
        assert proto.mirror(pair["input"]) == pair["output"]


def test_lawful_counterfactual_distinguishes_all_four_exact_racket_rules(proto, runtime):
    grid = proto.counterfactual_input()
    outputs = []
    rules = set()
    for params in proto.SETTINGS:
        assert proto.input_errors(grid, params) == []
        rule = proto.materialize_rule(params)
        rules.add(rule)
        result = runtime.apply(rule, grid)
        assert result == proto.mirror(grid, params)
        assert result != grid
        outputs.append(result)
    assert len(rules) == 4
    assert len({repr(output) for output in outputs}) == 4


def test_complete_episodes_identify_every_parameter_rival_and_public_projection_is_private(proto, runtime):
    for params in proto.SETTINGS:
        episode = proto.generate_episode(20261023, params, runtime=runtime)
        assert episode["parameters"] == params
        assert episode["identifiability"]["uniquely_identified"] is True
        assert episode["identifiability"]["remaining_parameters"] == [params]
        assert episode["identifiability"]["ambiguous_queries"] == 0
        assert len(episode["identifiability"]["rivals"]) == 3
        assert all(row["status"] == "refuted_by_demonstrations"
                   for row in episode["identifiability"]["rivals"])
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == proto.mirror(pair["input"], params)
        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        public["train"][0]["input"][0][0] = 99
        assert episode["train"][0]["input"][0][0] != 99


def test_repeated_episode_execution_is_exactly_deterministic(proto, runtime):
    params = {"axis": "column", "min_anchors": 3}
    assert proto.generate_episode(9821, params, runtime=runtime) == proto.generate_episode(
        9821, params, runtime=runtime
    )


def test_overlap_precedence_matches_the_canonical_racket_on_general_grids(proto, runtime):
    grid = [[3, 0, 2, 0, 3, 0, 2, 3, 0, 2]]
    for params in proto.SETTINGS:
        oriented = grid if params["axis"] == "row" else list(map(list, zip(*grid)))
        assert proto.mirror(oriented, params) == runtime.apply(proto.materialize_rule(params), oriented)


def test_cli_verification_exports_complete_private_evidence_and_public_challenges(proto, tmp_path):
    cli = PROTOTYPE.with_name("verify.py")
    assert cli.is_file(), "the requested evidence CLI is not implemented"
    result = subprocess.run([sys.executable, str(cli), "verify", "--seed", "20261023",
                             "--out", str(tmp_path)], capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path / "evidence.json").read_text())
    assert report["status"] == "prototype_verified"
    assert len(report["episodes"]) == 4
    assert report["summary"]["parameter_rivals_refuted"] == 12
    assert report["summary"]["canonical_pairs_passed"] == 4
    assert report["counterfactual"]["distinct_outputs"] == 4
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert all(case["changed_cells"] >= 100 for case in report["large_queries"])
    public = json.loads((tmp_path / "public_challenges.json").read_text())
    assert len(public) == 4
    for challenge in public:
        assert set(challenge) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in challenge["test"])


def test_cli_sampled_episode_and_invalid_parameters(proto, tmp_path):
    cli = PROTOTYPE.with_name("verify.py")
    assert cli.is_file(), "the requested episode CLI is not implemented"
    result = subprocess.run([sys.executable, str(cli), "episode", "--seed", "17",
                             "--sample-parameters", "--out", str(tmp_path)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    private = json.loads((tmp_path / "episode.json").read_text())
    assert private["parameters"] == proto.sample_parameters(17)
    public = json.loads((tmp_path / "challenge.json").read_text())
    assert public == proto.public_challenge(private)
    bad = subprocess.run([sys.executable, str(cli), "episode", "--seed", "17",
                          "--min-anchors", "4", "--out", str(tmp_path)],
                         capture_output=True, text=True, timeout=30)
    assert bad.returncode == 2


def test_reference_runtime_does_not_leave_deleted_snapshot_imports(proto):
    code = """import importlib.util, sys
spec = importlib.util.spec_from_file_location('prototype_cleanup', sys.argv[1])
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
with p.reference_runtime() as runtime:
    runtime.apply(p.materialize_rule(), [[2, 0, 2]])
from reviewer_support import load_selected_generator
load_selected_generator(p.TASK_ID, root=p.ROOT)
"""
    result = subprocess.run([sys.executable, "-c", code, str(PROTOTYPE)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
