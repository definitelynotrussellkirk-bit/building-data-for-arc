#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

EXPECTED = {
    "df74e338b4f5": "374fbf52b1f9c4606bffd2541c27a15c3c703285c23b8b77919261c705853d00",
    "204213f10aff": "9a459ef53fba3bfde7f64d0adcd117203965346408cd612193048126c21b52b2",
}


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == EXPECTED[task_id], (task_id, digest)
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, digest


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def nested_frame_counterexample():
    # Three concentric frames, each one blank-cell ring apart, but inset one cell
    # from a 15x15 canvas.  A center marker is inside all 3 frames.
    h = w = 15
    g = [[0 for _ in range(w)] for _ in range(h)]
    for lo, hi in [(1, 13), (3, 11), (5, 9)]:
        for c in range(lo, hi + 1):
            g[lo][c] = 9
            g[hi][c] = 9
        for r in range(lo, hi + 1):
            g[r][lo] = 9
            g[r][hi] = 9
    g[7][7] = 1
    return g


def sparse_legend_counterexample():
    return [
        [2, 0, 4, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 4, 4, 0, 0],
        [0, 0, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def main():
    manifest = {"schema": "audit-input-build-v1", "targets": {}}
    for task_id in EXPECTED:
        mod, digest = load(task_id)
        target_dir = ROOT / "checks" / "audit" / task_id
        if task_id == "df74e338b4f5":
            custom = nested_frame_counterexample()
            validation = {
                "self_check_present": hasattr(mod, "self_check"),
                "self_check_errors": None,
                "documented_domain": (
                    "three concentric rectangular color-9 frames, one blank-cell ring apart; "
                    "a non-{0,9} marker lies in a valid 0-cell"
                ),
            }
            samples = [mod.generate("audit-default-df-v1", i) for i in range(64)]
            sample_meta = {
                "seed": "audit-default-df-v1",
                "sample_indices": [0, 63],
                "difficulty": None,
                "overrides": {},
            }
        else:
            custom = sparse_legend_counterexample()
            validation = {
                "self_check_present": hasattr(mod, "self_check"),
                "self_check_errors": mod.self_check(custom) if hasattr(mod, "self_check") else None,
                "documented_domain": (
                    "row 0 lists colors 2 then 4 with a legal zero gap; each has one separated "
                    "connected body component below the legend"
                ),
            }
            # Mix all difficulty entry points while retaining the generator's default axis behavior.
            specs = [("easy", i) for i in range(16)] + [(None, i) for i in range(16, 48)] + [("hard", i) for i in range(48, 64)]
            samples = [mod.generate("audit-prefix-legend-v1", i, difficulty=d) for d, i in specs]
            sample_meta = {
                "seed": "audit-prefix-legend-v1",
                "sample_indices": [0, 63],
                "difficulty_counts": {"easy": 16, "default": 32, "hard": 16},
                "overrides": {},
            }
        write(target_dir / "input.json", custom)
        write(target_dir / "generated-inputs.json", {"inputs": samples})
        manifest["targets"][task_id] = {
            "generator_sha256": digest,
            "counterexample_validation": validation,
            "generated_sample": sample_meta,
            "generated_input_count": len(samples),
        }
    write(ROOT / "checks" / "audit" / "input-build-manifest.json", manifest)


if __name__ == "__main__":
    main()
