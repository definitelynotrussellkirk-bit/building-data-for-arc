#!/usr/bin/env python3
"""Bounded lawful witness for a centroid-distance shortcut on 25e18d9bd322."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "25e18d9bd322"
TICKET = "ticket-4964d90872b2b95e"
PROBE_SEED = "61c17e4abc99437c6417c701d58f6e8b87816fdc402bc86c97163af32f9da497"
SOURCE_SHA256 = "62c31795ef3e67c6bc7bddd21508b6ea8a416d604dea01ad4ea51e89313ab406"
RULE_HASH = "f275e1e6250c"
SOURCE = REPO / "generators" / TASK / "generator.py"
OUT = HERE / "witness.json"
MAX_DRAWS = 512


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())[:12]


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_25e18_generator", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = set()
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    program = programs.pop()
    assert normalized_rule_hash(program) == RULE_HASH
    return program


def crop(grid, obj):
    r1, c1, r2, c2 = obj["bbox"]
    out = [[0 for _ in range(c2 - c1 + 1)] for _ in range(r2 - r1 + 1)]
    for r, c in obj["cells"]:
        out[r - r1][c - c1] = grid[r][c]
    return out


def nearest_cell_key(marker, obj):
    mr, mc = marker
    nearest = min(abs(mr - r) + abs(mc - c) for r, c in obj["cells"])
    return nearest, obj["bbox"][0], obj["bbox"][1]


def average_cell_key(marker, obj):
    mr, mc = marker
    average = sum(abs(mr - r) + abs(mc - c) for r, c in obj["cells"]) / len(obj["cells"])
    return average, obj["bbox"][0], obj["bbox"][1]


def candidate_summary(marker, obj):
    return {
        "color": obj["color"],
        "cells": [list(cell) for cell in obj["cells"]],
        "bbox": list(obj["bbox"]),
        "size": obj["size"],
        "nearest_cell_manhattan": nearest_cell_key(marker, obj)[0],
        "average_cell_manhattan": average_cell_key(marker, obj)[0],
    }


def main() -> int:
    started = time.monotonic()
    if OUT.exists():
        raise FileExistsError(OUT)
    assert sha256_file(SOURCE) == SOURCE_SHA256
    generator = load_generator()
    base_seed = int(PROBE_SEED[:16], 16) & ((1 << 63) - 1)

    witness = None
    for draw in range(MAX_DRAWS):
        difficulty = ("easy", "medium", "hard")[draw % 3]
        grid = generator.generate(base_seed, draw, difficulty=difficulty)
        errors = generator.self_check(grid, difficulty=difficulty)
        assert errors == []
        analysis = generator._analyze(grid)
        marker = analysis["marker"]
        candidates = analysis["candidates"]
        correct = min(candidates, key=lambda obj: nearest_cell_key(marker, obj))
        rival = min(candidates, key=lambda obj: average_cell_key(marker, obj))
        correct_output = crop(grid, correct)
        rival_output = crop(grid, rival)
        mirror_output = generator.rule_mirror(grid)
        assert mirror_output == correct_output
        if correct_output != rival_output:
            witness = {
                "draw": draw,
                "seed": base_seed,
                "sample_index": draw,
                "difficulty": difficulty,
                "input": grid,
                "input_sha256": sha256_json(grid),
                "observed_axes": generator.observe_overrides(grid),
                "marker": list(marker),
                "candidates": [candidate_summary(marker, obj) for obj in candidates],
                "correct_candidate_index": candidates.index(correct),
                "centroid_shortcut_candidate_index": candidates.index(rival),
                "correct_output": correct_output,
                "centroid_shortcut_output": rival_output,
                "correct_output_sha256": sha256_json(correct_output),
                "centroid_shortcut_output_sha256": sha256_json(rival_output),
            }
            break

    if witness is None:
        report = {
            "schema": "arcpuzzles-adversarial-witness-ticket-v1",
            "ticket_id": TICKET,
            "status": "unknown",
            "task_id": TASK,
            "source_sha256": SOURCE_SHA256,
            "rule_hash": RULE_HASH,
            "probe_seed": PROBE_SEED,
            "shortcut": "choose the object with minimum average Manhattan distance over all cells",
            "draws_checked": MAX_DRAWS,
            "summary": "No lawful disagreement was found in the bounded deterministic draw budget.",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "probe_sha256": sha256_file(Path(__file__)),
        }
    else:
        program = canonical_program()
        bridge = RacketBridge(timeout=30, max_calls_before_restart=8)
        runtime = bridge.runtime_identity
        try:
            bridge.eval_text(f"(define __ticket_rule {wrap_rule(program)})")
            bridge.define_grid("__ticket_input", witness["input"])
            authority_output = bridge.eval_text("(__ticket_rule __ticket_input)")
        finally:
            bridge.shutdown()
        assert authority_output == witness["correct_output"]
        assert authority_output != witness["centroid_shortcut_output"]
        report = {
            "schema": "arcpuzzles-adversarial-witness-ticket-v1",
            "ticket_id": TICKET,
            "status": "completed",
            "task_id": TASK,
            "source_sha256": SOURCE_SHA256,
            "rule_hash": RULE_HASH,
            "probe_seed": PROBE_SEED,
            "shortcut": (
                "choose the candidate minimizing average Manhattan distance from the marker "
                "to all object cells, then use bbox row/column ties"
            ),
            "summary": (
                "A lawful generated scene refutes the average/centroid-distance shortcut; "
                "the independent nearest-cell computation, generator mirror, and exact Racket authority agree."
            ),
            "draws_checked": witness["draw"] + 1,
            "witness": witness,
            "authority_output_sha256": sha256_json(authority_output),
            "racket_runtime": runtime,
            "limitations": [
                "This is one deterministic witness, not a frequency estimate or full peer battery.",
                "The shortcut is already represented by the source's centroid-distance competitor; this ticket confirms rather than extends that contract.",
            ],
            "command": "python3 review.py run python3 ../checks/tickets/ticket-4964d90872b2b95e/probe.py",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "probe_sha256": sha256_file(Path(__file__)),
        }

    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "draws_checked": report["draws_checked"], "out": str(OUT), "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
