"""Reproduce the two audit findings without importing private rule runners."""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "checks" / "audit"
CANONICAL = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_cells(a, b):
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def canonical_record(task: str):
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task:
            return row
    raise KeyError(task)


def self_tile(grid, predicate):
    h, w = len(grid), len(grid[0])
    out = [[0] * (w * w) for _ in range(h * h)]
    for tr in range(h):
        for tc in range(w):
            if predicate(grid[tr][tc]):
                for r in range(h):
                    for c in range(w):
                        out[tr * h + r][tc * w + c] = grid[r][c]
    return out


def open_regions(grid, row_min=1, wall=5):
    h, w = len(grid), len(grid[0])
    seen = set()
    regions = []
    for r in range(row_min, h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == wall:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            region = []
            while queue:
                rr, cc = queue.popleft()
                region.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        row_min <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != wall
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            regions.append(region)
    return regions


def seed_preserving_fill(grid):
    """Literal implementation of the target SUMMARY: fill only empty cells."""
    out = [row[:] for row in grid]
    legend = [value for value in grid[0] if value not in (0, 5)]
    for region in open_regions(grid):
        present = [
            color
            for color in legend
            if any(grid[r][c] == color for r, c in region)
        ]
        fill = present[0] if present else 0
        for r, c in region:
            if grid[r][c] == 0:
                out[r][c] = fill
    return out


def load_apply(task: str):
    return json.loads((AUDIT / task / "racket.json").read_text())


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def audit_adfb():
    task = "adfbfbdb73c3"
    d = AUDIT / task
    inp = json.loads((d / "input.json").read_text())
    apply = load_apply(task)
    actual = apply["results"][0]["output"]
    rival = seed_preserving_fill(inp)
    write_json(d / "rival.json", rival)

    canonical = canonical_record(task)
    canonical_disagreements = 0
    for pair in canonical["train"] + canonical["test"]:
        canonical_disagreements += seed_preserving_fill(pair["input"]) != pair["output"]

    diffs = changed_cells(actual, rival)
    write_json(
        d / "metadata.json",
        {
            "task_id": task,
            "finding": "documented seed-preservation contradicts executable authority",
            "generator_sha256": apply["generator_sha256"],
            "rule_text_sha256": apply["rule_text_sha256"],
            "input_sha256": apply["results"][0]["input_sha256"],
            "racket_output_sha256": apply["results"][0]["output_sha256"],
            "rival_output_sha256": hashlib.sha256(
                json.dumps(rival, separators=(",", ":")).encode()
            ).hexdigest(),
            "changed_cell_count": len(diffs),
            "changed_cells": diffs,
            "canonical_pairs_checked": len(canonical["train"]) + len(canonical["test"]),
            "canonical_pairs_disagreeing_with_documented_rival": canonical_disagreements,
            "validator_errors": json.loads((d / "generation.json").read_text())["self_check"],
            "generation": json.loads((d / "generation.json").read_text()),
            "apply_command": apply["command"],
            "apply_cwd": apply["cwd"],
        },
    )


def audit_7e():
    task = "7e03da0eb439"
    d = AUDIT / task
    inp = json.loads((d / "input.json").read_text())
    apply = load_apply(task)
    actual = apply["results"][0]["output"]
    rival = self_tile(inp, lambda value: value > 1)
    write_json(d / "rival.json", rival)

    canonical = canonical_record(task)
    pairs = canonical["train"] + canonical["test"]
    canonical_fit = sum(
        self_tile(pair["input"], lambda value: value > 1) == pair["output"]
        for pair in pairs
    )
    diffs = changed_cells(actual, rival)
    write_json(
        d / "metadata.json",
        {
            "task_id": task,
            "finding": "value>1 trigger shortcut fits canonical but fails generated color counterexample",
            "generator_sha256": apply["generator_sha256"],
            "rule_text_sha256": apply["rule_text_sha256"],
            "input_sha256": apply["results"][0]["input_sha256"],
            "racket_output_sha256": apply["results"][0]["output_sha256"],
            "rival_output_sha256": hashlib.sha256(
                json.dumps(rival, separators=(",", ":")).encode()
            ).hexdigest(),
            "changed_cell_count": len(diffs),
            "first_changed_cells": diffs[:12],
            "canonical_pairs_checked": len(pairs),
            "canonical_pairs_fit_by_rival": canonical_fit,
            "validator_errors": json.loads((d / "generation.json").read_text())["self_check"],
            "generation": json.loads((d / "generation.json").read_text()),
            "apply_command": apply["command"],
            "apply_cwd": apply["cwd"],
        },
    )


if __name__ == "__main__":
    audit_adfb()
    audit_7e()
