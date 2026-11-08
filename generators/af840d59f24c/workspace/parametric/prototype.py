#!/usr/bin/env python3
"""Task-local, unapproved rule-parameter prototype for global zero-group ranks.

All labels and parameter-rival predictions come from the included Racket
bridge. No Python implementation of the output transform supplies labels.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import traceback

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "af840d59f24c"
VERSION = "0.1.0-prototype"
ROOT = find_root(__file__)
INPUT_PROFILES = ("canonical_sparse", "scrambled_order")
N_TRAIN, N_TEST = 4, 1


@dataclass(frozen=True)
class Parameters:
    grouping_axis: str = "columns"
    direction: str = "forward"

    def __post_init__(self):
        if type(self.grouping_axis) is not str or type(self.direction) is not str:
            raise TypeError("parameters must be strings")
        if self.grouping_axis not in ("columns", "rows"):
            raise ValueError("grouping_axis must be columns or rows")
        if self.direction not in ("forward", "reverse"):
            raise ValueError("direction must be forward or reverse")

    @property
    def key(self):
        return f"{self.grouping_axis}-{self.direction}"

    def as_dict(self):
        return {"grouping_axis": self.grouping_axis, "direction": self.direction}


SETTINGS = tuple(Parameters(axis, direction)
                 for axis in ("columns", "rows")
                 for direction in ("forward", "reverse"))
DEFAULT = SETTINGS[0]


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def json_sha256(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _seed(seed):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a coerced scalar")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def choose_parameters(seed):
    """Choose the hidden rule exactly once, independently of the input draws."""
    key = sha256(f"{TASK_ID}:{VERSION}:rule:{_seed(seed)}".encode())
    return SETTINGS[random.Random(int(key, 16)).randrange(len(SETTINGS))]


def canonical_authority(root=ROOT):
    path = canonical_path(root)
    programs = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK_ID:
                    programs.append(record["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise ValueError("selected canonical program is missing or text-ambiguous")
    program = programs[0]
    return {"program": program, "program_sha256": sha256(program.encode()),
            "normalized_rule_hash": sha256(" ".join(program.split()).encode())[:12],
            "ledger_sha256": sha256(path.read_bytes())}


def emit_program(parameters=DEFAULT, *, root=ROOT):
    """Derive four nearby rules; canonical/default returns the exact authority."""
    if not isinstance(parameters, Parameters):
        raise TypeError("use validated Parameters")
    program = canonical_authority(root)["program"]
    collection = "(map snd zeros)"
    comparison = "(lambda (c) (< c (snd p)))"
    if program.count(collection) != 1 or program.count(comparison) != 1:
        raise ValueError("canonical authority changed; re-review this prototype's derivation")
    coordinate = "snd" if parameters.grouping_axis == "columns" else "fst"
    ordering = "<" if parameters.direction == "forward" else ">"
    return program.replace(collection, f"(map {coordinate} zeros)").replace(
        comparison, f"(lambda (c) ({ordering} c ({coordinate} p)))")


def sample_inputs(seed, *, root=ROOT):
    """A common input distribution for all four rules, with bounded rejection.

    Both oriented canonical validators must accept each input. Consequently all
    parameter rivals have 4..8 groups and stay inside the ARC color alphabet.
    The parameter setting is deliberately absent from this function's API.
    """
    _seed(seed)
    generator, _, source_hash = load_selected_generator(TASK_ID, root=root)
    grids, draws, rejected, seen = [], [], [], set()
    for sample_index in range(80):
        profile = INPUT_PROFILES[sample_index % len(INPUT_PROFILES)]
        grid = generator.generate(seed, sample_index, difficulty="medium", scene_profile=profile)
        transpose = [list(row) for row in zip(*grid)]
        errors = generator.self_check(grid) + generator.self_check(transpose)
        digest = json_sha256(grid)
        if digest in seen:
            errors.append("duplicate input within episode")
        if errors:
            rejected.append({"sample_index": sample_index, "scene_profile": profile,
                             "input_sha256": digest, "reasons": errors})
            continue
        seen.add(digest)
        grids.append(grid)
        draws.append({"sample_index": sample_index, "scene_profile": profile,
                      "difficulty": "medium", "input_sha256": digest})
        if len(grids) == N_TRAIN + N_TEST:
            return {"grids": grids, "draws": draws, "rejected": rejected,
                    "generator_sha256": source_hash}
    raise ValueError(f"could not draw {N_TRAIN + N_TEST} distinct lawful inputs: {rejected}")


_WORKER = r'''
import hashlib
import json
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule

request = json.loads(Path("request.json").read_text())
result = {"outputs": {}, "programs": {}, "backend": "RacketBridge",
          "runtime": racket_runtime_status()}
with RacketBridge(timeout=20.0) as bridge:
    for key, program in request["programs"].items():
        callable_text = wrap_rule(program)
        bridge.eval_text("(define __parametric_rule " + callable_text + ")")
        outputs = []
        for grid in request["grids"]:
            bridge.define_grid("__parametric_input", grid)
            output = bridge.eval_text("(__parametric_rule __parametric_input)")
            if (not isinstance(output, list) or len(output) != len(grid)
                    or any(not isinstance(row, list) or len(row) != len(grid[0])
                           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                           for row in output)):
                raise ValueError("Racket output is not a same-shape ARC grid: " + key)
            outputs.append(output)
        result["outputs"][key] = outputs
        result["programs"][key] = {
            "source": program,
            "source_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "callable_text": callable_text,
            "callable_sha256": hashlib.sha256(callable_text.encode()).hexdigest()}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
'''


def execute_programs(programs, grids, *, root=ROOT):
    """Execute exact emitted sources in one isolated, selected local runtime."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    if not programs or not grids:
        raise ValueError("nonempty programs and inputs are required")
    with tempfile.TemporaryDirectory(prefix="af840-parametric-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(root), stage, TASK_ID)
        (stage / "request.json").write_text(json.dumps({"programs": programs, "grids": grids}))
        (stage / "execute.py").write_text(_WORKER)
        command = [sys.executable, "-B", "execute.py"]
        process = run_process(command, stage, timeout=180)
        if process["exit_code"] != 0 or process["timed_out"]:
            raise RuntimeError("Racket execution failed: " + json.dumps(process))
        result = json.loads(process["stdout"])
        result["worker"] = {"argv": command, "cwd": str(stage),
                            "exit_code": process["exit_code"],
                            "runtime_manifest_sha256": json_sha256(manifest),
                            "runtime_files": len(manifest["files"]),
                            "source_sha256": sha256(_WORKER.encode()),
                            "selected_generator_sha256": next(
                                row["sha256"] for row in manifest["files"]
                                if row["library_path"] == f"generators/{TASK_ID}/generator.py")}
        result["grids"] = grids
        result["executed_labels"] = len(programs) * len(grids)
        return result


def public_challenge(episode):
    """Whitelisted projection: no seed, parameters, program or query answer."""
    return {"train": [{"input": pair["input"], "output": pair["output"]}
                      for pair in episode["train"]],
            "test": [{"input": pair["input"]} for pair in episode["test"]]}


def rival_assessment(outputs, selected_key, demo_indices, query_indices):
    result = []
    truth = outputs[selected_key]
    for setting in SETTINGS:
        if setting.key == selected_key:
            continue
        predictions = outputs[setting.key]
        refuting = [index for index in demo_indices if predictions[index] != truth[index]]
        changing = [index for index in query_indices if predictions[index] != truth[index]]
        status = "refuted" if refuting else "ambiguous" if changing else "survived_all"
        result.append({"rival": setting.key, "status": status,
                       "refuting_demo_indices": refuting, "different_query_indices": changing})
    return result


def _sources(root):
    _, selected, digest = load_selected_generator(TASK_ID, root=root)
    home = Path(__file__).resolve().parent
    paths = {"prototype.py": home / "prototype.py", "README.md": home / "README.md",
             "test_parametric.py": home.parent.parent / "tests/test_parametric.py",
             "generator.py": selected, "canonical_ledger": canonical_path(root)}
    return {key: {"path": str(path.relative_to(root)), "sha256": sha256(path.read_bytes())}
            for key, path in paths.items()}


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def build_evidence(out, *, seed=17, root=ROOT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    sources = _sources(root)
    authority = canonical_authority(root)
    generator, _, source_hash = load_selected_generator(TASK_ID, root=root)
    if authority["normalized_rule_hash"] != generator.RULE_HASH:
        raise ValueError("canonical rule pin disagrees with the selected generator")
    chosen = {}
    for candidate_seed in range(_seed(seed), seed + 256):
        setting = choose_parameters(candidate_seed)
        chosen.setdefault(setting.key, candidate_seed)
        if len(chosen) == len(SETTINGS):
            break
    if len(chosen) != len(SETTINGS):
        raise ValueError("bounded seed search did not cover every parameter setting")

    programs = {setting.key: emit_program(setting, root=root) for setting in SETTINGS}
    programs["canonical_reference"] = authority["program"]
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    grids = [pair["input"] for pair in canonical]
    cases = [{"kind": "canonical", "variant": pair["variant"],
              "split": pair["split"], "pair_index": pair["pair_index"]} for pair in canonical]
    # Default-only parity controls exercise all canonical sampler profiles.
    controls = []
    for control_seed in (0, 17):
        for profile in generator.PROFILES:
            grid = generator.generate(control_seed, 0, difficulty="medium", scene_profile=profile)
            controls.append({"input": grid, "seed": control_seed, "scene_profile": profile})
    # Alternative rows rules are deliberately not evaluated on dense controls,
    # whose number of zero rows can exceed the ARC alphabet. Separate execution
    # preserves this domain boundary instead of silently clipping ranks.
    episode_draws = []
    # Public filenames are numbered in seed order, not by a fixed parameter
    # enumeration that would reveal the hidden rule from the filename alone.
    for setting in sorted(SETTINGS, key=lambda value: chosen[value.key]):
        episode_seed = chosen[setting.key]
        draw = sample_inputs(episode_seed, root=root)
        if draw["generator_sha256"] != source_hash:
            raise ValueError("generator source changed during episode construction")
        indices = list(range(len(grids), len(grids) + len(draw["grids"])))
        grids.extend(draw["grids"])
        cases.extend({"kind": "episode", "seed": episode_seed, "position": i}
                     for i in range(len(draw["grids"])))
        episode_draws.append((setting, episode_seed, draw, indices))

    # Canonical examples in this task are legal under all four settings.
    for index, grid in enumerate(grids):
        for axis in (0, 1):
            count = len({(r, c)[axis] for r, row in enumerate(grid)
                         for c, value in enumerate(row) if value == 0})
            if not 1 <= count <= 9:
                raise ValueError(f"case {index} is outside the rival comparison domain")
    execution = execute_programs(programs, grids, root=root)
    execution["cases"] = cases
    control_execution = execute_programs(
        {key: programs[key] for key in (DEFAULT.key, "canonical_reference")},
        [case["input"] for case in controls], root=root)
    control_execution["cases"] = [{key: value for key, value in row.items() if key != "input"}
                                  for row in controls]
    if any(run["worker"]["selected_generator_sha256"] != source_hash
           for run in (execution, control_execution)) or _sources(root) != sources:
        raise ValueError("source changed while preparing or executing evidence")
    parity = (execution["outputs"][DEFAULT.key][:len(canonical)] == [pair["output"] for pair in canonical]
              and execution["outputs"][DEFAULT.key] == execution["outputs"]["canonical_reference"]
              and control_execution["outputs"][DEFAULT.key] == control_execution["outputs"]["canonical_reference"])
    if not parity:
        raise ValueError("default parity failed")

    episodes, lessons = [], []
    for ordinal, (setting, episode_seed, draw, indices) in enumerate(episode_draws):
        outputs = execution["outputs"][setting.key]
        pairs = [{"input": grids[index], "output": outputs[index]} for index in indices]
        episode = {"seed": episode_seed, "parameters": setting.as_dict(),
                   "program": programs[setting.key], "program_sha256": sha256(programs[setting.key].encode()),
                   "generator_sha256": source_hash, "train": pairs[:N_TRAIN], "test": pairs[N_TRAIN:],
                   "sampling": {key: value for key, value in draw.items() if key != "grids"},
                   "execution_case_indices": indices}
        episodes.append(episode)
        production = rival_assessment(execution["outputs"], setting.key, indices[:N_TRAIN], indices[N_TRAIN:])
        rotations = [{"query_position": position,
                      "rivals": rival_assessment(execution["outputs"], setting.key,
                                                  [i for i in indices if i != query], [query])}
                     for position, query in enumerate(indices)]
        lessons.append({"episode_index": ordinal, "seed": episode_seed, "setting": setting.key,
                        "production": production, "rotations": rotations})
        _write_json(out / "public" / f"challenge-{ordinal:02d}.json", public_challenge(episode))

    witness_index = episode_draws[0][3][0]
    witness_outputs = {setting.key: execution["outputs"][setting.key][witness_index] for setting in SETTINGS}
    contrast = {"input": grids[witness_index], "case_index": witness_index,
                "lawful_under_canonical_validator": not generator.self_check(grids[witness_index]),
                "lawful_when_transposed": not generator.self_check([list(row) for row in zip(*grids[witness_index])]),
                "outputs": witness_outputs, "distinct_outputs": len({json_sha256(g) for g in witness_outputs.values()})}
    summary = {"episodes": len(episodes), "demonstrations_per_episode": N_TRAIN, "queries_per_episode": N_TEST,
               "parameter_rivals_checked": sum(len(row["production"]) for row in lessons),
               "parameter_rivals_refuted": sum(r["status"] == "refuted" for row in lessons for r in row["production"]),
               "production_ambiguities": sum(r["status"] == "ambiguous" for row in lessons for r in row["production"]),
               "rotation_queries": sum(len(row["rotations"]) for row in lessons),
               "rotation_rivals_checked": sum(len(rot["rivals"]) for row in lessons for rot in row["rotations"]),
               "rotation_rivals_refuted": sum(r["status"] == "refuted" for row in lessons for rot in row["rotations"] for r in rot["rivals"]),
               "rotation_ambiguities": sum(r["status"] == "ambiguous" for row in lessons for rot in row["rotations"] for r in rot["rivals"]),
               "canonical_labels_checked": len(canonical), "generated_default_parity_controls": len(controls),
               "executed_racket_labels": execution["executed_labels"] + control_execution["executed_labels"],
               "unique_inputs": len({json_sha256(g) for g in grids + [case["input"] for case in controls]}),
               "default_parity": parity, "contrast_distinct_outputs": contrast["distinct_outputs"]}
    status = "passed" if (parity and summary["parameter_rivals_refuted"] == 12
                          and summary["rotation_ambiguities"] == 0 and contrast["distinct_outputs"] == 4) else "failed"
    report = {"schema": "af840-parametric-prototype-v1", "status": status, "scope": "unapproved prototype",
              "version": VERSION, "task_id": TASK_ID, "source_hashes": sources,
              "canonical_authority": authority, "seed_search_start": seed,
              "parameter_space": [setting.as_dict() for setting in SETTINGS], "default": DEFAULT.as_dict(),
              "summary": summary, "lessons": lessons,
              "limitations": ["Four episodes from explicitly recorded seeds, not exhaustive seed coverage.",
                              "Rivals are the other three parameter settings; no claim about arbitrary programs.",
                              "Prototype input sampling uses two sparse profiles and validates both orientations.",
                              "Canonical production API, rule authority and approval records are unchanged."]}
    for key, program in programs.items():
        path = out / "programs" / f"{key}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program)
    for name, value in (("execution.json", execution), ("default-parity.json", control_execution),
                        ("episodes.private.json", episodes), ("contrast.json", contrast), ("report.json", report)):
        _write_json(out / name, value)
    manifest = {"schema": "af840-parametric-assets-v1", "files": {
        path.relative_to(out).as_posix(): sha256(path.read_bytes())
        for path in sorted(out.rglob("*")) if path.is_file()}}
    _write_json(out / "manifest.json", manifest)
    return report


def verify_evidence(out, *, root=ROOT):
    """Hash-check sources/assets, redraw seed-fixed episodes, rerun exact Racket."""
    out = Path(out)
    manifest = json.loads((out / "manifest.json").read_text())
    for relative, digest in manifest["files"].items():
        path = out / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(out.resolve()):
            raise ValueError(f"unsafe evidence asset path: {relative}")
        if not path.is_file() or sha256(path.read_bytes()) != digest:
            raise ValueError(f"asset hash mismatch: {relative}")
    report = json.loads((out / "report.json").read_text())
    if report["status"] != "passed":
        raise ValueError("retained evidence reports an unsuccessful experiment")
    current = _sources(root)
    if {key: row["sha256"] for key, row in current.items()} != {
            key: row["sha256"] for key, row in report["source_hashes"].items()}:
        raise ValueError("source hash mismatch: regenerate evidence after a source change")
    compared = 0
    for filename in ("execution.json", "default-parity.json"):
        saved = json.loads((out / filename).read_text())
        bank = {key: row["source"] for key, row in saved["programs"].items()}
        for key, program in bank.items():
            expected = canonical_authority(root)["program"] if key == "canonical_reference" else emit_program(
                next(setting for setting in SETTINGS if setting.key == key), root=root)
            if program != expected or (out / "programs" / f"{key}.rkt").read_text() != expected:
                raise ValueError("program derivation mismatch: " + key)
        replay = execute_programs(bank, saved["grids"], root=root)
        if replay["outputs"] != saved["outputs"] or replay["programs"] != saved["programs"]:
            raise ValueError("Racket replay mismatch: " + filename)
        if replay["worker"]["selected_generator_sha256"] != current["generator.py"]["sha256"]:
            raise ValueError("runtime selected source differs from the evidence source")
        compared += replay["executed_labels"]
    execution = json.loads((out / "execution.json").read_text())
    episodes = json.loads((out / "episodes.private.json").read_text())
    for index, episode in enumerate(episodes):
        setting = choose_parameters(episode["seed"])
        if setting.as_dict() != episode["parameters"]:
            raise ValueError("episode parameter selection changed")
        program = emit_program(setting, root=root)
        if (episode["program"] != program or episode["program_sha256"] != sha256(program.encode())
                or episode["generator_sha256"] != current["generator.py"]["sha256"]):
            raise ValueError("episode source identity changed")
        pairs = episode["train"] + episode["test"]
        drawn = sample_inputs(episode["seed"], root=root)
        if drawn["grids"] != [pair["input"] for pair in pairs]:
            raise ValueError("episode input replay changed")
        if {key: value for key, value in drawn.items() if key != "grids"} != episode["sampling"]:
            raise ValueError("episode sampling receipt changed")
        expected_outputs = [execution["outputs"][setting.key][i] for i in episode["execution_case_indices"]]
        if expected_outputs != [pair["output"] for pair in pairs]:
            raise ValueError("episode labels do not match executed Racket")
        public = json.loads((out / "public" / f"challenge-{index:02d}.json").read_text())
        if public != public_challenge(episode):
            raise ValueError("public challenge is not the masked episode")
        indices = episode["execution_case_indices"]
        if rival_assessment(execution["outputs"], setting.key, indices[:N_TRAIN], indices[N_TRAIN:]) != report["lessons"][index]["production"]:
            raise ValueError("retained rival assessment differs from executed outputs")
        rotations = [{"query_position": position,
                      "rivals": rival_assessment(execution["outputs"], setting.key,
                                                  [i for i in indices if i != query], [query])}
                     for position, query in enumerate(indices)]
        if rotations != report["lessons"][index]["rotations"]:
            raise ValueError("retained rotation assessment differs from executed outputs")
    if _sources(root) != current:
        raise ValueError("source changed during replay")
    return {"schema": "af840-parametric-replay-v1", "status": "passed",
            "source_hashes_match": True, "all_outputs_identical": True,
            "executed_racket_labels": compared, "episodes_replayed": len(episodes),
            "public_challenges_masked": len(episodes), "source_hashes": current,
            "evidence_manifest_sha256": sha256((out / "manifest.json").read_bytes())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="materialize all four settings with Racket labels")
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify", help="source-bound exact-Racket evidence replay")
    verify.add_argument("--evidence", type=Path, required=True)
    verify.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output path must be new; retain previous attempts")
    try:
        if args.command == "build":
            report = build_evidence(args.out, seed=args.seed)
        else:
            report = verify_evidence(args.evidence)
            _write_json(args.out, report)
        print(json.dumps({"status": report["status"], "out": str(args.out),
                          "summary": report.get("summary", {"executed_racket_labels": report["executed_racket_labels"]}
                                                if "executed_racket_labels" in report else {})}, sort_keys=True))
        return 0 if report["status"] == "passed" else 1
    except Exception as exc:
        failure = {"status": "failed", "error": repr(exc), "traceback": traceback.format_exc(),
                   "argv": sys.argv, "cwd": str(Path.cwd())}
        failure_path = args.out / "failure.json" if args.command == "build" else args.out
        _write_json(failure_path, failure)
        print(failure["traceback"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
