#!/usr/bin/env python3
"""Build source-bound causal and finite learnability evidence for 7fc158ab7b70."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


TASK_ID = "7fc158ab7b70"
STEP_A = (
    "Count the episode-selected input aggregate: either all nonzero cells or "
    "the distinct nonzero colors."
)
INTERMEDIATE = (
    "The input-dependent positive integer replication amount produced by that count."
)
STEP_B = (
    "Use the replication amount as the row factor, column factor, or both factors, "
    "then map each output coordinate back to its source cell."
)
WHY = (
    "B's output dimensions and source-coordinate divisors are the integer produced "
    "by A. The replication geometry therefore cannot be selected correctly before "
    "the input aggregate has been counted; replacing that intermediate changes the final grid."
)


def raw(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(raw(value)).hexdigest()


def program_digest(program: str) -> str:
    return hashlib.sha256(program.encode()).hexdigest()


def setting_key(settings: dict) -> str:
    return json.dumps(settings, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def counts(grid: list[list[int]]) -> tuple[int, int]:
    values = [cell for row in grid for cell in row if cell != 0]
    return len(values), len(set(values))


def selected_amount(grid: list[list[int]], settings: dict) -> int:
    cells, colors = counts(grid)
    return cells if settings["count_basis"] == "cells" else colors


def occupied_rows_expr() -> str:
    return """(for/sum ((r (range 0 (rows g))))
      (if (> (for/sum ((c (range 0 (cols g))))
               (if (!= (at g r c) 0) 1 0))
             0)
          1
          0))"""


def occupied_columns_expr() -> str:
    return """(for/sum ((c (range 0 (cols g))))
      (if (> (for/sum ((r (range 0 (rows g))))
               (if (!= (at g r c) 0) 1 0))
             0)
          1
          0))"""


def amount_program(settings: dict, amount_expr: str) -> str:
    axes = settings["scale_axes"]
    row_factor = "amount" if axes in {"both", "rows"} else "1"
    col_factor = "amount" if axes in {"both", "columns"} else "1"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (amount {amount_expr})
         (row-factor {row_factor})
         (col-factor {col_factor}))
    (build-grid (* h row-factor)
                (* w col-factor)
                (r c)
                (at g (/ r row-factor) (/ c col-factor))))))"""


def grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def validate_grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("Racket output is not a bounded grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("Racket output is not a rectangular ARC grid")
    return grid


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_causal_and_self_audit.py QUALIFICATION_DIR OUTPUT_DIR")
    qualification_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    repo = Path.cwd().resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)

    q = json.loads((qualification_dir / "qualification.json").read_text())
    execution_path = qualification_dir / "execution.json"
    execution_bytes = execution_path.read_bytes()
    execution = json.loads(execution_bytes)
    if q.get("status") != "qualified" or q.get("task_id") != TASK_ID:
        raise ValueError("expected the qualified main task")
    if hashlib.sha256(execution_bytes).hexdigest() != q["execution"]["sha256"]:
        raise ValueError("qualification execution hash differs")
    if len(q.get("jobs", [])) != 12 or len(execution.get("episodes", [])) != 12:
        raise ValueError("expected two seeds for each of six settings")

    runtime = repo / "shared/runtime"
    sys.path[:0] = [str(runtime)]
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped: dict[str, str] = {}
    evaluations = 0

    def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal evaluations
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        evaluations += 1
        return validate_grid(bridge.eval_text(f"({wrapped[program]} {grid_literal(grid)})"))

    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("protected Racket is required")

    findings = []
    audit_rows = []
    try:
        for episode, check in zip(execution["episodes"], execution["checks"]):
            settings = episode["settings"]
            expected_program_hash = q["programs"][setting_key(settings)]
            if program_digest(episode["program"]) != expected_program_hash:
                raise ValueError("episode program differs from qualified program")
            pairs = episode["train"] + episode["test"]
            replayed_reference = [apply(episode["program"], pair["input"]) for pair in pairs]
            if replayed_reference != [pair["output"] for pair in pairs]:
                raise ValueError("qualified reference replay differs")

            first_amount = selected_amount(episode["train"][0]["input"], settings)
            rivals = {
                "fixed_first_demo_intermediate": amount_program(settings, str(first_amount)),
                "input_side_as_intermediate": amount_program(settings, "(rows g)"),
                "occupied_rows_as_intermediate": amount_program(settings, occupied_rows_expr()),
                "occupied_columns_as_intermediate": amount_program(settings, occupied_columns_expr()),
            }
            rival_rows = []
            for name, program in rivals.items():
                outputs = [apply(program, pair["input"]) for pair in pairs]
                demo_matches = [output == pair["output"]
                                for output, pair in zip(outputs[:2], episode["train"])]
                query_disagreements = [index for index, (output, pair) in enumerate(
                    zip(outputs[2:], episode["test"])) if output != pair["output"]]
                survives = all(demo_matches)
                row = {
                    "name": name,
                    "program_sha256": program_digest(program),
                    "demo_matches": demo_matches,
                    "survives_demos": survives,
                    "query_disagreement_indices": query_disagreements,
                }
                rival_rows.append(row)
                if survives and query_disagreements:
                    findings.append({
                        "seed": episode["seed"],
                        "settings": deepcopy(settings),
                        "rival": name,
                        "query_disagreement_indices": query_disagreements,
                    })
            audit_rows.append({
                "seed": episode["seed"],
                "settings": deepcopy(settings),
                "demonstrations": len(episode["train"]),
                "queries": len(episode["test"]),
                "declared_setting_survivors": deepcopy(check["survivors"]),
                "custom_rivals": rival_rows,
            })

        witness_cases = []
        requested = [
            (0, {"count_basis": "cells", "scale_axes": "both"}),
            (17, {"count_basis": "colors", "scale_axes": "columns"}),
        ]
        for seed, settings in requested:
            episode = next(ep for ep in execution["episodes"]
                           if ep["seed"] == seed and ep["settings"] == settings)
            pair = next(pair for pair in episode["test"] if selected_amount(pair["input"], settings) > 1)
            amount = selected_amount(pair["input"], settings)
            wrong_amount = amount - 1
            counterfactual = amount_program(settings, str(wrong_amount))
            output = apply(episode["program"], pair["input"])
            wrong = apply(counterfactual, pair["input"])
            if output != pair["output"] or output == wrong:
                raise ValueError("wrong-intermediate witness failed to change the final output")
            cells, colors = counts(pair["input"])
            witness_cases.append({
                "input": deepcopy(pair["input"]),
                "settings": deepcopy(settings),
                "intermediate_value": {
                    "nonzero_cells": cells,
                    "distinct_nonzero_colors": colors,
                    "selected_count_basis": settings["count_basis"],
                    "selected_amount": amount,
                    "counterfactual_amount": wrong_amount,
                },
                "program": episode["program"],
                "output": output,
                "counterfactual_program": counterfactual,
                "counterfactual_output": wrong,
                "ablation": "wrong_intermediate",
            })
    finally:
        bridge.close()

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": deepcopy(q["source_binding"]),
        "racket": {"backend": "racket", "protected": True},
        "racket_runtime_identity": identity,
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": witness_cases,
        "limits": (
            "Two source-bound wrong-intermediate cases plus a finite visible-demo shortcut audit; "
            "not a universal proof of algorithmic depth or unique interpretation."
        ),
    }
    audit = {
        "schema": "arcpuzzles-parametric-visible-demo-self-audit-v1",
        "task_id": TASK_ID,
        "source_binding": deepcopy(q["source_binding"]),
        "racket": {"backend": "racket", "protected": True},
        "racket_runtime_identity": identity,
        "status": "passed" if not findings else "teaching_hole_found",
        "episodes_checked": len(audit_rows),
        "declared_settings_checked": 6,
        "custom_rivals_per_episode": 4,
        "racket_evaluations": evaluations,
        "findings": findings,
        "episodes": audit_rows,
        "limits": (
            "Finite audit of the six declared settings plus four count shortcuts over the "
            "12 qualified two-demo/four-query episodes; no universal uniqueness claim."
        ),
    }
    if findings:
        raise ValueError("visible demonstrations leave a tested wrong rule alive: " + json.dumps(findings))

    output_dir.mkdir(parents=True)
    witness_path = output_dir / "sequential-dependency-witness.json"
    audit_path = output_dir / "visible-demo-self-audit.json"
    witness_path.write_bytes(raw(witness))
    audit_path.write_bytes(raw(audit))

    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    dependency = {key: witness[key] for key in
                  ("step_a", "intermediate", "step_b", "why_b_depends_on_a")}
    dependency["witness_path"] = witness_path.name
    validation = validate_sequential_witness(
        {"sequential_dependency": dependency}, q,
        lambda _: witness_path.read_bytes(),
    )
    from arcpuzzles.review_sequential_replay import replay_witness
    replay = replay_witness(repo, witness, timeout=60)
    (output_dir / "sequential-dependency-replay.json").write_bytes(raw(replay))
    (output_dir / "summary.json").write_bytes(raw({
        "status": "passed",
        "task_id": TASK_ID,
        "witness_validation": validation,
        "owner_path_replay": {
            "status": replay["status"],
            "cases": len(replay["cases"]),
            "evaluations": replay["evaluations"],
        },
        "self_audit": {
            "status": audit["status"],
            "episodes_checked": audit["episodes_checked"],
            "custom_rivals_per_episode": audit["custom_rivals_per_episode"],
            "findings": len(findings),
        },
        "builder_racket_evaluations": evaluations,
        "files": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (witness_path, audit_path, output_dir / "sequential-dependency-replay.json")
        },
    }))
    print(json.dumps({
        "status": "passed",
        "witness_cases": len(witness_cases),
        "self_audit_episodes": len(audit_rows),
        "self_audit_findings": len(findings),
        "builder_racket_evaluations": evaluations,
        "owner_path_replay_evaluations": replay["evaluations"],
        "out": str(output_dir),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
