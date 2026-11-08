"""Bounded authoring audit for the ea763f9c5b1d native parametric family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "ea763f9c5b1d"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load("_ea763f9c5b1d_audit_prototype", HERE / "prototype.py")
A = _load("_ea763f9c5b1d_audit_adapter", HERE / "adapter.py")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def run(out: Path, seeds: int = 64):
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"rule_mode": mode}, "demos": demos, "queries": 4}
        for mode in P.RULE_MODES
        for seed, demos in ((0, 2), (17, 3), (29, 6))
    ]
    worker = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    (out / "worker.json").write_bytes(_raw(worker))

    failures = []
    lessons = 0
    rivals_checked = 0
    query_disagreements = 0
    public_checks = 0
    dimensions = set()
    anchor_sizes = set()
    public_ids = set()
    for seed in range(seeds):
        for demos in range(2, 7):
            by_mode = {
                mode: A.generate(seed, {"rule_mode": mode}, demos, 4)
                for mode in P.RULE_MODES
            }
            lessons += len(by_mode)
            parity_inputs = [p["input"] for p in by_mode["area_parity"]["train"] + by_mode["area_parity"]["test"]]
            threshold_inputs = [p["input"] for p in by_mode["anchor_threshold"]["train"] + by_mode["anchor_threshold"]["test"]]
            if parity_inputs != threshold_inputs:
                failures.append({"seed": seed, "demos": demos, "kind": "setting_input_mismatch"})
            for mode, episode in by_mode.items():
                intended_demo = [pair["output"] for pair in episode["train"]]
                intended_query = [pair["output"] for pair in episode["test"]]
                for name, solver in P.declared_rivals(mode).items():
                    rivals_checked += 1
                    demo_claim = [solver(pair["input"]) for pair in episode["train"]]
                    query_claim = [solver(pair["input"]) for pair in episode["test"]]
                    if demo_claim == intended_demo:
                        failures.append({
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "kind": "surviving_rival",
                            "rival": name,
                            "query_disagrees": query_claim != intended_query,
                        })
                    if query_claim != intended_query:
                        query_disagreements += 1
                keys = [json.dumps(p["input"], separators=(",", ":")) for p in episode["train"] + episode["test"]]
                if len(keys) != len(set(keys)):
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "kind": "duplicate_input"})
                one = A.generate(seed, {"rule_mode": mode}, demos, 1)
                first = {"train": episode["train"], "test": [episode["test"][0]]}
                if public_challenge_bytes(one) != public_challenge_bytes(first):
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "kind": "first_turn_drift"})
                public_checks += 1
                public_ids.add(public_challenge_id(first))
                changed = copy.deepcopy(first)
                changed.update(settings={"rule_mode": "private"}, program_solution="private")
                changed["test"][0]["output"] = [[9]]
                if public_challenge_bytes(changed) != public_challenge_bytes(first):
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "kind": "private_projection_leak"})
                for pair in episode["train"] + episode["test"]:
                    facts = P.analyze_scene(pair["input"])
                    dimensions.add((len(pair["input"]), len(pair["input"][0])))
                    anchor_sizes.add(facts["anchor_size"])
                    if pair["output"] != P.solve_python(pair["input"], mode):
                        failures.append({"seed": seed, "demos": demos, "mode": mode, "kind": "python_label_mismatch"})

    large = A.generate(17, {"rule_mode": "anchor_threshold"}, 3, 4)["test"][3]
    large_facts = P.analyze_scene(large["input"])
    summary = {
        "schema": "ea763f9c5b1d-parametric-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "limits": "Finite declared rivals, seeds and count bounds only; not a universal uniqueness or learning proof.",
        "python": {
            "seed_count": seeds,
            "demo_counts": [2, 3, 4, 5, 6],
            "lessons": lessons,
            "rival_checks": rivals_checked,
            "rival_query_disagreements": query_disagreements,
            "public_projection_checks": public_checks,
            "unique_first_turn_ids": len(public_ids),
            "dimensions": sorted([list(x) for x in dimensions]),
            "anchor_sizes": sorted(anchor_sizes),
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
            "shape": [len(large["input"]), len(large["input"][0])],
            "component_count": len(large_facts["component_sizes"]),
            "component_sizes": sorted(large_facts["component_sizes"]),
            "occupied_rows": large_facts["occupied_rows"],
            "occupied_cols": large_facts["occupied_cols"],
            "boundary_contact": any(r in (0, 29) or c in (0, 29) for r, c in large_facts["all_cells"]),
            "input_sha256": hashlib.sha256(_raw(large["input"])).hexdigest(),
            "output_sha256": hashlib.sha256(_raw(large["output"])).hexdigest(),
        },
        "programs": {
            mode: hashlib.sha256(A.program({"rule_mode": mode}).encode()).hexdigest()
            for mode in P.RULE_MODES
        },
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
