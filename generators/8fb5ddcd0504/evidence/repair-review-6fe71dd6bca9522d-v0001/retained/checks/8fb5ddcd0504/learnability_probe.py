"""Bounded private rival probe; does not modify or accept the generator."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2] / "repo"
TASK = "8fb5ddcd0504"
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mirror(grid, kind="canonical"):
    occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    r0, r1 = min(r for r, _ in occupied), max(r for r, _ in occupied)
    c0, c1 = min(c for _, c in occupied), max(c for _, c in occupied)
    a = [row[c0:c1+1] for row in grid[r0:r1+1]]
    lr = [row[::-1] for row in a]
    top = [x + y for x, y in zip(a, a if kind in ("repeat_horizontal", "repeat_both") else lr)]
    out = top + (top if kind in ("repeat_vertical", "repeat_both") else top[::-1])
    if kind == "fixed_output_6x4":
        out = [[out[r][c] if r < len(out) and c < len(out[0]) else 0
                for c in range(4)] for r in range(6)]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source = ROOT / "generators" / TASK / "generator.py"
    source_hash = sha(source.read_bytes())
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK)
    rows = catalog._variants()[selected.get("rule_task_id", TASK)]
    assert len(rows) == 1
    program = rows[0]["program_solution"]
    rivals = {
        "repeat_horizontal": program.replace("(flip-lr objg)", "objg").replace("(rotate-180 objg)", "(flip-ud objg)"),
        "repeat_vertical": program.replace("(flip-ud objg)", "objg").replace("(rotate-180 objg)", "(flip-lr objg)"),
        "repeat_both": program.replace("(flip-lr objg)", "objg").replace("(flip-ud objg)", "objg").replace("(rotate-180 objg)", "objg"),
        "fixed_output_6x4": program.replace("(base (empty-grid (* h 2) (* w 2) 0))", "(base (empty-grid 6 4 0))"),
    }
    assert all(value != program for value in rivals.values())
    lessons = [{"origin": "canonical_saved_pairs", "train": rows[0]["train"], "test": rows[0]["test"]}]
    with _local_imports(ROOT / "shared/runtime", source.parent):
        from reviewer_support import load_selected_generator
        generator, path, observed_hash = load_selected_generator(TASK, root=ROOT)
        assert path == source and observed_hash == source_hash
        invalid = []
        for seed in range(16):
            pairs = []
            for index in range(7):
                grid = generator.generate(seed, index, difficulty="medium")
                errors = generator.self_check(grid)
                if errors:
                    invalid.append({"seed": seed, "index": index, "errors": errors})
                pairs.append({"input": grid, "output": mirror(grid)})
            lessons.append({"origin": "generated", "seed": seed,
                            "sample_indices": list(range(7)), "train": pairs[:3], "test": pairs[3:]})
        findings, checks = [], []
        for lesson_index, lesson in enumerate(lessons):
            for name in rivals:
                agreement = [mirror(pair["input"], name) == pair["output"] for pair in lesson["train"]]
                disagreements = [mirror(pair["input"], name) != pair["output"] for pair in lesson["test"]]
                checks.append({"lesson_index": lesson_index, "origin": lesson["origin"],
                               "seed": lesson.get("seed"), "rival": name,
                               "demo_agreement": agreement, "query_disagreement": disagreements})
                if all(agreement) and any(disagreements):
                    query_index = disagreements.index(True)
                    findings.append({"lesson_index": lesson_index, "origin": lesson["origin"],
                                     "seed": lesson.get("seed"), "rival": name,
                                     "train": lesson["train"], "query": lesson["test"][query_index],
                                     "query_index": query_index})
        # Retain the canonical witness plus at most one generated witness per rival.
        retained, seen = [], set()
        for finding in findings:
            key = (finding["origin"], finding["rival"])
            if key not in seen:
                seen.add(key)
                retained.append(finding)
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        evaluations = 0
        cache = {}
        def execute(code, grid):
            nonlocal evaluations
            key = (code, json.dumps(grid))
            if key not in cache:
                cache[key] = _grid(apply(code, grid))
                evaluations += 1
            return cache[key]
        try:
            canonical_checked = 0
            for pair in rows[0]["train"] + rows[0]["test"]:
                assert execute(program, pair["input"]) == pair["output"]
                assert mirror(pair["input"]) == pair["output"]
                canonical_checked += 1
            for finding in retained:
                code = rivals[finding["rival"]]
                for pair in finding["train"]:
                    assert execute(program, pair["input"]) == pair["output"]
                    assert execute(code, pair["input"]) == pair["output"]
                pair = finding["query"]
                assert execute(program, pair["input"]) == pair["output"]
                prediction = execute(code, pair["input"])
                assert prediction != pair["output"]
                assert prediction == mirror(pair["input"], finding["rival"])
                finding["racket_rival_query_output"] = prediction
                finding["protected_replayed"] = True
            # Reassigning the existing canonical query as a demo defeats the
            # fixed-size rival; this does not establish universal identifiability.
            distinguishing = rows[0]["test"][0]
            rescued = execute(rivals["fixed_output_6x4"], distinguishing["input"]) != distinguishing["output"]
        finally:
            bridge.close()
    assert sha(source.read_bytes()) == source_hash
    programs = {"canonical": program, **rivals}
    for name, code in programs.items():
        (args.out / (name + ".rkt")).write_text(code)
    result = {
        "schema": "arcpuzzles-bounded-peer-learnability-v1", "task_id": TASK,
        "status": "finding" if retained else "no_finding_in_tested_family",
        "generator_sha256": source_hash, "rule_hash": selected["rule_hash"],
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "program_sha256": {name: sha(code.encode()) for name, code in programs.items()},
        "racket": identity, "racket_evaluations": evaluations,
        "counts": {"canonical_pairs_replayed": canonical_checked, "generated_lessons_screened": 16,
                   "generated_inputs_screened": 112, "rivals": len(rivals),
                   "lesson_rival_checks": len(checks), "python_screen_findings": len(findings),
                   "protected_retained_findings": len(retained), "invalid_generated_inputs": len(invalid)},
        "lesson_contract_present": False, "checks": checks, "findings": retained,
        "canonical_distinguishing_demo_available": rescued, "invalid_inputs": invalid,
        "remaining_limits": ["The generated screen uses an independent Python mirror; only retained cases and the three canonical labels were replayed in protected Racket.",
                             "Four finite rivals, sixteen deterministic generated lessons, no universal uniqueness claim.",
                             "No generator repair, approval, acceptance, or full battery was performed.",
                             "The previously retained ignored-control finding was not re-audited."],
    }
    (args.out / "report.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "racket_evaluations": evaluations, "report": str(args.out / "report.json")}))


if __name__ == "__main__":
    main()
