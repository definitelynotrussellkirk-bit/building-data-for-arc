#!/usr/bin/env python3
"""Proposed episode-level variants for aligned occupancy across stacked halves.

The selected production generator and canonical Racket authority stay unchanged.
Every label produced here is evaluated by the included protected Racket bridge.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys

from arc_repl.racket_bridge import RacketBridge

TASK = "55993f4c12af"
VERSION = "half-height-occupancy-parametric-v1"


@dataclass(frozen=True)
class Parameters:
    """Canonical/default setting: occupancy OR painted with color 4."""

    operation: str = "or"
    output_color: int = 4

    def __post_init__(self) -> None:
        if type(self.operation) is not str or self.operation not in ("xor", "and", "or"):
            raise ValueError("operation must be one of: xor, and, or")
        if type(self.output_color) is not int or not 1 <= self.output_color <= 9:
            raise ValueError("output_color must be an integer in 1..9, not bool")

    def as_dict(self) -> dict[str, object]:
        return {"operation": self.operation, "output_color": self.output_color}


DEFAULT = Parameters()
SETTINGS = tuple(
    Parameters(operation, color)
    for operation in ("xor", "and", "or")
    for color in range(1, 10)
)


def emit_program(parameters: Parameters = DEFAULT) -> str:
    """Return the exact callable Racket expression used for labels."""
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a Parameters instance")
    predicate = {
        "xor": "(not (equal? top bottom))",
        "and": "(and top bottom)",
        "or": "(or top bottom)",
    }[parameters.operation]
    return f"""(lambda (g)
  (let* ((half-height (/ (rows g) 2))
         (width (cols g)))
    (build-grid half-height width (r c)
      (let ((top (not (zero? (at g r c))))
            (bottom (not (zero? (at g (+ r half-height) c)))))
        (if {predicate} {parameters.output_color} 0)))))
"""

def _racket_list(value):
    if isinstance(value, list):
        return "(" + " ".join(_racket_list(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("grids must contain integer ARC colors 0..9, not bool")
    return str(value)


def execute_program(program: str, grids: list[list[list[int]]], *, bridge=None):
    """Apply an exact callable program to grids in real Racket, never Python."""
    if type(program) is not str or program not in {emit_program(p) for p in SETTINGS}:
        raise ValueError("program must be one of the declared materialized variants")
    if not isinstance(grids, list) or not grids:
        raise ValueError("at least one grid is required")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return execute_program(program, grids, bridge=owned_bridge)
    return bridge.eval_text("(map " + program + " '" + _racket_list(grids) + ")")


from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

PARAMETER_DOMAIN = "55993f4c12af:parameter-selection:v1:"


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _valid_seed(seed) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer, not bool")


def sample_parameters(seed: int) -> Parameters:
    """Choose one setting exactly once using a versioned hash domain."""
    _valid_seed(seed)
    digest = hashlib.sha256((PARAMETER_DOMAIN + str(seed)).encode()).digest()
    return SETTINGS[int.from_bytes(digest, "big") % len(SETTINGS)]


def covering_seeds(seed_start: int = 0, *, max_draws: int = 10000) -> list[int]:
    """Find one actually seed-selected episode for every declared setting."""
    _valid_seed(seed_start)
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError("max_draws must be a positive integer")
    chosen: dict[Parameters, int] = {}
    for seed in range(seed_start, seed_start + max_draws):
        chosen.setdefault(sample_parameters(seed), seed)
        if len(chosen) == len(SETTINGS):
            return [chosen[parameters] for parameters in SETTINGS]
    raise ValueError(
        f"only {len(chosen)}/{len(SETTINGS)} settings found in {max_draws} candidate seeds"
    )


def _difference(expected, observed):
    if not isinstance(expected, list) or not isinstance(observed, list):
        return {"expected_type": type(expected).__name__, "observed_type": type(observed).__name__}
    expected_width = len(expected[0]) if expected and isinstance(expected[0], list) else 0
    observed_width = len(observed[0]) if observed and isinstance(observed[0], list) else 0
    if len(expected) != len(observed) or any(
        not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b)
        for a, b in zip(expected, observed)
    ):
        return {
            "expected_shape": [len(expected), expected_width],
            "observed_shape": [len(observed), observed_width],
        }
    for row, (wanted_row, actual_row) in enumerate(zip(expected, observed)):
        for col, (wanted, actual) in enumerate(zip(wanted_row, actual_row)):
            if wanted != actual:
                return {"row": row, "col": col, "expected": wanted, "observed": actual}
    return None


def check_identifiability(train, *, bridge=None) -> dict[str, object]:
    """Enumerate all declared settings against demonstrations only."""
    if not isinstance(train, list) or not train:
        raise ValueError("at least one labeled demonstration is required")
    for index, pair in enumerate(train):
        if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
            raise ValueError(f"demonstration {index} must contain input and output")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return check_identifiability(train, bridge=owned_bridge)

    inputs = [pair["input"] for pair in train]
    rivals = []
    survivors = []
    for parameters in SETTINGS:
        program = emit_program(parameters)
        outputs = execute_program(program, inputs, bridge=bridge)
        matching = []
        first_difference = None
        for index, (pair, output) in enumerate(zip(train, outputs)):
            difference = _difference(pair["output"], output)
            if difference is None:
                matching.append(index)
            elif first_difference is None:
                first_difference = {"demo_index": index, **difference}
        survives = len(matching) == len(train)
        if survives:
            survivors.append(parameters.as_dict())
        rivals.append(
            {
                "parameters": parameters.as_dict(),
                "program_sha256": _text_digest(program),
                "matches_all_demos": survives,
                "matching_demo_indices": matching,
                "output_sha256": [_digest(output) for output in outputs],
                "first_difference": first_difference,
            }
        )
    return {
        "scope": "all 27 declared settings; demonstrations only; no query consulted",
        "settings_checked": len(SETTINGS),
        "demonstrations_checked": len(train),
        "survivors": survivors,
        "unique": len(survivors) == 1,
        "rivals": rivals,
    }


def make_episode(
    seed: int,
    *,
    difficulty=None,
    bridge=None,
    generator_bundle=None,
) -> dict[str, object]:
    """Generate three demonstrations and one query under one seed-selected rule.

    ``generator_bundle`` is an explicit test seam for a task-test process that
    already imported the same source tree through a repository mirror. Normal
    callers and the CLI use the source-bound public loader.
    """
    _valid_seed(seed)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return make_episode(
                seed,
                difficulty=difficulty,
                bridge=owned_bridge,
                generator_bundle=generator_bundle,
            )

    parameters = sample_parameters(seed)
    root = find_root(__file__)
    if generator_bundle is None:
        generator, source, source_hash = load_selected_generator(TASK, root=root)
    else:
        generator, source, source_hash = generator_bundle
        source = Path(source).resolve()
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise ValueError("generator_bundle source hash mismatch")
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
        raise ValueError("demonstrations do not uniquely identify the episode's chosen setting")

    prototype_source = Path(__file__).resolve()
    return {
        "schema": VERSION,
        "status": "prototype",
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
            "path": prototype_source.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(prototype_source.read_bytes()).hexdigest(),
        },
        "program": program,
        "program_sha256": _text_digest(program),
        "train": pairs[:3],
        "test": pairs[3:],
        "identifiability": identifiability,
    }


def public_challenge(episode) -> dict[str, object]:
    """Return a solver-safe ARC challenge without hidden settings or query labels."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def distinct_witness(*, bridge=None, generator=None) -> dict[str, object]:
    """Execute every setting on one lawful grid containing all occupancy states."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return distinct_witness(bridge=owned_bridge, generator=generator)
    if generator is None:
        generator = load_selected_generator(TASK, root=find_root(__file__))[0]
    grid = generator.generate(
        55993,
        0,
        difficulty="easy",
        half_h=3,
        grid_w=3,
        top_color=9,
        bot_color=7,
        relation_profile="balanced",
    )
    issues = generator.self_check(grid)
    if issues:
        raise ValueError(f"the four-state witness is outside the selected input domain: {issues}")
    outputs = [
        {
            "parameters": parameters.as_dict(),
            "program_sha256": _text_digest(emit_program(parameters)),
            "output": execute_program(emit_program(parameters), [grid], bridge=bridge)[0],
        }
        for parameters in SETTINGS
    ]
    distinct = len({_digest(row["output"]) for row in outputs})
    return {
        "input": grid,
        "input_sha256": _digest(grid),
        "self_check": issues,
        "state_order": ["00", "01", "10", "11"],
        "outputs": outputs,
        "distinct_outputs": distinct,
        "all_settings_distinct": distinct == len(SETTINGS),
    }



def canonical_parity(*, bridge=None) -> dict[str, object]:
    """Execute the canonical/default prototype on every labeled canonical pair."""
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return canonical_parity(bridge=owned_bridge)
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    program = emit_program(DEFAULT)
    outputs = execute_program(program, [pair["input"] for pair in pairs], bridge=bridge)
    records = [
        {**pair, "actual_output": output, "passed": output == pair["output"]}
        for pair, output in zip(pairs, outputs)
    ]
    return {
        "parameters": DEFAULT.as_dict(),
        "program": program,
        "program_sha256": _text_digest(program),
        "coverage": "all usable labeled pairs in every canonical variant",
        "pairs_checked": len(pairs),
        "passed": bool(records) and all(row["passed"] for row in records),
        "pairs": records,
    }


def _sources() -> dict[str, object]:
    """Return hashes for every source that defines or tests this prototype."""
    root = find_root(__file__)
    _, generator_source, generator_hash = load_selected_generator(TASK, root=root)
    source_paths = [
        Path(__file__).resolve(),
        root / f"generators/{TASK}/tests/test_parametric_extension.py",
    ]
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                programs.append({"program": program, "sha256": _text_digest(program)})
    return {
        "prototype_files": {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
        },
        "generator": {
            "path": generator_source.relative_to(root).as_posix(),
            "sha256": generator_hash,
        },
        "canonical_programs": programs,
    }


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _audit(out: Path, seed_start: int, bridge: RacketBridge) -> dict[str, object]:
    """Materialize one seed-selected, source-bound episode for every setting."""
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

    episode_summaries = []
    failures = []
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
                # Filesystem failures intentionally escape to the command receipt;
                # they are not relabeled as rejected generated episodes.
                private.write(json.dumps(episode, sort_keys=True, separators=(",", ":")) + "\n")
                public.write(json.dumps(public_challenge(episode), separators=(",", ":")) + "\n")
                private.flush()
                public.flush()
                episode_summaries.append(
                    {
                        "attempt_index": attempt_index,
                        "line_index": len(episode_summaries),
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
                        "completed": len(episode_summaries),
                        "failed": len(failures),
                    }
                ),
                flush=True,
            )

    ambiguous_train = [
        {
            "input": [
                [9, 9, 9],
                [9, 9, 9],
                [9, 9, 9],
                [7, 7, 7],
                [7, 7, 7],
                [7, 7, 7],
            ],
            "output": [[3, 3, 3], [3, 3, 3], [3, 3, 3]],
        }
    ]
    ambiguity = {
        "purpose": "diagnostic only: intentionally missing occupancy states; never an emitted episode",
        "train": ambiguous_train,
        "identifiability": check_identifiability(ambiguous_train, bridge=bridge),
    }
    _write_json(out / "ambiguity.json", ambiguity)

    expected_ambiguous = [Parameters("and", 3).as_dict(), Parameters("or", 3).as_dict()]
    passed = (
        parity["passed"]
        and witness["all_settings_distinct"]
        and not failures
        and len(episode_summaries) == len(SETTINGS)
        and ambiguity["identifiability"]["survivors"] == expected_ambiguous
    )
    report = {
        "schema": VERSION + "-audit",
        "status": "prototype",
        "passed": passed,
        "task_id": TASK,
        "default": DEFAULT.as_dict(),
        "parameter_values": {
            "operation": ["xor", "and", "or"],
            "output_color": list(range(1, 10)),
        },
        "parameter_dependent_input_constraints": [],
        "input_contract": (
            "an even-height grid split into equal stacked halves; one distinct nonzero "
            "foreground color per half; all four aligned occupancy states"
        ),
        "seed_start": seed_start,
        "seed_search_end": max(seeds),
        "selected_seeds": seeds,
        "settings_requested": len(SETTINGS),
        "episodes_completed": len(episode_summaries),
        "demonstrations_per_episode": 3,
        "queries_per_episode": 1,
        "canonical_pairs_checked": parity["pairs_checked"],
        "distinct_witness_outputs": witness["distinct_outputs"],
        "rival_settings_per_episode": len(SETTINGS),
        "episodes": episode_summaries,
        "failures": failures,
        "sources": _sources(),
        "runtime": bridge.runtime_identity,
        "limitations": [
            "Proposed task-local prototype, not a production parametric API or approval.",
            "One seed-selected episode per setting; finite evidence, not all seeds or all valid inputs.",
            "Identifiability is relative to these 27 declared settings, not every possible ARC rule.",
            "Diagnostic ambiguity is retained and intentionally outside the full-state generation domain.",
            "Public and private JSONL rows align by order; disclose only the public file to a solver.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    episode_parser = subparsers.add_parser(
        "episode", help="generate one complete seed-selected episode"
    )
    episode_parser.add_argument("--seed", type=int, required=True)
    episode_parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    episode_parser.add_argument("--out", type=Path, required=True)

    audit_parser = subparsers.add_parser(
        "audit", help="materialize finite Racket evidence for all 27 settings"
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
    print(
        json.dumps(
            {
                "status": "prototype",
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
