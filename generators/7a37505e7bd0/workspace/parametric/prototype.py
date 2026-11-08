#!/usr/bin/env python3
"""Bounded task-local episode prototype; every label is executed in Racket.

This does not change the selected per-puzzle API or confer production approval.
The unchanged task sampler supplies all inputs. See README.md for the domain,
exact commands, the six hidden settings, and finite-evidence limitations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "7a37505e7bd0"
SCHEMA = "7a37505e7bd0-bounded-parametric-prototype-v1"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
CANONICAL_PARAMETERS = {"counting_policy": "all_colors", "expansion_axis": "both"}
ALL_PARAMETERS = tuple(
    {"counting_policy": policy, "expansion_axis": axis}
    for policy in ("all_colors", "nonzero_colors")
    for axis in ("both", "rows", "columns")
)
BANDS = ("easy", "medium", "hard")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha256(grid) -> str:
    return _sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _nonnegative_integer(value, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer, excluding booleans")
    return value


def validate_parameters(parameters) -> dict[str, str]:
    if type(parameters) is not dict or set(parameters) != {"counting_policy", "expansion_axis"}:
        raise ValueError("parameters must contain exactly counting_policy and expansion_axis")
    if type(parameters["counting_policy"]) is not str or parameters["counting_policy"] not in {"all_colors", "nonzero_colors"}:
        raise ValueError("counting_policy must be all_colors or nonzero_colors")
    if type(parameters["expansion_axis"]) is not str or parameters["expansion_axis"] not in {"both", "rows", "columns"}:
        raise ValueError("expansion_axis must be both, rows, or columns")
    return dict(parameters)


def setting_key(parameters) -> str:
    params = validate_parameters(parameters)
    return params["counting_policy"] + "__" + params["expansion_axis"]


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the complete setting once; no input index or global RNG enters it."""
    _nonnegative_integer(seed, "seed")
    digest = hashlib.sha256(f"{SCHEMA}:episode:{seed}".encode()).digest()
    return dict(ALL_PARAMETERS[int.from_bytes(digest, "big") % len(ALL_PARAMETERS)])


def canonical_rule(root=ROOT) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("selected task must have exactly one canonical Racket authority")
    return programs.pop()


def materialize_program(parameters, *, root=ROOT, canonical_code=None) -> str:
    """Emit executable rule! source, with the exact selected canonical default."""
    params = validate_parameters(parameters)
    if params == CANONICAL_PARAMETERS:
        return canonical_rule(root) if canonical_code is None else canonical_code
    colors = "(grid-colors g)"
    if params["counting_policy"] == "nonzero_colors":
        colors = "(filter (lambda (color) (not (= color 0))) (grid-colors g))"
    vertical = "n" if params["expansion_axis"] in {"both", "rows"} else "1"
    horizontal = "n" if params["expansion_axis"] in {"both", "columns"} else "1"
    return (
        "(rule! (lambda (g)\n"
        f"  (let* ((n (max 1 (length {colors})))\n"
        f"         (vertical {vertical})\n"
        f"         (horizontal {horizontal}))\n"
        "    (grid-from-fn (* (rows g) vertical) (* (cols g) horizontal)\n"
        "      (lambda (r c)\n"
        "        (cell-at g (quotient r vertical) (quotient c horizontal)))))))"
    )


def _source_manifest(root: Path, generator_source: Path) -> dict[str, str]:
    paths = {Path(__file__).resolve(), generator_source.resolve(), canonical_path(root).resolve()}
    paths.update(path.resolve() for path in HOME.rglob("*") if path.is_file() and path.suffix in {".py", ".rkt", ".md"})
    test_path = HOME.parents[1] / "tests" / f"test_parametric_{TASK_ID}.py"
    if test_path.is_file():
        paths.add(test_path.resolve())
    # Bind the actually loaded local generator support and wrapper dependencies.
    for name, module in tuple(sys.modules.items()):
        if name == "reviewer_support" or name.startswith("puzzle_generators."):
            source = getattr(module, "__file__", None)
            if source and Path(source).is_file() and Path(source).resolve().is_relative_to(root):
                paths.add(Path(source).resolve())
    return {str(path.relative_to(root)): _sha_bytes(path.read_bytes()) for path in sorted(paths)}


class RacketOracle:
    """One live bridge plus a cache of actual, retained Racket executions.

    Cache keys bind exact program bytes and exact input grids. Python never
    creates an output grid. A caller-owned bridge remains caller-owned.
    """

    def __init__(self, *, bridge=None, root=ROOT):
        self.root = Path(root).resolve()
        self.generator, self.generator_source, _ = load_selected_generator(TASK_ID, root=self.root)
        self.canonical_code = canonical_rule(self.root)
        self.programs = {
            setting_key(p): materialize_program(p, root=self.root, canonical_code=self.canonical_code)
            for p in ALL_PARAMETERS
        }
        self.bridge = bridge if bridge is not None else RacketBridge()
        self.owns_bridge = bridge is None
        self.runtime = self.bridge.runtime_identity
        self.sources = _source_manifest(self.root, self.generator_source)
        self.definitions: dict[str, dict[str, str]] = {}
        self.executions: list[dict[str, Any]] = []
        self.cache: dict[tuple[str, str], dict[str, Any]] = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.owns_bridge:
            self.bridge.shutdown()
        return False

    def program(self, parameters) -> str:
        return self.programs[setting_key(parameters)]

    def validate_input(self, grid):
        grid = normalize_grid(grid)
        errors = self.generator.self_check(grid)
        if errors:
            raise ValueError("prototype input outside original teaching domain: " + "; ".join(errors))
        return grid

    def execute_program(self, code: str, grid, *, purpose: str) -> list[list[int]]:
        grid = self.validate_input(grid)
        digest = _sha_bytes(code.encode())
        if digest not in self.definitions:
            # These six programs are closed lambda forms with no shorthand,
            # dict literals, comments, or free auto-bound h/w variables. Use
            # the shared exact wrapper stripper; generic wrap_rule requires
            # the staged scripts namespace that review.py run does not add.
            callable_code = strip_rule_wrapper(code)
            name = f"__parametric_rule_{len(self.definitions)}"
            expression = f"(define {name} {callable_code})"
            self.bridge.eval_text(expression)
            self.definitions[digest] = {
                "function": name,
                "code": code,
                "sha256": digest,
                "callable_code": callable_code,
                "callable_sha256": _sha_bytes(callable_code.encode()),
                "definition_expression": expression,
            }
        definition = self.definitions[digest]
        self.bridge.define_grid("__parametric_input", grid)
        expression = f"({definition['function']} __parametric_input)"
        output = normalize_grid(self.bridge.eval_text(expression))
        self.executions.append({
            "execution_id": len(self.executions),
            "backend": "racket",
            "purpose": purpose,
            "program_sha256": digest,
            "callable_sha256": definition["callable_sha256"],
            "input": grid,
            "input_sha256": grid_sha256(grid),
            "output": output,
            "output_sha256": grid_sha256(output),
            "expression": expression,
        })
        return copy.deepcopy(output)

    def label(self, grid, parameters) -> list[list[int]]:
        code = self.program(parameters)
        grid = self.validate_input(grid)
        key = (_sha_bytes(code.encode()), grid_sha256(grid))
        if key not in self.cache:
            self.execute_program(code, grid, purpose=setting_key(parameters))
            self.cache[key] = self.executions[-1]
        return copy.deepcopy(self.cache[key]["output"])

    def label_record(self, grid, parameters):
        self.label(grid, parameters)
        return copy.deepcopy(self.cache[(_sha_bytes(self.program(parameters).encode()), grid_sha256(grid))])

    def sources_unchanged(self) -> bool:
        return self.sources == _source_manifest(self.root, self.generator_source)


def score_parameters(pairs, parameters, oracle: RacketOracle, *, query_index: int):
    """Check all five rivals using real labels, distinguishing survival/ambiguity."""
    params = validate_parameters(parameters)
    if not isinstance(pairs, list) or len(pairs) < 2:
        raise ValueError("need at least one demonstration and one labeled query")
    if type(query_index) is not int or not 0 <= query_index < len(pairs):
        raise ValueError("query_index must select one real labeled pair")
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or set(pair) != {"input", "output"}:
            raise ValueError("pairs must contain exactly input and output")
        if pair["output"] != oracle.label(pair["input"], params):
            raise ValueError(f"pair {index} does not match the executed Racket label")
    demos = [index for index in range(len(pairs)) if index != query_index]
    rivals = []
    for rival in ALL_PARAMETERS:
        if rival == params:
            continue
        records = [oracle.label_record(pair["input"], rival) for pair in pairs]
        mismatches = [index for index in demos if records[index]["output"] != pairs[index]["output"]]
        query_equal = records[query_index]["output"] == pairs[query_index]["output"]
        status = "refuted" if mismatches else ("survived_all" if query_equal else "ambiguous")
        rivals.append({
            "parameters": dict(rival),
            "status": status,
            "demo_mismatch_indices": mismatches,
            "query_equal": query_equal,
            "execution_ids": [record["execution_id"] for record in records],
            "output_sha256": [record["output_sha256"] for record in records],
        })
    return {
        "query_index": query_index,
        "demo_indices": demos,
        "identified": all(row["status"] == "refuted" for row in rivals),
        "measured_ambiguity": any(row["status"] == "ambiguous" for row in rivals),
        "rivals": rivals,
    }


def generate_episode(seed: int, *, difficulty="medium", sample_start=0, parameters=None, oracle=None):
    """Five demonstrations and one query share one setting and base input seed."""
    _nonnegative_integer(seed, "seed")
    _nonnegative_integer(sample_start, "sample_start")
    if difficulty not in BANDS:
        raise ValueError("difficulty must be easy, medium, or hard")
    params = choose_parameters(seed) if parameters is None else validate_parameters(parameters)
    if oracle is None:
        with RacketOracle() as runner:
            return generate_episode(seed, difficulty=difficulty, sample_start=sample_start,
                                    parameters=parameters, oracle=runner)
    pairs, sampling = [], []
    for offset in range(6):
        sample_index = sample_start + offset
        grid = oracle.generator.generate(seed, sample_index, difficulty=difficulty)
        record = oracle.label_record(grid, params)
        pairs.append({"input": grid, "output": record["output"]})
        sampling.append({
            "sample_index": sample_index,
            "input_sha256": record["input_sha256"],
            "racket_execution_id": record["execution_id"],
            "base_observables": oracle.generator.semantic_observables(grid),
        })
    score = score_parameters(pairs, params, oracle, query_index=5)
    if not score["identified"]:
        raise ValueError("complete prototype demonstrations do not distinguish all parameter settings")
    code = oracle.program(params)
    callable_code = strip_rule_wrapper(code)
    return {
        "schema": SCHEMA,
        "status": "prototype",
        "task_id": TASK_ID,
        "episode_seed": seed,
        "input_seed": seed,
        "sample_start": sample_start,
        "difficulty": difficulty,
        "parameters": params,
        "parameter_selection": "seeded" if parameters is None else "explicit",
        "parameter_seed_material": f"{SCHEMA}:episode:{seed}",
        "program": {"code": code, "sha256": _sha_bytes(code.encode()),
                    "callable_code": callable_code, "callable_sha256": _sha_bytes(callable_code.encode())},
        "sources": copy.deepcopy(oracle.sources),
        "runtime": copy.deepcopy(oracle.runtime),
        "train": pairs[:5],
        "test": pairs[5:],
        "sampling": sampling,
        "parameter_check": score,
    }


def public_challenge(episode):
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def save_episode(episode, out: Path, episode_id: str):
    if not episode_id.startswith("episode-") or not episode_id[8:].isdigit():
        raise ValueError("episode_id must be a private episode-NNNN identifier")
    out = Path(out)
    challenge = public_challenge(episode)
    public_bytes = (json.dumps(challenge, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    public_digest = _sha_bytes(public_bytes)
    paths = {
        "public": out / "public" / f"challenge-{public_digest}.json",
        "private": out / "private" / "episodes" / f"{episode_id}.episode.json",
        "receipt": out / "private" / "episodes" / f"{episode_id}.receipt.json",
    }
    if any(paths[key].exists() for key in ("private", "receipt")):
        raise FileExistsError("private episode output already exists; use a fresh private episode ID")
    if paths["public"].exists():
        if paths["public"].read_bytes() != public_bytes:
            raise ValueError("existing content-addressed public file does not match its expected bytes")
    else:
        paths["public"].parent.mkdir(parents=True, exist_ok=True)
        paths["public"].write_bytes(public_bytes)
    _write_json(paths["private"], episode)
    receipt = {key: copy.deepcopy(episode[key]) for key in (
        "schema", "status", "task_id", "episode_seed", "input_seed", "sample_start", "difficulty",
        "parameters", "parameter_selection", "parameter_seed_material", "program", "sources", "runtime", "sampling",
    )}
    receipt.update({
        "episode_id": episode_id,
        "label_backend": "racket",
        "racket_outputs": [copy.deepcopy(p["output"]) for p in episode["train"] + episode["test"]],
        "public_sha256": public_digest,
        "public_path": str(paths["public"].relative_to(out)),
        "private_sha256": _sha_bytes(paths["private"].read_bytes()),
    })
    _write_json(paths["receipt"], receipt)
    return {key: str(path) for key, path in paths.items()}


def ambiguity_control(oracle: RacketOracle):
    """Remove zero witnesses from lawful demos; retain a zero-containing query."""
    seed = 17
    # Counts 3,5,1,3,5 in demos; count 4 (including zero) in the query.
    indices = [0, 2, 3, 5, 7, 1]
    pairs = []
    for index in indices:
        grid = oracle.generator.generate(seed, index, difficulty="medium")
        pairs.append({"input": grid, "output": oracle.label(grid, CANONICAL_PARAMETERS)})
    return {
        "kind": "deliberately_incomplete_demonstration_control",
        "parameters": dict(CANONICAL_PARAMETERS),
        "seed": seed,
        "difficulty": "medium",
        "sample_indices": indices,
        "pairs": pairs,
        "score": score_parameters(pairs, CANONICAL_PARAMETERS, oracle, query_index=5),
        "solver_attempts": 0,
        "interpretation": "Lawful inputs with Racket labels. No zero in demos; a zero query separates counting policies. This is not an emitted complete episode or a solver attempt.",
    }


def build_evidence(out: Path, *, seeds=(0, 1, 2, 17), bands=BANDS, starts=(0, 3)):
    out = Path(out).resolve()
    for values, name in ((seeds, "seeds"), (bands, "bands"), (starts, "starts")):
        if not values or len(set(values)) != len(values):
            raise ValueError(f"{name} must be nonempty without duplicates")
    for seed in seeds:
        _nonnegative_integer(seed, "seed")
    for start in starts:
        _nonnegative_integer(start, "sample_start")
    if any(band not in BANDS for band in bands):
        raise ValueError("unsupported difficulty band")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("evidence output must be a new or empty directory")
    out.mkdir(parents=True, exist_ok=True)
    with RacketOracle() as oracle:
        programs = []
        for parameters in ALL_PARAMETERS:
            key = setting_key(parameters)
            code = oracle.program(parameters)
            path = out / "private" / "rules" / f"{key}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
            programs.append({"parameters": dict(parameters), "code": code,
                             "sha256": _sha_bytes(code.encode()), "path": str(path.relative_to(out))})
        lessons, rotations = [], []
        for band in bands:
            for seed in seeds:
                for start in starts:
                    for parameters in ALL_PARAMETERS:
                        episode_id = f"episode-{len(lessons):04d}"
                        episode = generate_episode(seed, difficulty=band, sample_start=start,
                                                   parameters=parameters, oracle=oracle)
                        paths = save_episode(episode, out, episode_id)
                        lessons.append({"episode_id": episode_id, "parameters": dict(parameters),
                                        "seed": seed, "sample_start": start, "difficulty": band,
                                        "paths": {key: str(Path(path).relative_to(out)) for key, path in paths.items()},
                                        "score": episode["parameter_check"]})
                        pairs = episode["train"] + episode["test"]
                        for query_index in range(6):
                            rotations.append({"episode_id": episode_id, "parameters": dict(parameters),
                                              **score_parameters(pairs, parameters, oracle, query_index=query_index)})
        canonical = []
        for pair in canonical_pairs(TASK_ID, root=oracle.root):
            candidate = oracle.label(pair["input"], CANONICAL_PARAMETERS)
            authority = oracle.execute_program(oracle.canonical_code, pair["input"], purpose="canonical_reference")
            canonical.append({**pair, "prototype_output": candidate, "authority_output": authority,
                              "matches": candidate == authority == pair["output"]})
        witness_input = oracle.generator.generate(17, 1, difficulty="medium")
        witness_outputs = [{"parameters": dict(p), "program_sha256": _sha_bytes(oracle.program(p).encode()),
                            "output": oracle.label(witness_input, p)} for p in ALL_PARAMETERS]
        witness = {"seed": 17, "sample_index": 1, "difficulty": "medium", "input": witness_input,
                   "input_sha256": grid_sha256(witness_input), "self_check_errors": oracle.generator.self_check(witness_input),
                   "outputs": witness_outputs,
                   "distinct_output_count": len({grid_sha256(row["output"]) for row in witness_outputs})}
        control = ambiguity_control(oracle)
        _write_json(out / "private" / "query-rotations.json", rotations)
        _write_json(out / "private" / "canonical-checks.json", {"authority_code": oracle.canonical_code,
                    "authority_sha256": _sha_bytes(oracle.canonical_code.encode()), "pairs": canonical})
        _write_json(out / "private" / "difference-witness.json", witness)
        _write_json(out / "private" / "ambiguity-negative-control.json", control)
        _write_json(out / "private" / "racket-definitions.json", list(oracle.definitions.values()))
        (out / "private" / "racket-executions.jsonl").write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in oracle.executions), encoding="utf-8")
        summary = {
            "settings": len(ALL_PARAMETERS),
            "episodes": len(lessons),
            "unique_public_challenges": len({row["paths"]["public"] for row in lessons}),
            "labeled_pairs": len(lessons) * 6,
            "production_identified": sum(row["score"]["identified"] for row in lessons),
            "production_ambiguous": sum(row["score"]["measured_ambiguity"] for row in lessons),
            "rotations": len(rotations),
            "rotations_identified": sum(row["identified"] for row in rotations),
            "rotations_ambiguous": sum(row["measured_ambiguity"] for row in rotations),
            "canonical_pairs": len(canonical),
            "canonical_matches": sum(row["matches"] for row in canonical),
            "witness_distinct_outputs": witness["distinct_output_count"],
            "negative_controls": 1,
            "negative_controls_ambiguous": int(control["score"]["measured_ambiguity"]),
            "solver_attempts": 0,
        }
        unchanged = oracle.sources_unchanged()
        passed = (unchanged and summary["production_identified"] == len(lessons)
                  and summary["rotations_identified"] == len(rotations)
                  and summary["canonical_matches"] == len(canonical) == 8
                  and summary["witness_distinct_outputs"] == 6
                  and summary["negative_controls_ambiguous"] == 1)
        report = {
            "schema": SCHEMA,
            "status": "prototype_bounded_checks_passed" if passed else "prototype_bounded_checks_failed",
            "canonical_parameters": dict(CANONICAL_PARAMETERS),
            "settings": programs,
            "seeds": list(seeds), "bands": list(bands), "sample_starts": list(starts),
            "seed_selection_examples": [{"seed": seed, "parameters": choose_parameters(seed)} for seed in seeds],
            "sources": oracle.sources, "sources_unchanged": unchanged,
            "runtime": oracle.runtime,
            "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
            "summary": summary,
            "episodes": lessons,
            "public_export": {
                "filename_policy": "challenge-<full SHA-256 of exact canonical public JSON bytes>.json",
                "canonical_bytes": "UTF-8, sorted object keys, compact separators, unescaped Unicode, one trailing newline",
                "identical_public_payloads_share_file": True,
                "challenge_visible": "Only public JSON bodies and their content-addressed filenames",
                "private_order": "Numeric private episode IDs, report mappings, parameter order and iteration order are not challenge-visible",
            },
            "actual_racket_executions": len(oracle.executions),
            "actual_racket_definitions": len(oracle.definitions),
            "cache_policy": "Each (exact program SHA-256, exact input SHA-256) is executed once; rotations reuse retained real labels. Canonical authority comparisons additionally execute the reference separately.",
            "limitations": [
                "Task-local proposed prototype; selected fixed-rule production generation and approval are unchanged.",
                "Finite declared-rival evidence across the reported settings, seeds, bands and starts; no proof of all seeds or all plausible human interpretations.",
                "Five alternatives are compared for each chosen setting; production generator rivals are not redefined for variant rules.",
                "Input domain is the selected generator's lawful 3x3 teaching profile with 1..5 colors, including its canonical exceptions. All-zero inputs are excluded.",
                "The scale factor is max(1, distinct colors under the counting policy); lawful inputs contain at least one nonzero color.",
                "Negative control deliberately removes zero-containing demonstrations and is not a generated complete episode or solver evidence.",
                "Private files include all labels, parameters, executable reference source and matrix ordering. Only public/*.json bodies and their content-addressed filenames are challenge-visible.",
            ],
        }
        report["artifact_sha256"] = {str(path.relative_to(out)): _sha_bytes(path.read_bytes())
                                     for path in sorted(out.rglob("*")) if path.is_file()}
        _write_json(out / "report.json", report)
        return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materialize = sub.add_parser("materialize", help="write all six executable rule! programs")
    materialize.add_argument("--out", type=Path, required=True)
    episode = sub.add_parser("episode", help="write one public challenge and private episode/receipt")
    episode.add_argument("--out", type=Path, required=True)
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--sample-start", type=int, default=0)
    episode.add_argument("--difficulty", choices=BANDS, default="medium")
    episode.add_argument("--counting-policy", choices=("all_colors", "nonzero_colors"))
    episode.add_argument("--expansion-axis", choices=("both", "rows", "columns"))
    evidence = sub.add_parser("evidence", help="execute complete bounded evidence including controls")
    evidence.add_argument("--out", type=Path, required=True)
    evidence.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 17])
    evidence.add_argument("--bands", choices=BANDS, nargs="+", default=list(BANDS))
    evidence.add_argument("--starts", type=int, nargs="+", default=[0, 3])
    args = parser.parse_args(argv)
    if args.command == "materialize":
        args.out.mkdir(parents=True, exist_ok=True)
        for parameters in ALL_PARAMETERS:
            (args.out / f"{setting_key(parameters)}.rkt").write_text(materialize_program(parameters), encoding="utf-8")
        print(json.dumps({"status": "materialized", "programs": 6, "out": str(args.out)}))
        return 0
    if args.command == "episode":
        if bool(args.counting_policy) != bool(args.expansion_axis):
            parser.error("provide both explicit parameters or neither for deterministic seed selection")
        parameters = None if args.counting_policy is None else {
            "counting_policy": args.counting_policy, "expansion_axis": args.expansion_axis}
        with RacketOracle() as oracle:
            value = generate_episode(args.seed, difficulty=args.difficulty, sample_start=args.sample_start,
                                     parameters=parameters, oracle=oracle)
            paths = save_episode(value, args.out, "episode-0000")
            _write_json(args.out / "private" / "racket-definitions.json", list(oracle.definitions.values()))
            _write_json(args.out / "private" / "racket-executions.json", oracle.executions)
            if not oracle.sources_unchanged():
                raise RuntimeError("source changed during episode execution")
        print(json.dumps({"status": "prototype_episode_written", "paths": paths}))
        return 0
    report = build_evidence(args.out, seeds=tuple(args.seeds), bands=tuple(args.bands), starts=tuple(args.starts))
    print(json.dumps({"status": report["status"], "summary": report["summary"],
                      "actual_racket_executions": report["actual_racket_executions"],
                      "report": str(args.out / "report.json")}, indent=2))
    return 0 if report["status"] == "prototype_bounded_checks_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
