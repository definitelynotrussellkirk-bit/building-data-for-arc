#!/usr/bin/env python3
"""Protected-Racket and public-projection audit for this task-local family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_f60cfd11346a_verify_prototype", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def audit(*, public_dir: Path) -> dict[str, Any]:
    prototype = _load_prototype()
    programs = {mode: prototype.program_for(mode) for mode in prototype.MODES}
    wrong_program = (HERE / "wrong_global_port_count.rkt").read_text(encoding="utf-8")
    wrapped = {name: wrap_rule(program) for name, program in {**programs, "wrong_global_port_count": wrong_program}.items()}
    evaluations = 0
    jobs = []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")

        def execute(name: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(f"({wrapped[name]} {_literal(grid)})")

        for mode in prototype.MODES:
            other = next(value for value in prototype.MODES if value != mode)
            for seed in (0, 17):
                for demos in (2, 6):
                    episode = prototype.generate_episode(seed, mode=mode, demos=demos, queries=4)
                    for pair in episode["train"] + episode["test"]:
                        actual = execute(mode, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError((mode, seed, demos, "label mismatch"))
                    other_fits = all(
                        execute(other, pair["input"]) == pair["output"]
                        for pair in episode["train"]
                    )
                    if other_fits:
                        raise AssertionError((mode, seed, demos, "setting not identified"))
                    jobs.append({
                        "mode": mode,
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "labels": demos + 4,
                    })

        witness_episode = prototype.generate_episode(
            0, mode="reachable_port_relay", demos=3, queries=4
        )
        witness_pair = next(
            pair for pair in witness_episode["test"]
            if prototype.analyze_scene(pair["input"])["active_port_count"] != 3
        )
        analysis = prototype.analyze_scene(witness_pair["input"])
        correct = execute("reachable_port_relay", witness_pair["input"])
        wrong = execute("wrong_global_port_count", witness_pair["input"])
        if correct != witness_pair["output"] or wrong == correct:
            raise AssertionError("causal counterfactual did not change the output")

        racket = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }

    public_dir.mkdir(parents=True, exist_ok=True)
    public_rows = []
    for mode in prototype.MODES:
        full = prototype.generate_episode(5, mode=mode, demos=3, queries=4)
        single = prototype.generate_episode(5, mode=mode, demos=3, queries=1)
        if single["train"] != full["train"] or single["test"] != full["test"][:1]:
            raise AssertionError("query stream is not prefix-stable")
        public = _public_episode(full)
        payload = public_challenge_bytes(public)
        digest = public_challenge_id(public)
        path = public_dir / f"challenge-{digest}.json"
        path.write_bytes(payload)
        first_single = public_challenge_bytes(_public_episode(single))
        first_from_full = public_challenge_bytes({
            "train": public["train"],
            "test": public["test"][:1],
        })
        if first_single != first_from_full:
            raise AssertionError("single-query first turn differs from four-query prefix")
        public_rows.append({
            "mode": mode,
            "path": path.name,
            "sha256": digest,
            "demos": 3,
            "queries": 4,
            "single_query_prefix_sha256": hashlib.sha256(first_single).hexdigest(),
        })

    python_audit = prototype.audit_python(seeds=range(32), demo_counts=range(2, 7))
    if python_audit["ambiguities"]:
        raise AssertionError(python_audit["ambiguities"][:3])

    return {
        "schema": "f60cfd11346a-parametric-audit-v1",
        "status": "passed",
        "program_sha256": {
            mode: hashlib.sha256(program.encode("utf-8")).hexdigest()
            for mode, program in programs.items()
        },
        "sources": {
            name: _sha(HERE / name)
            for name in (
                "adapter.py",
                "prototype.py",
                "canonical.rkt",
                "relay.rkt",
                "wrong_global_port_count.rkt",
            )
        },
        "protected_racket": racket,
        "racket_evaluations": evaluations,
        "jobs": jobs,
        "python_teaching_audit": python_audit,
        "public_exports": public_rows,
        "causal_probe": {
            "seed": 0,
            "active_port_count": analysis["active_port_count"],
            "all_port_count": len(analysis["all_ports"]),
            "selected_anchor": list(analysis["selected_anchor"]),
            "wrong_global_count_rank": len(analysis["all_ports"]),
            "outputs_differ": correct != wrong,
            "ablation": "wrong_intermediate",
        },
        "limits": (
            "Finite seeds, declared rivals, and protected executions only; owner "
            "native acceptance and training admission remain pending."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    args = parser.parse_args()
    report = audit(public_dir=args.public_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["racket_evaluations"],
        "episodes": report["python_teaching_audit"]["episodes"],
        "ambiguities": len(report["python_teaching_audit"]["ambiguities"]),
        "public_exports": len(report["public_exports"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
