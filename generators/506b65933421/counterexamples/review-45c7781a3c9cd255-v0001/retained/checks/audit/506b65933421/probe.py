from __future__ import annotations
import hashlib, importlib, json, sys
from collections import Counter
from pathlib import Path

packet = Path(__file__).resolve().parents[3]
repo = packet / "repo"
sys.path[:0] = [str(repo / "shared/runtime"), str(repo)]
task = "506b65933421"
mod = importlib.import_module(f"generators.{task}.generator")
source_hash = hashlib.sha256((repo / "generators" / task / "generator.py").read_bytes()).hexdigest()
canonical = next(json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").open() if json.loads(line).get("task_id") == task)
raw = canonical["train"][0]["input"]
grid = [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in raw]
assert not mod.self_check(grid)

def first_color_only(g):
    h, w = len(g), len(g[0])
    colors = []
    for row in g:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    out = [[0] * w for _ in range(h)]
    if colors:
        color = colors[0]
        cells = [(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value == color]
        if len(cells) >= 2:
            rs, cs = zip(*cells)
            for r in range(min(rs), max(rs) + 1):
                for c in range(min(cs), max(cs) + 1):
                    out[r][c] = color
    return out

normal = []
for difficulty in ("easy", None, "hard"):
    for sample_index in range(100):
        sample = mod.generate(90210, sample_index, difficulty=difficulty)
        normal.append((len({value for row in sample for value in row if value}), mod.self_check(sample, difficulty=difficulty)))
override = [len({value for row in mod.generate(90210, i, difficulty="medium", num_colors=2) for value in row if value}) for i in range(20)]
out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
(out_dir / "rival.json").write_text(json.dumps({"rival": "first_color_only_bbox", "output": first_color_only(grid)}, indent=2) + "\n")
probe = {
    "schema": "arcpuzzles-audit-probe-v1", "task_id": task, "generator_sha256": source_hash, "seed": 90210,
    "normal_samples": {"count": 300, "bands": {"easy": 100, "medium": 100, "hard": 100},
                       "distinct_color_count_histogram": {str(k): v for k, v in sorted(Counter(n for n, _ in normal).items())},
                       "self_check_failures": sum(bool(errors) for _, errors in normal)},
    "num_colors_2_override": {"count": 20, "distinct_color_count_histogram": {str(k): v for k, v in sorted(Counter(override).items())}},
    "canonical_counterexample": {"canonical_train_index": 0, "passes_self_check": True,
                                 "nonzero_colors": sorted({value for row in grid for value in row if value}),
                                 "rival": "first_color_only_bbox"},
}
(out_dir / "probe.json").write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
print(json.dumps(probe, sort_keys=True))
