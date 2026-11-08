from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / "repo"
CHECKS = WORK / "checks" / "audit"


def load(tid):
    path = ROOT / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_" + tid, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod, path, hashlib.sha256(path.read_bytes()).hexdigest()


def terminal_rival(grid, gen):
    key = gen._find_key(grid)
    if key is None:
        return [list(row) for row in grid]
    kr0, kc0, kh = key
    lefts = {grid[kr0 + i][kc0] for i in range(kh)}
    terminal = grid[kr0 + kh - 1][kc0 + 1]
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if kr0 <= r < kr0 + kh and kc0 <= c <= kc0 + 1:
                continue
            if value in lefts:
                out[r][c] = terminal
    return out


def main():
    catalog = Catalog(ROOT)

    tid = "3bf9215de862"
    gen, source, sha = load(tid)
    grid = json.loads((CHECKS / tid / "input.json").read_text())
    apply = catalog.apply(tid, [grid], reference="canonical", timeout=120)
    try:
        gen.generate(1, 0, cmd=5)
        generate_cmd5 = {"accepted": True}
    except Exception as exc:
        generate_cmd5 = {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}
    report = {
        "schema": "audit_probe/1", "task_id": tid, "generator_sha256": sha,
        "advertised_cmd_axis": gen.AXES["cmd"],
        "self_check": gen.self_check(grid),
        "generate_cmd5": generate_cmd5,
        "executed_rule_hash": apply["executed_rule_hash"],
        "rule_hash_matches_catalog": apply["rule_hash_matches_catalog"],
        "racket_output": apply["results"][0]["output"],
        "finding": "cmd=5 is advertised and canonical authority treats non-1/2/3 as right gravity, but generator and validator reject it",
    }
    (CHECKS / tid / "probe.json").write_text(json.dumps(report, indent=2) + "\n")

    tid = "35b257d07d86"
    gen, source, sha = load(tid)
    grids = []
    provenance = []
    for bi, band in enumerate(("easy", "medium", "hard")):
        for index in range(60):
            g = gen.generate(91300 + bi, index, difficulty=band)
            grids.append(g); provenance.append({"band": band, "index": index})
    receipts = [
        catalog.apply(tid, grids[start:start + 64], reference="canonical", timeout=300)
        for start in range(0, len(grids), 64)
    ]
    applied = receipts[0]
    outputs = [row["output"] for receipt in receipts for row in receipt["results"]]
    rivals = [terminal_rival(g, gen) for g in grids]
    matches = [i for i, (a, b) in enumerate(zip(outputs, rivals)) if a == b]
    valid = [i for i, g in enumerate(grids) if not gen.self_check(g)]
    canonical = canonical_pairs(tid, root=ROOT)
    canonical_rivals = [terminal_rival(p["input"], gen) for p in canonical]
    canonical_matches = [i for i, (p, r) in enumerate(zip(canonical, canonical_rivals)) if p["output"] == r]
    differing = next(i for i, (p, r) in enumerate(zip(canonical, canonical_rivals)) if p["output"] != r)
    sample = 0
    report = {
        "schema": "audit_probe/1", "task_id": tid, "generator_sha256": sha,
        "executed_rule_hash": applied["executed_rule_hash"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "generated_cases": len(grids), "self_check_valid_cases": len(valid),
        "terminal_color_rival_matches_generated": len(matches),
        "terminal_color_rival_generated_match_fraction": len(matches) / len(grids),
        "canonical_pairs": len(canonical),
        "terminal_color_rival_matches_canonical": len(canonical_matches),
        "canonical_differing_index": differing,
        "finding": "chain-constructed keys collapse every mapped target to the final right-hand color, so a single-terminal-color shortcut matches generated labels but not the canonical task",
    }
    outdir = CHECKS / tid
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (outdir / "generated_match.json").write_text(json.dumps({
        "provenance": provenance[sample], "input": grids[sample],
        "racket_output": outputs[sample], "terminal_rival": rivals[sample],
        "match": outputs[sample] == rivals[sample],
    }, indent=2) + "\n")
    p = canonical[differing]
    (outdir / "canonical_counterexample.json").write_text(json.dumps({
        "variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
        "input": p["input"], "canonical_output": p["output"],
        "terminal_rival": canonical_rivals[differing],
    }, indent=2) + "\n")
    print(json.dumps({"3bf9215de862": report if False else "see probe.json",
                      "35b257d07d86": report}, indent=2))

if __name__ == "__main__": main()
