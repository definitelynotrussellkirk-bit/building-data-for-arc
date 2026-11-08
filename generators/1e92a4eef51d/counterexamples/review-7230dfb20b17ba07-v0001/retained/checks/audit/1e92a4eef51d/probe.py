"""Findings-only audit of a key-independent body-palette shortcut.

Execute through review.py run. This program never changes a generator or rule.
The Python mirror is diagnostic; verify binds every retained label to public
arcpuzzles apply receipts and checks the independently materialized lesson.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "1e92a4eef51d"
SOURCE_SHA = "f1ed850f3f0edf2de4ca7b40493df62a055a4fd45ff580fc67c5ec0f89968e7c"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")


def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value != 0 and (r, c) != (0, 0)]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def body_colors(grid):
    return {v for r, row in enumerate(grid) for c, v in enumerate(row)
            if v != 0 and (r, c) != (0, 0)}


def reflect(body, horizontal):
    return [row[::-1] for row in body] if horizontal else body[::-1]


def mirror(grid):
    return reflect(crop(grid), grid[0][0] == 1)


def body_color_2_axis(grid):
    """Ignore the key; reflect horizontally iff the body contains colour 2."""
    return reflect(crop(grid), 2 in body_colors(grid))


def body_palette_then_canvas_axis(grid):
    """Ignore the key: body 2 -> horizontal; body 1 -> vertical; else canvas aspect."""
    colors = body_colors(grid)
    horizontal = True if 2 in colors else False if 1 in colors else len(grid[0]) > len(grid)
    return reflect(crop(grid), horizontal)


def load_source():
    gen, path, sha = load_selected_generator(TASK, root=ROOT)
    assert sha == SOURCE_SHA, (sha, SOURCE_SHA)
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    assert len(rows) == 1
    program = rows[0]["program_solution"]
    assert digest(" ".join(program.split()).encode())[:12] == gen.RULE_HASH == "bf7a0a12ef08"
    return gen, path, program


def prepare():
    gen, path, program = load_source()
    (HERE / "audited_generator.py").write_bytes(path.read_bytes())
    (HERE / "audited_rule.rkt").write_text(program)
    save("source.json", {
        "task_id": TASK, "generator_sha256": SOURCE_SHA,
        "generator_path": str(path.relative_to(ROOT)),
        "canonical_program_sha256": digest(program.encode()),
        "rule_hash": gen.RULE_HASH, "source_unchanged": True,
        "snapshots": ["audited_generator.py", "audited_rule.rkt"],
    })
    diagnostic = []
    racket_rows = []
    for band, seed, index in itertools.product((None, "easy", "medium", "hard"), range(4), range(16)):
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert body_color_2_axis(grid) == mirror(grid) == body_palette_then_canvas_axis(grid)
        diagnostic.append({"difficulty": band, "seed": seed, "sample_index": index,
                           "input_sha256": grid_hash(grid), "key": grid[0][0],
                           "body_colors": sorted(body_colors(grid)), "kind": "default"})
        if band is not None and seed < 2 and index < 8:
            racket_rows.append({"kind": "generated", "difficulty": band, "seed": seed,
                                "sample_index": index, "overrides": {}, "input": grid})
    for band, key, size, colors, components, relation in itertools.product(
            (None, "easy", "medium", "hard"), (1, 2), range(4, 8), range(1, 4),
            (1, 2), ("aligned", "conflict")):
        overrides = {"key": key, "blob_size": size, "n_distinct_colors": colors,
                     "n_components": components, "aspect_relation": relation}
        grid = gen.generate(17, 7, difficulty=band, **overrides)
        assert gen.self_check(grid, difficulty=band) == []
        observed = gen.observe_overrides(grid)
        assert all(observed[name] == value for name, value in overrides.items())
        assert body_color_2_axis(grid) == mirror(grid) == body_palette_then_canvas_axis(grid)
        diagnostic.append({"difficulty": band, "seed": 17, "sample_index": 7,
                           "overrides": overrides, "input_sha256": grid_hash(grid),
                           "key": key, "body_colors": sorted(body_colors(grid)), "kind": "override"})
    assert len(diagnostic) == 640 and len(racket_rows) == 48
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(canonical) == 4
    for index, pair in enumerate(canonical):
        assert gen.self_check(pair["input"]) == []
        racket_rows.append({"kind": "canonical", "canonical_pair": index,
                            "input": pair["input"], "canonical_output": pair["output"]})
    neutral = gen.generate(0, 0, difficulty="easy")
    for r, row in enumerate(neutral):
        for c, value in enumerate(row):
            if value and (r, c) != (0, 0):
                neutral[r][c] = 3
    for key in (1, 2):
        grid = deepcopy(neutral)
        grid[0][0] = key
        assert gen.self_check(grid) == []
        racket_rows.append({"kind": "counterfactual", "key": key, "input": grid,
                            "construction": "Generate easy seed 0 index 0, recolour every body cell to 3, set corner key.",
                            "in_validator_domain": True, "in_generated_support": False})
    assert len(racket_rows) == 54
    assert crop(racket_rows[-2]["input"]) == crop(racket_rows[-1]["input"])
    assert mirror(racket_rows[-2]["input"]) != mirror(racket_rows[-1]["input"])
    save("input.json", {"inputs": [row["input"] for row in racket_rows]})
    save("input_index.json", {"rows": [{k: v for k, v in row.items() if k != "input"} for row in racket_rows]})
    save("diagnostic-survey.json", {
        "generator_sha256": SOURCE_SHA, "scope": "Python-only diagnostic, not 640 Racket labels.",
        "default_draws": 256, "override_draws": 384, "total_draws": 640,
        "unique_inputs": len({row["input_sha256"] for row in diagnostic}), "rows": diagnostic,
    })
    save("rival.json", {
        "generator_sha256": SOURCE_SHA,
        "rivals": {fn.__name__: {"definition": fn.__doc__, "input_only": True,
                                 "reads_corner_key": False,
                                 "outputs": [fn(row["input"]) for row in racket_rows]}
                   for fn in (body_color_2_axis, body_palette_then_canvas_axis)},
        "declared_rivals": {name: list(getattr(gen, name, {}))
                            for name in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")},
    })
    print(json.dumps({"prepared": True, "diagnostic_draws": 640,
                      "racket_inputs": 54, "generator_sha256": SOURCE_SHA}))


def verify():
    gen, path, program = load_source()
    applied = json.loads((HERE / "racket.json").read_text())
    rows = json.loads((HERE / "input_index.json").read_text())["rows"]
    grids = json.loads((HERE / "input.json").read_text())["inputs"]
    assert applied["generator_sha256"] == SOURCE_SHA
    assert applied["rule_hash_matches_catalog"]
    assert applied["executed_rule_hash"] == "bf7a0a12ef08"
    assert len(applied["results"]) == len(grids) == len(rows) == 54
    comparisons = []
    for index, (grid, row, result) in enumerate(zip(grids, rows, applied["results"], strict=True)):
        assert grid == result["input"]
        assert result["output"] == mirror(grid)
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        if row["kind"] == "canonical":
            assert row["canonical_output"] == result["output"]
        comparisons.append({"index": index, "kind": row["kind"],
                            "input_sha256": grid_hash(grid), "output_sha256": grid_hash(result["output"]),
                            "generator_domain": result["generator_domain"],
                            "body_color_2_matches": body_color_2_axis(grid) == result["output"],
                            "body_palette_then_canvas_matches": body_palette_then_canvas_axis(grid) == result["output"]})
    generated = [row for row in comparisons if row["kind"] == "generated"]
    canonical = [row for row in comparisons if row["kind"] == "canonical"]
    counterfactual = [row for row in comparisons if row["kind"] == "counterfactual"]
    assert all(row["body_color_2_matches"] and row["body_palette_then_canvas_matches"] for row in generated)
    assert sum(row["body_color_2_matches"] for row in canonical) == 3
    assert all(row["body_palette_then_canvas_matches"] for row in canonical)
    assert [row["body_palette_then_canvas_matches"] for row in counterfactual] == [True, False]
    assert [row["body_color_2_matches"] for row in counterfactual] == [False, True]
    episodes = [json.loads(line) for line in (HERE / "production.jsonl").read_text().splitlines() if line.strip()]
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode["seed"] == 0 and episode["sample_indices"] == [0, 1, 2, 3]
    assert episode["provenance"]["generator_sha256"] == SOURCE_SHA
    assert episode["executed_rule_hash"] == "bf7a0a12ef08"
    assert episode["program"] == program
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert all(body_color_2_axis(pair["input"]) == pair["output"] for pair in pairs)
    assert all(body_palette_then_canvas_axis(pair["input"]) == pair["output"] for pair in pairs)
    # Verify production order independently against public apply, not just mirror.
    for index, pair in enumerate(pairs):
        matches = [result for row, result in zip(rows, applied["results"], strict=True)
                   if row.get("kind") == "generated" and row.get("difficulty") == "hard"
                   and row.get("seed") == 0 and row.get("sample_index") == index]
        assert len(matches) == 1
        assert pair["input"] == matches[0]["input"] and pair["output"] == matches[0]["output"]
    declared = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        declared[namespace] = {}
        for name, rival in getattr(gen, namespace, {}).items():
            canonical_matches = [rival(grids[index]) == applied["results"][index]["output"]
                                 for index, row in enumerate(rows) if row["kind"] == "canonical"]
            if namespace == "CANONICAL_SHORTCUTS":
                assert all(canonical_matches), (name, canonical_matches)
            declared[namespace][name] = {
                "canonical_matches": canonical_matches,
                "production_demo_matches": [rival(pair["input"]) == pair["output"] for pair in pairs[:3]],
                "production_query_matches": rival(pairs[3]["input"]) == pairs[3]["output"],
            }
    hook = gen.lesson_identifiable(pairs[:3], pairs[3])
    assert hook == []
    # Cheap explicit schedule check: all four cyclic starts and all held-out roles.
    schedule_rows = []
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            group = []
            for index in range(start, start + 4):
                match = [(grid, result) for grid, row, result in zip(grids, rows, applied["results"], strict=True)
                         if row.get("kind") == "generated" and row.get("difficulty") == band
                         and row.get("seed") == 0 and row.get("sample_index") == index]
                assert len(match) == 1
                grid, result = match[0]
                group.append({"input": grid, "output": result["output"]})
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(group) if i != query_index]
                query = group[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                assert all(body_palette_then_canvas_axis(pair["input"]) == pair["output"] for pair in group)
                schedule_rows.append({"difficulty": band, "seed": 0, "start": start,
                                      "query_position": query_index,
                                      "new_rival_survives_demos": True, "new_rival_matches_query": True,
                                      "declared_hook_errors": []})
    diagnostic = json.loads((HERE / "diagnostic-survey.json").read_text())
    report = {
        "finding_id": "A2-1e92-1", "classification": "unrefuted key-independent generator shortcut",
        "task_id": TASK, "generator_sha256": SOURCE_SHA,
        "rule_hash": "bf7a0a12ef08", "canonical_program_sha256": digest(program.encode()),
        "executed_callable_sha256": applied["rule_text_sha256"],
        "source_unchanged": digest(path.read_bytes()) == SOURCE_SHA,
        "root_cause": "_body_palette always anchors body colour 2 for key 1 and body colour 1 for key 2, while excluding the active key colour. No palette override removes the anchor. The corner key is therefore redundant throughout generated support.",
        "source_argument_scope": "All lawful seed/sample-index/difficulty and override choices in this source; inferred from its unconditional palette construction, not an exhaustive input enumeration.",
        "rivals": {
            "body_color_2_axis": {"definition": body_color_2_axis.__doc__, "generated_racket_matches": 48,
                                  "generated_racket_total": 48, "canonical_matches": 3,
                                  "canonical_total": 4, "is_canonical_shortcut": False},
            "body_palette_then_canvas_axis": {"definition": body_palette_then_canvas_axis.__doc__,
                                              "generated_racket_matches": 48, "generated_racket_total": 48,
                                              "canonical_matches": 4, "canonical_total": 4,
                                              "is_canonical_shortcut": True,
                                              "limitation": "This is a composite palette/aspect rule, not a proof about the globally simplest alternative."}},
        "diagnostic_survey": {"default_draws": 256, "override_draws": 384,
                              "total_draws": 640, "unique_inputs": diagnostic["unique_inputs"],
                              "labels": "Python mirror only; all retained 54 labels independently checked with Racket."},
        "racket": {"total_inputs": 54, "unique_inputs": len({grid_hash(grid) for grid in grids}),
                   "generated_inputs": 48, "canonical_inputs": 4, "counterfactual_inputs": 2,
                   "all_pass_validator": True, "comparisons": comparisons},
        "counterexample": {"input_indices": [52, 53], "same_body_and_canvas": True,
                           "only_difference": "corner key 1 versus 2", "racket_outputs_differ": True,
                           "in_validator_domain": True, "in_generated_support": False,
                           "why_outside_support": "Monochrome colour-3 bodies lack either mandatory 1/2 palette anchor.",
                           "role": "A valid-domain counterexample showing key dependence that current sampling cannot teach."},
        "production_episode": {"seed": 0, "difficulty": "hard", "sample_indices": [0, 1, 2, 3],
                               "demonstrations": 3, "queries": 1, "rejections": episode["rejections"],
                               "rival_fits_all_pairs": True, "lesson_identifiable_returned": hook,
                               "file": "production.jsonl"},
        "schedule_probe": {"seed": 0, "bands": ["easy", "medium", "hard"], "cyclic_starts": [0, 1, 2, 3],
                           "windows": 12, "query_roles": 48,
                           "unique_inputs": len({grid_hash(grid) for grid, row in zip(grids, rows, strict=True)
                                                 if row.get("kind") == "generated" and row.get("seed") == 0
                                                 and row.get("sample_index", 99) <= 6}),
                           "note": "Overlapping consecutive windows. The rival agrees on queries too; this is persistent shortcut support, not a demo-fit/query-disagreement finding.",
                           "rows": schedule_rows},
        "declared_rival_results": declared,
        "recommendation": "Add this body-palette rival and generate key-independent palettes. Include same-body/canvas examples under both keys using body colours outside {1,2}, then ensure each lesson teaches key dependence. Preserve the canonical Racket rule.",
        "scope": "Findings-only, exact assigned source. No task/source repair, no full battery, no universal learner claim. New source argument and bounded replayable Racket evidence supersede no previous audit resolution.",
    }
    save("finding.json", report)
    print(json.dumps({"status": "REPRODUCED", "finding_id": report["finding_id"],
                      "racket_total": 54, "generated_rival_matches": 48,
                      "canonical_composite_matches": 4, "schedule_query_roles": 48,
                      "generator_sha256": SOURCE_SHA}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else verify)()
