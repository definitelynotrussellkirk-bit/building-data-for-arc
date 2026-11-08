"""Finite deterministic self-review for the 46b45dd2aff8 native family."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_audit_46b_native", HERE / "native.py")
assert spec is not None and spec.loader is not None
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)

def run(seeds: int = 64):
    failures = []
    episodes = pairs = differences = large = 0
    for seed in range(seeds):
        for demos in (2, 3, 6):
            generated = {s: family.generate(seed, {family.PARAMETER: s}, demos, 4) for s in family.SETTINGS}
            episodes += len(generated)
            left, right = (generated[s] for s in family.SETTINGS)
            if [p["input"] for p in left["train"] + left["test"]] != [p["input"] for p in right["train"] + right["test"]]:
                failures.append({"seed": seed, "demos": demos, "kind": "setting-dependent-inputs"})
            for setting, episode in generated.items():
                pairs += len(episode["train"]) + len(episode["test"])
                survivors = family.surviving_rivals(episode["train"], setting)
                if survivors:
                    failures.append({"seed": seed, "demos": demos, "setting": setting, "survivors": survivors})
                if len(episode["test"][-1]["input"]) == 30 and len(episode["test"][-1]["input"][0]) == 30:
                    large += 1
            differences += sum(a["output"] != b["output"] for a, b in zip(left["test"], right["test"]))
    return {
        "schema": "46b45dd2aff8-native-parametric-audit-v1",
        "passed": not failures,
        "seeds": seeds,
        "episodes": episodes,
        "pairs": pairs,
        "setting_answer_differences": differences,
        "exact_30_inputs": large,
        "declared_rivals": sorted(family._rival_functions()),
        "failures": failures[:20],
        "limits": "finite deterministic sweep over declared rivals; not universal uniqueness",
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    args = parser.parse_args()
    report = run(args.seeds)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["passed"] else 1)
