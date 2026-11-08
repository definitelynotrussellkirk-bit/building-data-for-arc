"""Private bounded counterexample to declared-settings-only lesson checks.

Run from WORK/repo through the packet wrapper:
python3 ../checks/3108da8bf9e8/semantic-mutant-before.py --out ../checks/3108da8bf9e8/semantic-mutant-before.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import sys


TASK_ID = "3108da8bf9e8"
ROOT = Path(__file__).resolve().parents[2] / "repo"
HOME = ROOT / "generators" / TASK_ID / "workspace/parametric"
SEARCH_SEED = 438271
SEARCH_BOUND = 4096


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(out):
    if out.exists():
        raise FileExistsError(out)
    audit = load("_blocksort_mutant_probe_audit", HOME / "audit_native.py")
    proto = load("_blocksort_mutant_probe_prototype", HOME / "prototype.py")
    adapter = load("_blocksort_mutant_probe_adapter", HOME / "adapter.py")
    settings = {"rank_basis": "components_then_cells"}
    source = audit.source_binding()
    rng, demos, chosen_attempts, seen = random.Random(SEARCH_SEED), [], [], set()
    for attempt in range(1, SEARCH_BOUND + 1):
        grid = proto._draw_grid(rng, 3)
        proto.validate_grid(grid, canonical=True)
        fingerprint = audit.packed(grid)
        if fingerprint in seen:
            continue
        cells = audit.reference(grid, {"rank_basis": "cells"})
        four = audit.reference(grid, settings)
        eight = audit.rival_reference(grid, settings, "components8_then_cells")
        if cells != four and four == eight:
            demos.append(grid)
            seen.add(fingerprint)
            chosen_attempts.append(attempt)
            if len(demos) == 2:
                break
    else:
        raise RuntimeError("Bounded counterexample search exhausted")
    teaching = adapter.generate(0, settings, 2, 4)["train"]
    query, replacement = teaching[0]["input"], teaching[1]["input"]
    if len({audit.packed(grid) for grid in demos + [query, replacement]}) != 4:
        raise AssertionError("All counterexample and repair inputs must be distinct")
    programs = {"cells": adapter.program({"rank_basis": "cells"}),
                "components_then_cells": adapter.program(settings),
                "components8_then_cells": audit.rival_program(settings, "components8_then_cells")}
    report = {"schema": "3108da8bf9e8-semantic-mutant-counterexample-v1",
              "visibility": "controller_private", "training_admitted": False,
              "scope": "A deliberately selected counterexample subset outside clean generated/exported episodes; no source, acceptance or training admission changes.",
              "search": {"seed": SEARCH_SEED, "max_candidates": SEARCH_BOUND,
                         "evaluated_candidates": attempt, "selected_candidate_numbers": chosen_attempts,
                         "generator": "prototype._draw_grid(random.Random(seed),3)",
                         "selection": "cells output differs from C4+area; C4+area and C8+area outputs agree"},
              "source_files_sha256": source,
              "probe_sha256": audit.sha(Path(__file__).read_bytes()),
              "programs": {name: {"source": program, "sha256": audit.sha(program.encode())} for name, program in programs.items()},
              "execution_order": []}
    with audit._local_imports(audit.RUNTIME, audit.HOME):
        apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
        engine = audit.CachedEvaluator(apply)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("Protected Racket required")
        report["racket"] = identity
        try:
            def execute(name, grid, phase, pair_index):
                report["execution_order"].append({"phase": phase, "program": name, "pair_index": pair_index})
                actual = engine(programs[name], grid)
                expected = (audit.rival_reference(grid, settings, name) if name == "components8_then_cells"
                            else audit.reference(grid, {"rank_basis": name}))
                if actual != expected:
                    raise AssertionError("Independent reference mismatch: " + name)
                return actual
            # Every fit decision is frozen before the first query execution.
            demo_outputs = {name: [execute(name, grid, "demonstration", i) for i, grid in enumerate(demos)]
                            for name in programs}
            selected = demo_outputs["components_then_cells"]
            native_survivors = [name for name in ("cells", "components_then_cells") if demo_outputs[name] == selected]
            extra_survivors = ["components8_then_cells"] if demo_outputs["components8_then_cells"] == selected else []
            if native_survivors != ["components_then_cells"] or extra_survivors != ["components8_then_cells"]:
                raise AssertionError("Counterexample demonstration-fit requirements failed")
            report["fit_frozen_before_queries"] = True
            report["declared_setting_check"] = {"survivors": native_survivors, "passed": True,
                "scope": "Literal execution of both declared programs on these demos, using the native demonstration-fit criterion; this is not a native qualification receipt."}
            report["extra_rival_check"] = {"survivors": extra_survivors}
            query_outputs = {name: execute(name, query, "query", 0) for name in programs}
            if query_outputs["components8_then_cells"] == query_outputs["components_then_cells"]:
                raise AssertionError("Extra survivor does not disagree on the query")
            replacement_outputs = {name: execute(name, replacement, "replacement_demonstration", 1) for name in programs}
            repaired_survivors = [name for name in programs if demo_outputs[name][0] == selected[0]
                                  and replacement_outputs[name] == replacement_outputs["components_then_cells"]]
            if repaired_survivors != ["components_then_cells"]:
                raise AssertionError("Replacement does not eliminate the semantic mutant")
            repaired_train = [{"input": demos[0], "output": selected[0]},
                              {"input": replacement, "output": replacement_outputs["components_then_cells"]}]
            if any(pair["input"] == query for pair in repaired_train):
                raise AssertionError("Original query is not novel after repair")
            report.update({"status": "reproduced_expected_incremental_gate_failure",
                           "train": [{"input": grid, "output": selected[i]} for i, grid in enumerate(demos)],
                           "query": {"input": query}, "demo_executed_outputs": demo_outputs,
                           "query_executed_outputs": query_outputs,
                           "query_difference_cells": sum(a != b for ra, rb in zip(query_outputs["components_then_cells"], query_outputs["components8_then_cells"]) for a, b in zip(ra, rb)),
                           "repair": {"replacement_demo_index": 1, "repaired_train": repaired_train,
                                      "replacement_demo_executed_outputs": replacement_outputs,
                                      "demonstration_count": 2, "remaining_hypotheses": repaired_survivors,
                                      "original_query_retained": True, "query_remains_novel": True}})
        finally:
            bridge.close()
            report["execution"] = {"requests": engine.requests, "racket_evaluations": engine.evaluations,
                                   "cache_hits": engine.cache_hits}
    if audit.source_binding() != source:
        raise AssertionError("Task sources changed during probe")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "report": str(out), "search": report["search"],
                      "declared_survivors": native_survivors, "extra_survivors": extra_survivors,
                      "query_difference_cells": report["query_difference_cells"], "execution": report["execution"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
