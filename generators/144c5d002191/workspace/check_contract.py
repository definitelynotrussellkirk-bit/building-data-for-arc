"""Exhaust all declared integer controls at both curriculum residues.

This source-bound Python-only probe checks construction and observability.
It does not certify Racket labels or lesson identifiability; use the public
battery and lesson-census for those independent checks.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    gen, source, source_hash = load_selected_generator("144c5d002191", root=find_root(__file__))
    report = {
        "task_id": "144c5d002191", "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH, "scope": "Python construction and exact-control observability",
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": args.seed, "sample_indices": [0,1],
        "bands": ["easy","medium","hard"],
        "domains": {"grid_h":[7,16], "grid_w":[9,18], "n":[2,5], "template_size":[4,7]},
        "expected_cases": 9600, "checked": 0, "passed": 0, "failures": [],
    }
    for band, index, h, w, n, size in itertools.product(
            report["bands"], report["sample_indices"], range(7,17),
            range(9,19), range(2,6), range(4,8)):
        requested = dict(grid_h=h,grid_w=w,n=n,template_size=size)
        row = dict(difficulty=band,sample_index=index,overrides=requested)
        try:
            grid = gen.generate(args.seed,index,difficulty=band,**requested)
            observed = gen.observe_overrides(grid)
            reasons = gen.self_check(grid,difficulty=band)
            if observed != requested or reasons:
                row.update(observed=observed,validator_reasons=reasons,input=grid)
                report["failures"].append(row)
            else:
                report["passed"] += 1
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            report["failures"].append(row)
        report["checked"] += 1
    report["status"] = "pass" if report["checked"] == report["expected_cases"] == report["passed"] else "fail"
    path = args.out/"controls.json"
    path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256","checked","passed","status")}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

