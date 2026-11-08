"""Finite self-review for the vertical-flip/cue-axis family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "family.py"
    name = "_a6294f07bff6_audit_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
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
    parser.add_argument("--seeds", type=int, default=24)
    args = parser.parse_args()
    family = _load()
    failures = []
    episodes = pairs = public_views = stress = 0
    for seed in range(args.seeds):
        full = {mode: family.generate(seed, {"flip_rule": mode}, 6, 4) for mode in family.MODES}
        inputs = {mode: [pair["input"] for pair in ep["train"] + ep["test"]] for mode, ep in full.items()}
        if inputs[family.MODES[0]] != inputs[family.MODES[1]]:
            failures.append({"seed": seed, "failure": "unmatched_inputs"})
        if len({json.dumps(grid, separators=(",", ":")) for grid in inputs[family.MODES[0]]}) != 10:
            failures.append({"seed": seed, "failure": "duplicate_inputs"})
        for mode in family.MODES:
            for demos in (2, 3, 6):
                episode = family.generate(seed, {"flip_rule": mode}, demos, 4)
                episodes += 1
                pairs += demos + 4
                survivors = [candidate for candidate in family.MODES if all(family.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])]
                if survivors != [mode]:
                    failures.append({"seed": seed, "mode": mode, "demos": demos, "failure": "setting_survivors", "survivors": survivors})
                for rival in family.RIVALS:
                    if not any(family.rival_output(pair["input"], rival) != pair["output"] for pair in episode["train"]):
                        failures.append({"seed": seed, "mode": mode, "demos": demos, "failure": "harmful_rival", "rival": rival})
                grid = episode["test"][3]["input"]
                if (len(grid), len(grid[0])) == (30, 30) and sum(v != 0 for row in grid for v in row) >= 600:
                    stress += 1
            for query_index in range(4):
                public = family.public_turn(full[mode], query_index)
                if set(public) != {"train", "test"} or len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                    failures.append({"seed": seed, "mode": mode, "failure": "public_projection"})
                public_views += 1
    report = {
        "schema": "arcpuzzles-finite-parametric-self-review-v1",
        "task_id": family.TASK_ID,
        "status": "passed" if not failures else "failed",
        "limits": {"seeds": args.seeds, "settings": list(family.MODES), "demonstration_counts": [2, 3, 6], "queries": 4, "rivals": list(family.RIVALS), "claim": "finite declared-rival check, not universal uniqueness"},
        "episodes": episodes,
        "labeled_pairs": pairs,
        "public_views_checked": public_views,
        "substantive_30x30_cases": stress,
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
