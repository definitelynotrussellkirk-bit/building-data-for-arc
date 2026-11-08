from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "628b4a2c24c1"
PINNED_SOURCE_SHA256 = "05706a3385a684de45d3bd9546b8ed762bf2e2d902fc5b82a97c9cfb7490325d"
PROBE_SEED_HEX = "ee0895360d04183a3392038a40f94276a8a637ecb151ba3a1650387cdc027d3a"
ROOT = find_root(__file__)
# The packet stores repository tools under shared/tools, while wrap_rule
# imports the installed-runtime package name scripts.comment_solutions.
if "scripts" not in sys.modules:
    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared" / "tools")]
    sys.modules["scripts"] = scripts
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
OUT = Path(__file__).with_name("report.json")


def canonical_source() -> str:
    values = {
        row["program_solution"]
        for row in (
            json.loads(line)
            for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row.get("task_id") == TASK_ID
    }
    if len(values) != 1:
        raise RuntimeError(f"expected one canonical source, got {len(values)}")
    return values.pop()


def grid_literal(grid) -> str:
    grid = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute(source: str, grid, bridge: RacketBridge):
    expression = f"({wrap_rule(source)} {grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def wall_required_rival(grid):
    output = [row[:] for row in grid]
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        walls = [col for col, value in enumerate(row) if value == 8]
        if not walls:
            continue
        for col, value in enumerate(row):
            if value in (0, 8):
                continue
            stop = next((wall for wall in walls if wall > col), width)
            for target in range(col, stop):
                if output[row_index][target] == 0:
                    output[row_index][target] = value
    return output


def main() -> None:
    if SOURCE_SHA256 != PINNED_SOURCE_SHA256:
        raise RuntimeError(f"source hash drift: {SOURCE_SHA256}")
    grid = GEN.generate(0, 2, difficulty="medium")
    domain_errors = GEN.self_check(grid)
    if domain_errors:
        raise RuntimeError(f"lawful witness rejected: {domain_errors}")
    source = canonical_source()
    with RacketBridge() as bridge:
        racket_output = execute(source, grid, bridge)
    mirror_output = GEN.rule_mirror(grid)
    if racket_output != mirror_output:
        raise RuntimeError("canonical Racket and rule_mirror disagree")
    rival_output = wall_required_rival(grid)
    differences = [
        [row, col, rival_output[row][col], racket_output[row][col]]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if rival_output[row][col] != racket_output[row][col]
    ]
    active_rows_without_wall = [
        row
        for row, values in enumerate(grid)
        if any(value not in (0, 8) for value in values) and 8 not in values
    ]
    if not active_rows_without_wall or not differences:
        raise RuntimeError("probe did not reproduce the wall-required shortcut")
    report = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": "ticket-85a1d82cfeee59dd",
        "task_id": TASK_ID,
        "probe_seed_hex": PROBE_SEED_HEX,
        "generator_call": {"seed": 0, "sample_index": 2, "difficulty": "medium"},
        "source_path": str(SOURCE.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA256,
        "canonical_rule_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "domain_errors": domain_errors,
        "active_rows_without_wall": active_rows_without_wall,
        "difference_count": len(differences),
        "differences": differences,
        "input": grid,
        "canonical_racket_output": racket_output,
        "wall_required_rival_output": rival_output,
        "outcome": "finding",
        "classification": "reproduced teaching shortcut",
        "summary": "A rival that extends only rows containing a visible color-8 wall matches canonical demonstrations but fails this lawful generated scene because wall-less active rows must sweep to the right edge.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "outcome": "finding",
        "active_rows_without_wall": active_rows_without_wall,
        "difference_count": len(differences),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
