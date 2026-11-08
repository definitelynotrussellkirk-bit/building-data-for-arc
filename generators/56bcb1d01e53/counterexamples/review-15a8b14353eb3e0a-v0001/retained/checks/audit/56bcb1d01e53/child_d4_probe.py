#!/usr/bin/env python3
"""Bounded C4-versus-D4 shortcut probe. No Racket execution is performed."""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "56bcb1d01e53"
SOURCE_SHA256 = "7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d"
AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2] / "repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"
CANONICAL = ROOT / "shared/data/base/solutions/training/f8cc533f__56bcb1d01e53.json"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256, "source changed"
sys.path.insert(0, str(ROOT / "shared/runtime"))
spec = importlib.util.spec_from_file_location("child_d4_review_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def d4_rival(grid):
    """Use all square rotations/reflections; retain the other canonical branches."""
    h, w = len(grid), len(grid[0])
    bg = gen._background(grid)
    output = [row[:] for row in grid]
    iround = gen._iround
    for cluster in gen._clusters(grid, bg):
        rs, cs = zip(*cluster)
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        square = bh == bw
        cri, cci = iround((r1 + r2) / 2.0), iround((c1 + c2) / 2.0)
        if square:
            sr1, sr2, sc1, sc2 = r1, r2, c1, c2
        else:
            row_radius = max(cri - r1, r2 - cri)
            col_radius = max(cci - c1, c2 - cci)
            sr1, sr2 = max(0, cri - row_radius), min(h - 1, cri + row_radius)
            sc1, sc2 = max(0, cci - col_radius), min(w - 1, cci + col_radius)
        cr = (r1 + r2) / 2.0 if square else cri
        cc = (c1 + c2) / 2.0 if square else cci
        for r in range(sr1, sr2 + 1):
            for c in range(sc1, sc2 + 1):
                if output[r][c] != bg:
                    continue
                if square:
                    partners = (
                        (iround(cr + (c - cc)), iround(cc - (r - cr))),
                        (iround(cr - (r - cr)), iround(cc - (c - cc))),
                        (iround(cr - (c - cc)), iround(cc + (r - cr))),
                        (r, iround(2 * cc - c)),
                        (iround(2 * cr - r), c),
                        (iround(cr + (c - cc)), iround(cc + (r - cr))),
                        (iround(cr - (c - cc)), iround(cc - (r - cr))),
                    )
                else:
                    partners = (
                        (r, iround(2 * cc - c)),
                        (iround(2 * cr - r), c),
                        (iround(2 * cr - r), iround(2 * cc - c)),
                    )
                value = next((grid[rr][cc2] for rr, cc2 in partners
                              if 0 <= rr < h and 0 <= cc2 < w
                              and grid[rr][cc2] != bg), None)
                if value is not None:
                    output[r][c] = value
        if square and bh % 2 == 1 and output[cri][cci] == bg:
            fill = grid[cluster[0][0]][cluster[0][1]]

            def painted(rr, cc2):
                return (sr1 <= rr <= sr2 and sc1 <= cc2 <= sc2
                        and output[rr][cc2] == fill)

            cardinal = (cri > sr1 and cri < sr2 and cci > sc1 and cci < sc2
                        and painted(cri, cci - 1) and painted(cri, cci + 1)
                        and painted(cri - 1, cci) and painted(cri + 1, cci))
            diagonal = (bh >= 7 and bw >= 7
                        and painted(cri - 1, cci - 1) and painted(cri - 1, cci + 1)
                        and painted(cri + 1, cci - 1) and painted(cri + 1, cci + 1)
                        and painted(sr1, cci) and painted(sr2, cci)
                        and painted(cri, sc1) and painted(cri, sc2))
            if cardinal or diagonal:
                output[cri][cci] = fill
    return output


def grid_digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def differences(first, second):
    return [[r, c, first[r][c], second[r][c]]
            for r in range(len(first)) for c in range(len(first[0]))
            if first[r][c] != second[r][c]]


def main():
    outcomes = []
    for name, (size, cells) in gen._TEMPLATES.items():
        for code in range(8):
            for top, left in ((2, 2), (2, 3), (3, 2), (3, 3)):
                grid = [[1] * 12 for _ in range(12)]
                for r, c in gen._transform(cells, size, code):
                    grid[top + r][left + c] = 2
                mirror, rival = gen.rule_mirror(grid), d4_rival(grid)
                outcomes.append({"template": name, "transform": code,
                                 "origin": [top, left], "mirror_equal": mirror == rival,
                                 "differences": differences(mirror, rival)})
    data = json.loads(CANONICAL.read_text())
    pairs = [(f"train[{i}]", pair["input"], pair["output"])
             for i, pair in enumerate(data["visible_context"]["train"])]
    test_inputs = data["visible_context"]["test_inputs"]
    test_outputs = data["verification"]["expected_test_outputs"]
    assert len(test_inputs) == len(test_outputs) == 2
    for i, (item, output) in enumerate(zip(test_inputs, test_outputs)):
        grid = item["input"] if isinstance(item, dict) else item
        pairs.append((f"test[{i}]", grid, output))
    assert len(pairs) == 5
    canonical_results = []
    for label, grid, output in pairs:
        mirror, rival = gen.rule_mirror(grid), d4_rival(grid)
        canonical_results.append({"label": label, "input_sha256": grid_digest(grid),
                                  "output_sha256": grid_digest(output),
                                  "mirror_matches_stored_label": mirror == output,
                                  "rival_matches_stored_label": rival == output,
                                  "rival_differences": differences(output, rival)})
    cross = {(2, c) for c in range(5)} | {(r, 2) for r in range(5)}
    wing = {(0, 1), (1, 4), (4, 3), (3, 0)}
    cells = (cross | wing) - {(1, 4)}
    witness = [[1] * 11 for _ in range(11)]
    for r, c in cells:
        witness[3 + r][3 + c] = 2
    mirror, rival = gen.rule_mirror(witness), d4_rival(witness)
    evidence = {
        "task_id": TASK, "source_sha256": SOURCE_SHA256,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_source_sha256": hashlib.sha256(CANONICAL.read_bytes()).hexdigest(),
        "execution_status": {"racket_executed": False,
                             "note": "Predictions use the inspected Python mirror and exact rival below. Canonical comparisons use the five stored labels. A separate authority witness execution is pending in the parent audit."},
        "rival": {"name": "square_dihedral_closure", "function": "d4_rival",
                  "source": inspect.getsource(d4_rival)},
        "template_comparison": {"case_count": len(outcomes),
                                "agreement_count": sum(item["mirror_equal"] for item in outcomes),
                                "outcomes": outcomes},
        "canonical_five_pairs": canonical_results,
        "support_argument": "Every generated square is an orientation of odd5, center5, bridge5, or even6; each C4 completion is already D4-invariant. The rival leaves the rectangular branch unchanged. Unique icon colors and the packing gaps prevent cross-icon interactions. All eight orientations and four origin parity combinations were checked for each of the five templates.",
        "witness": {"canvas": [11, 11], "background": 1, "foreground": 2,
                    "origin": [3, 3], "relative_foreground_cells": sorted(map(list, cells)),
                    "self_check_errors": gen.self_check(witness), "input": witness,
                    "rule_mirror_output": mirror, "d4_rival_output": rival,
                    "mirror_additions": differences(witness, mirror),
                    "rival_extra_cells": differences(mirror, rival)},
    }
    assert len(outcomes) == 160 and all(item["mirror_equal"] for item in outcomes)
    assert all(item["mirror_matches_stored_label"] for item in canonical_results)
    assert not evidence["witness"]["self_check_errors"]
    assert len(evidence["witness"]["rival_extra_cells"]) == 4
    destination = AUDIT / "child-d4-evidence.json"
    destination.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"source_sha256": SOURCE_SHA256, "template_agreements": "160/160",
                      "canonical_rival_agreements": sum(item["rival_matches_stored_label"] for item in canonical_results),
                      "canonical_pairs": len(canonical_results), "witness_self_check": gen.self_check(witness),
                      "witness_rival_extra_cells": evidence["witness"]["rival_extra_cells"],
                      "racket_executed": False, "evidence": str(destination)}))


if __name__ == "__main__":
    main()
