"""Independent distribution and lesson-contract probe for cfd0943c5b14.

The probe labels generated inputs with the small explicit Python X-stamp oracle
in ``reference_probe.py``.  It is supplementary evidence: the repository's
rule-smoke and semantic gates remain the Racket-authority checks.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from reference_probe import (
    canonical_pairs,
    canonical_shortcut_fits,
    load_generator,
    observed,
    x_output,
)

BANDS = ("easy", "medium", "hard")


def _accepted(result):
    return result is True or result == []


def _digest(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_probe(module, *, draws_per_band=100, schedule_starts=100, seed=20261005):
    if type(draws_per_band) is not int or draws_per_band < 1:
        raise ValueError("draws_per_band must be a positive integer")
    if type(schedule_starts) is not int or schedule_starts < 1:
        raise ValueError("schedule_starts must be a positive integer")

    errors = []
    pairs = canonical_pairs()
    canonical_matches = 0
    for index, pair in enumerate(pairs):
        if x_output(pair["input"]) == pair["output"]:
            canonical_matches += 1
        else:
            errors.append(f"canonical pair {index}: independent oracle mismatch")
        if module.self_check(deepcopy(pair["input"])):
            errors.append(f"canonical pair {index}: self_check rejection")
        if not _accepted(module.strict_canonical_like(deepcopy(pair["input"]))):
            errors.append(f"canonical pair {index}: strict hook rejection")

    shortcut_fit = canonical_shortcut_fits()
    for name, fits in shortcut_fit.items():
        if not fits:
            errors.append(f"canonical shortcut {name} does not actually fit canonical labels")

    witness_hits = Counter()
    rival_disagreements = Counter()
    scene_counts = Counter()
    strict_hits = Counter()
    distinct_inputs = set()
    by_band = {}
    total_draws = 0

    for band_index, band in enumerate(BANDS):
        local_scenes = Counter()
        local_rivals = Counter()
        local_witnesses = Counter()
        local_strict = 0
        for index in range(draws_per_band):
            local_seed = seed + band_index * 100_000 + index * 37
            sample_index = index
            try:
                grid = module.generate(local_seed, sample_index, difficulty=band)
            except Exception as exc:
                errors.append(f"{band} draw {index}: generation raised {type(exc).__name__}: {exc}")
                continue
            total_draws += 1
            if grid != module.generate(local_seed, sample_index, difficulty=band):
                errors.append(f"{band} draw {index}: nondeterministic generation")
            findings = module.self_check(deepcopy(grid))
            if findings:
                errors.append(f"{band} draw {index}: self_check={findings}")
            independent = observed(grid)
            production = module.observe_overrides(deepcopy(grid))
            if production != independent:
                errors.append(
                    f"{band} draw {index}: observer mismatch {production!r} != {independent!r}"
                )
            expected_scene = module.schedule_profile(local_seed, sample_index, band)
            if independent["scene"] != expected_scene:
                errors.append(
                    f"{band} draw {index}: scene {independent['scene']!r} != schedule {expected_scene!r}"
                )
            intended = x_output(grid)
            if module.rule_mirror(deepcopy(grid)) != intended:
                errors.append(f"{band} draw {index}: Python mirror disagrees with independent oracle")
            if intended == grid:
                errors.append(f"{band} draw {index}: transformation is identity")

            local_scenes[independent["scene"]] += 1
            scene_counts[independent["scene"]] += 1
            distinct_inputs.add(_digest(grid))
            strict = _accepted(module.strict_canonical_like(deepcopy(grid)))
            local_strict += int(strict)
            strict_hits[band] += int(strict)
            for name, witness in module.SEMANTIC_WITNESSES.items():
                try:
                    fired = bool(witness(deepcopy(grid)))
                except Exception as exc:
                    errors.append(f"{band} draw {index}: witness {name} raised {exc!r}")
                    continue
                local_witnesses[name] += int(fired)
                witness_hits[name] += int(fired)
            for name, rival in module.LESSON_COMPETITORS.items():
                try:
                    differs = rival(deepcopy(grid)) != intended
                except Exception as exc:
                    errors.append(f"{band} draw {index}: rival {name} raised {exc!r}")
                    continue
                local_rivals[name] += int(differs)
                rival_disagreements[name] += int(differs)

        for scene in module.SCENES:
            if local_scenes[scene] == 0:
                errors.append(f"{band}: scheduled scene {scene} had zero support")
        for name in module.LESSON_COMPETITORS:
            if local_rivals[name] == 0:
                errors.append(f"{band}: competitor {name} had no counterexample")
        by_band[band] = {
            "draws": sum(local_scenes.values()),
            "scenes": dict(local_scenes),
            "strict": local_strict,
            "witness_hits": dict(local_witnesses),
            "rival_disagreements": dict(local_rivals),
        }

    rotations = 0
    ambiguous_rotations = 0
    lesson_errors = []
    period = len(module.SCENES)
    for band_index, band in enumerate(BANDS):
        for start in range(schedule_starts):
            lesson_seed = seed + 900_000 + band_index * 100_000 + start
            grids = [
                module.generate(lesson_seed, start + offset, difficulty=band)
                for offset in range(period)
            ]
            scenes = [observed(grid)["scene"] for grid in grids]
            expected = [module.SCENES[(start + offset) % period] for offset in range(period)]
            if scenes != expected:
                lesson_errors.append(
                    f"{band} start {start}: scene window {scenes!r} != {expected!r}"
                )
            labeled = [{"input": grid, "output": x_output(grid)} for grid in grids]
            for held_out in range(period):
                rotations += 1
                demos = [deepcopy(pair) for index, pair in enumerate(labeled) if index != held_out]
                query = deepcopy(labeled[held_out])
                reasons = module.lesson_identifiable(demos, query)
                surviving = [
                    name
                    for name, rival in module.LESSON_COMPETITORS.items()
                    if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                    and rival(deepcopy(query["input"])) != query["output"]
                ]
                if reasons or surviving:
                    ambiguous_rotations += 1
                    lesson_errors.append(
                        f"{band} start {start} held {held_out}: reasons={reasons!r}, surviving={surviving!r}"
                    )
    errors.extend(lesson_errors[:50])
    if len(lesson_errors) > 50:
        errors.append(f"...and {len(lesson_errors) - 50} additional lesson errors")

    return {
        "schema": "cfd0943c5b14-contract-probe-v1",
        "generator_version": module.VERSION,
        "canonical_oracle_matches": canonical_matches,
        "canonical_pairs": len(pairs),
        "canonical_shortcut_fit": shortcut_fit,
        "draws": total_draws,
        "draws_per_band": draws_per_band,
        "schedule_starts_per_band": schedule_starts,
        "distinct_inputs": len(distinct_inputs),
        "scene_counts": dict(scene_counts),
        "strict_hits": dict(strict_hits),
        "witness_hits": dict(witness_hits),
        "rival_disagreements": dict(rival_disagreements),
        "by_band": by_band,
        "cyclic_rotations_checked": rotations,
        "ambiguous_rotations": ambiguous_rotations,
        "errors": errors,
        "passed": not errors,
        "authority_note": (
            "The explicit Python oracle is independent test tooling; canonical Racket "
            "rule-smoke/semantic evidence remains authoritative."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--draws-per-band", type=int, default=100)
    parser.add_argument("--schedule-starts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = run_probe(
        module,
        draws_per_band=args.draws_per_band,
        schedule_starts=args.schedule_starts,
        seed=args.seed,
    )
    report["generator_sha256"] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "draws": report["draws"],
                "distinct_inputs": report["distinct_inputs"],
                "cyclic_rotations_checked": report["cyclic_rotations_checked"],
                "ambiguous_rotations": report["ambiguous_rotations"],
                "errors": len(report["errors"]),
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
