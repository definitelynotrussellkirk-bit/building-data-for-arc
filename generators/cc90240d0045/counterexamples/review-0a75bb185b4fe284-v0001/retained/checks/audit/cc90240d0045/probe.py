"""Findings-only audit; writes only to this script's audit directory.
Run through the packet's review.py run wrapper from packet_root.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, load_selected_generator
from puzzle_generators.helpers.grid import is_well_formed

TASK = "cc90240d0045"
EXPECTED_SOURCE = "b9229f802a18ae3e23d87a6d4d680b878bc67540b6e09f86735112ff7b9820c0"
OUT = Path(__file__).resolve().parent
ROOT = Path.cwd()


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def ring_reference(grid):
    out = copy.deepcopy(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0 and all(grid[r+dr][c+dc] == 5
                    for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc) != (0,0)):
                out[r][c] = 8
    return out


def cardinal_rival(grid):
    out = copy.deepcopy(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0 and all(grid[r+dr][c+dc] == 5
                    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))):
                out[r][c] = 8
    return out


def call_result(fn):
    try:
        return {"returned": fn()}
    except Exception as exc:
        return {"exception": type(exc).__name__, "message": str(exc)}


def run_probe():
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    assert digest == EXPECTED_SOURCE, (digest, EXPECTED_SOURCE)
    meta = json.loads((OUT / "canonical.json").read_text())
    rule = meta["variants"][0]["program_solution"]
    rule_hash = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert rule_hash == meta["rule_hash"] == "c71519cbcd39"
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical_fits = [cardinal_rival(p["input"]) == p["output"] for p in canonical]
    reference_fits = [ring_reference(p["input"]) == p["output"] for p in canonical]
    count, crashes, check_failures, rival_disagreements = 0, [], [], []
    input_hashes, shapes, ring_counts = set(), Counter(), Counter()
    representative = []
    for band in ("easy", "medium", "hard"):
        for seed in range(100):
            index = seed * 17 + 3
            try:
                grid = gen.generate(seed, index, difficulty=band)
            except Exception as exc:
                crashes.append({"band":band,"seed":seed,"sample_index":index,
                                "exception":type(exc).__name__,"message":str(exc)})
                continue
            count += 1
            errors = gen.self_check(grid)
            if errors:
                check_failures.append({"band":band,"seed":seed,"sample_index":index,"errors":errors})
            reference = ring_reference(grid)
            if cardinal_rival(grid) != reference:
                rival_disagreements.append({"band":band,"seed":seed,"sample_index":index})
            input_hashes.add(hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest())
            shapes[str((len(grid),len(grid[0])))] += 1
            ring_counts[str(sum(a != b for ar,br in zip(grid,reference) for a,b in zip(ar,br)))] += 1
            if seed == 0:
                representative.append({"kind":"generated","band":band,"seed":seed,
                                       "sample_index":index,"input":grid})
    # One complete ring, plus a seven-cell near-ring with its upper-left corner missing.
    witness = [[0]*10 for _ in range(8)]
    perimeter = [(dr,dc) for dr in range(3) for dc in range(3) if (dr,dc) != (1,1)]
    for start_col in (1,6):
        for dr,dc in perimeter:
            witness[1+dr][start_col+dc] = 5
    witness[1][6] = 0
    assert gen.self_check(witness) == []
    assert is_well_formed(witness)
    baseline = gen.generate(17,23,difficulty="medium")
    axes = [
        {"grid_h":5}, {"grid_w":14}, {"ring_count":4},
        {"palette_kind":"warm"}, {"palette_kind":"not-a-profile"},
        {"texture":"warm"}, {"texture":"not-a-profile"},
        {"palette_size":9}, {"position_bias":"overlap"},
        {"n_distinct_colors":4}, {"density":"dense"}, {"unknown_axis":7},
        {"grid_h":8.9}, {"ring_count":True},
    ]
    axis_results = []
    for overrides in axes:
        result = call_result(lambda: gen.generate(17,23,difficulty="medium",**overrides))
        if "returned" in result:
            grid = result.pop("returned")
            result.update({"accepted":True,"identical_to_no_override":grid == baseline,
                           "shape":[len(grid),len(grid[0])],"self_check":gen.self_check(grid)})
        else:
            result["accepted"] = False
        axis_results.append({"overrides":overrides,**result})
    floats = [[float(v) for v in row] for row in witness]
    malformed = [
        {"name":"float_palette_grid","input":floats},
        {"name":"scalar_integer","input":5},
        {"name":"non_row_member","input":[[0],5]},
    ]
    for case in malformed:
        case["self_check"] = call_result(lambda: gen.self_check(case["input"]))
        case["runtime_is_well_formed"] = is_well_formed(case["input"])
    apply_cases = [{"kind":"canonical","canonical_pair_index":i,"input":p["input"]}
                   for i,p in enumerate(canonical)] + representative + [{"kind":"near_ring_witness","input":witness}]
    for case in apply_cases:
        case["python_reference_output"] = ring_reference(case["input"])
        case["rival_output"] = cardinal_rival(case["input"])
    report = {
        "task_id":TASK,"stage":"unchanged_audit_target","generator_source_sha256":digest,
        "generator_version":gen.VERSION,"source_path":str(source),"selected_rule_hash":rule_hash,
        "rule_text_sha256":hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_labeled_pairs":len(canonical),"canonical_rival_fits":canonical_fits,
        "canonical_python_reference_fits":reference_fits,
        "census":{"bands":["easy","medium","hard"],"seed_range_inclusive":[0,99],
                  "sample_index_formula":"seed * 17 + 3","requested_draws":300,"returned_draws":count,
                  "crashes":crashes,"self_check_failures":check_failures,"unique_inputs":len(input_hashes),
                  "shape_counts":dict(shapes),"ring_count_counts":dict(ring_counts),
                  "rival_disagreements_against_python_reference":rival_disagreements,
                  "authority_limit":"Only the listed apply_cases are submitted to independent Racket; the full census uses the local explicit eight-neighbor Python reference."},
        "witness":{"self_check":gen.self_check(witness),"runtime_is_well_formed":is_well_formed(witness),
                   "missing_corner":[1,6],"near_ring_center":[2,7],"true_ring_center":[2,2],
                   "documented_domain":"8x10 grid; background 0; one complete gray 3x3 hollow ring with empty center; separated gray distractor that is not a complete 3x3 ring. The seven-cell near-ring is outside the hardcoded 2x2/bar distractor catalogue but satisfies the stated invariants and validator."},
        "override_probes":axis_results,"malformed_probes":malformed,
        "semantic_contract_inventory":{k:hasattr(gen,k) for k in ("strict_canonical_like","SEMANTIC_WITNESSES","SEMANTIC_RIVALS","CANONICAL_SHORTCUTS","LESSON_COMPETITORS","lesson_identifiable")},
        "apply_cases":apply_cases,"authority_status":"pending_public_arcpuzzles_apply"}
    dump("input.json",[case["input"] for case in apply_cases])
    dump("python-probe.json",report)
    print(json.dumps({"source_sha256":digest,"rule_hash":rule_hash,"canonical_fit":canonical_fits,
                      "draws":count,"crashes":len(crashes),"unique_inputs":len(input_hashes),
                      "rival_disagreements":len(rival_disagreements),"apply_case_count":len(apply_cases),
                      "override_probes":axis_results,
                      "malformed_probes":[{k:v for k,v in case.items() if k != "input"} for case in malformed]}))


def finalize():
    report = json.loads((OUT/"python-probe.json").read_text())
    racket = json.loads((OUT/"racket.json").read_text())
    assert racket["generator_sha256"] == EXPECTED_SOURCE
    assert racket["executed_rule_hash"] == report["selected_rule_hash"]
    assert racket["rule_hash_matches_catalog"] is True
    assert len(racket["results"]) == len(report["apply_cases"])
    for case, result in zip(report["apply_cases"],racket["results"]):
        assert result["error"] is None and result["valid_output"] is True
        assert case["input"] == result["input"]
        assert case["python_reference_output"] == result["output"]
        case["actual_racket_output"] = result["output"]
        case["rival_mismatch_cells"] = [[r,c] for r in range(len(result["output"]))
             for c in range(len(result["output"][0])) if case["rival_output"][r][c] != result["output"][r][c]]
        case["input_sha256"] = result["input_sha256"]
        case["output_sha256"] = result["output_sha256"]
    assert report["apply_cases"][-1]["rival_mismatch_cells"] == [[2,7]]
    assert not any(case["rival_mismatch_cells"] for case in report["apply_cases"][:-1])
    report["authority_status"] = "near_ring_counterexample_confirmed_by_public_racket_apply"
    report["authority_receipt"] = "racket.json"
    report["authority_receipt_sha256"] = hashlib.sha256((OUT/"racket.json").read_bytes()).hexdigest()
    dump("evidence.json",report)
    print(json.dumps({"status":report["authority_status"],"racket_case_count":len(report["apply_cases"]),
                      "witness_rival_mismatch_cells":report["apply_cases"][-1]["rival_mismatch_cells"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize",action="store_true")
    if parser.parse_args().finalize:
        finalize()
    else:
        run_probe()
