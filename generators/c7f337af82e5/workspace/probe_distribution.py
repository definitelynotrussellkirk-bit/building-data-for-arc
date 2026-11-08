"""Finite Python-oracle diagnostics; this neither runs Racket nor grants approval.

Replay every start in the requested finite range and every single-pair holdout.
Windows contain direct consecutive generator draws: production resampling is not
performed here. Use the source-bound public lesson census for that evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

# Resolve helpers only inside this script's own library/copied-runtime ancestry.
_helper_root = next((p for a in Path(__file__).resolve().parents for p in (a, a / "shared/runtime")
                     if (p / "reviewer_support.py").is_file()), None)
if _helper_root is not None:
    sys.path.insert(0, str(_helper_root))
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "c7f337af82e5"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def oracle(grid):
    """Independent four-neighbor traversal and explicit rectangle-domain checks."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("nonempty rectangular integer grid required")
    h, w = len(grid), len(grid[0])
    if grid[0][0] not in (1, 2):
        raise ValueError("missing control")
    if any(type(v) is not int or v not in ({grid[0][0]} if (r, c) == (0, 0) else {0, 7})
           for r, row in enumerate(grid) for c, v in enumerate(row)):
        raise ValueError("unexpected color or non-integer")
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    output, objects = deepcopy(grid), []
    output[0][0] = 0
    while unseen:
        todo = [min(unseen)]
        unseen.remove(todo[0])
        cells = set(todo)
        while todo:
            r, c = todo.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    cells.add(q)
                    todo.append(q)
        rs, cs = zip(*cells)
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        rim = {(r, c) for r, c in box if r in (r0, r1) or c in (c0, c1)}
        hollow = any(grid[r][c] == 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1))
        if cells != box and not (r1 - r0 >= 2 and c1 - c0 >= 2 and cells == rim):
            raise ValueError("component is neither an exact frame nor a filled rectangle")
        selected = (grid[0][0] == 1 and hollow) or (grid[0][0] == 2 and not hollow)
        if selected:
            for r, c in cells:
                output[r][c] = 8
        objects.append({"bbox": [r0, c0, r1, c1], "pixels": len(cells), "bbox_area": len(box),
                        "hollow": hollow, "selected": selected})
    if not 2 <= len(objects) <= 4 or {o["hollow"] for o in objects} != {True, False}:
        raise ValueError("expected 2..4 objects including a frame and a solid")
    return output, objects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if min(args.seeds, args.starts) < 1:
        parser.error("--seeds and --starts must be positive")
    root = find_root(__file__)
    source = next(p for p in (root / "generators" / TASK / "generator.py",
                             root / "puzzle_generators/per_puzzle" / TASK / "generator.py") if p.is_file())
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    spec = importlib.util.spec_from_file_location("distribution_probe_generator", source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    exec(compile(source_bytes, str(source), "exec"), gen.__dict__)
    rivals = {f"{attr}/{name}": fn for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
              for name, fn in getattr(gen, attr, {}).items()}
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    rows = [json.loads(line) for line in canonical_path(root).open()]
    rules = [r["program_solution"] for r in rows if r.get("task_id") == TASK]
    n_train = getattr(gen, "EXAMPLES_NEEDED", 4)
    report = {"schema": "c7f337af82e5-python-distribution-probe-v1", "task_id": TASK,
              "evidence_basis": "independent Python oracle; no Racket execution or production resampling",
              "invocation": {"argv": sys.argv, "cwd": str(Path.cwd())},
              "settings": {"seeds": args.seeds, "starts": args.starts, "n_train": n_train, "n_test": 1},
              "source": {"generator_sha256": source_hash, "declared_rule_hash": getattr(gen, "RULE_HASH", None),
                         "canonical_rule_text_sha256": [hashlib.sha256(s.encode()).hexdigest() for s in rules],
                         "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "canonical": {}, "per_band": {}, "errors": []}
    cache = {}
    def predict(name, grid):
        key = name, digest(grid)
        if key not in cache:
            cache[key] = rivals[name](deepcopy(grid))
        return cache[key]
    for name in rivals:
        try:
            fits = [predict(name, p["input"]) == p["output"] for p in pairs]
            report["canonical"][name] = {"pairs": len(fits), "matches": sum(fits), "fits_all": all(fits), "pair_matches": fits}
            if name.startswith("CANONICAL_SHORTCUTS/") and not all(fits):
                report["errors"].append(f"{name}: claimed canonical shortcut matches only {sum(fits)}/{len(fits)} labeled pairs")
        except Exception as exc:
            report["errors"].append(f"canonical {name}: {type(exc).__name__}: {exc}")
    report["canonical_oracle_matches"] = [oracle(p["input"])[0] == p["output"] for p in pairs]
    if not all(report["canonical_oracle_matches"]):
        report["errors"].append("independent oracle disagrees with canonical labels")
    profiles = {(len(p["input"]), len(p["input"][0]), tuple(sorted({v for r in p["input"] for v in r}))) for p in pairs}
    for band in ("easy", "medium", "hard"):
        counts, schedules, unique = Counter(), Counter(), set()
        stats = {name: {"draws": Counter(), "production": Counter(), "rotations": Counter(), "first_witnesses": {}} for name in rivals}
        records = []
        for seed in range(args.seeds):
            draws = {}
            for index in range(args.starts + n_train):
                try:
                    grid = gen.generate(seed, index, difficulty=band)
                    output, objs = oracle(grid)
                    key = digest(grid)
                    pair = {"input": grid, "output": output, "seed": seed, "sample_index": index, "input_sha256": key}
                    draws[index] = pair
                    unique.add(key)
                    records.append({k: pair[k] for k in ("seed", "sample_index", "input_sha256")})
                    counts.update(["draws", f"control_{grid[0][0]}", f"objects_{len(objs)}", f"selected_{sum(o['selected'] for o in objs)}", f"shape_{len(grid)}x{len(grid[0])}"])
                    counts["canonical_size_palette"] += (len(grid), len(grid[0]), tuple(sorted({v for r in grid for v in r}))) in profiles
                    counts["equal_bbox_area_cross_topology"] += any(a["hollow"] != b["hollow"] and a["bbox_area"] == b["bbox_area"] for a in objs for b in objs)
                    counts["solid_larger_bbox"] += any(not a["hollow"] and b["hollow"] and a["bbox_area"] > b["bbox_area"] for a in objs for b in objs)
                    if callable(getattr(gen, "schedule_profile", None)):
                        schedules[json.dumps(gen.schedule_profile(seed, index, difficulty=band), sort_keys=True, default=str)] += 1
                    for name in rivals:
                        prediction = predict(name, grid)
                        status = "matched" if prediction == output else "refuted"
                        stats[name]["draws"][status] += 1
                        if status == "refuted":
                            stats[name]["first_witnesses"].setdefault("draw_refutation", {**pair, "rival_output": prediction})
                except Exception as exc:
                    counts["draw_errors"] += 1
                    if counts["draw_errors"] <= 3:
                        report["errors"].append(f"{band} seed={seed} index={index}: {type(exc).__name__}: {exc}")
            for start in range(args.starts):
                if any(i not in draws for i in range(start, start + n_train + 1)):
                    counts["incomplete_windows"] += 1
                    continue
                window = [draws[i] for i in range(start, start + n_train + 1)]
                counts["windows"] += 1
                counts["duplicate_input_windows"] += len({p["input_sha256"] for p in window}) != len(window)
                for name in rivals:
                    try:
                        matches = [predict(name, p["input"]) == p["output"] for p in window]
                        for qi in range(n_train + 1):
                            status = "refuted" if any(not m for i, m in enumerate(matches) if i != qi) else ("survived_all" if matches[qi] else "ambiguous")
                            scopes = ("rotations", "production") if qi == n_train else ("rotations",)
                            for scope in scopes:
                                stats[name][scope][status] += 1
                                if status == "ambiguous":
                                    stats[name]["first_witnesses"].setdefault(scope, {"seed": seed, "start": start, "query_position": qi, "pairs": window, "query_rival_output": predict(name, window[qi]["input"])})
                    except Exception as exc:
                        counts["lesson_errors"] += 1
                        if counts["lesson_errors"] <= 3:
                            report["errors"].append(f"{band} seed={seed} start={start} rival={name}: {type(exc).__name__}: {exc}")
        report["per_band"][band] = {"counts": counts, "schedule_counts": schedules, "unique_input_count": len(unique), "unique_input_sha256": sorted(unique), "draw_records": records, "rivals": stats}
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        report["errors"].append("generator source changed while probe was running")
    ambiguous = sum(s[scope]["ambiguous"] for b in report["per_band"].values() for s in b["rivals"].values() for scope in ("production", "rotations"))
    report["status"] = "error" if report["errors"] else ("no_declared_rivals" if not rivals else ("ambiguity_found" if ambiguous else "no_ambiguity_found"))
    report["limits"] = "Finite requested starts only; only declared rivals; direct windows, including recorded duplicates, may differ from production rejection sampling. Python labels are not Racket verification."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "canonical_pairs": len(pairs), "rivals": len(rivals), "per_band": {b: {"counts": v["counts"], "unique_inputs": v["unique_input_count"]} for b, v in report["per_band"].items()}, "errors": report["errors"]}, indent=2))
    return 2 if report["errors"] or not rivals else int(bool(ambiguous))


if __name__ == "__main__":
    raise SystemExit(main())
