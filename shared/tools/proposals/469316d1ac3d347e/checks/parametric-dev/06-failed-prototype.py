#!/usr/bin/env python3
"""Task-local proposed rule variants for stacked occupancy (ARC 31d5ba1a).

The selected canonical generator and its Racket authority remain separate.
All labels here are evaluated by the included public Racket bridge.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "af0ae766e671"
VERSION = "stacked-occupancy-parametric-v1"
PARAMETER_DOMAIN = "af0ae766e671:parameter-selection:v1:"


@dataclass(frozen=True)
class Parameters:
    operation: str = "xor"
    output_color: int = 6

    def __post_init__(self):
        if type(self.operation) is not str or self.operation not in ("xor", "and", "or"):
            raise ValueError("operation must be one of: xor, and, or")
        if type(self.output_color) is not int or not 1 <= self.output_color <= 9:
            raise ValueError("output_color must be an integer in 1..9, not bool")

    def as_dict(self):
        return {"operation": self.operation, "output_color": self.output_color}


DEFAULT = Parameters()
SETTINGS = tuple(Parameters(operation, color)
                 for operation in ("xor", "and", "or") for color in range(1, 10))


def emit_program(parameters=DEFAULT):
    """Return the exact callable Racket expression used for every label."""
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a Parameters instance")
    predicate = {"xor": "(not (equal? upper lower))",
                 "and": "(and upper lower)", "or": "(or upper lower)"}[parameters.operation]
    return f"""(lambda (g)
  (let* ((half-h (quotient (rows g) 2))
         (width (cols g)))
    (build-grid half-h width (r c)
      (let ((upper (not (zero? (at g r c))))
            (lower (not (zero? (at g (+ r half-h) c)))))
        (if {predicate} {parameters.output_color} 0)))))
"""


def _racket_list(value):
    if isinstance(value, list):
        return "(" + " ".join(_racket_list(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("grids must contain integer ARC colors 0..9, not bool")
    return str(value)


def execute_program(program, grids, *, bridge=None):
    """Apply an exact callable program to grids in real Racket, never Python."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return execute_program(program, grids, bridge=owned_bridge)
    return bridge.eval_text("(map " + program + " '" + _racket_list(grids) + ")")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _text_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _valid_seed(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer, not bool")


def sample_parameters(seed):
    """Choose one of 27 settings once, using a versioned domain-separated hash."""
    _valid_seed(seed)
    index = int(hashlib.sha256((PARAMETER_DOMAIN + str(seed)).encode()).hexdigest(), 16) % len(SETTINGS)
    return SETTINGS[index]


def covering_seeds(seed_start=0, *, max_draws=10000):
    """Find one genuinely seed-selected episode per setting, with a finite cap."""
    _valid_seed(seed_start)
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError("max_draws must be a positive integer")
    chosen = {}
    for seed in range(seed_start, seed_start + max_draws):
        chosen.setdefault(sample_parameters(seed), seed)
        if len(chosen) == len(SETTINGS):
            return [chosen[parameters] for parameters in SETTINGS]
    raise ValueError(f"only {len(chosen)}/27 settings found in {max_draws} candidate seeds")


def _difference(expected, observed):
    if len(expected) != len(observed) or any(len(a) != len(b) for a, b in zip(expected, observed)):
        return {"expected_shape": [len(expected), len(expected[0])],
                "observed_shape": [len(observed), len(observed[0]) if observed else 0]}
    for r, (a, b) in enumerate(zip(expected, observed)):
        for c, (wanted, actual) in enumerate(zip(a, b)):
            if wanted != actual:
                return {"row": r, "col": c, "expected": wanted, "observed": actual}
    return None


def check_identifiability(train, *, bridge=None):
    """Enumerate all declared settings using demonstrations only.

    No query argument exists. Both ambiguity and zero surviving settings are
    reported honestly; callers decide whether a lesson may be emitted.
    """
    if not isinstance(train, list) or not train:
        raise ValueError("at least one labeled demonstration is required")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return check_identifiability(train, bridge=owned_bridge)
    inputs = [pair["input"] for pair in train]
    rivals, survivors = [], []
    for parameters in SETTINGS:
        program = emit_program(parameters)
        outputs = execute_program(program, inputs, bridge=bridge)
        matches, first_difference = [], None
        for index, (pair, output) in enumerate(zip(train, outputs)):
            difference = _difference(pair["output"], output)
            if difference is None:
                matches.append(index)
            elif first_difference is None:
                first_difference = {"demo_index": index, **difference}
        survives = len(matches) == len(train)
        if survives:
            survivors.append(parameters.as_dict())
        rivals.append({"parameters": parameters.as_dict(), "program_sha256": _text_digest(program),
                       "matches_all_demos": survives, "matching_demo_indices": matches,
                       "output_sha256": [_digest(output) for output in outputs],
                       "first_difference": first_difference})
    return {"scope": "all 27 declared settings; demonstrations only; no query consulted",
            "settings_checked": len(SETTINGS), "demonstrations_checked": len(train),
            "survivors": survivors, "unique": len(survivors) == 1, "rivals": rivals}


def make_episode(seed, *, difficulty=None, bridge=None):
    """Generate exactly three demos and one query under one seed-chosen rule."""
    parameters = sample_parameters(seed)  # The only rule draw for this episode.
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return make_episode(seed, difficulty=difficulty, bridge=owned_bridge)
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK, root=root)
    grids = [generator.generate(seed, index, difficulty=difficulty) for index in range(4)]
    for index, grid in enumerate(grids):
        issues = generator.self_check(grid, difficulty=difficulty)
        if issues:
            raise ValueError(f"selected input {index} failed its domain check: {issues}")
    program = emit_program(parameters)
    outputs = execute_program(program, grids, bridge=bridge)
    if not isinstance(outputs, list) or len(outputs) != 4:
        raise ValueError("Racket must return exactly four labeled outputs")
    pairs = [{"input": grid, "output": output, "sample_index": index,
              "input_sha256": _digest(grid), "output_sha256": _digest(output)}
             for index, (grid, output) in enumerate(zip(grids, outputs))]
    identifiability = check_identifiability(pairs[:3], bridge=bridge)
    if identifiability["survivors"] != [parameters.as_dict()]:
        raise ValueError("demonstrations do not uniquely identify the episode's chosen setting")
    return {"schema": VERSION, "status": "prototype", "task_id": TASK,
            "seed": seed, "difficulty": difficulty,
            "parameters": parameters.as_dict(), "parameter_selection": PARAMETER_DOMAIN,
            "sample_indices": [0, 1, 2, 3],
            "generator_source": {"path": source.relative_to(root).as_posix(), "sha256": source_hash},
            "prototype_source": {"path": Path(__file__).resolve().relative_to(root).as_posix(),
                                 "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            "program": program, "program_sha256": _text_digest(program),
            "train": pairs[:3], "test": pairs[3:], "identifiability": identifiability}


def public_challenge(episode):
    """Fresh, minimal ARC challenge with no rule, parameters, seeds, or answers."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}


def distinct_witness(*, bridge=None):
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return distinct_witness(bridge=owned_bridge)
    grid = [[0, 0, 9, 9], [0, 4, 0, 4]]
    generator = load_selected_generator(TASK, root=find_root(__file__))[0]
    issues = generator.self_check(grid)
    if issues:
        raise ValueError(f"the four-state witness is outside the selected input domain: {issues}")
    outputs = [{"parameters": parameters.as_dict(),
                "program_sha256": _text_digest(emit_program(parameters)),
                "output": execute_program(emit_program(parameters), [grid], bridge=bridge)[0]}
               for parameters in SETTINGS]
    unique = len({_digest(row["output"]) for row in outputs})
    return {"input": grid, "input_sha256": _digest(grid), "self_check": issues,
            "state_order": ["00", "01", "10", "11"], "outputs": outputs,
            "distinct_outputs": unique, "all_settings_distinct": unique == len(SETTINGS)}


def canonical_parity(*, bridge):
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    outputs = execute_program(emit_program(DEFAULT), [pair["input"] for pair in pairs], bridge=bridge)
    records = [{**pair, "actual_output": output, "passed": output == pair["output"]}
               for pair, output in zip(pairs, outputs)]
    return {"parameters": DEFAULT.as_dict(), "program": emit_program(DEFAULT),
            "program_sha256": _text_digest(emit_program(DEFAULT)),
            "coverage": "all usable labeled pairs in every canonical variant",
            "pairs_checked": len(pairs), "passed": bool(records) and all(row["passed"] for row in records),
            "pairs": records}


def _sources():
    root = find_root(__file__)
    _, generator_source, generator_hash = load_selected_generator(TASK, root=root)
    source_paths = [Path(__file__).resolve(), root / f"generators/{TASK}/tests/test_parametric_extension.py"]
    programs = []
    for line in canonical_path(root).open(encoding="utf-8"):
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                programs.append({"program": program, "sha256": _text_digest(program)})
    return {"prototype_files": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in source_paths},
            "generator": {"path": generator_source.relative_to(root).as_posix(), "sha256": generator_hash},
            "canonical_programs": programs}


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _audit(out, seed_start, bridge):
    seeds = covering_seeds(seed_start)
    programs = [{"parameters": parameters.as_dict(), "program": emit_program(parameters),
                 "program_sha256": _text_digest(emit_program(parameters))} for parameters in SETTINGS]
    _write_json(out / "programs.json", programs)
    parity = canonical_parity(bridge=bridge)
    _write_json(out / "canonical-parity.json", parity)
    witness = distinct_witness(bridge=bridge)
    _write_json(out / "witness.json", witness)
    episode_summaries, failures = [], []
    with (out / "episodes.private.jsonl").open("w", encoding="utf-8") as private, \
            (out / "challenges.public.jsonl").open("w", encoding="utf-8") as public:
        for index, seed in enumerate(seeds):
            parameters = sample_parameters(seed)
            try:
                episode = make_episode(seed, bridge=bridge)
                private.write(json.dumps(episode, sort_keys=True, separators=(",", ":")) + "\n")
                public.write(json.dumps(public_challenge(episode), separators=(",", ":")) + "\n")
                private.flush()
                public.flush()
                episode_summaries.append({"line_index": index, "seed": seed, "parameters": parameters.as_dict(),
                                          "program_sha256": episode["program_sha256"],
                                          "survivors": episode["identifiability"]["survivors"]})
            except Exception as exc:
                failures.append({"line_index": index, "seed": seed, "parameters": parameters.as_dict(),
                                 "error": f"{type(exc).__name__}: {exc}"})
            print(json.dumps({"episode": index + 1, "requested": len(seeds), "seed": seed,
                              "completed": len(episode_summaries), "failed": len(failures)}), flush=True)
    ambiguous_train = [{"input": [[9, 9, 9, 9], [4, 4, 4, 4]], "output": [[3, 3, 3, 3]]}]
    ambiguity = {"purpose": "diagnostic only: intentionally missing occupancy states; never an emitted episode",
                 "train": ambiguous_train, "identifiability": check_identifiability(ambiguous_train, bridge=bridge)}
    _write_json(out / "ambiguity.json", ambiguity)
    passed = (parity["passed"] and witness["all_settings_distinct"] and not failures
              and len(episode_summaries) == len(SETTINGS)
              and ambiguity["identifiability"]["survivors"] == [Parameters("and", 3).as_dict(), Parameters("or", 3).as_dict()])
    report = {"schema": VERSION + "-audit", "status": "prototype", "passed": passed,
              "task_id": TASK, "default": DEFAULT.as_dict(),
              "parameter_values": {"operation": ["xor", "and", "or"], "output_color": list(range(1, 10))},
              "parameter_dependent_input_constraints": [],
              "input_contract": "two equally sized stacked panels; one distinct nonzero color per panel; all four occupancy states",
              "seed_start": seed_start, "seed_search_end": max(seeds), "selected_seeds": seeds,
              "settings_requested": len(SETTINGS), "episodes_completed": len(episode_summaries),
              "demonstrations_per_episode": 3, "queries_per_episode": 1,
              "canonical_pairs_checked": parity["pairs_checked"], "distinct_witness_outputs": witness["distinct_outputs"],
              "rival_settings_per_episode": len(SETTINGS), "episodes": episode_summaries, "failures": failures,
              "sources": _sources(), "runtime": bridge.runtime_identity,
              "limitations": ["Proposed task-local prototype, not a production parametric API or approval.",
                              "One seed-selected episode per setting; finite evidence, not all seeds or all valid inputs.",
                              "Identifiability is relative to these 27 declared settings, not every possible ARC rule.",
                              "Diagnostic ambiguity is retained and intentionally outside the full-state generation domain.",
                              "Public and private JSONL rows align by order; disclose only the public file to a solver."]}
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    episode_parser = subparsers.add_parser("episode", help="generate one complete seed-selected episode")
    episode_parser.add_argument("--seed", type=int, required=True)
    episode_parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    episode_parser.add_argument("--out", type=Path, required=True)
    audit_parser = subparsers.add_parser("audit", help="materialize finite Racket evidence for all 27 settings")
    audit_parser.add_argument("--seed-start", type=int, default=0)
    audit_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output already exists; choose a new path to preserve earlier evidence")
    try:
        _valid_seed(args.seed if args.mode == "episode" else args.seed_start)
    except ValueError as exc:
        parser.error(str(exc))
    args.out.mkdir(parents=True)
    receipt = {"command": [sys.executable, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)],
               "cwd": str(Path.cwd()), "exit_code": None}
    exit_code = 1
    try:
        with RacketBridge() as bridge:
            if args.mode == "episode":
                episode = make_episode(args.seed, difficulty=args.difficulty, bridge=bridge)
                _write_json(args.out / "episode.private.json", episode)
                _write_json(args.out / "challenge.public.json", public_challenge(episode))
                (args.out / "program.rkt").write_text(episode["program"], encoding="utf-8")
                _write_json(args.out / "runtime.json", bridge.runtime_identity)
                receipt["sources"] = _sources()
                exit_code = 0
            else:
                report = _audit(args.out, args.seed_start, bridge)
                exit_code = 0 if report["passed"] else 1
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        print(receipt["error"], file=sys.stderr)
    receipt["exit_code"] = exit_code
    _write_json(args.out / "command.json", receipt)
    print(json.dumps({"status": "prototype", "mode": args.mode, "passed": exit_code == 0,
                      "out": str(args.out), "exit_code": exit_code}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
