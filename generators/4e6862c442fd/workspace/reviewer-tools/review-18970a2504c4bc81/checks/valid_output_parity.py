from __future__ import annotations

import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path

ROOT = Path.cwd()
BEFORE = ROOT.parent / "checks/originals/4e6862c442fd/generator.py.before"
AFTER = ROOT / "generators/4e6862c442fd/generator.py"
OUT = ROOT.parent / "checks/valid-output-parity.json"


def load(name: str, path: Path):
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


before = load("review_before_4e6862c442fd", BEFORE)
after = load("review_after_4e6862c442fd", AFTER)

calls = []
for seed in range(20):
    for sample_index in range(16):
        for difficulty in (None, "easy", "medium", "hard"):
            calls.append((seed, sample_index, difficulty, {}))

boundary_sets = [
    {"grid_h": 12, "grid_w": 18, "source_basis": 0, "target_basis": 7, "motif_id": 0},
    {"grid_h": 18, "grid_w": 26, "source_basis": 7, "target_basis": 0, "motif_id": 7},
    {"grid_h": 12, "grid_w": 26, "source_basis": 3, "target_basis": 3, "motif_id": 5},
    {"grid_h": 18, "grid_w": 18, "source_basis": 4, "target_basis": 2, "motif_id": 2},
]
for seed in range(8):
    for difficulty in (None, "easy", "medium", "hard"):
        for overrides in boundary_sets:
            calls.append((9000 + seed, 17, difficulty, overrides))

hash_before = hashlib.sha256()
hash_after = hashlib.sha256()
mismatches = []
for ordinal, (seed, sample_index, difficulty, overrides) in enumerate(calls):
    kwargs = dict(overrides)
    if difficulty is not None:
        kwargs["difficulty"] = difficulty
    left = before.generate(seed, sample_index, **kwargs)
    right = after.generate(seed, sample_index, **kwargs)
    left_bytes = json.dumps(left, separators=(",", ":")).encode()
    right_bytes = json.dumps(right, separators=(",", ":")).encode()
    hash_before.update(left_bytes)
    hash_after.update(right_bytes)
    if left != right:
        mismatches.append({
            "ordinal": ordinal,
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": overrides,
        })

result = {
    "schema": "valid-output-parity/1",
    "task_id": "4e6862c442fd",
    "before_source_sha256": hashlib.sha256(BEFORE.read_bytes()).hexdigest(),
    "after_source_sha256": hashlib.sha256(AFTER.read_bytes()).hexdigest(),
    "valid_calls_checked": len(calls),
    "mismatch_count": len(mismatches),
    "aggregate_before_sha256": hash_before.hexdigest(),
    "aggregate_after_sha256": hash_after.hexdigest(),
    "mismatches": mismatches[:20],
}
OUT.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(1 if mismatches else 0)
