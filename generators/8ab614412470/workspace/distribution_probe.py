#!/usr/bin/env python3
"""Source-bound distribution and teaching probe for generator 8ab614412470.

This is intentionally task-local.  It gives later reviewers one cheap command
that checks deterministic generation, validator acceptance, schedule coverage,
semantic witnesses/rivals, and every query rotation of all cyclic four-example
lesson starts.  It never consults private ARC answers; labels come from the
selected generator's ``rule_mirror``.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

BANDS = (None, "easy", "medium", "hard")


def _band_name(band: str | None) -> str:
    return "unbanded" if band is None else band


def _grid_digest(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _profile_key(observed: dict[str, Any]) -> str:
    return (
        f"{observed['grid_h']}x{observed['grid_w']}"
        f"/repeat={observed['n_repeated_colors']}"
        f"/singleton={observed['n_singleton_colors']}"
        f"/pattern={observed['repeat_pattern']}"
    )


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=str)}


def build_report(gen, *, per_band: int = 32, seed_base: int = 80000) -> dict[str, Any]:
    """Probe a loaded generator module and return a JSON-serializable report."""
    if type(per_band) is not int or per_band < 4:
        raise ValueError("per_band must be an integer >= 4")
    if type(seed_base) is not int:
        raise TypeError("seed_base must be an integer")

    failures: list[str] = []
    bands: dict[str, Any] = {}
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    rivals = dict(getattr(gen, "SEMANTIC_RIVALS", {}))
    witness_rivals = dict(getattr(gen, "WITNESS_RIVALS", {}))

    for band_index, band in enumerate(BANDS):
        profiles: Counter = Counter()
        schedules: Counter = Counter()
        witness_firings: Counter = Counter({name: 0 for name in witnesses})
        witness_disagreements: Counter = Counter({name: 0 for name in witnesses})
        digests: set[str] = set()
        validator_failures = 0
        determinism_failures = 0
        observation_failures = 0

        for sample_index in range(per_band):
            seed = seed_base + band_index * 10000 + sample_index
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
                replay = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:  # pragma: no cover - diagnostic path
                failures.append(
                    f"{_band_name(band)} sample {sample_index}: generation error {exc!r}"
                )
                continue

            if grid != replay:
                determinism_failures += 1
                failures.append(
                    f"{_band_name(band)} sample {sample_index}: nondeterministic replay"
                )

            digest = _grid_digest(grid)
            digests.add(digest)
            validator_errors = list(gen.self_check(grid))
            if validator_errors:
                validator_failures += 1
                failures.append(
                    f"{_band_name(band)} sample {sample_index}: validator "
                    + "; ".join(map(str, validator_errors))
                )
                continue

            try:
                observed = gen.observe_overrides(grid)
                profiles[_profile_key(observed)] += 1
            except Exception as exc:
                observation_failures += 1
                failures.append(
                    f"{_band_name(band)} sample {sample_index}: observation error {exc!r}"
                )

            schedule = gen.schedule_profile(seed, sample_index, difficulty=band)
            schedules[str(schedule)] += 1
            expected = gen.rule_mirror(grid)

            for witness_name, witness in witnesses.items():
                try:
                    fires = bool(witness(grid))
                except Exception as exc:  # pragma: no cover - diagnostic path
                    failures.append(
                        f"{_band_name(band)} sample {sample_index}: witness "
                        f"{witness_name} error {exc!r}"
                    )
                    continue
                if not fires:
                    failures.append(
                        f"{_band_name(band)} sample {sample_index}: witness "
                        f"{witness_name} did not fire"
                    )
                    continue
                witness_firings[witness_name] += 1

                names = witness_rivals.get(witness_name, ())
                if isinstance(names, str):
                    names = (names,)
                declared = [name for name in names if name in rivals]
                if declared and all(rivals[name](grid) != expected for name in declared):
                    witness_disagreements[witness_name] += 1
                else:
                    failures.append(
                        f"{_band_name(band)} sample {sample_index}: witness "
                        f"{witness_name} lacks full declared-rival disagreement"
                    )

        bands[_band_name(band)] = {
            "samples": per_band,
            "unique_inputs": len(digests),
            "profiles": _counter_dict(profiles),
            "schedule_profiles": _counter_dict(schedules),
            "determinism_failures": determinism_failures,
            "validator_failures": validator_failures,
            "observation_failures": observation_failures,
            "witness_firings": _counter_dict(witness_firings),
            "witness_rival_disagreements": _counter_dict(witness_disagreements),
        }

    # Four cyclic starts in each band exercise every residue of the four-slot
    # curriculum.  Hold out every pair once, not just the production-last query.
    lessons = 0
    rotations = 0
    ambiguous_rotations = 0
    rotation_findings: list[dict[str, Any]] = []
    for band_index, band in enumerate(BANDS):
        for start in range(4):
            pairs = []
            seed = seed_base + 50000 + band_index * 1000 + start
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            lessons += 1
            for query_index in range(4):
                rotations += 1
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                reasons = list(gen.lesson_identifiable(demos, query))
                if reasons:
                    ambiguous_rotations += 1
                    rotation_findings.append(
                        {
                            "band": _band_name(band),
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )
                    failures.append(
                        f"rotation ambiguity: band={_band_name(band)} "
                        f"start={start} query={query_index}: {'; '.join(reasons)}"
                    )

    report = {
        "schema": "8ab614412470-distribution-probe-v1",
        "generator_id": str(getattr(gen, "GENERATOR_ID", "unknown")),
        "generator_version": str(getattr(gen, "VERSION", "unknown")),
        "rule_hash": str(getattr(gen, "RULE_HASH", "unknown")),
        "per_band": per_band,
        "seed_base": seed_base,
        "samples_total": per_band * len(BANDS),
        "bands": bands,
        "rotation_check": {
            "demonstrations_per_lesson": 3,
            "lessons": lessons,
            "rotations": rotations,
            "ambiguous_rotations": ambiguous_rotations,
            "findings": rotation_findings,
        },
        "failures": failures,
    }
    report["status"] = "pass" if not failures else "fail"
    return report


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("distribution_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--per-band", type=int, default=32)
    parser.add_argument("--seed-base", type=int, default=80000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    # Direct execution from the source tree needs the shared runtime on sys.path.
    repo_root = Path(__file__).resolve().parents[3]
    runtime = repo_root / "shared" / "runtime"
    if runtime.is_dir() and str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))

    gen = _load_generator(args.generator.resolve())
    report = build_report(gen, per_band=args.per_band, seed_base=args.seed_base)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
