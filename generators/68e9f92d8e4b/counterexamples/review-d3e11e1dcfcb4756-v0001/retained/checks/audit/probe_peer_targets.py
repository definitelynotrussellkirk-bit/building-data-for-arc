"""Read-only, source-bound probes for the two fixed peer audit targets.

Run from WORK through run_with_racket.py; only checks/audit evidence is written.
Reference labels must come from the separate public arcpuzzles apply commands.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
TASKS = ("68e9f92d8e4b", "7185b8225f1c")


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def components(grid, *, match_color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    found = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = r + dr, c + dc
                if nxt in unseen and (not match_color or grid[nxt[0]][nxt[1]] == color):
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        found.append(cells)
    return found


def whole_nonzero_l_only(grid):
    """Rival: only complete a whole nonzero component that is itself an L."""
    out = [row[:] for row in grid]
    for cells in components(grid, match_color=False):
        colors = {grid[r][c] for r, c in cells}
        rows, cols = [r for r, _ in cells], [c for _, c in cells]
        if (len(colors) == 1 and len(cells) == 3
                and max(rows) - min(rows) == max(cols) - min(cols) == 1):
            color = next(iter(colors))
            for r in range(min(rows), max(rows) + 1):
                for c in range(min(cols), max(cols) + 1):
                    out[r][c] = color
    return out


def local_corner_closure(cells):
    """One simultaneous pass fills the fourth corner of 3-of-4 2x2 cells."""
    expanded = set(cells)
    candidates = {(r - dr, c - dc) for r, c in cells for dr in (0, 1) for dc in (0, 1)}
    for r, c in candidates:
        box = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
        if len(box & cells) == 3:
            expanded |= box
    return expanded


def local_corner_then_halo(grid):
    """Plausible local rival: complete small corners, then dilate each cell.

    It never computes a component bounding rectangle. Components and original
    red cells are preserved; singleton components do not initiate any paint.
    """
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for cells in components(grid, match_color=True):
        if len(cells) < 2:
            continue
        for sr, sc in local_corner_closure(cells):
            for r in range(max(0, sr - 1), min(h, sr + 2)):
                for c in range(max(0, sc - 1), min(w, sc + 2)):
                    if out[r][c] == 0:
                        out[r][c] = 3
    return out


RIVALS = {TASKS[0]: whole_nonzero_l_only, TASKS[1]: local_corner_then_halo}


def authority(task):
    rows = [json.loads(line) for line in canonical_path(ROOT).open() if line.strip()]
    sources = sorted({row["program_solution"] for row in rows if row.get("task_id") == task})
    assert len(sources) == 1
    source = sources[0]
    return {
        "program_solution_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
    }


def prepare():
    summaries = []
    for task in TASKS:
        gen, source, source_sha = load_selected_generator(task, root=ROOT)
        pairs = canonical_pairs(task, root=ROOT, labeled_only=True)
        cases = []
        for index, pair in enumerate(pairs):
            cases.append({
                "kind": "canonical", "canonical_index": index,
                "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                "seed": None, "sample_index": None, "difficulty": None, "overrides": {},
                "input": pair["input"], "canonical_output": pair["output"],
            })
        for band in ("easy", "medium", "hard"):
            for index in range(12):
                cases.append({
                    "kind": "generated_default", "seed": 23, "sample_index": index,
                    "difficulty": band, "overrides": {},
                    "input": gen.generate(23, index, difficulty=band),
                })
        if task == TASKS[1]:
            for index, profile in enumerate(gen.SCENE_PROFILES):
                cases.append({
                    "kind": "generated_override", "seed": 90210, "sample_index": index,
                    "difficulty": "medium", "overrides": {"scene_profile": profile},
                    "input": gen.generate(90210, index, difficulty="medium", scene_profile=profile),
                })
        for case in cases:
            grid = case["input"]
            case["self_check"] = gen.self_check(grid)
            case["input_sha256"] = digest(grid)
            case["rival_output"] = RIVALS[task](grid)
            case["observed_profile"] = gen.observe_overrides(grid) if hasattr(gen, "observe_overrides") else None
        if task == TASKS[0]:
            witness = pairs[0]["input"]
            membership = {
                "origin": "canonical variant 0, train pair 0",
                "seed": None, "sample_index": None, "difficulty": None, "overrides": {},
                "canonical_task_domain": True,
                "documented_generator_domain": False,
                "generated_support": False,
                "reason": "Canonical touching differently colored Ls violate the generator's separated nonzero-component grammar.",
            }
        else:
            witness = [[0] * 10 for _ in range(10)]
            for r, c in ((0, 0), (3, 3), (4, 3), (5, 3), (5, 4), (5, 5)):
                witness[r][c] = 2
            membership = {
                "origin": "hand-constructed long-arm L plus isolated singleton",
                "seed": None, "sample_index": None, "difficulty": None, "overrides": {},
                "canonical_task_domain": "reference-lawful extension of documented component/bbox semantics",
                "documented_generator_domain": True,
                "generated_support": False,
                "reason": "self_check and strict_canonical_like accept polyomino_concave; 3x3 L bbox is absent from every selected shape template/public multi-cell family.",
            }
        summary = {
            "task_id": task, "generator_sha256": source_sha, "version": gen.VERSION,
            "source_path": str(source.relative_to(ROOT)), **authority(task),
            "phase": "audit_current_source", "witness_membership": membership,
            "witness_self_check": gen.self_check(witness),
            "witness_strict_canonical_like": gen.strict_canonical_like(witness) if hasattr(gen, "strict_canonical_like") else "not declared",
            "witness_profile": gen.observe_overrides(witness) if hasattr(gen, "observe_overrides") else None,
            "rival_name": RIVALS[task].__name__,
            "canonical_declared_rivals": {},
            "population_cases": len(cases),
            "population_unique_inputs": len({case["input_sha256"] for case in cases}),
        }
        for registry_name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
            registry = getattr(gen, registry_name, {})
            summary["canonical_declared_rivals"][registry_name] = {
                name: {"fits": sum(rival(p["input"]) == p["output"] for p in pairs), "total": len(pairs)}
                for name, rival in registry.items()
            }
        if task == TASKS[1]:
            shapes = [gen._HORIZONTAL, gen._VERTICAL, *gen._CONCAVE_SHAPES, *gen._RECTANGLE_SHAPES]
            summary["shape_closure_checks"] = []
            for shape in shapes:
                cells = set(shape)
                rows, cols = [r for r, _ in cells], [c for _, c in cells]
                bbox = {(r, c) for r in range(min(rows), max(rows) + 1) for c in range(min(cols), max(cols) + 1)}
                summary["shape_closure_checks"].append({
                    "shape": sorted(shape), "one_pass_closure_equals_bbox": local_corner_closure(cells) == bbox,
                })
            summary["public_multicomponent_shapes"] = sorted({
                tuple(sorted((r - min(x for x, _ in cells), c - min(y for _, y in cells)) for r, c in cells))
                for grid in gen._PUBLIC_INPUTS.values()
                for cells in components(grid, match_color=True) if len(cells) >= 2
            })
        folder = OUT / task
        dump(folder / "input.json", witness)
        dump(folder / "rival.json", RIVALS[task](witness))
        dump(folder / "population-inputs.json", [case["input"] for case in cases])
        dump(folder / "cases.json", cases)
        dump(folder / "prepare.json", summary)
        summaries.append(summary)
    print(json.dumps(summaries, indent=2))


def differences(actual, rival):
    return [
        {"row": r, "col": c, "racket": actual[r][c], "rival": rival[r][c]}
        for r in range(len(actual)) for c in range(len(actual[0]))
        if actual[r][c] != rival[r][c]
    ]


def summarize():
    summaries = []
    for task in TASKS:
        folder = OUT / task
        gen, _, source_sha = load_selected_generator(task, root=ROOT)
        prep = json.loads((folder / "prepare.json").read_text())
        cases = json.loads((folder / "cases.json").read_text())
        single = json.loads((folder / "racket.json").read_text())
        population = json.loads((folder / "population-racket.json").read_text())
        assert prep["generator_sha256"] == source_sha == single["generator_sha256"] == population["generator_sha256"]
        assert prep["rule_hash"] == single["executed_rule_hash"] == population["executed_rule_hash"]
        assert single["rule_hash_matches_catalog"] and population["rule_hash_matches_catalog"]
        assert len(population["results"]) == len(cases)
        for case, result in zip(cases, population["results"]):
            assert result["error"] is None and result["valid_output"]
            assert result["input"] == case["input"]
            case["actual_racket_output"] = result["output"]
            case["rival_matches_racket"] = case["rival_output"] == result["output"]
            case["canonical_output_matches_racket"] = case.get("canonical_output", result["output"]) == result["output"]
        result = single["results"][0]
        assert result["error"] is None and result["valid_output"]
        rival = json.loads((folder / "rival.json").read_text())
        witness = {
            **prep,
            "executed_rule_text_sha256": single["rule_text_sha256"],
            "input": result["input"], "actual_racket_output": result["output"],
            "rival_output": rival, "differing_cells": differences(result["output"], rival),
            "public_apply_command": single["command"], "public_apply_effective_cwd": single["cwd"],
            "public_apply_exit_code": 0,
        }
        assert witness["differing_cells"]
        summary = {
            "task_id": task, "generator_sha256": source_sha, "rule_hash": prep["rule_hash"],
            "canonical_program_solution_sha256": prep["program_solution_sha256"],
            "executed_rule_text_sha256": single["rule_text_sha256"],
            "phase": "audit_current_source", "groups": {},
            "witness_self_check": prep["witness_self_check"],
            "witness_differing_cells": witness["differing_cells"],
            "population_racket_errors": 0,
            "scope": "Three bands, fixed seed 23, sample indices 0..11 in each band; 36 default draws. Canonical labeled rows all retained, including repeated variants.",
            "canonical_declared_rivals": prep["canonical_declared_rivals"],
        }
        for kind in sorted({case["kind"] for case in cases}):
            group = [case for case in cases if case["kind"] == kind]
            summary["groups"][kind] = {
                "n": len(group), "unique_inputs": len({case["input_sha256"] for case in group}),
                "self_check_rejections": sum(bool(case["self_check"]) for case in group),
                "rival_matches_racket": sum(case["rival_matches_racket"] for case in group),
                "canonical_output_matches_racket": sum(case["canonical_output_matches_racket"] for case in group) if kind == "canonical" else None,
            }
        if task == TASKS[1]:
            summary["scope"] += " All thirteen scene_profile overrides also tested at seed 90210, matching sample index 0..12, medium."
            declared = dict(gen.LESSON_COMPETITORS)
            rotation_rows = []
            production_rows = []
            for band in ("easy", "medium", "hard"):
                group = [case for case in cases if case["kind"] == "generated_default" and case["difficulty"] == band]
                for start in range(9):
                    pairs = [{"input": case["input"], "output": case["actual_racket_output"]} for case in group[start:start + 4]]
                    for qindex in range(4):
                        demos = [pair for i, pair in enumerate(pairs) if i != qindex]
                        query = pairs[qindex]
                        failures = [
                            name for name, fn in declared.items()
                            if all(fn(pair["input"]) == pair["output"] for pair in demos)
                            and fn(query["input"]) != query["output"]
                        ]
                        row = {"band": band, "seed": 23, "start_index": start, "query_offset": qindex,
                               "hook_reasons": gen.lesson_identifiable(demos, query), "ambiguous_declared_rivals": failures}
                        rotation_rows.append(row)
                        if qindex == 3:
                            production_rows.append(row)
            summary["declared_lesson_probe"] = {
                "demonstration_count": 3, "policy": "four consecutive sample indices, fourth query; all four holds-out also tested",
                "window_count": len(production_rows), "materialized_draws": 36,
                "unique_materialized_inputs": len({case["input_sha256"] for case in cases if case["kind"] == "generated_default"}),
                "production_ambiguities": sum(bool(row["ambiguous_declared_rivals"]) for row in production_rows),
                "rotation_count": len(rotation_rows),
                "rotation_ambiguities": sum(bool(row["ambiguous_declared_rivals"]) for row in rotation_rows),
                "hook_warnings": sum(bool(row["hook_reasons"]) for row in rotation_rows),
                "rival_names": list(declared), "sample_starts": "0..8, including both parity residues; fixed seed 23 in all three bands",
                "limitation": "Overlapping bounded windows, not 27 independent lessons or a 100-per-band census; no universal-rival claim.",
            }
            demos = [{"input": case["input"], "output": case["actual_racket_output"]} for case in cases
                     if case["kind"] == "generated_default" and case["difficulty"] == "easy" and case["sample_index"] in (0, 1, 2)]
            extension = {
                "task_id": task, "generator_sha256": source_sha, "rule_hash": prep["rule_hash"],
                "demonstrations": demos, "demo_replay": {"seed": 23, "sample_indices": [0, 1, 2], "difficulty": "easy", "overrides": {}},
                "query": {"input": result["input"], "output": result["output"]},
                "query_membership": prep["witness_membership"],
                "rival": "local_corner_then_halo", "rival_fits_all_demos": all(local_corner_then_halo(p["input"]) == p["output"] for p in demos),
                "rival_changes_query": local_corner_then_halo(result["input"]) != result["output"],
                "declared_hook_reasons": gen.lesson_identifiable(demos, {"input": result["input"], "output": result["output"]}),
                "classification": "domain-extension ambiguity, not a production-sampled query failure",
            }
            assert extension["rival_fits_all_demos"] and extension["rival_changes_query"]
            summary["shape_closure_checks"] = prep["shape_closure_checks"]
            summary["public_multicomponent_shapes"] = prep["public_multicomponent_shapes"]
            dump(folder / "domain-extension-lesson.json", extension)
            dump(folder / "declared-lesson-windows.json", rotation_rows)
        dump(folder / "cases.json", cases)
        dump(folder / "counterexample.json", witness)
        dump(folder / "summary.json", summary)
        summaries.append(summary)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        raise SystemExit("usage: probe_peer_targets.py prepare|summarize")
