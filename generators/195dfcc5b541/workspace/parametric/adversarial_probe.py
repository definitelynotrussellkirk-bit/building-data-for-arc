#!/usr/bin/env python3
"""Bounded adversarial probe for the 195dfcc5b541 parametric prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve()
ROOT = next(
    (
        parent
        for parent in HERE.parents
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file()
    ),
    HERE.parents[4],
)
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load(filename: str, name: str):
    path = HERE.with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_report(*, seed_start: int = 0, seed_count: int = 32) -> dict[str, Any]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative exact integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 256:
        raise ValueError("seed_count must be an exact integer in 1..256")

    proto = _load("prototype.py", "probe_parametric_prototype_195dfcc5b541")
    verify = _load("verify.py", "probe_parametric_verify_195dfcc5b541")

    failures = []
    attempts = []
    pair_count = 0
    first_episode = None
    for seed in range(seed_start, seed_start + seed_count):
        for setting in proto.SETTINGS:
            try:
                episode = proto.generate_episode(
                    seed,
                    reflection_mode=setting[0],
                    column_order=setting[1],
                    n_train=1,
                    n_test=1,
                )
                if first_episode is None:
                    first_episode = episode
                provenance = episode["private"]["pairs"]
                attempts.extend(row["accepted_attempt"] for row in provenance)
                pair_count += len(provenance)
                if not all(row["all_setting_outputs_distinct"] for row in provenance):
                    failures.append(
                        {
                            "seed": seed,
                            "setting": setting,
                            "reason": "setting outputs collapsed",
                        }
                    )
            except Exception as error:  # retained diagnostic, not silent shrinkage
                failures.append(
                    {
                        "seed": seed,
                        "setting": setting,
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )

    if first_episode is None:
        raise RuntimeError("seed sweep produced no episode")

    original_id = proto.public_id(first_episode)
    private_mutant = deepcopy(first_episode)
    private_mutant["private"]["seed"] += 999999
    private_mutant["private"]["setting"] = {
        "reflection_mode": "private-mutant",
        "column_order": "private-mutant",
    }
    query_answer_mutant = deepcopy(first_episode)
    for pair in query_answer_mutant["test"]:
        pair["output"] = [[0 for _ in row] for row in pair["output"]]
    visible_mutant = deepcopy(first_episode)
    visible_mutant["train"][0]["output"][0][0] = (
        visible_mutant["train"][0]["output"][0][0] + 1
    ) % 10
    projection_invariance = {
        "private_metadata_does_not_change_id": (
            proto.public_id(private_mutant) == original_id
        ),
        "query_answers_do_not_change_id": (
            proto.public_id(query_answer_mutant) == original_id
        ),
        "visible_demo_output_changes_id": (
            proto.public_id(visible_mutant) != original_id
        ),
    }

    boundary_episode = proto.generate_episode(
        seed_start + seed_count + 1,
        reflection_mode="dihedral",
        column_order="left_to_right",
        n_train=proto.MAX_COUNT,
        n_test=proto.MAX_COUNT,
    )
    boundary_hashes = [
        _grid_hash(pair["input"])
        for pair in [*boundary_episode["train"], *boundary_episode["test"]]
    ]
    boundary_status = (
        len(boundary_hashes) == 2 * proto.MAX_COUNT
        and len(set(boundary_hashes)) == len(boundary_hashes)
    )
    count_boundary = {
        "n_train": len(boundary_episode["train"]),
        "n_test": len(boundary_episode["test"]),
        "unique_inputs": len(set(boundary_hashes)),
        "status": "pass" if boundary_status else "fail",
    }

    with tempfile.TemporaryDirectory(prefix="195dfcc5b541-parametric-probe-") as temp:
        racket = verify.build_report(
            seed_base=seed_start + 777000,
            artifact_dir=Path(temp) / "racket",
        )
    racket_recheck = {
        "status": racket["status"],
        "seed_base": seed_start + 777000,
        "settings": racket["totals"]["settings"],
        "stored_labels_checked_by_racket": racket["totals"][
            "stored_labels_checked_by_racket"
        ],
        "rival_labels_checked_by_racket": racket["totals"][
            "rival_labels_checked_by_racket"
        ],
        "canonical_default": racket["canonical_default"],
        "all_public_challenges_masked": racket[
            "all_public_challenges_masked"
        ],
        "source": racket["source"],
    }

    status = "pass" if all(
        (
            not failures,
            attempts,
            all(projection_invariance.values()),
            boundary_status,
            racket_recheck["status"] == "pass",
        )
    ) else "fail"
    return {
        "schema": "195dfcc5b541-parametric-adversarial-probe-v1",
        "status": status,
        "seed_sweep": {
            "seed_start": seed_start,
            "seed_count": seed_count,
            "settings_per_seed": len(proto.SETTINGS),
            "episodes": seed_count * len(proto.SETTINGS),
            "pairs": pair_count,
            "failures": failures,
            "max_accepted_attempt": max(attempts) if attempts else None,
            "mean_accepted_attempt": (
                sum(attempts) / len(attempts) if attempts else None
            ),
            "attempt_histogram": {
                str(value): attempts.count(value) for value in sorted(set(attempts))
            },
        },
        "public_projection_invariance": projection_invariance,
        "count_boundary": count_boundary,
        "racket_recheck": racket_recheck,
        "limitations": [
            "The seed sweep is bounded and Python-mirrored; the separate retained verifier supplies exact Racket evidence.",
            "The maximum supported count is a prototype guardrail, not a production API claim.",
            "No claim is made against rules outside the four declared settings.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(seed_start=args.seed_start, seed_count=args.seed_count)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
