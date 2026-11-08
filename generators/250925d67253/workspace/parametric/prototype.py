#!/usr/bin/env python3
"""Task-local destination-frame parameter prototype for 250925d67253.

The selected production generator and canonical authority remain unchanged.
Each prototype episode chooses one frame once: canonical ``identity`` or a
``transpose`` interpretation of the centroid-selected 3x3 destination address.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable


TASK_ID = "250925d67253"
PARAMETER_SPEC = {
    "name": "destination_frame",
    "values": ("identity", "transpose"),
    "default": "identity",
}

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
RULE_DIR = HERE.parent / "rules"
CANONICAL_LEDGER = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_text(json.dumps(grid, separators=(",", ":")))


def _validate_frame(destination_frame: str) -> str:
    if destination_frame not in PARAMETER_SPEC["values"]:
        raise ValueError(
            "destination_frame must be one of "
            f"{PARAMETER_SPEC['values']}, got {destination_frame!r}"
        )
    return destination_frame


def choose_destination_frame(seed: int) -> str:
    """Choose one hidden setting deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return PARAMETER_SPEC["values"][seed % len(PARAMETER_SPEC["values"])]


def _load_generator():
    name = f"parametric_destination_frame_{TASK_ID}_generator"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_rule() -> str:
    """Return the selected canonical Racket source from the pinned ledger."""
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                return source
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def materialize_rule(destination_frame: str) -> str:
    """Load the exact retained Racket rule for one prototype setting."""
    frame = _validate_frame(destination_frame)
    path = RULE_DIR / f"{frame}.rkt"
    if not path.is_file():
        raise FileNotFoundError(f"missing prototype rule source: {path}")
    source = path.read_text(encoding="utf-8")
    if frame == "identity" and source != canonical_rule():
        raise RuntimeError("identity prototype rule is not byte-identical to canonical")
    return source


def _transform_target(target: int, destination_frame: str) -> int:
    frame = _validate_frame(destination_frame)
    row, column = divmod(target, 3)
    return target if frame == "identity" else 3 * column + row


def apply_python(grid: list[list[int]], destination_frame: str) -> list[list[int]]:
    """Independent Python mirror for either destination-frame setting."""
    frame = _validate_frame(destination_frame)
    generator = _load_generator()
    raw_mapping = generator._target_mapping(grid, "centroid")
    mapping = [_transform_target(target, frame) for target in raw_mapping]
    if sorted(mapping) != list(range(9)):
        raise ValueError(f"transformed targets are not a bijection: {mapping}")
    return generator._apply_mapping(grid, mapping)


def build_episode(
    *,
    seed: int,
    destination_frame: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 4,
    n_test: int = 1,
    labeler: Callable[[list[list[int]], str], list[list[int]]] = apply_python,
) -> dict[str, Any]:
    """Build a complete prototype episode with one fixed hidden rule setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer (not bool)")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")

    frame = (
        choose_destination_frame(seed)
        if destination_frame is None
        else _validate_frame(destination_frame)
    )
    generator = _load_generator()
    sample_indices = list(range(start_index, start_index + n_train + n_test))
    pairs: list[dict[str, Any]] = []
    for sample_index in sample_indices:
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": labeler(grid, frame)})

    return {
        "schema": "250925d67253-parametric-episode-v1",
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "parameters": {PARAMETER_SPEC["name"]: frame},
            "parameter_scope": "chosen once per episode",
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "sample_indices": sample_indices,
            "input_generator_version": generator.VERSION,
        },
    }


def _episode_frame(episode: dict[str, Any]) -> str:
    meta = episode.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("episode is missing metadata")
    parameters = meta.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode is missing parameter metadata")
    return _validate_frame(parameters.get(PARAMETER_SPEC["name"]))


def _all_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return [*train, *test]


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report any alternative frame that still fits every demonstration."""
    try:
        chosen = _episode_frame(episode)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    demos = episode.get("train")
    if not isinstance(demos, list) or not demos:
        return ["episode needs at least one demonstration"]

    findings: list[str] = []
    for rival in PARAMETER_SPEC["values"]:
        if rival == chosen:
            continue
        rival_fits = True
        for index, pair in enumerate(demos):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                findings.append(f"demo {index} is malformed")
                rival_fits = False
                continue
            if apply_python(pair["input"], rival) != pair["output"]:
                rival_fits = False
        if rival_fits:
            findings.append(
                f"demonstrations do not distinguish destination_frame={chosen!r} "
                f"from {rival!r}"
            )
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Strip hidden parameter metadata, Racket code, and query answers."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in train
        ],
        "test": [{"input": pair["input"]} for pair in test],
    }


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _racket_runtime():
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


def apply_racket(grid: list[list[int]], destination_frame: str) -> list[list[int]]:
    """Execute one exact materialized Racket rule in the pinned runtime."""
    source = materialize_rule(destination_frame)
    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=8) as bridge:
        return _execute_racket(bridge, wrap_rule, source, grid)


def _rotation_record(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    pairs = _all_pairs(episode)
    chosen = _episode_frame(episode)
    rival = next(value for value in PARAMETER_SPEC["values"] if value != chosen)
    demos = [index for index in range(len(pairs)) if index != query_index]
    refuting = [
        index
        for index in demos
        if apply_python(pairs[index]["input"], rival) != pairs[index]["output"]
    ]
    return {
        "query_index": query_index,
        "demonstration_indices": demos,
        "refuting_demo_indices": refuting,
        "identifiable": bool(refuting),
        "rival_changes_query": (
            apply_python(pairs[query_index]["input"], rival)
            != pairs[query_index]["output"]
        ),
    }


def build_evidence(
    *,
    seeds: list[int],
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 4,
    n_test: int = 1,
) -> dict[str, Any]:
    """Execute both settings and return bounded, source-bound prototype evidence."""
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("seeds must be a nonempty list")
    if any(type(seed) is not int for seed in seeds):
        raise TypeError("every seed must be an integer (not bool)")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    selected_settings = {choose_destination_frame(seed) for seed in seeds}
    if selected_settings != set(PARAMETER_SPEC["values"]):
        raise ValueError("seeds must demonstrate both destination_frame settings")

    from reviewer_support import canonical_pairs

    generator = _load_generator()
    programs = {frame: materialize_rule(frame) for frame in PARAMETER_SPEC["values"]}
    default_program_byte_identical = programs["identity"] == canonical_rule()
    canonical_checks: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    parity_results: list[bool] = []
    production_records: list[dict[str, Any]] = []
    rotation_records: list[dict[str, Any]] = []
    racket_label_executions = 0

    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=16) as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            actual = _execute_racket(bridge, wrap_rule, programs["identity"], pair["input"])
            canonical_checks.append(
                {
                    "variant": pair.get("variant"),
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "input_sha256": _grid_sha256(pair["input"]),
                    "expected_output_sha256": _grid_sha256(pair["output"]),
                    "actual_output_sha256": _grid_sha256(actual),
                    "passed": actual == pair["output"],
                }
            )

        for seed in seeds:
            frame = choose_destination_frame(seed)

            def racket_labeler(grid: list[list[int]], selected: str) -> list[list[int]]:
                nonlocal racket_label_executions
                racket_label_executions += 1
                return _execute_racket(bridge, wrap_rule, programs[selected], grid)

            episode = build_episode(
                seed=seed,
                destination_frame=frame,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                labeler=racket_labeler,
            )
            pairs = _all_pairs(episode)
            pair_checks = []
            for index, pair in enumerate(pairs):
                python_output = apply_python(pair["input"], frame)
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
            rotations = [_rotation_record(episode, index) for index in range(len(pairs))]
            rotation_records.extend(rotations)
            production = _rotation_record(episode, len(pairs) - 1)
            production_records.append(production)
            episodes.append(
                {
                    "seed": seed,
                    "parameters": {"destination_frame": frame},
                    "episode": episode,
                    "pair_checks": pair_checks,
                    "parameter_rival_findings": findings,
                    "production_identifiability": production,
                    "rotations": rotations,
                }
            )

        witness_grid = episodes[0]["episode"]["train"][0]["input"]
        witness_outputs = {
            frame: _execute_racket(bridge, wrap_rule, source, witness_grid)
            for frame, source in programs.items()
        }

    identity_output = witness_outputs["identity"]
    transpose_output = witness_outputs["transpose"]
    different_cells = [
        {"row": row, "column": column}
        for row in range(len(identity_output))
        for column in range(len(identity_output[row]))
        if identity_output[row][column] != transpose_output[row][column]
    ]
    witness = {
        "input": witness_grid,
        "input_sha256": _grid_sha256(witness_grid),
        "outputs": witness_outputs,
        "output_sha256": {
            frame: _grid_sha256(output) for frame, output in witness_outputs.items()
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
        "query_rotations": len(rotation_records),
        "rotations_identifiable": sum(row["identifiable"] for row in rotation_records),
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
        and counts["rotations_identifiable"] == counts["query_rotations"]
        and not all_findings
        and witness["different_cell_count"] > 0
    )

    return {
        "schema": "250925d67253-destination-frame-evidence-v1",
        "task_id": TASK_ID,
        "status": "proposed",
        "completion_state": "complete" if passed else "blocked",
        "passed": passed,
        "parameter_contract": {
            **PARAMETER_SPEC,
            "scope": "chosen once per episode",
            "canonical_setting": "identity",
            "input_constraints": [
                "the selected generator's lawful 19x19 two-color panel lattice",
                "all nine raw centroid targets form a bijection",
            ],
            "invariant_reasoning": [
                "identify the common panel background and marker color",
                "compute every panel's arithmetic marker centroid",
                "bucket each centroid into a 3x3 logical address",
                "copy each complete 5x5 panel into the interpreted address",
            ],
        },
        "canonical_authority_changed": False,
        "default_program_byte_identical": default_program_byte_identical,
        "programs": {
            frame: {
                "path": str((RULE_DIR / f"{frame}.rkt").relative_to(ROOT)),
                "sha256": _sha256_text(source),
                "text": source,
            }
            for frame, source in programs.items()
        },
        "sources": {
            "prototype": {
                "path": str(HERE.relative_to(ROOT)),
                "sha256": _sha256_bytes(HERE.read_bytes()),
            },
            "selected_generator": {
                "path": str(GENERATOR_PATH.relative_to(ROOT)),
                "sha256": _sha256_bytes(GENERATOR_PATH.read_bytes()),
                "version": generator.VERSION,
                "rule_hash": generator.RULE_HASH,
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
            "Evidence covers only the retained seeds, generated inputs, and two frame settings.",
            "The transpose setting adds a global coordinate-frame convention that demonstrations must teach; it does not change centroid computation or panel copying.",
            "Rival checks cover only identity versus transpose, not every possible coordinate transform or simpler program.",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
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
) -> dict[str, Any]:
    """Write private evidence and answer-masked public challenges."""
    out_dir = out_dir.resolve()
    public_dir = public_dir.resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out_dir}")
    if public_dir.exists() and any(public_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty public directory: {public_dir}")
    out_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    report = build_evidence(
        seeds=seeds,
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
    )
    _write_json(out_dir / "report.json", report)
    _write_json(out_dir / "setting-difference-witness.json", report["setting_difference_witness"])
    for ordinal, record in enumerate(report["episodes"], start=1):
        frame = record["parameters"]["destination_frame"]
        _write_json(out_dir / f"episode-{ordinal:02d}-{frame}.json", record)
        _write_json(
            public_dir / f"challenge-{ordinal:02d}.json",
            public_challenge(record["episode"]),
        )
    manifest = {
        "schema": "250925d67253-destination-frame-manifest-v1",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=4)
    parser.add_argument("--n-test", type=int, default=1)
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
