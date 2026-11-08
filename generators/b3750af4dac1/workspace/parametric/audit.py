#!/usr/bin/env python3
"""Bounded protected-Racket audit for the room-match neighbor relay family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_b3750af4dac1_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rival_programs(adapter, finish: str) -> dict[str, str]:
    if finish not in ("match_only", "mark_match_neighbors"):
        raise ValueError(finish)
    other = "mark_match_neighbors" if finish == "match_only" else "match_only"
    result = {"other_setting": adapter.program({"finish": other})}
    if finish == "match_only":
        from puzzle_generators.rule_wrap import wrap_rule

        canonical = wrap_rule(adapter.program({"finish": "match_only"}))
        result.update({
            "area_only": adapter.area_only_program(),
            "degree_only": adapter.degree_only_program(),
            "first_candidate": adapter.first_candidate_program(),
            "wrong_match_color": f"""(rule! (lambda (g)
  (define matched ({canonical} g))
  (cellmap matched (r c v) (if (= v 8) 4 v))))""",
            "erase_match": f"""(rule! (lambda (g)
  (define matched ({canonical} g))
  (empty-grid (rows matched) (cols matched) 0)))""",
        })
        return result

    result.update({
        "wrong_intermediate": adapter.counterfactual_program(),
        "strip_neighbors": adapter.strip_neighbor_program(),
        "query_neighbors": adapter.query_neighbor_program(),
        "mark_all_candidates": adapter.all_candidate_program(),
    })
    return result


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(out: Path) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    public_dir = out / "public"
    public_dir.mkdir()

    adapter = _load_adapter()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes, public_challenge_id

    jobs: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    evaluations = 0
    public_index: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime = bridge.runtime_identity
        cache: dict[str, str] = {}

        def apply(source: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            wrapped = cache.setdefault(source, wrap_rule(source))
            evaluations += 1
            return bridge.eval_text(f"({wrapped} {_literal(grid)})")

        for finish in ("match_only", "mark_match_neighbors"):
            settings = {"finish": finish}
            selected = adapter.program(settings)
            rivals = rival_programs(adapter, finish)
            for seed in (0, 17):
                for demos in (2, 3, 6):
                    episode = adapter.generate(seed, settings, demos, 4)
                    pairs = episode["train"] + episode["test"]
                    for pair in pairs:
                        actual = apply(selected, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError("selected protected-Racket label differs from claim")
                    survivors: list[str] = []
                    for name, source in rivals.items():
                        if all(
                            apply(source, pair["input"]) == pair["output"]
                            for pair in episode["train"]
                        ):
                            survivors.append(name)
                            if any(
                                apply(source, pair["input"]) != pair["output"]
                                for pair in episode["test"]
                            ):
                                harmful.append({
                                    "finish": finish,
                                    "seed": seed,
                                    "demos": demos,
                                    "rival": name,
                                })
                    jobs.append({
                        "finish": finish,
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "surviving_declared_rivals": survivors,
                    })

                episode = adapter.generate(seed, settings, 3, 4)
                for query_index in range(4):
                    public = adapter.public_turn(episode, query_index)
                    payload = public_challenge_bytes(public)
                    identifier = public_challenge_id(public)
                    if identifier != hashlib.sha256(payload).hexdigest():
                        raise AssertionError("public ID does not hash exact public bytes")
                    path = public_dir / f"{identifier}.json"
                    if path.exists() and path.read_bytes() != payload:
                        raise AssertionError("public ID collision")
                    path.write_bytes(payload)
                    public_index.append({
                        "finish": finish,
                        "seed": seed,
                        "query_index": query_index,
                        "id": identifier,
                        "path": f"public/{identifier}.json",
                    })

        witness_input = adapter.sample_input(17, "test", 3)
        selected_source = adapter.program({"finish": "mark_match_neighbors"})
        wrong_source = adapter.counterfactual_program()
        selected_output = apply(selected_source, witness_input)
        wrong_output = apply(wrong_source, witness_input)
        claimed = adapter.transform(witness_input, {"finish": "mark_match_neighbors"})
        if selected_output != claimed or selected_output == wrong_output:
            raise AssertionError("causal witness did not replay")
        difference = sum(
            left != right
            for left_row, right_row in zip(selected_output, wrong_output)
            for left, right in zip(left_row, right_row)
        )
        state = adapter.match_state(witness_input)
        counterfactual = {
            "schema": "arcpuzzles-parametric-causal-witness-v1",
            "task_id": "b3750af4dac1",
            "status": "reviewer_replayed",
            "step_a": "compute the exact room-signature match strip with a unique color-8 position",
            "intermediate": "the canonical one-row candidate strip",
            "step_b": "recover the selected room from that strip and mark its color-7 doorway neighbors with color 4",
            "why_b_depends_on_a": "the selected strip position names the room whose graph neighborhood is projected; the first same-area candidate names a different room with a different neighborhood",
            "counterfactual": "replace the exact-signature match intermediate with a first-same-area match before applying the same neighbor relay",
            "input": witness_input,
            "selected_output": selected_output,
            "counterfactual_output": wrong_output,
            "different_cells": difference,
            "match_index": state["match_index"],
            "area_only_index": state["area_only_index"],
            "neighbor_positions": state["neighbor_positions"],
            "area_neighbor_positions": state["area_neighbor_positions"],
            "selected_program_sha256": hashlib.sha256(selected_source.encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(wrong_source.encode()).hexdigest(),
        }
        (out / "counterfactual.private.json").write_bytes(_raw(counterfactual))

    if harmful:
        raise AssertionError(f"harmful declared rivals survived: {harmful}")
    if len({row["id"] for row in public_index}) != len(public_index):
        raise AssertionError("duplicate public challenges")

    execution = {
        "schema": "b3750af4dac1-bounded-audit-v1",
        "task_id": "b3750af4dac1",
        "runtime": runtime,
        "jobs": jobs,
        "protected_racket_evaluations": evaluations,
        "harmful_declared_rivals": harmful,
        "public_turns": public_index,
        "source": {
            name: _sha(HERE / name)
            for name in ("adapter.py", "family.py", "canonical.rkt", "promotion.json", "audit.py")
        },
        "limits": {
            "seeds": [0, 17],
            "demo_counts": [2, 3, 6],
            "queries": 4,
            "sampler_attempts": 64,
            "rivals_are_finite": True,
        },
    }
    (out / "execution.private.json").write_bytes(_raw(execution))
    summary = {
        "schema": "b3750af4dac1-audit-summary-v1",
        "status": "passed",
        "jobs": len(jobs),
        "protected_racket_evaluations": evaluations,
        "harmful_declared_rivals": 0,
        "public_turns": len(public_index),
        "causal_witness": "counterfactual.private.json",
        "execution": "execution.private.json",
    }
    (out / "summary.private.json").write_bytes(_raw(summary))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
