"""Reproduce the default three-demo omitted-key teaching defect."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
TASK = "5faf9d5e3e6d"
SOURCE = ROOT / "generators" / TASK / "generator.py"
EPISODE_PATH = OUT / "default_episode.jsonl"


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_5faf", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def crop_body(grid):
    body = [row[:] for row in grid]
    body[0][0] = 0
    cells = [(r, c) for r, row in enumerate(body) for c, v in enumerate(row) if v]
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [row[c0:c1+1] for row in body[r0:r1+1]]


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid):
    return [row[::-1] for row in grid]


def canonical(grid):
    key = grid[0][0]
    body = crop_body(grid)
    return {1: body, 2: rotate_cw(body), 3: rotate_180(body), 4: flip_lr(body)}[key]


def rival(grid):
    key = grid[0][0]
    body = crop_body(grid)
    # Agree on every supplied demo key; map the unseen identity key to clockwise.
    return {1: rotate_cw(body), 2: rotate_cw(body), 3: rotate_180(body), 4: flip_lr(body)}[key]


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    mod = load_generator()
    rows = [json.loads(line) for line in EPISODE_PATH.read_text().splitlines() if line.strip()]
    assert len(rows) == 1
    episode = rows[0]
    train = episode["train"]
    test = episode["test"]
    assert len(train) == 3 and len(test) == 1
    demo_keys = [pair["input"][0][0] for pair in train]
    query = test[0]
    query_key = query["input"][0][0]
    assert demo_keys == [2, 3, 4] and query_key == 1
    assert all(canonical(pair["input"]) == pair["output"] for pair in train + test)
    assert all(rival(pair["input"]) == pair["output"] for pair in train)
    rival_query = rival(query["input"])
    assert rival_query != query["output"]

    unseen = 0
    total = 0
    examples = []
    for seed in range(12):
        for band in ("easy", "medium", "hard"):
            for window in range(10):
                start = 4 * window
                keys = [
                    mod._scheduled_value(
                        seed, start + offset, "key", (1, 2, 3, 4), (1, 2, 3, 4)
                    )
                    for offset in range(4)
                ]
                total += 1
                missing = keys[3] not in keys[:3]
                unseen += int(missing)
                if missing and len(examples) < 8:
                    examples.append({"seed": seed, "difficulty": band, "start": start, "keys": keys})
    assert (unseen, total) == (207, 360)

    analysis = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "episode_generator_sha256": episode["provenance"]["generator_sha256"],
        "rule_hash": episode["executed_rule_hash"],
        "seed": episode["seed"],
        "sample_indices": episode["sample_indices"],
        "resolved_n_train": episode["provenance"]["demonstration_policy"]["resolved_n_train"],
        "declared_minimum": episode["provenance"]["demonstration_policy"]["declared_minimum"],
        "lesson_contract": episode["lesson_check"],
        "demo_keys": demo_keys,
        "query_key": query_key,
        "rival": "keys 2/3/4 canonical; unseen key 1 is rotate-cw instead of identity",
        "rival_matches_all_demonstrations": True,
        "rival_disagrees_on_query": True,
        "query_input_sha256": grid_hash(query["input"]),
        "canonical_query_output_sha256": grid_hash(query["output"]),
        "rival_query_output_sha256": grid_hash(rival_query),
        "structural_census": {
            "seeds": list(range(12)),
            "difficulties": ["easy", "medium", "hard"],
            "four_pair_stride_windows_per_seed_band": 10,
            "unseen_query_key_windows": unseen,
            "total_windows": total,
            "examples": examples,
            "scope": "key schedule only; exact retained episode is Racket-labelled",
        },
    }
    assert analysis["generator_sha256"] == analysis["episode_generator_sha256"]
    (OUT / "input.json").write_text(json.dumps(query["input"], indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps({"output": rival_query}, indent=2) + "\n")
    (OUT / "analysis.json").write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps(analysis, sort_keys=True))


if __name__ == "__main__":
    main()
