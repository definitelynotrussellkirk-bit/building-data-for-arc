#!/usr/bin/env python3
"""Bounded learnability and boundary audit for future reviewers."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_dfc7297269cc_audit_target", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise SystemExit("cannot load prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")

    failures = []
    episodes = 0
    pairs = 0
    exact_30 = 0
    setting_differences = 0
    for seed in range(args.seeds):
        for demos in (2, 3, 6):
            for queries in (1, 4):
                generated = {
                    setting: P.generate(seed, {P.PARAMETER: setting}, demos, queries)
                    for setting in P.SETTINGS
                }
                episodes += len(P.SETTINGS)
                pairs += len(P.SETTINGS) * (demos + queries)
                left, right = (generated[setting] for setting in P.SETTINGS)
                left_inputs = [pair["input"] for split in ("train", "test") for pair in left[split]]
                right_inputs = [pair["input"] for split in ("train", "test") for pair in right[split]]
                if left_inputs != right_inputs:
                    failures.append({"seed": seed, "demos": demos, "queries": queries, "error": "setting-confounded inputs"})
                for setting, episode in generated.items():
                    survivors = P.surviving_rivals(episode["train"], setting)
                    if survivors:
                        failures.append({"seed": seed, "demos": demos, "queries": queries, "setting": setting, "survivors": survivors})
                    for pair in episode["test"]:
                        if (len(pair["input"]), len(pair["input"][0])) == (30, 30):
                            exact_30 += 1
                setting_differences += sum(
                    a["output"] != b["output"]
                    for split in ("train", "test")
                    for a, b in zip(left[split], right[split])
                )

    report = {
        "schema": "dfc7297269cc-parametric-audit-v1",
        "seeds": args.seeds,
        "episodes": episodes,
        "pairs": pairs,
        "exact_30_pairs": exact_30,
        "setting_answer_differences": setting_differences,
        "failures": failures,
        "passed": not failures,
        "limits": "finite deterministic sweep over seeds and declared rivals; not a universal identifiability proof",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
