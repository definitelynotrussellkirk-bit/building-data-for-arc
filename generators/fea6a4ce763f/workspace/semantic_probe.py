#!/usr/bin/env python3
"""Finite, source-bound semantic probe for fea6a4ce763f.

This is a fast authoring aid, not an authority check or proof of induction.  It
uses the generator's independent Python rule mirror to inspect public profiles,
semantic witnesses, mapped rivals, and every query rotation over one finite
schedule period.  Use the repository battery and lesson census for Racket-bound
evidence.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_generator(path: Path) -> ModuleType:
    spec = spec_from_file_location("fea6a4ce763f_probe_generator", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import generator from {path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pair(gen: ModuleType, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def build_report(gen: ModuleType, *, seeds_per_band: int = 30) -> dict[str, Any]:
    """Return a deterministic finite semantic census for an imported generator."""
    if seeds_per_band < 1:
        raise ValueError("seeds_per_band must be positive")

    profiles_seen: set[str] = set()
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    rival_counterexample_failures: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    for band_index, band in enumerate(BANDS):
        for index in range(seeds_per_band):
            seed = 210_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            observed = gen.observe_overrides(grid).get("scene_profile")
            if observed is not None:
                profiles_seen.add(observed)
            truth = gen.rule_mirror(grid)
            fired = [
                name
                for name, witness in gen.SEMANTIC_WITNESSES.items()
                if witness(grid)
            ]
            for name in fired:
                witness_hits[name] += 1
                for rival_name in gen.WITNESS_RIVALS.get(name, []):
                    rival = gen.SEMANTIC_RIVALS[rival_name]
                    if rival(grid) == truth:
                        rival_counterexample_failures.append(
                            {
                                "band": band,
                                "index": index,
                                "seed": seed,
                                "witness": name,
                                "rival": rival_name,
                                "input_sha256": _grid_hash(grid),
                            }
                        )
            if len(examples) < 12:
                examples.append(
                    {
                        "band": band,
                        "index": index,
                        "seed": seed,
                        "profile": observed,
                        "phase": gen.semantic_phase(seed, index, band),
                        "witnesses": fired,
                        "input_sha256": _grid_hash(grid),
                        "output_sha256": _grid_hash(truth),
                    }
                )

    rotation_failures: list[dict[str, Any]] = []
    period = int(gen.LESSON_SCHEDULE_PERIOD)
    for band_index, band in enumerate(BANDS):
        for start in range(period):
            seed = 310_000 + band_index * 10_000 + start
            pairs = [_pair(gen, seed, start + offset, band) for offset in range(5)]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    rotation_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "query_index": query_index,
                            "reasons": list(reasons),
                            "query_input_sha256": _grid_hash(query["input"]),
                        }
                    )

    return {
        "schema": "fea6a4ce763f-semantic-probe-v1",
        "generator_id": gen.GENERATOR_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "authority": "python-rule-mirror-only; run repository battery/census for Racket evidence",
        "bands": list(BANDS),
        "seeds_per_band": seeds_per_band,
        "schedule_period": period,
        "profiles_seen": sorted(profiles_seen),
        "witness_hits": witness_hits,
        "rival_counterexample_failures": rival_counterexample_failures,
        "rotation_failures": rotation_failures,
        "examples": examples,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).parents[1] / "generator.py")
    parser.add_argument("--seeds-per-band", type=int, default=30)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    generator_path = args.generator.resolve()
    gen = _load_generator(generator_path)
    report = build_report(gen, seeds_per_band=args.seeds_per_band)
    report["generator_path"] = str(generator_path)
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if report["rival_counterexample_failures"] or report["rotation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
