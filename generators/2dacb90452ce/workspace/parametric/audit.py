#!/usr/bin/env python3
"""Finite self-review for the native 2dacb90452ce modal-parity family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_2dac_audit_family", HERE / "native.py")
if SPEC is None or SPEC.loader is None:
    raise SystemExit("cannot load native.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")

    failures = []
    episodes = pairs = exact_30 = differences = 0
    for seed in range(args.seeds):
        for demos in (2, 3, 6):
            generated = {
                setting: F.generate(seed, {F.PARAMETER: setting}, demos, 4)
                for setting in F.SETTINGS
            }
            episodes += len(F.SETTINGS)
            pairs += len(F.SETTINGS) * (demos + 4)
            left, right = (generated[setting] for setting in F.SETTINGS)
            left_inputs = [p["input"] for p in left["train"] + left["test"]]
            right_inputs = [p["input"] for p in right["train"] + right["test"]]
            if left_inputs != right_inputs:
                failures.append({"seed": seed, "demos": demos, "error": "setting-confounded inputs"})
            for setting, episode in generated.items():
                survivors = F.surviving_rivals(episode["train"], setting)
                if survivors:
                    failures.append({"seed": seed, "demos": demos, "setting": setting, "survivors": survivors})
                for pair in episode["test"]:
                    if (len(pair["output"]), len(pair["output"][0])) == (30, 30):
                        exact_30 += 1
            differences += sum(
                a["output"] != b["output"]
                for split in ("train", "test")
                for a, b in zip(left[split], right[split])
            )

    report = {
        "schema": "2dacb90452ce-native-parametric-audit-v1",
        "seeds": args.seeds,
        "episodes": episodes,
        "pairs": pairs,
        "exact_30_outputs": exact_30,
        "setting_answer_differences": differences,
        "declared_rivals": sorted(F.rival_outputs(F.generate(0, {F.PARAMETER: "fixed_two"}, 2, 4)["train"][0]["input"], "fixed_two")),
        "failures": failures,
        "passed": not failures,
        "limits": "finite deterministic sweep over declared feature shortcuts; not universal uniqueness",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
