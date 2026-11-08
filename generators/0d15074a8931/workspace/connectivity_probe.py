#!/usr/bin/env python3
"""Probe canonical-fitting rivals, witness coverage, and cyclic lesson windows.

Run from ``repo`` (normally through ``run_with_racket.py`` from the packet root):

    python3 generators/0d15074a8931/workspace/connectivity_probe.py \
        --samples-per-band 200 --out ../checks/connectivity-probe.json

The normal entry creates the same isolated per-puzzle runtime used by reviewer
checks, then re-executes this script inside it.  The probe discovers rivals and
witnesses from the generator declarations rather than maintaining a second
name list.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

TASK_ID = "0d15074a8931"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _exact_diagonal_fixture() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(9)]
    for r0, c0 in ((0, 0), (3, 3)):
        for r in range(r0, r0 + 3):
            for c in range(c0, c0 + 3):
                grid[r][c] = 4
    return grid


def _run_in_runtime(args: argparse.Namespace) -> int:
    from reviewer_support import canonical_pairs, find_root

    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    runtime_root = find_root(__file__)

    def pair(seed: int, sample_index: int, difficulty: str) -> dict[str, Any]:
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        return {"input": grid, "output": gen.rule_mirror(grid)}

    pairs = canonical_pairs(TASK_ID, root=runtime_root)
    canonical = {}
    failures: list[str] = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = sum(rival(item["input"]) == item["output"] for item in pairs)
        canonical[name] = {"matches": matches, "total": len(pairs)}
        if matches != len(pairs):
            failures.append(f"canonical shortcut {name!r} fits only {matches}/{len(pairs)} pairs")

    generated: dict[str, Any] = {}
    aggregate_rival_matches = {name: 0 for name in gen.LESSON_COMPETITORS}
    aggregate_witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    generated_total = 0
    for band_offset, band in enumerate(("easy", "medium", "hard")):
        rival_matches = {name: 0 for name in gen.LESSON_COMPETITORS}
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        unique_inputs: set[str] = set()
        for sample_index in range(args.samples_per_band):
            seed = args.seed_base + band_offset * args.samples_per_band + sample_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid)
            strict_errors = gen.strict_canonical_like(grid)
            if errors or strict_errors:
                failures.append(
                    f"{band} seed={seed} index={sample_index}: "
                    f"self={errors!r} strict={strict_errors!r}"
                )
                continue
            expected = gen.rule_mirror(grid)
            unique_inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
            for name, rival in gen.LESSON_COMPETITORS.items():
                hit = int(rival(grid) == expected)
                rival_matches[name] += hit
                aggregate_rival_matches[name] += hit
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hit = int(witness(grid))
                witness_hits[name] += hit
                aggregate_witness_hits[name] += hit
            generated_total += 1
        generated[band] = {
            "draws": args.samples_per_band,
            "unique_inputs": len(unique_inputs),
            "rival_matches": rival_matches,
            "witness_hits": witness_hits,
        }

    missing_witnesses = [name for name, hits in aggregate_witness_hits.items() if hits == 0]
    if missing_witnesses:
        failures.append(f"declared witnesses absent from generated sample: {missing_witnesses}")
    never_refuted = [
        name for name, matches in aggregate_rival_matches.items() if matches == generated_total
    ]
    if never_refuted:
        failures.append(f"declared rivals never refuted in generated sample: {never_refuted}")

    cyclic: dict[str, Any] = {}
    for band in ("easy", "medium", "hard"):
        failed_rotations: list[dict[str, Any]] = []
        rotations_checked = 0
        for start in range(args.cycle_length):
            lesson = [pair(args.seed_base + start, start + offset, band) for offset in range(5)]
            for query_index in range(5):
                demos = [item for index, item in enumerate(lesson) if index != query_index]
                query = lesson[query_index]
                reasons = gen.lesson_identifiable(demos, query)
                rival_failures = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(item["input"]) == item["output"] for item in demos)
                ]
                rotations_checked += 1
                if reasons or rival_failures:
                    failed_rotations.append(
                        {
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                            "unrefuted_rivals": rival_failures,
                        }
                    )
        cyclic[band] = {
            "starts_checked": args.cycle_length,
            "rotations_checked": rotations_checked,
            "passed": rotations_checked - len(failed_rotations),
            "failures": failed_rotations,
        }
        if failed_rotations:
            failures.append(
                f"{band}: {len(failed_rotations)}/{rotations_checked} query rotations ambiguous"
            )

    fixture = _exact_diagonal_fixture()
    fixture_expected = gen.rule_mirror(fixture)
    fixture_rivals = {
        name: {
            "output": rival(fixture),
            "differs_from_intended": rival(fixture) != fixture_expected,
        }
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    diagonal_name = "eight_connected_same_color"
    if diagonal_name not in fixture_rivals or not fixture_rivals[diagonal_name]["differs_from_intended"]:
        failures.append("exact diagonal fixture does not refute eight_connected_same_color")

    generator_path = Path(gen.__file__).resolve()
    result = {
        "schema": "0d15074a8931-connectivity-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "seed_base": args.seed_base,
        "samples_per_band": args.samples_per_band,
        "generated_total": generated_total,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts": canonical,
        "generated": generated,
        "aggregate_rival_matches": aggregate_rival_matches,
        "aggregate_witness_hits": aggregate_witness_hits,
        "cyclic_windows": cyclic,
        "exact_diagonal_fixture": {
            "input": fixture,
            "self_check": gen.self_check(fixture),
            "strict_canonical_like": gen.strict_canonical_like(fixture),
            "intended_output": fixture_expected,
            "canonical_shortcut_outputs": fixture_rivals,
        },
        "failures": failures,
        "passed": not failures,
    }
    _write_json(args.out.resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


def _run_from_source(args: argparse.Namespace) -> int:
    task_home = Path(__file__).resolve().parents[1]
    library = task_home.parents[1]
    if not (library / "src/arcpuzzles").is_dir():
        raise SystemExit("source entry must run from a packet checkout")
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="0d15074a-connectivity-") as temporary:
        runtime = Path(temporary)
        prepare_runtime(Catalog(library), runtime, TASK_ID)
        destination = runtime / "puzzle_generators/per_puzzle" / TASK_ID / "workspace"
        shutil.copytree(task_home / "workspace", destination, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        script = destination / Path(__file__).name
        command = [
            sys.executable,
            str(script),
            "--in-runtime",
            "--samples-per-band",
            str(args.samples_per_band),
            "--seed-base",
            str(args.seed_base),
            "--cycle-length",
            str(args.cycle_length),
            "--out",
            str(output),
        ]
        env = dict(os.environ, PYTHONPATH=str(runtime), PYTHONNOUSERSITE="1")
        env.pop("PYTHONHOME", None)
        completed = subprocess.run(
            command,
            cwd=runtime,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(completed.stdout, end="")
        runtime_record = {
            "cwd": str(runtime),
            "argv": command,
            "exit_code": completed.returncode,
            "isolated_import_root": str(runtime),
            "runtime_manifest_sha256": hashlib.sha256(
                (runtime / "RUNTIME_MANIFEST.json").read_bytes()
            ).hexdigest(),
        }
        _write_json(output.with_suffix(output.suffix + ".runtime.json"), runtime_record)
        return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=200)
    parser.add_argument("--seed-base", type=int, default=8867716)
    parser.add_argument("--cycle-length", type=int, default=24)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--in-runtime", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.samples_per_band <= 0 or args.cycle_length <= 0:
        parser.error("sample and cycle counts must be positive")
    return _run_in_runtime(args) if args.in_runtime else _run_from_source(args)


if __name__ == "__main__":
    raise SystemExit(main())
