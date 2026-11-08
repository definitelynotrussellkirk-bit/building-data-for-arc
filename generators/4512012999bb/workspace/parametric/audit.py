"""Run a bounded, source-bound sampler and protected-Racket shortcut audit.

Usage from the repository: python3 generators/4512012999bb/workspace/parametric/audit.py --out NEW_DIR
The report is private authoring evidence, including settings and query answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def load(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location("_frame_crop_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(value).hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    p, rivals = load("prototype"), load("rivals")
    source_paths = [HOME / name for name in ("prototype.py", "rivals.py", "adapter.py", "audit.py")]
    source_paths += [HOME.parents[1] / "generator.py", ROOT / "src/arcpuzzles/parametric_worker.py"]
    report = {
        "schema": "frame-crop-bounded-self-review-v1", "task_id": p.TASK,
        "status": "running", "sources": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in source_paths},
        "scope": "Finite ten-shortcut rejection on demonstrations; 64 bounded sampler requests; four executed episodes. No universal identification claim.",
        "query_answers_used_for_rival_selection": False,
        "sampler": [], "episodes": [], "rivals": {}, "evaluations": [], "sequential_cases": [],
    }
    bridge = None
    try:
        for seed in range(16):
            for alignment in p.ALIGNMENTS:
                for demos in (3, 6):
                    episode = p.generate(seed, {"alignment": alignment}, demos=demos, queries=4)
                    pairs = episode["train"] + episode["test"]
                    check(len(episode["train"]) == demos and len(episode["test"]) == 4, "sampler count mismatch")
                    check(len({json.dumps(x["input"]) for x in pairs}) == len(pairs), "duplicate sampler inputs")
                    report["sampler"].append({
                        "seed": seed, "alignment": alignment, "demos": demos, "queries": 4,
                        "success": True, "attempts": episode["sampling"]["attempts"],
                        "input_sizes": [[len(x["input"]), len(x["input"][0])] for x in pairs],
                        "output_sizes": [[len(x["output"]), len(x["output"][0])] for x in pairs],
                    })
        report["sampler_seconds"] = time.perf_counter() - started
        runtime = ROOT / "shared/runtime"
        with _local_imports(runtime, HOME):
            apply, identity, bridge = _real_evaluator(runtime)
            report["runtime"] = identity

            def execute(program, grid, purpose):
                begin = time.perf_counter()
                output = _grid(apply(program, grid))
                report["evaluations"].append({
                    "purpose": purpose, "program_sha256": digest(program.encode()),
                    "input_size": [len(grid), len(grid[0])],
                    "output_size": [len(output), len(output[0])],
                    "seconds": time.perf_counter() - begin,
                })
                return output

            for alignment in p.ALIGNMENTS:
                episode = p.generate(0, {"alignment": alignment}, demos=3, queries=4)
                program = episode["program_solution"]
                report["episodes"].append(episode)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(program, pair["input"], f"seed0/{alignment}/{split}/{index}")
                        check(actual == pair["output"], f"reference label mismatch {alignment}/{split}/{index}")
                report["rivals"][alignment] = {}
                for name, rival_program in rivals.programs(program).items():
                    mismatches = []
                    outputs = []
                    for index, pair in enumerate(episode["train"]):
                        actual = execute(rival_program, pair["input"], f"rival/{alignment}/{name}/demo{index}")
                        expected = rivals.predict(p.facts(pair["input"]), name, alignment)
                        check(actual == expected, f"Racket/Python rival mismatch {alignment}/{name}/{index}")
                        outputs.append(actual)
                        if actual != pair["output"]:
                            mismatches.append(index)
                    check(bool(mismatches), f"shortcut survived demonstrations: {alignment}/{name}")
                    report["rivals"][alignment][name] = {
                        "program": rival_program, "program_sha256": digest(rival_program.encode()),
                        "mismatch_demo_indices": mismatches, "demo_outputs": outputs,
                        "python_prediction_matches_racket": True,
                    }

            for queries in (1, 4):
                episode = p.generate(17, {"alignment": "match"}, demos=6, queries=queries)
                report["episodes"].append(episode)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(episode["program_solution"], pair["input"], f"endpoint/seed17/d6/q{queries}/{split}/{index}")
                        check(actual == pair["output"], f"endpoint mismatch q{queries}/{split}/{index}")

            # Same visible input for both settings. The counterfactual bypasses
            # score-driven orientation while preserving extraction and composition.
            witness = next(pair["input"] for pair in report["episodes"][0]["train"]
                           if p.facts(pair["input"])["direct_score"] != p.facts(pair["input"])["flip_score"])
            facts = p.facts(witness)
            for alignment in p.ALIGNMENTS:
                program = p.program({"alignment": alignment})
                flip = facts["flip_score"] > facts["direct_score"] if alignment == "match" else facts["flip_score"] < facts["direct_score"]
                wrong_name = "always_direct" if flip else "always_mirror"
                counterfactual = rivals.programs(program)[wrong_name]
                ordinary_output = execute(program, witness, f"sequential/{alignment}/ordinary")
                counterfactual_output = execute(counterfactual, witness, f"sequential/{alignment}/skip_a")
                check(ordinary_output == p.predict(witness, {"alignment": alignment}), "sequential ordinary mismatch")
                check(counterfactual_output == rivals.predict(facts, wrong_name, alignment), "sequential counterfactual mismatch")
                check(ordinary_output != counterfactual_output, "orientation ablation had no causal effect")
                report["sequential_cases"].append({
                    "settings": {"alignment": alignment}, "input": witness,
                    "program": program, "program_sha256": digest(program.encode()),
                    "intermediate_value": {key: facts[key] for key in ("candidate", "frame_bbox", "crop_bbox", "left_color", "right_color", "direct_score", "flip_score")},
                    "chosen_flip": flip, "ordinary_output": ordinary_output,
                    "ablation": "skip_a", "counterfactual_program": counterfactual,
                    "counterfactual_program_sha256": digest(counterfactual.encode()),
                    "counterfactual_output": counterfactual_output, "outputs_differ": True,
                })
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if bridge is not None:
            bridge.close()
        report["racket_evaluations"] = len(report["evaluations"])
        report["elapsed_seconds"] = time.perf_counter() - started
        report["actual_30x30_evaluations"] = [x for x in report["evaluations"] if x["input_size"] == [30, 30]]
        (args.out / "report.json").write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "sampler_requests": len(report["sampler"]),
                      "racket_evaluations": report["racket_evaluations"],
                      "elapsed_seconds": report["elapsed_seconds"], "report": str(args.out / "report.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
