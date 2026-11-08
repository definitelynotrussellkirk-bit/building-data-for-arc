#!/usr/bin/env python3
"""Bounded learnability and boundary audit for the native selector family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_selector_native_audit_adapter", HERE / "adapter.py")
adapter = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(adapter)


def run_audit(*, seeds=range(64)):
    seed_values = list(seeds)
    failures = []
    sizes = set()
    episodes = 0
    pairs = 0
    for seed in seed_values:
        for demos in range(2, 7):
            for mode in adapter.SETTINGS:
                episodes += 1
                try:
                    episode = adapter.generate(seed, {adapter.PARAMETER: mode}, demos, 4)
                    findings = adapter.teaching_check(episode)
                    if findings:
                        failures.append({"seed": seed, "demos": demos, "setting": mode, "findings": findings})
                    all_pairs = episode["train"] + episode["test"]
                    pairs += len(all_pairs)
                    if len({json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs}) != len(all_pairs):
                        failures.append({"seed": seed, "demos": demos, "setting": mode, "error": "duplicate input"})
                    for pair in all_pairs:
                        grid = pair["input"]
                        sizes.add((len(grid), len(grid[0])))
                        if adapter.claim(grid, mode) != pair["output"]:
                            failures.append({"seed": seed, "demos": demos, "setting": mode, "error": "claim mismatch"})
                except Exception as exc:  # retained as evidence instead of hiding a failed draw
                    failures.append({"seed": seed, "demos": demos, "setting": mode, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": adapter.TASK,
        "status": "passed" if not failures else "failed",
        "seeds": len(seed_values),
        "settings": list(adapter.SETTINGS),
        "demo_counts": list(range(2, 7)),
        "queries": 4,
        "episodes": episodes,
        "labeled_pairs_claims": pairs,
        "rivals": list(adapter.RIVALS),
        "sizes": [list(size) for size in sorted(sizes)],
        "failures": failures,
        "limits": "Finite declared rivals and bounded seeds; not universal rule uniqueness or owner acceptance.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        raise SystemExit("--seeds must be in 1..4096")
    result = run_audit(seeds=range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "episodes", "labeled_pairs_claims", "failures")}, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
