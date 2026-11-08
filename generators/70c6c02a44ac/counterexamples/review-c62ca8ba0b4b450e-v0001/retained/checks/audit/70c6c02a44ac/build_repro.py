from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "70c6c02a44ac"
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo" / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

seed = 3301
sample_indices = [1, 2, 3, 4]
grids = [module.generate(seed, index, difficulty="medium") for index in sample_indices]
checks = [module.self_check(grid) for grid in grids]
assert checks == [[], [], [], []]
profiles = [module.schedule_profile(seed, index, "medium") for index in sample_indices]
assert profiles == ["inside", "inside", "clipped", "inside"]

rival_outputs = [module._discard_clipped_anchor_rival(grid) for grid in grids]
(OUT / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
(OUT / "rival-output.json").write_text(json.dumps(rival_outputs, indent=2) + "\n")
(OUT / "repro-metadata.json").write_text(
    json.dumps(
        {
            "schema": "arcpuzzles-audit-reproducer-v1",
            "task_id": TASK,
            "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "rule_hash": module.RULE_HASH,
            "seed": seed,
            "sample_indices": sample_indices,
            "difficulty": "medium",
            "schedule_profiles": profiles,
            "self_check": checks,
            "lesson": {
                "query_list_index": 2,
                "query_sample_index": 3,
                "demo_list_indices": [0, 1, 3],
                "demo_sample_indices": [1, 2, 4],
            },
            "rival": "discard anchors whose copies cross the boundary",
            "claim": (
                "The three rotated demonstrations are all fully inside, so the rival "
                "matches them; the held-out clipped query differs."
            ),
            "generation_command": {
                "cwd": "repo",
                "argv": ["python3", "../checks/audit/70c6c02a44ac/build_repro.py"],
            },
            "racket_command": {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
                    TASK, "--input", "../checks/audit/70c6c02a44ac/input.json",
                    "--out", "../checks/audit/70c6c02a44ac/racket.json",
                ],
            },
        },
        indent=2,
        sort_keys=True,
    )
    + "\n"
)
