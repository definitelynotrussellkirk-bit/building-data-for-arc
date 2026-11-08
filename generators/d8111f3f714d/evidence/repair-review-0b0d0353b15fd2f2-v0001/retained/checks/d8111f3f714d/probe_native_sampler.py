#!/usr/bin/env python3
"""Bounded sampler/count and independent-claim probe; performs no Racket calls."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random


ROOT = Path.cwd().resolve()
TASK = "d8111f3f714d"
HOME = ROOT / f"generators/{TASK}/workspace/parametric"


def load(name):
    spec = importlib.util.spec_from_file_location(f"_branch_sampler_{name}", HOME / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(count):
    family, audit = load("native_family"), load("audit_native")
    records, failures, all_inputs, query_inputs = [], [], set(), set()
    shapes, branches, large = set(), set(), []
    attempts = passed = 0
    random_state = random.getstate()
    for seed in range(count):
        full_by_setting = {}
        for setting in family.SETTINGS:
            settings = {"branch_direction": setting}
            for demos, queries in [(6, 4), (2, 1), (3, 4)]:
                attempts += 1
                try:
                    ep = family.generate(seed, settings, demos, queries)
                    assert len(ep["train"]) == demos and len(ep["test"]) == queries
                    assert ep["meta"]["construction_attempts"] == [1] * 10
                    if demos == 6:
                        full_by_setting[setting] = ep
                    full = full_by_setting[setting]
                    assert ep["train"] == full["train"][:demos]
                    assert ep["test"] == full["test"][:queries]
                    pair_hashes = []
                    for split in ["train", "test"]:
                        for pair in ep[split]:
                            facts = audit.analyze_scene(pair["input"])
                            assert pair["output"] == audit.independent_apply(pair["input"], settings)
                            key = digest(pair["input"])
                            pair_hashes.append(key)
                            all_inputs.add(key)
                            if split == "test":
                                query_inputs.add(key)
                            shapes.add((len(pair["input"]), len(pair["input"][0])))
                            branches.add(len(facts["branches"]))
                    assert len(pair_hashes) == len(set(pair_hashes))
                    if demos == 6:
                        # The finite rival gate reads demonstrations only.
                        for rival in audit.RIVALS:
                            assert any(audit.independent_apply(pair["input"], settings, rival) != pair["output"] for pair in ep["train"][:2]), rival
                        pair = ep["test"][3]
                        painted = [(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value == 3]
                        quadrants = {(r >= 15, c >= 15) for r, c in painted}
                        assert len(quadrants) == 4 and len(painted) >= 70
                        large.append({"seed": seed, "setting": setting, "red_cells": sum(v == 2 for row in pair["input"] for v in row),
                                      "painted_cells": len(painted), "input_sha256": digest(pair["input"]), "output_sha256": digest(pair["output"])})
                    records.append({"seed": seed, "settings": settings, "demos": demos, "queries": queries,
                                    "input_sha256": pair_hashes, "program_sha256": ep["meta"]["program_sha256"], "status": "passed"})
                    passed += 1
                except Exception as exc:
                    failures.append({"seed": seed, "setting": setting, "demos": demos, "queries": queries,
                                     "error": f"{type(exc).__name__}: {exc}"})
        if len(full_by_setting) == 2:
            a, b = [full_by_setting[s] for s in family.SETTINGS]
            for split in ["train", "test"]:
                assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
                assert all(x["output"] != y["output"] for x, y in zip(a[split], b[split], strict=True))
    assert random.getstate() == random_state
    files = [HOME / name for name in ["native_family.py", "adapter.py", "prototype.py", "audit_native.py", "promotion.json"]]
    files += [Path(__file__).resolve(), ROOT / f"generators/{TASK}/generator.py"]
    return {"schema": "arcpuzzles-native-branch-sampler-v1", "task_id": TASK,
            "status": "failed" if failures else "passed", "requests": attempts, "passed": passed, "failures": failures,
            "seeds": list(range(count)), "count_requests": [[6, 4], [2, 1], [3, 4]],
            "source_sha256": {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            "distinct_inputs": len(all_inputs), "distinct_query_inputs": len(query_inputs),
            "shapes": sorted(shapes), "branch_counts": sorted(branches), "large_queries": large,
            "records": records, "racket_evaluations": 0,
            "limits": "Deterministic Python sampling, independent Python claim parity and finite demo-only rivals. No Racket labels, owner acceptance, training admission, universal seed or rival coverage are established by this probe."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        parser.error("--seeds must be within1..256")
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    result = run(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: result[k] for k in ["status", "requests", "passed", "distinct_inputs", "distinct_query_inputs", "failures"]}, sort_keys=True))
    raise SystemExit(bool(result["failures"]))


if __name__ == "__main__":
    main()
