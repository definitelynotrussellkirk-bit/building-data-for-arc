#!/usr/bin/env python3
"""Bounded source-bound peer audit: one center per color versus per object."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arcpuzzles.catalog import Catalog

TASK = "70abd9105769"
ROOT = find_root(__file__)


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def rival(grid):
    """Keep the floor center of the union bounding box for each nonzero color."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color in sorted({x for row in grid for x in row} - {0}):
        cells = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == color]
        rows, cols = zip(*cells)
        out[(min(rows) + max(rows)) // 2][(min(cols) + max(cols)) // 2] = color
    return out


def nonzero(grid):
    return [[r, c, x] for r, row in enumerate(grid) for c, x in enumerate(row) if x]


def geometry(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x}
    objects = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        todo, cells = [start], set()
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            cells.add((r, c))
            for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if (nr,nc) in remaining and grid[nr][nc] == color:
                    remaining.remove((nr,nc)); todo.append((nr,nc))
        rows, cols = zip(*cells)
        h, w = max(rows)-min(rows)+1, max(cols)-min(cols)+1
        objects.append(dict(color=color, bbox=[min(rows),min(cols),max(rows),max(cols)], cells=len(cells), filled_odd_square=h==w and h%2==1 and len(cells)==h*w))
    return objects


gen, source, digest = load_selected_generator(TASK, root=ROOT)
pairs = canonical_pairs(TASK, root=ROOT)
authority = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
authority = [row for row in authority if row.get("task_id") == TASK]
assert len(authority) == 1
rule = authority[0]["program_solution"]
settings = [dict(seed=seed, sample_index=0, difficulty="hard", grid_h=12, grid_w=13, squares=3) for seed in (1, 7, 19)]
demos = [gen.generate(**setting) for setting in settings]
query = [[4 if x else 0 for x in row] for row in demos[1]]
inputs = [p["input"] for p in pairs] + demos + [query]
applied = Catalog(ROOT).apply(TASK, inputs, reference="canonical", timeout=60, check_generator_domain=True)
outputs = [r["output"] for r in applied["results"]]
assert all(output is not None for output in outputs)
assert applied["generator_sha256"] == digest
assert applied["rule_hash_matches_catalog"]
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
canon_rows = []
for i, pair in enumerate(pairs):
    canon_rows.append(dict(variant=pair["variant"], split=pair["split"], pair_index=pair["pair_index"], retained_label_matches_racket=pair["output"]==outputs[i], rival_matches_racket=rival(pair["input"])==outputs[i]))
lesson_demos = []
for i, (setting, grid) in enumerate(zip(settings, demos)):
    label = outputs[len(pairs)+i]
    lesson_demos.append(dict(settings=setting, input=grid, output=label, rival_output=rival(grid), rival_matches_racket=rival(grid)==label, validator_errors=gen.self_check(grid, difficulty="hard")))
query_label = outputs[-1]
query_rival = rival(query)
query_geometry = geometry(query)
finding = dict(
    plausible_rival="Keep one center per foreground color, using that color's combined bounding box.",
    current_source_prevents_distinction="Ordinary generation samples target colors without replacement and assigns a unique color to each placed square.",
    all_canonical_pairs_fit=all(x["retained_label_matches_racket"] and x["rival_matches_racket"] for x in canon_rows),
    all_three_visible_generated_demonstrations_fit=all(x["rival_matches_racket"] for x in lesson_demos),
    lawful_constructed_query_disagrees=query_label!=query_rival,
    query_validator_errors=gen.self_check(query, difficulty="hard"),
    query_objects=query_geometry,
    query_racket_nonzero=nonzero(query_label), query_rival_nonzero=nonzero(query_rival),
    limit="One named rival, five canonical pairs and three generated demonstrations. Query is a legal same-color recoloring of generated geometry, not an ordinary emitted query. No full batteries, repairs, or exhaustive ambiguity search.",
)
assert finding["all_canonical_pairs_fit"] and finding["all_three_visible_generated_demonstrations_fit"]
assert finding["lawful_constructed_query_disagrees"] and not finding["query_validator_errors"]
assert len(query_geometry) == 3 and all(x["filled_odd_square"] for x in query_geometry)
evidence = dict(
    schema="bounded-peer-learnability-v1", task_id=TASK,
    generator_source="repo/generators/70abd9105769/generator.py", generator_sha256=digest,
    probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    command="WORK/.venv/bin/python review.py run python3 ../checks/70abd9105769/probe.py",
    command_cwd="arc_review", payload_cwd=str(Path.cwd()),
    canonical_rule=rule, canonical_rule_text_sha256=hashlib.sha256(rule.encode()).hexdigest(),
    reference_execution={key:applied[key] for key in ("schema","task_id","reference","rule_file","executed_rule_hash","catalog_rule_hash","rule_hash_matches_catalog","rule_text_sha256","generator_sha256","elapsed_seconds")},
    reference_results=applied["results"], canonical_comparisons=canon_rows,
    visible_demonstrations=lesson_demos,
    query=dict(input=query, racket_output=query_label, rival_output=query_rival, input_sha256=sha(query), output_sha256=sha(query_label)),
    finding=finding, source_unchanged_after=True,
)
(HERE / "evidence.json").write_text(json.dumps(evidence, indent=2)+"\n")
print(json.dumps(dict(task_id=TASK, generator_sha256=digest, executed_rule_hash=applied["executed_rule_hash"], racket_inputs=len(inputs), finding=finding, evidence="checks/70abd9105769/evidence.json"), indent=2))
