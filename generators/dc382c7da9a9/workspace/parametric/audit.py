#!/usr/bin/env python3
"""Bounded adversarial audit for the wall-distance scope family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PATH = HERE / "prototype.py"
NAME = "_audit_dc382c7da9a9_" + hashlib.sha256(str(PATH).encode()).hexdigest()[:16]
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load {PATH}")
P = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = P
SPEC.loader.exec_module(P)

RIVALS = (
    "all_equidistant",
    "shortest_path_midpoints",
    "manhattan_equidistant",
    "all_shortest_path_cells",
    "first_equidistant_only",
    "red_one_step_farther",
    "identity",
)


def _grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _visible(episode) -> str:
    from reviewer_support import public_challenge_bytes

    raw = public_challenge_bytes(episode)
    payload = json.loads(raw.decode("utf-8"))
    if set(payload) != {"train", "test"}:
        raise AssertionError("public projection has unexpected top-level keys")
    if any(set(pair) != {"input", "output"} for pair in payload["train"]):
        raise AssertionError("public demonstrations are malformed")
    if any(set(pair) != {"input"} for pair in payload["test"]):
        raise AssertionError("public queries leaked answers")
    serialized = json.dumps(payload, sort_keys=True)
    private_words = (
        "distance_scope",
        "episode_seed",
        "program_solution",
        "shortest_distance",
        "midpoint_cells",
    )
    if any(word in serialized for word in private_words):
        raise AssertionError("public projection leaked private metadata")
    return hashlib.sha256(raw).hexdigest()


def audit(seed_count: int = 16) -> dict:
    report = {
        "schema": "dc382c7da9a9-native-audit-v1",
        "seed_count": seed_count,
        "settings": list(P.DISTANCE_SCOPES),
        "demo_counts": [2, 3, 4, 5, 6],
        "query_count": 4,
        "episodes": 0,
        "visible_pairs": 0,
        "rival_checks": 0,
        "public_projections": 0,
        "stress_30x30": 0,
        "equal_cells_in_stress": 0,
        "midpoint_cells_in_stress": 0,
        "findings": [],
    }
    public_ids: set[str] = set()
    for seed in range(seed_count):
        matched_inputs = None
        for scope in P.DISTANCE_SCOPES:
            full = P.generate(seed, {"distance_scope": scope}, demos=6, queries=4)
            keys = [_grid_sha256(pair["input"]) for pair in full["train"] + full["test"]]
            if len(keys) != len(set(keys)):
                report["findings"].append({"seed": seed, "scope": scope, "issue": "duplicate_input"})
            if matched_inputs is None:
                matched_inputs = keys
            elif matched_inputs != keys:
                report["findings"].append({"seed": seed, "scope": scope, "issue": "settings_changed_inputs"})

            stress = full["test"][3]["input"]
            if (len(stress), len(stress[0])) != (30, 30):
                report["findings"].append({"seed": seed, "scope": scope, "issue": "missing_30x30"})
            facts = P.analyze(stress)
            report["equal_cells_in_stress"] += len(facts["equal_cells"])
            report["midpoint_cells_in_stress"] += len(facts["midpoint_cells"])
            if len(facts["equal_cells"]) < 100 or len(facts["midpoint_cells"]) != 1:
                report["findings"].append({
                    "seed": seed,
                    "scope": scope,
                    "issue": "weak_30x30",
                    "equal_cells": len(facts["equal_cells"]),
                    "midpoint_cells": len(facts["midpoint_cells"]),
                })

            public_id = _visible({
                "train": full["train"][:3],
                "test": full["test"],
                "meta": {"distance_scope": scope, "episode_seed": seed},
            })
            if public_id in public_ids:
                report["findings"].append({"seed": seed, "scope": scope, "issue": "duplicate_public_payload"})
            public_ids.add(public_id)
            report["public_projections"] += 1

            rivals = [rival for rival in RIVALS if rival != scope]
            rival_demo_outputs = {
                rival: [P.rival_output(pair["input"], rival) for pair in full["train"]]
                for rival in rivals
            }
            rival_query_outputs = {
                rival: [P.rival_output(pair["input"], rival) for pair in full["test"]]
                for rival in rivals
            }
            for demos in range(2, 7):
                report["episodes"] += 1
                report["visible_pairs"] += demos + 4
                report["stress_30x30"] += 1
                for rival in rivals:
                    report["rival_checks"] += 1
                    demo_refuted = any(
                        rival_demo_outputs[rival][index] != full["train"][index]["output"]
                        for index in range(demos)
                    )
                    query_disagrees = any(
                        rival_query_outputs[rival][index] != full["test"][index]["output"]
                        for index in range(4)
                    )
                    if not demo_refuted or not query_disagrees:
                        report["findings"].append({
                            "seed": seed,
                            "scope": scope,
                            "demos": demos,
                            "rival": rival,
                            "demo_refuted": demo_refuted,
                            "query_disagrees": query_disagrees,
                        })
    report["status"] = "passed" if not report["findings"] else "failed"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=16)
    args = parser.parse_args(argv)
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_keys = (
        "status",
        "episodes",
        "visible_pairs",
        "rival_checks",
        "public_projections",
        "stress_30x30",
        "equal_cells_in_stress",
        "midpoint_cells_in_stress",
    )
    print(json.dumps({key: report[key] for key in summary_keys}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
