"""Bounded self-audit for the aa378df15340 native parametric family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "aa378df15340"


def _load_family():
    path = HERE / "native_family.py"
    spec = importlib.util.spec_from_file_location("audit_native_aa378df15340", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


F = _load_family()


def _paint_segment(out, r, c, value):
    for k in range(c - r + 1):
        out[r + k][c - k] = value


def midpoint_only(grid):
    inter = F.copy_only(grid)
    out = deepcopy(inter)
    n = len(inter)
    for r in range(n):
        for c in range(r + 1, n):
            value = inter[r][c]
            if value == 0 or inter[c][r] != value:
                continue
            d = c - r
            if d % 2 == 0:
                k = d // 2
                out[r + k][c - k] = value
            else:
                k = d // 2
                out[r + k][c - k] = value
                out[r + k + 1][c - k - 1] = value
    return out


def upper_sources_only(grid):
    out = F.copy_only(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and r < c:
                _paint_segment(out, r, c, value)
    return out


def longest_orbits_only(grid):
    out = F.copy_only(grid)
    sources = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    longest = max(abs(c - r) for r, c, _ in sources)
    for r, c, value in sources:
        if abs(c - r) != longest:
            continue
        if r > c:
            r, c = c, r
        _paint_segment(out, r, c, value)
    return out


RIVALS = {
    "copy_only": F.copy_only,
    "midpoint_only": midpoint_only,
    "upper_sources_only": upper_sources_only,
    "longest_orbits_only": longest_orbits_only,
}


def run(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be 1..4096")
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((HERE / "promotion.json").read_text())
    protected_seeds = (0, 17, 313, 997)
    jobs = [
        {"seed": seed, "settings": {"mode": mode}, "demos": 2, "queries": 4}
        for mode in ("copy_only", "copy_then_bridge")
        for seed in protected_seeds
    ]
    protected = evaluate_contract(ROOT, TASK_ID, contract, jobs)

    survivor_rows = []
    pairs_checked = 0
    for seed in range(seed_count):
        canonical = F.generate(seed, {"mode": "copy_only"}, 6, 4)
        sequential = F.generate(seed, {"mode": "copy_then_bridge"}, 6, 4)
        c_pairs = canonical["train"] + canonical["test"]
        s_pairs = sequential["train"] + sequential["test"]
        if [p["input"] for p in c_pairs] != [p["input"] for p in s_pairs]:
            raise AssertionError(f"settings changed inputs at seed {seed}")
        if any(c["output"] == s["output"] for c, s in zip(c_pairs, s_pairs)):
            raise AssertionError(f"settings failed to distinguish a pair at seed {seed}")
        keys = [json.dumps(p["input"], separators=(",", ":")) for p in c_pairs]
        if len(keys) != len(set(keys)):
            raise AssertionError(f"duplicate input at seed {seed}")
        demos = sequential["train"][:2]
        survivors = [
            name for name, rival in RIVALS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
        ]
        if survivors:
            survivor_rows.append({"seed": seed, "survivors": survivors})
        pairs_checked += len(c_pairs) + len(s_pairs)
    if survivor_rows:
        raise AssertionError(f"declared rivals survived: {survivor_rows[:5]}")

    return {
        "schema": "arcpuzzles-bounded-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "episodes_checked": seed_count * 2,
        "pairs_checked": pairs_checked,
        "rivals": sorted(RIVALS),
        "rival_survivors": [],
        "protected_racket": {
            "episodes": len(protected["episodes"]),
            "evaluations": protected["racket_evaluations"],
            "identity": protected["racket"],
        },
        "limits": "Finite seeds and declared rivals only; not a uniqueness proof.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=256)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    report = run(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("task_id", "status", "seed_count", "pairs_checked")}))


if __name__ == "__main__":
    main()
