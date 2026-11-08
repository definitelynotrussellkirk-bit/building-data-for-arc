#!/usr/bin/env python3
"""Independent structural/hash verification for the retained public-ID export."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path.cwd()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


report = json.loads((HERE / "report.json").read_text())
assert report["canonical_parity"] == {"passed": 8, "total": 8, "unique_inputs": 4}
episodes = report["episodes"]
assert len(episodes) == 6
ids = [row["public_id"] for row in episodes]
assert ids == sorted(ids)
assert len(ids) == len(set(ids))
assert {tuple(sorted(row["parameters"].items())) for row in episodes} == {
    (("direction", direction), ("min_anchors", threshold))
    for direction in ("both", "horizontal", "vertical")
    for threshold in (2, 3)
}

for row in episodes:
    public_id = row["public_id"]
    assert len(public_id) == 64 and all(c in "0123456789abcdef" for c in public_id)
    assert row["public_path"] == f"public/{public_id}.json"
    assert row["private_path"] == f"private/{public_id}/private.json"
    assert row["rule_path"] == f"private/{public_id}/rule.rkt"

    public_path = HERE / row["public_path"]
    private_path = HERE / row["private_path"]
    rule_path = HERE / row["rule_path"]
    assert sha256(public_path) == public_id
    assert report["files_sha256"][row["public_path"]] == public_id
    assert report["files_sha256"][row["private_path"]] == sha256(private_path)
    assert report["files_sha256"][row["rule_path"]] == sha256(rule_path)

    public = json.loads(public_path.read_text())
    private = json.loads(private_path.read_text())
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and all(set(pair) == {"input", "output"} for pair in public["train"])
    assert len(public["test"]) == 4 and all(set(pair) == {"input"} for pair in public["test"])
    assert private["public_id"] == public_id
    assert private["public_path"] == row["public_path"]
    assert private["parameters"] == row["parameters"]
    assert private["n_train"] == 3 and private["n_test"] == 4
    assert len(private["query_outputs"]) == 4
    assert sha256(rule_path) == private["rule_sha256"] == row["rule_sha256"]

    inputs = [pair["input"] for pair in public["train"]] + [pair["input"] for pair in public["test"]]
    computed_input_hashes = [grid_sha(grid) for grid in inputs]
    assert len(set(computed_input_hashes)) == 7
    assert computed_input_hashes == private["input_sha256"] == row["input_sha256"]
    assert private["demo_only_survivors"] == [private["parameters"]]

contrast = json.loads((HERE / "contrast-private.json").read_text())
assert len(contrast["executed_settings"]) == 6
assert len({row["output_sha256"] for row in contrast["executed_settings"]}) == 6

for relative, expected in report["source_sha256"].items():
    assert sha256(REPO / relative) == expected, relative

print("verified 6 content-addressed public challenges, 3 demos + 4 distinct queries each")
