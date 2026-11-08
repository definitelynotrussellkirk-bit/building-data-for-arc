"""Bounded, source-bound independent audit; all outputs come from public apply."""
from pathlib import Path
import hashlib
import importlib.util
import itertools
import json
import sys

from puzzle_generators.base import set_ctx_observer

TASK = "857238219e77"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks/audit" / TASK
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def parse(grid):
    runs = []
    for c, column in enumerate(zip(*grid)):
        start = 0
        for color, cells in itertools.groupby(column):
            length = len(list(cells))
            if color:
                runs.append((start, c, length, color))
            start += length
    return runs


def predict(grid, mode="exact"):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for top, col, length, color in parse(grid):
        target = length == 3 and 0 < col < w - 1
        convert = target or (mode == "all_interior" and 0 < col < w - 1) or (mode == "include_edges" and length == 3)
        if convert:
            row = top + length // 2
            for c in range(max(0, col - 1), min(w, col + 2)):
                out[row][c] = color
        elif mode == "preserve_rejected":
            for r in range(top, top + length):
                out[r][col] = color
    return out


def observe(grid):
    h, w = len(grid), len(grid[0])
    runs = parse(grid)
    edge_cols = [c for _, c, length, _ in runs if length == 3 and c in (0, w - 1)]
    result = {"grid_h": h, "grid_w": w,
              "target_count": sum(length == 3 and 0 < c < w - 1 for _, c, length, _ in runs),
              "n_distinct_colors": len({v for row in grid for v in row if v}),
              "edge_side": "left" if edge_cols == [0] else "right" if edge_cols == [w - 1] else None}
    counts = {"short": sum(length == 2 for _, _, length, _ in runs),
              "long": sum(length == 4 for _, _, length, _ in runs), "edge": len(edge_cols)}
    return result, counts


def prepare():
    public = json.loads((OUT / "canonical-task.json").read_text())
    program = public["variants"][0]["program_solution"]
    rows = []
    for vi, variant in enumerate(public["variants"]):
        for split in ("train", "test"):
            pairs = variant[split]
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pi, pair in enumerate(pairs):
                rows.append({"population": "canonical", "variant": vi, "split": split,
                             "pair_index": pi, "grid": pair["input"], "public_output": pair["output"]})
    args = []
    for i, combo in enumerate(itertools.product((6, 15), (8, 17), (1, 5), (2, 4), ("left", "right"))):
        overrides = dict(zip(("grid_h", "grid_w", "target_count", "n_distinct_colors", "edge_side"), combo))
        args.append((i, 7, "medium", overrides))
    for band in ("easy", "medium", "hard"):
        args.extend((seed, seed % 10, band, {}) for seed in range(9))
    args.append((42, 3, "hard", {}))
    for seed, index, difficulty, overrides in args:
        contexts = []
        set_ctx_observer(contexts.append)
        try:
            grid = gen.generate(seed, index, difficulty=difficulty, **overrides)
        finally:
            set_ctx_observer(None)
        ctx = contexts[-1]
        actual, counts = observe(grid)
        rows.append({"population": "generated", "seed": seed, "sample_index": index,
                     "difficulty": difficulty, "overrides": overrides, "grid": grid,
                     "deterministic": grid == gen.generate(seed, index, difficulty=difficulty, **overrides),
                     "independent_observation": actual, "negative_counts": counts,
                     "generator_observation": gen.observe_overrides(grid),
                     "drawn": ctx.recorded_draws(), "consumed": ctx.overrides_used()})
    for row in rows:
        row["input_sha256"] = sha(row["grid"])
        row["self_check"] = gen.self_check(row["grid"])
        row["independent_output"] = predict(row["grid"])
        row["rival_outputs"] = {mode: predict(row["grid"], mode) for mode in
                                ("all_interior", "include_edges", "preserve_rejected")}
    report = {"schema": "bounded-generator-audit-v1", "task_id": TASK,
              "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "selected_rule_hash": public["rule_hash"],
              "selected_rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "grid_denominator": len(rows), "generated_denominator": len(args),
              "canonical_denominator": len(rows) - len(args), "rows": rows}
    (OUT / "input.json").write_text(json.dumps({"inputs": [row["grid"] for row in rows]}, indent=2) + "\n")
    (OUT / "prepared.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, sort_keys=True))


def assess():
    report = json.loads((OUT / "prepared.json").read_text())
    racket = json.loads((OUT / "racket.json").read_text())
    print("Racket keys:", sorted(racket))
    outcomes = [row["output"] for row in racket["results"]]
    if len(outcomes) != len(report["rows"]):
        raise RuntimeError("public apply returned wrong number of labels")
    failures = []
    for result in racket["results"]:
        if result["error"] or not result["valid_output"]:
            failures.append({"index": result["index"], "kind": "racket_execution", "error": result["error"]})
    rival_matches = {mode: {"canonical": 0, "generated": 0} for mode in
                     ("all_interior", "include_edges", "preserve_rejected")}
    for i, (row, actual) in enumerate(zip(report["rows"], outcomes)):
        row["racket_output"] = actual
        row["racket_output_sha256"] = sha(actual)
        if actual != row["independent_output"]:
            failures.append({"index": i, "kind": "reference_parity"})
        if row["self_check"]:
            failures.append({"index": i, "kind": "self_check", "details": row["self_check"]})
        if row["population"] == "canonical" and actual != row["public_output"]:
            failures.append({"index": i, "kind": "canonical_label"})
        if row["population"] == "generated":
            if not row["deterministic"] or row["independent_observation"] != row["generator_observation"]:
                failures.append({"index": i, "kind": "determinism_or_observation"})
            if row["negative_counts"] != {"short": 1, "long": 1, "edge": 1}:
                failures.append({"index": i, "kind": "teaching_negative_support"})
            for name, value in row["overrides"].items():
                if row["independent_observation"][name] != value or row["consumed"].get(name) != value:
                    failures.append({"index": i, "kind": "pinned_axis", "axis": name})
            for name, value in row["independent_observation"].items():
                if row["drawn"].get(name) != value:
                    failures.append({"index": i, "kind": "default_axis", "axis": name})
        for mode, rival in row["rival_outputs"].items():
            rival_matches[mode][row["population"]] += rival == actual
    report["failures"] = failures
    report["rival_matches"] = rival_matches
    report["canonical_program_sha256"] = report["selected_rule_sha256"]
    report["selected_rule_sha256"] = racket["rule_text_sha256"]
    report["public_apply_metadata"] = {k: v for k, v in racket.items() if k != "results"}
    report["racket_receipt_sha256"] = hashlib.sha256((OUT / "racket.json").read_bytes()).hexdigest()
    report["current_source_sha256"] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report["status"] = "no_issue_found" if not failures else "defect_found"
    (OUT / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "failures": failures, "rival_matches": rival_matches}, sort_keys=True))
    return bool(failures)


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    else:
        raise SystemExit(assess())
