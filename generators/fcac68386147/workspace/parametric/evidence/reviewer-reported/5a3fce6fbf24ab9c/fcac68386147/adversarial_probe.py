#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2] / "repo"
prototype_path = repo / "generators/fcac68386147/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("fcac68386147_parametric", prototype_path)
assert spec and spec.loader
prototype = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(repo))
spec.loader.exec_module(prototype)

evidence = Path(__file__).resolve().parent / "repeat-offset-evidence-v1"
report = json.loads((evidence / "report.json").read_text(encoding="utf-8"))

# Surface 1: maximum count and sampler boundaries.  A bounded seed sweep attacks
# duplicate generation, invalid tiles, and accidental coupling to the chosen rule.
sampler_cases = 0
max_output_shape = [0, 0]
for seed in range(256):
    inputs = prototype.sample_inputs(seed, prototype.MAX_TOTAL_PAIRS)
    assert len(inputs) == 16
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    assert len(fingerprints) == 16
    assert inputs == prototype.sample_episode(
        seed, demos=8, queries=8, setting=(0, 0)
    )["inputs"]
    assert inputs == prototype.sample_episode(
        seed, demos=8, queries=8, setting=(1, 1)
    )["inputs"]
    for grid in inputs:
        prototype._validate_tile(grid)
    sampler_cases += len(inputs)

boundary_grid = next(
    grid for grid in prototype.sample_inputs(0, 16) if len(grid) == 5
)
boundary_output = prototype.python_mirror(boundary_grid, 1, 1)
max_output_shape = [len(boundary_output), len(boundary_output[0])]
assert max_output_shape == [30, 30]

# Surface 2: exact public/private separation and content-addressed identities.
public_files = sorted((evidence / "public").glob("*.json"))
assert len(public_files) == 4
public_checks = []
for path in public_files:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    assert path.stem == digest
    challenge = json.loads(payload)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == report["counts"]["demos"]
    assert len(challenge["test"]) == report["counts"]["queries"]
    assert all(set(row) == {"input", "output"} for row in challenge["train"])
    assert all(set(row) == {"input"} for row in challenge["test"])
    assert b'"seed"' not in payload
    assert b'"parameters"' not in payload
    assert b'"program"' not in payload
    public_checks.append({"path": path.relative_to(evidence).as_posix(), "sha256": digest})

for episode_row in report["episodes"]:
    private = json.loads((evidence / episode_row["private_path"]).read_text(encoding="utf-8"))
    public_path = evidence / episode_row["public_path"]
    reconstructed = prototype.public_challenge(
        private["pairs"],
        demos=private["demo_count"],
        queries=private["query_count"],
    )
    assert prototype.public_challenge_bytes(reconstructed) == public_path.read_bytes()
    assert prototype.public_challenge_id(reconstructed) == public_path.stem
    assert "program" in private and "parameters" in private and "seed" in private

result = {
    "schema": "fcac68386147-adversarial-probe-v1",
    "status": "pass",
    "surfaces": {
        "sampler_count_boundaries": {
            "seeds_checked": 256,
            "inputs_checked": sampler_cases,
            "max_requested_pairs": 16,
            "max_5x5_offset_1_1_output_shape": max_output_shape,
            "duplicate_or_rule_stream_coupling_findings": 0,
        },
        "public_private_export": {
            "public_files_checked": len(public_files),
            "content_addressed_identities": public_checks,
            "hidden_field_leaks": 0,
            "private_to_public_exact_reconstructions": len(report["episodes"]),
        },
    },
    "bounded_limit": (
        "The sampler sweep covers seeds 0..255 and declared limits only; "
        "it is not an exhaustive proof over the 63-bit seed space."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
