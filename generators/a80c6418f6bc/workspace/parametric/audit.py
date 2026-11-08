"""Bounded authoring audit for the a80c6418f6bc transfer-orientation family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "a80c6418f6bc"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load("_a80c6418f6bc_audit_prototype", HERE / "prototype.py")
A = _load("_a80c6418f6bc_audit_adapter", HERE / "adapter.py")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _visible(episode):
    return {"train": episode["train"], "test": episode["test"]}


def run(out: Path, seeds: int = 64):
    if type(seeds) is not int or not 1 <= seeds <= 256:
        raise ValueError("seeds must be a literal integer in 1..256")
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"orientation": orientation}, "demos": demos, "queries": 4}
        for orientation in P.ORIENTATIONS
        for seed, demos in ((0, 2), (17, 3), (29, 6))
    ]
    worker = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    (out / "worker.json").write_bytes(_raw(worker))

    failures = []
    lessons = 0
    rival_checks = 0
    query_disagreements = 0
    public_checks = 0
    all_dimensions = set()
    mode_counts = {}
    public_ids = set()
    for seed in range(seeds):
        for demos in range(2, 7):
            episodes = {
                orientation: A.generate(seed, {"orientation": orientation}, demos, 4)
                for orientation in P.ORIENTATIONS
            }
            direct_inputs = [pair["input"] for pair in episodes["direct"]["train"] + episodes["direct"]["test"]]
            rotated_inputs = [pair["input"] for pair in episodes["rotate_180"]["train"] + episodes["rotate_180"]["test"]]
            if direct_inputs != rotated_inputs:
                failures.append({"seed": seed, "demos": demos, "kind": "setting_input_mismatch"})
            for orientation, episode in episodes.items():
                lessons += 1
                intended_demos = [pair["output"] for pair in episode["train"]]
                intended_queries = [pair["output"] for pair in episode["test"]]
                for name, rival in P.declared_rivals(orientation).items():
                    rival_checks += 1
                    demo_claim = [rival(pair["input"]) for pair in episode["train"]]
                    query_claim = [rival(pair["input"]) for pair in episode["test"]]
                    if demo_claim == intended_demos:
                        failures.append({
                            "seed": seed, "demos": demos, "orientation": orientation,
                            "kind": "surviving_rival", "rival": name,
                            "query_disagrees": query_claim != intended_queries,
                        })
                    if query_claim != intended_queries:
                        query_disagreements += 1
                hashes = [P.grid_hash(pair["input"]) for pair in episode["train"] + episode["test"]]
                if len(hashes) != len(set(hashes)):
                    failures.append({"seed": seed, "demos": demos, "orientation": orientation,
                                     "kind": "duplicate_input"})
                one = A.generate(seed, {"orientation": orientation}, demos, 1)
                expected_one = {"train": episode["train"], "test": episode["test"][:1]}
                if public_challenge_bytes(one) != public_challenge_bytes(expected_one):
                    failures.append({"seed": seed, "demos": demos, "orientation": orientation,
                                     "kind": "first_turn_drift"})
                hidden = copy.deepcopy(expected_one)
                hidden.update(settings={"orientation": "private"}, program_solution="private")
                hidden["test"][0]["output"] = [[9]]
                if public_challenge_bytes(hidden) != public_challenge_bytes(expected_one):
                    failures.append({"seed": seed, "demos": demos, "orientation": orientation,
                                     "kind": "private_projection_leak"})
                identifier = public_challenge_id(expected_one)
                public_ids.add(identifier)
                public_checks += 1
                for pair in episode["train"] + episode["test"]:
                    facts = P.analyze(pair["input"])
                    if facts["errors"]:
                        failures.append({"seed": seed, "demos": demos, "orientation": orientation,
                                         "kind": "invalid_input", "errors": facts["errors"]})
                    if pair["output"] != P.solve_python(pair["input"], orientation):
                        failures.append({"seed": seed, "demos": demos, "orientation": orientation,
                                         "kind": "python_label_mismatch"})
                    all_dimensions.add(facts["shape"])
                    mode_counts[facts["delta_mode"]] = mode_counts.get(facts["delta_mode"], 0) + 1

    public_dir = out / "public"
    public_dir.mkdir()
    private_rows = []
    for orientation in P.ORIENTATIONS:
        episode = A.generate(17, {"orientation": orientation}, 3, 4)
        visible = _visible(episode)
        identifier = public_challenge_id(visible)
        path = public_dir / f"{identifier}.json"
        path.write_bytes(public_challenge_bytes(visible))
        private_rows.append({
            "public_id": identifier,
            "settings": {"orientation": orientation},
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
            "query_output_sha256": [hashlib.sha256(_raw(pair["output"])).hexdigest()
                                    for pair in episode["test"]],
        })
    (out / "private.json").write_bytes(_raw(private_rows))

    large = A.generate(17, {"orientation": "rotate_180"}, 3, 4)["test"][3]
    large_facts = P.analyze(large["input"])
    global_cells = P.non_separator_nonzero_cells(large["input"])
    summary = {
        "schema": "a80c6418f6bc-transfer-orientation-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "scope": "Finite declared rivals, seeds, counts and profiles only; not a universal uniqueness or learning proof.",
        "python": {
            "seed_count": seeds,
            "demo_counts": [2, 3, 4, 5, 6],
            "lessons": lessons,
            "rival_checks": rival_checks,
            "rival_query_disagreements": query_disagreements,
            "public_projection_checks": public_checks,
            "unique_first_turn_ids": len(public_ids),
            "dimensions": [list(value) for value in sorted(all_dimensions)],
            "delta_mode_observations": mode_counts,
            "failures": failures,
        },
        "racket": {
            "identity": worker["racket"],
            "evaluations": worker["racket_evaluations"],
            "jobs": jobs,
            "checks": worker["checks"],
            "worker_sha256": hashlib.sha256((out / "worker.json").read_bytes()).hexdigest(),
        },
        "large_query": {
            "shape": list(large_facts["shape"]),
            "separator": list(large_facts["separator"]),
            "delta_mode": large_facts["delta_mode"],
            "delta_count": len(large_facts["delta"]),
            "non_separator_cells": len(global_cells),
            "occupied_rows": len({row for row, _ in global_cells}),
            "occupied_cols": len({col for _, col in global_cells}),
            "boundary_contact": any(row in (0, 29) or col in (0, 29) for row, col in global_cells),
            "input_sha256": hashlib.sha256(_raw(large["input"])).hexdigest(),
            "output_sha256": hashlib.sha256(_raw(large["output"])).hexdigest(),
        },
        "programs": {orientation: P.program_hash(orientation) for orientation in P.ORIENTATIONS},
        "public_files": sorted(path.name for path in public_dir.glob("*.json")),
        "training_admitted": False,
        "owner_acceptance": "not_performed",
    }
    (out / "summary.json").write_bytes(_raw(summary))
    if failures:
        raise AssertionError(f"audit found {len(failures)} failure(s)")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
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
