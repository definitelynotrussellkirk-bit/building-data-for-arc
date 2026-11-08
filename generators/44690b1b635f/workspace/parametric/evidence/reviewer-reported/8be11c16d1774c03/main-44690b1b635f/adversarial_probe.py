#!/usr/bin/env python3
"""Bounded adversarial probe for the 44690b1b635f parametric prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
CHECKS = HERE.parent
REPO = CHECKS.parent / "repo"
PROTOTYPE = REPO / "generators/44690b1b635f/workspace/parametric/prototype.py"
EVIDENCE = CHECKS / "parametric/44690b1b635f-maze-connectivity-phase-v1"
REPORT = HERE / "adversarial-report.json"

spec = importlib.util.spec_from_file_location("adversarial_44690b1b635f", PROTOTYPE)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load prototype")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def expect_value_error(fn, label: str) -> str:
    try:
        fn()
    except ValueError as error:
        return f"{label}: {error}"
    raise AssertionError(f"{label}: expected ValueError")


# Surface 1: sampler boundaries, deterministic uniqueness, and bounded retries.
max_seed_grids = p.episode_inputs(2**63 - 1, demos=8, queries=8, max_attempts=64, root=REPO)
assert len(max_seed_grids) == 16
assert len({p.grid_sha256(grid) for grid in max_seed_grids}) == 16
for grid in max_seed_grids:
    certificate = p.input_certificate(grid)
    assert certificate["cardinal_reachable_zero_count"] >= 3
    assert certificate["king_only_reachable_zero_count"] >= 3
    assert certificate["unreachable_zero_count_king"] >= 3
    assert certificate["four_setting_outputs_pairwise_distinct"] is True

template = p.episode_inputs(7, demos=1, queries=1, root=REPO)[0]
original_draw = p._draw_procedural_input
calls: list[tuple[int, int, int]] = []


def duplicate_draw(seed: int, slot: int, attempt: int):
    calls.append((seed, slot, attempt))
    return copy.deepcopy(template)


p._draw_procedural_input = duplicate_draw
try:
    try:
        p.episode_inputs(7, demos=2, queries=1, max_attempts=3, root=REPO)
    except RuntimeError as error:
        retry_error = str(error)
    else:
        raise AssertionError("duplicate sampler did not exhaust its retry limit")
finally:
    p._draw_procedural_input = original_draw
assert calls == [(7, 0, 0), (7, 1, 0), (7, 1, 1), (7, 1, 2)]
assert "slot 1 after 3 attempts" in retry_error
validation_receipts = [
    expect_value_error(lambda: p.episode_inputs(True), "bool seed"),
    expect_value_error(lambda: p.episode_inputs(0, demos=True), "bool count"),
    expect_value_error(lambda: p.episode_inputs(0, max_attempts=0), "zero attempts"),
]

# Surface 2: public/private separation, hashes, exact selected-rule execution.
manifest = json.loads((EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
assert manifest["counts"]["episodes"] == 4
assert [row["public_id"] for row in manifest["episodes"]] == sorted(
    row["public_id"] for row in manifest["episodes"]
)
for row in manifest["files"]:
    payload = (EVIDENCE / row["path"]).read_bytes()
    assert len(payload) == row["bytes"]
    assert hashlib.sha256(payload).hexdigest() == row["sha256"]

forbidden = (
    '"seed"',
    '"settings"',
    '"program_solution"',
    '"program_sha256"',
    '"query_answers"',
    "center_even",
    "arm_even",
)
private_episodes = []
for row in manifest["episodes"]:
    public_path = EVIDENCE / row["public_path"]
    private_path = EVIDENCE / row["private_path"]
    public_raw = public_path.read_bytes()
    public = json.loads(public_raw)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    assert public_path.name == f"challenge-{p.public_challenge_id(public)}.json"
    assert public_raw == p.public_challenge_bytes(public)
    assert not any(token in public_raw.decode("utf-8") for token in forbidden)
    assert p.public_payload(private) == public
    private_episodes.append(private)

original_private = copy.deepcopy(private_episodes[0])
projected = p.public_payload(private_episodes[0])
projected["train"][0]["input"][0][0] = (projected["train"][0]["input"][0][0] + 1) % 10
assert private_episodes[0] == original_private
bad_private = copy.deepcopy(private_episodes[0])
bad_private["train"][0]["input"][0][0] = True
validation_receipts.append(
    expect_value_error(lambda: p.public_payload(bad_private), "bool grid cell")
)
bad_private = copy.deepcopy(private_episodes[0])
bad_private["train"][0]["input"][0].pop()
validation_receipts.append(
    expect_value_error(lambda: p.public_payload(bad_private), "ragged grid")
)

with p.RacketBridge(max_calls_before_restart=128) as bridge:
    runtime_identity = bridge.runtime_identity
    for private in private_episodes:
        grids = [pair["input"] for pair in private["train"] + private["test"]]
        stored = [pair["output"] for pair in private["train"] + private["test"]]
        recognized = p.recognize_rule(private["program_solution"], root=REPO)
        assert recognized == private["settings"]
        actual = p.execute_rule_many(
            private["program_solution"], grids, bridge=bridge, root=REPO
        )
        oracle = [p.independent_output(grid, private["settings"]) for grid in grids]
        assert actual == stored == oracle
        assert private["query_answers"] == stored[private["demo_count"] :]
        assert all(
            len(item["eliminated_rivals_that_disagree"]) == 3
            and item["query_answer_used_for_demo_fit"] is False
            for item in private["query_identification"]
        )

report = {
    "schema": "44690b1b635f-parametric-adversarial-probe-v1",
    "status": "passed",
    "surfaces": {
        "sampler_boundaries_and_retry": {
            "max_seed": 2**63 - 1,
            "boundary_inputs": len(max_seed_grids),
            "distinct_inputs": len({p.grid_sha256(grid) for grid in max_seed_grids}),
            "duplicate_retry_calls": [list(item) for item in calls],
            "retry_error": retry_error,
        },
        "public_private_and_rule_parity": {
            "episodes": len(private_episodes),
            "pairs_reexecuted": sum(
                len(item["train"]) + len(item["test"]) for item in private_episodes
            ),
            "settings": [item["settings"] for item in private_episodes],
            "runtime_identity": runtime_identity,
            "manifest_sha256": hashlib.sha256(
                (EVIDENCE / "manifest.json").read_bytes()
            ).hexdigest(),
        },
    },
    "strict_rejections": validation_receipts,
    "finding": "No defect found in the bounded surfaces; exact retry exhaustion, strict numeric grids, visible-only IDs, and selected-rule Racket parity were retained.",
    "limits": [
        "The probe covered one maximum seed and one forced duplicate retry path, not every seed.",
        "Racket replay covered the four retained selected rules, not arbitrary source mutations.",
    ],
}
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
