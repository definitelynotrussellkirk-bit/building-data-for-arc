#!/usr/bin/env python3
"""Replay every finite schedule phase for the row-majority lesson.

Run from the packet root so the supported Racket wrapper is active::

    python3 run_with_racket.py python3 \
      generators/ff5eb7af92e7/workspace/probe_schedule_phases.py \
      --out ../checks/schedule-phase-probe.json

The probe checks one representative four-pair production lesson (three
observations plus one query) for each of the three profile phases in each
band.  It obtains labels through ``arcpuzzles apply`` and evaluates every
currently declared rival under both the production query position and all
four query rotations.  This is exhaustive over the finite profile phase, not
over seeds, grids, or undeclared hypotheses.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

TASK_ID = "ff5eb7af92e7"
DIFFICULTIES = ("easy", "medium", "hard")
PAIRS_PER_LESSON = 4


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "src" / "arcpuzzles").is_dir() and (candidate / "shared").is_dir():
            return candidate
    raise RuntimeError(f"could not find repo root above {start}")


def _load_generator(path: Path | None = None):
    generator_path = path or Path(__file__).resolve().parents[1] / "generator.py"
    spec = spec_from_file_location(f"schedule_probe_{TASK_ID}", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {generator_path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _seed_for_phase(module, phase_name: str) -> int:
    """Find the first small seed whose sample-zero profile is phase_name."""
    for seed in range(10 * len(module.SCHEDULE_PROFILES)):
        if module.schedule_profile(seed, 0, None) == phase_name:
            return seed
    raise RuntimeError(f"schedule never emits declared profile {phase_name!r}")


def schedule_cases(module) -> list[dict[str, Any]]:
    """Materialize all difficulty × finite-profile-phase representatives."""
    cases: list[dict[str, Any]] = []
    for difficulty in DIFFICULTIES:
        for phase_name in module.SCHEDULE_PROFILES:
            seed = _seed_for_phase(module, phase_name)
            grids = [
                module.generate(seed, sample_index, difficulty=difficulty)
                for sample_index in range(PAIRS_PER_LESSON)
            ]
            validation = [module.self_check(grid, difficulty=difficulty) for grid in grids]
            if any(validation):
                raise AssertionError(
                    f"invalid generated schedule case {difficulty}/{phase_name}: {validation}"
                )
            cases.append(
                {
                    "difficulty": difficulty,
                    "start_phase": phase_name,
                    "seed": seed,
                    "sample_indices": list(range(PAIRS_PER_LESSON)),
                    "profiles": [
                        module.schedule_profile(seed, sample_index, difficulty)
                        for sample_index in range(PAIRS_PER_LESSON)
                    ],
                    "observed_axes": [module.observe_overrides(grid) for grid in grids],
                    "witnesses": [
                        {
                            name: bool(predicate(grid))
                            for name, predicate in module.SEMANTIC_WITNESSES.items()
                        }
                        for grid in grids
                    ],
                    "grids": grids,
                }
            )
    return cases


def _apply_with_supported_cli(repo_root: Path, grids: list[list[list[int]]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-schedule-probe-") as directory:
        temp = Path(directory)
        input_path = temp / "inputs.json"
        output_path = temp / "racket.json"
        input_path.write_text(json.dumps({"inputs": grids}, separators=(",", ":")))
        argv = [
            sys.executable,
            "-m",
            "arcpuzzles",
            "apply",
            TASK_ID,
            "--input",
            str(input_path),
            "--out",
            str(output_path),
        ]
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "supported apply command failed\n"
                f"argv={argv!r}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        payload = json.loads(output_path.read_text())
        payload["probe_command"] = argv
        payload["probe_cwd"] = "repo"
        return payload


def _rival_verdicts(module, pairs: list[dict[str, Any]], query_index: int) -> dict[str, Any]:
    demo_indices = [index for index in range(len(pairs)) if index != query_index]
    rivals: dict[str, Any] = {}
    ambiguous: list[str] = []
    for name, rival in module.LESSON_COMPETITORS.items():
        demo_matches = [
            rival(pairs[index]["input"]) == pairs[index]["output"]
            for index in demo_indices
        ]
        query_disagrees = rival(pairs[query_index]["input"]) != pairs[query_index]["output"]
        survives = all(demo_matches)
        if survives and query_disagrees:
            ambiguous.append(name)
        rivals[name] = {
            "demo_matches": demo_matches,
            "survives_demos": survives,
            "query_disagrees": query_disagrees,
        }
    return {
        "query_index": query_index,
        "demo_indices": demo_indices,
        "ambiguous_rivals": ambiguous,
        "rivals": rivals,
    }


def run_probe(module, repo_root: Path) -> dict[str, Any]:
    cases = schedule_cases(module)
    flattened = [grid for case in cases for grid in case.pop("grids")]
    applied = _apply_with_supported_cli(repo_root, flattened)
    results = applied["results"]
    if len(results) != len(flattened):
        raise AssertionError(f"apply returned {len(results)} results for {len(flattened)} inputs")

    cursor = 0
    production_ambiguities = 0
    rotation_ambiguities = 0
    for case in cases:
        case_results = results[cursor : cursor + PAIRS_PER_LESSON]
        cursor += PAIRS_PER_LESSON
        pairs = [
            {"input": result["input"], "output": result["output"]}
            for result in case_results
        ]
        case["input_sha256"] = [result["input_sha256"] for result in case_results]
        case["output_sha256"] = [result["output_sha256"] for result in case_results]
        case["production"] = _rival_verdicts(module, pairs, PAIRS_PER_LESSON - 1)
        case["rotations"] = [
            _rival_verdicts(module, pairs, query_index)
            for query_index in range(PAIRS_PER_LESSON)
        ]
        production_ambiguities += len(case["production"]["ambiguous_rivals"])
        rotation_ambiguities += sum(
            len(rotation["ambiguous_rivals"]) for rotation in case["rotations"]
        )

    generator_path = Path(module.__file__).resolve()
    return {
        "schema": "ff5eb7af92e7-schedule-phase-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(generator_path),
        "generator_version": module.VERSION,
        "rule_hash_declared": module.RULE_HASH,
        "apply_authority": {
            key: applied[key]
            for key in (
                "executed_rule_hash",
                "catalog_rule_hash",
                "rule_hash_matches_catalog",
                "rule_text_sha256",
                "generator_sha256",
                "approved",
                "probe_command",
                "probe_cwd",
            )
        },
        "summary": {
            "cases": len(cases),
            "bands": len(DIFFICULTIES),
            "profile_phases": len(module.SCHEDULE_PROFILES),
            "pairs": len(flattened),
            "production_query_position": PAIRS_PER_LESSON - 1,
            "production_ambiguities": production_ambiguities,
            "rotations": len(cases) * PAIRS_PER_LESSON,
            "rotation_ambiguities": rotation_ambiguities,
        },
        "cases": cases,
        "limitations": [
            "Exhaustive only over the declared finite profile phase at sample index zero.",
            "One representative seed is used per phase; this does not enumerate grid identities.",
            "Only declared LESSON_COMPETITORS are tested; universal identifiability is not claimed.",
            "Labels come from the supported canonical Racket apply command, not a Python mirror.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new JSON report path (refuses overwrite)")
    args = parser.parse_args(argv)

    module = _load_generator()
    repo_root = _repo_root(Path(__file__).resolve())
    report = run_probe(module, repo_root)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        output = args.out if args.out.is_absolute() else (repo_root / args.out)
        if output.exists():
            raise FileExistsError(f"refusing to overwrite {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n")
        print(output)
    else:
        print(text)
    if report["summary"]["production_ambiguities"] or report["summary"]["rotation_ambiguities"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
