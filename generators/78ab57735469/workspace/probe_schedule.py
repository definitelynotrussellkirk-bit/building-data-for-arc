#!/usr/bin/env python3
"""Source-bound support probe for task 78ab57735469.

The shared semantic gate samples a bounded set of lessons.  This task-local tool
adds an inexpensive deterministic check of every declared competitor across
consecutive lesson starts and every possible query position.  It deliberately
iterates the generator's live declarations rather than copying rival names.

Labels for generated instances use the generator's independent Python
``rule_mirror``; canonical-shortcut claims are checked against canonical outputs.
Racket-labelled evidence remains the authority for final verification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "78ab57735469"


def _load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    if not path.is_file():
        path = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"schedule_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _grid_key(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def probe(
    *,
    seed: int = 0,
    starts: int = 8,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict:
    root = find_root(__file__)
    gen, generator_path = _load_generator(root)
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    if not competitors:
        raise RuntimeError("generator declares no LESSON_COMPETITORS")
    if not callable(getattr(gen, "rule_mirror", None)):
        raise RuntimeError("generator declares no callable rule_mirror")

    violations: list[dict] = []
    shortcut_results = {}
    canonical = canonical_pairs(TASK_ID, root=root)
    for name, rival in shortcuts.items():
        mismatches = []
        for index, pair in enumerate(canonical):
            prediction = rival([list(row) for row in pair["input"]])
            if prediction != pair["output"]:
                mismatches.append(index)
        shortcut_results[name] = {
            "canonical_pairs": len(canonical),
            "mismatch_indices": mismatches,
            "fits_all_pairs": not mismatches,
        }
        if mismatches:
            violations.append({
                "kind": "declared_canonical_shortcut_does_not_fit",
                "rival": name,
                "canonical_pair_indices": mismatches,
            })

    bands = tuple(bands)
    unique_inputs: set[str] = set()
    lessons_checked = 0
    rotations = 0
    rival_checks = 0
    ambiguous = []
    dimension_counts: dict[str, int] = {}
    for band in bands:
        for start in range(starts):
            examples = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid)
                if errors:
                    violations.append({
                        "kind": "generated_input_rejected",
                        "band": band,
                        "start": start,
                        "sample_index": sample_index,
                        "errors": errors,
                    })
                unique_inputs.add(_grid_key(grid))
                key = f"{len(grid)}x{len(grid[0])}"
                dimension_counts[key] = dimension_counts.get(key, 0) + 1
                examples.append({"input": grid, "output": gen.rule_mirror(grid)})
            lessons_checked += 1
            for query_index, query in enumerate(examples):
                demos = [item for i, item in enumerate(examples) if i != query_index]
                rotations += 1
                for name, rival in competitors.items():
                    rival_checks += 1
                    fits = all(
                        rival([list(row) for row in demo["input"]]) == demo["output"]
                        for demo in demos
                    )
                    changes_query = (
                        rival([list(row) for row in query["input"]]) != query["output"]
                    )
                    if fits and changes_query:
                        item = {
                            "band": band,
                            "lesson_start": start,
                            "query_index": query_index,
                            "rival": name,
                        }
                        ambiguous.append(item)
                        violations.append({"kind": "ambiguous_rotation", **item})

    source_hash = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    return {
        "schema": "78ab57735469-schedule-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "seed": seed,
        "starts": starts,
        "bands": list(bands),
        "declared_competitors": sorted(competitors),
        "canonical_shortcuts": shortcut_results,
        "dimension_observations": dimension_counts,
        "summary": {
            "bands": len(bands),
            "lesson_starts": starts,
            "lessons_checked": lessons_checked,
            "unique_inputs": len(unique_inputs),
            "query_rotations": rotations,
            "rival_checks": rival_checks,
            "ambiguous_rotations": len(ambiguous),
        },
        "ambiguous_rotations": ambiguous,
        "violations": violations,
        "scope_note": (
            "Finite checks against declared rivals on one deterministic seed; "
            "generated labels use rule_mirror, not Racket."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument(
        "--bands",
        nargs="+",
        choices=("easy", "medium", "hard"),
        default=("easy", "medium", "hard"),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = probe(seed=args.seed, starts=args.starts, bands=args.bands)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
