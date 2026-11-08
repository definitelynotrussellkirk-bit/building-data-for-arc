"""Bounded protected-Racket review evidence; never grants native acceptance.

Run from the packet with ``review.py run python3 generators/55ba26e599d3/
workspace/parametric/review_evidence.py --out ../checks/parametric/dda-review``.
After native qualification, the separate ``witness --qualification FILE --out
NEW_DIRECTORY`` command creates a source-bound sequential-dependency witness.
Outputs contain private labels/programs except the opaque files in public/.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shlex
import sys
import time

sys.dont_write_bytecode = True
TASK_ID = "55ba26e599d3"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DESCRIPTIONS = {
    "step_a": "Trace the row-major-red-endpoint DDA path and bind its first input-blue hit.",
    "intermediate": "The first hit coordinate and its entire four-connected input-blue component.",
    "step_b": "After the canonical path recoloring, recolor that selected input-blue component green.",
    "why_b_depends_on_a": "The path's input-dependent first blue hit selects which component B expands; other blue components remain unchanged outside the path.",
}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def dependencies():
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from reviewer_support import public_challenge_bytes, public_challenge_id
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_dda_review_adapter_" + digest(str(path).encode() + body)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module, _real_evaluator, _grid, public_challenge_bytes, public_challenge_id


def rival_program(mode):
    """Independent DDA implementation, without editing adapter source text.

    All selections use INPUT objects, never recolored output components. Size
    ties choose the first component in row-major discovery order.
    """
    selections = {
        "canonical": "'()",
        "first_hit_component": "(if (empty? hits) '() (filter (lambda (o) (member (first hits) (obj-cells o))) blues))",
        "last_hit_component": "(if (empty? hits) '() (filter (lambda (o) (member (last hits) (obj-cells o))) blues))",
        "all_hit_components": "(filter (lambda (o) (ormap (lambda (p) (member p (obj-cells o))) hits)) blues)",
        "all_blue": "blues",
        "largest_component": "(if (empty? blues) '() (list (first (sort blues > #:key obj-size))))",
        "smallest_component": "(if (empty? blues) '() (list (first (sort blues < #:key obj-size))))",
        "row_major_first_component": "(if (empty? blues) '() (list (first blues)))",
        "first_hit_eight_component": "(if (empty? hits) '() (filter (lambda (o) (member (first hits) (obj-cells o))) blues))",
        "paint_path_red": "'()",
        "axis_only_canonical": "'()",
        "axis_only_first_component": "(if (empty? hits) '() (filter (lambda (o) (member (first hits) (obj-cells o))) blues))",
        "extended_canonical": "'()",
        "extended_first_component": "(if (empty? hits) '() (filter (lambda (o) (member (first hits) (obj-cells o))) blues))",
    }
    selected = selections[mode]
    objects = "objects-8" if mode == "first_hit_eight_component" else "objects"
    base = "(paint-cells g path 2)" if mode == "paint_path_red" else """(paint-cells g
          (map (lambda (p) (let ((v (at g (first p) (second p))))
            (list (first p) (second p) (cond ((= v 0) 2) ((= v 1) 3) (else v))))) path))"""
    final = "(paint-cells base (append-map obj-cells selected) 3)"
    if mode.startswith("axis_only_"):
        final = f"(if (or (zero? dr) (zero? dc)) {final} g)"
    indices = "(range (- steps) (+ (* 2 steps) 1))" if mode.startswith("extended_") else "(range 0 (+ steps 1))"
    return f"""(rule! (lambda (g)
      (let* ((twos (find-color g 2)) (p1 (first twos)) (p2 (second twos))
             (r1 (first p1)) (c1 (second p1))
             (dr (- (first p2) r1)) (dc (- (second p2) c1))
             (steps (max (abs dr) (abs dc)))
             (path (filter (lambda (p) (and (>= (first p) 0) (< (first p) (rows g))
                                           (>= (second p) 0) (< (second p) (cols g))))
               (map (lambda (i)
               (let ((t (if (zero? steps) 0.0 (/ (+ 0.0 i) (+ 0.0 steps)))))
                 (list (inexact->exact (round (+ r1 (* t dr))))
                       (inexact->exact (round (+ c1 (* t dc)))))))
               {indices})))
             (hits (filter (lambda (p) (= (at g (first p) (second p)) 1)) path))
             (blues (filter (lambda (o) (= (obj-color o) 1)) ({objects} g 0)))
             (base {base})
             (selected {selected}))
        {final})))"""


RIVALS = ("canonical", "first_hit_component", "last_hit_component", "all_hit_components",
          "all_blue", "largest_component", "smallest_component",
          "row_major_first_component", "first_hit_eight_component", "paint_path_red",
          "axis_only_canonical", "axis_only_first_component",
          "extended_canonical", "extended_first_component")


def grid_signature(grid):
    return {"shape": [len(grid), len(grid[0])],
            "sha256": digest(json.dumps(grid, separators=(",", ":")).encode()),
            "colors": {str(c): sum(row.count(c) for row in grid) for c in sorted({c for row in grid for c in row})}}


class Execution:
    def __init__(self, apply, validate):
        self.apply, self.validate = apply, validate
        self.successful = self.failed = 0
        self.cache = {}

    def __call__(self, program, grid):
        key = (program, json.dumps(grid, separators=(",", ":")))
        if key not in self.cache:
            try:
                value = self.validate(self.apply(program, copy.deepcopy(grid)))
                self.successful += 1
            except Exception:
                self.failed += 1
                raise
            self.cache[key] = value
        return copy.deepcopy(self.cache[key])


def checked_episode(adapter, execute, settings, demos, queries=4, seed=17):
    episode = adapter.generate(seed, copy.deepcopy(settings), demos=demos, queries=queries)
    program = adapter.program(settings)
    if episode.get("program_solution") != program:
        raise ValueError("program_solution does not equal exact setting program")
    inputs, signatures = [], []
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"Requested {count} {split} pairs were not returned")
        for pair in pairs:
            inp, output = execute.validate(pair["input"]), execute.validate(pair["output"])
            actual = execute(program, inp)
            if actual != output:
                raise ValueError(f"Protected Racket label mismatch for {settings}, {split}")
            inputs.append(json.dumps(inp, separators=(",", ":")))
            signatures.append({"split": split, "input": grid_signature(inp), "output": grid_signature(output)})
    if len(inputs) != len(set(inputs)):
        raise ValueError("Demonstration/query inputs are not all distinct")
    return episode, signatures


def self_audit(episode, execute):
    """Every visible demonstration selects survivors before any query is read."""
    report, survivors = [], []
    for name in RIVALS:
        program = rival_program(name)
        mismatches, errors = [], []
        # Do not short circuit after elimination: check all visible demos.
        for index, pair in enumerate(episode["train"]):
            try:
                if execute(program, pair["input"]) != pair["output"]:
                    mismatches.append(index)
            except Exception as exc:
                errors.append({"demo": index, "error": type(exc).__name__, "message": str(exc)[:300]})
        survived = not mismatches and not errors
        report.append({"rival": name, "program_sha256": digest(program.encode()),
                       "demo_mismatches": mismatches, "errors": errors, "survived": survived})
        if survived:
            survivors.append((name, program))
    findings = []
    for name, program in survivors:
        query_mismatches, errors = [], []
        for index, pair in enumerate(episode["test"]):
            try:
                actual = execute(program, pair["input"])
                if actual != pair["output"]:
                    query_mismatches.append(index)
                    # Retain one complete, smallest-area observed disagreement per rival below.
                    findings.append({"rival": name, "query_index": index,
                        "input": pair["input"], "output": pair["output"],
                        "rival_output": actual, "program": episode["program_solution"],
                        "rival_program": program})
            except Exception as exc:
                errors.append({"query": index, "error": type(exc).__name__, "message": str(exc)[:300]})
        row = next(r for r in report if r["rival"] == name)
        row.update(query_mismatches=query_mismatches, query_errors=errors)
    minimal = []
    for name, _ in survivors:
        cases = [case for case in findings if case["rival"] == name]
        if cases:
            minimal.append(min(cases, key=lambda c: (len(c["input"]) * len(c["input"][0]), c["query_index"])))
    return {"scope": f"{len(RIVALS)} finite independent Racket rivals, one seed-17 {len(episode['train'])}-demo/four-query episode per setting; no universal uniqueness claim. Errors never count as elimination evidence of identification or as disagreements.",
            "rivals": report, "survivors": [name for name, _ in survivors],
            "surviving_rival_query_disagreements": len(findings), "minimal_observed_findings": minimal,
            "execution_errors": sum(len(row["errors"]) + len(row.get("query_errors", [])) for row in report)}


def source_hashes():
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes())
            for path in sorted(HERE.glob("*")) if path.is_file() and path.suffix in (".py", ".json", ".md", ".rkt")}


def witness(adapter, execute, identity, qualification):
    qualified = json.loads(qualification.read_bytes())
    if (qualified.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or qualified.get("task_id") != TASK_ID or qualified.get("status") != "qualified"
            or not isinstance(qualified.get("source_binding"), dict)):
        raise ValueError("Expected this task's successful native qualification with source_binding")
    settings = {"reach": "first_blue_component"}
    program, counterfactual = adapter.program(settings), adapter.program({"reach": "line_only"})
    key = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    if qualified.get("programs", {}).get(key) != digest(program.encode()):
        raise ValueError("Actual setting program differs from the native qualified program")
    for binding in qualified["source_binding"].get("files", []):
        path = ROOT / binding["path"]
        if not path.resolve().is_relative_to(ROOT) or digest(path.read_bytes()) != binding["sha256"]:
            raise ValueError("Qualified source bytes changed before sequential witness execution")
    grid = [[int(c) for c in row] for row in ("20001", "01100", "00001", "00011", "00002")]
    output, other = execute(program, grid), execute(counterfactual, grid)
    if output == other or output[1][2] != 3 or other[1][2] != 1:
        raise ValueError("The required first-component witness does not change cell (1,2)")
    return {"schema": "arcpuzzles-sequential-dependency-witness-v1",
            "source_binding": copy.deepcopy(qualified["source_binding"]), **DESCRIPTIONS,
            "racket": {"backend": "racket", "protected": True}, "runtime_identity": identity,
            "qualification_sha256": digest(qualification.read_bytes()),
            "cases": [{"input": grid, "settings": settings,
                       "intermediate_value": {"first_blue_hit": [1, 1], "input_blue_component": [[1, 1], [1, 2]]},
                       "program": program, "output": output, "counterfactual_program": counterfactual,
                       "counterfactual_output": other, "ablation": "skip_a"}]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", choices=("run", "witness"), default="run")
    parser.add_argument("--out", type=Path, required=True, help="New output directory; existing destinations are refused")
    parser.add_argument("--qualification", type=Path, help="Native qualification.json; used only to bind a sequential witness")
    args = parser.parse_args(argv)
    if args.mode == "witness" and args.qualification is None:
        parser.error("witness requires --qualification")
    if args.out.exists():
        parser.error("--out must name a new directory")
    adapter, evaluator, validate, public_bytes, public_id = dependencies()
    contract = json.loads((HERE / "promotion.json").read_bytes())
    keys = sorted(contract["parameters"])
    settings = [dict(zip(keys, values)) for values in itertools.product(*(contract["parameters"][k] for k in keys))]
    started, hashes = time.monotonic(), source_hashes()
    apply, identity, bridge = evaluator(ROOT / "shared/runtime")
    execute = Execution(apply, validate)
    args.out.mkdir(parents=True)
    try:
        if args.mode == "witness":
            write_json(args.out / "sequential-dependency.json", witness(adapter, execute, identity, args.qualification))
            summary = {"schema": "dda-review-command-v1", "mode": "witness"}
        else:
            (args.out / "public").mkdir()
            episodes, audits, boundaries, stress = [], [], [], []
            for setting in settings:
                episode, signatures = checked_episode(adapter, execute, setting, 3)
                identifier = public_id(episode)
                public_path = args.out / "public" / (identifier + ".json")
                if public_path.exists():
                    raise ValueError("Duplicate visible challenge across settings")
                public_path.write_bytes(public_bytes(episode))
                episodes.append({"settings": setting, "seed": 17, "public_id": identifier,
                    "program": episode["program_solution"], "program_sha256": digest(episode["program_solution"].encode()),
                    "train": episode["train"], "test": episode["test"], "signatures": signatures})
                audits.append({"settings": setting, "demos": 3, "public_id": identifier, **self_audit(episode, execute)})
                for demos in (2, 6):
                    bounded, signs = checked_episode(adapter, execute, setting, demos)
                    boundaries.append({"settings": setting, "seed": 17, "demos": demos,
                        "queries": 4, "successful": True, "signatures": signs})
                    if demos == 2:
                        audits.append({"settings": setting, "demos": 2, **self_audit(bounded, execute)})
                literal = [[int(c) for c in row] for row in ("20001", "01100", "00001", "00011", "00002")]
                expected = adapter.solve_python(literal, setting["reach"])
                actual = execute(adapter.program(setting), literal)
                if actual != expected:
                    raise ValueError("Protected Racket 5x5 minimum-size stress label mismatch")
                stress.append({"settings": setting, "profile": "literal_minimum_5x5",
                    "input": literal, "output": actual, "input_signature": grid_signature(literal),
                    "output_signature": grid_signature(actual), "successful": True})
            if hashes != source_hashes():
                raise ValueError("Prototype sources changed during evidence execution; rerun after source freeze")
            shapes = [pair["input"]["shape"] for episode in episodes for pair in episode["signatures"]]
            if [30, 30] not in shapes:
                raise ValueError("Generated episode did not exercise genuine 30x30 boundary")
            write_json(args.out / "episodes.private.json", episodes)
            write_json(args.out / "self-audit.private.json", audits)
            write_json(args.out / "boundaries.json", boundaries)
            write_json(args.out / "stress.private.json", stress)
            if args.qualification:
                write_json(args.out / "sequential-dependency.json", witness(adapter, execute, identity, args.qualification))
            summary = {"schema": "dda-review-evidence-v1", "mode": "run", "settings": settings,
                "source_sha256": hashes, "episode_requests": len(episodes), "boundary_requests": len(boundaries),
                "stress_requests": len(stress), "failed_requests": 0, "min_5x5_executed": True, "max_30x30_executed": True,
                "rival_count": len(RIVALS),
                "surviving_rival_query_disagreements": sum(a["surviving_rival_query_disagreements"] for a in audits),
                "rival_execution_errors": sum(a["execution_errors"] for a in audits),
                "limits": "Finite source-bound authoring evidence only; no acceptance, training admission, universal uniqueness, or controller execution claim."}
        summary.update(command=shlex.join([sys.executable, *sys.argv]), racket=identity,
                       successful_racket_requests=execute.successful, failed_racket_requests=execute.failed,
                       elapsed_seconds=round(time.monotonic() - started, 3))
        write_json(args.out / "proof.json", summary)
        print(json.dumps(summary, sort_keys=True))
        return int(bool(summary.get("surviving_rival_query_disagreements") or summary.get("rival_execution_errors")))
    except Exception as exc:
        write_json(args.out / "failure.json", {"error": type(exc).__name__, "message": str(exc),
            "successful_racket_requests": execute.successful, "failed_racket_requests": execute.failed,
            "racket": identity, "elapsed_seconds": round(time.monotonic() - started, 3)})
        raise
    finally:
        bridge.close()


if __name__ == "__main__":
    raise SystemExit(main())
