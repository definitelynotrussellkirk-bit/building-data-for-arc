#!/usr/bin/env python3
"""Bounded executable rival audit for the composition-order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HOME = Path(__file__).resolve().parent
NATIVE = HOME / "native.py"
_name = "_composition_order_audit_native_" + hashlib.sha256(str(NATIVE).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, NATIVE)
if _spec is None or _spec.loader is None:
    raise ImportError(NATIVE)
native = importlib.util.module_from_spec(_spec)
sys.modules[_name] = native
_spec.loader.exec_module(native)


def run_audit(seeds: Iterable[int]) -> dict:
    """Audit the full finite lesson bank without regenerating it per prefix.

    Generation determinism/prefix behavior is sampled once per setting/seed;
    all five supported demo counts are then audited as literal prefixes of the
    same source-bound six-demo bank.  This keeps 128-seed audits fast enough for
    packet launchers while retaining the same rival coverage.
    """
    seeds = list(seeds)
    harmful = []
    matched_failures = []
    prefix_failures = []
    label_failures = []
    episodes = 0
    labeled_pairs = 0
    for seed in seeds:
        full = {
            setting: native.generate(seed, {"composition_order": setting}, 6, 4)
            for setting in native.SETTINGS
        }
        for split in ("train", "test"):
            left = [pair["input"] for pair in full[native.SETTINGS[0]][split]]
            right = [pair["input"] for pair in full[native.SETTINGS[1]][split]]
            if left != right:
                matched_failures.append({"seed": seed, "split": split})
        for setting in native.SETTINGS:
            baseline = full[setting]
            short = native.generate(seed, {"composition_order": setting}, 2, 1)
            if short["train"] != baseline["train"][:2] or short["test"] != baseline["test"][:1]:
                prefix_failures.append({"seed": seed, "setting": setting,
                                        "kind": "minimum-prefix"})
            for pair in baseline["train"] + baseline["test"]:
                if native.transform(pair["input"], setting) != pair["output"]:
                    label_failures.append({"seed": seed, "setting": setting})
            for demos in range(2, 7):
                train = baseline["train"][:demos]
                episodes += 1
                labeled_pairs += demos + 4
                survivors = [
                    name for name in native.RIVAL_NAMES
                    if all(native.rival_output(pair["input"], name) == pair["output"]
                           for pair in train)
                ]
                if survivors != [setting]:
                    harmful.append({"seed": seed, "setting": setting,
                                    "demos": demos, "survivors": survivors})
    status = "passed" if not (harmful or matched_failures or prefix_failures or label_failures) else "failed"
    return {
        "schema": "arcpuzzles-parametric-rival-audit-v1",
        "task_id": "974fee515740",
        "status": status,
        "seeds": seeds,
        "settings": list(native.SETTINGS),
        "demo_counts": [2, 3, 4, 5, 6],
        "query_count": 4,
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "rivals": list(native.RIVAL_NAMES),
        "harmful_survivors": harmful,
        "matched_input_failures": matched_failures,
        "prefix_failures": prefix_failures,
        "label_failures": label_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")
    report = run_audit(range(args.seeds))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
