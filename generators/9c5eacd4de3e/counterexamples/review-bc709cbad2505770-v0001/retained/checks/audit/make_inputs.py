from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path[:0] = [str(REPO), str(REPO / "src"), str(REPO / "shared" / "runtime")]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_record(task_id: str) -> dict:
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == task_id:
                return record
    raise KeyError(task_id)


def decode(rows: list[str]) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in rows]


# 2f889ed81450: 63 ordinary samples plus one canonical boundary witness.
task = "2f889ed81450"
module = importlib.import_module(f"generators.{task}.generator")
ordinary = []
ordinary_meta = []
for sample_index in range(63):
    grid = module.generate(20261007, sample_index, difficulty="medium")
    errors = module.self_check(grid, difficulty="medium")
    seeds = [(r, c, grid[r][c]) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != 0]
    margins = [min(r, c, len(grid) - 1 - r, len(grid[0]) - 1 - c) for r, c, _ in seeds]
    ordinary.append(grid)
    ordinary_meta.append({
        "sample_index": sample_index,
        "self_check": errors,
        "seed_count": len(seeds),
        "minimum_border_margin": min(margins),
    })
record = canonical_record(task)
edge_witness = decode(record["train"][0]["input"])
inputs = ordinary + [edge_witness]
out_dir = PACKET / "checks/audit" / task
(out_dir / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(out_dir / "generation.json").write_text(json.dumps({
    "task_id": task,
    "generator_sha256": sha256(REPO / f"generators/{task}/generator.py"),
    "seed": 20261007,
    "difficulty": "medium",
    "ordinary_sample_indices": [0, 62],
    "ordinary": ordinary_meta,
    "witness": {
        "kind": "canonical_train_0",
        "self_check": module.self_check(edge_witness, difficulty="medium"),
        "belongs_to_documented_default_domain": False,
        "reason": "seed at row 1 has an out-of-bounds distance-2 ray; default generation forces margin >=2",
    },
}, indent=2) + "\n")

# 9c5eacd4de3e: exact three-demo/one-query spatial-order shortcut lesson.
task = "9c5eacd4de3e"
module = importlib.import_module(f"generators.{task}.generator")
inputs = []
meta = []
for sample_index in range(4):
    grid = module.generate(97, sample_index, difficulty="medium")
    inputs.append(grid)
    meta.append({
        "sample_index": sample_index,
        "self_check": module.self_check(grid, difficulty="medium"),
        "shape": [len(grid), len(grid[0])],
    })
out_dir = PACKET / "checks/audit" / task
(out_dir / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(out_dir / "generation.json").write_text(json.dumps({
    "task_id": task,
    "generator_sha256": sha256(REPO / f"generators/{task}/generator.py"),
    "seed": 97,
    "difficulty": "medium",
    "sample_indices": [0, 1, 2, 3],
    "samples": meta,
}, indent=2) + "\n")
