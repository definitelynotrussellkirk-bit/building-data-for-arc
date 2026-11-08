"""Bounded private self-review; run with the packet's review.py run launcher."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = "683b2102b08c"
DEMO_COUNTS = (2, 3, 6)
SIDES = ("left", "right")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_adjacent(home, filename):
    path = home / filename
    name = "_main_review_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_hashes(root, home):
    paths = [home / name for name in ("adapter.py", "prototype.py", "canonical.rkt", "promotion.json")]
    paths.append(root / "generators" / TASK / "generator.py")
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def strict_public(value):
    require(type(value) is dict and set(value) == {"train", "test"}, "Public top-level metadata leaked")
    require(type(value["test"]) is list and len(value["test"]) == 1, "Public prefix needs one query")
    require(all(type(p) is dict and set(p) == {"input", "output"} for p in value["train"]),
            "Public demonstration fields differ")
    require(all(type(p) is dict and set(p) == {"input"} for p in value["test"]), "Query label leaked")
    return public_challenge_bytes(value)


def rejects(operation, value, description):
    try:
        operation(value)
    except (ValueError, TypeError, KeyError):
        return
    raise ValueError("Negative verifier case was accepted: " + description)


def public_prefix(episode):
    prefix = {"train": episode["train"], "test": episode["test"][:1]}
    payload = public_challenge_bytes(prefix)
    visible = json.loads(payload)
    require(strict_public(visible) == payload, "Public prefix changed canonical bytes")
    changed = copy.deepcopy(episode)
    changed.update(settings={"private": True}, seed=-1, program_solution="private replacement")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    for pair in changed["test"][1:]:
        pair["input"] = [[8]]
    require(public_challenge_bytes({"train": changed["train"], "test": changed["test"][:1]}) == payload,
            "Private answers or future queries changed first-turn bytes")
    require(public_challenge_bytes(dict(prefix, settings={"private": True})) == payload,
            "Private metadata changed public bytes")
    leaked = copy.deepcopy(visible); leaked["settings"] = {"attach_side": "left"}
    rejects(strict_public, leaked, "settings leakage")
    leaked = copy.deepcopy(visible); leaked["test"][0]["output"] = [[1]]
    rejects(strict_public, leaked, "query output leakage")
    invalid = copy.deepcopy(visible); invalid["test"][0]["input"][0][0] = True
    rejects(public_challenge_bytes, invalid, "boolean cell")
    invalid = copy.deepcopy(visible); invalid["test"][0]["input"] = [[1], [1, 2]]
    rejects(public_challenge_bytes, invalid, "ragged grid")
    identifier = public_challenge_id(prefix)
    require(identifier == hashlib.sha256(payload).hexdigest(), "Public identity differs from exact bytes")
    return identifier, payload


def validate_episode(episode, program, demos, queries):
    require(episode.get("program_solution") == program, "Episode program differs from its setting")
    for split, count in (("train", demos), ("test", queries)):
        require(type(episode.get(split)) is list and len(episode[split]) == count, "Requested counts differ")
        for pair in episode[split]:
            _grid(pair["input"]); _grid(pair["output"])
    inputs = [json.dumps(p["input"]) for split in ("train", "test") for p in episode[split]]
    require(len(inputs) == len(set(inputs)), "Repeated demonstration/query input")


def sexpr(value):
    return "(" + " ".join(sexpr(x) for x in value) + ")" if isinstance(value, list) else str(value)


def review(output, seeds):
    require(not output.exists() and not output.is_symlink(), "Output path must be fresh")
    require(seeds and len(seeds) == len(set(seeds)) and all(0 <= s < 2**63 for s in seeds), "Invalid seeds")
    home = Path(__file__).resolve().parent
    root = find_root(home)
    hashes = source_hashes(root, home)
    adapter, prototype = (load_adjacent(home, name) for name in ("adapter.py", "prototype.py"))
    catalog = Catalog(root); row = catalog.describe(TASK)
    canonical = {v["program_solution"] for v in catalog._variants()[row.get("rule_task_id", TASK)]}
    programs = {side: adapter.program({"attach_side": side}) for side in SIDES}
    require(canonical == {programs["left"]}, "Default differs from exact canonical source")
    require((home / "canonical.rkt").read_text() == programs["left"], "Canonical resource bytes differ")
    require(programs["left"] != programs["right"], "Settings do not change the program")
    rivals = {side: prototype.rival_programs({"attach_side": side}) for side in SIDES}
    require(all(type(r) is dict and r for r in rivals.values()), "No declared rivals to review")
    rows, examples, structural, matched = [], [], {}, {}
    public_files, evaluations, calls = {}, 0, 0
    example_seed = 0 if 0 in seeds else seeds[0]
    runtime = root / "shared/runtime"
    with _local_imports(runtime, home):
        from puzzle_generators.rule_wrap import wrap_rule
        _, identity, bridge = _real_evaluator(runtime)
        wrapped = {}
        def execute(program, grids):
            nonlocal evaluations, calls
            require(type(program) is str and bool(program.strip()), "Empty rival program")
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            result = bridge.eval_text(f"(map {wrapped[program]} '{sexpr(grids)})")
            require(type(result) is list and len(result) == len(grids), "Protected batch count differs")
            result = [_grid(grid) for grid in result]
            evaluations += len(grids); calls += 1
            return result
        try:
            for seed in seeds:
                for side in SIDES:
                    settings = {"attach_side": side}
                    full = adapter.generate(seed, settings, 6, 4)
                    validate_episode(full, programs[side], 6, 4)
                    pairs = full["train"] + full["test"]
                    grids, labels = [p["input"] for p in pairs], [p["output"] for p in pairs]
                    if seed in matched:
                        require(grids == matched[seed], "Setting-dependent input sequence")
                    else:
                        matched[seed] = grids
                    require(execute(programs[side], grids) == labels, "Claimed labels differ from protected Racket")
                    predictions = {name: execute(program, grids) for name, program in rivals[side].items()}
                    for grid in grids:
                        key = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                        facts = prototype.analyze(grid)
                        compact = {k: v for k, v in facts.items() if k not in {"main_cells", "secondary_cells", "output"}}
                        foreground = sum(c not in (7, 4) for r in grid for c in r)
                        structural[key] = dict(compact, foreground_cells=foreground,
                                               foreground_density=foreground / (len(grid) * len(grid[0])))
                    for demos in DEMO_COUNTS:
                        episode = full if demos == 6 else adapter.generate(seed, settings, demos, 4)
                        validate_episode(episode, programs[side], demos, 4)
                        require(episode["train"] == full["train"][:demos] and episode["test"] == full["test"],
                                "Demo counts changed their prefix or the independent query stream")
                        one = adapter.generate(seed, settings, demos, 1)
                        validate_episode(one, programs[side], demos, 1)
                        identifier, payload = public_prefix(episode)
                        require(public_challenge_bytes(one) == payload, "Single/four-query first turns differ")
                        checks = {}
                        for name, actual in predictions.items():
                            fits = actual[:demos] == labels[:demos]
                            disagreements = [i for i, (a, b) in enumerate(zip(actual[6:], labels[6:])) if a != b]
                            checks[name] = {"fits_demos": fits, "query_disagrees": bool(disagreements),
                                            "different_queries": disagreements}
                            require(not (fits and disagreements),
                                    f"Teaching ambiguity: seed={seed}, side={side}, demos={demos}, rival={name}")
                        rows.append(dict(seed=seed, settings=settings, demos=demos, queries=4, status="passed", rivals=checks))
                        if seed == example_seed and demos == 3:
                            require(identifier not in public_files, "Duplicate visible example prefix")
                            public_files[identifier] = payload
                            examples.append(dict(seed=seed, settings=settings, **episode,
                                public_prefix_id=identifier, facts=[prototype.analyze(p["input"]) for p in episode["train"] + episode["test"]],
                                rival_outputs={n: p[:3] + p[6:] for n, p in predictions.items()}))
        finally:
            bridge.close()
    facts = list(structural.values())
    sizes = sorted({(f["height"], f["width"]) for f in facts})
    require((8, 8) in sizes and (30, 30) in sizes, "Required 8x8/30x30 boundary coverage missing")
    require(all(8 <= h <= 30 and 8 <= w <= 30 for h, w in sizes), "Unexpected size outside 8..30")
    stress = [dict(input_sha256=k, **f) for k, f in structural.items() if (f["height"], f["width"]) == (30, 30)]
    require(source_hashes(root, home) == hashes, "Source changed during self-review")
    report = dict(schema="arcpuzzles-task-local-self-review-v1", task_id=TASK, status="passed",
        source_hashes=hashes, racket=identity, seeds=seeds, example_seed=example_seed,
        protected_batch_calls=calls, protected_grid_evaluations=evaluations,
        counts={str(n): {"successes": sum(r["demos"] == n for r in rows), "attempts": len(seeds) * 2,
                         "success_rate": 1.0} for n in DEMO_COUNTS},
        settings_matched_inputs=True, independent_demo_query_streams=True, one_query_prefix_equal=True,
        projection_checks=["private_metadata_invariant", "query_answers_invariant", "future_queries_hidden",
                           "strict_settings_rejected", "strict_query_answer_rejected", "boolean_rejected", "ragged_rejected"],
        structural=dict(unique_inputs=len(facts), sizes=sizes, min_size=[8, 8], max_size=[30, 30],
            foreground_cells=[min(f["foreground_cells"] for f in facts), max(f["foreground_cells"] for f in facts)],
            foreground_density=[min(f["foreground_density"] for f in facts), max(f["foreground_density"] for f in facts)],
            main_components=[min(f["main_component_count"] for f in facts), max(f["main_component_count"] for f in facts)],
            secondary_components=[min(f["secondary_component_count"] for f in facts), max(f["secondary_component_count"] for f in facts)],
            canonical_collision_count=[min(f["collision_count"] for f in facts), max(f["collision_count"] for f in facts)],
            stress_30x30=stress), episodes=rows,
        limits="Finite declared rivals and sampled seeds only; no universal identifiability, owner acceptance, or training admission.")
    private = dict(task_id=TASK, source_hashes=hashes, racket=identity, programs=programs,
                   rival_programs=rivals, episodes=examples)
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    for identifier in sorted(public_files):
        (output / "public" / (identifier + ".json")).write_bytes(public_files[identifier])
    for name, value in (("examples.private.json", private), ("report.json", report)):
        (output / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    return {"status": "passed", "report": str(output / "report.json"), "configurations": len(rows),
            "protected_grid_evaluations": evaluations, "public_prefixes": len(public_files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    args = parser.parse_args()
    try:
        result = review(args.out, [0, 8, 17] if args.seed is None else args.seed)
    except Exception as error:
        print(json.dumps({"status": "failed", "error": type(error).__name__, "message": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
