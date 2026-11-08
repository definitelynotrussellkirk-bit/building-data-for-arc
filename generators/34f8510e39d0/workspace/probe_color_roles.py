#!/usr/bin/env python3
"""Finite CPU audit of geometry/color confounding; generated labels use a mirror.

Run from a repository or copy this file anywhere inside its staged runtime:
  python3 probe_color_roles.py --seeds 0,1,7,99 --indices 8 --out report.json

The portable reviewer_support helper supplies canonical labels. This program
never imports a private runner, loads a predecessor checkout, or executes Racket.
Use the recorded public apply command to obtain source-bound Racket receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys

# Repository direct execution and staged runtime execution use the same helper.
for ancestor in Path(__file__).resolve().parents:
    for directory in (ancestor, ancestor / "shared" / "runtime"):
        if (directory / "reviewer_support.py").is_file():
            sys.path.insert(0, str(directory))
            break
    else:
        continue
    break
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "34f8510e39d0"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def load_generator(root, source=None):
    if source is None:
        candidates = (root / "generators" / TASK_ID / "generator.py",
                      root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
        source = next((p for p in candidates if p.is_file()), None)
    if source is None or not source.is_file():
        raise FileNotFoundError(f"Selected generator missing under {root}")
    runtime = root / "shared" / "runtime"
    sys.path.insert(0, str(runtime if runtime.is_dir() else root))
    spec = importlib.util.spec_from_file_location("color_role_probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source.resolve()


def rectangles(grid):
    """Extract solid rectangles without consulting generator object helpers."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in remaining and grid[cell[0]][cell[1]] == color:
                    remaining.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        rs, cs = zip(*cells)
        box = min(rs), min(cs), max(rs), max(cs)
        shape = box[2] - box[0] + 1, box[3] - box[1] + 1
        if len(cells) == shape[0] * shape[1]:
            result.append({"color": color, "box": box, "shape": shape, "area": len(cells)})
    return result


def size_rival(grid):
    """Outline all solid nonzero rectangles, thickness>=2 and area>=6."""
    out = [row[:] for row in grid]
    for rect in rectangles(grid):
        if min(rect["shape"]) < 2 or rect["area"] < 6:
            continue
        r0, c0, r1, c1 = rect["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = 8
    return out


def matched_roles(grid):
    rects = rectangles(grid)
    targets = [rect for rect in rects if rect["color"] == 3]
    if not targets:
        return []
    largest = max(rect["area"] for rect in targets)
    return [(target, distractor) for target in targets if target["area"] == largest
            for distractor in rects if distractor["color"] not in (0, 3, 8)
            and target["shape"] == distractor["shape"]]


def swap_roles(grid, target, distractor):
    swapped = [row[:] for row in grid]
    for color, rect in ((distractor["color"], target), (3, distractor)):
        r0, c0, r1, c1 = rect["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                swapped[r][c] = color
    return swapped


def source_identity(root, generator, source):
    ledger = canonical_path(root)
    rules = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rule = row.get("program_solution")
                if not isinstance(rule, str) or not rule.strip():
                    raise ValueError("Selected canonical variant has no executable program_solution")
                rules.append({"source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
                              "normalized_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
                              "text": rule})
    return {"generator_path": str(source),
            "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "generator_version": generator.VERSION, "declared_rule_hash": generator.RULE_HASH,
            "probe_path": str(Path(__file__).resolve()),
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "canonical_ledger_path": str(ledger),
            "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
            "canonical_rules": rules}


def witness_record(gen, name, grid):
    return {"name": name, "input": grid, "input_sha256": digest(grid),
            "self_check_errors": gen.self_check(grid),
            "strict_canonical_like_errors": gen.strict_canonical_like(grid),
            "python_mirror_prediction": gen.rule_mirror(grid),
            "size_rival_prediction": size_rival(grid)}


def scan(gen, root, source, *, seeds, indices, bands, all_profiles):
    pairs = canonical_pairs(TASK_ID, root=root)
    canonical = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                  "input_sha256": digest(p["input"]),
                  "size_rival_matches_label": size_rival(p["input"]) == p["output"],
                  "python_mirror_matches_label": gen.rule_mirror(p["input"]) == p["output"]} for p in pairs]
    rows, first_grid, first_matched_grid = [], None, None
    groups = {}
    profiles = list(gen.PROFILE_NAMES) if all_profiles else [None]
    for band in bands:
        for profile in profiles:
            group = Counter()
            for seed in seeds:
                for index in range(indices):
                    override = {"scene_profile": profile} if profile is not None else {}
                    grid = gen.generate(seed, index, difficulty=band, **override)
                    if first_grid is None:
                        first_grid = grid
                    matches = matched_roles(grid)
                    if matches and first_matched_grid is None:
                        first_matched_grid = grid
                    agreement = size_rival(grid) == gen.rule_mirror(grid)
                    lawful = not gen.self_check(grid) and not gen.strict_canonical_like(grid)
                    group.update(draws=1, matched_geometry_draws=bool(matches),
                                 matched_distractors=len({tuple(d["box"]) for _, d in matches}),
                                 size_rival_agreements=agreement, size_rival_refutations=not agreement,
                                 unlawful_draws=not lawful)
                    rows.append({"band": band, "requested_profile": profile, "seed": seed,
                                 "sample_index": index, "observed_profile": gen.observe_overrides(grid)["scene_profile"],
                                 "input_sha256": digest(grid), "matched_role_pairs": len(matches),
                                 "size_rival_agrees_with_python_mirror": agreement, "lawful": lawful})
            group["unique_inputs"] = len({r["input_sha256"] for r in rows if r["band"] == band and r["requested_profile"] == profile})
            groups[f"{band}/{profile or 'default_schedule'}"] = dict(group)
    # Two isolated 3x3 rectangles are the smallest interior-bearing matched
    # role witness in this grammar. Its dimensions are intentionally outside
    # the five canonical scene profiles; self_check remains the lawful check.
    minimal = [[3, 3, 3, 0, 5, 5, 5] for _ in range(3)]
    target, distractor = matched_roles(minimal)[0]
    witnesses = [witness_record(gen, "minimal_matched_roles", minimal),
                 witness_record(gen, "minimal_role_swap", swap_roles(minimal, target, distractor)),
                 witness_record(gen, "first_generated", first_grid)]
    if first_matched_grid is not None:
        target, distractor = matched_roles(first_matched_grid)[0]
        witnesses.extend([witness_record(gen, "first_generated_matched_roles", first_matched_grid),
                          witness_record(gen, "first_generated_role_swap", swap_roles(first_matched_grid, target, distractor))])
    return {"schema": "34f8510e39d0-color-role-probe-v1", "task_id": TASK_ID,
            "label_authority": {"canonical_pairs": "portable canonical ledger labels",
                                "generated_and_counterfactual_outputs": "Python mirror predictions; not Racket authority receipts"},
            "scope": "Finite sampled input support, not universal identifiability or an intake gate",
            "sources": source_identity(root, gen, source),
            "replay": {"seeds": seeds, "sample_indices": list(range(indices)), "bands": bands, "all_profiles": all_profiles},
            "canonical": {"labeled_pairs": len(canonical),
                          "size_rival_matches": sum(p["size_rival_matches_label"] for p in canonical), "pairs": canonical},
            "summary": {"draws": len(rows), "unique_inputs": len({r["input_sha256"] for r in rows}),
                        "matched_geometry_draws": sum(bool(r["matched_role_pairs"]) for r in rows),
                        "size_rival_agreements": sum(r["size_rival_agrees_with_python_mirror"] for r in rows),
                        "size_rival_refutations": sum(not r["size_rival_agrees_with_python_mirror"] for r in rows),
                        "unlawful_draws": sum(not r["lawful"] for r in rows)},
            "per_band_profile": groups, "draws": rows, "witnesses": witnesses}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", default="0,1,7,99", help="comma-separated integer seeds")
    parser.add_argument("--indices", type=int, default=8, help="consecutive sample indices starting at zero")
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--all-profiles", action="store_true", help="cross every explicit profile with each seed/index/band")
    parser.add_argument("--generator-source", type=Path, help="explicit retained generator snapshot, otherwise selected source")
    parser.add_argument("--out", type=Path, required=True, help="new report file")
    parser.add_argument("--witness-inputs", type=Path, help="new input-only JSON for the public Racket apply command")
    args = parser.parse_args()
    if args.indices < 1:
        parser.error("--indices must be positive")
    seeds = [int(s) for s in args.seeds.split(",")]
    bands = args.bands.split(",")
    if not seeds or any(b not in ("easy", "medium", "hard") for b in bands):
        parser.error("seeds must be nonempty and bands must be easy,medium,hard")
    if args.witness_inputs is not None and args.out.resolve() == args.witness_inputs.resolve():
        parser.error("--out and --witness-inputs must resolve to distinct destinations")
    for path in (args.out, args.witness_inputs):
        if path is not None and path.exists():
            parser.error(f"refusing to overwrite {path}")
    root = find_root(__file__)
    gen, source = load_generator(root, args.generator_source)
    report = scan(gen, root, source, seeds=seeds, indices=args.indices, bands=bands, all_profiles=args.all_profiles)
    if args.witness_inputs:
        args.witness_inputs.parent.mkdir(parents=True, exist_ok=True)
        args.witness_inputs.write_text(json.dumps({"inputs": [w["input"] for w in report["witnesses"]]}, indent=2) + "\n")
        report["racket_verification"] = {
            "status": "not_run_by_this_probe", "witness_inputs_path": str(args.witness_inputs.resolve()),
            "witness_inputs_sha256": hashlib.sha256(args.witness_inputs.read_bytes()).hexdigest(),
            "input_order": [w["name"] for w in report["witnesses"]],
            "public_command_from_repository": "PYTHONPATH=src python3 -m arcpuzzles apply " + TASK_ID + " --reference canonical --input " + shlex.quote(str(args.witness_inputs.resolve())) + " --out NEW_RACKET_RECEIPT.json",
            "packet_note": "Run this public command through the packet's review.py run wrapper with its configured Racket environment."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(args.out.resolve()), "canonical": report["canonical"]["size_rival_matches"], "summary": report["summary"]}))


if __name__ == "__main__":
    main()
