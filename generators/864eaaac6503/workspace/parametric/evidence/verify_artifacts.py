#!/usr/bin/env python3
"""Read-only verification of the materialized parametric prototype evidence."""
from pathlib import Path
import hashlib
import json
import sys

WORK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORK / "repo/shared/runtime"))
from reviewer_support import find_root
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent / "episodes"
manifest = json.loads((OUT / "private/evidence.json").read_text())
for name, digest in manifest["source_sha256"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
for row in manifest["files"]:
    path = OUT / row["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], path
for row in manifest["programs"].values():
    assert hashlib.sha256(row["text"].encode()).hexdigest() == row["sha256"]
assert hashlib.sha256(manifest["rule_wrapper"].encode()).hexdigest() == manifest["rule_wrapper_sha256"]
settings = set()
train_count = query_count = 0
for path in sorted((OUT / "public").glob("episode-*.json")):
    public = json.loads(path.read_text())
    private = json.loads((OUT / "private" / path.name).read_text())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public["train"] == private["train"]
    assert public["test"] == [{"input": pair["input"]} for pair in private["test"]]
    direction = private["direction"]
    settings.add(direction)
    assert private["program"] == manifest["programs"][direction]["text"]
    assert private["program_sha256"] == manifest["programs"][direction]["sha256"]
    assert private["rival_check"]["demo_survivors"] == [direction]
    assert set(private["rival_check"]["rivals"]) == set(manifest["parameter"]["allowed"])
    assert private["rival_check"]["rivals"][direction]["full_episode_consistent"]
    assert all(not result["demo_consistent"] for key, result in private["rival_check"]["rivals"].items() if key != direction)
    train_count += len(public["train"])
    query_count += len(public["test"])
assert settings == {"ccw", "cw"}
assert manifest["episodes"] == manifest["identifiable_episodes"] == 2
assert train_count == manifest["demonstrations"] == 6
assert query_count == manifest["queries"] == 4
assert manifest["witness"]["distinct"]
print(json.dumps({"status": "passed", "episodes": 2, "demonstrations": train_count,
                  "queries": query_count, "public_schema": "train pairs and query inputs only",
                  "directions": sorted(settings), "source_and_artifact_hashes": "match"}, sort_keys=True))
