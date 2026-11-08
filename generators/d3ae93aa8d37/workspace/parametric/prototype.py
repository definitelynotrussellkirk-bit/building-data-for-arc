"""Task-local shortest-path tie-break prototype for ARC task d3ae93aa8d37.

The endpoints, walls, shortest-path objective, and cyan painting stay fixed.
One hidden episode-level parameter changes only the order in which equally
short BFS branches are explored:

* ``canonical_udlr`` (canonical/default): up, down, left, right.
* ``horizontal_first`` (proposed): left, right, up, down.

Every retained input has at least one horizontal and one vertical displacement,
keeps a Manhattan-length route open, and yields distinct equal-length outputs
under the two policies.  The production canonical authority is never modified.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "d3ae93aa8d37"
PROTOTYPE_VERSION = "path-tiebreak-prototype-v1"
ALLOWED_POLICIES = ("canonical_udlr", "horizontal_first")
DEFAULT_POLICY = "canonical_udlr"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4

_CANONICAL_NEIGHBORS = "cardinal-deltas"
_HORIZONTAL_NEIGHBORS = (
    "(list (list 0 -1) (list 0 1) (list -1 0) (list 1 0))"
)
_DIRECTION_ORDERS = {
    "canonical_udlr": ((-1, 0), (1, 0), (0, -1), (0, 1)),
    "horizontal_first": ((0, -1), (0, 1), (-1, 0), (1, 0)),
}


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str or policy not in ALLOWED_POLICIES:
        raise ValueError(
            f"path_tiebreak must be one of {ALLOWED_POLICIES}, got {policy!r}"
        )
    return policy


def _validate_counts(demo_count: Any, query_count: Any) -> tuple[int, int]:
    if type(demo_count) is not int or not 2 <= demo_count <= 6:
        raise ValueError("demo_count must be a literal integer in 2..6")
    if type(query_count) is not int or query_count != 4:
        raise ValueError("query_count must be the literal integer 4")
    return demo_count, query_count


def canonical_program() -> str:
    """Return the exact base canonical Racket program from this source tree."""
    from reviewer_support import canonical_path, find_root

    matches = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("content_hash") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one base canonical row for {TASK_ID}, found {len(matches)}"
        )
    return matches[0]["program_solution"].strip()


def rule_source(policy: Any = DEFAULT_POLICY) -> str:
    """Materialize exact Racket source for one BFS tie-break policy."""
    selected = _validate_policy(policy)
    source = canonical_program()
    if selected == DEFAULT_POLICY:
        return source
    if source.count(_CANONICAL_NEIGHBORS) != 1:
        raise RuntimeError("canonical neighbor order is not uniquely replaceable")
    return source.replace(_CANONICAL_NEIGHBORS, _HORIZONTAL_NEIGHBORS, 1)


def _validate_grid(grid: Any) -> tuple[int, int, tuple[int, int], tuple[int, int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(cell) is not int or cell not in (0, 2, 3, 5)
        for row in grid
        for cell in row
    ):
        raise ValueError("input cells must be literal integers from {0,2,3,5}")
    reds = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 2
    ]
    greens = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 3
    ]
    if len(reds) != 1 or len(greens) != 1:
        raise ValueError(
            f"expected exactly one red and one green endpoint, found {len(reds)}, {len(greens)}"
        )
    return height, width, reds[0], greens[0]


def _shortest_path(grid: list[list[int]], policy: Any) -> list[tuple[int, int]]:
    selected = _validate_policy(policy)
    height, width, start, goal = _validate_grid(grid)
    queue: deque[tuple[int, int]] = deque([start])
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            path: list[tuple[int, int]] = []
            cursor: tuple[int, int] | None = current
            while cursor is not None:
                path.append(cursor)
                cursor = parents[cursor]
            return list(reversed(path))
        row, column = current
        for dr, dc in _DIRECTION_ORDERS[selected]:
            neighbor = (row + dr, column + dc)
            nr, nc = neighbor
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and neighbor not in parents
            ):
                parents[neighbor] = current
                queue.append(neighbor)
    raise ValueError("red and green endpoints are disconnected")


def shortest_path_length(grid: list[list[int]], policy: Any = DEFAULT_POLICY) -> int:
    """Return edge count for the path selected by one policy."""
    return len(_shortest_path(grid, policy)) - 1


def python_mirror(grid: list[list[int]], policy: Any = DEFAULT_POLICY) -> list[list[int]]:
    """Independent Python mirror of both exact Racket tie-break settings."""
    path = _shortest_path(grid, policy)
    output = deepcopy(grid)
    for row, column in path[1:-1]:
        output[row][column] = 8
    return output


def _stream_rng(seed: Any, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def policy_for_seed(seed: Any) -> str:
    """Choose the hidden rule once from a rule-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_POLICIES)


def _load_parent_generator():
    from reviewer_support import find_root, load_selected_generator

    module, _path, _sha256 = load_selected_generator(
        TASK_ID, root=find_root(__file__)
    )
    return module


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _profile(pair_index: int, total: int) -> tuple[int, int, int, str]:
    if pair_index == total - 1:
        return 30, 30, 18, "hard"
    profiles = (
        (6, 6, 4, "easy"),
        (8, 9, 5, "easy"),
        (10, 11, 7, "medium"),
        (12, 13, 8, "medium"),
        (14, 15, 9, "hard"),
        (16, 14, 10, "hard"),
        (18, 17, 11, "hard"),
        (20, 19, 12, "hard"),
        (24, 23, 15, "hard"),
    )
    return profiles[pair_index % len(profiles)]


def _endpoint_distance(grid: list[list[int]]) -> int:
    _height, _width, start, goal = _validate_grid(grid)
    return abs(start[0] - goal[0]) + abs(start[1] - goal[1])


def _tie_is_observable(grid: list[list[int]]) -> bool:
    _height, _width, start, goal = _validate_grid(grid)
    if start[0] == goal[0] or start[1] == goal[1]:
        return False
    distance = _endpoint_distance(grid)
    return (
        shortest_path_length(grid, "canonical_udlr") == distance
        and shortest_path_length(grid, "horizontal_first") == distance
        and python_mirror(grid, "canonical_udlr")
        != python_mirror(grid, "horizontal_first")
    )


def sample_inputs(
    seed: Any,
    *,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> list[list[list[int]]]:
    """Draw distinct lawful parent inputs with observable shortest-path ties."""
    demo_count, query_count = _validate_counts(demo_count, query_count)
    rng = _stream_rng(seed, "inputs")
    parent = _load_parent_generator()
    total = demo_count + query_count
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()

    for pair_index in range(total):
        height, width, distance, difficulty = _profile(pair_index, total)
        for _attempt in range(500):
            generated_seed = rng.randrange(0, 2**63)
            grid = parent.generate(
                generated_seed,
                pair_index,
                difficulty=difficulty,
                grid_h=height,
                grid_w=width,
                n_walls=0,
                distance=distance,
                scene_profile="open_path",
                position_bias="offset",
            )
            errors = parent.self_check(grid)
            if errors:
                raise RuntimeError(f"parent generator emitted invalid input: {errors}")
            key = _json_key(grid)
            if key in seen or not _tie_is_observable(grid):
                continue
            seen.add(key)
            inputs.append(deepcopy(grid))
            break
        else:
            raise RuntimeError(
                f"could not draw distinct tie-separating input {pair_index + 1}/{total}"
            )
    return inputs


def sample_episode(
    seed: Any,
    *,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    demo_count, query_count = _validate_counts(demo_count, query_count)
    policy = policy_for_seed(seed)
    inputs = sample_inputs(seed, demo_count=demo_count, query_count=query_count)
    digest = hashlib.sha256(
        _json_key({"seed": seed, "inputs": inputs}).encode("utf-8")
    ).hexdigest()
    return {
        "episode_id": f"episode-{digest[:16]}",
        "seed": seed,
        "parameters": {"path_tiebreak": policy},
        "program": rule_source(policy),
        "inputs": inputs,
        "demo_count": demo_count,
        "query_count": query_count,
    }


def select_seeds(base_seed: Any) -> dict[str, Any]:
    if type(base_seed) is not int:
        raise TypeError("base_seed must be a literal integer")
    found: dict[str, int] = {}
    examined = 0
    for seed in range(base_seed, base_seed + 1000):
        examined += 1
        found.setdefault(policy_for_seed(seed), seed)
        if set(found) == set(ALLOWED_POLICIES):
            break
    if set(found) != set(ALLOWED_POLICIES):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_path_tiebreak": {policy: found[policy] for policy in ALLOWED_POLICIES},
        "seeds": [found[policy] for policy in ALLOWED_POLICIES],
    }


def public_challenge(
    pairs: list[dict[str, Any]], *, demo_count: int = DEFAULT_DEMO_COUNT
) -> dict[str, Any]:
    if type(pairs) is not list or not pairs:
        raise ValueError("pairs must be a non-empty list")
    if type(demo_count) is not int or not 0 < demo_count < len(pairs):
        raise ValueError("demo_count must leave at least one query pair")
    try:
        return {
            "train": [
                {
                    "input": deepcopy(pair["input"]),
                    "output": deepcopy(pair["output"]),
                }
                for pair in pairs[:demo_count]
            ],
            "test": [
                {"input": deepcopy(pair["input"])} for pair in pairs[demo_count:]
            ],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("each pair requires input and output grids") from exc


def public_id(challenge: dict[str, Any]) -> str:
    from reviewer_support import public_challenge_id

    return public_challenge_id(challenge)


def score_rival(
    predictions: dict[str, list[list[list[int]]]],
    *,
    chosen_policy: Any,
    demo_count: int = DEFAULT_DEMO_COUNT,
) -> dict[str, Any]:
    chosen = _validate_policy(chosen_policy)
    if set(predictions) != set(ALLOWED_POLICIES):
        raise ValueError("predictions must cover every declared path_tiebreak")
    lengths = {len(outputs) for outputs in predictions.values()}
    if len(lengths) != 1:
        raise ValueError("prediction lengths must agree")
    length = lengths.pop()
    if type(demo_count) is not int or not 0 < demo_count < length:
        raise ValueError("demo_count must leave at least one query")
    rival = next(policy for policy in ALLOWED_POLICIES if policy != chosen)
    demonstration_mismatches = [
        index
        for index in range(demo_count)
        if predictions[rival][index] != predictions[chosen][index]
    ]
    query_disagreements = [
        index
        for index in range(demo_count, length)
        if predictions[rival][index] != predictions[chosen][index]
    ]
    status = (
        "refuted_by_demonstrations"
        if demonstration_mismatches
        else "ambiguous_queries"
        if query_disagreements
        else "survived_all"
    )
    return {
        "chosen_policy": chosen,
        "rival_policy": rival,
        "status": status,
        "demonstration_indices": list(range(demo_count)),
        "query_indices": list(range(demo_count, length)),
        "demonstration_mismatches": demonstration_mismatches,
        "query_disagreements": query_disagreements,
    }


LIMITATIONS = [
    "Task-local prototype only; it does not change the selected canonical authority, catalog entry, approval state, or training admission.",
    "path_tiebreak=canonical_udlr is the exact base canonical Racket source after stripping outer whitespace.",
    "Only equal-length BFS branch order varies; endpoints, walls, reachability, shortest-path objective, endpoint preservation, and cyan interior painting remain fixed.",
    "Every retained input passes the selected production generator self_check, has a Manhattan-length route under both policies, and separates their outputs.",
    "Evidence covers one episode per setting, 2-6 demonstrations, exactly four distinct queries, and the single declared rival.",
    "Finite pairwise evidence does not prove uniqueness against arbitrary ARC programs or behavior outside the parent-generator domain.",
]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256(_json_key(value).encode("utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_bindings() -> dict[str, str]:
    from arc_repl import isolated_verifier, racket_bridge
    from reviewer_support import canonical_path, find_root

    here = Path(__file__).resolve()
    root = find_root(here)
    task_home = here.parents[2]
    paths = [
        here,
        task_home / "generator.py",
        task_home / "tests/test_parametric_path_tiebreak.py",
        canonical_path(root),
        Path(isolated_verifier.__file__).resolve(),
        Path(racket_bridge.__file__).resolve(),
        Path(racket_bridge.__file__).with_name("executor.py").resolve(),
        Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt",
    ]
    result = {}
    for path in paths:
        resolved = path.resolve(strict=True)
        result[resolved.relative_to(root).as_posix()] = _sha256(resolved.read_bytes())
    return result


def run_evidence(
    out: Path,
    *,
    base_seed: int = 20261024,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    racket_path: str | Path | None = None,
    verifier=None,
) -> dict[str, Any]:
    """Execute both Racket programs and retain fail-closed source-bound evidence."""
    demo_count, query_count = _validate_counts(demo_count, query_count)
    if verifier is None:
        from arc_repl.isolated_verifier import verify_candidate

        verifier = verify_candidate

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    report: dict[str, Any] = {
        "schema": "parametric-path-tiebreak-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "path_tiebreak",
            "allowed_values": list(ALLOWED_POLICIES),
            "original_default": DEFAULT_POLICY,
            "sampling_unit": "once per episode from a rule-only deterministic seed stream",
            "demo_count": demo_count,
            "query_count": query_count,
            "invariant_reasoning_steps": [
                "find the unique red start and green goal",
                "run breadth-first search through non-wall orthogonal neighbors",
                "reconstruct one shortest path from the first discovered parents",
                "paint only the path interior cyan while preserving endpoints and walls",
            ],
            "dependent_input_constraints": [
                "input passes the selected production generator self_check",
                "both row and column endpoint displacements are nonzero",
                "both declared policies retain a Manhattan-length path",
                "the two declared settings produce different outputs on every retained input",
            ],
        },
        "seed_selection": None,
        "rules": [],
        "episodes": [],
        "limitations": LIMITATIONS,
        "invocation": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    _write_json(out / "report.json", report)

    try:
        selection = select_seeds(base_seed)
        report["seed_selection"] = selection
        report["source_sha256"] = _source_bindings()

        selected_racket = (
            str(racket_path)
            if racket_path is not None
            else os.environ.get("RACKET_PATH", "")
        )
        binary = Path(selected_racket).expanduser().resolve(strict=True)
        if not binary.is_file():
            raise FileNotFoundError(f"Racket path is not a file: {binary}")
        report["runtime"] = {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary),
            "racket_sha256": _sha256(binary.read_bytes()),
            "controlled_verifier": verifier.__module__ != "arc_repl.isolated_verifier",
        }

        canonical = canonical_program()
        if rule_source(DEFAULT_POLICY) != canonical:
            raise RuntimeError("default program no longer equals the base canonical source")

        episodes = [
            sample_episode(seed, demo_count=demo_count, query_count=query_count)
            for seed in selection["seeds"]
        ]
        total_per_episode = demo_count + query_count
        execution_inputs = [
            {
                "episode_id": episode["episode_id"],
                "pair_index": pair_index,
                "role": "demonstration" if pair_index < demo_count else "query",
                "input": grid,
                "input_sha256": _json_sha256(grid),
            }
            for episode in episodes
            for pair_index, grid in enumerate(episode["inputs"])
        ]
        _write_json(out / "private/execution_inputs.json", execution_inputs)

        predictions: dict[str, list[list[list[int]]]] = {}
        parity_matches = 0
        for policy in ALLOWED_POLICIES:
            program = rule_source(policy)
            program_sha = _sha256(program.encode("utf-8"))
            safe_policy = policy.replace("_", "-")
            rule_rel = f"private/rules/path-tiebreak-{safe_policy}.rkt"
            receipt_rel = f"private/racket/path-tiebreak-{safe_policy}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"path_tiebreak": policy},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": policy == DEFAULT_POLICY,
                }
            )

            canary_input = execution_inputs[0]["input"]
            canary = {
                "input": canary_input,
                "output": python_mirror(canary_input, policy),
            }
            task = {
                "train": [canary],
                "test": [{"input": row["input"]} for row in execution_inputs],
            }
            receipt = verifier(task, program, racket_path=str(binary))
            _write_json(
                out / receipt_rel,
                {
                    "program": program,
                    "program_sha256": program_sha,
                    "canary": canary,
                    "input_order": "../execution_inputs.json",
                    "input_sha256": [row["input_sha256"] for row in execution_inputs],
                    "receipt": receipt,
                },
            )
            if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
                raise RuntimeError(
                    f"Racket execution failed for path_tiebreak={policy}: {receipt.get('error')}"
                )
            outputs = receipt.get("test_outputs")
            if type(outputs) is not list or len(outputs) != len(execution_inputs):
                raise RuntimeError(
                    f"Racket execution returned {0 if type(outputs) is not list else len(outputs)} "
                    f"outputs for {len(execution_inputs)} inputs at {policy}"
                )
            predictions[policy] = outputs
            for row, observed in zip(execution_inputs, outputs, strict=True):
                expected = python_mirror(row["input"], policy)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "path_tiebreak": policy,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch at path_tiebreak={policy}")
                parity_matches += 1

        from reviewer_support import public_challenge_bytes, public_challenge_id

        offset = 0
        score_rows: list[dict[str, Any]] = []
        exports: list[dict[str, Any]] = []
        for episode in episodes:
            chosen = episode["parameters"]["path_tiebreak"]
            episode_predictions = {
                policy: predictions[policy][offset : offset + total_per_episode]
                for policy in ALLOWED_POLICIES
            }
            offset += total_per_episode
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"], episode_predictions[chosen], strict=True
                )
            ]
            score = score_rival(
                episode_predictions,
                chosen_policy=chosen,
                demo_count=demo_count,
            )
            score_rows.append(score)
            public = public_challenge(pairs, demo_count=demo_count)
            visible_bytes = public_challenge_bytes(public)
            visible_id = public_challenge_id(public)
            if _sha256(visible_bytes) != visible_id:
                raise RuntimeError("public ID does not hash exact visible bytes")
            exports.append(
                {
                    "episode": episode,
                    "episode_predictions": episode_predictions,
                    "pairs": pairs,
                    "rival_check": score,
                    "public_bytes": visible_bytes,
                    "public_id": visible_id,
                }
            )

        for export in sorted(exports, key=lambda row: row["public_id"]):
            episode = export["episode"]
            visible_id = export["public_id"]
            visible_bytes = export["public_bytes"]
            public_rel = f"public/{visible_id}.json"
            public_path = out / public_rel
            if public_path.exists():
                raise RuntimeError(f"duplicate visible public challenge ID: {visible_id}")
            public_path.write_bytes(visible_bytes)

            private_rel = f"private/episodes/{episode['episode_id']}.json"
            _write_json(
                out / private_rel,
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "program": episode["program"],
                    "program_sha256": _sha256(episode["program"].encode("utf-8")),
                    "demo_count": demo_count,
                    "query_count": query_count,
                    "pairs": export["pairs"],
                    "cross_setting_outputs": export["episode_predictions"],
                    "rival_check": export["rival_check"],
                    "public_path": public_rel,
                    "public_id": visible_id,
                    "public_sha256": _sha256(visible_bytes),
                },
            )
            report["episodes"].append(
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "demo_count": demo_count,
                    "query_count": query_count,
                    "public_path": public_rel,
                    "public_id": visible_id,
                    "public_sha256": _sha256(visible_bytes),
                    "private_path": private_rel,
                    "private_sha256": _sha256((out / private_rel).read_bytes()),
                }
            )

        witness = execution_inputs[0]["input"]
        witness_outputs = {
            policy: predictions[policy][0] for policy in ALLOWED_POLICIES
        }
        witness_distinct = len(
            {_json_sha256(value) for value in witness_outputs.values()}
        ) == 2
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    policy: _json_sha256(output)
                    for policy, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": witness_distinct,
            },
        )

        report["summary"] = {
            "episodes": len(episodes),
            "retained_inputs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs) * len(ALLOWED_POLICIES),
            "racket_canaries": len(ALLOWED_POLICIES),
            "python_mirror_matches": parity_matches,
            "rival_checks": len(score_rows),
            "refuted_rivals": sum(
                row["status"] == "refuted_by_demonstrations" for row in score_rows
            ),
            "ambiguous_rivals": sum(
                row["status"] == "ambiguous_queries" for row in score_rows
            ),
            "survived_rivals": sum(
                row["status"] == "survived_all" for row in score_rows
            ),
            "query_disagreements": sum(
                len(row["query_disagreements"]) for row in score_rows
            ),
        }
        if _source_bindings() != report["source_sha256"]:
            raise RuntimeError("bound source files changed during evidence execution")
        report["status"] = (
            "pass"
            if witness_distinct
            and all(row["status"] == "refuted_by_demonstrations" for row in score_rows)
            else "ambiguity"
        )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}

    _write_json(out / "report.json", report)
    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append(
                {
                    "path": path.relative_to(out).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _sha256(path.read_bytes()),
                }
            )
    manifest = {
        "schema": "parametric-evidence-manifest-v1",
        "status": report["status"],
        "task_id": TASK_ID,
        "report": "report.json",
        "report_sha256": _sha256((out / "report.json").read_bytes()),
        "public_challenges": [
            row["public_path"] for row in report.get("episodes", [])
        ],
        "private_evidence": [
            row["private_path"] for row in report.get("episodes", [])
        ],
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261024)
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    args = parser.parse_args(argv)
    report = run_evidence(
        args.out,
        base_seed=args.base_seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "summary": report.get("summary"),
                "error": report.get("error"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
