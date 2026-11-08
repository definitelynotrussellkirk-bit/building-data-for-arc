"""Reusable bounded lesson audit for f13d23b71bd4's native family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_family_f13d23b71bd4_audit", HERE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family.py")
FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(FAMILY)


def _public_failure(public: Any) -> str | None:
    if type(public) is not dict or set(public) != {"train", "test"}:
        return "public turn must contain only train and test"
    if type(public["test"]) is not list or len(public["test"]) != 1:
        return "public turn must expose exactly one query"
    if set(public["test"][0]) != {"input"}:
        return "public query must contain only input"
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in public["train"]):
        return "public demonstrations must contain only input/output"
    text = json.dumps(public, sort_keys=True)
    if "fall_policy" in text or "program_solution" in text or "settings" in text:
        return "private metadata leaked into public turn"
    return None


def build_report(
    *,
    seeds: Iterable[int] = range(16),
    demo_counts: Iterable[int] = (2, 3, 6),
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    public_failures: list[dict[str, Any]] = []
    harmful_survivors = 0
    episodes = 0
    exact_30 = 0
    setting_differences = 0
    for seed in seeds:
        for demos in demo_counts:
            canonical = FAMILY.generate(seed, {"fall_policy": "all_large"}, demos, 4)
            alternate = FAMILY.generate(seed, {"fall_policy": "signal_ranked"}, demos, 4)
            for policy, episode in (("all_large", canonical), ("signal_ranked", alternate)):
                episodes += 1
                check = FAMILY.teaching_check(episode, {"fall_policy": policy})
                harmful_survivors += len(check["surviving_rivals"])
                if check["survivors"] != [{"fall_policy": policy}] or check["surviving_rivals"]:
                    failures.append({"seed": seed, "demos": demos, "policy": policy, "check": check})
                stress = episode["test"][3]
                if len(stress["input"]) == 30 and len(stress["input"][0]) == 30:
                    exact_30 += 1
                else:
                    failures.append({"seed": seed, "demos": demos, "policy": policy, "error": "missing 30x30 query"})
                for query_index in range(4):
                    public = FAMILY.public_turn(episode, query_index)
                    error = _public_failure(public)
                    if error:
                        public_failures.append({"seed": seed, "demos": demos, "policy": policy, "query": query_index, "error": error})
            canonical_inputs = [p["input"] for split in ("train", "test") for p in canonical[split]]
            alternate_inputs = [p["input"] for split in ("train", "test") for p in alternate[split]]
            if canonical_inputs != alternate_inputs:
                failures.append({"seed": seed, "demos": demos, "error": "setting-dependent inputs"})
            setting_differences += sum(
                left["output"] != right["output"]
                for left, right in zip(
                    canonical["train"] + canonical["test"],
                    alternate["train"] + alternate["test"],
                    strict=True,
                )
            )
    status = "passed" if not failures and not public_failures and harmful_survivors == 0 else "failed"
    return {
        "schema": "arcpuzzles-parametric-lesson-audit-v1",
        "task_id": "f13d23b71bd4",
        "status": status,
        "episodes": episodes,
        "exact_30x30_pairs": exact_30,
        "setting_dependent_answer_differences": setting_differences,
        "harmful_survivors": harmful_survivors,
        "failures": failures,
        "public_projection_failures": public_failures,
        "limitations": [
            "Finite audit over the supplied seeds, counts, two settings, and declared rival bank.",
            "Passing does not establish universal rule uniqueness or downstream learning benefit."
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16, help="audit seeds 0..N-1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(seeds=range(args.seeds))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
