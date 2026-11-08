from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "4b7b6d3a3a14"
ROOT = Path.cwd()
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def motif_colors(grid):
    return sorted({value for row in grid for value in row if value not in (0, 1, 2)})

pairs = canonical_pairs(TASK, root=ROOT)
sampled = []
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = gen.generate(5900 + index, index, difficulty=band)
        sampled.append({"band": band, "index": index, "colors": motif_colors(grid),
                        "marker": grid[0][0], "self_check": gen.self_check(grid)})
report = {
    "schema": "audit-domain-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_self_check": [gen.self_check(pair["input"]) for pair in pairs],
    "canonical_motif_color_counts": [len(motif_colors(pair["input"])) for pair in pairs],
    "sampled_draws": len(sampled),
    "sampled_by_band": dict(Counter(item["band"] for item in sampled)),
    "sampled_motif_color_counts": sorted({len(item["colors"]) for item in sampled}),
    "sampled_with_multiple_motif_colors": sum(len(item["colors"]) > 1 for item in sampled),
    "sampled_self_check_failures": sum(bool(item["self_check"]) for item in sampled),
    "marker_counts": dict(Counter(str(item["marker"]) for item in sampled)),
    "seed_recipe": "seed=5900+index, sample_index=index, 100 draws per easy/medium/hard",
}
print(json.dumps(report, indent=2))
