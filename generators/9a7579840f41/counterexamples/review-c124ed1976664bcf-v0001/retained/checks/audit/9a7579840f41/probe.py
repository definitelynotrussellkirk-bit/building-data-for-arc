"""Reproduce the current color-1-local-corners domain question for 9a7579840f41."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "9a7579840f41"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_color1_corner_rival(gen, grid):
    h, w = len(grid), len(grid[0])
    wire = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    shape = gen._normalize(
        [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    )
    corners = [
        (r, c)
        for r, c in wire
        if (((r - 1, c) in wire or (r + 1, c) in wire)
            and ((r, c - 1) in wire or (r, c + 1) in wire))
    ]
    out = [[0] * w for _ in range(h)]
    for r, c in corners:
        for dr, dc in shape:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 4
    return out


def connected_start_component_mirror(gen, grid):
    h, w = len(grid), len(grid[0])
    path, error = gen._trace_wire_from_start(grid)
    if not path:
        raise ValueError(error or "no start-connected path")
    shape = gen._normalize(
        [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    )
    out = [[0] * w for _ in range(h)]
    for r, c in gen._turns(path):
        for dr, dc in shape:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 4
    return out


def main() -> None:
    gen = load_generator()
    grid = json.loads((HERE / "input.json").read_text())
    rival = local_color1_corner_rival(gen, grid)
    independent = connected_start_component_mirror(gen, grid)
    (HERE / "rival_output.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "independent_output.json").write_text(json.dumps(independent, indent=2) + "\n")

    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_matches = sum(
        local_color1_corner_rival(gen, pair["input"]) == pair["output"]
        for pair in canonical
    )
    generated_matches = 0
    generated_total = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(100):
            sample = gen.generate(
                970_000 + band_index * 10_000 + i,
                23 * i + 11,
                difficulty=band,
            )
            generated_total += 1
            generated_matches += int(
                local_color1_corner_rival(gen, sample) == gen.rule_mirror(sample)
            )

    racket_path = HERE / "racket.json"
    racket_record = json.loads(racket_path.read_text()) if racket_path.exists() else None
    actual = racket_record["results"][0]["output"] if racket_record else None
    differences = [
        [r, c, actual[r][c], rival[r][c]]
        for r in range(len(rival))
        for c in range(len(rival[0]))
        if actual is not None and actual[r][c] != rival[r][c]
    ]
    evidence = {
        "schema": "arcpuzzles-audit-local-corners-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "ignore color 7 and stamp the normalized color-4 template at every local orthogonal corner of every color-1 component",
        "canonical_matches": f"{canonical_matches}/{len(canonical)}",
        "generated_matches": f"{generated_matches}/{generated_total}",
        "generated_sampler": "100 each easy/medium/hard; seed=970000+band*10000+i; sample_index=23*i+11",
        "counterexample": {
            "self_check_errors": gen.self_check(grid),
            "strict_canonical_like_errors": gen.strict_canonical_like(grid),
            "racket_present": racket_record is not None,
            "racket_generator_sha256": racket_record.get("generator_sha256") if racket_record else None,
            "rule_hash_matches_catalog": racket_record.get("rule_hash_matches_catalog") if racket_record else None,
            "authority_matches_start_component_mirror": actual == independent if actual else None,
            "authority_matches_rival": actual == rival if actual else None,
            "differing_cells": differences,
        },
        "finding": (
            "This is a domain question, not an accepted-domain output mismatch: the separator adds a disconnected "
            "L-shaped color-1 component and is rejected by self_check. On the emitted single-component wire grammar, "
            "the local-corners rival is answer-equivalent and makes color 7 causally unnecessary."
        ),
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
