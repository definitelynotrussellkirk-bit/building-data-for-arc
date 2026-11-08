#!/usr/bin/env python3
"""Bounded protected-Racket, teaching-rival, and public-projection evidence."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "6347dcb736b5"


def _load(name: str, filename: str):
    path = (HERE / filename).resolve()
    if path.parent != HERE or not path.is_file():
        raise FileNotFoundError(path)
    module_name = name + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(module_name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("_arc_6347_verify_prototype", "prototype.py")
ADAPTER = _load("_arc_6347_verify_adapter", "adapter.py")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _source_inventory() -> dict[str, dict[str, Any]]:
    paths = {
        "adapter": HERE / "adapter.py",
        "prototype": HERE / "prototype.py",
        "promotion": HERE / "promotion.json",
        "all_objects": HERE / "rules" / "all_objects.rkt",
        "marker_relay": HERE / "rules" / "marker_relay.rkt",
    }
    return {
        name: {
            "path": path.relative_to(HERE.parents[3]).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for name, path in paths.items()
    }


def build_evidence(
    output: str | Path,
    *,
    seeds: tuple[int, ...] = (0, 17),
    demos: int = 3,
) -> dict[str, Any]:
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"evidence destination is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    if not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("seeds must be nonempty nonnegative literal integers")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 2..6")

    finite_jobs: list[dict[str, Any]] = []
    finite_failures: list[dict[str, Any]] = []
    for seed in range(12):
        for demo_count in (2, 3, 6):
            for scope in PROTOTYPE.SCOPES:
                episode = ADAPTER.generate(seed, {"outline_scope": scope}, demo_count, 4)
                audit = PROTOTYPE.audit_teaching_set(episode["train"], scope)
                failed_rivals = [name for name, row in audit["rivals"].items() if not row["refuted"]]
                if audit["setting_survivors"] != [scope] or failed_rivals:
                    finite_failures.append({
                        "seed": seed,
                        "demos": demo_count,
                        "outline_scope": scope,
                        "setting_survivors": audit["setting_survivors"],
                        "unrefuted_rivals": failed_rivals,
                    })
                finite_jobs.append({
                    "seed": seed,
                    "demos": demo_count,
                    "queries": 4,
                    "outline_scope": scope,
                    "setting_survivors": audit["setting_survivors"],
                    "rivals": audit["rivals"],
                })
    finite_report = {
        "schema": "arcpuzzles-6347dcb736b5-finite-teaching-audit-v1",
        "task_id": TASK_ID,
        "seeds": list(range(12)),
        "demo_counts": [2, 3, 6],
        "settings": list(PROTOTYPE.SCOPES),
        "jobs": len(finite_jobs),
        "job_records": finite_jobs,
        "failures": finite_failures,
        "limits": "Finite declared-setting and named Python-rival audit; not a proof of unique induction.",
    }

    sources = {scope: ADAPTER.program({"outline_scope": scope}) for scope in PROTOTYPE.SCOPES}
    protected_jobs: list[dict[str, Any]] = []
    protected_failures: list[dict[str, Any]] = []
    cache: dict[tuple[str, str], list[list[int]]] = {}
    retained_episodes: list[dict[str, Any]] = []

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket runtime required")
        wrapped = {scope: wrap_rule(source) for scope, source in sources.items()}

        def apply(scope: str, grid: list[list[int]]) -> list[list[int]]:
            key = scope, PROTOTYPE.grid_digest(grid)
            if key not in cache:
                cache[key] = bridge.eval_text(f"({wrapped[scope]} {_grid_literal(grid)})")
            return deepcopy(cache[key])

        for seed in seeds:
            matched_inputs: list[str] | None = None
            for scope in PROTOTYPE.SCOPES:
                episode = ADAPTER.generate(seed, {"outline_scope": scope}, demos, 4)
                retained_episodes.append({"seed": seed, "outline_scope": scope, "episode": episode})
                inputs = [PROTOTYPE.grid_digest(pair["input"]) for pair in episode["train"] + episode["test"]]
                if matched_inputs is None:
                    matched_inputs = inputs
                elif inputs != matched_inputs:
                    protected_failures.append({
                        "kind": "settings_inputs_not_matched",
                        "seed": seed,
                        "outline_scope": scope,
                    })
                pairs = episode["train"] + episode["test"]
                mismatches = [
                    index for index, pair in enumerate(pairs)
                    if apply(scope, pair["input"]) != pair["output"]
                ]
                if mismatches:
                    protected_failures.append({
                        "kind": "selected_program_label_mismatch",
                        "seed": seed,
                        "outline_scope": scope,
                        "pair_indexes": mismatches,
                    })
                survivors = []
                query_disagreements = {}
                for candidate in PROTOTYPE.SCOPES:
                    if all(apply(candidate, pair["input"]) == pair["output"] for pair in episode["train"]):
                        survivors.append(candidate)
                    query_disagreements[candidate] = sum(
                        apply(candidate, pair["input"]) != pair["output"]
                        for pair in episode["test"]
                    )
                if survivors != [scope]:
                    protected_failures.append({
                        "kind": "protected_program_survivor_failure",
                        "seed": seed,
                        "outline_scope": scope,
                        "survivors": survivors,
                    })
                protected_jobs.append({
                    "seed": seed,
                    "demos": demos,
                    "queries": 4,
                    "settings": {"outline_scope": scope},
                    "survivors": survivors,
                    "query_disagreements": query_disagreements,
                    "input_sha256": inputs,
                    "program_sha256": hashlib.sha256(sources[scope].encode()).hexdigest(),
                })

    protected_report = {
        "schema": "arcpuzzles-6347dcb736b5-protected-execution-v1",
        "task_id": TASK_ID,
        "racket": identity,
        "settings": list(PROTOTYPE.SCOPES),
        "seeds": list(seeds),
        "demos": demos,
        "queries": 4,
        "programs": {
            scope: {
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
                "path": f"generators/{TASK_ID}/workspace/parametric/rules/{scope}.rkt",
            }
            for scope, source in sources.items()
        },
        "jobs": protected_jobs,
        "evaluations": len(cache),
        "failures": protected_failures,
    }

    projection_records: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    for retained in retained_episodes:
        seed = retained["seed"]
        scope = retained["outline_scope"]
        episode = retained["episode"]
        for query_index in range(4):
            public = PROTOTYPE.public_turn(episode, query_index)
            raw = public_challenge_bytes(public)
            public_id = public_challenge_id(public)
            if public_id != hashlib.sha256(raw).hexdigest():
                raise AssertionError("public ID differs from exact visible-byte hash")
            changed = dict(episode)
            changed["seed"] = seed + 999999
            changed["settings"] = {"outline_scope": "private-change"}
            changed["program_solution"] = "private-change"
            if public_challenge_bytes(PROTOTYPE.public_turn(changed, query_index)) != raw:
                raise AssertionError("private metadata changed public bytes")
            previous = payloads.get(public_id)
            if previous is not None:
                raise ValueError(f"duplicate visible challenge: {public_id}")
            payloads[public_id] = raw
            projection_records.append({
                "public_id": public_id,
                "filename": f"public/{public_id}.json",
                "seed": seed,
                "outline_scope": scope,
                "query_index": query_index,
            })
    public_dir = output / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    for public_id in sorted(payloads):
        (public_dir / f"{public_id}.json").write_bytes(payloads[public_id])
    projection_index = {
        "schema": "arcpuzzles-6347dcb736b5-public-turn-index-v1",
        "task_id": TASK_ID,
        "identity": "SHA-256 of exact reviewer_support.public_challenge_bytes",
        "projections": sorted(projection_records, key=lambda row: row["public_id"]),
        "private_fields_excluded": ["settings", "seed", "program_solution", "query answers", "future queries"],
    }

    summary = {
        "schema": "arcpuzzles-6347dcb736b5-parametric-evidence-summary-v1",
        "task_id": TASK_ID,
        "status": "passed" if not finite_failures and not protected_failures else "failed",
        "settings": list(PROTOTYPE.SCOPES),
        "seeds": list(seeds),
        "demonstrations": demos,
        "queries_per_episode": 4,
        "protected_racket_evaluations": len(cache),
        "public_files": len(payloads),
        "finite_audit": {"jobs": len(finite_jobs), "failures": finite_failures},
        "protected_execution": {"jobs": len(protected_jobs), "failures": protected_failures},
        "source_inventory": _source_inventory(),
        "evidence": [
            "finite-audit.json",
            "protected-execution.json",
            "projection-index.json",
            "public/",
        ],
        "limits": [
            "Finite named-rival audit only; it does not prove universal uniqueness.",
            "Reviewer protected execution is not owner acceptance or training admission.",
        ],
    }

    _write_json(output / "finite-audit.json", finite_report)
    _write_json(output / "protected-execution.json", protected_report)
    _write_json(output / "projection-index.json", projection_index)
    _write_json(output / "summary.json", summary)
    if summary["status"] != "passed":
        raise RuntimeError("evidence build found failures")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    summary = build_evidence(args.out, seeds=tuple(args.seeds or (0, 17)), demos=args.demos)
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
