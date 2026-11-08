#!/usr/bin/env python3
"""Draw one explicitly user-requested extra ticket; never alter native draws.

Run from the outer packet: python WORK/checks/tickets/draw_additional_ticket.py
Reruns resume the same recorded seed. Use --sequence N only for a separately
authorized subsequent draw. Native intake still expects exactly two tickets;
extra outcomes belong in RESULTS.work_scope and retained checks evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write_once(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    try:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError(f"Existing record differs; refusing replacement: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--sequence", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.sequence <= 99:
        parser.error("sequence must be 1..99")
    work = args.work.resolve()
    sys.path.insert(0, str(work / "repo/src"))
    from arcpuzzles.review_full_draw import load_manifest
    from arcpuzzles.review_tickets import CONSUMERS, INSTRUCTIONS, supplementary_contract
    manifest, packet_id = load_manifest(work)
    main_raw = (work / "ASSIGNMENT.json").read_bytes()
    audit_raw = (work / "AUDIT_ASSIGNMENT.json").read_bytes()
    assignment, audit = json.loads(main_raw), json.loads(audit_raw)
    blind_path = work / "BLIND_ASSIGNMENT.json"
    blind_id = json.loads(blind_path.read_bytes())["task_id"] if blind_path.exists() else None
    if assignment["packet_id"] != packet_id or audit != supplementary_contract(
        manifest, packet_id, assignment, bytes.fromhex(audit["seed"]), blind_id
    ):
        raise ValueError("Original draw/packet identity mismatch")
    base = work / "checks/tickets"
    base.mkdir(parents=True, exist_ok=True)
    previous = list(audit["tickets"])
    prior_bindings = []
    for sequence in range(1, args.sequence):
        path = base / f"additional-{sequence:03d}-draw.json"
        raw = path.read_bytes()
        prior = json.loads(raw)
        if prior["packet_id"] != packet_id or prior["assignment_id"] != assignment["assignment_id"]:
            raise ValueError("Prior extra ticket belongs to another assignment")
        previous.append(prior["ticket"])
        prior_bindings.append({"path": path.relative_to(work).as_posix(), "sha256": sha(raw)})
    excluded_types = {ticket["type"] for ticket in previous}
    excluded_tasks = {assignment["task_id"], blind_id} | {t.get("task_id") for t in previous}
    excluded_tasks.discard(None)
    policy = manifest["supplementary_ticket_policy"]
    candidates = {kind: [row for row in rows if row.get("task_id") not in excluded_tasks]
                  for kind, rows in policy["candidates"].items() if kind not in excluded_types}
    weights = {kind: weight for kind, weight in sorted(policy["weights"].items()) if candidates.get(kind)}
    if not weights:
        raise ValueError("No unused eligible ticket types remain")
    journal_path = base / f"additional-{args.sequence:03d}-seed.json"
    context = {"schema": "arcpuzzles-user-requested-ticket-seed-v1", "packet_id": packet_id,
               "assignment_id": assignment["assignment_id"], "sequence": args.sequence,
               "main_assignment_sha256": sha(main_raw), "native_audit_assignment_sha256": sha(audit_raw),
               "prior_additional_draws": prior_bindings,
               "authorization": "User explicitly requested: do another random ticket!"}
    if journal_path.exists():
        journal = json.loads(journal_path.read_bytes())
        if {key: value for key, value in journal.items() if key != "seed"} != context:
            raise ValueError("Seed journal context changed; refusing a fresh draw")
    else:
        journal = {**context, "seed": os.urandom(32).hex()}
        write_once(journal_path, journal)
    seed = bytes.fromhex(journal["seed"])
    if len(seed) != 32:
        raise ValueError("Invalid retained seed")
    total = sum(weights.values())
    roll = int.from_bytes(hashlib.sha256(seed + b":additional-ticket-type").digest(), "big") % total
    for kind, weight in weights.items():
        if roll < weight:
            break
        roll -= weight
    rows = candidates[kind]
    index = int.from_bytes(hashlib.sha256(seed + b":additional-ticket-target").digest(), "big") % len(rows)
    ticket = {**rows[index], "type": kind, "seed": sha(seed + b":additional-ticket-probe"),
              "consumer": CONSUMERS[kind], "budget": dict(policy["budget"])}
    if kind == "nvarc_visual":
        from arcpuzzles.review_nvarc import BUDGET
        ticket["budget"] = dict(BUDGET)
    ticket["ticket_id"] = "extra-ticket-" + sha(canonical({"packet_id": packet_id,
        "assignment_id": assignment["assignment_id"], "sequence": args.sequence, **ticket}))[:16]
    for binding in ticket.values():
        if isinstance(binding, dict) and set(binding) == {"path", "sha256"}:
            path = work / binding["path"]
            if path.is_symlink() or sha(path.read_bytes()) != binding["sha256"]:
                raise ValueError(f"Selected source identity changed: {binding['path']}")
    result = {"schema": "arcpuzzles-user-requested-ticket-draw-v1", "packet_id": packet_id,
              "assignment_id": assignment["assignment_id"], "sequence": args.sequence,
              "seed_journal": journal_path.relative_to(work).as_posix(), "seed": seed.hex(),
              "selection": "One weighted type from unused types; one uniform target within that type; SHA-256 modulo draws; no reroll.",
              "eligible_weights": weights, "eligible_candidate_counts": {k: len(candidates[k]) for k in weights},
              "excluded_types": sorted(excluded_types), "excluded_task_ids": sorted(excluded_tasks),
              "ticket": ticket, "instructions": INSTRUCTIONS[kind],
              "native_assignment_modified": False, "automatic_policy_change": False}
    draw_path = base / f"additional-{args.sequence:03d}-draw.json"
    write_once(draw_path, result)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
