"""Capture/compare valid public draws without importing a private generator alias."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--baseline")
a = p.parse_args()
g, source, sha = load_selected_generator("2692a3e47a66", root=find_root(__file__))
calls = []
for difficulty in (None, "easy", "medium", "hard"):
    for seed in (-7, 0, 71):
        for index in range(8):
            calls.append(dict(seed=seed, sample_index=index, difficulty=difficulty))
for profile in g.SCENE_PROFILES:
    for dims in ((7, 7), (17, 19), (30, 30)):
        calls.append(dict(seed=911, sample_index=5, difficulty="hard",
                          scene_profile=profile, grid_h=dims[0], grid_w=dims[1]))
rows = []
for call in calls:
    grid = g.generate(**call)
    assert g.self_check(grid) == []
    rows.append({"call": call, "grid_sha256": hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()).hexdigest()})
result = {"task_id": g.TASK_ID, "source": str(source),
          "generator_sha256": sha, "version": g.VERSION,
          "rule_hash": g.RULE_HASH, "valid_draws": rows, "count": len(rows)}
if a.baseline:
    before = json.loads(Path(a.baseline).read_text())
    result["baseline_sha256"] = before["generator_sha256"]
    result["unchanged_count"] = sum(x == y for x, y in zip(before["valid_draws"], rows))
    result["same_draws"] = before["valid_draws"] == rows
Path(a.out).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "valid_draws"}, indent=2))
if a.baseline:
    assert result["same_draws"], "valid scheduled or exact-override draws changed"
