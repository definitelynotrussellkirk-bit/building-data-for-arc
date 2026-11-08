#!/usr/bin/env python3
"""Task-local candidate-rank parameter prototype for 537b409b6744.

The selected production generator and canonical authority remain unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path


TASK_ID = "537b409b6744"
PARAMETER_SPEC = {
    "name": "candidate_rank",
    "values": ("nearest", "farthest"),
    "default": "nearest",
}

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
RULE_DIR = HERE.parent / "rules"
CANONICAL_LEDGER = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

_NEAREST_RANK_COMPARATOR = """             (lambda (a b) (cond ((< (first a) (first b)) #t)
                                 ((> (first a) (first b)) #f)
                                 (else (> (second a) (second b)))))))
"""
_FARTHEST_RANK_COMPARATOR = """             (lambda (a b) (cond ((> (first a) (first b)) #t)
                                 ((< (first a) (first b)) #f)
                                 (else (> (second a) (second b)))))))
"""
_NEAREST_RULE_COMMENT = "nearest such pair wins"
_FARTHEST_RULE_COMMENT = "farthest such pair wins"


def _validate_candidate_rank(candidate_rank: str) -> str:
    if candidate_rank not in PARAMETER_SPEC["values"]:
        raise ValueError(
            "candidate_rank must be one of "
            f"{PARAMETER_SPEC['values']}, got {candidate_rank!r}"
        )
    return candidate_rank


def choose_candidate_rank(seed: int) -> str:
    """Choose one hidden rank policy deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return PARAMETER_SPEC["values"][seed % len(PARAMETER_SPEC["values"])]


def canonical_rule() -> str:
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                return source
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def expected_farthest_rule(canonical_source: str | None = None) -> str:
    """Derive the only accepted alternative by reversing the primary gap order."""
    source = canonical_rule() if canonical_source is None else canonical_source
    if source.count(_NEAREST_RANK_COMPARATOR) != 1:
        raise RuntimeError("canonical rule does not contain the expected rank comparator")
    if source.count(_NEAREST_RULE_COMMENT) != 1:
        raise RuntimeError("canonical rule does not contain the expected rank comment")
    return source.replace(
        _NEAREST_RANK_COMPARATOR,
        _FARTHEST_RANK_COMPARATOR,
        1,
    ).replace(
        _NEAREST_RULE_COMMENT,
        _FARTHEST_RULE_COMMENT,
        1,
    )


def materialize_rule(candidate_rank: str) -> str:
    rank = _validate_candidate_rank(candidate_rank)
    path = RULE_DIR / f"{rank}.rkt"
    if not path.is_file():
        raise FileNotFoundError(f"missing prototype rule source: {path}")
    source = path.read_text(encoding="utf-8")
    expected = canonical_rule() if rank == "nearest" else expected_farthest_rule()
    if source != expected:
        raise RuntimeError(
            f"{rank} prototype rule does not match its exact declared program"
        )
    return source


def _load_module(path: Path, name: str):
    import importlib.util
    import sys

    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_generator():
    return _load_module(
        ROOT / "generators" / TASK_ID / "generator.py",
        f"parametric_candidate_rank_{TASK_ID}_generator",
    )


def _load_reference_probe():
    return _load_module(
        ROOT / "generators" / TASK_ID / "workspace" / "reference_probe.py",
        f"parametric_candidate_rank_{TASK_ID}_reference_probe",
    )


def apply_python(grid: list[list[int]], candidate_rank: str) -> list[list[int]]:
    """Apply either setting through the task's independent geometry oracle."""
    rank = _validate_candidate_rank(candidate_rank)
    probe = _load_reference_probe()
    if rank == "nearest":
        return probe.rule_output(grid)
    candidates = probe.ranked_candidates(grid)
    if not candidates:
        return [list(row) for row in grid]
    farthest_gap = candidates[-1]["gap"]
    selected = next(
        candidate for candidate in candidates if candidate["gap"] == farthest_gap
    )
    return probe.apply_candidate(grid, selected)


def _validate_count(name: str, value: int, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        qualifier = "positive" if minimum == 1 else f">= {minimum}"
        raise ValueError(f"{name} must be a {qualifier} integer (not bool)")
    return value


def build_episode(
    *,
    seed: int,
    candidate_rank: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
    labeler=None,
) -> dict:
    """Build one complete episode with a single fixed hidden rank policy."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    _validate_count("start_index", start_index, minimum=0)
    _validate_count("n_train", n_train, minimum=1)
    _validate_count("n_test", n_test, minimum=1)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")

    rank = (
        choose_candidate_rank(seed)
        if candidate_rank is None
        else _validate_candidate_rank(candidate_rank)
    )
    generator = _load_generator()
    label = apply_python if labeler is None else labeler
    sample_indices = list(range(start_index, start_index + n_train + n_test))
    pairs = []
    for sample_index in sample_indices:
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": label(grid, rank)})

    input_digests = [_grid_sha256(pair["input"]) for pair in pairs]
    if len(input_digests) != len(set(input_digests)):
        raise RuntimeError("episode inputs must be distinct across demonstrations and queries")
    rival = next(value for value in PARAMETER_SPEC["values"] if value != rank)
    nonidentifying = [
        index
        for index, pair in enumerate(pairs)
        if apply_python(pair["input"], rival) == pair["output"]
    ]
    if nonidentifying:
        raise RuntimeError(
            "episode input does not distinguish candidate_rank="
            f"{rank!r} from {rival!r}: pair indices {nonidentifying}"
        )

    return {
        "schema": "537b409b6744-candidate-rank-episode-v1",
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "parameters": {PARAMETER_SPEC["name"]: rank},
            "parameter_scope": "chosen once per episode",
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "sample_indices": sample_indices,
            "input_generator_version": generator.VERSION,
        },
    }


def _episode_rank(episode: dict) -> str:
    meta = episode.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("episode is missing metadata")
    parameters = meta.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode is missing parameter metadata")
    return _validate_candidate_rank(parameters.get(PARAMETER_SPEC["name"]))


def _all_pairs(episode: dict) -> list[dict]:
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return [*train, *test]


def parameter_rival_findings(episode: dict) -> list[str]:
    """Report whether the alternate setting still fits every demonstration."""
    try:
        chosen = _episode_rank(episode)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    demos = episode.get("train")
    if not isinstance(demos, list) or not demos:
        return ["episode needs at least one demonstration"]
    rival = next(value for value in PARAMETER_SPEC["values"] if value != chosen)
    malformed = []
    rival_fits = True
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            malformed.append(f"demo {index} is malformed")
            rival_fits = False
            continue
        if apply_python(pair["input"], rival) != pair["output"]:
            rival_fits = False
    if malformed:
        return malformed
    if rival_fits:
        return [
            f"demonstrations do not distinguish candidate_rank={chosen!r} "
            f"from {rival!r}"
        ]
    return []


def _public_helpers():
    from reviewer_support import public_challenge_bytes, public_challenge_id

    return public_challenge_bytes, public_challenge_id


def public_challenge(episode: dict) -> dict[str, list[dict]]:
    """Strip private state and return the exact validated visible projection."""
    public_challenge_bytes, _ = _public_helpers()
    return json.loads(public_challenge_bytes(episode))


def public_filename(challenge: dict) -> str:
    """Name a public challenge only from its exact visible bytes."""
    _, public_challenge_id = _public_helpers()
    return f"challenge-{public_challenge_id(challenge)}.json"


def sorted_unique_public_records(records: list[dict]) -> list[dict]:
    """Sort a batch by visible ID and reject duplicate visible payloads."""
    if not isinstance(records, list):
        raise ValueError("public records must be a list")
    seen: set[str] = set()
    for record in records:
        public_id = record.get("public_id") if isinstance(record, dict) else None
        if not isinstance(public_id, str) or not public_id:
            raise ValueError("public record is missing a visible public challenge ID")
        if public_id in seen:
            raise ValueError(f"duplicate visible public challenge ID: {public_id}")
        seen.add(public_id)
    return sorted(records, key=lambda record: record["public_id"])


def verify_public_challenge(challenge: dict) -> list[str]:
    """Return privacy/shape findings for an answer-masked public artifact."""
    if not isinstance(challenge, dict):
        return ["public challenge must be an object"]
    findings: list[str] = []
    forbidden = sorted(set(challenge) - {"train", "test"})
    if forbidden:
        findings.append(f"public challenge has forbidden top-level keys: {forbidden}")
    train = challenge.get("train")
    test = challenge.get("test")
    if not isinstance(train, list):
        findings.append("public challenge train must be a list")
        train = []
    if not isinstance(test, list):
        findings.append("public challenge test must be a list")
        test = []
    if len(train) < 1:
        findings.append("public challenge needs at least one training pair")
    if len(test) < 1:
        findings.append("public challenge needs at least one test pair")
    for index, pair in enumerate(train):
        if not isinstance(pair, dict):
            findings.append(f"train pair {index} must be an object")
        elif set(pair) != {"input", "output"}:
            findings.append(
                f"train pair {index} must contain exactly input and output"
            )
    for index, pair in enumerate(test):
        if not isinstance(pair, dict):
            findings.append(f"test pair {index} must be an object")
            continue
        if "output" in pair:
            findings.append(f"test pair {index} exposes an output")
        if set(pair) != {"input"}:
            findings.append(f"test pair {index} must contain only input")
    public_challenge_bytes, _ = _public_helpers()
    try:
        public_challenge_bytes(challenge)
    except ValueError as exc:
        findings.append(f"invalid public payload: {exc}")
    return findings


def _sha256_bytes(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_text(json.dumps(grid, separators=(",", ":")))


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _racket_runtime():
    import sys
    import types

    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared" / "tools")]
    sys.modules.setdefault("scripts", scripts)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    return RacketBridge, wrap_rule


def _execute_racket(bridge, wrap_rule, source: str, grid: list[list[int]]) -> list[list[int]]:
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    output = bridge.eval_text(expression)
    if not isinstance(output, list) or not output or not isinstance(output[0], list):
        raise RuntimeError(f"prototype rule returned non-grid output: {output!r}")
    return [[int(value) for value in row] for row in output]


def apply_racket(grid: list[list[int]], candidate_rank: str) -> list[list[int]]:
    """Execute one materialized setting through the pinned Racket runtime."""
    source = materialize_rule(candidate_rank)
    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=8) as bridge:
        return _execute_racket(bridge, wrap_rule, source, grid)


def _rotation_record(episode: dict, query_index: int) -> dict:
    pairs = _all_pairs(episode)
    chosen = _episode_rank(episode)
    rival = next(value for value in PARAMETER_SPEC["values"] if value != chosen)
    demo_indices = [index for index in range(len(pairs)) if index != query_index]
    refuting = [
        index
        for index in demo_indices
        if apply_python(pairs[index]["input"], rival) != pairs[index]["output"]
    ]
    return {
        "query_index": query_index,
        "demonstration_indices": demo_indices,
        "refuting_demo_indices": refuting,
        "identifiable": bool(refuting),
        "rival_changes_query": (
            apply_python(pairs[query_index]["input"], rival)
            != pairs[query_index]["output"]
        ),
    }


def _production_query_records(episode: dict) -> list[dict]:
    chosen = _episode_rank(episode)
    rival = next(value for value in PARAMETER_SPEC["values"] if value != chosen)
    demos = episode["train"]
    refuting_demo_indices = [
        index
        for index, pair in enumerate(demos)
        if apply_python(pair["input"], rival) != pair["output"]
    ]
    records = []
    for index, pair in enumerate(episode["test"]):
        records.append(
            {
                "query_index": index,
                "refuting_demo_indices": refuting_demo_indices,
                "identifiable": bool(refuting_demo_indices),
                "rival_changes_query": (
                    apply_python(pair["input"], rival) != pair["output"]
                ),
            }
        )
    return records


def build_evidence(
    *,
    seeds: list[int],
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
) -> dict:
    """Execute both settings and return bounded, source-bound prototype evidence."""
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("seeds must be a nonempty list")
    _validate_count("start_index", start_index, minimum=0)
    _validate_count("n_train", n_train, minimum=1)
    _validate_count("n_test", n_test, minimum=1)
    if n_test < 4:
        raise ValueError("bounded evidence requires at least four query inputs")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    if any(type(seed) is not int for seed in seeds):
        raise TypeError("every seed must be an integer (not bool)")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    selected_settings = {choose_candidate_rank(seed) for seed in seeds}
    if selected_settings != set(PARAMETER_SPEC["values"]):
        raise ValueError("seeds must demonstrate both candidate_rank settings")

    from reviewer_support import canonical_pairs

    generator = _load_generator()
    programs = {
        rank: materialize_rule(rank) for rank in PARAMETER_SPEC["values"]
    }
    default_program_byte_identical = programs["nearest"] == canonical_rule()
    canonical_checks: list[dict] = []
    episodes: list[dict] = []
    parity_results: list[bool] = []
    production_records: list[dict] = []
    query_records: list[dict] = []
    rotation_records: list[dict] = []
    public_records: list[dict] = []
    racket_label_executions = 0

    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            actual = _execute_racket(
                bridge, wrap_rule, programs["nearest"], pair["input"]
            )
            canonical_checks.append(
                {
                    "variant": pair.get("variant"),
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "input_sha256": _grid_sha256(pair["input"]),
                    "expected_sha256": _grid_sha256(pair["output"]),
                    "actual_sha256": _grid_sha256(actual),
                    "passed": actual == pair["output"],
                }
            )

        for seed in seeds:
            rank = choose_candidate_rank(seed)

            def racket_labeler(grid: list[list[int]], selected: str) -> list[list[int]]:
                nonlocal racket_label_executions
                racket_label_executions += 1
                return _execute_racket(
                    bridge, wrap_rule, programs[selected], grid
                )

            episode = build_episode(
                seed=seed,
                candidate_rank=rank,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                labeler=racket_labeler,
            )
            pairs = _all_pairs(episode)
            pair_checks = []
            for index, pair in enumerate(pairs):
                python_output = apply_python(pair["input"], rank)
                parity = python_output == pair["output"]
                parity_results.append(parity)
                pair_checks.append(
                    {
                        "pair_index": index,
                        "input_sha256": _grid_sha256(pair["input"]),
                        "racket_output_sha256": _grid_sha256(pair["output"]),
                        "python_output_sha256": _grid_sha256(python_output),
                        "python_parity": parity,
                    }
                )
            findings = parameter_rival_findings(episode)
            production = {
                "identifiable": not findings,
                "refuting_demo_count": sum(
                    apply_python(pair["input"], "farthest" if rank == "nearest" else "nearest")
                    != pair["output"]
                    for pair in episode["train"]
                ),
            }
            production_records.append(production)
            production_queries = _production_query_records(episode)
            query_records.extend(production_queries)
            rotations = [
                _rotation_record(episode, index) for index in range(len(pairs))
            ]
            rotation_records.extend(rotations)
            public = public_challenge(episode)
            _, public_challenge_id = _public_helpers()
            public_id = public_challenge_id(public)
            public_findings = verify_public_challenge(public)
            public_records.append(
                {
                    "public_id": public_id,
                    "challenge": public,
                    "findings": public_findings,
                    "passed": not public_findings,
                }
            )
            episodes.append(
                {
                    "public_id": public_id,
                    "public_filename": public_filename(public),
                    "seed": seed,
                    "parameters": {"candidate_rank": rank},
                    "episode": episode,
                    "pair_checks": pair_checks,
                    "parameter_rival_findings": findings,
                    "production_identifiability": production,
                    "query_records": production_queries,
                    "rotations": rotations,
                    "public_verifier_findings": public_findings,
                }
            )

        episodes = sorted_unique_public_records(episodes)
        public_records = sorted_unique_public_records(public_records)
        witness_grid = episodes[0]["episode"]["train"][0]["input"]
        witness_outputs = {
            rank: _execute_racket(bridge, wrap_rule, source, witness_grid)
            for rank, source in programs.items()
        }

    nearest_output = witness_outputs["nearest"]
    farthest_output = witness_outputs["farthest"]
    different_cells = [
        {"row": row, "column": column}
        for row in range(len(nearest_output))
        for column in range(len(nearest_output[row]))
        if nearest_output[row][column] != farthest_output[row][column]
    ]
    witness = {
        "input": witness_grid,
        "input_sha256": _grid_sha256(witness_grid),
        "outputs": witness_outputs,
        "output_sha256": {
            rank: _grid_sha256(output)
            for rank, output in witness_outputs.items()
        },
        "different_cell_count": len(different_cells),
        "first_differing_cells": different_cells[:20],
    }

    counts = {
        "settings_materialized": len(programs),
        "episodes": len(episodes),
        "distinct_settings_demonstrated": len(selected_settings),
        "canonical_pairs": len(canonical_checks),
        "canonical_passed": sum(row["passed"] for row in canonical_checks),
        "racket_label_executions": racket_label_executions,
        "python_parity_passed": sum(parity_results),
        "production_lessons": len(production_records),
        "production_identifiable": sum(row["identifiable"] for row in production_records),
        "query_pairs": len(query_records),
        "queries_changed_by_rival": sum(row["rival_changes_query"] for row in query_records),
        "query_rotations": len(rotation_records),
        "rotations_identifiable": sum(row["identifiable"] for row in rotation_records),
        "public_challenges": len(public_records),
        "public_verifier_passed": sum(row["passed"] for row in public_records),
    }
    all_findings = [
        finding
        for record in episodes
        for finding in record["parameter_rival_findings"]
    ]
    passed = bool(
        default_program_byte_identical
        and counts["canonical_passed"] == counts["canonical_pairs"] == 8
        and counts["python_parity_passed"] == counts["racket_label_executions"]
        and counts["production_identifiable"] == counts["production_lessons"]
        and counts["queries_changed_by_rival"] == counts["query_pairs"]
        and counts["rotations_identifiable"] == counts["query_rotations"]
        and counts["public_verifier_passed"] == counts["public_challenges"]
        and not all_findings
        and witness["different_cell_count"] > 0
    )

    return {
        "schema": "537b409b6744-candidate-rank-evidence-v1",
        "task_id": TASK_ID,
        "status": "proposed",
        "completion_state": "complete" if passed else "blocked",
        "passed": passed,
        "parameter_contract": {
            **PARAMETER_SPEC,
            "scope": "chosen once per episode",
            "canonical_setting": "nearest",
            "input_constraints": [
                "lawful selected-generator scenes with at least two qualifying candidates",
                "nearest and farthest settings produce different outputs",
            ],
            "invariant_reasoning": [
                "identify the modal background and same-color connected objects",
                "enumerate mover/wall pairs satisfying facing and span constraints",
                "rank candidates by gap according to the episode parameter",
                "move the selected mover through the wall, cut its channel, and widen the wall",
            ],
        },
        "canonical_authority_changed": False,
        "default_program_byte_identical": default_program_byte_identical,
        "programs": {
            rank: {
                "path": str((RULE_DIR / f"{rank}.rkt").relative_to(ROOT)),
                "sha256": _sha256_text(source),
                "text": source,
            }
            for rank, source in programs.items()
        },
        "sources": {
            "prototype": {
                "path": str(HERE.relative_to(ROOT)),
                "sha256": _sha256_bytes(HERE.read_bytes()),
            },
            "selected_generator": {
                "path": str((ROOT / "generators" / TASK_ID / "generator.py").relative_to(ROOT)),
                "sha256": _sha256_bytes(
                    (ROOT / "generators" / TASK_ID / "generator.py").read_bytes()
                ),
                "version": generator.VERSION,
                "rule_hash": generator.RULE_HASH,
            },
            "reference_probe": {
                "path": str(
                    (ROOT / "generators" / TASK_ID / "workspace" / "reference_probe.py").relative_to(ROOT)
                ),
                "sha256": _sha256_bytes(
                    (ROOT / "generators" / TASK_ID / "workspace" / "reference_probe.py").read_bytes()
                ),
            },
            "canonical_ledger": {
                "path": str(CANONICAL_LEDGER.relative_to(ROOT)),
                "sha256": _sha256_bytes(CANONICAL_LEDGER.read_bytes()),
            },
        },
        "replay": {
            "seeds": seeds,
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
        },
        "canonical_checks": canonical_checks,
        "episodes": episodes,
        "setting_difference_witness": witness,
        "counts": counts,
        "limitations": [
            "This is a task-local prototype, not a production parametric API or approval.",
            "Evidence covers only the retained seeds, generated inputs, and two rank settings.",
            "The farthest setting changes only candidate selection; component extraction and the move/cut/grow transformation stay fixed.",
            "Rival checks cover nearest versus farthest, not every possible candidate-ranking policy.",
        ],
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    *,
    out_dir: Path,
    public_dir: Path,
    seeds: list[int],
    difficulty: str,
    start_index: int,
    n_train: int,
    n_test: int,
) -> dict:
    """Write private evidence and answer-masked public challenges."""
    out_dir = out_dir.resolve()
    public_dir = public_dir.resolve()
    if (
        out_dir == public_dir
        or out_dir.is_relative_to(public_dir)
        or public_dir.is_relative_to(out_dir)
    ):
        raise ValueError("private and public evidence directories must not overlap")
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out_dir}")
    if public_dir.exists() and any(public_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite nonempty public directory: {public_dir}"
        )

    # Validate and execute the full bounded run before creating any new output
    # tree, so a rejected request does not leave replay-blocking empty paths.
    report = build_evidence(
        seeds=seeds,
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
    )
    out_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "report.json", report)
    _write_json(
        out_dir / "setting-difference-witness.json",
        report["setting_difference_witness"],
    )
    public_challenge_bytes, public_challenge_id = _public_helpers()
    for ordinal, record in enumerate(report["episodes"], start=1):
        rank = record["parameters"]["candidate_rank"]
        _write_json(out_dir / f"episode-{ordinal:02d}-{rank}.json", record)
        public = public_challenge(record["episode"])
        if public_challenge_id(public) != record["public_id"]:
            raise RuntimeError("public challenge identity changed after evidence build")
        public_path = public_dir / record["public_filename"]
        public_path.write_bytes(public_challenge_bytes(public))
    manifest = {
        "schema": "537b409b6744-candidate-rank-manifest-v1",
        "passed": report["passed"],
        "files": {
            str(path.relative_to(out_dir)): _sha256_bytes(path.read_bytes())
            for path in sorted(out_dir.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        },
        "public_files": {
            str(path.relative_to(public_dir)): _sha256_bytes(path.read_bytes())
            for path in sorted(public_dir.rglob("*"))
            if path.is_file()
        },
    }
    _write_json(out_dir / "manifest.json", manifest)
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    args = parser.parse_args()
    report = write_evidence(
        out_dir=args.out_dir,
        public_dir=args.public_dir,
        seeds=args.seeds,
        difficulty=args.difficulty,
        start_index=args.start_index,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "completion_state": report["completion_state"],
                "passed": report["passed"],
                "counts": report["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
