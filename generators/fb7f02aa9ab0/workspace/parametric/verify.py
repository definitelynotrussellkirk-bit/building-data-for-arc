"""Verify task-local episodes with protected Racket; export only the current query.

Run through the packet's Python wrapper, or with this checkout's ``src`` and
``shared/runtime`` on PYTHONPATH. The output directory must not already exist.
All labels, program text, settings, future queries and diagnostics stay private.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "fb7f02aa9ab0"
POLICIES = ("all", "largest")
CONTROLS = (3, 4, 6)
QUERIES = 4


class VerificationError(RuntimeError):
    def __init__(self, message, **context):
        super().__init__(message)
        self.context = context


def require(condition, message, **context):
    if not condition:
        raise VerificationError(message, **context)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def source_hashes():
    paths = [HOME / name for name in ("prototype.py", "adapter.py", "canonical.rkt", "verify.py")]
    paths += [ROOT / name for name in (
        "src/arcpuzzles/parametric_worker.py",
        "shared/runtime/reviewer_support.py",
        "shared/runtime/puzzle_generators/rule_wrap.py",
    )]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def load_local(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location("_fb7f02aa9ab0_verify_" + name, path)
    require(spec is not None, "Could not load adjacent module", module=name)
    module = importlib.util.module_from_spec(spec)
    # Compile source bytes explicitly, avoiding timestamp-based stale pyc reuse.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def cells(grid, color=None):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if (value != 0 if color is None else value == color)}


def component_sizes(points, diagonal=False):
    remaining, sizes = set(points), []
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        offsets += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while remaining:
        queue = [remaining.pop()]
        size = 0
        while queue:
            r, c = queue.pop()
            size += 1
            for dr, dc in offsets:
                neighbor = r + dr, c + dc
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def geometry(points):
    sizes4, sizes8 = component_sizes(points), component_sizes(points, diagonal=True)
    return {
        "nonzero_cells": len(points),
        "bbox": ([min(r for r, c in points), min(c for r, c in points),
                  max(r for r, c in points), max(c for r, c in points)] if points else None),
        "components4": len(sizes4), "components8": len(sizes8),
        "component_sizes4": sizes4, "component_sizes8": sizes8,
    }


def first_turn(episode):
    visible = copy.deepcopy(episode)
    visible["test"] = visible["test"][:1]
    return visible


class Verifier:
    def __init__(self, out, report, worker, public_helpers, prototype, adapter, apply):
        self.out, self.report = out, report
        self.worker, self.public_helpers = worker, public_helpers
        self.prototype, self.adapter, self.apply = prototype, adapter, apply

    def execute(self, program, grid, **context):
        self.report["counts"]["racket_calls"] += 1
        try:
            return self.worker._grid(self.apply(program, copy.deepcopy(grid)))
        except Exception as error:
            # A crash is a failed verification, never a demonstration refutation.
            raise VerificationError("Protected Racket execution failed",
                program_sha256=hashlib.sha256(program.encode()).hexdigest(),
                input_sha256=digest(grid), error_type=type(error).__name__,
                error=str(error), **context) from error

    def generate(self, seed, settings, demos, queries):
        self.report["counts"]["episode_generate_calls"] += 1
        try:
            return self.adapter.generate(seed, copy.deepcopy(settings), demos, queries)
        except Exception as error:
            failure = {"seed": seed, "settings": settings, "demos": demos,
                       "queries": queries, "error_type": type(error).__name__,
                       "error": str(error)}
            self.report["generation_failures"].append(failure)
            print("GENERATION FAILED: " + json.dumps(failure, sort_keys=True), file=sys.stderr)
            return None

    def validate_episode(self, generated, demos, queries, program):
        require(type(generated) is dict, "generate() must return an episode object")
        require(generated.get("program_solution") == program,
                "Generated program_solution does not equal adapter.program(settings)")
        normalized = {}
        for split, count in (("train", demos), ("test", queries)):
            pairs = generated.get(split)
            require(type(pairs) is list and len(pairs) == count,
                    "Generated pair count differs from request", split=split, expected=count)
            normalized[split] = []
            for index, pair in enumerate(pairs):
                require(type(pair) is dict and {"input", "output"} <= pair.keys(),
                        "Every private pair needs input and output", split=split, index=index)
                normalized[split].append({key: self.worker._grid(pair[key])
                                          for key in ("input", "output")})
        inputs = [digest(pair["input"]) for split in normalized.values() for pair in split]
        require(len(inputs) == len(set(inputs)), "Demonstration and query inputs must be distinct")
        return normalized

    def mirror_rival(self, program, spec, grid, **context):
        actual = self.execute(program, grid, **context)
        try:
            mirror = self.worker._grid(self.prototype._reference(copy.deepcopy(grid), **spec))
        except Exception as error:
            raise VerificationError("Python rival mirror failed", error_type=type(error).__name__,
                                    error=str(error), **context) from error
        require(actual == mirror, "Racket rival and Python mirror disagree",
                racket_output=actual, python_output=mirror, **context)
        self.report["counts"]["rival_mirror_checks"] += 1
        return actual

    def export_first_turn(self, generated, episode, seed, settings, demos, program):
        single = self.generate(seed, settings, demos, 1)
        if single is None:
            return {"status": "failed", "reason": "single-query generation failed"}
        single_episode = self.validate_episode(single, demos, 1, program)
        current = first_turn(generated)
        public_bytes = self.public_helpers.public_challenge_bytes(current)
        identifier = self.public_helpers.public_challenge_id(current)
        require(public_bytes == self.public_helpers.public_challenge_bytes(single),
                "First-turn public bytes depend on the requested private query count")
        require(episode["test"][0] == single_episode["test"][0],
                "First-query private label depends on requested query count")
        mutated = copy.deepcopy(current)
        mutated.update(seed=seed + 1, settings={"component_policy": "private mutation"},
                       task_id="private mutation", program_solution="private mutation",
                       total_queries=999, future_queries=copy.deepcopy(generated["test"][1:]))
        old_label = mutated["test"][0]["output"]
        mutated["test"][0]["output"] = [[9]] if old_label != [[9]] else [[0]]
        mutated["train"][0]["private_note"] = "private mutation"
        require(identifier == self.public_helpers.public_challenge_id(mutated),
                "Private metadata or query-label mutation changed the public content ID")
        require(public_bytes == self.public_helpers.public_challenge_bytes(mutated),
                "Private metadata or query-label mutation changed public bytes")
        expected = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
        require(json.loads(public_bytes) == expected,
                "Public export contains something besides demos and one current-query input")
        require(identifier == hashlib.sha256(public_bytes).hexdigest(),
                "Public content ID is not the hash of its exact file bytes")
        relative = "public/" + identifier + ".json"
        path = self.out / relative
        if path.exists():
            require(path.read_bytes() == public_bytes, "Public content-ID collision")
        else:
            path.write_bytes(public_bytes)
        self.report["counts"]["public_first_turn_checks"] += 1
        return {"status": "passed", "file": relative, "content_id": identifier,
                "public_query_count": 1, "queries1_prefix_bytes_equal": True,
                "queries1_private_label_equal": True, "private_mutation_id_equal": True}

    def episode(self, seed, policy, demos, bank):
        settings = {"component_policy": policy}
        generated = self.generate(seed, settings, demos, QUERIES)
        if generated is None:
            return
        episode = self.validate_episode(generated, demos, QUERIES, bank["program"])
        row = {"seed": seed, "settings": settings, "demos": demos, "queries": QUERIES,
               "episode": episode, "program_sha256": bank["program_sha256"],
               "label_checks": 0, "rivals_fitted_on": "train_only", "rivals": {},
               "survivors": [], "dangerous_survivors": []}
        self.report["episodes"].append(row)
        for split in ("train", "test"):
            for index, pair in enumerate(episode[split]):
                context = {"seed": seed, "policy": policy, "demos": demos,
                           "split": split, "index": index, "role": "target"}
                actual = self.execute(bank["program"], pair["input"], **context)
                require(actual == pair["output"], "Generated label disagrees with protected Racket",
                        expected=pair["output"], actual=actual, **context)
                row["label_checks"] += 1
                self.report["counts"]["episode_label_checks"] += 1
        for name, rival in bank["rivals"].items():
            result = {"demo_checks": 0, "refutation_indices": [], "demo_output_sha256": []}
            row["rivals"][name] = result
            # Deliberately execute every demo, including those after a refutation.
            for index, pair in enumerate(episode["train"]):
                actual = self.mirror_rival(rival["program"], rival["python_spec"], pair["input"],
                    seed=seed, policy=policy, demos=demos, rival=name, split="train", index=index)
                result["demo_checks"] += 1
                result["demo_output_sha256"].append(digest(actual))
                if actual != pair["output"]:
                    result["refutation_indices"].append(index)
            result["survived_demos"] = not result["refutation_indices"]
            if not result["survived_demos"]:
                continue
            row["survivors"].append(name)
            result.update(query_agreement_indices=[], query_disagreement_indices=[])
            for index, pair in enumerate(episode["test"]):
                actual = self.mirror_rival(rival["program"], rival["python_spec"], pair["input"],
                    seed=seed, policy=policy, demos=demos, rival=name, split="test", index=index)
                key = "query_agreement_indices" if actual == pair["output"] else "query_disagreement_indices"
                result[key].append(index)
            if result["query_disagreement_indices"]:
                row["dangerous_survivors"].append(name)
        require(not row["dangerous_survivors"], "A demo-fitting rival disagrees on private queries",
                seed=seed, policy=policy, demos=demos, rivals=row["dangerous_survivors"])
        row["public_first_turn"] = self.export_first_turn(
            generated, episode, seed, settings, demos, bank["program"])

    def stress(self, seeds, banks):
        for seed in seeds:
            for size_index, (height, width) in enumerate(((8, 11), (30, 30))):
                for control_index, control in enumerate(CONTROLS):
                    arguments = {"seed": seed, "index": 200000 + size_index * 100 + control_index,
                                 "control": control, "height": height, "width": width, "kind": "rails"}
                    self.report["counts"]["stress_input_calls"] += 1
                    try:
                        grid = self.worker._grid(self.prototype.make_input(**arguments))
                    except Exception as error:
                        failure = {"stage": "stress", "arguments": arguments,
                                   "error_type": type(error).__name__, "error": str(error)}
                        self.report["generation_failures"].append(failure)
                        print("GENERATION FAILED: " + json.dumps(failure, sort_keys=True), file=sys.stderr)
                        continue
                    require((len(grid), len(grid[0])) == (height, width),
                            "Stress generator did not honor dimensions", arguments=arguments)
                    row = {"arguments": arguments, "input_sha256": digest(grid),
                           "input_geometry": geometry(cells(grid)),
                           "operand_geometry": {str(color): geometry(cells(grid, color)) for color in (1, 2)},
                           "intermediate_geometry": geometry(self.prototype.intermediate(grid)),
                           "policies": {}}
                    self.report["stress"].append(row)
                    for policy in POLICIES:
                        expected = self.worker._grid(self.prototype.reference(copy.deepcopy(grid), policy))
                        actual = self.execute(banks[policy]["program"], grid,
                                              role="stress", policy=policy, arguments=arguments)
                        require(actual == expected, "Stress label disagrees with protected Racket",
                                policy=policy, arguments=arguments, expected=expected, actual=actual)
                        row["policies"][policy] = {"label": actual, "output_geometry": geometry(cells(actual))}
                        self.report["counts"]["stress_label_checks"] += 1


def run(out, seeds, demos, report):
    import arcpuzzles.parametric_worker as worker
    import reviewer_support

    for module, relative in ((worker, "src/arcpuzzles/parametric_worker.py"),
                             (reviewer_support, "shared/runtime/reviewer_support.py")):
        require(Path(module.__file__).resolve() == ROOT / relative,
                "Verifier imports must come from this checkout", module=module.__name__)
    prototype, adapter = load_local("prototype"), load_local("adapter")
    banks = report["programs"]
    for policy in POLICIES:
        settings = {"component_policy": policy}
        program = adapter.program(settings)
        require(type(program) is str and program.strip(), "Target program must be nonempty text", policy=policy)
        require(program == prototype.program(settings), "Adapter and prototype programs differ", policy=policy)
        specs, programs = prototype.rival_specs(policy), prototype.rival_programs(policy)
        require(type(specs) is dict and type(programs) is dict and specs and specs.keys() == programs.keys(),
                "Every declared rival needs exactly one program and Python mirror", policy=policy)
        banks[policy] = {"program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                         "rivals": {}}
        for name, rival in programs.items():
            require(type(name) is str and name and type(rival) is str and rival.strip(),
                    "Rival names and programs must be nonempty text", policy=policy)
            banks[policy]["rivals"][name] = {"program": rival,
                "program_sha256": hashlib.sha256(rival.encode()).hexdigest(), "python_spec": specs[name]}
    runtime = ROOT / "shared/runtime"
    with worker._local_imports(runtime, HOME):
        apply, identity, bridge = worker._real_evaluator(runtime)
        try:
            report["racket"] = identity
            require(identity.get("backend") == "racket" and identity.get("protected") is True,
                    "A real protected Racket backend is required")
            verifier = Verifier(out, report, worker, reviewer_support, prototype, adapter, apply)
            for seed in seeds:
                for count in demos:
                    for policy in POLICIES:
                        verifier.episode(seed, policy, count, banks[policy])
            verifier.stress(seeds[:1], banks)
        finally:
            bridge.close()
    require(not report["generation_failures"], "One or more requested generations failed; none were retried",
            failure_count=len(report["generation_failures"]))


def integer_argument(value, low, high):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if not low <= result <= high:
        raise argparse.ArgumentTypeError(f"must be in {low}..{high}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seed", type=lambda x: integer_argument(x, 0, 2**63 - 1), action="append",
                        help="repeatable; defaults to 0 and 17")
    parser.add_argument("--demos", type=lambda x: integer_argument(x, 3, 6), action="append",
                        help="repeatable; defaults to 3 and 6")
    args = parser.parse_args(argv)
    seeds, demos = args.seed if args.seed is not None else [0, 17], args.demos if args.demos is not None else [3, 6]
    out = args.out.resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        parser.error(f"--out must be a new writable directory: {error}")
    (out / "private").mkdir()
    (out / "public").mkdir()
    sys.dont_write_bytecode = True
    report = {"schema": "fb7f02aa9ab0-parametric-verification-v1", "task_id": TASK_ID,
              "status": "running", "request": {"seeds": seeds, "demos": demos,
              "policies": list(POLICIES), "queries": QUERIES, "generation_retries": 0},
              "bbox_order": "top,left,bottom,right (inclusive)", "indices": "zero_based",
              "scope": "finite declared rivals and requested inputs; not general correctness or admission",
              "counts": {name: 0 for name in ("racket_calls", "episode_generate_calls", "episode_label_checks",
                  "rival_mirror_checks", "public_first_turn_checks", "stress_input_calls", "stress_label_checks")},
              "programs": {}, "episodes": [], "stress": [], "generation_failures": []}
    try:
        report["source_sha256"] = source_hashes()
        report["source_set_sha256"] = digest(report["source_sha256"])
        run(out, seeds, demos, report)
        require(source_hashes() == report["source_sha256"], "Verifier sources changed during execution")
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["failure"] = {"error_type": type(error).__name__, "error": str(error),
                             "context": getattr(error, "context", {})}
        print("VERIFICATION FAILED: " + json.dumps(report["failure"], sort_keys=True), file=sys.stderr)
    finally:
        (out / "private/evidence.json").write_bytes(encoded(report))
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "generation_failures": len(report["generation_failures"]), **report["counts"]}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
