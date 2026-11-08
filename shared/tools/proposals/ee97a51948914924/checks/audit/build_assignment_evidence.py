#!/usr/bin/env python3
"""Build source-bound peer-audit evidence without editing audit targets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]

from reviewer_support import canonical_pairs, load_selected_generator  # noqa: E402

EXPECTED = {
    "8a67cd7d5f1e": "5bb99d91dbea1967437c94cff58e69a115bfe43a53d58b094ed8ad7f868ef56c",
    "58cd4c4a5bd4": "a11cf32f701aae8d64170b3a9e1e924042f49a2be92fbd9e8154f839fe9b8e12",
}
BANDS = ("easy", "medium", "hard")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(grid):
    return [len(grid), len(grid[0]), len({v for row in grid for v in row})]


def center_mirror_rival(grid):
    """Wrong rule: reflect marks around the geometric grid midpoint, not guide."""
    out = [row[:] for row in grid]
    w = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                nc = w - 1 - c
                if 0 <= nc < w:
                    out[r][nc] = value
    return out


def guide_axis_output_python(grid):
    """Independent readable oracle mirroring around first full color-5 column."""
    h, w = len(grid), len(grid[0])
    guide_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not guide_cols:
        return [row[:] for row in grid]
    p = guide_cols[0]
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                nc = 2 * p - c
                if 0 <= nc < w:
                    out[r][nc] = value
    return out


def main():
    assignment = json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())
    assert {x["task_id"]: x["generator_sha256"] for x in assignment["targets"]} == EXPECTED
    for task_id, expected_hash in EXPECTED.items():
        module, source, actual_hash = load_selected_generator(task_id, root=REPO)
        if actual_hash != expected_hash:
            raise RuntimeError(f"{task_id} changed: {actual_hash} != {expected_hash}")
        pairs = canonical_pairs(task_id, root=REPO, labeled_only=True)
        canonical_profiles = sorted({tuple(profile(p["input"])) for p in pairs})
        hvals = [p[0] for p in canonical_profiles]
        wvals = [p[1] for p in canonical_profiles]
        cvals = [p[2] for p in canonical_profiles]
        samples = []
        generated_inputs = []
        for band in BANDS:
            for seed in range(20):
                grid = module.generate(seed, 0, difficulty=band)
                generated_inputs.append(grid)
                pr = profile(grid)
                exact = tuple(pr) in set(canonical_profiles)
                envelope = (min(hvals) <= pr[0] <= max(hvals)
                            and min(wvals) <= pr[1] <= max(wvals)
                            and min(cvals) <= pr[2] <= max(cvals))
                samples.append({
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": 0,
                    "profile": pr,
                    "exact_profile": exact,
                    "canonical_envelope": envelope,
                    "self_check": module.self_check(grid, difficulty=band),
                    "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
                })
        canonical_validation = []
        for p in pairs:
            canonical_validation.append({
                "split": p["split"],
                "pair_index": p["pair_index"],
                "profile": profile(p["input"]),
                "self_check": module.self_check(p["input"]),
                "input": p["input"],
                "expected_output": p["output"],
            })
        base = module.generate(0, 0, difficulty="easy")
        if task_id == "8a67cd7d5f1e":
            probes = [
                {"palette_kind": "warm"}, {"palette_kind": "cool"},
                {"n": 2}, {"n": 5}, {"palette_size": 2}, {"palette_size": 7},
                {"n_distinct_colors": 2}, {"n_distinct_colors": 7},
                {"density": "sparse"}, {"position_bias": "spread_motifs"},
            ]
        else:
            probes = [
                {"palette_kind": "warm"}, {"palette_kind": "cool"},
                {"num_marks": 2}, {"num_marks": 3},
                {"n_distinct_colors": 1}, {"n_distinct_colors": 8},
            ]
        override_results = []
        for override in probes:
            try:
                got = module.generate(0, 0, difficulty="easy", **override)
                override_results.append({
                    "override": override,
                    "accepted": True,
                    "identical_to_default": got == base,
                    "profile": profile(got),
                    "self_check": module.self_check(got, difficulty="easy"),
                })
            except Exception as exc:
                override_results.append({
                    "override": override,
                    "accepted": False,
                    "exception": f"{type(exc).__name__}: {exc}",
                })
        report = {
            "schema": "arcpuzzles-peer-audit-profile-v1",
            "assignment_id": "review-d01b80b6a0de81c7",
            "target_task_id": task_id,
            "generator_path": str(source.relative_to(REPO)),
            "generator_sha256": actual_hash,
            "generator_rule_hash": getattr(module, "RULE_HASH", None),
            "canonical_profiles": [list(x) for x in canonical_profiles],
            "canonical_pair_count": len(pairs),
            "canonical_validation": canonical_validation,
            "sampling": {
                "policy": "difficulty in easy,medium,hard; seed 0..19; sample_index 0",
                "denominator": len(samples),
                "exact_profile_hits": sum(s["exact_profile"] for s in samples),
                "canonical_envelope_hits": sum(s["canonical_envelope"] for s in samples),
                "unique_input_hashes": len({s["input_sha256"] for s in samples}),
                "observed_profiles": sorted({tuple(s["profile"]) for s in samples}),
                "samples": samples,
            },
            "override_probes": override_results,
            "command": ["python3", "checks/audit/build_assignment_evidence.py"],
            "cwd": "WORK",
        }
        if task_id == "58cd4c4a5bd4":
            report["semantic_rival"] = {
                "name": "mirror_across_geometric_grid_midpoint",
                "description": "Use c' = width - 1 - c, ignoring the color-5 guide coordinate.",
                "generated_python_matches": sum(
                    center_mirror_rival(g) == guide_axis_output_python(g) for g in generated_inputs
                ),
                "generated_denominator": len(generated_inputs),
                "canonical_matches": sum(
                    center_mirror_rival(p["input"]) == p["output"] for p in pairs
                ),
                "canonical_denominator": len(pairs),
            }
            (HERE / task_id / "generated-inputs.json").write_text(
                json.dumps({"inputs": generated_inputs}, indent=2) + "\n"
            )
        out_dir = HERE / task_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "profile-and-contract.json").write_text(json.dumps(report, indent=2) + "\n")
        print(task_id, json.dumps({
            "sha": actual_hash,
            "exact": report["sampling"]["exact_profile_hits"],
            "envelope": report["sampling"]["canonical_envelope_hits"],
            "canonical_rejected": sum(bool(x["self_check"]) for x in canonical_validation),
            "rival": report.get("semantic_rival"),
        }))


if __name__ == "__main__":
    main()
