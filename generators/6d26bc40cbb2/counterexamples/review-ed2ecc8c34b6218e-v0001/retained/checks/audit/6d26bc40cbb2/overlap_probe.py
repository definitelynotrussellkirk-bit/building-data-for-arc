from __future__ import annotations
from collections import Counter
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
TASK = "6d26bc40cbb2"
PATH = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_6d26", PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

def rival_original_wins(grid):
    facts = module.analyze_scene(grid)["facts"]
    height, width = len(grid), len(grid[0])
    dr, dc = facts["delta"]
    out = [[value if value not in (0, 9) else 0 for value in row] for row in grid]
    for row, col in facts["payload"]:
        dst_row, dst_col = row + dr, col + dc
        if 0 <= dst_row < height and 0 <= dst_col < width and out[dst_row][dst_col] == 0:
            out[dst_row][dst_col] = grid[row][col]
    return out

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "sampler": {"bands": ["easy", "medium", "hard"], "seeds": "1..200", "sample_indices": "0..19", "window_starts": "0..16", "demo_count": 3},
    "bands": {},
    "first_ambiguous_window": None,
}
for band in report["sampler"]["bands"]:
    counts = Counter()
    for seed in range(1, 201):
        authoritative = []
        rival = []
        grids = []
        for index in range(20):
            grid = module.generate(seed, index, difficulty=band)
            expected = module.solve_python(grid)
            candidate = rival_original_wins(grid)
            facts = module.analyze_scene(grid)["facts"]
            counts["samples"] += 1
            counts["overlap_samples"] += bool(set(facts["payload"]) & set(facts["visible_shifted"]))
            counts["priority_disagreements"] += candidate != expected
            grids.append(grid)
            authoritative.append(expected)
            rival.append(candidate)
        for start in range(17):
            counts["windows"] += 1
            ambiguous = all(rival[start + offset] == authoritative[start + offset] for offset in range(3)) and rival[start + 3] != authoritative[start + 3]
            counts["ambiguous_windows"] += ambiguous
            if ambiguous and report["first_ambiguous_window"] is None:
                report["first_ambiguous_window"] = {"band": band, "seed": seed, "start": start, "demo_indices": [start, start + 1, start + 2], "query_index": start + 3}
    report["bands"][band] = dict(counts)
report["passed_as_counterexample"] = report["first_ambiguous_window"] is not None
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed_as_counterexample"] else 1)
