#!/usr/bin/env python3
"""Replay the retained lesson and score the canonical size-4 shortcut."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "d292e3214bb1"
EXPECTED_GENERATOR_SHA256 = "7d5d52380ad5d8a91ead2d79833755285942d236f86d5745737247d480452ffe"
HERE = Path(__file__).resolve().parent
EPISODE = HERE / "ambiguous-lesson.jsonl"
GENERATOR = HERE.parents[2] / "repo" / "generators" / TASK_ID / "generator.py"
CANONICAL = HERE.parents[2] / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
RACKET = HERE / "racket.json"
RUNTIME = HERE.parents[2] / "repo" / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair for split in ("train", "test") for pair in row.get(split, [])]
    raise KeyError(TASK_ID)


def red_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] != 2 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 2:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def recolor_size_four(grid):
    """Plausible shortcut: recolor the unique four-cell red component."""
    out = [row[:] for row in grid]
    for cells in red_components(grid):
        if len(cells) == 4:
            for row, col in cells:
                out[row][col] = 8
    return out


def main() -> int:
    episode = json.loads(EPISODE.read_text().splitlines()[0])
    racket = json.loads(RACKET.read_text())
    generator = load_generator()
    generator_hash = sha256(GENERATOR)
    assert generator_hash == EXPECTED_GENERATOR_SHA256
    assert racket["generator_sha256"] == generator_hash
    demo_matches = [recolor_size_four(pair["input"]) == pair["output"] for pair in episode["train"]]
    demo_sizes = [sorted((len(c) for c in red_components(pair["input"])), reverse=True) for pair in episode["train"]]
    query = episode["test"][0]
    rival = recolor_size_four(query["input"])
    intended = query["output"]
    query_sizes = sorted((len(c) for c in red_components(query["input"])), reverse=True)
    diffs = [
        [r, c, rival[r][c], intended[r][c]]
        for r in range(len(intended))
        for c in range(len(intended[0]))
        if rival[r][c] != intended[r][c]
    ]
    authoritative = racket["results"][0]["output"]
    assert authoritative == intended
    self_check_findings = generator.self_check(query["input"])
    canonical = canonical_pairs()
    canonical_matches = [recolor_size_four(pair["input"]) == pair["output"] for pair in canonical]
    report = {
        "schema": "arcpuzzles-audit-shortcut-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_hash,
        "episode_sha256": sha256(EPISODE),
        "seed": episode["seed"],
        "sample_indices": episode["sample_indices"],
        "difficulty": episode["provenance"]["difficulty"],
        "executed_rule_hash": episode["executed_rule_hash"],
        "racket_apply_sha256": sha256(RACKET),
        "racket_input_sha256": racket["results"][0]["input_sha256"],
        "racket_output_sha256": racket["results"][0]["output_sha256"],
        "racket_command": racket["command"],
        "racket_cwd": racket["cwd"],
        "input_self_check_findings": self_check_findings,
        "input_in_declared_domain": not self_check_findings,
        "canonical_pair_matches": canonical_matches,
        "canonical_matches": sum(canonical_matches),
        "canonical_pairs": len(canonical_matches),
        "rival": "recolor every size-4 color-2 component to 8",
        "demo_component_sizes": demo_sizes,
        "query_component_sizes": query_sizes,
        "demo_matches": demo_matches,
        "all_demos_match": all(demo_matches),
        "query_matches": rival == intended,
        "query_input": query["input"],
        "intended_output": intended,
        "rival_output": rival,
        "differing_cells": diffs,
    }
    (HERE / "shortcut_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (HERE / "rival.json").write_text(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": generator_hash,
        "executed_rule_hash": racket["executed_rule_hash"],
        "input": query["input"],
        "racket_output": authoritative,
        "rival_output": rival,
        "differing_cells": diffs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("task_id", "seed", "sample_indices", "demo_component_sizes", "query_component_sizes", "all_demos_match", "query_matches", "differing_cells")}, indent=2))
    return 0 if report["all_demos_match"] and not report["query_matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
