"""Focused tests for the task-local crossing-priority prototype only.

These do not approve a rule variant or alter the canonical production generator.
The tests exercise actual Racket execution, including simultaneous reads.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "13d2544b2b64"


def _prototype():
    # The public task-test runner relocates these tests. Bind to their own tree.
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("shared/runtime", "."):
            runtime = ancestor / relative
            if (runtime / "reviewer_support.py").is_file():
                if str(runtime) not in sys.path:
                    sys.path.insert(0, str(runtime))
                from reviewer_support import find_root

                root = find_root(__file__)
                path = root / "generators" / TASK_ID / "workspace/parametric/prototype.py"
                assert path.is_file(), "task-local parametric prototype is not implemented"
                spec = importlib.util.spec_from_file_location("crossing_priority_prototype", path)
                assert spec and spec.loader
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                return module
    raise AssertionError("no local library/runtime found")


def _crossing_with_overwrites_and_cascade_trap():
    grid = [[0 if r in (2, 5) or c in (2, 5) else 1 for c in range(8)]
            for r in range(8)]
    # At the central local (0,0): horizontal says 2, vertical says 3.
    grid[3][0] = grid[3][6] = 2
    grid[0][3] = grid[6][3] = 3
    grid[3][3] = 9
    # These corner matches overwrite the four sources in the output. Reading
    # the evolving output instead of the original input would yield 6 centrally.
    for r in (0, 6):
        for c in (0, 6):
            grid[r][c] = 6
    grid[3][1], grid[3][7] = 4, 5  # unequal colors must not agree
    grid[1][3] = 7  # a lone source must not paint its middle counterpart
    return grid


def test_default_rule_is_exact_canonical_source():
    p = _prototype()
    source = p.materialize_rule()
    assert source == p.canonical_record()["program_solution"]
    assert hashlib.sha256(source.encode()).hexdigest() == p.CANONICAL_SHA256
    assert p.normalize_parameters() == {"crossing_priority": "horizontal"}
    assert p.materialize_rule({"crossing_priority": "vertical"}) != source


def test_default_racket_reproduces_all_four_canonical_pairs():
    p = _prototype()
    record = p.canonical_record()
    pairs = record["train"] + record["test"]
    assert len(pairs) == 4
    with p.RacketRunner() as runner:
        observed = runner.run(p.materialize_rule(), [x["input"] for x in pairs])
    assert observed == [x["output"] for x in pairs]


def test_priority_changes_only_conflicts_and_preserves_original_input_reads():
    p = _prototype()
    grid = _crossing_with_overwrites_and_cascade_trap()
    original = copy.deepcopy(grid)
    with p.RacketRunner() as runner:
        horizontal = runner.run(p.materialize_rule(), [grid])[0]
        vertical = runner.run(p.materialize_rule({"crossing_priority": "vertical"}), [grid])[0]
    assert horizontal[3][3] == 2
    assert vertical[3][3] == 3
    assert [(r, c) for r in range(8) for c in range(8)
            if horizontal[r][c] != vertical[r][c]] == [(3, 3)]
    for output in (horizontal, vertical):
        assert output[0][3] == output[6][3] == output[3][0] == output[3][6] == 6
        assert output[3][4] == 1  # unequal pair
        assert output[4][3] == 1  # lone source
        assert all(output[r][c] == 0 for r in range(8) for c in range(8)
                   if r in (2, 5) or c in (2, 5))
    assert grid == original


@pytest.mark.parametrize("parameters", [
    {"crossing_priority": "diagonal"}, {"crossing_priority": "HORIZONTAL"},
    {"crossing_priority": True}, {"crossing_priority": 1},
    {"crossing_priority": []}, {"crossing_priority": None},
    {"unexpected": "horizontal"}, ["horizontal"], "horizontal",
])
def test_malformed_parameters_fail_loudly(parameters):
    p = _prototype()
    with pytest.raises(ValueError, match="parameter|crossing_priority"):
        p.normalize_parameters(parameters)
    with pytest.raises(ValueError, match="parameter|crossing_priority"):
        p.materialize_rule(parameters)


@pytest.mark.parametrize("seed", [True, -1, 1.5, "5", None])
def test_malformed_episode_seeds_fail_loudly(seed):
    p = _prototype()
    with pytest.raises(ValueError, match="seed"):
        p.parameters_from_seed(seed)


def test_seed_selection_is_deterministic_and_covers_the_declared_values():
    p = _prototype()
    first = [p.parameters_from_seed(seed) for seed in range(16)]
    assert first == [p.parameters_from_seed(seed) for seed in range(16)]
    assert {x["crossing_priority"] for x in first} == {"horizontal", "vertical"}
    assert p.parameters_from_seed(0) == {"crossing_priority": "horizontal"}
    assert p.parameters_from_seed(5) == {"crossing_priority": "vertical"}


@pytest.mark.parametrize("priority", ["horizontal", "vertical"])
def test_episode_demonstrations_refute_other_priority_before_conflicting_query(priority):
    p = _prototype()
    with p.RacketRunner() as runner:
        episode = p.build_episode(31, parameters={"crossing_priority": priority}, runner=runner)
        report = p.check_episode(episode, runner=runner)
    assert episode["parameters"] == {"crossing_priority": priority}
    assert len(episode["train"]) == 4
    assert len(episode["test"]) == 1
    assert report["passed"], report
    chosen = report["candidates"][priority]
    rival = report["candidates"]["vertical" if priority == "horizontal" else "horizontal"]
    assert chosen["demo_mismatch_indices"] == chosen["query_mismatch_indices"] == []
    assert rival["refuted_by_demonstrations"]
    assert rival["demo_mismatch_indices"]
    assert rival["query_mismatch_indices"] == [0]


def test_episode_generation_is_deterministic_and_inputs_do_not_depend_on_priority():
    p = _prototype()
    with p.RacketRunner() as runner:
        first = p.build_episode(17, runner=runner)
        assert first == p.build_episode(17, runner=runner)
        horizontal = p.build_episode(17, parameters={"crossing_priority": "horizontal"}, runner=runner)
        vertical = p.build_episode(17, parameters={"crossing_priority": "vertical"}, runner=runner)
    assert [x["input"] for x in horizontal["train"] + horizontal["test"]] == [
        x["input"] for x in vertical["train"] + vertical["test"]]
    assert horizontal["test"][0]["output"] != vertical["test"][0]["output"]
    assert first["test"][0]["input"] not in [x["input"] for x in first["train"]]


def test_public_projection_omits_all_hidden_fields_and_does_not_alias_private_data():
    p = _prototype()
    with p.RacketRunner() as runner:
        episode = p.build_episode(5, runner=runner)
    original = copy.deepcopy(episode)
    public = p.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    text = json.dumps(public)
    for hidden in ("parameters", "crossing_priority", "racket", "sha256", "seed", "source"):
        assert hidden not in text
    public["train"][0]["input"][0][0] = 9
    assert episode == original


def test_checker_does_not_use_query_answer_to_rescue_ambiguous_demonstrations():
    p = _prototype()
    with p.RacketRunner() as runner:
        episode = p.build_episode(0, runner=runner)
        episode["train"][2] = copy.deepcopy(episode["train"][0])
        report = p.check_episode(episode, runner=runner)
    assert not report["passed"]
    rival = report["candidates"]["vertical"]
    assert not rival["refuted_by_demonstrations"]
    assert rival["query_mismatch_indices"] == [0]
    assert any("demonstrations" in error for error in report["failures"])


def test_checker_rejects_tampered_query_answers_and_parameter_metadata():
    p = _prototype()
    with p.RacketRunner() as runner:
        episode = p.build_episode(0, runner=runner)
        tampered = copy.deepcopy(episode)
        tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
        assert not p.check_episode(tampered, runner=runner)["passed"]
        tampered = copy.deepcopy(episode)
        tampered["parameters"]["crossing_priority"] = "invalid"
        assert not p.check_episode(tampered, runner=runner)["passed"]


def test_bundle_replay_verifies_all_examples_rules_public_files_and_hashes(tmp_path):
    p = _prototype()
    destination = tmp_path / "priority-bundle"
    report = p.write_bundle(destination, seeds=[0, 5])
    assert report["passed"], report
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["pairs"] == 10
    assert report["canonical_default"]["matches"] == 4
    assert set(report["settings_observed"]) == {"horizontal", "vertical"}
    verified = p.verify_bundle(destination)
    assert verified["passed"], verified
    assert verified["counts"]["racket_checked_episode_pairs"] == 10
    public_file = destination / "public/challenge-000.json"
    payload = json.loads(public_file.read_text())
    payload["parameters"] = {"crossing_priority": "horizontal"}
    public_file.write_text(json.dumps(payload))
    assert not p.verify_bundle(destination)["passed"]


def test_bundle_checker_requires_every_retained_episode_exactly_once(tmp_path):
    p = _prototype()
    destination = tmp_path / "inventory-bundle"
    original = p.write_bundle(destination, seeds=[0, 5])
    report_file = destination / "report.json"
    manifest_file = destination / "manifest.json"
    for indices in ([], [0], [0, 0]):
        altered = copy.deepcopy(original)
        altered["episodes"] = [altered["episodes"][index] for index in indices]
        report_file.write_text(json.dumps(altered))
        manifest = json.loads(manifest_file.read_text())
        manifest["files"]["report.json"] = hashlib.sha256(report_file.read_bytes()).hexdigest()
        manifest_file.write_text(json.dumps(manifest))
        replay = p.verify_bundle(destination)
        assert not replay["passed"], f"report indices {indices!r} hid a retained episode from replay"
