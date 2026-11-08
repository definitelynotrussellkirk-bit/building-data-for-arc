#!/usr/bin/env python3
"""One explicitly requested extra ticket; never changes the issued assignment.

Run from the packet root:
  python3 WORK/checks/additional-ticket-001/draw_one_ticket.py --work WORK

The first invocation journals fresh entropy before selecting anything. Later
invocations resume exactly that seed and validate the immutable input hashes.
This is an opt-in extension, not the official two-ticket assignment command.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sys


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve(strict=True)
    destination = Path(__file__).resolve().parent
    destination.relative_to(work / "checks")
    names = ("PACKET-MANIFEST.json", "ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json")
    raw = {name: (work / name).read_bytes() for name in names}
    identities = {name: digest(data) for name, data in raw.items()}
    manifest, assignment, previous = (json.loads(raw[name]) for name in names)
    sys.path.insert(0, str(work / "repo" / "src"))
    from arcpuzzles.review_tickets import CONSUMERS, INSTRUCTIONS

    journal_path = destination / "seed.json"
    if not journal_path.exists():
        write_new(journal_path, {
            "schema": "reviewer-requested-extra-ticket-seed-v1",
            "authorization": "User requested: do another random ticket!",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "seed": secrets.token_bytes(32).hex(),
            "input_sha256": identities,
        })
    journal = json.loads(journal_path.read_text())
    if journal["input_sha256"] != identities:
        raise ValueError("Draw inputs changed; refusing to redraw")
    seed = bytes.fromhex(journal["seed"])
    if len(seed) != 32:
        raise ValueError("Seed journal must contain exactly 32 bytes")
    excluded = {assignment["task_id"]}
    excluded.update(t["task_id"] for t in previous["tickets"] if "task_id" in t)
    policy = manifest["supplementary_ticket_policy"]
    candidates = {
        kind: [row for row in rows if row.get("task_id") not in excluded]
        for kind, rows in sorted(policy["candidates"].items())
        if kind in policy["weights"]
    }
    candidates = {kind: rows for kind, rows in candidates.items() if rows}
    weights = {kind: policy["weights"][kind] for kind in candidates}
    roll = int.from_bytes(hashlib.sha256(seed + b":extra-ticket-type:0").digest(), "big") % sum(weights.values())
    original_roll = roll
    for kind, weight in weights.items():
        if roll < weight:
            break
        roll -= weight
    rows = candidates[kind]
    index = int.from_bytes(hashlib.sha256(seed + b":extra-ticket-target:0").digest(), "big") % len(rows)
    budget = dict(policy["budget"])
    if kind == "nvarc_visual":
        from arcpuzzles.review_nvarc import BUDGET
        budget = dict(BUDGET)
    ticket = {
        **rows[index], "type": kind, "consumer": CONSUMERS[kind],
        "seed": digest(seed + b":extra-ticket-probe:0"), "budget": budget,
    }
    ticket["ticket_id"] = "extra-ticket-" + digest(encoded({
        "packet_id": assignment["packet_id"], "assignment_id": assignment["assignment_id"], **ticket,
    }))[:16]
    draw = {
        "schema": "reviewer-requested-extra-ticket-v1",
        "scope": "User-authorized addition; not part of the immutable official two-ticket contract",
        "authorization": journal["authorization"],
        "packet_id": assignment["packet_id"], "assignment_id": assignment["assignment_id"],
        "created_utc": journal["created_utc"], "seed": journal["seed"],
        "input_sha256": identities,
        "sampler_sha256": digest(Path(__file__).read_bytes()),
        "sampling": "One weighted type, then one uniform target; sorted type order; SHA-256 modulo draws; no reroll",
        "excluded_task_ids": sorted(excluded), "eligible_weights": weights,
        "eligible_candidate_counts": {k: len(v) for k, v in candidates.items()},
        "eligible_pool_sha256": digest(encoded(candidates)),
        "type_roll": original_roll, "target_index": index,
        "ticket": ticket, "instructions": INSTRUCTIONS[kind],
    }
    draw_path = destination / "draw.json"
    if draw_path.exists():
        if json.loads(draw_path.read_text()) != draw:
            raise ValueError("Existing draw differs; refusing to overwrite or reroll")
    else:
        write_new(draw_path, draw)
    print(json.dumps(draw, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
