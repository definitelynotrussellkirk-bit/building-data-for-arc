"""Bounded protected-Racket labels, shortcut audit, and public-boundary checks.

Run through the packet's review.py run python3 wrapper. This is reviewer evidence,
not native qualification, owner acceptance, or training admission.
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

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "8a63cd5c5bfb"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import public_challenge_bytes
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("_rectangle_verified_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rival_programs(alternate, target):
    """Executable full rules; all selectors are total on the admitted grammar."""
    old = "(chosen (if (null? parts) 8 (obj-color (pick-max parts obj-size))))"
    if alternate.count(old) != 1:
        raise ValueError("Update source-bound rival recipes for changed alternate rule")
    selectors = {f"fixed_{color}": str(color) for color in range(1, 10) if color != 3}
    selectors.update({
        "global_largest": "(let* ((clean (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) 3) 0 (at g r c))))) (all (objects clean 0))) (if (null? all) 8 (obj-color (pick-max all obj-size))))",
        "largest_aggregate_color": "(let ((colors (filter (lambda (x) (> (length (find-color inside x)) 0)) '(1 2 4 5 6 7 8 9)))) (if (null? colors) 8 (pick-max colors (lambda (x) (length (find-color inside x))))))",
        "second_aggregate_color": "(let* ((colors (filter (lambda (x) (> (length (find-color inside x)) 0)) '(1 2 4 5 6 7 8 9))) (best (if (null? colors) 8 (pick-max colors (lambda (x) (length (find-color inside x)))))) (rest (filter (lambda (x) (not (= x best))) colors))) (if (null? rest) best (pick-max rest (lambda (x) (length (find-color inside x))))))",
        "smallest_interior": "(if (null? parts) 8 (obj-color (pick-min parts obj-size)))",
        "first_interior": "(if (null? parts) 8 (obj-color (first parts)))",
        "last_interior": "(if (null? parts) 8 (obj-color (first (reverse parts))))",
        "max_color_single_interior_component": "(let ((colors (filter (lambda (color) (= (length (filter (lambda (object) (= (obj-color object) color)) parts)) 1)) '(1 2 4 5 6 7 8 9)))) (if (null? colors) 8 (apply max colors)))",
        "min_color_single_interior_component": "(let ((colors (filter (lambda (color) (= (length (filter (lambda (object) (= (obj-color object) color)) parts)) 1)) '(1 2 4 5 6 7 8 9)))) (if (null? colors) 8 (apply min colors)))",
        "normalized_upper_left_component": "(let* ((rm (/ (+ r0 r1) 2)) (cm (/ (+ c0 c1) 2)) (candidates (filter (lambda (object) (ormap (lambda (cell) (let ((r (first cell)) (c (second cell))) (cond ((> r0 0) (and (< r rm) (< c cm))) ((< c1 (- (cols g) 1)) (and (< r rm) (> c cm))) ((< r1 (- (rows g) 1)) (and (> r rm) (> c cm))) (else (and (> r rm) (< c cm)))))) (obj-cells object))) parts))) (if (null? candidates) 8 (obj-color (first candidates))))",
    })
    rivals = {name: alternate.replace(old, "(chosen " + expr + ")")
              for name, expr in selectors.items()}
    rivals["largest_interior_setting"] = alternate
    rivals["exclude_cyan_interior"] = alternate.replace(
        "(parts (objects inside 0))",
        "(parts (filter (lambda (object) (not (= (obj-color object) 8))) (objects inside 0)))")
    rivals["eight_connected_interior"] = alternate.replace(
        "(parts (objects inside 0))", "(parts (objects-8 inside 0))")
    rivals["full_components_intersecting_interior"] = alternate.replace(
        "(parts (objects inside 0))",
        "(parts (filter (lambda (object) (ormap (lambda (cell) (and (< r0 (first cell) r1) (< c0 (second cell) c1))) (obj-cells object))) (objects g 0)))")
    boundary = "(and (or (= r r0) (= r r1) (= c c0) (= c c1)) (= (at out r c) 0))"
    if target.count(boundary) != 1:
        raise ValueError("Update source-bound painting rival recipes")
    rivals["overwrite_occupied_border"] = target.replace(
        boundary, "(or (= r r0) (= r r1) (= c c0) (= c c1))")
    rivals["fill_rectangle"] = target.replace(boundary, "(= (at out r c) 0)")
    return rivals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="New repository-relative evidence directory")
    args = parser.parse_args()
    named = Path(args.out)
    if named.is_absolute():
        parser.error("--out must be relative to the repository root")
    out = (ROOT / named).resolve()
    if not out.is_relative_to(ROOT.parent):
        parser.error("--out must remain within this packet's WORK tree")
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    adapter = load_adapter()
    source_paths = [HOME / name for name in
                    ("adapter.py", "verify.py", "canonical.rkt", "largest_interior.rkt", "promotion.json")]
    source_paths.append(ROOT / "generators" / TASK / "generator.py")
    binding = [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p.read_bytes())}
               for p in source_paths]
    out.mkdir(parents=True)
    for name in ("private", "public", "controller_public"):
        (out / name).mkdir()
    cache, wrapped = {}, {}
    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("Live protected Racket backend is required")
    evaluations = 0
    def execute(program, grid):
        nonlocal evaluations
        key = (program, json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            code = wrapped.setdefault(program, wrap_rule(program))
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            result = bridge.eval_text(f"({code} {literal})")
            adapter._grid(result)
            cache[key] = result
            evaluations += 1
        return copy.deepcopy(cache[key])

    jobs = [(mode, seed, demos, None) for mode in adapter.SETTINGS
            for seed in (0, 17) for demos in (2, 3, 6)]
    jobs += [("largest_interior", 0, 2, size) for size in
             ((12, 12), (12, 30), (30, 12), (30, 30))]
    rows, failures = [], []
    try:
        for number, (mode, seed, demos, size) in enumerate(jobs):
            settings = {"color_source": mode}
            extras = {} if size is None else {"height": size[0], "width": size[1]}
            episode = adapter.generate(seed, settings, demos, 4, **extras)
            target = adapter.program(settings)
            if episode["program_solution"] != target:
                raise AssertionError("Generated program differs from program(settings)")
            if len(episode["train"]) != demos or len(episode["test"]) != 4:
                raise AssertionError("Independent requested pair counts were not respected")
            inputs = [json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]]
            if len(set(inputs)) != len(inputs):
                raise AssertionError("Repeated demonstration/query input")
            for split in ("train", "test"):
                for pair in episode[split]:
                    actual = execute(target, pair["input"])
                    if actual != pair["output"]:
                        raise AssertionError(f"Python label differs from Racket in job {number} {split}")
                    pair["output"] = actual
                    if size and (len(actual), len(actual[0])) != size:
                        raise AssertionError("Exact dimension control changed output shape")
            one = adapter.generate(seed, settings, demos, 1, **extras)
            turn = lambda e: public_challenge_bytes({"train": e["train"], "test": e["test"][:1]})
            raw = turn(episode)
            if raw != turn(one):
                raise AssertionError("First turn depends on requested query count")
            poisoned = copy.deepcopy(episode)
            poisoned.update(settings={"secret": "poison"}, program_solution="secret", total_queries=999)
            for split in ("train", "test"):
                for pair in poisoned[split]:
                    pair.update(private="secret", settings="secret")
            for pair in poisoned["test"]:
                pair["output"] = [[9]]
            for pair in poisoned["test"][1:]:
                pair["input"] = [[9]]
            if turn(poisoned) != raw:
                raise AssertionError("Private/future-query fields changed first-turn identity")
            controller = public_challenge_bytes(episode)
            (out / "public" / (digest(raw) + ".json")).write_bytes(raw)
            (out / "controller_public" / (digest(controller) + ".json")).write_bytes(controller)
            audit = []
            for name, program in rival_programs(adapter.program({"color_source": "largest_interior"}), target).items():
                disagreement = [i for i, pair in enumerate(episode["train"])
                                if execute(program, pair["input"]) != pair["output"]]
                query_disagreement = []
                if not disagreement:
                    query_disagreement = [i for i, pair in enumerate(episode["test"])
                                          if execute(program, pair["input"]) != pair["output"]]
                dangerous = not disagreement and bool(query_disagreement)
                if dangerous:
                    failures.append({"job": number, "rival": name, "query_disagreement_indices": query_disagreement})
                audit.append({"rival": name, "program_sha256": digest(program.encode()),
                              "demo_disagreement_indices": disagreement,
                              "demo_survivor": not disagreement,
                              "query_disagreement_indices": query_disagreement,
                              "harmless_on_sampled_queries": not disagreement and not query_disagreement,
                              "dangerous_survivor": dangerous})
            private = {"settings": settings, "seed": seed, "demos": demos, "queries": 4,
                       "exact_dimensions": size, "program": target, "episode": episode,
                       "rival_programs": rival_programs(adapter.program({"color_source": "largest_interior"}), target),
                       "audit": audit}
            write(out / "private" / f"episode-{number:02}.json", private)
            pairs = episode["train"] + episode["test"]
            rows.append({"job": number, "settings": settings, "seed": seed, "demos": demos,
                         "queries": 4, "exact_dimensions": size,
                         "public_id": digest(raw), "controller_public_id": digest(controller),
                         "dimensions": [[len(p["input"]), len(p["input"][0])] for p in pairs],
                         "output_nonzero_cells": [sum(v != 0 for r in p["output"] for v in r) for p in pairs],
                         "output_changed_cells": [sum(a != b for ra, rb in zip(p["input"], p["output"])
                                                       for a, b in zip(ra, rb)) for p in pairs],
                         "audit": audit})
    except Exception as error:
        report = {"schema": "rectangle-color-bounded-verification-v1", "status": "incomplete",
                  "source_binding": binding, "racket": identity, "racket_evaluations": evaluations,
                  "completed_episodes": rows, "failed_job": number,
                  "error": {"type": type(error).__name__, "message": str(error)},
                  "limits": "Aborted bounded probe; no passing claim for unfinished jobs."}
        write(out / "report.json", report)
        print(json.dumps({"status": "incomplete", "failed_job": number,
                          "error": report["error"], "report": str(out / "report.json")}))
        return 1
    finally:
        bridge.close()
    checker = ROOT / "src/arcpuzzles/review_full_packet_files/check_public_exports.py"
    export_checks = {}
    for folder, count in (("public", 1), ("controller_public", 4)):
        checked = subprocess.run([sys.executable, "-I", str(checker), str(out / folder),
                                  "--queries", str(count)], capture_output=True, text=True)
        report = json.loads(checked.stdout)
        export_checks[folder] = {"status": report["status"], "files_checked": report["files_checked"],
                                 "queries": count, "findings": report["findings"]}
        if checked.returncode:
            failures.append({"public_export_check": folder, "findings": report["findings"]})
    if any(digest((ROOT / row["path"]).read_bytes()) != row["sha256"] for row in binding):
        failures.append({"source_changed_during_verification": True})
    report = {"schema": "rectangle-color-bounded-verification-v1",
              "status": "failed" if failures else "passed", "source_binding": binding,
              "racket": identity, "racket_evaluations": evaluations, "episodes": rows,
              "failures": failures, "public_export_checks": export_checks,
              "checks": {"distinct_inputs": True, "racket_labels": True,
                         "one_vs_four_first_turn_identical": True, "private_future_poison_invariant": True},
              "limits": "Finite seeds, dimensions, and executable rivals only. Queries classify surviving rivals; never eliminate them. Not qualification, acceptance, or training admission."}
    write(out / "report.json", report)
    print(json.dumps({"status": report["status"], "episodes": len(rows),
                      "racket_evaluations": evaluations, "failures": failures,
                      "report": str(out / "report.json")}, separators=(",", ":")))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
