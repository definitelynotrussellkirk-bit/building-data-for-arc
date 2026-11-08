#!/usr/bin/env python3
"""Build compact self-audit and sequential-dependency evidence.

The audit consumes native worker execution JSON, so its visible labels are the
protected-Racket labels used by qualification.  The witness independently
replays the qualified program and a skip-A counterfactual through protected
Racket and binds the result to the qualification source inventory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
TASK_ID = "d2534264df36"
STEP_A = (
    "Execute the canonical ring-completion rule so each independent nonzero "
    "source materializes its Chebyshev ring."
)
INTERMEDIATE = (
    "The ordered nonzero hits on the completed north hub ray, including the "
    "selected nearest/farthest hit row and its completed side color."
)
STEP_B = (
    "Use the selected hit row to set the cross extent and its side color to "
    "fill only blank cells of the interior orthogonal cross."
)
WHY = (
    "B cannot choose either its extent or color from the raw source because the "
    "hub ray is blank before A. Skipping A removes every ray hit and changes the "
    "final output on the retained protected-Racket cases."
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load("d2534264df36_evidence_prototype", HERE / "prototype.py")
rivals = _load("d2534264df36_evidence_rivals", HERE / "rivals.py")


def _protected(execution: dict) -> dict:
    if type(execution) is not dict:
        raise ValueError("execution must be an object")
    identity = execution.get("racket")
    if (
        type(identity) is not dict
        or identity.get("backend") != "racket"
        or identity.get("protected") is not True
    ):
        raise ValueError("evidence requires protected Racket execution")
    return identity


def _episode(execution: dict, seed: int, mode: str) -> dict:
    matches = [
        row
        for row in execution.get("episodes", [])
        if row.get("seed") == seed and row.get("settings") == {"cross_stop": mode}
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one native episode for seed {seed}, mode {mode}")
    return matches[0]


def _check(execution: dict, seed: int, mode: str) -> dict:
    matches = [
        row
        for row in execution.get("checks", [])
        if row.get("seed") == seed and row.get("settings") == {"cross_stop": mode}
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one native teaching check for seed {seed}, mode {mode}")
    return matches[0]


def audit_from_execution(
    execution: dict,
    *,
    seed: int = 71,
    demos: int = 2,
    queries: int = 4,
) -> dict:
    """Audit protected native labels against a finite authored rival set."""
    _protected(execution)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 4 <= queries <= 8:
        raise ValueError("queries must be an exact integer in 4..8")

    settings_rows = []
    for mode in prototype.MODES:
        episode = _episode(execution, seed, mode)
        if len(episode.get("train", [])) < demos or len(episode.get("test", [])) < queries:
            raise ValueError("native episode does not contain the requested audit slice")
        visible_slice = {
            "train": episode["train"][:demos],
            "test": episode["test"][:queries],
        }
        shortcut_rows = rivals.audit_episode(visible_slice, mode)
        if any(row["fits_all_demos"] for row in shortcut_rows):
            survivors = [row["name"] for row in shortcut_rows if row["fits_all_demos"]]
            raise ValueError("visible demonstrations retain shortcut rivals: " + ", ".join(survivors))
        teaching = _check(execution, seed, mode)
        settings_rows.append(
            {
                "selected_mode": mode,
                "declared_survivors": teaching.get("survivors"),
                "rivals": shortcut_rows,
            }
        )

    return {
        "schema": "d2534264df36-cross-stop-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "racket": {"backend": "racket", "protected": True},
        "counts": {
            "settings": len(settings_rows),
            "demos_used": demos,
            "queries_used": queries,
            "rivals": len(rivals.RIVAL_NAMES),
        },
        "repair": (
            "The input grammar includes independent singleton-row and singleton-column "
            "side witnesses, so the previously surviving paired-only activation rule "
            "is now contradicted in the minimum visible demonstrations."
        ),
        "settings": settings_rows,
        "limits": (
            "Finite authored rival audit over one protected-Racket seed; it does not "
            "prove uniqueness against every possible program."
        ),
    }


def _setting_key(settings: dict) -> str:
    return json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _find_pair(episode: dict, grid: list[list[int]]) -> dict:
    matches = [
        pair
        for pair in episode.get("train", []) + episode.get("test", [])
        if pair.get("input") == grid
    ]
    if len(matches) != 1:
        raise ValueError("witness input is not uniquely present in the native episode")
    return matches[0]


def build_sequential_witness(
    qualification: dict,
    execution: dict,
    *,
    seed: int = 71,
    sample_index: int = 4,
    modes: Iterable[str] = ("nearest_hit", "farthest_hit"),
) -> tuple[dict, dict]:
    """Replay qualified composed settings and raw-grid skip-A ablations."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    identity_claim = _protected(execution)
    source_binding = qualification.get("source_binding")
    programs = qualification.get("programs")
    if type(source_binding) is not dict or type(programs) is not dict:
        raise ValueError("qualification lacks source binding or program map")
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(sample_index) is not int or not 0 <= sample_index <= 10**6:
        raise ValueError("sample_index must be a bounded exact integer")
    requested_modes = tuple(modes)
    if not requested_modes or any(mode not in ("nearest_hit", "farthest_hit") for mode in requested_modes):
        raise ValueError("witness modes must be composed settings")

    grid = prototype.build_input(seed, sample_index)
    cases = []
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        runtime_identity = bridge.runtime_identity
        if runtime_identity.get("backend") != "racket" or runtime_identity.get("protected") is not True:
            raise ValueError("witness replay requires protected Racket")
        bridge.define_grid("d253_dependency_grid", grid)
        for mode in requested_modes:
            settings = {"cross_stop": mode}
            program = prototype.program(settings)
            expected_digest = programs.get(_setting_key(settings))
            if hashlib.sha256(program.encode()).hexdigest() != expected_digest:
                raise ValueError(f"{mode} program differs from the qualified program map")
            episode = _episode(execution, seed, mode)
            native_pair = _find_pair(episode, grid)
            counterfactual_program = prototype.skip_a_program(mode)
            output = bridge.eval_text(f"({wrap_rule(program)} d253_dependency_grid)")
            counterfactual_output = bridge.eval_text(
                f"({wrap_rule(counterfactual_program)} d253_dependency_grid)"
            )
            if output != native_pair.get("output"):
                raise ValueError("witness selected output differs from native protected label")
            if output == counterfactual_output:
                raise ValueError("skip-A counterfactual did not change final output")
            completed = prototype.oracle.complete_rings(grid)
            intermediate = prototype.oracle.ray_intermediate(completed, mode)
            cases.append(
                {
                    "input": grid,
                    "settings": settings,
                    "intermediate_value": intermediate,
                    "program": program,
                    "output": output,
                    "ablation": "skip_a",
                    "counterfactual_program": counterfactual_program,
                    "counterfactual_output": counterfactual_output,
                }
            )

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": source_binding,
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": cases,
    }
    replay = {
        "status": "protected_racket_replayed",
        "protected": True,
        "evaluations": 2 * len(cases),
        "seed": seed,
        "sample_index": sample_index,
        "sizes": [len(case["input"]) for case in cases],
        "modes": [case["settings"]["cross_stop"] for case in cases],
        "runtime": runtime_identity,
        "qualification_runtime_matches_protected_claim": (
            identity_claim.get("backend") == "racket" and identity_claim.get("protected") is True
        ),
    }
    return witness, replay


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain an object")
    return value


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    audit = actions.add_parser("audit")
    audit.add_argument("--execution", type=Path, required=True)
    audit.add_argument("--out", type=Path, required=True)
    audit.add_argument("--seed", type=int, default=71)
    audit.add_argument("--demos", type=int, default=2)
    audit.add_argument("--queries", type=int, default=4)
    witness = actions.add_parser("witness")
    witness.add_argument("--qualification", type=Path, required=True)
    witness.add_argument("--execution", type=Path, required=True)
    witness.add_argument("--out", type=Path, required=True)
    witness.add_argument("--replay-out", type=Path, required=True)
    witness.add_argument("--seed", type=int, default=71)
    witness.add_argument("--sample-index", type=int, default=4)
    args = parser.parse_args()

    if args.action == "audit":
        report = audit_from_execution(
            _read(args.execution), seed=args.seed, demos=args.demos, queries=args.queries
        )
        _write(args.out, report)
        print(json.dumps({"status": "pass", "out": str(args.out), "counts": report["counts"]}, sort_keys=True))
        return 0

    qualification = _read(args.qualification)
    evidence, replay = build_sequential_witness(
        qualification,
        _read(args.execution),
        seed=args.seed,
        sample_index=args.sample_index,
    )
    _write(args.out, evidence)
    _write(args.replay_out, replay)
    print(json.dumps({"status": "pass", "out": str(args.out), "replay": str(args.replay_out), "cases": len(evidence["cases"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
