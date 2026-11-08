#!/usr/bin/env python3
"""Source-bound curriculum audit for f2818d6c50ce.

This tool intentionally does not claim execution authority. It binds its report
to the exact generator SHA-256, verifies the Python rule mirror against every
usable canonical pair, then uses that mirror to inspect large sliding lessons
from the generator's actual schedule. Protected Racket parity is measured by the
repository rule-smoke / semantic / authority gates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
TASK_ROOT = HERE.parent
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_ROOT / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "audit_generator_f2818d6c50ce", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            train = row["train"] if isinstance(row["train"], list) else [row["train"]]
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return copy.deepcopy(train + test)
    raise RuntimeError(f"canonical task {task_id} not found")


def _seed(task_id: str, band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{task_id}|curriculum-audit-v1|{band}|{lesson_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _grid_hash(grid) -> str:
    blob = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def audit(per_band: int) -> dict[str, Any]:
    gen = _load_generator()
    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    pairs = _canonical_pairs(gen.TASK_ID)
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)

    canonical_mirror_mismatches = []
    canonical_shortcut_fit = {}
    for index, pair in enumerate(pairs):
        mirrored = gen._expected_output(copy.deepcopy(pair["input"]))
        if mirrored != pair["output"]:
            canonical_mirror_mismatches.append(index)
    for name, fn in sorted(shortcuts.items()):
        canonical_shortcut_fit[name] = all(
            fn(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs
        )

    report: dict[str, Any] = {
        "schema": "f2818d6c50ce-curriculum-audit-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "authority_scope": (
            "Python _expected_output mirror, first checked against all canonical pairs; "
            "protected Racket parity is separate evidence."
        ),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": per_band,
            "examples_per_lesson": gen.EXAMPLES_NEEDED,
            "queries_per_lesson": 1,
            "lesson_start": "lesson_index * 11",
            "example_indices": "start .. start + EXAMPLES_NEEDED",
            "seed": "sha256(task_id|curriculum-audit-v1|band|lesson_index)[:8]",
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
            "axis_domains": gen.AXES,
        },
        "canonical_pairs": len(pairs),
        "canonical_mirror_mismatches": canonical_mirror_mismatches,
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "competitors": sorted(competitors),
        "bands": {},
        "totals": {},
        "failures": [],
    }

    all_hashes: set[str] = set()
    total_examples = 0
    total_lessons = 0
    total_identifiable = 0
    total_selfcheck_failures = 0
    total_survivors = Counter()
    total_disagreements = Counter()
    total_witnesses = Counter()

    for band in BANDS:
        band_hashes: set[str] = set()
        profiles = Counter()
        witness_counts = Counter()
        competitor_disagreements = Counter()
        survivor_counts = Counter()
        selfcheck_failures = []
        unidentifiable = []
        strict_examples = 0

        for lesson_index in range(per_band):
            seed = _seed(gen.TASK_ID, band, lesson_index)
            start = lesson_index * LESSON_SAMPLE_STRIDE
            demos = []
            examples = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                replay = gen.generate(seed, sample_index, difficulty=band)
                if replay != grid:
                    report["failures"].append(
                        f"nondeterministic replay band={band} lesson={lesson_index} "
                        f"sample_index={sample_index}"
                    )
                errors = list(gen.self_check(grid, difficulty=band) or [])
                if errors:
                    selfcheck_failures.append(
                        {
                            "lesson": lesson_index,
                            "sample_index": sample_index,
                            "errors": errors[:3],
                        }
                    )
                output = gen._expected_output(copy.deepcopy(grid))
                pair = {"input": grid, "output": output}
                examples.append(pair)
                if offset < gen.EXAMPLES_NEEDED:
                    demos.append(pair)

                digest = _grid_hash(grid)
                band_hashes.add(digest)
                all_hashes.add(digest)
                total_examples += 1
                profile = gen.schedule_profile(seed, sample_index, difficulty=band)
                profiles[profile] += 1
                strict_examples += gen.strict_canonical_like(grid) == []
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(witness(copy.deepcopy(grid)))
                for name, competitor in competitors.items():
                    try:
                        competitor_disagreements[name] += (
                            competitor(copy.deepcopy(grid)) != output
                        )
                    except Exception as exc:
                        report["failures"].append(
                            f"competitor {name} raised {type(exc).__name__}: {exc}"
                        )

            query = examples[-1]
            reasons = list(gen.lesson_identifiable(demos, query) or [])
            if reasons:
                unidentifiable.append(
                    {"lesson": lesson_index, "start": start, "reasons": reasons}
                )
            else:
                total_identifiable += 1

            for name, competitor in competitors.items():
                survives = all(
                    competitor(copy.deepcopy(demo["input"])) == demo["output"]
                    for demo in demos
                )
                survivor_counts[name] += survives
            total_lessons += 1

        total_selfcheck_failures += len(selfcheck_failures)
        total_survivors.update(survivor_counts)
        total_disagreements.update(competitor_disagreements)
        total_witnesses.update(witness_counts)
        report["bands"][band] = {
            "lessons": per_band,
            "identifiable": per_band - len(unidentifiable),
            "unidentifiable": unidentifiable,
            "generated_examples": per_band * (gen.EXAMPLES_NEEDED + 1),
            "unique_inputs": len(band_hashes),
            "strict_examples": strict_examples,
            "profiles": dict(sorted(profiles.items())),
            "witness_firings": dict(sorted(witness_counts.items())),
            "competitor_disagreements": dict(sorted(competitor_disagreements.items())),
            "competitor_survived_demo_windows": dict(sorted(survivor_counts.items())),
            "selfcheck_failures": selfcheck_failures,
        }

    if canonical_mirror_mismatches:
        report["failures"].append("Python mirror disagrees with canonical output")
    for name, fits in canonical_shortcut_fit.items():
        if not fits:
            report["failures"].append(
                f"declared canonical shortcut {name!r} does not fit every canonical pair"
            )
    if total_selfcheck_failures:
        report["failures"].append(
            f"{total_selfcheck_failures} generated examples failed self_check"
        )
    if total_identifiable != total_lessons:
        report["failures"].append(
            f"only {total_identifiable}/{total_lessons} lessons identifiable"
        )
    for name, count in total_survivors.items():
        if count:
            report["failures"].append(
                f"competitor {name!r} survived {count}/{total_lessons} demo windows"
            )

    report["totals"] = {
        "lessons": total_lessons,
        "identifiable": total_identifiable,
        "generated_examples": total_examples,
        "unique_inputs": len(all_hashes),
        "selfcheck_failures": total_selfcheck_failures,
        "witness_firings": dict(sorted(total_witnesses.items())),
        "competitor_disagreements": dict(sorted(total_disagreements.items())),
        "competitor_survived_demo_windows": dict(sorted(total_survivors.items())),
    }
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 100:
        parser.error("--per-band must be at least 100 for the review contract")
    report = audit(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(
        f"curriculum-audit: {'PASS' if report['passed'] else 'FAIL'}; "
        f"lessons={report['totals']['identifiable']}/{report['totals']['lessons']} "
        f"identifiable; unique_inputs={report['totals']['unique_inputs']}/"
        f"{report['totals']['generated_examples']}; "
        f"survivors={report['totals']['competitor_survived_demo_windows']}"
    )
    if report["failures"]:
        for failure in report["failures"]:
            print(f"  - {failure}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
