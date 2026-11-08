#!/usr/bin/env python3
"""Reusable bounded adversarial probe for the orientation-scope prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
PROTOTYPE = REPO / "generators/d09fae8197f6/workspace/parametric/prototype.py"
OUT = HERE / "orientation-scope-adversarial-v1.json"
ORDINARY_EPISODES = 40
SEED_BASE = 202610230000
BOUNDARY_SEED = 202610239999


def load_prototype():
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location("_orientation_scope_adversarial", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def input_keys(episode):
    return {
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*episode["train"], *episode["test"]]
    }


def main() -> None:
    started = time.perf_counter()
    proto = load_prototype()
    attempts: list[int] = []
    setting_counts = {"dihedral": 0, "rotations": 0}
    sampling_failures = 0
    ordinary_pairs = 0
    all_unique = True

    for offset in range(ORDINARY_EPISODES):
        try:
            episode = proto.generate_episode(SEED_BASE + offset, demo_count=3, query_count=4, root=REPO)
        except Exception:
            sampling_failures += 1
            continue
        setting_counts[episode["parameter"]["orientation_scope"]] += 1
        rows = [*episode["train"], *episode["test"]]
        ordinary_pairs += len(rows)
        attempts.extend(row["candidate_attempt"] for row in rows)
        all_unique = all_unique and len(input_keys(episode)) == len(rows)

    boundary = proto.generate_episode(
        BOUNDARY_SEED,
        orientation_scope="dihedral",
        demo_count=8,
        query_count=4,
        root=REPO,
    )
    boundary_rows = [*boundary["train"], *boundary["test"]]
    attempts.extend(row["candidate_attempt"] for row in boundary_rows)
    all_unique = all_unique and len(input_keys(boundary)) == len(boundary_rows)

    public_source = proto.generate_episode(
        SEED_BASE - 1,
        orientation_scope="rotations",
        demo_count=3,
        query_count=4,
        root=REPO,
    )
    baseline_name = proto.public_filename(public_source)
    baseline_public = proto.public_challenge(public_source)

    private_mutation = deepcopy(public_source)
    private_mutation["seed"] = 999999999
    private_mutation["parameter"]["orientation_scope"] = "dihedral"
    private_mutation["source"] = {"private": "changed"}
    for pair in private_mutation["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    private_invariant = proto.public_filename(private_mutation) == baseline_name

    demo_mutation = deepcopy(public_source)
    old = demo_mutation["train"][0]["output"][0][0]
    demo_mutation["train"][0]["output"][0][0] = (old + 1) % 10
    demo_sensitive = proto.public_filename(demo_mutation) != baseline_name

    query_mutation = deepcopy(public_source)
    old = query_mutation["test"][0]["input"][0][0]
    query_mutation["test"][0]["input"][0][0] = (old + 1) % 10
    query_sensitive = proto.public_filename(query_mutation) != baseline_name

    hidden_absent = (
        "orientation_scope" not in baseline_public
        and "seed" not in baseline_public
        and "source" not in baseline_public
        and all(set(pair) == {"input"} for pair in baseline_public["test"])
    )

    if sampling_failures:
        raise AssertionError(f"{sampling_failures} ordinary episodes exhausted sampling")
    if ordinary_pairs != ORDINARY_EPISODES * 7:
        raise AssertionError(f"ordinary pair count mismatch: {ordinary_pairs}")
    if len(boundary_rows) != 12 or not all_unique:
        raise AssertionError("episode uniqueness/count boundary failed")
    if not (private_invariant and demo_sensitive and query_sensitive and hidden_absent):
        raise AssertionError("public/private projection invariant failed")

    sorted_attempts = sorted(attempts)
    p95_index = max(0, min(len(sorted_attempts) - 1, int(0.95 * len(sorted_attempts)) - 1))
    record = {
        "schema": "d09fae8197f6-orientation-scope-adversarial-v1",
        "status": "pass",
        "prototype_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
        "command": {
            "cwd": ".",
            "argv": [
                "python3", "review.py", "run", "python3",
                "../checks/parametric/adversarial_probe.py"
            ],
        },
        "sampler": {
            "ordinary_episodes": ORDINARY_EPISODES,
            "ordinary_pairs": ordinary_pairs,
            "max_boundary_demo_count": 8,
            "max_boundary_query_count": 4,
            "boundary_pairs": len(boundary_rows),
            "all_episode_inputs_unique": all_unique,
            "sampling_failures": sampling_failures,
            "auto_setting_counts": setting_counts,
            "candidate_attempt_count": len(attempts),
            "candidate_attempt_max": max(attempts),
            "candidate_attempt_median": statistics.median(attempts),
            "candidate_attempt_p95": sorted_attempts[p95_index],
        },
        "public_projection": {
            "private_metadata_and_query_answer_invariant": private_invariant,
            "demo_output_sensitive": demo_sensitive,
            "query_input_sensitive": query_sensitive,
            "hidden_tokens_absent": hidden_absent,
            "sample_public_filename": baseline_name,
        },
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "limits": [
            "Bounded Python-only adversarial probe; exact retained episode labels are separately Racket-verified.",
            "Forty ordinary seeds plus one maximum-count episode do not prove all-seed sampler success."
        ],
    }
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": record["status"],
        "ordinary_episodes": ORDINARY_EPISODES,
        "pairs": len(attempts),
        "candidate_attempt_max": max(attempts),
        "sampling_failures": sampling_failures,
        "evidence": str(OUT),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
