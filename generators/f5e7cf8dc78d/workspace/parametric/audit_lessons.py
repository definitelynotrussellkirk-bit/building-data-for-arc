"""Reusable bounded audit for the leftmost-ranked framed-band family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent


def _load_family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location("_f5_parametric_family_audit", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load family: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def build_report(
    *, seeds: Iterable[int] = range(64), demo_counts: tuple[int, ...] = (2, 3, 6)
) -> dict:
    family = _load_family()
    issues: list[dict] = []
    public_failures: list[dict] = []
    harmful = 0
    exact_30 = 0
    setting_differences = 0
    episodes = 0
    for seed in seeds:
        for demos in demo_counts:
            generated = {
                policy: family.generate(seed, {"frame_policy": policy}, demos, 4)
                for policy in family.POLICIES
            }
            if _inputs(generated[family.POLICIES[0]]) != _inputs(generated[family.POLICIES[1]]):
                issues.append({"seed": seed, "demos": demos, "kind": "setting-dependent-inputs"})
            shorter = family.generate(seed, {"frame_policy": "all_bands"}, demos, 2)
            if generated["all_bands"]["test"][:2] != shorter["test"]:
                issues.append({"seed": seed, "demos": demos, "kind": "query-prefix-instability"})
            for policy, episode in generated.items():
                episodes += 1
                check = family.teaching_check(episode, {"frame_policy": policy})
                harmful += len(check["surviving_rivals"])
                if check["survivors"] != [{"frame_policy": policy}] or check["surviving_rivals"]:
                    issues.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "policy": policy,
                            "kind": "teaching",
                            "check": check,
                        }
                    )
                stress = episode["test"][3]
                if (len(stress["input"]), len(stress["input"][0])) == (30, 30):
                    exact_30 += 1
                for query_index in range(4):
                    public = family.public_turn(episode, query_index)
                    if set(public) != {"train", "test"} or set(public["test"][0]) != {"input"}:
                        public_failures.append(
                            {"seed": seed, "demos": demos, "policy": policy, "query": query_index}
                        )
            setting_differences += sum(
                left["output"] != right["output"]
                for left, right in zip(
                    generated["all_bands"]["train"] + generated["all_bands"]["test"],
                    generated["leftmost_ranked"]["train"] + generated["leftmost_ranked"]["test"],
                    strict=True,
                )
            )
    return {
        "schema": "f5e7cf8dc78d-parametric-audit-v1",
        "status": "passed" if not issues and not public_failures and harmful == 0 else "failed",
        "episodes": episodes,
        "harmful_survivors": harmful,
        "exact_30x30_pairs": exact_30,
        "setting_dependent_answer_differences": setting_differences,
        "public_projection_failures": public_failures,
        "issues": issues,
        "limits": [
            "Finite declared-rival audit, not a universal uniqueness proof.",
            "Python labels are independently re-executed by native protected-Racket qualification.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(seeds=range(args.seeds))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
