from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "b6592c220670"
EXPECTED_GENERATOR_SHA256 = "5447275c4a8eb23119a9357aa3d8933543d6a801f923152243545dd72c91a3f2"
DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = tuple(range(30))
CYCLIC_STARTS = tuple(range(8))
EXACT_COUNTEREXAMPLE = {"difficulty": "easy", "seed": 0, "start": 0, "query_position": 1}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def main() -> int:
    repo = Path(__file__).resolve().parents[3] / "repo"
    generator_path = repo / "generators" / TASK_ID / "generator.py"
    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise AssertionError((generator_sha, EXPECTED_GENERATOR_SHA256))
    module = load_module(generator_path)

    canonical_path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_row = next(
        json.loads(line)
        for line in canonical_path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    canonical_pairs = canonical_row["train"] + canonical_row.get("test", [])
    canonical_shortcut_checks = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        fits = []
        for pair in canonical_pairs:
            fits.append(rival(pair["input"]) == pair["output"])
            if module.rule_mirror(pair["input"]) != pair["output"]:
                raise AssertionError(f"Python mirror misses canonical pair for {name}")
        canonical_shortcut_checks[name] = fits
        if not all(fits):
            raise AssertionError(f"declared canonical shortcut {name} does not fit canonical pairs")

    windows = 0
    rotations = 0
    production_failures = []
    rotation_failures = []
    invalid = []
    unique_inputs = set()
    reason_counts = Counter()
    first_counterexample = None

    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for start in CYCLIC_STARTS:
                pairs = []
                for offset in range(module.EXAMPLES_NEEDED + 1):
                    sample_index = start + offset
                    grid = module.generate(seed, sample_index, difficulty=difficulty)
                    errors = module.self_check(grid, difficulty=difficulty)
                    if errors:
                        invalid.append({
                            "difficulty": difficulty,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        })
                    output = module.rule_mirror(grid)
                    pairs.append({"input": grid, "output": output})
                    unique_inputs.add(frozen(grid))
                windows += 1

                production_reasons = module.lesson_identifiable(pairs[:-1], pairs[-1])
                if production_reasons:
                    production_failures.append({
                        "difficulty": difficulty,
                        "seed": seed,
                        "start": start,
                        "query_position": module.EXAMPLES_NEEDED,
                        "reasons": production_reasons,
                    })

                for query_position in range(len(pairs)):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_position]
                    query = pairs[query_position]
                    reasons = module.lesson_identifiable(demos, query)
                    rotations += 1
                    if reasons:
                        item = {
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "sample_indices": list(range(start, start + len(pairs))),
                            "query_position": query_position,
                            "query_sample_index": start + query_position,
                            "reasons": reasons,
                        }
                        rotation_failures.append(item)
                        reason_counts.update(reasons)
                    if {
                        "difficulty": difficulty,
                        "seed": seed,
                        "start": start,
                        "query_position": query_position,
                    } == EXACT_COUNTEREXAMPLE:
                        rival_name = "skip_identity_instruction"
                        rival = module.LESSON_COMPETITORS[rival_name]
                        demo_fits = [rival(pair["input"]) == pair["output"] for pair in demos]
                        rival_query = rival(query["input"])
                        first_counterexample = {
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "sample_indices": list(range(start, start + len(pairs))),
                            "query_position": query_position,
                            "query_sample_index": start + query_position,
                            "rival_name": rival_name,
                            "rival_description": "Treat code 1 as a no-op that emits no panel; apply all other instructions cumulatively.",
                            "validator_errors": [module.self_check(pair["input"], difficulty=difficulty) for pair in pairs],
                            "demo_fits": demo_fits,
                            "query_differs": rival_query != query["output"],
                            "lesson_identifiable_reasons": reasons,
                            "pairs": pairs,
                            "rival_query_output": rival_query,
                        }

    if invalid:
        raise AssertionError(f"invalid generated inputs: {invalid[:3]}")
    if first_counterexample is None:
        raise AssertionError("exact counterexample was not visited")
    if not all(first_counterexample["demo_fits"]) or not first_counterexample["query_differs"]:
        raise AssertionError(first_counterexample)

    out_dir = Path(__file__).resolve().parent
    query_pair = first_counterexample["pairs"][first_counterexample["query_position"]]
    (out_dir / "input.json").write_text(json.dumps(query_pair["input"], indent=2) + "\n")
    (out_dir / "python_oracle.json").write_text(json.dumps(query_pair["output"], indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(first_counterexample["rival_query_output"], indent=2) + "\n")
    report = {
        "task_id": TASK_ID,
        "classification": "reproduced query-rotation limitation",
        "generator_sha256": generator_sha,
        "rule_hash": module.RULE_HASH,
        "generator_version": module.VERSION,
        "canonical_pair_count": len(canonical_pairs),
        "declared_canonical_shortcuts": canonical_shortcut_checks,
        "declared_lesson_competitors": sorted(module.LESSON_COMPETITORS),
        "probe": {
            "difficulties": list(DIFFICULTIES),
            "seed_range": [min(SEEDS), max(SEEDS)],
            "seed_count": len(SEEDS),
            "cyclic_starts": list(CYCLIC_STARTS),
            "demo_count": module.EXAMPLES_NEEDED,
            "pairs_per_window": module.EXAMPLES_NEEDED + 1,
            "window_count": windows,
            "production_failure_count": len(production_failures),
            "rotation_count": rotations,
            "rotation_failure_count": len(rotation_failures),
            "invalid_input_count": len(invalid),
            "unique_input_count": len(unique_inputs),
            "reason_counts": dict(reason_counts),
            "first_production_failures": production_failures[:10],
            "first_rotation_failures": rotation_failures[:10],
        },
        "counterexample": first_counterexample,
        "racket_apply": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                "--input", f"../checks/audit/{TASK_ID}/input.json",
                "--out", f"../checks/audit/{TASK_ID}/racket.json",
            ],
            "status": "run separately; see racket.json",
        },
    }
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": TASK_ID,
        "windows": windows,
        "production_failures": len(production_failures),
        "rotations": rotations,
        "rotation_failures": len(rotation_failures),
        "unique_inputs": len(unique_inputs),
        "counterexample": {
            key: first_counterexample[key]
            for key in ("difficulty", "seed", "start", "query_position", "query_sample_index", "rival_name", "demo_fits", "query_differs")
        },
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
