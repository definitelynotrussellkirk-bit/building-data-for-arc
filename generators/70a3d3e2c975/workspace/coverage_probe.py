#!/usr/bin/env python3
"""Replay canonical topology coverage and every cyclic 3-demo/1-query window.

From the packet root:
  python3 run_with_racket.py python3 generators/70a3d3e2c975/workspace/coverage_probe.py \
      --seed-count 16 --output ../checks/coverage_after

The default draws 16 seeds x 3 bands x 4 inputs: 192 draws and 192 OVERLAPPING
windows, not 768 independent inputs. No model inference or solve data is used.
The task-local topology floor requires some canonical component support, not
that every lawful extension reproduce the tiny canonical distribution.
Exit 0 means the declared finite checks passed; 1 means a measured failure.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "70a3d3e2c975"
ROOT = Path(__file__).resolve().parents[3]
RULE_ATTRIBUTES = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(packed(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_grid(grid):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        raise ValueError("expected a nonempty rectangular integer grid")
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in grid):
        raise ValueError("expected a rectangular integer grid with colors 0..9")
    return [list(row) for row in grid]


def topology(grid):
    """Four-neighbor components of all left foreground, without color splitting.

Adjacency ignores color so touching unlike colors are honestly one polychrome
component. Exact component sizes and dimensions are reported but not required
to match: the support signature is (components, singletons, polychrome, colors).
"""
    grid = normalized_grid(grid)
    height, width = len(grid), len(grid[0])
    axis = width // 2
    errors = []
    if width % 2 != 1 or not all(row[axis] == 9 for row in grid):
        errors.append("missing centered full-height 9 rail")
    if any(grid[r][c] == 9 for r in range(height) for c in range(width) if c != axis):
        errors.append("9 outside center rail")
    if any(row[c] != 0 for row in grid for c in range(axis + 1, width)):
        errors.append("nonblank right half")
    remaining = {(r, c) for r in range(height) for c in range(axis) if grid[r][c] not in (0, 9)}
    source_colors = {grid[r][c] for r, c in remaining}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo, cells = [start], []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    todo.append(neighbor)
        components.append({"size": len(cells), "colors": sorted({grid[r][c] for r, c in cells})})
    if not components:
        errors.append("empty left foreground")
    signature = [len(components), sum(c["size"] == 1 for c in components),
                 sum(len(c["colors"]) != 1 for c in components), len(source_colors)]
    return {"shape": [height, width], "components": components, "signature": signature,
            "scaffold_errors": errors}


def declared_rules(module):
    """Keep the actual declarations and namespaces; no copied rival-name list."""
    rules, declarations, errors = {}, {}, []
    for attribute in RULE_ATTRIBUTES:
        raw = getattr(module, attribute, None)
        declarations[attribute] = {"present": raw is not None, "names": []}
        if raw is None:
            continue
        if not isinstance(raw, dict):
            errors.append(f"{attribute}: expected a dict of named callables")
            continue
        for name, function in raw.items():
            if not isinstance(name, str) or not callable(function):
                errors.append(f"{attribute}[{name!r}]: expected a string name and callable")
                continue
            declarations[attribute]["names"].append(name)
            rules[f"{attribute}/{name}"] = function
        declarations[attribute]["names"].sort()
    return dict(sorted(rules.items())), declarations, errors


def rule_agreement(function, grid, output):
    try:
        prediction = normalized_grid(function(copy.deepcopy(grid)))
        return {"matches_output": prediction == output, "error": None}
    except Exception as error:
        return {"matches_output": None, "error": f"{type(error).__name__}: {error}"}


def cyclic_windows(samples, cycle_length, names):
    """Evaluate every rotation, using cached per-input predictions exactly once."""
    windows = []
    for first in range(0, len(samples), cycle_length):
        cycle = samples[first:first + cycle_length]
        for start in range(cycle_length):
            demos = [cycle[(start + offset) % cycle_length] for offset in range(3)]
            query = cycle[(start + 3) % cycle_length]
            result = {"index": len(windows), "seed": query["seed"], "band": query["band"],
                      "cycle_start": start, "demos": [s["index"] for s in demos],
                      "query": query["index"], "refuted": [], "survived_all": [],
                      "query_discriminates": [], "errors": []}
            for name in names:
                observations = [s["rules"].get(name, {"error": "sample unavailable"}) for s in demos + [query]]
                if any(o["error"] for o in observations):
                    result["errors"].append(name)
                elif not all(o["matches_output"] for o in observations[:3]):
                    result["refuted"].append(name)
                elif observations[3]["matches_output"]:
                    result["survived_all"].append(name)
                else:
                    result["query_discriminates"].append(name)
            windows.append(result)
    return windows


def json_file(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def jsonl_file(path, rows):
    path.write_bytes(b"".join(packed(row) + b"\n" for row in rows))


def probe(runtime, args, output):
    sys.path.insert(0, str(runtime))
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge

    module = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    if not Path(module.__file__).resolve().is_relative_to(runtime):
        raise RuntimeError("generator import escaped the prepared runtime")
    manifest_path = runtime / "RUNTIME_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["files"]:
        if file_digest(runtime / item["runtime_path"]) != item["sha256"]:
            raise RuntimeError(f"runtime source drift: {item['runtime_path']}")
    rule_source = canonical_rule_source(TASK_ID)
    canonical = canonical_pairs(TASK_ID)
    rules, declarations, failures = declared_rules(module)
    canonical_topologies = [topology(pair["input"]) for pair in canonical]
    signatures = {tuple(t["signature"]) for t in canonical_topologies if not t["scaffold_errors"]}
    if not canonical or len(signatures) == 0 or any(t["scaffold_errors"] for t in canonical_topologies):
        failures.append("canonical examples do not establish the assumed centered-rail topology")
    canonical_checks = {name: [rule_agreement(fn, p["input"], p["output"]) for p in canonical]
                        for name, fn in rules.items()}
    bridge, samples = None, []
    try:
        bridge = RacketBridge()
        bridge.eval_text(f"(define coverage-rule {wrap_rule(rule_source)})")
        for band in args.bands:
            for seed in range(args.seed_start, args.seed_start + args.seed_count):
                for sample_index in range(args.cycle_length):
                    sample = {"index": len(samples), "seed": seed, "band": band,
                              "sample_index": sample_index, "rules": {}, "error": None}
                    try:
                        grid = normalized_grid(module.generate(seed, sample_index, difficulty=band))
                        sample.update(input=grid, input_sha256=digest(grid), topology=topology(grid))
                        bridge.define_grid("coverage-input", copy.deepcopy(grid))
                        answer = normalized_grid(bridge.eval_text("(coverage-rule coverage-input)"))
                        sample.update(output=answer, output_sha256=digest(answer))
                        sample["canonical_topology_support"] = (not sample["topology"]["scaffold_errors"]
                                                              and tuple(sample["topology"]["signature"]) in signatures)
                        sample["rules"] = {name: rule_agreement(fn, grid, answer) for name, fn in rules.items()}
                    except Exception as error:
                        sample["error"] = f"{type(error).__name__}: {error}"
                    samples.append(sample)
    finally:
        if bridge is not None:
            bridge.shutdown()
    windows = cyclic_windows(samples, args.cycle_length, rules)
    support = [s for s in samples if s.get("canonical_topology_support")]
    if not support:
        failures.append("zero generated support for canonical component topology")
    if any(s["error"] for s in samples):
        failures.append("generated input or canonical execution failed; see samples.jsonl")
    if any(s.get("topology", {}).get("scaffold_errors") for s in samples):
        failures.append("generated input violates the centered-rail scaffold")
    if any(w["errors"] for w in windows):
        failures.append("declared rule raised or returned an invalid grid")
    if any(w["survived_all"] or w["query_discriminates"] for w in windows):
        failures.append("a declared rival survives all three demonstrations in a cyclic window")
    rule_results = {}
    for name in rules:
        disagrees = [s for s in samples if s["rules"].get(name, {}).get("matches_output") is False]
        checks = canonical_checks[name]
        fits = bool(checks) and all(c["matches_output"] is True for c in checks)
        if any(c["error"] for c in checks):
            failures.append(f"{name}: canonical comparison error")
        if name.startswith("CANONICAL_SHORTCUTS/") and fits and not disagrees:
            failures.append(f"{name}: canonical-fitting shortcut has no generated counterexample")
        rule_results[name] = {"canonical_matches": sum(c["matches_output"] is True for c in checks),
                              "canonical_pair_count": len(checks), "canonical_fits_all": fits,
                              "canonical_errors": [c["error"] for c in checks if c["error"]],
                              "generated_disagreements": len(disagrees),
                              "counterexample_sample": disagrees[0]["index"] if disagrees else None,
                              "window_counts": {key: sum(name in w[key] for w in windows)
                                                for key in ("refuted", "survived_all", "query_discriminates", "errors")}}
    report = {
        "schema": "70a3d3e2c975-cyclic-topology-probe-v1", "task_id": TASK_ID,
        "status": "fail" if failures else "pass", "failures": failures,
        "notes": (["No grid-rule declarations; identifiability checks were unavailable."] if not rules else []),
        "recipe": {"seed_start_inclusive": args.seed_start, "seed_stop_exclusive": args.seed_start + args.seed_count,
                   "seed_count": args.seed_count, "bands": args.bands, "cycle_length": args.cycle_length,
                   "sample_indices": list(range(args.cycle_length)), "demos": 3, "queries": 1,
                   "window_policy": "every cyclic rotation; wrap within each seed/band cycle"},
        "source": {"probe_sha256": file_digest(__file__), "generator_sha256": file_digest(module.__file__),
                   "canonical_rule_utf8_sha256": hashlib.sha256(rule_source.encode()).hexdigest(),
                   "canonical_rule_normalized_hash": normalized_rule_hash(rule_source),
                   "canonical_pairs_sha256": digest(canonical), "runtime_manifest_sha256": file_digest(manifest_path)},
        "counts": {"draws_requested": len(samples), "draws_succeeded": sum(s["error"] is None for s in samples),
                   "unique_inputs": len({s["input_sha256"] for s in samples if "input_sha256" in s}),
                   "cyclic_windows": len(windows), "window_sample_references": 4 * len(windows),
                   "rival_window_evaluations": len(windows) * len(rules),
                   "windows_with_demo_survivors": sum(bool(w["survived_all"] or w["query_discriminates"]) for w in windows),
                   "windows_with_query_ambiguity": sum(bool(w["query_discriminates"]) for w in windows)},
        "topology": {"definition": "four-neighbor left foreground; signature=[components,singletons,polychrome_components,source_colors]",
                     "canonical_signatures": sorted(map(list, signatures)), "canonical_examples": canonical_topologies,
                     "support_draws": len(support), "support_unique_inputs": len({s["input_sha256"] for s in support}),
                     "support_by_band": {band: sum(s["band"] == band for s in support) for band in args.bands},
                     "generated_signature_counts": dict(sorted(Counter(json.dumps(s["topology"]["signature"]) for s in samples if "topology" in s).items()))},
        "declarations": declarations, "rules": rule_results,
        "limitations": ["Finite declared rivals only; passing does not establish unrestricted rule identifiability.",
                        "Cyclic windows reuse inputs and are not independent production lessons.",
                        "A zero-support floor can flag a lawful broad sampler at insufficient sample size."]}
    jsonl_file(output / "samples.jsonl", samples)
    jsonl_file(output / "windows.jsonl", windows)
    json_file(output / "canonical.json", canonical)
    json_file(output / "runtime_manifest.json", manifest)
    report["artifacts"] = {name: file_digest(output / name) for name in
                           ("samples.jsonl", "windows.jsonl", "canonical.json", "runtime_manifest.json")}
    json_file(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=16)
    parser.add_argument("--cycle-length", type=int, default=4)
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"), default=["easy", "medium", "hard"])
    parser.add_argument("--output", type=Path, default=ROOT.parent / "checks" / "coverage_probe")
    parser.add_argument("--runtime", type=Path, help="existing unmodified prepare_runtime snapshot (e.g. baseline)")
    args = parser.parse_args(argv)
    if args.seed_count < 1 or args.cycle_length < 4 or len(set(args.bands)) != len(args.bands):
        parser.error("seed-count must be positive, cycle-length >= 4, and bands distinct")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        if args.runtime:
            report = probe(args.runtime.resolve(), args, output)
        else:
            sys.path.insert(0, str(ROOT / "src"))
            from arcpuzzles import Catalog
            from arcpuzzles.runtime import prepare_runtime
            with tempfile.TemporaryDirectory(prefix=f"coverage-{TASK_ID}-") as directory:
                runtime = Path(directory).resolve()
                prepare_runtime(Catalog(ROOT), runtime, TASK_ID)
                report = probe(runtime, args, output)
    except Exception as error:
        report = {"status": "error", "failures": [f"{type(error).__name__}: {error}"]}
        json_file(output / "report.json", report)
    print(json.dumps({"status": report["status"], "report": str(output / "report.json"),
                      "counts": report.get("counts"), "topology_support": report.get("topology", {}).get("support_draws"),
                      "failures": report["failures"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
