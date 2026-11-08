#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit, public export and causal witness.

Run through ``review.py run`` or ``WORK/run_with_racket.py``.  Public files are
masked controller bundles; only the separately serialized single-query turns
are model-facing.  Reports, episode answers and witness programs are private.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "1034300a135f"
SETTINGS = [{"marker_order": name} for name in ("near_to_far", "far_to_near")]
LIMITS = [
    "Finite rival programs and this seed/count request only; no universal uniqueness claim.",
    "Rivals are fitted on demonstrations only; only survivors are checked on queries.",
    "Every executed output uses protected Racket; runtime errors abort the probe.",
    "No native acceptance, production approval or training admission is conferred.",
]
DEPENDENCY = {
    "step_a": "Globally rank individual marker identities by minimum distance from the input edge, with stable row-major ties and the episode's near/far ordering.",
    "intermediate": "The input-dependent ordered marker identities, coordinates, edge distances and colors; each identity's rank selects an output ring.",
    "step_b": "For each output cell, use its ring depth as an index into A's ranked colors, or use the background after the markers are exhausted.",
    "why_b_depends_on_a": "A marker's geometry can change its rank relative to other markers while preserving row-major color order. B must know those global ranks before choosing each ring's color. The paired witness moves one marker, changing other markers' ring assignments; skipping A preserves the same wrong row-major answer on both inputs. This is a data dependency, not an iterative state simulation.",
}


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def _prototype():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_marker_probe_prototype_" + digest(path.read_bytes()), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _worker():
    source = ROOT / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    module = importlib.import_module("arcpuzzles.parametric_worker")
    if Path(module.__file__).resolve() != source / "arcpuzzles/parametric_worker.py":
        raise ValueError("Probe worker must come from this checkout")
    return module


@contextmanager
def protected_racket():
    """Use the native worker's protected evaluator and exact grid validator."""
    worker = _worker()
    with worker._local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = worker._real_evaluator(ROOT / "shared/runtime")
        counts = {"evaluations": 0}
        def execute(program, grid):
            counts["evaluations"] += 1
            return worker._grid(apply(program, worker._grid(grid)))
        try:
            yield {"execute": execute, "identity": identity, "counts": counts}
        finally:
            bridge.close()


def _replace(program, before, after):
    if program.count(before) != 1:
        raise ValueError(f"Expected one exact native rule clause: {before}")
    return program.replace(before, after, 1)


def _sort_clause(program):
    clauses = ["(sorted (sort-by cells (lambda (p) (first p))))",
               "(sorted (sort-by cells (lambda (p) (- 0 (first p)))))",
               "(sorted (sort-by cells (lambda (p) (- (first p)))))"]
    found = [clause for clause in clauses if clause in program]
    if len(found) != 1:
        raise ValueError("Native spatial sort clause is missing or ambiguous")
    return found[0]


def skip_sort_program(program):
    return _replace(program, _sort_clause(program), "(sorted cells)")


def rival_programs(program, opposite):
    """Eleven total executable shortcuts, including both numeric tie breakers."""
    colors = "(sorted-colors (map second sorted))"
    rivals = {
        "opposite_setting": opposite,
        "skip_spatial_sort": skip_sort_program(program),
        "reverse_equal_distance_ties": _replace(program, "sort-by cells", "sort-by (reverse cells)"),
        "ascending_color_ties": _replace(program, "sort-by cells",
            "sort-by (sort-by cells (lambda (q) (second q)))"),
        "descending_color_ties": _replace(program, "sort-by cells",
            "sort-by (sort-by cells (lambda (q) (- 0 (second q))))"),
        "ignore_zero_markers": _replace(program, "(if (= (at g r c) bg)",
            "(if (or (= (at g r c) bg) (= (at g r c) 0))"),
        "deduplicate_colors": _replace(program, colors,
            "(sorted-colors (remove-duplicates (map second sorted)))"),
        "numeric_color_sort": _replace(program, colors,
            "(sorted-colors (sort-by (map second sorted) (lambda (color) color)))"),
        "extend_final_color": _replace(program,
            "(if (< d n) (nth sorted-colors d) bg)",
            "(if (= n 0) bg (nth sorted-colors (min d (- n 1))))"),
    }
    for cap in (8, 14):
        rivals[f"truncate_markers_at_{cap}"] = _replace(program, colors,
            f"(sorted-colors (take (map second sorted) (min {cap} (length sorted))))")
    return rivals


def audit_episode(episode, execute, rivals):
    """Verify all claims, fit rivals on every demo, then test only survivors."""
    grid = _worker()._grid
    program = episode["program_solution"]
    pairs = [pair for split in ("train", "test") for pair in episode[split]]
    if len({raw(grid(pair["input"])) for pair in pairs}) != len(pairs):
        raise ValueError("Demonstration and query inputs must all be distinct")
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            if grid(execute(program, pair["input"])) != grid(pair["output"]):
                raise ValueError(f"Racket label mismatch: {split}[{index}]")
    rows = []
    for name, rival in rivals.items():
        outputs = [grid(execute(rival, pair["input"])) for pair in episode["train"]]
        refutations = [i for i, (output, pair) in enumerate(zip(outputs, episode["train"]))
                       if output != pair["output"]]
        row = {"name": name, "program": rival, "program_sha256": digest(rival.encode()),
               "demo_refutations": refutations,
               "demo_output_sha256": [digest(raw(output)) for output in outputs],
               "survives_demonstrations": not refutations, "query_checks": []}
        if not refutations:
            for index, pair in enumerate(episode["test"]):
                output = grid(execute(rival, pair["input"]))
                if output != pair["output"]:
                    raise ValueError(f"Demonstration-surviving rival {name!r} harms query {index}")
                row["query_checks"].append({"query_index": index,
                    "matches": True, "output_sha256": digest(raw(output))})
        rows.append(row)
    return {"verified_label_count": len(pairs), "all_inputs_distinct": True,
            "rivals": rows, "harmful_demo_survivors": [], "limits": LIMITS}


def _background(grid):
    counts = Counter(value for row in grid for value in row if value)
    modes = [color for color, count in counts.items() if count == max(counts.values())]
    if len(modes) != 1:
        raise ValueError("Expected a unique nonzero modal background")
    return modes[0]


def pair_dimensions(pair):
    source, output = pair["input"], pair["output"]
    background = _background(source)
    return {"input": [len(source), len(source[0])], "output": [len(output), len(output[0])],
            "markers": sum(value != background for row in source for value in row)}


def source_hashes():
    paths = [ROOT / f"generators/{TASK_ID}/generator.py",
             ROOT / f"generators/{TASK_ID}/tests/test_native_probe.py",
             ROOT / "src/arcpuzzles/parametric_worker.py",
             ROOT / "shared/runtime/reviewer_support.py"]
    paths += [HOME / name for name in ("prototype.py", "adapter.py", "promotion.json", "native_probe.py")]
    paths += [HOME / "rules" / f"native_{setting['marker_order']}.rkt" for setting in SETTINGS]
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(paths)}


def _public_bytes(prototype, episode):
    expected = {"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
                "test": [{"input": p["input"]} for p in episode["test"]]}
    payload = prototype.native_challenge_bytes(episode)
    identity = prototype.native_challenge_id(episode)
    if json.loads(payload) != expected or identity != digest(payload):
        raise ValueError("Public bytes must be the exact visible projection and hash identity")
    return f"challenge-{identity}.json", payload


def build_probe(seed, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6 or type(queries) is not int or queries != 4:
        raise ValueError("The retained probe requires 2..6 demos and exactly four queries")
    before = source_hashes()
    prototype = _prototype()
    episodes, settings_reports, public, turns = [], [], {}, {}
    matched_inputs = None
    with protected_racket() as runtime:
        for setting in SETTINGS:
            episode = prototype.native_generate(seed, deepcopy(setting), demos=demos, queries=queries)
            program = prototype.native_program(setting)
            if (episode.get("program_solution") != program or len(episode["train"]) != demos
                    or len(episode["test"]) != queries):
                raise ValueError("Native episode differs from the requested setting/counts")
            inputs = [p["input"] for split in ("train", "test") for p in episode[split]]
            if matched_inputs is not None and inputs != matched_inputs:
                raise ValueError("Matched seed/count settings must use identical input draws")
            matched_inputs = deepcopy(inputs)
            opposite = next(s for s in SETTINGS if s != setting)
            audit = audit_episode(episode, runtime["execute"],
                                  rival_programs(program, prototype.native_program(opposite)))
            dimensions = {split: [pair_dimensions(pair) for pair in episode[split]]
                          for split in ("train", "test")}
            if not any(p["input"] == [30, 30] and p["output"] == [30, 30] and p["markers"] == 15
                       for p in dimensions["test"]):
                raise ValueError("Four-query probe needs a substantive 30x30, 15-marker case")
            filename, payload = _public_bytes(prototype, episode)
            if filename in public:
                raise ValueError("Duplicate visible controller bundle")
            public[filename] = payload
            turn_files = []
            for index in range(queries):
                turn = prototype.native_public_turn(episode, query_index=index)
                expected = {"train": deepcopy(episode["train"]),
                            "test": [{"input": episode["test"][index]["input"]}]}
                if turn != expected:
                    raise ValueError("Model turn leaks metadata, answers or future queries")
                turn_name, turn_bytes = _public_bytes(prototype, turn)
                if turn_name in turns:
                    raise ValueError("Duplicate visible model turn")
                turns[turn_name] = turn_bytes
                turn_files.append("turns/" + turn_name)
            private = {"task_id": TASK_ID, "seed": seed, "settings": deepcopy(setting),
                       "program": program, "program_sha256": digest(program.encode()),
                       "train": episode["train"], "test": episode["test"],
                       "public_file": "public/" + filename, "turn_files": turn_files}
            episodes.append(private)
            settings_reports.append({"settings": deepcopy(setting), "dimensions": dimensions,
                                     "public_file": private["public_file"], **audit})
        report = {"schema": "arcpuzzles-marker-native-probe-v1", "status": "passed",
                  "task_id": TASK_ID, "seed": seed, "counts": {"demos": demos, "queries": queries},
                  "source_sha256": before, "racket": runtime["identity"],
                  "racket_evaluations": runtime["counts"]["evaluations"],
                  "verified_label_count": sum(row["verified_label_count"] for row in settings_reports),
                  "matched_inputs_across_settings": True, "settings": settings_reports,
                  "public_scope": "public/ holds masked four-query controller bundles; expose only one turns/ file per model turn.",
                  "training_admitted": False, "limits": LIMITS}
    if source_hashes() != before:
        raise ValueError("Probe sources changed during execution")
    return public, turns, episodes, report


def export_probe(seed, demos, queries, out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    public, turns, episodes, report = build_probe(seed, demos, queries)
    # All checks precede publication. Sorted opaque paths prevent setting ordinals.
    files = {**{"public/" + name: data for name, data in public.items()},
             **{"turns/" + name: data for name, data in turns.items()},
             "episodes.private.jsonl": b"".join(raw(e) for e in sorted(episodes, key=lambda e: e["public_file"]))}
    report["files"] = {name: {"sha256": digest(data), "bytes": len(data)} for name, data in sorted(files.items())}
    out.mkdir(parents=True, exist_ok=False)
    for name, data in sorted(files.items()):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
    with (out / "report.json").open("xb") as handle:
        handle.write(raw(report))
    return report


def witness_inputs():
    first = [[7] * 11 for _ in range(11)]
    for row, col, color in ((0, 9, 2), (1, 3, 8), (2, 4, 4), (3, 5, 6), (8, 10, 1)):
        first[row][col] = color
    second = deepcopy(first)
    second[3][5], second[3][10] = 7, 6
    return [first, second]


def intermediate_value(grid, settings):
    height, width, background = len(grid), len(grid[0]), _background(grid)
    markers = [{"position": [r, c], "edge_distance": min(r, c, height - 1 - r, width - 1 - c),
                "color": value} for r, row in enumerate(grid) for c, value in enumerate(row) if value != background]
    sign = 1 if settings["marker_order"] == "near_to_far" else -1
    ranked = sorted(markers, key=lambda marker: sign * marker["edge_distance"])
    return {"background": background, "row_major_colors": [m["color"] for m in markers],
            "ranked_colors": [m["color"] for m in ranked],
            "ranked_markers": [{"rank": rank, **m} for rank, m in enumerate(ranked)]}


def _check_source_binding(binding):
    if binding.get("task_id") != TASK_ID or not binding.get("files") or not binding.get("executor"):
        raise ValueError("Qualification needs this task's native source binding")
    files = [(entry["path"], entry["sha256"]) for entry in binding["files"]]
    files += [("src/arcpuzzles/" + name, sha) for name, sha in binding["executor"].items()]
    for name, expected in files:
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT) or path.is_symlink() or digest(path.read_bytes()) != expected:
            raise ValueError(f"Qualified source changed or escaped checkout: {name}")


def write_witness(qualification, destination):
    destination, qualification = Path(destination), Path(qualification)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    qualified = json.loads(qualification.read_bytes())
    if (qualified.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or qualified.get("status") != "qualified" or qualified.get("task_id") != TASK_ID):
        raise ValueError("Witness requires a successful native qualification for this task")
    binding = qualified["source_binding"]
    _check_source_binding(binding)
    prototype, cases = _prototype(), []
    with protected_racket() as runtime:
        for setting in SETTINGS:
            program = prototype.native_program(setting)
            if qualified["programs"].get(raw(setting).decode().strip()) != digest(program.encode()):
                raise ValueError("Witness rule must be an exact native qualified setting program")
            counterfactual = skip_sort_program(program)
            outputs, wrong_outputs = [], []
            for grid in witness_inputs():
                output = runtime["execute"](program, grid)
                wrong = runtime["execute"](counterfactual, grid)
                if output == wrong:
                    raise ValueError("Skip-A counterfactual must change the final output")
                outputs.append(output)
                wrong_outputs.append(wrong)
                cases.append({"input": grid, "settings": deepcopy(setting),
                              "intermediate_value": intermediate_value(grid, setting),
                              "program": program, "output": output,
                              "counterfactual_program": counterfactual,
                              "counterfactual_output": wrong, "ablation": "skip_a"})
            if outputs[0] == outputs[1] or wrong_outputs[0] != wrong_outputs[1]:
                raise ValueError("Paired witness must change spatial ranks while preserving the skip-sort output")
        witness = {"schema": "arcpuzzles-sequential-dependency-witness-v1", "task_id": TASK_ID,
                   "source_binding": deepcopy(binding), **DEPENDENCY,
                   "racket": {"backend": "racket", "protected": True},
                   "racket_runtime_identity": runtime["identity"],
                   "racket_evaluations": runtime["counts"]["evaluations"], "cases": cases,
                   "limits": "Four bounded Racket cases establish the stated dependency, not universal algorithmic depth or iterative state reasoning."}
    _check_source_binding(binding)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(raw(witness))
    return witness


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--witness", type=Path)
    args = parser.parse_args(argv)
    if args.qualification or args.witness:
        if not args.qualification or not args.witness or args.out:
            parser.error("Use --qualification PATH --witness PATH together, without --out")
        result = write_witness(args.qualification, args.witness)
        summary = {"status": "passed", "cases": len(result["cases"]), "out": str(args.witness)}
    else:
        if args.out is None:
            parser.error("Probe export requires --out PATH")
        result = export_probe(args.seed, args.demos, args.queries, args.out)
        summary = {"status": result["status"], "verified_label_count": result["verified_label_count"],
                   "racket_evaluations": result["racket_evaluations"], "out": str(args.out)}
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
