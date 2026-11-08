"""Bounded adversarial self-audit for the task-local rank-selector family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

TASK_ID = "04e2ffe8dc8e"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_audit_04e2_rank", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _global_smallest_output(proto, grid):
    components = []
    for color in range(1, 10):
        for cells in proto._components(grid, color):
            components.append((len(cells), min(cells), cells))
    _, _, cells = min(components)
    output = [list(row) for row in grid]
    for row, col in cells:
        output[row][col] = 6
    return output


def run(output: Path) -> int:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    started = time.monotonic()
    proto = _load_prototype()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"selection_mode": mode}, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for demos in (2, 3, 6)
        for mode in proto.MODES
    ]

    from arcpuzzles.parametric_worker import evaluate_contract

    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    matched_inputs = 0
    first_turn_checks = 0
    fixed_rank_refutations = 0
    global_smallest_refutations = 0
    stress = []
    for seed in (0, 17, 31):
        for demos in (2, 3, 6):
            episodes = {
                mode: proto.generate(seed, {"selection_mode": mode}, demos, 4)
                for mode in proto.MODES
            }
            for split in ("train", "test"):
                left = [pair["input"] for pair in episodes[proto.MODES[0]][split]]
                right = [pair["input"] for pair in episodes[proto.MODES[1]][split]]
                if left != right:
                    raise ValueError("hidden setting changed input sampling")
            matched_inputs += 1
            one = proto.generate(seed, {"selection_mode": "key_rank_green"}, demos, 1)
            if one["test"] != episodes["key_rank_green"]["test"][:1]:
                raise ValueError("one-query prefix differs from four-query generation")
            first_turn_checks += 1

            ranked = episodes["key_rank_green"]["train"]
            ranks = [proto.intermediate_value(pair["input"]) for pair in ranked]
            if len(set(ranks[:2])) != 2:
                raise ValueError("two demonstrations leave a fixed-rank shortcut viable")
            for fixed_rank in range(1, 5):
                if all(proto.selected_green_rank(pair["input"], pair["output"]) == fixed_rank for pair in ranked):
                    raise ValueError(f"fixed-rank shortcut {fixed_rank} fits every ranked lesson")
                fixed_rank_refutations += 1

            canonical = episodes["smallest_green"]["train"]
            if not all(_global_smallest_output(proto, pair["input"]) != pair["output"] for pair in canonical):
                raise ValueError("global-smallest-any-color shortcut survived a canonical lesson")
            global_smallest_refutations += len(canonical)

        grid = proto.generate(seed, {"selection_mode": "key_rank_green"}, 3, 4)["test"][-1]["input"]
        quadrants = []
        for row0 in (0, 15):
            for col0 in (0, 15):
                quadrants.append(sum(grid[row][col] != 0 for row in range(row0, row0 + 15)
                                     for col in range(col0, col0 + 15)))
        stress.append({"seed": seed, "shape": [30, 30],
                       "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
                       "quadrant_nonzero": quadrants,
                       "rank": proto.intermediate_value(grid)})

    with proto.RacketEngine() as engine:
        causal_episode = proto.generate(7, {"selection_mode": "key_rank_green"}, 3, 4)
        pair = causal_episode["test"][0]
        actual = engine.apply(proto.program({"selection_mode": "key_rank_green"}), pair["input"])
        counterfactual = engine.apply(proto.counterfactual_program(1), pair["input"])
        if actual != pair["output"] or actual == counterfactual:
            raise ValueError("protected wrong-intermediate witness did not change the final output")
        causal = {"input_rank": proto.intermediate_value(pair["input"]),
                  "actual_rank": proto.selected_green_rank(pair["input"], actual),
                  "counterfactual_rank": proto.selected_green_rank(pair["input"], counterfactual),
                  "changed": True}

    sources = {
        path.relative_to(ROOT).as_posix(): _sha(path)
        for path in [HERE / name for name in
                     ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt", "key_rank.rkt", "probe.py")]
    }
    report = {
        "schema": "arcpuzzles-rank-selector-bounded-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": "Finite author self-audit; not owner qualification, acceptance, or training admission.",
        "native_jobs": len(native["checks"]),
        "native_racket_evaluations": native["racket_evaluations"],
        "native_checks": native["checks"],
        "racket": native["racket"],
        "matched_input_checks": matched_inputs,
        "first_turn_prefix_checks": first_turn_checks,
        "fixed_rank_refutations": fixed_rank_refutations,
        "global_smallest_refutations": global_smallest_refutations,
        "stress_30x30": stress,
        "causal_wrong_intermediate": causal,
        "source_sha256": sources,
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "limitations": [
            "The finite settings pool and explicit shortcuts are not a proof against all conceivable rules.",
            "Seeds 0, 17 and 31 plus demo counts 2, 3 and 6 are bounded observations.",
            "Owner source review, native qualification/acceptance and training admission remain separate.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "native_jobs": report["native_jobs"],
                      "racket_evaluations": report["native_racket_evaluations"],
                      "elapsed_seconds": report["elapsed_seconds"]}))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().out))
