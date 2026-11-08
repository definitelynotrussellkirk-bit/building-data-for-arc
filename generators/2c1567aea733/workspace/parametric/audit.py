#!/usr/bin/env python3
"""Bounded adversarial audit for the native anchor-color family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PATH = HERE / "prototype.py"
NAME = "_audit_2c1567aea733_" + hashlib.sha256(str(PATH).encode()).hexdigest()[:16]
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load {PATH}")
P = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = P
SPEC.loader.exec_module(P)

RANK_RIVALS = ("highest_top", "median_top", "lowest_top", "mean_top", "identity")


def _visible(episode):
    from reviewer_support import public_challenge_bytes

    payload = json.loads(public_challenge_bytes(episode).decode("utf-8"))
    if set(payload) != {"train", "test"}:
        raise AssertionError("public projection has unexpected top-level keys")
    if any(set(pair) != {"input", "output"} for pair in payload["train"]):
        raise AssertionError("public demonstrations are malformed")
    if any(set(pair) != {"input"} for pair in payload["test"]):
        raise AssertionError("public queries leaked answers")
    serialized = json.dumps(payload, sort_keys=True)
    if any(word in serialized for word in ("anchor_color", "episode_seed", "program_solution", "rule!")):
        raise AssertionError("public projection leaked private metadata")
    return hashlib.sha256(public_challenge_bytes(episode)).hexdigest()


def audit(seed_count: int = 16) -> dict:
    report = {
        "schema": "2c1567aea733-native-audit-v1",
        "seed_count": seed_count,
        "settings": list(P.ALLOWED_ANCHORS),
        "demo_counts": [2, 3, 4, 5, 6],
        "query_count": 4,
        "episodes": 0,
        "visible_pairs": 0,
        "rival_checks": 0,
        "public_projections": 0,
        "stress_30x30": 0,
        "findings": [],
    }
    public_ids = set()
    for seed in range(seed_count):
        matched_inputs = None
        for anchor in P.ALLOWED_ANCHORS:
            full = P.generate(seed, {"anchor_color": anchor}, demos=6, queries=4)
            keys = [P.grid_sha256(pair["input"]) for pair in full["train"] + full["test"]]
            if len(keys) != len(set(keys)):
                report["findings"].append({"seed": seed, "anchor": anchor, "issue": "duplicate_input"})
            if matched_inputs is None:
                matched_inputs = keys
            elif matched_inputs != keys:
                report["findings"].append({"seed": seed, "anchor": anchor, "issue": "settings_changed_inputs"})
            large = full["test"][3]["input"]
            if (len(large), len(large[0])) != (30, 30):
                report["findings"].append({"seed": seed, "anchor": anchor, "issue": "missing_30x30"})
            public_id = _visible({"train": full["train"][:3], "test": full["test"], "meta": {"anchor_color": anchor, "episode_seed": seed}})
            if public_id in public_ids:
                report["findings"].append({"seed": seed, "anchor": anchor, "issue": "duplicate_public_payload"})
            public_ids.add(public_id)
            report["public_projections"] += 1
            rivals = [f"anchor_{other}" for other in P.ALLOWED_ANCHORS if other != anchor] + list(RANK_RIVALS)
            rival_demo_outputs = {
                rival: [P.native_rival_output(pair["input"], rival) for pair in full["train"]]
                for rival in rivals
            }
            rival_query_outputs = {
                rival: [P.native_rival_output(pair["input"], rival) for pair in full["test"]]
                for rival in rivals
            }
            for demos in range(2, 7):
                report["episodes"] += 1
                report["visible_pairs"] += demos + 4
                report["stress_30x30"] += 1
                for rival in rivals:
                    report["rival_checks"] += 1
                    demo_mismatch = any(
                        rival_demo_outputs[rival][index] != full["train"][index]["output"]
                        for index in range(demos)
                    )
                    query_mismatch = any(
                        rival_query_outputs[rival][index] != full["test"][index]["output"]
                        for index in range(4)
                    )
                    if not demo_mismatch or not query_mismatch:
                        report["findings"].append({
                            "seed": seed, "anchor": anchor, "demos": demos, "rival": rival,
                            "demo_refuted": demo_mismatch, "query_disagrees": query_mismatch,
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
    print(json.dumps({k: report[k] for k in ("status", "episodes", "visible_pairs", "rival_checks", "public_projections", "stress_30x30")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
