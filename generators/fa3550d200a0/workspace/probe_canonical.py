"""Source-bound canonical/support probe using only public reviewer interfaces.

Run through review.py run.  ``run`` writes fresh evidence and invokes the public
``arcpuzzles apply`` CLI; independent Python predictions are diagnostics, never
reference labels.  ``assess`` reads retained inputs/predictions and actual Racket
receipts, so an old run remains auditable after the selected source changes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "fa3550d200a0"
ROOT = find_root(__file__)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def components(grid, diagonal=True):
    seen, result = set(), []
    deltas = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
              if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            seen.add((r, c))
            stack, cells = [(r, c)], []
            while stack:
                point = stack.pop()
                cells.append(point)
                for dr, dc in deltas:
                    rr, cc = point[0] + dr, point[1] + dc
                    if (0 <= rr < len(grid) and 0 <= cc < len(row)
                            and grid[rr][cc] and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            result.append(cells)
    return result


def canvas_data(grid):
    counts = Counter(v for row in grid for v in row if v)
    canvas = counts.most_common(1)[0][0]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == canvas]
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    output = [row[left:right + 1] for row in grid[top:bottom + 1]]
    anchors = {grid[r][c]: (r - top, c - left)
               for r in range(top, bottom + 1) for c in range(left, right + 1)
               if grid[r][c] not in (0, 2, canvas)}
    return canvas, (top, left, bottom, right), output, anchors


def stamp(grid, diagonal=True):
    canvas, (top, left, bottom, right), output, anchors = canvas_data(grid)
    for obj in components(grid, diagonal):
        if all(top <= r <= bottom and left <= c <= right for r, c in obj):
            continue
        markers = [(r, c) for r, c in obj if grid[r][c] not in (0, 2, canvas)]
        if not markers:
            continue
        sr, sc = markers[0]
        if grid[sr][sc] not in anchors:
            continue
        ar, ac = anchors[grid[sr][sc]]
        for r, c in obj:
            rr, cc = ar + r - sr, ac + c - sc
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = grid[r][c]
    return output


def window_rival(grid):
    _canvas, (top, left, bottom, right), output, anchors = canvas_data(grid)
    for r, row in enumerate(grid):
        for c, marker in enumerate(row):
            if top <= r <= bottom and left <= c <= right or marker not in anchors:
                continue
            ar, ac = anchors[marker]
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc, nr, nc = r + dr, c + dc, ar + dr, ac + dc
                    if (0 <= rr < len(grid) and 0 <= cc < len(row) and grid[rr][cc]
                            and 0 <= nr < len(output) and 0 <= nc < len(output[0])):
                        output[nr][nc] = grid[rr][cc]
    return output


def rival_inventory(gen):
    """Use declaration names directly; aliases of one function are one rival."""
    rivals, metadata, seen = {}, {}, {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        declarations = getattr(gen, namespace, {})
        if not isinstance(declarations, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        for name, fn in declarations.items():
            if not callable(fn):
                raise TypeError(f"{namespace}.{name} must be callable")
            alias = f"{namespace}.{name}"
            if id(fn) in seen:
                metadata[seen[id(fn)]]["declaration_aliases"].append(alias)
                continue
            key = name if name not in rivals else alias
            rivals[key] = fn
            seen[id(fn)] = key
            metadata[key] = {"origin": "selected_generator", "declaration_aliases": [alias]}
    if not rivals:
        rivals = {"audit_centered_3x3": window_rival,
                  "audit_four_connected": lambda grid: stamp(grid, False)}
        metadata = {name: {"origin": "independent_probe_no_source_declarations",
                           "declaration_aliases": []} for name in rivals}
    return rivals, metadata


def witnesses():
    radius = [[0] * 24 for _ in range(20)]
    for r in range(4, 10):
        for c in range(1, 7):
            radius[r][c] = 1
    radius[6][3], radius[8][5] = 3, 4
    radius[2][12], radius[2][13], radius[2][14] = 3, 2, 2
    radius[7][12], radius[8][12], radius[9][12] = 2, 4, 2
    diagonal = [[0] * 24 for _ in range(20)]
    for r in range(6, 12):
        for c in range(1, 7):
            diagonal[r][c] = 1
    diagonal[7][2], diagonal[10][5] = 3, 4
    for r, c, marker in ((2, 12, 3), (8, 12, 4), (14, 12, 5)):
        diagonal[r][c], diagonal[r + 1][c + 1] = marker, 2
    return (("radius_two", radius), ("diagonal_only", diagonal))


def profile(grid):
    return (len(grid), len(grid[0]), len({v for row in grid for v in row}))


def boundary_specs(gen, full=False):
    numeric = ("grid_h", "grid_w", "rect_h", "rect_w", "piece_count", "decoy_count")
    endpoints = {}
    for name in numeric:
        match = re.match(r"^(\d+)\.\.(\d+)", str(gen.AXES[name]["valid"]))
        if not match:
            raise ValueError(f"Cannot parse endpoint range for {name}: {gen.AXES[name]}")
        endpoints[name] = tuple(map(int, match.groups()))
    if full:
        for values in itertools.product(*(endpoints[n] for n in numeric),
                                        ("left", "right"), gen.PALETTE_KINDS):
            yield dict(zip((*numeric, "canvas_side", "palette_kind"), values))
    else:
        for index in range(16):
            yield {"grid_h": endpoints["grid_h"][bool(index & 1)],
                   "grid_w": endpoints["grid_w"][bool(index & 2)],
                   "rect_h": endpoints["rect_h"][bool(index & 4)],
                   "rect_w": endpoints["rect_w"][bool(index & 8)],
                   "piece_count": endpoints["piece_count"][bool(index & 1)],
                   "decoy_count": endpoints["decoy_count"][bool(index & 2)],
                   "canvas_side": "right" if index & 4 else "left",
                   "palette_kind": gen.PALETTE_KINDS[index % len(gen.PALETTE_KINDS)]}
        if endpoints["grid_h"][0] <= 20 <= endpoints["grid_h"][1] and endpoints["grid_w"][0] <= 20 <= endpoints["grid_w"][1]:
            for side, palette, rect_h, rect_w in itertools.product(
                    ("left", "right"), gen.PALETTE_KINDS, (6,), (6, 10)):
                yield dict(grid_h=20, grid_w=20, rect_h=rect_h, rect_w=rect_w,
                           piece_count=5, decoy_count=1, canvas_side=side, palette_kind=palette)


def declared_incompatibility(gen, overrides):
    """Interpret this task's explicit joint contract independently of generate."""
    for statement in getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", []):
        if statement.startswith("rect_w > grid_w - 10:"):
            if overrides["rect_w"] > overrides["grid_w"] - 10:
                return statement
        else:
            raise ValueError(f"Unrecognized declared incompatibility: {statement}")
    return None


def boundary_cpu(out):
    """Exhaust endpoint combinations plus advertised 20x20/30x30 interiors.

    This phase checks Python generation/domain/observable controls, not labels.
    It records every replay specification, hash, failure and declared rejection.
    """
    out.mkdir(parents=True, exist_ok=False)
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    body = source.read_bytes()
    assert sha(body) == digest
    (out / "generator-source.py").write_bytes(body)
    (out / "probe-source.py").write_bytes(Path(__file__).read_bytes())
    rivals, rival_meta = rival_inventory(gen)
    specs = list(boundary_specs(gen, full=True))
    first = specs[0]
    endpoints = {name: sorted({s[name] for s in specs})
                 for name in ("grid_h", "grid_w", "rect_h", "rect_w", "piece_count", "decoy_count")}
    for size in (20, 30):
        if (min(endpoints["grid_h"]) <= size <= max(endpoints["grid_h"])
                and min(endpoints["grid_w"]) <= size <= max(endpoints["grid_w"])):
            for values in itertools.product(endpoints["rect_h"], endpoints["rect_w"],
                                            endpoints["piece_count"], endpoints["decoy_count"],
                                            ("left", "right"), gen.PALETTE_KINDS):
                specs.append({**first, "grid_h": size, "grid_w": size,
                              **dict(zip(("rect_h", "rect_w", "piece_count", "decoy_count", "canvas_side", "palette_kind"), values))})
    specs = list({json.dumps(s, sort_keys=True): s for s in specs}.values())
    rows = []
    for index, overrides in enumerate(specs):
        incompatibility = declared_incompatibility(gen, overrides)
        record = {"seed": 90210, "sample_index": index, "difficulty": "hard",
                  "overrides": overrides, "declared_incompatibility": incompatibility}
        try:
            grid = gen.generate(90210, index, difficulty="hard", **overrides)
            observed = gen.observe_overrides(grid)
            mismatched = [k for k, v in overrides.items()
                          if type(observed.get(k)) is not type(v) or observed.get(k) != v]
            errors = gen.self_check(grid)
            reference_diagnostic = stamp(grid)
            record.update(input_sha256=grid_hash(grid), profile=profile(grid),
                          observed_axes=observed, self_check=errors, mismatch_axes=mismatched,
                          diagnostic_rivals_differ={n: fn(deepcopy(grid)) != reference_diagnostic for n, fn in rivals.items()},
                          status="unexpected_accept" if incompatibility else "failed" if errors or mismatched else "generated_exact")
        except Exception as exc:
            record.update(error=repr(exc), exception_type=type(exc).__name__,
                          status="declared_incompatible_rejected" if incompatibility and isinstance(exc, ValueError) else "unexpected_error")
        rows.append(record)
    status_counts = Counter(r["status"] for r in rows)
    failed = [r for r in rows if r["status"] not in ("generated_exact", "declared_incompatible_rejected")]
    report = {"schema": "fa3550d200a0-boundary-cpu-v1", "task_id": TASK,
              "generator_sha256": digest, "probe_sha256": sha(Path(__file__).read_bytes()),
              "rival_inventory": rival_meta, "declared_incompatibilities": getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", []),
              "status": "completed_with_failures" if failed else "completed",
              "scope": "512 exact endpoint tuples plus distinct advertised 20x20 and 30x30 tuples; one seed/index per tuple, Python diagnostic only",
              "tuple_count": len(rows), "status_counts": status_counts,
              "unique_generated_inputs": len({r["input_sha256"] for r in rows if "input_sha256" in r}),
              "size_counts": {str(k): v for k, v in Counter((r["overrides"]["grid_h"], r["overrides"]["grid_w"], r["status"]) for r in rows).items()},
              "failures": failed, "rows": rows}
    write_json(out / "assessment.json", report)
    write_json(out / "command.json", {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv], "exit_code": int(bool(failed))})
    print(json.dumps({k: report[k] for k in ("status", "generator_sha256", "tuple_count", "status_counts", "unique_generated_inputs", "size_counts")}), flush=True)
    return int(bool(failed))


def prepare(out, per_band=4, boundaries="smoke"):
    out.mkdir(parents=True, exist_ok=False)
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    body = source.read_bytes()
    assert sha(body) == digest, "Selected source changed during preparation"
    (out / "generator-source.py").write_bytes(body)
    (out / "probe-source.py").write_bytes(Path(__file__).read_bytes())
    rivals, rival_meta = rival_inventory(gen)
    cases, failures, declared_rejections = [], [], []

    def add(grid, kind, **meta):
        errors = gen.self_check(grid)
        predictions = {}
        for name, fn in rivals.items():
            try:
                predictions[name] = {"output": fn(deepcopy(grid)), "error": None}
            except Exception as exc:
                predictions[name] = {"output": None, "error": repr(exc)}
        observed = gen.observe_overrides(grid) if not errors else None
        cases.append({"index": len(cases), "kind": kind, "input": grid,
                      "input_sha256": grid_hash(grid), "profile": profile(grid),
                      "self_check": errors, "observed_axes": observed,
                      "diagnostic_stamp": stamp(grid), "rivals": predictions, **meta})

    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    for pair in canonical:
        add(pair["input"], "canonical", canonical_output=pair["output"],
            identity={k: pair[k] for k in ("variant", "split", "pair_index")})
    for seed, band in enumerate(("easy", "medium", "hard")):
        for index in range(per_band):
            spec = dict(seed=seed, sample_index=index, difficulty=band, overrides={})
            try:
                add(gen.generate(seed, index, difficulty=band), "generated", generated=spec)
            except Exception as exc:
                failures.append({"kind": "generated", "generated": spec, "error": repr(exc)})
    if boundaries != "none":
        for index, overrides in enumerate(boundary_specs(gen, full=boundaries == "full")):
            spec = dict(seed=90210, sample_index=index, difficulty="hard", overrides=overrides)
            incompatibility = declared_incompatibility(gen, overrides)
            try:
                add(gen.generate(90210, index, difficulty="hard", **overrides), "boundary", generated=spec)
                if incompatibility:
                    failures.append({"kind": "unexpected_boundary_accept", "generated": spec, "declared_incompatibility": incompatibility})
                cases[-1]["overrides_exact"] = all(
                    type(cases[-1]["observed_axes"].get(k)) is type(v)
                    and cases[-1]["observed_axes"].get(k) == v for k, v in overrides.items())
            except Exception as exc:
                row = {"kind": "boundary", "generated": spec, "error": repr(exc), "declared_incompatibility": incompatibility}
                (declared_rejections if incompatibility and isinstance(exc, ValueError) else failures).append(row)
    for name, grid in witnesses():
        add(grid, "handmade", witness=name)
    raw_rules = [json.loads(line)["program_solution"] for line in canonical_path(ROOT).open()
                 if json.loads(line).get("task_id") == TASK]
    record = {"schema": "fa3550d200a0-canonical-probe-v1", "task_id": TASK,
              "generator_sha256": digest, "generator_version": gen.VERSION,
              "probe_sha256": sha(Path(__file__).read_bytes()), "declared_rule_hash": gen.RULE_HASH,
              "canonical_rule_text_sha256": sorted({sha(r.encode()) for r in raw_rules}),
              "rival_inventory": rival_meta, "per_band_requested": per_band,
              "boundary_scope": boundaries, "generation_failures": failures,
              "declared_boundary_rejections": declared_rejections,
              "cases": cases}
    write_json(out / "prepared.json", record)
    for start in range(0, len(cases), 64):
        write_json(out / f"input-{start // 64:03d}.json", {"inputs": [c["input"] for c in cases[start:start + 64]]})
    print(json.dumps({"prepared": len(cases), "failures": len(failures), "source": digest}), flush=True)
    return record


def assess(out):
    prepared = json.loads((out / "prepared.json").read_text())
    results, receipts = [], []
    for path in sorted(out.glob("racket-*.json")):
        receipt = json.loads(path.read_text())
        assert receipt["generator_sha256"] == prepared["generator_sha256"]
        assert receipt["rule_hash_matches_catalog"] is True
        assert receipt["executed_rule_hash"] == prepared["declared_rule_hash"]
        results.extend(receipt["results"])
        receipts.append({"path": path.name, "sha256": sha(path.read_bytes()),
                         "rule_hash": receipt["executed_rule_hash"],
                         "callable_text_sha256": receipt["rule_text_sha256"]})
    assert len(results) == len(prepared["cases"]), "Missing Racket results"
    rows = []
    for case, actual in zip(prepared["cases"], results):
        assert actual["input"] == case["input"], "Receipt order or input mismatch"
        output = actual["output"]
        rows.append({"index": case["index"], "kind": case["kind"],
                     "input_sha256": case["input_sha256"], "profile": case["profile"],
                     "self_check": case["self_check"], "racket_error": actual["error"],
                     "racket_valid": actual["error"] is None and output is not None,
                     "diagnostic_matches": case["diagnostic_stamp"] == output,
                     "canonical_matches": case.get("canonical_output") == output if case["kind"] == "canonical" else None,
                     "overrides_exact": case.get("overrides_exact"),
                     "rival_matches": {n: p["error"] is None and p["output"] == output
                                       for n, p in case["rivals"].items()},
                     "rival_errors": {n: p["error"] for n, p in case["rivals"].items() if p["error"]}})
    groups = {}
    for kind in ("canonical", "generated", "boundary", "handmade"):
        group = [r for r in rows if r["kind"] == kind]
        groups[kind] = {"appearances": len(group), "unique_inputs": len({r["input_sha256"] for r in group}),
                        "validator_accepted": sum(not r["self_check"] for r in group),
                        "racket_valid": sum(r["racket_valid"] for r in group),
                        "canonical_matches": sum(r["canonical_matches"] is True for r in group),
                        "diagnostic_matches": sum(r["diagnostic_matches"] for r in group),
                        "override_exact": sum(r["overrides_exact"] is True for r in group),
                        "rival_matches": {n: sum(r["rival_matches"][n] for r in group)
                                          for n in prepared["rival_inventory"]},
                        "unique_rival_refutations": {n: len({r["input_sha256"] for r in group if not r["rival_matches"][n]})
                                                     for n in prepared["rival_inventory"]}}
    canonical_profiles = {tuple(c["profile"]) for c in prepared["cases"] if c["kind"] == "canonical"}
    bands = {}
    for band in ("easy", "medium", "hard"):
        selected = [c for c in prepared["cases"] if c["kind"] == "generated" and c["generated"]["difficulty"] == band]
        bands[band] = {"count": len(selected),
                       "exact_profile_hits": sum(tuple(c["profile"]) in canonical_profiles for c in selected),
                       "envelope_hits": sum(all(min(p[i] for p in canonical_profiles) <= c["profile"][i] <= max(p[i] for p in canonical_profiles)
                                                for i in range(3)) for c in selected),
                       "profile_counts": {str(k): v for k, v in Counter(tuple(c["profile"]) for c in selected).items()}}
    failures = list(prepared["generation_failures"])
    failures += [{"case_index": r["index"], "row": r} for r in rows
                 if not r["racket_valid"] or not r["diagnostic_matches"] or r["self_check"]
                 or r["canonical_matches"] is False or r["overrides_exact"] is False or r["rival_errors"]]
    report = {"schema": "fa3550d200a0-canonical-assessment-v1", "task_id": TASK,
              "generator_sha256": prepared["generator_sha256"], "probe_sha256": prepared["probe_sha256"],
              "assessment_probe_sha256": sha(Path(__file__).read_bytes()),
              "rival_inventory": prepared["rival_inventory"], "canonical_profiles": sorted(canonical_profiles),
              "groups": groups, "per_band": bands, "racket_receipts": receipts,
              "declared_boundary_rejections": prepared.get("declared_boundary_rejections", []),
              "failures": failures, "rows": rows,
              "status": "completed_with_failures" if failures else "completed",
              "claim_scope": "Finite actual-Racket input checks; not a complete lesson census or proof of universal induction."}
    write_json(out / "assessment.json", report)
    print(json.dumps({k: report[k] for k in ("status", "generator_sha256", "groups", "canonical_profiles", "per_band")}), flush=True)
    return int(bool(failures))


def run(out, per_band, boundaries):
    prepare(out, per_band, boundaries)
    commands = []
    for input_path in sorted(out.glob("input-*.json")):
        output_path = out / input_path.name.replace("input-", "racket-")
        argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
                "--input", str(input_path), "--out", str(output_path),
                "--check-generator-domain", "--timeout", "600"]
        completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        log = output_path.with_suffix(".log")
        log.write_text(completed.stdout + completed.stderr)
        commands.append({"argv": argv, "cwd": str(ROOT), "exit_code": completed.returncode,
                         "receipt": str(output_path), "log": str(log)})
        write_json(out / "commands.json", commands)
        if completed.returncode:
            print(completed.stdout + completed.stderr, flush=True)
            return completed.returncode
    return assess(out)


def lesson_rival_assessment(episode, rivals):
    """Each query is judged against demonstrations alone, independently."""
    demos, queries = episode["train"], episode["test"]
    rows, errors = {}, []
    for name, fn in rivals.items():
        predictions = []
        for index, pair in enumerate(demos + queries):
            try:
                predictions.append(fn(deepcopy(pair["input"])))
            except Exception as exc:
                predictions.append(None)
                errors.append({"rival": name, "pair_index": index, "error": repr(exc)})
        refutations = [i for i, pair in enumerate(demos) if predictions[i] != pair["output"]]
        fit = not refutations
        rows[name] = {"demonstration_refuting_indices": refutations, "fits_all_demonstrations": fit,
                      "queries": [{"query_index": i, "rival_output": predictions[len(demos) + i],
                                   "matches_reference": predictions[len(demos) + i] == pair["output"],
                                   "status": "refuted_by_demonstrations" if not fit else
                                             "survived_on_query" if predictions[len(demos) + i] == pair["output"] else "ambiguous"}
                                  for i, pair in enumerate(queries)]}
    return rows, errors


def four_query(out, seed=17):
    out.mkdir(parents=True, exist_ok=False)
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    body = source.read_bytes()
    assert sha(body) == digest
    (out / "generator-source.py").write_bytes(body)
    (out / "probe-source.py").write_bytes(Path(__file__).read_bytes())
    commands = []

    def execute(argv, log_name):
        completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        (out / log_name).write_text(completed.stdout + completed.stderr)
        commands.append({"argv": argv, "cwd": str(ROOT), "exit_code": completed.returncode, "log": log_name})
        write_json(out / "commands.json", commands)
        if completed.returncode:
            print(completed.stdout + completed.stderr, flush=True)
        return completed.returncode

    episode_path = out / "episode.jsonl"
    argv = [sys.executable, "-m", "arcpuzzles", "generate", TASK, "--count", "1",
            "--seed", str(seed), "--test", "4", "--allow-unapproved", "--out", str(episode_path)]
    if code := execute(argv, "generate.log"):
        return code
    episodes = [json.loads(line) for line in episode_path.read_text().splitlines() if line.strip()]
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode["provenance"]["generator_sha256"] == digest
    assert episode["executed_rule_hash"] == gen.RULE_HASH
    assert len(episode["test"]) == 4
    all_pairs = episode["train"] + episode["test"]
    write_json(out / "input.json", {"inputs": [p["input"] for p in all_pairs]})
    argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK, "--input", str(out / "input.json"),
            "--out", str(out / "racket.json"), "--check-generator-domain", "--timeout", "600"]
    if code := execute(argv, "apply.log"):
        return code
    receipt = json.loads((out / "racket.json").read_text())
    assert receipt["generator_sha256"] == digest
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["executed_rule_hash"] == gen.RULE_HASH
    assert len(receipt["results"]) == len(all_pairs)
    labels = []
    for index, (pair, actual) in enumerate(zip(all_pairs, receipt["results"])):
        labels.append({"pair_index": index, "split": "train" if index < len(episode["train"]) else "test",
                       "input_sha256": grid_hash(pair["input"]), "self_check": gen.self_check(pair["input"]),
                       "receipt_input_matches": pair["input"] == actual["input"],
                       "racket_error": actual["error"], "racket_label_matches": pair["output"] == actual["output"],
                       "independent_diagnostic_matches": stamp(pair["input"]) == actual["output"]})
    rivals, inventory = rival_inventory(gen)
    rival_rows, errors = lesson_rival_assessment(episode, rivals)
    demo_hashes = {grid_hash(p["input"]) for p in episode["train"]}
    query_hashes = {grid_hash(p["input"]) for p in episode["test"]}
    query_results = [{"query_index": i, "input_sha256": grid_hash(pair["input"]),
                      "ambiguous_rivals": [n for n, row in rival_rows.items() if row["queries"][i]["status"] == "ambiguous"],
                      "demonstration_only_check": True}
                     for i, pair in enumerate(episode["test"])]
    passed = (len(query_hashes) == 4 and not demo_hashes & query_hashes and not errors
              and all(not r["ambiguous_rivals"] for r in query_results)
              and all(not r["self_check"] and r["receipt_input_matches"] and r["racket_error"] is None
                      and r["racket_label_matches"] and r["independent_diagnostic_matches"] for r in labels))
    report = {"schema": "fa3550d200a0-four-query-v1", "task_id": TASK,
              "generator_sha256": digest, "probe_sha256": sha(Path(__file__).read_bytes()),
              "seed": seed, "status": "completed" if passed else "completed_with_failures",
              "demo_count": len(episode["train"]), "query_count": len(episode["test"]),
              "unique_demo_inputs": len(demo_hashes), "unique_query_inputs": len(query_hashes),
              "unique_all_inputs": len(demo_hashes | query_hashes), "demo_query_overlap": sorted(demo_hashes & query_hashes),
              "executed_rule_hash": receipt["executed_rule_hash"], "racket_receipt_sha256": sha((out / "racket.json").read_bytes()),
              "episode_sha256": sha(episode_path.read_bytes()), "demonstration_policy": episode["provenance"].get("demonstration_policy"),
              "sampling": episode.get("sampling"), "rival_inventory": inventory,
              "rivals": rival_rows, "rival_errors": errors, "per_query": query_results, "labels": labels,
              "limits": "One production episode at seed17. Every rival check uses only the original demonstrations. Query rotations and universal identifiability are not established."}
    write_json(out / "assessment.json", report)
    print(json.dumps({k: report[k] for k in ("status", "generator_sha256", "demo_count", "query_count", "unique_demo_inputs", "unique_query_inputs", "unique_all_inputs", "per_query")}), flush=True)
    return int(not passed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "assess", "run", "boundary-cpu", "four-query"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=4)
    parser.add_argument("--boundaries", choices=("smoke", "full", "none"), default="smoke")
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.phase == "four-query":
        raise SystemExit(four_query(out, args.seed))
    elif args.phase == "boundary-cpu":
        raise SystemExit(boundary_cpu(out))
    elif args.phase == "prepare":
        prepare(out, args.per_band, args.boundaries)
    elif args.phase == "assess":
        raise SystemExit(assess(out))
    else:
        raise SystemExit(run(out, args.per_band, args.boundaries))
