#!/usr/bin/env python3
"""Proposed task-local parameterization of which side of the gray frame is swapped."""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "51e59bb53cac"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SWAP_SCOPES = ("interior", "exterior")
DEFAULT_SWAP_SCOPE = "interior"
DECLARED_RIVALS = (*SWAP_SCOPES, "global", "identity")
MAX_COUNT = 32
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
DEFAULT_MAX_ATTEMPTS = 256
CANONICAL_RULE_HASH = "6efb83adf2b2"
INTERIOR_CONDITION = "(and (> r fr1) (< r fr2) (> c fc1) (< c fc2))"
EXTERIOR_CONDITION = "(or (< r fr1) (> r fr2) (< c fc1) (> c fc2))"


def _stable_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_stable_bytes(value))


def _validate_seed(seed: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a literal integer")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(name: str, value: int, *, maximum: int = MAX_COUNT) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be in 1..{maximum}")
    return value


def _validate_scope(value: str) -> str:
    if value not in SWAP_SCOPES:
        raise ValueError("swap_scope must be interior or exterior")
    return value


def choose_scope(seed: int) -> str:
    """Choose one hidden setting from the episode seed, before any input draws."""
    _validate_seed(seed)
    bit = hashlib.sha256(f"swap-scope-v1:{seed}".encode()).digest()[0] & 1
    return SWAP_SCOPES[bit]


@lru_cache(maxsize=1)
def generator():
    """Load the selected generator from this exact source tree."""
    return load_selected_generator(TASK_ID, root=ROOT)[0]


@lru_cache(maxsize=1)
def canonical_rule() -> str:
    """Return the one canonical Racket authority and verify its normalized hash."""
    rules = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rules.add(row["program_solution"])
    if len(rules) != 1:
        raise RuntimeError("expected exactly one canonical Racket authority")
    source = rules.pop()
    normalized = " ".join(source.split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    if digest != CANONICAL_RULE_HASH:
        raise RuntimeError(
            f"canonical rule changed: expected {CANONICAL_RULE_HASH}, got {digest}"
        )
    if source.count(INTERIOR_CONDITION) != 1:
        raise RuntimeError("canonical interior condition must occur exactly once")
    return source


@lru_cache(maxsize=2)
def rule_text(swap_scope: str) -> str:
    """Return exact materialized Racket for one setting."""
    _validate_scope(swap_scope)
    source = canonical_rule()
    expected = (
        source
        if swap_scope == DEFAULT_SWAP_SCOPE
        else source.replace(INTERIOR_CONDITION, EXTERIOR_CONDITION)
    )
    materialized = (HERE / "rules" / f"{swap_scope}.rkt").read_text(encoding="utf-8")
    if materialized != expected:
        raise RuntimeError(
            f"materialized {swap_scope} rule differs from its canonical derivation"
        )
    return materialized


def _swap_value(value: int, color_a: int, color_b: int) -> int:
    if value == color_a:
        return color_b
    if value == color_b:
        return color_a
    return value


def apply_python(grid: list[list[int]], swap_scope: str) -> list[list[int]]:
    """Audit mirror for the two proposed settings; Racket remains label authority."""
    _validate_scope(swap_scope)
    analysis = generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("input outside prototype domain: " + "; ".join(analysis["errors"]))
    top, left, bottom, right = analysis["bbox"]
    color_a, color_b = analysis["colors"]
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            inside = top < row < bottom and left < col < right
            outside = row < top or row > bottom or col < left or col > right
            selected = inside if swap_scope == "interior" else outside
            if selected:
                output[row][col] = _swap_value(grid[row][col], color_a, color_b)
    return output


def _global_swap(grid: list[list[int]]) -> list[list[int]]:
    analysis = generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("input outside prototype domain: " + "; ".join(analysis["errors"]))
    color_a, color_b = analysis["colors"]
    return [
        [_swap_value(value, color_a, color_b) for value in row]
        for row in grid
    ]


class RuleEngine:
    """Persistent Racket bridge that records every executed prediction."""

    def __init__(self) -> None:
        self.bridge = RacketBridge(timeout=10.0)
        self.executions: list[dict[str, Any]] = []

    def __enter__(self) -> "RuleEngine":
        return self

    def __exit__(self, *error: object) -> bool:
        self.close()
        return False

    def close(self) -> None:
        self.bridge.close()

    def apply(self, grid: list[list[int]], swap_scope: str) -> list[list[int]]:
        _validate_scope(swap_scope)
        errors = generator().self_check(grid)
        if errors:
            raise ValueError("input outside prototype domain: " + "; ".join(errors))
        source = rule_text(swap_scope)
        body = strip_rule_wrapper(source)
        if not body.startswith("(lambda (g)"):
            raise RuntimeError("materialized rule is not a self-contained lambda")
        before = _sha256_json(grid)
        self.bridge.define_grid("g", grid)
        output = self.bridge.eval_text(f"({body} g)")
        if _sha256_json(grid) != before:
            raise RuntimeError("Racket execution mutated the Python input")
        self.executions.append(
            {
                "swap_scope": swap_scope,
                "rule_sha256": _sha256_bytes(source.encode()),
                "input_sha256": before,
                "output_sha256": _sha256_json(output),
            }
        )
        return output


def _candidate_output(
    candidate: str,
    grid: list[list[int]],
    *,
    engine: RuleEngine,
) -> list[list[int]]:
    if candidate in SWAP_SCOPES:
        return engine.apply(grid, candidate)
    if candidate == "global":
        return _global_swap(grid)
    if candidate == "identity":
        return [row[:] for row in grid]
    raise ValueError(f"unknown declared rival: {candidate}")


def identify_query(
    demonstrations: list[dict[str, list[list[int]]]],
    query_input: list[list[int]],
    *,
    engine: RuleEngine,
) -> dict[str, Any]:
    """Fit declared rivals using demonstrations only, then predict the query."""
    if not demonstrations:
        raise ValueError("identification requires at least one demonstration")
    for pair in demonstrations:
        if set(pair) != {"input", "output"}:
            raise ValueError("demonstrations must contain exactly input and output")

    mismatches: dict[str, list[int]] = {}
    survivors: list[str] = []
    for candidate in DECLARED_RIVALS:
        bad = [
            index
            for index, pair in enumerate(demonstrations)
            if _candidate_output(candidate, pair["input"], engine=engine)
            != pair["output"]
        ]
        mismatches[candidate] = bad
        if not bad:
            survivors.append(candidate)

    query_predictions = {
        candidate: _sha256_json(
            _candidate_output(candidate, query_input, engine=engine)
        )
        for candidate in survivors
    }
    return {
        "survivors": survivors,
        "mismatching_demo_indices": mismatches,
        "query_prediction_sha256": query_predictions,
    }


def _sample_inputs(
    seed: int,
    count: int,
    *,
    max_attempts: int,
) -> tuple[list[list[list[int]]], int]:
    values: list[list[list[int]]] = []
    seen: set[str] = set()
    difficulties = ("easy", "medium", "hard")
    attempts = 0
    while len(values) < count and attempts < max_attempts:
        difficulty = difficulties[attempts % len(difficulties)]
        grid = generator().generate(seed, attempts, difficulty=difficulty)
        attempts += 1
        key = _sha256_json(grid)
        if key in seen:
            continue
        seen.add(key)
        values.append(grid)
    if len(values) != count:
        raise RuntimeError(
            f"distinct-input sampling exhausted after {attempts} attempts: "
            f"requested {count}, obtained {len(values)}"
        )
    return values, attempts


def generate_episode(
    seed: int,
    *,
    swap_scope: str | None = None,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    engine: RuleEngine | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> dict[str, Any]:
    """Generate one fixed-setting episode with Racket-derived labels."""
    _validate_seed(seed)
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    max_attempts = _validate_count("max_attempts", max_attempts, maximum=10000)
    selected = choose_scope(seed) if swap_scope is None else _validate_scope(swap_scope)

    owned = engine is None
    runner = RuleEngine() if owned else engine
    assert runner is not None
    start_execution = len(runner.executions)
    try:
        inputs, attempts = _sample_inputs(
            seed,
            demos + queries,
            max_attempts=max_attempts,
        )
        labeled: list[dict[str, list[list[int]]]] = []
        for grid in inputs:
            output = runner.apply(grid, selected)
            mirror = apply_python(grid, selected)
            if output != mirror:
                raise RuntimeError("Python/Racket mismatch for proposed setting")
            labeled.append({"input": grid, "output": output})

        demonstrations = labeled[:demos]
        query_pairs = labeled[demos:]
        checks = [
            identify_query(demonstrations, pair["input"], engine=runner)
            for pair in query_pairs
        ]
        for check in checks:
            if check["survivors"] != [selected]:
                raise RuntimeError(
                    "demonstrations do not identify the selected setting: "
                    + repr(check["survivors"])
                )

        public = {
            "train": demonstrations,
            "test": [{"input": pair["input"]} for pair in query_pairs],
        }
        private = {
            "seed": seed,
            "parameters": {"swap_scope": selected},
            "demos": demos,
            "queries": queries,
            "sampling_attempts": attempts,
            "rule": rule_text(selected),
            "rule_sha256": _sha256_bytes(rule_text(selected).encode()),
            "query_outputs": [pair["output"] for pair in query_pairs],
            "input_sha256": [_sha256_json(grid) for grid in inputs],
            "demo_only_survivors": checks[0]["survivors"],
            "query_checks": checks,
            "racket_execution_count": len(runner.executions) - start_execution,
        }
        return {"public": public, "private": private}
    finally:
        if owned:
            runner.close()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable_bytes(value) + b"\n")


def source_identity() -> dict[str, str]:
    paths = [
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "generators" / TASK_ID / "tests" / "test_generator_51e59bb53cac.py",
        ROOT / "generators" / TASK_ID / "tests" / "test_parametric_swap_scope.py",
        HERE / "prototype.py",
        HERE / "README.md",
        HERE / "rules" / "interior.rkt",
        HERE / "rules" / "exterior.rkt",
        canonical_path(ROOT),
    ]
    return {
        str(path.relative_to(ROOT)): _sha256_bytes(path.read_bytes())
        for path in paths
    }


def write_bundle(
    out: Path,
    *,
    seed: int,
    swap_scope: str = "both",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> dict[str, Any]:
    """Write visible-only public challenges and private evidence."""
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    _validate_seed(seed)
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    max_attempts = _validate_count("max_attempts", max_attempts, maximum=10000)

    if swap_scope == "both":
        scopes = SWAP_SCOPES
    elif swap_scope == "auto":
        scopes = (choose_scope(seed),)
    else:
        scopes = (_validate_scope(swap_scope),)

    episodes: list[dict[str, Any]] = []
    setting_map: dict[str, str] = {}
    with RuleEngine() as engine:
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        passed = 0
        for pair in pairs:
            actual = engine.apply(pair["input"], DEFAULT_SWAP_SCOPE)
            if actual != pair["output"]:
                raise RuntimeError("canonical default parity failed")
            passed += 1

        built: dict[str, dict[str, Any]] = {}
        pending: list[tuple[str, str, dict[str, Any]]] = []
        seen_public_ids: set[str] = set()
        for scope in scopes:
            episode = generate_episode(
                seed,
                swap_scope=scope,
                demos=demos,
                queries=queries,
                engine=engine,
                max_attempts=max_attempts,
            )
            public_id = public_challenge_id(episode["public"])
            if public_id in seen_public_ids:
                raise RuntimeError("duplicate visible public challenge payload")
            seen_public_ids.add(public_id)
            built[scope] = episode
            pending.append((public_id, scope, episode))

        # Public creation/report order is content-derived, never setting-derived.
        for public_id, scope, episode in sorted(pending, key=lambda row: row[0]):
            setting_map[public_id] = scope
            public_path = out / "public" / f"{public_id}.json"
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_challenge_bytes(episode["public"]))

            private = dict(episode["private"])
            rule = private.pop("rule")
            private["public_id"] = public_id
            _write_json(out / "private" / "episodes" / f"{public_id}.json", private)
            rule_hash = private["rule_sha256"]
            rule_path = out / "private" / "rules" / f"{rule_hash}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            if rule_path.exists() and rule_path.read_text(encoding="utf-8") != rule:
                raise RuntimeError("rule hash collision")
            rule_path.write_text(rule, encoding="utf-8")
            episodes.append(
                {
                    "public_id": public_id,
                    "swap_scope": scope,
                    "demos": demos,
                    "queries": queries,
                    "unique_inputs": len(set(private["input_sha256"])),
                    "rule_sha256": rule_hash,
                    "demo_only_survivors": private["demo_only_survivors"],
                }
            )

        witness_input = next(iter(built.values()))["public"]["train"][0]["input"]
        interior_output = engine.apply(witness_input, "interior")
        exterior_output = engine.apply(witness_input, "exterior")
        witness = {
            "input_sha256": _sha256_json(witness_input),
            "outputs_differ": interior_output != exterior_output,
            "output_sha256": {
                "interior": _sha256_json(interior_output),
                "exterior": _sha256_json(exterior_output),
            },
            "input": witness_input,
            "outputs": {
                "interior": interior_output,
                "exterior": exterior_output,
            },
        }
        if not witness["outputs_differ"]:
            raise RuntimeError("parameter witness does not distinguish settings")

        _write_json(out / "private" / "setting-map.json", setting_map)
        _write_json(out / "private" / "parameter-witness.json", witness)
        _write_json(out / "private" / "racket-executions.json", engine.executions)

    report = {
        "status": "proposed prototype; no production approval",
        "task_id": TASK_ID,
        "parameter": {
            "name": "swap_scope",
            "allowed_values": list(SWAP_SCOPES),
            "default": DEFAULT_SWAP_SCOPE,
            "fixed_per_episode": True,
        },
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "canonical_parity": {"passed": passed, "total": len(pairs)},
        "parameter_witness": {
            "input_sha256": witness["input_sha256"],
            "outputs_differ": witness["outputs_differ"],
            "output_sha256": witness["output_sha256"],
            "path": "private/parameter-witness.json",
        },
        "episodes": episodes,
        "source_sha256": source_identity(),
        "racket_executions": {
            "count": len(json.loads((out / "private" / "racket-executions.json").read_text())),
            "path": "private/racket-executions.json",
        },
        "limits": [
            "Bounded task-local prototype; it does not change the production API or canonical approval.",
            "Identifiability is checked only against interior, exterior, global-swap, and identity rivals.",
            "Evidence covers the recorded seed and the canonical generator's current 8..22 input domain.",
        ],
    }
    _write_json(out / "summary.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--swap-scope",
        choices=("auto", "both", *SWAP_SCOPES),
        default="both",
    )
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = write_bundle(
        args.out,
        seed=args.seed,
        swap_scope=args.swap_scope,
        demos=args.demos,
        queries=args.queries,
        max_attempts=args.max_attempts,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": len(report["episodes"]),
                "demos": report["demos"],
                "queries": report["queries"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
