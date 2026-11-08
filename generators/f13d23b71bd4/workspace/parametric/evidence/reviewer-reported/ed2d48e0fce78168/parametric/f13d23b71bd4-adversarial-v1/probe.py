#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_id

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/f13d23b71bd4/workspace/parametric/prototype.py"
OUT = Path(__file__).resolve().with_name("result.json")

spec = importlib.util.spec_from_file_location("f13_parametric_adversarial", SOURCE)
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

started = time.monotonic()
checks = []


def record(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})
    if not passed:
        raise AssertionError(f"{name}: {detail}")


# Surface 1: sampler boundaries/retry schedule. Exercise the maximum total pair
# pressure used by the public API without spending Racket calls on all 32 grids.
inputs = prototype._sample_inputs(731, 32, difficulty="hard", root=ROOT)
input_hashes = [row["input_sha256"] for row in inputs]
record("max_sampler_unique_32", len(set(input_hashes)) == 32,
       {"unique": len(set(input_hashes)), "attempts": [row["attempt"] for row in inputs]})
record("max_sampler_boundary_sizes", all(row["object_sizes"] == [1, 2, 3, 4, 5, 6] for row in inputs),
       {"profiles": len(inputs), "object_sizes": sorted({tuple(row["object_sizes"]) for row in inputs})})
record("max_sampler_retry_bound", max(row["attempt"] for row in inputs) < 32,
       {"max_attempt": max(row["attempt"] for row in inputs)})

# Surface 2a: exact Racket parity outside retained medium evidence.
with RacketBridge() as bridge:
    episodes = [
        prototype.make_episode(101, minimum_fall_size=3, demo_count=2, query_count=4,
                               difficulty="easy", root=ROOT, bridge=bridge),
        prototype.make_episode(202, minimum_fall_size=5, demo_count=2, query_count=4,
                               difficulty="hard", root=ROOT, bridge=bridge),
    ]
for episode in episodes:
    rivals = [row for row in episode["parameter_rivals"]
              if row["minimum_fall_size"] != episode["parameters"]["minimum_fall_size"]]
    record(
        f"racket_rivals_refuted_{episode['difficulty']}_t{episode['parameters']['minimum_fall_size']}",
        all(row["demonstration_mismatch_indices"] == [0, 1]
            and row["query_mismatch_indices"] == [0, 1, 2, 3]
            for row in rivals),
        rivals,
    )

# Surface 2b: source/parameter verifier rejection paths.
rejections = []
for label, callback in [
    ("bool_threshold", lambda: prototype.materialize_rule(True, root=ROOT)),
    ("float_threshold", lambda: prototype.materialize_rule(4.0, root=ROOT)),
    ("out_of_range_threshold", lambda: prototype.materialize_rule(6, root=ROOT)),
    ("tampered_canonical_source", lambda: prototype.materialize_rule(
        3, source=prototype.canonical_source(root=ROOT) + " ")),
    ("tampered_materialized_source", lambda: prototype.rule_callable(
        prototype.materialize_rule(3, root=ROOT).replace("(empty-grid h w bg)", "(empty-grid h w 0)", 1))),
    ("zero_demo_count", lambda: prototype.make_episode(0, demo_count=0, root=ROOT)),
    ("bool_query_count", lambda: prototype.make_episode(0, query_count=True, root=ROOT)),
]:
    try:
        callback()
    except (ValueError, AssertionError) as exc:
        rejections.append({"case": label, "error_type": type(exc).__name__, "error": str(exc)})
    else:
        raise AssertionError(f"{label} unexpectedly accepted")
record("rejection_paths", len(rejections) == 7, rejections)

# Surface 2c: public identity depends only on visible content.
episode = episodes[0]
public = prototype.public_challenge(episode)
original_id = public_challenge_id(public)
private_mutation = copy.deepcopy(episode)
private_mutation["seed"] += 1
private_mutation["parameters"]["minimum_fall_size"] = 5
private_mutation["test"][0]["output"][0][0] = (
    private_mutation["test"][0]["output"][0][0] + 1
) % 10
record("private_metadata_and_query_answer_do_not_change_public_id",
       public_challenge_id(prototype.public_challenge(private_mutation)) == original_id,
       {"public_id": original_id})
visible_mutation = copy.deepcopy(public)
visible_mutation["test"][0]["input"][0][0] = (visible_mutation["test"][0]["input"][0][0] + 1) % 10
record("visible_query_input_changes_public_id",
       public_challenge_id(visible_mutation) != original_id,
       {"before": original_id, "after": public_challenge_id(visible_mutation)})

result = {
    "schema": "arcpuzzles-parametric-adversarial-probe-v1",
    "task_id": prototype.TASK_ID,
    "prototype_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "status": "bounded_no_finding",
    "surfaces": [
        "sampler boundaries and retry schedule",
        "parameter/Racket parity plus public/private export and verifier rejection paths",
    ],
    "checks": checks,
    "elapsed_seconds": round(time.monotonic() - started, 6),
    "limitations": [
        "Bounded probe over one 32-input sampler draw and two cross-difficulty episodes.",
        "Rival family is limited to declared thresholds 3, 4, and 5.",
    ],
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "checks": len(checks),
                  "elapsed_seconds": result["elapsed_seconds"], "out": str(OUT)}, sort_keys=True))
