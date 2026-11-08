#!/usr/bin/env python3
"""Source-bound lesson identifiability census for task 49fe4f572f8d.

The shared battery intentionally materializes only a small smoke sample.  This
probe uses the same pinned seed recipe, difficulty bands, sample-index stride,
``puzzle_generators.runner.run_one`` path, and authoritative Racket execution,
but defaults to 100 complete five-demo lessons per band.  It records unique
inputs, the observed domain, cyclic schedule starts, declared-rival outcomes,
canonical-shortcut validity, and exact source hashes.

Run from the packet root so ``run_with_racket.py`` supplies the verified Racket:

    python3 run_with_racket.py python3 \
      generators/49fe4f572f8d/workspace/lesson_probe.py \
      --out ../checks/lesson-probe-final.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "49fe4f572f8d"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11
PINNED_SEED_SCHEMA = "profile-floor:v1"
DEFAULT_LESSONS_PER_BAND = 100

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_ROOT / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
TOOLS_ROOT = REPO_ROOT / "shared" / "tools"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def install_tools_namespace() -> None:
    """Expose ``shared/tools`` under the runtime's expected ``scripts`` name."""
    existing = sys.modules.get("scripts")
    if existing is not None:
        package_path = getattr(existing, "__path__", ())
        if str(TOOLS_ROOT) not in package_path:
            raise RuntimeError(
                "a conflicting scripts package is already loaded without shared/tools"
            )
        return
    package = types.ModuleType("scripts")
    package.__package__ = "scripts"
    package.__path__ = [str(TOOLS_ROOT)]
    sys.modules["scripts"] = package


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pinned_seed(task_id: str, band: str, index: int) -> int:
    """Match shared/tools/canonical_profile_gate.py::_pinned_seed exactly."""
    digest = hashlib.sha256(
        f"{PINNED_SEED_SCHEMA}:{task_id}:lesson:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _load_generator(path: Path = GENERATOR_PATH):
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("grid must be a nonempty list")
    if isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [[int(cell) for cell in row] for row in value]


def normalized_rule_hash(source: str) -> str:
    """Match the repository RULE_HASH convention."""
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_row(path: Path = CANONICAL_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise FileNotFoundError(f"canonical task {TASK_ID} not found in {path}")


def load_canonical_rule_source(
    path: Path = CANONICAL_PATH,
) -> tuple[str, str]:
    row = _canonical_row(path)
    source = row.get("program_solution")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"canonical task {TASK_ID} has no program_solution")
    return source.strip(), f"{path}:program_solution"


def load_canonical_pairs(path: Path = CANONICAL_PATH) -> list[dict[str, list[list[int]]]]:
    row = _canonical_row(path)
    pairs: list[dict[str, list[list[int]]]] = []
    train = row.get("train") or []
    test = row.get("test") or []
    if isinstance(test, dict):
        test = [test]
    for pair in [*train, *test]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            continue
        pairs.append(
            {
                "input": _normalize_grid(pair["input"]),
                "output": _normalize_grid(pair["output"]),
            }
        )
    return pairs


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _grid_profile(grid: list[list[int]]) -> dict[str, int]:
    foreground = [value for row in grid for value in row if value != 0]
    occupied_columns = sum(
        any(grid[row][column] != 0 for row in range(len(grid)))
        for column in range(len(grid[0]))
    )
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "cells": len(foreground),
        "occupied_columns": occupied_columns,
        "foreground_colors": len(set(foreground)),
    }


def _equal(left: Any, right: Any) -> bool:
    return left == right


def _call_lesson_hook(generator, demos: list[dict], query: dict) -> tuple[list[str], str | None]:
    hook = getattr(generator, "lesson_identifiable", None)
    if not callable(hook):
        return ["lesson_identifiable is not declared"], None
    try:
        reasons = hook(copy.deepcopy(demos), copy.deepcopy(query))
    except Exception as exc:  # evidence, not silence
        return [], f"{type(exc).__name__}: {exc}"
    if not isinstance(reasons, list) or any(not isinstance(item, str) for item in reasons):
        return [], f"invalid return {reasons!r}; expected list[str]"
    return reasons, None


def analyze_lessons(
    generator,
    lessons: list[dict],
    *,
    canonical_pairs: list[dict],
) -> dict[str, Any]:
    """Analyze already materialized Racket-backed lessons without hiding errors."""
    competitors = dict(getattr(generator, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}) or {})
    competitor_rows = {
        name: {
            "refuted_by_demos": 0,
            "survived_demos": 0,
            "query_discriminates": 0,
            "survived_all": 0,
            "errors": 0,
            "examples": [],
        }
        for name in competitors
    }
    per_band = {
        band: {
            "lessons": 0,
            "identifiable": 0,
            "unidentifiable": 0,
            "hook_errors": 0,
            "unique_inputs": 0,
        }
        for band in BANDS
    }
    input_hashes: set[str] = set()
    band_hashes: dict[str, set[str]] = {band: set() for band in BANDS}
    profiles: dict[str, set[int]] = {
        "height": set(),
        "width": set(),
        "cells": set(),
        "occupied_columns": set(),
        "foreground_colors": set(),
    }
    start_residues: Counter[int] = Counter()
    unidentifiable_examples: list[dict[str, Any]] = []
    hook_error_examples: list[dict[str, Any]] = []
    identifiable = 0
    unidentifiable = 0
    hook_errors = 0

    for lesson_index, lesson in enumerate(lessons):
        band = str(lesson.get("band", "unknown"))
        band_row = per_band.setdefault(
            band,
            {
                "lessons": 0,
                "identifiable": 0,
                "unidentifiable": 0,
                "hook_errors": 0,
                "unique_inputs": 0,
            },
        )
        band_row["lessons"] += 1
        start = int(lesson.get("sample_index", 0))
        schedule_size = len(getattr(generator, "SCHEDULE_PROFILES", ()))
        if schedule_size:
            start_residues[start % schedule_size] += 1

        pairs = [*lesson["demos"], lesson["query"]]
        for pair in pairs:
            grid = pair["input"]
            digest = _grid_hash(grid)
            input_hashes.add(digest)
            band_hashes.setdefault(band, set()).add(digest)
            for name, value in _grid_profile(grid).items():
                profiles[name].add(value)

        reasons, hook_error = _call_lesson_hook(
            generator, lesson["demos"], lesson["query"]
        )
        if hook_error is not None:
            hook_errors += 1
            band_row["hook_errors"] += 1
            if len(hook_error_examples) < 10:
                hook_error_examples.append(
                    {
                        "lesson": lesson_index,
                        "band": band,
                        "seed": lesson.get("seed"),
                        "sample_index": start,
                        "error": hook_error,
                    }
                )
        elif reasons:
            unidentifiable += 1
            band_row["unidentifiable"] += 1
            if len(unidentifiable_examples) < 10:
                unidentifiable_examples.append(
                    {
                        "lesson": lesson_index,
                        "band": band,
                        "seed": lesson.get("seed"),
                        "sample_index": start,
                        "reasons": reasons,
                    }
                )
        else:
            identifiable += 1
            band_row["identifiable"] += 1

        for name, competitor in competitors.items():
            row = competitor_rows[name]
            try:
                survives = all(
                    _equal(competitor(copy.deepcopy(pair["input"])), pair["output"])
                    for pair in lesson["demos"]
                )
                agrees_query = _equal(
                    competitor(copy.deepcopy(lesson["query"]["input"])),
                    lesson["query"]["output"],
                )
            except Exception as exc:
                row["errors"] += 1
                if len(row["examples"]) < 3:
                    row["examples"].append(
                        {
                            "band": band,
                            "seed": lesson.get("seed"),
                            "sample_index": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                continue
            if survives:
                row["survived_demos"] += 1
                key = "survived_all" if agrees_query else "query_discriminates"
                row[key] += 1
                if len(row["examples"]) < 3:
                    row["examples"].append(
                        {
                            "band": band,
                            "seed": lesson.get("seed"),
                            "sample_index": start,
                            "query_agrees": agrees_query,
                        }
                    )
            else:
                row["refuted_by_demos"] += 1

    for band, hashes in band_hashes.items():
        per_band.setdefault(band, {})["unique_inputs"] = len(hashes)

    canonical_shortcuts: dict[str, Any] = {}
    for name, shortcut in shortcuts.items():
        mismatches: list[int] = []
        errors: list[str] = []
        for index, pair in enumerate(canonical_pairs):
            try:
                predicted = shortcut(copy.deepcopy(pair["input"]))
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
                continue
            if not _equal(predicted, pair["output"]):
                mismatches.append(index)
        canonical_shortcuts[name] = {
            "canonical_pairs": len(canonical_pairs),
            "fits_all": bool(canonical_pairs) and not mismatches and not errors,
            "mismatch_indices": mismatches,
            "errors": errors,
        }

    domain = {
        name: {
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "values": sorted(values),
        }
        for name, values in profiles.items()
    }
    return {
        "lessons": len(lessons),
        "pairs": sum(len(lesson["demos"]) + 1 for lesson in lessons),
        "unique_inputs": len(input_hashes),
        "identifiable": identifiable,
        "unidentifiable": unidentifiable,
        "hook_errors": hook_errors,
        "per_band": per_band,
        "schedule_start_residues": dict(sorted(start_residues.items())),
        "domain": domain,
        "competitors_declared": sorted(competitors),
        "competitors": competitor_rows,
        "canonical_shortcuts": canonical_shortcuts,
        "unidentifiable_examples": unidentifiable_examples,
        "hook_error_examples": hook_error_examples,
    }


def materialize_lessons(generator, lessons_per_band: int) -> tuple[list[dict], list[str], dict[str, Any]]:
    """Use the production runner with one persistent authoritative Racket bridge."""
    install_tools_namespace()
    from puzzle_generators import runner

    rule_source, rule_file = load_canonical_rule_source()
    pinned_hash = getattr(generator, "RULE_HASH", None)
    actual_hash = normalized_rule_hash(rule_source)
    if pinned_hash != actual_hash:
        raise RuntimeError(
            f"RULE_HASH mismatch: generator pins {pinned_hash!r}, canonical is {actual_hash!r}"
        )
    bundle = runner.GeneratorBundle(
        task_id=TASK_ID,
        rule_task_id=getattr(generator, "RULE_TASK_ID", TASK_ID),
        rule_source=rule_source,
        rule_callable_text=runner.wrap_rule(rule_source),
        rule_file=rule_file,
        generator_module=generator,
        allow_identity_output=bool(getattr(generator, "ALLOW_IDENTITY_OUTPUT", False)),
        kind="per_puzzle",
    )
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    lessons: list[dict] = []
    errors: list[str] = []
    try:
        for band in BANDS:
            for index in range(lessons_per_band):
                seed = pinned_seed(TASK_ID, band, index)
                sample_index = index * LESSON_SAMPLE_STRIDE
                try:
                    instance = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=sample_index,
                        n_train=int(getattr(generator, "EXAMPLES_NEEDED", 5)),
                        n_test=1,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    errors.append(
                        f"band={band} index={index} seed={seed} "
                        f"sample_index={sample_index}: {type(exc).__name__}: {exc}"
                    )
                    continue
                lessons.append(
                    {
                        "band": band,
                        "index_in_band": index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "demos": instance["train"],
                        "query": instance["test"][0],
                    }
                )
    finally:
        bridge.shutdown()

    sampler = {
        "runner": "puzzle_generators.runner.run_one",
        "racket_rule_file": rule_file,
        "seed_recipe": (
            f"int(sha256('{PINNED_SEED_SCHEMA}:<task>:lesson:<band>:<index>')"
            ".hexdigest()[:12], 16)"
        ),
        "sample_index": f"index * {LESSON_SAMPLE_STRIDE}",
        "difficulty": "easy|medium|hard passed to every generated pair",
        "n_demos": int(getattr(generator, "EXAMPLES_NEEDED", 5)),
        "n_queries": 1,
        "dedup_and_validation": "runner.run_one production path",
    }
    return lessons, errors, sampler


def build_report(lessons_per_band: int) -> dict[str, Any]:
    generator = _load_generator()
    canonical_pairs = load_canonical_pairs()
    lessons, errors, sampler = materialize_lessons(generator, lessons_per_band)
    analysis = analyze_lessons(
        generator,
        lessons,
        canonical_pairs=canonical_pairs,
    )
    generator_hash = sha256_file(GENERATOR_PATH)
    expected = lessons_per_band * len(BANDS)
    failures: list[str] = []
    if errors:
        failures.append(f"{len(errors)} lesson materialization errors")
    if analysis["lessons"] != expected:
        failures.append(
            f"materialized {analysis['lessons']}/{expected} requested lessons"
        )
    if analysis["unidentifiable"]:
        failures.append(f"{analysis['unidentifiable']} unidentifiable lessons")
    if analysis["hook_errors"]:
        failures.append(f"{analysis['hook_errors']} lesson hook errors")
    survivors = {
        name: row["survived_demos"]
        for name, row in analysis["competitors"].items()
        if row["survived_demos"]
    }
    if survivors:
        failures.append(f"declared competitors survived demos: {survivors}")
    invalid_shortcuts = [
        name
        for name, row in analysis["canonical_shortcuts"].items()
        if not row["fits_all"]
    ]
    if invalid_shortcuts:
        failures.append(
            "declared canonical shortcuts do not fit every canonical pair: "
            + ", ".join(invalid_shortcuts)
        )

    return {
        "schema": "arcpuzzles-task-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": generator_hash,
        "rule_hash_pin": getattr(generator, "RULE_HASH", None),
        "lessons_per_band_requested": lessons_per_band,
        "lessons_requested": expected,
        "sampler": sampler,
        "materialization_errors": errors,
        "analysis": analysis,
        "status": "pass" if not failures else "fail",
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lessons-per-band",
        type=int,
        default=DEFAULT_LESSONS_PER_BAND,
        help="complete five-demo lessons per difficulty band (default: 100)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.lessons_per_band <= 0:
        parser.error("--lessons-per-band must be positive")

    report = build_report(args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    analysis = report["analysis"]
    print(
        f"{TASK_ID}: {report['status'].upper()} "
        f"lessons={analysis['lessons']}/{report['lessons_requested']} "
        f"unique_inputs={analysis['unique_inputs']} "
        f"identifiable={analysis['identifiable']} "
        f"unidentifiable={analysis['unidentifiable']} "
        f"hook_errors={analysis['hook_errors']}"
    )
    if report["failures"]:
        for failure in report["failures"]:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
