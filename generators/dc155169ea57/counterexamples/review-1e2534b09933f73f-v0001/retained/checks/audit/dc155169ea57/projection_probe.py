from __future__ import annotations

import hashlib
import json
from pathlib import Path

from generators.dc155169ea57 import generator

ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = ROOT / "checks" / "audit" / generator.TASK_ID / "input.json"
RACKET_PATH = ROOT / "checks" / "audit" / generator.TASK_ID / "racket.json"
CANONICAL_PATH = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
GENERATOR_PATH = ROOT / "repo" / "generators" / generator.TASK_ID / "generator.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid: list[list[int]], line: int) -> list[list[tuple[int, int]]]:
    return generator._components(grid, 1, below=line)


def projection_overlap(grid: list[list[int]]) -> bool:
    line = next(r for r, row in enumerate(grid) if all(v == 2 for v in row))
    comps = components(grid, line)
    colsets = [{c for _, c in comp} for comp in comps]
    return any(colsets[i] & colsets[j] for i in range(len(colsets)) for j in range(i + 1, len(colsets)))


def projection_group_rival(grid: list[list[int]]) -> list[list[int]]:
    """Merge disconnected blue components whenever their column projections overlap."""
    h, w = len(grid), len(grid[0])
    line = next(r for r, row in enumerate(grid) if all(v == 2 for v in row))
    comps = components(grid, line)
    groups = [set(comp) for comp in comps]
    changed = True
    while changed:
        changed = False
        out: list[set[tuple[int, int]]] = []
        while groups:
            group = groups.pop()
            cols = {c for _, c in group}
            merged = True
            while merged:
                merged = False
                keep = []
                for other in groups:
                    other_cols = {c for _, c in other}
                    if cols & other_cols:
                        group |= other
                        cols |= other_cols
                        merged = True
                        changed = True
                    else:
                        keep.append(other)
                groups = keep
            out.append(group)
        groups = out

    result = [[8 if r < line and v == 1 else v for v in row] for r, row in enumerate(grid)]
    pass_cols: set[int] = set()
    for group in groups:
        row_counts: dict[int, int] = {}
        for r, _ in group:
            row_counts[r] = row_counts.get(r, 0) + 1
        wide_rows = [r for r, count in row_counts.items() if count > 1]
        if wide_rows:
            delta = line - 1 - max(wide_rows)
        else:
            delta = h - 1 - max(r for r, _ in group)
            pass_cols.update(c for _, c in group)
        for r, c in group:
            nr = r + delta
            if 0 <= nr < h:
                result[nr][c] = 1
    for c in pass_cols:
        result[line][c] = 8
    return result


def canonical_inputs() -> list[list[list[int]]]:
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == generator.TASK_ID:
            return [pair["input"] for pair in row.get("train", [])] + [pair["input"] for pair in row.get("test", [])]
    raise RuntimeError("canonical task missing")


def main() -> None:
    grid = json.loads(INPUT_PATH.read_text())
    racket = json.loads(RACKET_PATH.read_text())
    authority = racket["results"][0]["output"]
    rival = projection_group_rival(grid)
    validator = generator.self_check(grid)
    assert validator == [], validator
    assert authority == generator.rule_mirror(grid)
    assert authority != rival

    generated = {}
    for band in ("easy", "medium", "hard"):
        overlaps = 0
        self_check_failures = 0
        for seed in range(1000):
            sample = generator.generate(seed, seed, difficulty=band)
            self_check_failures += bool(generator.self_check(sample, difficulty=band))
            overlaps += projection_overlap(sample)
        generated[band] = {
            "seed_range": [0, 999],
            "draws": 1000,
            "projection_overlap_draws": overlaps,
            "self_check_failures": self_check_failures,
        }

    canon = canonical_inputs()
    report = {
        "schema": "audit_projection_shortcut_v1",
        "task_id": generator.TASK_ID,
        "generator_sha256": sha256(GENERATOR_PATH),
        "rule_hash": racket["executed_rule_hash"],
        "counterexample": {
            "input_path": "checks/audit/dc155169ea57/input.json",
            "input": grid,
            "passes_target_self_check": not validator,
            "self_check_errors": validator,
            "profile_signature": generator.profile_signature(grid),
            "authority_output": authority,
            "rival": "merge disconnected color-1 components whose column projections overlap, then apply the same thin/wide fall rule to each projection group",
            "rival_output": rival,
            "outputs_disagree": authority != rival,
            "disagreement_cells": [
                [r, c, authority[r][c], rival[r][c]]
                for r in range(len(grid))
                for c in range(len(grid[0]))
                if authority[r][c] != rival[r][c]
            ],
            "racket_evidence": "checks/audit/dc155169ea57/racket.json",
        },
        "canonical_census": {
            "inputs": len(canon),
            "projection_overlap_inputs": sum(projection_overlap(x) for x in canon),
            "rival_matches_authority_inputs": sum(
                projection_group_rival(x) == generator.rule_mirror(x) for x in canon
            ),
        },
        "generated_census": generated,
        "limits": "Finite census over seeds 0..999 per band. Static placement uses disjoint left-to-right column bands, so the observed zero is also implied by the current construction, but this report does not claim anything about future source versions.",
        "command": ["env", "PYTHONPATH=.:shared/runtime", "python3", "../checks/audit/dc155169ea57/projection_probe.py"],
        "cwd": "repo",
    }
    out = ROOT / "checks" / "audit" / generator.TASK_ID / "projection_probe.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "checks" / "audit" / generator.TASK_ID / "rival_output.json").write_text(json.dumps(rival, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
