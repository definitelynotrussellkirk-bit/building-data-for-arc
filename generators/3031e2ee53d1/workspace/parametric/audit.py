"""Bounded, source-bound protected-Racket audit of the local edge prototype.

Run from the review packet with:
  python review.py run /absolute/path/to/WORK/.venv/bin/python \
    generators/3031e2ee53d1/workspace/parametric/audit.py

This is a finite teaching audit, not qualification or universal identification.
It executes every chosen label and the decisive rival comparisons in Racket;
there is no Python semantic prefilter. Rivals preserve the observed prefix.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HOME = Path(__file__).resolve().parent
TASK = "3031e2ee53d1"


def load_exact(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def same_root_support():
    for ancestor in HOME.parents:
        path = ancestor / "shared/runtime/reviewer_support.py"
        if path.is_file():
            return load_exact("_3031_audit_support", path)
    raise FileNotFoundError("same-checkout reviewer_support.py is unavailable")


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def rival_program(prototype, name, mode):
    if name == "opposite_setting":
        return prototype.program({"edge": "bounce" if mode == "linear" else "linear"})
    # Reuse the exact input detector from the proposed Racket source. Everything
    # after detection below is independently specified rival behavior.
    source = prototype.program({"edge": "bounce"})
    head = source.split("                (base-cols", 1)[0]
    use_period = "1" if name == "fixed_period_1" else "period"
    envelope_period = "1" if name == "first_row_envelope" else "use-period"
    phase = "(modulo (- r h) use-period)" if name == "reset_phase_at_input_end" else "(remainder r use-period)"
    columns = "(filter (lambda (cc) (!= (at g source-row cc) 0)) (range 0 w))" if name == "phase_envelope" else "base-cols"
    # An explicit closed interval fold consumes overshoot. Other rivals below
    # replace this continuation policy while retaining the inferred phase.
    anchor = "(if (> local-span 0) (min wave (- (* 2 local-span) wave)) local-left)"
    if name == "clamp":
        anchor = "(max 0 (min local-span raw))"
    elif name == "clamp_then_reverse":
        anchor = "(list-ref clamped-anchors block)"
    elif name == "wrap":
        anchor = "(modulo raw (+ local-span 1))"
    elif name in {"fixed_period_1", "reset_phase_at_input_end"} and mode == "linear":
        anchor = "raw"
    elif name == "no_drift":
        anchor = "local-left"
    return head + f"""                (use-period {use_period})
                (base-cols (filter (lambda (cc)
                                     (for/or ((rr (range 0 {envelope_period})))
                                       (!= (at g rr cc) 0)))
                                   (range 0 w)))
                (left (if (null? base-cols) 0 (apply min base-cols)))
                (right (if (null? base-cols) 0 (apply max base-cols)))
                (span (- w (+ 1 (- right left))))
                (clamped-anchors
                  (for/list ((q (range 0 w)))
                    (first
                      (foldl (lambda (ignored state)
                               (let* ((pos (first state))
                                      (vel (second state))
                                      (next (+ pos vel)))
                                 (cond ((zero? span) (list left 0))
                                       ((>= next span) (list span (- (abs vel))))
                                       ((<= next 0) (list 0 (abs vel)))
                                       (else (list next vel)))))
                             (list left shift) (range 0 q))))))
           (build-grid w w (r c)
             (if (< r h)
                 (at g r c)
                 (let* ((source-row {phase})
                        (block (quotient r use-period))
                        (local-cols {columns})
                        (local-left (if (null? local-cols) 0 (apply min local-cols)))
                        (local-right (if (null? local-cols) 0 (apply max local-cols)))
                        (local-span (- w (+ 1 (- local-right local-left))))
                        (raw (+ local-left (* shift block)))
                        (wave (if (> local-span 0) (modulo raw (* 2 local-span)) 0))
                        (anchor {anchor})
                        (src-c (- c (- anchor local-left))))
                   (if (and (>= src-c 0) (< src-c w))
                       (at g source-row src-c)
                       0)))))))"""


def main():
    support = same_root_support()
    root = support.find_root(__file__)
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    prototype = load_exact("_3031_exact_audit_prototype", HOME / "prototype.py")
    resources = [HOME / name for name in
                 ("prototype.py", "adapter.py", "canonical.rkt", "bounce.rkt", "audit.py", "promotion.json")]
    resources += [root / "shared/runtime/reviewer_support.py",
                  root / "src/arcpuzzles/parametric_worker.py"]
    hashes = {str(p.relative_to(root)): digest(p.read_bytes()) for p in resources}
    report = {
        "schema": "3031e2ee53d1-finite-racket-audit-v1",
        "source_sha256": hashes,
        "scope": {"seeds": [0, 12, 17], "demos": 2, "queries": 4,
                  "settings": ["linear", "bounce"],
                  "method": "All chosen labels and decisive rival comparisons execute in one protected Racket bridge; no Python semantic prefilter.",
                  "limits": "Finite declared rivals and three seeds only. A surviving rival fails only when it changes a query. No qualification, acceptance, large census, or training admission."},
        "programs": {}, "cases": {}, "lessons": [], "failures": [],
        "racket_evaluations": 0,
    }
    names = ("first_row_envelope", "phase_envelope", "clamp", "clamp_then_reverse",
             "wrap", "no_drift", "fixed_period_1", "reset_phase_at_input_end",
             "opposite_setting")
    cache = {}
    runtime = root / "shared/runtime"
    with _local_imports(runtime, HOME):
        apply, identity, bridge = _real_evaluator(runtime)
        report["runtime"] = identity

        def execute(program, grid):
            program_hash = digest(program)
            report["programs"].setdefault(program_hash, program)
            case_id = digest(json.dumps(grid, separators=(",", ":")))
            case = report["cases"].setdefault(case_id, {"input": grid, "outputs": {}})
            key = (program_hash, case_id)
            if key not in cache:
                report["racket_evaluations"] += 1
                result = _grid(apply(program, grid))
                if result[:len(grid)] != grid:
                    raise AssertionError("Racket execution changed the observed prefix")
                cache[key] = result
                case["outputs"][program_hash] = result
            return cache[key], {"case": case_id, "program": program_hash}

        try:
            # Keep the actual discovered pre-repair ambiguity reproducible.
            # Its stored episodes/programs remain untouched; only replay fields
            # are added. The negative control must still expose the old hole.
            before_path = HOME / "evidence/current/phase-reset-before.json"
            if before_path.is_file():
                before = json.loads(before_path.read_text(encoding="utf-8"))
                before["native_replay"] = {"runtime": identity, "modes": {},
                                            "audit_sha256": digest(Path(__file__).read_bytes()),
                                            "scope": "Both original demos and original query index 1, under both settings."}
                start_count = report["racket_evaluations"]
                for old_mode, old_episode in before["episodes"].items():
                    old_rival = rival_program(prototype, "reset_phase_at_input_end", old_mode)
                    replay = {"rival_program": old_rival, "checks": []}
                    before["native_replay"]["modes"][old_mode] = replay
                    for split, index in (("train", 0), ("train", 1), ("test", 1)):
                        pair = old_episode[split][index]
                        truth, _ = execute(old_episode["program_solution"], pair["input"])
                        candidate, _ = execute(old_rival, pair["input"])
                        if truth != pair["output"] or (candidate == truth) != (split == "train"):
                            raise AssertionError("Stored pre-repair phase-reset counterexample did not reproduce")
                        replay["checks"].append({"split": split, "index": index, "input": pair["input"],
                                                 "chosen_output": truth, "rival_output": candidate})
                before["native_replay"]["racket_evaluations"] = report["racket_evaluations"] - start_count
                before["result"] = "confirmed_teaching_hole_under_both_settings"
                before_path.write_text(json.dumps(before, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                report["negative_control"] = {"path": str(before_path.relative_to(root)),
                                               "sha256": digest(before_path.read_bytes()),
                                               "status": before["result"]}
            for seed in report["scope"]["seeds"]:
                matched_inputs = None
                for mode in report["scope"]["settings"]:
                    episode = prototype.generate(seed, {"edge": mode}, demos=2, queries=4)
                    inputs = [p["input"] for split in ("train", "test") for p in episode[split]]
                    if matched_inputs is not None and inputs != matched_inputs:
                        raise AssertionError("Input sampling depends on the private edge setting")
                    matched_inputs = inputs
                    lesson = {"seed": seed, "setting": mode, "facts": {}, "rivals": [], "public_ids": []}
                    report["lessons"].append(lesson)
                    program = episode["program_solution"]
                    labels = {}
                    for split in ("train", "test"):
                        lesson["facts"][split] = []
                        for index, pair in enumerate(episode[split]):
                            actual, ref = execute(program, pair["input"])
                            if actual != pair["output"]:
                                raise AssertionError(f"Python/Racket label mismatch {seed}/{mode}/{split}/{index}")
                            labels[(split, index)] = (actual, ref)
                            facts = prototype.describe(pair["input"])
                            facts.update({"case": ref["case"], "output_shape": [len(actual), len(actual[0])],
                                          "output_foreground": sum(v != 0 for row in actual for v in row),
                                          "continuation_foreground": sum(v != 0 for row in actual[len(pair['input']):] for v in row)})
                            lesson["facts"][split].append(facts)
                    for index in range(4):
                        visible = prototype.public_challenge(episode, index)
                        if set(visible) != {"train", "test"} or len(visible["test"]) != 1 or set(visible["test"][0]) != {"input"}:
                            raise AssertionError("Public projection leaks extra fields or future queries")
                        content_id = support.public_challenge_id(visible)
                        if content_id != prototype.public_id(visible):
                            raise AssertionError("Public ID differs from the same-root shared helper")
                        lesson["public_ids"].append(content_id)
                    for name in names:
                        rival = rival_program(prototype, name, mode)
                        entry = {"name": name, "program": digest(rival), "checked_demos": 0, "checked_queries": 0}
                        lesson["rivals"].append(entry)
                        try:
                            for index, pair in enumerate(episode["train"]):
                                actual, ref = execute(rival, pair["input"])
                                entry["checked_demos"] += 1
                                expected, expected_ref = labels[("train", index)]
                                if actual[len(pair["input"]):] != expected[len(pair["input"]):]:
                                    entry.update({"status": "eliminated_by_demo", "witness": {"split": "train", "index": index,
                                                  "case": ref["case"], "expected_program": expected_ref["program"],
                                                  "rival_program": ref["program"]}})
                                    break
                            else:
                                entry["status"] = "query_equivalent"
                                for index, pair in enumerate(episode["test"]):
                                    actual, ref = execute(rival, pair["input"])
                                    entry["checked_queries"] += 1
                                    expected, expected_ref = labels[("test", index)]
                                    if actual[len(pair["input"]):] != expected[len(pair["input"]):]:
                                        entry.update({"status": "teaching_hole", "witness": {"split": "test", "index": index,
                                                      "case": ref["case"], "expected_program": expected_ref["program"],
                                                      "rival_program": ref["program"]}})
                                        report["failures"].append({"seed": seed, "setting": mode, "rival": name,
                                                                   "reason": "fits both demonstrations and changes a query", "witness": entry["witness"]})
                                        break
                        except Exception as exc:
                            entry.update({"status": "execution_error", "error": f"{type(exc).__name__}: {exc}"})
                            report["failures"].append({"seed": seed, "setting": mode, "rival": name, "reason": entry["error"]})
        finally:
            bridge.close()
    for path in resources:
        if digest(path.read_bytes()) != hashes[str(path.relative_to(root))]:
            report["failures"].append({"reason": "source changed during audit", "path": str(path.relative_to(root))})
    statuses = [entry["status"] for lesson in report["lessons"] for entry in lesson["rivals"]]
    report["counts"] = {status: statuses.count(status) for status in sorted(set(statuses))}
    report["status"] = "pass" if not report["failures"] else "fail"
    output = HOME / "evidence/current/audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "racket_evaluations": report["racket_evaluations"],
                      "counts": report["counts"], "failures": report["failures"], "report": str(output)}, indent=2))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
