from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-0b3a725fce10d509"
TASK_ID = "766e2ddcc3d3"
PINNED_SOURCE_SHA256 = "1127566270bc6549e68c69627c7a740fad6b47beb6d9e2a9820c8c0f64a64561"
PINNED_RULE_HASH = "a22bbdd04976"
PROBE_SEED = "704d7b7a1afc3ccbd82d941950ecf700353ff087000a13214e15d1a7383b9ffa"
SAMPLE_INDEX = 3  # slot03_ctrl5_interior: lawful, generalized, and not a public anchor.
DIFFICULTY = "medium"
SHORTCUT_NAME = "memorize_one_output_per_control"
WITNESS_NAME = "new_shape_refutes_control_lookup"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]):
    prefix = "(rule!"
    if not program.startswith(prefix) or not program.endswith(")"):
        raise ValueError("unexpected canonical wrapper")
    bridge.define_grid("g", grid)
    body = program[len(prefix) : -1].strip()
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    return bridge.eval_text(expression)


def selected_program(root: Path) -> str:
    rows: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row["program_solution"])
    if len(rows) != 1:
        raise RuntimeError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    return rows[0]


def main() -> int:
    evidence_dir = Path(__file__).resolve().parent
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != PINNED_SOURCE_SHA256:
        raise SystemExit(
            f"pinned generator source mismatch: {source_sha256} != {PINNED_SOURCE_SHA256}"
        )
    if generator.RULE_HASH != PINNED_RULE_HASH:
        raise SystemExit(
            f"pinned rule hash mismatch: {generator.RULE_HASH} != {PINNED_RULE_HASH}"
        )

    digest = bytes.fromhex(PROBE_SEED)
    seed = int.from_bytes(digest[:8], "big") % (2**31)
    grid = generator.generate(seed, SAMPLE_INDEX, difficulty=DIFFICULTY)
    self_check = generator.self_check(grid, difficulty=DIFFICULTY)
    observables = generator.semantic_observables(grid)
    canonical_output = generator.rule_mirror(grid)
    shortcut_output = generator.LESSON_COMPETITORS[SHORTCUT_NAME](grid)
    program = selected_program(root)

    with RacketBridge(max_calls_before_restart=8) as bridge:
        racket_output = execute(bridge, program, grid)

    checks = {
        "source_sha256_matches_ticket": source_sha256 == PINNED_SOURCE_SHA256,
        "rule_hash_matches_ticket": generator.RULE_HASH == PINNED_RULE_HASH,
        "lawful": self_check == [],
        "generalized_non_anchor": observables.get("canonical_profile") is None,
        "scheduled_ctrl5_interior": (
            observables.get("ctrl") == 5
            and observables.get("marker_location") == "interior"
        ),
        "racket_python_parity": racket_output == canonical_output,
        "shortcut_refuted": shortcut_output != canonical_output,
        "declared_witness_fires": bool(generator.SEMANTIC_WITNESSES[WITNESS_NAME](grid)),
    }
    report = {
        "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "status": "completed" if all(checks.values()) else "unknown",
        "probe_seed": PROBE_SEED,
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
            "rule_hash": generator.RULE_HASH,
            "canonical_program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
        },
        "recipe": {
            "seed": seed,
            "sample_index": SAMPLE_INDEX,
            "difficulty": DIFFICULTY,
            "schedule_profile": generator.schedule_profile(seed, SAMPLE_INDEX, DIFFICULTY),
            "overrides": {},
        },
        "shortcut": {
            "name": SHORTCUT_NAME,
            "description": (
                "ignore the input shape and return the one public output memorized "
                "for the marker/control value"
            ),
        },
        "witness": WITNESS_NAME,
        "semantic_observables": observables,
        "input": grid,
        "self_check": self_check,
        "python_rule_mirror": canonical_output,
        "racket_output": racket_output,
        "shortcut_output": shortcut_output,
        "checks": checks,
    }
    report["checks"]["all_passed"] = all(checks.values())
    output_path = evidence_dir / "witness.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
