"""Read-only audit: compare declared overrides and check labels with Racket.

Run `prepare`, then public `arcpuzzles apply` on inputs.json, then `compare`.
No solve artifacts or unassigned source edits are involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK = "3e18c05a8b57"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def crop_color(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    if not cells:
        return [[0]]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [[grid[r][c] if grid[r][c] == color else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def independent_rule(grid):
    h, w = len(grid), len(grid[0])
    seen, symmetric = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color, stack, cells = grid[r][c], [(r, c)], set()
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                cells.add((a, b))
                for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    q = (a + da, b + db)
                    if (0 <= q[0] < h and 0 <= q[1] < w and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        stack.append(q)
            r0, r1 = min(a for a, _ in cells), max(a for a, _ in cells)
            c0, c1 = min(b for _, b in cells), max(b for _, b in cells)
            if all((r0 + r1 - a, c0 + c1 - b) in cells for a, b in cells):
                symmetric.append([[color if (a, b) in cells else 0
                                   for b in range(c0, c1 + 1)]
                                  for a in range(r0, r1 + 1)])
    assert len(symmetric) == 1, len(symmetric)
    return symmetric[0]


def prepare():
    gen, source, source_hash = load_selected_generator(TASK, root=find_root(__file__))
    base = gen.generate(17, 0, difficulty="easy")
    override_rows = []
    for kwargs in ({"palette_size": 4}, {"n_distinct_colors": 4},
                   {"palette_kind": "warm"}, {"palette_kind": "cool"},
                   {"texture": "warm"}, {"texture": "cool"},
                   {"audit_unknown_key": 123}, {"grid_h": 7}, {"grid_h": 14},
                   {"grid_w": 9}, {"grid_w": 16}):
        row = {"seed": 17, "sample_index": 0, "difficulty": "easy", "overrides": kwargs}
        try:
            grid = gen.generate(17, 0, difficulty="easy", **kwargs)
            row.update(accepted=True, identical_to_default=grid == base,
                       colors=sorted({v for line in grid for v in line}),
                       foreground_color_count=len({v for line in grid for v in line} - {0}),
                       self_check=gen.self_check(grid, difficulty="easy"))
        except Exception as exc:
            row.update(accepted=False, exception_type=type(exc).__name__, exception=str(exc))
        override_rows.append(row)
    cases = []
    for pair in canonical_pairs(TASK, root=find_root(__file__)):
        cases.append({"name": f"canonical-v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
                      "input": pair["input"], "canonical_output": pair["output"]})
    for band in ("easy", "medium", "hard"):
        for index in range(6):
            grid = gen.generate(17 + index, index, difficulty=band)
            cases.append({"name": f"generated-{band}-{17 + index}-{index}",
                          "input": grid, "difficulty": band,
                          "self_check": gen.self_check(grid, difficulty=band),
                          "independent_output": independent_rule(grid)})
    report = {"task_id": TASK, "source_sha256": source_hash,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "rule_hash": getattr(gen, "RULE_HASH", None), "declared_axes": gen.AXES,
              "override_probes": override_rows, "default_probe_input": base,
              "scope": "11 exact override probes; all canonical pairs; six fixed draws per difficulty; no target edits."}
    write("observations.json", report)
    write("case_manifest.json", cases)
    write("inputs.json", [c["input"] for c in cases])
    print(json.dumps({"source_sha256": source_hash, "override_probes": override_rows,
                      "racket_inputs": len(cases)}, indent=2))


def compare():
    gen, _, source_hash = load_selected_generator(TASK, root=find_root(__file__))
    original = json.loads((HERE / "observations.json").read_text())
    assert source_hash == original["source_sha256"]
    cases = json.loads((HERE / "case_manifest.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["reference"] == "canonical"
    assert len(cases) == len(receipt["results"])
    rows = []
    for case, result in zip(cases, receipt["results"]):
        assert result["error"] is None and result["valid_output"], result
        expected = case.get("canonical_output", case.get("independent_output"))
        assert expected == result["output"], case["name"]
        rows.append({"name": case["name"], "racket_matches_expected": True,
                     "color2_shortcut_matches": crop_color(case["input"], 2) == result["output"],
                     "self_check": gen.self_check(case["input"], difficulty=case.get("difficulty"))})
    canonical = [r for r in rows if r["name"].startswith("canonical-")]
    generated = [r for r in rows if r["name"].startswith("generated-")]
    witness = next((c for c, r in zip(cases, rows)
                    if c["name"].startswith("generated-") and not r["color2_shortcut_matches"]), None)
    assert all(r["color2_shortcut_matches"] for r in canonical)
    assert witness is not None
    write("color2-counterexample.json", {**witness, "rival_output": crop_color(witness["input"], 2)})
    report = {"task_id": TASK, "source_sha256": source_hash,
              "executed_rule_hash": receipt["executed_rule_hash"],
              "executed_wrapped_callable_sha256": receipt["rule_text_sha256"],
              "racket_results": len(rows), "racket_matches_expected": len(rows),
              "canonical_color2_shortcut_matches": sum(r["color2_shortcut_matches"] for r in canonical),
              "canonical_count": len(canonical),
              "generated_refutes_color2_shortcut": sum(not r["color2_shortcut_matches"] for r in generated),
              "generated_count": len(generated), "cases": rows,
              "finding": "Advertised palette and helpful-texture controls are ignored; advertised dimension endpoints reject. The color-2 canonical shortcut is refuted by generated examples."}
    write("comparison.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "compare"))
    args = parser.parse_args()
    globals()[args.mode]()
