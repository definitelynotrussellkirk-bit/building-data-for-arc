#!/usr/bin/env python3
"""Bounded adversarial probe for the a9c4475d7cda threshold prototype."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def load_prototype(root: Path):
    path = root / "generators/a9c4475d7cda/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("a9_threshold_adversarial", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_value_error(label, fn):
    try:
        fn()
    except ValueError as exc:
        return {"case": label, "rejected": True, "error": str(exc)}
    raise AssertionError(f"{label} was accepted")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    root = find_root(__file__)
    prototype = load_prototype(root)

    canonical = prototype.canonical_source(root=root)
    source_guard = [
        expect_value_error(
            "canonical_whitespace_tamper",
            lambda: prototype.materialize_rule(2, source=canonical + "\n"),
        ),
        expect_value_error(
            "illegal_materialized_threshold",
            lambda: prototype.rule_callable(
                canonical.replace(
                    prototype._threshold_fragment(2),
                    prototype._threshold_fragment(4),
                    1,
                )
            ),
        ),
        expect_value_error(
            "bool_setting",
            lambda: prototype.materialize_rule(True, root=root),
        ),
        expect_value_error(
            "duplicate_evidence_seeds",
            lambda: prototype.write_evidence((0, 0), out=args.out.parent / "dup"),
        ),
    ]

    random.seed(92023)
    rng_before = random.getstate()
    boundary_jobs = (
        {"seed": 100, "panel_threshold": 1, "demo_count": 1, "query_count": 16},
        {"seed": 101, "panel_threshold": 2, "demo_count": 16, "query_count": 1},
        {"seed": 102, "panel_threshold": 3, "demo_count": 4, "query_count": 4},
    )
    summaries = []
    retained = None
    with RacketBridge() as bridge:
        for job in boundary_jobs:
            episode = prototype.make_episode(root=root, bridge=bridge, **job)
            pairs = episode["train"] + episode["test"]
            expected_count = job["demo_count"] + job["query_count"]
            assert len(pairs) == expected_count
            assert len({pair["input_sha256"] for pair in pairs}) == expected_count
            assert episode["ambiguities"] == []
            assert all(
                type(cell) is int
                for pair in pairs
                for key in ("input", "output")
                for row in pair[key]
                for cell in row
            )
            assert all(
                rival["status"] in {"matches_episode", "refuted_by_demonstrations"}
                for rival in episode["parameter_rivals"]
            )
            summaries.append(
                {
                    **job,
                    "distinct_inputs": expected_count,
                    "racket_evaluations": episode["racket_evaluations"],
                    "ambiguities": 0,
                    "all_cells_exact_int": True,
                }
            )
            if job["panel_threshold"] == 2:
                retained = episode

        assert retained is not None
        replay = prototype.make_episode(
            root=root,
            bridge=bridge,
            seed=101,
            panel_threshold=2,
            demo_count=16,
            query_count=1,
        )
        assert replay == retained

    assert random.getstate() == rng_before

    public = prototype.public_challenge(retained)
    public_bytes = public_challenge_bytes(public)
    public_id = public_challenge_id(public)
    private_mutation = copy.deepcopy(retained)
    private_mutation["seed"] = 0
    private_mutation["parameters"]["panel_threshold"] = 1
    private_mutation["racket_source"] = "not public"
    private_mutation["test"][0]["output"][0][0] ^= 1
    assert public_challenge_bytes(prototype.public_challenge(private_mutation)) == public_bytes
    assert public_challenge_id(prototype.public_challenge(private_mutation)) == public_id

    visible_mutation = copy.deepcopy(retained)
    visible_mutation["train"][0]["output"][0][0] ^= 1
    assert public_challenge_id(prototype.public_challenge(visible_mutation)) != public_id

    result = {
        "schema": "a9c4475d7cda-parametric-adversarial-v1",
        "status": "pass",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_guard": source_guard,
        "boundary_jobs": summaries,
        "deterministic_replay": True,
        "global_rng_unchanged": True,
        "private_mutations_preserve_public_bytes_and_id": True,
        "visible_demo_label_mutation_changes_public_id": True,
        "public_id": public_id,
        "public_sha256": hashlib.sha256(public_bytes).hexdigest(),
        "limits": [
            "Probe covers three bounded jobs, not every seed or count combination.",
            "Only declared thresholds 1, 2, and 3 are exercised.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "out": str(args.out),
                      "elapsed_seconds": result["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
