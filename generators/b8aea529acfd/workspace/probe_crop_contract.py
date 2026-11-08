#!/usr/bin/env python3
"""Fast, source-bound crop-shortcut census; Python mirror labels, not authority.

Run through the packet's runtime wrapper. The public lesson-census command is
the separate Racket-backed check for production lessons and query rotations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "b8aea529acfd"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[7301, 91327])
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.out.exists():
        parser.error("Choose a new --out path to preserve earlier evidence")
    root = find_root(__file__)
    source = next(path for path in (
        root / "generators" / TASK / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ) if path.is_file())
    spec = importlib.util.spec_from_file_location("crop_probe_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    rivals = gen.CANONICAL_SHORTCUTS
    canonical_fit = {
        name: {"matched": sum(rival(pair["input"]) == pair["output"] for pair in pairs),
               "total": len(pairs)}
        for name, rival in rivals.items()
    }
    report = {
        "schema": "b8aea529acfd-crop-contract-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_data_sha256": hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "labels": "Canonical pairs use retained labels; generated census uses Python rule_mirror only.",
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "seeds": args.seeds, "sample_index_range_inclusive": [0, args.per_band - 1],
        "canonical_fit": canonical_fit, "runs": [], "first_witnesses": {}, "failures": [],
    }
    all_inputs = set()
    for seed in args.seeds:
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            profiles = Counter()
            unique = set()
            for index in range(args.per_band):
                grid = gen.generate(seed, index, difficulty=band)
                input_hash = digest(grid)
                unique.add(input_hash)
                all_inputs.add(input_hash)
                counts["draws"] += 1
                errors = gen.self_check(grid) + gen.strict_canonical_like(grid)
                if errors:
                    report["failures"].append({"seed": seed, "band": band,
                                               "sample_index": index, "input": grid,
                                               "errors": errors})
                facts = gen.semantic_observables(grid)
                profiles[str(facts.get("scene_profile"))] += 1
                expected = gen.rule_mirror(grid)
                disagreements = []
                for name, rival in rivals.items():
                    predicted = rival(grid)
                    if predicted != expected:
                        disagreements.append(name)
                        counts[name] += 1
                        report["first_witnesses"].setdefault(name, {
                            "seed": seed, "band": band, "sample_index": index,
                            "input_sha256": input_hash, "input": grid,
                            "python_mirror_output": expected, "rival_output": predicted,
                            "observables": facts,
                        })
                if len(disagreements) == len(rivals) and rivals:
                    counts["all_canonical_shortcuts_refuted"] += 1
            report["runs"].append({"seed": seed, "band": band, "counts": dict(counts),
                                   "unique_inputs": len(unique), "profiles": dict(profiles)})
    report["total_draws"] = sum(run["counts"]["draws"] for run in report["runs"])
    report["unique_inputs"] = len(all_inputs)
    valid = bool(rivals) and all(row["matched"] == row["total"] for row in canonical_fit.values())
    report["status"] = "passed_finite_python_probe" if valid and not report["failures"] else "failed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "total_draws", "unique_inputs")}))
    return 0 if report["status"] == "passed_finite_python_probe" else 1


if __name__ == "__main__":
    raise SystemExit(main())
