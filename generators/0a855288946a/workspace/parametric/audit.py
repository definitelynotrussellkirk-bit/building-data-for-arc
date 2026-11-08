"""Bounded, reusable teaching audit for the rotation-scope family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HERE = Path(__file__).resolve().parent
_NATIVE_PATH = HERE / "native.py"
_NAME = "_rotation_scope_audit_native_" + hashlib.sha256(str(_NATIVE_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _NATIVE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_NATIVE_PATH)
native = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = native
_SPEC.loader.exec_module(native)


def run_audit(seeds: Iterable[int]) -> dict:
    seeds = list(seeds)
    harmful = []
    matched_failures = []
    prefix_failures = []
    survivor_histogram: dict[str, int] = {}
    episodes = 0
    labeled_pairs = 0
    for seed in seeds:
        full_by_scope = {
            scope: native.generate(seed, {"rotation_scope": scope}, 6, 4)
            for scope in native.SETTINGS
        }
        if [p["input"] for p in full_by_scope[native.SETTINGS[0]]["train"]] != [
                p["input"] for p in full_by_scope[native.SETTINGS[1]]["train"]]:
            matched_failures.append({"seed": seed, "split": "train"})
        if [p["input"] for p in full_by_scope[native.SETTINGS[0]]["test"]] != [
                p["input"] for p in full_by_scope[native.SETTINGS[1]]["test"]]:
            matched_failures.append({"seed": seed, "split": "test"})
        for scope in native.SETTINGS:
            short = native.generate(seed, {"rotation_scope": scope}, 2, 1)
            if short["test"] != full_by_scope[scope]["test"][:1]:
                prefix_failures.append({"seed": seed, "scope": scope})
            for demos in range(2, 7):
                episode = native.generate(seed, {"rotation_scope": scope}, demos, 4)
                episodes += 1
                labeled_pairs += demos + 4
                survivors = [
                    name for name in native.RIVAL_NAMES
                    if all(native.rival_output(pair["input"], name) == pair["output"]
                           for pair in episode["train"])
                ]
                key = ",".join(survivors)
                survivor_histogram[key] = survivor_histogram.get(key, 0) + 1
                for rival in survivors:
                    if rival == scope:
                        continue
                    disagreements = [
                        index for index, pair in enumerate(episode["test"])
                        if native.rival_output(pair["input"], rival) != pair["output"]
                    ]
                    if disagreements:
                        harmful.append({
                            "seed": seed,
                            "scope": scope,
                            "demos": demos,
                            "rival": rival,
                            "query_disagreements": disagreements,
                        })
    return {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": "0a855288946a",
        "status": "passed" if not harmful and not matched_failures and not prefix_failures else "failed",
        "seed_count": len(seeds),
        "demo_counts": [2, 3, 4, 5, 6],
        "query_count": 4,
        "settings": list(native.SETTINGS),
        "rivals": list(native.RIVAL_NAMES),
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "survivor_histogram": dict(sorted(survivor_histogram.items())),
        "harmful_survivors": harmful,
        "matched_input_failures": matched_failures,
        "prefix_failures": prefix_failures,
        "limits": "Finite declared rivals and requested seeds only; not a proof against every possible rule.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=128, help="audit seeds 0..N-1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.seeds <= 4096:
        parser.error("--seeds must be in 1..4096")
    report = run_audit(range(args.seeds))
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "episodes", "labeled_pairs")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
