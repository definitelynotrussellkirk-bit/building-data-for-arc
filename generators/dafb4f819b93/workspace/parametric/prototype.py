#!/usr/bin/env python3
"""Proposed episode-level rank-delta extension for ARC task dafb4f819b93.

The canonical setting (rank_delta=0) fills an interior cell when the right-border
row label and bottom-border column label have the same rank in their shared
ordered palette.  The proposed setting (rank_delta=1) uses the same labels and
ordered palette, but fills with the row label only when its rank is exactly one
later than the column label's rank.  One setting is fixed for an entire episode.

This task-local prototype does not change the selected production generator,
canonical Racket authority, approval hashes, or training admission.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
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


TASK_ID = "dafb4f819b93"
VERSION = "1.0.0"
SCHEMA = "arcpuzzles-rank-delta-prototype-v1"
RANK_DELTAS = (0, 1)
DEFAULT_RANK_DELTA = 0
CANONICAL_SHA256 = "fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc"
PARAMETER_SPEC = {
    "name": "rank_delta",
    "values": RANK_DELTAS,
    "default": DEFAULT_RANK_DELTA,
    "meaning": (
        "fill with the row label when row-rank minus column-rank equals "
        "rank_delta"
    ),
}

# This alternative changes only the relation tested at each zero cell.  The
# border roles, shared ordered palette, preserved nonzero cells, and row-label
# paint source remain unchanged.
ALTERNATIVE_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (ordered-colors
                 (remove-duplicates
                  (map (lambda (rr) (at g rr (- w 1)))
                       (range 0 h)))))
           (cellmap g
                    (r c v)
                    (if (!= 0 v)
                        v
                        (let* ((row-color (at g r (- w 1)))
                               (col-color (at g (- h 1) c))
                               (row-entry
                                (find (lambda (pair)
                                        (= (second pair) row-color))
                                      (enumerate-list ordered-colors)))
                               (col-entry
                                (find (lambda (pair)
                                        (= (second pair) col-color))
                                      (enumerate-list ordered-colors))))
                          (if (= 1 (- (first row-entry) (first col-entry)))
                              row-color
                              0)))))))"""


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _grid_sha256(grid: Any) -> str:
    return _sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_count(name: str, value: Any) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a positive integer (not bool)")
    if not 1 <= value <= 12:
        raise ValueError(f"{name} must be in 1..12")


def _validate_rank_delta(rank_delta: Any) -> int:
    if type(rank_delta) is not int:
        raise TypeError("rank_delta must be the integer 0 or 1 (not bool)")
    if rank_delta not in RANK_DELTAS:
        raise ValueError("rank_delta must be exactly 0 or 1")
    return rank_delta


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the unique canonical Racket program for this task."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected exactly one canonical source for {TASK_ID}, got {len(sources)}"
        )
    source = sources.pop()
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    return source


def materialize_rule(
    rank_delta: int = DEFAULT_RANK_DELTA,
    *,
    root: Path | str | None = None,
) -> str:
    """Return the exact Racket source for one declared setting."""
    delta = _validate_rank_delta(rank_delta)
    if delta == DEFAULT_RANK_DELTA:
        return canonical_source(root=root)
    return ALTERNATIVE_RULE


def _rule_callable(source: str) -> str:
    if not isinstance(source, str) or not source.startswith("(rule!"):
        raise ValueError("Racket source must be an outer rule! form")
    if not source.endswith(")"):
        raise ValueError("Racket source has an incomplete rule! wrapper")
    body = source[len("(rule!") : -1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("Racket rule! body must be a single grid lambda")
    return body


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact Racket program on one normalized grid."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({_rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: Any) -> dict[str, int]:
    """Deterministically choose one setting for the whole episode."""
    _validate_seed(seed)
    return {"rank_delta": RANK_DELTAS[seed % len(RANK_DELTAS)]}


def _ordered_colors(grid: list[list[int]]) -> tuple[int, ...]:
    result: list[int] = []
    for row in grid:
        value = row[-1]
        if not result or result[-1] != value:
            result.append(value)
    return tuple(result)


def apply_python(
    grid: Any,
    rank_delta: int,
    *,
    root: Path | str | None = None,
) -> list[list[int]]:
    """Independent Python mirror for either rank-delta setting."""
    delta = _validate_rank_delta(rank_delta)
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    normalized = normalize_grid(grid)
    errors = generator.self_check(normalized)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    colors = _ordered_colors(normalized)
    ranks = {color: index for index, color in enumerate(colors)}
    n = len(normalized)
    right = [normalized[row][-1] for row in range(n)]
    bottom = normalized[-1]
    return [
        [
            normalized[row][column]
            if normalized[row][column] != 0
            else right[row]
            if ranks[right[row]] - ranks[bottom[column]] == delta
            else 0
            for column in range(n)
        ]
        for row in range(n)
    ]


def _input_rows(
    seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], str, str]:
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    attempt = 0
    sizes = (8, 10, 12, 14, 9, 11, 13)
    color_counts = (4, 5, 6)
    relations = ("different", "matched")
    difficulties = ("easy", "medium", "hard")
    while len(rows) < count and attempt < 300:
        index = len(rows)
        generation_seed = seed * 1_000_003 + attempt * 97 + 17
        sample_index = seed * 10_007 + attempt
        n = sizes[index % len(sizes)]
        n_colors = color_counts[index % len(color_counts)]
        relation = relations[index % len(relations)]
        difficulty = difficulties[index % len(difficulties)]
        attempt += 1
        grid = generator.generate(
            generation_seed,
            sample_index,
            difficulty=difficulty,
            grid_n=n,
            n_colors=n_colors,
            border_relation=relation,
        )
        errors = generator.self_check(grid)
        if errors:
            continue
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        rows.append(
            {
                "input": grid,
                "input_sha256": digest,
                "generation": {
                    "seed": generation_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "overrides": {
                        "grid_n": n,
                        "n_colors": n_colors,
                        "border_relation": relation,
                    },
                },
            }
        )
    if len(rows) != count:
        raise RuntimeError(
            f"could materialize only {len(rows)} of {count} distinct lawful inputs"
        )
    return rows, str(generator_path.relative_to(root)), generator_sha256


def make_episode(
    seed: Any,
    *,
    rank_delta: int | None = None,
    n_train: int = 2,
    n_test: int = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete episode with a single fixed hidden setting."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    root = find_root(__file__) if root is None else Path(root).resolve()
    delta = (
        parameters_for_seed(seed)["rank_delta"]
        if rank_delta is None
        else _validate_rank_delta(rank_delta)
    )
    rows, generator_path, generator_sha256 = _input_rows(
        seed, n_train + n_test, root=root
    )
    source = materialize_rule(delta, root=root)
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        assert active is not None
        pairs: list[dict[str, Any]] = []
        for row in rows:
            output = execute_rule(source, row["input"], bridge=active)
            pairs.append(
                {
                    **row,
                    "output": output,
                    "output_sha256": _grid_sha256(output),
                    "rank_delta": delta,
                }
            )
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"rank_delta": delta},
        "parameter_scope": "chosen once per episode",
        "n_train": n_train,
        "n_test": n_test,
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "program_sha256": _sha256(source),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "pairs": pairs,
    }


def _episode_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    pairs = episode.get("pairs")
    if not isinstance(pairs, list):
        pairs = list(episode.get("train", [])) + list(episode.get("test", []))
    return pairs


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Check Racket/Python parity and the one declared competing setting."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    try:
        delta = _validate_rank_delta(episode["parameters"]["rank_delta"])
    except (KeyError, TypeError) as error:
        raise ValueError("episode has no valid rank_delta setting") from error
    rival_delta = 1 - delta
    selected_source = materialize_rule(delta, root=root)
    rival_source = materialize_rule(rival_delta, root=root)
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        raise ValueError("episode requires at least one demonstration")
    if not isinstance(test, list) or not test:
        raise ValueError("episode requires at least one query")
    pairs = _episode_pairs(episode)
    if any(pair.get("rank_delta") != delta for pair in pairs):
        raise ValueError("episode pairs do not share one fixed rank_delta")

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        assert active is not None
        selected_outputs = [
            execute_rule(selected_source, pair["input"], bridge=active) for pair in pairs
        ]
        rival_train = [
            execute_rule(rival_source, pair["input"], bridge=active) for pair in train
        ]
        rival_queries = [
            execute_rule(rival_source, pair["input"], bridge=active) for pair in test
        ]

    outputs_match_selected = all(
        output == pair.get("output") for output, pair in zip(selected_outputs, pairs)
    )
    python_parity = all(
        apply_python(pair["input"], delta, root=root) == pair.get("output")
        for pair in pairs
    )
    rival_fits_demonstrations = all(
        output == pair.get("output") for output, pair in zip(rival_train, train)
    )
    queries = [
        {
            "query_index": index,
            "input_sha256": pair.get("input_sha256") or _grid_sha256(pair["input"]),
            "selected_output_sha256": _grid_sha256(pair["output"]),
            "rival_output_sha256": _grid_sha256(rival_output),
            "rival_query_differs": rival_output != pair["output"],
        }
        for index, (pair, rival_output) in enumerate(zip(test, rival_queries))
    ]
    no_ambiguity = (
        outputs_match_selected
        and python_parity
        and not rival_fits_demonstrations
        and all(row["rival_query_differs"] for row in queries)
    )
    return {
        "status": "no_ambiguity_found" if no_ambiguity else "needs_attention",
        "selected_rank_delta": delta,
        "rival_rank_delta": rival_delta,
        "outputs_match_selected_racket": outputs_match_selected,
        "python_parity": python_parity,
        "rival_fits_demonstrations": rival_fits_demonstrations,
        "queries": queries,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project only visible demonstrations and query inputs."""
    public = {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }
    public_challenge_bytes(public)
    return public


def public_filename(challenge: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(challenge)}.json"


def _sorted_unique_episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["public_id"])
    ids = [row["public_id"] for row in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate visible public challenge id")
    return ordered


def _canonical_checks(root: Path, bridge: RacketBridge) -> list[dict[str, Any]]:
    source = materialize_rule(DEFAULT_RANK_DELTA, root=root)
    rows = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        rows.append(
            {
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_output_sha256": _grid_sha256(pair["output"]),
                "actual_output_sha256": _grid_sha256(actual),
                "passed": actual == pair["output"],
            }
        )
    return rows


def materialize(
    out_dir: Path | str,
    *,
    seed: int = 0,
    n_train: int = 2,
    n_test: int = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write two source-bound, self-verifying episodes and public challenges."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out_dir).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory is not empty: {out}")
    public_dir = out / "public"
    private_dir = out / "private"
    program_dir = private_dir / "programs"
    public_dir.mkdir(parents=True, exist_ok=True)
    program_dir.mkdir(parents=True, exist_ok=True)

    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    with manager as active:
        assert active is not None
        canonical_checks = _canonical_checks(root, active)
        episodes: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        for delta in RANK_DELTAS:
            episode_seed = seed * 2 + delta
            episode = make_episode(
                episode_seed,
                rank_delta=delta,
                n_train=n_train,
                n_test=n_test,
                root=root,
                bridge=active,
            )
            analysis = analyze_episode(episode, root=root, bridge=active)
            challenge = public_challenge(episode)
            public_id = public_challenge_id(challenge)
            rows.append(
                {
                    "public_id": public_id,
                    "rank_delta": delta,
                    "episode": episode,
                    "analysis": analysis,
                    "challenge": challenge,
                }
            )

        witness_grid = rows[0]["episode"]["train"][0]["input"]
        witness_outputs = {
            str(delta): execute_rule(
                materialize_rule(delta, root=root), witness_grid, bridge=active
            )
            for delta in RANK_DELTAS
        }

    rows = _sorted_unique_episode_rows(rows)
    episode_records = []
    manifest_files = []
    for index, row in enumerate(rows, start=1):
        public_name = public_filename(row["challenge"])
        public_path = public_dir / public_name
        public_payload = public_challenge_bytes(row["challenge"])
        public_path.write_bytes(public_payload)
        private_path = private_dir / f"episode-{index:03d}.json"
        private_path.write_text(
            json.dumps(
                {
                    "episode": row["episode"],
                    "analysis": row["analysis"],
                    "public_id": row["public_id"],
                    "public_path": f"public/{public_name}",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        episode_records.append(
            {
                "rank_delta": row["rank_delta"],
                "seed": row["episode"]["seed"],
                "public_id": row["public_id"],
                "public_path": f"public/{public_name}",
                "private_path": f"private/{private_path.name}",
                "analysis_status": row["analysis"]["status"],
            }
        )
        manifest_files.extend(
            [
                {
                    "path": f"public/{public_name}",
                    "sha256": _sha256(public_payload),
                },
                {
                    "path": f"private/{private_path.name}",
                    "sha256": _sha256(private_path.read_bytes()),
                },
            ]
        )

    rule_hashes = {}
    for delta in RANK_DELTAS:
        path = program_dir / f"rank-delta-{delta}.rkt"
        source = materialize_rule(delta, root=root)
        path.write_text(source, encoding="utf-8")
        digest = _sha256(source)
        rule_hashes[str(delta)] = digest
        manifest_files.append(
            {"path": f"private/programs/{path.name}", "sha256": digest}
        )

    all_inputs = [
        pair["input"]
        for row in rows
        for pair in row["episode"]["pairs"]
    ]
    different_cells = [
        {"row": r, "column": c}
        for r in range(len(witness_outputs["0"]))
        for c in range(len(witness_outputs["0"][r]))
        if witness_outputs["0"][r][c] != witness_outputs["1"][r][c]
    ]
    identifiable = sum(
        row["analysis"]["status"] == "no_ambiguity_found" for row in rows
    )
    query_refutations = sum(
        query["rival_query_differs"]
        for row in rows
        for query in row["analysis"]["queries"]
    )
    canonical_passed = sum(row["passed"] for row in canonical_checks)
    default_source = materialize_rule(0, root=root)
    passed = (
        canonical_passed == len(canonical_checks)
        and identifiable == len(rows) == 2
        and query_refutations == 2 * n_test
        and len({_grid_sha256(grid) for grid in all_inputs}) == len(all_inputs)
        and _sha256(default_source) == CANONICAL_SHA256
        and bool(different_cells)
    )
    report = {
        "schema": SCHEMA,
        "version": VERSION,
        "task_id": TASK_ID,
        "status": "no_ambiguity_found" if passed else "needs_attention",
        "passed": passed,
        "prototype": True,
        "approved": False,
        "canonical_authority_changed": False,
        "default_program_byte_identical": default_source == canonical_source(root=root),
        "parameter_spec": PARAMETER_SPEC,
        "source_bindings": {
            "prototype_path": str(Path(__file__).resolve().relative_to(root)),
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "canonical_path": str(canonical_path(root).relative_to(root)),
            "canonical_program_sha256": CANONICAL_SHA256,
            "generator_path": rows[0]["episode"]["generator_path"],
            "generator_sha256": rows[0]["episode"]["generator_sha256"],
            "rule_sha256": rule_hashes,
        },
        "counts": {
            "settings": 2,
            "episodes": 2,
            "demonstrations": 2 * n_train,
            "queries": 2 * n_test,
            "distinct_inputs": len({_grid_sha256(grid) for grid in all_inputs}),
            "racket_labels": len(all_inputs),
            "canonical_pairs": len(canonical_checks),
            "canonical_pairs_passed": canonical_passed,
            "identifiable_episodes": identifiable,
            "queries_refuting_rival": query_refutations,
        },
        "canonical_checks": canonical_checks,
        "episodes": episode_records,
        "setting_difference_witness": {
            "input": witness_grid,
            "input_sha256": _grid_sha256(witness_grid),
            "outputs": witness_outputs,
            "output_sha256": {
                key: _grid_sha256(value) for key, value in witness_outputs.items()
            },
            "different_cell_count": len(different_cells),
            "first_differing_cells": different_cells[:24],
        },
        "limitations": [
            "Only rank_delta values 0 and 1 are proposed.",
            "Evidence is bounded to two episodes and one declared rival per setting.",
            "The prototype is task-local and is not a production parametric API.",
        ],
    }
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_files.append(
        {"path": "report.json", "sha256": _sha256(report_path.read_bytes())}
    )
    manifest = {
        "schema": "arcpuzzles-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "files": sorted(manifest_files, key=lambda row: row["path"]),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def verify_tree(
    out_dir: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Replay hashes, public projection, Racket labels, and rival checks."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out_dir).resolve()
    report_path = out / "report.json"
    manifest_path = out / "manifest.json"
    if not report_path.is_file() or not manifest_path.is_file():
        raise ValueError("evidence tree is missing report.json or manifest.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if report.get("task_id") != TASK_ID or manifest.get("task_id") != TASK_ID:
        raise ValueError("evidence tree belongs to another task")
    if report.get("source_bindings", {}).get("prototype_sha256") != _sha256(
        Path(__file__).read_bytes()
    ):
        raise ValueError("prototype source binding is stale")
    _, _, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    if report.get("source_bindings", {}).get("generator_sha256") != generator_sha256:
        raise ValueError("generator source binding is stale")

    for row in manifest.get("files", []):
        path = out / row["path"]
        if not path.is_file() or _sha256(path.read_bytes()) != row["sha256"]:
            kind = "public" if str(row.get("path", "")).startswith("public/") else "evidence"
            raise ValueError(f"{kind} file hash mismatch: {row.get('path')}")

    for delta in RANK_DELTAS:
        path = out / "private" / "programs" / f"rank-delta-{delta}.rkt"
        if path.read_text(encoding="utf-8") != materialize_rule(delta, root=root):
            raise ValueError(f"private Racket program mismatch for rank_delta={delta}")

    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=128
    )
    checked_queries = 0
    with manager as active:
        assert active is not None
        for row in report.get("episodes", []):
            private_path = out / row["private_path"]
            record = json.loads(private_path.read_text(encoding="utf-8"))
            episode = record["episode"]
            analysis = analyze_episode(episode, root=root, bridge=active)
            if analysis["status"] != "no_ambiguity_found":
                raise ValueError("private episode no longer refutes the declared rival")
            checked_queries += len(analysis["queries"])
            public = public_challenge(episode)
            expected_name = public_filename(public)
            public_path = out / row["public_path"]
            if public_path.name != expected_name:
                raise ValueError("public filename does not match visible challenge bytes")
            if public_path.read_bytes() != public_challenge_bytes(public):
                raise ValueError("public challenge bytes mismatch private projection")
            if record.get("public_id") != public_challenge_id(public):
                raise ValueError("public id mismatch private projection")

    if report.get("status") != "no_ambiguity_found" or report.get("passed") is not True:
        raise ValueError("report did not record a passing bounded assessment")
    return {
        "status": "pass",
        "task_id": TASK_ID,
        "episodes": len(report.get("episodes", [])),
        "queries": checked_queries,
        "manifest_files": len(manifest.get("files", [])),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("--out-dir", required=True, type=Path)
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--train", type=int, default=2)
    materialize_parser.add_argument("--test", type=int, default=4)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--out-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        report = materialize(
            args.out_dir,
            seed=args.seed,
            n_train=args.train,
            n_test=args.test,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1
    verification = verify_tree(args.out_dir)
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
