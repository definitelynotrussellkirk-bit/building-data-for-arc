#!/usr/bin/env python3
"""Proposed episode-wide symmetry-axis variant for 1a5d49e539de.

This task-local prototype leaves the selected generator and canonical rule
unchanged. It materializes exact Racket rules for left-right (canonical) and
top-bottom reflection and builds complete episodes around one fixed axis.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "1a5d49e539de"
SOURCE_TASK_ID = "73ccf9c2"
VERSION = "proposed-symmetry-axis-v1"
CANONICAL_RULE_SHA256 = "ded19620a536146dd1004f7a00301f9f343c45b010867ff2e24bec341b5d4af3"
TOP_BOTTOM_RULE_SHA256 = "4e9746b8c1581c1e328c10512cedd0f52f2426dfe6d972a6283ca88121568a75"
SELECTED_GENERATOR_SHA256 = "cc9524450ef524c7685a084aba5bd9dbba9455934a30af32d55ed62554312d37"
PARAMETER_SPEC = {
    "name": "symmetry_axis",
    "values": ("left-right", "top-bottom"),
    "default": "left-right",
    "scope": "one fixed value per episode",
}
RULE_DIR = Path(__file__).resolve().parent / "programs"

Grid = list[list[int]]
Labeler = Callable[[Grid, str], Grid]


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _grid_sha256(grid: Grid) -> str:
    return _sha256(_json_bytes(normalize_grid(grid)))


def _validate_axis(axis: str) -> str:
    if axis not in PARAMETER_SPEC["values"]:
        raise ValueError("symmetry_axis must be 'left-right' or 'top-bottom'")
    return axis


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    return seed


def _validate_nonnegative_int(value: int, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer (not bool)")
    return value


def _validate_positive_int(value: int, name: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer (not bool)")
    return value


def choose_symmetry_axis(seed: int) -> str:
    """Choose exactly one hidden rule setting from the deterministic episode seed."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:symmetry-axis:v1:{seed}".encode("utf-8")).digest()
    return PARAMETER_SPEC["values"][digest[0] % len(PARAMETER_SPEC["values"])]


def other_axis(axis: str) -> str:
    axis = _validate_axis(axis)
    return "top-bottom" if axis == "left-right" else "left-right"


def canonical_source(*, root: str | Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    source = row.get("program_solution")
                    if not isinstance(source, str) or not source:
                        raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                    sources.add(source)
    if len(sources) != 1:
        raise RuntimeError(f"expected one canonical Racket source for {TASK_ID}, found {len(sources)}")
    source = sources.pop()
    if _sha256(source) != CANONICAL_RULE_SHA256:
        raise RuntimeError("canonical Racket source hash does not match the pinned rule")
    return source


def materialize_rule(axis: str, *, root: str | Path | None = None) -> str:
    """Return the exact retained Racket program for one symmetry-axis setting."""
    axis = _validate_axis(axis)
    path = RULE_DIR / f"{axis}.rkt"
    if not path.is_file():
        raise FileNotFoundError(path)
    source = path.read_text(encoding="utf-8")
    if axis == "left-right" and source != canonical_source(root=root):
        raise RuntimeError("left-right rule is not byte-identical to canonical authority")
    if axis == "top-bottom":
        required = "(- (- oh 1) (first c))"
        forbidden = "(- (- ow 1) (second c))"
        if required not in source or forbidden in source:
            raise RuntimeError("top-bottom rule does not contain the expected reflection transform")
        if _sha256(source) != TOP_BOTTOM_RULE_SHA256:
            raise RuntimeError("top-bottom Racket source hash does not match the retained variant")
    return source


@lru_cache(maxsize=1)
def _selected_generator():
    root = find_root(__file__)
    module, _, digest = load_selected_generator(TASK_ID, root=root)
    if digest != SELECTED_GENERATOR_SHA256:
        raise RuntimeError(
            f"selected generator hash changed: expected {SELECTED_GENERATOR_SHA256}, got {digest}"
        )
    return module


def transpose_grid(grid: Grid) -> Grid:
    grid = normalize_grid(grid)
    return [list(column) for column in zip(*grid)]


def _is_symmetric(cells: list[tuple[int, int]], axis: str) -> bool:
    axis = _validate_axis(axis)
    generator = _selected_generator()
    normalized = set(generator._normalize(cells))
    if axis == "left-right":
        width = max(column for _, column in normalized) + 1
        return all((row, width - 1 - column) in normalized for row, column in normalized)
    height = max(row for row, _ in normalized) + 1
    return all((height - 1 - row, column) in normalized for row, column in normalized)


def apply_python(grid: Grid, axis: str) -> Grid:
    """Independent Python mirror: crop the first object asymmetric on ``axis``."""
    axis = _validate_axis(axis)
    grid = normalize_grid(grid)
    generator = _selected_generator()
    for component in generator._components8(grid):
        if not _is_symmetric(component[1], axis):
            return generator._crop_component(grid, component)
    raise ValueError(f"outside prototype rule domain: no {axis} asymmetric object")


def validate_input(grid: Grid, axis: str) -> list[str]:
    """Validate the selected canonical grammar in the axis's natural frame."""
    axis = _validate_axis(axis)
    try:
        grid = normalize_grid(grid)
        canonical_frame = grid if axis == "left-right" else transpose_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return list(_selected_generator().self_check(canonical_frame))


def build_episode(
    *,
    seed: int,
    symmetry_axis: str | None = None,
    difficulty: str | None = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
    max_attempts_per_pair: int = 128,
    labeler: Labeler = apply_python,
) -> dict[str, Any]:
    """Build one deterministic episode with one fixed, demonstration-visible rule.

    Candidate indices advance by 3 on rejection. This preserves each pair's
    canonical mod-3 size role while deliberately allowing the mod-4 target slot
    to change; a fixed target-first slot can make both axis rules select the same
    object forever. Each pair receives a disjoint bounded search interval.
    """
    _validate_seed(seed)
    _validate_nonnegative_int(start_index, "start_index")
    _validate_positive_int(n_train, "n_train")
    _validate_positive_int(n_test, "n_test")
    _validate_positive_int(max_attempts_per_pair, "max_attempts_per_pair")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if not callable(labeler):
        raise TypeError("labeler must be callable")

    axis = choose_symmetry_axis(seed) if symmetry_axis is None else _validate_axis(symmetry_axis)
    rival_axis = other_axis(axis)
    generator = _selected_generator()
    total = n_train + n_test
    pairs: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()

    for ordinal in range(total):
        accepted = None
        search_base = start_index + ordinal * (3 * max_attempts_per_pair + 1)
        for attempt in range(max_attempts_per_pair):
            sample_index = search_base + 3 * attempt
            canonical_grid = generator.generate(seed, sample_index, difficulty=difficulty)
            grid = canonical_grid if axis == "left-right" else transpose_grid(canonical_grid)
            input_sha256 = _grid_sha256(grid)
            if input_sha256 in seen_inputs:
                continue
            python_output = apply_python(grid, axis)
            rival_output = apply_python(grid, rival_axis)
            if python_output == rival_output:
                continue
            output = normalize_grid(labeler(grid, axis))
            if output != python_output:
                raise RuntimeError(
                    f"labeler disagrees with Python mirror for axis={axis}, sample_index={sample_index}"
                )
            accepted = {
                "input": grid,
                "output": output,
                "input_sha256": input_sha256,
                "output_sha256": _grid_sha256(output),
                "source_sample_index": sample_index,
                "search_attempt": attempt,
            }
            break
        if accepted is None:
            raise RuntimeError(
                f"failed to find pair {ordinal} after {max_attempts_per_pair} attempts"
            )
        seen_inputs.add(accepted["input_sha256"])
        pairs.append(accepted)

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "source_task_id": SOURCE_TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "parameters": {PARAMETER_SPEC["name"]: axis},
            "parameter_scope": "chosen once per episode",
            "parameter_selection": "sha256(task-id, parameter name, version, seed) modulo 2",
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
            "max_attempts_per_pair": max_attempts_per_pair,
            "selected_generator_sha256": SELECTED_GENERATOR_SHA256,
            "canonical_rule_sha256": CANONICAL_RULE_SHA256,
            "accepted_sample_indices": [pair["source_sample_index"] for pair in pairs],
            "rejection_stride": 3,
            "search_interval_width": 3 * max_attempts_per_pair + 1,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report when the alternative axis still fits all demonstrations."""
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    meta = episode.get("meta")
    if not isinstance(meta, dict):
        return ["episode is missing meta"]
    parameters = meta.get("parameters")
    if not isinstance(parameters, dict):
        return ["episode is missing parameter metadata"]
    try:
        axis = _validate_axis(parameters.get(PARAMETER_SPEC["name"]))
    except ValueError as exc:
        return [str(exc)]
    demos = episode.get("train")
    if not isinstance(demos, list) or not demos:
        return ["episode needs at least one demonstration"]

    rival = other_axis(axis)
    findings: list[str] = []
    rival_fits = True
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"demo {index} is malformed")
            rival_fits = False
            continue
        try:
            if apply_python(pair["input"], rival) != normalize_grid(pair["output"]):
                rival_fits = False
        except (TypeError, ValueError) as exc:
            findings.append(f"demo {index} cannot be evaluated: {exc}")
            rival_fits = False
    if rival_fits:
        findings.append(
            f"demonstrations do not distinguish symmetry_axis={axis!r} from {rival!r}"
        )
    return findings


def _grid_literal(grid: Grid) -> str:
    grid = normalize_grid(grid)
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def execute_racket(source: str, grid: Grid, *, bridge=None) -> Grid:
    """Execute exact `(rule! ...)` source through the packet's Racket bridge."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be nonempty Racket text")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Grid]]]:
    """Allowlist only visible demonstrations and query inputs."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list) or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return copy.deepcopy(
            {
                "train": [
                    {"input": pair["input"], "output": pair["output"]}
                    for pair in train
                ],
                "test": [{"input": pair["input"]} for pair in test],
            }
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("episode pairs are missing visible fields") from exc


def _episode_axis(episode: dict[str, Any]) -> str:
    try:
        return _validate_axis(episode["meta"]["parameters"][PARAMETER_SPEC["name"]])
    except (KeyError, TypeError) as exc:
        raise ValueError("episode is missing symmetry-axis metadata") from exc


def _racket_verified_episode(
    *,
    seed: int,
    bridge,
    root: Path,
    difficulty: str | None,
    start_index: int,
    n_train: int,
    n_test: int,
    max_attempts_per_pair: int,
) -> tuple[dict[str, Any], int]:
    axis = choose_symmetry_axis(seed)
    rival = other_axis(axis)
    source = materialize_rule(axis, root=root)
    rival_source = materialize_rule(rival, root=root)

    episode = build_episode(
        seed=seed,
        symmetry_axis=axis,
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
        max_attempts_per_pair=max_attempts_per_pair,
        labeler=lambda grid, selected_axis: execute_racket(
            materialize_rule(selected_axis, root=root), grid, bridge=bridge
        ),
    )
    pairs = [*episode["train"], *episode["test"]]
    rival_predictions: list[Grid] = []
    rival_matches_python = True
    for pair in pairs:
        prediction = execute_racket(rival_source, pair["input"], bridge=bridge)
        rival_predictions.append(prediction)
        if prediction != apply_python(pair["input"], rival):
            rival_matches_python = False

    demo_mismatches = [
        index
        for index, (pair, prediction) in enumerate(
            zip(episode["train"], rival_predictions[:n_train], strict=True)
        )
        if prediction != pair["output"]
    ]
    query_mismatches = [
        index
        for index, (pair, prediction) in enumerate(
            zip(episode["test"], rival_predictions[n_train:], strict=True)
        )
        if prediction != pair["output"]
    ]
    if demo_mismatches:
        rival_status = "refuted_by_demonstrations"
    elif query_mismatches:
        rival_status = "ambiguous_query"
    else:
        rival_status = "matches_episode"

    episode["racket_source"] = source
    episode["racket_sha256"] = _sha256(source)
    episode["racket_program_path"] = f"private/rules/{axis}.rkt"
    episode["parameter_rival"] = {
        "symmetry_axis": rival,
        "racket_sha256": _sha256(rival_source),
        "status": rival_status,
        "demonstration_mismatch_indices": demo_mismatches,
        "query_mismatch_indices": query_mismatches,
        "predictions": rival_predictions,
    }
    episode["racket_verification"] = {
        "selected_matches_python": True,
        "rival_matches_python": rival_matches_python,
        "selected_evaluations": len(pairs),
        "rival_evaluations": len(pairs),
    }
    episode["meta"]["prototype_sha256"] = _sha256(Path(__file__).read_bytes())
    episode["meta"]["selected_racket_sha256"] = _sha256(source)
    episode["meta"]["rival_racket_sha256"] = _sha256(rival_source)

    if parameter_rival_findings(episode):
        raise RuntimeError("retained demonstrations fail the Python parameter-rival check")
    if not rival_matches_python:
        raise RuntimeError("rival Racket program disagrees with the independent Python mirror")
    if rival_status != "refuted_by_demonstrations":
        raise RuntimeError(f"parameter rival is not identified by demonstrations: {rival_status}")
    return episode, 2 * len(pairs)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    *,
    seeds: list[int] | tuple[int, ...],
    out_dir: str | Path,
    public_dir: str | Path,
    root: str | Path | None = None,
    difficulty: str | None = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
    max_attempts_per_pair: int = 128,
    require_all_settings: bool = True,
) -> dict[str, Any]:
    """Write bounded private evidence and answer-masked public challenges."""
    seeds = list(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    _validate_nonnegative_int(start_index, "start_index")
    _validate_positive_int(n_train, "n_train")
    _validate_positive_int(n_test, "n_test")
    _validate_positive_int(max_attempts_per_pair, "max_attempts_per_pair")
    if type(require_all_settings) is not bool:
        raise TypeError("require_all_settings must be bool")

    root_path = find_root(__file__) if root is None else Path(root).resolve()
    # Bind both selected sources before creating output directories.
    rules = {axis: materialize_rule(axis, root=root_path) for axis in PARAMETER_SPEC["values"]}
    settings = {choose_symmetry_axis(seed) for seed in seeds}
    if require_all_settings and settings != set(PARAMETER_SPEC["values"]):
        raise ValueError(
            "retained seeds must cover both symmetry-axis settings; "
            f"got {sorted(settings)}"
        )

    out_path = Path(out_dir)
    public_path = Path(public_dir)
    out_path.mkdir(parents=True, exist_ok=False)
    public_path.mkdir(parents=True, exist_ok=False)
    private_path = out_path / "private"
    (private_path / "episodes").mkdir(parents=True)
    (private_path / "rules").mkdir(parents=True)

    try:
        for axis, source in rules.items():
            (private_path / "rules" / f"{axis}.rkt").write_text(source, encoding="utf-8")

        from arc_repl.racket_bridge import RacketBridge

        records: list[dict[str, Any]] = []
        racket_evaluations = 0
        with RacketBridge() as bridge:
            for seed in seeds:
                episode, evaluations = _racket_verified_episode(
                    seed=seed,
                    bridge=bridge,
                    root=root_path,
                    difficulty=difficulty,
                    start_index=start_index,
                    n_train=n_train,
                    n_test=n_test,
                    max_attempts_per_pair=max_attempts_per_pair,
                )
                challenge = public_challenge(episode)
                challenge_id = public_challenge_id(challenge)
                episode["public_challenge_id"] = challenge_id
                records.append(
                    {
                        "public_id": challenge_id,
                        "episode": episode,
                        "challenge": challenge,
                    }
                )
                racket_evaluations += evaluations

        records.sort(key=lambda row: row["public_id"])
        ids = [row["public_id"] for row in records]
        if len(ids) != len(set(ids)):
            raise RuntimeError("duplicate visible public challenge payloads")

        episode_rows = []
        public_rows = []
        for index, row in enumerate(records):
            private_rel = f"private/episodes/episode_{index:03d}.json"
            public_name = f"challenge_{row['public_id']}.json"
            public_rel = public_name
            row["episode"]["private_episode_path"] = private_rel
            row["episode"]["public_challenge_path"] = public_rel
            _write_json(out_path / private_rel, row["episode"])
            visible_bytes = public_challenge_bytes(row["challenge"])
            (public_path / public_name).write_bytes(visible_bytes)
            episode_rows.append(
                {
                    "private_path": private_rel,
                    "public_id": row["public_id"],
                    "public_path": public_rel,
                    "seed": row["episode"]["meta"]["seed"],
                    "symmetry_axis": _episode_axis(row["episode"]),
                    "accepted_sample_indices": row["episode"]["meta"]["accepted_sample_indices"],
                }
            )
            public_rows.append(
                {
                    "id": row["public_id"],
                    "path": public_rel,
                    "sha256": _sha256(visible_bytes),
                }
            )

        test_path = (
            root_path
            / "generators"
            / TASK_ID
            / "tests"
            / "test_parametric_symmetry_axis.py"
        )
        manifest = {
            "schema": "arcpuzzles-parametric-evidence-v1",
            "status": "verified",
            "task_id": TASK_ID,
            "source_task_id": SOURCE_TASK_ID,
            "prototype_version": VERSION,
            "prototype_status": "proposed_unapproved",
            "parameter": PARAMETER_SPEC,
            "settings_covered": sorted(settings),
            "episode_count": len(records),
            "demo_count_per_episode": n_train,
            "query_count_per_episode": n_test,
            "difficulty": difficulty,
            "start_index": start_index,
            "max_attempts_per_pair": max_attempts_per_pair,
            "selected_generator_sha256": SELECTED_GENERATOR_SHA256,
            "canonical_rule_sha256": CANONICAL_RULE_SHA256,
            "top_bottom_rule_sha256": TOP_BOTTOM_RULE_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "test_sha256": _sha256(test_path.read_bytes()) if test_path.is_file() else None,
            "racket_evaluations": racket_evaluations,
            "episodes": episode_rows,
            "public_challenges": public_rows,
            "limits": [
                "finite evidence for two settings and the retained seeds only",
                "prototype is not a production parametric API or training approval",
                "the alternative axis rule selects the first asymmetric object when outside the retained unique-axis grammar",
            ],
        }
        _write_json(out_path / "manifest.json", manifest)
        return manifest
    except Exception as exc:
        _write_json(
            private_path / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": seeds,
            },
        )
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--public-dir", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--max-attempts-per-pair", type=int, default=128)
    parser.add_argument("--allow-partial-settings", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest = write_evidence(
        seeds=args.seeds,
        out_dir=args.out_dir,
        public_dir=args.public_dir,
        difficulty=args.difficulty,
        start_index=args.start_index,
        n_train=args.n_train,
        n_test=args.n_test,
        max_attempts_per_pair=args.max_attempts_per_pair,
        require_all_settings=not args.allow_partial_settings,
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
