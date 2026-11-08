"""Findings-only, exact-source audit of endpoint recoloring and count controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.runtime import ApplyFailure, run_process
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "2361d6aa42c3"
EXPECTED_GENERATOR = "76dd4a9a4bb29446987896c36a8ec0a9eb2d3a5189b73d10ee0b48c63d6ee129"
EXPECTED_RULE = "228316915add4f78b2ef4269e0a618dc0c87f1043f9eaeba8c90ae0f11c78978"
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component, todo = [start], [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in DELTAS:
                other = (r + dr, c + dc)
                if other in remaining:
                    remaining.remove(other)
                    component.append(other)
                    todo.append(other)
        result.append(sorted(component))
    return result


def straight_stroke_end_rival(grid):
    """Recolor a green cell if either axis has exactly one green neighbor.

    This matches degree-one endpoints on separated straight segments, but also
    marks bends and some branch junctions. These predictions are a rival only;
    no Python function supplies reference labels.
    """
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]

    def green(r, c):
        return 0 <= r < h and 0 <= c < w and grid[r][c] == 3

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 3 and (green(r, c - 1) + green(r, c + 1) == 1
                               or green(r - 1, c) + green(r + 1, c) == 1):
                result[r][c] = 2
    return result


def small_runtime_apply(root, out, program, grids, generator_sha):
    """Copy only the documented wrapper, parser, and bridge dependencies.

    The public Catalog.apply path stages the full mapped authoring data and
    exhausted this workspace's disk. This fallback executes the same unchanged
    bridge/wrap_rule source in a small temporary layout and records every copy.
    """
    request_path = out / "label-request.json"
    write_json(request_path, {"program": program, "inputs": grids})
    with tempfile.TemporaryDirectory(prefix=f"audit-{TASK}-small-runtime-") as temp:
        runtime = Path(temp)
        copies = []
        arc = root / "shared/runtime/arc_repl"
        for source in arc.rglob("*"):
            if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                copies.append((source, Path("arc_repl") / source.relative_to(arc)))
        for name in ("__init__.py", "base.py", "rule_wrap.py"):
            copies.append((root / "shared/runtime/puzzle_generators" / name,
                           Path("puzzle_generators") / name))
        copies.append((root / "shared/tools/comment_solutions.py", Path("scripts/comment_solutions.py")))
        manifest = []
        for source, relative in copies:
            target = runtime / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            manifest.append({"source": str(source.relative_to(root)), "runtime_path": str(relative),
                             "sha256": digest(target.read_bytes()), "bytes": target.stat().st_size})
        write_json(out / "small-runtime-manifest.json", manifest)
        command = [sys.executable, str(Path(__file__).with_name("label_worker.py")), str(request_path)]
        run = run_process(command, runtime, timeout=120, extra_env={"PYTHONPATH": str(runtime)})
        write_json(out / "label-execution.json", {"command": command, "cwd": str(runtime),
                                                 "request_sha256": digest(request_path.read_bytes()), **run})
    if run["exit_code"] != 0 or run["timed_out"]:
        raise RuntimeError("Small Racket worker failed: " + run["stderr"][-2000:])
    executed = json.loads(run["stdout"])
    return {"schema": "2361d6aa42c3-small-runtime-racket-v1", "generator_sha256": generator_sha,
            "rule_text_sha256": digest(program),
            "rule_hash_matches_catalog": digest(program) == Catalog(root).describe(TASK)["rule_hash"],
            "runtime_identity": executed["runtime_identity"],
            "callable": executed["callable"], "callable_sha256": executed["callable_sha256"],
            "results": [{"input": grid, "output": label}
                        for grid, label in zip(grids, executed["outputs"], strict=True)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--minimal-runtime", action="store_true",
                        help="Use only recorded bridge/wrapper dependencies when full staging exceeds disk")
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source_path, generator_sha = load_selected_generator(TASK, root=root)
    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    rows.append(row)
    if generator_sha != EXPECTED_GENERATOR or len(rows) != 1:
        raise ValueError("Audited generator/canonical identity changed; reassess this probe")
    program = rows[0]["program_solution"]
    if digest(program) != EXPECTED_RULE:
        raise ValueError("Audited canonical rule changed; reassess this probe")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "generator-source.py").write_bytes(source_path.read_bytes())
    (out / "canonical-rule.rkt").write_text(program, encoding="utf-8")
    write_json(out / "canonical-record.json", rows[0])
    cases = []

    def add_case(name, kind, grid, **metadata):
        parts = components(grid)
        cases.append({"name": name, "kind": kind, "input": grid,
                      "self_check_errors": generator.self_check(grid),
                      "component_count": len(parts),
                      "all_components_straight": all(len({r for r, _ in part}) == 1
                                                      or len({c for _, c in part}) == 1
                                                      for part in parts),
                      **metadata})

    for difficulty in ("easy", "medium", "hard"):
        for index in range(4):
            add_case(f"default:{difficulty}:{index}", "default",
                     generator.generate(17, index, difficulty=difficulty),
                     seed=17, sample_index=index, difficulty=difficulty, overrides={})
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        add_case(f"canonical:{pair['split']}:{pair['pair_index']}", "canonical", pair["input"],
                 variant=pair["variant"], split=pair["split"], pair_index=pair["pair_index"],
                 canonical_expected=pair["output"])
    add_case("small-L", "lawful_handmade",
             [[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 0, 0], [0, 0, 0, 0]],
             domain_basis="4x4 integer ARC grid, colors 0/3, a cardinally connected bent path; bends occur in canonical examples")
    for requested in (7, 8):
        overrides = {"grid_h": 13, "grid_w": 13, "n_segments": requested}
        add_case(f"count-request:{requested}", "override",
                 generator.generate(17, 0, difficulty="hard", **overrides),
                 seed=17, sample_index=0, difficulty="hard", overrides=overrides,
                 requested_segments=requested, maximum_separated_parallel_segments=7,
                 requested_count_jointly_feasible=(requested <= 7))
    write_json(out / "inputs.json", cases)
    if args.minimal_runtime:
        applied = small_runtime_apply(root, out, program, [case["input"] for case in cases], generator_sha)
    else:
        try:
            applied = Catalog(root).apply(TASK, [case["input"] for case in cases],
                                          reference="canonical", check_generator_domain=True,
                                          timeout=120)
        except ApplyFailure as exc:
            write_json(out / "racket-failure.json", exc.run)
            raise
    write_json(out / "racket.json", applied)
    if applied["generator_sha256"] != EXPECTED_GENERATOR:
        raise RuntimeError("Reference execution used a different generator source")
    for case, execution in zip(cases, applied["results"], strict=True):
        reference = execution["output"]
        if reference is None:
            raise RuntimeError(f"Reference execution rejected {case['name']}: {execution}")
        rival = straight_stroke_end_rival(case["input"])
        case.update(reference_output=reference, rival_output=rival,
                    rival_matches_reference=(rival == reference),
                    disagreement_cells=[{"row": r, "column": c,
                                         "reference": reference[r][c], "rival": rival[r][c]}
                                        for r in range(len(reference))
                                        for c in range(len(reference[0]))
                                        if reference[r][c] != rival[r][c]])
        if "canonical_expected" in case:
            case["canonical_label_matches_racket"] = reference == case["canonical_expected"]
    write_json(out / "cases.json", cases)
    default = [case for case in cases if case["kind"] == "default"]
    canonical = [case for case in cases if case["kind"] == "canonical"]
    small_l = next(case for case in cases if case["name"] == "small-L")
    count_cases = [case for case in cases if case["kind"] == "override"]
    # A constructed lawful-domain challenge: the demonstrations are ordinary
    # draws; the query is canonical train 0. This is not a generated episode.
    query = next(case for case in canonical if case["split"] == "train" and case["pair_index"] == 0)
    demonstrations = default[:3]
    public = {"train": [{"input": case["input"], "output": case["reference_output"]}
                         for case in demonstrations], "test": [{"input": query["input"]}]}
    write_json(out / "public-shortcut-challenge.json", public)
    witness = {"construction": "Three default easy demonstrations, then canonical train 0 as a lawful-domain query; not a production-generated episode",
               "demonstration_recipes": [{key: case[key] for key in ("seed", "sample_index", "difficulty", "overrides")}
                                         for case in demonstrations],
               "query_canonical_identity": {key: query[key] for key in ("variant", "split", "pair_index")},
               "query_reference_output": query["reference_output"], "query_rival_output": query["rival_output"],
               "query_disagreement_cells": query["disagreement_cells"],
               "rival_fits_all_demonstrations": all(case["rival_matches_reference"] for case in demonstrations),
               "rival_disagrees_on_query": not query["rival_matches_reference"],
               "generator_sha256": generator_sha, "canonical_rule_sha256": EXPECTED_RULE}
    write_json(out / "private-shortcut-witness.json", witness)
    write_json(out / "small-L-counterexample.json", small_l)
    write_json(out / "segment-count-counterexamples.json", count_cases)
    summary = {"schema": "2361d6aa42c3-findings-only-audit-v1", "status": "completed_findings_only",
               "generator_sha256": generator_sha, "canonical_rule_sha256": EXPECTED_RULE,
               "probe_sha256": digest(Path(__file__).read_bytes()),
               "invoking_python_arguments": sys.argv, "effective_cwd": str(Path.cwd()),
               "reference": ("canonical Racket through the included bridge/wrap_rule with a recorded small dependency copy"
                             if args.minimal_runtime else "canonical Racket through Catalog.apply"),
               "python_output_scope": "Rival predictions only; no Python reference labels",
               "label_worker_sha256": digest(Path(__file__).with_name("label_worker.py").read_bytes()),
               "racket_input_count": len(cases), "racket_rule_text_sha256": applied["rule_text_sha256"],
               "racket_hash_matches_catalog": applied["rule_hash_matches_catalog"],
               "sampled_defaults": {"count": len(default), "by_band": dict(Counter(case["difficulty"] for case in default)),
                                     "all_components_straight": sum(case["all_components_straight"] for case in default),
                                     "rival_matches": sum(case["rival_matches_reference"] for case in default),
                                     "self_check_accepted": sum(not case["self_check_errors"] for case in default)},
               "canonical": {"count": len(canonical),
                             "labels_match_racket": sum(case["canonical_label_matches_racket"] for case in canonical),
                             "rival_disagrees": sum(not case["rival_matches_reference"] for case in canonical),
                             "self_check_accepted": sum(not case["self_check_errors"] for case in canonical)},
               "small_L": {"self_check_errors": small_l["self_check_errors"],
                           "rival_disagreement_cells": small_l["disagreement_cells"]},
               "count_controls": [{key: case[key] for key in ("name", "seed", "sample_index", "difficulty", "overrides",
                                                              "requested_segments", "component_count", "self_check_errors",
                                                              "requested_count_jointly_feasible")} for case in count_cases],
               "lawful_domain_witness": {key: witness[key] for key in ("rival_fits_all_demonstrations", "rival_disagrees_on_query")},
               "source_unchanged_after_probe": digest(source_path.read_bytes()) == generator_sha,
               "limits": ["Twelve fixed-seed default draws, three canonical pairs, one hand-made lawful bend, and two explicit overrides; no full battery.",
                          "Straight-only restriction was already recorded against this unchanged source; this is independent bounded confirmation.",
                          "The constructed challenge uses a canonical-domain query, not a query sampled by production generation.",
                          "No actual model training outcome is measured, and no target source or approval state is modified."]}
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
