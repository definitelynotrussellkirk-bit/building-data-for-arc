#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter

TASK_ID = "c5a96370d612"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = Path(__file__).resolve().parent


def load_generator():
    body = GENERATOR_PATH.read_bytes()
    spec = importlib.util.spec_from_file_location("audit_c5_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    exec(compile(body, str(GENERATOR_PATH), "exec"), module.__dict__)
    return module, hashlib.sha256(body).hexdigest()


def canonical_row():
    for line in CANONICAL_PATH.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise KeyError(TASK_ID)


def runs(grid):
    result = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            color = row[c]
            end = c
            while end + 1 < len(row) and row[end + 1] == color:
                end += 1
            result.append({"row": r, "start": c, "end": end, "color": color, "length": end - c + 1})
            c = end + 1
    return result


def extend_every_run(grid):
    out = [list(row) for row in grid]
    for run in runs(grid):
        right = run["end"] + 1
        if right < len(out[0]) and grid[run["row"]][right] == 0:
            out[run["row"]][right] = run["color"]
    return out


def main():
    gen, source_sha = load_generator()
    sample = {}
    total = Counter()
    failures = []
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        unique = set()
        for index in range(100):
            seed = 700_000 + index * 37
            try:
                grid = gen.generate(seed, index, difficulty=band)
                diagnostics = gen.self_check(grid)
                if diagnostics:
                    raise AssertionError(diagnostics)
                unique.add(json.dumps(grid, separators=(",", ":")))
                for run in runs(grid):
                    counts[run["length"]] += 1
                    total[run["length"]] += 1
            except Exception as exc:
                failures.append({"band": band, "index": index, "seed": seed, "error": f"{type(exc).__name__}: {exc}"})
        sample[band] = {"draws": 100, "unique_inputs": len(unique), "run_lengths": dict(sorted(counts.items()))}

    canonical = canonical_row()
    pair = canonical["train"][1]
    input_grid = pair["input"]
    expected = pair["output"]
    rival = extend_every_run(input_grid)
    (OUT / "input.json").write_text(json.dumps(input_grid, indent=2) + "\n")
    (OUT / "rival-output.json").write_text(json.dumps(rival, indent=2) + "\n")

    length3 = gen.generate(1, 0, texture="length_3_run")
    touching = gen.generate(1, 0, texture="dominoes_touching")
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "sample": {
            "seed_formula": "700000 + 37 * index",
            "sample_index_range": [0, 99],
            "bands": sample,
            "total_run_lengths": dict(sorted(total.items())),
            "failures": failures,
        },
        "validator_reproductions": {
            "length_3_run": {"input": length3, "self_check": gen.self_check(length3), "runs": runs(length3)},
            "dominoes_touching": {"input": touching, "self_check": gen.self_check(touching), "runs": runs(touching)},
        },
        "counterexample": {
            "scope": "canonical train pair 1",
            "input": input_grid,
            "expected_output": expected,
            "rival": "extend every nonzero horizontal run by one when its right neighbor is zero, regardless of run length",
            "rival_output": rival,
            "rival_fits_sampled_normal_domain": set(total) == {2},
            "rival_differs_from_expected": rival != expected,
            "canonical_runs": runs(input_grid),
        },
    }
    (OUT / "probe-result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "sampled_draws": 300,
        "run_lengths": dict(sorted(total.items())),
        "failures": len(failures),
        "length3_self_check": gen.self_check(length3),
        "touching_self_check": gen.self_check(touching),
        "rival_differs": rival != expected,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
