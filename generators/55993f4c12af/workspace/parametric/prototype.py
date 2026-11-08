#!/usr/bin/env python3
"""Proposed episode-level Boolean-operator variants for task 55993f4c12af.

This task-local authoring prototype preserves the canonical two-panel alignment,
foreground roles, yellow output, and cellwise Boolean reasoning.  Only the
occupancy operator varies once per episode: canonical OR, XOR, or AND.

It is deliberately separate from the approved production generator and canonical
Racket authority.  Every retained label and rival prediction is executed by the
bundled Racket runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "55993f4c12af"
VERSION = "proposed-boolean-operator-v1"
ALLOWED_OPERATORS = ("or", "xor", "and")
DEFAULT_OPERATOR = "or"
COVERAGE_SEEDS = (1, 0, 5)  # random.Random(seed).choice -> OR, XOR, AND
CANONICAL_RULE_HASH = "ce2dee847896"
CANONICAL_SHA256 = "4a881f6afe15a7d94c7976b3fa116e2f4a7c3831b163028bfdbc2284b63604ee"

OPERATOR_CONDITIONS = {
    "or": "(or (!= (at g r c) 0) (!= (at g (+ r hh) c) 0))",
    "xor": (
        "(or (and (!= (at g r c) 0) (= (at g (+ r hh) c) 0)) "
        "(and (= (at g r c) 0) (!= (at g (+ r hh) c) 0)))"
    ),
    "and": "(and (!= (at g r c) 0) (!= (at g (+ r hh) c) 0))",
}

TASK_HOME = Path(__file__).resolve().parents[2]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid: Any) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"parametric_input_source_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    canonical_condition = OPERATOR_CONDITIONS[DEFAULT_OPERATOR]
    if source.count(canonical_condition) != 1:
        raise ValueError("canonical source must contain exactly one OR condition")
    return source


def canonical_source(*, root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources: set[Any] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    operator: str = DEFAULT_OPERATOR,
    *,
    root: Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket for one bounded operator setting.

    The default returns canonical source byte-for-byte. Alternatives replace only
    the unique cellwise Boolean condition and leave every other reasoning step
    unchanged.
    """
    if type(operator) is not str or operator not in ALLOWED_OPERATORS:
        raise ValueError("operator must be one of: or, xor, and")
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if operator == DEFAULT_OPERATOR:
        return canonical
    alternative = canonical.replace(
        OPERATOR_CONDITIONS[DEFAULT_OPERATOR],
        OPERATOR_CONDITIONS[operator],
        1,
    )
    if alternative.count(OPERATOR_CONDITIONS[operator]) != 1:
        raise ValueError(f"failed to materialize exactly one {operator} condition")
    return alternative


def rule_callable(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    restored = source
    for operator in ALLOWED_OPERATORS:
        if operator == DEFAULT_OPERATOR:
            continue
        condition = OPERATOR_CONDITIONS[operator]
        if condition in restored:
            restored = restored.replace(
                condition, OPERATOR_CONDITIONS[DEFAULT_OPERATOR], 1
            )
            break
    _check_canonical_source(restored)
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    """Execute one materialized rule through Racket without mutating the input."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: int) -> dict[str, str]:
    _validate_seed(seed)
    return {"operator": random.Random(seed).choice(ALLOWED_OPERATORS)}


def episode_inputs(seed: int, *, root: Path | None = None) -> list[list[list[int]]]:
    """Materialize four lawful production-shaped inputs for one episode.

    The selected operator is not passed to production generation. Each input keeps
    all four occupancy states, making OR/XOR/AND pairwise distinguishable.
    """
    del root  # Kept for a uniform task-local prototype API.
    _validate_seed(seed)
    generator = _load_generator()
    band = ("easy", "medium", "hard")[seed % 3]
    input_seed = 559_930_000 + seed
    start = seed * 4
    grids = [
        generator.generate(input_seed, start + offset, difficulty=band)
        for offset in range(4)
    ]
    for grid in grids:
        errors = generator.self_check(grid, difficulty=band)
        if errors:
            raise ValueError("prototype input left canonical domain: " + "; ".join(errors))
    return grids


def _build_episode(seed: int, *, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    operator = parameters["operator"]
    sources = {
        setting: materialize_rule(setting, root=root)
        for setting in ALLOWED_OPERATORS
    }
    inputs = episode_inputs(seed, root=root)
    outputs = {
        setting: [execute_rule(source, grid, bridge=bridge) for grid in inputs]
        for setting, source in sources.items()
    }

    selected_outputs = outputs[operator]
    train = [
        {"input": copy.deepcopy(inputs[index]), "output": copy.deepcopy(selected_outputs[index])}
        for index in range(3)
    ]
    test = [
        {"input": copy.deepcopy(inputs[3]), "output": copy.deepcopy(selected_outputs[3])}
    ]

    rival_rows = []
    ambiguities = []
    for rival in ALLOWED_OPERATORS:
        if rival == operator:
            continue
        demo_mismatches = [
            index for index in range(3) if outputs[rival][index] != selected_outputs[index]
        ]
        query_mismatches = [
            0 if outputs[rival][3] != selected_outputs[3] else None
        ]
        query_mismatches = [index for index in query_mismatches if index is not None]
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "survives_demonstrations"
        )
        rival_rows.append(
            {
                "operator": rival,
                "status": status,
                "racket_sha256": _sha256(sources[rival]),
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )
        if not demo_mismatches:
            ambiguities.append(
                {
                    "operator": rival,
                    "query_differs": bool(query_mismatches),
                }
            )

    generator = _load_generator()
    generator_bytes = GENERATOR_PATH.read_bytes()
    selected_source = sources[operator]
    return {
        "schema": "55993f4c12af-parametric-episode/1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_contract": {
            "operator": {
                "allowed": list(ALLOWED_OPERATORS),
                "default": DEFAULT_OPERATOR,
                "selected_once_per_episode": True,
                "dependent_input_constraint": (
                    "each input contains 00, 10, 01, and 11 aligned occupancy states"
                ),
            }
        },
        "generator_sha256": _sha256(generator_bytes),
        "generator_version": generator.VERSION,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "input_policy": (
            "four consecutive production-generator inputs; first three are demonstrations "
            "and the fourth is the query"
        ),
        "train": train,
        "test": test,
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "limitations": [
            "bounded three-setting prototype; not production or training approval",
            "pairwise distinction is checked on retained episodes, not every possible ARC rule",
        ],
    }


def make_episode(
    seed: int,
    *,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _build_episode(seed, root=root, bridge=owned)
    return _build_episode(seed, root=root, bridge=bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return model-visible examples without hidden setting or query answer."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def canonical_replay(*, root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule(DEFAULT_OPERATOR, root=root)
    rows = []
    failures = []
    for pair in canonical_pairs(TASK_ID, root=root):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        passed = actual == pair["output"]
        row = {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": grid_sha256(pair["input"]),
            "expected_sha256": grid_sha256(pair["output"]),
            "actual_sha256": grid_sha256(actual),
            "passed": passed,
        }
        rows.append(row)
        if not passed:
            failures.append(row)
    return {
        "status": "pass" if not failures else "failed",
        "pairs_checked": len(rows),
        "canonical_source_sha256": _sha256(source),
        "failures": failures,
        "pairs": rows,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _files_manifest(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in {"report.json", "failure.json"}:
            continue
        body = path.read_bytes()
        rows.append({"path": relative, "bytes": len(body), "sha256": _sha256(body)})
    return rows


def write_evidence(
    seeds: Iterable[int],
    *,
    out: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__) if root is None else Path(root)

    with RacketBridge() as bridge:
        rules: dict[str, dict[str, str]] = {}
        for operator in ALLOWED_OPERATORS:
            source = materialize_rule(operator, root=root)
            path = out / "private" / "rules" / f"operator-{operator}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
            rules[operator] = {
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(source),
            }

        replay = canonical_replay(root=root, bridge=bridge)
        episodes = []
        private_episodes = []
        ambiguous_total = 0
        settings = set()
        for seed in seeds:
            episode = make_episode(seed, root=root, bridge=bridge)
            operator = episode["parameters"]["operator"]
            settings.add(operator)
            ambiguous_total += len(episode["ambiguities"])
            private = copy.deepcopy(episode)
            private["racket_path"] = rules[operator]["path"]
            private_path = out / "private" / "episodes" / f"episode-{seed:03d}.json"
            public_path = out / "public" / f"episode-{seed:03d}.json"
            _write_json(private_path, private)
            _write_json(public_path, public_challenge(private))
            private_episodes.append(private)
            episodes.append(
                {
                    "seed": seed,
                    "operator": operator,
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_path": public_path.relative_to(out).as_posix(),
                    "racket_path": rules[operator]["path"],
                    "racket_sha256": rules[operator]["sha256"],
                }
            )

        witness_grid = copy.deepcopy(private_episodes[0]["train"][0]["input"])
        witness = {
            "input": witness_grid,
            "input_sha256": grid_sha256(witness_grid),
            "outputs": {
                operator: execute_rule(
                    materialize_rule(operator, root=root), witness_grid, bridge=bridge
                )
                for operator in ALLOWED_OPERATORS
            },
            "output_sha256": {
                operator: grid_sha256(
                    execute_rule(
                        materialize_rule(operator, root=root), witness_grid, bridge=bridge
                    )
                )
                for operator in ALLOWED_OPERATORS
            },
            "pairwise_distinct": True,
        }
        witness["pairwise_distinct"] = (
            len({_json(value) for value in witness["outputs"].values()})
            == len(ALLOWED_OPERATORS)
        )
        _write_json(out / "private" / "cross-setting-witness.json", witness)

    report: dict[str, Any] = {
        "schema": "55993f4c12af-parametric-evidence/1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "parameter": {
            "name": "operator",
            "allowed": list(ALLOWED_OPERATORS),
            "default": DEFAULT_OPERATOR,
            "selected_once_per_episode": True,
        },
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "generator_sha256": _sha256(GENERATOR_PATH.read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "rules": rules,
        "episodes": episodes,
        "canonical_replay": replay,
        "witness_path": "private/cross-setting-witness.json",
        "counts": {
            "episodes": len(episodes),
            "settings_covered": len(settings),
            "ambiguous_parameter_rivals": ambiguous_total,
            "canonical_pairs_checked": replay["pairs_checked"],
        },
        "execution": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "racket_path": os.environ.get("RACKET_PATH"),
        },
        "limitations": [
            "The prototype is separate from the canonical production path and is unapproved.",
            "Three retained episodes establish only bounded source-bound evidence.",
            "Declared parameter rivals are not a proof against every plausible ARC interpretation.",
        ],
    }
    report["files"] = _files_manifest(out)
    _write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=list(COVERAGE_SEEDS))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (
        report["canonical_replay"]["status"] == "pass"
        and report["counts"]["ambiguous_parameter_rivals"] == 0
        and report["counts"]["settings_covered"] == len(ALLOWED_OPERATORS)
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
