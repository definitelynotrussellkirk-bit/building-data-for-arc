"""Reproduce exact-control and clean-diagonal coverage findings without edits."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "eb46daa8881c"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def centers(grid):
    return [(r, c) for r in range(1, len(grid)-1)
            for c in range(1, len(grid[0])-1)
            if grid[r][c] != 0 and all(grid[r+dr][c+dc] == grid[r][c]
                                       for dr, dc in CARDINAL)]


def predict(grid, *, clean_diagonals):
    out = copy.deepcopy(grid)
    for r, c in centers(grid):
        if not clean_diagonals or all(grid[r+dr][c+dc] == 0 for dr, dc in DIAGONALS):
            out[r][c] = 8
    return out


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    pairs = canonical_pairs(TASK, root=ROOT)
    canonical = {"pairs": len(pairs),
                 "intended_mirror_matches": sum(predict(p["input"], clean_diagonals=False) == p["output"] for p in pairs),
                 "clean_diagonal_rival_matches": sum(predict(p["input"], clean_diagonals=True) == p["output"] for p in pairs)}
    counts = {}
    samples = []
    for band in ("easy", "medium", "hard"):
        matches = valid = 0
        for seed in range(100):
            grid = GEN.generate(seed, 0, difficulty=band)
            valid += not GEN.self_check(grid, difficulty=band)
            matches += predict(grid, clean_diagonals=False) == predict(grid, clean_diagonals=True)
            samples.append({"difficulty": band, "seed": seed, "sample_index": 0, "input_sha256": digest(grid)})
        counts[band] = {"draws": 100, "self_check_passed": valid, "rival_agreement_with_python_mirror": matches}

    # Same center+arms, one lawful diagonal distractor. This lies outside the
    # sampler's documented clean-footprint support but its validator accepts it.
    witness = [[0]*5 for _ in range(5)]
    for r, c in [(2,2), (1,2), (3,2), (2,1), (2,3)]:
        witness[r][c] = 4
    witness[1][1] = 6

    ignored = []
    exact_witness = None
    for axis in ("palette_size", "n_distinct_colors"):
        for seed in range(100):
            grid = GEN.generate(seed, 0, difficulty="hard", **{axis: 1})
            observed = len({v for row in grid for v in row} - {0})
            if observed != 1:
                plain = GEN.generate(seed, 0, difficulty="hard")
                ignored.append({"axis": axis, "requested": 1,
                                "observed_nonzero_colors": observed,
                                "seed": seed, "sample_index": 0, "difficulty": "hard",
                                "same_as_no_override": grid == plain,
                                "self_check": GEN.self_check(grid, difficulty="hard"),
                                "input": grid, "input_sha256": digest(grid)})
                exact_witness = grid
                break

    generated = [GEN.generate(17, 0, difficulty=b) for b in ("easy", "medium", "hard")]
    racket_inputs = [witness, *generated, exact_witness]
    (OUT/"racket-inputs.json").write_text(json.dumps(racket_inputs)+"\n")
    record = {"task_id": TASK, "generator_sha256": SOURCE_SHA,
              "canonical": canonical, "default_census": counts,
              "sample_input_hashes": samples,
              "ignored_exact_controls": ignored,
              "diagonal_counterexample": {"input": witness, "input_sha256": digest(witness),
                  "self_check_easy": GEN.self_check(witness, difficulty="easy"),
                  "python_intended_output": predict(witness, clean_diagonals=False),
                  "rival_output": predict(witness, clean_diagonals=True),
                  "support": "validator_accepted; outside documented pure separated-plus default support"},
              "racket_input_roles": ["diagonal_counterexample", "easy_seed17", "medium_seed17", "hard_seed17", "exact_control_counterexample"],
              "limits": ["Census predictions use an independent Python mirror; separate Racket execution verifies retained examples.",
                         "300 finite default draws do not establish exhaustive support or universal identifiability."]}
    (OUT/"probe.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({"canonical": canonical, "default_census": counts,
                      "ignored_exact_controls": [{k:v for k,v in x.items() if k!='input'} for x in ignored],
                      "generator_sha256": SOURCE_SHA}))


if __name__ == "__main__":
    main()
