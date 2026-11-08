"""Source-bound findings-only replay: an ignore-portals rival survives five demos."""
from pathlib import Path
import hashlib
import json

from arcpuzzles.catalog import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "4cea2727fcf9"
EXPECTED = "91f94df8b2a448ccf8556bf788465ffa9faa1cc765baacbc692c6f2d6a9499a9"


def main():
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED, (digest, EXPECTED)
    program = Catalog(root).get(TASK)["variants"][0]["program_solution"]
    start = program.index("(define (portal-exit p)")
    depth = 0
    for end in range(start, len(program)):
        depth += (program[end] == "(") - (program[end] == ")")
        if depth == 0:
            break
    rival = program[:start] + "(define (portal-exit p) p)" + program[end+1:]
    report = {"task_id": TASK, "source": str(source.relative_to(root)),
              "generator_sha256": digest, "seed": 22, "difficulty": "medium",
              "canonical_program": program, "rival_program": rival,
              "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "rival_sha256": hashlib.sha256(rival.encode()).hexdigest(), "pairs": []}
    with RacketBridge() as bridge:
        report["runtime"] = bridge.runtime_identity
        def execute(code, grid):
            bridge.define_grid("g", grid)
            return bridge.eval_text(strip_rule_wrapper(code))
        for index in range(6):
            grid = gen.generate(22, index, difficulty="medium")
            errors = gen.self_check(grid, difficulty="medium")
            assert not errors, (index, errors)
            actual, alternate = execute(program, grid), execute(rival, grid)
            report["pairs"].append({"sample_index": index, "role": "demo" if index < 5 else "query",
                                     "input": grid, "self_check": errors,
                                     "input_sha256": hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest(),
                                     "portal_cells": sum(v == 4 for row in grid for v in row),
                                     "canonical_output": actual, "rival_output": alternate,
                                     "outputs_equal": actual == alternate})
        originals = canonical_pairs(TASK, root=root)
        checks = [execute(program, p["input"]) == p["output"] for p in originals]
        report["canonical_parity"] = {"passed": sum(checks), "total": len(checks)}
        assert all(checks)
    report["rival_fits_all_five_demos"] = all(p["outputs_equal"] for p in report["pairs"][:5])
    report["rival_differs_on_query"] = not report["pairs"][5]["outputs_equal"]
    assert report["rival_fits_all_five_demos"] and report["rival_differs_on_query"]
    # A finite axis-honesty probe, independent of the shortcut finding.
    baseline = gen.generate(22, 0, difficulty="medium")
    settings = [{"palette_kind": "warm"}, {"palette_size": 3},
                {"palette_size": 6}, {"n_distinct_colors": 3},
                {"n_distinct_colors": 6}, {"texture": "varied"}]
    report["axis_probe"] = [{"overrides": o, "same_as_baseline": gen.generate(22,0,difficulty="medium",**o) == baseline}
                             for o in settings]
    report["baseline_color_count"] = len({v for row in baseline for v in row})
    out = Path(__file__).with_name("replay.json")
    out.write_text(json.dumps(report,separators=(",",":"))+"\n")
    print(json.dumps({k:v for k,v in report.items() if k in {
        "generator_sha256", "canonical_parity", "rival_fits_all_five_demos",
        "rival_differs_on_query", "axis_probe", "baseline_color_count"}}))


if __name__ == "__main__":
    main()
