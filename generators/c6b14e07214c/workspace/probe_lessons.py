#!/usr/bin/env python3
"""Source-bound, relocated finite-rival lesson census (offline reviewer tool).

Run from the library with its normal Python/Racket environment. Defaults check
100 seeds x every declared cyclic start x each difficulty band. Labels come
only from the selected canonical Racket program; they are reviewer evidence,
NOT model-visible challenges. A nonzero exit retains the complete report.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from collections import Counter
from typing import Any, Callable


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def classify_lesson(demos: list[dict], query: dict, rivals: dict[str, Callable]) -> dict:
    """Classify the supplied names, not a copied list of known competitor names."""
    if not demos or any("input" not in pair or "output" not in pair for pair in [*demos, query]):
        raise ValueError("nonempty demonstrations and offline authoritative outputs are required")
    result = {"refuted": [], "answer_equivalent": [], "query_changing": []}
    for name, rival in sorted(rivals.items()):
        if not all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in demos):
            result["refuted"].append(name)
        elif rival(copy.deepcopy(query["input"])) == query["output"]:
            result["answer_equivalent"].append(name)
        else:
            result["query_changing"].append(name)
    return result


def _is_clean(value: Any) -> bool:
    return value if isinstance(value, bool) else isinstance(value, (list, tuple)) and not value


def _worker(request: dict) -> int:
    # This branch runs entirely inside a copied, independent runtime.
    from puzzle_generators import runner
    from arcpuzzles_worker import canonical_bundle
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

    tid = request["task_id"]
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{tid}.generator")
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    for name, fn in shortcuts.items():
        if name in rivals and rivals[name] is not fn:
            raise ValueError(f"conflicting rival implementations for {name}")
        rivals[name] = fn
    if not rivals:
        raise ValueError("no declared LESSON_COMPETITORS or CANONICAL_SHORTCUTS")
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", {})
    claims = getattr(gen, "WITNESS_RIVALS", {})
    semantic_rivals = getattr(gen, "SEMANTIC_RIVALS", {})
    starts = request["starts"]
    if starts is None:
        starts = list(range(len(getattr(gen, "SCHEDULE_PROFILES", (0,)))))
    demos_n = request["demos"] or getattr(gen, "EXAMPLES_NEEDED", 3)
    report = {
        "schema": "source-bound-lesson-probe-v1", "source": request["source"],
        "runtime_directory": str(Path.cwd()), "authority": "selected canonical Racket; no Python labels",
        "sampler": {"name": "direct generate with fixed seed and indexed draws; no retries",
                    "seeds_per_band": request["seeds_per_band"], "bands": ["easy", "medium", "hard"],
                    "seed_definition": "first 12 hex of sha256('review-lessons:v1:<task>:<band>:<case>')",
                    "case_range": [0, request["seeds_per_band"]-1], "base_index": "11 * case",
                    "cyclic_start_offsets": starts, "within_lesson_step": request["sample_step"],
                    "n_demos": demos_n, "n_queries": 1,
                    "overlap": "windows within one seed overlap; unique requests and input hashes counted separately",
                    "runner_pair_validation": True, "overrides": request["overrides"]},
        "canonical": {}, "rivals": sorted(rivals), "bands": {}, "witnesses": {},
        "counterexamples": {}, "failures": [], "ledger": [],
    }
    if canonical_rule_hash(tid) != request["source"]["rule_hash"]:
        raise ValueError("selected canonical rule hash changed during staging")
    bundle = canonical_bundle(runner, tid, gen)
    bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    all_hashes: set[str] = set()
    unique_requests = 0
    witness_counts = {name: Counter() for name in witnesses}
    witness_examples = {}
    try:
        canonical = canonical_pairs(tid)
        usable = [pair for pair in canonical if pair.get("output") is not None]
        report["canonical"] = {"pairs": len(canonical), "usable_pairs": len(usable), "shortcuts": {}}
        for index, pair in enumerate(usable):
            actual = runner._apply_rule(bridge, name, copy.deepcopy(pair["input"]))
            reasons = gen.self_check(copy.deepcopy(pair["input"]))
            if actual != pair["output"] or not _is_clean(reasons):
                report["failures"].append({"kind": "canonical", "index": index,
                                            "validator": reasons, "input": pair["input"],
                                            "actual": actual, "expected": pair["output"]})
        for short, fn in shortcuts.items():
            fits = sum(fn(copy.deepcopy(p["input"])) == p["output"] for p in usable)
            report["canonical"]["shortcuts"][short] = {"fits": fits, "denominator": len(usable)}
            if not usable or fits != len(usable):
                report["failures"].append({"kind": "declared_shortcut_not_canonical_fitting", "name": short})

        for band in report["sampler"]["bands"]:
            counters = Counter()
            refuted = Counter({key: 0 for key in rivals})
            equivalent = Counter({key: 0 for key in rivals})
            changing = Counter({key: 0 for key in rivals})
            profiles = Counter()
            band_hashes: set[str] = set()
            for case in range(request["seeds_per_band"]):
                seed = int(hashlib.sha256(f"review-lessons:v1:{tid}:{band}:{case}".encode()).hexdigest()[:12], 16)
                cache: dict[int, dict] = {}

                def pair_at(index: int) -> dict:
                    nonlocal unique_requests
                    if index in cache:
                        return cache[index]
                    grid = gen.generate(seed, index, difficulty=band, **request["overrides"])
                    actual = runner._apply_rule(bridge, name, copy.deepcopy(grid))
                    reasons = gen.self_check(copy.deepcopy(grid))
                    strict = getattr(gen, "strict_canonical_like", gen.self_check)(copy.deepcopy(grid))
                    pair_error = runner._validate_pair(grid, actual, allow_identity_output=bool(getattr(gen, "ALLOW_IDENTITY_OUTPUT", False)))
                    provenance = {"difficulty": band, "seed": seed, "sample_index": index,
                                  "overrides": request["overrides"], "input_sha256": digest(grid),
                                  "output_sha256": digest(actual)}
                    if not _is_clean(reasons) or not _is_clean(strict) or pair_error:
                        report["failures"].append({"kind": "generated_domain_or_pair", **provenance,
                            "self_check": reasons, "strict": strict, "pair_error": pair_error,
                            "input": grid, "actual": actual})
                    else:
                        counters["strict_clean_unique_requests"] += 1
                    counters["unique_generation_requests"] += 1
                    unique_requests += 1
                    band_hashes.add(digest(grid)); all_hashes.add(digest(grid))
                    profile = getattr(gen, "schedule_profile", lambda *a: "undeclared")(seed, index, band)
                    profiles[str(profile)] += 1
                    differences = []
                    for rival_name, rival in rivals.items():
                        rival_output = rival(copy.deepcopy(grid))
                        if rival_output != actual:
                            differences.append(rival_name)
                            report["counterexamples"].setdefault(rival_name, {
                                **provenance, "input": grid, "actual_racket_output": actual,
                                "rival_output": rival_output, "self_check": reasons,
                                "belongs_to_documented_generator_domain": not reasons})
                    for witness, predicate in witnesses.items():
                        if predicate(copy.deepcopy(grid)):
                            witness_counts[witness]["hits"] += 1
                            named = claims.get(witness, [])
                            if named:
                                witness_counts[witness]["checked"] += 1
                                holds = any(semantic_rivals[r](copy.deepcopy(grid)) != actual for r in named)
                                witness_counts[witness]["claim_holds" if holds else "claim_violated"] += 1
                                if not holds:
                                    report["failures"].append({"kind": "false_witness", "name": witness,
                                                              **provenance, "input": grid, "actual": actual})
                            witness_examples.setdefault(witness, provenance)
                    report["ledger"].append({**provenance, "profile": profile, "rivals_disagree": differences,
                                             "observed_axes": getattr(gen, "observe_overrides", lambda g: {})(grid)})
                    cache[index] = {"input": grid, "output": actual}
                    return cache[index]

                for offset in starts:
                    start = 11*case + offset
                    indices = [start + slot*request["sample_step"] for slot in range(demos_n+1)]
                    counters["lessons_requested"] += 1
                    try:
                        pairs = [pair_at(index) for index in indices]
                        classified = classify_lesson(pairs[:-1], pairs[-1], rivals)
                        counters["lessons_materialized"] += 1
                        if len({digest(p["input"]) for p in pairs}) != len(pairs):
                            counters["duplicate_input_lessons"] += 1
                            report["failures"].append({"kind": "duplicate_lesson", "band": band,
                                                       "seed": seed, "sample_indices": indices})
                        for key, counts in (("refuted", refuted), ("answer_equivalent", equivalent), ("query_changing", changing)):
                            counts.update(classified[key])
                        hook = getattr(gen, "lesson_identifiable", None)
                        reasons = hook(copy.deepcopy(pairs[:-1]), copy.deepcopy(pairs[-1])) if hook else None
                        if classified["query_changing"]:
                            counters["query_ambiguous_lessons"] += 1
                            report["failures"].append({"kind": "query_changing_survivor", "band": band,
                                "seed": seed, "sample_indices": indices, "survivors": classified["query_changing"],
                                "hook_reasons": reasons, "demos": pairs[:-1], "query": pairs[-1]})
                        if hook and bool(reasons) != bool(classified["query_changing"]):
                            counters["hook_classification_disagreements"] += 1
                            report["failures"].append({"kind": "hook_disagreement", "band": band,
                                                       "seed": seed, "sample_indices": indices, "reasons": reasons})
                    except Exception as exc:
                        counters["lesson_errors"] += 1
                        report["failures"].append({"kind": "lesson_error", "band": band,
                                                   "seed": seed, "sample_indices": indices,
                                                   "error": f"{type(exc).__name__}: {exc}"})
            report["bands"][band] = {**dict(counters), "unique_inputs": len(band_hashes),
                "profiles_over_unique_requests": dict(profiles), "refuted_by_demos": dict(refuted),
                "answer_equivalent_survivors": dict(equivalent), "query_changing_survivors": dict(changing)}
            print(f"{band}: {counters['lessons_materialized']} lessons, {len(band_hashes)} unique inputs, "
                  f"{counters['query_ambiguous_lessons']} query-ambiguous", flush=True)
    finally:
        bridge.shutdown()
    report["witnesses"] = {key: {**dict(value), "example": witness_examples.get(key)} for key, value in witness_counts.items()}
    report["unique_generation_requests"] = unique_requests
    report["unique_inputs"] = len(all_hashes)
    report["lessons_total"] = sum(b.get("lessons_materialized", 0) for b in report["bands"].values())
    report["passed"] = not report["failures"]
    report["scope"] = "finite declared rivals only; no universal induction or training-admission claim"
    Path(request["out"]).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "lessons": report["lessons_total"],
                      "unique_inputs": report["unique_inputs"], "failures": len(report["failures"])}))
    return 0 if report["passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", default="c6b14e07214c")
    parser.add_argument("--seeds-per-band", type=int, default=100)
    parser.add_argument("--demos", type=int)
    parser.add_argument("--starts", help="comma-separated sample-index offsets; default: all declared cyclic starts")
    parser.add_argument("--sample-step", type=int, default=1)
    parser.add_argument("--overrides", default="{}", help="JSON exact overrides; may disable default teaching schedule")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return _worker(json.loads(args.worker.read_text()))
    if args.out is None or args.seeds_per_band < 1 or args.sample_step < 1 or (args.demos is not None and args.demos < 1):
        parser.error("--out and positive count/step/demos are required")
    out = args.out.resolve()
    if out.exists():
        parser.error(f"refusing to overwrite retained evidence: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    root = next((p for p in Path(__file__).resolve().parents if (p / "catalog/puzzles.jsonl").is_file()), None)
    if root is None:
        parser.error("run this source copy from inside the ARCpuzzles library")
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    catalog = Catalog(root)
    source = catalog.describe(args.task_id)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-lesson-review-") as tmp:
        stage = Path(tmp)
        prepare_runtime(catalog, stage, args.task_id)
        script = stage / "lesson_probe.py"
        shutil.copy2(__file__, script)
        request = {"task_id": args.task_id, "seeds_per_band": args.seeds_per_band, "demos": args.demos,
                   "starts": [int(v) for v in args.starts.split(",")] if args.starts else None,
                   "sample_step": args.sample_step, "overrides": json.loads(args.overrides), "out": str(out),
                   "source": {"task_id": args.task_id, "generator_sha256": source["generator_sha256"],
                              "rule_hash": source["rule_hash"], "generator_path": source["generator"],
                              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
        (stage / "probe_request.json").write_text(json.dumps(request))
        command = [sys.executable, "-E", "-s", str(script), "--worker", "probe_request.json"]
        result = run_process(command, stage, timeout=3600, on_output=lambda text: print(text, end="", flush=True))
        if not out.exists():
            out.write_text(json.dumps({"passed": False, "source": request["source"], "runtime_directory": str(stage),
                                      "worker_failure": result}, indent=2) + "\n")
        if Catalog(root).describe(args.task_id)["generator_sha256"] != source["generator_sha256"]:
            raise RuntimeError("source changed during probe; retained report is for the earlier snapshot")
        return result["exit_code"] if result["exit_code"] is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
