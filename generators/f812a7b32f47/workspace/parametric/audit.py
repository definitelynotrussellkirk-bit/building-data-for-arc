#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit and strict public/private export.

Run from the packet outer directory::

    python3 review.py run python3 generators/f812a7b32f47/workspace/parametric/audit.py \
        --out ../checks/f812a7b32f47/audit --seeds 0 17

Programs, settings, labels and counterexamples remain private. This is a finite
reviewer audit; native qualification and owner acceptance are separate gates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK = "f812a7b32f47"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SETTINGS = ({"selection": "all"}, {"selection": "largest"})
DEMOS, QUERIES = 3, 4


def load_path(path):
    """Load exact adjacent sources without shared short module names."""
    path = Path(path).resolve()
    name = "_f812_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load local source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def public_support():
    return load_path(ROOT / "shared/runtime/reviewer_support.py")


def project_episode(episode):
    raw = public_support().public_challenge_bytes(episode)
    return raw, hashlib.sha256(raw).hexdigest()


def first_turn(episode):
    """Only the demonstrations and first query input; no turn-count fields."""
    if not episode.get("test"):
        raise ValueError("A first turn requires a query")
    raw, _ = project_episode({"train": episode["train"], "test": episode["test"][:1]})
    return json.loads(raw)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2,
                                     allow_nan=False) + "\n", encoding="utf-8")


def write_exports(episodes, output):
    """Refuse existing output and duplicate visible challenges before writing."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    encoded = [project_episode(episode) for episode in episodes]
    ids = [digest for _, digest in encoded]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate visible challenge in export")
    # Validate the private JSON before creating a destination as well.
    json.dumps(episodes, allow_nan=False)
    output.mkdir(parents=True, exist_ok=False)
    public = output / "public"
    public.mkdir()
    rows = []
    for index, (raw, digest) in sorted(enumerate(encoded), key=lambda item: item[1][1]):
        path = public / f"{digest}.json"
        path.write_bytes(raw)
        rows.append({"episode_index": index, "path": f"public/{path.name}",
                     "sha256": digest, "bytes": len(raw)})
    write_json(output / "private.json", episodes)
    return rows


def source_hashes():
    sources = [HERE / name for name in ("audit.py", "adapter.py", "prototype.py",
                                        "scenes.py", "promotion.json", "canonical.rkt")]
    sources += [HERE.parents[1] / "generator.py",
                ROOT / "shared/data/canonical/puzzles.jsonl",
                ROOT / "shared/runtime/reviewer_support.py",
                ROOT / "src/arcpuzzles/parametric_worker.py"]
    sources += sorted((HERE.parents[1] / "tests").glob("test_parametric*.py"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources if path.is_file()}


def projection_checks(episode):
    raw, digest = project_episode(episode)
    altered = copy.deepcopy(episode)
    altered.update(settings={"selection": "hidden changed setting"},
                   program="hidden changed program", program_solution="hidden changed program",
                   private_metadata={"total_count": 999, "final_turn": True})
    for pair in altered["test"]:
        pair["output"] = [[(value + 1) % 10 for value in row] for row in pair["output"]]
        pair["private_metadata"] = "hidden changed answer"
    other_raw, other_digest = project_episode(altered)
    support = public_support()
    future_changed = copy.deepcopy(altered)
    future_changed["test"] = future_changed["test"][:1]
    return {
        "private_metadata_invariance": raw == other_raw and digest == other_digest,
        "serializer_id_matches_saved_bytes": support.public_challenge_id(episode) == digest,
        "first_turn_future_invariance": first_turn(episode) == first_turn(future_changed),
        "first_turn_schema": (set(first_turn(episode)) == {"train", "test"}
                              and len(first_turn(episode)["test"]) == 1
                              and set(first_turn(episode)["test"][0]) == {"input"}),
    }


def run(output, seeds, demos=DEMOS, queries=QUERIES):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if (not seeds or len(seeds) != len(set(seeds))
            or any(type(seed) is not int or not 0 <= seed < 2**63 for seed in seeds)):
        raise ValueError("Use distinct integer seeds in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    before = source_hashes()
    prototype = load_path(HERE / "prototype.py")
    adapter = load_path(HERE / "adapter.py")
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    episodes, teaching, failures, inputs = [], [], [], {}
    minimal = None
    evaluations = 0

    def fail(code, detail, *, case=None):
        nonlocal minimal
        failures.append({"code": code, "detail": detail})
        if minimal is None and case is not None:
            minimal = {"code": code, **copy.deepcopy(case)}

    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def execute(program, grid):
                nonlocal evaluations
                evaluations += 1
                return _grid(apply(program, _grid(grid)))

            for settings in SETTINGS:
                selection = settings["selection"]
                expected_program = prototype.program(copy.deepcopy(settings))
                if adapter.program(copy.deepcopy(settings)) != expected_program:
                    fail("adapter_program", f"Adapter/prototype program differs for {selection}")
                for seed in seeds:
                    episode = copy.deepcopy(adapter.generate(seed, copy.deepcopy(settings), demos, queries))
                    if episode.get("program_solution") != expected_program:
                        fail("generated_program", f"Program mismatch for {selection}, seed {seed}")
                    if any(type(episode.get(split)) is not list or len(episode[split]) != count
                           for split, count in (("train", demos), ("test", queries))):
                        raise ValueError(f"Wrong independent counts for {selection}, seed {seed}")
                    episode.update(task_id=TASK, seed=seed, settings=copy.deepcopy(settings),
                                   program=expected_program)
                    index = len(episodes)
                    episodes.append(episode)
                    all_pairs = episode["train"] + episode["test"]
                    input_keys = [json.dumps(_grid(pair["input"]), separators=(",", ":"))
                                  for pair in all_pairs]
                    if len(input_keys) != len(set(input_keys)):
                        fail("duplicate_input", f"Repeated input for {selection}, seed {seed}")
                    if seed in inputs and input_keys != inputs[seed]:
                        fail("unmatched_inputs", f"Settings changed sampled inputs for seed {seed}")
                    inputs[seed] = input_keys
                    projection = projection_checks(episode)
                    for key, passed in projection.items():
                        if not passed:
                            fail(key, f"Projection failure for {selection}, seed {seed}")
                    for pair_index, pair in enumerate(all_pairs):
                        actual = execute(expected_program, pair["input"])
                        claimed = _grid(pair["output"])
                        python = _grid(prototype.solve(pair["input"], selection))
                        if actual != claimed or actual != python:
                            fail("selected_label", f"Selected Racket/Python/claim mismatch at {index}:{pair_index}",
                                 case={"episode_index": index, "pair_index": pair_index,
                                       "settings": settings, "input": pair["input"],
                                       "program": expected_program, "claimed_output": claimed,
                                       "racket_output": actual, "python_output": python})
                    # Every declared rival must execute on every demonstration.
                    # Runtime failure is a failed audit, never a refutation.
                    names = sorted(prototype.rival_solutions(episode["train"][0]["input"]))
                    rows = []
                    for name in names:
                        rival_program = prototype.rival_program(name)
                        row = {"name": name, "demo_refutations": [], "query_disagreements": [],
                               "errors": [], "program_sha256": hashlib.sha256(rival_program.encode()).hexdigest()}
                        for pair_index, pair in enumerate(episode["train"]):
                            try:
                                actual = execute(rival_program, pair["input"])
                                claimed_rival = _grid(prototype.rival_solutions(pair["input"])[name])
                                if actual != claimed_rival:
                                    fail("rival_label", f"Rival {name} Python/Racket differs at {index}:train:{pair_index}",
                                         case={"episode_index": index, "split": "train", "pair_index": pair_index,
                                               "rival": name, "input": pair["input"],
                                               "program": rival_program, "racket_output": actual,
                                               "python_output": claimed_rival})
                                if actual != pair["output"]:
                                    row["demo_refutations"].append(pair_index)
                            except Exception as exc:
                                row["errors"].append({"split": "train", "pair_index": pair_index,
                                                      "error": f"{type(exc).__name__}: {exc}"})
                                fail("rival_execution", f"Rival {name} failed on demo {index}:{pair_index}: {exc}")
                        row["survives_demos"] = not row["demo_refutations"] and not row["errors"]
                        if row["survives_demos"]:
                            for pair_index, pair in enumerate(episode["test"]):
                                try:
                                    actual = execute(rival_program, pair["input"])
                                    claimed_rival = _grid(prototype.rival_solutions(pair["input"])[name])
                                    if actual != claimed_rival:
                                        fail("rival_label", f"Surviving rival {name} Python/Racket query differs at {index}:{pair_index}")
                                    if actual != pair["output"]:
                                        row["query_disagreements"].append(pair_index)
                                        fail("teaching_ambiguity", f"Rival {name} fits all demos but changes query {index}:{pair_index}",
                                             case={"episode_index": index, "split": "test", "pair_index": pair_index,
                                                   "settings": settings, "rival": name, "input": pair["input"],
                                                   "program": expected_program, "output": pair["output"],
                                                   "counterfactual_program": rival_program,
                                                   "counterfactual_output": actual,
                                                   "train": episode["train"]})
                                except Exception as exc:
                                    row["errors"].append({"split": "test", "pair_index": pair_index,
                                                          "error": f"{type(exc).__name__}: {exc}"})
                                    fail("rival_execution", f"Surviving rival {name} failed query {index}:{pair_index}: {exc}")
                        rows.append(row)
                    teaching.append({"episode_index": index, "settings": settings, "seed": seed,
                                     "projection_checks": projection, "rivals": rows})
        finally:
            bridge.close()

    if source_hashes() != before:
        fail("source_changed", "Relevant sources changed during audit; rerun from frozen bytes")
    exported = write_exports(episodes, output)
    checker = load_path(ROOT.parent / "check_public_exports.py")
    public_check = checker.inspect([output / "public"], queries=queries, demos=demos)
    if public_check["status"] != "passed":
        fail("saved_public", "Saved public files failed the packet conformance checker")
    report = {
        "schema": "arcpuzzles-f812a7b32f47-parametric-audit-v1",
        "status": "failed" if failures else "passed", "task_id": TASK,
        "seeds": seeds, "settings": list(SETTINGS), "counts": {"demos": demos, "queries": queries},
        "source_sha256": before, "racket": identity, "racket_evaluations": evaluations,
        "matched_inputs_across_settings": not any(f["code"] == "unmatched_inputs" for f in failures),
        "teaching": teaching, "public_files": exported, "public_file_check": public_check,
        "failures": failures, "native_qualification": "not_performed", "owner_acceptance": "not_performed",
        "training_admitted": False,
        "limits": "Finite declared rivals and seeds only; surviving rivals that agree on these queries are reported, not universally equivalent. First-turn projection verifies available content, not a controller implementation.",
    }
    if minimal is not None:
        write_json(output / "counterexample.private.json", minimal)
        report["counterexample"] = "counterexample.private.json"
    write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Fresh output directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=DEMOS)
    parser.add_argument("--queries", type=int, choices=range(1, 5), default=QUERIES)
    options = parser.parse_args(argv)
    # Never overwrite an existing report, even when setup or execution fails.
    if options.out.exists() or options.out.is_symlink():
        parser.error(f"Output already exists: {options.out}")
    try:
        report = run(options.out, options.seeds, options.demos, options.queries)
    except Exception as exc:
        report = {"schema": "arcpuzzles-f812a7b32f47-parametric-audit-v1", "status": "failed",
                  "task_id": TASK, "error": f"{type(exc).__name__}: {exc}",
                  "source_sha256": source_hashes(), "training_admitted": False,
                  "native_qualification": "not_performed", "owner_acceptance": "not_performed"}
        options.out.mkdir(parents=True, exist_ok=True)
        write_json(options.out / "report.json", report)
    print(json.dumps({"status": report["status"], "report": str(options.out / "report.json"),
                      "episodes": len(report.get("teaching", [])),
                      "failures": report.get("failures", []), "error": report.get("error")},
                     sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
