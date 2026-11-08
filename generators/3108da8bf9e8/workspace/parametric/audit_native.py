"""Finite protected-Racket audit of whole-block ranking lessons.

Hypotheses are fitted to demonstrations before any query is checked. Racket
errors fail the audit; they never refute a hypothesis. Independent Python
extractors and breadth-first component counting check each executable meaning.
The deliberately ambiguous two-demo witness is private research evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
TASK_ID = "3108da8bf9e8"
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


SETTINGS = ({"rank_basis": "cells"}, {"rank_basis": "components_then_cells"})
JOBS = ((0, 2), (17, 3), (22, 6))
RIVALS = (
    "cell_count", "components8_then_cells", "color2_components_then_cells",
    "components4_only", "components4_then_reverse_cells",
    "reverse_components4_then_cells", "reverse_rank", "ascending_from_top_left",
    "identity", "row_local", "column_local", "reverse_macro_rows",
    "repaint_prefix", "fixed_map_demo1", "largest_component_then_cells",
    "perimeter_then_cells",
)
TARGET_ORDER = (6, 7, 8, 3, 4, 5, 0, 1, 2)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"rank_basis"}
            or type(settings["rank_basis"]) is not str
            or settings["rank_basis"] not in ("cells", "components_then_cells")):
        raise ValueError("Expected one exact rank_basis setting")
    return settings["rank_basis"]


def _bands(indices):
    result = []
    for index in indices:
        if not result or index != result[-1][-1] + 1:
            result.append([index])
        else:
            result[-1].append(index)
    return result


def geometry(grid):
    grid = _grid(grid)
    rows = _bands([r for r, row in enumerate(grid) if any(row)])
    cols = _bands([c for c in range(len(grid[0])) if any(grid[r][c] for r in range(len(grid)))])
    if len(rows) != 3 or len(cols) != 3:
        raise ValueError("Expected three occupied row bands and column bands")
    if len({len(band) for band in rows + cols}) != 1:
        raise ValueError("Expected nine equal square blocks")
    if rows[0][0] or cols[0][0] or rows[-1][-1] != len(grid) - 1 or cols[-1][-1] != len(grid[0]) - 1:
        raise ValueError("Outer padding is outside this family")
    occupied = {(r, c) for rb in rows for cb in cols for r in rb for c in cb}
    if any(grid[r][c] not in (1, 2) for r, c in occupied):
        raise ValueError("Block cells must be color1 or color2")
    if any(grid[r][c] != 0 for r in range(len(grid)) for c in range(len(grid[0])) if (r, c) not in occupied):
        raise ValueError("Separators must be all zero")
    return rows, cols


def extract_blocks(grid):
    rows, cols = geometry(grid)
    return [[[grid[r][c] for c in cb] for r in rb] for rb in rows for cb in cols]


def components(block, color=1, connectivity=4):
    if connectivity not in (4, 8):
        raise ValueError("Connectivity must be4 or8")
    pending = {(r, c) for r, row in enumerate(block) for c, value in enumerate(row) if value == color}
    result = []
    while pending:
        origin = min(pending)
        pending.remove(origin)
        group, stack = {origin}, [origin]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (connectivity == 4 and abs(dr) + abs(dc) != 1):
                        continue
                    point = r + dr, c + dc
                    if point in pending:
                        pending.remove(point)
                        group.add(point)
                        stack.append(point)
        result.append(group)
    return result


def component_count(block, color=1, connectivity=4):
    return len(components(block, color, connectivity))


def perimeter(block):
    points = {(r, c) for r, row in enumerate(block) for c, value in enumerate(row) if value == 1}
    return sum((r + dr, c + dc) not in points for r, c in points
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _key(block, settings, name):
    cells = sum(value == 1 for row in block for value in row)
    comps = component_count(block)
    if name == "cell_count":
        return (cells,)
    if name == "components8_then_cells":
        return component_count(block, connectivity=8), cells
    if name == "color2_components_then_cells":
        return component_count(block, color=2), len(block) ** 2 - cells
    if name == "components4_only":
        return (comps,)
    if name == "components4_then_reverse_cells":
        return comps, -cells
    if name == "reverse_components4_then_cells":
        return -comps, cells
    if name == "largest_component_then_cells":
        return max([0] + [len(group) for group in components(block)]), cells
    if name == "perimeter_then_cells":
        return perimeter(block), cells
    return (cells,) if _setting(settings) == "cells" else (comps, cells)


def _place(grid, blocks):
    rows, cols = geometry(grid)
    result = [[0] * len(grid[0]) for _ in grid]
    for index, block in enumerate(blocks):
        for dr, r in enumerate(rows[index // 3]):
            for dc, c in enumerate(cols[index % 3]):
                result[r][c] = block[dr][dc]
    return result


def learned_map(first_pair):
    """Fit one source-position permutation using this demonstration only."""
    inputs, outputs = extract_blocks(first_pair["input"]), extract_blocks(first_pair["output"])
    if len({packed(block) for block in inputs}) != 9:
        raise ValueError("A fixed-map witness requires nine distinct input blocks")
    result = []
    for block in outputs:
        if block not in inputs:
            raise ValueError("Output is not a whole-block permutation")
        result.append(inputs.index(block))
    if sorted(result) != list(range(9)):
        raise ValueError("Output does not preserve every whole block exactly once")
    return tuple(result)


def rival_reference(grid, settings, name, *, fixed_map=None):
    """Independent reference: no production or prototype functions are used."""
    _setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    blocks = extract_blocks(grid)
    key = lambda index: _key(blocks[index], settings, name)
    ranked = sorted(range(9), key=key, reverse=name == "reverse_rank")
    order = [ranked[index] for index in TARGET_ORDER]
    if name == "ascending_from_top_left":
        order = ranked
    elif name == "identity":
        order = list(range(9))
    elif name == "reverse_macro_rows":
        order = list(TARGET_ORDER)
    elif name == "row_local":
        order = [index for start in (0, 3, 6) for index in sorted(range(start, start + 3), key=key)]
    elif name == "column_local":
        order = [0] * 9
        for col in range(3):
            indices = sorted(range(col, 9, 3), key=key, reverse=True)
            for row, source in enumerate(indices):
                order[3 * row + col] = source
    elif name == "fixed_map_demo1":
        if fixed_map is None or sorted(fixed_map) != list(range(9)):
            raise ValueError("fixed_map_demo1 requires a source-position permutation")
        order = list(fixed_map)
    placed = [blocks[index] for index in order]
    if name == "repaint_prefix":
        side = len(blocks[0])
        placed = [[[1 if r * side + c < sum(v == 1 for row in block for v in row) else 2
                    for c in range(side)] for r in range(side)] for block in placed]
    return _place(grid, placed)


def reference(grid, settings):
    if _setting(settings) == "cells" and (len(grid) != 11 or len(grid[0]) != 11):
        raise ValueError("The exact canonical program has fixed11x11 geometry")
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name, *, fixed_map=None):
    """Independent complete Racket sources for every finite hypothesis."""
    basis = _setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    key = {
        "cell_count": "(list n)",
        "components8_then_cells": "(list (length (objects-8 b 2)) n)",
        "color2_components_then_cells": "(list (length (objects b 1)) (- (* k k) n))",
        "components4_only": "(list (length (objects b 2)))",
        "components4_then_reverse_cells": "(list (length (objects b 2)) (- n))",
        "reverse_components4_then_cells": "(list (- (length (objects b 2))) n)",
        "largest_component_then_cells": "(list (apply max (cons 0 (map obj-size (objects b 2)))) n)",
        "perimeter_then_cells": "(list (boundary b) n)",
    }.get(name, "(list n)" if basis == "cells" else "(list (length (objects b 2)) n)")
    descending = "#t" if name in ("reverse_rank", "column_local") else "#f"
    order = "(for/list ((i (list 6 7 8 3 4 5 0 1 2))) (list-ref ranked i))"
    if name == "ascending_from_top_left":
        order = "ranked"
    elif name == "identity":
        order = "records"
    elif name == "reverse_macro_rows":
        order = "(for/list ((i (list 6 7 8 3 4 5 0 1 2))) (list-ref records i))"
    elif name == "row_local":
        order = "(apply append (for/list ((r (range 0 3))) (sort (take (drop records (* r 3)) 3) less-record?)))"
    elif name == "column_local":
        order = "(for/list ((i (range 0 9))) (list-ref (sort (for/list ((r (range 0 3))) (list-ref records (+ (* r 3) (remainder i 3)))) less-record?) (quotient i 3)))"
    elif name == "fixed_map_demo1":
        if fixed_map is None or sorted(fixed_map) != list(range(9)):
            raise ValueError("fixed_map_demo1 requires a source-position permutation")
        order = "(for/list ((i (list " + " ".join(map(str, fixed_map)) + "))) (list-ref records i))"
    cell = "(if (< (+ (* dr k) dc) (third source)) 1 2)" if name == "repaint_prefix" else "(at (second source) dr dc)"
    return f"""(rule! (lambda (g)
  (define rs (filter (lambda (r) (and (!= (at g r 0) 0) (or (= r 0) (= (at g (- r 1) 0) 0)))) (range 0 (rows g))))
  (define cs (filter (lambda (c) (and (!= (at g 0 c) 0) (or (= c 0) (= (at g 0 (- c 1)) 0)))) (range 0 (cols g))))
  (define k (find-first (lambda (r) (= (at g r 0) 0)) (range 0 (rows g))))
  (define (boundary b)
    (for/sum ((r (range 0 k))) (for/sum ((c (range 0 k)))
      (if (= (at b r c) 1)
        (for/sum ((d (list (list 1 0) (list -1 0) (list 0 1) (list 0 -1))))
          (let ((nr (+ r (first d))) (nc (+ c (second d))))
            (if (or (< nr 0) (>= nr k) (< nc 0) (>= nc k) (!= (at b nr nc) 1)) 1 0))) 0))))
  (define (key< a b)
    (cond ((empty? a) #f) ((< (first a) (first b)) #t)
          ((> (first a) (first b)) #f) (else (key< (rest a) (rest b)))))
  (define records (for/list ((i (range 0 9)))
    (let* ((b (grid-from-fn k k (lambda (r c) (at g (+ (list-ref rs (quotient i 3)) r) (+ (list-ref cs (remainder i 3)) c)))))
           (n (for/sum ((r (range 0 k))) (for/sum ((c (range 0 k))) (if (= (at b r c) 1) 1 0)))))
      (list i b n {key}))))
  (define (less-record? a b)
    (if {descending} (key< (fourth b) (fourth a)) (key< (fourth a) (fourth b))))
  (define ranked (sort records less-record?))
  (define chosen {order})
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (or (= (at g r 0) 0) (= (at g 0 c) 0)) 0
        (let* ((br (- (length (filter (lambda (start) (<= start r)) rs)) 1))
               (bc (- (length (filter (lambda (start) (<= start c)) cs)) 1))
               (source (list-ref chosen (+ (* br 3) bc)))
               (dr (- r (list-ref rs br))) (dc (- c (list-ref cs bc))))
          {cell}))))))"""


class CachedEvaluator:
    def __init__(self, apply):
        self.apply, self.cache = apply, {}
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None

    def __call__(self, program, grid):
        self.requests += 1
        key = program, packed(grid)
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.last_request = {"program_sha256": sha(program.encode()), "input_sha256": sha(key[1])}
        self.evaluations += 1
        result = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(result)
        return result


def assess(name, program, train, test, execute):
    outputs = [execute(program, pair["input"]) for pair in train]
    rejected = [i for i, (out, pair) in enumerate(zip(outputs, train)) if out != pair["output"]]
    survives, prefix = not rejected, not any(i < 2 for i in rejected)
    checked_for = (["all_demonstrations"] if survives else []) + (["first_two_prefix"] if prefix else [])
    queries = [execute(program, pair["input"]) for pair in test] if checked_for else None
    differences = ([i for i, (out, pair) in enumerate(zip(queries, test)) if out != pair["output"]]
                   if queries is not None else None)
    return {"name": name, "program_sha256": sha(program.encode()), "demo_outputs": outputs,
            "rejected_by_demo_indices": rejected, "survives_demonstrations": survives,
            "survives_first_two": prefix, "query_checked_for": checked_for,
            "query_outputs": queries, "query_disagreement_indices": differences}


def ambiguous_demonstrations():
    """Two distinct lawful11x11 inputs with all nine blue regions connected."""
    result = []
    for turn, order in enumerate(((4, 1, 9, 3, 8, 2, 7, 5, 6), (2, 7, 5, 9, 3, 6, 1, 8, 4))):
        grid = [[0] * 11 for _ in range(11)]
        for index, count in enumerate(order):
            block = [[1 if 3 * r + c < count else 2 for c in range(3)] for r in range(3)]
            for _ in range((turn + index) % 4):
                block = [list(row) for row in zip(*block[::-1])]
            for r in range(3):
                for c in range(3):
                    grid[(index // 3) * 4 + r][(index % 3) * 4 + c] = block[r][c]
        result.append(grid)
    return result


def scene_facts(grid, settings):
    blocks = extract_blocks(grid)
    keys = [_key(block, settings, "reference") for block in blocks]
    counts = [sum(v == 1 for row in block for v in row) for block in blocks]
    groups = [component_count(block) for block in blocks]
    output = reference(grid, settings)
    rows, cols = geometry(grid)
    movement = learned_map({"input": grid, "output": output})
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
            "tile_size": len(blocks[0]), "active_cells": sum(v != 0 for row in grid for v in row),
            "color1_counts": counts, "component4_counts": groups,
            "component8_counts": [component_count(block, connectivity=8) for block in blocks],
            "rank_keys": keys, "unique_rank_keys": len(set(keys)),
            "tied_component_groups": {str(k): v for k, v in Counter(groups).items() if v > 1},
            "source_position_for_output": movement,
            "moved_blocks": sum(i != source for i, source in enumerate(movement)),
            "separator_row_widths": [rows[i + 1][0] - rows[i][-1] - 1 for i in range(2)],
            "separator_column_widths": [cols[i + 1][0] - cols[i][-1] - 1 for i in range(2)],
            "whole_block_multiset_preserved": sorted(map(packed, blocks)) == sorted(map(packed, extract_blocks(output)))}


def _load(path):
    name = "_blocksort_audit_" + sha(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_binding():
    paths = list(HOME.glob("*.py")) + list((TASK / "tests").glob("*.py")) + list(HOME.glob("*.rkt"))
    paths += [TASK / "generator.py", HOME / "promotion.json", ROOT / "shared/data/canonical/puzzles.jsonl",
              ROOT / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths)) if p.is_file()}


def before_witness(adapter, programs, engine):
    demos = ambiguous_demonstrations()
    teaching = adapter.generate(0, {"rank_basis": "components_then_cells"}, 2, 4)["train"]
    query = teaching[0]["input"]
    repair_input = teaching[1]["input"]
    if len({packed(grid) for grid in demos + [query, repair_input]}) != 4:
        raise AssertionError("Before-witness inputs and replacement demonstration must be distinct")
    outputs = {basis: [engine(program, grid) for grid in demos + [query]] for basis, program in programs.items()}
    if any(outputs["cells"][i] != outputs["components_then_cells"][i] for i in range(2)):
        raise AssertionError("Intended before-witness demonstrations do not fit both rules")
    if outputs["cells"][2] == outputs["components_then_cells"][2]:
        raise AssertionError("Before-witness query does not distinguish the rules")
    repair_outputs = {basis: engine(program, repair_input) for basis, program in programs.items()}
    repair_pair = {"input": repair_input, "output": repair_outputs["components_then_cells"]}
    survivors = [basis for basis in programs
                 if outputs[basis][0] == outputs["components_then_cells"][0]
                 and repair_outputs[basis] == repair_pair["output"]]
    if survivors != ["components_then_cells"]:
        raise AssertionError("Replacement demonstration does not identify the selected setting")
    repaired_train = [{"input": demos[0], "output": outputs["components_then_cells"][0]}, repair_pair]
    if any(pair["input"] == query for pair in repaired_train):
        raise AssertionError("The retained query must stay novel after demonstration repair")
    result = {
        "schema": "3108da8bf9e8-underidentified-prefix-witness-v1",
        "status": "reproduced_expected_ambiguity", "visibility": "controller_private",
        "training_admitted": False,
        "interpretation": "Both complete executable settings fit the two visible demonstrations; their predictions disagree on one lawful11x11 query. These are candidate alternatives, not multiple official gold answers. This subset is excluded from clean exports.",
        "train": [{"input": grid, "output": outputs["cells"][i]} for i, grid in enumerate(demos)],
        "query": {"input": query},
        "programs": {basis: {"source": program, "sha256": sha(program.encode())} for basis, program in programs.items()},
        "executed_outputs": outputs,
        "demo_survivors": list(programs),
        "query_difference_cells": sum(a != b for ra, rb in zip(outputs["cells"][2], outputs["components_then_cells"][2]) for a, b in zip(ra, rb)),
        "repair": {"action": "replace one weak demonstration with a distinct distinguishing example",
                   "replacement_demo_index": 1, "pair": repair_pair,
                   "replacement_demo_executed_outputs": repair_outputs,
                   "repaired_train": repaired_train, "demonstration_count": 2,
                   "remaining_declared_survivors": survivors,
                   "original_query_retained": True, "query_remains_novel": True,
                   "scope": "This counterexample repair establishes declared-setting identification only; the subset remains outside clean exports."},
    }
    return result


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    private.mkdir()
    report = {"schema": "3108da8bf9e8-native-finite-audit-v1", "status": "running",
              "visibility": "controller_private", "training_admitted": False,
              "source_files_sha256": source_binding(), "settings": deepcopy(SETTINGS),
              "jobs": [{"seed": seed, "demos": demos, "queries": 4} for seed, demos in JOBS],
              "extra_rivals": list(RIVALS), "programs": {}, "episodes": [],
              "findings": [], "first_two_prefix_findings": [],
              "limits": "Six episodes, two declared settings, sixteen extra executable rules including one fitted source-position map. Demonstration survivors are frozen before queries. No universal identifiability, owner acceptance or training admission. Default fixed11x11 geometry remains exact; larger grids belong only to the alternative grammar."}
    bridge, engine, phase = None, None, "setup"
    try:
        with _local_imports(RUNTIME, HOME):
            from arcpuzzles import Catalog
            adapter = _load(HOME / "adapter.py")
            apply, identity, bridge = _real_evaluator(RUNTIME)
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise ValueError("Protected Racket is required")
            report["racket"] = identity
            engine = CachedEvaluator(apply)
            programs = {s["rank_basis"]: adapter.program(deepcopy(s)) for s in SETTINGS}
            canonical = {v["program_solution"] for v in Catalog(ROOT).get(TASK_ID)["variants"] if isinstance(v.get("program_solution"), str)}
            if canonical != {programs["cells"]}:
                raise AssertionError("Native default differs from exact canonical source")
            def retain(program):
                identifier = sha(program.encode())
                report["programs"][identifier] = program
                return identifier
            phase = "deliberately_underidentified_before_witness"
            witness = before_witness(adapter, programs, engine)
            witness.update({"source_files_sha256": report["source_files_sha256"], "racket": identity})
            (private / "before-witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
            report["before_witness"] = {"path": "private/before-witness.json", "status": witness["status"],
                                        "query_difference_cells": witness["query_difference_cells"]}
            for seed, demos in JOBS:
                shared_train = None
                for settings in SETTINGS:
                    basis = settings["rank_basis"]
                    phase = f"generate:{seed}:{demos}:{basis}"
                    episode = adapter.generate(seed, deepcopy(settings), demos, 4)
                    if episode["program_solution"] != programs[basis]:
                        raise AssertionError("Episode does not retain its exact setting program")
                    pairs = {}
                    for split, count in (("train", demos), ("test", 4)):
                        if type(episode[split]) is not list or len(episode[split]) != count:
                            raise ValueError("Incorrect demonstration/query count")
                        pairs[split] = [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in episode[split]]
                    inputs = [p["input"] for p in pairs["train"] + pairs["test"]]
                    if len({packed(g) for g in inputs}) != len(inputs):
                        raise AssertionError("Episode inputs are not distinct")
                    train_inputs = [p["input"] for p in pairs["train"]]
                    if shared_train is not None and shared_train != train_inputs:
                        raise AssertionError("Demonstration draws differ across settings")
                    shared_train = train_inputs
                    phase = f"reference:{seed}:{demos}:{basis}"
                    for pair in pairs["train"] + pairs["test"]:
                        actual = engine(programs[basis], pair["input"])
                        if actual != pair["output"] or actual != reference(pair["input"], settings):
                            raise AssertionError("Claimed label or independent reference differs from Racket")
                    facts = [scene_facts(g, settings) for g in inputs]
                    fixed_map = learned_map(pairs["train"][0])
                    record = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                              "program_sha256": retain(programs[basis]), **pairs, "hypotheses": [],
                              "fixed_map_fitted_from_demo_index": 0, "learned_source_position_map": fixed_map,
                              "scene_facts": {"train": facts[:demos], "test": facts[demos:]}}
                    report["episodes"].append(record)
                    hypotheses = [("declared:" + s["rank_basis"], programs[s["rank_basis"]], s) for s in SETTINGS]
                    hypotheses += [(name, rival_program(settings, name, fixed_map=fixed_map), None) for name in RIVALS]
                    survivors = []
                    for name, program, declared in hypotheses:
                        phase = f"hypothesis:{seed}:{demos}:{basis}:{name}"
                        retain(program)
                        def execute(source, grid, name=name, declared=declared):
                            actual = engine(source, grid)
                            expected = reference(grid, declared) if declared is not None else rival_reference(grid, settings, name, fixed_map=fixed_map)
                            if actual != expected:
                                raise AssertionError("Racket hypothesis differs from independent meaning: " + name)
                            return actual
                        row = assess(name, program, pairs["train"], pairs["test"], execute)
                        record["hypotheses"].append(row)
                        if declared is not None and row["survives_demonstrations"]:
                            survivors.append(declared["rank_basis"])
                        finding = {"episode_index": len(report["episodes"]) - 1, "seed": seed,
                                   "settings": deepcopy(settings), "rival": name, "query_indices": row["query_disagreement_indices"]}
                        if row["survives_demonstrations"] and row["query_disagreement_indices"]:
                            report["findings"].append(dict(finding, kind="demo_survivor_query_disagreement"))
                        if row["survives_first_two"] and row["query_disagreement_indices"]:
                            report["first_two_prefix_findings"].append(dict(finding, kind="prefix_survivor_query_disagreement"))
                    record["declared_survivors"] = survivors
                    record["extra_survivors"] = [r["name"] for r in record["hypotheses"] if not r["name"].startswith("declared:") and r["survives_demonstrations"]]
                    if survivors != [basis]:
                        report["findings"].append({"kind": "declared_setting_not_identified", "episode_index": len(report["episodes"]) - 1})
                    stress = facts[-1]
                    stress_ok = (stress["input_shape"] == stress["output_shape"] == ([11, 11] if basis == "cells" else [30, 30])
                                 and stress["active_cells"] == (81 if basis == "cells" else 729)
                                 and stress["unique_rank_keys"] == 9 and stress["whole_block_multiset_preserved"]
                                 and (basis == "cells" or stress["separator_row_widths"] == stress["separator_column_widths"] == [1, 2]))
                    record["stress_check"] = {"passed": stress_ok,
                        "scope": "Exact11x11 canonical queries; alternate final query is30x30 with nine9x9blocks,729activecells,separatorwidths1and2,andnineuniqueranks."}
                    if not stress_ok:
                        report["findings"].append({"kind": "insufficient_boundary_stress", "episode_index": len(report["episodes"]) - 1, "facts": stress})
                    print(json.dumps({"seed": seed, "demos": demos, "rank_basis": basis,
                                      "racket_evaluations": engine.evaluations,
                                      "extra_survivors": record["extra_survivors"],
                                      "findings": len(report["findings"]),
                                      "prefix_findings": len(report["first_two_prefix_findings"])}), flush=True)
            if source_binding() != report["source_files_sha256"]:
                raise AssertionError("Source bytes changed during audit")
            report["reference_label_count"] = sum(demos + 4 for seed, demos in JOBS) * 2
            report["matched_demo_inputs_across_settings"] = True
            report["query_geometry_is_setting_dependent"] = True
            report["status"] = "failed" if report["findings"] or report["first_two_prefix_findings"] else "passed"
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error),
                                       "last_native_request": engine.last_request if engine else None}
    finally:
        if bridge is not None:
            bridge.close()
        if engine is not None:
            report["execution"] = {"requests": engine.requests, "racket_evaluations": engine.evaluations,
                "cache_hits": engine.cache_hits, "successful_cached_results": len(engine.cache),
                "cache_key": "exact complete program and exact validated grid"}
        target = private / "audit.json"
        target.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "report": str(target), "findings": len(report["findings"]),
                      "prefix_findings": len(report["first_two_prefix_findings"]),
                      "execution_failure": report.get("execution_failure")}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    result = run(parser.parse_args().out)
    raise SystemExit(0 if result["status"] == "passed" else 1)
