#!/usr/bin/env python3
"""Source-bound curriculum probe for generator 2f91d0756f23.

This probe is intentionally task-local and loads ``../generator.py`` by exact
path.  It assembles independent lessons with four consecutive demonstrations
and one query.  Lesson starts cycle through every residue modulo four, so the
small deterministic schedule is tested from every cyclic start rather than
inferred from marginal witness frequencies.

Labels in this probe come from the generator's independent Python mirror
``_solve_official``.  That mirror is separately bound to ``RULE_HASH`` and
checked against all canonical pairs and the repository's Racket rule-smoke
stage.  This probe is distribution/teaching evidence, not a claim of universal
induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "2f91d0756f23"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
REPO_ROOT = HERE.parents[2]
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "source_bound_generator_2f91d0756f23", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _seed(band: str, lesson_index: int) -> int:
    text = f"review-probe:v1:{TASK_ID}:{band}:{lesson_index}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], row["test"]]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {CANONICAL_PATH}")


def _profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def run_probe(*, lessons_per_band: int = 100) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band < 1:
        raise ValueError("lessons_per_band must be a positive integer")

    canonical_pairs = _canonical_pairs()
    canonical_profiles = {_profile(pair["input"]) for pair in canonical_pairs}
    shortcut_rows: dict[str, Any] = {}
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical_pairs]
        shortcut_rows[name] = {
            "fits": sum(fits),
            "pairs": len(fits),
            "fits_every_pair": all(fits),
        }

    report: dict[str, Any] = {
        "schema": "arc-generator-deep-probe-v1",
        "source": {
            "task_id": TASK_ID,
            "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
            "generator_sha256": _sha256_file(GENERATOR_PATH),
            "generator_version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
            "probe_path": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
            "probe_sha256": _sha256_file(Path(__file__).resolve()),
        },
        "sampler": {
            "lessons_per_band": lessons_per_band,
            "bands": ["easy", "medium", "hard"],
            "lesson_policy": "4 consecutive demos + next consecutive query",
            "seed_formula": "sha256('review-probe:v1:TASK:band:lesson')[:16]",
            "start_sample_index": "lesson_index * 5",
            "cyclic_start_policy": "start_sample_index % 4 visits all four residues",
            "inputs_per_lesson": 5,
            "labels": "generator._solve_official Python mirror; authority checked separately",
            "overlap_policy": "independent seed per lesson; no input reused across windows by construction",
        },
        "canonical_shortcuts": {
            "usable_pairs": len(canonical_pairs),
            "canonical_profiles": [list(p) for p in sorted(canonical_profiles)],
            "by_name": shortcut_rows,
            "all_fit_every_canonical_pair": bool(shortcut_rows)
            and all(row["fits_every_pair"] for row in shortcut_rows.values()),
        },
        "bands": {},
        "limitations": [
            "Finite deterministic probe; it does not establish universal induction.",
            "Deep-probe labels use the pinned Python mirror, not 1,500 independent Racket calls.",
            "Racket equivalence is instead checked by canonical tests, rule_smoke, and authority_sync.",
        ],
    }

    for band in ("easy", "medium", "hard"):
        unique_inputs: set[str] = set()
        cyclic_starts: Counter[int] = Counter()
        schedule_profiles: Counter[str] = Counter()
        axis_values: dict[str, list[int]] = {name: [] for name in gen.AXES}
        strict_failures: list[dict[str, Any]] = []
        unidentifiable: list[dict[str, Any]] = []
        witness_firings: Counter[str] = Counter()
        rival_disagreements: Counter[str] = Counter()
        competitor_survived_demos: Counter[str] = Counter()
        competitor_changed_query: Counter[str] = Counter()
        profile_hits = 0
        generated_inputs = 0

        for lesson_index in range(lessons_per_band):
            seed = _seed(band, lesson_index)
            start = lesson_index * 5
            cyclic_starts[start % 4] += 1
            pairs: list[dict[str, Any]] = []

            for offset in range(5):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                output = gen._solve_official(grid)
                pairs.append({"input": grid, "output": output})
                generated_inputs += 1
                unique_inputs.add(_grid_hash(grid))
                schedule_profiles[gen.schedule_profile(seed, sample_index, difficulty=band)] += 1
                profile_hits += int(_profile(grid) in canonical_profiles)

                observed = gen.observe_overrides(grid)
                for name in axis_values:
                    axis_values[name].append(observed[name])

                issues = gen.strict_canonical_like(grid)
                if issues and len(strict_failures) < 10:
                    strict_failures.append({
                        "lesson": lesson_index,
                        "sample_index": sample_index,
                        "reasons": list(issues),
                    })
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_firings[name] += int(bool(witness(grid)))
                for name, rival in gen.SEMANTIC_RIVALS.items():
                    rival_disagreements[name] += int(rival(grid) != output)

            demos, query = pairs[:4], pairs[4]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons and len(unidentifiable) < 10:
                unidentifiable.append({
                    "lesson": lesson_index,
                    "seed": seed,
                    "start_sample_index": start,
                    "reasons": reasons,
                })

            for name, rival in gen.LESSON_COMPETITORS.items():
                fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                if fits:
                    competitor_survived_demos[name] += 1
                    if rival(query["input"]) != query["output"]:
                        competitor_changed_query[name] += 1

        axis_limits = {
            name: {
                "min": min(values),
                "max": max(values),
                "distinct": sorted(set(values)),
            }
            for name, values in axis_values.items()
        }
        row = {
            "lessons": lessons_per_band,
            "lesson_windows_unique": lessons_per_band,
            "generated_inputs": generated_inputs,
            "unique_inputs": len(unique_inputs),
            "cyclic_start_counts": _counter_dict(cyclic_starts),
            "schedule_profile_counts": _counter_dict(schedule_profiles),
            "canonical_profile_hits": profile_hits,
            "axis_limits_observed": axis_limits,
            "strict_failures": len(strict_failures),
            "strict_failure_examples": strict_failures,
            "witness_firings": _counter_dict(witness_firings),
            "rival_disagreements": _counter_dict(rival_disagreements),
            "lessons_identifiable": lessons_per_band - len(unidentifiable),
            "lessons_unidentifiable": len(unidentifiable),
            "unidentifiable_examples": unidentifiable,
            "competitor_survived_all_demos": _counter_dict(competitor_survived_demos),
            "competitor_fit_demos_but_changed_query": _counter_dict(competitor_changed_query),
        }
        report["bands"][band] = row

    report["aggregate"] = {
        "lessons": lessons_per_band * 3,
        "generated_inputs": lessons_per_band * 3 * 5,
        "unique_inputs": sum(row["unique_inputs"] for row in report["bands"].values()),
        "strict_failures": sum(row["strict_failures"] for row in report["bands"].values()),
        "lessons_unidentifiable": sum(
            row["lessons_unidentifiable"] for row in report["bands"].values()
        ),
        "all_canonical_shortcuts_fit": report["canonical_shortcuts"][
            "all_fit_every_canonical_pair"
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    aggregate = report["aggregate"]
    print(
        "deep-probe: "
        f"{aggregate['lessons']} lessons, {aggregate['unique_inputs']}/"
        f"{aggregate['generated_inputs']} unique inputs, "
        f"strict_failures={aggregate['strict_failures']}, "
        f"unidentifiable={aggregate['lessons_unidentifiable']}"
    )
    return 0 if not aggregate["strict_failures"] and not aggregate["lessons_unidentifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
