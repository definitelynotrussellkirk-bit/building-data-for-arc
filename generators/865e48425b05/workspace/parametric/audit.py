#!/usr/bin/env python3
"""Bounded protected-Racket audit for the palette-mask layout family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "865e48425b05"
SETTINGS = (
    {"layout_policy": "horizontal"},
    {"layout_policy": "vertical"},
    {"layout_policy": "dominant_axis"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_palette_mask_layout_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _turn_bytes(visible: dict[str, Any]) -> bytes:
    """Canonical bytes for either a complete first turn or a later delta turn."""
    if "train" in visible:
        return public_challenge_bytes(visible)
    if set(visible) != {"test"} or type(visible["test"]) is not list or len(visible["test"]) != 1:
        raise ValueError("later turn must contain exactly one test input")
    pair = visible["test"][0]
    if type(pair) is not dict or set(pair) != {"input"}:
        raise ValueError("later turn query must contain only input")
    grid = pair["input"]
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("later turn input must be a strict ARC grid")
    return (json.dumps(visible, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _turn_id(visible: dict[str, Any]) -> str:
    return hashlib.sha256(_turn_bytes(visible)).hexdigest()


def _mismatched_cells(left: list[list[int]], right: list[list[int]]) -> int:
    height = max(len(left), len(right))
    width = max(len(left[0]), len(right[0]))
    total = 0
    for row in range(height):
        for col in range(width):
            a = left[row][col] if row < len(left) and col < len(left[0]) else None
            b = right[row][col] if row < len(right) and col < len(right[0]) else None
            total += a != b
    return total


def _public_projection(adapter, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    seen_payloads: set[bytes] = set()
    duplicate_payloads = 0
    for episode_index, episode in enumerate(episodes):
        episode_payloads: set[bytes] = set()
        one = adapter.generate(
            episode["seed"], episode["settings"], demos=len(episode["train"]), queries=1
        )
        for query_index in range(len(episode["test"])):
            try:
                visible = adapter.public_turn(episode, query_index)
                payload = _turn_bytes(visible)
                if payload in episode_payloads:
                    failures.append(
                        {"episode": episode_index, "query": query_index, "failure": "duplicate query within one episode"}
                    )
                episode_payloads.add(payload)
                if payload in seen_payloads:
                    duplicate_payloads += 1
                seen_payloads.add(payload)
                if query_index == 0 and visible != adapter.public_turn(one, 0):
                    failures.append(
                        {"episode": episode_index, "query": query_index, "failure": "first turn differs from one-query prefix"}
                    )
                if len(visible.get("test", [])) != 1 or set(visible["test"][0]) != {"input"}:
                    failures.append(
                        {"episode": episode_index, "query": query_index, "failure": "query is not singly masked"}
                    )
                if query_index == 0:
                    if len(visible.get("train", [])) != len(episode["train"]):
                        failures.append(
                            {"episode": episode_index, "query": query_index, "failure": "first turn lost demonstrations"}
                        )
                elif "train" in visible:
                    failures.append(
                        {"episode": episode_index, "query": query_index, "failure": "later turn repeats demonstrations"}
                    )

                changed = deepcopy(episode)
                changed["settings"] = {"layout_policy": "horizontal"}
                changed["program_solution"] = "private mutation"
                changed["seed"] = -999
                for index, pair in enumerate(changed["test"]):
                    pair["output"] = [[9]]
                    if index != query_index:
                        pair["input"] = [[8]]
                if query_index > 0:
                    changed["train"] = [{"input": [[7]], "output": [[6]]}]
                if adapter.public_turn(changed, query_index) != visible:
                    failures.append(
                        {"episode": episode_index, "query": query_index, "failure": "private/future mutation changed visible turn"}
                    )
                records.append(
                    {
                        "episode": episode_index,
                        "query_index": query_index,
                        "public_id": _turn_id(visible),
                        "bytes": len(payload),
                    }
                )
            except Exception as exc:  # retained as evidence
                failures.append(
                    {"episode": episode_index, "query": query_index, "exception": f"{type(exc).__name__}: {exc}"}
                )
    return {
        "turns_checked": len(records),
        "unique_turn_payloads": len(seen_payloads),
        "cross_episode_duplicate_payloads": duplicate_payloads,
        "records": records,
        "failures": failures,
    }


def _causal_witness(adapter, apply=None) -> dict[str, Any]:
    settings = {"layout_policy": "dominant_axis"}
    episode = adapter.generate(0, settings, demos=2, queries=4)
    grid = episode["train"][1]["input"]  # tall mask
    trace = adapter.dependency_trace(grid, settings)
    selected_program = adapter.program(settings)
    counterfactual_program = adapter.program({"layout_policy": "horizontal"})
    if apply is None:
        selected = adapter.solve(grid, settings)
        counterfactual = adapter.solve(grid, {"layout_policy": "horizontal"})
        backend = "python-claim"
    else:
        selected = apply(selected_program, grid)
        counterfactual = apply(counterfactual_program, grid)
        backend = "protected-racket"
    return {
        "schema": "865e48425b05-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "setting": settings,
        "step_a": trace["step_a"],
        "intermediate": trace["intermediate"],
        "step_b": trace["step_b"],
        "why_b_depends_on_a": trace["why_b_depends_on_a"],
        "selected_axis": trace["selected_axis"],
        "counterfactual": "skip A and always pack horizontally",
        "input": grid,
        "selected_program": selected_program,
        "counterfactual_program": counterfactual_program,
        "selected_output": selected,
        "counterfactual_output": counterfactual,
        "mismatched_cells": _mismatched_cells(selected, counterfactual),
        "execution_backend": backend,
    }


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    execute_racket: bool = True,
) -> dict[str, Any]:
    adapter = _load_adapter()
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    episodes = [
        adapter.generate(seed, settings, demos=demos, queries=4)
        for seed in seeds
        for demos in demo_counts
        for settings in SETTINGS
    ]
    harmful: list[dict[str, Any]] = []
    harmless: list[dict[str, Any]] = []
    parity: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    evaluations = 0
    bridge = None
    identity: dict[str, Any] = {"backend": "python-claim", "protected": False}
    apply = None
    if execute_racket:
        runtime = ROOT / "shared/runtime"
        context = _local_imports(runtime, HERE)
        context.__enter__()
        try:
            apply, identity, bridge = _real_evaluator(runtime)
        except Exception:
            context.__exit__(*sys.exc_info())
            raise
    else:
        context = None

    try:
        for episode_index, episode in enumerate(episodes):
            settings = episode["settings"]
            selected_program = adapter.program(settings)
            pairs = episode["train"] + episode["test"]
            if apply is not None:
                for pair_index, pair in enumerate(pairs):
                    actual = apply(selected_program, pair["input"])
                    evaluations += 1
                    if actual != pair["output"]:
                        parity.append(
                            {
                                "episode": episode_index,
                                "program": "selected",
                                "pair": pair_index,
                                "mismatched_cells": _mismatched_cells(actual, pair["output"]),
                            }
                        )

            rival_programs = adapter.rival_programs(settings)
            demo_rival_claims = [adapter.rival_outputs(pair["input"], settings) for pair in episode["train"]]
            survivor_names: list[str] = []
            for name, rival_program in rival_programs.items():
                fits = True
                for demo_index, pair in enumerate(episode["train"]):
                    claim = demo_rival_claims[demo_index][name]
                    actual = apply(rival_program, pair["input"]) if apply is not None else claim
                    if apply is not None:
                        evaluations += 1
                        if actual != claim:
                            parity.append(
                                {
                                    "episode": episode_index,
                                    "program": name,
                                    "pair": demo_index,
                                    "mismatched_cells": _mismatched_cells(actual, claim),
                                }
                            )
                    if actual != pair["output"]:
                        fits = False
                        break
                if not fits:
                    continue
                survivor_names.append(name)
                disagreements = []
                for query_index, pair in enumerate(episode["test"]):
                    claim = adapter.rival_outputs(pair["input"], settings)[name]
                    actual = apply(rival_program, pair["input"]) if apply is not None else claim
                    if apply is not None:
                        evaluations += 1
                        if actual != claim:
                            parity.append(
                                {
                                    "episode": episode_index,
                                    "program": name,
                                    "pair": len(episode["train"]) + query_index,
                                    "mismatched_cells": _mismatched_cells(actual, claim),
                                }
                            )
                    if actual != pair["output"]:
                        disagreements.append(query_index)
                row = {
                    "episode": episode_index,
                    "settings": settings,
                    "seed": episode["seed"],
                    "demos": len(episode["train"]),
                    "rival": name,
                    "query_disagreements": disagreements,
                }
                (harmful if disagreements else harmless).append(row)
            checks.append(
                {
                    "episode": episode_index,
                    "seed": episode["seed"],
                    "settings": settings,
                    "demos": len(episode["train"]),
                    "queries": len(episode["test"]),
                    "surviving_named_rivals": survivor_names,
                }
            )
        witness = _causal_witness(adapter, apply)
    finally:
        if bridge is not None:
            bridge.close()
        if context is not None:
            context.__exit__(None, None, None)

    public = _public_projection(adapter, episodes)
    failures = bool(
        harmful
        or parity
        or public["failures"]
        or witness["mismatched_cells"] <= 0
        or (execute_racket and identity.get("protected") is not True)
    )
    return {
        "schema": "865e48425b05-parametric-audit-v1",
        "task_id": TASK_ID,
        "settings": list(SETTINGS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": len(episodes),
        "labels_checked": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
        "racket_evaluations": evaluations,
        "racket": identity,
        "checks": checks,
        "harmful_survivors": harmful,
        "harmless_survivors": harmless,
        "python_racket_mismatches": parity,
        "public_projection": public,
        "sequential_dependency_witness": witness,
        "scope": "Finite named rivals and sampled seeds/counts only; not universal uniqueness.",
        "status": "fail" if failures else "pass",
    }


def write_public_examples(out_dir: Path, *, seed: int = 0, demos: int = 3) -> dict[str, Any]:
    adapter = _load_adapter()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    controller = out_dir / "controller"
    turns = out_dir / "turns"
    private = out_dir / "private"
    for path in (controller, turns, private):
        path.mkdir()
    metadata = []
    for settings in SETTINGS:
        episode = adapter.generate(seed, settings, demos=demos, queries=4)
        controller_payload = public_challenge_bytes(episode)
        controller_id = public_challenge_id(episode)
        (controller / f"{controller_id}.json").write_bytes(controller_payload)
        turn_ids = []
        for query_index in range(4):
            visible = adapter.public_turn(episode, query_index)
            turn_id = _turn_id(visible)
            (turns / f"{turn_id}.json").write_bytes(_turn_bytes(visible))
            turn_ids.append(turn_id)
        metadata.append(
            {
                "controller_id": controller_id,
                "turn_ids": turn_ids,
                "settings": settings,
                "episode": episode,
            }
        )
    (private / "episodes.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return {
        "episodes": len(metadata),
        "controller_files": len(list(controller.glob("*.json"))),
        "turn_files": len(list(turns.glob("*.json"))),
        "private": str(private / "episodes.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path)
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args()
    report = build_report(execute_racket=not args.no_racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.witness_out:
        args.witness_out.parent.mkdir(parents=True, exist_ok=True)
        args.witness_out.write_text(
            json.dumps(report["sequential_dependency_witness"], indent=2, sort_keys=True) + "\n"
        )
    public_summary = None
    if args.public_dir:
        public_summary = write_public_examples(args.public_dir)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes_checked": report["episodes_checked"],
                "labels_checked": report["labels_checked"],
                "racket_evaluations": report["racket_evaluations"],
                "harmful_survivors": len(report["harmful_survivors"]),
                "python_racket_mismatches": len(report["python_racket_mismatches"]),
                "public_failures": len(report["public_projection"]["failures"]),
                "out": str(args.out),
                "public": public_summary,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
