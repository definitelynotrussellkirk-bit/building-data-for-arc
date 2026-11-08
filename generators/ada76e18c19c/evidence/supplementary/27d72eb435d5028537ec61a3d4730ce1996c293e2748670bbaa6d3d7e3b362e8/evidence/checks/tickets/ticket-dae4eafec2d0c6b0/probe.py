#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "shared/runtime"))

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import load_selected_generator, normalize_grid

TASK_ID = "ada76e18c19c"
PINNED_SOURCE_SHA256 = "0fc03c3b4e7e07c5390a25d706b4595ae468fc8e4b4c376a1093dbf532044d4f"
PINNED_RULE_HASH = "714e73d2362f"
PROBE_SEED_HEX = "17078a0ac3a519be2ee0135f188a84e72f03a77fe9c6e3dac26b0f255b7b2f28"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def grid_literal(grid: list[list[int]]) -> str:
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def canonical_record() -> dict:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row, got {len(matches)}")
    return matches[0]


def rule_callable(source: str) -> str:
    """Mirror rule!'s canonical body-form auto-binding for a bare bridge."""
    source = source.strip()
    prefix = "(rule!"
    if not source.startswith(prefix) or not source.endswith(")"):
        raise AssertionError("canonical source is not one exact (rule! ...) form")
    body = source[len(prefix):-1].strip()
    if not body:
        raise AssertionError("canonical rule body is empty")
    if body.startswith("(lambda (g)"):
        return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def main() -> None:
    source_path = ROOT / f"generators/{TASK_ID}/generator.py"
    source_sha = sha256_bytes(source_path.read_bytes())
    assert source_sha == PINNED_SOURCE_SHA256, (source_sha, PINNED_SOURCE_SHA256)

    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    assert generator.RULE_HASH == PINNED_RULE_HASH

    # sample_index 1 selects the lawful extra_same_color teaching profile.
    seed = int(PROBE_SEED_HEX[:16], 16)
    grid = generator.generate(seed, 1, difficulty="medium")
    assert generator.schedule_profile(seed, 1, "medium") == "extra_same_color"
    assert generator.self_check(grid) == []
    assert generator.SEMANTIC_WITNESSES["extra_same_color"](grid)
    assert generator.WITNESS_RIVALS["extra_same_color"] == ["ignore_exact_count"]

    authoritative_mirror = generator.rule_mirror(grid)
    shortcut = generator.SEMANTIC_RIVALS["ignore_exact_count"](grid)
    assert authoritative_mirror != shortcut

    row_indices = [
        index for index, row in enumerate(grid)
        if generator._row_kind(row)[0] == "extra_same_color"
    ]
    assert len(row_indices) == 1
    witness_row = row_indices[0]
    assert authoritative_mirror[witness_row] == grid[witness_row]
    assert shortcut[witness_row] != grid[witness_row]

    record = canonical_record()
    program = record["program_solution"]
    normalized_rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert normalized_rule_hash == PINNED_RULE_HASH

    expression = f"({rule_callable(program)} '{grid_literal(grid)})"
    with RacketBridge(max_calls_before_restart=16) as bridge:
        racket_output = normalize_grid(bridge.eval_text(expression))
        runtime = bridge.runtime_identity
    assert racket_output == authoritative_mirror

    differing_cells = [
        [r, c, authoritative_mirror[r][c], shortcut[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if authoritative_mirror[r][c] != shortcut[r][c]
    ]
    result = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": "ticket-dae4eafec2d0c6b0",
        "task_id": TASK_ID,
        "source_sha256": source_sha,
        "rule_hash": PINNED_RULE_HASH,
        "probe_seed_hex": PROBE_SEED_HEX,
        "seed": seed,
        "sample_index": 1,
        "difficulty": "medium",
        "witness": "extra_same_color",
        "rival": "ignore_exact_count",
        "self_check_errors": [],
        "witness_row": witness_row,
        "witness_input_row": grid[witness_row],
        "canonical_output_row": authoritative_mirror[witness_row],
        "shortcut_output_row": shortcut[witness_row],
        "differing_cells": differing_cells,
        "racket_matches_python_mirror": True,
        "runtime": runtime,
        "verdict": "lawful witness refutes the exact-count shortcut",
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "witness": result["witness"],
        "rival": result["rival"],
        "witness_row": witness_row,
        "differing_cells": len(differing_cells),
        "racket_matches": True,
        "result": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
