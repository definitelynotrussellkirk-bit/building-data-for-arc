"""Bounded, findings-only audit. Never edits selected generator or shared files."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK_ID = "4fd85612056f"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def components(grid):
    seen = set()
    out = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        pending.append((nr, nc))
                        seen.add((nr, nc))
            lo_r = min(p[0] for p in cells)
            hi_r = max(p[0] for p in cells)
            lo_c = min(p[1] for p in cells)
            hi_c = max(p[1] for p in cells)
            cell_set = set(cells)
            height, width = hi_r - lo_r + 1, hi_c - lo_c + 1
            crop = [[grid[rr][cc] if (rr, cc) in cell_set else 0
                     for cc in range(lo_c, hi_c + 1)] for rr in range(lo_r, hi_r + 1)]
            out.append({"bbox": [lo_r, lo_c, hi_r, hi_c], "height": height,
                        "width": width, "cell_count": len(cells),
                        "nonrectangular": len(cells) < height * width, "crop": crop})
    return out


def first_nonrectangular_rival(grid):
    """Ignores height; first nonrectangular 4-connected component in reading order."""
    choices = [c for c in components(grid) if c["nonrectangular"]]
    return choices[0]["crop"] if choices else None


def load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_4fd85612056f", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    home = REPO / "generators" / TASK_ID
    source = (home / "generator.py").read_bytes()
    (HERE / "audited_generator.py").write_bytes(source)
    for name in ("notes.md", "SUMMARY.md"):
        (HERE / ("audited_" + name)).write_bytes((home / name).read_bytes())
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    exact = []
    for index, line in enumerate(canonical_path.read_bytes().splitlines(keepends=True), 1):
        if b'"task_id": "4fd85612056f"' in line:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                exact.append((index, line, row))
    assert len(exact) == 1, f"Expected one exact canonical row, got {len(exact)}"
    line_number, raw, canonical = exact[0]
    (HERE / "canonical_record.json").write_bytes(raw)
    rule = canonical["program_solution"].encode()
    (HERE / "canonical_rule.rkt").write_bytes(rule)
    index_path = home / "evidence/review_index.json"
    index_record = json.loads(index_path.read_text()) if index_path.exists() else None
    dump("source_hashes.json", {
        "task_id": TASK_ID, "generator_path": "generators/4fd85612056f/generator.py",
        "generator_sha256": sha(source), "generator_version": "1.4.0",
        "canonical_path": str(canonical_path.relative_to(REPO)), "canonical_line": line_number,
        "canonical_record_sha256_including_newline": sha(raw),
        "canonical_rule_text_sha256": sha(rule),
        "notes_sha256": sha((home / "notes.md").read_bytes()),
        "associated_notes_sha256": sha((home / "evidence/associated_notes.jsonl").read_bytes()),
        "audit_index_path": "generators/4fd85612056f/evidence/review_index.json",
        "audit_index_exists": index_path.exists(), "audit_index": index_record,
    })
    generator = load_generator()
    cases = []

    def add(case_id, grid, **extra):
        comp = components(grid)
        cases.append({"case_id": case_id, "input": grid,
                      "self_check": generator.self_check(grid), "components": comp,
                      "nonrectangular_count": sum(c["nonrectangular"] for c in comp),
                      "rival_output": first_nonrectangular_rival(grid), **extra})

    # Five canonical labels and examples, accessed only for this assigned audit task.
    for split in ("train", "test"):
        for pair_index, pair in enumerate(canonical[split]):
            add(f"canonical_{split}_{pair_index}", pair["input"], kind="canonical",
                canonical_split=split, canonical_pair_index=pair_index,
                expected_output=pair["output"], seed=None, sample_index=None, overrides=None)

    # 18 independent seed/sample/difficulty coordinates, all helpful default texture.
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for sample_index in (0, 1):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                add(f"generated_{difficulty}_{seed}_{sample_index}", grid, kind="generated",
                    seed=seed, sample_index=sample_index, difficulty=difficulty, overrides={})

    # Compact counterexample with all declared grid dimensions and components in range.
    witness = [[2, 2, 0, 1, 0],
               [2, 0, 0, 1, 0],
               [0, 0, 1, 1, 0],
               [0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0]]
    add("manual_two_irregular", witness, kind="manual", seed=None, sample_index=None,
        overrides=None, expected_output=[[0, 1], [0, 1], [1, 1]])
    dump("witness_input.json", witness)

    # One declared integer override, sufficient to test whether it is honored.
    baseline = generator.generate(0, 0, difficulty="medium")
    overridden = generator.generate(0, 0, difficulty="medium", grid_h=5)
    dump("override_probe.json", {
        "seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"grid_h": 5},
        "declared_axis": generator.AXES["grid_h"], "requested_height": 5,
        "actual_height": len(overridden), "actual_width": len(overridden[0]),
        "identical_to_no_override": overridden == baseline,
        "self_check": generator.self_check(overridden), "input": overridden,
        "corresponding_racket_case_id": "generated_medium_0_0"
    })
    dump("cases.json", cases)
    dump("input.json", {"inputs": [c["input"] for c in cases]})
    print(json.dumps({"stage": "prepare", "case_count": len(cases),
                      "generated_count": sum(c["kind"] == "generated" for c in cases),
                      "canonical_count": sum(c["kind"] == "canonical" for c in cases),
                      "source_sha256": sha(source), "rule_text_sha256": sha(rule),
                      "audit_index_exists": index_path.exists(),
                      "override_actual_height": len(overridden),
                      "witness_self_check": generator.self_check(witness)}))


def compare():
    cases = json.loads((HERE / "cases.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    assert len(racket["results"]) == len(cases)
    assert racket["rule_hash_matches_catalog"]
    rows = []
    for case, result in zip(cases, racket["results"], strict=True):
        assert case["input"] == result["input"]
        row = {**case, "racket_output": result["output"], "racket_error": result["error"],
               "rival_matches_racket": case["rival_output"] == result["output"]}
        if "expected_output" in case:
            row["racket_matches_expected"] = case["expected_output"] == result["output"]
        rows.append(row)
    generated = [r for r in rows if r["kind"] == "generated"]
    canonical = [r for r in rows if r["kind"] == "canonical"]
    witness = next(r for r in rows if r["case_id"] == "manual_two_irregular")
    summary = {
        "task_id": TASK_ID, "generator_sha256": racket["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
        "racket_case_count": len(rows), "racket_errors": sum(bool(r["racket_error"]) for r in rows),
        "generated_count": len(generated),
        "generated_self_check_passed": sum(not r["self_check"] for r in generated),
        "generated_unique_nonrectangular": sum(r["nonrectangular_count"] == 1 for r in generated),
        "generated_rival_matches": sum(r["rival_matches_racket"] for r in generated),
        "canonical_count": len(canonical),
        "canonical_racket_matches": sum(r["racket_matches_expected"] for r in canonical),
        "canonical_self_check_rejections": [{"case_id": r["case_id"], "self_check": r["self_check"]}
                                             for r in canonical if r["self_check"]],
        "canonical_rival_disagreements": [r["case_id"] for r in canonical if not r["rival_matches_racket"]],
        "manual_witness": witness,
        "override_probe": json.loads((HERE / "override_probe.json").read_text()),
        "scope": "One task; 18 helpful generated inputs, five canonical pairs, one manual witness, one override comparison. No battery or solve access."
    }
    assert summary["racket_errors"] == 0
    assert summary["canonical_racket_matches"] == 5
    assert summary["generated_self_check_passed"] == 18
    assert summary["generated_unique_nonrectangular"] == 18
    assert summary["generated_rival_matches"] == 18
    assert not witness["self_check"] and not witness["rival_matches_racket"]
    assert witness["racket_matches_expected"]
    dump("comparisons.json", rows)
    dump("findings.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("manual_witness", "override_probe")}))


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
