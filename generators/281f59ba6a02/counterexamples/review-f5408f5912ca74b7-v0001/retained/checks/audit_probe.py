"""Findings-only source-bound reproducer for the two immutable audit targets.
Run from packet root: python3 run_with_racket.py python3 ../checks/audit_probe.py
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(grid):
    return [[int(value) for value in row] for row in grid]


def literal(value):
    return "(" + " ".join(literal(x) if isinstance(x, list) else str(x) for x in value) + ")"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def selected_matrix(grid):
    rs = [r for r in range(1, len(grid)) if grid[r][0] == 8]
    cs = [c for c in range(1, len(grid[0])) if grid[0][c] == 8]
    return [[grid[r][c] for c in cs] for r in rs] if rs and cs else [[0]]


def starburst(grid, arm_source):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if not all((grid[r][c], grid[r-1][c], grid[r+1][c], grid[r][c-1], grid[r][c+1])):
                continue
            a, b = grid[r][c], grid[r + arm_source][c]
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if dr == dc == 0:
                        out[nr][nc] = a
                    elif (dr == 0 or dc == 0) and abs(dr) + abs(dc) <= 2:
                        out[nr][nc] = b
                    elif abs(dr) == abs(dc):
                        out[nr][nc] = a
    return out


def main():
    root = Path(__file__).resolve().parents[1]
    repo = root / "repo"
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    targets = json.loads((root / "AUDIT_ASSIGNMENT.json").read_text())["targets"]
    ids = [target["task_id"] for target in targets]
    canonical = {tid: [] for tid in ids}
    for line in (repo / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") in canonical:
            canonical[row["task_id"]].append(row)
    report = {}
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-audit-") as directory:
        prepare_runtime(Catalog(repo), Path(directory), task_ids=ids)
        sys.path.insert(0, directory)
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        with RacketBridge() as bridge:
            for target in targets:
                tid = target["task_id"]
                path = repo / f"generators/{tid}/generator.py"
                assert sha(path) == target["generator_sha256"], "Audit target source drift"
                gen = module(path, "audit_" + tid)
                programs = {row["program_solution"] for row in canonical[tid]}
                assert len(programs) == 1, "Ambiguous reference authority"
                bridge.eval_text(f"(define audit-rule {wrap_rule(next(iter(programs)))})")
                oracle = lambda grid: bridge.eval_text(f"(audit-rule '{literal(grid)})")
                result = {"generator_sha256": sha(path), "canonical": [], "generated": 0,
                          "generated_output_colors": [], "oracle_python_mismatches": 0,
                          "down_arm_rival_mismatches": 0, "generated_selfcheck_failures": 0}
                for variant, row in enumerate(canonical[tid]):
                    for split in ("train", "test"):
                        pairs = row.get(split, [])
                        pairs = [pairs] if isinstance(pairs, dict) else pairs
                        for index, pair in enumerate(pairs):
                            grid, expected = normalize(pair["input"]), normalize(pair["output"])
                            output = oracle(grid)
                            result["canonical"].append({"variant": variant, "split": split, "index": index,
                                 "input": grid, "output": output, "matches_stored": output == expected,
                                 "selfcheck": gen.self_check(grid),
                                 "down_arm_rival_matches": (starburst(grid, 1) == output) if tid == "281f59ba6a02" else None})
                colors = set()
                for band in (None, "easy", "medium", "hard"):
                    for seed in range(32):
                        grid = gen.generate(seed, 0, difficulty=band)
                        output = oracle(grid)
                        result["generated"] += 1
                        result["generated_selfcheck_failures"] += bool(gen.self_check(grid))
                        colors.update(v for row in output for v in row)
                        predicted = selected_matrix(grid) if tid == "3f600d3093b8" else starburst(grid, -1)
                        result["oracle_python_mismatches"] += predicted != output
                        if tid == "281f59ba6a02":
                            result["down_arm_rival_mismatches"] += starburst(grid, 1) != output
                result["generated_output_colors"] = sorted(colors)
                default = gen.generate(0, 0, difficulty="medium")
                if tid == "3f600d3093b8":
                    result["inert_overrides"] = {key: gen.generate(0, 0, difficulty="medium", **{key: value}) == default
                        for key, value in {"palette_kind": "warm", "palette_size": 9, "n_distinct_colors": 9,
                                           "texture": "cool", "surprise_unknown_control": True}.items()}
                    result["rejected_declared_boundary"] = {}
                    for key, value in {"grid_h": 6, "n_row_markers": 6}.items():
                        try:
                            gen.generate(0, 0, difficulty="medium", **{key: value})
                        except Exception as exc:
                            result["rejected_declared_boundary"][key] = f"{type(exc).__name__}: {exc}"
                    try:
                        gen.generate(0, 0, n_row_markers=1)
                    except Exception as exc:
                        result["one_row_override_error"] = str(exc)
                else:
                    requested = {"grid_h": 10, "grid_w": 10, "n_plus": 1, "center_color": 9, "arm_color": 1}
                    actual = gen.generate(0, 0, difficulty="medium", **requested)
                    result["ignored_override_witness"] = {"seed": 0, "sample_index": 0, "difficulty": "medium",
                        "requested": requested, "observed_shape": [len(actual), len(actual[0])],
                        "same_as_unoverridden": actual == default, "input": actual}
                    grid = [[0] * 10 for _ in range(10)]
                    grid[4][4], grid[3][4], grid[5][4], grid[4][3], grid[4][5] = 4, 2, 3, 5, 6
                    output = oracle(grid)
                    result["asymmetric_arm_witness"] = {"input": grid, "output": output,
                        "down_arm_rival_output": starburst(grid, 1), "selfcheck": gen.self_check(grid),
                        "rule_mirror_matches": starburst(grid, -1) == output,
                        "rival_disagrees": starburst(grid, 1) != output,
                        "scope": "canonical-equivalent rival; stress case follows executable oracle, not uniquely inferred from demos"}
                    result["malformed_grid_selfcheck"] = {"color_10_3x3": gen.self_check([[10]*3 for _ in range(3)]),
                                                         "oversize_31x31": gen.self_check([[4]*31 for _ in range(31)])}
                assert all(row["matches_stored"] for row in result["canonical"])
                assert result["oracle_python_mismatches"] == 0
                report[tid] = result
        sys.path.remove(directory)
    out = root / "checks/audit-evidence.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({tid: {k: v for k, v in row.items() if k not in
            {"canonical", "asymmetric_arm_witness", "ignored_override_witness"}} for tid, row in report.items()}, indent=2))


if __name__ == "__main__":
    main()
