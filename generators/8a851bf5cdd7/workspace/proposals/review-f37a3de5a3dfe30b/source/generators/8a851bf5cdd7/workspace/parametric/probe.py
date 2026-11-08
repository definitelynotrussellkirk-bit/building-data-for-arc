"""Bounded sampler, native-contract, and Racket evidence; no acceptance action."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract

HOME = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location("_stencil_probe_" + name, HOME / f"{name}.py")
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
    p, export = load("prototype"), load("export")
    rows, failures, examples, boundaries = [], [], [], []
    checks = 0
    with p.RacketEngine() as engine:
        for seed in (0, 17):
            for demos in range(2, 7):
                paired_inputs = None
                for direction in p.DIRECTIONS:
                    request = {"seed": seed, "demos": demos, "queries": 4, "direction": direction}
                    try:
                        episode = p.generate(seed, {"direction": direction}, demos, 4, engine=engine)
                        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                        if paired_inputs is not None and paired_inputs != inputs:
                            raise AssertionError("setting-dependent inputs")
                        paired_inputs = inputs
                        for pair in episode["train"] + episode["test"]:
                            if p.python_oracle(pair["input"], episode["settings"]) != pair["output"]:
                                raise AssertionError("independent oracle mismatch")
                            checks += 1
                        rows.append({**request, "status": "passed", "labels": len(inputs),
                                     "survivors": episode["certificate"]["survivors"],
                                     "query_input_shapes": [[len(x["input"]), len(x["input"][0])]
                                                            for x in episode["test"]]})
                        if seed == 17 and demos == 3:
                            examples.append(episode)
                    except Exception as error:
                        failures.append({**request, "error": type(error).__name__, "message": str(error)})
        for index, profile in enumerate(((3, 3, "balanced"), (3, 9, "sparse"),
                                          (30, 3, "dense"), (30, 9, "balanced"))):
            grid = p.sample_input(91, "query", index, profile)
            for direction in p.DIRECTIONS:
                settings = {"direction": direction}
                label = engine.apply(p.program(settings), grid)
                if label != p.python_oracle(grid, settings):
                    raise AssertionError("boundary Racket/oracle mismatch")
                a, b, c = p.panels(grid)
                nonzero = [sum(bool(x) for row in panel for x in row) for panel in (a, b, c)]
                boundaries.append({"settings": settings, "panel_profile": list(profile),
                                   "input": grid, "output": label, "nonzero_per_panel": nonzero,
                                   "output_changed_cells": sum(x != y for row, out in zip(c, label)
                                                                for x, y in zip(row, out))})
        if failures:
            raise AssertionError(json.dumps(failures))
        export.write_export(examples, args.out / "examples", engine=engine)
        export_check = export.verify_export(args.out / "examples", engine=engine)
        evaluations = engine.evaluations
        identity = examples[0]["racket"]
    contract = json.loads((HOME / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"direction": direction}, "demos": 3, "queries": 4}
            for seed in (0, 17) for direction in p.DIRECTIONS]
    native = evaluate_contract(HOME.parents[3], p.TASK_ID, contract, jobs)
    # The worker's raw rows say accepted_parametric even though this direct call
    # grants no acceptance. Retain checks/runtime only and explicitly qualify scope.
    native_receipt = {"scope": "direct protected worker compatibility; NOT owner qualification",
                      "checks": native["checks"], "racket": native["racket"],
                      "racket_evaluations": native["racket_evaluations"],
                      "variant_approved": False, "training_admitted": False}
    sources = {}
    for path in [HOME.parent.parent / "generator.py", *sorted(HOME.glob("*.py")),
                 HOME / "promotion.json", *sorted((HOME / "rules").glob("*.rkt"))]:
        sources[str(path.relative_to(HOME.parent.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"schema": "arcpuzzles-stencil-bounded-probe-v1", "task_id": p.TASK_ID,
              "status": "passed", "requests": rows, "attempted": len(rows) + len(failures),
              "successful": len(rows), "failures": failures, "independent_oracle_matches": checks,
              "boundary_labels": len(boundaries), "racket_evaluations": evaluations, "racket": identity,
              "source_sha256": sources, "export": export_check, "native_worker": native_receipt,
              "limits": ["Two seeds and five demo counts; not all seeds or all programs.",
                         "Equal-panel width is3w+2: maximum30x29; exact30x30 is outside grammar.",
                         "No owner approval, variant acceptance, or training admission.",
                         "Canonical Python generator repairs are checked separately; the exact default Racket program is unchanged."]}
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "boundaries.json").write_text(json.dumps(boundaries, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "successful": len(rows),
                      "attempted": report["attempted"], "oracle_matches": checks,
                      "boundary_labels": len(boundaries), "native_jobs": len(native["checks"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
