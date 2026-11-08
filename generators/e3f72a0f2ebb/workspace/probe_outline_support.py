#!/usr/bin/env python3
"""Bounded, source-bound support measurements for e3f72a0f2ebb.

This authoring probe reads labeled canonical data. It must not be used during a
visible-only solve. Generated outputs below are independently computed Python
predictions; --racket-witnesses additionally labels at most 64 exact inputs with
the public Catalog.apply API. Large lesson/rotation scoring belongs to the
shared ``arcpuzzles lesson-census`` command.

The default population is the direct generate(seed, index, difficulty=band)
population, before production rejection or duplicate filtering. Joint overrides
exhaust the four advertised integer domains at the requested seeds and indices.
Every failure is retained. Successful cases contribute to counts and a digest;
only their first feature witnesses retain complete grids.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
import time
import traceback
import types


TASK_ID = "e3f72a0f2ebb"
RULE_HASH = "8d3a7f6a327b"
AXIS_NAMES = ("grid_h", "grid_w", "n_blobs", "n_distinct_colors")
BANDS = ("easy", "medium", "hard")


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_new_json(path, value):
    """Publish a complete report atomically, refusing even a racing existing file."""
    path = Path(path).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        # Unlike replace(), link() cannot overwrite a concurrently created report.
        os.link(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def normalize_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty list/tuple grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        raise ValueError("grid colors must be Python integers in 0..9")
    return [list(row) for row in grid]


def analyze(grid):
    """Independent 4-connected same-color components and tight frame geometry."""
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    components = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        frontier, cells = [start], {start}
        unseen.remove(start)
        while frontier:
            row, col = frontier.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    frontier.append(neighbor)
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        frame = ({(top, c) for c in range(left, right + 1)}
                 | {(bottom, c) for c in range(left, right + 1)}
                 | {(r, left) for r in range(top, bottom + 1)}
                 | {(r, right) for r in range(top, bottom + 1)})
        added, removed = frame - cells, cells - frame
        if len(cells) == 1:
            kind = "singleton"
        elif top == bottom or left == right:
            kind = "line"
        elif cells == frame:
            kind = "complete_frame"
        elif added and removed:
            kind = "add_and_delete"
        elif added:
            kind = "add_only"
        else:
            kind = "delete_only"
        components.append({"color": color, "cells": cells, "frame": frame,
                           "bbox": (top, left, bottom, right), "added": added,
                           "removed": removed, "kind": kind,
                           "shape": digest(sorted((r - top, c - left) for r, c in cells))})
    output = [[0] * width for _ in range(height)]
    owners = {}
    for index, component in enumerate(components):
        for point in component["frame"]:
            owners.setdefault(point, []).append(index)
            output[point[0]][point[1]] = component["color"]
    intersections = {point: indices for point, indices in owners.items() if len(indices) > 1}
    cross_color = sum(len({components[i]["color"] for i in indices}) > 1
                      for indices in intersections.values())
    other_input = sum(any(point in other["cells"]
                          for j, other in enumerate(components) if i != j)
                      for i, component in enumerate(components) for point in component["frame"])
    bbox_overlaps, bbox_touches = 0, 0
    for one, two in itertools.combinations(components, 2):
        a, b, c, d = one["bbox"]
        e, f, g, h = two["bbox"]
        bbox_overlaps += not (c < e or g < a or d < f or h < b)
        bbox_touches += not (c + 1 < e or g + 1 < a or d + 1 < f or h + 1 < b)
    colors = Counter(component["color"] for component in components)
    added_pixels = sum(grid[r][c] == 0 and output[r][c] != 0
                       for r in range(height) for c in range(width))
    removed_pixels = sum(grid[r][c] != 0 and output[r][c] == 0
                         for r in range(height) for c in range(width))
    recolored_pixels = sum(grid[r][c] != 0 and output[r][c] not in (0, grid[r][c])
                           for r in range(height) for c in range(width))
    features = {
        "repeated_color": any(count > 1 for count in colors.values()),
        "identity_component": any(not c["added"] and not c["removed"] for c in components),
        "singleton": any(c["kind"] == "singleton" for c in components),
        "line": any(c["kind"] == "line" for c in components),
        "complete_frame": any(c["kind"] == "complete_frame" for c in components),
        "requires_additions": any(c["added"] for c in components),
        "requires_interior_deletions": any(c["removed"] for c in components),
        "component_requires_both": any(c["added"] and c["removed"] for c in components),
        "frame_intersection": bool(intersections),
        "cross_color_frame_intersection": bool(cross_color),
        "frame_on_other_input": bool(other_input),
        "bbox_overlap": bool(bbox_overlaps),
        "bbox_without_blank_separator": bool(bbox_touches),
    }
    return {"input": grid, "independent_output": output, "components": components,
            "observed": dict(zip(AXIS_NAMES, (height, width, len(components), len(colors)))),
            "colors": sorted(colors), "features": features,
            "pixel_counts": {"input_nonzero": sum(len(c["cells"]) for c in components),
                             "frame_additions_by_component": sum(len(c["added"]) for c in components),
                             "interior_deletions_by_component": sum(len(c["removed"]) for c in components),
                             "actual_additions": added_pixels, "actual_deletions": removed_pixels,
                             "actual_recolorings": recolored_pixels,
                             "frame_intersection_cells": len(intersections),
                             "cross_color_frame_intersection_cells": cross_color,
                             "frame_on_other_input_pairs": other_input,
                             "bbox_overlap_pairs": bbox_overlaps,
                             "bbox_without_blank_separator_pairs": bbox_touches}}


def compact_analysis(result):
    return {key: result[key] for key in ("observed", "colors", "features", "pixel_counts")}


def profile_keys(result):
    """Keep exact color identities distinct from the shared palette-count profile."""
    height, width = result["observed"]["grid_h"], result["observed"]["grid_w"]
    palette_count = len(result["colors"]) + int(any(0 in row for row in result["input"]))
    return (height, width, tuple(result["colors"])), (height, width, palette_count)


def load_environment():
    """Find public helpers in this same tree, then ask find_root to bind its data."""
    here = Path(__file__).resolve()
    helper_path = None
    for ancestor in here.parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            candidate = ancestor / relative
            if candidate.is_file():
                helper_path = candidate
                break
        if helper_path:
            break
    if helper_path is None:
        raise FileNotFoundError("No local reviewer_support.py ancestor; use a complete library/runtime")
    sys.path.insert(0, str(helper_path.parent))
    from reviewer_support import canonical_pairs, canonical_path, find_root
    root = find_root(here)
    for relative in ("shared/runtime", "src"):
        if (root / relative).is_dir():
            sys.path.insert(0, str(root / relative))
    adjacent = here.parent.parent / "generator.py"
    candidates = [adjacent, root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"]
    generator_path = next((p for p in candidates if p.is_file() and p.parent.name == TASK_ID), None)
    if generator_path is None:
        raise FileNotFoundError(f"No selected {TASK_ID} generator inside {root}")
    if not generator_path.resolve().is_relative_to(root):
        raise ValueError("Selected generator escaped the local library/runtime")
    source = generator_path.read_bytes()
    module = types.ModuleType("_outline_support_selected_generator")
    module.__file__ = str(generator_path)
    sys.modules[module.__name__] = module
    # Compile these exact recorded bytes; a stale .pyc cannot select other code.
    exec(compile(source, str(generator_path), "exec"), module.__dict__)
    return root, module, canonical_pairs, canonical_path, helper_path


class Statistics:
    def __init__(self):
        self.count = 0
        self.inputs, self.outputs = set(), set()
        self.histograms = {key: Counter() for key in AXIS_NAMES}
        self.features, self.pixels = Counter(), Counter()
        self.color_presence, self.palettes = Counter(), Counter()
        self.shape_kinds, self.shapes = Counter(), Counter()
        self.residues = {}

    def add(self, result, index=None, period=None):
        self.count += 1
        self.inputs.add(digest(result["input"]))
        self.outputs.add(digest(result["independent_output"]))
        for name, value in result["observed"].items():
            self.histograms[name][value] += 1
        self.features.update(name for name, value in result["features"].items() if value)
        self.pixels.update(result["pixel_counts"])
        self.color_presence.update(result["colors"])
        self.palettes[",".join(map(str, result["colors"]))] += 1
        self.shape_kinds.update(c["kind"] for c in result["components"])
        self.shapes.update(c["shape"] for c in result["components"])
        if period is not None and index is not None:
            residue = self.residues.setdefault(index % period, {"draws": 0, "features": Counter()})
            residue["draws"] += 1
            residue["features"].update(name for name, value in result["features"].items() if value)

    def report(self):
        return {"analyzed": self.count, "unique_inputs": len(self.inputs),
                "unique_inputs_sha256": digest(sorted(self.inputs)),
                "unique_independent_outputs": len(self.outputs),
                "histograms": self.histograms, "instances_with": self.features,
                "pixel_totals": self.pixels, "color_presence": self.color_presence,
                "palette_counts": self.palettes, "component_kind_counts": self.shape_kinds,
                "unique_translation_normalized_shapes": len(self.shapes),
                "all_shape_counts_sha256": digest(self.shapes),
                "most_frequent_shape_hashes": self.shapes.most_common(24),
                "index_residues": self.residues}


class Witnesses:
    """First exact witnesses for measured categories, capped independently of failures."""
    def __init__(self, limit=64):
        self.limit, self.rows, self.reasons = limit, {}, set()

    def add(self, result, replay, reasons):
        fresh = set(reasons) - self.reasons
        if not fresh:
            return
        key = digest(result["input"])
        if key not in self.rows and len(self.rows) >= self.limit:
            return
        self.reasons.update(fresh)
        if key not in self.rows:
            self.rows[key] = {"input_sha256": key, "input": result["input"],
                              "independent_output": result["independent_output"],
                              "independent_output_sha256": digest(result["independent_output"]),
                              "analysis": compact_analysis(result), "replay": replay, "reasons": []}
        self.rows[key]["reasons"] = sorted(set(self.rows[key]["reasons"]) | fresh)


def failure(report, kind, replay=None, result=None, **detail):
    row = {"kind": kind, **detail}
    if replay is not None:
        row["replay"] = replay
    if result is not None:
        row.update(input=result["input"], input_sha256=digest(result["input"]),
                   independent_output=result["independent_output"], analysis=compact_analysis(result))
    report["failures"].append(row)


def error(report, kind, replay=None, result=None, exc=None, **detail):
    row = {"kind": kind, **detail}
    if replay is not None:
        row["replay"] = replay
    if result is not None:
        row.update(input=result["input"], input_sha256=digest(result["input"]))
    if exc is not None:
        row["exception"] = f"{type(exc).__name__}: {exc}"
        if hasattr(exc, "run"):
            row["process_receipt"] = exc.run
    report["errors"].append(row)


def check_functions(module, result, band, report, replay, *, overrides=None, canonical=False):
    fn = getattr(module, "self_check", None)
    if callable(fn):
        inp = deepcopy(result["input"])
        try:
            reasons = fn(inp, difficulty=band)
            if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
                raise TypeError("self_check must return a list of strings")
            if inp != result["input"]:
                raise ValueError("self_check mutated its input")
            if reasons:
                failure(report, "canonical_rejected" if canonical else "generated_rejected",
                        replay, result, reasons=reasons)
        except Exception as exc:
            error(report, "self_check_error", replay, result, exc)
    observed_fn = getattr(module, "observe_overrides", None)
    if callable(observed_fn):
        inp = deepcopy(result["input"])
        try:
            observed = observed_fn(inp)
            if not isinstance(observed, dict):
                raise TypeError("observe_overrides must return a dict")
            if inp != result["input"]:
                raise ValueError("observe_overrides mutated its input")
            mismatches = {name: {"independent": value, "hook": repr(observed.get(name))}
                          for name, value in result["observed"].items()
                          if type(observed.get(name)) is not int or observed[name] != value}
            if mismatches:
                failure(report, "observer_mismatch", replay, result, mismatches=mismatches)
        except Exception as exc:
            error(report, "observer_error", replay, result, exc)
    if overrides:
        mismatches = {name: {"requested": value, "observed": result["observed"][name]}
                      for name, value in overrides.items() if result["observed"][name] != value}
        if mismatches:
            failure(report, "override_mismatch", replay, result, mismatches=mismatches)


def check_generated_domain(result, report, replay):
    reasons = []
    if not 2 <= result["observed"]["n_blobs"] <= 4:
        reasons.append("direct normal draws must contain 2..4 components")
    if not result["features"]["component_requires_both"]:
        reasons.append("no component requires both frame additions and interior deletion")
    for name in ("frame_intersection", "frame_on_other_input", "bbox_without_blank_separator"):
        if result["features"][name]:
            reasons.append(name)
    if reasons:
        failure(report, "generated_domain", replay, result, reasons=reasons)


def load_rivals(module, report):
    rivals = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        raw = getattr(module, namespace, None)
        if not isinstance(raw, dict) or not raw:
            failure(report, "missing_or_invalid_rival_declaration", namespace=namespace,
                    declaration=repr(raw))
            continue
        for name, fn in raw.items():
            key = f"{namespace}:{name}"
            if not isinstance(name, str) or not name or not callable(fn):
                error(report, "invalid_rival_declaration", namespace=namespace, name=repr(name))
                continue
            rivals[key] = fn
            report["rivals"][key] = {"namespace": namespace, "name": name,
                                      "canonical": Counter(), "generated_by_band": {},
                                      "first_refutation": None}
    return rivals


def score_rivals(rivals, report, result, target, replay, witnesses, *, canonical=False):
    for key, fn in rivals.items():
        row = report["rivals"][key]
        counts = (row["canonical"] if canonical else
                  row["generated_by_band"].setdefault(replay["difficulty"], Counter()))
        inp = deepcopy(result["input"])
        try:
            prediction = normalize_grid(fn(inp))
            if inp != result["input"]:
                raise ValueError("rival mutated its input")
            if len(prediction) != len(target) or len(prediction[0]) != len(target[0]):
                raise ValueError("rival changed the output dimensions")
            equal = prediction == target
            counts["agrees" if equal else "refuted"] += 1
            if not equal:
                if row["first_refutation"] is None:
                    row["first_refutation"] = {"replay": replay, "input": result["input"],
                                               "input_sha256": digest(result["input"]),
                                               "expected_output": target, "rival_output": prediction,
                                               "label_basis": "canonical" if canonical else "independent_python"}
                witnesses.add(result, replay, [f"refutes:{key}"])
                if canonical and row["namespace"] == "CANONICAL_SHORTCUTS":
                    failure(report, "claimed_canonical_shortcut_refuted", replay, result,
                            rival=key, canonical_output=target, rival_output=prediction)
        except Exception as exc:
            counts["errors"] += 1
            error(report, "rival_error", replay, result, exc, rival=key)


def parse_domains(module):
    axes = getattr(module, "AXES", None)
    if not isinstance(axes, dict):
        raise ValueError("AXES must declare the four exact integer controls")
    domains = {}
    for name in AXIS_NAMES:
        declaration = axes.get(name)
        if not isinstance(declaration, dict) or declaration.get("type") != "int":
            raise ValueError(f"missing integer AXES[{name!r}]")
        valid = declaration.get("valid")
        match = re.fullmatch(r"\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*", str(valid))
        if match:
            low, high = map(int, match.groups())
            values = list(range(low, high + 1))
        elif isinstance(valid, str) and re.fullmatch(r"\d+(?:\|\d+)*", valid):
            values = sorted(set(map(int, valid.split("|"))))
        else:
            raise ValueError(f"unrecognized exact integer domain {name}={valid!r}")
        if not values or not all(1 <= value <= 30 for value in values):
            raise ValueError(f"unbounded/out-of-scope domain {name}={valid!r}")
        domains[name] = values
    if math.prod(map(len, domains.values())) > 30000:
        raise ValueError("joint enumeration exceeds 30,000 axis tuples; narrow the probe explicitly")
    return domains


def run_probe(args, report):
    root, module, canonical_pairs, canonical_path, helper_path = load_environment()
    generator_path = Path(module.__file__)
    report["root"] = str(root)
    report["source"] = {"generator_path": str(generator_path), "generator_sha256": file_digest(generator_path),
                        "generator_version": getattr(module, "VERSION", None),
                        "declared_rule_hash": getattr(module, "RULE_HASH", None),
                        "probe_path": str(Path(__file__).resolve()), "probe_sha256": file_digest(__file__),
                        "reviewer_support_path": str(helper_path), "reviewer_support_sha256": file_digest(helper_path)}
    ledger = canonical_path(root)
    report["source"]["canonical_ledger_sha256"] = file_digest(ledger)
    rows = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    rules = []
    for index, row in enumerate(rows):
        program = row.get("program_solution")
        if not isinstance(program, str) or not program.strip():
            raise ValueError(f"canonical variant {index} lacks its rule source")
        normalized = " ".join(program.split()).encode()
        rules.append({"variant": index, "record_sha256": digest(row),
                      "rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
                      "normalized_rule_sha256": hashlib.sha256(normalized).hexdigest(),
                      "rule_hash": hashlib.sha256(normalized).hexdigest()[:12]})
    report["source"]["canonical_rules"] = rules
    if not rules or any(row["rule_hash"] != RULE_HASH for row in rules):
        raise ValueError(f"selected canonical authority must remain {RULE_HASH}")
    if getattr(module, "RULE_HASH", None) != RULE_HASH:
        failure(report, "rule_pin_mismatch", expected=RULE_HASH, actual=getattr(module, "RULE_HASH", None))
    for name in ("generate", "self_check", "observe_overrides"):
        if not callable(getattr(module, name, None)):
            failure(report, "missing_callable", name=name)
    if not callable(getattr(module, "generate", None)):
        return
    period = getattr(module, "LESSON_SCHEDULE_PERIOD", None)
    if type(period) is not int or period <= 0:
        period = None
    report["schedule"] = {"declared_period": period, "examples_needed": getattr(module, "EXAMPLES_NEEDED", None),
                          "note": "Residues describe direct draw indices; this probe assembles no lessons."}
    witnesses = Witnesses()
    rivals = load_rivals(module, report)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("no labeled canonical pairs")
    canonical_stats = Statistics()
    canonical_color_sets, canonical_profile_counts = set(), set()
    report["canonical"] = {
        "labeled_pairs": len(pairs), "pairs": [],
        "profile_definitions": {
            "exact_canonical_dimension_color_set_hits": "height, width, and exact set of nonzero colors",
            "canonical_profile_count_hits": "height, width, and total palette cardinality including zero when present; shared profile-floor convention",
        },
    }
    for pair in pairs:
        replay = {"population": "canonical", **{key: pair[key] for key in ("variant", "split", "pair_index")}}
        result = analyze(pair["input"])
        canonical_stats.add(result)
        color_set_key, profile_count_key = profile_keys(result)
        canonical_color_sets.add(color_set_key)
        canonical_profile_counts.add(profile_count_key)
        report["canonical"]["pairs"].append({"replay": replay, "input_sha256": digest(pair["input"]),
                                               "output_sha256": digest(pair["output"]),
                                               "analysis": compact_analysis(result)})
        witnesses.add(result, replay, [f"canonical:{pair['variant']}:{pair['split']}:{pair['pair_index']}"])
        if result["independent_output"] != pair["output"]:
            failure(report, "independent_canonical_mismatch", replay, result, canonical_output=pair["output"])
        check_functions(module, result, None, report, replay, canonical=True)
        score_rivals(rivals, report, result, pair["output"], replay, witnesses, canonical=True)
    report["canonical"]["support"] = canonical_stats.report()
    report["canonical"]["dimension_color_set_profiles"] = sorted(canonical_color_sets)
    report["canonical"]["dimension_palette_count_profiles"] = sorted(canonical_profile_counts)
    for row in report["rivals"].values():
        counts = row["canonical"]
        row["canonical_status"] = ("error" if counts["errors"] else "refuted" if counts["refuted"]
                                    else "fits_all_labeled_pairs" if counts["agrees"] == len(pairs) else "incomplete")
    default_stats, default_digest = Statistics(), hashlib.sha256()
    report["default_support"] = {"requested": len(args.band) * args.seeds * args.indices,
                                  "attempted": 0, "per_band": {}}
    for band in args.band:
        stats = Statistics()
        color_set_hits, profile_count_hits = 0, 0
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            for index in range(args.index_start, args.index_start + args.indices):
                replay = {"population": "default", "difficulty": band, "seed": seed,
                          "sample_index": index, "overrides": {}}
                report["default_support"]["attempted"] += 1
                try:
                    result = analyze(module.generate(seed, index, difficulty=band))
                except Exception as exc:
                    error(report, "default_generation_error", replay, exc=exc)
                    default_digest.update(json_bytes({"replay": replay, "error": f"{type(exc).__name__}: {exc}"}) + b"\n")
                    continue
                stats.add(result, index, period)
                default_stats.add(result, index, period)
                color_set_key, profile_count_key = profile_keys(result)
                color_set_hits += color_set_key in canonical_color_sets
                profile_count_hits += profile_count_key in canonical_profile_counts
                reasons = [name for name, value in result["features"].items() if value]
                reasons += [f"color:{color}" for color in result["colors"]]
                reasons += [f"band_residue:{band}:{index % period if period else 'undeclared'}"]
                witnesses.add(result, replay, reasons)
                check_generated_domain(result, report, replay)
                check_functions(module, result, band, report, replay)
                score_rivals(rivals, report, result, result["independent_output"], replay, witnesses)
                default_digest.update(json_bytes({"replay": replay, "input_sha256": digest(result["input"]),
                                                  "analysis": compact_analysis(result)}) + b"\n")
        report["default_support"]["per_band"][band] = {**stats.report(),
                                                        "exact_canonical_dimension_color_set_hits": color_set_hits,
                                                        "canonical_profile_count_hits": profile_count_hits,
                                                        "requested": args.seeds * args.indices}
        print(f"default {band}: {stats.count}/{args.seeds * args.indices} analyzed", file=sys.stderr, flush=True)
    report["default_support"]["all_bands"] = default_stats.report()
    report["default_support"]["ordered_case_rows_sha256"] = default_digest.hexdigest()
    report["joint_support"] = {"status": "skipped" if args.skip_joint else "running"}
    if not args.skip_joint:
        domains = parse_domains(module)
        joint = report["joint_support"]
        joint.update(domains=domains, axes_declaration=module.AXES,
                     compatibility="n_distinct_colors <= n_blobs", attempted=0,
                     compatible_attempts=0, compatible_analyzed=0,
                     incompatible_attempts=0, incompatible_rejected=0, per_band={})
        tuples = list(itertools.product(*(domains[name] for name in AXIS_NAMES)))
        legal = sum(values[3] <= values[2] for values in tuples)
        factor = len(args.band) * args.joint_seeds * args.joint_indices
        joint.update(axis_tuples=len(tuples), compatible_axis_tuples=legal,
                     incompatible_axis_tuples=len(tuples) - legal,
                     expected_attempts=len(tuples) * factor, expected_compatible_attempts=legal * factor,
                     expected_incompatible_attempts=(len(tuples) - legal) * factor)
        joint_digest = hashlib.sha256()
        rejection_counts = Counter()
        for band in args.band:
            stats = Statistics()
            for values in tuples:
                overrides = dict(zip(AXIS_NAMES, values))
                compatible = values[3] <= values[2]
                for seed in range(args.joint_seed_start, args.joint_seed_start + args.joint_seeds):
                    for index in range(args.joint_index_start, args.joint_index_start + args.joint_indices):
                        replay = {"population": "joint", "difficulty": band, "seed": seed,
                                  "sample_index": index, "overrides": overrides}
                        joint["attempted"] += 1
                        joint["compatible_attempts" if compatible else "incompatible_attempts"] += 1
                        try:
                            grid = module.generate(seed, index, difficulty=band, **overrides)
                        except ValueError as exc:
                            if compatible:
                                failure(report, "compatible_joint_rejected", replay, exception=str(exc))
                            else:
                                joint["incompatible_rejected"] += 1
                                rejection_counts[str(exc)] += 1
                            joint_digest.update(json_bytes({"replay": replay, "rejected": str(exc)}) + b"\n")
                            continue
                        except Exception as exc:
                            error(report, "joint_generation_error", replay, exc=exc)
                            joint_digest.update(json_bytes({"replay": replay, "error": f"{type(exc).__name__}: {exc}"}) + b"\n")
                            continue
                        try:
                            result = analyze(grid)
                        except Exception as exc:
                            error(report, "joint_grid_error", replay, exc=exc, returned_grid=repr(grid))
                            joint_digest.update(json_bytes({"replay": replay, "grid_error": str(exc)}) + b"\n")
                            continue
                        joint_digest.update(json_bytes({"replay": replay, "input_sha256": digest(result["input"]),
                                                        "analysis": compact_analysis(result)}) + b"\n")
                        if not compatible:
                            failure(report, "incompatible_joint_accepted", replay, result)
                            continue
                        joint["compatible_analyzed"] += 1
                        stats.add(result, index, period)
                        check_generated_domain(result, report, replay)
                        check_functions(module, result, band, report, replay, overrides=overrides)
                        witnesses.add(result, replay, [f"joint:{name}:{value}" for name, value in overrides.items()])
            joint["per_band"][band] = stats.report()
            print(f"joint {band}: {stats.count} compatible grids analyzed", file=sys.stderr, flush=True)
        joint.update(status="complete", ordered_case_rows_sha256=joint_digest.hexdigest(),
                     expected_rejection_reasons=rejection_counts)
    report["witnesses"] = list(witnesses.rows.values())
    report["racket"] = {"status": "not_requested", "labeled_inputs": 0}
    if args.racket_witnesses:
        selected = report["witnesses"][:args.racket_limit]
        report["racket"] = {"status": "running", "requested_inputs": len(selected),
                            "selection": "first exact canonical, feature, band/residue, and joint witnesses",
                            "input_sha256s": [row["input_sha256"] for row in selected],
                            "api": "Catalog(root).apply(TASK_ID, inputs, reference='canonical', allow_unapproved=True)",
                            "timeout_seconds": args.racket_timeout}
        try:
            if not (root / "catalog/puzzles.jsonl").is_file():
                raise FileNotFoundError("This runtime has no mirrored public Catalog; run --racket-witnesses from the library or task-test snapshot")
            from arcpuzzles import Catalog
            applied = Catalog(root).apply(TASK_ID, [row["input"] for row in selected],
                                           reference="canonical", allow_unapproved=True, timeout=args.racket_timeout)
            report["racket"]["receipt"] = applied
            if applied.get("executed_rule_hash") != RULE_HASH or applied.get("rule_hash_matches_catalog") is not True:
                error(report, "racket_authority_mismatch", expected=RULE_HASH)
            if applied.get("generator_sha256") != report["source"]["generator_sha256"]:
                error(report, "racket_generator_source_mismatch")
            results = applied.get("results")
            if not isinstance(results, list) or len(results) != len(selected):
                raise ValueError("Catalog.apply returned an incomplete result list")
            labeled = 0
            for witness, label in zip(selected, results, strict=True):
                if label.get("error") or label.get("valid_output") is not True:
                    error(report, "racket_label_error", witness["replay"], label=label)
                    continue
                actual = normalize_grid(label["output"])
                labeled += 1
                if label.get("input") != witness["input"]:
                    error(report, "racket_input_mismatch", witness["replay"], label=label)
                if actual != witness["independent_output"]:
                    failure(report, "independent_racket_mismatch", witness["replay"],
                            analyze(witness["input"]), racket_output=actual)
            report["racket"].update(status="complete", labeled_inputs=labeled)
        except Exception as exc:
            report["racket"]["status"] = "error"
            error(report, "racket_execution_error", exc=exc)
    manifest = {}
    for loaded in list(sys.modules.values()):
        path = getattr(loaded, "__file__", None)
        if path:
            resolved = Path(path).resolve()
            if resolved.is_file() and resolved.is_relative_to(root) and resolved.suffix == ".py":
                manifest[str(resolved.relative_to(root))] = file_digest(resolved)
    report["source"]["loaded_local_python_sources"] = manifest
    for path, expected in ((generator_path, report["source"]["generator_sha256"]),
                           (ledger, report["source"]["canonical_ledger_sha256"]),
                           (Path(__file__), report["source"]["probe_sha256"])):
        if file_digest(path) != expected:
            error(report, "source_changed_during_probe", path=str(path), initial_sha256=expected,
                  final_sha256=file_digest(path))


def self_test():
    tests = 0
    one = analyze([[0, 0, 0], [0, 8, 0], [0, 0, 0]])
    assert one["features"]["singleton"] and one["independent_output"] == one["input"]
    tests += 1
    cross = analyze([[0, 3, 0], [3, 3, 3], [0, 3, 0]])
    assert cross["pixel_counts"]["actual_additions"] == 4
    assert cross["pixel_counts"]["actual_deletions"] == 1
    assert cross["features"]["component_requires_both"]
    tests += 1
    diagonal = analyze([[2, 0], [0, 2]])
    assert diagonal["observed"]["n_blobs"] == 2 and diagonal["features"]["repeated_color"]
    assert diagonal["independent_output"] == diagonal["input"]
    tests += 1
    line = analyze([[4, 4, 4]])
    assert line["features"]["line"] and not line["features"]["requires_additions"]
    tests += 1
    interference = analyze([[2, 2, 2, 2, 2], [2, 0, 0, 0, 0], [2, 0, 0, 0, 0],
                            [2, 0, 0, 0, 0], [2, 0, 0, 0, 3]])
    assert interference["pixel_counts"]["frame_intersection_cells"] == 1
    assert interference["pixel_counts"]["cross_color_frame_intersection_cells"] == 1
    assert interference["features"]["frame_on_other_input"]
    tests += 1
    try:
        analyze([[True]])
    except ValueError:
        tests += 1
    else:
        raise AssertionError("boolean colors must be rejected")
    same_count_a = analyze([[0, 2, 2], [0, 0, 0]])
    same_count_b = analyze([[0, 7, 7], [0, 0, 0]])
    colors_a, count_a = profile_keys(same_count_a)
    colors_b, count_b = profile_keys(same_count_b)
    assert colors_a != colors_b and count_a == count_b == (2, 3, 2)
    tests += 1
    return {"self_test": "passed", "assertion_cases": tests}


def parser():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("--out", type=Path, help="new JSON report path; existing paths are refused")
    cli.add_argument("--self-test", action="store_true", help="test independent analysis on seven tiny handmade cases")
    cli.add_argument("--band", choices=BANDS, action="append")
    cli.add_argument("--seed-start", type=int, default=0)
    cli.add_argument("--seeds", type=int, default=16)
    cli.add_argument("--index-start", type=int, default=0)
    cli.add_argument("--indices", type=int, default=64)
    cli.add_argument("--skip-joint", action="store_true")
    cli.add_argument("--joint-seed-start", type=int, default=0)
    cli.add_argument("--joint-seeds", type=int, default=1)
    cli.add_argument("--joint-index-start", type=int, default=0)
    cli.add_argument("--joint-indices", type=int, default=4)
    cli.add_argument("--racket-witnesses", action="store_true")
    cli.add_argument("--racket-limit", type=int, default=64)
    cli.add_argument("--racket-timeout", type=float, default=180)
    return cli


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        if args.out is None:
            return 0
    if args.out is None:
        cli.error("--out is required unless only --self-test is requested")
    if args.out.exists() or args.out.is_symlink():
        cli.error(f"output must be new: {args.out}")
    for name in ("seeds", "indices", "joint_seeds", "joint_indices"):
        if getattr(args, name) <= 0:
            cli.error(f"--{name.replace('_', '-')} must be positive")
    if not 1 <= args.racket_limit <= 64:
        cli.error("--racket-limit must be in 1..64")
    if not math.isfinite(args.racket_timeout) or args.racket_timeout <= 0:
        cli.error("--racket-timeout must be finite and positive")
    args.band = list(dict.fromkeys(args.band or BANDS))
    command = [sys.executable, *sys.argv]
    started = time.monotonic()
    report = {"schema": "e3f72a0f2ebb-outline-support-v1", "task_id": TASK_ID, "status": "running",
              "started_utc": datetime.now(timezone.utc).isoformat(), "argv": command,
              "shell_command": shlex.join(command), "cwd": str(Path.cwd().resolve()),
              "python_version": sys.version, "settings": {key: str(value) if isinstance(value, Path) else value
                                                           for key, value in vars(args).items()},
              "sampling": "direct generate calls; no rejection resampling or lesson assembly",
              "output_basis": "independent row-major component-frame prediction; optional public Racket witness labels",
              "failures": [], "errors": [], "rivals": {},
              "limits": ["Finite seeds and indices do not exhaust random support.",
                         "Rival counts describe individual inputs; use shared lesson-census for teaching/rotation evidence.",
                         "Frame collisions are reported as domain failures; Python paint order is not assumed authoritative there.",
                         "Only the four task-specific integer axes are independently observed; unrelated override types are outside this probe.",
                         "Successful case details are compacted into counts/digests; every failed case retains its exact replay."]}
    try:
        run_probe(args, report)
    except BaseException as exc:
        error(report, "probe_execution_error", exc=exc, traceback=traceback.format_exc())
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "error" if report["errors"] else "failed" if report["failures"] else "no_findings"
    exit_code = 2 if report["errors"] else 1 if report["failures"] else 0
    report["exit_code"] = exit_code
    report["summary"] = {"failure_count": len(report["failures"]), "error_count": len(report["errors"]),
                         "failure_kinds": Counter(row["kind"] for row in report["failures"]),
                         "error_kinds": Counter(row["kind"] for row in report["errors"])}
    try:
        atomic_new_json(args.out, report)
    except Exception as exc:
        print(f"Cannot publish report: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "exit_code": exit_code,
                      "report": str(args.out.resolve()), **report["summary"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
