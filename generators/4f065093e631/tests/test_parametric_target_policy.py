"""Portable, prototype-only contracts for the target-policy extension.

Faults these tests detect: replacing the original selector, using scene labels
without executing Racket, changing a hidden rule between pairs, or revealing
private metadata in a public challenge. No production acceptance is widened.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "4f065093e631"
ROOT = find_root(__file__)


def _load_prototype():
    load_selected_generator(TASK_ID, root=ROOT)
    path = ROOT / "generators" / TASK_ID / "workspace/parametric/target_policy.py"
    assert path.is_file(), "The requested target-policy prototype is not implemented"
    spec = importlib.util.spec_from_file_location("target_policy_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _border(box):
    r0, c0, r1, c1 = box
    return {(r, c) for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)}


def _expected(grid, scene, policy):
    targets = sorted(scene["targets"])
    chosen = targets[:1] if policy == "first" else targets[-1:] if policy == "last" else targets
    output = [row[:] for row in grid]
    for target in chosen:
        for r, c in _border(target):
            output[r][c] = scene["frame_color"]
    return output


def test_default_program_is_exact_canonical():
    prototype = _load_prototype()
    from reviewer_support import canonical_path
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if json.loads(line).get("task_id") == TASK_ID]
    assert len(rows) == 1
    assert prototype.materialize_program(root=ROOT) == rows[0]["program_solution"]
    assert len({prototype.materialize_program(policy, root=ROOT)
                for policy in ("first", "last", "all")}) == 3


@pytest.mark.parametrize("bad", ["nearest", "", 0, None])
def test_parameter_domain_is_closed(prototype, bad):
    with pytest.raises(ValueError, match="target_policy"):
        prototype.materialize_program(bad, root=ROOT)


def test_sampler_is_deterministic_and_constructively_distinguishing(prototype):
    generator, _source, _sha = load_selected_generator(TASK_ID, root=ROOT)
    random_state = random.getstate()
    dims = set()
    for pair_index in range(4):
        sampled = prototype.sample_scene(1729, pair_index, root=ROOT)
        assert sampled == prototype.sample_scene(1729, pair_index, root=ROOT)
        grid, scene = sampled["input"], sampled["scene"]
        frames = generator._find_frames(grid)
        source = max(frames, key=lambda row: row[-1])
        assert list(source[1:5]) == scene["source"]
        assert sum(frame[-1] == source[-1] for frame in frames) == 1
        slots = generator._zero_slots(grid, scene["frame_height"], scene["frame_width"])
        assert {tuple(box) for box in slots} == {tuple(scene["source"]), *(tuple(box) for box in scene["targets"])}
        assert len(scene["targets"]) >= 2
        assert len({json.dumps(_expected(grid, scene, policy)) for policy in ("first", "last", "all")}) == 3
        assert generator.rule_mirror(grid) == _expected(grid, scene, "first")
        assert sum(value == scene["smaller_color"] for row in grid for value in row) == 8
        assert len(_border(scene["source"])) > 8
        dims.add((len(grid), len(grid[0])))
        if pair_index == 3:
            assert (len(grid), len(grid[0])) == (30, 30)
            assert len(scene["targets"]) == 4
    assert random.getstate() == random_state
    assert len(dims) >= 3


def test_size_overrides_are_exact_and_impossible_sizes_fail(prototype):
    sample = prototype.sample_scene(99, 2, height=24, width=26, root=ROOT)
    assert (len(sample["input"]), len(sample["input"][0])) == (24, 26)
    for kwargs in ({"height": 31}, {"width": True}, {"height": 12, "width": 12}):
        with pytest.raises(ValueError):
            prototype.sample_scene(99, 3, root=ROOT, **kwargs)
    for bad in (True, -1, 1.5):
        with pytest.raises(ValueError):
            prototype.sample_scene(bad, 0, root=ROOT)
    with pytest.raises(ValueError):
        prototype.sample_scene(99, 4, root=ROOT)


@pytest.fixture(scope="module")
def tiny_execution(prototype):
    sample = prototype.sample_scene(1, 0, height=12, width=12, root=ROOT)
    with prototype.Runtime(root=ROOT, timeout=120) as runtime:
        outputs = {policy: runtime.execute(policy, sample["input"])
                   for policy in ("first", "last", "all")}
    return sample, runtime, outputs


def test_live_runtime_reports_identity_and_executes_each_policy(tiny_execution):
    sample, runtime, outputs = tiny_execution
    assert runtime.identity["backend"] == "racket"
    assert runtime.identity["binary_sha256"]
    for policy, output in outputs.items():
        assert output == _expected(sample["input"], sample["scene"], policy)
    assert len(runtime.calls) == 3
    assert all(call["status"] == "passed" for call in runtime.calls)


def test_numbered_public_filenames_do_not_encode_policy(prototype, tiny_execution, tmp_path):
    sample, runtime, outputs = tiny_execution
    # This is an export-unit fixture, with genuine executed labels from the
    # tiny scene. Changing only the publication seed must not resample pairs.
    base = {
        "schema": prototype.SCHEMA, "status": "passed",
        "programs": {policy: {"text": code, "sha256": hashlib.sha256(code.encode()).hexdigest()}
                     for policy, code in runtime.programs.items()},
        "episodes": [{"id": f"episode-{policy}", "seed": 1,
                      "parameters": {"target_policy": policy},
                      "pairs": [{"role": "train", "input": sample["input"], "output": output},
                                {"role": "test", "input": sample["input"], "output": output}]}
                     for policy, output in outputs.items()],
    }
    policies_at_position = [set() for _ in range(3)]
    seed_zero_order = None
    for seed in range(32):
        report = deepcopy(base)
        report["seed"] = seed
        before = deepcopy(report)
        manifest_path = prototype.write_bundle(report, tmp_path / f"seed-{seed}")
        manifest = json.loads(manifest_path.read_text())
        order = [item["episode_id"] for item in manifest["public_challenges"]]
        for position, episode_id in enumerate(order):
            policies_at_position[position].add(episode_id)
        assert report == before
        assert manifest["episodes"] == before["episodes"]
        if seed == 0:
            seed_zero_order = order
    repeat = deepcopy(base)
    repeat["seed"] = 0
    repeated_manifest = json.loads(prototype.write_bundle(repeat, tmp_path / "repeat-zero").read_text())
    assert [item["episode_id"] for item in repeated_manifest["public_challenges"]] == seed_zero_order
    assert all(values == {"episode-first", "episode-last", "episode-all"}
               for values in policies_at_position)


@pytest.fixture(scope="module")
def evidence(prototype):
    return prototype.build_evidence(seed=1729, root=ROOT, timeout=120)


def test_saved_labels_come_from_all_three_racket_settings(prototype, evidence):
    assert evidence["schema"] == "arc-parametric-target-policy-evidence-v1"
    assert evidence["parameter_name"] == "target_policy"
    assert set(evidence["programs"]) == {"first", "last", "all"}
    assert evidence["execution"]["engine"] == "arc_repl.racket_bridge.RacketBridge"
    assert len(evidence["execution"]["calls"]) >= 16
    for program in evidence["programs"].values():
        assert hashlib.sha256(program["text"].encode()).hexdigest() == program["sha256"]
    for episode in evidence["episodes"]:
        policy = episode["parameters"]["target_policy"]
        assert [pair["role"] for pair in episode["pairs"]] == ["train"] * 3 + ["test"]
        for pair in episode["pairs"]:
            assert pair["output"] == _expected(pair["input"], pair["scene"], policy)
            assert pair["input_sha256"] == prototype.grid_sha256(pair["input"])
            assert pair["output_sha256"] == prototype.grid_sha256(pair["output"])
        for rival_policy, rival in episode["rivals"].items():
            assert rival["pair_matches"] == [rival_policy == policy] * 4
            for rotation in rival["rotations"]:
                assert rotation["status"] == ("survived_all" if rival_policy == policy else "rejected_by_demonstrations")
            assert rival["production"]["status"] == ("survived_all" if rival_policy == policy else "rejected_by_demonstrations")


def test_default_racket_preserves_every_canonical_pair(evidence):
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    checks = evidence["canonical_checks"]
    assert checks["pair_count"] == len(pairs) == 4
    assert checks["all_passed"] is True
    for actual, expected in zip(checks["pairs"], pairs):
        assert actual["input"] == expected["input"]
        assert actual["expected_output"] == expected["output"]
        assert actual["executed_output"] == expected["output"]


def test_bundle_separates_challenges_and_refuses_overwriting(prototype, evidence, tmp_path):
    destination = tmp_path / "bundle"
    manifest_path = prototype.write_bundle(evidence, destination)
    manifest = json.loads(manifest_path.read_text())
    assert len(manifest["public_challenges"]) == 3
    by_id = {episode["id"]: episode for episode in manifest["episodes"]}
    for record in manifest["public_challenges"]:
        public_path = destination / record["path"]
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == record["sha256"]
        challenge = json.loads(public_path.read_text())
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 3 and len(challenge["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        episode = by_id[record["episode_id"]]
        assert challenge["test"][0]["input"] == episode["pairs"][3]["input"]
    for relative, digest in manifest["source_hashes"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        prototype.write_bundle(evidence, destination)
