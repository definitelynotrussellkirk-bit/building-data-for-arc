#!/usr/bin/env python3
"""Source-bound whole-lesson rival census for ARC task f1347e0836ec.

The probe reads rival callables directly from the selected generator, checks
that each declared canonical shortcut really fits every retained canonical
pair, and scores every cyclic start of the four-profile lesson schedule.  It
uses the generator's Python rule mirror for cheap exhaustive lesson scoring;
the repository rule-smoke and semantic-gate stages independently compare that
mirror with the selected Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "f1347e0836ec"
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_module(path: Path):
    name = f"lesson_probe_{TASK_ID}_{_sha256(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(f"{TASK_ID} is absent from {path}")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return [*row.get("train", []), *test]


def _callable_mapping(module: Any, name: str) -> dict[str, Callable]:
    value = getattr(module, name, None)
    if not isinstance(value, dict) or not value:
        raise TypeError(f"{name} must be a non-empty mapping")
    if not all(isinstance(key, str) and callable(fn) for key, fn in value.items()):
        raise TypeError(f"{name} must map string names to callables")
    return dict(value)


def _lesson(
    generator: Any,
    *,
    seed: int,
    band: str,
    start: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    pair_count = int(generator.EXAMPLES_NEEDED) + 1
    pairs: list[dict[str, Any]] = []
    profiles: list[str] = []
    for offset in range(pair_count):
        sample_index = start + offset
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = list(generator.self_check(grid, difficulty=band) or [])
        if findings:
            raise AssertionError(
                f"self_check failed at {band}/seed={seed}/index={sample_index}: "
                + "; ".join(findings)
            )
        pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
        profiles.append(
            str(generator.schedule_profile(seed, sample_index, difficulty=band))
        )
    return pairs[:-1], pairs[-1], profiles


def _score_band(
    generator: Any,
    *,
    band: str,
    seeds: range,
    starts: list[int],
) -> dict[str, Any]:
    rivals = _callable_mapping(generator, "LESSON_COMPETITORS")
    survivors = {name: 0 for name in rivals}
    query_disagreement_survivors = {name: 0 for name in rivals}
    demo_disagreements = {name: 0 for name in rivals}
    query_disagreements = {name: 0 for name in rivals}
    first_survivor: dict[str, Any] = {}
    unique_inputs: set[str] = set()
    profile_sequences: Counter[str] = Counter()
    lessons = 0
    pairs_seen = 0

    for seed in seeds:
        for start in starts:
            demos, query, profiles = _lesson(
                generator, seed=seed, band=band, start=start
            )
            lessons += 1
            all_pairs = [*demos, query]
            pairs_seen += len(all_pairs)
            profile_sequences["->".join(profiles)] += 1
            for pair in all_pairs:
                unique_inputs.add(_grid_sha256(pair["input"]))

            findings = list(generator.lesson_identifiable(demos, query) or [])
            if findings:
                raise AssertionError(
                    f"lesson_identifiable failed at {band}/seed={seed}/start={start}: "
                    + "; ".join(findings)
                )

            for name, rival in rivals.items():
                misses = sum(
                    rival(pair["input"]) != pair["output"] for pair in demos
                )
                query_miss = rival(query["input"]) != query["output"]
                demo_disagreements[name] += misses
                query_disagreements[name] += int(query_miss)
                if misses == 0:
                    survivors[name] += 1
                    query_disagreement_survivors[name] += int(query_miss)
                    first_survivor.setdefault(
                        name,
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_disagrees": query_miss,
                            "profiles": profiles,
                            "demo_inputs": [pair["input"] for pair in demos],
                            "query_input": query["input"],
                        },
                    )

    return {
        "lessons": lessons,
        "pairs_seen": pairs_seen,
        "unique_inputs": len(unique_inputs),
        "duplicate_input_occurrences": pairs_seen - len(unique_inputs),
        "cyclic_starts_seen": starts,
        "profile_sequences": dict(sorted(profile_sequences.items())),
        "demo_disagreements": demo_disagreements,
        "query_disagreements": query_disagreements,
        "survivors_after_demos": survivors,
        "query_disagreement_survivors": query_disagreement_survivors,
        "first_survivor": first_survivor,
    }


def run_census(
    *,
    generator_path: Path,
    canonical_path: Path,
    lessons_per_band: int = 100,
    seed_start: int = 0,
) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    generator_path = generator_path.resolve()
    canonical_path = canonical_path.resolve()
    repo_root = generator_path.parents[2]
    runtime_path = repo_root / "shared" / "runtime"
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

    generator = _load_module(generator_path)
    if generator.TASK_ID != TASK_ID:
        raise ValueError(f"generator TASK_ID {generator.TASK_ID!r} != {TASK_ID!r}")

    canonical = _canonical_row(canonical_path)
    pairs = _canonical_pairs(canonical)
    shortcuts = _callable_mapping(generator, "CANONICAL_SHORTCUTS")
    shortcut_fit: dict[str, Any] = {}
    for name, shortcut in shortcuts.items():
        fit = sum(shortcut(pair["input"]) == pair["output"] for pair in pairs)
        shortcut_fit[name] = {
            "fit_pairs": fit,
            "canonical_pairs": len(pairs),
            "fits_all_canonical_pairs": fit == len(pairs),
        }

    schedule = tuple(generator.SCHEDULE_PROFILES)
    starts = list(range(len(schedule)))
    seeds = range(seed_start, seed_start + lessons_per_band)
    bands = {
        band: _score_band(
            generator,
            band=band,
            seeds=seeds,
            starts=starts,
        )
        for band in BANDS
    }

    probe_path = Path(__file__).resolve()
    return {
        "schema": "f1347e0836ec-lesson-rival-census-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(generator_path),
            "generator_sha256": _sha256(generator_path),
            "generator_version": str(generator.VERSION),
            "rule_hash": str(generator.RULE_HASH),
            "canonical_path": str(canonical_path),
            "canonical_ledger_sha256": _sha256(canonical_path),
            "probe_path": str(probe_path),
            "probe_sha256": _sha256(probe_path),
        },
        "oracle": {
            "kind": "selected generator rule_mirror",
            "canonical_pairs_matched": sum(
                generator.rule_mirror(pair["input"]) == pair["output"]
                for pair in pairs
            ),
            "canonical_pairs_total": len(pairs),
            "live_racket_cross_check": (
                "external repository rule_smoke and semantic_gate evidence"
            ),
        },
        "sampler": {
            "demo_count": int(generator.EXAMPLES_NEEDED),
            "query_count": 1,
            "sequential_sample_indices": True,
            "seed_start": seed_start,
            "seed_stop_exclusive": seed_start + lessons_per_band,
            "seeds_per_band": lessons_per_band,
            "cyclic_starts": starts,
            "schedule_profiles": list(schedule),
        },
        "declared_rivals": sorted(
            _callable_mapping(generator, "LESSON_COMPETITORS")
        ),
        "declared_canonical_shortcuts": sorted(shortcuts),
        "canonical_shortcut_fit": shortcut_fit,
        "bands": bands,
        "claim_scope": (
            "Finite source-bound census over the listed seeds and every cyclic "
            "schedule start; it verifies the declared rival set, not universal "
            "rule induction."
        ),
    }


def _has_survivors(report: dict[str, Any]) -> bool:
    return any(
        count
        for band in report["bands"].values()
        for count in band["survivors_after_demos"].values()
    )


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve()
    task_home = here.parent.parent
    repo_root = task_home.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=task_home / "generator.py")
    parser.add_argument(
        "--canonical",
        type=Path,
        default=repo_root / "shared/data/canonical/puzzles.jsonl",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-no-survivors", action="store_true")
    args = parser.parse_args(argv)

    report = run_census(
        generator_path=args.generator,
        canonical_path=args.canonical,
        lessons_per_band=args.lessons_per_band,
        seed_start=args.seed_start,
    )
    text = json.dumps(report, indent=2) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    if args.require_no_survivors and _has_survivors(report):
        return 1
    if not all(
        row["fits_all_canonical_pairs"]
        for row in report["canonical_shortcut_fit"].values()
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
