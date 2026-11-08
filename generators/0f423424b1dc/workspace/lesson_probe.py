#!/usr/bin/env python3
"""Source-bound curriculum probe for generator ``0f423424b1dc``.

The packet's semantic gate intentionally materializes only a small number of
complete Racket-backed lessons.  This task-local probe cheaply inspects a much
larger deterministic population with the generator's independently parity-tested
Python mirror.  It reports exactly how lessons were assembled, every source
hash, cyclic schedule coverage, unique inputs/outputs, strict support, witness
firings, and which declared rivals each four-demo lesson refutes.

This is evidence about the sampled curriculum, not proof of universal rule
induction.  Establish Racket parity separately with the packet's rule-smoke and
semantic gates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
TASK_ID = "0f423424b1dc"
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"

for runtime_path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return _sha256_bytes(_stable_json(value).encode())


def _normalized_rule_hash(source: str) -> str:
    return _sha256_bytes(" ".join(source.split()).encode())[:12]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record() -> dict[str, Any]:
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise FileNotFoundError(f"canonical task {TASK_ID} not found in {CANONICAL_PATH}")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [*list(row.get("train") or []), *list(row.get("test") or [])]


def _probe_seed(band: str, lesson_index: int) -> int:
    token = f"lesson-probe:v1:{TASK_ID}:{band}:{lesson_index}"
    return int(hashlib.sha256(token.encode()).hexdigest()[:12], 16)


def _shape(grid: list[list[int]]) -> str:
    return f"{len(grid)}x{len(grid[0])}"


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def _json_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def _observed_values(values: dict[str, set[Any]]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    for name, seen in sorted(values.items()):
        out[name] = sorted(seen, key=lambda item: (type(item).__name__, repr(item)))
    return out


def run_probe(*, per_band: int = 100, expected_generator_sha: str | None = None) -> dict[str, Any]:
    """Inspect ``per_band`` disjoint five-pair lessons in each difficulty band."""
    if isinstance(per_band, bool) or not isinstance(per_band, int) or per_band <= 0:
        raise ValueError("per_band must be a positive integer")

    gen = _load_generator()
    canonical = _canonical_record()
    canonical_pairs = _canonical_pairs(canonical)
    canonical_rule_source = str(canonical.get("program_solution") or "")
    generator_sha = _sha256_file(GENERATOR_PATH)
    canonical_rule_hash = _normalized_rule_hash(canonical_rule_source)

    shortcuts: dict[str, Any] = {}
    all_shortcuts_fit = True
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        fit_count = sum(
            rival(pair["input"]) == pair["output"] for pair in canonical_pairs
        )
        shortcuts[name] = {
            "canonical_pairs_fit": fit_count,
            "canonical_pairs_total": len(canonical_pairs),
            "fits_every_canonical_pair": fit_count == len(canonical_pairs),
        }
        all_shortcuts_fit &= fit_count == len(canonical_pairs)

    report: dict[str, Any] = {
        "schema": "arc-generator-lesson-probe-v1",
        "task_id": TASK_ID,
        "status": "PASS",
        "source": {
            "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
            "generator_sha256": generator_sha,
            "generator_version": str(gen.VERSION),
            "declared_rule_hash": str(gen.RULE_HASH),
            "canonical_rule_hash": canonical_rule_hash,
            "canonical_ledger_path": str(CANONICAL_PATH.relative_to(REPO)),
            "canonical_ledger_sha256": _sha256_file(CANONICAL_PATH),
            "probe_path": str(HERE.relative_to(REPO)),
            "probe_sha256": _sha256_file(HERE),
            "expected_generator_sha256": expected_generator_sha,
            "expected_generator_sha256_matches": (
                expected_generator_sha is None or expected_generator_sha == generator_sha
            ),
        },
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "lessons_per_band": per_band,
            "pairs_per_lesson": 5,
            "demos_per_lesson": 4,
            "queries_per_lesson": 1,
            "seed_derivation": (
                "int(sha256('lesson-probe:v1:<task>:<band>:<lesson_index>')"
                ".hexdigest()[:12], 16)"
            ),
            "lesson_start_sample_index": "lesson_index * 5",
            "pair_sample_index": "lesson_start + pair_offset, pair_offset=0..4",
            "windows_overlap": False,
            "cyclic_schedule_check": "all start residues modulo 4 are reported",
            "output_oracle": (
                "generator.rule_mirror; use rule_smoke/semantic_gate evidence for "
                "independent Racket parity"
            ),
        },
        "domain_limits": {
            "declared_axes": gen.AXES,
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
            "examples_needed": int(gen.EXAMPLES_NEEDED),
            "known_limit": (
                "column-independent scenes with 6..12 rows/columns, 1..3 lawful "
                "target columns, and at most one distractor of each declared kind"
            ),
        },
        "canonical_shortcuts": {
            "canonical_pairs": len(canonical_pairs),
            "all_fit_every_canonical_pair": all_shortcuts_fit,
            "results": shortcuts,
        },
        "bands": {},
        "problems": [],
    }

    if canonical_rule_hash != str(gen.RULE_HASH):
        report["problems"].append(
            f"declared RULE_HASH {gen.RULE_HASH} != canonical {canonical_rule_hash}"
        )
    if expected_generator_sha is not None and expected_generator_sha != generator_sha:
        report["problems"].append(
            f"generator SHA mismatch: expected {expected_generator_sha}, got {generator_sha}"
        )
    if not all_shortcuts_fit:
        report["problems"].append("a declared canonical shortcut does not fit every canonical pair")

    for band in ("easy", "medium", "hard"):
        input_hashes: set[str] = set()
        output_hashes: set[str] = set()
        pair_hashes: set[str] = set()
        start_residues: Counter[int] = Counter()
        profile_counts: Counter[str] = Counter()
        shape_counts: Counter[str] = Counter()
        palette_counts: Counter[int] = Counter()
        witness_pair_counts: Counter[str] = Counter()
        rival_disagreement_pairs: Counter[str] = Counter()
        rival_refuted_lessons: Counter[str] = Counter()
        observed: dict[str, set[Any]] = defaultdict(set)
        strict_hits = 0
        identifiable = 0
        self_check_failures = 0
        lesson_errors: list[dict[str, Any]] = []

        for lesson_index in range(per_band):
            seed = _probe_seed(band, lesson_index)
            start = lesson_index * 5
            start_residues[start % 4] += 1
            pairs: list[dict[str, Any]] = []
            refuted_here = {name: False for name in gen.LESSON_COMPETITORS}

            for pair_offset in range(5):
                sample_index = start + pair_offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                findings = list(gen.self_check(grid) or [])
                if findings:
                    self_check_failures += 1
                    if len(lesson_errors) < 20:
                        lesson_errors.append({
                            "lesson_index": lesson_index,
                            "pair_offset": pair_offset,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": findings[0],
                        })
                output = gen.rule_mirror(grid)
                pair = {"input": grid, "output": output}
                pairs.append(pair)

                input_hashes.add(_digest(grid))
                output_hashes.add(_digest(output))
                pair_hashes.add(_digest(pair))
                shape_counts[_shape(grid)] += 1
                palette_counts[_palette_size(grid)] += 1
                profile_counts[str(gen.schedule_profile(seed, sample_index, band))] += 1
                strict_hits += int(not gen.strict_canonical_like(grid))

                axes = gen.observe_overrides(grid)
                for name, value in axes.items():
                    observed[name].add(value)
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_pair_counts[name] += int(bool(witness(grid)))
                for name, rival in gen.LESSON_COMPETITORS.items():
                    disagrees = rival(grid) != output
                    rival_disagreement_pairs[name] += int(disagrees)
                    if pair_offset < 4 and disagrees:
                        refuted_here[name] = True

            reasons = list(gen.lesson_identifiable(pairs[:4], pairs[4]) or [])
            if not reasons:
                identifiable += 1
            elif len(lesson_errors) < 20:
                lesson_errors.append({
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "sample_index": start,
                    "error": f"lesson_identifiable: {reasons}",
                })
            for name, refuted in refuted_here.items():
                rival_refuted_lessons[name] += int(refuted)

        band_row = {
            "lessons": per_band,
            "pairs": per_band * 5,
            "identifiable_lessons": identifiable,
            "self_check_failures": self_check_failures,
            "strict_pairs": strict_hits,
            "strict_fraction": strict_hits / (per_band * 5),
            "unique_inputs": len(input_hashes),
            "unique_outputs": len(output_hashes),
            "unique_pairs": len(pair_hashes),
            "start_residues_mod_4": _json_counter(start_residues),
            "profile_counts": _json_counter(profile_counts),
            "shape_counts": _json_counter(shape_counts),
            "palette_size_counts": _json_counter(palette_counts),
            "witness_pair_counts": _json_counter(witness_pair_counts),
            "rival_disagreement_pairs": _json_counter(rival_disagreement_pairs),
            "rival_refuted_lessons": _json_counter(rival_refuted_lessons),
            "observed_axis_values": _observed_values(observed),
            "errors": lesson_errors,
        }
        report["bands"][band] = band_row

        if identifiable != per_band:
            report["problems"].append(
                f"{band}: only {identifiable}/{per_band} lessons identifiable"
            )
        if self_check_failures:
            report["problems"].append(
                f"{band}: {self_check_failures} generated pairs failed self_check"
            )
        for rival_name, count in rival_refuted_lessons.items():
            if count != per_band:
                report["problems"].append(
                    f"{band}: rival {rival_name} refuted in only {count}/{per_band} lessons"
                )

    if report["problems"]:
        report["status"] = "FAIL"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--expected-generator-sha")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    report = run_probe(
        per_band=args.per_band,
        expected_generator_sha=args.expected_generator_sha,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{report['task_id']}: {report['status']} — "
        + ", ".join(
            f"{band} {row['identifiable_lessons']}/{row['lessons']} lessons, "
            f"{row['unique_inputs']}/{row['pairs']} unique inputs"
            for band, row in report["bands"].items()
        )
    )
    if report["problems"]:
        for problem in report["problems"]:
            print(f"FAIL: {problem}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
