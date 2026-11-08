from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "70a3e6be3283"
TICKET_SEED = "d4cf7b0d4857f102f2aeeb528c475952e43672ad43880e07a22df898e2b83f0e"
EXPECTED_SOURCE_SHA256 = "a8b0b36e5d88360cb5fd9760fd55e6b6f48ab55b9fdfdc11225c6ef7dc83a177"
EXPECTED_RULE_HASH = "0aa424eca0f9"
ROOT = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().parent / "witness.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_70_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rule() -> str:
    matches = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row, found {len(matches)}")
    return matches[0]


def line_output(grid, points, *, full_axis: bool):
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    (r1, c1, color), (r2, c2, _color2) = points
    if r1 == r2:
        columns = range(width) if full_axis else range(min(c1, c2), max(c1, c2) + 1)
        for col in columns:
            out[r1][col] = color
    else:
        rows = range(height) if full_axis else range(min(r1, r2), max(r1, r2) + 1)
        for row in rows:
            out[row][c1] = color
    return out


def main():
    source = ROOT / "generators" / TASK_ID / "generator.py"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_sha == EXPECTED_SOURCE_SHA256
    module = load_module(source)
    seed = int.from_bytes(bytes.fromhex(TICKET_SEED)[:8], "big") & ((1 << 63) - 1)

    selected = None
    for sample_index in range(64):
        grid = module.generate(seed, sample_index)
        if module.self_check(grid):
            continue
        points = sorted(
            (row, col, value)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value != 0
        )
        (r1, c1, _), (r2, c2, _) = points
        interior = (
            (r1 == r2 and min(c1, c2) > 0 and max(c1, c2) < len(grid[0]) - 1)
            or (c1 == c2 and min(r1, r2) > 0 and max(r1, r2) < len(grid) - 1)
        )
        if interior:
            selected = (sample_index, grid, points)
            break
    if selected is None:
        raise AssertionError("no internal-endpoint witness found in 64 deterministic draws")

    sample_index, grid, points = selected
    correct = line_output(grid, points, full_axis=False)
    rival = line_output(grid, points, full_axis=True)
    rule = canonical_rule()
    rule_hash = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert rule_hash == EXPECTED_RULE_HASH
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge(timeout=15.0) as bridge:
        racket_output = bridge.eval_text(f"({wrap_rule(rule)} {literal})")
    assert racket_output == correct
    assert rival != correct
    differing = [
        [row, col, correct[row][col], rival[row][col]]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if correct[row][col] != rival[row][col]
    ]
    record = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": "ticket-3e92390b2fee94d8",
        "task_id": TASK_ID,
        "source_sha256": source_sha,
        "rule_hash": rule_hash,
        "probe_seed_hex": TICKET_SEED,
        "derived_integer_seed": seed,
        "sample_index": sample_index,
        "self_check_errors": module.self_check(grid),
        "shortcut": "extend the connecting line across the full aligned row or column",
        "shortcut_plausibility": "two aligned endpoints suggest a line, but the canonical rule limits it to the inclusive endpoint span",
        "endpoints": [list(point) for point in points],
        "axis": "row" if points[0][0] == points[1][0] else "col",
        "input": grid,
        "canonical_racket_output": racket_output,
        "full_axis_shortcut_output": rival,
        "differing_cells": differing,
        "result": "lawful witness refutes the full-axis shortcut; canonical Racket matches the inclusive-span oracle",
    }
    OUT.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "sample_index": sample_index,
        "axis": record["axis"],
        "differing_cell_count": len(differing),
        "racket_matches": True,
        "self_check_errors": record["self_check_errors"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
