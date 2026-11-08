"""Bounded private authoring audit and first-turn public challenge export."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "8b6543be4517"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def sources():
    paths = [p for p in HERE.rglob("*") if p.is_file()
             and p.suffix in {".py", ".rkt", ".json", ".md"}
             and not {"evidence", "examples", "__pycache__"}.intersection(p.relative_to(HERE).parts)]
    paths.append(HERE.parents[1] / "generator.py")
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def describe(grid):
    counts = Counter(cell for row in grid for cell in row)
    return {"shape": [len(grid), len(grid[0])],
            "color_counts": {str(k): v for k, v in sorted(counts.items())},
            "nonzero_cells": sum(n for color, n in counts.items() if color != 0)}


def grid_svg(grid):
    colors = ("#111111", "#0074d9", "#ff4136", "#2ecc40", "#ffdc00",
              "#aaaaaa", "#f012be", "#ff851b", "#7fdbff", "#870c25")
    h, w, size = len(grid), len(grid[0]), 18
    cells = "".join(f'<rect x="{c*size}" y="{r*size}" width="18" height="18" '
                    f'fill="{colors[v]}" stroke="#666" stroke-width=".4"/>'
                    f'<text x="{c*size+9}" y="{r*size+13}" text-anchor="middle" '
                    f'font-size="10" fill="{"white" if v in (0,1,2,9) else "black"}">{v}</text>'
                    for r, row in enumerate(grid) for c, v in enumerate(row))
    return f'<svg role="img" aria-label="{h} rows, {w} columns" width="{w*size}" height="{h*size}" viewBox="0 0 {w*size} {h*size}">{cells}</svg>'


def write_html(path, cases):
    sections = []
    for case in cases:
        grids = "".join(f'<figure><figcaption>{html.escape(label)}</figcaption>{grid_svg(grid)}</figure>'
                        for label, grid in case["grids"])
        sections.append(f'<section><h2>{html.escape(case["title"])}</h2><div>{grids}</div></section>')
    path.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Private mirror/rank evidence</title>'
                    '<style>body{font:15px system-ui;margin:24px;background:#f4f5f7;color:#17202a}'
                    'section{background:white;padding:18px;margin:20px 0}section>div{display:flex;flex-wrap:wrap;gap:20px}'
                    'figure{margin:0;max-width:100%;overflow:auto}figcaption{margin:8px 0;font-weight:600}'
                    'svg{display:block}h1{font-size:26px}</style><h1>Private authoring evidence</h1>'
                    '<p>Exact integer grids, with cell values printed. Intermediate component interpretation is diagnostic metadata. '
                    'The counterfactual labels below are protected Racket executions; this page is not a model challenge.</p>'
                    + "".join(sections) + '</html>', encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if args.out.exists() or args.out.is_symlink():
        parser.error("output already exists; choose a new path")
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    before = sources()
    summary = {"schema": "mirror-rank-authoring-audit-v1", "task_id": TASK,
               "status": "running", "command": shlex.join([sys.executable, *sys.argv]),
               "source_sha256": before, "episode_successes": 0, "episode_failures": 0,
               "failures": [], "episodes": [], "runtime_identities": [],
               "counterfactual_successes": 0,
               "scope": "Six episodes, finite declared Python rivals fitted on demonstrations only; all gold labels and the causal counterfactual use protected Racket. No universal uniqueness, training benefit, native qualification or acceptance claim.",
               "public_scope": "Only the first current query and visible demonstrations; no future queries, total-count hints, labels, program, setting or seed. Controller mappings remain private."}
    episodes, index, views = [], [], []
    try:
        sys.path[:0] = [str(ROOT / "shared/runtime"), str(ROOT / "src")]
        spec = importlib.util.spec_from_file_location("_mirror_rank_audit_family", HERE / "family.py")
        family = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = family
        spec.loader.exec_module(family)
        from reviewer_support import public_challenge_bytes

        for seed, demos in ((0, 2), (17, 3), (97, 6)):
            for mode in ("closure", "largest_after"):
                job = {"seed": seed, "settings": {"mode": mode}, "demos": demos, "queries": 4}
                try:
                    episode = family.generate(**job)
                    # Recheck transport projection from only this current query.
                    visible = {"train": episode["train"], "test": [episode["test"][0]]}
                    public_bytes = public_challenge_bytes(visible)
                    digest = hashlib.sha256(public_bytes).hexdigest()
                    public_name = f"public/{digest}.json"
                    public_path = out / public_name
                    if public_path.exists() and public_path.read_bytes() != public_bytes:
                        raise RuntimeError("public content hash collision")
                    public_path.write_bytes(public_bytes)
                    episode_index = len(episodes)
                    episodes.append(episode)
                    index.append({"episode_index": episode_index, "public_path": public_name,
                                  "public_sha256": digest, "seed": seed, "settings": job["settings"],
                                  "current_query_index": 0, "current_answer": episode["test"][0]["output"],
                                  "future_queries_private": episode["test"][1:],
                                  "controller": "Reveal one next query only after the preceding answer; do not reveal the total count or signal the final turn."})
                    details = [{"split": split, "pair_index": i,
                                "input": describe(pair["input"]), "output": describe(pair["output"])}
                               for split in ("train", "test") for i, pair in enumerate(episode[split])]
                    summary["episodes"].append({**job, "episode_index": episode_index,
                                                "pair_statistics": details, "teaching": episode["teaching"]})
                    if episode["racket"] not in summary["runtime_identities"]:
                        summary["runtime_identities"].append(episode["racket"])
                    summary["episode_successes"] += 1
                    if mode == "largest_after" and seed == 0:
                        pair = episode["train"][0]
                        intermediate = family.intermediate(pair["input"])
                        counter_program = family.counterfactual_program()
                        outputs, runtime = family.execute(counter_program, [pair["input"]])
                        if outputs[0] == pair["output"]:
                            raise RuntimeError("wrong-intermediate counterfactual did not change final output")
                        witness = {"input": pair["input"], "settings": job["settings"],
                                   "program": episode["program_solution"], "output": pair["output"],
                                   "counterfactual_program": counter_program, "counterfactual_output": outputs[0],
                                   "intermediate_value": intermediate, "ablation": "wrong_intermediate", "racket": runtime,
                                   "scope": "Protected label evidence; the qualification-bound native witness is built separately."}
                        write_json(out / "counterfactual.private.json", witness)
                        original = family.components(pair["input"])
                        largest = max(map(len, original), default=0)
                        original_winners = [sorted(map(list, p)) for p in original if len(p) == largest]
                        summary["rank_inversion"] = {**intermediate, "original_maximum_cell_sets": original_winners,
                                                     "wrong_intermediate_output_differs": True,
                                                     "interpretation": "Reflected pixels join fragments within each side; the divider separates the sides. Original component ranking selects different final painted cells."}
                        summary["counterfactual_successes"] += 1
                        views.append({"title": "Seed 0, first alternate demonstration: recompute after closure",
                                      "grids": [("Input", pair["input"]), ("Completed", intermediate["completed_grid"]),
                                                ("Final", pair["output"]), ("Original-component selection", outputs[0])]})
                    if mode == "largest_after" and seed == 17:
                        pair = episode["test"][3]
                        views.append({"title": "Substantial 30 × 30 query (private labels)",
                                      "grids": [("Input", pair["input"]), ("Completed", family.intermediate(pair["input"])["completed_grid"]),
                                                ("Final", pair["output"])]})
                except Exception as error:
                    summary["episode_failures"] += 1
                    summary["failures"].append({"job": job, "error": f"{type(error).__name__}: {error}",
                                                "traceback": traceback.format_exc()})
                # Preserve successful lessons and useful failure reports even on later failure.
                write_json(out / "episodes.private.json", episodes)
                write_json(out / "index.private.json", index)
                write_json(out / "summary.private.json", summary)
        if sources() != before:
            raise RuntimeError("task sources changed during audit; evidence cannot bind current source")
        if summary["episode_successes"] != 6 or summary["episode_failures"] or summary["counterfactual_successes"] != 1:
            raise RuntimeError("bounded audit incomplete; inspect retained failures")
        write_html(out / "inspection.private.html", views)
        summary["status"] = "passed"
    except Exception as error:
        summary["status"] = "failed"
        summary["failures"].append({"stage": "audit", "error": f"{type(error).__name__}: {error}",
                                    "traceback": traceback.format_exc()})
    write_json(out / "summary.private.json", summary)
    print(json.dumps({"status": summary["status"], "episode_successes": summary["episode_successes"],
                      "episode_failures": summary["episode_failures"], "summary": str(out / "summary.private.json")}))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
