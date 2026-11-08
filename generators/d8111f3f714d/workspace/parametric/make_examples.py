#!/usr/bin/env python3
"""Execute both native branch settings and save private controllers/actor turns."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root


TASK_ID = "d8111f3f714d"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _local_module(filename):
    path = HERE / filename
    name = "_branch_examples_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sources():
    home = f"generators/{TASK_ID}/workspace/parametric"
    names = [f"generators/{TASK_ID}/generator.py",
             *(f"{home}/{name}" for name in ("prototype.py", "native_family.py", "adapter.py",
                                               "promotion.json", "export.py", "make_examples.py")),
             "shared/data/canonical/puzzles.jsonl", "shared/runtime/reviewer_support.py",
             "shared/runtime/arc_repl/racket_bridge.py", "shared/runtime/puzzle_generators/rule_wrap.py",
             "src/arcpuzzles/parametric_worker.py", "src/arcpuzzles/catalog.py"]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(names)}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer within {low}..{high}")
    return value


def build_examples(out, *, report, seed=0, demos=3, queries=4):
    """Retain real native execution without granting qualification or acceptance."""
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    destination, report_path = Path(out), Path(report)
    for path in (destination, report_path):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
    if report_path.resolve().is_relative_to(destination.resolve()):
        raise ValueError("Report must be outside the exported file inventory")
    family, export = _local_module("native_family.py"), _local_module("export.py")
    contract = json.loads((HERE / "promotion.json").read_bytes())
    sources = _sources()
    jobs = [{"seed": seed, "settings": {"branch_direction": setting},
             "demos": demos, "queries": queries} for setting in family.SETTINGS]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    identity = native.get("racket", {})
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("Examples require actual protected Racket execution")
    wrappers = native.get("episodes")
    if type(wrappers) is not list or len(wrappers) != len(jobs):
        raise ValueError("Native execution did not retain every requested episode")
    episodes = []
    for job, wrapper in zip(jobs, wrappers, strict=True):
        episode = family.generate(job["seed"], job["settings"], job["demos"], job["queries"])
        checked = export.validate_episode(episode)
        labels = {split: [{"input": p["input"], "output": p["output"]} for p in checked[split]]
                  for split in ("train", "test")}
        native_labels = {split: wrapper[split] for split in ("train", "test")}
        if (export.json_bytes(labels) != export.json_bytes(native_labels)
                or checked["program_solution"] != wrapper["program"]
                or wrapper["settings"] != job["settings"] or wrapper["seed"] != job["seed"]):
            raise ValueError("Recreated adapter episode differs from executed native labels or program")
        checked["native_wrapper"] = deepcopy(wrapper)
        checked["native_validation"] = {
            "status": "labels_executed", "owner_acceptance": "not_performed", "training_admitted": False,
            "metadata_recreated_from_unchanged_adapter": True, "labels_matched_exactly": True,
            "reference_marker_scope": "The native wrapper's historical accepted_parametric string is retained verbatim; it does not grant owner acceptance.",
        }
        episodes.append(checked)
    if _sources() != sources:
        raise ValueError("Source changed during native execution or metadata reconstruction")
    context = {
        "schema": "arcpuzzles-native-branch-export-context-v1", "task_id": TASK_ID,
        "native_acceptance": "owner_pending", "training_admitted": False,
        "contract": contract, "jobs": jobs, "source_sha256": sources,
        "native_execution": native,
        "limits": "Native worker verifies the selected finite settings and saved labels. This is example execution, not full native qualification, owner acceptance or a tested turn controller. Recreated adapter metadata is private and labels/programs are compared exactly to the retained native result.",
    }
    manifest = export.write_episodes(episodes, destination, context=context)
    if _sources() != sources:
        raise ValueError("Source changed during publication; do not use this export as current evidence")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    result = {
        "schema": "arcpuzzles-native-branch-examples-v1", "status": "passed", "task_id": TASK_ID,
        "seed": seed, "demonstrations": demos, "queries": queries, "settings_count": len(jobs),
        "native_acceptance": "owner_pending", "training_admitted": False,
        "source_sha256": sources,
        "program_sha256": {w["settings"]["branch_direction"]: w["program_sha256"] for w in wrappers},
        "racket": identity, "racket_evaluations": native["racket_evaluations"],
        "native_execution_sha256": hashlib.sha256(export.json_bytes(native)).hexdigest(),
        "manifest_sha256": digest(destination / "manifest.json"),
        "private_metadata_sha256": digest(destination / "private/metadata.jsonl"),
        "private_context_sha256": digest(destination / "private/context.json"),
        "controller_ids": manifest["controller_ids"], "turn_ids": manifest["turn_ids"],
        "actor_visible_directory": "turns", "private_controller_directory": "private/controllers",
        "limits": context["limits"],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("xb") as handle:
        handle.write(export.json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    result = build_examples(args.out, report=args.report, seed=args.seed, demos=args.demos, queries=args.queries)
    print(json.dumps({key: result[key] for key in ("status", "settings_count", "racket_evaluations",
                                                 "manifest_sha256", "native_acceptance", "training_admitted")}, sort_keys=True))


if __name__ == "__main__":
    main()
