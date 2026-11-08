"""Bounded findings-only audit; call through the packet's run_with_racket.py."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
TASK = "85d3a8e1aa7f"


def dump(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def centerless_rival(g):
    """Choose the most frequent non-7 color excluding the center, then its mean direction.

    Numeric color breaks frequency ties. No use of the input center value.
    This is a distribution shortcut probe, not a claimed reference implementation.
    """
    n = len(g)
    m = n // 2
    counts = Counter(g[r][c] for r in range(n) for c in range(n)
                     if (r, c) != (m, m) and g[r][c] != 7)
    if not counts:
        return [[7] * n for _ in range(n)]
    kc = min(counts, key=lambda c: (-counts[c], c))
    coords = [(r, c) for r in range(n) for c in range(n)
              if (r, c) != (m, m) and g[r][c] == kc]
    dr = -1 if sum(r for r, _ in coords) < m * len(coords) else 1
    dc = -1 if sum(c for _, c in coords) < m * len(coords) else 1
    out = [[7] * n for _ in range(n)]
    for k in range(m + 1):
        out[m + dr * k][m + dc * k] = kc
    return out


def describe(g, mod):
    n = len(g)
    m = n // 2
    kc = g[m][m]
    counts = {name: 0 for name in ("top_left", "top_right", "bottom_left", "bottom_right")}
    cells = []
    axis = 0
    for r in range(n):
        for c in range(n):
            if g[r][c] != kc or (r, c) == (m, m):
                continue
            cells.append((r, c))
            if r == m or c == m:
                axis += 1
            else:
                counts[("top_" if r < m else "bottom_") + ("left" if c < m else "right")] += 1
    normal_domain = (
        n % 2 == 1 and 5 <= n <= 19 and kc != 7 and axis == 0
        and len([v for v in counts.values() if v]) == 1
        and max(counts.values()) >= 4
    )
    return {
        "self_check_errors": mod.self_check(g),
        "dimensions": [n, n],
        "center_color": kc,
        "off_center_key_count": len(cells),
        "key_quadrant_counts": counts,
        "off_center_key_axis_count": axis,
        "normal_single_quadrant_domain": normal_domain,
        "normal_domain_note": "Checks the implementation's actual size range 5..19 and the advertised >=4 key cells in one quadrant; deliberate degenerate textures classified separately.",
        "input_sha256": sha(json.dumps(g, separators=(",", ":")).encode()),
    }


def main():
    source = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target", source)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lines = (REPO / "shared/data/canonical/puzzles.jsonl").read_bytes().splitlines(keepends=True)
    row_bytes = next(line for line in lines if json.loads(line).get("task_id") == TASK)
    row = json.loads(row_bytes)
    (HERE / "canonical_row.jsonl").write_bytes(row_bytes)
    (HERE / "canonical_rule.rkt").write_text(row["program_solution"])
    provenance = {
        "task_id": TASK,
        "generator_path": "repo/generators/85d3a8e1aa7f/generator.py",
        "generator_sha256": sha(source.read_bytes()),
        "generator_version": mod.VERSION,
        "canonical_row_sha256": sha(row_bytes),
        "canonical_rule_sha256": sha(row["program_solution"].encode()),
        "rule_execution": "Outputs must come from the retained public arcpuzzles apply receipt, not this probe.",
    }
    grids = []
    records = []

    def add(label, grid, **kwargs):
        records.append({"input_index": len(grids), "label": label, **kwargs, **describe(grid, mod)})
        grids.append(grid)

    # A balanced two-quadrant input is neither a normal generated quadrant nor
    # any of the three declared degenerate textures.
    split = [[7] * 7 for _ in range(7)]
    for r, c in [(3, 3), (0, 0), (0, 1), (1, 0), (1, 1), (6, 6), (6, 5), (5, 6), (5, 5)]:
        split[r][c] = 1
    add("balanced_two_quadrant_validator_witness", split,
        origin="manual", seed=None, sample_index=None, overrides=None,
        domain_verdict="Violates the stated >=4 key cells in a single quadrant invariant; not empty_quadrant, all_kc, or no_kc. Mean equals center exactly on both axes.")

    overrides = {"grid_n": 7, "key_color": 1, "quadrant_choice": "top_left",
                 "n_key_cells": 15, "n_distractors": 0}
    add("advertised_controls_exceed_quadrant_capacity", mod.generate(0, 0, **overrides),
        origin="generator", seed=0, sample_index=0, difficulty=None, overrides=overrides,
        domain_verdict="Normal single-quadrant input, but asks for 15 off-center key cells using individually advertised valid controls; only 9 fit and no incompatibility is raised.")

    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for index in range(4):
                add(f"default_{band}_{seed}_{index}", mod.generate(seed, index, difficulty=band),
                    origin="generator", seed=seed, sample_index=index, difficulty=band, overrides={},
                    domain_verdict="Default generation; normal domain checked in this record.")

    for split_name in ("train", "test"):
        for index, pair in enumerate(row[split_name]):
            add(f"canonical_{split_name}_{index}", pair["input"], origin="canonical",
                seed=None, sample_index=None, overrides=None, canonical_split=split_name,
                canonical_index=index, canonical_expected_output=pair["output"],
                domain_verdict="Exact retained canonical example.")

    dump("input.json", {"inputs": grids})
    dump("probe_metadata.json", {"provenance": provenance, "cases": records,
        "scope": "36 bounded default draws, 3 exact canonical inputs, 1 manual validator witness and 1 exact-control capacity witness; no battery or repair."})
    dump("rival_outputs.json", {"rival": centerless_rival.__doc__,
          "outputs": [centerless_rival(g) for g in grids]})
    print(json.dumps({"cases": len(grids), "provenance": provenance,
                      "witnesses": records[:2]}, indent=2))


if __name__ == "__main__":
    main()
