#!/usr/bin/env python3
"""Portable, current-source Racket/rival probe for f48cc30d7943.

Run through the packet's public wrapper, or from an independently installed
library with Racket available.  See probe_semantics_README.md.  This is an
authoring tool: never open it or its evidence during a visible-only solve.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

try:
    from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK = "f48cc30d7943"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
D8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
NAMESPACES = ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def dump(path, value):
    path.write_bytes(encoded(value) + b"\n")


def chambers(grid, *, directions=D4, passable=lambda v: v != 5):
    """Independent finite-grid flood fill; it does not use generator helpers."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if passable(v)}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells, queue = {start}, deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    cells.add(p)
                    queue.append(p)
        result.append(cells)
    return result


def rectangle(cells):
    rs, cs = zip(*cells)
    return {(r, c) for r in range(min(rs), max(rs) + 1) for c in range(min(cs), max(cs) + 1)}


def graph_distances(cells, seeds):
    found, queue = {p: 0 for p in seeds}, deque(seeds)
    while queue:
        r, c = queue.popleft()
        for dr, dc in D4:
            p = (r + dr, c + dc)
            if p in cells and p not in found:
                found[p] = found[(r, c)] + 1
                queue.append(p)
    return found


def red_objects(grid, cells, directions):
    unseen = {p for p in cells if grid[p[0]][p[1]] == 2}
    count = 0
    while unseen:
        queue = [unseen.pop()]
        count += 1
        for r, c in queue:
            for dr, dc in directions:
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    queue.append(p)
    return count


def transform(grid, *, directions=D4, passable=lambda v: v != 5,
              predicate=lambda n: n == 2, count="cells", fill_box=False,
              count_box=False, accept=lambda g, cells: True, paint_marks=False,
              radius=None, graph_limit=False, marker=None, supplied=None):
    out = deepcopy(grid)
    regions = chambers(grid, directions=directions, passable=passable) if supplied is None else supplied
    for cells in regions:
        scan = rectangle(cells) if count_box else cells
        reds = {p for p in scan if grid[p[0]][p[1]] == 2}
        if count in ("objects4", "objects8"):
            n = red_objects(grid, scan, D4 if count == "objects4" else D8)
        elif count == "marks":
            n = sum(grid[r][c] not in (0, 5) for r, c in scan)
        elif count == "red_and_eight":
            n = sum(grid[r][c] in (2, 8) for r, c in scan)
        else:
            n = len(reds)
        qualifies = predicate(n) or (marker is not None and any(marker(grid[r][c]) for r, c in cells))
        if not qualifies or not accept(grid, cells):
            continue
        distances = graph_distances(cells, reds) if graph_limit else {}
        for r, c in rectangle(cells) if fill_box else cells:
            if radius is not None and min(abs(r - sr) + abs(c - sc) for sr, sc in reds) > radius:
                continue
            if graph_limit and distances[(r, c)] > max(len(grid), len(grid[0])):
                continue
            if grid[r][c] == 0 or (paint_marks and grid[r][c] not in (2, 5)):
                out[r][c] = 8
    return out


def full_line_regions(grid):
    rows = [r for r, row in enumerate(grid) if all(v == 5 for v in row)]
    cols = [c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid)]
    result = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 5:
                key = (sum(rr < r for rr in rows), sum(cc < c for cc in cols))
                result.setdefault(key, set()).add((r, c))
    return list(result.values())


def open_component(grid, cells):
    return any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in cells)


def thin(cells):
    return not any({(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} <= cells for r, c in cells)


def tree(cells):
    return sum((r + dr, c + dc) in cells for r, c in cells for dr, dc in ((1, 0), (0, 1))) == len(cells) - 1


def zero_regions_adjacent_seeds(grid):
    out = deepcopy(grid)
    for cells in chambers(grid, passable=lambda v: v == 0):
        reds = {(r + dr, c + dc) for r, c in cells for dr, dc in D4
                if 0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])
                and grid[r + dr][c + dc] == 2}
        if len(reds) == 2:
            for r, c in cells:
                out[r][c] = 8
    return out


def separated_at_most_eight(grid, cells):
    reds = [(r, c) for r, c in cells if grid[r][c] == 2]
    return len(reds) != 2 or sum(abs(a - b) for a, b in zip(*reds)) <= 8


# An independently authored bank.  These names are deliberately not assumed to
# match the generator's keys; the actual declarations are also loaded below.
INDEPENDENT_RIVALS = {
    "full_line_partition": lambda g: transform(g, supplied=full_line_regions(g)),
    "eight_connected_rooms": lambda g: transform(g, directions=D8),
    "zero_red_only_passable": lambda g: transform(g, passable=lambda v: v in (0, 2)),
    "component_bbox_fill": lambda g: transform(g, fill_box=True),
    "component_bbox_seed_count": lambda g: transform(g, count_box=True),
    "solid_rectangles_only": lambda g: transform(g, accept=lambda g, c: c == rectangle(c)),
    "positive_even_seed_count": lambda g: transform(g, predicate=lambda n: n > 0 and n % 2 == 0),
    "two_modulo_three": lambda g: transform(g, predicate=lambda n: n % 3 == 2),
    "two_or_at_least_four": lambda g: transform(g, predicate=lambda n: n == 2 or n >= 4),
    "all_nonwall_marks_are_seeds": lambda g: transform(g, count="marks"),
    "paint_every_nonwall_nonred_cell": lambda g: transform(g, paint_marks=True),
    "nearest_seed_radius_eight": lambda g: transform(g, radius=8),
    "enclosed_rooms_only": lambda g: transform(g, accept=lambda g, c: not open_component(g, c)),
    "walls_required": lambda g: transform(g) if any(5 in row for row in g) else deepcopy(g),
    "two_chambers_required": lambda g: transform(g) if len(chambers(g)) >= 2 else deepcopy(g),
    "two_red_objects_four": lambda g: transform(g, count="objects4"),
    "two_red_objects_eight": lambda g: transform(g, count="objects8"),
    "zero_regions_adjacent_two_red_cells": zero_regions_adjacent_seeds,
    "at_least_two_seed_cells": lambda g: transform(g, predicate=lambda n: n >= 2),
    "one_or_two_seed_cells": lambda g: transform(g, predicate=lambda n: 1 <= n <= 2),
    "rectangles_or_thin_paths": lambda g: transform(g, accept=lambda g, c: c == rectangle(c) or thin(c)),
    "rectangles_or_trees": lambda g: transform(g, accept=lambda g, c: c == rectangle(c) or tree(c)),
    "rectangles_or_open_components": lambda g: transform(g, accept=lambda g, c: c == rectangle(c) or open_component(g, c)),
    "graph_flood_at_most_max_dimension": lambda g: transform(g, graph_limit=True),
    "eight_as_wall": lambda g: transform(g, passable=lambda v: v not in (5, 8)),
    "red_plus_eight_seed_count": lambda g: transform(g, count="red_and_eight"),
    "cyan_marker_activates": lambda g: transform(g, marker=lambda v: v == 8),
    "foreign_marker_activates": lambda g: transform(g, marker=lambda v: v not in (0, 2, 5, 8)),
    "two_reds_with_manhattan_separation_at_most_eight": lambda g: transform(g, accept=separated_at_most_eight),
}


def hand_cases():
    result = []
    def add(name, rows, purpose):
        grid = [[int(v) for v in row] if isinstance(row, str) else list(row) for row in rows]
        result.append({"id": name, "kind": "witness", "input": grid, "purpose": purpose})
    add("bent_bbox_zero_decoy", ["200", "552", "050"], "Disconnected zero lies inside a qualifying chamber's bounding box.")
    add("bent_bbox_red_decoy", ["200", "552", "250"], "Disconnected red lies inside a qualifying chamber's bounding box.")
    add("diagonal_one_plus_one", ["205", "552"], "Two one-red chambers touch only diagonally.")
    add("diagonal_two_plus_one", ["2205", "5552"], "A qualifying chamber touches a one-red chamber diagonally.")
    add("gray_island", ["202", "050", "000"], "A gray island makes a connected nonrectangle.")
    add("red_chain_bridge", ["0220"], "Adjacent red cells remain traversable.")
    add("open_wall_doorway", ["202", "050", "020"], "An incomplete wall does not isolate the third red.")
    add("single_open_qualifying_chamber", ["022"], "The reference needs neither a wall nor multiple chambers.")
    add("long_qualifying_corridor", ["22000000000"], "Filling extends beyond a Manhattan radius of eight.")
    add("separated_two_reds", ["2000000002"], "The two red seeds may be farther than eight Manhattan steps apart.")
    add("no_zero_qualifying", ["22"], "No original zero means no visible edit.")
    add("all_wall", ["55", "55"], "No traversable chamber exists.")
    add("all_zero", ["00", "00"], "A zero-red chamber remains unchanged.")
    for n in range(7):
        add("seed_count_" + str(n), [[2] * n + [0]], "Exact red-cell count " + str(n) + ".")
    for color in (1, 3, 4, 6, 7, 8, 9):
        add("passable_color_bridge_" + str(color), [[2, 0, color, 0, 2]], "This non-5 color is preserved and joins two red sides.")
    add("extra_color_not_a_seed", ["2230"], "A nonred mark is preserved and does not contribute a red seed.")
    add("enclosed_bent_bbox_zero_decoy", ["55555", "52005", "55525", "50505", "55555"], "The bent witness also works within a full outer frame.")
    add("minimal_bent_qualifying", ["20", "52"], "Smallest bent qualifying three-cell component.")
    add("nonzero_preservation_without_zero", ["223"], "Only original zeros can change, even in a qualifying room.")
    return result


def selected_source():
    for relative in (f"generators/{TASK}/generator.py", f"puzzle_generators/per_puzzle/{TASK}/generator.py"):
        path = ROOT / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"No selected {TASK} generator in this tree: {ROOT}")


def load_generator(path):
    spec = importlib.util.spec_from_file_location("f48cc30d7943_live_semantic_probe", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_binding():
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append({"line_sha256": digest(line.rstrip("\n").encode()), "program": row["program_solution"]})
    normalized = {" ".join(row["program"].split()) for row in rows}
    if len(normalized) != 1:
        raise ValueError("Selected canonical authority is missing or ambiguous")
    return {"selected_row_sha256": [r["line_sha256"] for r in rows],
            "raw_program_sha256": sorted({digest(r["program"].encode()) for r in rows}),
            "normalized_rule_sha256": digest(next(iter(normalized)).encode()),
            "rule_hash": digest(next(iter(normalized)).encode())[:12]}


def source_files(source):
    paths = {source, Path(__file__).resolve(), HERE / "design_variants.json"}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                paths.add(path)
    for relative in ("src/arcpuzzles/cli.py", "src/arcpuzzles/runtime.py", "src/arcpuzzles/worker.py",
                     "src/arcpuzzles/catalog.py", "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"):
        path = ROOT / relative
        if path.is_file():
            paths.add(path)
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)}


def assert_current(binding):
    for relative, expected in binding["files"].items():
        path = ROOT / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or not path.resolve().is_relative_to(ROOT):
            raise RuntimeError("Invalid source binding path: " + relative)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise RuntimeError("Stale source binding: " + relative)
    if canonical_binding() != binding["canonical"]:
        raise RuntimeError("Stale canonical rule or pair binding")


def pure_call(function, grid, *, kind="grid"):
    outputs = []
    for _ in range(2):
        argument = deepcopy(grid)
        value = function(argument)
        if argument != grid:
            raise ValueError("Callable mutated its input")
        if kind == "grid":
            value = normalize_grid(value)
            if (len(value), len(value[0])) != (len(grid), len(grid[0])):
                raise ValueError("Callable changed grid dimensions")
        elif kind == "bool" and type(value) is not bool:
            raise ValueError("Witness must return a bool")
        outputs.append(value)
    if outputs[0] != outputs[1]:
        raise ValueError("Callable is nondeterministic on repeated input")
    return outputs[0]


def declarations(generator):
    inventory, functions = {}, {"independent/" + n: f for n, f in INDEPENDENT_RIVALS.items()}
    for namespace in NAMESPACES:
        bank = getattr(generator, namespace, None)
        if not isinstance(bank, dict) or not bank or not all(isinstance(n, str) and callable(f) for n, f in bank.items()):
            raise ValueError(namespace + " must be a nonempty dict[str, callable]")
        inventory[namespace] = sorted(bank)
        functions.update({namespace + "/" + n: f for n, f in bank.items()})
    witnesses = getattr(generator, "SEMANTIC_WITNESSES", None)
    mapping = getattr(generator, "WITNESS_RIVALS", None)
    if not isinstance(witnesses, dict) or not witnesses or not isinstance(mapping, dict):
        raise ValueError("Nonempty SEMANTIC_WITNESSES and WITNESS_RIVALS are required")
    for name, function in witnesses.items():
        if not isinstance(name, str) or not callable(function):
            raise ValueError("Invalid semantic witness declaration")
        rivals = mapping.get(name)
        if not isinstance(rivals, list) or not rivals or any(r not in generator.SEMANTIC_RIVALS for r in rivals):
            raise ValueError("Invalid WITNESS_RIVALS entry: " + name)
    inventory["SEMANTIC_WITNESSES"] = sorted(witnesses)
    inventory["WITNESS_RIVALS"] = deepcopy(mapping)
    return inventory, functions, witnesses


def collect_cases(generator, seeds):
    cases = [{"id": f"canonical_{p['variant']}_{p['split']}_{p['pair_index']}", "kind": "canonical",
              "input": p["input"], "canonical_output": p["output"],
              "identity": {k: p[k] for k in ("variant", "split", "pair_index")}}
             for p in canonical_pairs(TASK, root=ROOT)]
    cases.extend(hand_cases())
    for case in json.loads((HERE / "design_variants.json").read_text())["cases"]:
        cases.append({"id": case["id"], "kind": "design", "input": case["input"],
                      "retained_reference_output": case["reference_output"],
                      "valid_core": case["valid_core"], "variant": case["variant"],
                      "intent": "intentional negative geometry boundary" if not case["valid_core"] else "design comparison"})
    for band in ("easy", "medium", "hard"):
        for seed in seeds:
            for index in range(3):
                first = generator.generate(seed, index, difficulty=band)
                second = generator.generate(seed, index, difficulty=band)
                if first != second:
                    raise ValueError("Generator draw changed on exact replay")
                grid = normalize_grid(first)
                errors = generator.self_check(deepcopy(grid))
                if errors:
                    raise ValueError("Generated teaching-domain failure: " + repr(errors))
                cases.append({"id": f"generated_{band}_{seed}_{index}", "kind": "generated", "input": grid,
                              "replay": {"seed": seed, "sample_index": index, "difficulty": band},
                              "schedule_profile": generator.schedule_profile(seed, index, difficulty=band)})
    return cases


def apply_public(cases, out, binding, timeout, receipts):
    if not (ROOT / "catalog/puzzles.jsonl").is_file():
        raise RuntimeError("Reference execution requires this task's independent library checkout, not a tests-only runtime; no sibling fallback is allowed")
    environment = os.environ.copy()
    own_paths = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    environment["PYTHONPATH"] = os.pathsep.join(own_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for number, start in enumerate(range(0, len(cases), 64)):
        batch = cases[start:start + 64]
        inp, ref = out / f"inputs-{number:02d}.json", out / f"reference-{number:02d}.json"
        dump(inp, {"inputs": [case["input"] for case in batch]})
        argv = [sys.executable, "-m", "arcpuzzles", "--library", str(ROOT), "apply", TASK,
                "--input", str(inp), "--timeout", str(timeout), "--out", str(ref)]
        receipt = {"argv": argv, "cwd": str(ROOT), "input_sha256": digest(inp.read_bytes()),
                   "generator_sha256": binding["generator_sha256"], "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        receipts.append(receipt)
        started = time.monotonic()
        try:
            process = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True, text=True, timeout=timeout + 30)
        except subprocess.TimeoutExpired as exc:
            receipt.update({"exit_code": None, "timed_out": True, "elapsed_seconds": round(time.monotonic() - started, 3)})
            (out / f"reference-{number:02d}.stdout.log").write_bytes(exc.stdout or b"")
            (out / f"reference-{number:02d}.stderr.log").write_bytes(exc.stderr or b"")
            dump(out / "command_receipts.json", receipts)
            raise
        receipt.update({"exit_code": process.returncode, "timed_out": False,
                        "elapsed_seconds": round(time.monotonic() - started, 3)})
        (out / f"reference-{number:02d}.stdout.log").write_text(process.stdout)
        (out / f"reference-{number:02d}.stderr.log").write_text(process.stderr)
        dump(out / "command_receipts.json", receipts)
        assert_current(binding)
        if process.returncode:
            raise RuntimeError("Public Racket apply failed; see retained command receipt and logs")
        if digest(inp.read_bytes()) != receipt["input_sha256"]:
            raise RuntimeError("Reference inputs changed during public apply")
        raw = json.loads(ref.read_text())
        if (raw.get("generator_sha256") != binding["generator_sha256"]
                or raw.get("task_id") != TASK or raw.get("rule_task_id") != TASK
                or raw.get("reference") != "canonical" or raw.get("rule_hash_matches_catalog") is not True
                or raw.get("executed_rule_hash") != binding["canonical"]["rule_hash"]
                or raw.get("catalog_rule_hash") != binding["canonical"]["rule_hash"]):
            raise RuntimeError("Public reference source/rule binding mismatch")
        receipt["reference_sha256"] = digest(ref.read_bytes())
        receipt["executed_rule_hash"] = raw["executed_rule_hash"]
        receipt["rule_callable_text_sha256"] = raw["rule_text_sha256"]
        for case, item in zip(batch, raw["results"], strict=True):
            if item.get("error") is not None or not item.get("valid_output") or item["input"] != case["input"]:
                raise RuntimeError("Reference error or input ordering mismatch: " + case["id"])
            answer = normalize_grid(item["output"])
            if item["input_sha256"] != digest(encoded(case["input"])) or item["output_sha256"] != digest(encoded(answer)):
                raise RuntimeError("Reference grid digest mismatch: " + case["id"])
            case["reference_output"] = answer
            for key in ("canonical_output", "retained_reference_output"):
                if key in case and case[key] != answer:
                    raise RuntimeError("Retained/canonical label drift: " + case["id"])
        dump(out / "command_receipts.json", receipts)


def evaluate(cases, generator, inventory, functions, witnesses):
    predictions = {}
    stats = {name: {"canonical_failures": [], "generated_disagreements": [], "hand_disagreements": [], "errors": []} for name in functions}
    issues, witness_hits = [], {name: [] for name in witnesses}
    for case in cases:
        grid, expected = case["input"], case["reference_output"]
        if transform(grid) != expected:
            issues.append("Independent rule model differs from Racket: " + case["id"])
        case["self_check"] = generator.self_check(deepcopy(grid))
        case["predictions"], case["witnesses"] = {}, {}
        for name, function in functions.items():
            try:
                prediction = pure_call(function, grid)
                key = digest(encoded(prediction))
                predictions[key] = prediction
                differs = prediction != expected
                case["predictions"][name] = {"output_sha256": key, "differs": differs}
                if differs:
                    kind = "canonical_failures" if case["kind"] == "canonical" else "generated_disagreements" if case["kind"] == "generated" else "hand_disagreements"
                    stats[name][kind].append(case["id"])
            except Exception as exc:
                error = type(exc).__name__ + ": " + str(exc)
                case["predictions"][name] = {"error": error}
                stats[name]["errors"].append({"case": case["id"], "error": error})
                issues.append(name + " failed on " + case["id"])
        for name, function in witnesses.items():
            try:
                fires = pure_call(function, grid, kind="bool")
                mapped = inventory["WITNESS_RIVALS"][name]
                refuted = [r for r in mapped if case["predictions"]["SEMANTIC_RIVALS/" + r].get("differs")]
                case["witnesses"][name] = {"fires": fires, "refuted_mapped_rivals": refuted}
                if fires:
                    witness_hits[name].append(case["id"])
                    if not refuted:
                        issues.append("False semantic witness claim: " + name + " on " + case["id"])
            except Exception as exc:
                case["witnesses"][name] = {"error": type(exc).__name__ + ": " + str(exc)}
                issues.append("Witness failure: " + name + " on " + case["id"])
    for name, entry in stats.items():
        entry["canonical_fitting"] = not entry["canonical_failures"] and not entry["errors"]
        entry["sampled_generator_fitting"] = not entry["generated_disagreements"] and not entry["errors"]
        choices = entry["hand_disagreements"] + entry["generated_disagreements"]
        entry["smallest_retained_counterexample"] = min(choices, key=lambda name: next((len(c["input"]) * len(c["input"][0]), len(c["input"]), name) for c in cases if c["id"] == name), default=None)
        if name.startswith("CANONICAL_SHORTCUTS/") and not entry["canonical_fitting"]:
            issues.append("Declared canonical shortcut does not fit every canonical pair: " + name)
    for name, hits in witness_hits.items():
        if not hits:
            issues.append("Declared witness was not exercised: " + name)
    return stats, predictions, witness_hits, issues


def artifacts(out):
    return {path.name: {"bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
            for path in sorted(out.iterdir()) if path.is_file() and path.name not in ("results.json", "failure.json")}


def verify_retained_labels(previous, old, cases, binding):
    """Bind rescored cases to original raw reference bytes, not just a summary."""
    reference_names = sorted(name for name in old["artifacts"]
                             if name.startswith("reference-") and name.endswith(".json"))
    receipts = old.get("command_receipts", [])
    if not receipts or len(reference_names) != len(receipts):
        raise RuntimeError("Supply the original Racket-run results, not a chained retained-label verification")
    original = []
    for name, receipt in zip(reference_names, receipts, strict=True):
        path = previous.parent / name
        if digest(path.read_bytes()) != receipt.get("reference_sha256"):
            raise RuntimeError("Reference file is not bound to its command receipt: " + name)
        raw = json.loads(path.read_text())
        if (raw.get("task_id") != TASK or raw.get("rule_task_id") != TASK
                or raw.get("generator_sha256") != binding["generator_sha256"]
                or raw.get("reference") != "canonical" or raw.get("rule_hash_matches_catalog") is not True
                or raw.get("executed_rule_hash") != binding["canonical"]["rule_hash"]
                or raw.get("catalog_rule_hash") != binding["canonical"]["rule_hash"]):
            raise RuntimeError("Retained public reference source/rule binding mismatch")
        original.extend(raw["results"])
    for case, item in zip(cases, original, strict=True):
        if (item.get("error") is not None or item.get("valid_output") is not True
                or case["input"] != item["input"] or case["reference_output"] != item["output"]
                or item["input_sha256"] != digest(encoded(case["input"]))
                or item["output_sha256"] != digest(encoded(case["reference_output"]))):
            raise RuntimeError("Retained case differs from its original Racket record: " + case["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New output directory; existing paths are refused")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--expect-source-sha256")
    parser.add_argument("--verify-retained", type=Path, help="Verify/rescore exact retained bytes; rejects changed source, probe or reference artifacts")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "f48cc30d7943-portable-semantic-probe-v1", "task_id": TASK,
              "argv": sys.argv, "cwd": str(Path.cwd()), "library_root": str(ROOT),
              "python_executable": sys.executable, "reference_method": "public python -m arcpuzzles --library ... apply",
              "command_receipts": []}
    try:
        source = selected_source()
        generator = load_generator(source)
        binding = {"generator_path": str(source.relative_to(ROOT)), "generator_sha256": digest(source.read_bytes()),
                   "files": source_files(source), "canonical": canonical_binding()}
        record["source_bindings"] = binding
        if args.expect_source_sha256 and args.expect_source_sha256 != binding["generator_sha256"]:
            raise RuntimeError("Expected selected generator SHA-256 does not match current bytes")
        if getattr(generator, "RULE_HASH", None) != binding["canonical"]["rule_hash"]:
            raise RuntimeError("Generator RULE_HASH does not match selected canonical authority")
        inventory, functions, witnesses = declarations(generator)
        record["declarations"] = inventory
        if args.verify_retained:
            previous = args.verify_retained.resolve()
            old = json.loads(previous.read_text())
            if old.get("status") != "passed":
                raise RuntimeError("Retained run is not a completed pass")
            assert_current(old["source_bindings"])
            if old["source_bindings"] != binding or old["declarations"] != inventory:
                raise RuntimeError("Retained source or actual declaration inventory is stale")
            for name, entry in old["artifacts"].items():
                if Path(name).name != name:
                    raise RuntimeError("Invalid retained artifact filename: " + name)
                path = previous.parent / name
                if not path.is_file() or path.stat().st_size != entry["bytes"] or digest(path.read_bytes()) != entry["sha256"]:
                    raise RuntimeError("Retained artifact is missing or changed: " + name)
            cases = [{k: v for k, v in case.items() if k not in ("predictions", "witnesses", "self_check")} for case in old["cases"]]
            verify_retained_labels(previous, old, cases, binding)
            record["retained_run"] = {"path": str(previous), "sha256": digest(previous.read_bytes()),
                                      "reference_rerun": False, "reference_command_receipts": old["command_receipts"]}
        else:
            cases = collect_cases(generator, args.seeds)
            assert_current(binding)
            dump(out / "materialized_cases.json", cases)
            apply_public(cases, out, binding, args.timeout, record["command_receipts"])
        stats, predictions, hits, issues = evaluate(cases, generator, inventory, functions, witnesses)
        assert_current(binding)
        dump(out / "predicted_outputs.json", predictions)
        record.update({"status": "passed" if not issues else "failed", "issues": issues, "statistics": stats,
                       "cases": cases, "witness_hits": hits,
                       "counts": {kind: sum(c["kind"] == kind for c in cases) for kind in ("canonical", "witness", "design", "generated")},
                       "unique_inputs": len({digest(encoded(c["input"])) for c in cases})})
        summary = {"status": record["status"], "generator_sha256": binding["generator_sha256"], "counts": record["counts"],
                   "unique_inputs": record["unique_inputs"], "declaration_sizes": {n: len(inventory[n]) for n in NAMESPACES},
                   "independent_rivals": len(INDEPENDENT_RIVALS), "issues": issues,
                   "canonical_fitting_and_sample_fitting": [name for name, entry in stats.items() if entry["canonical_fitting"] and entry["sampled_generator_fitting"]],
                   "limits": "Finite named alternatives and retained draws only. Hand witnesses can lie outside the teaching grammar or sampler. Agreement does not prove universal induction; this is not a lesson or private-query correctness check."}
        dump(out / "summary.json", summary)
        record["artifacts"] = artifacts(out)
        dump(out / "results.json", record)
        print(json.dumps(summary, indent=2))
        return 0 if not issues else 1
    except Exception as exc:
        record.update({"status": "failed", "error": type(exc).__name__ + ": " + str(exc), "traceback": traceback.format_exc()})
        dump(out / "failure.json", record)
        print(json.dumps({"status": "failed", "error": record["error"], "evidence": str(out / "failure.json")}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
