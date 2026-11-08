from __future__ import annotations
import hashlib, importlib, json, sys
from pathlib import Path

packet = Path(__file__).resolve().parents[3]
repo = packet / "repo"
sys.path[:0] = [str(repo / "shared/runtime"), str(repo)]
task = "526efe994f76"
mod = importlib.import_module(f"generators.{task}.generator")
source_hash = hashlib.sha256((repo / "generators" / task / "generator.py").read_bytes()).hexdigest()
inputs, entries = [], []
for sample_index in range(10, 15):
    grid = mod.generate(1, sample_index, difficulty="easy")
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    assert len(anchors) == 1
    entries.append({"sample_index": sample_index, "anchor": list(anchors[0]),
                    "anchor_parity": sum(anchors[0]) % 2,
                    "self_check_errors": mod.self_check(grid, difficulty="easy")})
    inputs.append(grid)
out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
probe = {"schema": "arcpuzzles-audit-probe-v1", "task_id": task, "generator_sha256": source_hash,
         "seed": 1, "difficulty": "easy", "sample_indices": list(range(10, 15)), "entries": entries}
(out_dir / "probe.json").write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
print(json.dumps(probe, sort_keys=True))
