from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import time
from collections import Counter
from pathlib import Path

TICKET_ID = "ticket-a3f2df44fc733942"
TICKET_SEED = "4edadde2228f1e5c54e33660f53324f03cd490e238b74719e2317b15eaff5fde"
EXPECTED_SOURCE_SHA256 = "1b6782f0c8e7f177d427cd8f901e9c49faa310bd187ba1915d7fd33de8add3de"
EXPECTED_RULE_HASH = "2d7db8fb7aa9"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = ROOT / "generators" / "2636c90a673a" / "generator.py"
OUT = Path(__file__).resolve().parent


def load_generator():
    actual = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    if actual != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("ticket_2636", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.RULE_HASH != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule hash mismatch: {module.RULE_HASH}")
    return module, actual


def intended(grid):
    keep = [i for i, value in enumerate(grid[0]) if value == 1]
    return [[row[i] for i in keep] for row in grid[1:]]


def schedule_frequency_rival(grid):
    """Exploit the default two-phase selector/decoy count schedule."""
    counts = Counter(value for value in grid[0] if value != 0)
    modal = max(counts.values())
    if modal == 3:
        candidates = [value for value, count in counts.items() if count == 2]
        marker = min(candidates) if candidates else min(counts, key=lambda v: (-counts[v], v))
    else:
        marker = min(counts, key=lambda v: (-counts[v], v))
    keep = [i for i, value in enumerate(grid[0]) if value == marker]
    return [[row[i] for i in keep] for row in grid[1:]]


def main():
    started = time.monotonic()
    gen, source_sha = load_generator()
    rng = random.Random(int(TICKET_SEED, 16))

    samples = []
    by_band = {}
    for band in ("easy", "medium", "hard"):
        band_rows = []
        for _ in range(40):
            seed = rng.randrange(0, 2**31)
            sample_index = rng.randrange(0, 2**20)
            grid = gen.generate(seed, sample_index, difficulty=band)
            target = intended(grid)
            rival = schedule_frequency_rival(grid)
            row = {
                "seed": seed,
                "sample_index": sample_index,
                "header_counts": dict(sorted(Counter(grid[0]).items())),
                "matches": rival == target,
            }
            band_rows.append(row)
            samples.append(row | {"difficulty": band})
        by_band[band] = {
            "draws": len(band_rows),
            "matches": sum(row["matches"] for row in band_rows),
            "header_count_shapes": dict(
                Counter(str(tuple(sorted(Counter(gen.generate(row["seed"], row["sample_index"], difficulty=band)[0]).values()))) for row in band_rows)
            ),
        }

    # Use the ticket seed to choose a deterministic traversal order over lawful
    # exact-control candidates. The first separating witness is retained.
    candidates = [(seed, sample_index, band) for band in ("easy", "medium", "hard")
                  for seed in range(32) for sample_index in range(8)]
    rng.shuffle(candidates)
    witness = None
    for seed, sample_index, band in candidates:
        grid = gen.generate(seed, sample_index, difficulty=band, n_keep=3)
        target = intended(grid)
        rival = schedule_frequency_rival(grid)
        if rival != target:
            witness = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": band,
                "overrides": {"n_keep": 3},
                "input": grid,
                "self_check": gen.self_check(grid),
                "header_counts": dict(sorted(Counter(grid[0]).items())),
                "intended_output": target,
                "schedule_frequency_rival_output": rival,
            }
            break
    if witness is None:
        raise RuntimeError("no separating lawful exact-control witness found")

    input_path = OUT / "witness-input.json"
    input_path.write_text(json.dumps({"input": witness["input"]}, separators=(",", ":")) + "\n")
    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "ticket_seed": TICKET_SEED,
        "task_id": gen.TASK_ID,
        "source_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "scope": "one deterministic 120-draw default probe plus one lawful exact-control witness",
        "default_probe": {
            "draws": len(samples),
            "matches": sum(row["matches"] for row in samples),
            "all_match": all(row["matches"] for row in samples),
            "by_band": by_band,
        },
        "witness": witness,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "conclusion": (
            "finding: the schedule-aware frequency rival fits every bounded default draw "
            "but is not authority-equivalent because a lawful n_keep=3 override separates it"
        ),
    }
    (OUT / "probe-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "draws": result["default_probe"]["draws"],
        "matches": result["default_probe"]["matches"],
        "witness": {k: witness[k] for k in ("seed", "sample_index", "difficulty", "overrides", "header_counts", "self_check")},
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
