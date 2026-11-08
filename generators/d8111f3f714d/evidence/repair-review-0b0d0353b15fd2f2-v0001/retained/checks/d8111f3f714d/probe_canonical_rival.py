#!/usr/bin/env python3
"""Check the predeclared rivals against original canonical demos, then one emitted case."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root


TASK = "d8111f3f714d"
ROOT = find_root(__file__)
WORK = ROOT.parent
HOME = ROOT / f"generators/{TASK}/workspace/parametric"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def run(out):
    if out.exists():
        raise FileExistsError(out)
    audit = load(HOME / "audit_native.py", "_canonical_branch_audit")
    ledger = canonical_path(ROOT)
    variants = []
    for raw in ledger.read_bytes().splitlines(keepends=True):
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            variants.append((row, hashlib.sha256(raw).hexdigest()))
    originals = [(row, h) for row, h in variants if row.get("content_hash") == TASK]
    if len(originals) != 1:
        raise ValueError("Expected exactly one original canonical row")
    original, original_line_sha256 = originals[0]
    demos = deepcopy(original["train"])
    settings = {"branch_direction": "toward_trunk"}
    intended = audit.rival_program(settings, "intended")
    if intended != original["program_solution"]:
        raise ValueError("Exact canonical program differs")
    # These names were declared and audited before this canonical screen.
    screen = {
        name: [i for i, pair in enumerate(demos)
               if audit.independent_apply(pair["input"], settings, name) != pair["output"]]
        for name in audit.RIVALS
    }
    survivors = [name for name, bad in screen.items() if not bad]
    if survivors != ["first_five_only"]:
        raise ValueError("The bounded survivor set changed: " + repr(survivors))
    frozen_screen = audit.json_bytes(screen)
    chosen = survivors[0]
    rival = audit.rival_program(settings, chosen)

    # Only now inspect the predeclared first native demonstration as a counterexample.
    prior = WORK / f"checks/{TASK}/native-branch-teaching-audit"
    prior_report = json.loads((prior / "report.json").read_text())
    if prior_report["status"] != "passed":
        raise ValueError("Prior native audit did not pass")
    for path, expected in prior_report["source_sha256"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Native audit source drift: " + path)
    for path, expected in prior_report["artifact_sha256"].items():
        if digest(prior / path) != expected:
            raise ValueError("Native audit artifact drift: " + path)
    episodes = json.loads((prior / "episodes.json").read_text())
    source_episode = next(row["episode"] for row in episodes
                          if row["seed"] == 0 and row["settings"] == settings)
    native = load(HOME / "native_family.py", "_canonical_branch_native")
    regenerated = native.generate(0, settings, demos=2, queries=4)
    if regenerated["train"] != source_episode["train"] or regenerated["test"] != source_episode["test"]:
        raise ValueError("Current native generator differs from retained emitted episode")
    pair = source_episode["train"][0]
    grid = pair["input"]
    facts = audit.analyze_scene(grid)
    input_sha256 = audit.sha(audit.json_bytes(grid))
    retained_evaluations = json.loads((prior / "evaluations.json").read_text())
    reused = {}
    for name, program in [("intended", intended), ("rival", rival)]:
        program_sha256 = audit.sha(program.encode())
        program_path = prior / "programs" / (program_sha256 + ".rkt")
        if program_path.read_text() != program:
            raise ValueError("Retained exact program differs")
        records = [row for row in retained_evaluations
                   if row["program_sha256"] == program_sha256 and row["input_sha256"] == input_sha256]
        if len(records) != 1:
            raise ValueError("Need one exact prior application for " + name)
        reused[name] = records[0]
    actual = reused["intended"]["output"]
    alternative = reused["rival"]["output"]
    if actual != pair["output"] or actual != audit.independent_apply(grid, settings):
        raise ValueError("Intended emitted counterexample label differs")
    if alternative != audit.independent_apply(grid, settings, chosen):
        raise ValueError("Rival emitted counterexample label differs")
    changed = [[r, c] for r in range(len(grid)) for c in range(len(grid[0])) if actual[r][c] != alternative[r][c]]
    if not changed:
        raise ValueError("Retained emitted case is not a counterexample")

    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        runtime = bridge.runtime_identity
        if runtime != prior_report["racket"]:
            raise ValueError("Prior native runtime identity differs")
        executor = audit.ProtectedExecutor(bridge)
        canonical_fit = []
        for i, demo in enumerate(demos):
            reference = executor.apply(intended, demo["input"])
            prediction = executor.apply(rival, demo["input"])
            if reference != demo["output"] or prediction != reference:
                raise ValueError("Protected canonical-demo fit failed")
            canonical_fit.append({"index": i, "input": demo["input"], "output": reference,
                                  "rival_output": prediction,
                                  "branch_count": len(audit.analyze_scene(demo["input"])["branches"])})
    if audit.json_bytes(screen) != frozen_screen:
        raise ValueError("Counterexample access mutated the demo-only selection")

    out.mkdir(parents=True)
    (out / "intended.rkt").write_text(intended)
    (out / "rival.rkt").write_text(rival)
    save(out / "canonical-fit.json", canonical_fit)
    save(out / "protected-execution.json", {"racket": runtime, "evaluations": executor.evaluations,
                                           "racket_evaluations": len(executor.evaluations),
                                           "cache_hits": executor.cache_hits})
    save(out / "reused-native-evaluations.json", {
        "source_report": f"checks/{TASK}/native-branch-teaching-audit/report.json",
        "source_report_sha256": digest(prior / "report.json"),
        "source_evaluations_sha256": digest(prior / "evaluations.json"),
        "source_inputs_sha256": digest(prior / "inputs.json"), "racket": prior_report["racket"],
        "evaluations": reused, "fresh_reference_applications": 0})
    save(out / "counterexample.json", {
        "emitted_by": f"generators/{TASK}/workspace/parametric/native_family.py",
        "request": {"seed": 0, "settings": settings, "demos": 2, "queries": 4},
        "split": "train", "pair_index": 0, "current_generation_reproduced": True,
        "input": grid, "intended_output": actual, "rival_output": alternative,
        "changed_cells": changed, "changed_cell_count": len(changed), "input_facts": facts,
        "input_sha256": input_sha256,
        "intended_program_sha256": audit.sha(intended.encode()),
        "rival_program_sha256": audit.sha(rival.encode())})
    artifacts = {p.name: digest(p) for p in out.iterdir() if p.is_file()}
    report = {
        "schema": "arcpuzzles-canonical-branch-rival-v1", "question_id": "generator-shortcuts",
        "task_id": TASK, "status": "passed", "chosen_rival": chosen,
        "rival_description": "Find and fill the unique trunk, then connect only the first five non-endpoint red cells in row-major order toward it.",
        "selection_scope": "The only survivor among thirteen already-declared rivals on the four original canonical training pairs; not a globally strongest-rule claim.",
        "canonical_demo_count": len(demos), "canonical_branch_counts": [row["branch_count"] for row in canonical_fit],
        "canonical_content_hash": original["content_hash"], "canonical_exact_line_sha256": original_line_sha256,
        "canonical_variants": [{"content_hash": row["content_hash"], "source": row["source"],
                                 "training_pairs": len(row["train"]), "query_pairs": len(row["test"]),
                                 "used_for_selection": row["content_hash"] == TASK} for row, _ in variants],
        "excluded_augmented_variant_reason": "The augmented row repeats canonical pairs and places the original held-out pair in train; it is not an additional original demonstration.",
        "python_screen_demo_disagreements": screen, "survivors": survivors,
        "selection_frozen_before_counterexample": True,
        "fresh_protected_racket_applications": len(executor.evaluations),
        "reused_protected_native_applications": 2,
        "counterexample_branch_count": len(facts["branches"]), "counterexample_changed_cells": len(changed),
        "proposed_generator_emits_counterexample": True,
        "source_sha256": {"checks/" + TASK + "/probe_canonical_rival.py": digest(Path(__file__)),
                          **{"repo/" + p: h for p, h in prior_report["source_sha256"].items()}},
        "artifact_sha256": artifacts, "owner_acceptance": "not_performed", "training_admitted": False,
        "limits": ["The first-five cap is a branch-count extrapolation shortcut; no less arbitrary survivor occurred in this finite predeclared set.",
                   "No canonical held-out-query failure is claimed; only original train pairs select the rival.",
                   "The original production generator emits at most five branches, so it cannot emit this >5-branch counterexample. The separate native family does.",
                   "Eight fresh protected applications verify the four canonical demos under both programs. The exact emitted counterexample outputs reuse two source-bound protected native-audit applications, not new executions."]}
    save(out / "report.json", report)
    print(json.dumps({"status": report["status"], "chosen_rival": chosen,
                      "canonical_demos": len(demos), "fresh_racket_applications": len(executor.evaluations),
                      "reused_racket_applications": 2, "counterexample_branches": len(facts["branches"]),
                      "changed_cells": len(changed)}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
