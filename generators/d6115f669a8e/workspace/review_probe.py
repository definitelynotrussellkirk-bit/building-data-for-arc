"""Source-bound lesson census for generator d6115f669a8e.

The probe imports the generator under test, iterates its actual
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations, and evaluates
all cyclic starts of the declared five-profile curriculum.  Python mirrors are
used only for high-volume rival scoring; a bounded sample is checked against the
canonical Racket authority in the same run.

Run from the packet root through ``run_with_racket.py``; see README.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
# ``wrap_rule`` imports the repository's shared tooling through its portable
# package name.  Expose that read-only package only inside this probe process.
if "scripts" not in sys.modules:
    scripts = ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared/tools")]
    sys.modules["scripts"] = scripts

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return _sha256_bytes(encoded)


def _load_module(path: Path):
    name = "d6115f669a8e_probe_" + _sha256_bytes(str(path.resolve()).encode())[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record(task_id: str) -> dict:
    matches = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id:
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical row for {task_id}, found {len(matches)}")
    return matches[0]


def _grid_literal(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class RacketOracle:
    def __init__(self, program_solution: str):
        self.bridge = RacketBridge(timeout=30)
        self.function_name = "__d6115f669a8e_probe_rule"
        self.bridge.eval_text(f"(define {self.function_name} {wrap_rule(program_solution)})")
        self.calls = 0

    def apply(self, grid):
        self.calls += 1
        return self.bridge.eval_text(f"({self.function_name} {_grid_literal(grid)})")

    def close(self):
        self.bridge.shutdown()


def run_census(generator, record: dict, *, generator_path: Path, lessons_per_start: int, racket_per_band: int) -> dict:
    cycle = int(generator.EXAMPLES_NEEDED)
    if cycle != len(generator.SCHEDULE_PROFILES):
        raise AssertionError("EXAMPLES_NEEDED must equal the schedule cycle length")
    bands = ("easy", "medium", "hard")
    canonical_pairs = record["train"] + record["test"]

    shortcut_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs)
        for name, rival in generator.CANONICAL_SHORTCUTS.items()
    }

    unique_inputs: set[str] = set()
    input_occurrences = 0
    invalid_inputs = []
    profile_counts = Counter()
    strict_counts = Counter()
    individual_disagreements = {
        name: Counter() for name in generator.LESSON_COMPETITORS
    }
    surviving_lessons = {
        name: Counter() for name in generator.LESSON_COMPETITORS
    }
    lessons_by_band = Counter()
    starts_by_band = {band: Counter() for band in bands}
    racket_candidates: list[dict] = []

    for band in bands:
        for start in range(cycle):
            for seed_root in range(lessons_per_start):
                # Consecutive windows preserve the actual sampler's seed and
                # sample-index semantics while covering every cyclic schedule start.
                base_index = seed_root * cycle + start
                demos = []
                for offset in range(cycle):
                    sample_index = base_index + offset
                    grid = generator.generate(seed_root, sample_index, difficulty=band)
                    input_occurrences += 1
                    unique_inputs.add(_digest(grid))
                    texture = generator.schedule_profile(seed_root, sample_index, band)
                    profile_counts[(band, texture)] += 1
                    strict_counts[band] += int(generator.strict_canonical_like(grid))
                    errors = generator.self_check(grid, difficulty=band)
                    if errors:
                        invalid_inputs.append({
                            "band": band,
                            "seed": seed_root,
                            "sample_index": sample_index,
                            "errors": errors,
                            "input": grid,
                        })
                    target = generator.rule_mirror(grid)
                    demos.append({"input": grid, "output": target})
                    for name, rival in generator.LESSON_COMPETITORS.items():
                        individual_disagreements[name][band] += int(rival(grid) != target)

                    # Racket-check complete first windows for each cyclic start.
                    if seed_root < racket_per_band:
                        racket_candidates.append({
                            "band": band,
                            "start": start,
                            "seed": seed_root,
                            "sample_index": sample_index,
                            "texture": texture,
                            "input": grid,
                            "mirror": target,
                        })

                lessons_by_band[band] += 1
                starts_by_band[band][start] += 1
                for name, rival in generator.LESSON_COMPETITORS.items():
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        surviving_lessons[name][band] += 1

    oracle = RacketOracle(record["program_solution"])
    racket_failures = []
    try:
        for case in racket_candidates:
            actual = oracle.apply(case["input"])
            if actual != case["mirror"]:
                racket_failures.append({
                    key: value for key, value in case.items() if key not in {"mirror"}
                } | {"racket_output": actual, "mirror_output": case["mirror"]})
        for index, pair in enumerate(canonical_pairs):
            actual = oracle.apply(pair["input"])
            if actual != pair["output"]:
                racket_failures.append({
                    "canonical_pair": index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "expected_output": pair["output"],
                })
    finally:
        oracle.close()

    competitor_rows = {}
    for name in generator.LESSON_COMPETITORS:
        competitor_rows[name] = {
            "individual_disagreements_by_band": dict(individual_disagreements[name]),
            "surviving_complete_lessons_by_band": dict(surviving_lessons[name]),
        }

    failures = []
    if invalid_inputs:
        failures.append(f"{len(invalid_inputs)} generated inputs failed self_check")
    missing_shortcut_fits = [name for name, fits in shortcut_fit.items() if not fits]
    if missing_shortcut_fits:
        failures.append("declared canonical shortcuts do not fit all canonical pairs: " + ", ".join(missing_shortcut_fits))
    surviving = {
        name: dict(counts)
        for name, counts in surviving_lessons.items()
        if sum(counts.values())
    }
    if surviving:
        failures.append("declared rivals survived complete lessons: " + json.dumps(surviving, sort_keys=True))
    if racket_failures:
        failures.append(f"{len(racket_failures)} Python/Racket parity failures")

    return {
        "schema": "d6115f669a8e-source-bound-lesson-census-v1",
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "declared_rule_hash": generator.RULE_HASH,
        "rule_source_sha256": _sha256_bytes(record["program_solution"].encode()),
        "sampler": {
            "bands": list(bands),
            "seed_roots": [0, lessons_per_start - 1],
            "lessons_per_cyclic_start_per_band": lessons_per_start,
            "cyclic_starts": list(range(cycle)),
            "lesson_length": cycle,
            "sample_index_formula": "seed_root * lesson_length + cyclic_start + offset",
            "seed_formula": "seed_root (constant inside one lesson)",
            "racket_sample": (
                f"all {cycle} demos for seed roots 0..{racket_per_band - 1} "
                f"at every cyclic start in every band, plus all canonical pairs"
            ),
        },
        "coverage": {
            "lessons_by_band": dict(lessons_by_band),
            "cyclic_starts_by_band": {band: dict(counts) for band, counts in starts_by_band.items()},
            "input_occurrences": input_occurrences,
            "unique_inputs": len(unique_inputs),
            "profile_occurrences": {
                f"{band}:{texture}": count
                for (band, texture), count in sorted(profile_counts.items())
            },
            "strict_canonical_like_occurrences_by_band": dict(strict_counts),
        },
        "canonical_shortcuts": {
            "canonical_pair_count": len(canonical_pairs),
            "fits_every_canonical_pair": shortcut_fit,
        },
        "lesson_competitors": competitor_rows,
        "racket": {
            "generated_cases_checked": len(racket_candidates),
            "canonical_pairs_checked": len(canonical_pairs),
            "calls": oracle.calls,
            "failures": racket_failures,
        },
        "invalid_inputs": invalid_inputs,
        "domain_limits": [
            "The census evaluates only this generator's declared 2-or-3-color, exactly-three-component domain.",
            "Rival refutation is finite evidence over declared rivals; it is not universal program induction.",
            "High-volume scoring uses the task-local Python mirror; the bounded subset and all canonical pairs are checked against Racket.",
        ],
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py")
    parser.add_argument("--lessons-per-start", type=int, default=100)
    parser.add_argument("--racket-per-band", type=int, default=1)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    if args.lessons_per_start < 1 or args.racket_per_band < 0:
        parser.error("lesson and Racket sample counts must be nonnegative, with at least one lesson")
    generator_path = args.generator.resolve()
    generator = _load_module(generator_path)
    record = _canonical_record(generator.TASK_ID)
    report = run_census(
        generator,
        record,
        generator_path=generator_path,
        lessons_per_start=args.lessons_per_start,
        racket_per_band=args.racket_per_band,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "passed": report["passed"],
        "lessons_by_band": report["coverage"]["lessons_by_band"],
        "unique_inputs": report["coverage"]["unique_inputs"],
        "racket_calls": report["racket"]["calls"],
        "failures": report["failures"],
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
