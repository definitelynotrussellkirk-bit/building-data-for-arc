#!/usr/bin/env python3
"""Bounded adversarial probe for the 537b409b6744 candidate-rank prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PROTOTYPE_PATH = (
    ROOT / "generators/537b409b6744/workspace/parametric/prototype.py"
)
OUT = HERE.parent / "result.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "candidate_rank_adversarial_prototype", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    prototype = load_prototype()
    canonical = prototype.canonical_rule()
    nearest = prototype.materialize_rule("nearest")
    farthest = prototype.materialize_rule("farthest")

    tie_grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 2, 4, 4, 4, 4],
        [0, 2, 2, 2, 2, 2, 4, 4, 4, 4],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    probe = prototype._load_reference_probe()
    candidates = probe.ranked_candidates(tie_grid)
    python_tie_output = prototype.apply_python(tie_grid, "farthest")
    racket_tie_output = prototype.apply_racket(tie_grid, "farthest")

    episode = prototype.build_episode(seed=0, n_train=3, n_test=4)
    public = prototype.public_challenge(episode)
    visible_bytes = public_challenge_bytes(public)
    visible_id = public_challenge_id(public)

    private_change = copy.deepcopy(episode)
    private_change["meta"]["seed"] = 999999
    private_change["meta"]["parameters"]["candidate_rank"] = "farthest"
    private_change["test"][0]["output"][0][0] = (
        private_change["test"][0]["output"][0][0] + 1
    ) % 10
    private_change_id = public_challenge_id(
        prototype.public_challenge(private_change)
    )

    visible_change = copy.deepcopy(public)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    visible_change_id = public_challenge_id(visible_change)

    leaked = copy.deepcopy(public)
    leaked["meta"] = {"candidate_rank": "nearest"}
    leaked["test"][0]["output"] = episode["test"][0]["output"]
    leak_findings = prototype.verify_public_challenge(leaked)

    invalid_numeric = copy.deepcopy(public)
    invalid_numeric["test"][0]["input"][0][0] = True
    numeric_findings = prototype.verify_public_challenge(invalid_numeric)

    duplicate_rejected = False
    duplicate_error = None
    try:
        prototype.sorted_unique_public_records(
            [{"public_id": visible_id}, {"public_id": visible_id}]
        )
    except ValueError as exc:
        duplicate_rejected = True
        duplicate_error = str(exc)

    checks = {
        "nearest_is_exact_canonical": nearest == canonical,
        "farthest_is_exact_declared_transform": (
            farthest == prototype.expected_farthest_rule(canonical)
        ),
        "farthest_differs_from_canonical": farthest != canonical,
        "tie_candidates_are_equal_gap_with_larger_wall_first": [
            (row["gap"], row["wall_size"]) for row in candidates
        ] == [(1, 10), (1, 8)],
        "tie_python_matches_racket": python_tie_output == racket_tie_output,
        "public_id_hashes_exact_written_bytes": sha256_bytes(visible_bytes) == visible_id,
        "public_filename_uses_visible_id": (
            prototype.public_filename(public) == f"challenge-{visible_id}.json"
        ),
        "private_metadata_and_query_answer_do_not_change_id": (
            private_change_id == visible_id
        ),
        "visible_query_input_changes_id": visible_change_id != visible_id,
        "metadata_leak_rejected": any(
            "forbidden top-level keys" in finding for finding in leak_findings
        ),
        "query_answer_leak_rejected": any(
            "exposes an output" in finding for finding in leak_findings
        ),
        "boolean_color_rejected": any(
            "exact integer colors 0..9" in finding for finding in numeric_findings
        ),
        "duplicate_visible_payload_rejected": duplicate_rejected,
    }

    result = {
        "schema": "537b409b6744-candidate-rank-adversarial-v1",
        "task_id": "537b409b6744",
        "scope": [
            "parameter/Racket parity on an equal-gap tie boundary",
            "public/private projection, exact-byte identity, numeric validation, and rejection paths",
        ],
        "status": "bounded_no_finding" if all(checks.values()) else "finding",
        "passed": all(checks.values()),
        "checks": checks,
        "tie_boundary": {
            "candidate_gap_wall_size": [
                [row["gap"], row["wall_size"]] for row in candidates
            ],
            "input_sha256": sha256_bytes(
                json.dumps(tie_grid, separators=(",", ":")).encode("utf-8")
            ),
            "python_output_sha256": sha256_bytes(
                json.dumps(python_tie_output, separators=(",", ":")).encode("utf-8")
            ),
            "racket_output_sha256": sha256_bytes(
                json.dumps(racket_tie_output, separators=(",", ":")).encode("utf-8")
            ),
        },
        "public_boundary": {
            "visible_id": visible_id,
            "visible_bytes": len(visible_bytes),
            "private_change_id": private_change_id,
            "visible_change_id": visible_change_id,
            "leak_findings": leak_findings,
            "numeric_findings": numeric_findings,
            "duplicate_error": duplicate_error,
        },
        "source_sha256": {
            "prototype": sha256_bytes(PROTOTYPE_PATH.read_bytes()),
            "nearest_rule": sha256_bytes(
                (PROTOTYPE_PATH.parent / "rules/nearest.rkt").read_bytes()
            ),
            "farthest_rule": sha256_bytes(
                (PROTOTYPE_PATH.parent / "rules/farthest.rkt").read_bytes()
            ),
        },
        "limits": [
            "One crafted equal-gap boundary and one retained episode were exercised.",
            "This does not establish safety for every lawful grid or every ranking policy.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "status": result["status"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
