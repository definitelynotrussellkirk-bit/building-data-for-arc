#!/usr/bin/env python3
"""Source-bound lesson/rival probe for 8922fefc96ff."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "8922fefc96ff"


def load_module(repo: Path):
    sys.path.insert(0, str(repo / "shared" / "runtime"))
    source = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def canonical_output(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        endpoints = [c for c, value in enumerate(row) if value == 7]
        if len(endpoints) == 2 and all(row[c] == 0 for c in range(endpoints[0] + 1, endpoints[1])):
            for c in range(endpoints[0], endpoints[1] + 1):
                out[r][c] = 7
    return out


def unconditional_pair_output(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        endpoints = [c for c, value in enumerate(row) if value == 7]
        if len(endpoints) == 2:
            for c in range(endpoints[0], endpoints[1] + 1):
                out[r][c] = 7
    return out


def blocked_rows(grid):
    result = []
    for r, row in enumerate(grid):
        endpoints = [c for c, value in enumerate(row) if value == 7]
        if len(endpoints) == 2:
            interior = row[endpoints[0] + 1:endpoints[1]]
            if any(value != 0 for value in interior):
                result.append({"row": r, "endpoints": endpoints, "interior": interior})
    return result


def main():
    root = Path(__file__).resolve().parents[3]
    repo = root / "repo"
    module, source = load_module(repo)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    census = {}
    witness = None
    for band in ("easy", "medium", "hard"):
        stats = {
            "lessons": 100,
            "pair_draws": 500,
            "pairs_with_blocked_row": 0,
            "rival_survives_all_four_demos": 0,
            "survives_demos_and_changes_query": 0,
        }
        for seed in range(100):
            grids = [module.generate(seed, index, difficulty=band) for index in range(5)]
            stats["pairs_with_blocked_row"] += sum(bool(blocked_rows(grid)) for grid in grids)
            truths = [canonical_output(grid) for grid in grids]
            rivals = [unconditional_pair_output(grid) for grid in grids]
            survives = all(rivals[i] == truths[i] for i in range(4))
            if survives:
                stats["rival_survives_all_four_demos"] += 1
            if survives and rivals[4] != truths[4]:
                stats["survives_demos_and_changes_query"] += 1
                if witness is None:
                    witness = {
                        "band": band,
                        "seed": seed,
                        "sample_indices": list(range(5)),
                        "inputs": grids,
                        "canonical_python_outputs": truths,
                        "rival_outputs": rivals,
                        "query_blocked_rows": blocked_rows(grids[4]),
                        "query_self_check": module.self_check(grids[4]),
                    }
        census[band] = stats

    if witness is None:
        raise SystemExit("no witness found in the bounded census")

    payload = {
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": source_sha,
        "rival": "fill every row with exactly two orange cells, ignoring whether the interior is empty",
        "ordinary_lesson_census": census,
        "witness": witness,
        "limits": "Finite census of 100 five-pair lessons per band; four demonstrations followed by one query; one named rival only. Canonical Python results are corroborated by separate Racket apply evidence for the retained witness.",
    }
    out = Path(__file__).with_name("report.json")
    out.write_text(json.dumps(payload, indent=2) + "\n")
    Path(__file__).with_name("episode-inputs.json").write_text(json.dumps({"inputs": witness["inputs"]}, indent=2) + "\n")
    Path(__file__).with_name("rival-outputs.json").write_text(json.dumps({"outputs": witness["rival_outputs"]}, indent=2) + "\n")
    print(json.dumps({"report": str(out), "sha256": source_sha, "census": census, "witness": {k: v for k, v in witness.items() if k not in {"inputs", "canonical_python_outputs", "rival_outputs"}}}, indent=2))


if __name__ == "__main__":
    main()
