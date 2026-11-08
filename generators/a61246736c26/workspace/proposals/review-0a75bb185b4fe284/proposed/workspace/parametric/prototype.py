"""Proposed two-setting extension; not a production generator or approval API."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime
from puzzle_generators.base import gen_ctx
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

TASK = "a61246736c26"
VERSION = "1.0.0"
ROOT = find_root(__file__)
PROTOTYPE_DIR = Path(__file__).resolve().parent
DEFAULT_STROKE_SYMBOL = 2
ALLOWED_STROKE_SYMBOLS = (2, 8)
CANONICAL_RULE_HASH = "08238424436c"
PROFILE_ORDER = ("row_cycle_012", "permuted_frames", "four_columns_reverse", "shared_pattern")
_EXECUTION_RECEIPTS = []


def digest(value):
    data = value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def selected_rule():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [row for line in handle if (row := json.loads(line)).get("task_id") == TASK]
    if len(rows) != 1:
        raise ValueError("The prototype requires one exact selected canonical rule")
    program = rows[0]["program_solution"]
    if digest(" ".join(program.split()))[:12] != CANONICAL_RULE_HASH:
        raise ValueError("Canonical rule changed; reassess the proposed parameter before use")
    return program


def materialize_rule(stroke_symbol=DEFAULT_STROKE_SYMBOL):
    if type(stroke_symbol) is not int or stroke_symbol not in ALLOWED_STROKE_SYMBOLS:
        raise ValueError("stroke_symbol must be the literal integer 2 or 8")
    program = selected_rule()
    mapping = "(hash 1 frame 2 fill)"
    if program.count(mapping) != 1:
        raise ValueError("Expected exactly one canonical recoloring mapping")
    return program if stroke_symbol == 2 else program.replace(mapping, "(hash 1 frame 8 fill)", 1)


def setting_from_seed(seed):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK + "_parametric", difficulty=None, overrides={})
    return ctx.draw_choice("stroke_symbol", list(ALLOWED_STROKE_SYMBOLS))


def source_bindings():
    _module, source, generator_sha = load_selected_generator(TASK, root=ROOT)
    paths = [PROTOTYPE_DIR / "prototype.py", PROTOTYPE_DIR / "racket_worker.py", PROTOTYPE_DIR / "README.md",
             ROOT / "generators" / TASK / "tests/test_parametric_extension.py",
             canonical_path(ROOT), ROOT / "shared/runtime/arc_repl/racket_bridge.py",
             ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
             ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
             ROOT / "shared/runtime/reviewer_support.py"]
    return {"generator_path": source.relative_to(ROOT).as_posix(), "generator_sha256": generator_sha, "generator_version": _module.VERSION,
            "canonical_rule_text_sha256": digest(selected_rule()), "canonical_rule_hash": CANONICAL_RULE_HASH,
            "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path.read_bytes())}
                      for path in paths if path.is_file()]}


def execute_programs(programs, inputs):
    if not programs or not inputs:
        raise ValueError("Supply at least one program and input")
    inputs = [normalize_grid(grid) for grid in inputs]
    request = {"programs": dict(programs), "inputs": inputs}
    with tempfile.TemporaryDirectory(prefix="a61246736c26-parametric-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(ROOT), stage, TASK)
        command = [sys.executable, str(PROTOTYPE_DIR / "racket_worker.py")]
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env["PYTHONNOUSERSITE"] = "1"
        run = subprocess.run(command, cwd=stage, env=env, input=json.dumps(request),
                             text=True, capture_output=True, timeout=120)
        receipt = {"argv": command, "cwd": str(stage), "exit_code": run.returncode,
                   "runtime_manifest_sha256": digest(manifest), "request_sha256": digest(request),
                   "stdout_sha256": digest(run.stdout), "stderr": run.stderr,
                   "purpose": "Exact materialized rules executed by supplied wrap_rule and RacketBridge"}
        _EXECUTION_RECEIPTS.append(receipt)
        if run.returncode:
            receipt.update(stdout=run.stdout, request=request)
            raise RuntimeError("Racket worker failed: " + run.stderr)
        result = json.loads(run.stdout)
        result["outputs"] = {key: [normalize_grid(grid) for grid in values]
                             for key, values in result["outputs"].items()}
        if set(result["outputs"]) != set(programs) or any(len(values) != len(inputs) for values in result["outputs"].values()):
            raise RuntimeError("Incomplete Racket result")
        selected = [item for item in manifest["files"] if item["library_path"] == f"generators/{TASK}/generator.py"]
        result["generator_sha256"] = selected[0]["sha256"]
        result["runtime_manifest_sha256"] = digest(manifest)
        receipt["output_grid_hashes"] = {key: [digest(grid) for grid in values] for key, values in result["outputs"].items()}
        return result


def check_parameter_rivals(episode):
    pairs = episode["train"] + episode["test"]
    predictions = episode["executed_predictions"]
    selected = str(episode["parameters"]["stroke_symbol"])
    if set(predictions) != {str(value) for value in ALLOWED_STROKE_SYMBOLS}:
        raise ValueError("Every declared setting needs executed predictions")
    if any(len(values) != len(pairs) for values in predictions.values()):
        raise ValueError("Every setting needs every pair prediction")
    if predictions[selected] != [pair["output"] for pair in pairs]:
        raise ValueError("Episode outputs disagree with selected Racket labels")

    def score(demonstrations, queries):
        scored = []
        for value in ALLOWED_STROKE_SYMBOLS:
            values = predictions[str(value)]
            refuted = [index for index in demonstrations if values[index] != pairs[index]["output"]]
            differing = [index for index in queries if values[index] != pairs[index]["output"]]
            status = "refuted_by_demonstrations" if refuted else "ambiguous_query" if differing else "survived_all"
            scored.append({"parameters": {"stroke_symbol": value}, "status": status,
                           "refuting_demonstration_pair_indices": refuted,
                           "disagreeing_query_pair_indices": differing})
        return scored

    production = score(list(range(3)), [3])
    rotations = [{"query_pair_index": query, "demonstration_pair_indices": [index for index in range(4) if index != query],
                  "rivals": score([index for index in range(4) if index != query], [query])}
                 for query in range(4)]
    ambiguous = any(row["status"] == "ambiguous_query" for row in production)
    rotation_ambiguities = sum(any(row["status"] == "ambiguous_query" for row in rotation["rivals"]) for rotation in rotations)
    return {"declared_settings": [{"stroke_symbol": value} for value in ALLOWED_STROKE_SYMBOLS],
            "production": production, "query_rotations": rotations,
            "production_ambiguous": ambiguous, "ambiguous_query_rotations": rotation_ambiguities,
            "status": "ambiguity_found" if ambiguous or rotation_ambiguities else "no_ambiguity_found",
            "scope": "Only the two declared parameter settings; not all possible ARC hypotheses."}


def generate_episode(seed, *, difficulty="medium"):
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium or hard")
    # Exactly one rule draw. This value is reused for all demonstrations and the query.
    selected = setting_from_seed(seed)
    generator, _path, generator_sha = load_selected_generator(TASK, root=ROOT)
    inputs = [generator.generate(seed, index, difficulty=difficulty, scene_profile=profile)
              for index, profile in enumerate(PROFILE_ORDER)]
    for grid in inputs:
        errors = generator.self_check(grid, difficulty=difficulty)
        if errors:
            raise ValueError("Canonical generator rejected a prototype input: " + repr(errors))
    if len({digest(grid) for grid in inputs}) != 4:
        raise ValueError("Episode contains duplicate inputs")
    programs = {str(value): materialize_rule(value) for value in ALLOWED_STROKE_SYMBOLS}
    execution = execute_programs(programs, inputs)
    if execution["generator_sha256"] != generator_sha:
        raise RuntimeError("Generator changed during episode; rerun on stable source bytes")
    outputs = execution["outputs"][str(selected)]
    pairs = [{"input": grid, "output": copy.deepcopy(output)} for grid, output in zip(inputs, outputs, strict=True)]
    episode = {"schema": "a61246736c26-parametric-private-v1", "status": "prototype", "task_id": TASK,
               "seed": seed, "difficulty": difficulty, "prototype_version": VERSION,
               "parameters": {"stroke_symbol": selected},
               "parameter_selection": {"method": "GenCtx keyed draw_choice", "label": "stroke_symbol", "seed": seed,
                                       "sample_index": 0, "draw_count": 1, "sampled_once_per_episode": True,
                                       "allowed_values": list(ALLOWED_STROKE_SYMBOLS)},
               "demonstration_policy": {"n_train": 3, "n_test": 1, "profile_order": list(PROFILE_ORDER),
                                        "query_policy": "last pair; all four single-query holdouts additionally scored",
                                        "identifiability_scope": "declared stroke_symbol settings only"},
               "program": programs[str(selected)], "program_sha256": digest(programs[str(selected)]),
               "wrapped_program": execution["wrapped_programs"][str(selected)],
               "wrapped_program_sha256": digest(execution["wrapped_programs"][str(selected)]),
               "label_engine": execution["engine"], "racket_binary_sha256": execution["racket_binary_sha256"],
               "generator_sha256": generator_sha, "runtime_manifest_sha256": execution["runtime_manifest_sha256"],
               "sampling": [{"seed": seed, "sample_index": index, "scene_profile": profile,
                             "input_sha256": digest(grid)} for index, (profile, grid) in enumerate(zip(PROFILE_ORDER, inputs, strict=True))],
               "train": pairs[:3], "test": pairs[3:], "executed_predictions": execution["outputs"]}
    episode["parameter_checks"] = check_parameter_rivals(episode)
    return episode


def public_challenge(episode):
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]]}


def build_evidence(output, *, seeds=(0, 1), difficulties=("easy", "medium", "hard")):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    bindings = source_bindings()
    receipt_start = len(_EXECUTION_RECEIPTS)

    def write(relative, value):
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    try:
        programs = {str(value): materialize_rule(value) for value in ALLOWED_STROKE_SYMBOLS}
        canonical = canonical_pairs(TASK, root=ROOT)
        # A retained canonical input is a lawful, source-bound distinguishing witness.
        probe_inputs = [pair["input"] for pair in canonical]
        probe = execute_programs(programs, probe_inputs)
        program_records = []
        for value in ALLOWED_STROKE_SYMBOLS:
            relative = f"programs/stroke-{value}.rkt"
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(programs[str(value)], encoding="utf-8")
            wrapped_relative = f"programs/stroke-{value}.callable.rkt"
            (output / wrapped_relative).write_text(probe["wrapped_programs"][str(value)], encoding="utf-8")
            program_records.append({"parameters": {"stroke_symbol": value}, "path": relative,
                                    "sha256": digest(programs[str(value)]), "wrapped_path": wrapped_relative,
                                    "wrapped_sha256": digest(probe["wrapped_programs"][str(value)])})
        default_check = {"all_match": probe["outputs"]["2"] == [pair["output"] for pair in canonical],
                         "pairs_checked": len(canonical), "pairs": canonical,
                         "executed_outputs": probe["outputs"]["2"], "engine": "RacketBridge"}
        distinguishing = {"input": probe_inputs[0], "input_sha256": digest(probe_inputs[0]),
                          "outputs": {key: values[0] for key, values in probe["outputs"].items()},
                          "different_outputs": probe["outputs"]["2"][0] != probe["outputs"]["8"][0],
                          "engine": "RacketBridge", "lawful_source": "first selected canonical labeled input"}
        write("canonical-default.json", default_check)
        write("distinguishing-input.json", distinguishing)
        episodes = []
        settings = set()
        production_ambiguous = rotation_ambiguous = 0
        input_hashes = set()
        for difficulty in difficulties:
            for seed in seeds:
                episode = generate_episode(seed, difficulty=difficulty)
                number = len(episodes) + 1
                private = f"private/episode-{number:03d}.json"
                public = f"public/challenge-{number:03d}.json"
                write(private, episode)
                write(public, public_challenge(episode))
                settings.add(episode["parameters"]["stroke_symbol"])
                input_hashes.update(row["input_sha256"] for row in episode["sampling"])
                checks = episode["parameter_checks"]
                production_ambiguous += int(checks["production_ambiguous"])
                rotation_ambiguous += checks["ambiguous_query_rotations"]
                episodes.append({"seed": seed, "difficulty": difficulty, "parameters": episode["parameters"],
                                 "private_path": private, "public_path": public,
                                 "program_sha256": episode["program_sha256"], "parameter_check_status": checks["status"]})
        if bindings != source_bindings():
            raise RuntimeError("Source files changed during evidence generation; retain this attempt and rerun")
        covered = settings == set(ALLOWED_STROKE_SYMBOLS)
        passed = covered and default_check["all_match"] and distinguishing["different_outputs"] and not production_ambiguous and not rotation_ambiguous
        write("execution-receipts.json", _EXECUTION_RECEIPTS[receipt_start:])
        count = len(episodes)
        report = {"schema": "a61246736c26-parametric-evidence-v1", "status": "prototype_pass" if passed else "prototype_incomplete_or_failed",
                  "task_id": TASK, "prototype_version": VERSION, "source_bindings": bindings,
                  "parameter_contract": {"name": "stroke_symbol", "allowed_values": [2, 8], "canonical_default": 2,
                                         "draw_frequency": "once per seeded episode", "input_constraints_change": False,
                                         "meaning": "Solid fill replaces the selected pattern symbol; other symbol is preserved."},
                  "programs": program_records, "seeds": list(seeds), "difficulties": list(difficulties),
                  "demonstration_policy": {"train": 3, "test": 1, "profile_order": list(PROFILE_ORDER),
                                           "production_query_index": 3, "query_holdouts_checked": [0, 1, 2, 3]},
                  "summary": {"episodes": count, "labeled_pairs": count * 4, "unique_input_grids": len(input_hashes),
                              "settings_observed": sorted(settings), "all_declared_settings_covered": covered,
                              "production_rival_checks": count * 2, "production_ambiguous_episodes": production_ambiguous,
                              "query_rotations": count * 4, "query_rotation_rival_checks": count * 8,
                              "ambiguous_query_rotations": rotation_ambiguous,
                              "racket_grid_applications": count * 8 + len(canonical) * 2},
                  "canonical_default": {"path": "canonical-default.json", "all_match": default_check["all_match"], "pairs_checked": len(canonical)},
                  "distinguishing_input": {"path": "distinguishing-input.json", "different_outputs": distinguishing["different_outputs"]},
                  "episodes": episodes,
                  "limitations": ["Separate proposed prototype; no canonical rule, runtime API or approval was changed.",
                                  "Finite seeds and declared settings only. No claim about all ARC hypotheses or all random inputs.",
                                  "Three fixed demonstrations and one query; all four holdouts tested against parameter rivals only.",
                                  "Input profiles are an explicit bounded authoring curriculum, not production distribution evidence."],
                  "artifact_manifest": [{"path": path.relative_to(output).as_posix(), "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
                                        for path in sorted(output.rglob("*")) if path.is_file()]}
        write("report.json", report)
        return report
    except Exception as exc:
        write("error.json", {"status": "error", "type": type(exc).__name__, "message": str(exc),
                             "source_bindings": bindings, "execution_receipts": _EXECUTION_RECEIPTS[receipt_start:]})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New evidence directory; existing paths are refused")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--difficulty", action="append", choices=("easy", "medium", "hard"), dest="difficulties")
    args = parser.parse_args(argv)
    report = build_evidence(args.out, seeds=tuple(args.seeds or (0, 1)),
                            difficulties=tuple(args.difficulties or ("easy", "medium", "hard")))
    print(json.dumps({"status": report["status"], "summary": report["summary"], "report": str(args.out / "report.json")}, indent=2))
    return 0 if report["status"] == "prototype_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
