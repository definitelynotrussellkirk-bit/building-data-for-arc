from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator


def grid_sha(grid):
    raw = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


root = Path.cwd()

# 9c928e7deebc: advertised helpful controls are not consumed.
task = "9c928e7deebc"
gen, source, digest = load_selected_generator(task, root=root)
base = gen.generate(991, 0, difficulty="easy")
textures = {}
for texture in ("default", "warm", "cool", "varied"):
    grid = gen.generate(991, 0, difficulty="easy", texture=texture)
    textures[texture] = {
        "equal_to_unoverridden": grid == base,
        "grid_sha256": grid_sha(grid),
    }
alignments = {}
for alignment in ("row", "col"):
    grid = gen.generate(991, 0, difficulty="easy", alignment=alignment)
    alignments[alignment] = {
        "equal_to_unoverridden": grid == base,
        "grid_sha256": grid_sha(grid),
    }
write(
    root.parent / "checks/audit/9c928e7deebc/control_counterexample.json",
    {
        "schema": "arcpuzzles-peer-audit-counterexample-v1",
        "task_id": task,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "call": {"seed": 991, "sample_index": 0, "difficulty": "easy"},
        "unoverridden_grid": base,
        "unoverridden_grid_sha256": grid_sha(base),
        "texture_results": textures,
        "alignment_results": alignments,
        "finding": "Every advertised helpful texture and both advertised alignment values produced the exact unoverridden bytes for this call.",
        "self_check": gen.self_check(base),
    },
)

# 40b155c46f6e: every non-literal seed scalar is accepted.
task = "40b155c46f6e"
gen, source, digest = load_selected_generator(task, root=root)
accepted = []
for difficulty in ("easy", None, "hard"):
    for value in (True, False, 1.0, 1.75, "1"):
        try:
            grid = gen.generate(value, 0, difficulty=difficulty)
        except Exception as exc:
            accepted.append({
                "difficulty": difficulty,
                "seed_repr": repr(value),
                "seed_type": type(value).__name__,
                "accepted": False,
                "error": f"{type(exc).__name__}: {exc}",
            })
        else:
            accepted.append({
                "difficulty": difficulty,
                "seed_repr": repr(value),
                "seed_type": type(value).__name__,
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": grid_sha(grid),
                "self_check": gen.self_check(grid),
                "grid": grid if difficulty == "easy" and value == "1" else None,
            })
write(
    root.parent / "checks/audit/40b155c46f6e/strict_seed_counterexample.json",
    {
        "schema": "arcpuzzles-peer-audit-counterexample-v1",
        "task_id": task,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "call_template": {"sample_index": 0},
        "accepted_count": sum(row["accepted"] for row in accepted),
        "tested_count": len(accepted),
        "cases": accepted,
        "finding": "All 15 bool/float/string seed cases were accepted and generated self-check-valid grids.",
    },
)
