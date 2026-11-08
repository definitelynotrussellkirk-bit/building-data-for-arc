#!/usr/bin/env python3
"""Journal one user-requested extra peer ticket without changing the assignment.

Run from the packet root with Python 3.12+: 
  python3 WORK/checks/additional-ticket-001/draw_one_ticket.py --work WORK
The first invocation saves entropy before selecting a task. Replays use exactly
that seed and refuse changed input identities. This is an explicit extension,
not a native fourth repair target or a replacement assignment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def uniform_index(seed: bytes, size: int) -> tuple[int, int]:
    """Hash-based rejection sampling avoids modulo bias; retries are recorded."""
    limit = 2**256 - 2**256 % size
    counter = 0
    while True:
        number = int.from_bytes(hashlib.sha256(seed + b":additional-peer:" + str(counter).encode()).digest(), "big")
        if number < limit:
            return number % size, counter
        counter += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve(strict=True)
    destination = Path(__file__).resolve().parent
    destination.relative_to(work / "checks")
    raw = {name: (work / name).read_bytes() for name in ("PACKET-MANIFEST.json", "ASSIGNMENT.json")}
    identities = {name: sha(data) for name, data in raw.items()}
    manifest, assignment = (json.loads(raw[name]) for name in raw)
    excluded = {row["task_id"] for row in assignment["repair_targets"]}
    pool = sorted(set(manifest["repair_target_policy"]["ids"]) - excluded)
    if not pool:
        raise ValueError("No unused tasks remain")
    journal_path = destination / "seed.json"
    if not journal_path.exists():
        write_new(journal_path, {
            "schema": "reviewer-requested-extra-peer-seed-v1",
            "authorization": "User requested: do another random ticket plz!",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "seed": secrets.token_bytes(32).hex(), "input_sha256": identities,
        })
    journal = json.loads(journal_path.read_bytes())
    if journal["input_sha256"] != identities:
        raise ValueError("Draw inputs changed; refusing to redraw")
    seed = bytes.fromhex(journal["seed"])
    if len(seed) != 32:
        raise ValueError("Seed must contain exactly 32 bytes")
    index, rejections = uniform_index(seed, len(pool))
    task_id = pool[index]
    source = manifest["generators"][task_id]
    source_path = work / "repo" / source["generator"]
    if sha(source_path.read_bytes()) != source["generator_sha256"]:
        raise ValueError("Selected generator source changed; keep the draw and investigate")
    draw = {
        "schema": "reviewer-requested-extra-peer-v1", **journal,
        "packet_id": assignment["packet_id"], "assignment_id": assignment["assignment_id"],
        "scope": "One user-authorized bounded adversarial peer review; outside the immutable three-target contract",
        "sampling": "Uniform single draw over sorted remaining repair-target IDs, SHA-256 rejection sampling; no reroll",
        "sampler_sha256": sha(Path(__file__).read_bytes()),
        "excluded_task_ids": sorted(excluded), "eligible_count": len(pool),
        "eligible_pool_sha256": sha(encoded(pool)), "eligible_ids": pool,
        "selected_index": index, "rejection_count": rejections,
        "ticket": {"type": "adversarial_witness", "task_id": task_id, "source": source,
                   "probe_seed": sha(seed + b":additional-peer-probe")},
        "instructions": "Inspect one plausible shortcut or defect, retain a small source-bound Racket-backed witness and any focused repair proposal; no full peer battery or census.",
    }
    draw["ticket"]["ticket_id"] = "extra-ticket-" + sha(encoded({"assignment_id": assignment["assignment_id"], "seed": journal["seed"], "task_id": task_id}))[:16]
    path = destination / "draw.json"
    if path.exists():
        if json.loads(path.read_bytes()) != draw:
            raise ValueError("Existing draw differs; refusing to overwrite or reroll")
    else:
        write_new(path, draw)
    print(json.dumps({"ticket": draw["ticket"], "eligible_count": len(pool), "selected_index": index, "draw": str(path)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
