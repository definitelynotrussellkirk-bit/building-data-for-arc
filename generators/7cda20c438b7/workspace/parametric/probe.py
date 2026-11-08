"""Bounded authoring study and native-adapter check for the proposed X/cross family."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from reviewer_support import public_challenge_bytes


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_x_neighborhood_probe_impl", HERE / "prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def _stats(grid, settings):
    centers = P.centers(grid, settings)
    used = Counter((r + dr, c + dc) for r, c in centers
                   for dr, dc in P.NEIGHBORHOODS[settings["neighborhood"]])
    height, width = len(grid), len(grid[0])
    nonzero = sum(value != 0 for row in grid for value in row)
    edge = sum(grid[r][c] != 0 for r in range(height) for c in range(width)
               if r in (0, height - 1) or c in (0, width - 1))
    return {"shape": [height, width], "nonzero_cells": nonzero,
            "density": nonzero / (height * width), "filled_centers": len(centers),
            "shared_arm_cells": sum(n > 1 for n in used.values()),
            "nonzero_boundary_cells": edge,
            "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()}


def run(output):
    if output.exists():
        raise FileExistsError(output)
    started = time.monotonic()
    report = {"schema": "x-neighborhood-bounded-authoring-v1", "task_id": P.TASK_ID,
              "scope": "Prototype only; no production audit resolution or variant acceptance.",
              "source_sha256": P.source_bindings(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "cases": [], "failures": [], "successes": 0, "attempts": 0}
    with P.Reference() as reference:
        for seed in (0, 17):
            for demos in range(2, 7):
                episodes = []
                for setting in P.NEIGHBORHOODS:
                    settings = {"neighborhood": setting}
                    report["attempts"] += 1
                    try:
                        episode = P.generate(seed, settings, demos, 4)
                        certificate = P.verify_episode(episode, reference)
                        if certificate["survivors"] != ["setting:" + setting]:
                            raise ValueError("a declared shortcut survived constructed demonstrations")
                        one = P.generate(seed, settings, demos, 1)
                        first = {"train": episode["train"], "test": [episode["test"][0]]}
                        if public_challenge_bytes(first) != public_challenge_bytes(one):
                            raise ValueError("single-query and multi-query first turns differ")
                        report["cases"].append({"seed": seed, "settings": settings,
                            "demos": demos, "queries": 4, "certificate": certificate,
                            "query_geometry": [_stats(pair["input"], settings) for pair in episode["test"]],
                            "same_first_turn_as_one_query": True})
                        report["successes"] += 1
                        episodes.append(episode)
                    except Exception as error:
                        report["failures"].append({"seed": seed, "demos": demos, "settings": settings,
                                                   "error": type(error).__name__ + ": " + str(error)})
                if len(episodes) == 2:
                    for split in ("train", "test"):
                        if [p["input"] for p in episodes[0][split]] != [p["input"] for p in episodes[1][split]]:
                            raise ValueError("hidden settings changed input sampling")
        witness = [[3, 0, 3, 0, 3], [0, 0, 0, 0, 0], [3, 0, 3, 0, 3]]
        default = {"neighborhood": "diagonal"}
        canonical = reference.apply(P.program(default), witness)
        shortcut = reference.apply(P.hypotheses(default)["isolated_only"], witness)
        assert canonical == [[3, 0, 3, 0, 3], [0, 4, 0, 4, 0], [3, 0, 3, 0, 3]]
        assert shortcut == witness
        report["retained_overlap_witness"] = {"input": witness, "canonical_output": canonical,
                                              "isolated_only_output": shortcut}
        report["racket_applications"] = reference.calls
        identity = reference.bridge.runtime_identity
        report["runtime"] = {k: identity[k] for k in ("schema", "backend", "protected",
            "binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256")}
    # Exercise the actual native consumer without qualification or acceptance.
    from arcpuzzles.parametric_worker import evaluate_contract
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"neighborhood": setting}, "demos": 3, "queries": 4}
            for seed in (0, 17) for setting in P.NEIGHBORHOODS]
    native = evaluate_contract(HERE.parents[3], P.TASK_ID, contract, jobs)
    report["native_adapter"] = {"checks": native["checks"], "racket": native["racket"],
                                "racket_evaluations": native["racket_evaluations"],
                                "qualified": False, "accepted": False}
    report["elapsed_seconds"] = round(time.monotonic() - started, 4)
    report["limitations"] = [
        "Two seeds and the five supported demo counts are bounded observations, not a universal sampler proof.",
        "Identifiability is relative to the two settings and six explicit shortcuts, not all conceivable rules.",
        "The repaired canonical generator now enforces shared-arm overlap and rejects undeclared controls.",
        "The sample grammar uses separated motif patches; it does not model arbitrary natural-scene clutter.",
        "No model training, generalization benefit, qualification or acceptance is claimed."]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"attempts": report["attempts"], "successes": report["successes"],
                      "failures": len(report["failures"]), "racket_applications": report["racket_applications"],
                      "native_jobs": len(native["checks"]), "seconds": report["elapsed_seconds"]}))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().out))
