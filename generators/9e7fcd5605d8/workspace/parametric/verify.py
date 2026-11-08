"""Bounded protected-Racket evidence for the task-local threshold prototype.

This is an authoring verifier, not a turn controller or training-admission tool.
Only hash-named first-turn projections go into public/. All programs, settings,
seeds, complete examples, future queries, and reference answers remain private.
Run through the packet's review.py run launcher to select its bundled runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "9e7fcd5605d8"
RUNTIME = REPO / "shared/runtime"
sys.dont_write_bytecode = True


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(body):
    return hashlib.sha256(body).hexdigest()


def _load_path(path, tag):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(REPO):
        raise ValueError(f"Expected a regular source file in this checkout: {path}")
    body = path.read_bytes()
    name = "_hole_verify_" + tag + "_" + _sha(str(path).encode() + body)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def strict_grid(value):
    """Accept only exact ARC JSON grids, returning an independent value."""
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("A grid needs 1..30 list rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("Grid cells must be exact integers 0..9 in a rectangle")
    return [row[:] for row in value]


class Executor:
    """Cache actual protected-reference results, never a Python mirror."""
    def __init__(self, apply, identity):
        if (type(identity) is not dict or identity.get("backend") != "racket"
                or identity.get("protected") is not True):
            raise ValueError("Verification requires a protected Racket backend")
        self.apply = apply
        self.cache = {}
        self.requests = self.executions = self.cache_hits = self.failures = 0

    def __call__(self, program, grid):
        if type(program) is not str or not program.strip():
            raise ValueError("Reference programs must be nonempty exact text")
        grid = strict_grid(grid)
        key = (program, _bytes(grid))
        self.requests += 1
        if key in self.cache:
            self.cache_hits += 1
            return strict_grid(self.cache[key])
        self.executions += 1
        try:
            result = strict_grid(self.apply(program, grid))
        except Exception:
            self.failures += 1
            raise
        self.cache[key] = result
        return strict_grid(result)

    def stats(self):
        return {"requests": self.requests, "executions": self.executions,
                "cache_hits": self.cache_hits, "failed_executions": self.failures}


def normalize_episode(value, demos, queries, expected_program):
    if (type(value) is not dict or type(value.get("program_solution")) is not str
            or value["program_solution"] != expected_program):
        raise ValueError("Generated program_solution must exactly match program(settings)")
    episode = {"program_solution": expected_program}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        pairs = value.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"Generated {split} count differs from the request")
        episode[split] = []
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("Every pair needs explicit input and output grids")
            normalized = {key: strict_grid(pair[key]) for key in ("input", "output")}
            if (len(normalized["input"]) != len(normalized["output"])
                    or len(normalized["input"][0]) != len(normalized["output"][0])):
                raise ValueError("This recoloring task must preserve grid dimensions")
            identity = _bytes(normalized["input"])
            if identity in seen:
                raise ValueError("Demonstration and query inputs must all be distinct")
            seen.add(identity)
            episode[split].append(normalized)
    return episode


def label_episode(value, demos, queries, program, execute):
    """Compare every claimed label and retain the actual Racket output."""
    episode = normalize_episode(value, demos, queries, program)
    comparisons = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            actual = strict_grid(execute(program, pair["input"]))
            comparisons.append({"split": split, "index": index,
                                "input_sha256": _sha(_bytes(pair["input"])),
                                "claimed_output_sha256": _sha(_bytes(pair["output"])),
                                "actual_output_sha256": _sha(_bytes(actual)),
                                "matches": pair["output"] == actual})
            pair["output"] = actual
    return episode, comparisons


def audit_rivals(episode, programs, execute):
    """Execute every visible demo; errors never count as a refutation."""
    rows = []
    for name, program in programs.items():
        row = {"name": name, "program_sha256": _sha(program.encode()),
               "refuted": False, "survived_demos": False,
               "demo_disagreements": [], "query_disagreements": [], "errors": []}
        for index, pair in enumerate(episode["train"]):
            try:
                if strict_grid(execute(program, pair["input"])) != pair["output"]:
                    row["demo_disagreements"].append(index)
            except Exception as error:
                row["errors"].append({"split": "train", "index": index,
                                      "error": f"{type(error).__name__}: {error}"})
        if row["errors"]:
            row["status"] = "execution_failed"
        elif row["demo_disagreements"]:
            row.update(status="refuted", refuted=True)
        else:
            row["survived_demos"] = True
            for index, pair in enumerate(episode["test"]):
                try:
                    if strict_grid(execute(program, pair["input"])) != pair["output"]:
                        row["query_disagreements"].append(index)
                except Exception as error:
                    row["errors"].append({"split": "test", "index": index,
                                          "error": f"{type(error).__name__}: {error}"})
            row["status"] = ("execution_failed" if row["errors"] else
                             "wrong_query_survivor" if row["query_disagreements"] else
                             "survives_and_agrees")
        rows.append(row)
    return rows


def _aggregate_rule(threshold, per_color):
    peers = "(filter (lambda (peer) (= (obj-color peer) (obj-color obj))) objs)" if per_color else "objs"
    return f"""(rule!
  (let ()
    (define (holes obj)
      (let* ((cells (obj-cells obj)) (bb (bbox-of-cells cells))
             (r0 (first bb)) (c0 (second bb))
             (h (+ 1 (- (third bb) r0))) (w (+ 1 (- (fourth bb) c0)))
             (norm (map (lambda (p) (list (- (first p) r0) (- (second p) c0))) cells))
             (mask (paint-cells (empty-grid h w 0) norm 1)))
        (length (filter
          (lambda (region)
            (not (any? (lambda (p)
                         (or (= (first p) 0) (= (first p) (- h 1))
                             (= (second p) 0) (= (second p) (- w 1)))) region)))
          (find-0-regions mask 0)))))
    (let ((objs (objects g 0)))
      (for/fold ((out g)) ((obj (in-list objs)))
        (paint-cells out (obj-cells obj)
          (if (>= (apply + (map holes {peers})) {threshold}) 8 4))))))"""


def public_projection(episode):
    """Use the shared canonical byte/id contract on ONE visible query only."""
    support = _load_path(RUNTIME / "reviewer_support.py", "public_support")
    projection = copy.deepcopy(episode)
    if type(projection.get("test")) is not list or not projection["test"]:
        raise ValueError("A first-turn projection needs a query")
    projection["test"] = projection["test"][:1]
    payload = support.public_challenge_bytes(projection)
    identity = support.public_challenge_id(projection)
    public = json.loads(payload)
    if (identity != _sha(payload) or set(public) != {"train", "test"}
            or len(public["test"]) != 1 or set(public["test"][0]) != {"input"}):
        raise ValueError("Public challenge violated the one-query byte contract")
    return payload, identity


def _canonical_program():
    programs = set()
    with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row.get("program_solution"))
    if len(programs) != 1 or type(next(iter(programs), None)) is not str:
        raise ValueError("The selected task must have one exact canonical program")
    return programs.pop()


def _source_hashes():
    paths = [HERE / name for name in ("prototype.py", "adapter.py", "rules.py", "verify.py", "canonical.rkt")]
    paths += [HERE.parents[1] / "generator.py",
              HERE.parents[1] / "tests/test_parametric_verifier.py",
              REPO / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "reviewer_support.py",
              RUNTIME / "puzzle_generators/rule_wrap.py",
              RUNTIME / "arc_repl/racket_bridge.py"]
    return {path.relative_to(REPO).as_posix(): _sha(path.read_bytes()) for path in paths}


def _jobs(seeds):
    if type(seeds) is not list or not 1 <= len(seeds) <= 2 or len(set(seeds)) != len(seeds):
        raise ValueError("Use one or two distinct seeds; the verifier is bounded to eight episodes")
    if any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds):
        raise ValueError("Seeds must be exact integers in 0..2**63-1")
    layouts = [(seed, 2) for seed in seeds] + [(91, 6), (17, 3)]
    return [{"seed": seed, "settings": {"min_holes": threshold}, "demos": demos, "queries": 4}
            for seed, demos in layouts for threshold in (1, 2)]


def _input_summary(episode, prototype):
    result = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            grid = pair["input"]
            if not 11 <= len(grid) <= 30 or not 11 <= len(grid[0]) <= 30:
                raise ValueError("Sampler inputs must have 11..30 rows and columns")
            colors = sorted({cell for row in grid for cell in row} - {0})
            if not colors or set(colors) & {4, 8}:
                raise ValueError("Input colors must exclude both output labels")
            objects = prototype.analyze(grid)
            if not 4 <= len(objects) <= 16:
                raise ValueError("Sampler inputs must have 4..16 components")
            holes = Counter(obj["holes"] for obj in objects)
            if not {0, 1, 2, 3} <= set(holes):
                raise ValueError("Every retained input must cover hole counts 0,1,2,3")
            result.append({"split": split, "index": index,
                           "shape": [len(grid), len(grid[0])], "objects": len(objects),
                           "colors": colors, "hole_count_histogram": dict(sorted(holes.items()))})
    return result


def _write_json(path, value):
    path.write_bytes(_bytes(value))


def run(out, seeds=None):
    """Write fresh private evidence and two hash-named first-turn examples."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"Evidence destination already exists: {out}")
    jobs = _jobs([0, 17] if seeds is None else seeds)
    out.mkdir(parents=True, exist_ok=False)
    (out / "private").mkdir()
    (out / "public").mkdir()
    report = {"schema": "topology-parametric-self-review-v1", "visibility": "private",
              "task_id": TASK_ID, "status": "running", "training_admission": False,
              "turn_controller": False, "jobs_requested": jobs, "episodes": [],
              "programs": {}, "examples": [], "paired_settings_checks": [], "errors": [],
              "coverage_limits": [
                  "Finite declared rivals and bounded seeds do not prove universal induction.",
                  "Sampling uses separated monochromatic components; touching/nested multicolor scenes are outside this sampler.",
                  "Foreground 4/8-connectivity and color-blind connectivity can agree on this separated domain.",
                  "At min_holes=1, positive enclosed area is equivalent to positive enclosed-region count.",
                  "Prototype topology summaries are corroborative; every retained label is executed by protected Racket.",
                  "This verifier publishes only first-turn challenges and grants no training admission."]}
    bridge = execute = None
    episodes = {}
    exemplars = set()
    try:
        report["source_sha256"] = _source_hashes()
        prototype = _load_path(HERE / "prototype.py", "prototype")
        rules = _load_path(HERE / "rules.py", "rules")
        canonical = _canonical_program()
        if prototype.program({"min_holes": 1}) != canonical:
            raise ValueError("Default program differs from selected canonical text")
        report["canonical_program_sha256"] = _sha(canonical.encode())
        from arcpuzzles.parametric_worker import _real_evaluator
        apply, identity, bridge = _real_evaluator(RUNTIME)
        execute = Executor(apply, identity)
        report["racket"] = identity
        for job in jobs:
            row = {**copy.deepcopy(job), "status": "running", "errors": []}
            report["episodes"].append(row)
            try:
                program = prototype.program(job["settings"])
                report["programs"][_sha(program.encode())] = program
                row["program_sha256"] = _sha(program.encode())
                generated = prototype.generate(**job)
                episode, comparisons = label_episode(generated, job["demos"], 4, program, execute)
                row["label_checks"] = comparisons
                row["materialized"] = True
                if any(not comparison["matches"] for comparison in comparisons):
                    row["errors"].append("A generator output claim differs from actual Racket execution")
                row["input_summary"] = _input_summary(episode, prototype)
                rivals = rules.rival_programs(job["settings"])
                threshold = job["settings"]["min_holes"]
                rivals.update({"per_color_hole_sum": _aggregate_rule(threshold, True),
                               "whole_grid_hole_sum": _aggregate_rule(threshold, False)})
                if any(type(name) is not str or not name or type(text) is not str or not text.strip()
                       for name, text in rivals.items()):
                    raise ValueError("Rivals require nonempty names and exact Racket text")
                for text in rivals.values():
                    report["programs"][_sha(text.encode())] = text
                row["rivals"] = audit_rivals(episode, rivals, execute)
                row["survivors"] = [r["name"] for r in row["rivals"] if r["survived_demos"]]
                row["expected_equivalent_survivors"] = ["hole_cell_threshold"] if threshold == 1 else []
                for rival in row["rivals"]:
                    if rival["status"] in {"execution_failed", "wrong_query_survivor"}:
                        row["errors"].append(f"Rival {rival['name']}: {rival['status']}")
                prefix_raw = prototype.generate(job["seed"], job["settings"], job["demos"], 1)
                prefix, prefix_checks = label_episode(prefix_raw, job["demos"], 1, program, execute)
                row["one_query_label_checks"] = prefix_checks
                if any(not comparison["matches"] for comparison in prefix_checks):
                    row["errors"].append("A one-query prefix output claim differs from Racket")
                payload, public_id = public_projection(episode)
                if public_projection(prefix) != (payload, public_id):
                    raise ValueError("One-query generation changes first-turn public bytes")
                mutated = copy.deepcopy(episode)
                mutated.update(settings={"min_holes": 999}, seed=-999, program_solution="private mutation")
                for pair in mutated["test"]:
                    pair["output"] = [[9]]
                for pair in mutated["test"][1:]:
                    pair["input"] = [[9]]
                if public_projection(mutated) != (payload, public_id):
                    raise ValueError("Private metadata, answers, or future inputs change public identity")
                row["public_boundary"] = {"one_query_prefix_equal": True,
                                          "private_mutation_invariant": True,
                                          "query_answer_absent": True,
                                          "future_query_inputs_absent": True,
                                          "first_turn_sha256": public_id}
                row["status"] = "pass" if not row["errors"] else "fail"
                episodes[(job["seed"], job["demos"], threshold)] = episode
                if row["status"] == "pass" and job["demos"] == 2 and threshold not in exemplars:
                    private_path = f"private/example_min_holes_{threshold}.json"
                    private = {"schema": "topology-private-racket-example-v1", "visibility": "private",
                               "task_id": TASK_ID, **job, **episode,
                               "program_sha256": row["program_sha256"],
                               "label_authority": "protected_racket", "training_admission": False}
                    _write_json(out / private_path, private)
                    public_path = f"public/{public_id}.json"
                    (out / public_path).write_bytes(payload)
                    report["examples"].append({"settings": job["settings"], "private_path": private_path,
                                               "private_sha256": _sha((out / private_path).read_bytes()),
                                               "public_path": public_path, "public_sha256": public_id})
                    exemplars.add(threshold)
            except Exception as error:
                row["status"] = "fail"
                row.setdefault("materialized", False)
                row["errors"].append(f"{type(error).__name__}: {error}")
        for seed, demos in sorted({(job["seed"], job["demos"]) for job in jobs}):
            pair = [episodes.get((seed, demos, threshold)) for threshold in (1, 2)]
            if any(episode is None for episode in pair):
                report["errors"].append(f"Missing paired materialization for seed={seed}, demos={demos}")
                continue
            signatures = [[_sha(_bytes(p["input"])) for split in ("train", "test") for p in episode[split]]
                          for episode in pair]
            changed = [i for i, (a, b) in enumerate(zip(pair[0]["test"], pair[1]["test"]))
                       if a["output"] != b["output"]]
            check = {"seed": seed, "demos": demos, "same_inputs_across_settings": signatures[0] == signatures[1],
                     "queries_changed_by_setting": changed}
            report["paired_settings_checks"].append(check)
            if not check["same_inputs_across_settings"] or changed != [0, 1, 2, 3]:
                report["errors"].append("Setting pairing or per-query parameter effect failed")
        if exemplars != {1, 2}:
            report["errors"].append("Both settings require a complete 2-demo/4-query Racket-labeled example")
        if report["source_sha256"] != _source_hashes():
            report["errors"].append("Source changed during verification; rerun on frozen bytes")
    except Exception as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        if bridge is not None:
            bridge.close()
        if execute is not None:
            report["racket_evaluations"] = execute.stats()
    checks = [check for row in report["episodes"] for check in row.get("label_checks", [])]
    prefix_checks = [check for row in report["episodes"] for check in row.get("one_query_label_checks", [])]
    rivals = [rival for row in report["episodes"] for rival in row.get("rivals", [])]
    report["counts"] = {"requested_episodes": len(jobs),
                        "materialized_episodes": sum(row.get("materialized", False) for row in report["episodes"]),
                        "passed_episodes": sum(row["status"] == "pass" for row in report["episodes"]),
                        "label_claims_compared": len(checks),
                        "one_query_label_claims_compared": len(prefix_checks),
                        "label_mismatches": sum(not c["matches"] for c in checks + prefix_checks),
                        "rival_episode_checks": len(rivals),
                        "rivals_refuted": sum(r["refuted"] for r in rivals),
                        "rival_execution_failures": sum(bool(r["errors"]) for r in rivals),
                        "wrong_query_survivors": sum(bool(r["query_disagreements"]) for r in rivals),
                        "private_complete_examples": len(report["examples"]),
                        "public_first_turn_files": len(report["examples"])}
    report["status"] = ("pass" if not report["errors"]
                        and report["counts"]["passed_episodes"] == len(jobs) else "fail")
    _write_json(out / "self_review.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New evidence directory; existing paths are rejected")
    parser.add_argument("--seed", action="append", type=int, help="Repeat once or twice; defaults to 0 and 17")
    args = parser.parse_args(argv)
    try:
        report = run(args.out, args.seed)
    except Exception as error:
        print(json.dumps({"status": "fail", "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "racket_evaluations": report.get("racket_evaluations"),
                      "report": str(args.out / "self_review.json"),
                      "errors": report["errors"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
