#!/usr/bin/env python3
"""Proposed episode-level panel-threshold extension for a9c4475d7cda.

The selected production generator and canonical threshold-2 rule remain
unchanged.  This task-local authoring tool chooses one hidden threshold per
complete episode, samples lawful inputs whose panel counts visibly contain
1, 2, and 3, and obtains every selected and rival label from exact materialized
Racket programs through the bundled runtime.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "a9c4475d7cda"
VERSION = "proposed-panel-threshold-v1"
ALLOWED_PANEL_THRESHOLDS = (1, 2, 3)
DEFAULT_PANEL_THRESHOLD = 2
MAX_PAIRS_PER_SPLIT = 16
CANONICAL_SOURCE_SHA256 = (
    "4e6231455ecb950b5c408077976da1f2ee06d3b29707dbbd2717e6cdbbeb6668"
)
CANONICAL_RULE_HASH = "8cfb5cf9c2c4"
BASE_GENERATOR_SHA256 = (
    "1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51"
)
THRESHOLD_FRAGMENT_TEMPLATE = (
    "\n                                 {value})"
    "\n                             1"
    "\n                             0)"
)


def _sha256(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def grid_sha256(grid) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _threshold_fragment(value: int) -> str:
    return THRESHOLD_FRAGMENT_TEMPLATE.format(value=value)


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int or not 1 <= value <= MAX_PAIRS_PER_SPLIT:
        raise ValueError(
            f"{name} must be an integer in 1..{MAX_PAIRS_PER_SPLIT}"
        )


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def _validate_panel_threshold(panel_threshold: int) -> None:
    if (
        type(panel_threshold) is not int
        or panel_threshold not in ALLOWED_PANEL_THRESHOLDS
    ):
        raise ValueError(
            "panel_threshold must be one of the exact integers "
            f"{ALLOWED_PANEL_THRESHOLDS}"
        )


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    fragment = _threshold_fragment(DEFAULT_PANEL_THRESHOLD)
    if source.count(fragment) != 1:
        raise ValueError("canonical source must contain exactly one guarded threshold site")
    return source


def canonical_source(*, root=None) -> str:
    """Load the one exact canonical source and fail closed on source drift."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one distinct canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    panel_threshold: int = DEFAULT_PANEL_THRESHOLD,
    *,
    root=None,
    source: str | None = None,
) -> str:
    """Return exact Racket for one proposed hidden threshold setting."""
    _validate_panel_threshold(panel_threshold)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if panel_threshold == DEFAULT_PANEL_THRESHOLD:
        return canonical
    return canonical.replace(
        _threshold_fragment(DEFAULT_PANEL_THRESHOLD),
        _threshold_fragment(panel_threshold),
        1,
    )


def _canonicalize_materialized_source(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    matches = [
        value
        for value in ALLOWED_PANEL_THRESHOLDS
        if source.count(_threshold_fragment(value)) == 1
    ]
    if len(matches) != 1:
        raise ValueError("Racket source must contain exactly one allowed threshold site")
    canonicalized = source.replace(
        _threshold_fragment(matches[0]),
        _threshold_fragment(DEFAULT_PANEL_THRESHOLD),
        1,
    )
    _check_canonical_source(canonicalized)
    return canonicalized


def rule_callable(source: str) -> str:
    """Wrap a source-bound materialized rule for the bare Racket bridge."""
    _canonicalize_materialized_source(source)
    return wrap_rule(source)


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Apply the actual Racket rule; no Python output mirror supplies labels."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _resolve_root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


@lru_cache(maxsize=4)
def _selected_generator(root_text: str):
    root = Path(root_text)
    module, source_path, digest = load_selected_generator(TASK_ID, root=root)
    if digest != BASE_GENERATOR_SHA256:
        raise ValueError(
            "selected generator SHA256 changed from the prototype's pinned source"
        )
    return module, source_path, digest


def _derived_coordinates(seed: int, index: int, attempt: int) -> tuple[int, int]:
    payload = f"{TASK_ID}:{VERSION}:input:{seed}:{index}:{attempt}".encode()
    digest = hashlib.sha256(payload).digest()
    input_seed = int.from_bytes(digest[:8], "big") % (2**63)
    sample_index = int.from_bytes(digest[8:16], "big") % (2**31)
    return input_seed, sample_index


def _sample_inputs(
    seed: int,
    count: int,
    *,
    difficulty: str,
    root: Path,
) -> list[dict[str, Any]]:
    module, _, _ = _selected_generator(str(root))
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    profiles = tuple(module.COUNT_PROFILES)
    for index in range(count):
        profile = profiles[index % len(profiles)]
        for attempt in range(32):
            input_seed, sample_index = _derived_coordinates(seed, index, attempt)
            grid = module.generate(
                input_seed,
                sample_index,
                difficulty=difficulty,
                count_profile=profile,
            )
            diagnostics = module.self_check(grid)
            if diagnostics:
                raise AssertionError(
                    "selected generator rejected its own parametric input: "
                    + "; ".join(diagnostics)
                )
            observed = module.observe_overrides(grid)
            if observed.get("count_profile") != profile:
                raise AssertionError(
                    f"selected generator profile drifted: {observed!r}"
                )
            analysis = module._parse_grid(grid)
            panel_counts = [
                value for row in analysis["counts"] for value in row
            ]
            if not {1, 2, 3} <= set(panel_counts):
                raise AssertionError(
                    f"boundary profile lost counts 1, 2, or 3: {panel_counts}"
                )
            digest = grid_sha256(grid)
            if digest in seen:
                continue
            seen.add(digest)
            result.append(
                {
                    "input": grid,
                    "input_sha256": digest,
                    "input_seed": input_seed,
                    "sample_index": sample_index,
                    "attempt": attempt,
                    "count_profile": profile,
                    "grid_h": observed["grid_h"],
                    "grid_w": observed["grid_w"],
                    "panel_counts": panel_counts,
                }
            )
            break
        else:
            raise RuntimeError(
                f"could not sample distinct input {index} after 32 attempts"
            )
    return result


def parameters_for_seed(seed: int) -> dict[str, int]:
    """Choose exactly one setting per episode without touching global RNG state."""
    _validate_seed(seed)
    return {
        "panel_threshold": ALLOWED_PANEL_THRESHOLDS[
            seed % len(ALLOWED_PANEL_THRESHOLDS)
        ]
    }


def make_episode(
    seed: int,
    *,
    panel_threshold: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
    difficulty: str = "medium",
    root=None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting episode with independent split counts."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    _validate_difficulty(difficulty)
    selected = (
        parameters_for_seed(seed)["panel_threshold"]
        if panel_threshold is None
        else panel_threshold
    )
    _validate_panel_threshold(selected)
    resolved_root = _resolve_root(root)
    inputs = _sample_inputs(
        seed,
        demo_count + query_count,
        difficulty=difficulty,
        root=resolved_root,
    )
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(
                seed,
                selected,
                demo_count,
                query_count,
                difficulty,
                inputs,
                root=resolved_root,
                bridge=owned,
            )
    return _make_episode(
        seed,
        selected,
        demo_count,
        query_count,
        difficulty,
        inputs,
        root=resolved_root,
        bridge=bridge,
    )


def _make_episode(
    seed: int,
    selected: int,
    demo_count: int,
    query_count: int,
    difficulty: str,
    inputs: list[dict[str, Any]],
    *,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    canonical = canonical_source(root=root)
    rules = {
        value: materialize_rule(value, source=canonical)
        for value in ALLOWED_PANEL_THRESHOLDS
    }
    outputs = {
        value: [execute_rule(rule, row["input"], bridge=bridge) for row in inputs]
        for value, rule in rules.items()
    }
    for index in range(len(inputs)):
        hashes = {
            grid_sha256(outputs[value][index])
            for value in ALLOWED_PANEL_THRESHOLDS
        }
        if len(hashes) != len(ALLOWED_PANEL_THRESHOLDS):
            raise AssertionError(
                f"pair {index} failed to distinguish all threshold settings"
            )

    pairs = []
    for row, output in zip(inputs, outputs[selected], strict=True):
        pairs.append(
            {
                "input": copy.deepcopy(row["input"]),
                "output": output,
                "input_sha256": row["input_sha256"],
                "output_sha256": grid_sha256(output),
                "panel_threshold": selected,
                "panel_counts": list(row["panel_counts"]),
                "input_provenance": {
                    "input_seed": row["input_seed"],
                    "sample_index": row["sample_index"],
                    "attempt": row["attempt"],
                    "count_profile": row["count_profile"],
                    "grid_h": row["grid_h"],
                    "grid_w": row["grid_w"],
                },
            }
        )

    rival_rows = []
    ambiguities = []
    for value in ALLOWED_PANEL_THRESHOLDS:
        train_mismatches = [
            index
            for index in range(demo_count)
            if outputs[value][index] != outputs[selected][index]
        ]
        query_mismatches = [
            index
            for index in range(query_count)
            if outputs[value][demo_count + index]
            != outputs[selected][demo_count + index]
        ]
        status = (
            "refuted_by_demonstrations"
            if train_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "panel_threshold": value,
            "racket_sha256": _sha256(rules[value]),
            "status": status,
            "demonstration_mismatch_indices": train_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_output_sha256": [
                grid_sha256(grid) for grid in outputs[value][:demo_count]
            ],
            "query_output_sha256": [
                grid_sha256(grid) for grid in outputs[value][demo_count:]
            ],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    source = rules[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"panel_threshold": selected},
        "parameter_selection": (
            "one seed-modulo-three selection before any pair unless explicitly "
            "overridden"
        ),
        "selection_scope": "once_per_episode",
        "allowed_panel_thresholds": list(ALLOWED_PANEL_THRESHOLDS),
        "canonical_default": DEFAULT_PANEL_THRESHOLD,
        "demo_count": demo_count,
        "query_count": query_count,
        "input_constraint": (
            "every input is emitted by the selected fixed-rule generator with a "
            "declared count profile containing panel counts 1, 2, and 3"
        ),
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "base_generator_sha256": BASE_GENERATOR_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/panel-threshold-{selected}.rkt",
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(inputs) * len(ALLOWED_PANEL_THRESHOLDS),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Explicit allowlist: labeled demos plus query inputs, no private answers."""
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_evidence(
    seeds,
    *,
    out,
    root=None,
    demo_count: int = 3,
    query_count: int = 4,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Retain finite source-bound evidence in a newly created directory."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    _validate_difficulty(difficulty)
    resolved_root = _resolve_root(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        return _write_evidence(
            seeds,
            out=out,
            root=resolved_root,
            demo_count=demo_count,
            query_count=query_count,
            difficulty=difficulty,
        )
    except Exception as exc:
        _write_json(
            out / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(seeds),
            },
        )
        raise


def _write_evidence(
    seeds: tuple[int, ...],
    *,
    out: Path,
    root: Path,
    demo_count: int,
    query_count: int,
    difficulty: str,
) -> dict[str, Any]:
    source_path = Path(__file__).resolve()
    task_dir = root / f"generators/{TASK_ID}"
    snapshot = out / "private/source_snapshot"
    snapshot.mkdir(parents=True)
    source_paths = (
        source_path,
        task_dir / "tests/test_parametric_threshold.py",
        task_dir / "workspace/parametric/README.md",
        task_dir / "workspace/parametric/adapter.py",
        task_dir / "workspace/parametric/promotion.json",
    )
    source_rows = []
    for path in source_paths:
        if path.is_file():
            target = snapshot / path.name
            target.write_bytes(path.read_bytes())
            source_rows.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256(path.read_bytes()),
                    "snapshot_path": str(target.relative_to(out)),
                }
            )

    rules = {
        value: materialize_rule(value, root=root)
        for value in ALLOWED_PANEL_THRESHOLDS
    }
    for value, source in rules.items():
        path = out / f"private/rules/panel-threshold-{value}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    canonical_checks = []
    episodes = []
    all_input_hashes: list[str] = []
    public_ids: set[str] = set()
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(rules[DEFAULT_PANEL_THRESHOLD], pair["input"], bridge=bridge)
            if actual != pair["output"]:
                raise AssertionError(
                    "canonical threshold-2 materialization failed a canonical pair"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "output_sha256": grid_sha256(actual),
                    "matched": True,
                }
            )

        for ordinal, seed in enumerate(seeds):
            episode = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                difficulty=difficulty,
                root=root,
                bridge=bridge,
            )
            public = public_challenge(episode)
            visible_id = public_challenge_id(public)
            if visible_id in public_ids:
                raise AssertionError(f"duplicate visible challenge ID: {visible_id}")
            public_ids.add(visible_id)
            private_path = out / f"private/episode-{ordinal:03d}.json"
            public_path = out / f"public/challenge-{visible_id}.json"
            _write_json(private_path, episode)
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_challenge_bytes(public))
            pair_hashes = [
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            ]
            all_input_hashes.extend(pair_hashes)
            episodes.append(
                {
                    "public_id": visible_id,
                    "public_path": str(public_path.relative_to(out)),
                    "private_path": str(private_path.relative_to(out)),
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "racket_sha256": episode["racket_sha256"],
                    "train_pairs": len(episode["train"]),
                    "query_pairs": len(episode["test"]),
                    "distinct_inputs": len(set(pair_hashes)),
                    "ambiguities": len(episode["ambiguities"]),
                }
            )

    if len(set(all_input_hashes)) != len(all_input_hashes):
        raise AssertionError("evidence set contains duplicate input grids")

    episodes.sort(key=lambda row: row["public_id"])
    counts = {
        "episodes": len(episodes),
        "train_pairs": sum(row["train_pairs"] for row in episodes),
        "query_pairs": sum(row["query_pairs"] for row in episodes),
        "distinct_input_grids": len(set(all_input_hashes)),
        "settings_exercised": len(
            {row["parameters"]["panel_threshold"] for row in episodes}
        ),
        "canonical_pairs_checked": len(canonical_checks),
        "ambiguous_parameter_rivals": sum(row["ambiguities"] for row in episodes),
    }
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "scope": (
            "finite evidence for thresholds 1, 2, and 3; no fixed-rule approval "
            "or training-admission claim"
        ),
        "parameters": {
            "panel_threshold": list(ALLOWED_PANEL_THRESHOLDS),
            "default": DEFAULT_PANEL_THRESHOLD,
            "selection_scope": "once_per_episode",
        },
        "demo_count": demo_count,
        "query_count": query_count,
        "difficulty": difficulty,
        "counts": counts,
        "base_generator_sha256": BASE_GENERATOR_SHA256,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "prototype_sha256": _sha256(source_path.read_bytes()),
        "runtime": racket_runtime_status(),
        "canonical_replay": canonical_checks,
        "source_snapshot": source_rows,
        "episodes": episodes,
        "limitations": [
            "Only the declared thresholds 1, 2, and 3 are tested as parameter rivals.",
            "Evidence covers the listed seeds and generated inputs, not every future seed.",
            "This prototype is proposed and unapproved; the canonical generator is unchanged.",
        ],
    }

    files = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        files.append(
            {
                "path": str(path.relative_to(out)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path.read_bytes()),
            }
        )
    report["files"] = files
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Racket-backed panel-threshold prototype evidence"
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
        difficulty=args.difficulty,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
