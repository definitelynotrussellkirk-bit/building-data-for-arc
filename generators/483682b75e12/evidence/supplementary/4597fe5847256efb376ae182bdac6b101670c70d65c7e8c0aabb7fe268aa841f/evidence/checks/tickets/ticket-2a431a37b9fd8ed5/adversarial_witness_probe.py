#!/usr/bin/env python3
"""Retain one lawful witness against a plausible bbox-height shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TICKET_ID = "ticket-2a431a37b9fd8ed5"
TASK_ID = "483682b75e12"
TICKET_SEED = "bdde266aa3ce816c180b03b9a05c642eeae97197635f803d71288ea713b42b39"
PINNED_SOURCE_SHA256 = "189fbe70222e7cb05feeb7114eb0ad2a3f4f557e532cf23e3ea0a8c686979f7e"
PINNED_RULE_HASH = "a2a5ebf00ff5"

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
for dependency in (REPO, REPO / "shared" / "runtime"):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import strip_rule_wrapper  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"ticket_target_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    foreground = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (7, 8)
    }
    result: list[list[tuple[int, int]]] = []
    seen: set[tuple[int, int]] = set()
    for start in sorted(foreground):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        cells: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            r, c = cell
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in foreground and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        result.append(sorted(cells))
    return result


def bbox_height_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: shift by component bbox height, not cell count."""
    h, w = len(grid), len(grid[0])
    out = [[8 if grid[r][c] == 8 else 7 for c in range(w)] for r in range(h)]
    for cells in components(grid):
        jump = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        for r, c in cells:
            if r - jump >= 0:
                out[r - jump][c] = grid[r][c]
    return out


def canonical_program() -> str:
    programs = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    unique = sorted(set(programs))
    if len(unique) != 1:
        raise RuntimeError(f"expected one unique canonical program, got {len(unique)}")
    return unique[0]


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("canonical program is not a lambda rule")
    return f"({body} {grid_literal(grid)})"


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [r, c]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def main() -> int:
    source = REPO / "generators" / TASK_ID / "generator.py"
    observed_source_hash = sha256(source)
    if observed_source_hash != PINNED_SOURCE_SHA256:
        raise SystemExit(f"pinned source changed: {observed_source_hash}")
    generator = load_generator(source)
    if generator.RULE_HASH != PINNED_RULE_HASH:
        raise SystemExit(f"pinned rule hash changed: {generator.RULE_HASH}")

    # Use the ticket seed directly; one exact profile is the entire targeted probe.
    grid = generator.generate(TICKET_SEED, 0, scene_profile="horizontal_six")
    errors = generator.self_check(grid)
    if errors:
        raise SystemExit(f"generated witness is unlawful: {errors}")
    facts = generator._extract_facts(grid)
    if not facts["components"] or any(component["size"] != 6 for component in facts["components"]):
        raise SystemExit("focused witness is not composed of horizontal six-cell components")
    heights = [
        max(r for r, _ in component["cells"]) - min(r for r, _ in component["cells"]) + 1
        for component in facts["components"]
    ]
    if any(height != 1 for height in heights):
        raise SystemExit(f"focused witness bbox heights are not one: {heights}")

    canonical = generator.rule_mirror(grid)
    shortcut = bbox_height_shortcut(grid)
    differences = differing_cells(canonical, shortcut)
    if not differences:
        raise SystemExit("bbox-height shortcut was not refuted")

    program = canonical_program()
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        racket_output = bridge.eval_text(application(program, grid))
        runtime = bridge.runtime_identity
    if racket_output != canonical:
        raise SystemExit("exact canonical Racket disagrees with Python mirror")

    component_rows = []
    for component, height in zip(facts["components"], heights):
        component_rows.append(
            {
                "size": component["size"],
                "bbox_height": height,
                "canonical_jump": component["size"],
                "shortcut_jump": height,
                "cells": [list(cell) for cell in component["cells"]],
            }
        )
    report: dict[str, Any] = {
        "schema": "arcpuzzles-adversarial-witness-ticket-v1",
        "status": "completed",
        "ticket_id": TICKET_ID,
        "ticket_seed": TICKET_SEED,
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "pinned_identity": {
            "generator_sha256": observed_source_hash,
            "declared_rule_hash": generator.RULE_HASH,
            "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
        "plausible_shortcut": {
            "name": "bbox_height_jump",
            "description": "Move each component upward by its bounding-box height rather than by total cell count.",
            "why_plausible": "For vertical bars, bounding-box height equals cell count, so the shortcut can mimic the intended motion on a natural shape family.",
        },
        "lawful_witness": {
            "scene_profile": "horizontal_six",
            "self_check_errors": errors,
            "components": component_rows,
            "input": grid,
            "canonical_output": canonical,
            "shortcut_output": shortcut,
            "differing_cells": differences,
            "differing_cell_count": len(differences),
        },
        "verification": {
            "exact_canonical_racket_matches_python_mirror": True,
            "shortcut_refuted": True,
            "racket_runtime": runtime,
        },
        "assessment": (
            "The current generator already contains a lawful horizontal-six profile that refutes this shortcut; this ticket retains one source-bound witness and does not claim a new peer safety finding."
        ),
        "limitations": [
            "One plausible shortcut and one generated witness were inspected, per ticket budget.",
            "No full peer battery or frequency census was run.",
        ],
    }
    out = HERE / "witness.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "out": str(out), "differing_cells": len(differences)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
