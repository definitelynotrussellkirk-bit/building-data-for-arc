#!/usr/bin/env python3
"""Source-bound, findings-only audit using public authoring APIs.

Run through WORK/run_with_racket.py so cwd is WORK/repo and local dependencies
are selected. Rivals below are independent hypotheses, never reference labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, load_selected_generator

TASK = "351de765e33f"
REPO = Path.cwd().resolve()
OUT = REPO.parent / "checks" / "audit" / TASK


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def load():
    module, source, source_sha = load_selected_generator(TASK, root=REPO)
    catalog = Catalog(REPO)
    row = catalog.get(TASK)
    program = row["variants"][0]["program_solution"]
    identity = {
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_path": str(source.relative_to(REPO.parent)),
        "generator_sha256": source_sha,
        "canonical_rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_rule_sha256": hashlib.sha256(" ".join(program.split()).encode()).hexdigest(),
        "rule_hash": row["rule_hash"],
        "probe_sha256": sha(Path(__file__)),
        "colorblind_rival_connectivity": 8,
    }
    assert module.RULE_HASH == identity["normalized_rule_sha256"][:12] == row["rule_hash"]
    return module, catalog, identity


def components(grid, *, monochrome, diagonals=False):
    """Independent extraction: canonical-style four neighbors or eight-neighbor rival."""
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                  if (dr != 0 or dc != 0) and (diagonals or dr == 0 or dc == 0)]
    seen = set()
    found = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            cells = []
            todo = [(r, c)]
            seen.add((r, c))
            while todo:
                a, b = todo.pop()
                cells.append((a, b))
                for dr, dc in directions:
                    x, y = a + dr, b + dc
                    if (0 <= x < len(grid) and 0 <= y < len(grid[0])
                            and (x, y) not in seen and grid[x][y] != 0
                            and (not monochrome or grid[x][y] == color)):
                        seen.add((x, y))
                        todo.append((x, y))
            found.append({"size": len(cells), "top": min(x for x, _ in cells),
                          "left": min(y for _, y in cells), "cells": sorted(cells)})
    return sorted(found, key=lambda obj: (-obj["size"], obj["top"], obj["left"]))


def paint(grid, obj):
    out = deepcopy(grid)
    if obj:
        for r, c in obj["cells"]:
            out[r][c] = 8
    return out


def colorblind_rank_two(grid):
    objs = components(grid, monochrome=False, diagonals=True)
    return paint(grid, objs[min(1, len(objs) - 1)] if objs else None)


def second_distinct_size(grid):
    objs = components(grid, monochrome=True)
    sizes = sorted({obj["size"] for obj in objs}, reverse=True)
    target = next((obj for obj in objs if len(sizes) > 1 and obj["size"] == sizes[1]), None)
    return paint(grid, target)


def domain_facts(grid, module):
    contact_edges = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                x, y = r + dr, c + dc
                if x < len(grid) and y < len(row) and grid[x][y] not in (0, value):
                    contact_edges.append([[r, c], [x, y]])
    return {
        "arc_grid_legal": (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30
                           and all(len(row) == len(grid[0]) for row in grid)
                           and all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)),
        "self_check": module.self_check(grid),
        "observed_overrides": module.observe_overrides(grid),
        "monochrome_sizes": [obj["size"] for obj in components(grid, monochrome=True)],
        "colorblind_sizes": [obj["size"] for obj in components(grid, monochrome=False, diagonals=True)],
        "different_color_orthogonal_contacts": contact_edges,
    }


def prepare():
    module, catalog, identity = load()
    records = []
    for pair in canonical_pairs(TASK, root=REPO, labeled_only=True):
        grid = pair["input"]
        records.append({"kind": "canonical", "variant": pair["variant"],
                        "split": pair["split"], "pair_index": pair["pair_index"],
                        "seed": None, "sample_index": None, "difficulty": None,
                        "overrides": None, "public_task_domain_legal": True,
                        "input": grid, "canonical_output": pair["output"],
                        "colorblind_rival_output": colorblind_rank_two(grid),
                        "distinct_size_rival_output": second_distinct_size(grid),
                        **domain_facts(grid, module)})
    # Eight profile witnesses in each band. No private generator functions used.
    for band in ("easy", "medium", "hard"):
        for i, profile in enumerate(module.SCENE_PROFILES):
            grid = module.generate(48100, i, difficulty=band, scene_profile=profile)
            records.append({"kind": "generated", "seed": 48100, "sample_index": i,
                            "difficulty": band, "overrides": {"scene_profile": profile},
                            "input": grid, "mirror_output": module.rule_mirror(grid),
                            "colorblind_rival_output": colorblind_rank_two(grid),
                            "distinct_size_rival_output": second_distinct_size(grid),
                            **domain_facts(grid, module)})
    assert len(records) == 27
    assert json.loads((OUT / "input.json").read_text()) == {"inputs": [record["input"] for record in records]}
    write("prepared_8neighbor.json", {**identity, "records": records})
    print(json.dumps({**identity, "input_count": len(records),
                      "canonical_self_check": [r["self_check"] for r in records[:3]],
                      "canonical_colorblind_fits": [r["canonical_output"] == r["colorblind_rival_output"] for r in records[:3]]}))


def verify():
    module, catalog, identity = load()
    prepared = json.loads((OUT / "prepared_8neighbor.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    assert prepared["generator_sha256"] == identity["generator_sha256"] == receipt["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"]
    assert receipt["executed_rule_hash"] == identity["rule_hash"]
    records = []
    for ex, result in zip(prepared["records"], receipt["results"], strict=True):
        assert ex["input"] == result["input"]
        assert result["error"] is None and result["valid_output"]
        out = result["output"]
        expected = ex.get("canonical_output", ex.get("mirror_output"))
        assert expected == out
        records.append({**ex, "racket_output": out,
                        "racket_input_sha256": result["input_sha256"],
                        "racket_output_sha256": result["output_sha256"],
                        "racket_domain_check": result.get("domain_check"),
                        "colorblind_rival_disagrees": ex["colorblind_rival_output"] != out,
                        "distinct_size_rival_disagrees": ex["distinct_size_rival_output"] != out})
    generated = [r for r in records if r["kind"] == "generated"]
    canonical = [r for r in records if r["kind"] == "canonical"]
    assert all(r["self_check"] == [] and not r["colorblind_rival_disagrees"] for r in generated)
    summary = {"reference_inputs": len(records), "generated_inputs": len(generated),
               "generated_colorblind_matches": sum(not r["colorblind_rival_disagrees"] for r in generated),
               "canonical_colorblind_matches": sum(not r["colorblind_rival_disagrees"] for r in canonical),
               "canonical_count": len(canonical),
               "canonical_self_check_rejections": sum(bool(r["self_check"]) for r in canonical),
               "all_reference_outputs_match_canonical_or_mirror": True}
    write("verified.json", {**identity, "reference_receipt_sha256": sha(OUT / "racket.json"),
                            "summary": summary, "records": records})
    # A small full-grid artifact is the exact public demonstration that defeats
    # a rival indistinguishable on every current generated grid.
    witness = next(r for r in canonical if r["colorblind_rival_disagrees"])
    write("minimal_witness.json", {**identity, "witness": witness})
    print(json.dumps(summary))


def lessons():
    module, catalog, identity = load()
    bands = {}
    for band in ("easy", "medium", "hard"):
        episodes = catalog.generate(TASK, count=3, seed=48200, difficulty=band,
                                    n_train=5, n_test=2, allow_unapproved=True, timeout=180)
        rows = []
        for episode in episodes:
            assert episode["provenance"]["generator_sha256"] == identity["generator_sha256"]
            assert episode["executed_rule_hash"] == identity["rule_hash"]
            assert not episode.get("rejections")
            all_pairs = episode["train"] + episode["test"]
            facts = [domain_facts(pair["input"], module) for pair in all_pairs]
            assert all(f["self_check"] == [] for f in facts)
            distinct_wrong = [second_distinct_size(p["input"]) != p["output"] for p in all_pairs]
            colorblind_wrong = [colorblind_rank_two(p["input"]) != p["output"] for p in all_pairs]
            rows.append({"seed": episode["seed"], "sample_indices": episode["sample_indices"],
                         "profiles": [f["observed_overrides"]["scene_profile"] for f in facts],
                         "distinct_size_rival_survives_train": not any(distinct_wrong[:5]),
                         "distinct_size_rival_fails_query": any(distinct_wrong[5:]),
                         "colorblind_rival_matches_every_pair": not any(colorblind_wrong),
                         "pairs": [{"split": "train" if i < 5 else "test", "pair_index": i if i < 5 else i-5,
                                    "sample_index": episode["sample_indices"][i],
                                    "input": p["input"], "racket_output": p["output"],
                                    "distinct_size_rival_output": second_distinct_size(p["input"]),
                                    "colorblind_rival_output": colorblind_rank_two(p["input"]),
                                    "self_check": facts[i]["self_check"]}
                                   for i, p in enumerate(all_pairs)]})
        summary = {"lessons": len(rows), "reference_labeled_inputs": sum(len(r["pairs"]) for r in rows),
                   "unique_inputs": len({digest(p["input"]) for r in rows for p in r["pairs"]}),
                   "self_check_errors": 0,
                   "colorblind_matches_all": sum(r["colorblind_rival_matches_every_pair"] for r in rows),
                   "distinct_size_rival_survives_train": sum(r["distinct_size_rival_survives_train"] for r in rows),
                   "unrefuted_wrong_query_lessons": sum(r["distinct_size_rival_survives_train"] and r["distinct_size_rival_fails_query"] for r in rows)}
        bands[band] = {"summary": summary, "episodes": episodes, "scored_lessons": rows}
        write("lessons.json", {**identity, "complete": False, "seed_range": [48200, 48202],
                               "public_api": "Catalog.generate", "n_train": 5, "n_test": 2,
                               "overrides": {}, "sample_index": 0, "bands": bands})
        print(band, json.dumps(summary), flush=True)
    write("lessons.json", {**identity, "complete": True, "seed_range": [48200, 48202],
                           "public_api": "Catalog.generate", "n_train": 5, "n_test": 2,
                           "overrides": {}, "sample_index": 0, "bands": bands})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "verify", "lessons"))
    args = parser.parse_args()
    {"prepare": prepare, "verify": verify, "lessons": lessons}[args.action]()
