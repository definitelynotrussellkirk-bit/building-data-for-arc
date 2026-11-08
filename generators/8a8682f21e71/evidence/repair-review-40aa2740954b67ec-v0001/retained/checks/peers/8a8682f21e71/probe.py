from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, load_selected_generator

TASK_ID = "8a8682f21e71"
EXPECTED_SHA256 = "0629141c376895c1b0de71535e58764fc072f9498827bf9b52d475083a0da43a"
SEEDS = (0, 17)
DEMOS = 5
QUERIES = 4


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_program(root: Path) -> str:
    for line in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise ValueError(f"canonical program missing for {TASK_ID}")


def main() -> None:
    here = Path(__file__).resolve()
    root = find_root(here)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SHA256:
        raise ValueError(f"peer source changed: {source_sha256}")
    program = canonical_program(root)
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    episodes = []
    total_evaluations = 0
    try:
        for seed in SEEDS:
            pairs = []
            for sample_index in range(DEMOS + QUERIES):
                grid = module.generate(seed, sample_index, difficulty="medium")
                errors = module.self_check(grid)
                if errors:
                    raise AssertionError(f"self_check rejected seed={seed} sample={sample_index}: {errors}")
                output = apply(program, grid)
                total_evaluations += 1
                mirror = module.rule_mirror(grid)
                if mirror != output:
                    raise AssertionError(f"Python mirror diverged from Racket at seed={seed} sample={sample_index}")
                pairs.append({"input": grid, "output": output})
            demos = pairs[:DEMOS]
            query_records = []
            for query_index, pair in enumerate(pairs[DEMOS:]):
                findings = module.lesson_identifiable(demos, pair)
                rival_status = {}
                for name, rival in module.LESSON_COMPETITORS.items():
                    disagreements = [
                        index
                        for index, demo in enumerate(demos)
                        if rival(demo["input"]) != demo["output"]
                    ]
                    rival_status[name] = {
                        "refuted_by_demo_indices": disagreements,
                        "survives_demos": not disagreements,
                        "changes_query": rival(pair["input"]) != pair["output"],
                    }
                query_records.append(
                    {
                        "query_index": query_index,
                        "input_sha256": digest(pair["input"]),
                        "output_sha256": digest(pair["output"]),
                        "shape": [len(pair["input"]), len(pair["input"][0])],
                        "lesson_findings": findings,
                        "rivals": rival_status,
                    }
                )
            episodes.append(
                {
                    "seed": seed,
                    "demo_input_sha256": [digest(pair["input"]) for pair in demos],
                    "queries": query_records,
                }
            )
    finally:
        bridge.close()

    findings = [
        {"seed": episode["seed"], "query_index": query["query_index"], "reasons": query["lesson_findings"]}
        for episode in episodes
        for query in episode["queries"]
        if query["lesson_findings"]
    ]
    result = {
        "schema": "arcpuzzles-bounded-peer-learnability-v1",
        "task_id": TASK_ID,
        "source_path": source_path.relative_to(root).as_posix(),
        "source_sha256": source_sha256,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "racket": identity,
        "scope": {
            "seeds": list(SEEDS),
            "demonstrations_per_episode": DEMOS,
            "queries_per_episode": QUERIES,
            "rivals": sorted(module.LESSON_COMPETITORS),
        },
        "protected_racket_evaluations": total_evaluations,
        "episodes": episodes,
        "finding_count": len(findings),
        "findings": findings,
        "verdict": "bounded_no_finding" if not findings else "finding",
        "limits": "Finite declared rivals and two seeds only; this is not a uniqueness proof or production approval.",
    }
    out = here.with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "finding_count": len(findings), "racket_evaluations": total_evaluations}, sort_keys=True))


if __name__ == "__main__":
    main()
