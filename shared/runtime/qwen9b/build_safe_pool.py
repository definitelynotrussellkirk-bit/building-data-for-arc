#!/usr/bin/env python3
"""Build the SAFE-tagged pool assets for the live generator lane.

Reads the generator assignment queue and writes:

  safe_pool.json      {task_id: recommended_mix_weight} for every task whose
                      train_safety is reviewed_safe (tier-1) — the ONLY tasks
                      the live lane may draw. Tier-2 (reviewed_standard,
                      provisionally_safe) joins only behind --tier2 and is
                      tagged in the manifest.
  safe_pool_manifest.json  provenance: queue sha256, counts, drops, timestamp.

A task is DROPPED (loud, listed in the manifest) when it is safe-tagged but
lacks a per_puzzle generator directory or a canonical row with a non-empty
program_solution — the live lane cannot produce verified rows for it.

  python3 qwen9b/build_safe_pool.py [--tier2] [--out-dir qwen9b/colab/assets]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data/derived/kimi_generator_assignment.jsonl"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
GEN_ROOT = ROOT / "puzzle_generators/per_puzzle"

TIER1 = {"reviewed_safe"}
TIER2 = {"reviewed_standard", "provisionally_safe"}


def load_queue(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def load_canonical_index(path: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            task_id = row.get("task_id")
            if task_id and (row.get("program_solution") or "").strip():
                index[task_id] = row
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--queue", default=str(QUEUE))
    parser.add_argument("--canonical", default=str(CANONICAL))
    parser.add_argument("--tier2", action="store_true",
                        help="also admit reviewed_standard / provisionally_safe (tier-2, tagged)")
    parser.add_argument("--out-dir", default=str(ROOT / "qwen9b/colab/assets"))
    args = parser.parse_args()

    queue_path = Path(args.queue)
    canonical_path = Path(args.canonical)
    rows = load_queue(queue_path)
    canonical = load_canonical_index(canonical_path)

    tiers = TIER1 | (TIER2 if args.tier2 else set())
    pool: dict[str, float] = {}
    tier_of: dict[str, int] = {}
    dropped: list[dict] = []
    for row in rows:
        safety = row.get("train_safety")
        if safety not in tiers or row.get("active_semantic_veto"):
            continue
        weight = float(row.get("recommended_mix_weight") or 0.0)
        if weight <= 0:
            continue
        task_id = row["task_id"]
        if not (GEN_ROOT / task_id).is_dir():
            dropped.append({"task_id": task_id, "reason": "no per_puzzle generator dir"})
            continue
        if task_id not in canonical:
            dropped.append({"task_id": task_id, "reason": "no canonical program_solution"})
            continue
        pool[task_id] = weight
        tier_of[task_id] = 1 if safety in TIER1 else 2

    if not pool:
        raise SystemExit("LOUD: safe pool is empty — refusing to write assets")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pool_path = out_dir / "safe_pool.json"
    pool_path.write_text(json.dumps(pool, indent=1, sort_keys=True) + "\n")
    manifest = {
        "schema_version": "qwen9b_safe_pool_v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "queue": str(queue_path),
        "queue_sha256": hashlib.sha256(queue_path.read_bytes()).hexdigest(),
        "canonical": str(canonical_path),
        "canonical_sha256": hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
        "tier2_included": bool(args.tier2),
        "tasks": len(pool),
        "tier1": sum(1 for t in tier_of.values() if t == 1),
        "tier2": sum(1 for t in tier_of.values() if t == 2),
        "total_weight": round(sum(pool.values()), 4),
        "dropped": dropped,
    }
    manifest_path = out_dir / "safe_pool_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=1, sort_keys=True))
    print(f"wrote {pool_path} ({len(pool)} tasks) + {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
