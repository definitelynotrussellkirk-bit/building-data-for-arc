from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
SOURCE = REPO / "generators" / "7c105b75673c" / "generator.py"
INPUT_PATH = Path(__file__).with_name("input.json")
RACKET_PATH = Path(__file__).with_name("racket.json")

spec = importlib.util.spec_from_file_location("audited_7c105b75673c", SOURCE)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def tile_bounds(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = []
    prev = -1
    for c in dividers + [w]:
        if c - prev - 1 > 0:
            bounds.append((prev + 1, c))
        prev = c
    return bounds


def tile_counts(grid):
    return [
        sum(grid[r][c] not in (0, 9) for r in range(len(grid)) for c in range(c0, c1))
        for c0, c1 in tile_bounds(grid)
    ]


def unique_count_only(grid):
    counts = tile_counts(grid)
    frequencies = Counter(counts)
    candidates = [i for i, count in enumerate(counts) if frequencies[count] == 1]
    return [[8 if len(candidates) == 1 and c == candidates[0] else 0 for c in range(len(counts))]]


grid = json.loads(INPUT_PATH.read_text())
racket = json.loads(RACKET_PATH.read_text())
actual = racket["results"][0]["output"]
rival = unique_count_only(grid)

# The imported canonical lesson also exposes the same nuisance shortcut.
canonical_record = None
for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
    candidate = json.loads(line)
    if candidate.get("task_id") == gen.TASK_ID:
        canonical_record = candidate
        break
assert canonical_record is not None
canonical_pairs = []
for split, pairs in (("train", canonical_record["train"]), ("test", [canonical_record["test"]])):
    for index, pair in enumerate(pairs):
        counts = tile_counts(pair["input"])
        frequencies = Counter(counts)
        canonical_pairs.append({
            "split": split,
            "index": index,
            "tile_nonbackground_counts": counts,
            "unique_cell_count_shortcut_available": sum(v == 1 for v in frequencies.values()) == 1,
            "output": pair["output"],
        })

sample_stats = {}
for band_index, band in enumerate(("easy", "medium", "hard")):
    draws = 100
    unique_count_witnesses = 0
    validator_failures = 0
    for i in range(draws):
        generated = gen.generate(73000 + band_index * 1000 + i, i, difficulty=band)
        validator_failures += bool(gen.self_check(generated))
        counts = tile_counts(generated)
        freq = Counter(counts)
        unique_count_witnesses += sum(v == 1 for v in freq.values()) == 1
    sample_stats[band] = {
        "draws": draws,
        "validator_failures": validator_failures,
        "unique_cell_count_shortcut_available": unique_count_witnesses,
    }

report = {
    "schema": "audit-equal-area-odd-tile-v1",
    "task_id": gen.TASK_ID,
    "version": gen.VERSION,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "executed_rule_hash": racket["executed_rule_hash"],
    "input_sha256": racket["results"][0]["input_sha256"],
    "validator_errors": gen.self_check(grid),
    "tile_nonbackground_counts": tile_counts(grid),
    "actual_racket_output": actual,
    "unique_cell_count_rival_output": rival,
    "rival_disagrees": rival != actual,
    "canonical_pairs": canonical_pairs,
    "generator_sample": sample_stats,
    "domain_note": (
        "The input is accepted by self_check and the selected Racket rule, but the current "
        "generator deliberately emits an odd tile with a different cell count."
    ),
    "commands": [
        {
            "cwd": "repo",
            "argv": [
                "python3", "-m", "arcpuzzles", "apply", "7c105b75673c",
                "--input", "../checks/audit/7c105b75673c/input.json",
                "--out", "../checks/audit/7c105b75673c/racket.json"
            ],
        },
        {"cwd": "repo", "argv": ["python3", "../checks/audit/7c105b75673c/probe.py"]},
    ],
}
Path(__file__).with_name("counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
