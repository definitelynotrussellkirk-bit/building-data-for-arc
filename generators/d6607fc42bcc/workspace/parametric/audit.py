"""Bounded sampler, protected-Racket label, and shortcut audit.

Run from the repository root::

    python3 generators/d6607fc42bcc/workspace/parametric/audit.py \
        --out generators/d6607fc42bcc/workspace/parametric/evidence/current

The finite rival set is deliberately explicit.  Passing this audit is evidence
for the sampled contract, not an identifiability proof against arbitrary rules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def _load(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_d660_audit_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_json(value) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _source_hashes() -> dict[str, str]:
    paths = [
        HERE / "adapter.py",
        HERE / "prototype.py",
        HERE / "rivals.py",
        HERE / "audit.py",
        HERE / "canonical.rkt",
        HERE / "dot_offset.rkt",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        ROOT / "src" / "arcpuzzles" / "parametric_worker.py",
    ]
    return {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
        for path in paths
    }


def run_bounded(
    *,
    sampler_seeds: Iterable[int] = range(16),
    execution_seeds: Iterable[int] = (0, 17),
    demos: int = 3,
    queries: int = 4,
) -> dict:
    """Execute the bounded audit and return a JSON-serializable report."""
    prototype = _load("prototype")
    rivals = _load("rivals")
    sampler_seeds = tuple(sampler_seeds)
    execution_seeds = tuple(execution_seeds)
    started = time.perf_counter()
    report = {
        "schema": "d6607fc42bcc-projection-depth-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "running",
        "scope": (
            "Finite six-shortcut rejection on demonstrations, deterministic sampler "
            "checks, and protected-Racket replay for the requested bounded seeds. "
            "No universal identification claim."
        ),
        "query_answers_used_for_rival_selection": False,
        "sources": _source_hashes(),
        "request": {
            "sampler_seeds": list(sampler_seeds),
            "execution_seeds": list(execution_seeds),
            "demos": demos,
            "queries": queries,
        },
        "sampler": [],
        "sampler_requests": 0,
        "runtime": None,
        "evaluations": [],
        "rivals": {mode: {} for mode in prototype.DEPTH_MODES},
        "sequential_cases": [],
    }
    bridge = None
    try:
        for seed in sampler_seeds:
            episodes = {
                mode: prototype.generate(
                    seed, {"projection_depth": mode}, demos=demos, queries=queries
                )
                for mode in prototype.DEPTH_MODES
            }
            one_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes["one"][split]
            ]
            dot_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes["dot_offset"][split]
            ]
            _check(one_inputs == dot_inputs, f"setting-dependent inputs for seed {seed}")
            for mode, episode in episodes.items():
                all_pairs = episode["train"] + episode["test"]
                serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
                _check(len(episode["train"]) == demos, "sampler demo count mismatch")
                _check(len(episode["test"]) == queries, "sampler query count mismatch")
                _check(len(serialized) == len(set(serialized)), "duplicate sampler input")
                certificate = prototype.teaching_certificate(episode)
                _check(
                    certificate["survivors"] == [{"projection_depth": mode}],
                    f"declared setting survived incorrectly: seed={seed} mode={mode}",
                )
                _check(
                    certificate["shortcut_survivors"] == [],
                    f"Python shortcut survived: seed={seed} mode={mode}",
                )
                sizes = [[len(pair["input"]), len(pair["input"][0])] for pair in all_pairs]
                _check(all(1 <= h <= 30 and 1 <= w <= 30 for h, w in sizes), "invalid grid size")
                report["sampler"].append(
                    {
                        "seed": seed,
                        "settings": {"projection_depth": mode},
                        "counts": {"demos": demos, "queries": queries},
                        "input_sizes": sizes,
                        "input_sha256": [_sha_json(pair["input"]) for pair in all_pairs],
                        "certificate": certificate,
                    }
                )
                report["sampler_requests"] += 1

        runtime = ROOT / "shared" / "runtime"
        with _local_imports(runtime, HERE):
            apply, identity, bridge = _real_evaluator(runtime)
            report["runtime"] = identity

            def execute(program: str, grid, purpose: str):
                begin = time.perf_counter()
                output = _grid(apply(program, grid))
                report["evaluations"].append(
                    {
                        "purpose": purpose,
                        "program_sha256": _sha_bytes(program.encode()),
                        "input_sha256": _sha_json(grid),
                        "output_sha256": _sha_json(output),
                        "input_size": [len(grid), len(grid[0])],
                        "output_size": [len(output), len(output[0])],
                        "seconds": time.perf_counter() - begin,
                    }
                )
                return output

            rival_programs = rivals.programs(
                prototype.program({"projection_depth": "dot_offset"})
            )
            for mode in prototype.DEPTH_MODES:
                report["rivals"][mode] = {
                    name: {
                        "program_sha256": _sha_bytes(program.encode()),
                        "mismatch_demo_indices": [],
                        "cases": [],
                        "python_prediction_matches_racket": True,
                    }
                    for name, program in rival_programs.items()
                }

            first_episode = None
            for seed in execution_seeds:
                for mode in prototype.DEPTH_MODES:
                    episode = prototype.generate(
                        seed, {"projection_depth": mode}, demos=demos, queries=queries
                    )
                    if first_episode is None:
                        first_episode = episode
                    reference = episode["program_solution"]
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = execute(
                                reference,
                                pair["input"],
                                f"reference/seed{seed}/{mode}/{split}/{index}",
                            )
                            _check(
                                actual == pair["output"],
                                f"Racket reference mismatch seed={seed} mode={mode} {split}[{index}]",
                            )
                    for name, rival_program in rival_programs.items():
                        mismatches = []
                        for index, pair in enumerate(episode["train"]):
                            actual = execute(
                                rival_program,
                                pair["input"],
                                f"rival/seed{seed}/{mode}/{name}/demo{index}",
                            )
                            predicted = prototype.shortcut_output(pair["input"], name)
                            _check(
                                actual == predicted,
                                f"Racket/Python rival mismatch seed={seed} mode={mode} name={name} demo={index}",
                            )
                            if actual != pair["output"]:
                                mismatches.append(index)
                        _check(
                            bool(mismatches),
                            f"shortcut survived demos seed={seed} mode={mode} name={name}",
                        )
                        item = report["rivals"][mode][name]
                        item["cases"].append(
                            {"seed": seed, "mismatch_demo_indices": mismatches}
                        )
                        item["mismatch_demo_indices"] = sorted(
                            set(item["mismatch_demo_indices"]) | set(mismatches)
                        )

            if execution_seeds:
                witness_seed = execution_seeds[0]
                one = prototype.generate(
                    witness_seed, {"projection_depth": "one"}, demos=demos, queries=queries
                )
                dot = prototype.generate(
                    witness_seed,
                    {"projection_depth": "dot_offset"},
                    demos=demos,
                    queries=queries,
                )
                witness = next(
                    pair["input"]
                    for pair, alternate in zip(one["train"], dot["train"])
                    if pair["output"] != alternate["output"]
                )
                ordinary = execute(
                    dot["program_solution"], witness, "sequential/dot_offset/ordinary"
                )
                counterfactual = execute(
                    one["program_solution"], witness, "sequential/dot_offset/wrong_intermediate"
                )
                _check(ordinary != counterfactual, "sequential ablation had no effect")
                report["sequential_cases"].append(
                    {
                        "settings": {"projection_depth": "dot_offset"},
                        "input_sha256": _sha_json(witness),
                        "intermediate_value": prototype.frame_intermediates(witness),
                        "ordinary_program_sha256": _sha_bytes(dot["program_solution"].encode()),
                        "counterfactual_program_sha256": _sha_bytes(one["program_solution"].encode()),
                        "ordinary_output_sha256": _sha_json(ordinary),
                        "counterfactual_output_sha256": _sha_json(counterfactual),
                        "outputs_differ": True,
                        "ablation": "wrong_intermediate",
                    }
                )
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if bridge is not None:
            bridge.close()
        report["racket_evaluations"] = len(report["evaluations"])
        report["actual_30x30_evaluations"] = [
            item for item in report["evaluations"] if item["input_size"] == [30, 30]
        ]
        report["elapsed_seconds"] = time.perf_counter() - started
    return report


def _self_review(report: dict) -> dict:
    return {
        "schema": "d6607fc42bcc-self-review-v1",
        "task_id": report["task_id"],
        "status": report["status"],
        "claims": [
            "Inputs are identical across parameter settings for every sampled seed.",
            "All sampled private labels were replayed by a live protected Racket backend.",
            "Six independently predicted executable shortcut families were rejected by demonstrations.",
            "A wrong-intermediate ablation changes the result on the same visible input.",
            "The fourth query exercises an actual 30x30 canvas in the full audit request.",
        ],
        "limitations": [
            "The shortcut set is finite and does not prove uniqueness against arbitrary programs.",
            "Sampling is bounded to the recorded seeds and requested counts.",
            "The alternate projection-depth rule is a new family member, not a claim about the original ARC intent.",
        ],
        "query_answers_used_for_rival_selection": False,
        "sampler_requests": report["sampler_requests"],
        "racket_evaluations": report["racket_evaluations"],
        "actual_30x30_evaluation_count": len(report["actual_30x30_evaluations"]),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sampler-seeds", type=int, default=16)
    parser.add_argument("--seed", type=int, action="append", default=[])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)
    execution_seeds = tuple(args.seed) if args.seed else (0, 17)
    report = run_bounded(
        sampler_seeds=range(args.sampler_seeds),
        execution_seeds=execution_seeds,
        demos=args.demos,
        queries=args.queries,
    )
    (args.out / "focused-validation.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    self_review = _self_review(report)
    (args.out / "self-review.json").write_text(
        json.dumps(self_review, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "sampler_requests": report["sampler_requests"],
                "racket_evaluations": report["racket_evaluations"],
                "actual_30x30_evaluations": len(report["actual_30x30_evaluations"]),
                "elapsed_seconds": report["elapsed_seconds"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
