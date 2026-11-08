"""Private, bounded demo-only self-review for the iterated rectangle-completion family.

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


TASK = "d89b3f447c00"
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


def _episode(adapter, rivals, seed, rounds, demos):
    settings = {"completion_rounds": rounds}
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
            predicted = rivals.solve(pair["input"], rounds, "exact")
            if predicted != pair["output"]:
                raise AssertionError("Independent exact mirror disagrees with a claim label")
    if len(set(hashes)) != len(hashes):
        raise AssertionError("Episode repeats a demonstration or query input")
    return episode


def _demo_only(rivals, episode, rounds):
    survivors, harmful = [], []
    for name in rivals.names(rounds):
        fits = all(rivals.solve(pair["input"], rounds, name) == pair["output"]
                   for pair in episode["train"])
        if fits:
            survivors.append(name)
            disagreements = [index for index, pair in enumerate(episode["test"])
                             if rivals.solve(pair["input"], rounds, name) != pair["output"]]
            if disagreements:
                harmful.append({"rival": name, "query_indices": disagreements})
    return survivors, harmful


def _sampler(adapter, rivals, seeds):
    report = {"requests": [], "failures": [], "racket_executed": False,
              "claim_check": "Independent Python exact implementation, not authoritative execution"}
    matched = {}
    for seed in seeds:
        for demos in range(2, 7):
            for rounds in (1, 2):
                row = {"seed": seed, "settings": {"completion_rounds": rounds},
                       "demos": demos, "queries": 4}
                try:
                    episode = _episode(adapter, rivals, seed, rounds, demos)
                    survivors, harmful = _demo_only(rivals, episode, rounds)
                    input_hashes = {split: [_sha(pair["input"]) for pair in episode[split]]
                                    for split in ("train", "test")}
                    key = (seed, demos)
                    if key in matched and input_hashes != matched[key]:
                        raise AssertionError("Shared input seed produces setting-dependent inputs")
                    matched[key] = input_hashes
                    prefix_key = (seed, "prefix")
                    prefixes = {"train": input_hashes["train"][:2], "test": input_hashes["test"]}
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


def _enabling_rectangle(original, intermediate, output):
    """Authored structural explanation beside separately executed labels."""
    for row, line in enumerate(output):
        for col, color in enumerate(line):
            if not color or color == intermediate[row][col]:
                continue
            for other_row in range(len(output)):
                for other_col in range(len(line)):
                    if other_row == row or other_col == col:
                        continue
                    support = [(row, other_col), (other_row, col), (other_row, other_col)]
                    if all(intermediate[r][c] == color for r, c in support):
                        new_support = [[r, c] for r, c in support if original[r][c] != color]
                        if new_support:
                            return {"second_round_target": [row, col, color],
                                    "supporting_corners": [list(p) for p in support],
                                    "corners_supplied_by_first_round": new_support}
    raise AssertionError("Second-round change lacks a first-round enabling rectangle")


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
                for rounds in (1, 2):
                    episode = _episode(adapter, rivals, seed, rounds, 3)
                    chosen = adapter.program({"completion_rounds": rounds})
                    independent = rivals.program("exact", rounds)
                    detail = {"seed": seed, "settings": {"completion_rounds": rounds},
                              "program": chosen, "independent_program": independent,
                              "train": episode["train"], "test": episode["test"],
                              "rivals": {}, "teaching_demos": 2, "protected_demo_labels": 3,
                              "surviving_rivals": [], "harmful_survivors": []}
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = apply(chosen, pair["input"])
                            independent_actual = apply(independent, pair["input"])
                            if actual != pair["output"] or independent_actual != actual:
                                raise AssertionError(f"Racket exact-label disagreement: {seed}/{rounds}/{split}/{index}")
                    for name in rivals.names(rounds):
                        code = rivals.program(name, rounds)
                        digest = _sha(code)
                        result["rival_programs"][digest] = code
                        outputs = [apply(code, pair["input"]) for pair in episode["train"][:2]]
                        predicted = [rivals.solve(pair["input"], rounds, name) for pair in episode["train"][:2]]
                        if outputs != predicted:
                            raise AssertionError(f"Independent Python/Racket rival mismatch: {seed}/{rounds}/{name}")
                        disagrees = [index for index, (output, pair) in enumerate(zip(outputs, episode["train"]))
                                     if output != pair["output"]]
                        record = {"program_sha256": digest,
                                  "demonstration_output_sha256": [_sha(output) for output in outputs],
                                  "eliminating_demo_indices": disagrees}
                        if disagrees:
                            witness_key = f"rounds{rounds}:{name}"
                            if witness_key not in result["minimal_eliminators"]:
                                index = disagrees[0]
                                pair = episode["train"][index]
                                result["minimal_eliminators"][witness_key] = {
                                    "seed": seed, "settings": {"completion_rounds": rounds},
                                    "demo_index": index, "input_sha256": _sha(pair["input"]),
                                    "selected_output_sha256": _sha(pair["output"]),
                                    "rival_output": outputs[index], "rival_program_sha256": digest}
                        else:
                            detail["surviving_rivals"].append(name)
                            query_outputs = [apply(code, pair["input"]) for pair in episode["test"]]
                            query_claims = [rivals.solve(pair["input"], rounds, name) for pair in episode["test"]]
                            if query_outputs != query_claims:
                                raise AssertionError(f"Rival query Python/Racket mismatch: {seed}/{rounds}/{name}")
                            query_disagreements = [index for index, (output, pair)
                                                   in enumerate(zip(query_outputs, episode["test"]))
                                                   if output != pair["output"]]
                            record.update(query_output_sha256=[_sha(output) for output in query_outputs],
                                          disagreeing_query_indices=query_disagreements)
                            if query_disagreements:
                                failure = {"seed": seed, "settings": {"completion_rounds": rounds},
                                           "rival": name, "query_indices": query_disagreements}
                                detail["harmful_survivors"].append(failure)
                                result["failures"].append(failure)
                        detail["rivals"][name] = record
                    if rounds == 2 and "causal_case" not in result:
                        counterfactual = adapter.program({"completion_rounds": 1})
                        for pair in episode["train"]:
                            intermediate = apply(counterfactual, pair["input"])
                            if intermediate != pair["output"]:
                                result["causal_case"] = {
                                    "input": pair["input"], "settings": {"completion_rounds": rounds},
                                    "intermediate_value": {"grid": intermediate,
                                        "meaning": "Protected first-round completion of the original input",
                                        "enabling_example": _enabling_rectangle(
                                            pair["input"], intermediate, pair["output"])},
                                    "program": chosen, "output": pair["output"],
                                    "counterfactual_program": counterfactual,
                                    "counterfactual_output": intermediate,
                                    "ablation": "skip_a"}
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
    result = {"schema": "arcpuzzles-private-completion-self-review-v1", "task_id": TASK,
              "source_sha256": snapshot, "command": list(sys.argv),
              "teaching_scope": "Rivals are tested on the first two demonstrations; the third default demonstration and all four queries also receive protected exact-label checks. More-demo sampler requests reuse the same teaching prefix.",
              "sampling_repair": "The original first two demonstrations were large square boards with four colors, while the compact query had one color. Board-level palette and canvas gates were added after independent review found a protected counterexample. The revised second teaching example is compact and one-color; prior evidence remains source-bound to the earlier prototype.",
              "limits": "Bounded finite-rival review; no universal uniqueness, owner acceptance, or training admission."}
    code = 0
    try:
        rivals = _load(HERE / "rivals.py", "_independent_rectangle_rivals_")
        adapter = _load(HERE / "adapter.py", "_audited_rectangle_adapter_")
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
