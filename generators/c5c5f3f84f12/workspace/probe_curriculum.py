#!/usr/bin/env python3
"""Fast source-bound curriculum probe for c5c5f3f84f12.

This complements the shared lesson census.  The census samples many materialized
lessons but does not rotate every query code through every cyclic schedule start.
This probe does exactly that, dynamically using the generator's declared
LESSON_COMPETITORS, SEMANTIC_WITNESSES, and CANONICAL_SHORTCUTS.  It also checks
canonical rows and exact boundary overrides.

Run from the repository root:

    PYTHONPATH=shared/runtime:src python3 \
      generators/c5c5f3f84f12/workspace/probe_curriculum.py \
      --seeds-per-band 8 --out ../checks/curriculum-probe.json

The probe uses the task-local independent Python oracle.  Racket parity belongs
in the focused regression test and shared battery, not this fast diagnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "c5c5f3f84f12"
BANDS = ("easy", "medium", "hard")
CORNERS = ("tl", "tr", "br", "bl")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:4], "big")


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_default_generator(root: Path):
    package_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(package_name)
    except ModuleNotFoundError:
        path = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location(package_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import generator at {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = module
        spec.loader.exec_module(module)
        return module


def _canonical_pairs(root: Path) -> list[dict[str, Any]]:
    candidates = (
        root / "data" / "canonical" / "puzzles.jsonl",
        root / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError("canonical puzzles.jsonl not found")
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            train = list(row.get("train", []))
            test = row.get("test", [])
            if isinstance(test, dict):
                test = [test]
            pairs = [*train, *list(test)]
            if not pairs:
                raise ValueError(f"canonical row for {TASK_ID} has no pairs")
            return pairs
    raise KeyError(f"canonical row for {TASK_ID} not found in {path}")


def _add_error(errors: list[dict[str, Any]], category: str, **details: Any) -> None:
    errors.append({"category": category, **details})


def run_probe(*, gen, root: Path, seeds_per_band: int = 8) -> dict[str, Any]:
    """Return a JSON-safe report; do not raise for semantic failures."""
    if seeds_per_band < 1:
        raise ValueError("seeds_per_band must be >= 1")

    root = Path(root).resolve()
    errors: list[dict[str, Any]] = []
    pairs = _canonical_pairs(root)
    generator_path = root / "generators" / TASK_ID / "generator.py"

    canonical_checked = 0
    canonical_unique_inputs: set[str] = set()
    for index, pair in enumerate(pairs):
        grid = pair["input"]
        issues = list(gen.self_check(grid))
        if issues:
            _add_error(errors, "canonical_self_check", pair=index, issues=issues)
        try:
            actual = gen._solve_official(grid)
        except Exception as exc:  # diagnostic tool: retain all failures in report
            _add_error(
                errors,
                "canonical_oracle_exception",
                pair=index,
                exception=f"{type(exc).__name__}: {exc}",
            )
        else:
            if actual != pair["output"]:
                _add_error(errors, "canonical_oracle_mismatch", pair=index)
        canonical_checked += 1
        canonical_unique_inputs.add(_grid_hash(grid))

    declared_competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    declared_witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    declared_shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))

    shortcut_fit: dict[str, dict[str, Any]] = {}
    for name, shortcut in sorted(declared_shortcuts.items()):
        fits = 0
        shortcut_errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                if shortcut(pair["input"]) == pair["output"]:
                    fits += 1
            except Exception as exc:
                shortcut_errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        shortcut_fit[name] = {
            "pairs": len(pairs),
            "fits": fits,
            "errors": shortcut_errors,
        }
        if fits != len(pairs) or shortcut_errors:
            _add_error(
                errors,
                "declared_canonical_shortcut_does_not_fit_canonical",
                rival=name,
                fits=fits,
                pairs=len(pairs),
                exceptions=shortcut_errors,
            )

    lessons_checked = 0
    generated_pair_checks = 0
    generated_unique_inputs: set[str] = set()
    query_corner_counts: Counter[str] = Counter()
    start_residue_counts: Counter[str] = Counter()
    per_band_lessons: Counter[str] = Counter()
    refuted_lesson_counts: Counter[str] = Counter()
    witnessed_lesson_counts: Counter[str] = Counter()

    for band in BANDS:
        for seed_index in range(seeds_per_band):
            seed = _seed(f"curriculum-probe:v1:{TASK_ID}:{band}:{seed_index}")
            cache: dict[int, tuple[list[list[int]], list[list[int]]]] = {}

            def pair_for(sample_index: int):
                nonlocal generated_pair_checks
                if sample_index not in cache:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    output = gen._solve_official(grid)
                    cache[sample_index] = (grid, output)
                    generated_pair_checks += 1
                    generated_unique_inputs.add(_grid_hash(grid))
                return cache[sample_index]

            for start in range(4):
                demos = []
                for offset in range(4):
                    grid, output = pair_for(start + offset)
                    issues = list(gen.self_check(grid, difficulty=band))
                    if issues:
                        _add_error(
                            errors,
                            "generated_self_check",
                            band=band,
                            seed_index=seed_index,
                            start=start,
                            sample_index=start + offset,
                            issues=issues,
                        )
                    demos.append({"input": grid, "output": output})

                demo_corners = {
                    gen.observe_overrides(pair["input"])["corner_position"]
                    for pair in demos
                }
                if demo_corners != set(CORNERS):
                    _add_error(
                        errors,
                        "cyclic_demo_corner_coverage",
                        band=band,
                        seed_index=seed_index,
                        start=start,
                        observed=sorted(demo_corners),
                    )

                competitor_refuted = {}
                for name, rival in sorted(declared_competitors.items()):
                    try:
                        refuted = any(
                            rival(pair["input"]) != pair["output"] for pair in demos
                        )
                    except Exception as exc:
                        refuted = False
                        _add_error(
                            errors,
                            "competitor_exception",
                            band=band,
                            seed_index=seed_index,
                            start=start,
                            rival=name,
                            exception=f"{type(exc).__name__}: {exc}",
                        )
                    competitor_refuted[name] = refuted

                witness_present = {}
                for name, predicate in sorted(declared_witnesses.items()):
                    try:
                        present = any(predicate(pair["input"]) for pair in demos)
                    except Exception as exc:
                        present = False
                        _add_error(
                            errors,
                            "witness_exception",
                            band=band,
                            seed_index=seed_index,
                            start=start,
                            witness=name,
                            exception=f"{type(exc).__name__}: {exc}",
                        )
                    witness_present[name] = present

                for query_offset in range(4):
                    query_index = start + 4 + query_offset
                    query_grid, query_output = pair_for(query_index)
                    query = {"input": query_grid, "output": query_output}
                    query_corner = gen.observe_overrides(query_grid)["corner_position"]
                    query_corner_counts[query_corner] += 1
                    start_residue_counts[str(start)] += 1
                    per_band_lessons[band] += 1
                    lessons_checked += 1

                    reasons = list(gen.lesson_identifiable(demos, query))
                    if reasons:
                        _add_error(
                            errors,
                            "lesson_not_identifiable",
                            band=band,
                            seed_index=seed_index,
                            start=start,
                            query_offset=query_offset,
                            reasons=reasons,
                        )
                    for name, refuted in competitor_refuted.items():
                        if refuted:
                            refuted_lesson_counts[name] += 1
                        else:
                            _add_error(
                                errors,
                                "competitor_survives_demos",
                                band=band,
                                seed_index=seed_index,
                                start=start,
                                query_offset=query_offset,
                                rival=name,
                            )
                    for name, present in witness_present.items():
                        if present:
                            witnessed_lesson_counts[name] += 1
                        else:
                            _add_error(
                                errors,
                                "declared_witness_missing_from_demos",
                                band=band,
                                seed_index=seed_index,
                                start=start,
                                query_offset=query_offset,
                                witness=name,
                            )

    override_cases = 0
    override_profiles = (
        {"grid_h": 8, "grid_w": 20, "distractor_color": 3, "blob_size": 3},
        {"grid_h": 20, "grid_w": 8, "distractor_color": 7, "blob_size": 8},
    )
    for band in BANDS:
        for profile_index, profile in enumerate(override_profiles):
            for corner in CORNERS:
                expected = {**profile, "corner_position": corner}
                seed = _seed(
                    f"curriculum-probe:v1:override:{TASK_ID}:{band}:"
                    f"{profile_index}:{corner}"
                )
                try:
                    grid = gen.generate(seed, 97, difficulty=band, **expected)
                    observed = gen.observe_overrides(grid)
                except Exception as exc:
                    _add_error(
                        errors,
                        "override_exception",
                        band=band,
                        expected=expected,
                        exception=f"{type(exc).__name__}: {exc}",
                    )
                else:
                    if observed != expected:
                        _add_error(
                            errors,
                            "override_not_exact",
                            band=band,
                            expected=expected,
                            observed=observed,
                        )
                    issues = list(gen.self_check(grid, difficulty=band))
                    if issues:
                        _add_error(
                            errors,
                            "override_self_check",
                            band=band,
                            expected=expected,
                            issues=issues,
                        )
                override_cases += 1

    expected_lessons = len(BANDS) * seeds_per_band * 4 * 4
    for name in declared_competitors:
        refuted_lesson_counts.setdefault(name, 0)
    for name in declared_witnesses:
        witnessed_lesson_counts.setdefault(name, 0)

    return {
        "schema": "c5c5f3f84f12-curriculum-probe-v1",
        "status": "pass" if not errors else "fail",
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "scope": {
            "oracle": "task-local independent Python mirror",
            "bands": list(BANDS),
            "seeds_per_band": seeds_per_band,
            "lesson_policy": (
                "four consecutive demos at every start residue 0..3; four "
                "subsequent query offsets rotate every corner into query position"
            ),
            "rivals": "loaded dynamically from generator declarations",
        },
        "canonical": {
            "pairs_checked": canonical_checked,
            "unique_inputs": len(canonical_unique_inputs),
            "shortcut_fit": shortcut_fit,
        },
        "cyclic_lessons": {
            "lessons_checked": lessons_checked,
            "expected_lessons": expected_lessons,
            "generated_pair_checks": generated_pair_checks,
            "unique_generated_inputs": len(generated_unique_inputs),
            "per_band_lessons": dict(sorted(per_band_lessons.items())),
            "start_residue_counts": dict(sorted(start_residue_counts.items())),
            "query_corner_counts": dict(sorted(query_corner_counts.items())),
        },
        "rivals": {
            "lesson_competitors": sorted(declared_competitors),
            "semantic_witnesses": sorted(declared_witnesses),
            "canonical_shortcuts": sorted(declared_shortcuts),
            "refuted_lesson_counts": dict(sorted(refuted_lesson_counts.items())),
            "witnessed_lesson_counts": dict(sorted(witnessed_lesson_counts.items())),
        },
        "overrides": {
            "cases_checked": override_cases,
            "bands": list(BANDS),
            "profiles_per_corner": list(override_profiles),
        },
        "errors": errors,
        "limits": [
            "This is a deterministic declared-rival probe, not a proof against unknown hypotheses.",
            "Racket parity is intentionally delegated to the focused regression and shared battery.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-band", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = _repo_root_from_script()
    gen = _load_default_generator(root)
    report = run_probe(gen=gen, root=root, seeds_per_band=args.seeds_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "lessons_checked": report["cyclic_lessons"]["lessons_checked"],
                "errors": len(report["errors"]),
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
