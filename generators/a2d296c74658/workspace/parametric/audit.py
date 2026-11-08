"""Source-bound finite semantic audit for a2d296c74658 completion modes.

The default census checks eight seeds, every demo count 2..6, both settings,
and four queries.  Protected checks cover seeds 0/17, demo counts 2/6, both
settings, canonical pairs, and substantive independent 30x30 stress grids.
Queries are scored against a rival only after every demo fits.  No runtime
error is counted as a rival refutation; actual and cached logical checks are
reported separately.  This tool never accepts or promotes a generator.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents
            if (path / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file())
TASK = "a2d296c74658"
SETTINGS = ({"completion_mode": "vertical"}, {"completion_mode": "cascade"})


def load_local(name, path=None):
    path = path or HERE / (name + ".py")
    identity = "_a2d296c74658_semantic_audit_" + name
    spec = importlib.util.spec_from_file_location(identity, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[identity] = module
    spec.loader.exec_module(module)
    return module


RIVALS = load_local("rivals")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def hash_sources(paths):
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(map(Path, paths))}


def source_paths():
    return sorted([path for path in HERE.iterdir()
                   if path.is_file() and path.suffix in (".py", ".rkt", ".json")]
                  + list((HERE.parents[1] / "tests").glob("test_parametric*.py"))
                  + [HERE.parents[1] / "generator.py"])


def source_state(before, after):
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    return {"unchanged": not changed, "changed_paths": changed,
            "start_sha256": before, "end_sha256": after}


def canonical_pairs():
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    row = next(item for item in records if item.get("task_id") == TASK)
    test = row["test"] if type(row["test"]) is list else [row["test"]]
    def grid(value):
        return [[int(v) for v in r] for r in value]
    return [{"input": grid(pair["input"]), "output": grid(pair["output"])}
            for pair in row["train"] + test]


def stress_grids():
    """Full-canvas structure: a long lattice and mixed controls in every quadrant."""
    lattice = [[7 if r % 2 == c % 2 == 0 else 0 for c in range(30)] for r in range(30)]
    # Original 4s in the outer row make B's non-A origin independently necessary.
    lattice[29] = [4 if c % 2 == 0 else 0 for c in range(30)]
    patterns = [
        [[7, 0, 7, 0, 4], [0, 0, 0, 0, 0], [7, 0, 7, 0, 4],
         [4, 0, 4, 0, 4], [0, 7, 0, 7, 0]],
        [[0, 0, 7, 0, 7], [4, 0, 0, 0, 8], [0, 0, 7, 0, 7],
         [4, 0, 0, 0, 4], [7, 0, 7, 0, 7]],
        [[0, 7, 0, 4, 0], [4, 0, 4, 0, 0], [0, 7, 0, 4, 0],
         [3, 0, 3, 0, 7], [4, 9, 4, 0, 0]],
    ]
    mixed = [[0] * 30 for _ in range(30)]
    for br in range(6):
        for bc in range(6):
            tile = deepcopy(patterns[(br + 2 * bc) % len(patterns)])
            if (br + bc) % 2:
                tile.reverse()
            if bc % 2:
                tile = [row[::-1] for row in tile]
            for r in range(5):
                for c in range(5):
                    mixed[5 * br + r][5 * bc + c] = tile[r][c]
    return {"long_vertical_lattice": lattice, "mixed_full_canvas_controls": mixed}


def _grid_check(grid, source):
    RIVALS._grid(grid)
    if len(grid) != len(source) or len(grid[0]) != len(source[0]):
        raise ValueError("Output changed grid dimensions")


def _keys(episode, split):
    return [_digest(pair["input"]) for pair in episode[split]]


def _minimal(findings):
    selected = {}
    for finding in findings:
        key = (finding["settings"]["completion_mode"], finding["equivalence_group"])
        rank = (len(finding["input"]) * len(finding["input"][0]), finding["demos"],
                finding["seed"], finding["query_index"])
        if key not in selected or rank < selected[key][0]:
            selected[key] = (rank, finding)
    return [selected[key][1] for key in sorted(selected)]


def run_python(prototype, seeds=tuple(range(8)), demo_counts=(2, 3, 4, 5, 6), queries=4):
    counts, dimensions, feature_counts = Counter(), Counter(), Counter()
    rows, errors, findings = [], [], []
    inputs, pairs, oracle_cache, baseline = set(), set(), {}, {}
    def expected(grid, settings):
        key = (settings["completion_mode"], _digest(grid))
        counts["logical_oracle_checks"] += 1
        if key not in oracle_cache:
            oracle_cache[key] = RIVALS.oracle(grid, settings)
        return oracle_cache[key]
    for seed in seeds:
        counts["generate_calls"] += 1
        baseline[seed] = prototype.generate(seed, SETTINGS[0], demos=max(demo_counts), queries=queries)
    for settings in SETTINGS:
        for seed in seeds:
            for demos in demo_counts:
                job = {"seed": seed, "settings": dict(settings), "demos": demos, "queries": queries}
                row = dict(job)
                try:
                    counts["generate_calls"] += 2
                    episode = prototype.generate(seed, settings, demos=demos, queries=queries)
                    repeat = prototype.generate(seed, settings, demos=demos, queries=queries)
                    counts["episodes"] += 1
                    deterministic = episode == repeat
                    counts["determinism_checks"] += 1
                    counts["determinism_passes"] += deterministic
                    if not deterministic:
                        errors.append({**job, "error": "Generation was not deterministic"})
                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        raise ValueError("Requested pair counts were not honored")
                    program = prototype.program(settings)
                    counts["program_checks"] += 1
                    counts["program_passes"] += episode["program_solution"] == program
                    if episode["program_solution"] != program:
                        errors.append({**job, "error": "program_solution differs from program(settings)"})
                    prefixes_match = (_keys(episode, "train") == _keys(baseline[seed], "train")[:demos]
                                      and _keys(episode, "test") == _keys(baseline[seed], "test"))
                    counts["matched_input_and_prefix_checks"] += 1
                    counts["matched_input_and_prefix_passes"] += prefixes_match
                    if not prefixes_match:
                        errors.append({**job, "error": "Inputs changed with settings or pair counts"})
                    keys = _keys(episode, "train") + _keys(episode, "test")
                    distinct = len(set(keys)) == len(keys)
                    counts["distinct_input_checks"] += 1
                    counts["distinct_input_passes"] += distinct
                    if not distinct:
                        errors.append({**job, "error": "Duplicate input within an episode"})
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            grid, output = pair["input"], pair["output"]
                            _grid_check(output, grid)
                            if min(len(grid), len(grid[0])) < 7:
                                raise ValueError("Generated sample is below the declared 7-cell dimension minimum")
                            reference = expected(grid, settings)
                            counts["pair_claims_checked"] += 1
                            counts["pair_claims_match_oracle"] += output == reference
                            if output != reference:
                                errors.append({**job, "split": split, "index": index, "input": grid,
                                               "output": output, "oracle_output": reference,
                                               "error": "Label differs from independent oracle"})
                            details = RIVALS.describe(grid)
                            counts["nonidentity_pairs"] += grid != output
                            counts["30x30_pairs"] += (details["height"], details["width"]) == (30, 30)
                            dimensions[f"{details['height']}x{details['width']}"] += 1
                            for key in ("a_count", "b_count", "a_interior_count", "a_edge_count"):
                                feature_counts[key] += details[key]
                            for key, value in details["b_endpoint_origins"].items():
                                feature_counts["b_" + key] += value
                            inputs.add(_digest(grid))
                            pairs.add(_digest(pair))
                    lesson = RIVALS.audit_lesson(episode, settings)
                    row["rivals"] = lesson["rivals"]
                    row["finding_count"] = len(lesson["findings"])
                    row["error_count"] = len(lesson["errors"])
                    for rival in lesson["rivals"]:
                        counts["rival_lessons"] += 1
                        counts["rival_demo_evaluations"] += rival["demo_checks"]
                        counts["rival_query_evaluations"] += rival["query_checks"]
                        counts["surviving_rival_lessons"] += rival["fits_all_demos"] is True
                    errors.extend({**job, **error} for error in lesson["errors"])
                    findings.extend({**job, **finding, "intended_program": program}
                                    for finding in lesson["findings"])
                except Exception as exc:
                    errors.append({**job, "error": f"{type(exc).__name__}: {exc}"})
                    row["status"] = "error"
                rows.append(row)
    canonical = canonical_pairs()
    canonical_checks = [RIVALS.oracle(pair["input"], SETTINGS[0]) == pair["output"] for pair in canonical]
    exact_default = prototype.program(SETTINGS[0]) == (HERE / "canonical.rkt").read_text()
    if not all(canonical_checks) or not exact_default:
        errors.append({"error": "Canonical pair or exact default program mismatch"})
    counts["unique_inputs"] = len(inputs)
    counts["unique_input_output_pairs"] = len(pairs)
    counts["actual_oracle_evaluations"] = len(oracle_cache)
    counts["query_disagreements"] = len(findings)
    counts["errors"] = len(errors)
    return {"status": "passed" if not findings and not errors else "failed",
            "scope": {"seeds": list(seeds), "demo_counts": list(demo_counts),
                      "settings": list(SETTINGS), "queries": queries,
                      "protocol": "Exact generated lessons; deterministic replays and matched count prefixes; no finding-based input selection"},
            "counts": dict(counts), "dimension_occurrences": dict(sorted(dimensions.items())),
            "feature_occurrences": dict(feature_counts), "episodes": rows,
            "canonical_pair_matches": canonical_checks, "default_program_is_exact_canonical": exact_default,
            "finding_keys": [{key: f[key] for key in ("seed", "settings", "demos", "rival", "query_index")}
                             for f in findings],
            "minimal_findings": _minimal(findings), "errors": errors}


def run_protected(prototype, seeds=(0, 17), demo_counts=(2, 6), queries=4):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    counts, records, errors, findings, stress = Counter(), [], [], [], []
    cache = {}
    causal = None
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, HERE):
        execute, identity, bridge = _real_evaluator(runtime)
        def actual(program, grid, kind):
            counts["logical_" + kind + "_checks"] += 1
            key = (_digest(program), _digest(grid))
            if key in cache:
                counts["cache_hits"] += 1
                return deepcopy(cache[key])
            counts["actual_racket_executions"] += 1
            counts["actual_" + kind + "_executions"] += 1
            output = execute(program, deepcopy(grid))
            _grid_check(output, grid)
            cache[key] = deepcopy(output)
            return output
        def rival_actual(rival, grid):
            output = actual(rival.program, grid, "rival")
            python = rival.apply(grid)
            counts["rival_python_parity_checks"] += 1
            if output != python:
                raise ValueError("Protected/Python rival mismatch: " + rival.name)
            return output
        try:
            canonical_checks = []
            for pair in canonical_pairs():
                output = actual(prototype.program(SETTINGS[0]), pair["input"], "intended")
                canonical_checks.append(output == pair["output"] == RIVALS.oracle(pair["input"], SETTINGS[0]))
            if not all(canonical_checks):
                errors.append({"error": "Canonical protected output mismatch"})
            for settings in SETTINGS:
                for seed in seeds:
                    for demos in demo_counts:
                        job = {"seed": seed, "settings": dict(settings), "demos": demos, "queries": queries}
                        try:
                            episode = prototype.generate(seed, settings, demos=demos, queries=queries)
                            program = prototype.program(settings)
                            counts["episodes"] += 1
                            for split in ("train", "test"):
                                for index, pair in enumerate(episode[split]):
                                    output = actual(program, pair["input"], "intended")
                                    expected = RIVALS.oracle(pair["input"], settings)
                                    counts["pair_claims_checked"] += 1
                                    counts["pair_claims_match_racket_and_oracle"] += output == pair["output"] == expected
                                    if output != pair["output"] or output != expected:
                                        errors.append({**job, "split": split, "index": index, "input": pair["input"],
                                                       "claim": pair["output"], "racket_output": output,
                                                       "oracle_output": expected, "error": "Claim/Racket/oracle mismatch"})
                                    if settings["completion_mode"] == "cascade" and causal is None:
                                        skip = next(r for r in RIVALS.bank(settings) if r.name == "skip_a")
                                        counter = rival_actual(skip, pair["input"])
                                        if counter != output:
                                            intermediate = actual(prototype.program(SETTINGS[0]), pair["input"], "intended")
                                            continued = rival_actual(skip, intermediate)
                                            if intermediate != RIVALS.first_stage(pair["input"]) or continued != output:
                                                raise ValueError("Independent stage decomposition did not match intended program")
                                            causal = {**job, "split": split, "pair_index": index,
                                                      "input": pair["input"], "a_program": prototype.program(SETTINGS[0]),
                                                      "intermediate": intermediate, "b_program": skip.program,
                                                      "output": output, "counterfactual_output_without_a": counter,
                                                      "b_endpoint_origins": RIVALS.describe(pair["input"])["b_endpoint_origins"],
                                                      "replayed_in_protected_racket": True}
                            lesson = RIVALS.audit_lesson(episode, settings, execute=rival_actual)
                            records.append({**job, "rivals": lesson["rivals"],
                                            "finding_count": len(lesson["findings"]), "errors": lesson["errors"]})
                            counts["rival_lessons"] += len(lesson["rivals"])
                            for row in lesson["rivals"]:
                                counts["rival_demo_checks"] += row["demo_checks"]
                                counts["rival_query_checks"] += row["query_checks"]
                                counts["surviving_rival_lessons"] += row["fits_all_demos"] is True
                            errors.extend({**job, **error} for error in lesson["errors"])
                            findings.extend({**job, **finding, "intended_program": program}
                                            for finding in lesson["findings"])
                        except Exception as exc:
                            errors.append({**job, "error": f"{type(exc).__name__}: {exc}"})
            for name, grid in stress_grids().items():
                for settings in SETTINGS:
                    output = actual(prototype.program(settings), grid, "intended")
                    expected = RIVALS.oracle(grid, settings)
                    counts["stress_intended_checks"] += 1
                    if output != expected:
                        errors.append({"stress": name, "settings": settings, "error": "Stress label mismatch"})
                    rivals = []
                    for rival in RIVALS.bank(settings):
                        try:
                            alternate = rival_actual(rival, grid)
                            counts["stress_rival_checks"] += 1
                            rivals.append({"rival": rival.name, "python_parity": True,
                                           "differs_from_intended": alternate != output})
                        except Exception as exc:
                            errors.append({"stress": name, "settings": settings, "rival": rival.name,
                                           "error": f"{type(exc).__name__}: {exc}"})
                    stress.append({"fixture": name, "settings": settings, "input": grid, "output": output,
                                   "measurements": RIVALS.describe(grid), "rivals": rivals,
                                   "input_sha256": _digest(grid), "output_sha256": _digest(output)})
        finally:
            bridge.close()
    counts["query_disagreements"] = len(findings)
    counts["errors"] = len(errors)
    counts["distinct_successful_program_input_executions"] = len(cache)
    return {"status": "passed" if not findings and not errors else "failed",
            "scope": {"seeds": list(seeds), "demo_counts": list(demo_counts), "settings": list(SETTINGS),
                      "queries": queries, "stress_fixtures": list(stress_grids()),
                      "protocol": "Protected intended labels and independent oracle; demo-first rival execution; every rival additionally evaluated on both full 30x30 fixtures"},
            "identity": identity, "bridge_closed": True, "counts": dict(counts),
            "canonical_pair_matches": canonical_checks, "episodes": records, "stress": stress,
            "causal_candidate": causal, "minimal_findings": _minimal(findings), "errors": errors}


def run_retained_before():
    """Reproduce the retained ordinary production lesson; do not mutate it."""
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, HERE):
        legacy = load_local("legacy_generator", HERE.parents[1] / "generator.py")
        grids = [legacy.generate(0, index, difficulty="easy") for index in range(3, 7)]
        canonical = (HERE / "canonical.rkt").read_text()
        execute, identity, bridge = _real_evaluator(runtime)
        counts = Counter()
        try:
            pairs = []
            bank = {r.name: r for r in RIVALS.bank(SETTINGS[0])}
            cap = bank["a_cap_two_per_column"]
            cap_outputs = []
            for grid in grids:
                output = execute(canonical, grid)
                alternate = execute(cap.program, grid)
                counts["actual_racket_executions"] += 2
                if output != RIVALS.oracle(grid, SETTINGS[0]) or alternate != cap.apply(grid):
                    raise AssertionError("Before reproduction disagreed with independent semantics")
                pairs.append({"input": grid, "output": output})
                cap_outputs.append(alternate)
            fit = [pair["output"] == alternate for pair, alternate in zip(pairs, cap_outputs)]
            interior = [[0] * 9 for _ in range(9)]
            for r in (0, 2, 4, 6):
                interior[r][2] = 7
            interior[2][6] = interior[4][6] = 7
            edge = bank["a_shared_chains_only_at_edges"]
            correct = execute(canonical, interior)
            alternate = execute(edge.program, interior)
            counts["actual_racket_executions"] += 2
            if correct != RIVALS.oracle(interior, SETTINGS[0]) or alternate != edge.apply(interior):
                raise AssertionError("Interior support witness disagreed with independent semantics")
            validation = [legacy.self_check(grid) for grid in grids]
            interior_validation = legacy.self_check(interior)
            hook = legacy.lesson_identifiable(pairs[:3], pairs[3])
        finally:
            bridge.close()
    reproduced = all(fit[:3]) and not fit[3] and not any(validation)
    support = correct != alternate and not interior_validation
    return {"status": "passed" if reproduced and support else "failed",
            "scope": "Retained original generator, easy seed 0, sample indices 3..6; one lawful authored interior-chain support witness",
            "identity": identity, "bridge_closed": True, "counts": dict(counts),
            "ordinary_retained_finding": {"reproduced": reproduced, "settings": SETTINGS[0],
                "seed": 0, "difficulty": "easy", "sample_indices": [3, 4, 5, 6],
                "canonical_program": canonical, "rival": cap.name, "program": cap.program,
                "train": pairs[:3], "test": [pairs[3]], "rival_outputs": cap_outputs,
                "demo_matches": fit[:3], "query_match": fit[3],
                "validator_errors": validation, "legacy_lesson_hook_errors": hook},
            "authored_support_witness": {"reproduced": support,
                "classification": "Authored lawful support counterexample, not an ordinary generated query failure",
                "input": interior, "output": correct, "rival_output": alternate,
                "rival": edge.name, "program": edge.program, "validator_errors": interior_validation}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--before", action="store_true")
    parser.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--demo-counts", default="2,3,4,5,6")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("Output exists; choose a new source-bound evidence path")
    started = time.monotonic()
    before = hash_sources(source_paths())
    report = {"schema": "a2d296c74658-semantic-audit-v1", "task_id": TASK,
              "observed_utc": datetime.now(timezone.utc).isoformat(),
              "finite_scope": "Only named settings, seeds, pair counts, executable rivals and fixtures; no universal uniqueness, acceptance or training-admission claim",
              "equivalences": {"original_b_priority": ["b_before_a", "b_reads_original"],
                  "excluded_equivalent_variants": ["in-place versus simultaneous within either stage",
                                                    "repeat A then B to a fixed point",
                                                    "new-only versus two-new-endpoints",
                                                    "original endpoints with current zero eligibility versus old-four-only"]},
              "rival_bank": {s["completion_mode"]: [{"name": r.name, "description": r.description,
                    "equivalence_group": r.equivalence_group or r.name,
                    "program_sha256": hashlib.sha256(r.program.encode()).hexdigest()}
                    for r in RIVALS.bank(s)] for s in SETTINGS}}
    try:
        if args.before:
            report["before"] = run_retained_before()
        else:
            prototype = load_local("prototype")
            report["python"] = run_python(prototype, tuple(map(int, args.seeds.split(","))),
                                            tuple(map(int, args.demo_counts.split(","))))
            report["racket"] = {"status": "not_requested"} if args.python_only else run_protected(prototype)
    except Exception as exc:
        report["fatal_error"] = f"{type(exc).__name__}: {exc}"
    report["source_binding"] = source_state(before, hash_sources(source_paths()))
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["status"] = "failed" if ("fatal_error" in report or not report["source_binding"]["unchanged"]
        or any(report.get(key, {}).get("status") == "failed" for key in ("python", "racket", "before"))) else "passed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "source_unchanged": report["source_binding"]["unchanged"],
                      "python": report.get("python", {}).get("counts"),
                      "racket": report.get("racket", {}).get("counts"),
                      "before": report.get("before", {}).get("status"),
                      "fatal_error": report.get("fatal_error"),
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
