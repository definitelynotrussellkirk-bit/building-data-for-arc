#!/usr/bin/env python3
"""Bounded protected-Racket authoring audit; no qualification or acceptance.

Run with the packet wrapper and --out NEW_DIRECTORY. Only public-firstturn/
contains model-visible material; every other output is private audit evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
for folder in (ROOT / "src", ROOT / "shared/runtime"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles.runtime import validate_grid
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "8b320727aa72"
SEEDS = (0, 17)


def _load(path):
    name = "_arc_native_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_raw(value))


def _replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Rival construction requires exactly one source fragment: " + old)
    return source.replace(old, new, 1)


def rival_programs(source):
    """Ten explicit nearby mistakes; all remain ordinary executable Racket."""
    final = "(recolor-cells consensus marked 1)"
    cells = "(map obj-cells selected)"
    overlap = "(ormap (lambda (cell) (member cell disagreements)) (obj-cells o))"
    definitions = {
        "local_mark": ("Mark erased coordinates only, without their recovered components.",
                       final, "(recolor-cells consensus disagreements 1)"),
        "all_foreground": ("Mark every foreground component, including undamaged distractors.",
                           cells, "(map obj-cells components)"),
        "all_recovered_colors": (
            "Mark every component of a color recovered at an erased coordinate.", overlap,
            "(member (obj-color o) (map (lambda (cell) (at consensus (first cell) (second cell))) disagreements))"),
        "objects_8": ("Use diagonal as well as orthogonal same-color connectivity.",
                      "(objects component-grid background)", "(objects-8 component-grid background)"),
        "anycolor_4": (
            "Join orthogonally touching foreground of different colors before selection.",
            "(component-grid consensus)",
            "(component-grid (build-grid tile-h tile-w (r c) (if (= (at consensus r c) background) background 1)))"),
        "first_damaged_component": (
            "Mark only the first damaged component in the runtime object order.", cells,
            "(map obj-cells (if (null? selected) '() (list (first selected))))"),
        "largest_components": (
            "Mark all components of maximum size regardless of damage.", cells,
            "(map obj-cells (filter (lambda (o) (= (obj-size o) (apply max (map obj-size components)))) components))"),
        "smallest_components": (
            "Mark all components of minimum size regardless of damage.", cells,
            "(map obj-cells (filter (lambda (o) (= (obj-size o) (apply min (map obj-size components)))) components))"),
        "components_before_recovery": (
            "Find components in the anomalous tile before restoring erased cells.",
            "(component-grid consensus)", "(component-grid anomaly)"),
        "first_tile_components": (
            "Use the first physical tile for component topology instead of recovered consensus.",
            "(component-grid consensus)", "(component-grid (first tiles))"),
    }
    return {name: {"description": description, "program": _replace(source, old, new)}
            for name, (description, old, new) in definitions.items()}


def _first(episode):
    return {"train": episode["train"], "test": episode["test"][:1]}


def _save_public(folder, payload):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (hashlib.sha256(payload).hexdigest() + ".json")
    if path.exists():
        raise ValueError("Duplicate public first-turn payload")
    path.write_bytes(payload)
    return path


def _sources():
    return [{"path": path.relative_to(ROOT).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(HOME.iterdir())
            if path.is_file() and path.suffix in {".py", ".rkt", ".json"}]


def run_audit(output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    started = time.monotonic()
    sources = _sources()
    adapter = _load(HOME / "adapter.py")
    checker = _load(ROOT / "src/arcpuzzles/review_full_packet_files/check_public_exports.py")
    programs = {action: adapter.program({"disagreement_action": action}) for action in adapter.ACTIONS}
    rivals = rival_programs(programs["mark_component"])
    program_records = {}
    for name, source in ({**programs, **{"rival_" + k: v["program"] for k, v in rivals.items()}}).items():
        path = output / "private/programs" / (name + ".rkt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        program_records[name] = {"path": path.relative_to(output).as_posix(),
                                 "sha256": hashlib.sha256(source.encode()).hexdigest()}

    episodes, witnesses, survivors, failures = [], [], [], []
    selected_labels, first_turn_checks, declared_checks, evaluations = 0, 0, 0, 0
    cache = {}
    sample_public = None
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise ValueError("The bounded audit requires actual protected Racket")

        def execute(program, grid):
            nonlocal evaluations
            key = (program, _raw(grid))
            if key not in cache:
                cache[key] = validate_grid(adapter.execute(program, grid, bridge))
                evaluations += 1
            return deepcopy(cache[key])

        for seed in SEEDS:
            for action in adapter.ACTIONS:
                settings = {"disagreement_action": action}
                episode = adapter.generate(seed, settings, 3, 4)
                if episode["program_solution"] != programs[action]:
                    raise AssertionError("Episode program changed")
                if len(episode["train"]) != 3 or len(episode["test"]) != 4:
                    raise AssertionError("The audit requires three demos and four queries")
                for pair in episode["train"] + episode["test"]:
                    actual = execute(programs[action], validate_grid(pair["input"]))
                    if actual != validate_grid(pair["output"]):
                        raise AssertionError(f"Protected Racket label mismatch: {action}, seed {seed}")
                    selected_labels += 1
                compatible = []
                for rival_action, source in programs.items():
                    predictions = [execute(source, pair["input"]) for pair in episode["train"]]
                    declared_checks += len(predictions)
                    if all(got == pair["output"] for got, pair in zip(predictions, episode["train"])):
                        compatible.append(rival_action)
                if compatible != [action]:
                    failures.append({"kind": "declared_setting_survivors", "seed": seed,
                                     "setting": action, "survivors": compatible})

                one = adapter.generate(seed, settings, 3, 1)
                public = _first(episode)
                payload = public_challenge_bytes(public)
                if public_challenge_bytes(_first(one)) != payload:
                    raise AssertionError("One-query and four-query first turns differ")
                changed = deepcopy(episode)
                changed.update(settings={"disagreement_action": "private-other"}, seed=-999)
                for pair in changed["test"]:
                    pair["output"] = [[9]]
                for pair in changed["test"][1:]:
                    pair["input"] = [[7]]
                if (public_challenge_bytes(_first(changed)) != payload
                        or public_challenge_id(_first(changed)) != public_challenge_id(public)):
                    raise AssertionError("Hidden metadata, answers, or future inputs affect the first turn")
                first_turn_checks += 1
                public_path = _save_public(output / "public-firstturn", payload)
                sample_public = json.loads(payload)
                private_path = output / "private/episodes" / f"{action}-seed-{seed}.json"
                _write(private_path, {**episode, "seed": seed, "settings": settings,
                                      "all_selected_labels_executed_in_protected_racket": True})
                episodes.append({"seed": seed, "settings": settings,
                                 "private_path": private_path.relative_to(output).as_posix(),
                                 "first_turn_path": public_path.relative_to(output).as_posix(),
                                 "declared_demo_survivors": compatible,
                                 "counts": {"demos": 3, "queries": 4}})

                if action != "mark_component":
                    continue
                for name, rival in rivals.items():
                    predictions = [execute(rival["program"], pair["input"])
                                   for pair in episode["train"][:2]]
                    different = [i for i, got in enumerate(predictions)
                                 if got != episode["train"][i]["output"]]
                    if not different:
                        survivors.append({"seed": seed, "rival": name})
                        continue
                    index = different[0]
                    pair = episode["train"][index]
                    witness_path = output / "private/rival-witnesses" / f"{name}-seed-{seed}.json"
                    _write(witness_path, {
                        "seed": seed, "settings": settings, "demonstration_index": index,
                        "rival": name, "description": rival["description"],
                        "input": pair["input"], "output": pair["output"],
                        "rival_output": predictions[index],
                        "program_path": "../programs/mark_component.rkt",
                        "rival_program_path": "../programs/rival_" + name + ".rkt",
                        "racket": {"backend": "racket", "protected": True},
                    })
                    witnesses.append({"seed": seed, "rival": name, "demonstration_index": index,
                                      "path": witness_path.relative_to(output).as_posix()})

    public_check = checker.inspect([output / "public-firstturn"], queries=1, demos=3)
    if public_check["status"] != "passed":
        failures.append({"kind": "public_export", "findings": public_check["findings"]})
    negatives = {}
    for name, expected in (("query_output", "public_schema"), ("boolean_cell", "public_grid"),
                           ("duplicate_input", "duplicate_input"), ("wrong_count", "query_count")):
        value = deepcopy(sample_public)
        if name == "query_output":
            value["test"][0]["output"] = [[9]]
        elif name == "boolean_cell":
            value["train"][0]["input"][0][0] = False
        elif name == "duplicate_input":
            value["test"][0]["input"] = deepcopy(value["train"][0]["input"])
        # Rehash deliberately malformed bytes; the check must detect the defect,
        # not just an unrelated stale filename. The serializer would strip leaks.
        path = _save_public(output / "private/negative-public" / name, _raw(value))
        negatives[name] = checker.inspect([path], queries=4 if name == "wrong_count" else 1, demos=3)
        if (negatives[name]["status"] != "failed"
                or expected not in {row["code"] for row in negatives[name]["findings"]}):
            failures.append({"kind": "negative_public_case", "case": name, "expected": expected})
    if survivors:
        failures.append({"kind": "extra_rival_survivors", "survivors": survivors})
    if _sources() != sources:
        failures.append({"kind": "source_changed_during_audit"})
    report = {
        "schema": "8b320727aa72-native-bounded-audit-v1", "task_id": TASK_ID,
        "status": "failed" if failures else "passed", "seeds": list(SEEDS),
        "racket": runtime, "racket_evaluations": evaluations,
        "selected_labels_checked": selected_labels, "declared_demo_program_checks": declared_checks,
        "first_turn_checks": first_turn_checks, "episodes": episodes,
        "programs": program_records, "source_files": sources,
        "rival_audit": {"episodes_checked": len(SEEDS), "rivals_per_episode": len(rivals),
                        "demonstrations_used_per_episode": 2,
                        "rivals": {name: value["description"] for name, value in rivals.items()},
                        "survivors": survivors, "witnesses": witnesses},
        "public_check": public_check, "negative_public_checks": negatives,
        "failures": failures, "owner_accepted": False, "training_admitted": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "command": "python3 review.py run python3 generators/8b320727aa72/workspace/parametric/check_native.py --out NEW_DIRECTORY",
        "limits": ["Two fixed seeds and ten declared nearby rivals; no universal uniqueness claim.",
                   "Extra rivals use the first two original demonstrations only, never query answers.",
                   "This is authoring evidence, not native qualification, owner acceptance or training admission.",
                   "Public-firstturn files are model inputs; other files and complete episodes are private."],
    }
    _write(output / "audit.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    report = run_audit(args.out)
    print(json.dumps({key: report[key] for key in (
        "status", "seeds", "racket_evaluations", "selected_labels_checked", "first_turn_checks",
        "elapsed_seconds", "failures", "owner_accepted", "training_admitted")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
