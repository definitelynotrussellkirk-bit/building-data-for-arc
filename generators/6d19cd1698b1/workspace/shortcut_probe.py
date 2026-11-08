"""Source-bound, Racket-labelled rival-rule census for task 6d19cd1698b1.

Run from the packet root (the wrapper changes directory into repo):
  python3 run_with_racket.py python3 generators/6d19cd1698b1/workspace/shortcut_probe.py \
      --out ../checks/shortcut-after.json --cases-out ../checks/shortcut-after.jsonl

Use --generator to compare a frozen baseline without editing or importing it as
selected source. Exit 1 means a verification failure; --require-refuted also
fails when either structural rival survives the default-draw census.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
from typing import Callable

TASK_ID = "6d19cd1698b1"
Grid = list[list[int]]


def runs_in_row(row: list[int]):
    c = 0
    while c < len(row):
        if row[c] == 0:
            c += 1
            continue
        start, color = c, row[c]
        while c + 1 < len(row) and row[c + 1] == color:
            c += 1
        yield start, c, color
        c += 1


def color_envelope(grid: Grid) -> Grid:
    """Rival: only expand the outermost extent of each color in each row."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}, key=row.index):
            positions = [c for c, v in enumerate(row) if v == color]
            for c in (positions[0] - 1, positions[-1] + 1):
                if 0 <= c < len(row) and row[c] == 0:
                    out[r][c] = color
    return out


def _filtered_runs(grid: Grid, keep: Callable[[int, int, int], bool]) -> Grid:
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for i, (start, end, color) in enumerate(runs_in_row(row)):
            if keep(i, start, end):
                for c in (start - 1, end + 1):
                    if 0 <= c < len(row) and row[c] == 0:
                        out[r][c] = color
    return out


def first_two_runs(grid: Grid) -> Grid:
    return _filtered_runs(grid, lambda i, start, end: i < 2)


def ignore_singletons(grid: Grid) -> Grid:
    return _filtered_runs(grid, lambda i, start, end: end > start)


RIVALS = {"color_envelope": color_envelope, "first_two_runs": first_two_runs,
          "ignore_singletons": ignore_singletons}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path):
    name = "shortcut_generator_" + digest(path.read_bytes())[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def racket_literal(value) -> str:
    if isinstance(value, list):
        return "(" + " ".join(racket_literal(x) for x in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"Not an ARC cell: {value!r}")
    return str(value)


def find_repo(explicit: Path | None) -> Path:
    candidates = [explicit.resolve()] if explicit else [Path.cwd(), *Path(__file__).resolve().parents]
    for path in candidates:
        if (path / "catalog/puzzles.jsonl").is_file():
            return path
    raise ValueError("Cannot locate ARCpuzzles repository; pass --repo PATH")


def census(args) -> dict:
    repo = find_repo(args.repo)
    # The source layout deliberately separates shared/tools from shared/runtime.
    # Use the repository's own relocatable staging API rather than path shims.
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-rival-probe-") as directory:
        prepare_runtime(Catalog(repo), Path(directory), TASK_ID)
        sys.path.insert(0, directory)
        try:
            return _census(args, repo)
        finally:
            sys.path.remove(directory)


def _census(args, repo) -> dict:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    source = (args.generator or repo / f"generators/{TASK_ID}/generator.py").resolve()
    gen = load_module(source)
    if gen.TASK_ID != TASK_ID:
        raise ValueError(f"This rival suite is task-specific: expected {TASK_ID}")
    rows = [json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").open()
            if f'"{TASK_ID}"' in line]
    rows = [row for row in rows if row.get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError(f"Expected one canonical authority, got {len(rows)}")
    canonical = rows[0]
    report = {"schema": "arcpuzzles-rival-census-v1", "task_id": TASK_ID,
              "generator_sha256": digest(source.read_bytes()), "version": gen.VERSION,
              "canonical_row_sha256": digest(json.dumps(canonical, sort_keys=True).encode()),
              "rule_hash": digest(" ".join(canonical["program_solution"].split()).encode())[:12],
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "plan": {"default_seeds": args.seeds, "sample_index": 0,
                       "bands": [None, "easy", "medium", "hard"], "boundary_seeds": 8,
                       "boundaries": [[3, 7], [10, 14]], "profiles": list(gen.SCENE_PROFILES)},
              "generated": 0, "canonical_pairs": 0, "mirror_mismatches": 0,
              "canonical_mismatches": 0, "errors": [], "groups": {}, "witnesses": {}}
    records = []
    for split in ("train", "test"):
        for i, pair in enumerate(canonical[split]):
            records.append({"kind": "canonical", "split": split, "index": i,
                            "input": pair["input"], "stored_output": pair["output"]})
    for band in (None, "easy", "medium", "hard"):
        plans = [("default", seed, {}) for seed in range(args.seeds)]
        plans += [("boundary", seed, {"grid_h": h, "grid_w": w, "scene_profile": profile})
                  for h, w in ((3, 7), (10, 14)) for profile in gen.SCENE_PROFILES
                  for seed in range(8)]
        for kind, seed, overrides in plans:
            context = {"kind": kind, "difficulty": band, "seed": seed,
                       "sample_index": 0, "overrides": overrides}
            try:
                grid = gen.generate(seed, 0, difficulty=band, **overrides)
                original = copy.deepcopy(grid)
                errors = gen.self_check(grid, difficulty=band, meta={"overrides": overrides})
                if errors:
                    raise ValueError(f"self_check: {errors}")
                if grid != original:
                    raise AssertionError("self_check mutated its input")
                if grid != gen.generate(seed, 0, difficulty=band, **overrides):
                    raise AssertionError("deterministic replay failed")
                context.update(input=grid, observed=gen.observe_overrides(grid))
                records.append(context)
            except Exception as exc:
                report["errors"].append({**context, "error": f"{type(exc).__name__}: {exc}"})
    cases_file = None
    if args.cases_out:
        args.cases_out.parent.mkdir(parents=True, exist_ok=True)
        cases_file = args.cases_out.open("w", encoding="utf-8")
    try:
        with RacketBridge() as bridge:
            bridge.eval_text(f"(define probe-rule {wrap_rule(canonical['program_solution'])})")
            for offset in range(0, len(records), 32):
                batch = records[offset:offset + 32]
                outputs = bridge.eval_text(f"(map probe-rule '{racket_literal([r['input'] for r in batch])})")
                if not isinstance(outputs, list) or len(outputs) != len(batch):
                    raise ValueError("Racket batch returned an unexpected shape")
                for record, out in zip(batch, outputs):
                    grid = record["input"]
                    original = copy.deepcopy(grid)
                    mirror = gen.rule_mirror(grid)
                    if grid != original:
                        report["errors"].append({"kind": "mirror_mutation", **record})
                    report["mirror_mismatches"] += mirror != out
                    disagreement = {name: rival(grid) != out for name, rival in RIVALS.items()}
                    group = report["groups"].setdefault(record["kind"],
                        {"count": 0, "refutations": {key: 0 for key in RIVALS}, "profiles": Counter()})
                    group["count"] += 1
                    for name, differs in disagreement.items():
                        group["refutations"][name] += differs
                        if differs and name not in report["witnesses"]:
                            report["witnesses"][name] = {**record, "output": out,
                                                        "rival_output": RIVALS[name](grid)}
                    if record["kind"] == "canonical":
                        report["canonical_pairs"] += 1
                        report["canonical_mismatches"] += out != record["stored_output"]
                    else:
                        report["generated"] += 1
                        group["profiles"][record["observed"]["scene_profile"]] += 1
                    if cases_file:
                        cases_file.write(json.dumps({**record, "output": out,
                                                     "rival_disagrees": disagreement}, sort_keys=True) + "\n")
            # Exhaustive local-rule parity is deliberately separate from the
            # calibrated generator domain. It does not admit these grids.
            total = mismatches = 0
            if args.exhaustive_width:
                product = itertools.product((0, 2, 5), repeat=args.exhaustive_width)
                while True:
                    grids = [[list(row)] for row in itertools.islice(product, 32)]
                    if not grids:
                        break
                    outputs = bridge.eval_text(f"(map probe-rule '{racket_literal(grids)})")
                    total += len(grids)
                    mismatches += sum(gen.rule_mirror(grid) != out for grid, out in zip(grids, outputs))
            report["exhaustive_local_parity"] = {"palette": [0, 2, 5], "width": args.exhaustive_width,
                                                  "cases": total, "mismatches": mismatches,
                                                  "scope": "oracle/mirror only, not generator admission"}
    finally:
        if cases_file:
            cases_file.close()
    if args.cases_out:
        report["cases_sha256"] = digest(args.cases_out.read_bytes())
    report["passed_verification"] = not (report["errors"] or report["mirror_mismatches"]
        or report["canonical_mismatches"] or report["exhaustive_local_parity"]["mismatches"])
    report["structural_rivals_refuted_by_defaults"] = all(
        report["groups"]["default"]["refutations"][name] > 0
        for name in ("color_envelope", "first_two_runs"))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases-out", type=Path)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--exhaustive-width", type=int, default=7)
    parser.add_argument("--require-refuted", action="store_true")
    args = parser.parse_args()
    if args.seeds < 1 or not 0 <= args.exhaustive_width <= 8:
        parser.error("--seeds must be positive; --exhaustive-width must be 0..8 (0 disables)")
    report = census(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("version", "generated", "groups",
                         "passed_verification", "structural_rivals_refuted_by_defaults")}, indent=2))
    return int(not report["passed_verification"] or
               (args.require_refuted and not report["structural_rivals_refuted_by_defaults"]))


if __name__ == "__main__":
    raise SystemExit(main())
