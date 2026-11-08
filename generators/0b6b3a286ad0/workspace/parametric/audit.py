"""Private, bounded demo-only self-review for the two-stage lookup family.

Run through this packet's review.py launcher.  The ordinary sampler probe uses
independent Python rules.  The two requested seed lessons additionally execute
the chosen rule, an independent exact rule, and every active rival on all visible
demonstrations through the same-checkout protected Racket bridge.  Only rivals
that fit those demonstrations are then considered against the queries.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


TASK = "0b6b3a286ad0"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _load(path, prefix):
    name = prefix + hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(value):
    if isinstance(value, str):
        raw = value.encode()
    elif isinstance(value, bytes):
        raw = value
    else:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _snapshot():
    candidates = [ROOT / "generators" / TASK / "generator.py"]
    candidates.extend(path for path in HERE.iterdir()
                      if path.is_file() and (path.suffix in (".py", ".rkt")
                                             or path.name == "promotion.json"))
    return {str(path.relative_to(ROOT)): _sha(path.read_bytes())
            for path in sorted(candidates)}


def _episode(adapter, rivals, seed, depth, demos):
    settings = {"lookup_depth": depth}
    episode = adapter.generate(seed, settings, demos=demos, queries=4)
    if episode.get("program_solution") != adapter.program(settings):
        raise AssertionError("Returned program differs from the fixed requested setting")
    if len(episode["train"]) != demos or len(episode["test"]) != 4:
        raise AssertionError("Sampler returned an incorrect demonstration/query count")
    hashes = []
    for split in ("train", "test"):
        for pair in episode[split]:
            _grid(pair["input"])
            _grid(pair["output"])
            hashes.append(_sha(pair["input"]))
            predicted = rivals.solve(pair["input"], depth, "exact")
            if predicted != pair["output"]:
                raise AssertionError("Independent exact mirror disagrees with a claim label")
    if len(set(hashes)) != len(hashes):
        raise AssertionError("Episode repeats a demonstration or query input")
    return episode


def _demo_only(rivals, episode, depth):
    survivors, harmful = [], []
    for name in rivals.names(depth):
        fits = all(rivals.solve(pair["input"], depth, name) == pair["output"]
                   for pair in episode["train"])
        if fits:
            survivors.append(name)
            disagreements = [index for index, pair in enumerate(episode["test"])
                             if rivals.solve(pair["input"], depth, name) != pair["output"]]
            if disagreements:
                harmful.append({"rival": name, "query_indices": disagreements})
    return survivors, harmful


def _sampler(adapter, rivals, seeds):
    report = {"requests": [], "failures": [], "racket_executed": False,
              "claim_check": "Independent Python exact implementation, not authoritative execution"}
    matched = {}
    for seed in seeds:
        for demos in range(3, 7):
            for depth in (1, 2):
                row = {"seed": seed, "settings": {"lookup_depth": depth},
                       "demos": demos, "queries": 4}
                try:
                    episode = _episode(adapter, rivals, seed, depth, demos)
                    survivors, harmful = _demo_only(rivals, episode, depth)
                    input_hashes = {split: [_sha(pair["input"]) for pair in episode[split]]
                                    for split in ("train", "test")}
                    key = (seed, demos)
                    if key in matched and input_hashes != matched[key]:
                        raise AssertionError("Shared input seed produces setting-dependent inputs")
                    matched[key] = input_hashes
                    prefix_key = (seed, "prefix")
                    prefixes = {"train": input_hashes["train"][:3], "test": input_hashes["test"]}
                    if prefix_key in matched and prefixes != matched[prefix_key]:
                        raise AssertionError("Demo count changed the core teaching prefix or query inputs")
                    matched[prefix_key] = prefixes
                    row.update(status="pass" if not harmful else "teaching_failure",
                               input_sha256=input_hashes, surviving_rivals=survivors,
                               harmful_survivors=harmful,
                               shapes={split: [[len(pair["input"]), len(pair["input"][0])]
                                               for pair in episode[split]]
                                       for split in ("train", "test")})
                    if harmful:
                        report["failures"].append(row)
                except Exception as exc:
                    row.update(status="error", error=type(exc).__name__, message=str(exc))
                    report["failures"].append(row)
                report["requests"].append(row)
    report["request_count"] = len(report["requests"])
    report["success_count"] = sum(row["status"] == "pass" for row in report["requests"])
    report["failure_count"] = len(report["failures"])
    return report


def _protected(adapter, rivals, seeds):
    result = {"episodes": [], "rival_programs": {}, "minimal_eliminators": {},
              "failures": [], "racket_evaluations": 0, "cache_hits": 0}
    runtime = ROOT / "shared" / "runtime"
    cache = {}
    with _local_imports(runtime, HERE):
        execute, identity, bridge = _real_evaluator(runtime)
        result["racket"] = identity

        def apply(program, grid):
            key = (_sha(program), _sha(grid))
            if key not in cache:
                cache[key] = _grid(execute(program, grid))
                result["racket_evaluations"] += 1
            else:
                result["cache_hits"] += 1
            return cache[key]

        try:
            for seed in seeds:
                for depth in (1, 2):
                    episode = _episode(adapter, rivals, seed, depth, 3)
                    chosen = adapter.program({"lookup_depth": depth})
                    independent = rivals.program("exact", depth)
                    detail = {"seed": seed, "settings": {"lookup_depth": depth},
                              "program": chosen, "independent_program": independent,
                              "train": episode["train"], "test": episode["test"],
                              "rivals": {}, "surviving_rivals": [], "harmful_survivors": []}
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = apply(chosen, pair["input"])
                            independent_actual = apply(independent, pair["input"])
                            if actual != pair["output"] or independent_actual != actual:
                                raise AssertionError(f"Racket exact-label disagreement: {seed}/{depth}/{split}/{index}")
                    for name in rivals.names(depth):
                        code = rivals.program(name, depth)
                        digest = _sha(code)
                        result["rival_programs"][digest] = code
                        outputs = [apply(code, pair["input"]) for pair in episode["train"]]
                        predicted = [rivals.solve(pair["input"], depth, name) for pair in episode["train"]]
                        if outputs != predicted:
                            raise AssertionError(f"Independent Python/Racket rival mismatch: {seed}/{depth}/{name}")
                        disagrees = [index for index, (output, pair) in enumerate(zip(outputs, episode["train"]))
                                     if output != pair["output"]]
                        record = {"program_sha256": digest,
                                  "demonstration_output_sha256": [_sha(output) for output in outputs],
                                  "eliminating_demo_indices": disagrees}
                        if disagrees:
                            witness_key = f"depth{depth}:{name}"
                            if witness_key not in result["minimal_eliminators"]:
                                index = disagrees[0]
                                pair = episode["train"][index]
                                result["minimal_eliminators"][witness_key] = {
                                    "seed": seed, "settings": {"lookup_depth": depth},
                                    "demo_index": index, "input_sha256": _sha(pair["input"]),
                                    "selected_output_sha256": _sha(pair["output"]),
                                    "rival_output": outputs[index], "rival_program_sha256": digest}
                        else:
                            detail["surviving_rivals"].append(name)
                            query_outputs = [apply(code, pair["input"]) for pair in episode["test"]]
                            query_claims = [rivals.solve(pair["input"], depth, name) for pair in episode["test"]]
                            if query_outputs != query_claims:
                                raise AssertionError(f"Rival query Python/Racket mismatch: {seed}/{depth}/{name}")
                            query_disagreements = [index for index, (output, pair)
                                                   in enumerate(zip(query_outputs, episode["test"]))
                                                   if output != pair["output"]]
                            record.update(query_output_sha256=[_sha(output) for output in query_outputs],
                                          disagreeing_query_indices=query_disagreements)
                            if query_disagreements:
                                failure = {"seed": seed, "settings": {"lookup_depth": depth},
                                           "rival": name, "query_indices": query_disagreements}
                                detail["harmful_survivors"].append(failure)
                                result["failures"].append(failure)
                        detail["rivals"][name] = record
                    if depth == 2 and "causal_case" not in result:
                        for pair in episode["train"]:
                            counterfactual = rivals.program("wrong_intermediate", depth)
                            counterfactual_output = apply(counterfactual, pair["input"])
                            if counterfactual_output != pair["output"]:
                                facts = rivals.parse(pair["input"])
                                branch = 1 if rivals.has_match(facts["query"], facts["key1"]) else 2
                                result["causal_case"] = {
                                    "input": pair["input"], "settings": {"lookup_depth": depth},
                                    "intermediate_value": {"panel": "value" + str(branch),
                                                           "grid": facts["value" + str(branch)]},
                                    "program": chosen, "output": pair["output"],
                                    "counterfactual_program": counterfactual,
                                    "counterfactual_output": counterfactual_output,
                                    "ablation": "wrong_intermediate"}
                                break
                    result["episodes"].append(detail)
        finally:
            bridge.close()
    result["failure_count"] = len(result["failures"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sampler-count", type=int, default=8)
    parser.add_argument("--racket-seed", type=int, action="append")
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("Refusing an existing evidence destination")
    if not 1 <= args.sampler_count <= 8:
        raise ValueError("Sampler count must be within the assigned bounded range 1..8")
    seeds = args.racket_seed or [0, 17]
    if len(seeds) > 2 or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("At most two nonnegative protected seeds are supported")
    started = time.monotonic()
    snapshot = _snapshot()
    result = {"schema": "arcpuzzles-private-lookup-self-review-v1", "task_id": TASK,
              "source_sha256": snapshot, "command": list(sys.argv),
              "sampling_repairs": {
                  "color_frequency": "The original single-target construction made the true key color consistently rarer than the decoy key color. A source-bound probe on the retained seed 0/17 lessons found the minority-color rule agreed with all 28 labels. The repaired teaching query repeats its true key five times, and a selected value repeats its true key twice, to distinguish template matching from frequency at each hop without adding demonstrations.",
                  "query_order": "A seed-deterministic permutation shared across settings varies which of the four query roles appears first while keeping demo/query counts independent.",
                  "before_evidence": "checks/0b6b3a286ad0/self-review.json",
                  "shortcut_evidence": "checks/0b6b3a286ad0/minority-shortcut.json"},
              "limits": "Bounded finite-rival review; no universal uniqueness, owner acceptance, or training admission."}
    code = 0
    try:
        rivals = _load(HERE / "rivals.py", "_independent_lookup_rivals_")
        adapter = _load(HERE / "adapter.py", "_audited_lookup_adapter_")
        result["rival_descriptions"] = rivals.DESCRIPTIONS
        result["sampler"] = _sampler(adapter, rivals, range(args.sampler_count))
        result["protected"] = _protected(adapter, rivals, seeds)
        if snapshot != _snapshot():
            raise AssertionError("Source changed during the bounded audit")
        if result["sampler"]["failure_count"] or result["protected"]["failure_count"]:
            result["status"] = "finding"
            code = 1
        else:
            result["status"] = "finite_no_finding"
    except Exception as exc:
        result.update(status="error", error=type(exc).__name__, message=str(exc))
        code = 1
    result["elapsed_seconds"] = round(time.monotonic() - started, 6)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "output": str(args.out),
                      "sampler_success_count": result.get("sampler", {}).get("success_count"),
                      "sampler_failure_count": result.get("sampler", {}).get("failure_count"),
                      "protected_failure_count": result.get("protected", {}).get("failure_count"),
                      "racket_evaluations": result.get("protected", {}).get("racket_evaluations"),
                      "error": result.get("error"), "message": result.get("message")}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
