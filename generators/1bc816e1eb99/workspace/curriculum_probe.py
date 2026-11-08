"""Source-bound 128+-lesson-per-band audit for 1bc816e1eb99.

The probe uses the generator's actual linked sampler and its declared rival
functions.  A lesson is four consecutive demonstrations followed by the next
query; all four cyclic schedule starts are therefore tested repeatedly.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import canonical_pairs, intended_output, load_generator, racket_outputs

HERE = Path(__file__).resolve().parent


def digest_grid(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def audit(module, lessons_per_band: int, racket_samples: int) -> dict:
    competitors = dict(module.LESSON_COMPETITORS)
    shortcuts = dict(module.CANONICAL_SHORTCUTS)
    canonical_fit = {
        name: sum(solver(pair["input"]) == pair["output"] for pair in canonical_pairs())
        for name, solver in shortcuts.items()
    }
    bands = ("easy", "medium", "hard")
    report = {
        "schema": "1bc816e1eb99-curriculum-probe-v1",
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_probe_sha256": hashlib.sha256((HERE / "reference_probe.py").read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "domain_limits": {
            "axes": module.AXES,
            "profiles": list(module.SCHEDULE_PROFILES),
            "examples_needed": module.EXAMPLES_NEEDED,
            "input_palette": [0, 4],
            "supported_component_topologies": ["filled rectangle", "rectangular frame", "3x3 one-edge-notch solid"],
        },
        "actual_sampler": (
            "For each band and lesson index L, seed=730000+10000*band_index+L; "
            "the four demos use sample_index L..L+3 and the query uses L+4. "
            "Outputs are computed by the independent workspace topology oracle; "
            "the first requested grids are also batch-checked against Racket."
        ),
        "canonical_pairs": len(canonical_pairs()),
        "canonical_shortcut_fit_counts": canonical_fit,
        "lessons_per_band": lessons_per_band,
        "bands": {},
        "racket": {"requested": racket_samples, "checked": 0, "mismatches": []},
    }
    racket_grids: list[list[list[int]]] = []
    failures: list[dict] = []

    for band_index, band in enumerate(bands):
        inputs: set[str] = set()
        profiles = Counter()
        rival_disagreements = Counter()
        rival_demo_survivals = Counter()
        rival_harmful_survivals = Counter()
        starts = Counter()
        identifiable = 0
        self_check_errors = 0
        nondeterministic = 0
        generated = 0
        for lesson_index in range(lessons_per_band):
            seed = 730000 + 10000 * band_index + lesson_index
            start = lesson_index
            starts[start % len(module.SCHEDULE_PROFILES)] += 1
            pairs = []
            for offset in range(module.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = module.generate(seed, sample_index, difficulty=band)
                generated += 1
                if grid != module.generate(seed, sample_index, difficulty=band):
                    nondeterministic += 1
                issues = module.self_check(grid, difficulty=band)
                self_check_errors += bool(issues)
                if issues and len(failures) < 12:
                    failures.append({"band": band, "lesson": lesson_index, "offset": offset, "errors": issues})
                truth = intended_output(grid)
                pairs.append({"input": grid, "output": truth})
                inputs.add(digest_grid(grid))
                profiles[module.schedule_profile(seed, sample_index, band)] += 1
                for name, solver in competitors.items():
                    rival_disagreements[name] += solver(grid) != truth
                if len(racket_grids) < racket_samples:
                    racket_grids.append(grid)
            demos, query = pairs[:-1], pairs[-1]
            reasons = module.lesson_identifiable(demos, query)
            if not reasons:
                identifiable += 1
            elif len(failures) < 12:
                failures.append({"band": band, "lesson": lesson_index, "identifiability": reasons})
            for name, solver in competitors.items():
                survives = all(solver(pair["input"]) == pair["output"] for pair in demos)
                rival_demo_survivals[name] += survives
                rival_harmful_survivals[name] += survives and solver(query["input"]) != query["output"]
        report["bands"][band] = {
            "lessons": lessons_per_band,
            "generated_inputs": generated,
            "unique_inputs": len(inputs),
            "cyclic_start_counts": dict(sorted(starts.items())),
            "profile_counts": dict(sorted(profiles.items())),
            "identifiable_lessons": identifiable,
            "self_check_errors": self_check_errors,
            "nondeterministic_replays": nondeterministic,
            "rival_input_disagreements": dict(sorted(rival_disagreements.items())),
            "rival_demo_survivals": dict(sorted(rival_demo_survivals.items())),
            "rival_harmful_survivals": dict(sorted(rival_harmful_survivals.items())),
        }

    if racket_samples:
        outputs = racket_outputs(racket_grids)
        mismatches = [
            index for index, (grid, output) in enumerate(zip(racket_grids, outputs, strict=True))
            if intended_output(grid) != output
        ]
        report["racket"] = {"requested": racket_samples, "checked": len(outputs), "mismatches": mismatches}
    report["failures"] = failures
    report["passed"] = (
        all(count == len(canonical_pairs()) for count in canonical_fit.values())
        and not failures
        and not report["racket"]["mismatches"]
        and all(
            cell["identifiable_lessons"] == lessons_per_band
            and cell["self_check_errors"] == 0
            and cell["nondeterministic_replays"] == 0
            and all(value == 0 for value in cell["rival_harmful_survivals"].values())
            for cell in report["bands"].values()
        )
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=128)
    parser.add_argument("--racket-samples", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 100:
        parser.error("--lessons-per-band must be at least 100 for this review")
    if not 0 <= args.racket_samples <= 64:
        parser.error("--racket-samples must be in 0..64")
    module = load_generator(args.generator)
    report = audit(module, args.lessons_per_band, args.racket_samples)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "bands": report["bands"], "racket": report["racket"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
