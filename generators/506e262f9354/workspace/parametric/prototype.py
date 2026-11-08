#!/usr/bin/env python3
"""Proposed episode-level expansion-direction variant for ARC task 506e262f9354."""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "506e262f9354"
ALLOWED_DIRECTIONS = ("up", "down")
DEFAULT_DIRECTION = "up"
ROOT = find_root(__file__)
DEFAULT_TRAIN_COUNT = 3
DEFAULT_QUERY_COUNT = 4
PROTOTYPE_VERSION = "1.1.0"

_GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _validate_direction(expansion_direction: str) -> None:
    if type(expansion_direction) is not str or expansion_direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            "expansion_direction must be one of "
            f"{ALLOWED_DIRECTIONS}, got {expansion_direction!r}"
        )


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the exact selected canonical Racket program from the local ledger."""
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
        raise ValueError(
            f"canonical variants for {TASK_ID} disagree on program_solution"
        )
    source = sources.pop()
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"canonical record for {TASK_ID} has no program_solution")
    return source


def program_for(expansion_direction: str = DEFAULT_DIRECTION, *, root: Path = ROOT) -> str:
    """Materialize exact Racket for one proposed episode-level direction."""
    _validate_direction(expansion_direction)
    source = canonical_source(root=root)
    if expansion_direction == DEFAULT_DIRECTION:
        return source

    endpoint = "(rbot (max-of first sevens))"
    reach = "(let ((d (- rbot r))"
    if source.count(endpoint) != 1 or source.count(reach) != 1:
        raise ValueError("canonical source no longer matches the guarded direction template")
    return source.replace(endpoint, "(rtop (min-of first sevens))").replace(
        reach, "(let ((d (- r rtop))"
    )


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute one complete rule through the protected Racket bridge."""
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(_program_body(program))
    finally:
        if owns_bridge:
            active.shutdown()


def python_mirror(grid, *, expansion_direction: str = DEFAULT_DIRECTION):
    """Independent diagnostic mirror; Racket remains the label authority."""
    _validate_direction(expansion_direction)
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list of rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    sevens = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    ]
    if not sevens:
        raise ValueError("grid must contain at least one color-7 source cell")
    columns = {c for _, c in sevens}
    if len(columns) != 1:
        raise ValueError("color-7 source cells must occupy one column")
    source_col = next(iter(columns))
    apex_row = (
        max(r for r, _ in sevens)
        if expansion_direction == "up"
        else min(r for r, _ in sevens)
    )
    output = [[0 for _ in range(width)] for _ in range(len(grid))]
    for r in range(len(grid)):
        reach = apex_row - r if expansion_direction == "up" else r - apex_row
        if reach < 0:
            continue
        for c in range(width):
            distance = abs(c - source_col)
            if distance <= reach:
                output[r][c] = 7 if distance % 2 == 0 else 8
    return output


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
    if type(train_count) is not int or not 3 <= train_count <= 8:
        raise ValueError("train_count must be an exact integer in 3..8")
    if type(query_count) is not int or not 1 <= query_count <= 8:
        raise ValueError("query_count must be an exact integer in 1..8")


def select_setting(seed: int) -> str:
    """Choose one hidden direction from an episode-only deterministic stream."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:expansion-direction:{seed}".encode()).digest()
    return ALLOWED_DIRECTIONS[digest[0] % len(ALLOWED_DIRECTIONS)]


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
        if python_mirror(grid, expansion_direction="up") == python_mirror(
            grid, expansion_direction="down"
        ):
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
        f"could not sample {count} distinct direction-separating inputs "
        f"within {max_attempts} attempts"
    )


def generate_claims(
    seed: int,
    *,
    expansion_direction: str,
    difficulty: str = "medium",
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Build deterministic Python label claims for independent Racket replay.

    The promotion worker re-executes every claim through protected Racket.  This
    helper deliberately does not construct a bridge, avoiding nested runtime
    lifecycles while reusing the reviewed sampler and diagnostic mirror.
    """
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    _validate_direction(expansion_direction)
    samples = _sample_inputs(seed, train_count + query_count, difficulty)
    pairs = [
        {
            "input": row["grid"],
            "output": python_mirror(
                row["grid"], expansion_direction=expansion_direction
            ),
        }
        for row in samples
    ]
    return {
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "program_solution": program_for(expansion_direction, root=root),
    }


def make_episode(
    seed: int,
    *,
    expansion_direction: str | None = None,
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
    selected = select_setting(seed) if expansion_direction is None else expansion_direction
    _validate_direction(selected)
    rival = next(value for value in ALLOWED_DIRECTIONS if value != selected)

    samples = _sample_inputs(seed, train_count + query_count, difficulty)
    programs = {direction: program_for(direction, root=root) for direction in ALLOWED_DIRECTIONS}
    outputs = {direction: [] for direction in ALLOWED_DIRECTIONS}

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        for row in samples:
            grid = row["grid"]
            for direction in ALLOWED_DIRECTIONS:
                output = execute_rule(programs[direction], grid, bridge=active)
                mirror = python_mirror(grid, expansion_direction=direction)
                if output != mirror:
                    raise AssertionError(
                        f"Racket/Python parity failed for direction {direction}"
                    )
                outputs[direction].append(output)
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
    status = (
        "refuted_by_demonstrations"
        if demo_mismatches
        else "ambiguous_query"
    )
    program = programs[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"expansion_direction": selected},
        "seed": seed,
        "difficulty": difficulty,
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_program_sha256": normalized_program_sha256(program),
        "selection_scope": "once_per_episode",
        "sampling": [
            {key: row[key] for key in ("input_sha256", "input_seed", "sample_index")}
            for row in samples
        ],
        "parameter_rivals": [
            {
                "expansion_direction": rival,
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        ],
        "ambiguities": (
            []
            if status == "refuted_by_demonstrations"
            else [{"expansion_direction": rival, "reason": status}]
        ),
        "source": {
            "generator_path": str(GENERATOR_PATH.relative_to(root)),
            "generator_sha256": GENERATOR_SHA256,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and answer-free query inputs."""
    return json.loads(_public_challenge_bytes(episode))


def public_bytes(episode: dict[str, Any]) -> bytes:
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(episode)



def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _difference_coordinates(left, right):
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("comparison grids must have matching dimensions")
    return [
        [r, c]
        for r, (lrow, rrow) in enumerate(zip(left, right))
        for c, (lvalue, rvalue) in enumerate(zip(lrow, rrow))
        if lvalue != rvalue
    ]


def write_evidence(
    *,
    seed: int,
    out: Path,
    root: Path = ROOT,
    difficulty: str = "medium",
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write source-bound private/public evidence for both proposed settings."""
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    try:
        episodes = []
        pending_public = []
        distinct_inputs = set()
        canonical_rows = []
        private_episodes = {}
        bridge_context = RacketBridge() if bridge is None else nullcontext(bridge)
        with bridge_context as active_bridge:
            runtime_identity = active_bridge.runtime_identity
            canonical_program = program_for(DEFAULT_DIRECTION, root=root)
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(
                    canonical_program, pair["input"], bridge=active_bridge
                )
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
                raise AssertionError("canonical up program failed a labelled canonical pair")

            for direction in ALLOWED_DIRECTIONS:
                episode = make_episode(
                    seed,
                    expansion_direction=direction,
                    difficulty=difficulty,
                    train_count=train_count,
                    query_count=query_count,
                    root=root,
                    bridge=active_bridge,
                )
                rule_rel = Path("private/rules") / f"expansion-{direction}.rkt"
                private_rel = Path("private") / f"episode-{direction}.json"
                rule_path = temp / rule_rel
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(episode["program"], encoding="utf-8")

                private = dict(episode)
                private["racket_path"] = rule_rel.as_posix()
                private["racket_sha256"] = _file_sha256(rule_path)
                _write_json(temp / private_rel, private)
                private_episodes[direction] = private

                visible_id = public_id(private)
                public_rel = Path("public") / f"challenge-{visible_id}.json"
                pending_public.append(
                    {
                        "direction": direction,
                        "private": private,
                        "private_rel": private_rel,
                        "public_id": visible_id,
                        "public_rel": public_rel,
                        "public_bytes": public_bytes(private),
                        "rule_rel": rule_rel,
                        "rule_path": rule_path,
                    }
                )

                for pair in private["train"] + private["test"]:
                    distinct_inputs.add(grid_sha256(pair["input"]))

            public_ids = [row["public_id"] for row in pending_public]
            if len(public_ids) != len(set(public_ids)):
                raise ValueError("duplicate public challenge id")
            for row in pending_public:
                if hashlib.sha256(row["public_bytes"]).hexdigest() != row["public_id"]:
                    raise ValueError("public identifier does not hash exact visible bytes")

            for row in sorted(pending_public, key=lambda item: item["public_id"]):
                public_path = temp / row["public_rel"]
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(row["public_bytes"])
                row["public_path"] = public_path

            for row in pending_public:
                private = row["private"]
                rival = private["parameter_rivals"][0]
                episodes.append(
                    {
                        "expansion_direction": row["direction"],
                        "seed": seed,
                        "difficulty": difficulty,
                        "train_count": len(private["train"]),
                        "query_count": len(private["test"]),
                        "private_path": row["private_rel"].as_posix(),
                        "private_sha256": _file_sha256(temp / row["private_rel"]),
                        "public_path": row["public_rel"].as_posix(),
                        "public_sha256": _file_sha256(row["public_path"]),
                        "public_id": row["public_id"],
                        "racket_path": row["rule_rel"].as_posix(),
                        "racket_sha256": _file_sha256(row["rule_path"]),
                        "normalized_racket_sha256": private["normalized_program_sha256"],
                        "rival_status": rival["status"],
                        "rival_demonstration_mismatch_indices": rival[
                            "demonstration_mismatch_indices"
                        ],
                        "rival_query_mismatch_indices": rival["query_mismatch_indices"],
                    }
                )

            up_inputs = [
                pair["input"]
                for pair in private_episodes["up"]["train"] + private_episodes["up"]["test"]
            ]
            down_inputs = [
                pair["input"]
                for pair in private_episodes["down"]["train"]
                + private_episodes["down"]["test"]
            ]
            if up_inputs != down_inputs:
                raise AssertionError("direction setting changed the episode input draws")
            witness_input = up_inputs[0]
            witness_outputs = {
                direction: execute_rule(
                    program_for(direction, root=root),
                    witness_input,
                    bridge=active_bridge,
                )
                for direction in ALLOWED_DIRECTIONS
            }

        witness = {
            "schema": "arcpuzzles-parametric-setting-witness-v1",
            "task_id": TASK_ID,
            "parameter": "expansion_direction",
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                direction: grid_sha256(output)
                for direction, output in witness_outputs.items()
            },
            "difference_coordinates": _difference_coordinates(
                witness_outputs["up"], witness_outputs["down"]
            ),
        }
        if not witness["difference_coordinates"]:
            raise AssertionError("retained witness does not separate direction settings")
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
                "name": "expansion_direction",
                "allowed_values": list(ALLOWED_DIRECTIONS),
                "original_default": DEFAULT_DIRECTION,
                "selection_scope": "once_per_episode",
                "input_constraints_depend_on_parameter": False,
            },
            "reasoning_invariants": [
                "locate one contiguous vertical color-7 source",
                "use the endpoint facing the selected expansion direction as the apex",
                "paint a canvas-clipped triangle whose reach grows one cell per row",
                "alternate 7 and 8 by horizontal distance from the source column",
                "write zero outside the triangle",
            ],
            "episodes": episodes,
            "runtime": runtime_identity,
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
                "normalized_program_sha256": normalized_program_sha256(canonical_program),
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
                "finite declared-rival evidence does not prove unique induction",
                "the prototype is separate from canonical generate(), approval, and training admission",
                "inputs retain the selected generator's 5..16 by 7..18 domain",
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
        description="Materialize and Racket-verify both expansion-direction settings."
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
