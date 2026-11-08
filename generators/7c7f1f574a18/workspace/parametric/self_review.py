r"""Bounded, source-bound teaching audit for the task-local parametric family.

Run from the packet with its supplied protected Racket runtime::

    python3 review.py run python3 \
      generators/7c7f1f574a18/workspace/parametric/self_review.py \
      --out ../checks/parametric/self-review

Only ``public/*.json`` are public challenges. Every public file contains the
demonstrations and exactly one query input. Programs, settings, later queries,
labels, and the audit report remain private authoring evidence. This finite
audit neither qualifies nor accepts a parametric family.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


sys.dont_write_bytecode = True
TASK_ID = "7c7f1f574a18"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SETTINGS = tuple({"min_hole_area": value} for value in (1, 2, 3))
MAX_FAILURE_CASES = 16


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                              allow_nan=False) + "\n", encoding="utf-8")


def _source_hashes():
    paths = [
        HERE / "self_review.py", HERE / "prototype.py", HERE / "adapter.py",
        HERE / "promotion.json", HERE / "canonical.rkt",
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "shared/runtime/reviewer_support.py",
        ROOT / "src/arcpuzzles/parametric_worker.py",
        ROOT / "shared/data/canonical/puzzles.jsonl",
    ]
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes())
            for path in paths if path.is_file()}


def _load_prototype():
    path = HERE / "prototype.py"
    body = path.read_bytes()
    name = "_task_parametric_self_review_" + _sha(body)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load the exact sibling prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Compile the hashed source, avoiding timestamp-dependent cached bytecode.
    exec(compile(body, str(path), "exec"), module.__dict__)
    for name in ("program", "generate", "rival_programs", "analyze"):
        if not callable(getattr(module, name, None)):
            raise ValueError(f"The sibling prototype must export {name}()")
    return module


def _episode(value, program, demos, queries, grid):
    if not isinstance(value, dict) or value.get("program_solution") != program:
        raise ValueError("generate() must return its exact chosen program_solution")
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = value.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"Requested {count} {split} pairs; got a different count")
        result[split] = []
        for pair in pairs:
            if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
                raise ValueError("Each private pair must contain input and output")
            result[split].append({"input": grid(pair["input"]),
                                  "output": grid(pair["output"])})
    return result


def _profile(grid, analysis):
    if not isinstance(analysis, dict) or type(analysis.get("components")) is not list:
        raise ValueError("analyze() must return a components list")
    components = analysis["components"]
    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=counts.get)
    foreground = [(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value != background]
    areas, boundary_areas = [], []
    for component in components:
        for region in component["gap_regions"]:
            (boundary_areas if region["touches_boundary"] else areas).append(
                region["area"])
    return {
        "height": len(grid), "width": len(grid[0]),
        "components": len(components), "foreground_cells": len(foreground),
        "occupied_rows": len({r for r, _ in foreground}),
        "occupied_columns": len({c for _, c in foreground}),
        "foreground_bbox": ([min(r for r, _ in foreground),
                              min(c for _, c in foreground),
                              max(r for r, _ in foreground),
                              max(c for _, c in foreground)] if foreground else None),
        "component_areas": [len(obj["cells"]) for obj in components],
        "max_enclosed_areas": [obj["max_enclosed_area"] for obj in components],
        "solid_components": sum(bool(obj["solid_bbox"]) for obj in components),
        "enclosed_region_areas": sorted(areas),
        "boundary_region_areas": sorted(boundary_areas),
    }


def review(out, seeds, demos, queries):
    started = time.monotonic()
    source_hashes = _source_hashes()
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    runtime = ROOT / "shared/runtime"
    private, public = out / "private", out / "public"
    private.mkdir()
    public.mkdir()
    program_dir = private / "programs"
    program_dir.mkdir()
    failures, failure_cases, records, episodes = [], [], [], []
    cache, profile_cache, program_hashes = {}, {}, {}
    evaluations = 0
    cache_hits = 0
    label_checks = 0

    def failure(kind, context, case=None):
        failures.append({"kind": kind, **context})
        if case is not None and len(failure_cases) < MAX_FAILURE_CASES:
            failure_cases.append({"kind": kind, **context, **case})

    def retain_program(program):
        if type(program) is not str or not program.strip():
            raise ValueError("Every chosen and rival program must be nonempty Racket text")
        if program not in program_hashes:
            digest = _sha(program.encode("utf-8"))
            program_hashes[program] = digest
            (program_dir / (digest + ".rkt")).write_text(program, encoding="utf-8")
        return program_hashes[program]

    with _local_imports(runtime, HERE):
        from reviewer_support import public_challenge_bytes, public_challenge_id
        prototype = _load_prototype()
        programs = {setting["min_hole_area"]: prototype.program(copy.deepcopy(setting))
                    for setting in SETTINGS}
        for program in programs.values():
            retain_program(program)
        catalog = Catalog(ROOT)
        selected = catalog.describe(TASK_ID)
        canonical = {row.get("program_solution") for row in
                     catalog._variants().get(selected.get("rule_task_id", TASK_ID), [])}
        if canonical != {programs[1]}:
            failure("canonical_default_source_mismatch", {})
        apply, identity, bridge = _real_evaluator(runtime)

        def execute(program, grid):
            nonlocal evaluations, cache_hits
            key = (retain_program(program), _sha(_bytes(grid)))
            if key in cache:
                cache_hits += 1
                return cache[key]
            evaluations += 1
            value = _grid(apply(program, copy.deepcopy(grid)))
            cache[key] = value
            return value

        try:
            for seed in seeds:
                shared_inputs = None
                for setting in SETTINGS:
                    threshold = setting["min_hole_area"]
                    chosen = programs[threshold]
                    context = {"seed": seed, "settings": dict(setting)}
                    failures_before = len(failures)
                    episode = _episode(prototype.generate(seed, dict(setting), demos, queries),
                                       chosen, demos, queries, _grid)
                    episode_index = len(episodes)
                    inputs = [pair["input"] for split in ("train", "test")
                              for pair in episode[split]]
                    input_bytes = [_bytes(value) for value in inputs]
                    if len(set(input_bytes)) != len(input_bytes):
                        failure("duplicate_episode_inputs", context)
                    if shared_inputs is None:
                        shared_inputs = input_bytes
                    elif shared_inputs != input_bytes:
                        failure("settings_change_inputs", context)

                    expected = {}
                    for split in ("train", "test"):
                        expected[split] = []
                        for index, pair in enumerate(episode[split]):
                            actual = execute(chosen, pair["input"])
                            expected[split].append(actual)
                            label_checks += 1
                            if actual != pair["output"]:
                                failure("claimed_label_mismatch", {
                                    **context, "split": split, "pair_index": index}, {
                                    "input": pair["input"], "claimed_output": pair["output"],
                                    "racket_output": actual,
                                    "program_sha256": retain_program(chosen)})
                            input_hash = _sha(_bytes(pair["input"]))
                            if input_hash not in profile_cache:
                                profile_cache[input_hash] = _profile(
                                    pair["input"], prototype.analyze(copy.deepcopy(pair["input"])))

                    declared = prototype.rival_programs(dict(setting))
                    if not isinstance(declared, dict) or any(type(k) is not str for k in declared):
                        raise ValueError("rival_programs() must return a string-keyed program map")
                    rivals = dict(declared)
                    for alternative, alternative_program in programs.items():
                        if alternative != threshold:
                            name = f"alternative_setting_{alternative}"
                            if name in rivals and rivals[name] != alternative_program:
                                raise ValueError(f"Reserved rival name conflicts: {name}")
                            rivals[name] = alternative_program
                    checks = []
                    for name, rival in sorted(rivals.items()):
                        rival_hash = retain_program(rival)
                        demo_agreement = [execute(rival, pair["input"]) == pair["output"]
                                          for pair in episode["train"]]
                        query_disagreement = [execute(rival, pair["input"]) != actual
                                              for pair, actual in
                                              zip(episode["test"], expected["test"])]
                        survives = all(demo_agreement)
                        ambiguous = survives and any(query_disagreement)
                        checks.append({
                            "name": name, "program_sha256": rival_hash,
                            "demo_agreement": demo_agreement,
                            "query_disagreement": query_disagreement,
                            "survives_demonstrations": survives,
                            "status": ("underidentified" if ambiguous else
                                       "finite_equivalent_survivor" if survives else
                                       "eliminated_by_demonstrations"),
                        })
                        if ambiguous:
                            index = query_disagreement.index(True)
                            pair = episode["test"][index]
                            failure("demo_survivor_changes_query", {
                                **context, "rival": name, "query_index": index}, {
                                "train": episode["train"], "query_input": pair["input"],
                                "chosen_output": expected["test"][index],
                                "rival_output": execute(rival, pair["input"]),
                                "program_sha256": retain_program(chosen),
                                "counterfactual_program_sha256": rival_hash})

                    first_turn = {"train": episode["train"], "test": episode["test"][:1]}
                    visible_bytes = public_challenge_bytes(first_turn)
                    visible_id = public_challenge_id(first_turn)
                    visible = json.loads(visible_bytes)
                    public_shape_ok = (
                        set(visible) == {"train", "test"} and len(visible["test"]) == 1
                        and all(set(pair) == {"input", "output"} for pair in visible["train"])
                        and all(set(pair) == {"input"} for pair in visible["test"])
                        and _sha(visible_bytes) == visible_id)
                    if not public_shape_ok:
                        failure("public_projection_schema_or_identity", context)
                    altered = copy.deepcopy(first_turn)
                    altered.update(seed="private-changed", settings={"private": "changed"},
                                   program="private-changed", future_queries=episode["test"][1:])
                    altered["test"][0]["output"] = [[9]]
                    hidden_independent = public_challenge_bytes(altered) == visible_bytes
                    if not hidden_independent:
                        failure("public_identity_depends_on_hidden_fields", context)
                    one = _episode(prototype.generate(seed, dict(setting), demos, 1),
                                   chosen, demos, 1, _grid)
                    first_turn_equal = public_challenge_bytes(one) == visible_bytes
                    if not first_turn_equal:
                        failure("query_count_changes_first_turn", context, {
                            "one_query_first_turn": json.loads(public_challenge_bytes(one)),
                            "requested_count_first_turn": visible})
                    public_path = public / (visible_id + ".json")
                    if public_path.exists() and public_path.read_bytes() != visible_bytes:
                        raise ValueError("Public content identity collision")
                    public_path.write_bytes(visible_bytes)
                    episodes.append({**context, "task_id": TASK_ID,
                                     "program_sha256": retain_program(chosen), **episode})
                    records.append({
                        **context, "private_episode_index": episode_index,
                        "program_sha256": retain_program(chosen),
                        "counts": {"demos": demos, "queries": queries},
                        "public_first_turn": "public/" + public_path.name,
                        "public_contains_one_query_only": public_shape_ok,
                        "public_identity_ignores_private_fields": hidden_independent,
                        "first_turn_equal_for_one_and_requested_queries": first_turn_equal,
                        "rivals": checks,
                        "passed": len(failures) == failures_before,
                    })
        finally:
            bridge.close()

    if _source_hashes() != source_hashes:
        failure("source_changed_during_audit", {})
    (private / "episodes.jsonl").write_bytes(
        b"".join(_bytes(episode) + b"\n" for episode in episodes))
    if failure_cases:
        _write_json(private / "failure-cases.json", failure_cases)
    profiles = list(profile_cache.values())
    checks = [check for record in records for check in record["rivals"]]
    summary = {
        "schema": "arcpuzzles-task-local-self-review-v1", "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "scope": "Finite demonstration-only rival audit; no qualification, acceptance, or universal uniqueness claim.",
        "survivor_interpretation": "A finite_equivalent_survivor matches these demonstrations and sampled queries only.",
        "source_sha256": source_hashes, "racket": identity,
        "request": {"seeds": seeds, "demos": demos, "queries": queries},
        "racket_evaluations": evaluations, "memoized_evaluation_hits": cache_hits,
        "distinct_programs": len(program_hashes), "private_label_checks": label_checks,
        "counts": {
            "episodes": len(records), "episodes_passed": sum(row["passed"] for row in records),
            "episodes_failed": sum(not row["passed"] for row in records),
            "rivals_eliminated_by_demos": sum(row["status"] == "eliminated_by_demonstrations" for row in checks),
            "finite_equivalent_survivors": sum(row["status"] == "finite_equivalent_survivor" for row in checks),
            "underidentified_rivals": sum(row["status"] == "underidentified" for row in checks),
            "failures": len(failures), "retained_failure_cases": len(failure_cases),
            "distinct_inputs": len(profiles),
        },
        "profiles": {
            "canvas_shapes": sorted({(p["height"], p["width"]) for p in profiles}),
            "component_counts": sorted({p["components"] for p in profiles}),
            "component_areas": sorted({area for p in profiles for area in p["component_areas"]}),
            "max_enclosed_areas": sorted({area for p in profiles for area in p["max_enclosed_areas"]}),
            "enclosed_region_areas": sorted({area for p in profiles for area in p["enclosed_region_areas"]}),
            "boundary_region_areas": sorted({area for p in profiles for area in p["boundary_region_areas"]}),
            "stress_30x30": [p for p in profiles if p["height"] == p["width"] == 30],
        },
        "episodes": records, "failures": failures,
        "artifacts": {"private_episodes": "private/episodes.jsonl",
                      "private_programs": "private/programs",
                      "public_first_turns": "public",
                      "private_failure_cases": "private/failure-cases.json" if failure_cases else None},
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    _write_json(out / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path,
                        help="Fresh evidence directory; existing directories are rejected")
    parser.add_argument("--seed", action="append", type=int,
                        help="Repeat for multiple seeds; default: 0 and 17")
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=3)
    parser.add_argument("--queries", type=int, choices=range(1, 5), default=4)
    args = parser.parse_args(argv)
    seeds = args.seed if args.seed is not None else [0, 17]
    if any(not 0 <= seed <= 2**63 - 1 for seed in seeds):
        parser.error("Seeds must be integers in 0..2**63-1")
    if len(seeds) != len(set(seeds)):
        parser.error("Repeated seeds would duplicate the audit; provide distinct seeds")
    out = args.out.resolve()
    if out.exists():
        parser.error("--out must name a fresh path")
    out.mkdir(parents=True)
    try:
        summary = review(out, seeds, args.demos, args.queries)
    except Exception as exc:
        error = {"schema": "arcpuzzles-task-local-self-review-v1", "status": "error",
                 "error": type(exc).__name__, "message": str(exc),
                 "source_sha256": _source_hashes(),
                 "scope": "An interrupted audit supplies no passing evidence."}
        _write_json(out / "summary.json", error)
        print(json.dumps({"status": "error", "error": type(exc).__name__,
                          "message": str(exc), "summary": str(out / "summary.json")}))
        return 1
    print(json.dumps({"status": summary["status"], "counts": summary["counts"],
                      "racket_evaluations": summary["racket_evaluations"],
                      "elapsed_seconds": summary["elapsed_seconds"],
                      "summary": str(out / "summary.json")}, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
