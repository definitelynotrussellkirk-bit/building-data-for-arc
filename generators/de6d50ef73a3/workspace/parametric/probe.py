"""Bounded marker-placement sampler and protected-Racket evidence; no acceptance."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract

HOME = Path(__file__).resolve().parent


def load(name):
    path = HOME / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_marker_probe_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)

    p = load("prototype")
    rows, failures, examples, boundaries = [], [], [], []
    oracle_checks = 0
    with p.RacketEngine() as engine:
        for seed in (0, 17):
            for demos in range(2, 7):
                paired_inputs = None
                for placement in p.PLACEMENTS:
                    request = {
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "placement": placement,
                    }
                    try:
                        episode = p.generate(
                            seed, {"placement": placement}, demos, 4, engine=engine
                        )
                        inputs = [
                            pair["input"] for pair in episode["train"] + episode["test"]
                        ]
                        if paired_inputs is not None and paired_inputs != inputs:
                            raise AssertionError("setting-dependent inputs")
                        paired_inputs = inputs
                        for pair in episode["train"] + episode["test"]:
                            expected = p.python_oracle(pair["input"], episode["settings"])
                            if expected != pair["output"]:
                                raise AssertionError("independent oracle mismatch")
                            oracle_checks += 1
                        corners = [p.marker_info(pair["input"])["corner"]
                                   for pair in episode["test"]]
                        rows.append({
                            **request,
                            "status": "passed",
                            "labels": len(inputs),
                            "survivors": episode["certificate"]["survivors"],
                            "query_corners": corners,
                            "query_shapes": [
                                [len(pair["input"]), len(pair["input"][0])]
                                for pair in episode["test"]
                            ],
                        })
                        if seed == 17 and demos == 2:
                            examples.append(episode)
                    except Exception as error:
                        failures.append({
                            **request,
                            "error": type(error).__name__,
                            "message": str(error),
                        })

        for index, profile in enumerate(p.QUERY_PROFILES):
            grid = p.sample_input(91, "query", index, profile)
            info = p.marker_info(grid)
            for placement in p.PLACEMENTS:
                settings = {"placement": placement}
                output = engine.apply(p.program(settings), grid)
                if output != p.python_oracle(grid, settings):
                    raise AssertionError("boundary Racket/oracle mismatch")
                boundaries.append({
                    "settings": settings,
                    "profile": list(profile),
                    "marker_corner": info["corner"],
                    "input": grid,
                    "output": output,
                    "nonzero_input": sum(bool(v) for row in grid for v in row),
                    "nonzero_output": sum(bool(v) for row in output for v in row),
                })
        if failures:
            raise AssertionError(json.dumps(failures))
        evaluations = engine.evaluations
        identity = examples[0]["racket"]

    contract = json.loads((HOME / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"placement": placement}, "demos": 2, "queries": 4}
        for seed in (0, 17)
        for placement in p.PLACEMENTS
    ]
    native = evaluate_contract(HOME.parents[3], p.TASK_ID, contract, jobs)
    native_receipt = {
        "scope": "direct protected worker compatibility; NOT owner qualification",
        "checks": native["checks"],
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"],
        "variant_approved": False,
        "training_admitted": False,
    }

    sources = {}
    paths = [
        HOME.parent.parent / "generator.py",
        HOME.parent.parent / "tests" / "test_generator_contract.py",
        HOME.parent.parent / "tests" / "test_parametric_placement.py",
        *sorted(HOME.glob("*.py")),
        HOME / "promotion.json",
        *sorted((HOME / "rules").glob("*.rkt")),
    ]
    for path in paths:
        relative = path.relative_to(HOME.parents[2])
        sources[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()

    report = {
        "schema": "arcpuzzles-marker-placement-bounded-probe-v1",
        "task_id": p.TASK_ID,
        "status": "passed",
        "requests": rows,
        "attempted": len(rows) + len(failures),
        "successful": len(rows),
        "failures": failures,
        "independent_oracle_matches": oracle_checks,
        "boundary_labels": len(boundaries),
        "racket_evaluations": evaluations,
        "racket": identity,
        "source_sha256": sources,
        "native_worker": native_receipt,
        "retained_examples": examples,
        "limits": [
            "Two seeds and five demonstration counts; not all seeds or all programs.",
            "Teaching is uniqueness only within the six declared total rivals.",
            "The marker input grammar is intentionally narrower than the canonical global-crop domain.",
            "No owner approval, variant acceptance, or training admission.",
        ],
    }
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "boundaries.json").write_text(
        json.dumps(boundaries, separators=(",", ":")) + "\n"
    )
    print(json.dumps({
        "status": report["status"],
        "successful": report["successful"],
        "attempted": report["attempted"],
        "oracle_matches": oracle_checks,
        "boundary_labels": len(boundaries),
        "native_jobs": len(native["checks"]),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
