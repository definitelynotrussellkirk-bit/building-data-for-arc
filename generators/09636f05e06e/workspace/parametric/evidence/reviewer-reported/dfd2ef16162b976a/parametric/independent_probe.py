"""Independent finite verification of the proposed zero-line parameter family.

Run from the repository through review.py run. This is evidence tooling, not
label authority or production approval. Every built episode is Racket-labeled.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(Path.cwd())
SOURCE = ROOT / "generators/09636f05e06e/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("independent_zero_line_prototype", SOURCE)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def stated_operation(grid, mode, color):
    active_rows = [any(value == 0 for value in row) for row in grid]
    active_cols = [any(row[col] == 0 for row in grid) for col in range(len(grid[0]))]
    out = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            erase = ((mode in ("both", "rows") and active_rows[row]) or
                     (mode in ("both", "columns") and active_cols[col]))
            if erase and grid[row][col] != color:
                out[row][col] = 0
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    started = time.monotonic()
    rows, unique_inputs, program_hashes = [], set(), set()
    expected_inputs = None
    boundaries = [P.GEN.generate(731, index, grid_h=h, grid_w=w,
                  n_zero_rows=nr, n_zero_cols=nc, palette_size=10, texture="scatter")
                  for index, (h,w,nr,nc) in enumerate([
                      (12,12,2,2), (12,22,2,4), (22,12,4,2), (22,22,4,4)])]
    boundary_checks = 0
    with P.RacketLabeler() as labeler:
        for mode in ("both", "rows", "columns"):
            for color in range(1,10):
                e = P.build_episode(args.seed, n_train=3, n_test=4,
                                    mode=mode, protected_color=color, labeler=labeler)
                pairs = e["train"] + e["test"]
                assert len(e["train"]) == 3 and len(e["test"]) == 4
                inputs = [json.dumps(p["input"], separators=(",", ":")) for p in pairs]
                assert len(set(inputs)) == 7
                if expected_inputs is None:
                    expected_inputs = inputs
                assert inputs == expected_inputs, "hidden settings changed the input distribution"
                unique_inputs.update(inputs)
                for pair in pairs:
                    assert not P.GEN.self_check(pair["input"])
                    assert pair["output"] == stated_operation(pair["input"], mode, color)
                teaching = e["private"]["teaching"]
                assert teaching["parameter_survivors"] == [[mode, color]]
                assert all(q["agreement"] and q["distinct_predictions"] == 1
                           for q in teaching["queries"])
                program = e["private"]["program"]
                digest = hashlib.sha256(program.encode()).hexdigest()
                assert digest == e["private"]["program_sha256"]
                program_hashes.add(digest)
                for grid in boundaries:
                    assert labeler.label(program, grid) == stated_operation(grid, mode, color)
                    boundary_checks += 1
                visible = public_challenge_bytes(e)
                visible_id = public_challenge_id(e)
                assert hashlib.sha256(visible).hexdigest() == visible_id
                projected = json.loads(visible)
                assert set(projected) == {"train", "test"}
                assert all(set(p) == {"input"} for p in projected["test"])
                rows.append({"mode":mode, "protected_color":color,
                             "program_sha256":digest, "program":program, "public_id":visible_id,
                             "train":3, "test":4,
                             "parameter_survivors":teaching["parameter_survivors"],
                             "structural_survivor_count":len(teaching["structural_survivors"]),
                             "queries_agree":len(teaching["queries"]),
                             "input_attempts":[d["attempts"] for d in e["private"]["input_draws"]]})
    assert len(program_hashes) == 27
    report = {"status":"passed", "scope":"finite proposed-prototype verification, no approval",
              "seed":args.seed, "settings_checked":len(rows), "episodes_checked":len(rows),
              "racket_labeled_episode_pairs":sum(r["train"]+r["test"] for r in rows),
              "query_predictions_checked":sum(r["queries_agree"] for r in rows),
              "unique_episode_inputs":len(unique_inputs),
              "paired_comparison":"The same seven inputs are deliberately reused across all27 settings; pair counts are not unique-input counts.",
              "extra_racket_boundary_labels":boundary_checks,
              "boundary_dimensions":[[len(g),len(g[0])] for g in boundaries],
              "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "probe_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "generator_sha256":hashlib.sha256(P.GENERATOR_SOURCE.read_bytes()).hexdigest(),
              "elapsed_seconds":round(time.monotonic()-started,3), "settings":rows,
              "limits":"One controlled seed; 27 parameters and six declared structural rival forms. No completeness, model-learning, all-seed, or training-admission claim."}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k != "settings"},indent=2))


if __name__ == "__main__":
    main()
