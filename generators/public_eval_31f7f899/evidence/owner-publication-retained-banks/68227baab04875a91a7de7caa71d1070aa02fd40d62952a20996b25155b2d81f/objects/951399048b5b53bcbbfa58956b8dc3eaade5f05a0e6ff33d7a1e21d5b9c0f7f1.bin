"""Protected-Racket finite-rival audit for the bar-height ordering family."""
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

_spec = importlib.util.spec_from_file_location("audit_31_native_family", HOME / "native_family.py")
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)

RIVALS = (
    "ascending", "descending", "identity_heights", "reverse_input",
    "all_shortest", "all_longest", "fixed_three", "color_order",
    "width_order", "bottom_heavy_even", "color_order_descending",
)
RIVAL_MEANINGS = {
    "ascending": "Sort measured heights ascending across left-to-right slots.",
    "descending": "Sort measured heights descending across left-to-right slots.",
    "identity_heights": "Keep each slot's original height.",
    "reverse_input": "Assign the measured height sequence in reverse input order.",
    "all_shortest": "Resize every slot to the shortest measured height.",
    "all_longest": "Resize every slot to the longest measured height.",
    "fixed_three": "Resize every slot to height three.",
    "color_order": "Order measured heights by ascending numeric slot color.",
    "width_order": "Order measured heights by ascending slot width.",
    "bottom_heavy_even": "Use the intended ascending order but put the extra cell of even heights below the carrier.",
    "color_order_descending": "Order measured heights by descending numeric slot color.",
}


def rival_programs():
    base = native.CANONICAL
    line = "(define assigned (sort measured (if descending > <)))"
    if base.count(line) != 1:
        raise ValueError("canonical assigned-height line changed")
    def assigned(expr):
        return base.replace(line, f"(define assigned {expr})", 1)
    programs = {
        "ascending": base,
        "descending": native.ALTERNATIVE,
        "identity_heights": assigned("measured"),
        "reverse_input": assigned("(reverse measured)"),
        "all_shortest": assigned("(make-list (length measured) (apply min measured))"),
        "all_longest": assigned("(make-list (length measured) (apply max measured))"),
        "fixed_three": assigned("(make-list (length measured) 3)"),
        "color_order": assigned("(map second (sort (map list slots measured) (lambda (a b) (< (third (first a)) (third (first b))))))"),
        "width_order": assigned("(map second (sort (map list slots measured) (lambda (a b) (< (- (second (first a)) (first (first a))) (- (second (first b)) (first (first b)))))))"),
        "color_order_descending": assigned("(map second (sort (map list slots measured) (lambda (a b) (> (third (first a)) (third (first b))))))"),
    }
    top = "(top (- axis-row (quotient height 2)))"
    if base.count(top) != 1:
        raise ValueError("canonical height anchoring line changed")
    programs["bottom_heavy_even"] = base.replace(
        top, "(top (- axis-row (quotient (- height 1) 2)))", 1)
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
        for setting in ({"height_order": "ascending"}, {"height_order": "descending"}):
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
                    except Exception as error:  # rivals are required to be total on this bank
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
