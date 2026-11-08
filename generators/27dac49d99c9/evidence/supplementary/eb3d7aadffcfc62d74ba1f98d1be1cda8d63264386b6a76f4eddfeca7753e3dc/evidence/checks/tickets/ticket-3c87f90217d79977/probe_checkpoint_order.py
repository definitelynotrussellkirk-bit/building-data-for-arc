#!/usr/bin/env python3
"""One bounded adversarial witness probe for ARC generator 27dac49d99c9."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator, normalize_grid

TICKET_ID = "ticket-3c87f90217d79977"
TASK_ID = "27dac49d99c9"
PROBE_SEED = "c727977010c8d261b5fa4f851841f25778c5f80f342648eb6cb32afe7779f98d"
PINNED_GENERATOR_SHA256 = "a4231963866199b5e2d5f3aef08c6518f83769e681d41240b8dc9025088f4b7e"
PINNED_RULE_HASH = "7439a388fdc4"
CANONICAL_PATH_CLAUSE = (
    "(define path (append (path-between g p2 p3) "
    "(path-between g p3 p4) (path-between g p4 p6)))"
)
RIVAL_PATH_CLAUSE = (
    "(define path (append (path-between g p2 p4) "
    "(path-between g p4 p6) (path-between g p6 p3)))"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha256(grid: Any) -> str:
    payload = json.dumps(normalize_grid(grid), separators=(",", ":"), sort_keys=True).encode()
    return sha256_bytes(payload)


def canonical_source(root: Path) -> str:
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    matches.append(source)
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, got {len(matches)}")
    source = matches[0]
    digest = sha256_bytes(source.encode())
    if digest[:12] != PINNED_RULE_HASH:
        raise RuntimeError(f"canonical rule hash mismatch: {digest[:12]}")
    if source.count(CANONICAL_PATH_CLAUSE) != 1:
        raise RuntimeError("canonical checkpoint-order clause is not uniquely present")
    return source


def diff_cells(left: list[list[int]], right: list[list[int]]) -> list[dict[str, Any]]:
    return [
        {"row": row, "col": col, "authority": left[row][col], "rival": right[row][col]}
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def marker_positions(grid: list[list[int]]) -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (2, 3, 4, 6):
                found[str(value)] = [row, col]
    return found


def main() -> None:
    work = Path(__file__).resolve().parents[3]
    root = work / "repo"
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    if generator_sha256 != PINNED_GENERATOR_SHA256:
        raise RuntimeError(
            f"generator hash mismatch: expected {PINNED_GENERATOR_SHA256}, got {generator_sha256}"
        )

    authority_source = canonical_source(root)
    rival_source = authority_source.replace(CANONICAL_PATH_CLAUSE, RIVAL_PATH_CLAUSE, 1)
    authority_sha256 = sha256_bytes(authority_source.encode())
    rival_sha256 = sha256_bytes(rival_source.encode())
    base_seed = int(PROBE_SEED[:16], 16) & ((1 << 63) - 1)
    difficulties = ("easy", "medium", "hard", None)
    candidates: list[dict[str, Any]] = []
    for sample_index in range(24):
        difficulty = difficulties[sample_index % len(difficulties)]
        seed = (base_seed + sample_index * 0x9E3779B97F4A7C15) & ((1 << 63) - 1)
        grid = normalize_grid(generator.generate(seed, sample_index, difficulty=difficulty))
        reasons = list(generator.self_check(grid, difficulty=difficulty) or [])
        if reasons:
            continue
        candidates.append(
            {
                "grid": grid,
                "recipe": {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "overrides": {},
                },
            }
        )

    if not candidates:
        raise RuntimeError("bounded probe produced no lawful generated candidates")

    witness = None
    with RacketBridge(timeout=20.0) as bridge:
        bridge.eval_text(f"(define __authority {wrap_rule(authority_source)})")
        bridge.eval_text(f"(define __rival {wrap_rule(rival_source)})")
        for candidate in candidates:
            grid = candidate["grid"]
            bridge.define_grid("__audit_input", grid)
            authority = normalize_grid(bridge.eval_text("(__authority __audit_input)"))
            rival = normalize_grid(bridge.eval_text("(__rival __audit_input)"))
            differences = diff_cells(authority, rival)
            if differences:
                witness = {
                    **candidate,
                    "authoritative_output": authority,
                    "rival_output": rival,
                    "differing_cells": differences,
                    "marker_positions": marker_positions(grid),
                    "runtime_identity": bridge.runtime_identity,
                }
                break

    if witness is None:
        output = {
            "schema": "arcpuzzles-adversarial-witness-v1",
            "ticket_id": TICKET_ID,
            "task_id": TASK_ID,
            "status": "unknown",
            "shortcut": "route markers as 2->4->6->3, treating color 3 as terminal goal",
            "bounded_probe": {"lawful_candidates": len(candidates), "limit": 24},
            "reason": "No separating witness was found in the one bounded 24-candidate probe.",
            "source_binding": {
                "generator_path": str(generator_path.relative_to(root)),
                "generator_sha256": generator_sha256,
                "canonical_rule_sha256": authority_sha256,
                "canonical_rule_hash": authority_sha256[:12],
                "rival_rule_sha256": rival_sha256,
            },
        }
    else:
        grid = witness.pop("grid")
        authority = witness.pop("authoritative_output")
        rival = witness.pop("rival_output")
        output = {
            "schema": "arcpuzzles-adversarial-witness-v1",
            "ticket_id": TICKET_ID,
            "task_id": TASK_ID,
            "status": "completed",
            "shortcut": {
                "name": "terminal_goal_order",
                "description": "route markers as 2->4->6->3, treating color 3 as the terminal goal",
                "why_plausible": (
                    "The pinned generator docstring calls color 3 the goal and says the route goes "
                    "from start to goal through checkpoints 4 and 6; the canonical written rule "
                    "instead visits 3 before 4 and 6."
                ),
                "canonical_order": [2, 3, 4, 6],
                "rival_order": [2, 4, 6, 3],
            },
            "source_binding": {
                "generator_path": str(generator_path.relative_to(root)),
                "generator_sha256": generator_sha256,
                "canonical_program_path": str(canonical_path(root).relative_to(root)),
                "canonical_rule_sha256": authority_sha256,
                "canonical_rule_hash": authority_sha256[:12],
                "rival_rule_sha256": rival_sha256,
                "probe_seed": PROBE_SEED,
            },
            "recipe": witness["recipe"],
            "input": grid,
            "authoritative_output": authority,
            "rival_output": rival,
            "input_sha256": grid_sha256(grid),
            "authoritative_output_sha256": grid_sha256(authority),
            "rival_output_sha256": grid_sha256(rival),
            "marker_positions": witness["marker_positions"],
            "differing_cell_count": len(witness["differing_cells"]),
            "differing_cells": witness["differing_cells"],
            "validation": {
                "generator_self_check": "passed",
                "arc_rectangular_grids": "passed",
                "authority_executed_by_racket": True,
                "rival_executed_by_racket": True,
                "rival_disagrees": True,
                "lawful_candidates_examined": candidates.index(next(c for c in candidates if c["recipe"] == witness["recipe"])) + 1,
                "runtime_identity": witness["runtime_identity"],
            },
            "scope": (
                "One source-bound generated witness against one plausible shortcut; not a peer "
                "battery, distribution census, or claim about all generated lessons."
            ),
        }

    out_path = Path(__file__).with_name("witness.json")
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": output["status"],
        "shortcut": "terminal_goal_order",
        "lawful_candidates": len(candidates),
        "differing_cell_count": output.get("differing_cell_count"),
        "recipe": output.get("recipe"),
        "output": str(out_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
