"""Exhaust every cyclic start in the four-slot teaching schedule."""
from __future__ import annotations
from collections import Counter
import hashlib, json
from pathlib import Path

from reference_probe import analyze, labeled, load_generator

HERE = Path(__file__).resolve().parents[1]
GEN = load_generator()


def audit():
    rows = []
    ambiguous = []
    unique = set()
    witness_hits = Counter()
    for band in (None, "easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            grids = [GEN.generate(91000 + start, start + offset, difficulty=band) for offset in range(4)]
            pairs = [labeled(grid) for grid in grids]
            stats = [analyze(grid) for grid in grids]
            for grid in grids:
                unique.add(json.dumps(grid, separators=(",", ":")))
                for name, witness in GEN.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(witness(grid))
            rotations = []
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                reasons = GEN.lesson_identifiable(demos, pairs[held_out])
                rotations.append({"query_index": held_out, "reasons": reasons})
                if reasons:
                    ambiguous.append({"band": band, "start": start, "query_index": held_out, "reasons": reasons})
            rows.append({"band": band, "start": start, "observed": stats, "rotations": rotations})
    source = HERE / "generator.py"
    return {
        "task_id": GEN.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "lesson_count": len(rows),
        "pairs_per_lesson": 4,
        "demonstrations_per_rotation": GEN.EXAMPLES_NEEDED,
        "rotation_count": sum(len(row["rotations"]) for row in rows),
        "ambiguous_rotations": len(ambiguous),
        "unique_inputs": len(unique),
        "witness_hits": dict(sorted(witness_hits.items())),
        "ambiguities": ambiguous,
        "lessons": rows,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(1 if report["ambiguities"] else 0)
