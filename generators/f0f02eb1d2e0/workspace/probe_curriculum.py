#!/usr/bin/env python3
"""Source-bound curriculum and override probe for f0f02eb1d2e0.

Run from the repository root with:
  PYTHONPATH=shared/runtime python3 generators/f0f02eb1d2e0/workspace/probe_curriculum.py \
      --out ../checks/f0f02eb1d2e0-curriculum-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
from typing import Any

TASK_ID = "f0f02eb1d2e0"
BANDS = ("easy", "medium", "hard")
AXIS_BOUNDARIES = {
    "grid_h": (6, 12),
    "grid_w": (9, 14),
    "n_targets": (1, 4),
    "n_bent_decoys": (0, 2),
    "n_other_decoys": (0, 2),
    "corner_offset": (0, 3),
}


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "shared" / "data" / "canonical" / "puzzles.jsonl").exists():
            return parent
    raise RuntimeError("repository root not found")


def _load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _canonical_pairs(root: Path) -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs
    return canonical_pairs(TASK_ID, root=root)


def _pair(gen, seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = _repo_root()
    gen, source = _load_generator(root)
    failures: list[dict[str, Any]] = []

    canonical = _canonical_pairs(root)
    canonical_shortcut_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fit = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_shortcut_fit[name] = fit
        if not all(fit):
            failures.append({"kind": "canonical_shortcut_misdeclared", "rival": name, "fit": fit})

    override_cases = 0
    for case_index, values in enumerate(itertools.product(*AXIS_BOUNDARIES.values())):
        overrides = dict(zip(AXIS_BOUNDARIES, values))
        band = BANDS[case_index % len(BANDS)]
        grid = gen.generate(9100 + case_index, 1000 + case_index, difficulty=band, **overrides)
        override_cases += 1
        findings = gen.self_check(grid, difficulty=band, meta={"overrides": overrides})
        observed = gen.observe_overrides(grid)
        if findings or observed != overrides:
            failures.append({
                "kind": "override_case",
                "case_index": case_index,
                "band": band,
                "overrides": overrides,
                "observed": observed,
                "findings": findings,
            })

    lesson_windows = 0
    query_rotations = 0
    rival_refutations = {name: 0 for name in gen.LESSON_COMPETITORS}
    for band_index, band in enumerate(BANDS):
        for start in range(4):
            pairs = [_pair(gen, 7000 + 100 * band_index + start, start + offset, band) for offset in range(4)]
            lesson_windows += 1
            for name, rival in gen.LESSON_COMPETITORS.items():
                disagreements = sum(rival(pair["input"]) != pair["output"] for pair in pairs)
                rival_refutations[name] += disagreements
                if disagreements < 2:
                    failures.append({
                        "kind": "weak_window_refutation",
                        "band": band,
                        "start": start,
                        "rival": name,
                        "disagreements": disagreements,
                    })
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query_rotations += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({
                        "kind": "ambiguous_rotation",
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    })

    result = {
        "schema": "f0f02eb1d2e0-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "joint_override_boundary_cases": override_cases,
        "lesson_windows": lesson_windows,
        "query_rotations": query_rotations,
        "rival_refutation_counts": rival_refutations,
        "failures": failures,
        "passed": not failures,
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": result["passed"],
        "joint_override_boundary_cases": override_cases,
        "lesson_windows": lesson_windows,
        "query_rotations": query_rotations,
        "failures": len(failures),
        "out": str(out),
    }, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
