"""Bounded read-only sampler review; run from the packet's protected wrapper."""
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time


BASE = Path(__file__).resolve().parents[3]
HOME = BASE / "repo/generators/89c85768abe1/workspace/parametric"
OUT = Path(__file__).with_name("report.json")
SEEDS = [0, 1, 2, 3, 7, 17, 42, 99, 2026, 424242, 2**31 - 1, 2**63 - 1]
COUNTS = [2, 3, 6]


def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HOME.iterdir())
            if p.name in {"prototype.py", "adapter.py", "racket_rules.py", "canonical.rkt", "promotion.json"}}


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def reconstruct(grid):
    points = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                points.setdefault(color, []).append((r, c))
    out = deepcopy(grid)
    for color, cells in points.items():
        r0 = min(r for r, c in cells)
        r1 = max(r for r, c in cells)
        c0 = min(c for r, c in cells)
        c1 = max(c for r, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def groups(grid, diagonal=False):
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r in range(h) for c in range(w) if grid[r][c]}
    result = []
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    while todo:
        start = min(todo)
        todo.remove(start)
        cells, queue = {start}, deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in offsets:
                p = (r + dr, c + dc)
                if p in todo:
                    todo.remove(p)
                    cells.add(p)
                    queue.append(p)
        result.append(cells)
    return result


def retain(grid, cells):
    return [[v if (r, c) in cells else 0 for c, v in enumerate(row)]
            for r, row in enumerate(grid)]


def oracle(grid, mode):
    completed = reconstruct(grid)
    if mode == "all":
        return completed
    return retain(completed, max(groups(completed), key=len))


def newly_painted(grid):
    completed = reconstruct(grid)
    selected = max(groups(completed),
                   key=lambda cells: sum(grid[r][c] == 0 for r, c in cells))
    return retain(completed, selected)


def selected_bbox_solid(grid):
    completed = reconstruct(grid)
    selected = max(groups(completed), key=len)
    out = retain(completed, selected)
    r0, r1 = min(r for r, c in selected), max(r for r, c in selected)
    c0, c1 = min(c for r, c in selected), max(c for r, c in selected)
    color = completed[min(selected)[0]][min(selected)[1]]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if not out[r][c]:
                out[r][c] = color
    return out


def add_failure(report, label, detail):
    report["failures"].append({"check": label, "detail": detail})


def main():
    started = time.monotonic()
    before = hashes()
    spec = importlib.util.spec_from_file_location("bounded_rectangle_review", HOME / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    report = {
        "schema": "task-local-bounded-adversarial-review-v1",
        "source_sha256": before,
        "task_id": "89c85768abe1",
        "seeds": SEEDS,
        "demos": COUNTS,
        "queries": 4,
        "declared_rivals": list(adapter.rival_names),
        "backend": "independent Python oracle; Racket qualification remains separate",
        "failures": [],
        "prior_design_finding": {
            "rival": "newly_painted_area",
            "status": "coverage gap reported before this probe; no incorrect query label alleged",
            "reason": "Initial teaching margins of 3 or more let area-minus-marker-count rank components identically. A union10 versus isolated9 distinguishes them.",
        },
    }
    coverage = {"shape": Counter(), "rectangles": Counter(), "components": Counter(),
                "component_rectangles": Counter(), "large_completed_cells": [],
                "large_output_cells": [], "large_extent": [], "all8_connected": 0,
                "grids": 0, "episodes": 0, "unique_inputs_by_seed_role_index": set()}
    survivors = Counter()
    extra = {"newly_painted_area": newly_painted, "selected_bbox_solid": selected_bbox_solid}
    extra_counts = {name: {"surviving_lessons": 0, "query_conflicts": 0,
                           "first_two_demo_refutations": 0} for name in extra}
    cached = {}
    global_rng_state = random.getstate()
    for seed in SEEDS:
        for demos in COUNTS:
            matched_inputs = None
            for mode in ("all", "largest_component"):
                ctx = {"seed": seed, "demos": demos, "mode": mode}
                try:
                    episode = adapter.generate(seed, {"mode": mode}, demos, 4)
                except Exception as exc:
                    add_failure(report, "generation", {**ctx, "error": repr(exc)})
                    continue
                cached[(seed, demos, mode)] = episode
                coverage["episodes"] += 1
                inputs = [p["input"] for p in episode["train"] + episode["test"]]
                if len({grid_hash(g) for g in inputs}) != demos + 4:
                    add_failure(report, "within_episode_unique_inputs", ctx)
                if matched_inputs is not None and matched_inputs != inputs:
                    add_failure(report, "matched_inputs_across_settings", ctx)
                matched_inputs = inputs
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    add_failure(report, "exact_counts", ctx)
                teaching = adapter.teaching_report(episode, {"mode": mode})
                if not teaching["accepted"]:
                    add_failure(report, "declared_teaching_gate", {**ctx, "report": teaching})
                for name in adapter.rival_names:
                    agrees = all(adapter.rival_output(p["input"], name) == p["output"]
                                 for p in episode["train"])
                    if agrees:
                        survivors[(mode, demos, name)] += 1
                        conflicts = [i for i, p in enumerate(episode["test"])
                                     if adapter.rival_output(p["input"], name) != p["output"]]
                        if conflicts:
                            add_failure(report, "declared_rival_query_ambiguity",
                                        {**ctx, "rival": name, "queries": conflicts})
                for name, rival in extra.items():
                    if mode != "largest_component":
                        continue
                    if any(rival(p["input"]) != p["output"] for p in episode["train"][:2]):
                        extra_counts[name]["first_two_demo_refutations"] += 1
                    if all(rival(p["input"]) == p["output"] for p in episode["train"]):
                        extra_counts[name]["surviving_lessons"] += 1
                        conflicts = [i for i, p in enumerate(episode["test"])
                                     if rival(p["input"]) != p["output"]]
                        extra_counts[name]["query_conflicts"] += bool(conflicts)
                        if conflicts:
                            add_failure(report, "extra_rival_query_ambiguity",
                                        {**ctx, "rival": name, "queries": conflicts})
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        grid = pair["input"]
                        if pair["output"] != oracle(grid, mode):
                            add_failure(report, "independent_oracle_label", {**ctx, "split": split, "index": index})
                        if adapter.validate_input(grid):
                            add_failure(report, "lawful_input", {**ctx, "split": split, "index": index})
                        if mode != "largest_component":
                            continue
                        coverage["grids"] += 1
                        completed = reconstruct(grid)
                        comps = groups(completed)
                        if len(comps) < 2 or sorted(map(len, comps))[-1] == sorted(map(len, comps))[-2]:
                            add_failure(report, "unique_largest_generated_component", {**ctx, "split": split, "index": index})
                        coverage["shape"][f"{len(grid)}x{len(grid[0])}"] += 1
                        coverage["rectangles"][len({v for row in grid for v in row} - {0})] += 1
                        coverage["components"][len(comps)] += 1
                        for comp in comps:
                            coverage["component_rectangles"][len({completed[r][c] for r, c in comp})] += 1
                        coverage["all8_connected"] += len(groups(completed, True)) == 1
                        coverage["unique_inputs_by_seed_role_index"].add(grid_hash(grid))
                        if split == "test" and index == 3:
                            if len(grid) != 30 or len(grid[0]) != 30:
                                add_failure(report, "30x30_boundary", ctx)
                            cells = set().union(*comps)
                            coverage["large_completed_cells"].append(len(cells))
                            coverage["large_output_cells"].append(sum(v != 0 for row in pair["output"] for v in row))
                            coverage["large_extent"].append([
                                max(r for r, c in cells) - min(r for r, c in cells) + 1,
                                max(c for r, c in cells) - min(c for r, c in cells) + 1])
            for mode in ("all", "largest_component"):
                baseline = cached.get((seed, 2, mode))
                current = cached.get((seed, demos, mode))
                if baseline and current:
                    if current["train"][:2] != baseline["train"] or current["test"] != baseline["test"]:
                        add_failure(report, "count_independent_prefix", {"seed": seed, "demos": demos, "mode": mode})
    if random.getstate() != global_rng_state:
        add_failure(report, "global_random_state_mutation", "Generation changed random.getstate().")
    for seed in (0, 424242, 2**63 - 1):
        for mode in ("all", "largest_component"):
            baseline = adapter.generate(seed, {"mode": mode}, 3, 4)
            settings = {"mode": mode}
            mutated = adapter.generate(seed, settings, 3, 4)
            settings["mode"] = "all" if mode == "largest_component" else "largest_component"
            mutated["train"][0]["input"][0][0] = 9
            mutated["train"][0]["output"][0][0] = 8
            mutated["train"].append({"input": [[7]], "output": [[7]]})
            mutated["private_sampler"]["attempts"] = -1
            adapter.generate(17, {"mode": settings["mode"]}, 6, 4)
            if adapter.generate(seed, {"mode": mode}, 3, 4) != baseline:
                add_failure(report, "returned_data_or_cross_call_contamination", {"seed": seed, "mode": mode})
            one = adapter.generate(seed, {"mode": mode}, 3, 1)
            if one["train"] != baseline["train"] or one["test"] != baseline["test"][:1]:
                add_failure(report, "query_count_independent_prefix", {"seed": seed, "mode": mode})
    coverage["unique_inputs_by_seed_role_index"] = len(coverage["unique_inputs_by_seed_role_index"])
    for name in ("shape", "rectangles", "components", "component_rectangles"):
        coverage[name] = dict(sorted(coverage[name].items()))
    report["coverage"] = coverage
    report["declared_survivors"] = [{"mode": m, "demos": d, "rival": r, "lessons": n}
                                      for (m, d, r), n in sorted(survivors.items())]
    report["additional_rivals"] = extra_counts
    report["source_sha256_after"] = hashes()
    if before != report["source_sha256_after"]:
        add_failure(report, "source_drift_during_probe", "Repeat against stable source.")
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["status"] = "passed_bounded_checks" if not report["failures"] else "findings"
    report["limits"] = [
        "Bounded selected seeds, not exhaustive or universal identifiability.",
        "This review does not execute Racket; native protected qualification is the authority check.",
        "Observed completed-component counts: " + ", ".join(map(str, coverage["components"]))
        + "; observed rectangles per component: " + ", ".join(map(str, coverage["component_rectangles"]))
        + ". These describe the bounded generated distribution, not every validator-legal arrangement.",
    ]
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "episodes": coverage["episodes"],
                      "failures": report["failures"], "additional_rivals": extra_counts,
                      "elapsed_seconds": report["elapsed_seconds"], "report": str(OUT)}))


if __name__ == "__main__":
    main()
