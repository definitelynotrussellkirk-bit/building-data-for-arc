#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "401026bab1f6"
_START = Path(__file__).resolve()
ROOT = next(
    candidate
    for parent in _START.parents
    for candidate in (parent, parent / "repo")
    if (candidate / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file()
)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
OUTDIR = ROOT.parent / "checks" / "audit" / TASK_ID

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def reflect_only_frames_with_two_marks(grid):
    analysis = GEN._analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    out = [row[:] for row in grid]
    for frame in analysis["frames"]:
        if len(frame["marks"]) < 2:
            continue
        r0, _c0, r1, _c1 = frame["bbox"]
        for r, c in frame["marks"]:
            mr = r0 + r1 - r
            if out[mr][c] == 0:
                out[mr][c] = 7
    return out


canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
canonical_frame_mark_counts = []
canonical_rival_fits = True
for pair in canonical:
    analysis = GEN._analyze(pair["input"])
    canonical_frame_mark_counts.append([len(frame["marks"]) for frame in analysis["frames"]])
    canonical_rival_fits &= reflect_only_frames_with_two_marks(pair["input"]) == pair["output"]

generated_min_marks = 999
ordinary_rival_fits = True
ordinary_count = 0
for band in ("easy", "medium", "hard"):
    for seed in range(20):
        for sample_index in range(16):
            grid = GEN.generate(seed, sample_index, difficulty=band)
            analysis = GEN._analyze(grid)
            generated_min_marks = min(
                generated_min_marks,
                *(len(frame["marks"]) for frame in analysis["frames"]),
            )
            ordinary_rival_fits &= reflect_only_frames_with_two_marks(grid) == GEN.rule_mirror(grid)
            ordinary_count += 1

base = GEN.generate(
    7331,
    0,
    difficulty="medium",
    grid_h=12,
    grid_w=12,
    n_frames=1,
    pattern_mode="top_only",
)
analysis = GEN._analyze(base)
marks = sorted(analysis["frames"][0]["marks"])
singleton = [row[:] for row in base]
for r, c in marks[1:]:
    singleton[r][c] = 0
single_analysis = GEN._analyze(singleton)
intended = GEN.rule_mirror(singleton)
rival = reflect_only_frames_with_two_marks(singleton)

report = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "candidate_rival": "reflect only frames containing at least two color-4 marks",
    "canonical_pairs": len(canonical),
    "canonical_frame_mark_counts": canonical_frame_mark_counts,
    "canonical_rival_fits": canonical_rival_fits,
    "ordinary_generated_checked": ordinary_count,
    "ordinary_min_marks_per_frame": generated_min_marks,
    "ordinary_rival_fits": ordinary_rival_fits,
    "counterexample": {
        "self_check": GEN.self_check(singleton),
        "frame_mark_counts": [len(frame["marks"]) for frame in single_analysis["frames"]],
        "input": singleton,
        "intended_output_python_mirror": intended,
        "rival_output": rival,
        "disagrees": intended != rival,
    },
}
OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / "singleton_input.json").write_text(json.dumps({"input": singleton}, indent=2) + "\n")
(OUTDIR / "singleton_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if canonical_rival_fits and ordinary_rival_fits and intended != rival and not report["counterexample"]["self_check"] else 1)
