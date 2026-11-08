#!/usr/bin/env python3
"""Proposed episode-level horizontal fan-stride extension for 1856980929fe.

The production generator and canonical authority stay unchanged.  This task-local
prototype varies only the horizontal displacement per downward fan level:
``k * rectangle_width * fan_stride`` with canonical ``fan_stride=1`` and one
nearby alternative ``fan_stride=2``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "1856980929fe"
PROTOTYPE_VERSION = "1.0.0"
FAN_STRIDES = (1, 2)
DEFAULT_FAN_STRIDE = 1
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
CANONICAL_SHA256 = "d57dfba75662273fbbd5aced174f3a28831099169574954cffd383ff42478ccf"
CANONICAL_STRIDE_TERM = "(* k rw)"
STRIDE_TWO_TERM = "(* (* k 2) rw)"
SEED_COUNT_SCHEDULE = (3, 2, 1, 3, 2, 1, 3)
DIFFICULTY_SCHEDULE = ("easy", "medium", "hard", None)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative plain integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} count must be a positive plain integer")
    if value <= 0:
        raise ValueError(f"{name} count must be positive")
    return value


def _validate_fan_stride(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("fan_stride must be a plain integer")
    if value not in FAN_STRIDES:
        raise ValueError(f"fan_stride must be one of {FAN_STRIDES}, got {value!r}")
    return value


def choose_setting(seed: Any) -> int:
    """Select one episode-fixed fan stride deterministically from a seed."""
    validated = _validate_seed(seed)
    return FAN_STRIDES[validated % len(FAN_STRIDES)]


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    if source.count(CANONICAL_STRIDE_TERM) != 2:
        raise ValueError("canonical source must contain exactly two stride terms")
    if STRIDE_TWO_TERM in source:
        raise ValueError("canonical source unexpectedly contains stride-two term")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load the unique pinned canonical Racket authority for this task."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
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
    return _check_canonical_source(sources.pop())


def materialize_rule(
    fan_stride: int = DEFAULT_FAN_STRIDE,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared stride while preserving exact canonical bytes."""
    selected = _validate_fan_stride(fan_stride)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selected == DEFAULT_FAN_STRIDE:
        return canonical
    alternative = canonical.replace(CANONICAL_STRIDE_TERM, STRIDE_TWO_TERM)
    if alternative.count(STRIDE_TWO_TERM) != 2:
        raise AssertionError("failed to materialize stride-two rule")
    return alternative


def restore_canonical(source: Any) -> str:
    """Restore either declared materialization to exact canonical source bytes."""
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    if source.count(STRIDE_TWO_TERM) == 2:
        restored = source.replace(STRIDE_TWO_TERM, CANONICAL_STRIDE_TERM)
    elif source.count(CANONICAL_STRIDE_TERM) == 2:
        restored = source
    else:
        raise ValueError("Racket source is not a declared fan_stride materialization")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper from a declared rule source."""
    restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    callable_source = source[len("(rule!") : -1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("expected a wrapped grid lambda")
    return callable_source


def _racket_grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact declared Racket rule on one normalized grid."""
    normalized = normalize_grid(grid)
    expression = f"({rule_callable(source)} {_racket_grid_literal(normalized)})"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(timeout=30)
    with manager as active:
        assert active is not None
        return normalize_grid(active.eval_text(expression))


def _derived_generation_seed(episode_seed: int, pair_index: int, attempt: int) -> int:
    digest = _sha256(f"{TASK_ID}:{episode_seed}:{pair_index}:{attempt}")
    return int(digest[:16], 16)


def _generate_inputs(
    episode_seed: int,
    count: int,
    *,
    root: Path,
    bridge: RacketBridge,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    sources = {
        str(stride): materialize_rule(stride, root=root) for stride in FAN_STRIDES
    }
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pair_index in range(count):
        n_seeds = SEED_COUNT_SCHEDULE[pair_index % len(SEED_COUNT_SCHEDULE)]
        difficulty = DIFFICULTY_SCHEDULE[pair_index % len(DIFFICULTY_SCHEDULE)]
        for attempt in range(100):
            generation_seed = _derived_generation_seed(
                episode_seed, pair_index, attempt
            )
            try:
                grid = generator.generate(
                    generation_seed,
                    pair_index,
                    difficulty=difficulty,
                    n_seeds=n_seeds,
                )
            except ValueError:
                continue
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(
                    f"selected generator emitted invalid input {pair_index}: {errors}"
                )
            observed = generator.observe_overrides(grid)
            if observed.get("n_seeds") != n_seeds:
                raise AssertionError(
                    f"selected generator missed n_seeds={n_seeds}: {observed}"
                )
            normalized = normalize_grid(grid)
            digest = _grid_sha256(normalized)
            if digest in seen:
                continue
            outputs = {
                key: execute_rule(source, normalized, bridge=bridge)
                for key, source in sources.items()
            }
            if outputs["1"] == outputs["2"]:
                continue
            seen.add(digest)
            rows.append(
                {
                    "input": normalized,
                    "input_sha256": digest,
                    "counterfactual_outputs": outputs,
                    "sampling": {
                        "seed": generation_seed,
                        "sample_index": pair_index,
                        "attempt": attempt,
                        "difficulty": difficulty,
                        "n_seeds": n_seeds,
                    },
                }
            )
            break
        else:
            raise AssertionError(
                f"could not generate a distinct stride-discriminating input for pair {pair_index}"
            )
    return rows, {
        "path": generator_path.relative_to(root).as_posix(),
        "sha256": generator_sha256,
    }


def make_episode(
    seed: Any,
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one deterministic fixed-setting episode with distinct queries."""
    episode_seed = _validate_seed(seed)
    demos = _validate_count(demo_count, "demo")
    queries = _validate_count(query_count, "query")
    selected = choose_setting(episode_seed)
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    manager = (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(timeout=30, max_calls_before_restart=128)
    )
    with manager as active:
        assert active is not None
        rows, generator_source = _generate_inputs(
            episode_seed,
            demos + queries,
            root=resolved_root,
            bridge=active,
        )
    pairs = []
    for row in rows:
        outputs = row["counterfactual_outputs"]
        pairs.append(
            {
                **row,
                "output": outputs[str(selected)],
                "fan_stride": selected,
            }
        )
    return {
        "schema": "arcpuzzles-fan-stride-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": episode_seed,
        "parameters": {"fan_stride": selected},
        "generator_source": generator_source,
        "program_sha256": _sha256(materialize_rule(selected, root=resolved_root)),
        "train": pairs[:demos],
        "test": pairs[demos:],
        "pairs": pairs,
    }


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Re-execute both settings and determine whether demos identify the rule."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    selected = _validate_fan_stride(episode["parameters"]["fan_stride"])
    train = episode["train"]
    test = episode["test"]
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    manager = (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(timeout=30, max_calls_before_restart=128)
    )
    settings: list[dict[str, Any]] = []
    with manager as active:
        assert active is not None
        for stride in FAN_STRIDES:
            source = materialize_rule(stride, root=resolved_root)
            train_predictions = [
                execute_rule(source, pair["input"], bridge=active) for pair in train
            ]
            query_predictions = [
                execute_rule(source, pair["input"], bridge=active) for pair in test
            ]
            demo_mismatches = [
                index
                for index, (prediction, pair) in enumerate(
                    zip(train_predictions, train, strict=True)
                )
                if prediction != pair["output"]
            ]
            query_mismatches = [
                index
                for index, (prediction, pair) in enumerate(
                    zip(query_predictions, test, strict=True)
                )
                if prediction != pair["output"]
            ]
            status = (
                "matches_episode"
                if not demo_mismatches and not query_mismatches
                else "refuted_by_demonstrations"
                if demo_mismatches
                else "ambiguous_query"
            )
            settings.append(
                {
                    "fan_stride": stride,
                    "status": status,
                    "program_sha256": _sha256(source),
                    "demonstration_mismatch_indices": demo_mismatches,
                    "query_mismatch_indices": query_mismatches,
                    "train_predictions": train_predictions,
                    "query_predictions": query_predictions,
                }
            )
    matches = [
        row["fan_stride"] for row in settings if row["status"] == "matches_episode"
    ]
    return {
        "status": (
            "no_ambiguity_found"
            if matches == [selected]
            and all(
                row["status"] == "refuted_by_demonstrations"
                for row in settings
                if row["fan_stride"] != selected
            )
            else "ambiguity_or_label_failure"
        ),
        "selected_fan_stride": selected,
        "matching_settings": matches,
        "settings": settings,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only model-visible demonstrations and query inputs."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def public_filename(episode: dict[str, Any]) -> str:
    """Name public evidence from exactly the visible challenge bytes."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_public(path: Path, challenge: dict[str, Any]) -> None:
    payload = public_challenge_bytes(challenge)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == payload:
            raise ValueError(f"duplicate visible public challenge: {path.name}")
        raise AssertionError(f"public challenge identifier collision: {path.name}")
    path.write_bytes(payload)


def _file_record(path: Path, *, relative_to: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": _sha256(path.read_bytes()),
    }


def _canonical_replay(
    canonical: str,
    *,
    root: Path,
    bridge: RacketBridge,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = execute_rule(canonical, pair["input"], bridge=bridge)
        rows.append(
            {
                **pair,
                "actual": actual,
                "matches": actual == pair["output"],
                "input_sha256": _grid_sha256(pair["input"]),
                "actual_output_sha256": _grid_sha256(actual),
            }
        )
    if not rows or not all(row["matches"] for row in rows):
        raise AssertionError("canonical fan_stride=1 failed a labeled canonical pair")
    return rows


def verify_evidence(
    out: Path | str,
    *,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Re-execute a written bundle and verify public/private boundaries."""
    evidence_root = Path(out).resolve()
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    report = json.loads((evidence_root / "report.json").read_text(encoding="utf-8"))
    if report.get("task_id") != TASK_ID:
        raise AssertionError("evidence report belongs to another task")
    if report.get("status") != "proposed_unapproved" or report.get("approved") is not False:
        raise AssertionError("evidence must remain explicitly proposed and unapproved")

    canonical = canonical_source(root=resolved_root)
    rule_sources: dict[int, str] = {}
    for row in report["rules"]:
        stride = _validate_fan_stride(row["fan_stride"])
        path = evidence_root / row["path"]
        source = path.read_text(encoding="utf-8")
        if _sha256(path.read_bytes()) != row["sha256"]:
            raise AssertionError(f"rule hash mismatch for fan_stride={stride}")
        if source != materialize_rule(stride, source=canonical):
            raise AssertionError(f"stored rule is not exact fan_stride={stride}")
        rule_sources[stride] = source
    if set(rule_sources) != set(FAN_STRIDES):
        raise AssertionError("evidence must contain every declared rule setting")

    for row in report["files"]:
        path = evidence_root / row["path"]
        if not path.is_file() or _sha256(path.read_bytes()) != row["sha256"]:
            raise AssertionError(f"payload file hash mismatch: {row['path']}")

    labels_checked = 0
    rival_predictions_checked = 0
    distinct_inputs: set[str] = set()
    settings_exercised: set[int] = set()
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        canonical_rows = _canonical_replay(canonical, root=resolved_root, bridge=bridge)
        stored_canonical = json.loads(
            (evidence_root / report["canonical_check_path"]).read_text(encoding="utf-8")
        )
        if stored_canonical != canonical_rows:
            raise AssertionError("stored canonical replay differs from live Racket replay")

        for row in report["episodes"]:
            episode = json.loads(
                (evidence_root / row["private_path"]).read_text(encoding="utf-8")
            )
            stored_analysis = json.loads(
                (evidence_root / row["analysis_path"]).read_text(encoding="utf-8")
            )
            selected = _validate_fan_stride(episode["parameters"]["fan_stride"])
            settings_exercised.add(selected)
            visible = public_challenge(episode)
            public_path = evidence_root / row["public_path"]
            if public_path.name != public_filename(episode):
                raise AssertionError("public filename is not derived from visible bytes")
            if public_path.read_bytes() != public_challenge_bytes(visible):
                raise AssertionError("public challenge bytes contain drift or private data")

            live_analysis = analyze_episode(
                episode, root=resolved_root, bridge=bridge
            )
            if live_analysis != stored_analysis:
                raise AssertionError("stored rival analysis differs from live Racket replay")
            if live_analysis["status"] != "no_ambiguity_found":
                raise AssertionError("episode is ambiguous under a declared setting")
            by_stride = {item["fan_stride"]: item for item in live_analysis["settings"]}
            pairs = episode["train"] + episode["test"]
            for pair_index, pair in enumerate(pairs):
                distinct_inputs.add(pair["input_sha256"])
                local_index = (
                    pair_index
                    if pair_index < len(episode["train"])
                    else pair_index - len(episode["train"])
                )
                prediction_key = (
                    "train_predictions"
                    if pair_index < len(episode["train"])
                    else "query_predictions"
                )
                selected_prediction = by_stride[selected][prediction_key][local_index]
                if selected_prediction != pair["output"]:
                    raise AssertionError("selected Racket prediction differs from stored label")
                labels_checked += 1
                for stride in FAN_STRIDES:
                    prediction = by_stride[stride][prediction_key][local_index]
                    if prediction != pair["counterfactual_outputs"][str(stride)]:
                        raise AssertionError("stored counterfactual differs from Racket replay")
                    rival_predictions_checked += 1

    if settings_exercised != set(FAN_STRIDES):
        raise AssertionError(
            f"evidence must exercise both fan strides, got {settings_exercised}"
        )
    if len(distinct_inputs) != report["counts"]["distinct_input_grids"]:
        raise AssertionError("distinct-input count drift")
    return {
        "schema": "arcpuzzles-parametric-evidence-verification-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "episodes_checked": len(report["episodes"]),
        "labels_checked": labels_checked,
        "rival_predictions_checked": rival_predictions_checked,
        "canonical_pairs_checked": len(canonical_rows),
        "distinct_input_grids": len(distinct_inputs),
        "settings_exercised": sorted(settings_exercised),
        "report_sha256": _sha256((evidence_root / "report.json").read_bytes()),
    }


def _write_evidence(
    seeds: tuple[int, ...],
    *,
    out: Path,
    root: Path,
    demo_count: int,
    query_count: int,
) -> dict[str, Any]:
    canonical = canonical_source(root=root)
    prototype_path = Path(__file__).resolve()
    generator_path = root / "generators" / TASK_ID / "generator.py"
    source_rows = [
        {
            "role": "prototype",
            "path": prototype_path.relative_to(root).as_posix(),
            "sha256": _sha256(prototype_path.read_bytes()),
        },
        {
            "role": "selected_generator",
            "path": generator_path.relative_to(root).as_posix(),
            "sha256": _sha256(generator_path.read_bytes()),
        },
    ]

    rule_rows: list[dict[str, Any]] = []
    for stride in FAN_STRIDES:
        source = materialize_rule(stride, source=canonical)
        path = out / f"private/rules/fan-stride-{stride}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                "fan_stride": stride,
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(path.read_bytes()),
                "callable_sha256": _sha256(rule_callable(source)),
            }
        )

    episode_rows: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    public_payloads: dict[str, dict[str, Any]] = {}
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        canonical_rows = _canonical_replay(canonical, root=root, bridge=bridge)
        canonical_check_path = "private/canonical-default-check.json"
        _write_json(out / canonical_check_path, canonical_rows)

        for index, seed in enumerate(seeds):
            episode = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            replay = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            if replay != episode:
                raise AssertionError("same-seed episode replay changed")
            analysis = analyze_episode(episode, root=root, bridge=bridge)
            if analysis["status"] != "no_ambiguity_found":
                raise AssertionError("declared stride rival was not refuted by demonstrations")

            public = public_challenge(episode)
            public_path = f"public/{public_filename(episode)}"
            if public_path in public_payloads:
                raise ValueError(f"duplicate visible public challenge: {public_path}")
            public_payloads[public_path] = public
            private_path = f"private/episodes/episode-{index:03d}.json"
            analysis_path = f"private/episodes/episode-{index:03d}-analysis.json"
            _write_json(out / private_path, episode)
            _write_json(out / analysis_path, analysis)
            distinct_inputs.update(pair["input_sha256"] for pair in episode["pairs"])
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "demo_count": len(episode["train"]),
                    "query_count": len(episode["test"]),
                    "public_path": public_path,
                    "public_id": public_challenge_id(public),
                    "private_path": private_path,
                    "analysis_path": analysis_path,
                    "episode_sha256": _sha256(_stable_json(episode)),
                    "deterministic_replay": True,
                    "rivals": [
                        {
                            key: item[key]
                            for key in (
                                "fan_stride",
                                "status",
                                "demonstration_mismatch_indices",
                                "query_mismatch_indices",
                            )
                        }
                        for item in analysis["settings"]
                    ],
                }
            )

    for public_path in sorted(public_payloads):
        _write_public(out / public_path, public_payloads[public_path])

    episode_rows.sort(key=lambda row: row["public_id"])
    settings_exercised = {row["parameters"]["fan_stride"] for row in episode_rows}
    if settings_exercised != set(FAN_STRIDES):
        raise AssertionError(
            f"seed set must exercise both fan strides, got {settings_exercised}"
        )
    ambiguous_count = sum(
        rival["status"] == "ambiguous_query"
        for episode in episode_rows
        for rival in episode["rivals"]
    )
    files = [
        _file_record(path, relative_to=out)
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    report: dict[str, Any] = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "fan_stride",
            "allowed_values": list(FAN_STRIDES),
            "original_default": DEFAULT_FAN_STRIDE,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "find each solid green rectangle independently, retain every seed, "
            "advance one rectangle-height downward per level, stamp symmetric "
            "left/right copies, and clip at the canvas; only the horizontal "
            "rectangle-width multiplier changes"
        ),
        "input_scope": (
            f"lawful production inputs with {demo_count} demonstrations and "
            f"{query_count} distinct queries per episode; each retained input "
            "distinguishes fan_stride 1 from 2"
        ),
        "sources": source_rows,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "canonical_source_sha256": CANONICAL_SHA256,
        "canonical_check_path": canonical_check_path,
        "episodes": episode_rows,
        "files": files,
        "counts": {
            "episodes": len(episode_rows),
            "train_pairs": demo_count * len(episode_rows),
            "query_pairs": query_count * len(episode_rows),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(settings_exercised),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": len(FAN_STRIDES) * len(episode_rows),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed task-local prototype only; no production API, catalog, approval, or training-admission change.",
            "Evidence covers fan_stride values 1 and 2 and the supplied finite seed set, not all seeds or alternative hypotheses.",
            "Input grammar is shared across settings, but the evidence sampler retains only inputs where the two declared settings differ visibly.",
            "The canonical fan_stride=1 source is byte-identical to the pinned authority and is replayed on every labeled canonical record.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def write_evidence(
    seeds: tuple[int, ...] | list[int],
    *,
    out: Path | str,
    root: Path | str | None = None,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Create and independently re-verify a compact evidence bundle."""
    seed_values = tuple(_validate_seed(seed) for seed in seeds)
    if not seed_values:
        raise ValueError("at least one seed is required")
    if len(set(seed_values)) != len(seed_values):
        raise ValueError("episode seeds must be distinct")
    demos = _validate_count(demo_count, "demo")
    queries = _validate_count(query_count, "query")
    output = Path(out).resolve()
    if output.exists():
        raise FileExistsError(output)
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = _write_evidence(
            seed_values,
            out=output,
            root=resolved_root,
            demo_count=demos,
            query_count=queries,
        )
        verification = verify_evidence(output, root=resolved_root)
        _write_json(output / "verification.json", verification)
        return report
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = write_evidence(
        tuple(args.seeds),
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "episodes": report["counts"]["episodes"],
                "train_pairs": report["counts"]["train_pairs"],
                "query_pairs": report["counts"]["query_pairs"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
