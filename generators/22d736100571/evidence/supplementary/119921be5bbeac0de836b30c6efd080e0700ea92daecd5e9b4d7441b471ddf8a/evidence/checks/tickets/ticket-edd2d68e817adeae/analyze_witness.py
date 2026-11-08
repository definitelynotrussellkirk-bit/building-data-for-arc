from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators/22d736100571/generator.py"
EPISODE = HERE / "lesson.jsonl"
OUT = HERE / "witness.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_neighbor_rival(grid):
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            horizontal = c > 0 and c + 1 < w and grid[r][c - 1] == 2 and grid[r][c + 1] == 2
            vertical = r > 0 and r + 1 < h and grid[r - 1][c] == 2 and grid[r + 1][c] == 2
            if horizontal or vertical:
                out[r][c] = 2
    return out


def main() -> None:
    g = load_generator()
    episode = json.loads(EPISODE.read_text().splitlines()[0])
    pairs = episode["train"] + episode["test"]
    fits = [local_neighbor_rival(pair["input"]) == pair["output"] for pair in pairs]
    query = episode["test"][0]
    rival_output = local_neighbor_rival(query["input"])
    differences = [
        {"row": r, "column": c, "reference": query["output"][r][c], "rival": rival_output[r][c]}
        for r in range(len(query["input"]))
        for c in range(len(query["input"][0]))
        if query["output"][r][c] != rival_output[r][c]
    ]
    result = {
        "schema": "arcpuzzles-adversarial-witness-ticket-v1",
        "ticket_id": "ticket-edd2d68e817adeae",
        "task_id": "22d736100571",
        "source_path": "repo/generators/22d736100571/generator.py",
        "source_sha256": sha256(SOURCE),
        "expected_source_sha256": "67378d6b4be7a0d84490fdc90a8bb4e94a09e75854eb9ee6b1cfdb3ae7f768b6",
        "source_matches_pin": sha256(SOURCE) == "67378d6b4be7a0d84490fdc90a8bb4e94a09e75854eb9ee6b1cfdb3ae7f768b6",
        "rule_hash": episode["executed_rule_hash"],
        "rival": "Fill an original zero only when its immediate horizontal or vertical neighbors are both red, in one simultaneous pass.",
        "lesson": {
            "seed": episode["seed"],
            "difficulty": "easy",
            "sample_indices": episode["sample_indices"],
            "accepted_indices": [row["sample_index"] for row in episode["sampling"]["accepted_pairs"]],
            "rejections": episode["sampling"]["rejections"],
            "train_rival_fits": fits[: len(episode["train"])],
            "query_rival_fits": fits[len(episode["train"]):],
        },
        "validator_errors": g.self_check(query["input"]),
        "query_input": query["input"],
        "racket_output": query["output"],
        "rival_output": rival_output,
        "differing_cells": differences,
        "status": "reproduced_teaching_ambiguity" if all(fits[:3]) and not fits[3] else "not_reproduced",
        "limits": [
            "One ordered seed-0 easy lesson only; no broad census was run.",
            "This is a teaching-support finding, not a wrong Racket label.",
            "The target also has separate retained override-contract findings that were not re-probed here.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    assert result["source_matches_pin"]
    assert not result["validator_errors"]
    assert result["lesson"]["train_rival_fits"] == [True, True, True]
    assert result["lesson"]["query_rival_fits"] == [False]
    assert differences == [{"row": 2, "column": 7, "reference": 0, "rival": 2}]
    print(json.dumps({
        "status": result["status"],
        "train_rival_fits": result["lesson"]["train_rival_fits"],
        "query_rival_fits": result["lesson"]["query_rival_fits"],
        "differing_cells": differences,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
