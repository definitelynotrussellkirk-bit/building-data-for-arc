"""Bounded protected-Racket audit of the source-qualified parametric prototype.

Run through the packet's review.py run wrapper. Qualification is an input to
this tool; this tool neither qualifies nor accepts a generator. Every output
directory must be new, and all retained rule programs and query banks are private.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from arcpuzzles import Catalog
from arcpuzzles.parametric_promotion import _check_execution, _ready, settings_space
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from arcpuzzles.review_parametric_admission import validate_sequential_witness


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "0083f06314c3"
EXPECTED_SETTINGS = ({"orientation": "fixed"}, {"orientation": "rotations"})
MAX_EVALUATIONS = 150
BOUNDARY_SEED = 23


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def program_hash(program):
    if type(program) is not str or not program.strip():
        raise ValueError("Expected nonempty exact Racket program text")
    return hashlib.sha256(program.encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    with Path(path).open("xb") as handle:
        handle.write(raw(value))


def load_prototype():
    path = HERE / "prototype.py"
    require(path.is_file() and not path.is_symlink() and path.resolve() == path,
            "Prototype must be a regular file in this exact task home")
    name = "_template_parametric_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for name in ("generate", "program", "rule_mirror", "rival_programs",
                 "rival_outputs", "teaching_check", "dependency_intermediate", "export_batch"):
        require(callable(getattr(module, name, None)), "Missing prototype API: " + name)
    return module


def pairs(episode, split, count):
    values = episode.get(split)
    require(type(values) is list and len(values) == count,
            f"Expected exactly {count} {split} pairs")
    return [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
            for pair in values]


def check_source(binding, contract):
    for name in ("arcpuzzles.parametric_promotion", "arcpuzzles.parametric_worker",
                 "arcpuzzles.review_parametric_admission"):
        require(Path(sys.modules[name].__file__).resolve().is_relative_to(ROOT / "src/arcpuzzles"),
                "Native verifier was imported from a different checkout")
    live_contract, live_binding = _ready(Catalog(ROOT), TASK_ID)
    require(live_binding == binding and live_contract == contract,
            "Current source closure/contract differs from native qualification")


def qualification_inputs(path):
    path = Path(path).resolve()
    qualification = json.loads(path.read_bytes())
    require(qualification.get("schema") == "arcpuzzles-parametric-qualification-v1"
            and qualification.get("status") == "qualified"
            and qualification.get("task_id") == TASK_ID,
            "A successful native qualification for this task is required")
    binding, contract = qualification["source_binding"], qualification["contract"]
    check_source(binding, contract)
    require(qualification["execution"].get("path") == "execution.json",
            "Expected native sibling execution.json")
    execution_path = path.parent / "execution.json"
    require(not execution_path.is_symlink()
            and file_hash(execution_path) == qualification["execution"]["sha256"],
            "Native execution receipt is missing or changed")
    execution = json.loads(execution_path.read_bytes())
    require(_check_execution(execution, qualification["jobs"], binding, contract)
            == qualification["programs"], "Native program inventory differs")
    episodes = copy.deepcopy(execution["episodes"])
    require(len(episodes) == 4, "Audit expects four qualified episodes (two seeds per setting)")
    expected_settings = {raw(setting) for setting in EXPECTED_SETTINGS}
    require({raw(episode["settings"]) for episode in episodes} == expected_settings,
            "Qualified episodes must cover exactly fixed and rotations settings")
    seeds_by_setting = []
    for setting in EXPECTED_SETTINGS:
        selected = [episode for episode in episodes if episode["settings"] == setting]
        require(len(selected) == 2 and all(type(episode["seed"]) is int for episode in selected),
                "Expected two native episodes with integer seeds per setting")
        seeds = {episode["seed"] for episode in selected}
        require(len(seeds) == 2, "Native qualification must use two distinct seeds per setting")
        seeds_by_setting.append(seeds)
    require(seeds_by_setting[0] == seeds_by_setting[1],
            "Native qualification must use the same two seeds for both settings")
    for episode in episodes:
        episode["train"] = pairs(episode, "train", 3)
        episode["test"] = pairs(episode, "test", 4)
        episode["program_solution"] = episode["program"]
    return qualification, execution, episodes, execution_path


def check_export(prototype, episodes, output):
    output = Path(output).resolve()
    require(not output.exists() and not output.is_symlink(), "Export directory must be new")
    prototype.export_batch(copy.deepcopy(episodes), output)
    from reviewer_support import public_challenge_bytes

    expected = {}
    for episode in episodes:
        visible = {"train": episode["train"],
                   "test": [{"input": episode["test"][0]["input"]}]}
        payload = public_challenge_bytes(visible)
        identifier = hashlib.sha256(payload).hexdigest()
        require(identifier not in expected, "Duplicate first-turn public challenge")
        expected[identifier] = (payload, episode)
    for folder in ("public", "private"):
        files = sorted((output / folder).iterdir())
        require(all(p.is_file() and not p.is_symlink() for p in files)
                and {p.name for p in files} == {key + ".json" for key in expected},
                "Export must contain exactly one matching public/private file per episode")
    for identifier, (payload, episode) in expected.items():
        require((output / "public" / (identifier + ".json")).read_bytes() == payload,
                "Public file differs from the canonical first-query projection")
        private = json.loads((output / "private" / (identifier + ".json")).read_bytes())
        require(pairs(private, "train", 3) == episode["train"]
                and pairs(private, "test", 4) == episode["test"],
                "Private export must preserve every Racket-labeled query in order")
        require(private.get("settings") == episode["settings"],
                "Private export lost its fixed episode setting")
        exported_program = private.get("program_solution", private.get("program"))
        require(exported_program == episode["program"], "Private export program changed")
    checker = ROOT.parent / "check_public_exports.py"
    completed = subprocess.run(
        [sys.executable, str(checker), str(output / "public"), "--queries", "1", "--demos", "3"],
        capture_output=True, text=True, timeout=60,
    )
    require(completed.returncode == 0,
            "Public-file checker failed: " + completed.stdout[-1500:] + completed.stderr[-500:])
    receipt = json.loads(completed.stdout)
    require(receipt.get("status") == "passed" and receipt.get("files_checked") == 4,
            "Public-file checker did not verify all four projections")
    return {"path": str(output), "episodes": 4, "public_queries_per_episode": 1,
            "private_queries_per_episode": 4, "private_labels": 28,
            "label_source": "Hash-verified native execution receipt; not re-executed for export",
            "public_checker_sha256": file_hash(checker), "public_checker": receipt}


def audit(qualification_path, output, export=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "arcpuzzles-parametric-bounded-audit-v1", "task_id": TASK_ID,
              "status": "running", "racket_evaluations": 0,
              "evaluation_limit": MAX_EVALUATIONS, "executions": [],
              "boundary_checks": [], "teaching_checks": [], "failures": [],
              "training_admitted": False,
              "limits": ["Finite settings, seeds and named rivals only; no universal uniqueness claim.",
                         "This audit does not grant native qualification or acceptance.",
                         "Rival survival is computed from demonstrations alone; query labels are checked afterwards."]}
    bridge = None
    try:
        q, native, episodes, execution_path = qualification_inputs(qualification_path)
        binding, contract = q["source_binding"], q["contract"]
        report.update(source_binding=copy.deepcopy(binding),
                      audit_source_sha256=file_hash(Path(__file__)),
                      qualification={"path": str(Path(qualification_path).resolve()),
                                     "sha256": file_hash(qualification_path),
                                     "execution_path": str(execution_path),
                                     "execution_sha256": file_hash(execution_path),
                                     "reused_episodes": len(episodes),
                                     "reported_racket_evaluations": native["racket_evaluations"]})
        runtime = ROOT / "shared/runtime"
        with _local_imports(runtime, HERE):
            prototype = load_prototype()
            settings = settings_space(contract)
            require(len(settings) == 2 and {raw(s) for s in settings}
                    == {raw(s) for s in prototype.SETTINGS}
                    == {raw(s) for s in EXPECTED_SETTINGS},
                    "Declared settings differ from fixed/rotations prototype settings")
            programs = {raw(setting): prototype.program(copy.deepcopy(setting)) for setting in settings}
            for key, program in programs.items():
                require(q["programs"].get(key.decode().strip()) == program_hash(program),
                        "Prototype setting program differs from native qualification")
            for episode in episodes:
                require(episode["program"] == programs[raw(episode["settings"])],
                        "Qualified episode uses a different program")
                for pair in episode["train"] + episode["test"]:
                    require(_grid(prototype.rule_mirror(copy.deepcopy(pair["input"]),
                                                       copy.deepcopy(episode["settings"]))) == pair["output"],
                            "Python mirror differs from a qualified Racket label")
            report["native_python_label_comparisons"] = sum(
                len(ep["train"]) + len(ep["test"]) for ep in episodes)
            apply, identity, bridge = _real_evaluator(runtime)
            report["racket"] = identity

            def execute(program, grid, scope):
                require(report["racket_evaluations"] < MAX_EVALUATIONS,
                        "Bounded Racket evaluation budget exceeded")
                report["racket_evaluations"] += 1
                row = {"scope": scope, "program_sha256": program_hash(program),
                       "input_sha256": digest(_grid(grid))}
                report["executions"].append(row)
                result = _grid(apply(program, copy.deepcopy(grid)))
                row["output_sha256"] = digest(result)
                return result

            boundary_episodes = []
            for setting in settings:
                program = programs[raw(setting)]
                for demos in (2, 6):
                    generated = prototype.generate(BOUNDARY_SEED, copy.deepcopy(setting),
                                                   demos=demos, queries=4)
                    require(generated.get("program_solution") == program,
                            "Boundary episode changed its setting program")
                    episode = {"task_id": TASK_ID, "seed": BOUNDARY_SEED,
                               "settings": copy.deepcopy(setting), "program": program,
                               "program_sha256": program_hash(program),
                               "train": pairs(generated, "train", demos),
                               "test": pairs(generated, "test", 4)}
                    require(len({digest(p["input"]) for p in episode["train"] + episode["test"]})
                            == demos + 4, "Boundary episode has repeated inputs")
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            label = execute(program, pair["input"], f"boundary:{setting}:{demos}:{split}:{index}")
                            mirror = _grid(prototype.rule_mirror(copy.deepcopy(pair["input"]),
                                                               copy.deepcopy(setting)))
                            require(label == pair["output"] == mirror,
                                    "Boundary Racket, generated label and Python mirror disagree")
                    survivors = [copy.deepcopy(setting)]
                    for rival_setting in settings:
                        if raw(rival_setting) == raw(setting):
                            continue
                        results = []
                        for index, pair in enumerate(episode["train"]):
                            value = execute(programs[raw(rival_setting)], pair["input"],
                                            f"boundary-setting-rival:{setting}:{demos}:{index}")
                            require(value == _grid(prototype.rule_mirror(
                                copy.deepcopy(pair["input"]), copy.deepcopy(rival_setting))),
                                "Other-setting Python mirror differs from protected Racket")
                            results.append(value == pair["output"])
                        if all(results):
                            survivors.append(copy.deepcopy(rival_setting))
                    require(survivors == [setting], "Boundary demonstrations do not identify the setting")
                    boundary_episodes.append(episode)
                    report["boundary_checks"].append({"seed": BOUNDARY_SEED, "settings": setting,
                        "demos": demos, "queries": 4, "surviving_settings": survivors,
                        "input_shapes": [[len(p["input"]), len(p["input"][0])]
                                         for p in episode["train"] + episode["test"]]})

            for setting in settings:
                episode = next(ep for ep in episodes if raw(ep["settings"]) == raw(setting))
                teaching = {**copy.deepcopy(episode), "train": copy.deepcopy(episode["train"][:2]), "test": []}
                claim = prototype.teaching_check(copy.deepcopy(teaching))
                rivals = prototype.rival_programs(copy.deepcopy(setting))
                require(type(rivals) is dict and rivals, "Expected a finite named Racket rival family")
                observed = {name: [] for name in rivals}
                for index, pair in enumerate(teaching["train"]):
                    reference = execute(programs[raw(setting)], pair["input"], f"teaching-reference:{setting}:{index}")
                    require(reference == pair["output"], "Teaching reference label changed")
                    mirrors = prototype.rival_outputs(copy.deepcopy(pair["input"]), copy.deepcopy(setting))
                    require(set(mirrors) == set(rivals), "Python and Racket rival inventories differ")
                    for name, program in rivals.items():
                        actual = execute(program, pair["input"], f"teaching-rival:{setting}:{name}:{index}")
                        require(actual == _grid(mirrors[name]), "Rival Python/Racket mismatch: " + name)
                        observed[name].append({"demo_index": index, "input_sha256": digest(pair["input"]),
                                               "output": actual, "expected_output": reference,
                                               "matches": actual == reference})
                survivors = [name for name, rows in observed.items() if all(row["matches"] for row in rows)]
                require(set(claim.get("surviving_rivals", [])) == set(survivors),
                        "teaching_check disagrees with executed demo-only rival survival")
                require(claim.get("status") == ("ambiguous" if survivors else "identified"),
                        "teaching_check status differs from executed rival survival")
                for name, index in claim.get("refuted_by", {}).items():
                    require(name in observed and type(index) is int and 0 <= index < 2
                            and not observed[name][index]["matches"],
                            "teaching_check names an invalid refuting demonstration")
                if survivors:
                    report["failures"].append({"kind": "demo_prefix_has_surviving_rivals",
                                               "settings": setting, "demos_used": 2,
                                               "surviving_rivals": survivors})
                query_checks = []
                for name in survivors:
                    for index, pair in enumerate(episode["test"]):
                        actual = execute(rivals[name], pair["input"], f"surviving-rival:{setting}:{name}:{index}")
                        mirror = prototype.rival_outputs(copy.deepcopy(pair["input"]), copy.deepcopy(setting))[name]
                        require(actual == _grid(mirror), "Surviving-rival query mirror differs from Racket")
                        query_checks.append({"rival": name, "query_index": index,
                                             "output": actual, "expected_output": pair["output"]})
                        if actual != pair["output"]:
                            report["failures"].append({"kind": "demo_survivor_changes_query", "settings": setting,
                                                       "rival": name, "query_index": index,
                                                       "input": pair["input"], "output": pair["output"],
                                                       "rival_output": actual})
                report["teaching_checks"].append({"seed": episode["seed"], "settings": setting,
                    "demos_used": 2, "queries_used_for_survival": 0, "claim": claim,
                    "rival_program_sha256": {name: program_hash(program) for name, program in rivals.items()},
                    "demonstrations": observed, "surviving_rivals": survivors,
                    "surviving_rival_query_checks": query_checks})

            setting = {"orientation": "rotations"}
            episode = next(ep for ep in episodes if ep["settings"] == setting)
            grid = episode["train"][1]["input"]
            program = prototype.program(copy.deepcopy(setting))
            counterfactual = prototype.rival_programs(copy.deepcopy(setting))["always_a"]
            intermediate = prototype.dependency_intermediate(copy.deepcopy(grid))
            require(type(intermediate) is dict and set(intermediate)
                    == {"selector_color", "selected_panel", "template", "other_template"},
                    "Dependency helper must expose the selector and both cropped templates")
            require(type(intermediate["selector_color"]) is int
                    and 0 <= intermediate["selector_color"] <= 9
                    and intermediate["selector_color"] != 2
                    and type(intermediate["selected_panel"]) is int
                    and intermediate["selected_panel"] == 1,
                    "Second native demonstration must select template B")
            intermediate["template"] = _grid(intermediate["template"])
            intermediate["other_template"] = _grid(intermediate["other_template"])
            require(intermediate["template"] != intermediate["other_template"],
                    "Dependency witness needs distinct selected and unselected templates")
            label = execute(program, grid, "sequential-witness:reference")
            wrong = execute(counterfactual, grid, "sequential-witness:wrong_intermediate")
            require(label == episode["train"][1]["output"] and label != wrong,
                    "Replacing selected template B with A must change the actual Racket output")
            witness = {"schema": "arcpuzzles-sequential-dependency-witness-v1",
                "source_binding": copy.deepcopy(binding),
                "racket": {"backend": identity["backend"], "protected": identity["protected"]},
                "racket_runtime_identity": copy.deepcopy(identity),
                "step_a": "Read the selector panel and choose template A for selector color 2, otherwise template B; crop the chosen template to its nonzero bounding box.",
                "intermediate": "The input-dependent selected panel index and cropped template, together with the selector color and the unselected cropped template.",
                "step_b": "Enumerate the selected template's allowed orientations, match its nonzero cells in exact colors against the search board with template zeros as wildcards, then recolor the union of all matched template cells to 8.",
                "why_b_depends_on_a": "The selector determines which template's shape, colors and wildcard positions constrain every orientation and match. Replacing selected template B with A changes the matched cells and final recolored union on the witness input.",
                "cases": [{"input": grid, "settings": setting,
                    "intermediate_value": copy.deepcopy(intermediate),
                    "program": program, "output": label,
                    "counterfactual_program": counterfactual, "counterfactual_output": wrong,
                    "ablation": "wrong_intermediate"}],
                "limits": "One source-bound protected-Racket causal witness; no universal depth or training-gain claim."}
            check_source(binding, contract)
            write_json(output / "sequential-witness.json", witness)
            dependency = {key: witness[key] for key in
                          ("step_a", "intermediate", "step_b", "why_b_depends_on_a")}
            dependency["witness_path"] = "sequential-witness.json"
            report["native_witness_validation"] = validate_sequential_witness(
                {"sequential_dependency": dependency}, q,
                lambda name: (output / name).read_bytes())
            write_json(output / "boundary-episodes.private.json", {
                "schema": "arcpuzzles-parametric-boundary-episodes-v1", "task_id": TASK_ID,
                "source_binding_sha256": digest(binding), "racket": identity,
                "episodes": boundary_episodes, "private": True})
            report["sequential_witness"] = {"path": "sequential-witness.json",
                                             "sha256": file_hash(output / "sequential-witness.json")}
            report["boundary_episode_bank"] = {"path": "boundary-episodes.private.json",
                "sha256": file_hash(output / "boundary-episodes.private.json"),
                "episodes": 4, "labels": 32, "queries_per_episode": 4}
            if export is not None:
                report["export"] = check_export(prototype, episodes, export)
            check_source(binding, contract)
            report["status"] = "failed" if report["failures"] else "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if bridge is not None:
            bridge.close()
        write_json(output / "audit.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--export", type=Path)
    options = parser.parse_args()
    try:
        report = audit(options.qualification, options.out, options.export)
        print(json.dumps({"status": report["status"], "audit": str(options.out.resolve() / "audit.json"),
                          "racket_evaluations": report["racket_evaluations"],
                          "error": report.get("error"), "failures": len(report["failures"])}))
        return 0 if report["status"] == "passed" else 1
    except Exception as error:
        print(json.dumps({"status": "failed", "error": type(error).__name__, "message": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
