#!/usr/bin/env python3
"""Materialize one native contract run plus compact adversarial evidence.

The command-line path always uses the protected Racket evaluator. Tests may pass
``python_apply_program`` explicitly to exercise serialization without spawning a
nested Racket process; such output is marked by the worker as backend ``test``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "89704f9047c0"
_SCHEMA = "89704f9047c0-parametric-evidence-v1"


def _load_prototype():
    path = Path(__file__).with_name("prototype.py")
    spec = importlib.util.spec_from_file_location("_task_89704f9047c0_evidence_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _contract(root: Path) -> dict[str, Any]:
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "promotion.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "arcpuzzles-parametric-adapter-v1":
        raise ValueError("unexpected promotion contract schema")
    return value


def qualification_jobs(*, seed: int = 20261024) -> list[dict[str, Any]]:
    """One matched three-demo/four-query Racket job for every setting."""
    PROTOTYPE._integer(seed, 0, 2**63 - 1, "seed")
    return [
        {"seed": seed, "settings": copy.deepcopy(settings), "demos": 3, "queries": 4}
        for settings in PROTOTYPE.SETTINGS
    ]


def python_apply_program(program: str, grid: list[list[int]]) -> list[list[int]]:
    """Test-only evaluator with the same finite program table as the adapter."""
    matches = [
        settings
        for settings in PROTOTYPE.SETTINGS
        if PROTOTYPE.program(settings) == program
    ]
    if len(matches) != 1:
        raise ValueError(f"program maps to {len(matches)} declared settings")
    return PROTOTYPE.apply_python(grid, matches[0])


def _input_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def projection_evidence(*, seed: int = 20261024) -> dict[str, Any]:
    """Check matched inputs, count edges, sequential projection, and 30x30 reach."""
    ordinary = [
        PROTOTYPE.generate_episode(seed, settings, demos=3, queries=4)
        for settings in PROTOTYPE.SETTINGS
    ]
    baseline_inputs = [
        pair["input"] for pair in [*ordinary[0]["train"], *ordinary[0]["test"]]
    ]
    matched_inputs = all(
        [pair["input"] for pair in [*episode["train"], *episode["test"]]] == baseline_inputs
        for episode in ordinary[1:]
    )
    teaching = [PROTOTYPE.teaching_survivors(episode) for episode in ordinary]

    prefix_checks = []
    public_shapes = []
    public_ids = []
    for settings, four in zip(PROTOTYPE.SETTINGS, ordinary):
        one = PROTOTYPE.generate_episode(seed, settings, demos=3, queries=1)
        visible_one = PROTOTYPE.public_turn(one, 0)
        visible_four = PROTOTYPE.public_turn(four, 0)
        prefix_checks.append(public_challenge_bytes(visible_one) == public_challenge_bytes(visible_four))
        public_shapes.append(
            set(visible_four) == {"train", "test"}
            and len(visible_four["test"]) == 1
            and set(visible_four["test"][0]) == {"input"}
            and all(set(pair) == {"input", "output"} for pair in visible_four["train"])
        )
        public_ids.append(PROTOTYPE.public_turn_id(four, 0))

    minimum = PROTOTYPE.generate_episode(seed, PROTOTYPE.DEFAULT_SETTINGS, demos=2, queries=1)
    maximum = PROTOTYPE.generate_episode(seed, PROTOTYPE.DEFAULT_SETTINGS, demos=6, queries=8)
    ordinary_query_dimensions = [
        [len(pair["input"]), len(pair["input"][0])] for pair in ordinary[0]["test"]
    ]
    all_keys = [_input_key(grid) for grid in baseline_inputs]
    return {
        "schema": _SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": [copy.deepcopy(settings) for settings in PROTOTYPE.SETTINGS],
        "matched_inputs_across_settings": matched_inputs,
        "demonstration_only_survivors": teaching,
        "all_teaching_sets_unique": all(
            survivors == [settings]
            for survivors, settings in zip(teaching, PROTOTYPE.SETTINGS)
        ),
        "first_turn_matches_single_query": all(prefix_checks),
        "public_projection_private_fields_absent": all(public_shapes),
        "public_first_turn_ids": public_ids,
        "public_ids_unique_by_visible_labels": len(set(public_ids)) == len(public_ids),
        "ordinary_query_dimensions": ordinary_query_dimensions,
        "ordinary_inputs_distinct": len(all_keys) == len(set(all_keys)),
        "reaches_30_by_30": [30, 30] in ordinary_query_dimensions,
        "boundary_counts": {
            "minimum": {"demos": len(minimum["train"]), "queries": len(minimum["test"])},
            "maximum": {"demos": len(maximum["train"]), "queries": len(maximum["test"])},
        },
    }


def _write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    pending = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


def _write_json(path: Path, value: Any) -> None:
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    _write_bytes(path, raw)


def _write_public_examples(destination: Path, *, seed: int) -> list[str]:
    public_dir = destination / "public"
    expected: set[Path] = set()
    for settings in PROTOTYPE.SETTINGS:
        episode = PROTOTYPE.generate_episode(seed, settings, demos=3, queries=4)
        visible = PROTOTYPE.public_turn(episode, 0)
        raw = public_challenge_bytes(visible)
        path = public_dir / f"challenge-{hashlib.sha256(raw).hexdigest()}.json"
        _write_bytes(path, raw)
        expected.add(path)
    for stale in public_dir.glob("challenge-*.json"):
        if stale not in expected:
            stale.unlink()
    return [str(path) for path in sorted(expected)]


def materialize(
    output: Path | str,
    *,
    root: Path | str | None = None,
    seed: int = 20261024,
    apply_program: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    """Run the native worker and write deterministic execution/adversarial JSON."""
    source_root = _root(root)
    destination = Path(output).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    execution = evaluate_contract(
        source_root,
        TASK_ID,
        _contract(source_root),
        qualification_jobs(seed=seed),
        apply_program=apply_program,
    )
    execution = {"schema": _SCHEMA, "task_id": TASK_ID, "seed": seed, **execution}
    adversarial = projection_evidence(seed=seed)
    execution_path = destination / "execution.json"
    adversarial_path = destination / "adversarial.json"
    _write_json(execution_path, execution)
    _write_json(adversarial_path, adversarial)
    public_files = _write_public_examples(destination, seed=seed)
    return {
        "execution": str(execution_path),
        "execution_sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest(),
        "adversarial": str(adversarial_path),
        "adversarial_sha256": hashlib.sha256(adversarial_path.read_bytes()).hexdigest(),
        "public_files": public_files,
        "backend": execution["racket"].get("backend"),
        "protected": execution["racket"].get("protected"),
        "racket_evaluations": execution["racket_evaluations"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).with_name("evidence") / "current",
        help="evidence directory (default: task-local evidence/current)",
    )
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args(argv)
    result = materialize(args.out, seed=args.seed)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
