"""Replay one source-bound canonical DDA rounding discrepancy, without editing it."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import types

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, load_selected_generator, normalize_grid


TASK = "55ba26e599d3"
GENERATOR_SHA = "9d75ef957334cd4da23262a897308df40322f1f0c6672cfe7171308f640c1372"
AUTHORITY_SHA = "e810f2e5a08105c051b618db2bce8f7ccf699a4b3d55be1ed022cd1ac4ecde50"
PROGRAM_SHA = "bf0d327958300a83e20504a5b60c4f7c42c81e4f0fe54ae0929d071b142abc0c"
RELATIVE_SOURCE = f"generators/{TASK}/generator.py"
OLD = "(round(row1 + index * drow / steps), round(col1 + index * dcol / steps))"
NEW = "(round(row1 + (index / steps) * drow), round(col1 + (index / steps) * dcol))"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK, root=root)
    assert source_sha == GENERATOR_SHA, "Proposal is bound to different generator bytes"
    authority = root / "shared/data/base/solutions/training/bcb3040b__55ba26e599d3.json"
    assert sha(authority.read_bytes()) == AUTHORITY_SHA
    program = json.loads(authority.read_text())["racket_target"]["target_code"]
    assert sha(program.encode()) == PROGRAM_SHA
    source = source_path.read_text()
    assert source.count(OLD) == 1
    proposed_source = source.replace(OLD, NEW)
    patch = "".join(difflib.unified_diff(source.splitlines(keepends=True),
        proposed_source.splitlines(keepends=True),
        fromfile="a/" + RELATIVE_SOURCE, tofile="b/" + RELATIVE_SOURCE))
    assert (Path(__file__).parent / "canonical-arithmetic-order.patch").read_text() == patch
    proposed = types.ModuleType("_rounding_proposal_only")
    proposed.__file__ = str(source_path)
    exec(compile(proposed_source, str(source_path) + " [in-memory proposal]", "exec"),
         proposed.__dict__)
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    cases = []
    try:
        # The smallest canvas covering the known divergent endpoint pair; also
        # check its transpose to cover both interpolated axes without a census.
        for transpose in (False, True):
            grid = [[0] * 23 for _ in range(12)]
            grid[0][0] = grid[11][22] = 2
            grid[3][6] = 1  # Witness the canonical blue-to-green branch too.
            if transpose:
                grid = [list(row) for row in zip(*grid)]
            endpoints = module._endpoints(grid)
            assert module.self_check(grid) == []
            current = module.rule_mirror(grid)
            expected = normalize_grid(apply(program, grid))
            repaired = proposed.rule_mirror(grid)
            assert current != expected, "The pinned production defect did not reproduce"
            assert repaired == expected, "Proposed arithmetic does not match actual Racket"
            differences = [dict(row=r, col=c, current=current[r][c], racket=expected[r][c])
                for r in range(len(grid)) for c in range(len(grid[0]))
                if current[r][c] != expected[r][c]]
            assert len(differences) == 2
            cases.append(dict(name="transpose" if transpose else "shallow",
                input=grid, endpoints=endpoints, divergent_step=15,
                current_path_coordinate=module._line_cells(*endpoints)[15],
                proposed_path_coordinate=proposed._line_cells(*endpoints)[15],
                program=program, racket_output=expected,
                current_python_output=current, proposed_python_output=repaired,
                differing_cells=differences,
                assertions=dict(current_mismatch_reproduced=True, proposed_parity=True)))
    finally:
        bridge.close()
    assert sha(source_path.read_bytes()) == GENERATOR_SHA, "Selected source changed during replay"
    evidence = dict(schema="arcpuzzles-canonical-rounding-proposal-v1", status="proposed",
        source_binding=dict(generator_path=RELATIVE_SOURCE, generator_sha256=source_sha,
            authority_path=authority.relative_to(root).as_posix(), authority_sha256=AUTHORITY_SHA,
            canonical_program_sha256=PROGRAM_SHA,
            proposed_generator_sha256=sha(proposed_source.encode()),
            replay_sha256=sha(Path(__file__).read_bytes()), patch_sha256=sha(patch.encode())),
        racket=identity, cases=cases,
        root_cause="Python multiply-before-divide differs from canonical Racket divide-before-multiply at floating half-step boundaries.",
        limits=["Two bounded fixtures only; no universal parity claim.",
            "Selected generator, canonical authority and approval remain unchanged.",
            "Proposal requires owner integration, source-specific checks and fresh canonical approval."])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(dict(status="proposed", protected_racket=identity["protected"],
        cases=len(cases), current_mismatches=2, proposed_parity_cases=2,
        evidence=str(args.out))))


if __name__ == "__main__":
    main()
