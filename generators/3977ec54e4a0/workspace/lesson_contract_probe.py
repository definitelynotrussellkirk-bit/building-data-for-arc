#!/usr/bin/env python3
"""Hash-bound cyclic lesson probe for generator 3977ec54e4a0.

The shared lesson census samples complete lessons, but a small periodic schedule
also permits exhaustive cyclic-start checking.  This probe imports the selected
generator's *actual* ``LESSON_COMPETITORS`` declaration, materializes 12 cyclic
starts per difficulty, and reports every rival that survives all three visible
demonstrations.  It also verifies the declared schedule and canonical slot.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "3977ec54e4a0"
BANDS = ("easy", "medium", "hard")
STARTS = range(12)


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "generators" / TASK_ID / "generator.py").is_file():
            return parent
    raise RuntimeError("could not locate repository root")


def _load_generator(repo_root: Path):
    runtime = repo_root / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    source = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"lesson_probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def _grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    repo_root = _find_repo_root()
    generator, source = _load_generator(repo_root)
    rivals = dict(generator.LESSON_COMPETITORS)
    expected_profiles = set(generator.SCHEDULE_PROFILES)

    failures = []
    bands = {}
    all_unique = set()
    for band in BANDS:
        band_unique = set()
        band_failures = []
        witness_hits = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        canonical_examples = 0
        for start in STARTS:
            seed = int(
                hashlib.sha256(
                    f"lesson-census:v1:{TASK_ID}:{band}:{start}".encode()
                ).hexdigest()[:8],
                16,
            )
            demos = []
            profiles = []
            for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                grid = generator.generate(seed, sample_index, difficulty=band)
                output = generator.rule_mirror(grid)
                demos.append((grid, output))
                profiles.append(
                    generator.schedule_profile(seed, sample_index, band)
                )
                digest = _grid_hash(grid)
                band_unique.add(digest)
                all_unique.add(digest)
                canonical_examples += not generator.strict_canonical_like(grid)
                for name, witness in generator.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += bool(witness(grid))

            if set(profiles) != expected_profiles:
                band_failures.append(
                    {
                        "start": start,
                        "kind": "schedule_profiles",
                        "profiles": profiles,
                    }
                )
            for rival_name, solve in rivals.items():
                if all(solve(grid) == output for grid, output in demos):
                    band_failures.append(
                        {
                            "start": start,
                            "kind": "surviving_rival",
                            "rival": rival_name,
                            "profiles": profiles,
                        }
                    )

        failures.extend({"band": band, **item} for item in band_failures)
        bands[band] = {
            "cyclic_starts": len(STARTS),
            "materialized_examples": len(STARTS) * generator.EXAMPLES_NEEDED,
            "unique_input_hashes": len(band_unique),
            "canonical_examples": canonical_examples,
            "witness_hits": witness_hits,
            "failures": band_failures,
        }

    passed = not failures and bool(rivals)
    report = {
        "schema": "arc.lesson-contract-probe.v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "lesson_policy": {
            "examples_needed": generator.EXAMPLES_NEEDED,
            "schedule_profiles": list(generator.SCHEDULE_PROFILES),
            "cyclic_starts_per_band": len(STARTS),
            "seed_recipe": "sha256('lesson-census:v1:TASK:band:start')[:8]",
        },
        "declared_rivals": sorted(rivals),
        "bands": bands,
        "unique_input_hashes_all_bands": len(all_unique),
        "failures": failures,
        "domain_limit": (
            "Finite checks cover only the generator's declared executable rivals; "
            "they do not establish universal identifiability."
        ),
        "status": "PASS" if passed else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
