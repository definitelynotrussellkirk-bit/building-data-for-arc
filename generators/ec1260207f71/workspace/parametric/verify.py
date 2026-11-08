#!/usr/bin/env python3
"""Replay the proposed family through native protected Racket and export examples.

Run through review.py run; this is a bounded authoring check, not acceptance.
Every saved label is independently replayed, and failed rivals fail the run.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "ec1260207f71"


def _load():
    spec = importlib.util.spec_from_file_location("_ec1260_verified_prototype", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    started = time.monotonic()
    prototype = _load()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"transfer_order": order}, "demos": demos, "queries": 4}
            for seed in (0, 17) for demos in (2, 3, 6) for order in prototype.ORDERS]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert native["racket"]["backend"] == "racket" and native["racket"]["protected"] is True
    assert len(native["checks"]) == len(jobs)
    # Do not propagate the worker's internal accepted_parametric episode label:
    # this is authoring evidence, and no qualification/acceptance was performed.
    episodes = [prototype.generate(**job) for job in jobs]
    apply, runtime, bridge = _real_evaluator(ROOT / "shared/runtime")
    cache = {}
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        key = (program, json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            cache[key] = apply(program, copy.deepcopy(grid))
            evaluations += 1
        return copy.deepcopy(cache[key])

    teaching = []
    programs = {}
    try:
        for job, episode, checked in zip(jobs, episodes, native["episodes"]):
            assert checked["train"] == episode["train"] and checked["test"] == episode["test"]
            rivals = prototype.rival_programs(job["settings"])
            programs[job["settings"]["transfer_order"]] = rivals
            rejected = {}
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    claimed = prototype.rival_outputs(pair["input"], job["settings"])
                    for name, program in rivals.items():
                        actual = execute(program, pair["input"])
                        assert actual == claimed[name], ("Racket rival mismatch", job, split, index, name)
                        if split == "train" and actual != pair["output"]:
                            rejected.setdefault(name, index)
                    chosen = job["settings"]["transfer_order"]
                    assert execute(rivals[chosen], pair["input"]) == pair["output"]
            survivors = [name for name in rivals if name not in rejected]
            assert survivors == [job["settings"]["transfer_order"]]
            assert rejected == episode["certificate"]["rejected"]
            teaching.append({**job, "survivors": survivors, "rejected_by_demo": rejected,
                             "query_identifiable": [True] * 4,
                             "query_answers_used_for_fitting": False})
        canonical_count = 0
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert execute(prototype.program({"transfer_order": "aligned"}), pair["input"]) == pair["output"]
            canonical_count += 1
        # Literal destination witness, independent of the Python transformation.
        witness = [[0] * 7 for _ in range(14)]
        for i in range(4):
            witness[i][0] = 2
            witness[10 + i][6] = 2
        witness[0][3] = 8
        literal_outputs = {}
        for order, destination in (("aligned", 10), ("reversed", 13)):
            expected = copy.deepcopy(witness)
            expected[0] = [2, 8, 8, 4, 0, 0, 0]
            expected[destination] = [8, 8, 8, 8, 8, 8, 2]
            actual = execute(prototype.program({"transfer_order": order}), witness)
            assert actual == expected
            literal_outputs[order] = actual
    finally:
        bridge.close()
    negative_cases = []
    for name in ("query_label", "program", "duplicate_input", "boolean_cell", "forged_certificate"):
        bad = copy.deepcopy(episodes[0])
        if name == "query_label":
            bad["test"][0]["output"][0][0] = 9
        elif name == "program":
            bad["program_solution"] = "(rule! (lambda (g) g))"
        elif name == "duplicate_input":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        elif name == "boolean_cell":
            bad["test"][0]["input"][0][1] = False
        else:
            bad["certificate"] = {"identified": True}
            bad["test"][0]["output"][0][0] = 9
        try:
            prototype.verify_episode(bad)
        except ValueError as error:
            negative_cases.append({"case": name, "rejected": True, "reason": str(error)})
        else:
            raise AssertionError(f"Verifier accepted {name}")
    for episode in episodes:
        single = prototype.generate(episode["seed"], episode["settings"], len(episode["train"]), 1)
        assert prototype.visible_turn(episode, 0) == public_challenge_bytes(single)
    # Four compact examples: each setting at each tested seed, three demonstrations.
    retained = [e for e in episodes if len(e["train"]) == 3]
    output.mkdir(parents=True, exist_ok=False)
    exported = prototype.write_export(retained, output / "examples")
    (output / "racket-programs.private.json").write_text(json.dumps(programs, indent=2) + "\n")
    (output / "literal-witness.private.json").write_text(json.dumps(
        {"input": witness, "outputs": literal_outputs}, indent=2) + "\n")
    paths = [HERE / name for name in ("adapter.py", "prototype.py", "verify.py", "promotion.json", "canonical.rkt")]
    paths += [HERE.parents[1] / "generator.py", HERE.parents[1] / "tests/test_parametric.py"]
    source_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    sample = retained[0]["test"][-1]
    report = {
        "schema": "ec1260207f71-protected-authoring-check-v1", "status": "passed",
        "task_id": TASK_ID, "source_sha256": source_hashes,
        "native_adapter_jobs": native["checks"], "racket": native["racket"],
        "native_racket_evaluations": native["racket_evaluations"],
        "extra_unique_racket_evaluations": evaluations,
        "episodes_attempted": len(jobs), "episodes_succeeded": len(jobs), "episodes_failed": 0,
        "verified_pair_labels": sum(j["demos"] + j["queries"] for j in jobs),
        "queries_verified": sum(j["queries"] for j in jobs),
        "canonical_pairs_replayed": canonical_count, "literal_setting_witnesses": 2,
        "teaching_certificates": teaching, "negative_cases": negative_cases,
        "first_turn_prefix_checks": len(episodes),
        "query_shapes": [list(shape) for shape in prototype.QUERY_SHAPES],
        "thirty_by_thirty": {"bar_length": 14, "red_cells": sum(v == 2 for row in sample["input"] for v in row),
            "marker_count": sum(v == 8 for row in sample["input"] for v in row),
            "filled_cyan_output_cells": sum(v == 8 for row in sample["output"] for v in row)},
        "retained_examples": len(retained), "export_public_ids": exported["public_ids"],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "qualification_or_acceptance_performed": False, "training_admitted": False,
        "limits": ["Two fixed seeds and demo counts 2, 3, 6; not a universal seed claim.",
            "Finite rivals only; conjunctive or other undeclared shortcuts may remain.",
            "Canonical generator semantic/authority audits are unchanged.",
            "The batch public files are controller-side; expose visible_turn one query at a time."]}
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "episodes_succeeded", "verified_pair_labels",
        "queries_verified", "canonical_pairs_replayed", "native_racket_evaluations",
        "extra_unique_racket_evaluations", "elapsed_seconds")}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    verify(args.out)


if __name__ == "__main__":
    main()
