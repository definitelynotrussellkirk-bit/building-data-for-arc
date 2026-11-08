"""Protected-Racket finite-rival audit for aligned-segment normalization."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _real_evaluator

_spec = importlib.util.spec_from_file_location("audit_e376_native_family", HOME / "native_family.py")
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)

RIVALS = (
    "middle", "longest", "shortest", "first", "last", "second",
    "median_length", "average_floor", "fixed_four", "fixed_six",
    "preserve_lengths", "color_middle", "row_major_middle",
)
RIVAL_MEANINGS = {
    "middle": "Use the positional middle segment along the aligned guide.",
    "longest": "Use the longest segment.",
    "shortest": "Use the shortest segment.",
    "first": "Use the first segment along the guide.",
    "last": "Use the last segment along the guide.",
    "second": "Use the second segment along the guide.",
    "median_length": "Use the statistical median of segment lengths.",
    "average_floor": "Use the floor of the arithmetic mean length.",
    "fixed_four": "Resize every segment to length four.",
    "fixed_six": "Resize every segment to length six.",
    "preserve_lengths": "Keep each segment's original length.",
    "color_middle": "Order by numeric color and use that middle object's length.",
    "row_major_middle": "Use the middle object in detector row-major order.",
}


def rival_programs():
    base = native.CANONICAL
    line = """(define target-length
     (if longest
         (apply max (map obj-size obs))
         (obj-size (list-ref ordered (quotient (length ordered) 2)))))"""
    if base.count(line) != 1:
        raise ValueError("canonical target-length block changed")
    def target(expr):
        return base.replace(line, f"(define target-length {expr})", 1)
    programs = {
        "middle": base,
        "longest": native.ALTERNATIVE,
        "shortest": target("(apply min (map obj-size obs))"),
        "first": target("(obj-size (first ordered))"),
        "last": target("(obj-size (list-ref ordered (- (length ordered) 1)))"),
        "second": target("(obj-size (list-ref ordered 1))"),
        "median_length": target("(list-ref (sort (map obj-size obs) <) (quotient (length obs) 2))"),
        "average_floor": target("(quotient (apply + (map obj-size obs)) (length obs))"),
        "fixed_four": target("4"),
        "fixed_six": target("6"),
        "color_middle": target("(obj-size (list-ref (sort obs (lambda (a b) (< (obj-color a) (obj-color b)))) (quotient (length obs) 2)))"),
        "row_major_middle": target("(obj-size (list-ref obs (quotient (length obs) 2)))"),
    }
    loop = "((i (range target-length)))"
    if base.count(loop) != 1:
        raise ValueError("canonical redraw loop changed")
    programs["preserve_lengths"] = base.replace(loop, "((i (range (obj-size obj))))", 1)
    return programs


def _binding(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run_audit(output=None, *, seeds=(0, 17, 43), demos=2):
    programs = rival_programs()
    apply, identity, bridge = _real_evaluator(RUNTIME)
    evaluations = 0
    refuted = 0
    disagreements = []
    survivors_report = []
    runtime_errors = []
    try:
        for setting in ({"target_mode": "middle"}, {"target_mode": "longest"}):
            intended = native.program(setting)
            for seed in seeds:
                lesson = native.generate(seed, setting, 6, 4)
                pairs = lesson["train"] + lesson["test"]
                for split_index, pair in enumerate(pairs):
                    actual = apply(intended, copy.deepcopy(pair["input"])); evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(f"intended protected label mismatch at {setting}/{seed}/{split_index}")
                survivors = []
                for name, rival in programs.items():
                    demo_ok = True
                    try:
                        for pair in lesson["train"][:demos]:
                            actual = apply(rival, copy.deepcopy(pair["input"])); evaluations += 1
                            if actual != pair["output"]:
                                demo_ok = False
                                break
                    except Exception as error:
                        runtime_errors.append({"settings": setting, "seed": seed, "rival": name,
                                               "error": f"{type(error).__name__}: {error}"})
                        continue
                    if not demo_ok:
                        refuted += 1
                        continue
                    survivors.append(name)
                    for query_index, pair in enumerate(lesson["test"]):
                        actual = apply(rival, copy.deepcopy(pair["input"])); evaluations += 1
                        if actual != pair["output"]:
                            disagreements.append({"settings": setting, "seed": seed,
                                "rival": name, "query_index": query_index,
                                "input": pair["input"], "intended_output": pair["output"],
                                "rival_output": actual})
                            break
                survivors_report.append({"settings": setting, "seed": seed,
                                         "fit_demonstrations": demos, "survivors": survivors})
    finally:
        bridge.close()
    status = "passed" if not disagreements and not runtime_errors else "failed"
    report = {
        "schema": "arcpuzzles-protected-finite-rival-audit-v1",
        "task_id": native.TASK_ID,
        "status": status,
        "protected": bool(identity.get("protected")),
        "racket": identity,
        "seeds": list(seeds),
        "fit_demonstrations": demos,
        "queries_per_episode": 4,
        "rivals": RIVAL_MEANINGS,
        "survivors": survivors_report,
        "evaluations": evaluations,
        "refuted_rivals": refuted,
        "query_disagreements": disagreements,
        "runtime_errors": runtime_errors,
        "source_binding": [_binding(HOME / "native_family.py"), _binding(TASK / "reference.rkt"),
                           _binding(Path(__file__))],
        "limits": "Finite named rivals and seeds; no universal identifiability claim.",
    }
    if output is not None:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--seed", type=int, action="append")
    args = parser.parse_args()
    result = run_audit(args.out, seeds=tuple(args.seed or (0, 17, 43)), demos=args.demos)
    print(json.dumps({k: result[k] for k in ("status", "evaluations", "refuted_rivals",
                                             "query_disagreements", "runtime_errors")}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
