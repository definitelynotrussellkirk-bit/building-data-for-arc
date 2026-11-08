#!/usr/bin/env python3
"""Cheap source-bound support probe for canonical-fitting shortcut rivals.

The sampler and contract may be different source files.  This lets a reviewer
run a newly articulated rival against an immutable baseline sampler, then rerun
it against the repair.  The probe checks three things:

1. the rival really fits every canonical pair;
2. ordinary generated examples refute it in every difficulty band; and
3. no consecutive training window leaves the rival consistent with all demos.

It is intentionally label-cheap: ``rule_mirror`` supplies provisional labels.
A passing repair still needs the shared Racket-backed semantic gate/census.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from reviewer_support import canonical_pairs

BANDS = ("easy", "medium", "hard")


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_seeds(text: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(item.strip()) for item in text.split(",") if item.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seeds must be comma-separated integers") from exc
    if not seeds:
        raise argparse.ArgumentTypeError("at least one seed is required")
    return seeds


def _rivals(contract: ModuleType) -> dict[str, object]:
    raw = getattr(contract, "CANONICAL_SHORTCUTS", None)
    if not isinstance(raw, dict) or not raw:
        raise RuntimeError("contract source must declare nonempty CANONICAL_SHORTCUTS")
    invalid = sorted(name for name, fn in raw.items() if not isinstance(name, str) or not callable(fn))
    if invalid:
        raise RuntimeError(f"invalid canonical shortcut declaration(s): {invalid}")
    return dict(raw)


def run_probe(
    *,
    root: Path,
    task_id: str,
    sampler_path: Path,
    contract_path: Path,
    samples_per_band: int,
    window_starts: int,
    seeds: tuple[int, ...],
) -> dict:
    sampler = _load(sampler_path, "support_sampler")
    contract = _load(contract_path, "support_contract")
    if not callable(getattr(sampler, "generate", None)):
        raise RuntimeError("sampler source has no generate()")
    if not callable(getattr(sampler, "rule_mirror", None)):
        raise RuntimeError("sampler source has no rule_mirror()")
    rivals = _rivals(contract)
    canonical = list(canonical_pairs(task_id, root=root, labeled_only=True))
    if not canonical:
        raise RuntimeError(f"no labeled canonical pairs for {task_id}")

    demos_needed = int(getattr(contract, "EXAMPLES_NEEDED", 3))
    if demos_needed < 1:
        raise RuntimeError("EXAMPLES_NEEDED must be positive")

    report = {
        "schema": "rival-support-probe-v1",
        "task_id": task_id,
        "sampler_path": str(sampler_path),
        "sampler_sha256": _sha256(sampler_path),
        "contract_path": str(contract_path),
        "contract_sha256": _sha256(contract_path),
        "canonical_pairs": len(canonical),
        "examples_needed": demos_needed,
        "samples_per_band": samples_per_band,
        "window_starts": window_starts,
        "seeds": list(seeds),
        "rivals": {},
        "warnings": [],
    }

    for name, rival in rivals.items():
        canonical_matches = sum(
            rival(pair["input"]) == pair["output"] for pair in canonical
        )
        rival_report = {
            "canonical_matches": canonical_matches,
            "canonical_total": len(canonical),
            "bands": {},
        }
        canonical_fitting = canonical_matches == len(canonical)
        for band in BANDS:
            refuted = 0
            draws = 0
            ambiguous_windows = []
            for seed in seeds:
                generated = []
                enough = max(samples_per_band, window_starts + demos_needed - 1)
                for sample_index in range(enough):
                    grid = sampler.generate(seed, sample_index, difficulty=band)
                    expected = sampler.rule_mirror(grid)
                    agrees = rival(grid) == expected
                    if sample_index < samples_per_band:
                        draws += 1
                        refuted += not agrees
                    generated.append(agrees)
                for start in range(window_starts):
                    if all(generated[start : start + demos_needed]):
                        ambiguous_windows.append({"seed": seed, "start": start})
            rival_report["bands"][band] = {
                "draws": draws,
                "refuted": refuted,
                "refutation_rate": refuted / draws if draws else None,
                "ambiguous_windows": ambiguous_windows,
                "ambiguous_window_count": len(ambiguous_windows),
            }
            if canonical_fitting and refuted == 0:
                report["warnings"].append(
                    f"{name}: canonical-fitting rival is never refuted in {band}"
                )
            if canonical_fitting and ambiguous_windows:
                report["warnings"].append(
                    f"{name}: {len(ambiguous_windows)} {band} training windows leave rival viable"
                )
        report["rivals"][name] = rival_report

    report["passed"] = not report["warnings"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="repository root")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--sampler", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=60)
    parser.add_argument("--window-starts", type=int, default=20)
    parser.add_argument("--seeds", type=_parse_seeds, default=(0, 1, 2))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.samples_per_band < 1 or args.window_starts < 1:
        parser.error("sample counts must be positive")
    try:
        report = run_probe(
            root=args.root.resolve(),
            task_id=args.task_id,
            sampler_path=args.sampler.resolve(),
            contract_path=args.contract.resolve(),
            samples_per_band=args.samples_per_band,
            window_starts=args.window_starts,
            seeds=args.seeds,
        )
    except Exception as exc:
        print(f"probe error: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
