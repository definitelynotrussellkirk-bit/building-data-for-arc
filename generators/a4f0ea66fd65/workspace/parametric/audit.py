"""Finite self-review for the vector-copy repeat family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    name = "_vector_repeat_audit_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    p = _load()
    episodes = 0
    labeled_pairs = 0
    public_views = 0
    large_cases = 0
    harmful = []
    distinct_failures = []
    matched_failures = []
    for seed in range(args.seeds):
        by_mode = {mode: p.generate(seed, {"copy_extent": mode}, demos=6, queries=4) for mode in p.MODES}
        def keys(ep):
            return [json.dumps(pair["input"], separators=(",", ":")) for split in ("train", "test") for pair in ep[split]]
        if keys(by_mode[p.MODES[0]]) != keys(by_mode[p.MODES[1]]):
            matched_failures.append(seed)
        if len(set(keys(by_mode[p.MODES[0]]))) != 10:
            distinct_failures.append(seed)
        for mode in p.MODES:
            for demos in (2, 3, 6):
                episode = p.generate(seed, {"copy_extent": mode}, demos=demos, queries=4)
                report = p.teaching_report(episode, mode)
                episodes += 1
                labeled_pairs += len(episode["train"]) + len(episode["test"])
                if report["surviving_harmful_rivals"]:
                    harmful.append({"seed": seed, "mode": mode, "demos": demos, "survivors": report["surviving_harmful_rivals"]})
                grid = episode["test"][3]["input"]
                if len(grid) == 30 and len(grid[0]) == 30:
                    large_cases += 1
            sample = by_mode[mode]
            for query_index in range(4):
                public = p.public_turn(sample, query_index)
                if set(public) != {"train", "test"} or len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                    raise AssertionError("public projection leaked or changed structure")
                public_views += 1
    status = "passed" if not (harmful or distinct_failures or matched_failures) else "failed"
    report = {
        "schema": "arcpuzzles-finite-parametric-self-review-v1",
        "task_id": p.TASK_ID,
        "status": status,
        "limits": {
            "seeds": args.seeds,
            "settings": list(p.MODES),
            "demonstration_counts": [2, 3, 6],
            "queries": 4,
            "rivals": 9,
            "claim": "finite declared-rival check, not universal uniqueness",
        },
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "public_views_checked": public_views,
        "substantive_30x30_cases": large_cases,
        "harmful_survivors": harmful,
        "distinct_input_failures": distinct_failures,
        "matched_input_failures": matched_failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
