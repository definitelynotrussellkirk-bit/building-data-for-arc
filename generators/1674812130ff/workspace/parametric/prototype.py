#!/usr/bin/env python3
"""Proposed episode-level completion-transform variant for ARC task 1674812130ff."""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "1674812130ff"
ALLOWED_TRANSFORMS = ("rotate_180", "flip_lr")
DEFAULT_TRANSFORM = "rotate_180"
DEFAULT_TRAIN_COUNT = 2
DEFAULT_QUERY_COUNT = 4
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)

_GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _validate_transform(completion_transform: str) -> None:
    if type(completion_transform) is not str or completion_transform not in ALLOWED_TRANSFORMS:
        raise ValueError(
            "completion_transform must be one of "
            f"{ALLOWED_TRANSFORMS}, got {completion_transform!r}"
        )


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the exact canonical Racket program for the selected task."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if not matches:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    sources = {row.get("program_solution") for row in matches}
    if len(sources) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree on program_solution")
    source = sources.pop()
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"canonical record for {TASK_ID} has no program_solution")
    return source


def program_for(completion_transform: str = DEFAULT_TRANSFORM, *, root: Path = ROOT) -> str:
    """Materialize exact Racket for one proposed episode-level transform."""
    _validate_transform(completion_transform)
    source = canonical_source(root=root)
    if completion_transform == DEFAULT_TRANSFORM:
        return source
    needle = "(rotate-180 g)"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded transform template")
    return source.replace(needle, "(flip-lr g)")


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute one complete rule through the protected Racket bridge."""
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns_bridge:
            active.shutdown()


def python_complete(grid, *, completion_transform: str = DEFAULT_TRANSFORM):
    """Independent diagnostic mirror; Racket remains the label authority."""
    _validate_transform(completion_transform)
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list of rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    height = len(grid)
    source = [row[:] for row in grid]
    if completion_transform == "rotate_180":
        transformed = [list(reversed(row)) for row in reversed(source)]
    else:
        transformed = [list(reversed(row)) for row in source]
    return [
        [
            source[r][c] if source[r][c] != 7 else transformed[r][c]
            for c in range(width)
        ]
        for r in range(height)
    ]


def grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalized_program_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(train_count: int, query_count: int) -> None:
    if type(train_count) is not int or not 1 <= train_count <= 8:
        raise ValueError("train_count must be an exact integer in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 8:
        raise ValueError("query_count must be an exact integer in 1..8")


def select_setting(seed: int) -> str:
    """Choose one hidden transform from an episode-only deterministic stream."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:completion-transform:{seed}".encode()).digest()
    return ALLOWED_TRANSFORMS[digest[0] % len(ALLOWED_TRANSFORMS)]


def _derived_seed(seed: int, candidate_index: int) -> int:
    payload = f"{TASK_ID}:parametric-input:{seed}:{candidate_index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0x7FFFFFFF


def _sample_inputs(seed: int, count: int, difficulty: str):
    accepted = []
    seen = set()
    max_attempts = max(40, count * 20)
    for candidate_index in range(max_attempts):
        input_seed = _derived_seed(seed, candidate_index)
        grid = _GEN.generate(input_seed, candidate_index, difficulty=difficulty)
        errors = _GEN.self_check(grid)
        if errors:
            raise RuntimeError(f"selected generator emitted an invalid grid: {errors}")
        digest = grid_sha256(grid)
        if digest in seen:
            continue
        rotate = python_complete(grid, completion_transform="rotate_180")
        flip = python_complete(grid, completion_transform="flip_lr")
        if rotate == flip:
            continue
        seen.add(digest)
        accepted.append(
            {
                "grid": grid,
                "input_sha256": digest,
                "input_seed": input_seed,
                "sample_index": candidate_index,
            }
        )
        if len(accepted) == count:
            return accepted
    raise RuntimeError(
        f"could not sample {count} distinct transform-separating inputs "
        f"within {max_attempts} attempts"
    )


def make_episode(
    seed: int,
    *,
    completion_transform: str | None = None,
    difficulty: str = "medium",
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one private episode, deriving every label in matching Racket."""
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    selected = select_setting(seed) if completion_transform is None else completion_transform
    _validate_transform(selected)
    rival = next(value for value in ALLOWED_TRANSFORMS if value != selected)

    samples = _sample_inputs(seed, train_count + query_count, difficulty)
    programs = {transform: program_for(transform, root=root) for transform in ALLOWED_TRANSFORMS}
    outputs = {transform: [] for transform in ALLOWED_TRANSFORMS}

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        for row in samples:
            grid = row["grid"]
            for transform in ALLOWED_TRANSFORMS:
                output = execute_rule(programs[transform], grid, bridge=active)
                mirror = python_complete(grid, completion_transform=transform)
                if output != mirror:
                    raise AssertionError(
                        f"Racket/Python parity failed for transform {transform}"
                    )
                outputs[transform].append(output)
    finally:
        if owns_bridge:
            active.shutdown()

    pairs = [
        {"input": row["grid"], "output": outputs[selected][index]}
        for index, row in enumerate(samples)
    ]
    demo_mismatches = [
        index
        for index in range(train_count)
        if outputs[selected][index] != outputs[rival][index]
    ]
    query_mismatches = [
        index
        for index in range(query_count)
        if outputs[selected][train_count + index] != outputs[rival][train_count + index]
    ]
    rival_status = "refuted_by_demonstrations" if demo_mismatches else "ambiguous_query"
    program = programs[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"completion_transform": selected},
        "seed": seed,
        "difficulty": difficulty,
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_program_sha256": normalized_program_sha256(program),
        "input_provenance": [
            {key: row[key] for key in ("input_sha256", "input_seed", "sample_index")}
            for row in samples
        ],
        "parameter_rivals": [
            {
                "completion_transform": rival,
                "status": rival_status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        ],
        "ambiguities": [] if demo_mismatches else [rival],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return canonical visible bytes with private rule material removed."""
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    """Return the opaque SHA-256 identifier of exactly the public bytes."""
    return _public_challenge_id(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a detached public challenge containing no query answers."""
    return json.loads(public_bytes(episode))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _difference_coordinates(a, b) -> list[list[int]]:
    if len(a) != len(b) or any(len(ar) != len(br) for ar, br in zip(a, b)):
        raise ValueError("grids must have matching dimensions")
    return [
        [r, c]
        for r, (ar, br) in enumerate(zip(a, b))
        for c, (av, bv) in enumerate(zip(ar, br))
        if av != bv
    ]


def write_evidence(
    *,
    seed: int,
    out: str | Path,
    difficulty: str = "medium",
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Materialize exact rules plus privacy-separated public/private evidence."""
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    root = Path(root).resolve()
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))

    try:
        context = nullcontext(bridge) if bridge is not None else RacketBridge()
        with context as active_bridge:
            canonical_program = program_for(DEFAULT_TRANSFORM, root=root)
            canonical_rows = []
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical_program, pair["input"], bridge=active_bridge)
                row = {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                    "matches": actual == pair["output"],
                }
                canonical_rows.append(row)
            if not canonical_rows or not all(row["matches"] for row in canonical_rows):
                raise AssertionError(
                    "canonical rotate_180 program failed a labelled canonical pair"
                )

            episodes = []
            private_episodes: dict[str, dict[str, Any]] = {}
            distinct_inputs = set()
            for transform in ALLOWED_TRANSFORMS:
                episode = make_episode(
                    seed,
                    completion_transform=transform,
                    difficulty=difficulty,
                    train_count=train_count,
                    query_count=query_count,
                    root=root,
                    bridge=active_bridge,
                )
                rule_rel = Path("private/rules") / f"completion-{transform}.rkt"
                private_rel = Path("private") / f"episode-{transform}.json"
                rule_path = temp / rule_rel
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(episode["program"], encoding="utf-8")

                private = dict(episode)
                private["racket_path"] = rule_rel.as_posix()
                private["racket_sha256"] = _file_sha256(rule_path)
                _write_json(temp / private_rel, private)
                private_episodes[transform] = private

                visible_id = public_id(private)
                public_rel = Path("public") / f"challenge-{visible_id}.json"
                public_path = temp / public_rel
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(public_bytes(private))

                for pair in private["train"] + private["test"]:
                    distinct_inputs.add(grid_sha256(pair["input"]))
                rival = private["parameter_rivals"][0]
                episodes.append(
                    {
                        "completion_transform": transform,
                        "seed": seed,
                        "difficulty": difficulty,
                        "train_count": len(private["train"]),
                        "query_count": len(private["test"]),
                        "private_path": private_rel.as_posix(),
                        "private_sha256": _file_sha256(temp / private_rel),
                        "public_path": public_rel.as_posix(),
                        "public_sha256": _file_sha256(public_path),
                        "public_id": visible_id,
                        "racket_path": rule_rel.as_posix(),
                        "racket_sha256": _file_sha256(rule_path),
                        "normalized_racket_sha256": private[
                            "normalized_program_sha256"
                        ],
                        "rival_status": rival["status"],
                        "rival_demonstration_mismatch_indices": rival[
                            "demonstration_mismatch_indices"
                        ],
                        "rival_query_mismatch_indices": rival[
                            "query_mismatch_indices"
                        ],
                    }
                )

            rotate_inputs = [
                pair["input"]
                for pair in private_episodes["rotate_180"]["train"]
                + private_episodes["rotate_180"]["test"]
            ]
            flip_inputs = [
                pair["input"]
                for pair in private_episodes["flip_lr"]["train"]
                + private_episodes["flip_lr"]["test"]
            ]
            if rotate_inputs != flip_inputs:
                raise AssertionError("transform setting changed the episode input draws")
            witness_input = rotate_inputs[0]
            witness_outputs = {
                transform: execute_rule(
                    program_for(transform, root=root),
                    witness_input,
                    bridge=active_bridge,
                )
                for transform in ALLOWED_TRANSFORMS
            }

        witness = {
            "schema": "arcpuzzles-parametric-setting-witness-v1",
            "task_id": TASK_ID,
            "parameter": "completion_transform",
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                transform: grid_sha256(output)
                for transform, output in witness_outputs.items()
            },
            "difference_coordinates": _difference_coordinates(
                witness_outputs["rotate_180"], witness_outputs["flip_lr"]
            ),
        }
        if not witness["difference_coordinates"]:
            raise AssertionError("retained witness does not separate transform settings")
        _write_json(temp / "setting-difference-witness.json", witness)
        _write_json(temp / "canonical-default-check.json", canonical_rows)

        prototype_path = Path(__file__).resolve()
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "status": "proposed_unapproved",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameter": {
                "name": "completion_transform",
                "allowed_values": list(ALLOWED_TRANSFORMS),
                "original_default": DEFAULT_TRANSFORM,
                "selection_scope": "once_per_episode",
                "input_constraints_depend_on_parameter": False,
            },
            "reasoning_invariants": [
                "identify color 7 as the writable background",
                "preserve every existing non-background cell",
                "use the central color-4 divider and color-8 anchors as scene structure",
                "complete the blank right half from the matching left-side figure",
                "apply one fixed geometric counterpart map throughout the episode",
            ],
            "episodes": episodes,
            "sources": {
                "canonical_ledger": {
                    "path": str(canonical_path(root).relative_to(root)),
                    "sha256": _file_sha256(canonical_path(root)),
                },
                "generator": {
                    "path": str(GENERATOR_PATH.relative_to(root)),
                    "sha256": GENERATOR_SHA256,
                },
                "prototype": {
                    "path": str(prototype_path.relative_to(root)),
                    "sha256": _file_sha256(prototype_path),
                },
            },
            "canonical_default": {
                "program_sha256": hashlib.sha256(canonical_program.encode()).hexdigest(),
                "normalized_program_sha256": normalized_program_sha256(
                    canonical_program
                ),
                "pairs": canonical_rows,
                "all_match": all(row["matches"] for row in canonical_rows),
            },
            "witness_path": "setting-difference-witness.json",
            "counts": {
                "episodes": len(episodes),
                "train_pairs": sum(row["train_count"] for row in episodes),
                "query_pairs": sum(row["query_count"] for row in episodes),
                "distinct_input_grids": len(distinct_inputs),
                "settings_exercised": len(episodes),
                "canonical_pairs_checked": len(canonical_rows),
                "ambiguous_parameter_rivals": sum(
                    row["rival_status"] != "refuted_by_demonstrations"
                    for row in episodes
                ),
            },
            "limitations": [
                "identifiability is checked only against the declared opposite transform",
                "finite demonstrations do not prove unique induction against every program",
                "the prototype is separate from canonical generate(), approval, and training admission",
            ],
        }
        _write_json(temp / "report.json", report)

        files = []
        for path in sorted(temp.rglob("*")):
            if path.is_file():
                files.append(
                    {
                        "path": path.relative_to(temp).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": _file_sha256(path),
                    }
                )
        manifest = {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "status": "proposed_unapproved",
            "files": files,
        }
        _write_json(temp / "manifest.json", manifest)
        temp.rename(out)
        return report
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main(
    argv: list[str] | None = None, *, bridge: RacketBridge | None = None
) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Materialize and Racket-verify both completion-transform settings."
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--train", type=int, default=DEFAULT_TRAIN_COUNT)
    parser.add_argument("--test", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    report = write_evidence(
        seed=args.seed,
        out=args.out,
        difficulty=args.difficulty,
        train_count=args.train,
        query_count=args.test,
        bridge=bridge,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "out": str(args.out),
                "counts": report["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
