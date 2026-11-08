"""One bounded domain-collapse witness for ticket-be6a9b6a2f843f97."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402
from reviewer_support import normalize_grid  # noqa: E402

TICKET_ID = "ticket-be6a9b6a2f843f97"
TASK_ID = "235a1d06b9d3"
EXPECTED_SOURCE_SHA256 = "371aa4f2e992601d1cfa5a57d3cbaa8545c243355daa99eac6c420fbcb916379"
EXPECTED_RULE_HASH = "0df093c037e1"
TICKET_SEED = "134a2702dfb2631f3d569a6ab215714030e2bb1578e519f2c15c408469367c8c"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def load_generator():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"generator identity mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("ticket_235a1d06b9d3", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def canonical_row():
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            digest = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
            if digest != EXPECTED_RULE_HASH:
                raise RuntimeError(f"rule identity mismatch: {digest}")
            return row
    raise RuntimeError("canonical row not found")


def execute(program: str, grid, bridge: RacketBridge):
    function = wrap_rule(program)
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def shortcut_row1_anchor(grid):
    """Wrong shortcut: use input[1][1], not the canonical input[2][1], as background."""
    background = grid[1][1]
    return [list(grid[0]), list(grid[1]), [background if value == background else 6 for value in grid[0]]]


def main() -> int:
    started = time.monotonic()
    generator, source_sha = load_generator()
    row = canonical_row()
    pairs = [*row["train"], *row["test"]]
    canonical_shortcut_matches = [shortcut_row1_anchor(pair["input"]) == pair["output"] for pair in pairs]

    # One profile draw each is enough to verify the implemented domain keeps the two anchors equal;
    # the validator itself enforces every non-cue lower-row cell equals input[2][1].
    seed = int(TICKET_SEED[:16], 16)
    profile_checks = []
    for index, profile in enumerate(generator.SCENE_PROFILES):
        grid = generator.generate(seed + index, index, difficulty="medium", scene_profile=profile)
        errors = generator.self_check(grid, meta={"overrides": {"scene_profile": profile}})
        profile_checks.append({
            "scene_profile": profile,
            "self_check_errors": errors,
            "row1_anchor": grid[1][1],
            "row2_anchor": grid[2][1],
            "anchors_equal": grid[1][1] == grid[2][1],
            "official_equals_shortcut": generator.rule_mirror(grid) == shortcut_row1_anchor(grid),
        })

    witness = [[3, 0, 3, 0, 0], [7, 0, 0, 0, 0], [0, 3, 3, 3, 3]]
    validator_errors = generator.self_check(witness)
    official_mirror = generator.rule_mirror(witness)
    shortcut_output = shortcut_row1_anchor(witness)
    with RacketBridge(timeout=30, max_calls_before_restart=8) as bridge:
        official_racket = execute(row["program_solution"], witness, bridge)
        runtime = bridge.runtime_identity

    mismatch_cells = [
        [r, c]
        for r in range(len(official_racket))
        for c in range(len(official_racket[0]))
        if official_racket[r][c] != shortcut_output[r][c]
    ]
    domain_collapse_reproduced = (
        all(canonical_shortcut_matches)
        and all(check["self_check_errors"] == [] and check["anchors_equal"] and check["official_equals_shortcut"] for check in profile_checks)
        and official_racket == official_mirror
        and official_racket != shortcut_output
        and bool(validator_errors)
    )
    elapsed = time.monotonic() - started
    result = {
        "schema": "supplementary-adversarial-domain-collapse-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "normalized_rule_hash": EXPECTED_RULE_HASH,
        "ticket_seed": TICKET_SEED,
        "shortcut": {
            "name": "use_row1_col1_as_background_anchor",
            "description": "Use input[1][1] instead of canonical input[2][1] as the background anchor.",
        },
        "canonical_pairs": {
            "count": len(pairs),
            "shortcut_matches_every_pair": all(canonical_shortcut_matches),
            "matches": canonical_shortcut_matches,
        },
        "generated_domain_profile_probe": {
            "count": len(profile_checks),
            "all_profiles_anchor_equal_and_shortcut_equivalent": all(
                check["self_check_errors"] == [] and check["anchors_equal"] and check["official_equals_shortcut"]
                for check in profile_checks
            ),
            "checks": profile_checks,
            "structural_reason": (
                "self_check defines background as input[2][1] and requires every lower-row cell outside column 0, "
                "including input[1][1], to equal that background."
            ),
        },
        "reference_lawful_discriminator": {
            "input": witness,
            "validator_errors": validator_errors,
            "passes_target_validator": validator_errors == [],
            "authoritative_output": official_racket,
            "python_mirror_output": official_mirror,
            "shortcut_output": shortcut_output,
            "mismatch_cells": mismatch_cells,
            "mismatch_cell_count": len(mismatch_cells),
            "reference_lawful": True,
        },
        "python_mirror_matches_racket": official_mirror == official_racket,
        "domain_collapse_reproduced": domain_collapse_reproduced,
        "bounded_result": "current generator domain cannot distinguish the canonical anchor from the row-1 shortcut",
        "scope": "Five canonical pairs, one draw per 16 declared profiles, and one Racket-executed discriminator; not a census or peer battery.",
        "elapsed_seconds": elapsed,
        "runtime": runtime,
    }
    (HERE.parent / "witness.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema": "arcpuzzles-ticket-probe-receipt-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "finding_reproduced": domain_collapse_reproduced,
        "elapsed_seconds": elapsed,
        "exit_code": 0,
        "command": ["python3", "review.py", "run", "python3", f"../checks/tickets/{TICKET_ID}/probe.py"],
        "cwd": "packet root",
        "witness_sha256": hashlib.sha256((HERE.parent / "witness.json").read_bytes()).hexdigest(),
        "bounded_scope": result["scope"],
    }
    (HERE.parent / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "canonical_pairs_shortcut_matches": all(canonical_shortcut_matches),
        "profiles_checked": len(profile_checks),
        "all_profiles_shortcut_equivalent": result["generated_domain_profile_probe"]["all_profiles_anchor_equal_and_shortcut_equivalent"],
        "validator_errors_on_discriminator": validator_errors,
        "authoritative_output": official_racket,
        "shortcut_output": shortcut_output,
        "mismatch_cell_count": len(mismatch_cells),
        "domain_collapse_reproduced": domain_collapse_reproduced,
        "elapsed_seconds": elapsed,
    }, indent=2, sort_keys=True))
    return 0 if domain_collapse_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
