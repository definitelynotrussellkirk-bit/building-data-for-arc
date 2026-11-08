#!/usr/bin/env python3
"""Source-bound census of actual three-demo teaching windows for 8dd7ace7de9a.

The probe deliberately scores the generator's *declared* CANONICAL_SHORTCUTS
and LESSON_COMPETITORS rather than copying a rival-name list.  It mirrors the
semantic gate's pinned per-band sampler (SHA-256 seeds, sample-index stride 11),
uses the independent reference_probe rule implementation for labels, and emits
one deterministic JSON artifact suitable for reviewer/intake replay.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

TASK_ID = "8dd7ace7de9a"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11
WORKSPACE = Path(__file__).resolve().parent
DEFAULT_GENERATOR = WORKSPACE.parent / "generator.py"


def _load_module(path: Path, name_prefix: str) -> ModuleType:
    path = path.resolve()
    name = f"{name_prefix}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reference_probe() -> ModuleType:
    return _load_module(WORKSPACE / "reference_probe.py", "reference_probe")


def _pinned_seed(task_id: str, band: str, index: int) -> int:
    """Exact seed construction used by the inherited semantic lesson gate."""
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _domain_summary(rows: list[dict[str, int | bool]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in sorted(rows[0]) if rows else ():
        values = [row[name] for row in rows]
        if all(type(value) is bool for value in values):
            result[name] = {"values": sorted(set(values))}
        else:
            result[name] = {"min": min(values), "max": max(values)}
    return result


def _safe_call(fn: Callable, grid: list[list[int]]) -> tuple[Any | None, str | None]:
    try:
        return fn(deepcopy(grid)), None
    except Exception as exc:  # explicit evidence, never silently swallowed
        return None, f"{type(exc).__name__}: {exc}"


def run_probe(
    *,
    generator_path: str | Path = DEFAULT_GENERATOR,
    lessons_per_band: int = 100,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the deterministic lesson census and optionally write its JSON report."""
    if isinstance(lessons_per_band, bool) or not isinstance(lessons_per_band, int):
        raise TypeError("lessons_per_band must be an integer")
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    generator_path = Path(generator_path).resolve()
    gen = _load_module(generator_path, "generator_under_probe")
    ref = _reference_probe()

    n_demos = getattr(gen, "EXAMPLES_NEEDED", None)
    if isinstance(n_demos, bool) or not isinstance(n_demos, int) or n_demos < 2:
        raise ValueError(f"EXAMPLES_NEEDED must be an integer >=2, got {n_demos!r}")

    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    lesson_competitors = getattr(gen, "LESSON_COMPETITORS", None)
    if not isinstance(shortcuts, dict) or not shortcuts:
        raise ValueError("generator must declare nonempty CANONICAL_SHORTCUTS")
    if not isinstance(lesson_competitors, dict) or not lesson_competitors:
        raise ValueError("generator must declare nonempty LESSON_COMPETITORS")
    if any(not callable(fn) for fn in shortcuts.values()):
        raise TypeError("every CANONICAL_SHORTCUTS value must be callable")
    if any(not callable(fn) for fn in lesson_competitors.values()):
        raise TypeError("every LESSON_COMPETITORS value must be callable")

    # Score the union, auto-including a canonical shortcut if an author forgot
    # to repeat it in LESSON_COMPETITORS. This matches the inherited gate's
    # current policy while retaining both original declaration lists.
    competitors: dict[str, Callable] = dict(lesson_competitors)
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)

    canonical = ref.canonical_pairs()
    canonical_fit: dict[str, dict[str, int]] = {}
    failures: list[dict[str, Any]] = []
    for name, shortcut in sorted(shortcuts.items()):
        fit = 0
        for pair_index, pair in enumerate(canonical):
            value, error = _safe_call(shortcut, pair["input"])
            if error is None and value == pair["output"]:
                fit += 1
            else:
                failures.append({
                    "kind": "canonical_shortcut_mismatch",
                    "shortcut": name,
                    "pair_index": pair_index,
                    "error": error,
                })
        canonical_fit[name] = {"fit": fit, "total": len(canonical)}

    per_band: dict[str, Any] = {}
    all_input_hashes: set[str] = set()
    total_hook_errors = 0
    total_competitor_errors = 0
    total_identifiable = 0
    total_unidentifiable = 0

    for band in BANDS:
        input_hashes: set[str] = set()
        observations: list[dict[str, int | bool]] = []
        start_residues: Counter[int] = Counter()
        competitor_rows = {
            name: {
                "lessons_refuted_by_demos": 0,
                "lessons_surviving_demos": 0,
                "lessons_surviving_all": 0,
                "errors": 0,
            }
            for name in sorted(competitors)
        }
        witness_rows = {
            name: {"lessons_firing_in_demos": 0, "demo_inputs_firing": 0}
            for name in sorted(getattr(gen, "SEMANTIC_WITNESSES", {}))
        }
        band_identifiable = 0
        band_unidentifiable = 0
        band_hook_errors = 0

        for lesson_index in range(lessons_per_band):
            seed = _pinned_seed(TASK_ID, f"lesson:{band}", lesson_index)
            start = lesson_index * LESSON_SAMPLE_STRIDE
            start_residues[start % len(getattr(gen, "SCHEDULE_PROFILES", (0, 1, 2)))] += 1
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(n_demos + 1)
            ]
            outputs: list[list[list[int]]] = []
            for offset, grid in enumerate(grids):
                errors = gen.self_check(deepcopy(grid))
                if errors:
                    failures.append({
                        "kind": "self_check",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start + offset,
                        "errors": list(errors),
                    })
                answer = ref.rule_output(deepcopy(grid))
                mirror, mirror_error = _safe_call(gen.rule_mirror, grid)
                if mirror_error is not None or mirror != answer:
                    failures.append({
                        "kind": "mirror_disagreement",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start + offset,
                        "error": mirror_error,
                    })
                outputs.append(answer)
                digest = ref.grid_hash(grid)
                input_hashes.add(digest)
                all_input_hashes.add(digest)
                try:
                    observations.append(ref.observed(deepcopy(grid)))
                except Exception as exc:
                    failures.append({
                        "kind": "observer_error",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start + offset,
                        "error": f"{type(exc).__name__}: {exc}",
                    })

            demos = [
                {"input": deepcopy(grid), "output": deepcopy(output)}
                for grid, output in zip(grids[:n_demos], outputs[:n_demos], strict=True)
            ]
            query = {"input": deepcopy(grids[-1]), "output": deepcopy(outputs[-1])}

            try:
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if not isinstance(reasons, list) or any(
                    not isinstance(reason, str) for reason in reasons
                ):
                    raise TypeError("lesson_identifiable must return list[str]")
            except Exception as exc:
                reasons = []
                band_hook_errors += 1
                total_hook_errors += 1
                failures.append({
                    "kind": "lesson_hook_error",
                    "band": band,
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "sample_index": start,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            else:
                if reasons:
                    band_unidentifiable += 1
                    total_unidentifiable += 1
                    failures.append({
                        "kind": "unidentifiable_lesson",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "reasons": reasons,
                    })
                else:
                    band_identifiable += 1
                    total_identifiable += 1

            for name, rival in sorted(competitors.items()):
                row = competitor_rows[name]
                demo_values: list[bool] = []
                rival_failed = False
                for demo in demos:
                    value, error = _safe_call(rival, demo["input"])
                    if error is not None:
                        row["errors"] += 1
                        total_competitor_errors += 1
                        rival_failed = True
                        failures.append({
                            "kind": "competitor_error",
                            "competitor": name,
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "error": error,
                        })
                        break
                    demo_values.append(value == demo["output"])
                if rival_failed:
                    continue
                survives_demos = all(demo_values)
                if survives_demos:
                    row["lessons_surviving_demos"] += 1
                    q_value, q_error = _safe_call(rival, query["input"])
                    if q_error is not None:
                        row["errors"] += 1
                        total_competitor_errors += 1
                        failures.append({
                            "kind": "competitor_query_error",
                            "competitor": name,
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start + n_demos,
                            "error": q_error,
                        })
                    elif q_value == query["output"]:
                        row["lessons_surviving_all"] += 1
                    failures.append({
                        "kind": "competitor_survived_demos",
                        "competitor": name,
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                    })
                else:
                    row["lessons_refuted_by_demos"] += 1

            for name, witness in sorted(getattr(gen, "SEMANTIC_WITNESSES", {}).items()):
                fired = 0
                for demo in demos:
                    value, error = _safe_call(witness, demo["input"])
                    if error is not None:
                        failures.append({
                            "kind": "witness_error",
                            "witness": name,
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "error": error,
                        })
                    elif bool(value):
                        fired += 1
                witness_rows[name]["demo_inputs_firing"] += fired
                if fired:
                    witness_rows[name]["lessons_firing_in_demos"] += 1
                else:
                    failures.append({
                        "kind": "witness_missing_from_lesson",
                        "witness": name,
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                    })

        per_band[band] = {
            "lessons": lessons_per_band,
            "demonstrations": lessons_per_band * n_demos,
            "queries": lessons_per_band,
            "generated_inputs": lessons_per_band * (n_demos + 1),
            "unique_inputs": len(input_hashes),
            "identifiable": band_identifiable,
            "unidentifiable": band_unidentifiable,
            "hook_errors": band_hook_errors,
            "cyclic_start_modulus": len(getattr(gen, "SCHEDULE_PROFILES", (0, 1, 2))),
            "cyclic_start_residues": {
                str(key): start_residues[key]
                for key in range(len(getattr(gen, "SCHEDULE_PROFILES", (0, 1, 2))))
            },
            "domain_limits": _domain_summary(observations),
            "competitors": competitor_rows,
            "witnesses": witness_rows,
        }

    total_lessons = lessons_per_band * len(BANDS)
    totals = {
        "bands": len(BANDS),
        "lessons": total_lessons,
        "demonstrations": total_lessons * n_demos,
        "queries": total_lessons,
        "generated_inputs": total_lessons * (n_demos + 1),
        "identifiable": total_identifiable,
        "unidentifiable": total_unidentifiable,
        "hook_errors": total_hook_errors,
        "competitor_errors": total_competitor_errors,
    }
    report: dict[str, Any] = {
        "schema": "8dd7ace7de9a-lesson-probe-v1",
        "source": {
            "task_id": TASK_ID,
            "generator_path": "generators/8dd7ace7de9a/generator.py",
            "generator_sha256": _sha256(generator_path),
            "probe_sha256": _sha256(Path(__file__).resolve()),
            "rule_hash": getattr(gen, "RULE_HASH", None),
            "version": getattr(gen, "VERSION", None),
        },
        "sampler": {
            "policy": (
                "For each band and lesson index k, use the inherited semantic-gate "
                "seed profile-floor:v1:<task>:lesson:<band>:k, start at k*11, "
                "then generate EXAMPLES_NEEDED consecutive demos plus one query "
                "with the same seed and difficulty."
            ),
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "lesson_sample_stride": LESSON_SAMPLE_STRIDE,
            "n_demos": n_demos,
            "n_queries": 1,
            "labels": "independent workspace/reference_probe.py rule_output",
            "actual_generator_declarations": {
                "canonical_shortcuts": sorted(shortcuts),
                "lesson_competitors": sorted(lesson_competitors),
            },
            "declared_axes": getattr(gen, "AXES", None),
        },
        "canonical_shortcut_fit": {
            "pairs": len(canonical),
            "all_fit": all(row["fit"] == row["total"] for row in canonical_fit.values()),
            "per_shortcut": canonical_fit,
        },
        "totals": totals,
        "unique_inputs_across_bands": len(all_input_hashes),
        "per_band": per_band,
        "all_passed": not failures,
        "failures": failures,
    }

    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_probe(
        generator_path=args.generator,
        lessons_per_band=args.lessons_per_band,
        output_path=args.out,
    )
    print(json.dumps({
        "all_passed": report["all_passed"],
        "totals": report["totals"],
        "unique_inputs_across_bands": report["unique_inputs_across_bands"],
        "output": str(args.out),
    }, indent=2, sort_keys=True))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
