#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ID = "5faf9d5e3e6d"
GENERATOR = HERE.parents[2] / "repo" / "generators" / TASK_ID / "generator.py"


def crop_body(grid):
    pts = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    top = min(r for r, _ in pts)
    bottom = max(r for r, _ in pts)
    left = min(c for _, c in pts)
    right = max(c for _, c in pts)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid):
    return [row[::-1] for row in grid]


def canonical_prediction(grid):
    body = crop_body(grid)
    key = grid[0][0]
    return {1: body, 2: rotate_cw(body), 3: rotate_180(body), 4: flip_lr(body)}[key]


def rival_prediction(grid):
    body = crop_body(grid)
    key = grid[0][0]
    # Preserve every visible meaning except the unseen key 1; map that one to
    # clockwise rotation instead of identity.
    return {1: rotate_cw(body), 2: rotate_cw(body), 3: rotate_180(body), 4: flip_lr(body)}[key]


episode = json.loads((HERE / "default_episode.jsonl").read_text().splitlines()[0])
pairs = [*episode["train"], *episode["test"]]
inputs = [pair["input"] for pair in pairs]
authority = [pair["output"] for pair in pairs]
canonical = [canonical_prediction(grid) for grid in inputs]
rival = [rival_prediction(grid) for grid in inputs]
keys = [grid[0][0] for grid in inputs]
assert canonical == authority
agreement = [candidate == expected for candidate, expected in zip(rival, authority)]
assert agreement[:3] == [True, True, True]
assert agreement[3] is False
assert keys == [2, 3, 4, 1]

(HERE / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
(HERE / "rival.json").write_text(json.dumps({
    "task_id": TASK_ID,
    "rival": "keys 2/3/4 canonical; unseen key 1 mapped to rotate_cw instead of identity",
    "outputs": rival,
}, indent=2) + "\n")
report = {
    "schema": "audit-teaching-ambiguity-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "declared_rule_hash": "abd7c563a610",
    "episode_seed": episode["seed"],
    "sample_indices": episode["sample_indices"],
    "demonstration_keys": keys[:3],
    "query_key": keys[3],
    "rival_agrees_with_authority": agreement,
    "all_demonstrations_fit": all(agreement[:3]),
    "query_differs": not agreement[3],
    "authority_query_output": authority[3],
    "rival_query_output": rival[3],
    "source_episode": "default_episode.jsonl",
    "inputs": "input.json",
    "rival_outputs": "rival.json",
    "command": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "generate", TASK_ID, "--count", "1", "--seed", "42", "--allow-unapproved", "--out", "../checks/audit/5faf9d5e3e6d/default_episode.jsonl"],
    },
}
(HERE / "analysis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
