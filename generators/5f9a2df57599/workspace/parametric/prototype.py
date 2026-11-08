#!/usr/bin/env python3
"""Proposed episode-level side-boundary extension for ARC task 5f9a2df57599.

The canonical rule treats the left and right canvas edges as valid walls around
zero components.  This task-local prototype keeps every other predicate fixed
and adds one episode-level policy: preserve that canonical edge behavior or
require literal gray side walls.  It does not modify the production generator,
canonical ledger, catalog, approval state, or training admission.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5f9a2df57599"
PROTOTYPE_VERSION = "1.0.0"
SCHEMA = "arcpuzzles-side-boundary-prototype-v1"
STATUS = "proposed_unapproved"
SIDE_POLICIES = ("canvas_edges", "gray_walls")
CANONICAL_POLICY = "canvas_edges"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_EPISODE_COUNT = 8
GENERATOR_SHA256 = "f641de5c1ef15a254272dce952d0951d29a2be87c6d88873638543dcac41a51e"
CANONICAL_RULE_HASH = "5b73d3931a5c"
CANONICAL_RAW_SHA256 = "e8cf01347e8f1013e5af75c1170767e3bac1afd1974dca142f8ff406e41672bd"

LEFT_CANONICAL_ANCHOR = "(left-wall (or (zero? c1) "
LEFT_STRICT_ANCHOR = "(left-wall (and (> c1 0) "
RIGHT_CANONICAL_ANCHOR = "(right-wall (or (= c2 (- w 1)) "
RIGHT_STRICT_ANCHOR = "(right-wall (and (< c2 (- w 1)) "

_DEMO_PROFILES = (
    "left_n1",
    "right_n1",
    "rect_n2",
    "mixed_n2",
    "irregular_n1",
    "left_n1",
    "right_n1",
    "rect_n3",
)
_QUERY_PROFILES = (
    "left_n1",
    "right_n1",
    "mixed_n2",
    "irregular_n2",
    "rect_n3",
    "mixed_n3",
    "left_n1",
    "right_n1",
)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain integer")
    return seed


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int or not 1 <= value <= MAX_EPISODE_COUNT:
        raise ValueError(f"{name} must be a plain integer in 1..{MAX_EPISODE_COUNT}")
    return value


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str or policy not in SIDE_POLICIES:
        raise ValueError(f"side_boundary_policy must be one of {SIDE_POLICIES}")
    return policy


def choose_policy(seed: Any, policy: Any = None) -> str:
    """Choose one deterministic episode policy, or validate an explicit one."""
    validated_seed = _validate_seed(seed)
    if policy is not None:
        return _validate_policy(policy)
    return SIDE_POLICIES[validated_seed % len(SIDE_POLICIES)]


def canonical_record(*, root: Path | str | None = None) -> dict[str, Any]:
    """Load the unique canonical ledger row and verify its exact rule binding."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    rows: list[dict[str, Any]] = []
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, got {len(rows)}")
    source = rows[0].get("program_solution")
    if not isinstance(source, str):
        raise ValueError("canonical row is missing Racket program_solution")
    if _sha256(source) != CANONICAL_RAW_SHA256:
        raise ValueError("canonical raw Racket source hash drifted")
    normalized = " ".join(source.split())
    if _sha256(normalized)[:12] != CANONICAL_RULE_HASH:
        raise ValueError("canonical normalized Racket rule hash drifted")
    if normalized.count(LEFT_CANONICAL_ANCHOR) != 1:
        raise ValueError("canonical source lacks unique left-wall anchor")
    if normalized.count(RIGHT_CANONICAL_ANCHOR) != 1:
        raise ValueError("canonical source lacks unique right-wall anchor")
    return rows[0]


def materialize_program(
    policy: Any = CANONICAL_POLICY,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize a policy while preserving exact canonical bytes by default."""
    selected = _validate_policy(policy)
    canonical = canonical_record(root=root)["program_solution"]
    if selected == CANONICAL_POLICY:
        return canonical
    normalized = " ".join(canonical.split())
    strict = normalized.replace(LEFT_CANONICAL_ANCHOR, LEFT_STRICT_ANCHOR, 1)
    strict = strict.replace(RIGHT_CANONICAL_ANCHOR, RIGHT_STRICT_ANCHOR, 1)
    if strict.count(LEFT_STRICT_ANCHOR) != 1 or strict.count(RIGHT_STRICT_ANCHOR) != 1:
        raise AssertionError("failed to materialize strict side-wall predicates")
    return strict


def _rule_callable(source: Any) -> str:
    if not isinstance(source, str) or not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("Racket source must be a wrapped rule! lambda")
    callable_source = source[len("(rule!") : -1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("Racket rule must wrap a one-grid lambda")
    return callable_source


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 8 <= len(grid) <= 30:
        raise ValueError("grid must contain 8..30 rows")
    if type(grid[0]) is not list or not 8 <= len(grid[0]) <= 30:
        raise ValueError("grid must contain 8..30 columns")
    width = len(grid[0])
    normalized: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or value not in (0, 5) for value in row):
            raise ValueError("grid cells must be exact integers 0 or 5")
        normalized.append(list(row))
    return normalized


def _racket_grid_literal(grid: Any) -> str:
    normalized = _validate_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in normalized
    ) + ")"


def execute(bridge: RacketBridge, source: str, grid: Any) -> list[list[int]]:
    """Execute one materialized Racket rule on one validated input grid."""
    expression = f"({_rule_callable(source)} '{_racket_grid_literal(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def _zero_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 0
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        reached = {start}
        frontier = [start]
        while frontier:
            row, column = frontier.pop()
            for delta_row, delta_column in _ORTHOGONAL:
                neighbour = row + delta_row, column + delta_column
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(reached)
    return components


def python_apply(grid: Any, policy: Any = CANONICAL_POLICY) -> list[list[int]]:
    """Independent Python oracle for the two declared side-boundary policies."""
    normalized = _validate_grid(grid)
    selected = _validate_policy(policy)
    height, width = len(normalized), len(normalized[0])
    output = deepcopy(normalized)
    for cells in _zero_components(normalized):
        row0 = min(row for row, _ in cells)
        row1 = max(row for row, _ in cells)
        column0 = min(column for _, column in cells)
        column1 = max(column for _, column in cells)
        top_wall = row0 > 0 and all(
            normalized[row0 - 1][column] == 5
            for column in range(column0, column1 + 1)
        )
        bottom_wall = row1 < height - 1 and all(
            normalized[row1 + 1][column] == 5
            for column in range(column0, column1 + 1)
        )
        if selected == "canvas_edges":
            left_wall = column0 == 0 or all(
                normalized[row][column0 - 1] == 5
                for row in range(row0, row1 + 1)
            )
            right_wall = column1 == width - 1 or all(
                normalized[row][column1 + 1] == 5
                for row in range(row0, row1 + 1)
            )
        else:
            left_wall = column0 > 0 and all(
                normalized[row][column0 - 1] == 5
                for row in range(row0, row1 + 1)
            )
            right_wall = column1 < width - 1 and all(
                normalized[row][column1 + 1] == 5
                for row in range(row0, row1 + 1)
            )
        excluded_left_vertical = column0 == 0 and column1 == 0 and row1 > row0
        if top_wall and bottom_wall and left_wall and right_wall and not excluded_left_vertical:
            for row, column in cells:
                output[row][column] = 4
    return output


def _grid_hash(grid: Any) -> str:
    return _sha256(_stable_json(_validate_grid(grid)))


def _generate_inputs(
    seed: int,
    demo_count: int,
    query_count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    generator, generator_path, source_hash = load_selected_generator(TASK_ID, root=root)
    if source_hash != GENERATOR_SHA256:
        raise ValueError(f"selected generator hash drifted: {source_hash}")

    seen: set[str] = set()

    def build(kind: str, profiles: tuple[str, ...], count: int, offset: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for index in range(count):
            profile = profiles[index]
            for attempt in range(100):
                request_seed = seed * 1_000_003 + offset + index * 7_919 + attempt * 101 + 17
                sample_index = seed * 65_537 + offset * 3 + index * 193 + attempt * 17 + 29
                grid = generator.generate(
                    request_seed,
                    sample_index,
                    difficulty="medium",
                    scene_profile=profile,
                )
                errors = generator.self_check(grid, difficulty="medium")
                if errors:
                    raise AssertionError(f"generator returned invalid {profile} scene: {errors}")
                digest = _grid_hash(grid)
                if digest in seen:
                    continue
                seen.add(digest)
                rows.append(
                    {
                        "kind": kind,
                        "index": index,
                        "scene_profile": profile,
                        "input": grid,
                        "input_sha256": digest,
                        "generator_request": {
                            "seed": request_seed,
                            "sample_index": sample_index,
                            "difficulty": "medium",
                            "scene_profile": profile,
                        },
                    }
                )
                break
            else:
                raise RuntimeError(f"could not generate distinct {kind} input {index}")
        return rows

    demos = build("demonstration", _DEMO_PROFILES, demo_count, 10_000)
    queries = build("query", _QUERY_PROFILES, query_count, 90_000)
    source = {
        "path": generator_path.relative_to(root).as_posix(),
        "sha256": source_hash,
    }
    return demos, queries, source


def make_episode(
    seed: Any,
    *,
    policy: Any = None,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one fixed-policy lesson with separate demonstrations and queries."""
    validated_seed = _validate_seed(seed)
    demos = _validate_count(demo_count, "demo_count")
    queries = _validate_count(query_count, "query_count")
    selected = choose_policy(validated_seed, policy)
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    demo_rows, query_rows, source = _generate_inputs(
        validated_seed, demos, queries, root=resolved_root
    )
    rows = demo_rows + query_rows
    programs = {
        candidate: materialize_program(candidate, root=resolved_root)
        for candidate in SIDE_POLICIES
    }
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        outputs = {
            candidate: [execute(active, program, row["input"]) for row in rows]
            for candidate, program in programs.items()
        }
    for candidate in SIDE_POLICIES:
        expected = [python_apply(row["input"], candidate) for row in rows]
        if outputs[candidate] != expected:
            raise AssertionError(f"Racket/Python mismatch for policy {candidate}")

    train = [
        {"input": deepcopy(row["input"]), "output": deepcopy(outputs[selected][index])}
        for index, row in enumerate(demo_rows)
    ]
    test = [
        {
            "input": deepcopy(row["input"]),
            "output": deepcopy(outputs[selected][demos + index]),
        }
        for index, row in enumerate(query_rows)
    ]
    rivals: list[dict[str, Any]] = []
    for candidate in SIDE_POLICIES:
        demo_mismatches = [
            index
            for index in range(demos)
            if outputs[candidate][index] != outputs[selected][index]
        ]
        query_mismatches = [
            index
            for index in range(queries)
            if outputs[candidate][demos + index] != outputs[selected][demos + index]
        ]
        rivals.append(
            {
                "side_boundary_policy": candidate,
                "status": (
                    "matches_episode" if not demo_mismatches else "refuted_by_demonstrations"
                ),
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )
    matching = [row["side_boundary_policy"] for row in rivals if row["status"] == "matches_episode"]
    ambiguities = [] if matching == [selected] else [{"matching_policies": matching}]
    if ambiguities:
        raise AssertionError(f"demonstrations did not identify policy: {ambiguities}")

    selected_program = programs[selected]
    episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": STATUS,
        "approved": False,
        "seed": validated_seed,
        "parameters": {"side_boundary_policy": selected},
        "parameter_contract": {
            "side_boundary_policy": {
                "allowed": list(SIDE_POLICIES),
                "default": CANONICAL_POLICY,
                "episode_fixed": True,
                "input_constraints_depend_on_parameter": False,
            }
        },
        "counts": {"demonstrations": demos, "queries": queries},
        "source": source,
        "rule": {
            "racket_source": selected_program,
            "sha256": _sha256(selected_program),
        },
        "rules": {
            candidate: {
                "racket_source": programs[candidate],
                "sha256": _sha256(programs[candidate]),
            }
            for candidate in SIDE_POLICIES
        },
        "fixtures": {
            "demonstrations": deepcopy(demo_rows),
            "queries": deepcopy(query_rows),
        },
        "train": train,
        "test": test,
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }
    episode["public_id"] = public_challenge_id(episode)
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a detached public view with demonstrations and query inputs only."""
    return json.loads(public_challenge_bytes(episode).decode("utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_row(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(base).as_posix(),
        "sha256": _sha256(path.read_bytes()),
        "bytes": path.stat().st_size,
    }


def _seeds_for_both_policies(seed_start: int) -> list[int]:
    found: dict[str, int] = {}
    for seed in range(seed_start, seed_start + 1_000):
        found.setdefault(choose_policy(seed), seed)
        if len(found) == len(SIDE_POLICIES):
            return [found[policy] for policy in SIDE_POLICIES]
    raise RuntimeError("could not find one deterministic seed per policy")


def write_evidence(
    out: Path | str,
    *,
    seed_start: Any = 0,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Write source-bound private/public evidence for both policy settings."""
    validated_seed_start = _validate_seed(seed_start)
    demos = _validate_count(demo_count, "demo_count")
    queries = _validate_count(query_count, "query_count")
    destination = Path(out).resolve()
    if destination.exists():
        raise FileExistsError(f"output directory already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + ".tmp")
    if staging.exists():
        raise FileExistsError(f"staging directory already exists: {staging}")
    staging.mkdir()

    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    programs = {
        policy: materialize_program(policy, root=resolved_root)
        for policy in SIDE_POLICIES
    }
    seeds = _seeds_for_both_policies(validated_seed_start)
    try:
        with RacketBridge(timeout=20, startup_timeout=60) as bridge:
            canonical = canonical_pairs(TASK_ID, root=resolved_root, labeled_only=True)
            if len(canonical) != 4:
                raise AssertionError(f"expected four labeled canonical pairs, got {len(canonical)}")
            for index, pair in enumerate(canonical):
                racket_output = execute(bridge, programs[CANONICAL_POLICY], pair["input"])
                python_output = python_apply(pair["input"], CANONICAL_POLICY)
                if racket_output != pair["output"] or python_output != pair["output"]:
                    raise AssertionError(f"canonical pair {index} failed exact default reproduction")

            episodes = [
                make_episode(
                    seed,
                    demo_count=demos,
                    query_count=queries,
                    root=resolved_root,
                    bridge=bridge,
                )
                for seed in seeds
            ]

        for policy, source in programs.items():
            path = staging / "rules" / f"{policy}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

        episode_rows: list[dict[str, Any]] = []
        for episode in episodes:
            public = public_challenge(episode)
            content_id = public_challenge_id(episode)
            filename = f"{content_id}.json"
            public_path = staging / "public" / filename
            private_path = staging / "private" / filename
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_challenge_bytes(public))
            _write_json(private_path, episode)
            episode_rows.append(
                {
                    "seed": episode["seed"],
                    "public_id": content_id,
                    "parameters": episode["parameters"],
                    "public_path": public_path.relative_to(staging).as_posix(),
                    "private_path": private_path.relative_to(staging).as_posix(),
                    "parameter_rivals": episode["parameter_rivals"],
                }
            )

        ambiguity_count = sum(len(episode["ambiguities"]) for episode in episodes)
        report = {
            "schema": SCHEMA,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "status": STATUS,
            "approved": False,
            "scope": "task-local proposed prototype only",
            "parameters": {
                "side_boundary_policy": {
                    "allowed": list(SIDE_POLICIES),
                    "default": CANONICAL_POLICY,
                    "episode_fixed": True,
                    "input_constraints_depend_on_parameter": False,
                }
            },
            "counts": {
                "episodes": 2,
                "episode_settings_exercised": 2,
                "demonstrations_per_episode": demos,
                "queries_per_episode": queries,
                "train_pairs": 2 * demos,
                "query_pairs": 2 * queries,
                "canonical_pairs_checked": len(canonical),
                "ambiguous_parameter_rivals": ambiguity_count,
            },
            "canonical": {
                "raw_sha256": CANONICAL_RAW_SHA256,
                "normalized_rule_hash": CANONICAL_RULE_HASH,
            },
            "generator": {
                "path": episodes[0]["source"]["path"],
                "sha256": episodes[0]["source"]["sha256"],
            },
            "prototype": {
                "path": Path(__file__).resolve().relative_to(resolved_root).as_posix(),
                "sha256": _sha256(Path(__file__).read_bytes()),
            },
            "rules": {
                policy: {
                    "path": f"rules/{policy}.rkt",
                    "sha256": _sha256(source),
                }
                for policy, source in programs.items()
            },
            "episodes": episode_rows,
            "limits": [
                "finite evidence covers two deterministic seeds and one declared binary parameter",
                "prototype does not change production generation, canonical authority, approval, or training admission",
            ],
        }
        _write_json(staging / "report.json", report)
        files = [
            _file_row(path, staging)
            for path in sorted(staging.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        ]
        _write_json(
            staging / "manifest.json",
            {
                "schema": "arcpuzzles-side-boundary-evidence-manifest-v1",
                "files": files,
            },
        )
        staging.replace(destination)
        return report
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    args = parser.parse_args(argv)
    report = write_evidence(
        args.out,
        seed_start=args.seed_start,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
