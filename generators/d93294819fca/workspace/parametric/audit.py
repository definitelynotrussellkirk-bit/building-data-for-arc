"""Reusable protected-Racket audit/export and causal-witness builder.

Run through review.py run (see README). Does not approve a variant or alter
shared code. All retained query answers and programs stay controller-private.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK = "d93294819fca"


def adjacent(name):
    spec = importlib.util.spec_from_file_location(f"_d932_audit_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


def grid_checked(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid)):
        raise ValueError("reference did not return an exact integer color grid")
    return grid


def run_audit(output, previous=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    root, p, rivals = find_root(__file__), adjacent("prototype"), adjacent("racket_rivals")
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return grid_checked(apply(program, deepcopy(grid)))

    report = {"schema": "d93294819fca-gray-bridge-audit-v1", "status": "running",
              "racket": identity, "episodes": [], "boundaries": [], "count_edges": [],
              "scope": "Prototype only; canonical production generator unchanged",
              "limits": "Finite settings, rivals, seeds and size probes; no universal uniqueness or training gain"}
    try:
        episodes = []
        for seed in (0, 17):
            for role in p.GRAY_ROLES:
                settings = {"gray_role": role}
                episode = p.generate(seed, settings, 3, 4)
                for split in ("train", "test"):
                    for pair in episode[split]:
                        actual = execute(episode["program_solution"], pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError(f"Python/Racket label mismatch: {seed}/{role}/{split}")
                        pair["output"] = actual
                survivors, eliminations = [], {}
                for name in p.RIVALS[role]:
                    rp = rivals.program(role, name)
                    rejected_by = []
                    for i, pair in enumerate(episode["train"]):
                        actual = execute(rp, pair["input"])
                        if actual != p.rival_output(pair["input"], role, name):
                            raise AssertionError(f"rival Python/Racket mismatch: {role}/{name}/{i}")
                        if actual != pair["output"]:
                            rejected_by.append(i)
                    # One large query also exercises each rival's runtime totality.
                    q = episode["test"][-1]["input"]
                    if execute(rp, q) != p.rival_output(q, role, name):
                        raise AssertionError(f"large rival mismatch: {role}/{name}")
                    eliminations[name] = rejected_by
                    if not rejected_by:
                        survivors.append(name)
                cert = p.teaching_check(episode, settings)
                if survivors or not cert["ok"]:
                    raise AssertionError(f"teaching failure: {seed}/{role}/{survivors}")
                first_only = p.generate(seed, settings, 3, 1)
                if public_challenge_bytes(p.visible_turn(first_only, 0)) != public_challenge_bytes(p.visible_turn(episode, 0)):
                    raise AssertionError("first-turn projection depends on future query count")
                episode["metadata"].update(label_basis="executed protected Racket",
                                           racket=identity, teaching=cert)
                report["episodes"].append({"seed": seed, "settings": settings,
                    "demos": 3, "queries": 4, "public_id": public_challenge_id(episode),
                    "demo_attempts": episode["metadata"]["demonstration_attempts"],
                    "rivals_eliminated_by_demo": eliminations, "survivors": survivors,
                    "first_turn_equal_single_query": True,
                    "query_shapes": [[len(x["input"]), len(x["input"][0])] for x in episode["test"]]})
                episodes.append(episode)
        p.write_batch(episodes, output / "examples")

        boundary_cases = []
        for height, width in ((8, 8), (8, 30), (30, 8), (30, 30)):
            for phase in range(3):
                grid = p.sample_input(27, phase, height, width)
                info = p.validate_input(grid)
                answers = {}
                for role in p.GRAY_ROLES:
                    settings = {"gray_role": role}
                    answers[role] = execute(p.program(settings), grid)
                    if answers[role] != p.transform(grid, settings):
                        raise AssertionError(f"size boundary label mismatch {height}/{width}/{phase}/{role}")
                summary = {"shape": [height, width], "seed": 27, "phase": phase, **info,
                           "foreground_cells": sum(x != 0 for row in grid for x in row)}
                report["boundaries"].append(summary)
                boundary_cases.append({**summary, "input": grid, "outputs": answers})
        save(output / "boundary-cases.private.json", boundary_cases)

        # Maximum demo count has three additional, independently drawn examples.
        for role in p.GRAY_ROLES:
            setting = {"gray_role": role}
            extra = p.generate(0, setting, 6, 4)
            for pair in extra["train"][3:]:
                if execute(p.program(setting), pair["input"]) != pair["output"]:
                    raise AssertionError("maximum-demo boundary label mismatch")
            report["count_edges"].append({"settings": setting, "seed": 0, "demos": 6,
                "queries": 4, "extra_demo_labels_checked": 3,
                "teaching": p.teaching_check(extra, setting)})
        attempts = []
        for seed in range(32):
            episode = p.generate(seed, {"gray_role": "bridge"}, 3, 4)
            attempts.append(episode["metadata"]["demonstration_attempts"])
        report["sampling"] = {"seeds": list(range(32)), "requested": 32, "completed": 32,
                              "failed": 0, "attempts": attempts, "max_attempts": max(attempts),
                              "reference_scope": "Python sampling; only separately listed pairs executed in Racket"}

        if previous:
            old = json.loads(Path(previous).read_text())
            rp = rivals.program("bridge", "smallest_perimeter")
            fits = []
            for pair in old["train"]:
                correct = execute(old["program_solution"], pair["input"])
                if correct != pair["output"]:
                    raise AssertionError("historical witness label mismatch")
                fits.append(execute(rp, pair["input"]) == correct)
            differences, query_outputs = [], []
            for i, pair in enumerate(old["test"]):
                correct = execute(old["program_solution"], pair["input"])
                prediction = execute(rp, pair["input"])
                if correct != pair["output"]:
                    raise AssertionError("historical query label mismatch")
                if correct != prediction:
                    differences.append(i)
                query_outputs.append(prediction)
            if not all(fits) or not differences:
                raise AssertionError("original perimeter defect did not reproduce")
            current = p.generate(17, {"gray_role": "bridge"}, 3, 4)
            rejected = [i for i, pair in enumerate(current["train"])
                        if execute(rp, pair["input"]) != pair["output"]]
            if not rejected:
                raise AssertionError("perimeter defect remains")
            proof = {"old_prototype_sha256": old["prototype_sha256"],
                     "new_prototype_sha256": hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest(),
                     "seed": 17, "settings": {"gray_role": "bridge"}, "racket": identity,
                     "program": old["program_solution"], "counterfactual_program": rp,
                     "old_demos": old["train"], "old_queries": old["test"],
                     "counterfactual_query_outputs": query_outputs,
                     "fits_all_old_demos": all(fits), "wrong_old_queries": differences,
                     "new_distinguishing_demo": current["train"][rejected[0]],
                     "new_distinguishing_demo_indices": rejected,
                     "repair": "Thin merged area6/perimeter14 versus compact area7/perimeter12; no extra demo"}
            save(output / "perimeter-repair.private.json", proof)
            report["perimeter_repair"] = {k: proof[k] for k in (
                "old_prototype_sha256", "new_prototype_sha256", "fits_all_old_demos",
                "wrong_old_queries", "new_distinguishing_demo_indices", "repair")}
        report.update(status="passed", racket_evaluations=evaluations,
                      elapsed_seconds=round(time.monotonic() - started, 3))
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}",
                      racket_evaluations=evaluations,
                      elapsed_seconds=round(time.monotonic() - started, 3))
        save(output / "summary.json", report)
        raise
    finally:
        bridge.close()
    save(output / "summary.json", report)
    print(json.dumps({"status": report["status"], "racket_evaluations": evaluations,
                      "episodes": len(report["episodes"]), "boundary_inputs": len(report["boundaries"]),
                      "sampling": report["sampling"], "elapsed_seconds": report["elapsed_seconds"]}))


def write_witness(qualification, destination):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_promotion import _ready
    root, p, rivals = find_root(__file__), adjacent("prototype"), adjacent("racket_rivals")
    q = json.loads(Path(qualification).read_text())
    if q.get("status") != "qualified" or _ready(Catalog(root), TASK)[1] != q["source_binding"]:
        raise ValueError("qualification must match the current exact source")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    try:
        settings = {"gray_role": "bridge"}
        grid = p.generate(0, settings, 3, 4)["train"][0]["input"]
        actual_program = p.program(settings)
        if hashlib.sha256(actual_program.encode()).hexdigest() not in q["programs"].values():
            raise ValueError("causal program was not qualified")
        counterfactual_program = rivals.program("bridge", "wrong_order")
        actual = grid_checked(apply(actual_program, grid))
        counterfactual = grid_checked(apply(counterfactual_program, grid))
        intermediate = grid_checked(apply("(rule! (recolor g 5 3))", grid))
        if actual == counterfactual:
            raise AssertionError("counterfactual did not change the answer")
        descriptions = {
            "step_a": "Convert gray bridge cells to green and recompute green 4-connected components.",
            "intermediate": "The converted grid and its input-dependent merged component membership and areas.",
            "step_b": "Choose the unique smallest component of that intermediate grid and paint it yellow.",
            "why_b_depends_on_a": "The original smallest green object joins another object, so a different untouched object becomes smallest. Selecting before joining gives the wrong target."}
        witness = {"schema": "arcpuzzles-sequential-dependency-witness-v1",
                   "source_binding": q["source_binding"], **descriptions,
                   "racket": {"backend": identity["backend"], "protected": identity["protected"]},
                   "runtime_identity": identity,
                   "cases": [{"input": grid, "settings": settings,
                              "intermediate_value": {"grid": intermediate,
                                  "component_sizes": list(map(len, p.components(intermediate)))},
                              "program": actual_program, "output": actual,
                              "counterfactual_program": counterfactual_program,
                              "counterfactual_output": counterfactual, "ablation": "wrong_order"}]}
        save(destination, witness)
        print(json.dumps({"status": "passed", "witness": str(destination),
                          "racket_evaluations": 3, "different_outputs": True}))
    finally:
        bridge.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("check")
    check.add_argument("--out", required=True)
    check.add_argument("--perimeter-before")
    witness = sub.add_parser("witness")
    witness.add_argument("--qualification", required=True)
    witness.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.action == "check":
        run_audit(args.out, args.perimeter_before)
    else:
        write_witness(args.qualification, args.out)


if __name__ == "__main__":
    main()
