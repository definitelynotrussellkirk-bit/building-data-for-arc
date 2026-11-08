"""Build compact training lessons that refute a declared finite rival registry.

The selector accepts query INPUTS only. It never uses query correctness to choose
or reject demonstrations. Labels must already have been executed by Racket; the
CLI verifies the source report, corpus hash, and generator hash before use.
This is research tooling, not approval or a universal identifiability guarantee.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


class CoverageError(ValueError):
    """The candidate demonstrations cannot meet the stated rival obligation."""


def minimum_cover(coverage, target, *, max_demos=5):
    """Exact set cover over a small rival registry; minimize demos, then indices.

    Dynamic programming costs O(candidates * 2**rivals). This is intentionally
    bounded to 16 rivals so a review helper cannot allocate an unbounded state
    space. The six-rival task needs only 64 states.
    """
    if type(max_demos) is not int or max_demos < 1:
        raise ValueError("max_demos must be a positive integer")
    names = sorted(set(target))
    if not names:
        raise ValueError("at least one rival is required")
    if len(names) > 16:
        raise ValueError("exact-cover registry is limited to 16 rivals")
    targets = set(names)
    covered = set().union(*coverage) if coverage else set()
    missing = targets - covered
    if missing:
        raise CoverageError(f"missing rival witnesses: {sorted(missing)}")
    bits = {name: 1 << index for index, name in enumerate(names)}
    full = (1 << len(names)) - 1
    dp = {0: ()}
    for index, hits in enumerate(coverage):
        mask = sum(bits[name] for name in targets.intersection(hits))
        for seen, chosen in list(dp.items()):
            combined = seen | mask
            candidate = chosen + (index,)
            if len(candidate) > max_demos:
                continue
            old = dp.get(combined)
            if old is None or (len(candidate), candidate) < (len(old), old):
                dp[combined] = candidate
    if full not in dp:
        raise CoverageError(f"demo budget {max_demos} cannot cover all named rivals")
    return list(dp[full])


def _key(grid):
    return json.dumps(grid, separators=(",", ":"))


def select_demos(demos, rivals, *, query_inputs, max_demos=5):
    """Return original candidate indices; query outputs are not an input."""
    forbidden = {_key(grid) for grid in query_inputs}
    seen = {}
    eligible, coverage = [], []
    for index, demo in enumerate(demos):
        key, output_key = _key(demo["input"]), _key(demo["output"])
        if key in seen and seen[key] != output_key:
            raise ValueError("duplicate input has inconsistent labels")
        duplicate = key in seen
        seen[key] = output_key
        if duplicate or key in forbidden:
            continue
        hits = {name for name, rival in rivals.items()
                if rival(copy.deepcopy(demo["input"])) != demo["output"]}
        eligible.append(index)
        coverage.append(hits)
    return [eligible[index] for index in minimum_cover(coverage, set(rivals), max_demos=max_demos)]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="Racket review_probe main report")
    parser.add_argument("--phase", default="final")
    parser.add_argument("--pool-size", type=int, default=20, help="Each disjoint pool reserves its last row as query")
    parser.add_argument("--max-demos", type=int, default=5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.pool_size < 2:
        parser.error("--pool-size must be >=2")
    if args.out.exists():
        parser.error("output directory already exists; never overwrite evidence")
    source = json.loads(args.report.read_text())
    if source.get("failures"):
        raise ValueError("source Racket report contains failures")
    variant = source["variants"][args.phase]
    cases_path = args.report.parent / source["cases_file"]
    if _sha(cases_path) != source["cases_sha256"]:
        raise ValueError("source corpus hash mismatch")
    home = Path(__file__).resolve().parents[1]
    if _sha(home / "generator.py") != variant["generator_sha256"]:
        raise ValueError("generator source changed since Racket census")
    for root in home.parents:
        if (root / "shared/runtime/puzzle_generators/base.py").is_file():
            sys.path.insert(0, str(root / "shared/runtime"))
            break
    spec = importlib.util.spec_from_file_location("lesson_generator", home / "generator.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rivals = gen.SEMANTIC_RIVALS
    cases = [json.loads(line) for line in cases_path.open()]
    cases = [case for case in cases if case.get("phase") == args.phase]
    # Deduplicate globally before partitioning: no grid crosses lesson boundaries.
    unique, deduped, labels = set(), [], {}
    for case in cases:
        key = _key(case["input"])
        value = _key(case["output"])
        if key in labels and labels[key] != value:
            raise ValueError("source corpus has inconsistent labels")
        labels[key] = value
        if key not in unique:
            unique.add(key)
            deduped.append(case)
    args.out.mkdir(parents=True)
    public, private, metadata, rejected = [], [], [], []
    dropped_tail = 0
    for start in range(0, len(deduped), args.pool_size):
        pool = deduped[start:start + args.pool_size]
        if len(pool) < args.pool_size:
            dropped_tail += len(pool)
            break
        candidates, query = pool[:-1], pool[-1]
        try:
            indices = select_demos(candidates, rivals, query_inputs=[query["input"]], max_demos=args.max_demos)
        except CoverageError as exc:
            rejected.append({"pool_start": start, "reason": str(exc),
                             "candidate_sources": [{k: x[k] for k in ("band", "seed", "sample_index")} for x in candidates]})
            continue
        selected = [candidates[index] for index in indices]
        lesson_id = f"{gen.TASK_ID}-witness-{start // args.pool_size:04d}"
        public.append({"id": lesson_id,
                       "train": [{"input": x["input"], "output": x["output"]} for x in selected],
                       "test": [{"input": query["input"]}]})
        # Query labels are read for export only after selection has completed.
        private.append({"id": lesson_id, "test": [{"output": query["output"]}]})
        refuted = {name: [j for j, demo in enumerate(selected)
                         if rival(copy.deepcopy(demo["input"])) != demo["output"]]
                   for name, rival in rivals.items()}
        if not all(refuted.values()):
            raise AssertionError("selector returned a lesson missing a rival witness")
        metadata.append({"id": lesson_id, "pool_start": start, "candidate_indices": indices,
                         "candidate_count": len(candidates), "refuted_by_demo": refuted,
                         "demo_sources": [{k: x[k] for k in ("band", "seed", "sample_index")} for x in selected],
                         "query_source": {k: query[k] for k in ("band", "seed", "sample_index")},
                         "query_output_used_for_selection": False})
    outputs = {"challenges.jsonl": public, "private_labels.jsonl": private, "provenance.jsonl": metadata,
               "rejections.jsonl": rejected}
    for name, rows in outputs.items():
        (args.out / name).write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows))
    result = {
        "schema": "arcpuzzles-witness-lessons-v1", "task_id": gen.TASK_ID,
        "research_only": True, "training_admitted": False,
        "source_report_sha256": _sha(args.report), "source_corpus_sha256": _sha(cases_path),
        "generator_sha256": variant["generator_sha256"], "tool_sha256": _sha(__file__),
        "rivals": sorted(rivals), "candidate_pool_size": args.pool_size - 1,
        "query_count_per_lesson": 1, "max_demos": args.max_demos,
        "input_rows": len(cases), "unique_input_rows": len(deduped), "dropped_tail_rows": dropped_tail,
        "accepted_lessons": len(public), "rejected_pools": len(rejected),
        "selected_demo_count": sum(len(x["train"]) for x in public),
        "demo_count_histogram": {str(n): sum(len(x["train"]) == n for x in public) for n in range(1, args.max_demos+1)},
        "query_changing_named_rivals_surviving_demos": 0,
        "limitation": "Only the declared finite registry is refuted. Not universal rule identification or model accuracy.",
        "file_sha256": {name: _sha(args.out / name) for name in outputs},
    }
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    # Failed pools are evidence, not silently removed while claiming full success.
    return 1 if rejected or not public else 0


if __name__ == "__main__":
    raise SystemExit(main())
