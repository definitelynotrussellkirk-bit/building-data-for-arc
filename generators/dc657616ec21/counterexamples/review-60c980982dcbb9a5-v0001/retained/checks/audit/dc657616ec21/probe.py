#!/usr/bin/env python3
from __future__ import annotations
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
GEN_PATH = REPO / "generators/dc657616ec21/generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
OUT = Path(__file__).with_name("rival_probe.json")
SEED = 99173
N = 400
BANDS = ("easy", "medium", "hard")

spec = importlib.util.spec_from_file_location("audit_dc657616ec21", GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

def equality(values):
    return [[8 if a == b else 0 for b in values] for a in values]

def analyze(grid):
    facts, errors = mod._analyze(grid)
    if errors:
        raise ValueError(errors)
    proxy = [(min(p["bbox"]) + 1) // 2 for p in facts["panels"]]
    return {
        "depths": facts["depths"],
        "proxy_classes": proxy,
        "official": equality(facts["depths"]),
        "rival": equality(proxy),
        "agrees": equality(facts["depths"]) == equality(proxy),
        "panel_facts": facts["panels"],
    }

canonical = None
for line in CANONICAL.read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == mod.TASK_ID:
        canonical = row
        break
assert canonical is not None
canonical_rows = []
for i, pair in enumerate(canonical["train"]):
    info = analyze(pair["input"])
    canonical_rows.append({
        "train_index": i,
        "rival_matches_canonical_output": info["rival"] == pair["output"],
        "depths": info["depths"],
        "proxy_classes": info["proxy_classes"],
    })

bands = {}
for band in BANDS:
    samples = []
    for sample_index in range(N):
        grid = mod.generate(SEED, sample_index, difficulty=band)
        info = analyze(grid)
        samples.append(info)
    cyclic_survivors = []
    for start in range(N):
        indices = [start, (start + 1) % N, (start + 2) % N]
        if all(samples[i]["agrees"] for i in indices):
            cyclic_survivors.append(start)
    first_disagreement = next((i for i, x in enumerate(samples) if not x["agrees"]), None)
    bands[band] = {
        "sample_count": N,
        "single_input_agreements": sum(x["agrees"] for x in samples),
        "cyclic_three_demo_windows": N,
        "cyclic_three_demo_survivors": len(cyclic_survivors),
        "first_surviving_start": cyclic_survivors[0] if cyclic_survivors else None,
        "first_disagreement_sample_index": first_disagreement,
    }

out = {
    "schema": "audit_rival_probe/1",
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "declared_rule_hash": mod.RULE_HASH,
    "rival": "ceil(min(panel_bbox_height,panel_bbox_width)/2) equality matrix",
    "canonical_train_pairs": canonical_rows,
    "canonical_pairs_fit": all(x["rival_matches_canonical_output"] for x in canonical_rows),
    "sampler": {
        "seed": SEED,
        "sample_indices": [0, N - 1],
        "difficulty_bands": list(BANDS),
        "lesson_policy": "all cyclic windows of three consecutive sample indices within each 400-input band",
    },
    "bands": bands,
    "command": {
        "cwd": "repo",
        "argv": ["python3", "../checks/audit/dc657616ec21/probe.py"],
        "environment": {"PYTHONPATH": "shared/runtime:src"},
    },
}
OUT.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
