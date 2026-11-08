#!/usr/bin/env python3
"""One bounded production-lesson probe for area versus bounding-box ranking.

Prescreen at most sixteen seeds; stop at the first three-demo/one-query hole.
Materialize that one lesson through Catalog.generate with its automatic demo
policy, then replay both programs through protected Racket on its four pairs.
No production, authority, approval, or sampler changes are made.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time


TASK = "7dc43942b7b3"
ROOT = Path(__file__).resolve().parents[2] / "repo"
GENERATOR = ROOT / f"generators/{TASK}/generator.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(g):
    seen, result = set(), []
    for r, row in enumerate(g):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                a, b = todo.pop()
                cells.append((a, b))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    x, y = a + dr, b + dc
                    if (0 <= x < len(g) and 0 <= y < len(g[0])
                            and g[x][y] == color and (x, y) not in seen):
                        seen.add((x, y))
                        todo.append((x, y))
            result.append(sorted(cells))
    return result


def box_area(cells):
    return ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
            * (max(c for _, c in cells) - min(c for _, c in cells) + 1))


def prediction(g, *, bbox=False):
    objects = components(g)
    if len(objects) != 3:
        raise ValueError("the bounded hypothesis expects the declared three-object grammar")
    # Both Python and Racket sorting are stable for equal keys; object discovery
    # is row-major, so the rival's tie convention is concrete and reproducible.
    objects.sort(key=box_area if bbox else len)
    out = [[0 for _ in row] for row in g]
    for color, cells in zip((2, 3, 4), objects):
        for r, c in cells:
            out[r][c] = color
    return out


def object_stats(g):
    return [{"color": g[cells[0][0]][cells[0][1]], "cells": len(cells),
             "bbox_area": box_area(cells), "first_cell": list(cells[0])}
            for cells in components(g)]


def probe(max_seeds):
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    source_hash = sha(GENERATOR)
    report = {
        "task_id": TASK, "status": "running", "generator_sha256": source_hash,
        "probe_sha256": sha(Path(__file__)), "prescreen_seed_limit": max_seeds,
        "seeds_checked": [], "difficulty": None, "errors": [],
        "rival": "bounding_box_area_with_stable_reading_order_ties",
        "production_changed": False, "approval_changed": False,
        "limits": [
            "One bounded rival and at most sixteen seeds; no universal learnability claim.",
            "The generator is currently unverified; explicit research opt-in does not approve it.",
            "A no-issue outcome covers only the enumerated three-demo lessons.",
            "The repair is a concrete proposal; the production sampler is unchanged.",
        ],
    }
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, GENERATOR.parent):
        spec = importlib.util.spec_from_file_location("_peer_area_generator", GENERATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if module.EXAMPLES_NEEDED != 3:
            raise ValueError("declared demonstration count changed; revise the bounded probe explicitly")
        chosen = None
        for seed in range(max_seeds):
            report["seeds_checked"].append(seed)
            grids = [module.generate(seed, index, difficulty=None) for index in range(4)]
            if any(module.self_check(g) for g in grids):
                continue
            intended = [prediction(g) for g in grids]
            alternate = [prediction(g, bbox=True) for g in grids]
            if intended[:3] == alternate[:3] and intended[3] != alternate[3]:
                chosen = seed, grids
                break
        if chosen is None:
            report["status"] = "bounded_no_issue"
            return report
        seed, grids = chosen
        catalog = Catalog(ROOT)
        record = catalog.get(TASK)
        programs = {v["program_solution"] for v in record["variants"] if v.get("program_solution")}
        if len(programs) != 1:
            raise ValueError("expected exactly one canonical rule")
        canonical = next(iter(programs))
        old = "(< (obj-size a) (obj-size b))"
        new = "(< (* (obj-h a) (obj-w a)) (* (obj-h b) (obj-w b)))"
        if canonical.count(old) != 1:
            raise ValueError("the exact canonical ranking expression changed")
        rival = canonical.replace(old, new)
        # This is the actual production assembly, including its automatic
        # EXAMPLES_NEEDED policy, rejection handling, and canonical execution.
        episode = catalog.generate(TASK, count=1, seed=seed, difficulty=None,
                                   n_test=1, sample_index=0, allow_unapproved=True,
                                   timeout=35)[0]
        if len(episode["train"]) != 3 or len(episode["test"]) != 1:
            raise ValueError("production did not assemble the declared three-demo/one-query lesson")
        pairs = episode["train"] + episode["test"]
        if [p["input"] for p in pairs] != grids or episode["sample_indices"] != [0, 1, 2, 3]:
            raise ValueError("production assembly differs from the prescreen; do not claim this witness")
        if episode["program"] != canonical:
            raise ValueError("production changed the selected canonical program")
        report.update({
            "seed": seed, "sample_indices": episode["sample_indices"],
            "program": canonical, "rival_program": rival,
            "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
            "canonical_rule_hash": record["rule_hash"],
            "production_provenance": episode["provenance"],
            "production_rejections": episode["rejections"],
            "production_canonical_executions": len(pairs),
            "runtime_source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in (
                ROOT / "src/arcpuzzles/runtime.py", ROOT / "src/arcpuzzles/worker.py",
                runtime / "puzzle_generators/helpers/blobs.py")},
        })
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity
        cases = []
        try:
            for index, pair in enumerate(pairs):
                actual = _grid(apply(canonical, pair["input"]))
                alternate = _grid(apply(rival, pair["input"]))
                if actual != pair["output"] or actual != prediction(pair["input"]):
                    raise ValueError("canonical label disagrees with production or the independent prescreen")
                if alternate != prediction(pair["input"], bbox=True):
                    raise ValueError("bounding-box rival's Python and Racket meanings disagree")
                cases.append({"split": "train" if index < 3 else "test",
                              "pair_index": index if index < 3 else 0,
                              "sample_index": index, "input": pair["input"], "output": actual,
                              "rival_output": alternate, "agrees": actual == alternate,
                              "object_statistics": object_stats(pair["input"])})
        finally:
            bridge.close()
        if [p["agrees"] for p in cases] != [True, True, True, False]:
            raise ValueError("the exact retained lesson does not establish the candidate teaching hole")
        if sha(GENERATOR) != source_hash:
            raise ValueError("generator source changed during the probe")
        report.update({
            "status": "verified_production_lesson_hole", "source_stable": True,
            "protected_replay_evaluations": 8, "cases": cases,
            "repair_proposal": {
                "status": "proposed_not_implemented",
                "teaching_example": "A three-cell line, five-cell plus, and six-cell 2x3 rectangle in distinct colors.",
                "intended_order": [3, 5, 6], "bbox_order_by_cell_count": [3, 6, 5],
                "sampler_requirement": "Guarantee a size/bounding-box-order inversion within every supported three-demo lesson, or add an executable lesson competitor that rejects unsupported automatic lessons.",
                "scope": "The supplied canonical first demo already illustrates this distinction; ordinary generated lessons need the same teaching guarantee.",
            },
        })
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-seeds", type=int, default=16)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be a new file")
    if not 1 <= args.max_seeds <= 16:
        parser.error("--max-seeds must be in 1..16")
    started = time.monotonic()
    def deadline(_signal, _frame):
        raise TimeoutError("bounded peer probe exceeded 120 seconds")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(120)
    try:
        result = probe(args.max_seeds)
    except Exception as exc:
        result = {"task_id": TASK, "status": "probe_error", "error": type(exc).__name__, "message": str(exc)}
    finally:
        signal.alarm(0)
    result["elapsed_seconds"] = time.monotonic() - started
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({k: result[k] for k in ("task_id", "status", "elapsed_seconds")}
                     | {k: result[k] for k in ("seed", "seeds_checked", "protected_replay_evaluations", "error", "message") if k in result}))
    return 1 if result["status"] == "probe_error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
