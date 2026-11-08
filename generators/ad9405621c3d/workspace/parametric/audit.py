"""Reproducible, source-bound finite semantic audit for ad9405621c3d.

Run through the packet's review.py run wrapper.  Python checks cover eight seeds,
every supported demo count 3..6, both settings and four queries.  Protected Racket
checks seeds 0/17 at demo counts 3/6, plus substantive 30x30 stress inputs.  Query
disagreement is inspected only after a rival fits every demo; errors never count
as refutations.  This is a finite bank audit, not a proof of universal induction.
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

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "ad9405621c3d"
SETTINGS = ({"route_mode": "direct"}, {"route_mode": "via_farthest"})


def load_local(name):
    path = HOME / (name + ".py")
    identity = "_ad9405621c3d_semantic_" + name
    spec = importlib.util.spec_from_file_location(identity, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[identity] = module
    spec.loader.exec_module(module)
    return module


RIVALS = load_local("rivals")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def hash_sources(paths):
    return {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in sorted(map(Path, paths))}


def source_paths():
    return sorted([path for path in HOME.iterdir()
                   if path.is_file() and path.suffix in (".py", ".rkt", ".json")]
                  + list((HOME.parents[1] / "tests").glob("test_parametric*.py")))


def source_state(before, after):
    changed = sorted(path for path in set(before) | set(after)
                     if before.get(path) != after.get(path))
    return {"unchanged": not changed, "changed_paths": changed,
            "start_sha256": before, "end_sha256": after}


def stress_grids():
    """Two actual full-canvas routing problems, not small padded fixtures."""
    snake = [[5] * 30 for _ in range(30)]
    for row in range(30):
        if row % 2 == 0:
            snake[row] = [0] * 30
        else:
            snake[row][29 if (row // 2) % 2 == 0 else 0] = 0
    snake[0][0] = snake[0][2] = 8
    mesh = [[5] * 30 for _ in range(30)]
    axes = (1, 7, 13, 19, 28)
    for row in range(30):
        for col in range(30):
            if row in axes or col in axes:
                mesh[row][col] = 0
    mesh[1][1] = mesh[13][13] = 6
    return {"serpentine": snake, "cyclic_mesh": mesh}


def _input_keys(episode, split):
    return [_digest(pair["input"]) for pair in episode[split]]


def _grid_check(grid, source):
    if (type(grid) is not list or len(grid) != len(source)
            or any(type(row) is not list or len(row) != len(source[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError("output is not a same-shape exact integer ARC grid")


def _compact_findings(findings):
    minimal = {}
    for finding in findings:
        key = (finding["settings"]["route_mode"], finding["rival"])
        rank = (len(finding["input"]) * len(finding["input"][0]), finding["demos"],
                finding["seed"], finding["query_index"])
        previous = minimal.get(key)
        if previous is None or rank < previous[0]:
            minimal[key] = (rank, finding)
    return [minimal[key][1] for key in sorted(minimal)]


def run_python(prototype, seeds=tuple(range(8)), demo_counts=(3, 4, 5, 6), queries=4):
    counts, dimensions, colors = Counter(), Counter(), Counter()
    episodes, findings, errors = [], [], []
    inputs, pairs, oracle_cache = set(), set(), {}
    baseline = {}
    def expected(grid, settings):
        key = (settings["route_mode"], _digest(grid))
        if key not in oracle_cache:
            oracle_cache[key] = RIVALS.oracle(grid, settings)
        return oracle_cache[key]
    for seed in seeds:
        counts["generate_calls"] += 1
        baseline[seed] = prototype.generate(seed, SETTINGS[0], max(demo_counts), queries)
    for settings in SETTINGS:
        for seed in seeds:
            for demos in demo_counts:
                job = {"seed": seed, "settings": dict(settings), "demos": demos, "queries": queries}
                row = dict(job)
                try:
                    counts["generate_calls"] += 2
                    episode = prototype.generate(seed, settings, demos, queries)
                    repeat = prototype.generate(seed, settings, demos, queries)
                    counts["episodes"] += 1
                    counts["deterministic_matches"] += _json(episode) == _json(repeat)
                    if episode != repeat:
                        errors.append({**job, "error": "generation was not deterministic"})
                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        raise ValueError("requested demo/query counts were not honored")
                    program = prototype.program(settings)
                    counts["program_matches"] += episode["program_solution"] == program
                    if episode["program_solution"] != program:
                        errors.append({**job, "error": "program_solution differs from program(settings)"})
                    prefix = (_input_keys(episode, "train") == _input_keys(baseline[seed], "train")[:demos]
                              and _input_keys(episode, "test") == _input_keys(baseline[seed], "test"))
                    counts["matched_input_and_prefix_checks"] += 1
                    counts["matched_input_and_prefix_passes"] += prefix
                    if not prefix:
                        errors.append({**job, "error": "inputs changed with settings or requested demo count"})
                    keys = _input_keys(episode, "train") + _input_keys(episode, "test")
                    counts["distinct_pair_episode_checks"] += 1
                    counts["distinct_pair_episode_passes"] += len(set(keys)) == len(keys)
                    if len(set(keys)) != len(keys):
                        errors.append({**job, "error": "duplicate input within an episode"})
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            grid, output = pair["input"], pair["output"]
                            _grid_check(output, grid)
                            reference = expected(grid, settings)
                            counts["pair_claims_checked"] += 1
                            counts["pair_claims_match_oracle"] += reference == output
                            if reference != output:
                                errors.append({**job, "split": split, "index": index,
                                               "input": grid, "output": output,
                                               "oracle_output": reference, "error": "claim differs from independent oracle"})
                            feature = RIVALS.describe(grid, settings)
                            counts["nonidentity_pairs"] += output != grid
                            counts["via_extra_pairs"] += feature["via_extra_cells"] > 0
                            counts["farthest_tie_pairs"] += feature["farthest_ties"] > 1
                            counts["30x30_pairs"] += (feature["height"], feature["width"]) == (30, 30)
                            dimensions[f"{feature['height']}x{feature['width']}"] += 1
                            colors[str(feature["color"])] += 1
                            inputs.add(_digest(grid))
                            pairs.add(_digest(pair))
                    lesson = RIVALS.audit_lesson(episode, settings)
                    row["rivals"] = lesson["rivals"]
                    row["finding_count"] = len(lesson["findings"])
                    row["error_count"] = len(lesson["errors"])
                    errors.extend({**job, **error} for error in lesson["errors"])
                    for record in lesson["rivals"]:
                        counts["rival_lessons"] += 1
                        counts["rival_demo_evaluations"] += record["demo_checks"]
                        counts["rival_query_evaluations"] += record["query_checks"]
                        counts["surviving_rival_lessons"] += record["fits_all_demos"]
                    findings.extend({**finding, **job, "intended_program": program}
                                    for finding in lesson["findings"])
                except Exception as exc:
                    errors.append({**job, "error": f"{type(exc).__name__}: {exc}"})
                    row["status"] = "error"
                episodes.append(row)
    counts["query_disagreements"] = len(findings)
    counts["errors"] = len(errors)
    counts["unique_inputs"] = len(inputs)
    counts["unique_input_output_pairs"] = len(pairs)
    counts["distinct_oracle_evaluations"] = len(oracle_cache)
    return {
        "status": "passed" if not findings and not errors else "failed",
        "scope": {"seeds": list(seeds), "demo_counts": list(demo_counts),
                  "settings": list(SETTINGS), "queries": queries,
                  "sampling": "Exact generated lessons; matched inputs across settings and count prefixes; no finding-based filtering"},
        "counts": dict(counts), "dimension_occurrences": dict(sorted(dimensions.items())),
        "endpoint_color_occurrences": dict(sorted(colors.items())), "episodes": episodes,
        "generator_reported_teaching_construction": {
            str(seed): prototype.teaching_summary(seed) for seed in seeds
        } if callable(getattr(prototype, "teaching_summary", None)) else {},
        "finding_keys": [{key: f[key] for key in ("seed", "settings", "demos", "queries", "rival", "query_index")}
                         for f in findings],
        "minimal_findings": _compact_findings(findings), "errors": errors,
    }


def run_protected(prototype, seeds=(0, 17), demo_counts=(3, 6), queries=4):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    counts, records, findings, errors, stress = Counter(), [], [], [], []
    cache = {}
    causal_candidate = None
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, HOME):
        execute, identity, bridge = _real_evaluator(runtime)
        def actual(program, grid, kind):
            counts["logical_" + kind + "_calls"] += 1
            key = (_digest(program), _digest(grid))
            if key in cache:
                counts["cache_hits"] += 1
                return deepcopy(cache[key])
            counts["actual_racket_executions"] += 1
            counts["actual_" + kind + "_executions"] += 1
            result = execute(program, deepcopy(grid))
            _grid_check(result, grid)
            cache[key] = deepcopy(result)
            return result
        def rival_actual(rival, grid):
            result = actual(rival.program, grid, "rival")
            python = rival.apply(grid)
            counts["rival_python_parity_checks"] += 1
            if result != python:
                raise ValueError(f"protected/Python rival mismatch: {rival.name}")
            return result
        try:
            for settings in SETTINGS:
                for seed in seeds:
                    for demos in demo_counts:
                        job = {"seed": seed, "settings": dict(settings), "demos": demos, "queries": queries}
                        episode = prototype.generate(seed, settings, demos, queries)
                        program = prototype.program(settings)
                        counts["episodes"] += 1
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                try:
                                    output = actual(program, pair["input"], "intended")
                                    independent = RIVALS.oracle(pair["input"], settings)
                                    counts["pair_claims_checked"] += 1
                                    counts["pair_claims_match_racket_and_oracle"] += output == pair["output"] == independent
                                    if not (output == pair["output"] == independent):
                                        errors.append({**job, "split": split, "index": index,
                                                       "input": pair["input"], "claim": pair["output"],
                                                       "racket_output": output, "oracle_output": independent,
                                                       "error": "claim/Racket/oracle mismatch"})
                                    if settings["route_mode"] == "via_farthest" and causal_candidate is None:
                                        counterprogram = prototype.program({"route_mode": "direct"})
                                        counteroutput = actual(counterprogram, pair["input"], "intended")
                                        if counteroutput != output:
                                            causal_candidate = {
                                                **job, "split": split, "pair_index": index,
                                                "input": pair["input"], "program": program, "output": output,
                                                "intermediate_value": RIVALS.describe(pair["input"], settings)["waypoint"],
                                                "counterfactual_program": counterprogram,
                                                "counterfactual_output": counteroutput, "ablation": "skip_a",
                                            }
                                except Exception as exc:
                                    errors.append({**job, "split": split, "index": index,
                                                   "error": f"{type(exc).__name__}: {exc}"})
                        lesson = RIVALS.audit_lesson(episode, settings, execute=rival_actual)
                        records.append({**job, "rivals": lesson["rivals"],
                                        "finding_count": len(lesson["findings"]), "errors": lesson["errors"]})
                        errors.extend({**job, **error} for error in lesson["errors"])
                        findings.extend({**finding, **job, "intended_program": program}
                                        for finding in lesson["findings"])
            for name, grid in stress_grids().items():
                for settings in SETTINGS:
                    expected = RIVALS.oracle(grid, settings)
                    output = actual(prototype.program(settings), grid, "intended")
                    counts["stress_intended_checks"] += 1
                    if output != expected:
                        errors.append({"stress": name, "settings": settings,
                                       "error": "protected stress output differs from independent oracle"})
                    rival_checks = []
                    for rival in RIVALS.bank(settings):
                        try:
                            result = rival_actual(rival, grid)
                            rival_checks.append({"rival": rival.name, "python_parity": True,
                                                 "differs_from_intended": result != output})
                            counts["stress_rival_checks"] += 1
                        except Exception as exc:
                            errors.append({"stress": name, "settings": settings, "rival": rival.name,
                                           "error": f"{type(exc).__name__}: {exc}"})
                    stress.append({"fixture": name, "settings": settings, "input": grid,
                                   "output": output, "measurements": RIVALS.describe(grid, settings),
                                   "input_sha256": _digest(grid), "output_sha256": _digest(output),
                                   "rivals": rival_checks})
        finally:
            bridge.close()
    counts["query_disagreements"] = len(findings)
    counts["errors"] = len(errors)
    counts["distinct_program_input_evaluations"] = len(cache)
    return {"status": "passed" if not findings and not errors else "failed",
            "scope": {"seeds": list(seeds), "demo_counts": list(demo_counts),
                      "settings": list(SETTINGS), "queries": queries,
                      "stress_fixtures": list(stress_grids()),
                      "rival_protocol": "Fit actual Racket demonstration labels first; query checks only for survivors; every rival also runs on both 30x30 fixtures"},
            "identity": identity, "bridge_closed": True, "counts": dict(counts),
            "episodes": records, "stress": stress, "causal_candidate": causal_candidate,
            "minimal_findings": _compact_findings(findings), "errors": errors}


def replay_findings(path):
    """Re-execute retained BEFORE labels, without regenerating changed sources."""
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    retained = json.loads(Path(path).read_text())
    findings = retained.get("selected_findings", retained.get("minimal_findings", []))
    checks = []
    with _local_imports(ROOT / "shared" / "runtime", HOME):
        execute, identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
        try:
            for finding in findings:
                pairs = finding["train"] + [{"input": finding["input"], "output": finding["output"]}]
                for index, pair in enumerate(pairs):
                    output = execute(finding["intended_program"], pair["input"])
                    alternate = execute(finding["program"], pair["input"])
                    is_demo = index < len(finding["train"])
                    checks.append({"rival": finding["rival"], "split": "train" if is_demo else "test",
                                   "index": index, "intended_label_matches": output == pair["output"],
                                   "rival_prediction_matches": (alternate == output) if is_demo
                                   else (alternate == finding["rival_output"] and alternate != output)})
        finally:
            bridge.close()
    return {"status": "passed" if checks and all(c["intended_label_matches"] and c["rival_prediction_matches"] for c in checks) else "failed",
            "retained_input_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "identity": identity, "bridge_closed": True, "actual_racket_executions": len(checks) * 2,
            "checks": checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--seeds", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--demo-counts", default="3,4,5,6")
    parser.add_argument("--replay-findings", type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output exists; choose a new source-bound report path")
    started = time.monotonic()
    before = hash_sources(source_paths())
    report = {"schema": "ad9405621c3d-semantic-audit-v1", "task_id": TASK,
              "observed_utc": datetime.now(timezone.utc).isoformat(),
              "finite_scope": "Only the listed settings, seeds, counts, executable rivals and fixtures were checked. No universal uniqueness claim; no acceptance or training admission.",
              "rival_bank": {s["route_mode"]: [{"name": r.name, "description": r.description,
                                                  "program_sha256": hashlib.sha256(r.program.encode()).hexdigest()} for r in RIVALS.bank(s)]
                             for s in SETTINGS}}
    try:
        if args.replay_findings:
            report["replay"] = replay_findings(args.replay_findings)
        else:
            prototype = load_local("prototype")
            seeds = tuple(int(value) for value in args.seeds.split(","))
            demos = tuple(int(value) for value in args.demo_counts.split(","))
            report["python"] = run_python(prototype, seeds, demos)
            report["racket"] = {"status": "not_requested"} if args.python_only else run_protected(prototype)
    except Exception as exc:
        report["fatal_error"] = f"{type(exc).__name__}: {exc}"
    report["source_binding"] = source_state(before, hash_sources(source_paths()))
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["status"] = "failed" if (
        "fatal_error" in report or not report["source_binding"]["unchanged"]
        or any(report.get(key, {}).get("status") == "failed" for key in ("python", "racket", "replay"))
    ) else "passed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "source_unchanged": report["source_binding"]["unchanged"],
                      "python": report.get("python", {}).get("counts"),
                      "racket": report.get("racket", {}).get("counts"),
                      "replay": report.get("replay", {}).get("status"),
                      "fatal_error": report.get("fatal_error"),
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
