#!/usr/bin/env python3
"""Source-bound contract/rotation probe; never loads canonical or solve data."""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import types

TASK = "cc8c719680e6"
HERE = Path(__file__).resolve().parent
GENERATOR = HERE.parents[1] / "generator.py"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_selected():
    source = GENERATOR.read_bytes()
    module = types.ModuleType("contract_review_selected_generator")
    module.__file__ = str(GENERATOR)
    sys.modules[module.__name__] = module
    exec(compile(source, str(GENERATOR), "exec"), module.__dict__)
    return module, hashlib.sha256(source).hexdigest()


def capture_hook(gen, demos, query):
    before = copy.deepcopy((demos, query))
    try:
        result = gen.lesson_identifiable(demos, query)
        outcome = {"return": result, "valid_return_type": isinstance(result, list) and all(isinstance(x, str) for x in result)}
    except Exception as exc:
        outcome = {"error_type": type(exc).__name__, "error": str(exc)}
    outcome["mutated_inputs"] = (demos, query) != before
    return outcome


def score(gen, demos, query):
    survived, ambiguous, errors = [], [], []
    for name, rival in gen.LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                survived.append(name)
                if rival(query["input"]) != query["output"]:
                    ambiguous.append(name)
        except Exception as exc:
            errors.append({"rival": name, "error_type": type(exc).__name__, "error": str(exc)})
    return {"survived_demos": survived, "query_discriminating_survivors": ambiguous, "errors": errors}


def pair(gen, seed, index, difficulty):
    grid = gen.generate(seed, index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "before_findings.json")
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()
    gen, source_sha256 = load_selected()
    report = {
        "schema": "cc8c719680e6-contract-probe-v1",
        "task_id": TASK,
        "generator_sha256": source_sha256,
        "generator_version": gen.VERSION,
        "rule_hash_declared": gen.RULE_HASH,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command_from_packet_root": "python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/contract_review/probe.py --out " + str(args.out),
        "oracle": "selected Python rule_mirror; no canonical or solve data read",
        "override_cases": 0,
        "override_failures": [],
        "ordinary_lessons": [],
        "query_rotations": [],
        "edge_cases": {},
    }
    axis_names = ("scene_profile", "n_blobs", "color_relation", "edge_mode", "palette_kind")
    domains = (gen.SCENE_PROFILES, gen.N_BLOBS, gen.COLOR_RELATIONS, gen.EDGE_MODES, gen.PALETTE_KINDS)
    for difficulty, seed_offset, (index, values) in itertools.product(("easy", "medium", "hard"), range(args.seeds), enumerate(itertools.product(*domains))):
        overrides = dict(zip(axis_names, values))
        seed = 23000 + 1000 * seed_offset + index
        report["override_cases"] += 1
        replay = {"seed": seed, "sample_index": index, "difficulty": difficulty, "overrides": overrides}
        try:
            grid = gen.generate(seed, index, difficulty=difficulty, **overrides)
            errors = gen.self_check(grid, meta={"overrides": overrides})
            observed = gen.observe_overrides(grid)
            deterministic = grid == gen.generate(seed, index, difficulty=difficulty, **overrides)
            if errors or observed != overrides or not deterministic:
                report["override_failures"].append({"replay": replay, "self_check": errors, "observed": observed, "deterministic": deterministic, "input": grid})
        except Exception as exc:
            report["override_failures"].append({"replay": replay, "error_type": type(exc).__name__, "error": str(exc)})
    for difficulty, seed_offset, start in itertools.product(("easy", "medium", "hard"), range(args.seeds), range(4)):
        seed = 1042 + seed_offset
        pairs = [pair(gen, seed, index, difficulty) for index in range(start, start + 5)]
        ordinary = {"seed": seed, "start": start, "difficulty": difficulty, "hook": capture_hook(gen, pairs[:4], pairs[4]), "rivals": score(gen, pairs[:4], pairs[4])}
        report["ordinary_lessons"].append(ordinary)
        for query_position in range(5):
            demos = [item for index, item in enumerate(pairs) if index != query_position]
            query = pairs[query_position]
            row = {"seed": seed, "start": start, "difficulty": difficulty, "query_position": query_position,
                   "query_schedule_index": start + query_position,
                   "demo_schedule_indexes": [start + index for index in range(5) if index != query_position],
                   "input_hashes": [digest(item["input"]) for item in pairs],
                   "hook": capture_hook(gen, demos, query), "rivals": score(gen, demos, query)}
            report["query_rotations"].append(row)
    pairs = [pair(gen, 1042, index, "easy") for index in range(5)]
    off_profile = [[*row, 0] for row in pairs[0]["input"]]
    off_pair = {"input": off_profile, "output": gen.rule_mirror(off_profile)}
    demos = [off_pair] + copy.deepcopy(pairs[1:4])
    report["edge_cases"]["self_check_valid_7x8_demo"] = {
        "construction": "generate(seed=1042, sample_index=0, difficulty='easy'), append zero column",
        "input": off_profile, "self_check": gen.self_check(off_profile),
        "observed_overrides": gen.observe_overrides(off_profile), "hook": capture_hook(gen, demos, pairs[4])}
    for name, extra in (("missing_input_key", {"output": pairs[0]["output"]}), ("missing_output_key", {"input": pairs[0]["input"]}), ("invalid_input_none", {"input": None, "output": pairs[0]["output"]})):
        report["edge_cases"]["valid_four_plus_" + name] = {"extra_demo": extra, "hook": capture_hook(gen, pairs[:4] + [extra], pairs[4])}
    rotations = report["query_rotations"]
    report["summary"] = {
        "override_cases": report["override_cases"],
        "override_failures": len(report["override_failures"]),
        "ordinary_lessons": len(report["ordinary_lessons"]),
        "ordinary_hook_failures": sum(bool(row["hook"].get("return") or row["hook"].get("error")) for row in report["ordinary_lessons"]),
        "rotations": len(rotations),
        "rotated_ambiguous_queries": sum(bool(row["rivals"]["query_discriminating_survivors"]) for row in rotations),
        "rotated_hook_rejections_without_ambiguous_query": sum(bool(row["hook"].get("return")) and not row["rivals"]["query_discriminating_survivors"] for row in rotations),
        "rotated_hook_false_acceptances": sum(row["hook"].get("return") == [] and bool(row["rivals"]["query_discriminating_survivors"]) for row in rotations),
        "rotated_hook_errors": sum("error" in row["hook"] for row in rotations),
        "edge_case_exceptions": [name for name, result in report["edge_cases"].items() if "error" in result["hook"]],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "generator_sha256": source_sha256, **report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
