"""Reproduce finite teaching audits, protected labels and one-query exports.

Run with the packet's review.py run wrapper. This creates review evidence only;
native qualification and owner acceptance remain separate existing commands.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_a85_verify_native", HERE / "native.py")
native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(native)


def validate_turn(public, episode, index):
    from reviewer_support import public_challenge_bytes
    if type(public) is not dict or set(public) != {"train", "test"}:
        raise ValueError("public turn contains private or unknown top-level fields")
    if type(public["train"]) is not list or any(type(pair) is not dict or
            set(pair) != {"input", "output"} for pair in public["train"]):
        raise ValueError("public demonstrations have unexpected fields")
    if (type(public["test"]) is not list or len(public["test"]) != 1
            or type(public["test"][0]) is not dict or set(public["test"][0]) != {"input"}):
        raise ValueError("public turn must have exactly one unlabeled query")
    actual = public_challenge_bytes(public)  # includes exact typed grid validation
    expected = public_challenge_bytes(native.public_turn(episode, index))
    if actual != expected:
        raise ValueError("public turn differs from its controller projection")
    return hashlib.sha256(actual).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def run(out, seeds):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes

    source_paths = (HERE / "prototype.py", HERE / "native.py", HERE / "adapter.py",
                    HERE / "promotion.json", Path(__file__).resolve())
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    minimum = json.loads((HERE / "promotion.json").read_text())["limits"]["demos"][0]
    if not 1 <= len(seeds) <= 8 or len(set(seeds)) != len(seeds):
        raise ValueError("provide one to eight distinct bounded seeds")
    cache, wrapped = {}, {}
    episodes, audits, statistics = [], [], []
    jobs = failures = 0
    with RacketBridge(timeout=20.0, max_calls_before_restart=512) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("verification requires protected Racket")

        def execute(program, grid):
            key = (program, tuple(map(tuple, grid)))
            if key not in cache:
                if program not in wrapped:
                    wrapped[program] = wrap_rule(program)
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                output = bridge.eval_text(f"({wrapped[program]} {literal})")
                # Validate both dimensions and exact integer output cells.
                public_challenge_bytes({"train": [{"input": grid, "output": output}],
                                        "test": [{"input": grid}]})
                cache[key] = output
            return deepcopy(cache[key])

        for seed in seeds:
            matched = None
            for value in native.SETTINGS:
                settings = {"axis_tolerance": value}
                full = native.generate(seed, settings, 6, 4)
                core = native.generate(seed, settings, minimum, 4)
                jobs += 2
                inputs = {split: [p["input"] for p in full[split]] for split in ("train", "test")}
                if matched is None:
                    matched = inputs
                if inputs != matched or core["test"] != full["test"]:
                    raise AssertionError("settings or demo counts changed query/input sampling")
                for pair in full["train"] + full["test"]:
                    actual = execute(full["program_solution"], pair["input"])
                    if pair["output"] != actual:
                        raise AssertionError("Python claim differs from protected Racket label")
                    pair["output"] = actual
                core["train"] = full["train"][:minimum]
                core["test"] = full["test"]
                rival_programs = native.rival_programs(value)
                demo_predictions = []
                for pair in core["train"]:
                    mirrors = native.declared_rivals(pair["input"], value)
                    if set(mirrors) != set(rival_programs):
                        raise AssertionError("every declared rival needs an executable program")
                    predictions = {name: execute(program, pair["input"])
                                   for name, program in rival_programs.items()}
                    if predictions != mirrors:
                        raise AssertionError("rival mirror differs from its protected program")
                    demo_predictions.append(predictions)
                teaching = []
                for name, program in rival_programs.items():
                    refuted = [i for i, pair in enumerate(core["train"])
                               if demo_predictions[i][name] != pair["output"]]
                    survives = not refuted
                    if survives and any(execute(program, pair["input"]) != pair["output"]
                                        for pair in core["test"]):
                        raise AssertionError(f"demo-surviving rival changes a query: {seed}/{value}/{name}")
                    teaching.append({"rival": name, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                                     "refuted_by_demos": refuted, "survives_demos": survives,
                                     "surviving_query_disagreements": 0})
                setting_survivors = []
                for candidate in native.SETTINGS:
                    candidate_program = native.program({"axis_tolerance": candidate})
                    if all(execute(candidate_program, p["input"]) == p["output"] for p in core["train"]):
                        setting_survivors.append(candidate)
                if setting_survivors != [value]:
                    raise AssertionError("demonstrations fail to identify the chosen setting")
                public_paths = []
                first_id = None
                for index in range(4):
                    turn = native.public_turn(core, index)
                    identifier = validate_turn(turn, core, index)
                    name = f"challenge-{identifier}.json"
                    (out / "public").mkdir(exist_ok=True)
                    destination = out / "public" / name
                    if destination.exists():
                        raise ValueError("duplicate visible challenge in export batch")
                    destination.write_bytes(public_challenge_bytes(turn))
                    public_paths.append("public/" + name)
                    first_id = first_id or identifier
                single = deepcopy(core)
                single["test"] = single["test"][:1]
                if native.public_turn(single) != native.public_turn(core):
                    raise AssertionError("first-turn multi-query projection diverges")
                private_path = f"private/episode-{first_id}.json"
                _write(out / private_path, {**core, "settings": settings, "seed": seed,
                                           "teaching": teaching, "setting_survivors": setting_survivors,
                                           "status": "reviewer evidence; owner acceptance pending"})
                episodes.append({"private_path": private_path, "public_turns": public_paths,
                                 "seed": seed, "settings": settings, "demos": minimum, "queries": 4})
                audits.append({"seed": seed, "settings": settings, "rivals": teaching,
                               "setting_survivors": setting_survivors})
            for grid in matched["test"]:
                facts = native.scene_facts(grid)
                statistics.append({"seed": seed, "shape": [len(grid), len(grid[0])],
                                   "noise_cells": len(facts["noise_cells"]),
                                   "selected_panel_noise": facts["panel_noise_count"],
                                   "target": list(facts["target"]), "marker": list(facts["marker"])})
    if sources != {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}:
        raise ValueError("source changed during verification; results cannot bind current bytes")
    episodes.sort(key=lambda row: row["public_turns"][0])
    report = {"schema": "a85-native-review-evidence-v1", "task_id": native.TASK_ID,
              "status": "reviewer verified; owner acceptance pending", "source_sha256": sources,
              "racket": {k: v for k, v in identity.items() if not k.endswith("_path")},
              "generation": {"attempts": jobs, "successes": jobs, "failures": failures,
                             "seeds": seeds, "demos": [minimum, 6], "queries": 4},
              "protected_evaluations": len(cache), "episodes": episodes, "teaching_audits": audits,
              "query_statistics": statistics,
              "checks": {"matched_inputs": True, "query_prefix_independent_of_demo_count": True,
                         "labels_executed": True, "finite_rivals_demo_only": True,
                         "no_harmful_survivors": True, "single_query_first_turn_parity": True,
                         "public_names_visible_bytes_only": True},
              "limits": ["Finite declared rival set and retained seeds; no universal uniqueness claim.",
                         "Canonical production and original prototype remain unchanged.",
                         "Native owner acceptance and training admission are separate."]}
    _write(out / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args()
    report = run(args.out, args.seed or [0, 17])
    print(json.dumps({"report": str(args.out / "report.json"), "generation": report["generation"],
                      "protected_evaluations": report["protected_evaluations"],
                      "episodes": len(report["episodes"]), "checks": report["checks"]}, indent=2))


if __name__ == "__main__":
    main()
