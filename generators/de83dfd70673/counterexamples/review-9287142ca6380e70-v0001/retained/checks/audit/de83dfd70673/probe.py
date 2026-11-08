#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "de83dfd70673"
BANDS = (None, "easy", "medium", "hard")
DRAWS_PER_BAND = 30


def canonical_program(root: Path) -> str:
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.append(row["program_solution"])
    unique = set(programs)
    if len(unique) != 1:
        raise RuntimeError(f"expected one unique canonical program, found {len(unique)}")
    return unique.pop()


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    if body.lstrip().startswith("(lambda"):
        bridge.define_grid("audit_input", grid)
        return bridge.eval_text(f"({body} audit_input)")
    bridge.define_grid("g", grid)
    return bridge.eval_text(body)


def components(grid: list[list[int]]):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield color, cells


def closed_frame_only_rival(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for color, cells in components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if r1 - r0 >= 2 and c1 - c0 >= 2 and cells == border:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    out[r][c] = color
    return out


def open_l() -> list[list[int]]:
    grid = [[0] * 6 for _ in range(6)]
    for r, c in ((1, 1), (1, 2), (1, 3), (2, 1), (3, 1)):
        grid[r][c] = 3
    return grid


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    program = canonical_program(root)
    generated_checked = 0
    mismatches = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for band in BANDS:
            for sample_index in range(DRAWS_PER_BAND):
                grid = generator.generate(9173, sample_index, difficulty=band)
                canonical = execute(bridge, program, grid)
                rival = closed_frame_only_rival(grid)
                generated_checked += 1
                if canonical != rival:
                    mismatches.append({"difficulty": band, "sample_index": sample_index, "input": grid})
        witness = open_l()
        canonical_witness = execute(bridge, program, witness)
        rival_witness = closed_frame_only_rival(witness)

    unknown_key_grid = generator.generate(0, 0, difficulty="easy", __override_contract_unknown_axis__=1)
    try:
        generator.generate(0, 0, difficulty="easy", grid_h=10)
    except Exception as exc:
        grid_h_contract = {"exception_type": type(exc).__name__, "message": str(exc)}
    else:
        grid_h_contract = {"accepted": True}
    degenerate = generator.generate(0, 0, difficulty="easy", texture="no_frames", grid_h=8, grid_w=9)

    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "semantic_finding": {
            "rival": "fill only exact closed one-cell-thick rectangular frames",
            "generated_draws_checked": generated_checked,
            "draws_per_band": DRAWS_PER_BAND,
            "bands": list(BANDS),
            "generated_mismatch_count": len(mismatches),
            "open_l_input": witness,
            "canonical_output": canonical_witness,
            "rival_output": rival_witness,
            "witness_outputs_equal": canonical_witness == rival_witness,
        },
        "contract_findings": {
            "unknown_override_accepted": {
                "key": "__override_contract_unknown_axis__",
                "output_shape": [len(unknown_key_grid), len(unknown_key_grid[0])],
            },
            "declared_grid_h_10": grid_h_contract,
            "degenerate_requested_shape": [8, 9],
            "degenerate_actual_shape": [len(degenerate), len(degenerate[0])],
        },
    }
    if mismatches:
        raise AssertionError(f"closed-frame rival failed on {len(mismatches)} generated draws")
    if canonical_witness == rival_witness:
        raise AssertionError("open-L witness did not distinguish the canonical rule")
    if grid_h_contract.get("accepted"):
        raise AssertionError("declared grid_h=10 unexpectedly accepted")
    if [len(degenerate), len(degenerate[0])] == [8, 9]:
        raise AssertionError("degenerate path unexpectedly honored requested dimensions")

    out = Path(__file__).with_name("evidence.json")
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "reproduced",
        "evidence": str(out),
        "source_sha256": source_sha,
        "generated_draws_matching_rival": generated_checked,
        "open_l_refutes_rival": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
