#!/usr/bin/env python3
"""Source-bound episode identifiability probe for ARC task 20014c9d3729.

The repository semantic gate measures witness frequency per generated input.
This probe checks the stronger training-unit property: for every assembled
(two-demo, one-query) lesson window, each declared canonical-compatible rival
must either be refuted by a demonstration or agree with the intended rule on
the query.  It imports rival declarations from the selected generator rather
than copying a task-specific rival list into the tool.

Racket remains the output authority.  This probe intentionally uses the
selected generator's ``rule_mirror`` only after the normal rule-smoke stage has
established parity; the source hash in the report makes that dependency
explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


TASK_ID = "20014c9d3729"
DEFAULT_BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_lesson_probe", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_path(generator_path: Path) -> Path:
    for ancestor in generator_path.resolve().parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            candidate = ancestor / relative
            if candidate.is_file():
                return candidate
    raise FileNotFoundError("could not locate canonical puzzles.jsonl")


def _canonical_pairs(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            record_id = record.get("id", record.get("content_hash"))
            if record_id != TASK_ID:
                continue
            return [*record.get("train", []), *record.get("test", [])]
    raise KeyError(f"task {TASK_ID} not found in {path}")


def _declared_rivals(module) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}
    for declaration in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        value = getattr(module, declaration, {})
        if not isinstance(value, dict):
            raise TypeError(f"{declaration} must be a mapping")
        for name, function in value.items():
            if name in rivals and rivals[name] is not function:
                raise ValueError(f"rival {name!r} has conflicting declarations")
            if not callable(function):
                raise TypeError(f"rival {name!r} is not callable")
            rivals[name] = function
    if not rivals:
        raise ValueError("generator declares no canonical shortcuts or lesson competitors")
    return rivals


def run_probe(
    *,
    generator_path: Path,
    seed: int,
    starts: int,
    bands: tuple[str, ...] = DEFAULT_BANDS,
) -> dict[str, Any]:
    if starts < 1:
        raise ValueError("starts must be positive")
    module = _load_module(generator_path)
    if getattr(module, "TASK_ID", None) != TASK_ID:
        raise ValueError(f"selected module is not task {TASK_ID}")
    examples_needed = int(getattr(module, "EXAMPLES_NEEDED", 2))
    if examples_needed < 1:
        raise ValueError("EXAMPLES_NEEDED must be positive")
    if not callable(getattr(module, "rule_mirror", None)):
        raise ValueError("generator must expose rule_mirror for source-bound probing")

    rivals = _declared_rivals(module)
    canonical_file = _canonical_path(generator_path)
    canonical_pairs = _canonical_pairs(canonical_file)

    canonical_checks: dict[str, Any] = {}
    compatible: dict[str, Callable] = {}
    for name, rival in sorted(rivals.items()):
        mismatches = []
        for pair_index, pair in enumerate(canonical_pairs):
            try:
                actual = rival(pair["input"])
            except Exception as exc:  # report rival failures, do not hide them
                mismatches.append(
                    {"pair_index": pair_index, "exception": f"{type(exc).__name__}: {exc}"}
                )
                continue
            if actual != pair["output"]:
                mismatches.append({"pair_index": pair_index, "output_mismatch": True})
        fits = not mismatches
        canonical_checks[name] = {
            "fits_all_pairs": fits,
            "pairs_checked": len(canonical_pairs),
            "mismatches": mismatches,
        }
        if fits:
            compatible[name] = rival

    band_reports: dict[str, Any] = {}
    total_ambiguous = 0
    all_unique_inputs: set[str] = set()
    for band in bands:
        unique_inputs: set[str] = set()
        windows = []
        rival_totals = {
            name: {
                "demo_refuted_windows": 0,
                "query_disagreement_windows": 0,
                "ambiguous_windows": 0,
            }
            for name in compatible
        }
        for start in range(starts):
            indices = list(range(start, start + examples_needed + 1))
            grids = [module.generate(seed, index, difficulty=band) for index in indices]
            intended = [module.rule_mirror(grid) for grid in grids]
            keys = [_grid_key(grid) for grid in grids]
            unique_inputs.update(keys)
            all_unique_inputs.update(keys)
            window_findings = []
            for name, rival in compatible.items():
                rival_outputs = [rival(grid) for grid in grids]
                demo_refuted = any(
                    rival_outputs[index] != intended[index]
                    for index in range(examples_needed)
                )
                query_disagrees = rival_outputs[-1] != intended[-1]
                ambiguous = query_disagrees and not demo_refuted
                if demo_refuted:
                    rival_totals[name]["demo_refuted_windows"] += 1
                if query_disagrees:
                    rival_totals[name]["query_disagreement_windows"] += 1
                if ambiguous:
                    rival_totals[name]["ambiguous_windows"] += 1
                    total_ambiguous += 1
                    window_findings.append(
                        {
                            "rival": name,
                            "reason": "fits every demo but disagrees on query",
                        }
                    )
            if window_findings:
                windows.append(
                    {
                        "start": start,
                        "sample_indices": indices,
                        "input_hashes": keys,
                        "findings": window_findings,
                    }
                )
        band_reports[band] = {
            "lesson_windows": starts,
            "examples_per_window": examples_needed,
            "query_examples_per_window": 1,
            "generated_input_occurrences": starts * (examples_needed + 1),
            "unique_inputs": len(unique_inputs),
            "rivals": rival_totals,
            "ambiguous_windows": windows,
        }

    blockers = []
    noncompatible_declared = sorted(set(rivals) - set(compatible))
    if noncompatible_declared:
        blockers.append(
            "declared canonical shortcuts do not fit every canonical pair: "
            + ", ".join(noncompatible_declared)
        )
    if total_ambiguous:
        blockers.append(f"{total_ambiguous} rival/window ambiguities found")

    return {
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "seed": seed,
        "bands": list(bands),
        "lesson_assembly": {
            "policy": "cyclic consecutive sample indices",
            "demos": examples_needed,
            "query": 1,
            "starts_per_band": starts,
            "sample_index_window": "start .. start + EXAMPLES_NEEDED",
            "sampler": "generator.generate(seed, sample_index, difficulty=band)",
            "labeler": "generator.rule_mirror (requires separate final-source Racket parity evidence)",
        },
        "domain_limits": {
            "only_declared_rivals": True,
            "does_not_establish_universal_induction": True,
            "named_bands_only": list(bands),
        },
        "canonical_pairs_checked": len(canonical_pairs),
        "declared_rivals": sorted(rivals),
        "canonical_compatibility": canonical_checks,
        "band_reports": band_reports,
        "unique_inputs_across_bands": len(all_unique_inputs),
        "ambiguous_rival_windows": total_ambiguous,
        "blockers": blockers,
        "passed": not blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_generator = Path(__file__).resolve().parents[1] / "generator.py"
    parser.add_argument("--generator", type=Path, default=default_generator)
    parser.add_argument("--seed", type=int, default=20014)
    parser.add_argument("--starts", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = run_probe(
        generator_path=args.generator.resolve(), seed=args.seed, starts=args.starts
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{'PASS' if report['passed'] else 'FAIL'}: "
        f"{len(DEFAULT_BANDS) * args.starts} lesson windows, "
        f"{report['unique_inputs_across_bands']} unique inputs, "
        f"{report['ambiguous_rival_windows']} ambiguous rival/windows"
    )
    print(f"report: {args.out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
