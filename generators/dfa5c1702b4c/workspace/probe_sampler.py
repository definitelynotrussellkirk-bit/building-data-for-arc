"""Independent, source-bound geometry and cyclic-lesson probe for dfa5c1702b4c.

Run through the packet's supported wrapper, for example::

    python3 review.py run python3 generators/dfa5c1702b4c/workspace/probe_sampler.py \
        --seed 0 --seed 6 --seed 17 --out ../checks/sampler.json

This is an authoring diagnostic. Generated labels come from the independent
Python geometry oracle below, checked against every labeled canonical pair and
the retained Racket witnesses. Use the shared production lesson census for
fresh Racket labels and accepted/rejected production sample indices.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK_ID = "dfa5c1702b4c"
RULE_HASH = "5264524f1c03"
ROOT = find_root(__file__)


def task_home(root=ROOT):
    """Select a documented library/runtime layout, never a parent-depth guess."""
    for relative in (f"generators/{TASK_ID}", f"puzzle_generators/per_puzzle/{TASK_ID}"):
        candidate = Path(root) / relative
        if (candidate / "generator.py").is_file():
            return candidate
    raise FileNotFoundError(f"No {TASK_ID} generator under {root}")


def load_generator(path=None):
    selected = Path(path or os.environ.get("DFA5C1702B4C_GENERATOR_PATH") or
                    task_home() / "generator.py").resolve()
    name = "dfa5c1702b4c_probe_" + hashlib.sha256(selected.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, selected)
    if spec is None or spec.loader is None:
        raise ImportError(str(selected))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def color_boxes(grid):
    """Recover one color's bounding box directly from its occupied cells."""
    points = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                points.setdefault(color, set()).add((row, col))
    result = []
    for color, cells in points.items():
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        result.append({"color": color, "cells": cells, "top": r0, "left": c0,
                       "bottom": r1, "right": c1,
                       "rows": set(range(r0, r1 + 1)), "cols": set(range(c0, c1 + 1))})
    return result


def geometry_errors(grid):
    """Independent grammar check: solid, distinct-color rectangles with moats."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected a nonempty integer grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged or non-list row"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    boxes = color_boxes(grid)
    errors = []
    if not 2 <= len(boxes) <= 7:
        errors.append("expected 2..7 distinct nonzero colors")
    for box in boxes:
        rectangle = {(r, c) for r in box["rows"] for c in box["cols"]}
        if box["cells"] != rectangle:
            errors.append(f"color {box['color']} does not fill its single rectangle")
        for row, col in box["cells"]:
            neighbors = ((row + dr, col + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
            if any(0 <= r < len(grid) and 0 <= c < width and grid[r][c] not in (0, box["color"])
                   for r, c in neighbors):
                errors.append(f"color {box['color']} touches another color")
                break
    return errors


def oracle(grid, *, order="top", row_threshold=1, col_threshold=1, swap=False):
    """Compute overlaps with explicit coordinate-set intersections.

    This does not import or call the generator's implementation or its oracle.
    The optional alterations support diagnostic rivals, not reference labels.
    """
    keys = {
        "top": lambda box: (box["top"], box["left"]),
        "top_tie_reverse": lambda box: (box["top"], -box["left"]),
        "bottom": lambda box: (box["bottom"], box["left"]),
        "center": lambda box: (box["top"] + box["bottom"], box["left"]),
        "left": lambda box: (box["left"], box["top"]),
        "color": lambda box: box["color"],
    }
    boxes = sorted(color_boxes(grid), key=keys[order])
    output = []
    for i, one in enumerate(boxes):
        row = []
        for j, two in enumerate(boxes):
            if i == j:
                row.append(3)
                continue
            shared_rows = int(len(one["rows"] & two["rows"]) >= row_threshold)
            shared_cols = int(len(one["cols"] & two["cols"]) >= col_threshold)
            row.append(shared_cols + 2 * shared_rows if swap else shared_rows + 2 * shared_cols)
        output.append(row)
    return output


INDEPENDENT_RIVALS = {
    "bottom_sort": lambda grid: oracle(grid, order="bottom"),
    "center_sort": lambda grid: oracle(grid, order="center"),
    "two_row_overlap": lambda grid: oracle(grid, row_threshold=2),
    "two_col_overlap": lambda grid: oracle(grid, col_threshold=2),
    "swap_codes": lambda grid: oracle(grid, swap=True),
    "left_sort": lambda grid: oracle(grid, order="left"),
    "color_sort": lambda grid: oracle(grid, order="color"),
    "top_tie_reverse": lambda grid: oracle(grid, order="top_tie_reverse"),
}


def observed(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_distinct_colors": len(color_boxes(grid))}


def get_canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def declared_rivals(module):
    result = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        values = getattr(module, namespace, {})
        if not isinstance(values, dict) or any(not isinstance(k, str) or not callable(v)
                                               for k, v in values.items()):
            raise ValueError(f"{namespace} must map string names to callable rivals")
        result.update({f"{namespace}:{name}": rival for name, rival in values.items()})
    return result


def _rival_output(rival, grid):
    copied = deepcopy(grid)
    result = rival(copied)
    if copied != grid:
        raise ValueError("rival mutated its input")
    return result


def _hook_reasons(module, pairs, query_index):
    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        return ["lesson_identifiable is not declared"]
    demos = [deepcopy(pair) for index, pair in enumerate(pairs) if index != query_index]
    query = deepcopy(pairs[query_index])
    before = deepcopy((demos, query))
    reasons = hook(demos, query)
    if (demos, query) != before:
        raise ValueError("lesson_identifiable mutated the lesson")
    if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
        raise ValueError("lesson_identifiable must return a list of reason strings")
    return reasons


def audit(*, generator_path=None, module=None, seeds=(0, 6, 17), bands=("easy", "medium", "hard"),
          starts=None, samples_per_seed=32):
    """Inspect every requested cyclic start and every query position.

    Starts default to every residue of the declared finite schedule. The report
    keeps all requested seed/index/input-hash bindings, but bounds grid examples.
    These are direct generator calls; no production rejection policy is implied.
    """
    module = module or load_generator(generator_path)
    source = Path(module.__file__).resolve()
    seeds, bands = tuple(seeds), tuple(bands)
    period = getattr(module, "LESSON_SCHEDULE_PERIOD", None)
    contract_errors = []
    if type(period) is not int or period < 1:
        contract_errors.append("positive LESSON_SCHEDULE_PERIOD is not declared")
        period = None
    if starts is None:
        starts = range(period or 2)
    starts = tuple(starts)
    if not seeds or not bands or not starts or samples_per_seed < 0:
        raise ValueError("need seeds, bands, starts and nonnegative samples_per_seed")
    n_demos = getattr(module, "EXAMPLES_NEEDED", 3)
    if type(n_demos) is not int or not 1 <= n_demos <= 32:
        raise ValueError("EXAMPLES_NEEDED must be an integer in 1..32")
    for name in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        if not getattr(module, name, None):
            contract_errors.append(f"{name} is not declared or empty")
    declared = declared_rivals(module)
    rivals = {**{f"independent:{name}": rival for name, rival in INDEPENDENT_RIVALS.items()},
              **declared}
    canonical = get_canonical_pairs()
    canonical_fits = {}
    for name, rival in rivals.items():
        matches = [_rival_output(rival, pair["input"]) == pair["output"] for pair in canonical]
        canonical_fits[name] = {"matching_pairs": sum(matches), "total_pairs": len(matches),
                                "fits_all": all(matches)}
    if any(oracle(pair["input"]) != pair["output"] for pair in canonical):
        raise AssertionError("independent geometry oracle disagrees with a canonical label")
    canonical_profiles = {tuple(observed(pair["input"]).values()) for pair in canonical}
    counts = {name: {"refuted_draws": 0, "production": Counter(), "rotations": Counter()}
              for name in rivals}
    failures, windows, bindings = [], [], []
    per_band, all_unique = {}, set()
    total_rotation_checks = 0
    for band in bands:
        cache, band_unique, shapes, sizes, colors = {}, set(), set(), set(), Counter()
        strict_hits = profile_hits = dimension_four_hits = 0
        requested_indices = sorted(set(range(samples_per_seed)) |
                                   {start + offset for start in starts for offset in range(n_demos + 1)})
        for seed in seeds:
            for index in requested_indices:
                grid = module.generate(seed, index, difficulty=band)
                errors = geometry_errors(grid)
                if errors:
                    raise AssertionError(f"{band} seed={seed} index={index}: {errors}")
                output = oracle(grid)
                key = grid_hash(grid)
                values = observed(grid)
                boxes = color_boxes(grid)
                rival_outputs = {name: _rival_output(rival, grid) for name, rival in rivals.items()}
                for name, result in rival_outputs.items():
                    counts[name]["refuted_draws"] += result != output
                profile_hook = getattr(module, "schedule_profile", None)
                profile = profile_hook(seed, index, difficulty=band) if callable(profile_hook) else None
                strict_hook = getattr(module, "strict_canonical_like", None)
                strict = strict_hook(deepcopy(grid)) if callable(strict_hook) else None
                strict_hits += strict == [] or strict is True
                profile_hits += tuple(values.values()) in canonical_profiles
                dimension_four_hits += any(len(box["rows"]) == 4 or len(box["cols"]) == 4
                                           for box in boxes)
                band_unique.add(key)
                all_unique.add(key)
                shapes.add((len(grid), len(grid[0])))
                sizes.add(len(boxes))
                colors.update(value for row in output for value in row)
                pair = {"input": grid, "output": output}
                cache[seed, index] = (pair, rival_outputs)
                bindings.append({"band": band, "seed": seed, "sample_index": index,
                                 "input_sha256": key, "profile": profile, **values})
        for seed in seeds:
            for start in starts:
                entries = [cache[seed, start + offset] for offset in range(n_demos + 1)]
                pairs = [entry[0] for entry in entries]
                window = {"band": band, "seed": seed, "start": start,
                          "indices": list(range(start, start + n_demos + 1)),
                          "production_ambiguities": [], "rotation_ambiguities": [], "hook_findings": []}
                for query_index in range(n_demos + 1):
                    total_rotation_checks += 1
                    reasons = _hook_reasons(module, pairs, query_index)
                    if reasons:
                        finding = {"query_index": start + query_index, "reasons": reasons}
                        window["hook_findings"].append(finding)
                    for name in rivals:
                        demo_fit = all(entry[1][name] == entry[0]["output"]
                                       for index, entry in enumerate(entries) if index != query_index)
                        query_fit = entries[query_index][1][name] == pairs[query_index]["output"]
                        status = "refuted" if not demo_fit else "survived_all" if query_fit else "ambiguous"
                        counts[name]["rotations"][status] += 1
                        if query_index == n_demos:
                            counts[name]["production"][status] += 1
                        if status == "ambiguous":
                            finding = {"rival": name, "query_index": start + query_index}
                            window["rotation_ambiguities"].append(finding)
                            if query_index == n_demos:
                                window["production_ambiguities"].append(finding)
                if window["production_ambiguities"] or window["rotation_ambiguities"] or window["hook_findings"]:
                    failures.append(window)
                windows.append(window)
        per_band[band] = {"draws": len(cache), "unique_inputs": len(band_unique),
                          "shape_count": len(shapes), "object_counts": sorted(sizes),
                          "output_values": dict(sorted(colors.items())),
                          "canonical_profile_hits": profile_hits, "strict_hook_hits": strict_hits,
                          "dimension_four_hits": dimension_four_hits,
                          "windows": len(seeds) * len(starts)}
    return {"schema": "dfa5c1702b4c-sampler-probe-v1", "task_id": TASK_ID,
            "generator_path": str(source), "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "rule_hash": RULE_HASH,
            "label_scope": "Independent geometry oracle; canonical and retained Racket witness checks are separate tests.",
            "production_materialization": False, "seeds": list(seeds), "bands": list(bands),
            "declared_period": period, "starts": list(starts),
            "covers_all_declared_starts": period is not None and set(range(period)) <= set(starts),
            "n_demos": n_demos, "samples_per_seed": samples_per_seed,
            "canonical_pairs": len(canonical), "canonical_rival_fits": canonical_fits,
            "declared_rivals": sorted(declared), "rivals": counts, "per_band": per_band,
            "unique_inputs": len(all_unique), "draw_count": len(bindings),
            "window_count": len(windows), "rotation_count": total_rotation_checks,
            "contract_errors": contract_errors, "failures": failures,
            "draw_bindings": bindings, "windows": windows,
            "status": "failed" if failures or contract_errors else "no_ambiguity_found"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-path", type=Path)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--band", choices=("easy", "medium", "hard"), action="append")
    parser.add_argument("--starts", help="comma-separated starts; default every declared schedule residue")
    parser.add_argument("--samples-per-seed", type=int, default=32)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    report = audit(generator_path=args.generator_path, seeds=args.seed or (0, 6, 17),
                   bands=args.band or ("easy", "medium", "hard"),
                   starts=None if args.starts is None else tuple(map(int, args.starts.split(","))),
                   samples_per_seed=args.samples_per_seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "generator_sha256": report["generator_sha256"],
                      "draws": report["draw_count"], "unique_inputs": report["unique_inputs"],
                      "windows": report["window_count"], "rotations": report["rotation_count"],
                      "failed_windows": len(report["failures"]), "contract_errors": report["contract_errors"]}))
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
