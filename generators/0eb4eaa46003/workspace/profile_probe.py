"""Independent authoring probe for task 0eb4eaa46003.

This file measures pixels using its own monochromatic four-neighbor BFS. It
does not call the generator's object, profile, label, or witness helpers.
``oracle_output`` is a Python interpretation of the public rule, not an executed
Racket label. Use public ``arcpuzzles apply``/``Catalog.apply`` for that evidence.

From a library root::

    PYTHONPATH=src:shared/runtime python3 \
      generators/0eb4eaa46003/workspace/profile_probe.py --seed 0 --seed 37

The report goes to stdout so the caller can choose a retained checks destination.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0eb4eaa46003"
AXIS_BOUNDS = {
    "grid_h": (10, 24),
    "grid_w": (14, 24),
    "shape_size": (4, 10),
    "n_distract": (2, 3),
    "palette_size": (4, 6),
}
RIVAL_NAMES = (
    "row_only_first", "column_only_first", "copy_blue", "copy_red",
    "first_candidate", "fixed_color4", "minimum_color_first", "bbox_only_first",
)
DECLARATION_NAMESPACES = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")


@dataclass(frozen=True)
class Component:
    color: int
    cells: frozenset[tuple[int, int]]

    @property
    def bbox(self):
        rows, columns = zip(*self.cells)
        return min(rows), min(columns), max(rows), max(columns)

    @property
    def mask(self):
        top, left, _, _ = self.bbox
        return frozenset((r - top, c - left) for r, c in self.cells)

    @property
    def rows(self):
        top, _, bottom, _ = self.bbox
        return tuple(sum(r == wanted for r, _ in self.cells)
                     for wanted in range(top, bottom + 1))

    @property
    def columns(self):
        _, left, _, right = self.bbox
        return tuple(sum(c == wanted for _, c in self.cells)
                     for wanted in range(left, right + 1))


def components(grid):
    """Enumerate nonzero monochromatic components, ordered by bbox top-left."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must have rows")
    if any(not isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("grid rows must be sequences")
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        raise ValueError("grid colors must be literal integers 0 through 9")
    found, visited = [], set()
    for row in range(len(grid)):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in visited:
                continue
            pending = deque([(row, column)])
            visited.add((row, column))
            cells = set()
            while pending:
                r, c = pending.popleft()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < len(grid) and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            found.append(Component(color, frozenset(cells)))
    return sorted(found, key=lambda obj: obj.bbox[:2])


def scene(grid):
    objects = components(grid)
    blues = [obj for obj in objects if obj.color == 1]
    reds = [obj for obj in objects if obj.color == 2]
    candidates = [obj for obj in objects if obj.color not in (1, 2)]
    if not blues or not reds:
        raise ValueError("both anchor colors are required")
    matches = [obj for obj in candidates
               if obj.rows == blues[0].rows and obj.columns == reds[0].columns]
    return {"objects": objects, "blues": blues, "reds": reds,
            "candidates": candidates, "matches": matches}


def crop8(obj):
    if obj is None:
        return [[0]]
    top, left, bottom, right = obj.bbox
    return [[8 if (r, c) in obj.cells else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]


def oracle_output(grid):
    """Public-rule mirror: select the first joint profile match and recolor 8."""
    matches = scene(grid)["matches"]
    if not matches:
        raise ValueError("no joint profile match")
    return crop8(matches[0])


def observed_axes(grid):
    data = scene(grid)
    if len(data["matches"]) != 1:
        raise ValueError("exact controls require one joint target")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "shape_size": len(data["matches"][0].cells),
            "n_distract": len(data["candidates"]) - 1,
            "palette_size": len({value for row in grid for value in row})}


def rival_predictions(grid):
    data = scene(grid)
    blue, red, candidates = data["blues"][0], data["reds"][0], data["candidates"]

    def first(predicate):
        return next((obj for obj in candidates if predicate(obj)), None)

    chosen = {
        "row_only_first": first(lambda obj: obj.rows == blue.rows),
        "column_only_first": first(lambda obj: obj.columns == red.columns),
        "copy_blue": blue,
        "copy_red": red,
        "first_candidate": candidates[0] if candidates else None,
        "fixed_color4": first(lambda obj: obj.color == 4),
        "minimum_color_first": min(candidates, key=lambda obj: (obj.color, *obj.bbox[:2]))
                               if candidates else None,
        "bbox_only_first": first(lambda obj: len(obj.rows) == len(blue.rows)
                                 and len(obj.columns) == len(red.columns)),
    }
    return {name: crop8(obj) for name, obj in chosen.items()}


def refuted_rivals(grid):
    expected = oracle_output(grid)
    return sorted(name for name, prediction in rival_predictions(grid).items()
                  if prediction != expected)


def anchor_blind_incidence_prediction(grid):
    """Pick the most repeated candidate profiles, without reading anchor profiles.

    Each candidate counts itself once in each incidence count. Bbox order breaks
    equal scores, as in the proposed shortcut. This intentionally ignores which
    row/column profiles colors 1 and 2 identify.
    """
    candidates = [obj for obj in components(grid) if obj.color not in (1, 2)]
    if not candidates:
        return [[0]]

    def score(obj):
        return (sum(other.rows == obj.rows for other in candidates)
                + sum(other.columns == obj.columns for other in candidates))

    return crop8(max(candidates, key=score))


def anchor_copy_then_incidence_prediction(grid):
    """First spatial candidate copying either anchor; otherwise incidence max."""
    data = scene(grid)
    anchor_masks = {data["blues"][0].mask, data["reds"][0].mask}
    for candidate in data["candidates"]:
        if candidate.mask in anchor_masks:
            return crop8(candidate)
    return anchor_blind_incidence_prediction(grid)


def anchor_role_predictions(grid):
    return {
        "candidate_profile_incidence": anchor_blind_incidence_prediction(grid),
        "anchor_copy_then_incidence": anchor_copy_then_incidence_prediction(grid),
    }


def _sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"))
                          .encode()).hexdigest()


def evaluate_declarations(declarations, grid, expected):
    """Evaluate the actual declared callables without merging their namespaces."""
    result = {}
    for namespace, rivals in declarations.items():
        result[namespace] = {}
        for name, rival in rivals.items():
            copied = deepcopy(grid)
            try:
                prediction = rival(copied)
                result[namespace][name] = {
                    "prediction": prediction,
                    "agrees_with_expected": prediction == expected,
                    "mutated_input": copied != grid,
                }
            except Exception as error:
                result[namespace][name] = {"error": repr(error), "mutated_input": copied != grid}
    return result


def declared_lesson_windows(draws, declarations):
    """Score every available consecutive four-draw window and query holdout.

    These are direct Python-labelled draws, not public materializer executions.
    A rival agreeing with every pair is ``survived_all``, not an ambiguity.
    """
    grouped = {}
    for draw in draws:
        grouped.setdefault((draw["difficulty"], draw["seed"]), {})[draw["sample_index"]] = draw
    windows = []
    for (difficulty, seed), by_index in grouped.items():
        for start in sorted(by_index):
            indices = list(range(start, start + 4))
            if any(index not in by_index for index in indices):
                continue
            rotations = []
            for query in indices:
                demonstrations = [index for index in indices if index != query]
                counts, unrefuted = {}, []
                for namespace, rivals in declarations.items():
                    counts[namespace] = dict.fromkeys(("refuted", "survived_all", "ambiguous", "error"), 0)
                    for name in rivals:
                        results = {index: by_index[index]["declared_rivals"][namespace][name]
                                   for index in indices}
                        if any("error" in result or result["mutated_input"] for result in results.values()):
                            status = "error"
                        elif any(not results[index]["agrees_with_expected"] for index in demonstrations):
                            status = "refuted"
                        elif results[query]["agrees_with_expected"]:
                            status = "survived_all"
                        else:
                            status = "ambiguous"
                        counts[namespace][status] += 1
                        if status != "refuted":
                            unrefuted.append({"namespace": namespace, "name": name, "status": status})
                rotations.append({"query_sample_index": query,
                                  "demonstration_sample_indices": demonstrations,
                                  "rival_status_counts": counts, "unrefuted": unrefuted})
            windows.append({"difficulty": difficulty, "seed": seed, "start": start,
                            "input_sha256s": [by_index[index]["input_sha256"] for index in indices],
                            "rotations": rotations})
    return windows


def collect_report(seeds=(0, 37), indices=range(8), bands=("easy", "medium", "hard")):
    """Finite deterministic pixel coverage; this function does not execute Racket."""
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    declarations = {name: dict(getattr(generator, name)) for name in DECLARATION_NAMESPACES}
    draws, failures = [], []
    for band in bands:
        for seed in seeds:
            for index in indices:
                try:
                    grid = generator.generate(seed, index, difficulty=band)
                    reasons = generator.self_check(grid, difficulty=band)
                    prediction = oracle_output(grid)
                    refuted = refuted_rivals(grid)
                    anchor_roles = anchor_role_predictions(grid)
                    unrefuted_anchor_roles = [name for name, value in anchor_roles.items()
                                             if value == prediction]
                    declared = evaluate_declarations(declarations, grid, prediction)
                    declaration_issues = []
                    for namespace, results in declared.items():
                        for name, result in results.items():
                            if "error" in result or result["mutated_input"]:
                                declaration_issues.append({"namespace": namespace, "name": name,
                                                           "result": result})
                    draw = {"difficulty": band, "seed": seed, "sample_index": index,
                            "input": grid, "input_sha256": _sha256(grid),
                            "python_rule_prediction": prediction,
                            "observed_axes": observed_axes(grid),
                            "refuted_rivals": refuted, "self_check_reasons": reasons,
                            "anchor_role_rival_predictions": anchor_roles,
                            "declared_rivals": declared}
                    draws.append(draw)
                    if (reasons or declaration_issues
                            or (index % 2 and set(refuted) != set(RIVAL_NAMES))
                            or (index % 2 == 0 and unrefuted_anchor_roles)):
                        failures.append({"difficulty": band, "seed": seed,
                                         "sample_index": index, "reasons": reasons,
                                         "unrefuted": sorted(set(RIVAL_NAMES) - set(refuted)),
                                         "unrefuted_anchor_roles": unrefuted_anchor_roles,
                                         "declaration_issues": declaration_issues})
                except Exception as error:
                    failures.append({"difficulty": band, "seed": seed,
                                     "sample_index": index, "error": repr(error)})
    canonical = []
    canonical_fit = {namespace: {name: {"pair_results": []} for name in rivals}
                     for namespace, rivals in declarations.items()}
    for pair in canonical_pairs(TASK_ID, root=root):
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        canonical.append({**identity,
                          "input_sha256": _sha256(pair["input"]),
                          "mirror_matches_stored_output": oracle_output(pair["input"]) == pair["output"],
                          "self_check_reasons": generator.self_check(pair["input"])})
        declared = evaluate_declarations(declarations, pair["input"], pair["output"])
        for namespace, results in declared.items():
            for name, result in results.items():
                canonical_fit[namespace][name]["pair_results"].append({**identity, **result})
    for namespace, rivals in canonical_fit.items():
        for name, result in rivals.items():
            pairs = result["pair_results"]
            errors = any("error" in pair or pair["mutated_input"] for pair in pairs)
            fits = not errors and all(pair["agrees_with_expected"] for pair in pairs)
            result["fits_all_labeled_canonical_pairs"] = fits
            result["status"] = "error" if errors else "fits_all" if fits else "refuted"
            if errors or (namespace == "CANONICAL_SHORTCUTS" and not fits):
                failures.append({"canonical_declaration": {"namespace": namespace, "name": name},
                                 "status": result["status"]})
    windows = declared_lesson_windows(draws, declarations)
    ambiguous_rotations = errored_rotations = survived_all_rotations = 0
    for window in windows:
        for rotation in window["rotations"]:
            statuses = {row["status"] for row in rotation["unrefuted"]}
            ambiguous_rotations += "ambiguous" in statuses
            errored_rotations += "error" in statuses
            survived_all_rotations += "survived_all" in statuses
            if statuses & {"ambiguous", "error"}:
                failures.append({"lesson_window": {key: window[key] for key in ("difficulty", "seed", "start")},
                                 "query_sample_index": rotation["query_sample_index"],
                                 "unrefuted": rotation["unrefuted"]})
    return {"schema": "0eb4eaa46003-independent-profile-probe-v1", "task_id": TASK_ID,
            "generator_path": str(source.relative_to(root)), "generator_sha256": source_hash,
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "label_basis": "independent Python rule mirror for generated inputs; stored canonical outputs; no new Racket labels executed",
            "coverage": {"seeds": list(seeds), "sample_indices": list(indices), "bands": list(bands)},
            "independent_rival_inventory": list(RIVAL_NAMES),
            "independent_anchor_role_rivals": ["candidate_profile_incidence", "anchor_copy_then_incidence"],
            "declared_rival_inventory": {namespace: list(rivals)
                                         for namespace, rivals in declarations.items()},
            "canonical_rival_fit": canonical_fit,
            "declared_lesson_windows": windows,
            "declared_window_summary": {"windows": len(windows), "rotations": 4 * len(windows),
                                        "ambiguous_rotations": ambiguous_rotations,
                                        "errored_rotations": errored_rotations,
                                        "survived_all_rotations": survived_all_rotations},
            "lesson_policy": {"demonstrations": 3, "queries": 1,
                              "query_policy": "hold out each retained pair; preserve remaining order",
                              "scope": "Consecutive direct draws; Python labels; no public materializer execution"},
            "canonical": canonical, "draw_count": len(draws), "draws": draws,
            "failures": failures,
            "status": "fail" if failures or any(not row["mirror_matches_stored_output"]
                                                   or row["self_check_reasons"] for row in canonical)
                      else "pass"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--count", type=int, default=8)
    arguments = parser.parse_args()
    if arguments.count < 1:
        parser.error("--count must be positive")
    report = collect_report(arguments.seed or (0, 37), range(arguments.count))
    print(json.dumps(report, indent=2))
    return report["status"] != "pass"


if __name__ == "__main__":
    raise SystemExit(main())
