#!/usr/bin/env python3
"""Reproducible distribution and two-query lesson probe for Nearest-Corner Dock.

Run from any directory, using only this checkout's shared/runtime imports::

    python3 generators/93e709ad4848/workspace/probe_review.py \
        --seed-start 0 --lessons-per-band 100 --out var/nearest-corner-probe

The output directory must be new.  ``pairs.jsonl`` contains every distinct
generated input and the diagnostic Python helper's output, so a separate public
``arcpuzzles apply`` run can bind the same inputs to the unchanged Racket rule.
This probe never describes its Python comparisons as Racket verification.

Each difficulty uses exactly the requested consecutive seeds.  The default
population starts each 3-demo/2-query lesson at sample index zero.  A second,
explicitly overlapping population exercises every start in SCHEDULE_PERIOD.
Both populations implement the public worker's contiguous-attempt, rejection,
and duplicate-pair policy using the Python diagnostic labels.  Rejections are
retained as sampling cost; a zero-rejection window has the exact requested five
sample indices. Use --require-no-rejections only for an additional strict audit.
Both query answers, every declared canonical shortcut, and every declared lesson
competitor are checked.  There is no held-out solve-episode access in this tool.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TASK_ID = "93e709ad4848"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 2
N_PAIRS = N_DEMOS + N_QUERIES
MAX_REPLAYS_PER_INPUT = 3
MAX_EXAMPLES = 3
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def packed(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(packed(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        return ["grid must have 1..30 list rows"]
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        return ["grid must have 1..30 columns"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integers 0..9, excluding bool"]
    return []


def components(points: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(points)
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, stack = {first}, [first]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        result.append(group)
    return result


def independent_semantics(grid: Any) -> tuple[dict[str, Any], list[str], Any]:
    """Compute bbox geometry from pixels, without calling generator helpers."""
    errors = grid_errors(grid)
    if errors:
        return {}, errors, None
    height, width = len(grid), len(grid[0])
    points = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    colors = sorted({grid[row][col] for row, col in points})
    groups = components(points)
    features: dict[str, Any] = {
        "grid_h": height, "grid_w": width,
        "canvas_kind": "square" if height == width else "rectangular",
        "object_cells": len(points), "nonzero_color_count": len(colors),
        "nonzero_component_count_4": len(groups),
    }
    if len(colors) != 1:
        errors.append(f"expected one nonzero color, got {colors}")
    if len(groups) != 1:
        errors.append(f"expected one 4-connected nonzero object, got {len(groups)}")
    if errors:
        return features, errors, None
    row0, row1 = min(row for row, _ in points), max(row for row, _ in points)
    col0, col1 = min(col for _, col in points), max(col for _, col in points)
    crop_h, crop_w = row1 - row0 + 1, col1 - col0 + 1
    center_r2, center_c2 = row0 + row1, col0 + col1
    candidates = ((0, 0), (0, width - crop_w), (height - crop_h, 0),
                  (height - crop_h, width - crop_w))
    scores = [((2 * row + crop_h - 1 - center_r2) ** 2
               + (2 * col + crop_w - 1 - center_c2) ** 2) for row, col in candidates]
    # Python's first minimum preserves the Racket list's TL, TR, BL, BR tie order.
    chosen = min(range(4), key=lambda index: scores[index])
    target_r, target_c = candidates[chosen]
    output = [[0] * width for _ in range(height)]
    for row, col in points:
        output[row - row0 + target_r][col - col0 + target_c] = grid[row][col]
    mask = [[int((row0 + row, col0 + col) in points) for col in range(crop_w)]
            for row in range(crop_h)]
    zeros = {(row, col) for row in range(crop_h) for col in range(crop_w) if mask[row][col] == 0}
    holes = sum(not any(row in (0, crop_h - 1) or col in (0, crop_w - 1)
                        for row, col in group) for group in components(zeros))
    corners = ("top_left", "top_right", "bottom_left", "bottom_right")
    centroid_bottom = 2 * sum(row for row, _ in points) > len(points) * (height - 1)
    centroid_right = 2 * sum(col for _, col in points) > len(points) * (width - 1)
    anchor_bottom, anchor_right = 2 * row0 > height - 1, 2 * col0 > width - 1
    features.update({
        "object_color": colors[0], "bbox_h": crop_h, "bbox_w": crop_w,
        "bbox_row0": row0, "bbox_col0": col0,
        "row_center_relation": "tie" if center_r2 == height - 1 else ("top" if center_r2 < height - 1 else "bottom"),
        "col_center_relation": "tie" if center_c2 == width - 1 else ("left" if center_c2 < width - 1 else "right"),
        "selected_corner": corners[chosen], "corner_score_tie_count": scores.count(min(scores)),
        "touches_input_edge": row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1,
        "mask_lr_symmetric": mask == [list(reversed(row)) for row in mask],
        "mask_ud_symmetric": mask == list(reversed(mask)),
        "hole_count": holes, "crop_shape_sha256": digest(mask),
        "centroid_corner_differs": int(centroid_bottom) * 2 + int(centroid_right) != chosen,
        "bbox_anchor_corner_differs": int(anchor_bottom) * 2 + int(anchor_right) != chosen,
        "move_dr": target_r - row0, "move_dc": target_c - col0,
        "identity": output == grid,
    })
    return features, errors, output


def hook_reasons(fn: Any, *args: Any, allow_bool: bool = False, **kwargs: Any) -> tuple[list[str], str | None, bool]:
    copied = copy.deepcopy(args)
    before = copy.deepcopy(copied)
    try:
        result = fn(*copied, **kwargs)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}", copied != before
    if isinstance(result, bool) and allow_bool:
        return ([] if result else ["predicate returned False"]), None, copied != before
    if not isinstance(result, (list, tuple)) or any(not isinstance(reason, str) for reason in result):
        return [], f"invalid reasons result: {type(result).__name__}", copied != before
    return list(result), None, copied != before


def load_generator() -> Any:
    sys.path.insert(0, str(RUNTIME))
    name = f"nearest_corner_review_generator_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Probe:
    def __init__(self, generator: Any, args: argparse.Namespace):
        self.generator, self.args = generator, args
        self.failures: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.draws: dict[tuple[str, int, int], dict[str, Any]] = {}
        self.pairs: dict[str, dict[str, Any]] = {}
        self.lessons: list[dict[str, Any]] = []
        self.rule_examples: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.generation_calls = 0
        self.shortcuts = self.rules("CANONICAL_SHORTCUTS", required=True)
        self.competitors = self.rules("LESSON_COMPETITORS", required=True)
        self.semantic_rivals = self.rules("SEMANTIC_RIVALS")
        self.lesson_rules = dict(self.competitors)
        for name, fn in self.shortcuts.items():
            if name in self.lesson_rules and self.lesson_rules[name] is not fn:
                self.fail("rule_declaration_conflict", f"{name} has different shortcut and lesson callables")
            self.lesson_rules.setdefault(name, fn)
        self.all_rules = dict(self.lesson_rules)
        for name, fn in self.semantic_rivals.items():
            if name in self.all_rules and self.all_rules[name] is not fn:
                self.fail("rule_declaration_conflict", f"{name} has different semantic-rival and lesson callables")
            self.all_rules.setdefault(name, fn)
        self.witnesses = self.rules("SEMANTIC_WITNESSES")
        self.claims = copy.deepcopy(getattr(generator, "WITNESS_RIVALS", {}))
        if not isinstance(self.claims, dict):
            self.fail("witness_declaration", "WITNESS_RIVALS must be a dictionary")
            self.claims = {}
        for witness, names in list(self.claims.items()):
            names = [names] if isinstance(names, str) else names
            if (witness not in self.witnesses or not isinstance(names, (list, tuple))
                    or not names or any(name not in self.semantic_rivals for name in names)):
                self.fail("witness_declaration", f"invalid WITNESS_RIVALS entry {witness!r}")
                del self.claims[witness]
            else:
                self.claims[witness] = list(names)
        self.oracle = getattr(generator, "_semantic_oracle", None)
        if not callable(self.oracle):
            raise ValueError("selected generator must expose agreed _semantic_oracle(grid) diagnostic helper")
        self.period = getattr(generator, "SCHEDULE_PERIOD", None)
        self.schedule = getattr(generator, "schedule_profile", None)
        self.profiles = getattr(generator, "SCHEDULE_PROFILES", None)
        self.profile_keys: set[str] = set()
        if self.schedule is not None or self.profiles is not None or self.period is not None:
            if not callable(self.schedule):
                self.fail("schedule_declaration", "declared schedule requires schedule_profile callable")
            if type(self.period) is not int or not 1 <= self.period <= 1000:
                self.fail("schedule_declaration", "all cyclic starts require explicit SCHEDULE_PERIOD in 1..1000")
                self.period = None
            if not isinstance(self.profiles, (list, tuple, set, frozenset)) or not self.profiles:
                self.fail("schedule_declaration", "SCHEDULE_PROFILES must enumerate the declared profiles")
            else:
                try:
                    for value in self.profiles:
                        hash(value)
                        self.profile_keys.add(packed(value))
                except Exception as exc:
                    self.fail("schedule_declaration", f"profile must be hashable and JSON serializable: {exc}")

    def fail(self, category: str, message: str, **details: Any) -> None:
        self.failures.append({"category": category, "message": message, **details})

    def rules(self, attribute: str, required: bool = False) -> dict[str, Any]:
        raw = getattr(self.generator, attribute, {})
        if not isinstance(raw, dict):
            self.fail("rule_declaration", f"{attribute} must be dict[str, callable]")
            return {}
        if required and not raw:
            self.fail("rule_declaration", f"{attribute} must declare at least one task-local rule")
        rules = {}
        for name, fn in raw.items():
            if not isinstance(name, str) or not name or not callable(fn):
                self.fail("rule_declaration", f"invalid {attribute} entry {name!r}")
            else:
                rules[name] = fn
        return rules

    def run_rule(self, name: str, fn: Any, grid: Any, output: Any, replay: dict[str, Any]) -> dict[str, Any]:
        try:
            prediction = fn(copy.deepcopy(grid))
            errors = grid_errors(prediction)
            if errors:
                raise ValueError("; ".join(errors))
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            self.fail("rival_error", message, rival=name, **replay)
            return {"status": "error", "error": message}
        status = "fit" if prediction == output else "disagree"
        item = {"status": status, "prediction_sha256": digest(prediction)}
        examples = self.rule_examples[name][status]
        if len(examples) < MAX_EXAMPLES:
            examples.append({**replay, "input_sha256": digest(grid), "output_sha256": digest(output),
                             "rival_output_sha256": digest(prediction), "rival_output": prediction})
        return item

    def canonical(self) -> dict[str, Any]:
        from src.core.canonical_pairs import load_task_pairs

        pairs = load_task_pairs(TASK_ID, CANONICAL_PATH)
        if not pairs:
            self.fail("canonical_missing", "no assigned canonical pairs were found")
        rows = []
        counts = {name: Counter() for name in self.all_rules}
        for index, pair in enumerate(pairs):
            replay = {"population": "canonical", "canonical_index": index,
                      "row_index": pair["row_index"], "split": pair["split"], "pair_index": pair["pair_index"]}
            source, target = pair["input"], pair["output"]
            features, errors, independent = independent_semantics(source)
            row = {**replay, "input_sha256": digest(source), "output_sha256": digest(target),
                   "features": features, "domain_errors": errors, "rivals": {}}
            if errors:
                self.fail("canonical_domain", "; ".join(errors), **replay)
            if target is None:
                self.fail("canonical_missing_answer", "canonical pair has no output", **replay)
                rows.append(row)
                continue
            if independent != target:
                self.fail("canonical_independent_semantics", "bbox-crop calculation differs from canonical pair", **replay)
            try:
                helper = self.oracle(copy.deepcopy(source))
                row["python_helper_matches"] = helper == target
                if helper != target:
                    self.fail("canonical_python_helper", "diagnostic helper differs from canonical pair", **replay)
            except Exception as exc:
                row["python_helper_matches"] = False
                self.fail("canonical_python_helper", f"{type(exc).__name__}: {exc}", **replay)
            strict = getattr(self.generator, "strict_canonical_like", None)
            if callable(strict):
                reasons, error, _ = hook_reasons(strict, source, allow_bool=True)
                row["strict_canonical_like"] = {"reasons": reasons, "error": error}
                if reasons or error:
                    self.fail("canonical_strict_rejection", error or "; ".join(reasons), **replay)
            for name, fn in self.all_rules.items():
                scored = self.run_rule(name, fn, source, target, replay)
                row["rivals"][name] = scored
                counts[name][scored["status"]] += 1
                if name in self.shortcuts and scored["status"] != "fit":
                    self.fail("canonical_shortcut_not_a_shortcut", "declared canonical shortcut does not fit this canonical pair",
                              rival=name, **replay)
            rows.append(row)
        return {
            "pair_count": len(pairs), "answer_pair_count": sum(pair["output"] is not None for pair in pairs),
            "normalized_pairs_sha256": digest(pairs), "pairs": rows,
            "rules": {name: {"denominator": len(pairs), **dict(counter),
                             "all_canonical_pairs_fit": bool(pairs) and counter["fit"] == len(pairs)}
                      for name, counter in counts.items()},
        }

    def draw(self, band: str, seed: int, sample_index: int) -> dict[str, Any]:
        key = band, seed, sample_index
        if key in self.draws:
            return self.draws[key]
        replay = {"band": band, "seed": seed, "sample_index": sample_index}
        record: dict[str, Any] = {**replay, "draw_id": f"{band}:{seed}:{sample_index}",
                                  "runtime_rejection_reasons": [], "domain_errors": [], "rivals": {},
                                  "witnesses": {}, "schedule_profile": None}
        self.draws[key] = record
        try:
            self.generation_calls += 1
            raw = copy.deepcopy(self.generator.generate(seed=seed, sample_index=sample_index, difficulty=band))
            grid = raw.get("input") if isinstance(raw, dict) else raw
            self.generation_calls += 1
            replayed = self.generator.generate(seed=seed, sample_index=sample_index, difficulty=band)
            record["deterministic_replay"] = replayed == raw
            if replayed != raw:
                self.fail("deterministic_replay", "repeated generate call differs", **replay)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            record["generation_error"] = message
            record["runtime_rejection_reasons"].append("generate: " + message)
            self.fail("generation_error", message, **replay)
            return record
        malformed = grid_errors(grid)
        if malformed:
            record["runtime_rejection_reasons"].extend(malformed)
            self.fail("malformed_input", "; ".join(malformed), **replay)
            return record
        record["input_sha256"] = digest(grid)
        features, domain_errors, independent = independent_semantics(grid)
        record["features"], record["domain_errors"] = features, domain_errors
        if domain_errors:
            self.fail("generated_domain", "; ".join(domain_errors), **replay)
        for name, allow_bool in (("self_check", False), ("strict_canonical_like", True)):
            fn = getattr(self.generator, name, None)
            if not callable(fn):
                record[name] = {"declared": False}
                continue
            parameters = inspect.signature(fn).parameters
            accepts_band = "difficulty" in parameters or any(p.kind == p.VAR_KEYWORD for p in parameters.values())
            reasons, error, mutated = hook_reasons(fn, grid, allow_bool=allow_bool,
                                                   **({"difficulty": band} if accepts_band else {}))
            record[name] = {"declared": True, "reasons": reasons, "error": error, "mutated_input": mutated}
            if reasons or error or (name == "self_check" and mutated):
                message = error or "; ".join(reasons) or "self_check mutated input"
                self.fail(name, message, **replay)
                if name == "self_check":
                    record["runtime_rejection_reasons"].append("self_check: " + message)
        output = None
        try:
            output = self.oracle(copy.deepcopy(grid))
            output_errors = grid_errors(output)
            if output_errors:
                raise ValueError("; ".join(output_errors))
            record["output_sha256"] = digest(output)
            record["independent_semantics_match"] = independent == output
            if independent != output:
                self.fail("independent_semantics", "diagnostic output differs from independent bbox crop/placement", **replay)
            # This is exactly the public runner's pair digest, including its 12-digit truncation.
            worker_blob = json.dumps([grid, output], ensure_ascii=False, separators=(",", ":"))
            record["worker_pair_hash"] = hashlib.sha256(worker_blob.encode()).hexdigest()[:12]
            if not getattr(self.generator, "ALLOW_IDENTITY_OUTPUT", False) and output == grid:
                record["runtime_rejection_reasons"].append("validate.output_equals_input")
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            self.fail("python_oracle", message, **replay)
            record["runtime_rejection_reasons"].append("python_oracle: " + message)
            record["oracle_error"] = message
        if output is not None and not grid_errors(output):
            for name, fn in self.all_rules.items():
                record["rivals"][name] = self.run_rule(name, fn, grid, output, replay)
        observer = getattr(self.generator, "observe_overrides", None)
        if callable(observer):
            try:
                observed = observer(copy.deepcopy(grid))
                if not isinstance(observed, dict):
                    raise TypeError("observe_overrides must return a dictionary")
                packed(observed)
                record["observed_axes"] = observed
            except Exception as exc:
                self.fail("observe_overrides", f"{type(exc).__name__}: {exc}", **replay)
        for name, fn in self.witnesses.items():
            try:
                fired = fn(copy.deepcopy(grid))
                if type(fired) is not bool:
                    raise TypeError("witness must return bool")
                record["witnesses"][name] = fired
                claimed = self.claims.get(name, [])
                if fired and claimed and not any(record["rivals"].get(rival, {}).get("status") == "disagree"
                                                 for rival in claimed):
                    self.fail("witness_rival_claim", "firing witness has no observed disagreement with its named rivals",
                              witness=name, rivals=claimed, **replay)
            except Exception as exc:
                self.fail("witness_error", f"{type(exc).__name__}: {exc}", witness=name, **replay)
        if callable(self.schedule):
            try:
                profile = self.schedule(seed, sample_index, difficulty=band)
                hash(profile)
                profile_key = packed(profile)
                record["schedule_profile"] = profile
                if self.profile_keys and profile_key not in self.profile_keys:
                    self.fail("undeclared_schedule_profile", f"observed {profile_key}", **replay)
                if self.period:
                    later = self.schedule(seed, sample_index + self.period, difficulty=band)
                    record["schedule_period_verified"] = later == profile
                    if later != profile:
                        self.fail("schedule_not_periodic", "profile does not repeat after SCHEDULE_PERIOD", **replay)
            except Exception as exc:
                self.fail("schedule_error", f"{type(exc).__name__}: {exc}", **replay)
        input_hash = record["input_sha256"]
        if input_hash not in self.pairs:
            self.pairs[input_hash] = {
                "input_sha256": input_hash, "output_sha256": record.get("output_sha256"),
                "input": grid, "output": output, "label_source": "generator._semantic_oracle; diagnostic Python only",
                "independent_semantics_match": record.get("independent_semantics_match", False),
                "features": features, "domain_errors": domain_errors,
                "occurrence_count": 0, "example_replays": [],
            }
        pair = self.pairs[input_hash]
        if pair["output"] != output:
            self.fail("same_input_different_output", "helper output changed for an identical input", **replay)
        pair["occurrence_count"] += 1
        if len(pair["example_replays"]) < MAX_REPLAYS_PER_INPUT:
            pair["example_replays"].append(replay)
        return record

    def lesson(self, policy: str, band: str, seed: int, start: int) -> None:
        row: dict[str, Any] = {"policy": policy, "band": band, "seed": seed, "sample_index_start": start,
                               "requested_sample_indices": list(range(start, start + N_PAIRS)),
                               "accepted_sample_indices": [], "draw_ids": [], "input_sha256": [],
                               "rejections": [], "rivals": {}, "lesson_hook_queries": []}
        accepted, seen = [], set()
        for sample_index in range(start, start + N_PAIRS * 5):
            record = self.draw(band, seed, sample_index)
            reasons = list(record["runtime_rejection_reasons"])
            pair_hash = record.get("worker_pair_hash")
            if not reasons and pair_hash in seen:
                reasons.append("duplicate pair")
            if reasons:
                rejection = {"sample_index": sample_index, "reasons": reasons,
                             "input_sha256": record.get("input_sha256")}
                row["rejections"].append(rejection)
                if self.args.require_no_rejections:
                    self.fail("runtime_policy_rejection", "; ".join(reasons), policy=policy, band=band, seed=seed,
                              sample_index_start=start, rejected_sample_index=sample_index)
                continue
            seen.add(pair_hash)
            accepted.append(record)
            row["accepted_sample_indices"].append(sample_index)
            row["draw_ids"].append(record["draw_id"])
            row["input_sha256"].append(record["input_sha256"])
            if len(accepted) == N_PAIRS:
                break
        row["materialized"] = len(accepted) == N_PAIRS
        row["matches_requested_contiguous_window"] = row["accepted_sample_indices"] == row["requested_sample_indices"]
        row["domain_valid"] = len(accepted) == N_PAIRS and all(not item["domain_errors"] for item in accepted)
        if not row["materialized"]:
            self.fail("lesson_underproduction", f"produced {len(accepted)}/{N_PAIRS} pairs", policy=policy, band=band,
                      seed=seed, sample_index_start=start)
            self.lessons.append(row)
            return
        pairs = [{"input": self.pairs[item["input_sha256"]]["input"],
                  "output": self.pairs[item["input_sha256"]]["output"]} for item in accepted]
        discriminators = [[], []]
        for name in sorted(self.lesson_rules):
            statuses = [item["rivals"].get(name, {}).get("status", "unscored") for item in accepted]
            demo_fits = statuses[:N_DEMOS] == ["fit"] * N_DEMOS
            query_fits = [status == "fit" for status in statuses[N_DEMOS:]]
            errors = any(status not in ("fit", "disagree") for status in statuses)
            if errors:
                status = "error"
            elif not demo_fits:
                status = "refuted"
            elif all(query_fits):
                status = "survived_all"
            else:
                status = "query_discriminates"
                for query_index, fits in enumerate(query_fits):
                    if not fits:
                        discriminators[query_index].append(name)
                self.fail("unidentifiable_query", "rival fits all three demos and disagrees with at least one query",
                          rival=name, policy=policy, band=band, seed=seed, sample_index_start=start,
                          query_indices=[i for i, fits in enumerate(query_fits) if not fits])
            row["rivals"][name] = {"status": status, "demo_pair_statuses": statuses[:N_DEMOS],
                                     "query_pair_statuses": statuses[N_DEMOS:]}
        row["all_rivals_refuted_by_demos"] = bool(self.lesson_rules) and all(
            value["status"] == "refuted" for value in row["rivals"].values())
        row["both_queries_identifiable_against_declared_rivals"] = bool(self.lesson_rules) and not any(discriminators) and all(
            value["status"] != "error" for value in row["rivals"].values())
        hook = getattr(self.generator, "lesson_identifiable", None)
        for query_index in range(N_QUERIES):
            if not callable(hook):
                row["lesson_hook_queries"].append({"query_index": query_index, "declared": False})
                continue
            reasons, error, _ = hook_reasons(hook, pairs[:N_DEMOS], pairs[N_DEMOS + query_index])
            hook_row = {"query_index": query_index, "declared": True, "reasons": reasons, "error": error,
                        "query_changing_demo_survivors": discriminators[query_index]}
            row["lesson_hook_queries"].append(hook_row)
            if error or reasons:
                self.fail("lesson_hook", error or "; ".join(reasons), policy=policy, band=band, seed=seed,
                          sample_index_start=start, query_index=query_index)
            if not error and not reasons and discriminators[query_index]:
                self.fail("lesson_hook_false_identifiable", "hook accepted query despite a query-changing demo survivor",
                          policy=policy, band=band, seed=seed, sample_index_start=start, query_index=query_index,
                          rivals=discriminators[query_index])
        self.lessons.append(row)

    def summary(self) -> dict[str, Any]:
        distributions, rival_draw_counts, witness_counts, schedules = {}, {}, {}, {}
        for band in BANDS:
            draws = [row for row in self.draws.values() if row["band"] == band]
            hashes = sorted({row["input_sha256"] for row in draws if "input_sha256" in row})
            features: dict[str, Counter] = defaultdict(Counter)
            for row in draws:
                for name, value in row.get("features", {}).items():
                    if name != "crop_shape_sha256":
                        features[name][packed(value)] += 1
                for name, value in row.get("observed_axes", {}).items():
                    features["observed:" + name][packed(value)] += 1
            distributions[band] = {
                "sample_tuple_count": len(draws), "well_formed_input_count": sum("input_sha256" in row for row in draws),
                "independent_domain_valid_count": sum("input_sha256" in row and not row["domain_errors"] for row in draws),
                "diagnostic_output_count": sum("output_sha256" in row for row in draws),
                "independent_output_match_count": sum(row.get("independent_semantics_match", False) for row in draws),
                "deterministic_replay_count": sum(row.get("deterministic_replay", False) for row in draws),
                "unique_input_count": len(hashes), "unique_input_sha256": hashes,
                "unique_crop_shape_count": len({row.get("features", {}).get("crop_shape_sha256") for row in draws}
                                               - {None}),
                "feature_histograms": {name: dict(sorted(counter.items())) for name, counter in sorted(features.items())},
            }
            rival_draw_counts[band] = {
                name: {"sample_tuple_denominator": len(draws), **dict(Counter(
                    row["rivals"].get(name, {}).get("status", "unscored") for row in draws))}
                for name in self.all_rules}
            witness_counts[band] = {
                name: {"sample_tuple_denominator": len(draws), "fired": sum(row["witnesses"].get(name, False) for row in draws),
                       "evaluated": sum(name in row["witnesses"] for row in draws)} for name in self.witnesses}
            counts = Counter(packed(row["schedule_profile"]) for row in draws if row["schedule_profile"] is not None)
            missing = sorted(self.profile_keys - set(counts))
            schedules[band] = {"observed_profile_counts": dict(sorted(counts.items())), "missing_declared_profiles": missing,
                               "period_checks": sum("schedule_period_verified" in row for row in draws),
                               "period_matches": sum(row.get("schedule_period_verified", False) for row in draws)}
            if missing:
                self.fail("schedule_coverage", f"declared profiles were not observed: {missing}", band=band)
        lesson_stats = {}
        policies = ("runtime_start_zero", "all_cyclic_starts") if self.period else ("runtime_start_zero",)
        for policy in policies:
            lesson_stats[policy] = {}
            for band in BANDS:
                rows = [row for row in self.lessons if row["policy"] == policy and row["band"] == band]
                rival_counts = {}
                for name in self.lesson_rules:
                    status_counts = Counter(row["rivals"].get(name, {}).get("status", "unmaterialized") for row in rows)
                    rival_counts[name] = {"lesson_denominator": len(rows), **dict(status_counts),
                                         "examples": {status: [{key: row[key] for key in
                                                        ("seed", "sample_index_start", "accepted_sample_indices", "input_sha256")}
                                                       for row in rows if row["rivals"].get(name, {}).get("status") == status][:MAX_EXAMPLES]
                                                      for status in ("refuted", "survived_all", "query_discriminates", "error")}}
                lesson_stats[policy][band] = {
                    "lesson_denominator": len(rows), "query_denominator": len(rows) * N_QUERIES,
                    "materialized": sum(row["materialized"] for row in rows),
                    "raw_contiguous_windows_preserved": sum(row["matches_requested_contiguous_window"] for row in rows),
                    "rejection_count": sum(len(row["rejections"]) for row in rows),
                    "domain_valid_lessons": sum(row["domain_valid"] for row in rows),
                    "all_rivals_refuted_by_demos": sum(row.get("all_rivals_refuted_by_demos", False) for row in rows),
                    "both_queries_identifiable_against_declared_rivals": sum(
                        row.get("both_queries_identifiable_against_declared_rivals", False) for row in rows),
                    "hook_query_count": sum(value.get("declared", False) for row in rows for value in row["lesson_hook_queries"]),
                    "hook_accepted_query_count": sum(value.get("declared", False) and not value.get("error") and not value.get("reasons")
                                                      for row in rows for value in row["lesson_hook_queries"]),
                    "rivals": rival_counts,
                }
        return {"distributions": distributions, "rival_draw_counts": rival_draw_counts,
                "witness_counts": witness_counts, "schedule_coverage": schedules, "lessons": lesson_stats,
                "rival_fit_and_disagreement_examples": self.rule_examples}


def write_jsonl(path: Path, rows: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(packed(row) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--require-no-rejections", action="store_true",
                        help="additional strict assertion; default records lawful duplicate/identity retries as sampling cost")
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args(argv)
    if args.lessons_per_band < 100:
        parser.error("--lessons-per-band must be at least 100")
    if args.out.exists():
        parser.error("--out must be new; preserve previous evidence instead of overwriting it")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.out = args.out.resolve()
    source_paths = [GENERATOR_PATH, Path(__file__).resolve(), CANONICAL_PATH,
                    RUNTIME / "puzzle_generators" / "base.py", RUNTIME / "puzzle_generators" / "runner.py",
                    RUNTIME / "puzzle_generators" / "helpers" / "grid.py",
                    RUNTIME / "src" / "core" / "canonical_pairs.py", REPO / "src" / "arcpuzzles" / "worker.py",
                    REPO / "shared" / "tools" / "generator_semantic_gate.py",
                    REPO / "shared" / "tools" / "check_generator_override_contract.py"]
    source_hashes = {str(path.relative_to(REPO)): file_digest(path) for path in source_paths}
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        generator = load_generator()
        probe = Probe(generator, args)
        canonical = probe.canonical()
        for band in BANDS:
            for seed in range(args.seed_start, args.seed_start + args.lessons_per_band):
                probe.lesson("runtime_start_zero", band, seed, 0)
                if probe.period:
                    for start in range(probe.period):
                        probe.lesson("all_cyclic_starts", band, seed, start)
        summary = probe.summary()
        after = {str(path.relative_to(REPO)): file_digest(path) for path in source_paths}
        if source_hashes != after:
            probe.fail("source_drift", "one or more bound source files changed while this probe was running",
                       changed_paths=[name for name in source_hashes if source_hashes[name] != after[name]])
        write_jsonl(args.out / "pairs.jsonl", probe.pairs.values())
        write_jsonl(args.out / "draws.jsonl", probe.draws.values())
        write_jsonl(args.out / "lessons.jsonl", probe.lessons)
        write_jsonl(args.out / "failures.jsonl", probe.failures)
        report = {
            "schema_version": 1, "task_id": TASK_ID, "generator_version": getattr(generator, "VERSION", None),
            "status": "FAIL" if probe.failures else "PASS_PYTHON_PROBE_PENDING_RACKET_PARITY",
            "label_authority": {"source": "selected generator._semantic_oracle", "racket_executed_by_this_probe": False,
                                "independent_check": "pixel-derived bbox crop, same color, nearest target-bbox center, TL/TR/BL/BR tie order",
                                "required_followup": "public arcpuzzles apply on every input in pairs.jsonl; compare full outputs"},
            "sources_sha256": source_hashes, "source_hashes_unchanged_at_end": source_hashes == after,
            "python_version": platform.python_version(),
            "runtime_import_root": "shared/runtime", "selected_generator_path": str(GENERATOR_PATH.relative_to(REPO)),
            "replay_command": ["python3", str(Path(__file__).resolve().relative_to(REPO)), "--seed-start", str(args.seed_start),
                               "--lessons-per-band", str(args.lessons_per_band),
                               *(["--require-no-rejections"] if args.require_no_rejections else []),
                               "--out", "NEW_OUTPUT_DIRECTORY"],
            "sampling": {"bands": list(BANDS), "seed_start_inclusive": args.seed_start,
                         "seed_end_inclusive": args.seed_start + args.lessons_per_band - 1,
                         "lessons_per_band": args.lessons_per_band, "n_demos": N_DEMOS, "n_queries": N_QUERIES,
                         "runtime_start_zero_sample_indices": list(range(N_PAIRS)),
                         "schedule_period": probe.period,
                         "cyclic_start_indices": list(range(probe.period)) if probe.period else [],
                         "max_attempts_per_lesson": N_PAIRS * 5,
                         "require_no_rejections": args.require_no_rejections,
                         "rejection_policy": "lawful duplicate/identity skips are reported sampling cost; generation, malformed, selfcheck, oracle, domain and underproduction errors still fail",
                         "overlap": "all_cyclic_starts includes start zero; policies are separate populations and share cached draws",
                         "runtime_policy": "worker.py same seed within episode, contiguous sample attempts, self_check, valid pair, identity policy, duplicate-pair rejection",
                         "runtime_labels_are_provisional": True},
            "declarations": {"CANONICAL_SHORTCUTS": sorted(probe.shortcuts), "LESSON_COMPETITORS": sorted(probe.competitors),
                             "lesson_rules_scored": sorted(probe.lesson_rules), "SEMANTIC_RIVALS": sorted(probe.semantic_rivals),
                             "SEMANTIC_WITNESSES": sorted(probe.witnesses), "WITNESS_RIVALS": probe.claims,
                             "SCHEDULE_PROFILES": sorted(probe.profile_keys),
                             "ALLOW_IDENTITY_OUTPUT": bool(getattr(generator, "ALLOW_IDENTITY_OUTPUT", False))},
            "canonical": canonical,
            "totals": {"sample_tuples": len(probe.draws), "generate_calls_including_replays": probe.generation_calls,
                       "unique_generated_inputs": len(probe.pairs), "lesson_windows_including_policy_overlap": len(probe.lessons),
                       "query_positions_including_policy_overlap": len(probe.lessons) * N_QUERIES},
            "sampling_cost": {
                "rejection_records_across_overlapping_policies": sum(len(row["rejections"]) for row in probe.lessons),
                "unique_rejected_sample_tuples": len({(row["band"], row["seed"], rejection["sample_index"])
                                                        for row in probe.lessons for rejection in row["rejections"]}),
                "affected_windows_across_overlapping_policies": sum(bool(row["rejections"]) for row in probe.lessons),
                "affected_default_episode_count": sum(row["policy"] == "runtime_start_zero" and bool(row["rejections"])
                                                       for row in probe.lessons),
                "affected_default_episodes": [
                    {key: row[key] for key in ("band", "seed", "sample_index_start", "requested_sample_indices",
                                               "accepted_sample_indices", "rejections")}
                    for row in probe.lessons if row["policy"] == "runtime_start_zero" and row["rejections"]],
            },
            "failures": {"count": len(probe.failures), "category_counts": dict(Counter(row["category"] for row in probe.failures)),
                         "examples": probe.failures[:30], "all_records": "failures.jsonl"},
            **summary,
            "artifacts": {name: {"sha256": file_digest(args.out / name), "bytes": (args.out / name).stat().st_size}
                          for name in ("pairs.jsonl", "draws.jsonl", "lessons.jsonl", "failures.jsonl")},
        }
    except Exception as exc:
        report = {"schema_version": 1, "task_id": TASK_ID, "status": "ERROR",
                  "sources_sha256": source_hashes, "fatal_error": f"{type(exc).__name__}: {exc}"}
        (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ERROR", "report": str(args.out / "report.json"), "error": report["fatal_error"]}))
        return 2
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.out / "report.json"),
                      "totals": report["totals"], "failure_count": report["failures"]["count"]}, sort_keys=True))
    return 1 if probe.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
