#!/usr/bin/env python3
"""Reproduce an underdetermined five-example lesson for audit target 08294dfb28a0."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
TASK = "08294dfb28a0"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def save(name: str, value: object) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_target_{TASK}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(2, h):
        for c in range(w):
            if (r, c) in seen or not 5 <= grid[r][c] <= 9:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(comp)
    return result


def crop_largest_motif(grid: list[list[int]]) -> list[list[int]]:
    comps = components(grid)
    if not comps:
        return [[0]]
    comp = max(comps, key=lambda cells: (len(cells), -min(c[0] for c in cells), -min(c[1] for c in cells)))
    r0, r1 = min(r for r, _ in comp), max(r for r, _ in comp)
    c0, c1 = min(c for _, c in comp), max(c for _, c in comp)
    color = grid[comp[0][0]][comp[0][1]]
    cell_set = set(comp)
    return [[color if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def transform(piece: list[list[int]], key: int, *, unseen_two_identity: bool = False) -> list[list[int]]:
    if key == 2 and unseen_two_identity:
        return [row[:] for row in piece]
    if key == 2:
        return [list(row) for row in zip(*piece[::-1])]
    if key == 3:
        return [row[::-1] for row in piece]
    if key == 4:
        return [row[::-1] for row in piece[::-1]]
    return [row[:] for row in piece]


def solve(grid: list[list[int]], *, unseen_two_identity: bool = False) -> list[list[int]]:
    keys = [v for v in grid[0] if 1 <= v <= 4]
    if not keys:
        return [[0]]
    motif = crop_largest_motif(grid)
    pieces = [transform(motif, key, unseen_two_identity=unseen_two_identity) for key in keys]
    h = max(len(piece) for piece in pieces)
    w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * w for _ in range(h)]
    offset = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                out[r][offset + c] = value
        offset += len(piece[0]) + 1
    return out


def main() -> int:
    generator = load_generator()
    source_sha = sha256_bytes(SOURCE.read_bytes())
    if source_sha != "a04da760bca19edbb6bd9ab6581c8cf3c538007b545fce4a346a0be0ddfadedf":
        raise RuntimeError(f"assigned source changed: {source_sha}")

    seed = 2
    band = "easy"
    samples = [generator.generate(seed, i, difficulty=band) for i in range(5)]
    checks = [generator.self_check(grid, difficulty=band) for grid in samples]
    if any(checks):
        raise AssertionError(checks)
    keys = [[v for v in grid[0] if 1 <= v <= 4] for grid in samples]

    save("input.json", samples)
    command = [
        "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
        "--input", f"../checks/audit/{TASK}/input.json",
        "--out", f"../checks/audit/{TASK}/racket.json",
    ]
    racket_path = HERE / "racket.json"
    if racket_path.exists():
        racket_path.unlink()
    completed = subprocess.run(
        command,
        cwd=WORK,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        timeout=180,
    )
    (HERE / "racket-command.log").write_text(completed.stdout + completed.stderr)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    receipt = json.loads(racket_path.read_text())
    actual = [entry["output"] for entry in receipt["results"]]
    canonical_python = [solve(grid) for grid in samples]
    if canonical_python != actual:
        raise AssertionError("independent Python rule does not match public Racket receipt")
    rival = [solve(grid, unseen_two_identity=True) for grid in samples]
    demo_matches = [rival[i] == actual[i] for i in range(4)]
    query_matches = rival[4] == actual[4]
    if not all(demo_matches) or query_matches:
        raise AssertionError({"demo_matches": demo_matches, "query_matches": query_matches})

    generation = {
        "schema": "arc-audit-generation-v1",
        "task_id": TASK,
        "generator_version": generator.VERSION,
        "generator_sha256": source_sha,
        "seed": seed,
        "difficulty": band,
        "sample_indices": list(range(5)),
        "demo_indices": list(range(4)),
        "query_index": 4,
        "keys": keys,
        "input_sha256": [grid_sha(grid) for grid in samples],
        "self_check_results": checks,
    }
    save("generation.json", generation)
    counterexample = {
        "schema": "arc-generator-audit-counterexample-v1",
        "task_id": TASK,
        "classification": "reproduced teaching defect",
        "finding": "Four demonstrations omit transform key 2; a rival that maps unseen key 2 to identity fits every demo and changes the query.",
        "generator_sha256": source_sha,
        "generator_version": generator.VERSION,
        "rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "seed": seed,
        "difficulty": band,
        "demo_sample_indices": list(range(4)),
        "query_sample_index": 4,
        "demo_keys": keys[:4],
        "query_keys": keys[4],
        "rival": "Use the canonical mappings for keys 1, 3, and 4; map unseen key 2 to identity instead of rotate-clockwise.",
        "rival_matches_each_demo": demo_matches,
        "rival_matches_query": query_matches,
        "query_input": samples[4],
        "actual_racket_output": actual[4],
        "rival_output": rival[4],
        "self_check_results": checks,
        "input_passes_generator_self_check": not any(checks),
        "belongs_to_documented_generator_domain": True,
        "apply_command": command,
        "apply_cwd": "workspace_root",
        "apply_effective_cwd": receipt.get("effective_cwd", "repo"),
        "apply_exit_code": completed.returncode,
        "evidence_paths": [
            f"checks/audit/{TASK}/generation.json",
            f"checks/audit/{TASK}/input.json",
            f"checks/audit/{TASK}/racket.json",
            f"checks/audit/{TASK}/counterexample.json",
        ],
        "limits": [
            "This is one deterministic five-example lesson, not a frequency estimate.",
            "The rival tests only the unseen-key ambiguity; it is not an exhaustive hypothesis search.",
            "No audit-target source was modified.",
        ],
    }
    save("counterexample.json", counterexample)
    print(json.dumps({
        "generator_sha256": source_sha,
        "keys": keys,
        "demo_matches": demo_matches,
        "query_matches": query_matches,
        "executed_rule_hash": receipt["executed_rule_hash"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
