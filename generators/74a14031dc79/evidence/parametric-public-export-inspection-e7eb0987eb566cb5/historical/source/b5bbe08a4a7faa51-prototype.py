#!/usr/bin/env python3
"""Proposed, unapproved occupancy-rule variants for ARC task 74a14031dc79.

The selected production generator and canonical Racket authority remain fixed to
cellwise OR.  This task-local prototype changes only the Boolean occupancy rule
applied to the same aligned left/right panel cells: OR (canonical), XOR, or AND.
A setting is drawn once per episode and all labels are executed by Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import random
import shutil
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "74a14031dc79"
VERSION = "proposed-occupancy-rule-v2"
ALLOWED_OCCUPANCY_RULES = ("or", "xor", "and")
DEFAULT_OCCUPANCY_RULE = "or"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_DEMO_COUNT = 16
MAX_QUERY_COUNT = 16
CANONICAL_RULE_HASH = "582367af483f"
CANONICAL_SHA256 = "bd4f2565f177818a412fd3058b418b8a650087446e70b4cd9666643159fdefaa"
CANONICAL_CONDITION = "(or (!= 0 (at g r c)) (!= 0 (at g r (+ c 4))))"
XOR_CONDITION = (
    "(= 1 (+ (if (!= 0 (at g r c)) 1 0) "
    "(if (!= 0 (at g r (+ c 4))) 1 0)))"
)
AND_CONDITION = "(and (!= 0 (at g r c)) (!= 0 (at g r (+ c 4))))"
RULE_CONDITIONS = {
    "or": CANONICAL_CONDITION,
    "xor": XOR_CONDITION,
    "and": AND_CONDITION,
}


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")


def _validate_count(name: str, value: Any, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in 1..{maximum}")
    return value


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_CONDITION) != 1:
        raise ValueError("canonical source must contain exactly one guarded OR condition")
    if XOR_CONDITION in source or AND_CONDITION in source:
        raise ValueError("canonical source unexpectedly contains a variant condition")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def _validate_setting(occupancy_rule: Any) -> str:
    if type(occupancy_rule) is not str or occupancy_rule not in ALLOWED_OCCUPANCY_RULES:
        allowed = ", ".join(ALLOWED_OCCUPANCY_RULES)
        raise ValueError(f"occupancy_rule must be one of: {allowed}")
    return occupancy_rule


def materialize_rule(
    occupancy_rule: str = DEFAULT_OCCUPANCY_RULE,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    setting = _validate_setting(occupancy_rule)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if setting == DEFAULT_OCCUPANCY_RULE:
        return canonical
    return canonical.replace(CANONICAL_CONDITION, RULE_CONDITIONS[setting], 1)


def rule_setting(source: str, *, root: str | Path | None = None) -> str:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return "or"
    for setting in ("xor", "and"):
        condition = RULE_CONDITIONS[setting]
        if source == canonical.replace(CANONICAL_CONDITION, condition, 1):
            return setting
    raise ValueError("source is not the pinned canonical rule or a guarded occupancy variant")


def rule_callable(source: str, *, root: str | Path | None = None) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    rule_setting(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    """Execute the exact Racket source; there is no Python answer mirror."""
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def execute_rule_many(
    source: str,
    grids: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Execute one exact Racket rule over many grids in one bridge request."""
    normalized_grids = [normalize_grid(grid) for grid in grids]
    grid_literals = [
        "(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        for grid in normalized_grids
    ]
    list_literal = "'(" + " ".join(grid_literals) + ")"
    expression = f"(map {rule_callable(source, root=root)} {list_literal})"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def relation_set(grid: Any) -> set[str]:
    normalized = normalize_grid(grid)
    if not normalized or any(len(row) != 7 for row in normalized):
        raise ValueError("prototype inputs must be nonempty h x 7 grids")
    return {
        f"{int(row[column] != 0)}{int(row[column + 4] != 0)}"
        for row in normalized
        for column in range(3)
    }


def distinguishing_input() -> list[list[int]]:
    """A lawful fixed witness containing 00, 10, 01, and 11 relations."""
    return [
        [0, 6, 6, 4, 0, 0, 8],
        [0, 0, 6, 4, 8, 0, 0],
        [6, 0, 6, 4, 8, 8, 0],
        [6, 6, 0, 4, 0, 8, 0],
    ]


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {"occupancy_rule": random.Random(seed).choice(ALLOWED_OCCUPANCY_RULES)}


def _load_selected_generator(root: Path):
    path = root / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(f"parametric_source_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import selected generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct lawful inputs independently of the hidden rule setting."""
    _validate_seed(seed)
    demonstrations = _validate_count("demo_count", demo_count, MAX_DEMO_COUNT)
    queries = _validate_count("query_count", query_count, MAX_QUERY_COUNT)
    required = demonstrations + queries
    root_path = find_root(__file__) if root is None else Path(root)
    generator = _load_selected_generator(root_path)
    bands = ("easy", "medium", "hard", "medium")
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    attempt_limit = max(64, required * 16)
    for candidate_index in range(attempt_limit):
        band = bands[candidate_index % len(bands)]
        input_seed = 740_031 + seed * 97 + candidate_index
        sample_index = 40 + seed * 4 + candidate_index
        grid = normalize_grid(generator.generate(input_seed, sample_index, difficulty=band))
        if relation_set(grid) != {"00", "10", "01", "11"}:
            raise AssertionError(
                "selected generator emitted a prototype input without the full truth table"
            )
        identity = grid_sha256(grid)
        if identity in seen:
            continue
        seen.add(identity)
        inputs.append(grid)
        if len(inputs) == required:
            return inputs
    raise RuntimeError(
        f"could not draw {required} distinct prototype inputs in {attempt_limit} attempts"
    )


def _make_episode_with_bridge(
    seed: int,
    root: Path,
    bridge: RacketBridge,
    *,
    demo_count: int,
    query_count: int,
) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    selected = parameters["occupancy_rule"]
    selected_source = materialize_rule(selected, root=root)
    inputs = episode_inputs(
        seed,
        demo_count=demo_count,
        query_count=query_count,
        root=root,
    )
    outputs_by_setting = {
        setting: execute_rule_many(
            materialize_rule(setting, root=root), inputs, bridge=bridge, root=root
        )
        for setting in ALLOWED_OCCUPANCY_RULES
    }
    selected_outputs = outputs_by_setting[selected]

    train = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs[:demo_count], selected_outputs[:demo_count])
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs[demo_count:], selected_outputs[demo_count:])
    ]

    rivals: list[dict[str, Any]] = []
    ambiguities: list[str] = []
    for setting in ALLOWED_OCCUPANCY_RULES:
        source = materialize_rule(setting, root=root)
        outputs = outputs_by_setting[setting]
        demo_mismatches = [
            index
            for index in range(demo_count)
            if outputs[index] != selected_outputs[index]
        ]
        query_mismatches = [
            index
            for index in range(query_count)
            if outputs[demo_count + index] != selected_outputs[demo_count + index]
        ]
        status = "matches_episode" if not demo_mismatches else "refuted_by_demonstrations"
        rivals.append(
            {
                "occupancy_rule": setting,
                "rule_sha256": _sha256(source),
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )
        if setting != selected and not demo_mismatches:
            ambiguities.append(setting)

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameters": parameters,
        "rule": {
            "occupancy_rule": selected,
            "racket_source": selected_source,
            "sha256": _sha256(selected_source),
        },
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "input_source": {
            "kind": "selected_generator",
            "generator_path": f"generators/{TASK_ID}/generator.py",
            "generator_sha256": _sha256(
                (root / f"generators/{TASK_ID}/generator.py").read_bytes()
            ),
            "input_sha256": [grid_sha256(grid) for grid in inputs],
        },
        "train": train,
        "test": test,
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }


def make_episode(
    seed: Any,
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    _validate_seed(seed)
    demonstrations = _validate_count("demo_count", demo_count, MAX_DEMO_COUNT)
    queries = _validate_count("query_count", query_count, MAX_QUERY_COUNT)
    root_path = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode_with_bridge(
                seed,
                root_path,
                owned,
                demo_count=demonstrations,
                query_count=queries,
            )
    return _make_episode_with_bridge(
        seed,
        root_path,
        bridge,
        demo_count=demonstrations,
        query_count=queries,
    )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the exact helper-defined visible challenge projection."""
    return json.loads(public_challenge_bytes(episode))


def public_export_plan(episodes: Any) -> list[dict[str, Any]]:
    """Sort episodes by visible-content ID and reject duplicate public payloads."""
    rows: list[dict[str, Any]] = []
    seen: dict[str, bytes] = {}
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        prior = seen.get(identifier)
        if prior is not None:
            if prior == payload:
                raise ValueError(f"duplicate visible public payload: {identifier}")
            raise RuntimeError(f"public challenge SHA-256 collision: {identifier}")
        seen[identifier] = payload
        rows.append(
            {
                "public_id": identifier,
                "public_bytes": payload,
                "episode": episode,
            }
        )
    return sorted(rows, key=lambda row: row["public_id"])


def _canonical_check(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule("or", root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    actual_outputs = execute_rule_many(
        source, [pair["input"] for pair in pairs], bridge=bridge, root=root
    )
    rows = []
    for pair, actual in zip(pairs, actual_outputs):
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": grid_sha256(pair["input"]),
                "expected_sha256": grid_sha256(pair["output"]),
                "actual_sha256": grid_sha256(actual),
                "passed": actual == pair["output"],
            }
        )
    if not rows or not all(row["passed"] for row in rows):
        raise AssertionError("canonical OR replay failed")
    return {
        "task_id": TASK_ID,
        "rule_hash": CANONICAL_RULE_HASH,
        "source_sha256": _sha256(source),
        "pairs": rows,
        "passed": True,
    }


def _distinguishing_witness(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    grid = distinguishing_input()
    outputs = {
        setting: execute_rule(
            materialize_rule(setting, root=root), grid, bridge=bridge, root=root
        )
        for setting in ALLOWED_OCCUPANCY_RULES
    }
    if len({_stable_json(output) for output in outputs.values()}) != len(ALLOWED_OCCUPANCY_RULES):
        raise AssertionError("declared settings are not distinct on the retained witness")
    return {
        "input": grid,
        "input_sha256": grid_sha256(grid),
        "relations": sorted(relation_set(grid)),
        "outputs": outputs,
        "output_sha256": {setting: grid_sha256(value) for setting, value in outputs.items()},
    }


def write_evidence(
    seeds: tuple[int, ...] | list[int],
    *,
    out: str | Path,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute all labels in Racket and write public/private source-bound evidence."""
    seed_values = tuple(seeds)
    if not seed_values:
        raise ValueError("at least one episode seed is required")
    for seed in seed_values:
        _validate_seed(seed)
    if len(seed_values) != len(set(seed_values)):
        raise ValueError("episode seeds must be unique")
    demonstrations = _validate_count("demo_count", demo_count, MAX_DEMO_COUNT)
    queries = _validate_count("query_count", query_count, MAX_QUERY_COUNT)

    root_path = find_root(__file__) if root is None else Path(root)
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(out_path)

    prototype_path = root_path / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    test_path = root_path / f"generators/{TASK_ID}/tests/test_parametric_occupancy_rule.py"
    generator_path = root_path / f"generators/{TASK_ID}/generator.py"

    with RacketBridge() as bridge:
        runtime = racket_runtime_status()
        canonical_check = _canonical_check(root_path, bridge)
        witness = _distinguishing_witness(root_path, bridge)

        rule_payloads: list[dict[str, Any]] = []
        for setting in ALLOWED_OCCUPANCY_RULES:
            source = materialize_rule(setting, root=root_path)
            relative = Path("private/rules") / f"occupancy-{setting}.rkt"
            rule_payloads.append(
                {
                    "source": source,
                    "row": {
                        "occupancy_rule": setting,
                        "path": relative.as_posix(),
                        "sha256": _sha256(source),
                        "canonical": setting == DEFAULT_OCCUPANCY_RULE,
                    },
                }
            )

        generated_episodes: list[dict[str, Any]] = []
        deterministic_by_seed: dict[int, bool] = {}
        for seed in seed_values:
            episode = make_episode(
                seed,
                demo_count=demonstrations,
                query_count=queries,
                root=root_path,
                bridge=bridge,
            )
            replay_parameters = parameters_for_seed(seed)
            replay_inputs = episode_inputs(
                seed,
                demo_count=demonstrations,
                query_count=queries,
                root=root_path,
            )
            deterministic = (
                replay_parameters == episode["parameters"]
                and [grid_sha256(grid) for grid in replay_inputs]
                == episode["input_source"]["input_sha256"]
            )
            if not deterministic:
                raise AssertionError(
                    f"episode seed {seed} did not replay its parameters and inputs deterministically"
                )
            deterministic_by_seed[seed] = deterministic
            generated_episodes.append(episode)

        export_plan = public_export_plan(generated_episodes)

    private = out_path / "private"
    public = out_path / "public"
    rules_dir = private / "rules"
    episodes_dir = private / "episodes"
    snapshot_dir = private / "source_snapshot"
    rules_dir.mkdir(parents=True)
    episodes_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)
    public.mkdir(parents=True)

    _write_json(private / "canonical_original_check.json", canonical_check)
    _write_json(private / "distinguishing_witness.json", witness)

    rule_rows = []
    for item in rule_payloads:
        row = item["row"]
        (out_path / row["path"]).write_text(item["source"], encoding="utf-8")
        rule_rows.append(row)

    episode_rows = []
    ambiguous_count = 0
    for item in export_plan:
        episode = item["episode"]
        identifier = item["public_id"]
        private_rel = Path("private/episodes") / f"{identifier}.json"
        public_rel = Path("public") / f"{identifier}.json"
        _write_json(out_path / private_rel, episode)
        (out_path / public_rel).write_bytes(item["public_bytes"])
        ambiguous_count += len(episode["ambiguities"])
        episode_rows.append(
            {
                "public_id": identifier,
                "seed": episode["seed"],
                "parameters": episode["parameters"],
                "counts": episode["counts"],
                "private_path": private_rel.as_posix(),
                "public_path": public_rel.as_posix(),
                "public_sha256": _sha256(item["public_bytes"]),
                "episode_sha256": _sha256(_stable_json(episode)),
                "deterministic_replay": deterministic_by_seed[episode["seed"]],
                "parameter_rivals": episode["parameter_rivals"],
            }
        )

    shutil.copy2(prototype_path, snapshot_dir / "prototype.py")
    shutil.copy2(test_path, snapshot_dir / "test_parametric_occupancy_rule.py")

    files = []
    for path in sorted(out_path.rglob("*")):
        if path.is_file() and path.name not in {"report.json", "manifest.json"}:
            files.append(
                {
                    "path": path.relative_to(out_path).as_posix(),
                    "sha256": _sha256(path.read_bytes()),
                }
            )

    settings_exercised = {
        row["parameters"]["occupancy_rule"] for row in episode_rows
    }
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v2",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "parameter": {
            "name": "occupancy_rule",
            "allowed_values": list(ALLOWED_OCCUPANCY_RULES),
            "original_default": DEFAULT_OCCUPANCY_RULE,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "read aligned cells from the two three-column panels around the separator, "
            "evaluate a fixed episode-level Boolean occupancy rule, and paint active output cells blue"
        ),
        "input_scope": (
            f"{demonstrations} demonstrations and {queries} queries per episode from a "
            "deterministic selected-generator sequence; every input contains 00, "
            "left-only 10, right-only 01, and overlap 11"
        ),
        "public_identity": {
            "algorithm": "sha256",
            "bytes": "reviewer_support.public_challenge_bytes",
            "includes": "visible demonstration inputs/outputs and query inputs only",
            "duplicate_policy": "reject",
            "order": "ascending public_id",
        },
        "rules": rule_rows,
        "episodes": episode_rows,
        "counts": {
            "episodes": len(episode_rows),
            "episode_settings_exercised": len(settings_exercised),
            "settings_exercised": len(ALLOWED_OCCUPANCY_RULES),
            "demonstrations_per_episode": demonstrations,
            "queries_per_episode": queries,
            "train_pairs": demonstrations * len(episode_rows),
            "query_pairs": queries * len(episode_rows),
            "distinct_public_challenges": len(episode_rows),
            "parameter_rival_episode_checks": len(ALLOWED_OCCUPANCY_RULES) * len(episode_rows),
            "ambiguous_parameter_rivals": ambiguous_count,
            "canonical_pairs_checked": len(canonical_check["pairs"]),
        },
        "runtime": runtime,
        "sources": [
            {
                "path": prototype_path.relative_to(root_path).as_posix(),
                "sha256": _sha256(prototype_path.read_bytes()),
                "snapshot": "private/source_snapshot/prototype.py",
            },
            {
                "path": test_path.relative_to(root_path).as_posix(),
                "sha256": _sha256(test_path.read_bytes()),
                "snapshot": "private/source_snapshot/test_parametric_occupancy_rule.py",
            },
            {
                "path": generator_path.relative_to(root_path).as_posix(),
                "sha256": _sha256(generator_path.read_bytes()),
                "snapshot": None,
            },
        ],
        "files": files,
        "limitations": [
            "Proposed prototype only; it does not alter or approve the selected production rule.",
            "Evidence covers the supplied seeds and finite generated inputs, not every lawful grid or competing rule.",
            "Rival checks cover only occupancy_rule in {'or','xor','and'}.",
            "Every retained demonstration deliberately contains all four occupancy relations; weaker lessons may be ambiguous.",
            f"Requested counts are bounded to 1..{MAX_DEMO_COUNT} demonstrations and 1..{MAX_QUERY_COUNT} queries per episode.",
            "Duplicate visible public challenges are rejected instead of receiving seed- or order-derived suffixes.",
            "The OR setting is source-identical to the pinned canonical Racket rule and is replayed on every labeled canonical pair.",
        ],
        "effective_cwd": os.getcwd(),
        "process_argv": sys.argv,
    }
    _write_json(out_path / "report.json", report)

    manifest_files = []
    for path in sorted(out_path.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest_files.append(
                {
                    "path": path.relative_to(out_path).as_posix(),
                    "sha256": _sha256(path.read_bytes()),
                }
            )
    _write_json(
        out_path / "manifest.json",
        {
            "schema": "arcpuzzles-parametric-evidence-manifest-v2",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "files": manifest_files,
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(
        tuple(args.seeds),
        out=args.out,
        demo_count=args.demos,
        query_count=args.queries,
    )
    print(
        json.dumps(
            {"report": str(args.out / "report.json"), "counts": report["counts"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
