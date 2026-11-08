#!/usr/bin/env python3
"""Proposed Boolean-operation variants for ARC task 0520fde7.

The selected canonical generator and Racket authority remain separate. Every
prototype label and rival prediction is executed by the included public Racket
bridge; no Python output oracle labels an episode.
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

TASK = "79353e95283d"
VERSION = "aligned-panels-boolean-operation-parametric-v1"
PARAMETER_DOMAIN = "79353e95283d:boolean-operation-selection:v1:"


@dataclass(frozen=True)
class Parameters:
    """One hidden Boolean operation, fixed for a complete episode."""

    operation: str = "and"

    def __post_init__(self):
        if type(self.operation) is not str or self.operation not in ("and", "or", "xor"):
            raise ValueError("operation must be one of: and, or, xor")

    def as_dict(self):
        return {"operation": self.operation}


DEFAULT = Parameters()
SETTINGS = tuple(Parameters(operation) for operation in ("and", "or", "xor"))


def emit_program(parameters=DEFAULT):
    """Return the exact callable Racket expression used for labels."""
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a Parameters instance")
    predicate = {
        "and": "(and left right)",
        "or": "(or left right)",
        "xor": "(not (equal? left right))",
    }[parameters.operation]
    return f"""(lambda (g)
  (build-grid (rows g) 3 (r c)
    (let ((left (= 1 (at g r c)))
          (right (= 1 (at g r (+ c 4)))))
      (if {predicate} 2 0))))
"""


def _racket_list(value):
    if isinstance(value, list):
        return "(" + " ".join(_racket_list(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("grids must contain integer ARC colors 0..9, not bool")
    return str(value)


def execute_program(program, grids, *, bridge=None):
    """Apply an exact callable program to grids in real Racket, never Python."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket text")
    if not isinstance(grids, list) or not grids:
        raise ValueError("grids must be a nonempty list")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return execute_program(program, grids, bridge=owned_bridge)
    return bridge.eval_text("(map " + program + " '" + _racket_list(grids) + ")")


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _text_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _valid_seed(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer, not bool")


def sample_parameters(seed):
    """Choose one operation once through a versioned, domain-separated hash."""
    _valid_seed(seed)
    digest = hashlib.sha256((PARAMETER_DOMAIN + str(seed)).encode()).digest()
    return SETTINGS[int.from_bytes(digest, "big") % len(SETTINGS)]


def covering_seeds(seed_start=0, *, max_draws=1000):
    """Find one genuinely seed-selected episode for each declared setting."""
    _valid_seed(seed_start)
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError("max_draws must be a positive integer")
    chosen = {}
    for seed in range(seed_start, seed_start + max_draws):
        chosen.setdefault(sample_parameters(seed), seed)
        if len(chosen) == len(SETTINGS):
            return [chosen[parameters] for parameters in SETTINGS]
    raise ValueError(
        f"only {len(chosen)}/{len(SETTINGS)} settings found in {max_draws} candidate seeds"
    )


def _difference(expected, observed):
    if not isinstance(expected, list) or not isinstance(observed, list):
        return {"kind": "not_grid"}
    expected_width = len(expected[0]) if expected and isinstance(expected[0], list) else 0
    observed_width = len(observed[0]) if observed and isinstance(observed[0], list) else 0
    if len(expected) != len(observed) or any(
        not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b)
        for a, b in zip(expected, observed)
    ):
        return {
            "kind": "shape",
            "expected_shape": [len(expected), expected_width],
            "observed_shape": [len(observed), observed_width],
        }
    for r, (wanted_row, actual_row) in enumerate(zip(expected, observed)):
        for c, (wanted, actual) in enumerate(zip(wanted_row, actual_row)):
            if wanted != actual:
                return {
                    "kind": "cell",
                    "row": r,
                    "col": c,
                    "expected": wanted,
                    "observed": actual,
                }
    return None


def check_identifiability(train, *, bridge=None):
    """Enumerate declared operations using demonstrations only, never the query."""
    if not isinstance(train, list) or not train:
        raise ValueError("at least one labeled demonstration is required")
    for pair in train:
        if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
            raise ValueError("each demonstration must contain input and output")
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
        rivals.append(
            {
                "parameters": parameters.as_dict(),
                "program_sha256": _text_digest(program),
                "matches_all_demos": survives,
                "matching_demo_indices": matches,
                "first_difference": first_difference,
                "output_sha256": [_digest(output) for output in outputs],
            }
        )
    return {
        "scope": "all three declared operations; demonstrations only; no query consulted",
        "settings_checked": len(SETTINGS),
        "demonstrations_checked": len(train),
        "survivors": survivors,
        "unique": len(survivors) == 1,
        "rivals": rivals,
    }


def make_episode(seed, *, difficulty=None, bridge=None):
    """Generate three demonstrations and one query under one seed-chosen rule."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return make_episode(seed, difficulty=difficulty, bridge=owned_bridge)
    parameters = sample_parameters(seed)  # The only rule draw in this episode.
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
    pairs = [
        {
            "input": grid,
            "output": output,
            "sample_index": index,
            "input_sha256": _digest(grid),
            "output_sha256": _digest(output),
        }
        for index, (grid, output) in enumerate(zip(grids, outputs))
    ]
    identifiability = check_identifiability(pairs[:3], bridge=bridge)
    if identifiability["survivors"] != [parameters.as_dict()]:
        raise ValueError("demonstrations do not uniquely identify the chosen operation")
    prototype_path = Path(__file__).resolve()
    return {
        "schema": VERSION,
        "status": "proposed_prototype",
        "task_id": TASK,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": parameters.as_dict(),
        "parameter_selection": PARAMETER_DOMAIN,
        "sample_indices": [0, 1, 2, 3],
        "generator_source": {
            "path": source.relative_to(root).as_posix(),
            "sha256": source_hash,
        },
        "prototype_source": {
            "path": prototype_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
        },
        "program": program,
        "program_sha256": _text_digest(program),
        "train": pairs[:3],
        "test": pairs[3:],
        "identifiability": identifiability,
    }


def public_challenge(episode):
    """Return only visible demonstrations and query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def distinct_witness(*, bridge=None):
    """Execute all settings on one lawful grid containing 00, 01, 10, and 11."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return distinct_witness(bridge=owned_bridge)
    grid = [
        [0, 0, 1, 5, 0, 1, 0],
        [1, 0, 0, 5, 1, 0, 0],
    ]
    generator = load_selected_generator(TASK, root=find_root(__file__))[0]
    issues = generator.self_check(grid)
    if issues:
        raise ValueError(f"four-state witness is outside the selected input domain: {issues}")
    outputs = [
        {
            "parameters": parameters.as_dict(),
            "program": emit_program(parameters),
            "program_sha256": _text_digest(emit_program(parameters)),
            "output": execute_program(emit_program(parameters), [grid], bridge=bridge)[0],
        }
        for parameters in SETTINGS
    ]
    unique = len({_digest(row["output"]) for row in outputs})
    return {
        "input": grid,
        "input_sha256": _digest(grid),
        "self_check": issues,
        "state_order": ["00", "01", "10", "11"],
        "outputs": outputs,
        "distinct_outputs": unique,
        "all_settings_distinct": unique == len(SETTINGS),
    }


def canonical_parity(*, bridge):
    """Execute the canonical default on every usable labeled canonical pair."""
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    outputs = execute_program(
        emit_program(DEFAULT), [pair["input"] for pair in pairs], bridge=bridge
    )
    records = [
        {**pair, "actual_output": output, "passed": output == pair["output"]}
        for pair, output in zip(pairs, outputs)
    ]
    return {
        "parameters": DEFAULT.as_dict(),
        "program": emit_program(DEFAULT),
        "program_sha256": _text_digest(emit_program(DEFAULT)),
        "coverage": "all usable labeled canonical train and test pairs",
        "pairs_checked": len(pairs),
        "passed": bool(records) and all(row["passed"] for row in records),
        "pairs": records,
    }


def _sources():
    root = find_root(__file__)
    _, generator_source, generator_hash = load_selected_generator(TASK, root=root)
    task_home = root / "generators" / TASK
    source_paths = [
        Path(__file__).resolve(),
        task_home / "tests/test_parametric_boolean_operation.py",
        task_home / "workspace/parametric/README.md",
    ]
    prototype_files = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
        if path.is_file()
    }
    canonical_programs = []
    for line in canonical_path(root).open(encoding="utf-8"):
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                canonical_programs.append(
                    {"program": program, "sha256": _text_digest(program)}
                )
    return {
        "prototype_files": prototype_files,
        "generator": {
            "path": generator_source.relative_to(root).as_posix(),
            "sha256": generator_hash,
        },
        "canonical_programs": canonical_programs,
    }


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _audit(out, seed_start, bridge):
    seeds = covering_seeds(seed_start)
    programs = [
        {
            "parameters": parameters.as_dict(),
            "program": emit_program(parameters),
            "program_sha256": _text_digest(emit_program(parameters)),
        }
        for parameters in SETTINGS
    ]
    _write_json(out / "programs.json", programs)
    parity = canonical_parity(bridge=bridge)
    _write_json(out / "canonical-parity.json", parity)
    witness = distinct_witness(bridge=bridge)
    _write_json(out / "witness.json", witness)

    summaries, failures = [], []
    with (out / "episodes.private.jsonl").open("w", encoding="utf-8") as private, \
            (out / "challenges.public.jsonl").open("w", encoding="utf-8") as public:
        for attempt_index, seed in enumerate(seeds):
            parameters = sample_parameters(seed)
            try:
                episode = make_episode(seed, bridge=bridge)
            except Exception as exc:
                failures.append(
                    {
                        "attempt_index": attempt_index,
                        "line_index": None,
                        "seed": seed,
                        "parameters": parameters.as_dict(),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            else:
                private.write(
                    json.dumps(episode, sort_keys=True, separators=(",", ":")) + "\n"
                )
                public.write(
                    json.dumps(public_challenge(episode), separators=(",", ":")) + "\n"
                )
                private.flush()
                public.flush()
                summaries.append(
                    {
                        "attempt_index": attempt_index,
                        "line_index": len(summaries),
                        "seed": seed,
                        "parameters": parameters.as_dict(),
                        "program_sha256": episode["program_sha256"],
                        "survivors": episode["identifiability"]["survivors"],
                    }
                )
            print(
                json.dumps(
                    {
                        "episode": attempt_index + 1,
                        "requested": len(seeds),
                        "seed": seed,
                        "completed": len(summaries),
                        "failed": len(failures),
                    }
                ),
                flush=True,
            )

    ambiguous_train = [
        {"input": [[1, 1, 1, 5, 1, 1, 1]], "output": [[2, 2, 2]]}
    ]
    ambiguity = {
        "purpose": "diagnostic only: state 11 alone cannot distinguish AND from OR",
        "train": ambiguous_train,
        "identifiability": check_identifiability(ambiguous_train, bridge=bridge),
    }
    _write_json(out / "ambiguity.json", ambiguity)

    expected_ambiguous = [Parameters("and").as_dict(), Parameters("or").as_dict()]
    passed = (
        parity["passed"]
        and witness["all_settings_distinct"]
        and not failures
        and len(summaries) == len(SETTINGS)
        and ambiguity["identifiability"]["survivors"] == expected_ambiguous
    )
    report = {
        "schema": VERSION + "-audit",
        "status": "proposed_prototype",
        "passed": passed,
        "task_id": TASK,
        "default": DEFAULT.as_dict(),
        "parameter_values": {"operation": ["and", "or", "xor"]},
        "parameter_dependent_input_constraints": [
            "Demonstrations must contain truth states that distinguish the chosen operation; ordinary selected draws contain all four states."
        ],
        "input_contract": "two aligned binary three-column panels separated by one legal color",
        "seed_start": seed_start,
        "seed_search_end": max(seeds),
        "selected_seeds": seeds,
        "settings_requested": len(SETTINGS),
        "episodes_completed": len(summaries),
        "demonstrations_per_episode": 3,
        "queries_per_episode": 1,
        "canonical_pairs_checked": parity["pairs_checked"],
        "distinct_witness_outputs": witness["distinct_outputs"],
        "rival_settings_per_episode": len(SETTINGS),
        "episodes": summaries,
        "failures": failures,
        "sources": _sources(),
        "runtime": bridge.runtime_identity,
        "limitations": [
            "Proposed task-local prototype, not a production parametric API, canonical relabeling, approval, or training admission.",
            "One seed-selected episode per setting; finite evidence, not all seeds or all valid inputs.",
            "Identifiability is relative to AND, OR, and XOR, not every possible ARC rule.",
            "The intentionally ambiguous diagnostic is retained and never emitted as an ordinary episode.",
            "Only public challenges omit parameters, reference programs, seeds, and query outputs.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    episode_parser = subparsers.add_parser(
        "episode", help="generate one complete seed-selected episode"
    )
    episode_parser.add_argument("--seed", type=int, required=True)
    episode_parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    episode_parser.add_argument("--out", type=Path, required=True)
    audit_parser = subparsers.add_parser(
        "audit", help="materialize finite Racket evidence for all three operations"
    )
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
    receipt = {
        "command": [
            sys.executable,
            str(Path(__file__).resolve()),
            *(sys.argv[1:] if argv is None else argv),
        ],
        "cwd": str(Path.cwd()),
        "exit_code": None,
    }
    exit_code = 1
    try:
        with RacketBridge() as bridge:
            if args.mode == "episode":
                episode = make_episode(
                    args.seed, difficulty=args.difficulty, bridge=bridge
                )
                _write_json(args.out / "episode.private.json", episode)
                _write_json(args.out / "challenge.public.json", public_challenge(episode))
                (args.out / "program.rkt").write_text(
                    episode["program"], encoding="utf-8"
                )
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
    print(
        json.dumps(
            {
                "status": "proposed_prototype",
                "mode": args.mode,
                "passed": exit_code == 0,
                "out": str(args.out),
                "exit_code": exit_code,
            }
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
