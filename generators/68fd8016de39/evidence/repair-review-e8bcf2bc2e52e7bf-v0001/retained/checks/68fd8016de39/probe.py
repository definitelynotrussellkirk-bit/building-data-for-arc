"""Bounded, source-pinned default-lesson overlap-priority probe.

From the packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/68fd8016de39/probe.py \
    --out ../checks/68fd8016de39/evidence.json

The small Python prescreen only chooses candidate seeds. Findings require the
actual Catalog.generate default lesson and protected replay of both programs.
All labels and both interpretations remain private authoring evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import find_root, load_selected_generator

TASK = "68fd8016de39"
GENERATOR_SHA256 = "316d18d5363dadb62bbe7f3abbee09201ebd382ff2cb6371a0a34627bf994e72"
PROGRAM_SHA256 = "afb832c50702b08be9d6d15a9ebac8bc5e1bb0e0d5eac0b12cac450f287a4b96"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mirror(grid, reverse=False):
    """Exact sign-step spans of this authority; seed selection, not label proof."""
    positions = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                positions.setdefault(color, []).append((row, col))
    result = [[0 for _ in grid[0]] for _ in grid]
    for color in sorted(positions, reverse=reverse):
        points = positions[color]
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(points)
        dr, dc = (r2 > r1) - (r2 < r1), (c2 > c1) - (c2 < c1)
        for step in range(max(abs(r2-r1), abs(c2-c1)) + 1):
            row, col = r1 + step*dr, c1 + step*dc
            if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                result[row][col] = color
    return result


def run(output, seeds=32):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError("Choose a new evidence path")
    if type(seeds) is not int or not 1 <= seeds <= 32:
        raise ValueError("seeds must be an integer in 1..32")
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != GENERATOR_SHA256:
        raise ValueError("Generator source changed; revise the probe explicitly")
    catalog = Catalog(root)
    description = catalog.describe(TASK)
    programs = {row["program_solution"] for row in catalog.get(TASK)["variants"]}
    if len(programs) != 1:
        raise ValueError("Canonical program is not unique")
    correct = next(iter(programs))
    if sha(correct.encode()) != PROGRAM_SHA256:
        raise ValueError("Canonical program changed; revise the probe explicitly")
    needle = "(in-list (pair-groups g))"
    if correct.count(needle) != 1:
        raise ValueError("Expected one explicit color-paint order")
    rival = correct.replace(needle, "(in-list (reverse (pair-groups g)))")
    prescreen, actual, witness = [], [], None
    for seed in range(seeds):
        # The production default resolves to three demos; no sampler changes.
        inputs = [module.generate(seed, index) for index in range(4)]
        demo_fit = all(mirror(grid) == mirror(grid, True) for grid in inputs[:3])
        query_disagrees = mirror(inputs[3]) != mirror(inputs[3], True)
        prescreen.append({"seed": seed, "demo_fit": demo_fit, "query_disagrees": query_disagrees})
        if not demo_fit or not query_disagrees:
            continue
        episode = catalog.generate(TASK, count=1, seed=seed, allow_unapproved=True, timeout=60)[0]
        if episode["program"] != correct or len(episode["train"]) != 3 or len(episode["test"]) != 1:
            raise ValueError("Catalog default program/count contract changed")
        runtime = root / "shared/runtime"
        rows = []
        with _local_imports(runtime, runtime):
            apply, identity, bridge = _real_evaluator(runtime)
            try:
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        canonical_output = _grid(apply(correct, pair["input"]))
                        rival_output = _grid(apply(rival, pair["input"]))
                        if canonical_output != pair["output"]:
                            raise ValueError("Protected replay disagrees with native label")
                        rows.append({"split": split, "pair_index": index,
                                     "correct_output": canonical_output, "rival_output": rival_output,
                                     "rival_matches": canonical_output == rival_output})
            finally:
                bridge.close()
        all_demos_fit = all(row["rival_matches"] for row in rows if row["split"] == "train")
        differs = [row for row in rows if row["split"] == "test" and not row["rival_matches"]]
        actual.append({"seed": seed, "all_demos_fit": all_demos_fit,
                       "queries_disagreeing": len(differs), "racket_evaluations": 2*len(rows)})
        if all_demos_fit and differs:
            witness = {"seed": seed, "original_episode": episode, "racket": identity,
                       "racket_evaluations": 2*len(rows), "replay": rows,
                       "alternative_answer_stream": {
                           "status": "research_candidate_only", "training_admitted": False,
                           "reason": "Both executed rules fit every original visible demonstration.",
                           "query_predictions": [{"pair_index": row["pair_index"],
                                                  "canonical": row["correct_output"],
                                                  "candidate_alternative": row["rival_output"]}
                                                 for row in differs]}}
            break
    result = {
        "schema": "arcpuzzles-peer-default-lesson-probe-v1", "task_id": TASK,
        "classification": "default_lesson_ambiguity" if witness else "no_finding_in_bounded_scope",
        "source": {"path": source.relative_to(root).as_posix(), "sha256": source_sha,
                   "rule_hash": description["rule_hash"], "program_sha256": PROGRAM_SHA256,
                   "probe_sha256": sha(Path(__file__).read_bytes())},
        "generation": {"api": "Catalog.generate", "count": 1, "n_train": "omitted; native default",
                       "n_test": "omitted; native default", "difficulty": "omitted",
                       "allow_unapproved": True, "catalog_approved": description["approved"],
                       "catalog_train_safety": description["train_safety"]},
        "correct_program": correct, "rival_program": rival, "rival_program_sha256": sha(rival.encode()),
        "rival": "Same canonical sign-step spans; reverse color-paint order so lower color wins overlaps.",
        "python_prescreen": prescreen, "actual_default_lessons": actual, "witness": witness,
        "remaining_repair": "Teach overlap precedence with a distinguishing demonstration before accepting a query that depends on it; preserve this original lesson separately for optional ambiguity research.",
        "limits": "One declared order rival and a bounded deterministic seed prescreen. Only retained actual lessons and protected replay count as evidence; no full battery, universal uniqueness claim, source repair, approval, or training admission.",
        "training_admitted": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write((json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return {"classification": result["classification"], "seeds_prescreened": len(prescreen),
            "actual_lessons": len(actual), "witness_seed": witness["seed"] if witness else None,
            "racket_evaluations": sum(row["racket_evaluations"] for row in actual),
            "evidence": str(output.resolve()), "evidence_sha256": sha(output.read_bytes())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    print(json.dumps(run(args.out, args.seeds), indent=2, sort_keys=True))
