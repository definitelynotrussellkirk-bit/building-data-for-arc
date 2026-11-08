"""Bounded protected-Racket and finite-rival audit for candidate-choice lessons."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "8d37d130fec1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _load(path, tag):
    body = path.read_bytes()
    name = f"_8d37_candidate_{tag}_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


P = _load(HERE / "prototype.py", "prototype")
A = _load(HERE / "adapter.py", "adapter")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _turn(episode, index=0):
    return {"train": copy.deepcopy(episode["train"]),
            "test": [copy.deepcopy(episode["test"][index])]}


def run(out: Path, seed_count: int = 24):
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    if type(seed_count) is not int or not 1 <= seed_count <= 128:
        raise ValueError("seed_count must be an exact integer in 1..128")
    out.mkdir(parents=True)
    (out / "public").mkdir()

    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": seed, "settings": {"candidate_choice": choice},
         "demos": demos, "queries": 4}
        for choice in P.CHOICES
        for seed, demos in ((0, 2), (17, 3), (29, 6))
    ]
    worker = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    (out / "worker.json").write_bytes(_raw(worker))

    failures = []
    lessons = rival_checks = public_checks = 0
    candidate_patterns = set()
    shapes = set()
    program_hashes = {
        choice: hashlib.sha256(A.program({"candidate_choice": choice}).encode()).hexdigest()
        for choice in P.CHOICES
    }
    for seed in range(seed_count):
        for demos in range(2, 7):
            episodes = {
                choice: A.generate(seed, {"candidate_choice": choice}, demos, 4)
                for choice in P.CHOICES
            }
            first_inputs = [pair["input"] for split in ("train", "test")
                            for pair in episodes["first"][split]]
            last_inputs = [pair["input"] for split in ("train", "test")
                           for pair in episodes["last"][split]]
            if first_inputs != last_inputs:
                failures.append({"seed": seed, "demos": demos, "kind": "setting_input_mismatch"})
            for choice, episode in episodes.items():
                lessons += 1
                report = P.teaching_report(episode, {"candidate_choice": choice})
                rival_checks += len(report["tested_rivals"])
                if not report["accepted"]:
                    failures.append({"seed": seed, "demos": demos, "choice": choice,
                                     "kind": "teaching_failure", "report": report})
                keys = [json.dumps(pair["input"], separators=(",", ":"))
                        for split in ("train", "test") for pair in episode[split]]
                if len(keys) != len(set(keys)):
                    failures.append({"seed": seed, "demos": demos, "choice": choice,
                                     "kind": "duplicate_input"})
                one = A.generate(seed, {"candidate_choice": choice}, demos, 1)
                if public_challenge_bytes(_turn(one)) != public_challenge_bytes(_turn(episode)):
                    failures.append({"seed": seed, "demos": demos, "choice": choice,
                                     "kind": "first_turn_drift"})
                mutated = copy.deepcopy(episode)
                mutated.update(settings={"private": 1}, seed=-1, program_solution="private")
                for pair in mutated["test"]:
                    pair["output"] = [[9]]
                for pair in mutated["test"][1:]:
                    pair["input"] = [[9]]
                if public_challenge_bytes(_turn(mutated)) != public_challenge_bytes(_turn(episode)):
                    failures.append({"seed": seed, "demos": demos, "choice": choice,
                                     "kind": "private_projection_leak"})
                public_checks += 1
                for pair in episode["train"] + episode["test"]:
                    facts = P.analyze(pair["input"])
                    shapes.add((len(pair["input"]), len(pair["input"][0])))
                    candidate_patterns.add(facts["candidate_indices"])
                    if pair["output"] != P.solve(pair["input"], {"candidate_choice": choice}):
                        failures.append({"seed": seed, "demos": demos, "choice": choice,
                                         "kind": "python_label_mismatch"})

    public_examples = []
    for choice in P.CHOICES:
        episode = A.generate(17, {"candidate_choice": choice}, 3, 4)
        turn = _turn(episode)
        payload = public_challenge_bytes(turn)
        identifier = public_challenge_id(turn)
        if identifier != hashlib.sha256(payload).hexdigest():
            failures.append({"choice": choice, "kind": "public_id_mismatch"})
        path = out / "public" / f"challenge-{identifier}.json"
        path.write_bytes(payload)
        public_examples.append({"choice": choice, "path": path.relative_to(out).as_posix(),
                                "sha256": identifier})

    large = A.generate(17, {"candidate_choice": "last"}, 3, 4)["test"][3]
    large_facts = P.analyze(large["input"])
    summary = {
        "schema": "8d37d130fec1-candidate-choice-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "limits": "Finite seeds and named rivals only; not a universal uniqueness or measured-learning proof.",
        "python": {
            "seed_count": seed_count,
            "demo_counts": [2, 3, 4, 5, 6],
            "lessons": lessons,
            "rival_checks": rival_checks,
            "public_projection_checks": public_checks,
            "candidate_index_patterns": [list(value) for value in sorted(candidate_patterns)],
            "input_shapes": [list(value) for value in sorted(shapes)],
            "failures": failures,
        },
        "racket": {
            "identity": worker["racket"],
            "evaluations": worker["racket_evaluations"],
            "jobs": jobs,
            "checks": worker["checks"],
            "worker_sha256": _sha(out / "worker.json"),
        },
        "program_sha256": program_hashes,
        "large_query": {
            "shape": [len(large["input"]), len(large["input"][0])],
            "non_background_cells": sum(value != 8 for row in large["input"] for value in row),
            "candidate_indices": list(large_facts["candidate_indices"]),
            "candidate_areas": list(large_facts["candidate_areas"]),
            "input_sha256": hashlib.sha256(_raw(large["input"])).hexdigest(),
            "output_sha256": hashlib.sha256(_raw(large["output"])).hexdigest(),
        },
        "public_examples": public_examples,
        "source_sha256": {
            path.relative_to(ROOT).as_posix(): _sha(path)
            for path in (HERE / "prototype.py", HERE / "adapter.py", HERE / "canonical.rkt",
                         HERE / "promotion.json", HERE.parents[1] / "generator.py",
                         HERE.parents[1] / "tests/test_parametric_candidate_choice.py")
        },
        "owner_acceptance": "not_performed",
        "training_admitted": False,
    }
    (out / "summary.json").write_bytes(_raw(summary))
    if failures:
        raise AssertionError(f"audit found {len(failures)} failure(s)")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=24)
    args = parser.parse_args()
    summary = run(args.out, args.seeds)
    print(json.dumps({
        "status": summary["status"],
        "lessons": summary["python"]["lessons"],
        "rival_checks": summary["python"]["rival_checks"],
        "racket_evaluations": summary["racket"]["evaluations"],
        "large_query": summary["large_query"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
