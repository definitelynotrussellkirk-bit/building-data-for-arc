from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "a2fc4c442e35"
ROOT = Path.cwd()
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def run_lengths(grid):
    lengths = []
    for row in grid:
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            value = row[c]
            start = c
            while c < len(row) and row[c] == value:
                c += 1
            lengths.append(c - start)
    return lengths

pairs = canonical_pairs(TASK, root=ROOT)
sampled = []
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = gen.generate(4800 + index, index, difficulty=band)
        sampled.append({"band": band, "index": index, "lengths": run_lengths(grid),
                        "self_check": gen.self_check(grid)})
report = {
    "schema": "audit-domain-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_self_check": [gen.self_check(pair["input"]) for pair in pairs],
    "canonical_run_lengths": [run_lengths(pair["input"]) for pair in pairs],
    "sampled_draws": len(sampled),
    "sampled_by_band": dict(Counter(item["band"] for item in sampled)),
    "sampled_run_lengths": sorted({n for item in sampled for n in item["lengths"]}),
    "sampled_with_non_three_run": sum(any(n != 3 for n in item["lengths"]) for item in sampled),
    "sampled_self_check_failures": sum(bool(item["self_check"]) for item in sampled),
    "seed_recipe": "seed=4800+index, sample_index=index, 100 draws per easy/medium/hard",
}
print(json.dumps(report, indent=2))
