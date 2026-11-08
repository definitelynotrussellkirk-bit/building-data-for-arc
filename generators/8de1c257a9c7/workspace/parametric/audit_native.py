"""Independent, bounded audit of native stamp-transform episodes.

No family geometry, Python label helper, or finite template validator is used
to interpret inputs. Every declared rival has a complete protected Racket
program and an independently authored Python meaning. Demonstration fits are
frozen before queries are executed; exceptions never eliminate a hypothesis.
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


TASK_ID = "8de1c257a9c7"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SETTINGS = ("identity", "mirror_horizontal")
RIVAL_NAMES = (
    "historical_count_identity", "historical_count_mirror_horizontal",
    "first_red_only", "last_red_only", "fill_template_bbox",
    "fixed_cardinal_cross", "local_3x3_only", "preserve_input",
    "preserve_cyan_source", "cyan_at_markers_only", "xor_overlaps",
    "bbox_center_anchor", "bbox_topleft_anchor",
)

# Literal historical bank, deliberately independent of generator.py. Missing
# cardinalities produce the empty output, making both lookup rivals total.
COUNT_OFFSETS = {
    4: ((-1, 0), (0, -1), (0, 1), (1, 0)),
    6: ((-2, 0), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 2)),
    8: ((-2, -1), (-1, -1), (-1, 0), (0, -1), (1, -1), (1, 0), (1, 1), (2, 1)),
    9: ((-2, -1), (-2, 1), (-1, -2), (-1, -1), (-1, 1), (-1, 2), (0, -1), (0, 1), (1, 0)),
    10: ((-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 0), (1, 1), (2, 0)),
    14: ((-3, 0), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
         (-1, -2), (-1, -1), (-1, 1), (-1, 2), (0, -2), (0, -1), (0, 1), (0, 2)),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _setting(settings):
    if settings is None or settings == {}:
        return "identity"
    if (type(settings) is not dict or set(settings) != {"stamp_transform"}
            or type(settings["stamp_transform"]) is not str
            or settings["stamp_transform"] not in SETTINGS):
        raise ValueError("settings require the single bounded stamp_transform parameter")
    return settings["stamp_transform"]


def _strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors")
    return grid


def facts(grid):
    """Extract independent geometry and enforce the shared native grammar."""
    _strict_grid(grid)
    h, w = len(grid), len(grid[0])
    if min(h, w) < 8:
        raise ValueError("native canvas dimensions must be in 8..30")
    if any(cell not in {0, 2, 3, 8} for row in grid for cell in row):
        raise ValueError("native inputs allow only colors 0, 2, 3, 8")
    positions = {color: [(r, c) for r, row in enumerate(grid)
                         for c, cell in enumerate(row) if cell == color]
                 for color in (2, 3, 8)}
    if len(positions[3]) != 1 or not positions[8] or not positions[2]:
        raise ValueError("one green, nonempty cyan source, and red destinations are required")
    green = positions[3][0]
    source = {green, *positions[8]}
    reached, queue = {green}, [green]
    while queue:
        r, c = queue.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                cell = (r + dr, c + dc)
                if cell in source and cell not in reached:
                    reached.add(cell)
                    queue.append(cell)
    if reached != source:
        raise ValueError("green plus cyan must be 8-connected")
    offsets = tuple((r - green[0], c - green[1]) for r, c in positions[8])
    for rr, rc in positions[2]:
        for dr, dc in offsets:
            if not (0 <= rr + dr < h and 0 <= rc + dc < w and 0 <= rc - dc < w):
                raise ValueError("every complete stamp must fit under both settings")
    return {"h": h, "w": w, "height": h, "width": w, "green": green,
            "reds": tuple(positions[2]), "cyans": tuple(positions[8]),
            "offsets": offsets, "shape_offsets": offsets, "cyan_count": len(offsets),
            "bbox": (min(r for r, _ in positions[8]), min(c for _, c in positions[8]),
                     max(r for r, _ in positions[8]), max(c for _, c in positions[8]))}


def self_check(grid):
    try:
        facts(grid)
        return []
    except (ValueError, TypeError) as error:
        return [str(error)]


def _transformed(offsets, setting):
    return [(dr, -dc if setting == "mirror_horizontal" else dc) for dr, dc in offsets]


def _paint(grid, centers, offsets, *, keep=None, xor=False):
    h, w = len(grid), len(grid[0])
    output = deepcopy(keep) if keep is not None else [[0] * w for _ in range(h)]
    counts = Counter((rr + dr, rc + dc) for rr, rc in centers for dr, dc in offsets
                     if 0 <= rr + dr < h and 0 <= rc + dc < w)
    for (r, c), count in counts.items():
        if not xor or count % 2:
            output[r][c] = 8
    return output


def reference(grid, settings):
    f = facts(grid)
    return _paint(grid, f["reds"], _transformed(f["offsets"], _setting(settings)))


def rival_output(name, grid, settings):
    """Total wrong-rule meanings, independent of the family's Python helpers."""
    if name not in RIVAL_NAMES:
        raise ValueError("unknown rival: " + str(name))
    f, setting = facts(grid), _setting(settings)
    centers = f["reds"]
    offsets = _transformed(f["offsets"], setting)
    keep = None
    if name.startswith("historical_count_"):
        orientation = name.removeprefix("historical_count_")
        offsets = _transformed(COUNT_OFFSETS.get(f["cyan_count"], ()), orientation)
    elif name == "first_red_only":
        centers = centers[:1]
    elif name == "last_red_only":
        centers = centers[-1:]
    elif name == "fill_template_bbox":
        offsets = [(r, c) for r in range(min(r for r, _ in offsets), max(r for r, _ in offsets) + 1)
                   for c in range(min(c for _, c in offsets), max(c for _, c in offsets) + 1)]
    elif name == "fixed_cardinal_cross":
        offsets = COUNT_OFFSETS[4]
    elif name == "local_3x3_only":
        offsets = [(r, c) for r, c in offsets if abs(r) <= 1 and abs(c) <= 1]
    elif name == "preserve_input":
        keep = grid
    elif name == "preserve_cyan_source":
        keep = [[8 if cell == 8 else 0 for cell in row] for row in grid]
    elif name == "cyan_at_markers_only":
        offsets = [(0, 0)]
    elif name in {"bbox_center_anchor", "bbox_topleft_anchor"}:
        r0, c0, r1, c1 = f["bbox"]
        anchor = ((r0 + r1) // 2, (c0 + c1) // 2) if name == "bbox_center_anchor" else (r0, c0)
        offsets = _transformed([(r - anchor[0], c - anchor[1]) for r, c in f["cyans"]], setting)
    return _paint(grid, centers, offsets, keep=keep, xor=name == "xor_overlaps")


def reference_program(settings):
    """Read selected authority, independently specialize its single offset step."""
    from arcpuzzles import Catalog
    programs = {row["program_solution"] for row in Catalog(ROOT).get(TASK_ID)["variants"]
                if isinstance(row.get("program_solution"), str)}
    if len(programs) != 1:
        raise ValueError("one exact selected canonical program is required")
    source = next(iter(programs))
    if _setting(settings) == "identity":
        return source
    old = "(list (- (first p) gr) (- (second p) gc))"
    if source.count(old) != 1:
        raise ValueError("canonical horizontal-offset specialization point differs")
    return source.replace(old, "(list (- (first p) gr) (- gc (second p)))")


def _literal_offsets(offsets):
    return "'(" + " ".join(f"({r} {c})" for r, c in offsets) + ")"


def rival_program(name, settings):
    """Return a self-contained protected Racket program for one named shortcut."""
    if name not in RIVAL_NAMES:
        raise ValueError("unknown rival: " + str(name))
    setting = _setting(settings)
    dc = "(- ac (second p))" if setting == "mirror_horizontal" else "(- (second p) ac)"
    anchors = "(ar (first (first (find-color g 3)))) (ac (second (first (find-color g 3))))"
    if name == "bbox_center_anchor":
        anchors = "(ar (quotient (+ (apply min (map first cyans)) (apply max (map first cyans))) 2)) (ac (quotient (+ (apply min (map second cyans)) (apply max (map second cyans))) 2))"
    elif name == "bbox_topleft_anchor":
        anchors = "(ar (apply min (map first cyans))) (ac (apply min (map second cyans)))"
    raw_offsets = f"(map (lambda (p) (list (- (first p) ar) {dc})) cyans)"
    if name.startswith("historical_count_"):
        orientation = name.removeprefix("historical_count_")
        anchors = ""
        raw_offsets = "(cond " + " ".join(
            f"((= (length cyans) {count}) {_literal_offsets(_transformed(offsets, orientation))})"
            for count, offsets in COUNT_OFFSETS.items()) + " (else '()))"
    elif name == "fixed_cardinal_cross":
        anchors, raw_offsets = "", _literal_offsets(COUNT_OFFSETS[4])
    elif name == "cyan_at_markers_only":
        anchors, raw_offsets = "", "'((0 0))"
    offsets = "raw-offsets"
    if name == "local_3x3_only":
        offsets = "(filter (lambda (p) (and (<= (abs (first p)) 1) (<= (abs (second p)) 1))) raw-offsets)"
    elif name == "fill_template_bbox":
        offsets = "(apply append (map (lambda (r) (map (lambda (c) (list r c)) (range (apply min (map second raw-offsets)) (+ 1 (apply max (map second raw-offsets)))))) (range (apply min (map first raw-offsets)) (+ 1 (apply max (map first raw-offsets))))))"
    centers = "reds"
    if name == "first_red_only":
        centers = "(list (first reds))"
    elif name == "last_red_only":
        centers = "(list (last reds))"
    initial = "(cellmap g (r c v) 0)"
    if name == "preserve_input":
        initial = "g"
    elif name == "preserve_cyan_source":
        initial = "(cellmap g (r c v) (if (= v 8) 8 0))"
    color = "(if (= (cell-at gx nr nc) 8) 0 8)" if name == "xor_overlaps" else "8"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (reds (find-color g 2)) (cyans (find-color g 8))
         {anchors}
         (raw-offsets {raw_offsets}) (offsets {offsets})
         (centers {centers}) (initial {initial}))
    (reduce (lambda (gg red)
      (reduce (lambda (gx off)
        (let ((nr (+ (first red) (first off)))
              (nc (+ (second red) (second off))))
          (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
              (set-cell gx nr nc {color}) gx))) gg offsets))
      initial centers))))"""


class CachedEvaluator:
    """Same-checkout live protected evaluator with exact program/input caching."""

    def __init__(self, root=ROOT):
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        self.root = Path(root).resolve()
        self._imports = _local_imports(self.root / "shared/runtime", HERE)
        self._imports.__enter__()
        try:
            self._apply, self.identity, self._bridge = _real_evaluator(self.root / "shared/runtime")
        except Exception:
            self._imports.__exit__(*sys.exc_info())
            raise
        self._cache = {}
        self.records = []
        self.evaluations = 0
        self.cache_hits = 0
        self.closed = False

    def execute(self, program, grid):
        if self.closed:
            raise RuntimeError("evaluator is closed")
        _strict_grid(grid)
        key = (hashlib.sha256(program.encode()).hexdigest(), digest(grid))
        if key in self._cache:
            self.cache_hits += 1
            return deepcopy(self._cache[key])
        output = _strict_grid(self._apply(program, deepcopy(grid)))
        self.evaluations += 1
        self._cache[key] = deepcopy(output)
        self.records.append({"program_sha256": key[0], "input_sha256": key[1],
                             "output_sha256": digest(output)})
        return deepcopy(output)

    __call__ = execute

    def close(self):
        if not self.closed:
            self._bridge.close()
            self._imports.__exit__(None, None, None)
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def _candidate_programs(settings):
    return {**{"setting:" + value: reference_program({"stamp_transform": value}) for value in SETTINGS},
            **{name: rival_program(name, settings) for name in RIVAL_NAMES}}


def _candidate_meaning(name, grid, settings):
    if name.startswith("setting:"):
        return reference(grid, {"stamp_transform": name.removeprefix("setting:")})
    return rival_output(name, grid, settings)


def fit_demonstrations(train, settings, evaluator):
    """Fit the complete finite hypothesis set on demonstrations only."""
    if not isinstance(train, list) or not train:
        raise ValueError("at least one demonstration is required")
    chosen = _setting(settings)
    for pair in train:
        if _strict_grid(pair["output"]) != reference(pair["input"], settings):
            raise ValueError("demonstration claim differs from independent intended semantics")
    hypotheses = []
    for name, program in _candidate_programs(settings).items():
        refuting, differences = [], []
        for index, pair in enumerate(train):
            observed = evaluator.execute(program, pair["input"])
            expected = _candidate_meaning(name, pair["input"], settings)
            if observed != expected:
                raise ValueError(f"Racket/Python rival parity failed: {name} demonstration {index}")
            cells = sum(a != b for ra, rb in zip(observed, pair["output"], strict=True)
                        for a, b in zip(ra, rb, strict=True))
            if cells:
                refuting.append(index)
                differences.append(cells)
        hypotheses.append({"name": name, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                           "refuting_demo_indices": refuting, "different_cells": differences})
    survivors = [row["name"] for row in hypotheses if not row["refuting_demo_indices"]]
    return {"schema": "stamp-transform-demo-only-certificate-v1", "selected": chosen,
            "demo_count": len(train), "demonstrations_sha256": digest(train),
            "hypotheses": hypotheses, "survivors": survivors,
            "identifiable": survivors == ["setting:" + chosen],
            "fit_scope": "demonstrations only; queries not consulted"}


def pair_features(grid, settings):
    f, selected = facts(grid), _setting(settings)
    offsets = _transformed(f["offsets"], selected)
    coverage = Counter((rr + dr, rc + dc) for rr, rc in f["reds"] for dr, dc in offsets)
    output_cells = set(coverage)
    r0, c0, r1, c1 = f["bbox"]
    return {"height": f["h"], "width": f["w"], "cyan_count": f["cyan_count"],
            "red_count": len(f["reds"]), "source_bbox": list(f["bbox"]),
            "outside_local_3x3": any(abs(r) > 1 or abs(c) > 1 for r, c in offsets),
            "even_overlap_cells": sum(count % 2 == 0 for count in coverage.values()),
            "source_cells_cleared": len(set(f["cyans"]) - output_cells),
            "green_not_bbox_center": f["green"] != ((r0 + r1) // 2, (c0 + c1) // 2),
            "green_not_bbox_topleft": f["green"] != (r0, c0),
            "output_cyan_count": len(output_cells),
            "output_bbox": [min(r for r, _ in output_cells), min(c for _, c in output_cells),
                            max(r for r, _ in output_cells), max(c for _, c in output_cells)],
            "output_boundary_cells": sum(r in {0, f["h"] - 1} or c in {0, f["w"] - 1}
                                         for r, c in output_cells)}


def paired_count_witness(train):
    if len(train) < 2:
        raise ValueError("paired count witness needs two demonstrations")
    left, right = facts(train[0]["input"]), facts(train[1]["input"])
    matched = all(left[key] == right[key] for key in ("h", "w", "green", "reds", "cyan_count"))
    changed = {}
    for value in SETTINGS:
        setting = {"stamp_transform": value}
        changed[value] = reference(train[0]["input"], setting) != reference(train[1]["input"], setting)
    if not matched or left["offsets"] == right["offsets"] or not all(changed.values()):
        raise ValueError("first demonstrations do not refute geometry-blind cardinality lookup")
    return {"matched_dimensions_green_reds_cyan_count": True,
            "distinct_offsets": True, "different_outputs_by_setting": changed,
            "inputs_sha256": [digest(pair["input"]) for pair in train[:2]],
            "conclusion": "Any deterministic rule using only these matched features gives the same answer to both inputs and must fail one demonstration."}


def audit_episode(episode, settings, evaluator):
    selected = _setting(settings)
    certificate = fit_demonstrations(episode["train"], settings, evaluator)
    if not certificate["identifiable"]:
        raise ValueError("demonstrations retain rival hypotheses: " + repr(certificate["survivors"]))
    frozen = deepcopy(certificate)
    frozen_hash = digest(frozen)
    count_witness = paired_count_witness(episode["train"])
    features = {"train": [pair_features(pair["input"], settings) for pair in episode["train"]],
                "test": []}
    for feature in features["train"][:2]:
        if not (feature["outside_local_3x3"] and feature["even_overlap_cells"]
                and feature["source_cells_cleared"] and feature["green_not_bbox_center"]
                and feature["green_not_bbox_topleft"]):
            raise ValueError("first demonstrations omit an intended shortcut intervention")
    programs = _candidate_programs(settings)
    query_checks = []
    for index, pair in enumerate(episode["test"]):
        if _strict_grid(pair["output"]) != reference(pair["input"], settings):
            raise ValueError("query claim differs from independent intended semantics")
        # Totality/parity on queries is downstream of the frozen teaching fit.
        # These outputs never amend the surviving-hypothesis set.
        outputs = {}
        for name, program in programs.items():
            output = evaluator.execute(program, pair["input"])
            if output != _candidate_meaning(name, pair["input"], settings):
                raise ValueError(f"Racket/Python rival parity failed: {name} query {index}")
            outputs[name] = digest(output)
        if outputs["setting:" + selected] != digest(pair["output"]):
            raise ValueError("selected Racket query label differs")
        features["test"].append(pair_features(pair["input"], settings))
        query_checks.append({"query_index": index, "input_sha256": digest(pair["input"]),
                             "output_sha256": digest(pair["output"]), "hypothesis_outputs": outputs})
    if digest(certificate) != frozen_hash:
        raise ValueError("query execution altered the demonstration certificate")
    return {"settings": {"stamp_transform": selected}, "certificate": frozen,
            "certificate_sha256_before_queries": frozen_hash,
            "certificate_sha256_after_queries": digest(certificate),
            "paired_count_witness": count_witness, "features": features, "queries": query_checks}


def source_files(root=ROOT):
    """Small source inventory for this independent audit and its same-task inputs."""
    root = Path(root).resolve()
    paths = [root / f"generators/{TASK_ID}/generator.py",
             root / f"generators/{TASK_ID}/tests/test_native_audit_{TASK_ID}.py"]
    paths.extend(path for path in HERE.iterdir() if path.is_file() and path.suffix in {".py", ".rkt", ".json"})
    paths.extend(root / "src/arcpuzzles" / name for name in
                 ("parametric_worker.py", "parametric_promotion.py", "catalog.py", "runtime.py"))
    return [{"path": path.relative_to(root).as_posix(),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(set(paths)) if path.is_file()]


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_stamp_native_audit_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def screen(adapter=None):
    """Cheap deterministic Python screen; it does not claim Racket execution."""
    adapter = _load_adapter() if adapter is None else adapter
    checked, signatures = 0, set()
    for seed in (0, 17, 101):
        matched = None
        for value in SETTINGS:
            settings = {"stamp_transform": value}
            episode = adapter.generate(seed, settings, 2, 4)
            inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
            if matched is not None and inputs != matched:
                raise ValueError("native settings alter matched inputs")
            matched = inputs
            if len({digest(grid) for grid in inputs}) != len(inputs):
                raise ValueError("native episode contains duplicate inputs")
            paired_count_witness(episode["train"])
            for name in RIVAL_NAMES:
                if all(rival_output(name, pair["input"], settings) == pair["output"] for pair in episode["train"]):
                    raise ValueError(f"Python minimum-demo screen retains {name}: seed={seed} setting={value}")
            for split in ("train", "test"):
                for pair in episode[split]:
                    grid = pair["input"]
                    signatures.add(tuple(facts(grid)["offsets"]))
                    if _strict_grid(pair["output"]) != reference(grid, settings):
                        raise ValueError("Python screen claim differs from independent intended semantics")
            checked += 1
    return {"episodes": checked, "demos": 2, "queries": 4,
            "distinct_source_geometries": len(signatures), "backend": "independent_python_screen"}


def run_audit(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    adapter = _load_adapter()
    before = source_files()
    preliminary = screen(adapter)
    episodes, results = [], []
    with CachedEvaluator() as evaluator:
        for seed, demos in ((0, 2), (17, 2), (101, 6)):
            matched = None
            for value in SETTINGS:
                settings = {"stamp_transform": value}
                episode = adapter.generate(seed, settings, demos, 4)
                inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                if matched is not None and inputs != matched:
                    raise ValueError("native settings alter matched episode inputs")
                matched = inputs
                if episode["program_solution"] != reference_program(settings):
                    raise ValueError("adapter program differs from independently read setting authority")
                result = audit_episode(episode, settings, evaluator)
                result.update(seed=seed, demos=demos, queries=4)
                results.append(result)
                episodes.append({"seed": seed, "settings": settings, **episode})
        report = {"schema": "stamp-transform-native-independent-audit-v1", "task_id": TASK_ID,
                  "status": "passed", "episodes": results, "episode_count": len(results),
                  "extra_rivals": list(RIVAL_NAMES), "declared_settings": list(SETTINGS),
                  "preliminary_screen": preliminary, "runtime": evaluator.identity,
                  "racket_evaluations": evaluator.evaluations, "cache_hits": evaluator.cache_hits,
                  "source_files": before, "training_admitted": False,
                  "limitations": "Six authored episodes and 13 explicit shortcut programs plus both settings; no arbitrary-program uniqueness, learner-performance measurement, production-audit resolution, or owner acceptance."}
        executions = deepcopy(evaluator.records)
    if source_files() != before:
        raise ValueError("audit source inputs changed during execution")
    out.mkdir(parents=True, exist_ok=False)
    programs = {value: _candidate_programs({"stamp_transform": value}) for value in SETTINGS}
    for name, data in (("report.json", report), ("episodes.private.json", episodes),
                       ("executions.json", executions), ("programs.private.json", programs)):
        (out / name).write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--screen-only", action="store_true")
    args = parser.parse_args(argv)
    if args.screen_only:
        print(json.dumps(screen(), sort_keys=True))
    else:
        if args.out is None:
            parser.error("--out is required unless --screen-only")
        report = run_audit(args.out)
        print(json.dumps({key: report[key] for key in
                          ("status", "episode_count", "racket_evaluations", "cache_hits", "limitations")},
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
