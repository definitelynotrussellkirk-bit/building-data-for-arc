#!/usr/bin/env python3
"""Retain one lawful witness against a top-half-only span-fill shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402
from reviewer_support import normalize_grid  # noqa: E402

TICKET_ID = "extra-ticket-147bfd6c27f90e8b"
TASK_ID = "2359fcadf037"
EXPECTED_SOURCE_SHA256 = "c39c1581114dab28df27a7529c31d6f962d87d147a0851bd9622b603fc357e4b"
EXPECTED_RULE_HASH = "e7d1bc8a4d75"
TICKET_SEED = "b01bb96a5fd7e2c149cb6bd73258dad0291927bbb345445a015224f99a45d329"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
SHORTCUT = HERE / "shortcut.rkt"
OUT = HERE / "result.json"


def _load_generator():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"generator identity mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("extra_ticket_2359_generator", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import pinned generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _canonical_row():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            program = row["program_solution"]
            digest = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
            if digest != EXPECTED_RULE_HASH:
                raise RuntimeError(f"rule identity mismatch: {digest}")
            return row, program
    raise RuntimeError("canonical row not found")


def _execute(program: str, grid: list[list[int]], bridge: RacketBridge) -> list[list[int]]:
    function = wrap_rule(program)
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def _active_spans(grid: list[list[int]]) -> list[dict[str, int]]:
    h, w = len(grid), len(grid[0])
    spans = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 6]
        if len(rows) == 2:
            spans.append({"column": c, "top": rows[0], "bottom": rows[1]})
    return spans


def _fill(grid: list[list[int]], *, top_half_only: bool) -> list[list[int]]:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 6]
        if len(rows) != 2:
            continue
        top, bottom = rows
        if top_half_only and not (2 * top < h):
            continue
        if any(grid[r][c] != 0 for r in range(top + 1, bottom)):
            continue
        for r in range(top, bottom + 1):
            out[r][c] = 6
    return out


def build_result() -> dict:
    started = time.monotonic()
    generator, source_sha = _load_generator()
    row, canonical_program = _canonical_row()
    shortcut_program = SHORTCUT.read_text(encoding="utf-8")
    canonical_pairs = [*row["train"], row["test"]]
    seed = int(TICKET_SEED[:16], 16) & ((1 << 63) - 1)
    witness = generator.generate(seed, 0, difficulty=None)
    errors = generator.self_check(witness, difficulty=None)
    spans = _active_spans(witness)
    lower = [span for span in spans if 2 * span["top"] >= len(witness)]
    if errors:
        raise AssertionError(f"generated witness is outside grammar: {errors}")
    if not lower:
        raise AssertionError("ticket-seed sample does not contain a lower-half active span")

    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=16) as bridge:
        shortcut_pair_outputs = [
            _execute(shortcut_program, _grid(pair["input"]), bridge)
            for pair in canonical_pairs
        ]
        canonical_output = _execute(canonical_program, witness, bridge)
        shortcut_output = _execute(shortcut_program, witness, bridge)
        runtime = bridge.runtime_identity

    canonical_gold = [_grid(pair["output"]) for pair in canonical_pairs]
    canonical_matches = [actual == expected for actual, expected in zip(shortcut_pair_outputs, canonical_gold)]
    canonical_mirror = _fill(witness, top_half_only=False)
    shortcut_mirror = _fill(witness, top_half_only=True)
    if canonical_output != canonical_mirror:
        raise AssertionError("Python canonical mirror disagrees with pinned Racket rule")
    if shortcut_output != shortcut_mirror:
        raise AssertionError("Python shortcut mirror disagrees with retained Racket shortcut")
    mismatch_cells = [
        [r, c]
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if canonical_output[r][c] != shortcut_output[r][c]
    ]
    if not all(canonical_matches):
        raise AssertionError("shortcut is already refuted by a canonical pair")
    if not mismatch_cells:
        raise AssertionError("generated witness does not refute shortcut")

    return {
        "schema": "arcpuzzles-voluntary-extra-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "normalized_rule_hash": EXPECTED_RULE_HASH,
        "ticket_seed": TICKET_SEED,
        "shortcut": {
            "name": "fill_only_when_upper_endpoint_is_in_top_half",
            "description": (
                "Apply the exact two-endpoint/empty-gap rule only when twice the upper "
                "endpoint row is less than the grid height."
            ),
            "program_path": f"checks/extra-tickets/{TICKET_ID}/shortcut.rkt",
            "program_sha256": hashlib.sha256(SHORTCUT.read_bytes()).hexdigest(),
        },
        "canonical_pairs": {
            "count": len(canonical_pairs),
            "shortcut_matches_every_pair": all(canonical_matches),
            "matches": canonical_matches,
        },
        "generated_witness": {
            "seed": seed,
            "sample_index": 0,
            "difficulty": None,
            "dimensions": [len(witness), len(witness[0])],
            "self_check_errors": errors,
            "active_spans": spans,
            "lower_half_active_spans": lower,
            "input": witness,
            "canonical_racket_output": canonical_output,
            "shortcut_racket_output": shortcut_output,
            "canonical_racket_equals_python_mirror": canonical_output == canonical_mirror,
            "shortcut_racket_equals_python_mirror": shortcut_output == shortcut_mirror,
            "canonical_racket_equals_shortcut_racket": canonical_output == shortcut_output,
            "mismatch_cells": mismatch_cells,
            "mismatch_cell_count": len(mismatch_cells),
        },
        "bounded_result": "lawful_generated_witness_refutes_shortcut",
        "safety_finding": False,
        "scope": (
            "Three canonical pairs and the first production-generator sample derived "
            "from the ticket seed; one retained shortcut and five Racket evaluations, not a census."
        ),
        "runtime": runtime,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    result = build_result()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": result["ticket_id"],
        "task_id": result["task_id"],
        "canonical_pairs_shortcut_matches": result["canonical_pairs"]["shortcut_matches_every_pair"],
        "lower_half_active_spans": result["generated_witness"]["lower_half_active_spans"],
        "mismatch_cells": result["generated_witness"]["mismatch_cells"],
        "bounded_result": result["bounded_result"],
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
