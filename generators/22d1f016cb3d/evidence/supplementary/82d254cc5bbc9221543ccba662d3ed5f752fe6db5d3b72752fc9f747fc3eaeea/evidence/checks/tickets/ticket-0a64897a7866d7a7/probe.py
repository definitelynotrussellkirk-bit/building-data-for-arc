#!/usr/bin/env python3
"""One read-only, source-bound probe of independent prototype pair counts."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import signal
import sys
import time


TICKET_ID = "ticket-0a64897a7866d7a7"
TASK_ID = "22d1f016cb3d"
TICKET_SEED = "3974532ec418e0a7cd472edf56a771b3a3207d08aeb1c277957c9c20f45760b4"
GENERATOR_SHA256 = "26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd"
MANIFEST_SHA256 = "31dc3c3adea911365f0d8b73273328b81ce337fc245c57536da8ce4ec2bdfcb7"
RULE_HASH = "2219db85ca5f"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3] / "repo")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("result.json"))
    args = parser.parse_args()
    started = time.monotonic()
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    signal.alarm(115)
    repo = args.repo.resolve()
    task = repo / "generators" / TASK_ID
    generator_path = task / "generator.py"
    prototype_path = task / "workspace" / "parametric" / "prototype.py"
    manifest_path = prototype_path.parent / "evidence" / "manifest.json"
    assert sha256(generator_path) == GENERATOR_SHA256, "pinned generator mismatch"
    assert sha256(manifest_path) == MANIFEST_SHA256, "pinned evidence manifest mismatch"
    manifest = json.loads(manifest_path.read_text())
    verified_files = []
    for item in manifest["files"]:
        path = repo / item["path"]
        assert path.stat().st_size == item["bytes"], item["path"]
        assert sha256(path) == item["sha256"], item["path"]
        verified_files.append(item["path"])

    spec = importlib.util.spec_from_file_location("ticket_boundary_palette", prototype_path)
    assert spec is not None and spec.loader is not None
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    seed = int(TICKET_SEED, 16)
    requested = {"demo_count": 2, "query_count": 4}
    try:
        requested_episode = prototype.build_episode(root=repo, seed=seed, **requested)
    except TypeError as error:
        request_result = {"supported": False, "exception_type": type(error).__name__,
                          "exception_message": str(error)}
    else:
        request_result = {"supported": True,
                          "actual_demo_count": len(requested_episode["train"]),
                          "actual_query_count": len(requested_episode["test"])}

    # Exercise the actual supported count path without writing rules or exports
    # back into the peer. This is the same count-boundary probe, not a battery.
    episode = prototype.build_episode(root=repo, seed=seed)
    setting = episode["parameter"]["boundary_palette"]
    source = prototype.racket_source(setting, root=repo)
    canonical = prototype.racket_source(prototype.DEFAULT_BOUNDARY_PALETTE, root=repo)
    assert prototype.normalized_hash(canonical) == RULE_HASH, "pinned rule mismatch"
    assert prototype.rule_path(setting).read_text() == source, "retained rule mismatch"
    pairs = episode["train"] + episode["test"]
    executed = prototype._racket_outputs(source, [pair["input"] for pair in pairs])
    mismatches = [index for index, (pair, output) in enumerate(zip(pairs, executed))
                  if pair["output"] != output]
    assert not mismatches, "default-count episode label mismatch"
    unique = len({tuple(map(tuple, pair["input"])) for pair in pairs})
    result = {
        "schema": "arcpuzzles-source-bound-parameter-query-probe-v1",
        "ticket_id": TICKET_ID,
        "type": "parameter_queries",
        "status": "completed",
        "consumer": "task_support_or_prototype_followup",
        "classification": "prototype_support_limit",
        "peer_safety_finding": False,
        "task_id": TASK_ID,
        "source": {
            "generator_path": str(generator_path.relative_to(repo)),
            "generator_sha256": GENERATOR_SHA256,
            "prototype_path": str(prototype_path.relative_to(repo)),
            "prototype_sha256": sha256(prototype_path),
            "evidence_manifest_path": str(manifest_path.relative_to(repo)),
            "evidence_manifest_sha256": MANIFEST_SHA256,
            "verified_manifest_file_count": len(verified_files),
            "canonical_rule_hash": RULE_HASH,
        },
        "seed": {"ticket_seed_hex": TICKET_SEED, "episode_seed": seed,
                 "derivation": "int(ticket_seed_hex, 16)"},
        "boundary": "independent demonstration/query counts",
        "build_episode_signature": str(inspect.signature(prototype.build_episode)),
        "request": requested,
        "request_result": request_result,
        "supported_default": {
            "actual_demo_count": len(episode["train"]),
            "actual_query_count": len(episode["test"]),
            "unique_input_count": unique,
            "pairs_executed_in_racket": len(executed),
            "label_mismatch_indices": mismatches,
            "boundary_palette": setting,
            "episode": episode,
            "racket_text": source,
            "racket_sha256": hashlib.sha256(source.encode()).hexdigest(),
        },
        "prior_evidence_status": {
            "verification_status": manifest["verification_status"],
            "public_identifier_status": manifest["public_identifier_status"],
            "variant_approved": manifest["variant_approved"],
            "production_parametric_api": manifest["production_parametric_api"],
        },
        "scope": {
            "targeted_probe_count": 1,
            "peer_source_edits": False,
            "canonical_safety_assessed": False,
            "variant_approval_granted": False,
            "four_query_support_verified": False,
            "limits": ["One seeded default 4-demo/1-query episode was executed.",
                       "Independent 2-demo/4-query request is unsupported by the pinned API.",
                       "No alternative-setting, public-writer, full-suite or census rerun."],
        },
        "execution": {"argv": sys.argv, "cwd": str(Path.cwd()),
                      "started_at_utc": started_at,
                      "elapsed_seconds": round(time.monotonic() - started, 6)},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    signal.alarm(0)
    print(json.dumps({"ticket_id": TICKET_ID, "status": result["status"],
                      "request_result": request_result,
                      "supported_counts": [len(episode["train"]), len(episode["test"])],
                      "racket_labels_verified": len(executed),
                      "peer_safety_finding": False,
                      "elapsed_seconds": result["execution"]["elapsed_seconds"],
                      "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
