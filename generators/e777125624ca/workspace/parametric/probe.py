"""Run the bounded authoring/self-review probe for the aligned-panel family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "e777125624ca"
HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_aligned_panel_impl", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    root = find_root(__file__)
    prototype = _load()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    seeds = [0, 17]
    demo_counts = [2, 3, 6]
    settings = [{"rule_mode": value} for value in ("nor", "sparser_difference")]
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for setting, seed, demos in itertools.product(settings, seeds, demo_counts)
    ]

    python_checks = []
    for job in jobs:
        episode = prototype.generate(
            job["seed"], job["settings"], job["demos"], job["queries"]
        )
        failures = prototype.teaching_failures(
            episode["train"], episode["test"], job["settings"]
        )
        if failures:
            raise ValueError("self-review failed: " + "; ".join(failures))
        one = prototype.generate(job["seed"], job["settings"], job["demos"], 1)
        projected = {
            "train": episode["train"],
            "test": [{"input": episode["test"][0]["input"]}],
        }
        if public_challenge_bytes(one) != public_challenge_bytes(projected):
            raise ValueError("one-query/four-query first-turn projection drifted")
        python_checks.append(
            {
                **job,
                "status": "passed",
                "input_count": job["demos"] + 4,
                "query_shapes": [
                    [len(pair["input"]), len(pair["input"][0])]
                    for pair in episode["test"]
                ],
                "query_sparser": [
                    prototype.scene_facts(pair["input"])["sparser"]
                    for pair in episode["test"]
                ],
            }
        )

    for seed in seeds:
        left = prototype.generate(seed, settings[0], 2, 4)
        right = prototype.generate(seed, settings[1], 2, 4)
        if [pair["input"] for pair in left["train"] + left["test"]] != [
            pair["input"] for pair in right["train"] + right["test"]
        ]:
            raise ValueError("hidden setting changed sampled inputs")

    executed = evaluate_contract(root, TASK_ID, contract, jobs)
    stress = prototype.generate(0, settings[1], 2, 4)["test"][-1]["input"]
    facts = prototype.scene_facts(stress)
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": "Bounded author self-review; not owner acceptance or training admission.",
        "settings": settings,
        "seeds": seeds,
        "demo_counts": demo_counts,
        "queries": 4,
        "python_jobs": python_checks,
        "plausible_rivals": [
            "always-left selector",
            "always-right selector",
            "opposite selector",
            "XOR",
            "canonical NOR",
            "one-panel complement",
            "equality",
            "intersection",
        ],
        "protected_racket": {
            "jobs": len(executed["checks"]),
            "evaluations": executed["racket_evaluations"],
            "runtime": executed["racket"],
            "all_single_setting_survivors": all(
                len(row["survivors"]) == 1 and row["survivors"][0] == row["settings"]
                for row in executed["checks"]
            ),
        },
        "stress": {
            "shape": [len(stress), len(stress[0])],
            "nonzero_cells": sum(value != 0 for row in stress for value in row),
            "canonical_width_limit": 7,
            "facts": facts,
        },
        "source_sha256": {
            name: _sha(HERE / name)
            for name in (
                "adapter.py",
                "prototype.py",
                "nor.rkt",
                "sparser_difference.rkt",
                "promotion.json",
            )
        },
        "owner_acceptance": "not_performed",
        "training_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "out": str(args.out),
                "jobs": len(result["python_jobs"]),
                "racket_evaluations": result["protected_racket"]["evaluations"],
            }
        )
    )


if __name__ == "__main__":
    main()
